"""LLMProvider 内部委托 batch executor 的接缝完整测试(Phase 12 T11 + T15)。

T11 落地 5 case:
  - phase="candidates" + router 已配 → 走 LLMBatchExecutor,返回 per_dimension_batch_metadata
  - phase="candidates" 部分失败 → promotable=False
  - phase="discovery" + 仅 router(无 llm_client) → 不走 batch,直接 raise ProviderNotAvailable
  - 老 caller LLMProvider(llm_client) 位置参数兼容
  - 既没 router 也没 llm_client → raise ProviderNotAvailable

T15 补 4 case 到 9:
  - phase="convergence" 不走 batch — 应走 llm_client 老路径(stub 被调)
  - generate 公共签名稳定:(self, phase, context_bundle, template_prompts, node, **kwargs)
  - router 完全失败(7 dim 全 timeout)→ promotable=False + error_class=timeout
  - LLMProvider(batch_concurrency=N) 必须透传到底层 LLMBatchExecutor 限制 in-flight
"""

import asyncio
import inspect
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


# ---------------------------------------------------------------------------
# T15 补充的 4 个 case → 总 9 case
# ---------------------------------------------------------------------------

def test_llm_provider_convergence_NOT_batched() -> None:
    """Case 6:phase='convergence' 不走 batch — 应走 llm_client 老路径。

    即使配了 router + policy,convergence 也只走 llm_client.call();stub.called=True 证明。
    """
    router, policy = _make_fake_router(7)

    class StubClient:
        """记录是否被调到 + 返一个合法 convergence JSON。"""
        called = False

        def call(self, messages: list) -> str:
            StubClient.called = True
            # 合法 convergence 最小 JSON,绕过 validate_phase_output_for_acceptance
            return (
                '{"converged_choices": ['
                '{"dimension_id": "d1", "chosen_candidate": "c1", '
                '"rationale": "r", "rejected_alternatives": []}'
                '], "cross_dimension_consistency": {"conflicts": []}}'
            )

    stub = StubClient()
    # llm_client + router 同时配;convergence 必须仅走 stub,不动 router
    provider = LLMProvider(llm_client=stub, router=router, policy=policy)
    out = provider.generate(
        phase="convergence",
        context_bundle={},
        template_prompts={"system_prompt": "sys"},
        node={},
    )
    # 关键断言:stub 被调用 = 走了老路径,没去拨 router
    assert StubClient.called is True
    # 老路径 metadata.promotable=True 是默认语义(LLMProvider.generate 老路径硬写 True)
    assert out["metadata"]["promotable"] is True
    assert out["metadata"]["generator_type"] == "llm"


def test_llm_provider_public_signature_unchanged() -> None:
    """Case 7:generate(phase, context_bundle, template_prompts, node, **kwargs) 公共签名稳定。

    防止内部 batch executor 接入意外破坏外部 caller(如 AgentPhaseRunner)的调用契约。
    inspect 把 **kwargs 显示为 'kwargs'(VAR_KEYWORD)是 Python 的固定行为。
    """
    sig = inspect.signature(LLMProvider.generate)
    params = list(sig.parameters.keys())
    # self + 4 positional + **kwargs
    assert params == ["self", "phase", "context_bundle", "template_prompts", "node", "kwargs"]


def test_llm_provider_router_failure_propagates() -> None:
    """Case 8:router 完全失败(7 dim 全 timeout × 3 attempts)→ promotable=False。

    每个 dim 都走 ProviderTimeout × 3 触发 max_attempts 耗尽,
    LLMProvider 必须把 7 dim 的 failed/timeout 透传到 per_dimension_batch_metadata。
    """
    from Plugins.AgentBridge.Compiler.providers.base import ProviderTimeout

    fa = FakeAdapter()
    # 7 dim × 3 attempts(默认 max_attempts) = 21 个 timeout output
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout(f"t{i}")) for i in range(7 * 3)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    # batch_concurrency=1 + RetryPolicySpec 默认 backoff_base_s=2 会让 case 跑数十秒;
    # LLMProvider 内部用的是 RetryPolicySpec() 默认值,这里调小 concurrency 不影响测试语义,
    # 但为了不动 production,接受 ~默认 retry 时间(timeout error 默认 backoff
    # exponential base=2 第 1 次 2s + 第 2 次 4s ≈ 6s/dim × 7 dim = 42s — 太慢)。
    # 因此用 concurrency=7 让 7 dim 并行,总耗时 ≈ 6s + jitter。
    provider = LLMProvider(router=router, policy=policy, batch_concurrency=7)

    out = provider.generate(
        phase="candidates",
        context_bundle=_make_ctx_with_dims(7),
        template_prompts={"system_prompt": "sys"},
        node={},
    )
    assert out["metadata"]["promotable"] is False
    assert len(out["per_dimension_batch_metadata"]) == 7
    assert all(m["status"] == "failed" for m in out["per_dimension_batch_metadata"])
    assert all(m["error_class"] == "timeout" for m in out["per_dimension_batch_metadata"])


def test_llm_provider_batch_concurrency_propagated() -> None:
    """Case 9:LLMProvider(batch_concurrency=N) 必须传到底层 LLMBatchExecutor。

    通过 CountingFake 在每次 structured 调用进入/退出时维护 in-flight 计数,
    断 max in-flight == 2 证明 semaphore 上限确为 2。
    """
    in_flight = {"count": 0, "max": 0}

    class CountingFake(FakeAdapter):
        """子类化 FakeAdapter:override astructured_with_usage(LLMBatchExecutor 实际调用的钩子)。

        关键设计:LLMProvider._generate_candidates_via_batch 用 RetryPolicySpec() 默认值,
        jitter_ms 默认 (100, 500)。每个 task 进 sem 后先 jitter sleep ~100-500ms,
        然后才进 CountingFake。要让 in_flight 窗口稳定重叠,CountingFake 内 sleep 必须
        显著大于 jitter 上限(500ms),否则 max 可能拍到 1。这里取 0.6s 确保重叠。
        """

        async def astructured_with_usage(self, call, schema):
            in_flight["count"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["count"])
            # > jitter 上限 500ms,确保并发窗口稳定重叠
            await asyncio.sleep(0.6)
            try:
                return await super().astructured_with_usage(call, schema)
            finally:
                in_flight["count"] -= 1

    fa = CountingFake()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": []})
        for i in range(7)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    # 关键:batch_concurrency=2 必须在底层强制 semaphore=2
    provider = LLMProvider(router=router, policy=policy, batch_concurrency=2)

    provider.generate(
        phase="candidates",
        context_bundle=_make_ctx_with_dims(7),
        template_prompts={"system_prompt": "sys"},
        node={},
    )
    assert in_flight["max"] == 2, f"batch_concurrency 未透传,max={in_flight['max']}"
