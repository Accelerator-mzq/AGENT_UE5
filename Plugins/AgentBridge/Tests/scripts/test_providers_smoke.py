# -*- coding: utf-8 -*-
"""providers 子树 smoke 测试 — 模块可 import,类层次正确。"""

from Plugins.AgentBridge.Compiler.providers import (
    ProviderAdapter,
    ProviderCall,
    ProviderResult,
    ProviderError,
    ProviderTimeout,
    ProviderUnsupportedResponse,
    SchemaValidationError,
)
from Plugins.AgentBridge.Compiler.providers._retry import (
    with_transient_retry,
    is_transient_network_message,
    is_rate_limited,
)


def test_exception_hierarchy() -> None:
    """4 类 typed exception 应继承自 ProviderError。"""
    assert issubclass(ProviderTimeout, ProviderError)
    assert issubclass(ProviderUnsupportedResponse, ProviderError)
    assert issubclass(SchemaValidationError, ProviderError)


def test_is_rate_limited_429() -> None:
    assert is_rate_limited(Exception("HTTP 429 Too Many Requests")) is True


def test_is_rate_limited_529_overload() -> None:
    assert is_rate_limited(Exception("529 overloaded_error")) is True


def test_is_rate_limited_non_rate_limit() -> None:
    assert is_rate_limited(Exception("Connection reset by peer")) is False


def test_is_transient_network_message_timeout() -> None:
    assert is_transient_network_message("Request timed out") is True


def test_provider_call_dataclass_defaults() -> None:
    pc = ProviderCall(model="x", messages=[])
    assert pc.temperature == 0.0
    assert pc.timeout_s is None
    assert pc.extra == {}
