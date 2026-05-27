"""LLMProvider 内部委托 batch executor 的接缝测试(Phase 12 T11)。

验证:
  - phase="candidates" + router 已配 → 走 LLMBatchExecutor,返回 per_dimension_batch_metadata
  - phase="discovery" + 仅 router(无 llm_client) → 不走 batch,直接 raise ProviderNotAvailable
  - 老 caller LLMProvider(llm_client) 位置参数兼容
"""

from typing import Any

import pytest
from pydantic import BaseModel

from Plugins.AgentBridge.Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Plugins.AgentBridge.Compiler.providers.capability_router import (
    CapabilityRouter, ProviderPolicy,
)
from Plugins.AgentBridge.Compiler.stages.agent_protocol import (
    LLMProvider, ProviderNotAvailable,
)


def _make_fake_router(n_dims: int = 7) -> tuple[CapabilityRouter, ProviderPolicy]:
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": [f"c{i+1}"]})
        for i in range(n_dims)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    return router, policy


def _make_ctx_with_dims(n_dims: int = 7) -> dict:
    return {
        "design_space_report": {
            "discovery_dimensions": [
                {"dimension_id": f"d{i+1}", "name": f"dim {i+1}", "description": "test",
                 "variant_bounds": {}}
                for i in range(n_dims)
            ]
        }
    }


def test_llm_provider_candidates_phase_routes_to_batch_executor() -> None:
    """phase='candidates' + router 已配 → 走 LLMBatchExecutor。"""
    router, policy = _make_fake_router(7)
    provider = LLMProvider(router=router, policy=policy, batch_concurrency=2)

    out = provider.generate(
        phase="candidates",
        context_bundle=_make_ctx_with_dims(7),
        template_prompts={"system_prompt": "sys", "domain_prompt": "dom"},
        node={"id": "test-node"},
    )
    assert "per_dimension_batch_metadata" in out
    assert len(out["per_dimension_batch_metadata"]) == 7
    assert all(m["status"] == "success" for m in out["per_dimension_batch_metadata"])
    assert out["metadata"]["promotable"] is True
    assert out["metadata"]["generator_type"] == "llm"


def test_llm_provider_candidates_partial_failure_promotable_false() -> None:
    """1 dim 失败 → promotable=False。"""
    fa = FakeAdapter()
    # 第 1 个 dim 走全 timeout,其余成功
    from Plugins.AgentBridge.Compiler.providers.base import ProviderTimeout
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout(f"t{i}")) for i in range(3)
    ] + [
        FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []})
        for i in range(6)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    # concurrency=1 让 FakeAdapter outputs 顺序消费
    provider = LLMProvider(router=router, policy=policy, batch_concurrency=1)

    out = provider.generate(
        phase="candidates",
        context_bundle=_make_ctx_with_dims(7),
        template_prompts={"system_prompt": "sys"},
        node={},
    )
    assert out["metadata"]["promotable"] is False
    assert out["per_dimension_batch_metadata"][0]["status"] == "failed"
    assert out["per_dimension_batch_metadata"][0]["error_class"] == "timeout"


def test_llm_provider_discovery_phase_NOT_batched() -> None:
    """phase='discovery' 即使 router 已配也不走 batch — 老路径走 llm_client。
    本 case 验证:无 llm_client 时 discovery 直接 raise ProviderNotAvailable(确认没走 batch)。"""
    router, policy = _make_fake_router(7)
    provider = LLMProvider(router=router, policy=policy)
    # discovery 必走老路径,而老路径无 llm_client → raise
    with pytest.raises(ProviderNotAvailable):
        provider.generate(
            phase="discovery",
            context_bundle={},
            template_prompts={"system_prompt": "sys"},
            node={},
        )


def test_llm_provider_positional_llm_client_backward_compat() -> None:
    """LLMProvider(llm_client) 位置参数构造方式不能破(stage4_*.py 现有用法)。"""

    class StubClient:
        def call(self, messages: list) -> str:
            return '{"discovery_dimensions": [], "locked_dimensions": []}'

    provider = LLMProvider(StubClient())   # 位置参数
    # 不抛 = 兼容
    assert provider._client is not None
    assert provider._router is None


def test_llm_provider_no_router_no_client_raises() -> None:
    """既没 router 也没 llm_client → candidates 仍会 raise(由老路径触发)。"""
    provider = LLMProvider()
    with pytest.raises(ProviderNotAvailable):
        provider.generate(
            phase="candidates",
            context_bundle={},
            template_prompts={"system_prompt": "sys"},
            node={},
        )
