"""candidates_batch_orchestrator 完整 10 case 集成测试。

Phase 12 T10 落地最小 5 case:happy path / retry-recover / 3x-timeout-fails /
unsupported-no-retry / concurrency-enforcement。
Phase 12 T15 在此基础上补 5 case 到完整 10:
  - Case 6: schema_fail 默认在 retry_on,应被重试
  - Case 7: jitter sleep 实际生效(用真延时断言总耗时下界)
  - Case 8: 6 success + 1 fail → promotable=False, partial=True
  - Case 9: DimensionBatch 各字段(status/attempt/duration/model/parsed_payload/usage)全填
  - Case 10: 落盘到 DimensionBatch 的字段必须不含 api_key 原文(evidence redaction)
设计依据:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §3.4 + §4 + §6.3
"""

import asyncio
import time
from dataclasses import asdict

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


# ---------------------------------------------------------------------------
# T15 补充的 5 个 case → 总 10 case
# ---------------------------------------------------------------------------

def test_batch_schema_fail_retries() -> None:
    """Case 6:SchemaValidationError 在默认 retry_on 白名单内 → 应被重试 1 次后恢复。"""
    # SchemaValidationError 在 providers.base,从那里导入
    from Plugins.AgentBridge.Compiler.providers.base import SchemaValidationError

    fa = FakeAdapter()
    fa.program("m", outputs=[
        # 第 1 次坏 shape,第 2 次正常成功
        FakeModelProgram(raise_error=SchemaValidationError("invalid shape 1")),
        FakeModelProgram(schema_value={"dimension_id": "d1", "candidates": ["c1"]}),
        # 其余 6 dim 各 1 次成功
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
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.01),
        concurrency=1,  # 顺序消费 FakeAdapter outputs
    ))
    # 第 1 个 dim 经 retry 后恢复成功
    assert report.per_dimension[0].status == "success"
    assert report.per_dimension[0].attempt_count == 2
    assert report.promotable is True
    assert report.partial is False


def test_batch_jitter_sleep_applied() -> None:
    """Case 7:启用 jitter (50, 50) + concurrency=1 + 7 dim 时,总耗时 ≥ 7 * 50ms = 350ms。

    设计:不 monkeypatch asyncio.sleep(可能干扰 asyncio.run 内部其他 sleep),
    改测真延时下界更稳定。
    每个 dim 进入临界区前 jitter sleep ~50ms,concurrency=1 序列化 → 总耗时 ≥ 350ms。
    """
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": []})
        for i in range(7)
    ])
    router = CapabilityRouter()
    router.register(fa)
    policy = ProviderPolicy(preferred_models=["m"])
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
        for i in range(7)
    ]
    start = time.monotonic()
    asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        # jitter 固定 50ms(j_min == j_max → uniform 必然返回 50)
        retry_policy=RetryPolicySpec(jitter_ms=(50, 50)),
        concurrency=1,
    ))
    elapsed_ms = (time.monotonic() - start) * 1000
    # 7 dim × 50ms = 350ms 下界(允许些许调度开销宽容,真实跑通约 380ms+)
    assert elapsed_ms >= 350, f"jitter 未生效,总耗时仅 {elapsed_ms}ms"


def test_batch_promotable_requires_all_success() -> None:
    """Case 8:6 success + 1 fail → promotable=False, partial=True。"""
    from Plugins.AgentBridge.Compiler.providers.base import ProviderTimeout

    fa = FakeAdapter()
    # 第 1 个 dim 连续 3 次 timeout(永远失败),其余 6 个各 1 次 success
    fa.program("m", outputs=[
        FakeModelProgram(raise_error=ProviderTimeout(f"t{i}")) for i in range(3)
    ] + [
        FakeModelProgram(schema_value={"dimension_id": f"d{i+2}", "candidates": []})
        for i in range(6)
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
        concurrency=1,  # 顺序消费 outputs 让分配可预期
    ))
    success_count = sum(1 for b in report.per_dimension if b.status == "success")
    failed_count = sum(1 for b in report.per_dimension if b.status == "failed")
    assert success_count == 6
    assert failed_count == 1
    assert report.promotable is False
    assert report.partial is True


def test_batch_per_dim_metadata_full_fields() -> None:
    """Case 9:所有 DimensionBatch 字段都应填。

    断字段:status / attempt_count / duration_ms / model / parsed_payload / usage。
    FakeAdapter 通过 astructured_with_usage 透传 FakeModelProgram.usage,这里也一并断 dict 类型。
    """
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(
            schema_value={"dimension_id": f"d{i+1}", "candidates": []},
            usage={"prompt": 100, "completion": 50, "total": 150},
        )
        for i in range(7)
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
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1)),
        concurrency=3,
    ))
    for b in report.per_dimension:
        assert b.status == "success"
        assert b.attempt_count == 1
        assert b.duration_ms >= 0
        assert b.model == "m"
        assert b.parsed_payload is not None
        assert b.parsed_payload["dimension_id"].startswith("d")
        # usage 必须落盘成 dict;FakeAdapter astructured_with_usage 已透传 usage,
        # 即使透传机制变(降级)dict 类型断言依然成立
        assert isinstance(b.usage, dict)


def test_batch_per_dim_metadata_does_not_leak_api_key() -> None:
    """Case 10:落盘到 DimensionBatch 的字段必须不含 api_key 原文 — 防 evidence 泄密。

    api_key 仅应停在 policy 上,在 _rebind 后封进 ProviderCall,
    LLMBatchExecutor 不把 api_key 写进 DimensionBatch 任何字段。
    """
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": []})
        for i in range(7)
    ])
    router = CapabilityRouter()
    router.register(fa)
    # 配真 api_key 形式(脱敏前形如此)
    policy = ProviderPolicy(
        preferred_models=["m"],
        api_key="sk-real-secret-1234567890",
        api_base="https://api.example.com",
    )
    ex = LLMBatchExecutor()
    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": "x"}]}
        for i in range(7)
    ]
    report = asyncio.run(ex.run_candidates_batch(
        dimensions=dims, router=router, policy=policy, schema=CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1)),
        concurrency=3,
    ))
    # 序列化每个 DimensionBatch,确认 api_key 原文从未出现
    for b in report.per_dimension:
        d = asdict(b)
        serialized = str(d)
        assert "sk-real-secret-1234567890" not in serialized, (
            f"api_key 泄漏到 DimensionBatch: {d}"
        )
