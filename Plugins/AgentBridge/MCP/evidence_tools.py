"""
MCP 后端证据裁决工具适配层。

职责：
  - 读取标准化测试证据目录
  - 基于 manifest 做轻量 pass/fail/escalate 初判
  - 输出结构化验收摘要
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft7Validator

PLUGIN_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_DIR / "Scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from evidence import evidence_manager
from evidence.run_id import validate_run_id
from bridge.project_config import get_project_root, get_schemas_dir


RUN_WORKSPACE_ID_PATTERN = re.compile(r"^run-\d{8}-\d{6}-[0-9a-fA-F]{4,12}$")
BATCH_ID_PATTERN = re.compile(r"^batch-\d{8}-\d{3}$")
RUN_WORKSPACE_ROOT = get_project_root() / "ProjectState" / "runs"
BATCHES_ROOT = get_project_root() / "ProjectState" / "batches"
ACTIVE_BATCH_POINTER_PATH = BATCHES_ROOT / "active_batch.json"
CURRENT_PROMOTED_POINTER_PATH = BATCHES_ROOT / "current_promoted_batch.json"
RUN_COMPARISON_SCHEMA_PATH = get_schemas_dir() / "run_comparison.schema.json"
BATCH_MANIFEST_SCHEMA_PATH = get_schemas_dir() / "batch_manifest.schema.json"
PROMOTED_ARTIFACTS = (
    "metadata.json",
    "root_skill_contract.json",
    "clarification_gate_report.json",
    "skill_graph.json",
    "design_space_report.json",
    "realization_candidates.json",
    "converged_realization_pack.json",
    "skill_fragments",
    "cross_review_report.json",
    "build_ir.json",
    "naming_resolution_log.json",
    "reviewed_handoff_v3.json",
)
MAX_STAGE_BY_VERSION = {
    "1.0": 5,
    "2.0": 7,
}
DEFAULT_CLEANUP_POLICY = {
    "formal_runs": {
        "policy": "manual_cleanup_only",
        "retain": "forever",
    },
    "fast_mode_runs": {
        "policy": "keep_latest_n",
        "default_keep_count": 5,
    },
    "promoted_batches": {
        "policy": "retain_forever",
    },
    "failed_runs": {
        "policy": "keep_execution_log",
        "artifact_cleanup": "optional",
    },
}


def _make_response(
    status: str,
    summary: str,
    data: dict | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict:
    """构造与 Bridge 工具一致的统一返回格式。"""
    return {
        "status": status,
        "summary": summary,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _get_evidence_root() -> Path:
    """兼容 evidence_manager 中可能被临时改写的根目录变量。"""
    return Path(evidence_manager.EVIDENCE_ROOT)


def _get_run_dir(run_id: str) -> Path:
    """返回 run_id 对应的证据目录。"""
    if not validate_run_id(run_id):
        raise ValueError(f"非法 run_id: {run_id}")
    return _get_evidence_root() / run_id


def _missing_path_response(path: Path, label: str) -> dict:
    """统一处理路径不存在。"""
    return _make_response(
        "failed",
        f"{label}不存在",
        errors=[f"FILE_NOT_FOUND: {path.as_posix()}"],
    )


def _list_files(run_dir: Path, subdir: str) -> list[Path]:
    """列出某个证据子目录下的全部文件。"""
    target_dir = run_dir / subdir
    if not target_dir.exists():
        return []
    return sorted(path for path in target_dir.iterdir() if path.is_file())


def _to_relative_paths(run_dir: Path, files: list[Path]) -> list[str]:
    """将绝对路径转换为相对 run_id 目录的路径。"""
    return [path.relative_to(run_dir).as_posix() for path in files]


def _read_text_file(path: Path) -> str:
    """以宽松方式读取文本内容，避免日志中的异常编码中断流程。"""
    return path.read_text(encoding="utf-8", errors="ignore")


def _utc_now_iso() -> str:
    """返回带时区的 ISO 时间。"""
    return datetime.now(timezone.utc).isoformat()


def _path_to_project_relative(path: Path) -> str:
    """将路径转换为相对项目根目录的稳定路径。"""
    try:
        return path.resolve().relative_to(get_project_root()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _load_json_file(path: Path) -> Any:
    """读取 JSON 文件。"""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json_file(path: Path, payload: Any) -> Path:
    """写入 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return path


def _validate_payload_with_schema(payload: dict[str, Any], schema_path: Path, label: str) -> None:
    """使用本地 schema 校验输出结构。"""
    schema = _load_json_file(schema_path)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    if not errors:
        return

    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        details.append(f"{location}: {error.message}")
    raise ValueError(f"{label} schema 校验失败: " + " | ".join(details))


def _validate_workspace_run_id(run_id: str) -> None:
    """校验 Phase 11 Run Workspace 的 run_id。"""
    if not RUN_WORKSPACE_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"非法 run_id: {run_id}")


def _get_workspace_run_dir(run_id: str) -> Path:
    """返回 Phase 11 run workspace 目录。"""
    _validate_workspace_run_id(run_id)
    return RUN_WORKSPACE_ROOT / run_id


def _normalize_completed_stages(stages: Any) -> list[Any]:
    """对 metadata/session 中的 completed stages 做轻量归一化。"""
    if not isinstance(stages, list):
        return []

    normalized = []
    for item in stages:
        if isinstance(item, int):
            normalized.append(item)
            continue
        if isinstance(item, str):
            text = item.strip()
            if text.isdigit():
                normalized.append(int(text))
            else:
                normalized.append(text)
    return normalized


def _derive_completed_stages_from_session(session: dict[str, Any]) -> list[int]:
    """在 metadata 缺失时，从 session.stage_outputs 反推出已完成阶段。"""
    stage_outputs = session.get("stage_outputs", {})
    if not isinstance(stage_outputs, dict):
        return []

    completed = []
    for stage_key, output_path in stage_outputs.items():
        match = re.match(r"^stage_(\d+)$", str(stage_key))
        if not match:
            continue
        if output_path and Path(output_path).exists():
            completed.append(int(match.group(1)))
    return sorted(set(completed))


def _load_optional_json(path: Path) -> Any | None:
    """读取可选 JSON 文件，不存在时返回 None。"""
    if not path.exists():
        return None
    return _load_json_file(path)


def _load_run_workspace_snapshot(run_id: str) -> dict[str, Any]:
    """加载 run workspace 快照，统一 compare/promote 的输入口径。"""
    run_dir = _get_workspace_run_dir(run_id)
    if not run_dir.exists():
        raise FileNotFoundError(f"run workspace 不存在: {run_dir}")

    metadata = _load_optional_json(run_dir / "metadata.json") or {}
    session = _load_optional_json(run_dir / "session.json") or {}
    if not metadata and not session:
        raise FileNotFoundError(f"run workspace 缺少 metadata.json / session.json: {run_dir}")

    session_version = metadata.get("session_version") or session.get("session_version") or "1.0"
    pipeline_stages_completed = _normalize_completed_stages(
        metadata.get("pipeline_stages_completed")
    )
    if not pipeline_stages_completed:
        pipeline_stages_completed = _derive_completed_stages_from_session(session)

    cross_review = _load_optional_json(run_dir / "cross_review_report.json") or {}
    reviewed_handoff = _load_optional_json(run_dir / "reviewed_handoff_v3.json") or {}

    provisional_items = metadata.get("provisional_items")
    if not isinstance(provisional_items, list):
        provisional_items = reviewed_handoff.get("provisional_items", [])
        if not isinstance(provisional_items, list):
            provisional_items = []

    constraint_violations = metadata.get("constraint_violations")
    if not isinstance(constraint_violations, int):
        constraint_violations = (
            cross_review.get("constraint_preservation_summary", {}).get("violations", 0)
        )

    snapshot = {
        "run_id": run_id,
        "run_dir": run_dir,
        "metadata": metadata,
        "session": session,
        "session_version": session_version,
        "status": metadata.get("status") or session.get("status") or "pending",
        "fast_mode": bool(metadata.get("fast_mode", session.get("fast_mode", False))),
        "generator_provider": metadata.get("generator_provider") or session.get("generator_provider"),
        "pipeline_stages_completed": pipeline_stages_completed,
        "constraint_violations": int(constraint_violations or 0),
        "provisional_items": provisional_items,
        "metadata_promotable": metadata.get("promotable"),
        "output_dir": metadata.get("output_dir") or session.get("output_dir") or str(run_dir),
    }
    return snapshot


def _expected_stage_count(session_version: str) -> int:
    """返回当前版本预期的最大阶段数。"""
    return MAX_STAGE_BY_VERSION.get(session_version or "2.0", 7)


def _is_stage_completion_full(snapshot: dict[str, Any]) -> bool:
    """判断 run 是否完成了全部阶段。"""
    completed = snapshot.get("pipeline_stages_completed", [])
    expected_count = _expected_stage_count(snapshot.get("session_version", "2.0"))
    if not completed:
        return False
    if all(isinstance(item, int) for item in completed):
        return sorted(set(completed)) == list(range(1, expected_count + 1))
    return len(set(completed)) >= expected_count


def _evaluate_promotable(snapshot: dict[str, Any]) -> dict[str, Any]:
    """统一 promotable 判定。"""
    reasons = []

    if snapshot.get("fast_mode"):
        reasons.append("fast_mode run 不可 promote")
    if snapshot.get("status") != "completed":
        reasons.append(f"run 状态不是 completed，而是 {snapshot.get('status')}")
    if snapshot.get("constraint_violations", 0) > 0:
        reasons.append(
            f"constraint_violations = {snapshot.get('constraint_violations', 0)}"
        )
    if not _is_stage_completion_full(snapshot):
        reasons.append("pipeline_stages_completed 不完整")
    if snapshot.get("generator_provider") == "heuristic_fallback":
        reasons.append("heuristic_fallback 产物不可 promote")
    if snapshot.get("metadata_promotable") is False:
        reasons.append("metadata.promotable = false")

    return {
        "promotable": len(reasons) == 0,
        "reasons": reasons,
        "checks": {
            "fast_mode": bool(snapshot.get("fast_mode", False)),
            "status": snapshot.get("status"),
            "constraint_violations": int(snapshot.get("constraint_violations", 0)),
            "pipeline_complete": _is_stage_completion_full(snapshot),
            "generator_provider": snapshot.get("generator_provider"),
            "metadata_promotable": snapshot.get("metadata_promotable"),
        },
    }


def _canonical_json(value: Any) -> str:
    """生成稳定 JSON 文本，用于比较。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_digest(value: Any) -> str:
    """生成稳定摘要，避免直接比较大对象。"""
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _extract_constraint_map(run_dir: Path) -> dict[str, Any]:
    """提取 constraint_fields 中的核心值。"""
    payload = _load_optional_json(run_dir / "root_skill_contract.json") or {}
    fields = payload.get("constraint_fields", {})
    result = {}
    if not isinstance(fields, dict):
        return result

    for key, value in fields.items():
        if isinstance(value, dict) and "value" in value:
            result[key] = value.get("value")
        else:
            result[key] = value
    return result


def _extract_realization_map(run_dir: Path) -> dict[str, Any]:
    """提取 converged choices。"""
    payload = _load_optional_json(run_dir / "converged_realization_pack.json") or {}
    items = payload.get("converged_choices", [])
    result = {}
    if not isinstance(items, list):
        return result

    for item in items:
        if not isinstance(item, dict):
            continue
        dimension_id = item.get("dimension_id")
        if not dimension_id:
            continue
        result[dimension_id] = {
            "chosen_candidate": item.get("chosen_candidate"),
            "chosen_candidate_name": item.get("chosen_candidate_name"),
            "design_freedom": item.get("design_freedom"),
            "provisional": item.get("provisional", False),
        }
    return result


def _extract_fragment_map(run_dir: Path) -> dict[str, Any]:
    """提取 skill fragments 的稳定摘要。"""
    fragment_dir = run_dir / "skill_fragments"
    result = {}
    if not fragment_dir.exists():
        return result

    for file_path in sorted(fragment_dir.glob("*.json")):
        payload = _load_json_file(file_path)
        result[file_path.name] = {
            "digest": _stable_digest(payload),
            "emitted_families": payload.get("emitted_families", []),
            "status": payload.get("status"),
        }
    return result


def _extract_build_ir_map(run_dir: Path) -> dict[str, Any]:
    """提取 build_ir 中的 build steps。"""
    payload = _load_optional_json(run_dir / "build_ir.json") or {}
    steps = payload.get("build_steps", [])
    result = {}
    if not isinstance(steps, list):
        return result

    for item in steps:
        if not isinstance(item, dict):
            continue
        step_id = item.get("step_id")
        if not step_id:
            continue
        result[step_id] = {
            "digest": _stable_digest(item),
            "action": item.get("action"),
            "source_skill_instance_id": item.get("source_skill_instance_id"),
        }
    return result


def _extract_naming_map(run_dir: Path) -> dict[str, Any]:
    """提取 naming_resolution_log 的逐 action 摘要。"""
    payload = _load_optional_json(run_dir / "naming_resolution_log.json") or {}
    entries = payload.get("entries", [])
    result = {}
    if not isinstance(entries, list):
        return result

    for item in entries:
        if not isinstance(item, dict):
            continue
        action_id = item.get("ir_action_id")
        if not action_id:
            continue
        result[action_id] = item.get("naming_resolution_log", {})
    return result


def _extract_provisional_ids(snapshot: dict[str, Any]) -> list[str]:
    """提取 provisional item id 列表。"""
    result = []
    for item in snapshot.get("provisional_items", []):
        if isinstance(item, dict) and item.get("item_id"):
            result.append(item["item_id"])
    return sorted(set(result))


def _build_diff_entries(
    category: str,
    run_a_map: dict[str, Any],
    run_b_map: dict[str, Any],
    default_impact: str = "medium",
) -> list[dict[str, Any]]:
    """生成 added / removed / changed 差异明细。"""
    details = []
    all_keys = sorted(set(run_a_map) | set(run_b_map))
    for item_key in all_keys:
        if item_key not in run_a_map:
            details.append(
                {
                    "category": category,
                    "item_key": item_key,
                    "change_type": "added_in_run_b",
                    "impact": default_impact,
                    "run_a_value": None,
                    "run_b_value": run_b_map[item_key],
                }
            )
            continue
        if item_key not in run_b_map:
            details.append(
                {
                    "category": category,
                    "item_key": item_key,
                    "change_type": "removed_in_run_b",
                    "impact": default_impact,
                    "run_a_value": run_a_map[item_key],
                    "run_b_value": None,
                }
            )
            continue
        if _stable_digest(run_a_map[item_key]) != _stable_digest(run_b_map[item_key]):
            details.append(
                {
                    "category": category,
                    "item_key": item_key,
                    "change_type": "changed",
                    "impact": default_impact,
                    "run_a_value": run_a_map[item_key],
                    "run_b_value": run_b_map[item_key],
                }
            )
    return details


def _build_run_comparison(snapshot_a: dict[str, Any], snapshot_b: dict[str, Any]) -> dict[str, Any]:
    """构建跨 run 比较结果。"""
    run_a_dir = snapshot_a["run_dir"]
    run_b_dir = snapshot_b["run_dir"]

    constraints_a = _extract_constraint_map(run_a_dir)
    constraints_b = _extract_constraint_map(run_b_dir)
    realizations_a = _extract_realization_map(run_a_dir)
    realizations_b = _extract_realization_map(run_b_dir)
    fragments_a = _extract_fragment_map(run_a_dir)
    fragments_b = _extract_fragment_map(run_b_dir)
    build_ir_a = _extract_build_ir_map(run_a_dir)
    build_ir_b = _extract_build_ir_map(run_b_dir)
    naming_a = _extract_naming_map(run_a_dir)
    naming_b = _extract_naming_map(run_b_dir)
    provisional_a = set(_extract_provisional_ids(snapshot_a))
    provisional_b = set(_extract_provisional_ids(snapshot_b))

    constraint_differences = _build_diff_entries("constraint", constraints_a, constraints_b, "high")
    realization_differences = _build_diff_entries("realization", realizations_a, realizations_b)
    fragment_differences = _build_diff_entries("fragment", fragments_a, fragments_b)
    build_ir_differences = _build_diff_entries("build_ir", build_ir_a, build_ir_b)
    naming_differences = _build_diff_entries("naming", naming_a, naming_b, "low")

    comparison = {
        "comparison_version": "1.0",
        "comparison_id": f"cmp-{snapshot_a['run_id']}-vs-{snapshot_b['run_id']}",
        "run_a_id": snapshot_a["run_id"],
        "run_b_id": snapshot_b["run_id"],
        "compared_at": _utc_now_iso(),
        "summary": {
            "constraint_consistent": len(constraint_differences) == 0,
            "constraint_changes": len(constraint_differences),
            "realization_changes": len(realization_differences),
            "fragment_changes": len(fragment_differences),
            "build_ir_changes": len(build_ir_differences),
            "naming_changes": len(naming_differences),
            "provisional_delta": len(provisional_b) - len(provisional_a),
        },
        "details": {
            "constraint_differences": constraint_differences,
            "realization_differences": realization_differences,
            "fragment_differences": fragment_differences,
            "build_ir_differences": build_ir_differences,
            "naming_differences": naming_differences,
            "provisional_changes": {
                "added": sorted(provisional_b - provisional_a),
                "removed": sorted(provisional_a - provisional_b),
            },
        },
        "metadata": {
            "run_a_promotable": _evaluate_promotable(snapshot_a)["promotable"],
            "run_b_promotable": _evaluate_promotable(snapshot_b)["promotable"],
            "compared_artifacts": [
                "root_skill_contract.json",
                "converged_realization_pack.json",
                "skill_fragments/*.json",
                "build_ir.json",
                "naming_resolution_log.json",
                "metadata.provisional_items",
            ],
            "cleanup_policy": DEFAULT_CLEANUP_POLICY,
        },
    }
    _validate_payload_with_schema(comparison, RUN_COMPARISON_SCHEMA_PATH, "run_comparison")
    return comparison


def _next_batch_id() -> str:
    """生成 batch_id，按当天顺序递增。"""
    BATCHES_ROOT.mkdir(parents=True, exist_ok=True)
    date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"batch-{date_part}-"
    sequence = 1
    for child in BATCHES_ROOT.iterdir():
        if not child.is_dir():
            continue
        if not child.name.startswith(prefix):
            continue
        tail = child.name[len(prefix):]
        if tail.isdigit():
            sequence = max(sequence, int(tail) + 1)
    batch_id = f"{prefix}{sequence:03d}"
    if not BATCH_ID_PATTERN.fullmatch(batch_id):
        raise ValueError(f"非法 batch_id: {batch_id}")
    return batch_id


def _copy_promoted_artifacts(run_dir: Path, promoted_dir: Path) -> list[str]:
    """复制允许 promote 的正式产物。"""
    promoted_dir.mkdir(parents=True, exist_ok=True)
    copied = []

    for artifact_name in PROMOTED_ARTIFACTS:
        source_path = run_dir / artifact_name
        if not source_path.exists():
            continue

        target_path = promoted_dir / artifact_name
        if source_path.is_dir():
            shutil.copytree(source_path, target_path, dirs_exist_ok=True)
        else:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
        copied.append(artifact_name.replace("\\", "/"))

    return copied


def _load_batch_manifest(batch_id: str) -> dict[str, Any]:
    """读取 batch manifest。"""
    return _load_json_file(BATCHES_ROOT / batch_id / "manifest.json")


def _save_batch_manifest(manifest: dict[str, Any], batch_dir: Path) -> Path:
    """校验并保存 batch manifest。"""
    _validate_payload_with_schema(manifest, BATCH_MANIFEST_SCHEMA_PATH, "batch_manifest")
    return _write_json_file(batch_dir / "manifest.json", manifest)


def _update_active_batch(batch_id: str, make_active: bool) -> None:
    """更新唯一 active batch 指针。"""
    BATCHES_ROOT.mkdir(parents=True, exist_ok=True)

    if not make_active:
        return

    previous_batch_id = None
    if ACTIVE_BATCH_POINTER_PATH.exists():
        previous_payload = _load_json_file(ACTIVE_BATCH_POINTER_PATH)
        previous_batch_id = previous_payload.get("active_batch_id")

    if previous_batch_id and previous_batch_id != batch_id:
        previous_manifest_path = BATCHES_ROOT / previous_batch_id / "manifest.json"
        if previous_manifest_path.exists():
            previous_manifest = _load_json_file(previous_manifest_path)
            previous_manifest["active"] = False
            _save_batch_manifest(previous_manifest, previous_manifest_path.parent)

    _write_json_file(
        ACTIVE_BATCH_POINTER_PATH,
        {
            "active_batch_id": batch_id,
            "updated_at": _utc_now_iso(),
        },
    )


def _create_batch_from_snapshot(
    snapshot: dict[str, Any],
    promoted_by: str,
    notes: str,
    make_active: bool,
    update_base_project: bool,
) -> dict[str, Any]:
    """执行 promote 主流程。"""
    promotable = _evaluate_promotable(snapshot)
    if not promotable["promotable"]:
        return _make_response(
            "failed",
            f"run 不可 promote: {snapshot['run_id']}",
            data={
                "run_id": snapshot["run_id"],
                "checks": promotable["checks"],
            },
            errors=[f"PROMOTE_REJECTED: {reason}" for reason in promotable["reasons"]],
        )

    batch_id = _next_batch_id()
    batch_dir = BATCHES_ROOT / batch_id
    promoted_dir = batch_dir / "promoted_artifacts"
    copied_artifacts = _copy_promoted_artifacts(snapshot["run_dir"], promoted_dir)
    promoted_at = _utc_now_iso()

    promotion_report = {
        "report_version": "1.0",
        "batch_id": batch_id,
        "source_run_id": snapshot["run_id"],
        "promoted_at": promoted_at,
        "promoted_by": promoted_by,
        "artifacts_promoted": copied_artifacts,
        "remaining_provisionals": _extract_provisional_ids(snapshot),
        "notes": notes,
        "base_project_update": {
            "requested": update_base_project,
            "applied": False,
            "mode": "not_requested",
        },
        "cleanup_policy": DEFAULT_CLEANUP_POLICY,
    }

    if update_base_project:
        _write_json_file(
            CURRENT_PROMOTED_POINTER_PATH,
            {
                "batch_id": batch_id,
                "source_run_id": snapshot["run_id"],
                "updated_at": promoted_at,
                "mode": "governance_pointer_only",
            },
        )
        promotion_report["base_project_update"] = {
            "requested": True,
            "applied": True,
            "mode": "governance_pointer_only",
            "pointer_path": _path_to_project_relative(CURRENT_PROMOTED_POINTER_PATH),
        }

    promotion_report_path = _write_json_file(batch_dir / "promotion_report.json", promotion_report)

    manifest = {
        "manifest_version": "1.0",
        "batch_id": batch_id,
        "source_run_id": snapshot["run_id"],
        "created_at": promoted_at,
        "promoted_at": promoted_at,
        "active": bool(make_active),
        "promoted_by": promoted_by,
        "promoted_artifacts": copied_artifacts,
        "source_snapshot": {
            "session_version": snapshot.get("session_version", "2.0"),
            "status": snapshot.get("status"),
            "fast_mode": bool(snapshot.get("fast_mode", False)),
            "generator_provider": snapshot.get("generator_provider"),
            "pipeline_stages_completed": snapshot.get("pipeline_stages_completed", []),
            "constraint_violations": int(snapshot.get("constraint_violations", 0)),
            "promotable": True,
            "run_output_dir": snapshot.get("output_dir"),
        },
        "paths": {
            "batch_dir": _path_to_project_relative(batch_dir),
            "promoted_artifacts_dir": _path_to_project_relative(promoted_dir),
            "promotion_report_path": _path_to_project_relative(promotion_report_path),
        },
        "cleanup_policy": DEFAULT_CLEANUP_POLICY,
        "metadata": {
            "base_project_pointer_updated": bool(update_base_project),
            "note": (
                "Phase 11 当前仅更新治理层 baseline 指针，不直接回写 Source/Content。"
                if update_base_project
                else "仅创建 batch，不更新 baseline 指针。"
            ),
        },
    }

    _save_batch_manifest(manifest, batch_dir)
    _update_active_batch(batch_id, make_active)

    return _make_response(
        "success",
        f"Batch 创建成功: {batch_id}",
        data={
            "batch_id": batch_id,
            "source_run_id": snapshot["run_id"],
            "manifest_path": _path_to_project_relative(batch_dir / "manifest.json"),
            "promotion_report_path": _path_to_project_relative(promotion_report_path),
            "promoted_artifacts_dir": _path_to_project_relative(promoted_dir),
            "active": bool(make_active),
            "artifacts_promoted": copied_artifacts,
        },
    )


def _derive_open_questions(manifest: dict[str, Any]) -> list[str]:
    """从 manifest 中提取当前仍未解决的问题。"""
    summary = manifest.get("summary", {})
    evidence_items = manifest.get("evidence_items", [])

    questions = []
    if not evidence_items:
        questions.append("当前 run_id 下没有登记任何证据项。")
    if summary.get("total_checks", 0) <= 0:
        questions.append("summary.total_checks 为 0，无法证明测试覆盖度。")
    if summary.get("warnings", 0) > 0:
        questions.append(f"存在 {summary.get('warnings', 0)} 条 warning，需要确认是否影响验收。")
    if manifest.get("status") == "pending":
        questions.append("manifest 仍处于 pending，尚未形成明确验收结论。")
    return questions


def _derive_judgment(manifest: dict[str, Any], criteria: dict[str, Any] | None = None) -> dict[str, Any]:
    """根据 manifest 与简单准则生成轻量判定结果。"""
    criteria = criteria or {}
    summary = manifest.get("summary", {})
    evidence_items = manifest.get("evidence_items", [])
    manifest_status = manifest.get("status", "pending")

    required_types = criteria.get("required_types", [])
    min_checks = criteria.get("min_checks", 0)

    if not isinstance(required_types, list):
        raise ValueError("criteria.required_types 必须是数组")
    if not isinstance(min_checks, int) or min_checks < 0:
        raise ValueError("criteria.min_checks 必须是大于等于 0 的整数")

    present_types = {item.get("type") for item in evidence_items}
    missing_types = sorted(item_type for item_type in required_types if item_type not in present_types)
    total_checks = summary.get("total_checks", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    warnings_count = summary.get("warnings", 0)

    open_questions = _derive_open_questions(manifest)
    if missing_types:
        open_questions.append("缺少必需证据类型: " + ", ".join(missing_types))
    if total_checks < min_checks:
        open_questions.append(
            f"检查数量不足：要求至少 {min_checks} 项，当前 {total_checks} 项。"
        )

    if failed > 0 or manifest_status == "fail":
        judgment = "fail"
        confidence = "high" if not missing_types and total_checks >= min_checks else "medium"
        reasoning = f"已记录失败检查 {failed} 项，当前证据支持直接判定为 fail。"
    elif not evidence_items or missing_types or total_checks < min_checks or warnings_count > 0 or manifest_status == "escalate":
        judgment = "escalate"
        confidence = "low" if not evidence_items else "medium"
        reasoning = "当前证据存在缺口或不确定项，建议升级人工确认。"
    elif manifest_status == "pass" or (total_checks > 0 and passed >= total_checks):
        judgment = "pass"
        confidence = "high"
        reasoning = "当前证据覆盖完整，且未发现失败项，可初步判定为 pass。"
    else:
        judgment = "escalate"
        confidence = "medium"
        reasoning = "当前证据没有明确失败，但也不足以自动通过，建议升级人工确认。"

    return {
        "judgment": judgment,
        "confidence": confidence,
        "reasoning": reasoning,
        "open_questions": open_questions,
        "required_types": required_types,
        "missing_types": missing_types,
        "min_checks": min_checks,
        "evidence_count": len(evidence_items),
        "summary": summary,
    }


def evidence_load_manifest(run_id: str) -> dict:
    """读取指定 run_id 的 evidence manifest。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        return _make_response(
            "success",
            "Evidence manifest 加载成功",
            data=manifest,
        )
    except FileNotFoundError as exc:
        message = str(exc).split(": ", 1)[-1]
        return _missing_path_response(Path(message), "manifest 文件")
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence manifest 加载失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_load_screenshots(run_id: str) -> dict:
    """列出 screenshots 目录下的全部文件。"""
    try:
        run_dir = _get_run_dir(run_id)
        if not run_dir.exists():
            return _missing_path_response(run_dir, "run_id 目录")

        files = _list_files(run_dir, "screenshots")
        return _make_response(
            "success",
            "Screenshots 读取成功",
            data={
                "run_id": run_id,
                "files": _to_relative_paths(run_dir, files),
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Screenshots 读取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_load_logs(run_id: str) -> dict:
    """读取 logs 目录下的全部日志文件内容。"""
    try:
        run_dir = _get_run_dir(run_id)
        if not run_dir.exists():
            return _missing_path_response(run_dir, "run_id 目录")

        logs = []
        for file_path in _list_files(run_dir, "logs"):
            logs.append(
                {
                    "file": file_path.relative_to(run_dir).as_posix(),
                    "content": _read_text_file(file_path),
                }
            )

        return _make_response(
            "success",
            "Logs 读取成功",
            data={
                "run_id": run_id,
                "logs": logs,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Logs 读取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_load_report(run_id: str) -> dict:
    """读取 reports 目录下的全部报告文件内容。"""
    try:
        run_dir = _get_run_dir(run_id)
        if not run_dir.exists():
            return _missing_path_response(run_dir, "run_id 目录")

        reports = []
        for file_path in _list_files(run_dir, "reports"):
            reports.append(
                {
                    "file": file_path.relative_to(run_dir).as_posix(),
                    "content": _read_text_file(file_path),
                }
            )

        return _make_response(
            "success",
            "Reports 读取成功",
            data={
                "run_id": run_id,
                "reports": reports,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Reports 读取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_judge_acceptance(run_id: str, criteria: dict[str, Any]) -> dict:
    """基于 manifest 覆盖度与摘要做轻量验收判定。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        judgment = _derive_judgment(manifest, criteria)
        return _make_response(
            "success",
            "Evidence acceptance 判定完成",
            data=judgment,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence acceptance 判定失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_decide_escalation(run_id: str) -> dict:
    """判断当前 run_id 是否需要升级人工确认。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        summary = manifest.get("summary", {})
        open_questions = _derive_open_questions(manifest)

        needs_human = False
        reasons = []
        if manifest.get("status") == "escalate":
            needs_human = True
            reasons.append("manifest 已显式标记为 escalate")
        if summary.get("warnings", 0) > 0:
            needs_human = True
            reasons.append(f"存在 {summary.get('warnings', 0)} 条 warning")
        if summary.get("total_checks", 0) <= 0:
            needs_human = True
            reasons.append("未记录有效检查数量")
        if summary.get("failed", 0) > 0 and summary.get("passed", 0) > 0:
            needs_human = True
            reasons.append("同时存在 passed 与 failed，需要人工确认边界")

        if needs_human:
            reason = "；".join(reasons)
            escalation_note = "建议人工复核以下问题：" + "；".join(open_questions or reasons)
        else:
            reason = "当前证据状态明确，无需升级人工确认"
            escalation_note = ""

        return _make_response(
            "success",
            "Evidence escalation 判定完成",
            data={
                "needs_human": needs_human,
                "reason": reason,
                "escalation_note": escalation_note,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence escalation 判定失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_export_summary(run_id: str) -> dict:
    """汇总 manifest 并导出结构化验收摘要。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        judgment = _derive_judgment(manifest, {})
        return _make_response(
            "success",
            "Evidence summary 导出成功",
            data={
                "run_id": manifest.get("run_id"),
                "test_type": manifest.get("test_type"),
                "status": manifest.get("status"),
                "evidence_count": len(manifest.get("evidence_items", [])),
                "judgment": judgment.get("judgment"),
                "open_questions": judgment.get("open_questions", []),
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence summary 导出失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_list_runs(date_filter: str | None = None) -> dict:
    """列出当前证据根目录下的全部 run_id。"""
    try:
        runs = evidence_manager.list_runs(date_filter)
        return _make_response(
            "success",
            "Evidence runs 列出成功",
            data={"runs": runs},
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence runs 列出失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_compare_runs(run_a_id: str, run_b_id: str, output_path: str | None = None) -> dict:
    """比较两个 Phase 11 run 的核心产物差异。"""
    try:
        snapshot_a = _load_run_workspace_snapshot(run_a_id)
        snapshot_b = _load_run_workspace_snapshot(run_b_id)
        comparison = _build_run_comparison(snapshot_a, snapshot_b)

        saved_path = None
        if output_path:
            target_path = Path(output_path)
            if not target_path.is_absolute():
                target_path = get_project_root() / target_path
            _write_json_file(target_path, comparison)
            saved_path = _path_to_project_relative(target_path)

        data = dict(comparison)
        if saved_path:
            data["output_path"] = saved_path

        return _make_response(
            "success",
            "Run comparison 完成",
            data=data,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Run comparison 失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_create_batch(
    source_run_id: str,
    promoted_by: str = "human_review",
    notes: str = "",
    make_active: bool = True,
) -> dict:
    """从 promotable run 创建 batch。"""
    try:
        snapshot = _load_run_workspace_snapshot(source_run_id)
        return _create_batch_from_snapshot(
            snapshot=snapshot,
            promoted_by=promoted_by,
            notes=notes,
            make_active=make_active,
            update_base_project=False,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Create batch 失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_promote_run(
    source_run_id: str,
    promoted_by: str = "human_review",
    notes: str = "",
    make_active: bool = True,
    update_base_project: bool = True,
) -> dict:
    """promote run 到 batch，并更新治理层 baseline 指针。"""
    try:
        snapshot = _load_run_workspace_snapshot(source_run_id)
        return _create_batch_from_snapshot(
            snapshot=snapshot,
            promoted_by=promoted_by,
            notes=notes,
            make_active=make_active,
            update_base_project=update_base_project,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Promote run 失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )
