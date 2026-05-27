"""Provider adapter contract — async-first(主表面)+ sync shim(向后兼容)。

从 ForgeUE_codex 移植适配:把 LLM 提供商抽象成统一的 ProviderAdapter,
让 Stage 4 Candidates batch executor 不绑死具体 SDK。

Async 主表面:`acompletion` / `astructured` / `astructured_with_usage`。
Sync 子集是 `asyncio.run` shim,服务现有 sync 调用方(LLMProvider.generate 等)。
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Awaitable, TypeVar

from pydantic import BaseModel


class ProviderError(RuntimeError):
    """Generic provider failure (transport, auth, rate-limit)."""


class ProviderTimeout(ProviderError):
    """Request exceeded latency budget."""


class ProviderUnsupportedResponse(ProviderError):
    """Provider returned a deterministically bad/empty response shape that
    this adapter cannot consume — e.g. `/submit` with no id, `/query`
    success with no image URLs, choices array without content.

    Distinct from generic `ProviderError` so FailureModeMap routes this
    to `unsupported_response` → `Decision.abort_or_fallback` (honours
    `on_fallback` when configured, else terminates) rather than
    `provider_error` → `fallback_model` → same-step retry. The latter
    would re-bill a paid provider (Hunyuan/Qwen/Tripo3D) for the same
    deterministic bad shape. Mirrors `MeshWorkerUnsupportedResponse`
    on the worker side — 2026-04 共性平移 extends the pattern from
    mesh-only to all provider surfaces."""


class SchemaValidationError(ProviderError):
    """Provider returned content that doesn't match the requested schema."""

    def __init__(self, message: str, *, raw: Any = None) -> None:
        super().__init__(message)
        self.raw = raw


@dataclass
class ProviderCall:
    model: str
    messages: list[dict[str, Any]]
    temperature: float = 0.0
    max_tokens: int | None = None
    timeout_s: float | None = None
    seed: int | None = None
    api_key: str | None = None
    api_base: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResult:
    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)


T = TypeVar("T")


def _run_sync(coro: Awaitable[T]) -> T:
    """Run an async coroutine from a sync context.

    Uses `asyncio.run` when no loop is running. If called from within an
    already-running event loop we raise a clear error — callers should use
    the async method directly in that case, not the sync shim.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # Close the coroutine so we don't leak an "un-awaited coroutine" warning.
    if hasattr(coro, "close"):
        coro.close()
    raise RuntimeError(
        "Sync ProviderAdapter shim called from inside a running event loop. "
        "Use the async method (acompletion/astructured/astructured_with_usage) directly."
    )


def _is_overridden(cls: type, method_name: str) -> bool:
    """Detect whether subclass overrode a given method from ProviderAdapter.

    Used to protect against infinite recursion between sync/async shims:
    an adapter must override at least one side (completion OR acompletion),
    else both defaults would endlessly delegate to each other.
    """
    base_impl = getattr(ProviderAdapter, method_name, None)
    sub_impl = getattr(cls, method_name, None)
    return base_impl is not None and sub_impl is not base_impl


class ProviderAdapter(ABC):
    """Implemented by e.g. LiteLLMAdapter, FakeAdapter.

    Dual-surface contract:
    - Async methods (`acompletion` / `astructured`) — the primary surface
      for new code.
    - Sync methods (`completion` / `structured`) — back-compat surface for
      existing callers.

    The two are mutually-delegating: a concrete adapter overrides ONE side
    and the other is provided automatically.
    - Override sync only  → async default wraps sync in `asyncio.to_thread`
    - Override async only → sync default calls `asyncio.run(async)`
    - Override both       → both direct
    - Override neither    → infinite recursion (developer error; we detect
      and raise a clear error below).
    """

    name: str

    @abstractmethod
    def supports(self, model: str) -> bool:
        """Whether this adapter can handle the given model id. Pure-function
        string matching — no I/O."""

    # ---- Async surface (primary for new code) ---------------------------

    async def acompletion(self, call: ProviderCall) -> ProviderResult:
        if not _is_overridden(type(self), "completion"):
            raise NotImplementedError(
                f"{type(self).__name__} must override acompletion or completion"
            )
        return await asyncio.to_thread(self.completion, call)

    async def astructured(
        self,
        call: ProviderCall,
        schema: type[BaseModel],
    ) -> BaseModel:
        if not _is_overridden(type(self), "structured"):
            raise NotImplementedError(
                f"{type(self).__name__} must override astructured or structured"
            )
        return await asyncio.to_thread(self.structured, call, schema)

    async def astructured_with_usage(
        self,
        call: ProviderCall,
        schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, int]]:
        """Same contract as `astructured` but also returns token-usage.

        BudgetTracker needs per-call usage to charge the run. Adapters that
        can report it (LiteLLM via instructor's `create_with_completion`,
        Fake via its `FakeModelProgram.usage`) override this; the default
        falls back to `astructured` and reports an empty usage dict so
        back-compat callers (plus adapters without usage telemetry) keep
        working unchanged.

        This is a separate method from `astructured` so existing test
        fixtures / subclasses that only override the plain `astructured`
        continue to work — the default implementation here picks up their
        overridden `astructured` via `self.astructured(...)`.
        """
        obj = await self.astructured(call, schema)
        return obj, {}

    # ---- Sync surface (back-compat) -------------------------------------

    def completion(self, call: ProviderCall) -> ProviderResult:
        if not _is_overridden(type(self), "acompletion"):
            raise NotImplementedError(
                f"{type(self).__name__} must override acompletion or completion"
            )
        return _run_sync(self.acompletion(call))

    def structured(
        self,
        call: ProviderCall,
        schema: type[BaseModel],
    ) -> BaseModel:
        if not _is_overridden(type(self), "astructured"):
            raise NotImplementedError(
                f"{type(self).__name__} must override astructured or structured"
            )
        return _run_sync(self.astructured(call, schema))
