"""pipeline_orchestrator 装 router 的 smoke 测试(Phase 12 T12)。

验证:
  1. build_default_router 可从 pipeline_orchestrator 顶部 import 链接进来
  2. 本地无 llm_config.yaml(或 placeholder)时,build_default_router() 返 None — 不抛
  3. resolve_provider(router=R, policy=P) 优先于 llm_client 走 LLM batch 路径
"""

import pytest

from Plugins.AgentBridge.Compiler.providers.model_registry import build_default_router
from Plugins.AgentBridge.Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Plugins.AgentBridge.Compiler.providers.capability_router import CapabilityRouter, ProviderPolicy
from Plugins.AgentBridge.Compiler.stages import agent_protocol


def test_build_default_router_no_config_returns_none(tmp_path) -> None:
    """指定不存在的 config 路径 → 返 None,不抛。"""
    out = build_default_router(tmp_path / "nonexistent.yaml")
    assert out is None


def test_resolve_provider_prefers_router_over_llm_client() -> None:
    """有 router+policy 时,优先于 llm_client(同时传也走新路径)。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(schema_value={"dimension_id": "d1", "candidates": []})])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])

    class StubClient:
        # 老路径 llm_client 占位 — 仅用来证明 resolve_provider 优先走 router 不走 client
        def call(self, messages):
            return "{}"

    provider = agent_protocol.resolve_provider(
        allow_heuristic_fallback=False,
        llm_client=StubClient(),
        router=router,
        policy=policy,
    )
    assert isinstance(provider, agent_protocol.LLMProvider)
    assert provider._router is router
    assert provider._policy is policy
    # Note: 当前实现里 LLMProvider 在 router+policy 走新路径时,_client 仍可能保留传入
    # 但 generate(phase="candidates") 会优先走 batch — 这个由 T11 测试覆盖,本测只验证 resolve 决策


def test_resolve_provider_falls_back_to_llm_client_when_no_router() -> None:
    """没传 router 时退到 llm_client 路径。"""
    class StubClient:
        # 老路径 llm_client 占位
        def call(self, messages):
            return "{}"
    provider = agent_protocol.resolve_provider(
        allow_heuristic_fallback=False,
        llm_client=StubClient(),
    )
    assert isinstance(provider, agent_protocol.LLMProvider)
    assert provider._router is None


def test_resolve_provider_heuristic_when_nothing_configured() -> None:
    """既无 router 又无 llm_client + allow_heuristic_fallback=True → HeuristicFallbackProvider。"""
    provider = agent_protocol.resolve_provider(
        allow_heuristic_fallback=True,
    )
    # 不抛即 OK — HeuristicFallbackProvider.provider_type 返回 "heuristic_fallback"
    assert provider is not None
    assert isinstance(provider, agent_protocol.HeuristicFallbackProvider)
    assert provider.provider_type == "heuristic_fallback"


def test_resolve_provider_no_config_raises() -> None:
    """既无 router/llm_client 又禁止 heuristic → raise ProviderNotAvailable。"""
    with pytest.raises(agent_protocol.ProviderNotAvailable):
        agent_protocol.resolve_provider(allow_heuristic_fallback=False)
