# -*- coding: utf-8 -*-
"""Phase 12 L2-A:providers 子树单元测试整合(spec §6.2 覆盖度目标 ≥ 85%)。

合并自 Phase 0 + T13 的 4 个 smoke 文件:
- test_providers_smoke.py(base + _retry + 异常体系)
- test_litellm_adapter_smoke.py(LiteLLMAdapter)
- test_router_registry_smoke.py(CapabilityRouter + model_registry)
- test_fake_adapter_smoke.py(FakeAdapter offline 桩)

Phase 12 T14 在末尾 Section E 增补缺失 case,提高 spec §6.2 覆盖度。
"""

from __future__ import annotations

import asyncio
import time as _time
from pathlib import Path

import pytest
from pydantic import BaseModel

# ============================================================================
# 公共 import — 所有 section 共用,避免重复
# ============================================================================

from Plugins.AgentBridge.Compiler.providers import (
    ProviderAdapter,
    ProviderCall,
    ProviderResult,
    ProviderError,
    ProviderTimeout,
    ProviderUnsupportedResponse,
    SchemaValidationError,
)
from Plugins.AgentBridge.Compiler.providers._retry import (
    with_transient_retry,
    is_transient_network_message,
    is_rate_limited,
)
from Plugins.AgentBridge.Compiler.providers.litellm_adapter import (
    LiteLLMAdapter,
    _is_anthropic_family,
    _maybe_apply_prompt_cache,
    _maybe_auto_compact,
    _extract_text,
)
from Plugins.AgentBridge.Compiler.providers.capability_router import (
    CapabilityRouter,
    ProviderPolicy,
    PreparedRoute,
)
from Plugins.AgentBridge.Compiler.providers.model_registry import (
    load_provider_policy_from_yaml,
    build_default_router,
)
from Plugins.AgentBridge.Compiler.providers.fake_adapter import (
    FakeAdapter,
    FakeModelProgram,
)


# ============================================================================
# Section A: base + _retry + 异常体系(原 test_providers_smoke.py)
# ============================================================================

def test_exception_hierarchy() -> None:
    """4 类 typed exception 应继承自 ProviderError。"""
    assert issubclass(ProviderTimeout, ProviderError)
    assert issubclass(ProviderUnsupportedResponse, ProviderError)
    assert issubclass(SchemaValidationError, ProviderError)


def test_is_rate_limited_429() -> None:
    assert is_rate_limited(Exception("HTTP 429 Too Many Requests")) is True


def test_is_rate_limited_529_overload() -> None:
    assert is_rate_limited(Exception("529 overloaded_error")) is True


def test_is_rate_limited_non_rate_limit() -> None:
    assert is_rate_limited(Exception("Connection reset by peer")) is False


def test_is_transient_network_message_timeout() -> None:
    assert is_transient_network_message("Request timed out") is True


def test_provider_call_dataclass_defaults() -> None:
    pc = ProviderCall(model="x", messages=[])
    assert pc.temperature == 0.0
    assert pc.timeout_s is None
    assert pc.extra == {}


# ============================================================================
# Section B: LiteLLMAdapter(原 test_litellm_adapter_smoke.py)
# ============================================================================

def test_litellm_adapter_init() -> None:
    # 构造默认 timeout 应回写到实例字段,name 固定为 "litellm"
    a = LiteLLMAdapter(default_timeout_s=30.0)
    assert a.name == "litellm"
    assert a._default_timeout_s == 30.0


def test_litellm_adapter_supports_anything() -> None:
    # supports() 设计为宽松通过,具体 gating 由 ProviderPolicy 负责
    a = LiteLLMAdapter()
    assert a.supports("anything/at/all") is True


def test_is_anthropic_family() -> None:
    # anthropic/ 前缀 / claude- 前缀 / 模型名含 claude 都算 Anthropic 家族
    assert _is_anthropic_family("anthropic/claude-3-haiku-20240307") is True
    assert _is_anthropic_family("claude-3-opus") is True
    assert _is_anthropic_family("gpt-4o") is False


def test_prompt_cache_short_system_no_inject() -> None:
    """system msg < 1024 字符不应注入 cache_control。"""
    call = ProviderCall(
        model="claude-3-haiku",
        messages=[{"role": "system", "content": "短"}],
        extra={"_forge_prompt_cache": True},
    )
    out = _maybe_apply_prompt_cache(call)
    # 短 system 不被 tag,content 保持原始 str
    assert isinstance(out[0]["content"], str)


def test_prompt_cache_long_system_injects() -> None:
    """system msg ≥ 1024 字符且开关开启时应注入 cache_control。"""
    long_text = "x" * 1500
    call = ProviderCall(
        model="anthropic/claude-3-haiku",
        messages=[{"role": "system", "content": long_text}],
        extra={"_forge_prompt_cache": True},
    )
    out = _maybe_apply_prompt_cache(call)
    # 长 system 被 tag 成 multi-block 含 cache_control
    assert isinstance(out[0]["content"], list)
    assert out[0]["content"][0].get("cache_control") == {"type": "ephemeral"}


def test_prompt_cache_off_by_default() -> None:
    """没有 _forge_prompt_cache=True 时,不注入 cache_control(即便是长 system)。"""
    long_text = "x" * 1500
    call = ProviderCall(
        model="anthropic/claude-3-haiku",
        messages=[{"role": "system", "content": long_text}],
        extra={},  # 未设 _forge_prompt_cache
    )
    out = _maybe_apply_prompt_cache(call)
    # 不被 tag,content 维持 str
    assert isinstance(out[0]["content"], str)


def test_extract_text_empty_choices_raises_unsupported() -> None:
    """resp.choices=[] 时应 raise ProviderUnsupportedResponse,而非静默回空字符串。"""
    class FakeResp:
        choices = []  # empty list

    with pytest.raises(ProviderUnsupportedResponse):
        _extract_text(FakeResp())


def test_extract_text_missing_choices_raises_unsupported() -> None:
    """resp 没有 .choices 属性时也应 raise ProviderUnsupportedResponse。"""
    class FakeResp:
        pass  # 无 choices

    with pytest.raises(ProviderUnsupportedResponse):
        _extract_text(FakeResp())


# ============================================================================
# Section C: CapabilityRouter + ProviderPolicy(原 test_router_registry_smoke.py)
# ============================================================================

def test_router_register_resolve() -> None:
    """LiteLLMAdapter 注册后 _resolve 任意 model 都返回它(因 supports always True)。"""
    r = CapabilityRouter()
    a = LiteLLMAdapter()
    r.register(a)
    assert r._resolve("any/model") is a


def test_router_no_adapter_raises() -> None:
    # 没注册任何 adapter 时 _resolve 必须抛 ProviderError
    r = CapabilityRouter()
    with pytest.raises(ProviderError):
        r._resolve("any/model")


def test_load_policy_missing_file_returns_none() -> None:
    # 配置文件不存在应优雅降级返回 None
    assert load_provider_policy_from_yaml("/nonexistent/path.yaml") is None


def test_load_policy_placeholder_returns_none(tmp_path: Path) -> None:
    # api_key 是占位符时(YOUR_API_KEY_HERE / REPLACE_ME 等)应返回 None
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: anthropic\nmodel: claude-3-haiku\napi_key: REPLACE_ME\n",
        encoding="utf-8",
    )
    assert load_provider_policy_from_yaml(cfg) is None


def test_load_policy_valid(tmp_path: Path) -> None:
    # 有效配置应正确装配 ProviderPolicy 各字段
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: anthropic\n"
        "model: anthropic/claude-3-haiku-20240307\n"
        "api_key: sk-real-but-faked-for-test-1234567890\n"
        "base_url: https://api.example.com\n"
        "timeout_sec: 30\n"
        "max_tokens: 4096\n",
        encoding="utf-8",
    )
    p = load_provider_policy_from_yaml(cfg)
    assert p is not None
    assert p.preferred_models == ["anthropic/claude-3-haiku-20240307"]
    assert p.fallback_models == []
    assert p.timeout_s == 30.0
    assert p.max_tokens == 4096


def test_build_default_router_missing_config_returns_none() -> None:
    # 配置缺失时 build_default_router 应返回 None 给调用方降级机会
    assert build_default_router("/nonexistent/path.yaml") is None


def test_provider_policy_default_fields() -> None:
    """ProviderPolicy dataclass 默认值合理。"""
    p = ProviderPolicy()
    assert p.preferred_models == []
    assert p.fallback_models == []
    assert p.timeout_s == 60.0
    assert p.temperature == 0.7
    assert p.extra == {}


def test_router_routes_returns_preferred_first() -> None:
    """_routes 应该按 preferred → fallback 顺序输出,deduped。"""
    p = ProviderPolicy(
        preferred_models=["m1", "m2"],
        fallback_models=["m2", "m3"],  # m2 重复应去重
        api_key="k", api_base="b",
    )
    routes = CapabilityRouter._routes(p)
    assert len(routes) == 3
    assert [r.model for r in routes] == ["m1", "m2", "m3"]


def test_router_routes_empty_raises() -> None:
    # 没有任何 preferred / fallback model 时 _routes 必须抛 ProviderError
    p = ProviderPolicy()
    with pytest.raises(ProviderError):
        CapabilityRouter._routes(p)


def test_load_policy_auto_prefix_anthropic(tmp_path: Path) -> None:
    """provider=anthropic + model 裸写 → 自动拼 anthropic/ 前缀。"""
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: anthropic\n"
        "model: claude-3-haiku-20240307\n"
        "api_key: sk-test-fake-1234567890\n",
        encoding="utf-8",
    )
    p = load_provider_policy_from_yaml(cfg)
    assert p is not None
    assert p.preferred_models == ["anthropic/claude-3-haiku-20240307"], \
        f"expected auto-prefix, got: {p.preferred_models}"


def test_load_policy_existing_prefix_not_doubled(tmp_path: Path) -> None:
    """model 已带 / 视为合规,不重复拼前缀。"""
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: anthropic\n"
        "model: openai/gpt-4o\n"
        "api_key: sk-test-fake-1234567890\n",
        encoding="utf-8",
    )
    p = load_provider_policy_from_yaml(cfg)
    assert p is not None
    assert p.preferred_models == ["openai/gpt-4o"], \
        f"expected no double-prefix, got: {p.preferred_models}"


def test_load_policy_unknown_provider_no_prefix(tmp_path: Path) -> None:
    """未知 provider(如 'bedrock')不强拼前缀,让 litellm 自己抛清晰错误。"""
    cfg = tmp_path / "llm_config.yaml"
    cfg.write_text(
        "provider: bedrock\n"
        "model: anthropic.claude-3-haiku\n"
        "api_key: sk-test-fake-1234567890\n",
        encoding="utf-8",
    )
    p = load_provider_policy_from_yaml(cfg)
    assert p is not None
    # provider 不在 known_providers 集合内,model 保持裸名
    assert p.preferred_models == ["anthropic.claude-3-haiku"]


def test_load_policy_from_example_template_with_real_key_substituted(tmp_path: Path) -> None:
    """example yaml 替换 api_key 后应能装载，且 Phase 12 新字段进 policy.extra。

    注意：Phase 0 移植的 model_registry.load_provider_policy_from_yaml 把
    prompt_cache.enabled 扁平化成 extra["prompt_cache_enabled"]（bool），
    其余四个字段（concurrency / retry / auto_compact / budget）保留嵌套 dict。
    """
    src = Path("Plugins/AgentBridge/Config/llm_config.example.yaml")
    dst = tmp_path / "llm_config.yaml"
    text = src.read_text(encoding="utf-8").replace("YOUR_API_KEY_HERE", "sk-test-fake-key-1234567890")
    dst.write_text(text, encoding="utf-8")

    p = load_provider_policy_from_yaml(dst)
    assert p is not None, "example yaml 替换 api_key 后必须能装载"
    # Phase 12 新字段进 extra
    assert "concurrency" in p.extra
    assert p.extra["concurrency"]["candidates_batch"] == 3
    assert "retry" in p.extra
    assert p.extra["retry"]["max_attempts"] == 3
    # prompt_cache 在 model_registry 里被扁平化成 prompt_cache_enabled 布尔
    assert "prompt_cache_enabled" in p.extra
    assert p.extra["prompt_cache_enabled"] is True
    assert "auto_compact" in p.extra
    assert p.extra["auto_compact"]["enabled"] is False
    assert "budget" in p.extra
    assert p.extra["budget"]["observe_only"] is True


# ============================================================================
# Section D: FakeAdapter(原 test_fake_adapter_smoke.py)
# ============================================================================

class DimSchema(BaseModel):
    """FakeAdapter structured 测试用的 schema。"""
    dimension_id: str
    score: int


def test_fake_adapter_supports_only_programmed() -> None:
    """未注册 model 应返 False,注册后返 True。"""
    fa = FakeAdapter()
    assert fa.supports("not-programmed") is False
    fa.program("test-model", outputs=[FakeModelProgram(text="x")])
    assert fa.supports("test-model") is True


def test_fake_adapter_sequential_pop() -> None:
    """多个 outputs 按 FIFO 顺序弹出。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(text="first"),
        FakeModelProgram(text="second"),
    ])
    call = ProviderCall(model="m", messages=[])
    r1 = asyncio.run(fa.acompletion(call))
    r2 = asyncio.run(fa.acompletion(call))
    assert r1.text == "first"
    assert r2.text == "second"


def test_fake_adapter_raise_error() -> None:
    """raise_error 字段触发指定 exception。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(raise_error=ProviderTimeout("simulated"))])
    call = ProviderCall(model="m", messages=[])
    with pytest.raises(ProviderTimeout):
        asyncio.run(fa.acompletion(call))


def test_fake_adapter_structured() -> None:
    """schema_value 通过 Pydantic 校验,返回 BaseModel 实例。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1", "score": 5},
    )])
    call = ProviderCall(model="m", messages=[])
    obj = asyncio.run(fa.astructured(call, DimSchema))
    assert isinstance(obj, DimSchema)
    assert obj.dimension_id == "d1"
    assert obj.score == 5


def test_fake_adapter_structured_invalid_raises() -> None:
    """schema_value 不满足 schema 时 raise SchemaValidationError。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1"},  # 缺 score
    )])
    call = ProviderCall(model="m", messages=[])
    with pytest.raises(SchemaValidationError):
        asyncio.run(fa.astructured(call, DimSchema))


def test_fake_adapter_astructured_with_usage_returns_tuple() -> None:
    """astructured_with_usage 返回 (obj, usage) 二元组。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1", "score": 5},
        usage={"prompt": 100, "completion": 50, "total": 150},
    )])
    call = ProviderCall(model="m", messages=[])
    obj, usage = asyncio.run(fa.astructured_with_usage(call, DimSchema))
    assert isinstance(obj, DimSchema)
    assert usage == {"prompt": 100, "completion": 50, "total": 150}


# ============================================================================
# Section E: Phase 12 T14 新增 case — 补 spec §6.2 缺失
# ============================================================================

class _RetryStubExc(ProviderError):
    """retry 测试用的 transient 异常子类。"""
    pass


def test_provider_result_dataclass_with_usage() -> None:
    """ProviderResult dataclass 字段类型与基础语义。"""
    pr = ProviderResult(text="x", model="m", usage={"total": 10})
    assert pr.text == "x"
    assert pr.model == "m"
    assert pr.usage == {"total": 10}


def test_provider_result_default_usage_empty_dict() -> None:
    """ProviderResult.usage 默认为空 dict,raw 默认空 dict(spec §6.2 dataclass shape)。"""
    pr = ProviderResult(text="abc", model="m")
    assert pr.text == "abc"
    assert pr.usage == {}
    assert pr.raw == {}


def test_capability_router_preferred_then_fallback_order() -> None:
    """_routes 应按 preferred → fallback 顺序输出,不去重时序保 preferred 优先。"""
    p = ProviderPolicy(preferred_models=["m1", "m2"], fallback_models=["m3"])
    routes = CapabilityRouter._routes(p)
    assert [r.model for r in routes] == ["m1", "m2", "m3"]


def test_capability_router_unsupported_model_no_fallback() -> None:
    """空 adapter 列表时 _resolve 直接抛 ProviderError(无 fallback 路径)。"""
    router = CapabilityRouter()
    with pytest.raises(ProviderError):
        router._resolve("nonexistent/model")


def test_with_transient_retry_exhausts_max_attempts() -> None:
    """with_transient_retry 在 max_attempts 用完后必须抛最后一次的异常。"""
    call_count = {"n": 0}

    def flaky() -> str:
        call_count["n"] += 1
        raise _RetryStubExc("Connection reset by peer")

    with pytest.raises(_RetryStubExc):
        with_transient_retry(
            flaky,
            transient_check=lambda e: True,  # 始终视作 transient
            max_attempts=3,
            backoff_s=0.001,
        )
    # 应该刚好尝试 3 次(max_attempts)
    assert call_count["n"] == 3


def test_with_transient_retry_non_transient_propagates_immediately() -> None:
    """transient_check 返 False 时,异常立即冒出,不消耗剩余尝试。"""
    call_count = {"n": 0}

    def fn() -> str:
        call_count["n"] += 1
        raise ValueError("business-logic 4xx")

    with pytest.raises(ValueError):
        with_transient_retry(
            fn,
            transient_check=lambda e: False,  # 非 transient
            max_attempts=5,
            backoff_s=0.001,
        )
    # 只调用 1 次,不重试
    assert call_count["n"] == 1


def test_with_transient_retry_recovers_on_second_attempt(monkeypatch) -> None:
    """前 N-1 次失败,最后一次成功:返回该成功结果,且 sleep 调用 ≥ 1 次。"""
    sleeps: list[float] = []
    monkeypatch.setattr(_time, "sleep", lambda s: sleeps.append(s))

    call_count = {"n": 0}

    def flaky() -> str:
        call_count["n"] += 1
        if call_count["n"] < 3:
            raise _RetryStubExc("connection reset")
        return "ok"

    out = with_transient_retry(
        flaky,
        transient_check=lambda e: True,
        max_attempts=5,
        backoff_s=0.5,
    )
    assert out == "ok"
    assert call_count["n"] == 3
    # 失败 2 次 + 成功 1 次 → sleep 至少 2 次
    assert len(sleeps) >= 2


def test_litellm_auto_compact_off_by_default_returns_messages_unchanged() -> None:
    """LiteLLMAdapter _maybe_auto_compact 默认无 _forge_auto_compact_tokens 标记时,
    原样返回 messages list,不裁剪。"""
    call = ProviderCall(model="m", messages=[{"role": "user", "content": "短"}])
    out = _maybe_auto_compact(call)
    # 返回 list,内容与原 messages 等价(注意:实现返回的是 list(call.messages) 副本)
    assert isinstance(out, list)
    assert out == [{"role": "user", "content": "短"}]


def test_litellm_auto_compact_when_flag_set_truncates() -> None:
    """设置 _forge_auto_compact_tokens 后,超 budget 的 messages 应被裁。"""
    call = ProviderCall(
        model="m",
        messages=[
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "x" * 5000},
            {"role": "assistant", "content": "a"},
            {"role": "user", "content": "tail"},
        ],
        extra={"_forge_auto_compact_tokens": 10, "_forge_auto_compact_tail": 1},
    )
    out = _maybe_auto_compact(call)
    # 触发 compact:返回的 list 长度应 < 原 messages 数
    assert len(out) < 4
    # tail 必保留(尾部最后一条)
    assert out[-1]["content"] == "tail"


def test_prepared_route_carries_policy_keys() -> None:
    """PreparedRoute 应正确把 ProviderPolicy 的 api_key/api_base/timeout_s 透出。"""
    p = ProviderPolicy(
        preferred_models=["m1"],
        api_key="k",
        api_base="https://api.example.com",
        timeout_s=42.0,
    )
    routes = CapabilityRouter._routes(p)
    assert len(routes) == 1
    assert routes[0].model == "m1"
    assert routes[0].api_key == "k"
    assert routes[0].api_base == "https://api.example.com"
    assert routes[0].timeout_s == 42.0


def test_is_transient_network_message_5xx() -> None:
    """5xx HTTP 状态(502/503/504)文本应被视为 transient。"""
    assert is_transient_network_message("HTTP 502 Bad Gateway") is True
    assert is_transient_network_message("503 service unavailable") is True


def test_is_transient_network_message_business_error() -> None:
    """业务级错误(4xx 非 408/429)不应被视为 transient。"""
    assert is_transient_network_message("400 bad request") is False
    assert is_transient_network_message("invalid api key") is False
