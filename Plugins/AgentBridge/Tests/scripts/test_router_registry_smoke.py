# -*- coding: utf-8 -*-
"""capability_router + model_registry smoke 测试。

覆盖:
- CapabilityRouter 注册 / _resolve / 空 adapter 抛 ProviderError
- ProviderPolicy dataclass 默认值
- _routes 去重 + preferred 优先 + 空 policy 抛 ProviderError
- load_provider_policy_from_yaml 各种异常路径(缺文件 / 占位符 / 有效)
- build_default_router 配置缺失返回 None
"""

from pathlib import Path

import pytest

from Plugins.AgentBridge.Compiler.providers.capability_router import (
    CapabilityRouter, ProviderPolicy, PreparedRoute,
)
from Plugins.AgentBridge.Compiler.providers.model_registry import (
    load_provider_policy_from_yaml,
    build_default_router,
)
from Plugins.AgentBridge.Compiler.providers.base import ProviderError


def test_router_register_resolve() -> None:
    """LiteLLMAdapter 注册后 _resolve 任意 model 都返回它(因 supports always True)。"""
    from Plugins.AgentBridge.Compiler.providers.litellm_adapter import LiteLLMAdapter
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
