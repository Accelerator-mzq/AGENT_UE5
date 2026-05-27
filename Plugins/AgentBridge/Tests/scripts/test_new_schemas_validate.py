"""新 Schema(provider_call / retry_policy)语法 + 实例校验。"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, validate

SCHEMA_DIR = Path("Plugins/AgentBridge/Schemas")


def test_provider_call_schema_valid_meta() -> None:
    s = json.loads((SCHEMA_DIR / "provider_call.schema.json").read_text(encoding="utf-8"))
    Draft7Validator.check_schema(s)


def test_retry_policy_schema_valid_meta() -> None:
    s = json.loads((SCHEMA_DIR / "retry_policy.schema.json").read_text(encoding="utf-8"))
    Draft7Validator.check_schema(s)


def test_provider_call_minimal_instance() -> None:
    s = json.loads((SCHEMA_DIR / "provider_call.schema.json").read_text(encoding="utf-8"))
    validate(
        instance={"model": "anthropic/claude-3-haiku", "messages": [{"role": "user", "content": "hi"}]},
        schema=s,
    )


def test_provider_call_extra_field_rejected() -> None:
    s = json.loads((SCHEMA_DIR / "provider_call.schema.json").read_text(encoding="utf-8"))
    with pytest.raises(Exception):
        validate(
            instance={"model": "m", "messages": [], "unknown_field": "x"},
            schema=s,
        )


def test_retry_policy_default_compatible() -> None:
    s = json.loads((SCHEMA_DIR / "retry_policy.schema.json").read_text(encoding="utf-8"))
    validate(
        instance={
            "max_attempts": 3,
            "backoff_mode": "exponential",
            "backoff_base_s": 2.0,
            "jitter_ms": [100, 500],
            "retry_on": ["timeout", "transient_network", "schema_fail"],
            "no_retry_on": ["unsupported_response", "4xx_non_429"],
        },
        schema=s,
    )
