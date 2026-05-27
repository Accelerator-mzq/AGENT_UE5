"""Deterministic fake adapter for tests + offline CI.

从 ForgeUE_codex 移植适配,服务 T14/T15 单元 + 集成测试(让 candidates_batch_orchestrator
等模块测试不打真 LLM)。

Usage:
    fa = FakeAdapter()
    fa.program("anthropic/claude-3-haiku", outputs=[
        FakeModelProgram(text='{"name": "Bob"}'),
        FakeModelProgram(schema_value={"name": "Bob", "level": 3}),
    ])
    # 首次 acompletion / astructured 弹 deque 第 1 个 program,后续按顺序弹
"""
from __future__ import annotations

import json
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Callable

from pydantic import BaseModel, ValidationError

from .base import (
    ProviderAdapter,
    ProviderCall,
    ProviderError,
    ProviderResult,
    SchemaValidationError,
)


SchemaBuilder = Callable[[ProviderCall, "type[BaseModel]"], Any]


@dataclass
class FakeModelProgram:
    """One scripted response for one call.

    Provide either a static ``schema_value`` / ``text`` or a dynamic
    ``schema_builder`` callable that inspects the incoming ``ProviderCall`` and
    returns a raw dict (e.g. to echo candidate ids extracted from the prompt).
    """

    text: str | None = None
    schema_value: dict | None = None               # raw dict — validated against requested schema
    schema_builder: SchemaBuilder | None = None    # dynamic alternative to schema_value
    raise_error: BaseException | None = None
    usage: dict[str, int] = field(default_factory=lambda: {"prompt": 10, "completion": 20, "total": 30})


class FakeAdapter(ProviderAdapter):
    name = "fake"

    def __init__(self) -> None:
        # 每个 model 一条 FIFO 队列,acompletion / astructured 各弹一格
        self._programs: dict[str, deque[FakeModelProgram]] = defaultdict(deque)
        # 调用历史(用于测试断言 prompts / messages 是否传对)
        self._calls: list[tuple[str, ProviderCall]] = []
        self._supported: set[str] = set()

    # ---- programming ----

    def program(self, model: str, *, outputs: list[FakeModelProgram]) -> None:
        # 注册脚本响应,后续 supports(model) 返 True
        self._programs[model].extend(outputs)
        self._supported.add(model)

    def calls_for(self, model: str) -> list[ProviderCall]:
        # 测试断言用:取出某 model 收到的全部 ProviderCall
        return [c for m, c in self._calls if m == model]

    # ---- ProviderAdapter surface ----

    def supports(self, model: str) -> bool:
        return model in self._supported

    def _pop(self, model: str) -> FakeModelProgram:
        queue = self._programs.get(model)
        if not queue:
            raise ProviderError(f"FakeAdapter has no programmed response for model={model}")
        return queue.popleft()

    async def acompletion(self, call: ProviderCall) -> ProviderResult:
        self._calls.append((call.model, call))
        p = self._pop(call.model)
        if p.raise_error is not None:
            raise p.raise_error
        text = p.text
        if text is None and p.schema_value is not None:
            text = json.dumps(p.schema_value, ensure_ascii=False)
        if text is None:
            text = ""
        return ProviderResult(text=text, model=call.model, usage=dict(p.usage))

    async def astructured(self, call: ProviderCall, schema: type[BaseModel]) -> BaseModel:
        self._calls.append((call.model, call))
        p = self._pop(call.model)
        if p.raise_error is not None:
            raise p.raise_error
        value: Any
        if p.schema_builder is not None:
            built = p.schema_builder(call, schema)
            value = built.model_dump(mode="json") if isinstance(built, BaseModel) else built
        elif p.schema_value is not None:
            value = p.schema_value
        elif p.text is not None:
            try:
                value = json.loads(p.text)
            except json.JSONDecodeError as exc:
                raise SchemaValidationError(f"fake adapter text not JSON: {exc}", raw=p.text) from exc
        else:
            raise SchemaValidationError("fake program has no schema_value, text, or schema_builder")
        try:
            return schema.model_validate(value)
        except ValidationError as exc:
            raise SchemaValidationError(str(exc), raw=value) from exc

    async def astructured_with_usage(
        self, call: ProviderCall, schema: type[BaseModel],
    ) -> tuple[BaseModel, dict[str, int]]:
        """Delegates to `self.astructured` so subclasses that override only
        `astructured` (e.g. a latency-injecting test fixture) still get their
        override honoured. Usage is peeked from the next-in-line program
        before `astructured` pops it, so the two stay in sync."""
        queue = self._programs.get(call.model)
        usage: dict[str, int] = dict(queue[0].usage) if queue else {}
        obj = await self.astructured(call, schema)
        return obj, usage
