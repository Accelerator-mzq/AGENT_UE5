"""Capability Router — 按 ProviderPolicy 在多 model 间路由(preferred → fallback)。

从 ForgeUE_codex `src/framework/providers/capability_router.py` 移植适配:
- 删除 image_* 方法(本项目 LLM 文本路径不需要)
- 删除 D plan 的 `prepared_routes` 分支(本期单 model 不实现)
- 删除 `_stash_route_pricing_*` 系列(本期 budget 是 observe-only,T07 才接)
- 内嵌 `ProviderPolicy` + `PreparedRoute` dataclass(避免引入 framework.core.policies 跨模块依赖)

Fallback 循环骨架保留以便中期扩多 model,但本期 `policy.fallback_models=[]` 始终空。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel

from .base import (
    ProviderAdapter,
    ProviderCall,
    ProviderError,
    ProviderResult,
    ProviderUnsupportedResponse,
    _run_sync,
)


# ---------------------------------------------------------------------------
# 内嵌 dataclass — 本项目最小化 ProviderPolicy / PreparedRoute
# ---------------------------------------------------------------------------

@dataclass
class ProviderPolicy:
    """本项目最小化版 ProviderPolicy。

    本期单 model,fallback_models 默认空。中期扩多 model 路由时再丰富字段
    (例如 ForgeUE 那种 prepared_routes / latency_limit_ms / pricing)。
    """
    preferred_models: list[str] = field(default_factory=list)
    fallback_models: list[str] = field(default_factory=list)
    api_key_env: str | None = None      # 保留字段以兼容未来 env 取 key 的场景
    api_base: str | None = None
    api_key: str | None = None          # 本项目直接传 key,不强制走 env(简化本期配置)
    timeout_s: float = 60.0
    max_tokens: int | None = None
    temperature: float = 0.7
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class PreparedRoute:
    """单条路由配置(simplified,本期不实现 ForgeUE D plan 的 prepared_routes)。"""
    model: str
    api_key: str | None = None
    api_base: str | None = None
    timeout_s: float | None = None


# ---------------------------------------------------------------------------
# RoutedCall — 内部 helper(本期保留,与 ForgeUE 行为一致)
# ---------------------------------------------------------------------------

@dataclass
class RoutedCall:
    """resolved adapter + model 组合,内部传递用。"""
    adapter: ProviderAdapter
    model: str


# ---------------------------------------------------------------------------
# CapabilityRouter
# ---------------------------------------------------------------------------

class CapabilityRouter:
    """LLM provider 路由器:按 policy 决定 preferred → fallback 顺序。

    Async 主表面:`acompletion` / `astructured`。
    Sync 子集是 `_run_sync` shim,服务现有 sync 调用方。
    """

    def __init__(self) -> None:
        self._adapters: list[ProviderAdapter] = []

    def register(self, adapter: ProviderAdapter) -> None:
        # 注册一个 ProviderAdapter 到路由表末尾。
        self._adapters.append(adapter)

    def clear(self) -> None:
        # 清空已注册的 adapter(测试 / 重置用)。
        self._adapters.clear()

    def _resolve(self, model: str) -> ProviderAdapter:
        # 找到第一个 supports(model) 为 True 的 adapter,否则抛 ProviderError。
        for a in self._adapters:
            if a.supports(model):
                return a
        raise ProviderError(f"no adapter registered for model={model}")

    # ---- candidate iteration ------------------------------------------------

    @staticmethod
    def _routes(policy: ProviderPolicy) -> list[PreparedRoute]:
        """Yield PreparedRoute entries in preferred → fallback order, deduped.

        本期简化版:只支持 preferred_models + fallback_models 字符串路径,
        不实现 ForgeUE D plan 的 `prepared_routes`(那是多 model 路由场景的进阶配置)。
        """
        seen: set[str] = set()
        out: list[PreparedRoute] = []
        for m in list(policy.preferred_models) + list(policy.fallback_models):
            if m in seen:
                continue
            seen.add(m)
            out.append(PreparedRoute(
                model=m,
                api_key=policy.api_key,
                api_base=policy.api_base,
                timeout_s=policy.timeout_s,
            ))
        if not out:
            raise ProviderError("ProviderPolicy has no preferred / fallback models")
        return out

    # ---- Async surface (primary) -------------------------------------------

    async def acompletion(
        self, *, policy: ProviderPolicy, call_template: ProviderCall,
    ) -> tuple[ProviderResult, str]:
        # Iterate preferred → fallback routes; first success wins.
        errors: list[tuple[str, ProviderError]] = []
        for route in self._routes(policy):
            call = _rebind(call_template, route=route, policy=policy)
            adapter = self._resolve(route.model)
            try:
                result = await adapter.acompletion(call)
                return result, route.model
            except ProviderUnsupportedResponse:
                # Deterministic protocol mismatch — falling back to the
                # next route would burn a paid call on a model that
                # didn't actually fail. Surface up to caller's
                # abort_or_fallback handling instead.
                raise
            except ProviderError as exc:
                errors.append((route.model, exc))
                continue
        raise _raise_exhausted(errors, "completion")

    async def astructured(
        self, *, policy: ProviderPolicy, call_template: ProviderCall,
        schema: type[BaseModel],
    ) -> tuple[BaseModel, str, dict[str, int]]:
        """Structured call with explicit token-usage hand-off.

        Returns a 3-tuple `(obj, model, usage)`; BudgetTracker(T07 再接)需要
        最后一个元素来 charge 这次 run。返回 usage 而不是用 thread-local 传,
        避免 `asyncio.gather` 场景下 task 共享同一 event-loop 线程导致的 race。
        """
        errors: list[tuple[str, ProviderError]] = []
        for route in self._routes(policy):
            call = _rebind(call_template, route=route, policy=policy)
            adapter = self._resolve(route.model)
            try:
                obj, usage = await adapter.astructured_with_usage(call, schema)
                return obj, route.model, usage
            except ProviderUnsupportedResponse:
                raise
            except ProviderError as exc:
                errors.append((route.model, exc))
                continue
        raise _raise_exhausted(errors, "structured")

    # ---- Sync shims (back-compat) ------------------------------------------

    def completion(
        self, *, policy: ProviderPolicy, call_template: ProviderCall,
    ) -> tuple[ProviderResult, str]:
        return _run_sync(self.acompletion(
            policy=policy, call_template=call_template,
        ))

    def structured(
        self, *, policy: ProviderPolicy, call_template: ProviderCall,
        schema: type[BaseModel],
    ) -> tuple[BaseModel, str, dict[str, int]]:
        return _run_sync(self.astructured(
            policy=policy, call_template=call_template, schema=schema,
        ))


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _raise_exhausted(
    errors: list[tuple[str, ProviderError]], action: str,
) -> ProviderError:
    """Build (and return) a composite ProviderError that preserves EVERY
    per-route error so callers can `raise _raise_exhausted(...)`.

    保留每个 route 的失败信息,避免只剩 last error 把 root cause 吞掉(例如
    preferred chain 三条全失败时,只看 last 的 message 会丢前面 2 条的原因)。
    """
    if not errors:
        return ProviderError(
            f"exhausted ProviderPolicy without a single {action} call"
        )
    detail = "; ".join(f"{m}: {exc}" for m, exc in errors)
    # 当所有 route 失败原因同类(e.g. 全 schema_validation_fail),保留具体子类型,
    # 让 caller 仍能基于 isinstance 做精细分流。
    types = {type(e) for _, e in errors}
    cls = types.pop() if len(types) == 1 else ProviderError
    composite = cls(
        f"exhausted {len(errors)} route(s) for {action}: {detail}"
    )
    composite.__cause__ = errors[-1][1]
    return composite


def _rebind(
    call: ProviderCall, *, route: PreparedRoute, policy: ProviderPolicy,
) -> ProviderCall:
    """把 route + policy 的字段绑定到 ProviderCall(新对象,不 mutate 原 call)。

    本期简化版字段绑定:
      - model:始终用 route.model
      - temperature / max_tokens:call 优先,policy 回退
      - timeout_s:route → call → policy 优先级
      - api_key / api_base:route 优先,call 回退
    """
    return ProviderCall(
        model=route.model,
        messages=list(call.messages),
        temperature=call.temperature or policy.temperature,
        max_tokens=call.max_tokens or policy.max_tokens,
        timeout_s=route.timeout_s or call.timeout_s or policy.timeout_s,
        seed=call.seed,
        api_key=route.api_key or call.api_key,
        api_base=route.api_base or call.api_base,
        extra=dict(call.extra),
    )
