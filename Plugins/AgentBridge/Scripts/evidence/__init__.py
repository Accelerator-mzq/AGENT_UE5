"""
测试证据标准化模块。

提供 run_id 生成/解析，以及标准化证据目录与 manifest 管理能力。
"""

from .run_id import generate_run_id, parse_run_id, validate_run_id
from .evidence_manager import (
    EVIDENCE_ROOT,
    add_evidence_item,
    create_evidence_dir,
    create_manifest,
    list_runs,
    load_manifest,
    register_evidence,
    save_manifest,
)

__all__ = [
    "EVIDENCE_ROOT",
    "add_evidence_item",
    "create_evidence_dir",
    "create_manifest",
    "generate_run_id",
    "list_runs",
    "load_manifest",
    "parse_run_id",
    "register_evidence",
    "save_manifest",
    "validate_run_id",
]
