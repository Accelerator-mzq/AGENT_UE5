"""design_space_report 扩字段后向后兼容校验。

T09(Phase 12 LLM Internal Reopen)新增 per_dimension_batch_metadata 字段后,
必须保证:
  1. 现有(Phase 11)example 不含新字段时仍合法 — 向后兼容
  2. 合法填充新字段(LLM 生成产物形态)能通过校验
  3. 非法值(status 越界、error_class 越界等)被 schema 拒绝
"""

import json
from pathlib import Path

import pytest
from jsonschema import validate, ValidationError

# 项目相对路径(测试运行时 cwd = 项目根目录)
SCHEMA_PATH = Path("Plugins/AgentBridge/Schemas/design_space_report.schema.json")
EXAMPLE_PATH = Path(
    "Plugins/AgentBridge/Schemas/examples/phase11_design_space_report.example.json"
)


def _load_schema() -> dict:
    """读取扩展后的 design_space_report schema。"""
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_example() -> dict:
    """读取 Phase 11 现有合法 example,作为最小合法 instance 基底。"""
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def test_existing_report_without_new_field_still_valid() -> None:
    """老 report 不含 per_dimension_batch_metadata 仍合法(向后兼容)。"""
    schema = _load_schema()
    instance = _load_example()
    # 现有 example 不含新字段;扩 schema 后必须依然合法
    assert "per_dimension_batch_metadata" not in instance, (
        "前提失效:example 已经被改成含新字段了,无法测向后兼容"
    )
    try:
        validate(instance=instance, schema=schema)
    except ValidationError as exc:
        pytest.fail(f"现有 example 实例在扩 schema 后失败: {exc.message}")


def test_new_per_dim_metadata_valid() -> None:
    """加 per_dimension_batch_metadata 填合法值应通过。"""
    schema = _load_schema()
    instance = _load_example()
    # 构造典型的 LLM 单维度成功批次产物
    instance["per_dimension_batch_metadata"] = [
        {
            "dimension_id": "d1",
            "model": "anthropic/claude-3-haiku-20240307",
            "attempt_count": 1,
            "duration_ms": 28000,
            "usage": {"prompt": 1500, "completion": 800, "total": 2300},
            "status": "success",
            "error_class": None,
            "raw_response_id": "msg_abc123",
        }
    ]
    validate(instance=instance, schema=schema)


def test_new_per_dim_metadata_invalid_status() -> None:
    """status 非 enum 值应被拒。"""
    schema = _load_schema()
    instance = _load_example()
    instance["per_dimension_batch_metadata"] = [
        {
            "dimension_id": "d1",
            "model": "m",
            "attempt_count": 1,
            "status": "INVALID_STATUS",
        }
    ]
    with pytest.raises(ValidationError):
        validate(instance=instance, schema=schema)


def test_new_per_dim_metadata_rate_limit_error_class_valid() -> None:
    """error_class=rate_limit 与 transient_network 必须合法。

    跨 task 修复:T10 实现的 LLMBatchExecutor._classify 会写出 "rate_limit"
    和 "transient_network",但 T09 schema 漏了它们(且原本拼成 rate_limited)。
    本 case 守护 T11/T12 落盘 design_space_report 时 schema 校验不爆。
    """
    schema = _load_schema()
    instance = _load_example()
    instance["per_dimension_batch_metadata"] = [
        {
            "dimension_id": "d1",
            "model": "m",
            "attempt_count": 2,
            "status": "failed",
            "error_class": "rate_limit",
        },
        {
            "dimension_id": "d2",
            "model": "m",
            "attempt_count": 3,
            "status": "failed",
            "error_class": "transient_network",
        },
    ]
    validate(instance=instance, schema=schema)
