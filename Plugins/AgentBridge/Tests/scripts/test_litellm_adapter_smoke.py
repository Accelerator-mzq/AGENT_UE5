"""LiteLLMAdapter smoke 测试 — 不打真 LLM,只验证类构造与基础逻辑。"""

from Plugins.AgentBridge.Compiler.providers.litellm_adapter import (
    LiteLLMAdapter,
    _is_anthropic_family,
    _maybe_apply_prompt_cache,
)
from Plugins.AgentBridge.Compiler.providers.base import ProviderCall


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
