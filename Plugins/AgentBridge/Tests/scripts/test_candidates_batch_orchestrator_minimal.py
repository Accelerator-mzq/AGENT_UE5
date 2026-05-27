"""candidates_batch_orchestrator 最小 happy path:7 dim 全 FakeAdapter 返成功。

Phase 12 T10 — TDD 第一步,先让 import 失败暴露模块缺失,再补实现。
设计依据:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §3.4 + §4
"""

import asyncio

from pydantic import BaseModel

# 项目 convention:从项目根 (pytest.ini pythonpath=.) 用全路径 import
from Plugins.AgentBridge.Compiler.providers.fake_adapter import (
    FakeAdapter, FakeModelProgram,
)
from Plugins.AgentBridge.Compiler.providers.capability_router import (
    CapabilityRouter, ProviderPolicy,
)
from Plugins.AgentBridge.Compiler.providers.base import (
    ProviderTimeout, ProviderUnsupportedResponse,
)
from Plugins.AgentBridge.Compiler.stages.candidates_batch_orchestrator import (
    LLMBatchExecutor,
    DimensionBatch,
    AggregatedReport,
    RetryPolicySpec,
)


class CandSchema(BaseModel):
    """Stage 4 Candidates 最小返回结构,只为测试 LLMBatchExecutor 通路。"""
    dimension_id: str
    candidates: list[str]


def make_router_7_success() -> tuple[CapabilityRouter, ProviderPolicy]:
    """构造一个 router:对单 model "m" 注册 7 个 happy path FakeModelProgram。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": [f"c_{i+1}"]})
        for i in range(7)
    ])
    r = CapabilityRouter()
    r.register(fa)
    p = ProviderPolicy(preferred_models=["m"], fallback_models=[])
    return r, p


def test_batch_7_dims_all_success() -> None:
    """7 个 dimension 各自 LLM 调一次全成功,promotable 为 True、partial 为 False。"""
    router, policy = make_router_7_success()
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": f"d{i+1}"}]}
        for i in range(7)
    ]
    report: AggregatedReport = asyncio.run(ex.run_candidates_batch(
        dimensions=dims,
        router=router,
        policy=policy,
        schema=CandSchema,
        retry_policy=RetryPolicySpec(),
        concurrency=3,
    ))
    # 7 个 dim 全部成功,promotable=True,且无任何 failed 故 partial=False
    assert len(report.per_dimension) == 7
    assert all(b.status == "success" for b in report.per_dimension)
    assert report.promotable is True
    assert report.partial is False


def test_batch_single_dim_retry_recovers() -> None:
    """单 dim 第 1 次 timeout、第 2 次成功;其余 6 dim 直接成功。

    concurrency=1 让 FakeAdapter 队列顺序可控 (一个 dim 消费完才走下一个)。
    """
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout("simulated 1")),
        FakeModelProgram(schema_value={"dimension_id": "d1", "candidates": ["c1"]}),
        # 其余 6 dim 各 1 次成功 output
        *[FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []}) for i in range(6)],
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
        for i in range(7)
    ]
    # jitter_ms / backoff 压到 ~0 让 retry 测试不慢
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,
    ))
    assert report.per_dimension[0].status == "success"
    assert report.per_dimension[0].attempt_count == 2  # 第 1 次 timeout 第 2 次成功
    assert report.promotable is True
    assert report.partial is False


def test_batch_single_dim_3x_timeout_fails() -> None:
    """单 dim 连续 3 次 timeout,耗尽 max_attempts,该 dim 失败,promotable=False。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout(f"timeout {i}")) for i in range(3)
    ] + [
        FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []}) for i in range(6)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
        for i in range(7)
    ]
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,
    ))
    assert report.per_dimension[0].status == "failed"
    assert report.per_dimension[0].error_class == "timeout"
    assert report.per_dimension[0].attempt_count == 3
    assert report.promotable is False
    assert report.partial is True


def test_batch_unsupported_response_no_retry() -> None:
    """ProviderUnsupportedResponse 是确定性坏 shape,不应触发 retry(立即 fail)。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderUnsupportedResponse("bad shape")),
    ] + [
        FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []}) for i in range(6)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
        for i in range(7)
    ]
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,
    ))
    assert report.per_dimension[0].status == "failed"
    assert report.per_dimension[0].error_class == "unsupported_response"
    assert report.per_dimension[0].attempt_count == 1  # 关键:不重试
    assert report.promotable is False


def test_batch_concurrency_limit_enforced() -> None:
    """concurrency=2 时 max in-flight 必须 ≤ 2。

    通过 CountingFake 在 astructured_with_usage 进入 / 退出时更新计数,
    取整个 run 周期内 in-flight 峰值,断言 == 2。
    """
    in_flight = {"count": 0, "max": 0}

    class CountingFake(FakeAdapter):
        """子类化 FakeAdapter,在每次 structured 调用前后维护 in-flight 计数。"""

        async def astructured_with_usage(self, call, schema):
            in_flight["count"] += 1
            in_flight["max"] = max(in_flight["max"], in_flight["count"])
            # 制造 ~50ms 延迟,让 semaphore 真的能并发出 max 个 task
            await asyncio.sleep(0.05)
            try:
                return await super().astructured_with_usage(call, schema)
            finally:
                in_flight["count"] -= 1

    fa = CountingFake()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": []}) for i in range(7)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
        for i in range(7)
    ]
    asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1)),
        concurrency=2,
    ))
    # semaphore=2 严格意义上 max 不能超过 2
    assert in_flight["max"] == 2
