"""
测试证据目录与 manifest 管理。

说明：
  - 默认证据根目录为 ProjectState/Evidence/
  - 每次测试运行对应一个 run_id 子目录
  - manifest 保存前会执行 schema 校验
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator, FormatChecker

from bridge.project_config import get_project_root, get_schemas_dir
from evidence.run_id import validate_run_id


EVIDENCE_ROOT = get_project_root() / "ProjectState" / "Evidence"
EVIDENCE_SCHEMA_PATH = get_schemas_dir() / "evidence_manifest.schema.json"
MANIFEST_FILE_NAME = "evidence_manifest.json"

# 任务要求固定 4 个标准子目录。
EVIDENCE_SUBDIRS = ("screenshots", "logs", "reports", "state")
EVIDENCE_TYPE_TO_SUBDIR = {
    "screenshot": "screenshots",
    "log": "logs",
    "report": "reports",
    "state_summary": "state",
    # assertion_result 没有独立目录，统一并入 reports。
    "assertion_result": "reports",
}
VALID_TEST_TYPES = {
    "automation_test",
    "functional_test",
    "smoke_test",
    "gauntlet_session",
    "manual_check",
}


def _utc_now_iso() -> str:
    """返回带时区的 ISO 8601 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def _get_evidence_root() -> Path:
    """兼容测试时把 EVIDENCE_ROOT 临时改成字符串路径。"""
    return Path(EVIDENCE_ROOT)


def _load_manifest_schema() -> dict[str, Any]:
    """加载 evidence manifest schema。"""
    with EVIDENCE_SCHEMA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _validate_manifest(manifest: dict[str, Any]) -> None:
    """在保存前执行 schema 校验，不通过时抛出 ValueError。"""
    validator = Draft7Validator(
        _load_manifest_schema(),
        format_checker=FormatChecker(),
    )
    errors = sorted(validator.iter_errors(manifest), key=lambda item: list(item.path))

    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        details.append(f"{location}: {error.message}")

    # 这里额外补充相对路径约束，避免把绝对路径写入 manifest。
    for index, item in enumerate(manifest.get("evidence_items", [])):
        raw_path = str(item.get("path", "")).strip()
        normalized = Path(raw_path)
        if raw_path.startswith(("/", "\\")) or normalized.is_absolute():
            details.append(f"evidence_items.{index}.path: 必须是相对于 run_id 目录的路径")
        elif ".." in normalized.parts:
            details.append(f"evidence_items.{index}.path: 不能包含上级目录跳转 '..'")

    if not details:
        return

    raise ValueError("evidence_manifest schema 校验失败: " + " | ".join(details))


def _validate_test_type(test_type: str) -> None:
    """校验 test_type 是否在允许列表内。"""
    if test_type not in VALID_TEST_TYPES:
        raise ValueError(f"非法 test_type: {test_type}")


def _validate_evidence_type(evidence_type: str) -> None:
    """校验证据类型是否受支持。"""
    if evidence_type not in EVIDENCE_TYPE_TO_SUBDIR:
        raise ValueError(f"非法 evidence_type: {evidence_type}")


def _get_run_dir(run_id: str) -> Path:
    """返回 run_id 对应目录。"""
    if not validate_run_id(run_id):
        raise ValueError(f"非法 run_id: {run_id}")
    return _get_evidence_root() / run_id


def _make_unique_target_path(target_dir: Path, source_name: str) -> Path:
    """当同名文件已存在时，自动追加序号避免覆盖。"""
    candidate = target_dir / source_name
    if not candidate.exists():
        return candidate

    stem = Path(source_name).stem
    suffix = Path(source_name).suffix
    index = 1
    while True:
        candidate = target_dir / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
        index += 1


def create_evidence_dir(run_id: str) -> str:
    """创建标准化证据目录，并返回 run_id 目录路径。"""
    run_dir = _get_run_dir(run_id)
    run_dir.mkdir(parents=True, exist_ok=True)

    for subdir in EVIDENCE_SUBDIRS:
        (run_dir / subdir).mkdir(parents=True, exist_ok=True)

    return str(run_dir)


def register_evidence(run_id: str, evidence_type: str, source_path: str, description: str) -> str:
    """
    复制证据文件到标准化目录，并返回相对路径。

    说明：
      - description 由调用方保留，用于后续 add_evidence_item()
      - 当前函数仅负责标准化落盘，不直接修改 manifest
    """
    _validate_evidence_type(evidence_type)

    source = Path(source_path)
    if not source.exists():
        raise FileNotFoundError(f"证据文件不存在: {source}")
    if source.is_dir():
        raise ValueError(f"register_evidence 仅支持文件复制，不支持目录: {source}")
    if not description.strip():
        raise ValueError("description 不能为空")

    run_dir = Path(create_evidence_dir(run_id))
    subdir = EVIDENCE_TYPE_TO_SUBDIR[evidence_type]
    target_dir = run_dir / subdir
    target_path = _make_unique_target_path(target_dir, source.name)

    shutil.copy2(source, target_path)
    return target_path.relative_to(run_dir).as_posix()


def create_manifest(run_id: str, test_type: str, test_scope: str) -> dict[str, Any]:
    """创建一个空的 manifest。"""
    if not validate_run_id(run_id):
        raise ValueError(f"非法 run_id: {run_id}")
    _validate_test_type(test_type)
    if not test_scope.strip():
        raise ValueError("test_scope 不能为空")

    return {
        "run_id": run_id,
        "created_at": _utc_now_iso(),
        "test_type": test_type,
        "test_scope": test_scope,
        "evidence_items": [],
        "summary": {
            "total_checks": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        },
        "status": "pending",
    }


def add_evidence_item(
    manifest: dict[str, Any],
    item_type: str,
    path: str,
    description: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """向 manifest 追加一条证据项。"""
    _validate_evidence_type(item_type)
    if not path.strip():
        raise ValueError("path 不能为空")
    if not description.strip():
        raise ValueError("description 不能为空")

    item = {
        "type": item_type,
        "path": path.replace("\\", "/"),
        "description": description,
        "timestamp": timestamp or _utc_now_iso(),
    }
    manifest.setdefault("evidence_items", []).append(item)
    return manifest


def save_manifest(manifest: dict[str, Any], run_id: str) -> str:
    """校验并保存 manifest 到标准目录。"""
    if manifest.get("run_id") != run_id:
        raise ValueError("manifest.run_id 与 save_manifest(run_id) 不一致")

    run_dir = Path(create_evidence_dir(run_id))
    manifest_path = run_dir / MANIFEST_FILE_NAME

    _validate_manifest(manifest)

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, ensure_ascii=False, indent=2)
    return str(manifest_path)


def load_manifest(run_id: str) -> dict[str, Any]:
    """加载并校验指定 run_id 的 manifest。"""
    manifest_path = _get_run_dir(run_id) / MANIFEST_FILE_NAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest 不存在: {manifest_path}")

    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    _validate_manifest(manifest)
    return manifest


def list_runs(date_filter: str | None = None) -> list[str]:
    """列出当前证据根目录下的全部 run_id。"""
    root = _get_evidence_root()
    if not root.exists():
        return []

    result = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if not validate_run_id(child.name):
            continue
        if date_filter and not child.name.startswith(f"{date_filter}_"):
            continue
        result.append(child.name)

    return sorted(result)
