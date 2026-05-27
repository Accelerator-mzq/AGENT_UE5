"""Stage 4 Candidates 按 dimension 分批 + concurrency 控制 + 纯结构拼接聚合。

Phase 12 T10 — LLM Internal Reopen 核心调度层:把 Stage 4 Candidates 从
"单次 LLM 调用拿 7 dim" 改成 "7 个 dimension 各自独立 LLM 调用,asyncio 并发,
失败可重试"。

设计依据:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §3.4 + §4

关键设计:
- async-only 主表面,通过 `asyncio.run` 桥接到 sync 调用方(Stage 4 现有同步 entry)
- `asyncio.Semaphore(concurrency)` 控制最大并发,防止短时把 provider quota 打爆
- 每个 dim 进入临界区前先做 jitter sleep(避免 7 个 task 同步触发产生峰值)
- retry loop 按 RetryPolicySpec.retry_on 决定是否重试:
  - timeout / transient_network / rate_limit / schema_fail → 可重试
  - unsupported_response → **永不重试**(确定性坏 shape,重试浪费 quota)
- 聚合阶段纯结构拼接:promotable = 全部 success;partial = 有任一 failed
"""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from ..providers._retry import is_rate_limited, is_transient_network_message
from ..providers.base import (
    ProviderCall,
    ProviderError,
    ProviderTimeout,
    ProviderUnsupportedResponse,
    SchemaValidationError,
)
from ..providers.capability_router import CapabilityRouter, ProviderPolicy


# ---------------------------------------------------------------------------
# Data classes — RetryPolicySpec / DimensionBatch / AggregatedReport
# ---------------------------------------------------------------------------

@dataclass
class RetryPolicySpec:
    """retry_policy.schema.json 的运行时镜像。

    字段语义对齐 Schemas/retry_policy.schema.json(T08 落地),
    数值默认值匹配 design doc §4.2 推荐值。
    """
    # 最多尝试次数(含首次),例如 3 = 首次 + 2 次重试
    max_attempts: int = 3
    # 退避模式:目前仅支持 "exponential" / "linear"
    backoff_mode: str = "exponential"
    # 指数退避基数 (秒),实际等待 = backoff_base_s * 2^attempt(封顶 8s)
    backoff_base_s: float = 2.0
    # 启动 jitter + 每次 backoff 后再叠加的随机 jitter (毫秒)
    jitter_ms: tuple[int, int] = (100, 500)
    # 哪些 error_class 会触发 retry;其他直接 fail
    retry_on: tuple[str, ...] = (
        "timeout", "transient_network", "schema_fail", "rate_limit",
    )


@dataclass
class DimensionBatch:
    """单个 dimension 的 batch 执行结果。

    Schema 对齐 design_space_report.schema.json 的 per_dimension_batch_metadata
    (T09 已扩字段:dimension_id / model / attempt_count / duration_ms / usage /
    status / error_class / raw_response_id)。
    """
    dimension_id: str
    prompt_messages: list[dict[str, Any]]
    attempt_count: int = 0
    duration_ms: int = 0
    usage: dict[str, int] = field(default_factory=dict)
    # "success" | "failed" | "pending"
    status: str = "pending"
    error_class: str | None = None
    raw_response_id: str | None = None
    model: str | None = None
    parsed_payload: dict[str, Any] | None = None


@dataclass
class AggregatedReport:
    """7 个 dim batch 聚合后的总报告 — 纯结构拼接,无额外业务规则。

    - promotable:全部 dim 都 success 才可推进到 Stage 5
    - partial:有任一 failed 就标 True,供 governance / observability 看
    """
    per_dimension: list[DimensionBatch]
    promotable: bool
    partial: bool = False
    aggregation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# LLMBatchExecutor — 核心调度器
# ---------------------------------------------------------------------------

class LLMBatchExecutor:
    """Stage 4 Candidates 分批执行器 — async-only,通过 asyncio.run 桥接到 sync 调用方。"""

    async def run_candidates_batch(
        self,
        *,
        dimensions: list[dict[str, Any]],
        router: CapabilityRouter,
        policy: ProviderPolicy,
        schema: type[BaseModel],
        retry_policy: RetryPolicySpec | None = None,
        concurrency: int = 3,
    ) -> AggregatedReport:
        """按 concurrency 并发跑所有 dim,gather 后做纯结构聚合。

        Args:
            dimensions: 形如 [{"dimension_id": "d1", "prompt_messages": [...]}]
            router: 已注册 adapter 的 CapabilityRouter
            policy: ProviderPolicy(preferred_models / fallback_models / temperature / ...)
            schema: pydantic schema,LLM 返回会按它做 structured parse
            retry_policy: RetryPolicySpec;None 时用默认值
            concurrency: 最大并发 task 数,asyncio.Semaphore 控制
        """
        retry_policy = retry_policy or RetryPolicySpec()
        sem = asyncio.Semaphore(concurrency)

        async def one_batch(d: dict[str, Any]) -> DimensionBatch:
            # 单个 dim 的 coroutine 包装,把 sem 等所有上下文带进去
            return await self._run_one(d, router, policy, schema, retry_policy, sem)

        results = await asyncio.gather(*(one_batch(d) for d in dimensions))

        # 聚合:全 success 才 promotable;有任一 failed 就 partial
        promotable = all(b.status == "success" for b in results)
        partial = any(b.status == "failed" for b in results)
        return AggregatedReport(
            per_dimension=results,
            promotable=promotable,
            partial=partial,
        )

    async def _run_one(
        self,
        d: dict[str, Any],
        router: CapabilityRouter,
        policy: ProviderPolicy,
        schema: type[BaseModel],
        retry_policy: RetryPolicySpec,
        sem: asyncio.Semaphore,
    ) -> DimensionBatch:
        """跑单个 dim 的完整流程:semaphore + jitter + retry loop + 错误分类。"""
        batch = DimensionBatch(
            dimension_id=d["dimension_id"],
            prompt_messages=d["prompt_messages"],
        )
        async with sem:
            # 启动 jitter — 避免 7 个 task 同瞬触发对 provider 产生峰值
            j_min, j_max = retry_policy.jitter_ms
            await asyncio.sleep(random.uniform(j_min, j_max) / 1000)

            start = time.monotonic()
            for attempt in range(retry_policy.max_attempts):
                batch.attempt_count = attempt + 1
                try:
                    call = ProviderCall(
                        model=policy.preferred_models[0],
                        messages=batch.prompt_messages,
                        temperature=policy.temperature,
                        max_tokens=policy.max_tokens,
                        timeout_s=policy.timeout_s,
                        api_key=policy.api_key,
                        api_base=policy.api_base,
                        # _forge_prompt_cache:让 LiteLLM 走 prompt-cache 头
                        # (FakeAdapter 忽略,真 LLM 路径才用)
                        extra={"_forge_prompt_cache": True},
                    )
                    obj, model_used, usage = await router.astructured(
                        policy=policy, call_template=call, schema=schema,
                    )
                    batch.model = model_used
                    batch.usage = usage or {}
                    batch.parsed_payload = obj.model_dump(mode="json")
                    batch.status = "success"
                    batch.duration_ms = int((time.monotonic() - start) * 1000)
                    return batch
                except ProviderUnsupportedResponse:
                    # **关键**:unsupported_response 永不重试。
                    # 这是确定性坏 shape,retry 只会再次烧钱拿同样的坏返回。
                    # 必须在通用 ProviderError 之前 catch — 否则会被分类成
                    # provider_error 走 retry 路径。
                    batch.status = "failed"
                    batch.error_class = "unsupported_response"
                    batch.duration_ms = int((time.monotonic() - start) * 1000)
                    return batch
                except (ProviderTimeout, SchemaValidationError, ProviderError) as exc:
                    # 通用错误路径:分类 + 决定是否 retry
                    # 注意 ProviderTimeout / SchemaValidationError 都是 ProviderError 子类,
                    # 这里显式列出是为了让分类逻辑明确(且让阅读时不依赖继承关系)
                    error_class = self._classify(exc)
                    is_last_attempt = (attempt + 1 >= retry_policy.max_attempts)
                    is_retryable = error_class in retry_policy.retry_on
                    if is_last_attempt or not is_retryable:
                        batch.status = "failed"
                        batch.error_class = error_class
                        batch.duration_ms = int((time.monotonic() - start) * 1000)
                        return batch
                    # 还有重试 budget,sleep backoff 然后 continue 下一轮
                    await self._sleep_backoff(retry_policy, attempt, exc)
            # safety net,理论上 unreachable(loop 内必然 return)
            batch.status = "failed"
            batch.error_class = "exhausted"
            batch.duration_ms = int((time.monotonic() - start) * 1000)
            return batch

    def _classify(self, exc: Exception) -> str:
        """把异常映射到 retry_policy.retry_on 用的 error_class 字符串。

        注意分类顺序:
        - ProviderTimeout 优先(类型最具体)
        - SchemaValidationError 次之(独立子类型)
        - 然后 ProviderError 拆 rate_limit / transient_network / generic
        """
        if isinstance(exc, ProviderTimeout):
            return "timeout"
        if isinstance(exc, SchemaValidationError):
            return "schema_fail"
        if isinstance(exc, ProviderError):
            # rate_limit 必须先判:它跟 transient_network 在 marker 上有重叠(429),
            # 但 rate_limit 要走更长退避,不能被 transient 退避吃掉
            if is_rate_limited(exc):
                return "rate_limit"
            if is_transient_network_message(str(exc)):
                return "transient_network"
            return "provider_error"
        return "unknown"

    async def _sleep_backoff(
        self,
        rp: RetryPolicySpec,
        attempt: int,
        exc: Exception,
    ) -> None:
        """按 backoff_mode + rate-limit 标记决定 sleep 时长。

        - exponential:base * 2^attempt,封顶 8s
        - linear:固定 base
        - rate_limit 命中时把 base 拉到 max(base*2, 5s) 防连续撞墙
        - 每次再叠加 jitter_ms 随机数,避免 wave-front 同步重试
        """
        if rp.backoff_mode == "exponential":
            base = min(rp.backoff_base_s * 2 ** attempt, 8.0)
        else:
            base = rp.backoff_base_s
        if is_rate_limited(exc):
            base = max(base * 2, 5.0)
        j_min, j_max = rp.jitter_ms
        await asyncio.sleep(base + random.uniform(j_min, j_max) / 1000)
