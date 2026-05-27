"""FakeAdapter 单测桩 smoke 测试。"""

import asyncio

import pytest
from pydantic import BaseModel

from Plugins.AgentBridge.Compiler.providers.fake_adapter import FakeAdapter, FakeModelProgram
from Plugins.AgentBridge.Compiler.providers.base import (
    ProviderCall, ProviderTimeout, SchemaValidationError,
)


class DimSchema(BaseModel):
    dimension_id: str
    score: int


def test_fake_adapter_supports_only_programmed() -> None:
    """未注册 model 应返 False,注册后返 True。"""
    fa = FakeAdapter()
    assert fa.supports("not-programmed") is False
    fa.program("test-model", outputs=[FakeModelProgram(text="x")])
    assert fa.supports("test-model") is True


def test_fake_adapter_sequential_pop() -> None:
    """多个 outputs 按 FIFO 顺序弹出。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[
        FakeModelProgram(text="first"),
        FakeModelProgram(text="second"),
    ])
    call = ProviderCall(model="m", messages=[])
    r1 = asyncio.run(fa.acompletion(call))
    r2 = asyncio.run(fa.acompletion(call))
    assert r1.text == "first"
    assert r2.text == "second"


def test_fake_adapter_raise_error() -> None:
    """raise_error 字段触发指定 exception。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(raise_error=ProviderTimeout("simulated"))])
    call = ProviderCall(model="m", messages=[])
    with pytest.raises(ProviderTimeout):
        asyncio.run(fa.acompletion(call))


def test_fake_adapter_structured() -> None:
    """schema_value 通过 Pydantic 校验,返回 BaseModel 实例。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1", "score": 5},
    )])
    call = ProviderCall(model="m", messages=[])
    obj = asyncio.run(fa.astructured(call, DimSchema))
    assert isinstance(obj, DimSchema)
    assert obj.dimension_id == "d1"
    assert obj.score == 5


def test_fake_adapter_structured_invalid_raises() -> None:
    """schema_value 不满足 schema 时 raise SchemaValidationError。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1"},  # 缺 score
    )])
    call = ProviderCall(model="m", messages=[])
    with pytest.raises(SchemaValidationError):
        asyncio.run(fa.astructured(call, DimSchema))


def test_fake_adapter_astructured_with_usage_returns_tuple() -> None:
    """astructured_with_usage 返回 (obj, usage) 二元组。"""
    fa = FakeAdapter()
    fa.program("m", outputs=[FakeModelProgram(
        schema_value={"dimension_id": "d1", "score": 5},
        usage={"prompt": 100, "completion": 50, "total": 150},
    )])
    call = ProviderCall(model="m", messages=[])
    obj, usage = asyncio.run(fa.astructured_with_usage(call, DimSchema))
    assert isinstance(obj, DimSchema)
    assert usage == {"prompt": 100, "completion": 50, "total": 150}
