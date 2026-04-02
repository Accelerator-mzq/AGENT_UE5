"""
Phase 7 治理审计与一致性工具。

职责：
1. 统一校验 execution_report / snapshot manifest / promotion_status。
2. 生成可读的治理审计摘要。
3. 生成 JRPG pack 的跨入口一致性报告。
4. 生成 Phase 7 归档前检查表。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import yaml


def load_json_file(file_path: str) -> Dict[str, Any]:
    """读取 JSON 文件；文件不存在时返回空字典。"""
    if not file_path or not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """读取 YAML 文件；文件不存在时返回空字典。"""
    if not file_path or not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def build_execution_governance_entry(
    entry_name: str,
    execution_report_path: str,
    *,
    extra_report_paths: Dict[str, str] | None = None,
) -> Dict[str, Any]:
    """基于 execution_report 构建统一治理审计条目。"""
    execution_report = load_json_file(execution_report_path)
    snapshot_ref = execution_report.get("snapshot_ref", "")
    promotion_status = execution_report.get("promotion_status", {})
    regression_summary = execution_report.get("regression_summary", {})
    snapshot_manifest = load_json_file(snapshot_ref)

    checks = {
        "execution_report_exists": _build_check(
            bool(execution_report),
            actual=execution_report_path,
        ),
        "execution_report_is_succeeded": _build_check(
            execution_report.get("execution_status") == "succeeded",
            actual=execution_report.get("execution_status", ""),
        ),
        "regression_summary_present": _build_check(
            bool(regression_summary) and regression_summary.get("status") == "captured",
            actual=regression_summary,
        ),
        "snapshot_manifest_complete": _build_check(
            _snapshot_manifest_complete(snapshot_manifest, execution_report_path),
            actual=snapshot_manifest,
        ),
        "promotion_status_complete": _build_check(
            _promotion_status_complete(promotion_status, snapshot_ref),
            actual=promotion_status,
        ),
    }

    extra_report_details: Dict[str, Any] = {}
    if extra_report_paths:
        for report_name, report_path in extra_report_paths.items():
            report_payload = load_json_file(report_path)
            extra_report_details[report_name] = {
                "path": report_path,
                "exists": bool(report_payload),
                "report_type": report_payload.get("report_type", ""),
                "overall_status": report_payload.get("overall_status", ""),
            }
            checks[f"{report_name}_present"] = _build_check(bool(report_payload), actual=report_path)
            if report_payload:
                checks[f"{report_name}_passed"] = _build_check(
                    report_payload.get("overall_status", "passed") == "passed",
                    actual=report_payload.get("overall_status", ""),
                )

    return {
        "entry_name": entry_name,
        "execution_report_path": execution_report_path,
        "snapshot_ref": snapshot_ref,
        "promotion_status": promotion_status,
        "regression_summary": regression_summary,
        "extra_reports": extra_report_details,
        "checks": checks,
        "overall_status": "passed" if all(item["passed"] for item in checks.values()) else "failed",
    }


def write_governance_audit_summary(
    report_dir: str,
    summary_name: str,
    execution_entries: Iterable[Tuple[str, str, Dict[str, str] | None]],
) -> Dict[str, str]:
    """写出治理审计摘要 JSON 和 Markdown。"""
    entries = [
        build_execution_governance_entry(name, report_path, extra_report_paths=extra_report_paths)
        for name, report_path, extra_report_paths in execution_entries
    ]
    payload = {
        "report_type": "phase7_governance_audit_summary",
        "generated_at": datetime.now().isoformat(),
        "summary_name": summary_name,
        "entries": entries,
        "overall_status": "passed" if all(entry["overall_status"] == "passed" for entry in entries) else "failed",
    }

    output_root = Path(report_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{summary_name}.json"
    md_path = output_root / f"{summary_name}.md"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as file:
        file.write(_render_governance_audit_markdown(payload))

    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "overall_status": payload["overall_status"],
    }


def build_jrpg_pack_consistency_payload(
    *,
    greenfield_handoff: Dict[str, Any],
    brownfield_handoff: Dict[str, Any],
    smoke_handoff: Dict[str, Any],
    router_results: Dict[str, Dict[str, Any]],
    pack_modules: Dict[str, Any],
) -> Dict[str, Any]:
    """构建 JRPG pack 跨入口一致性负载。"""
    handoffs = {
        "greenfield": greenfield_handoff,
        "brownfield": brownfield_handoff,
        "smoke": smoke_handoff,
    }
    manifest_paths = {
        name: handoff.get("metadata", {}).get("skill_pack_manifest", "")
        for name, handoff in handoffs.items()
    }
    pack_ids = {
        name: _resolve_effective_pack_id(handoff)
        for name, handoff in handoffs.items()
    }
    base_domain_refs = {
        name: handoff.get("governance_context", {}).get("base_domain_refs", [])
        for name, handoff in handoffs.items()
    }

    manifest_required_skills = smoke_handoff.get("metadata", {}).get("skill_pack_manifest", "")
    loaded_required_skills = [entry.get("module_id", "") for entry in pack_modules.get("required_skills", [])]
    loaded_review_extensions = [entry.get("module_id", "") for entry in pack_modules.get("review_extensions", [])]
    loaded_validation_extensions = [entry.get("module_id", "") for entry in pack_modules.get("validation_extensions", [])]
    loaded_delta_policies = [entry.get("module_id", "") for entry in pack_modules.get("delta_policies", [])]

    checks = {
        "all_paths_use_same_manifest": _build_check(len(set(manifest_paths.values())) == 1, actual=manifest_paths),
        "all_paths_use_same_pack_id": _build_check(len(set(pack_ids.values())) == 1, actual=pack_ids),
        "all_paths_preserve_governance_domains": _build_check(
            len({tuple(values) for values in base_domain_refs.values()}) == 1,
            actual=base_domain_refs,
        ),
        "router_always_hits_jrpg_pack": _build_check(
            all(
                result.get("pack_id") == "genre-jrpg"
                and "genre-jrpg" in result.get("router_result", {}).get("activated_pack_ids", [])
                for result in router_results.values()
            ),
            actual=router_results,
        ),
        "required_skills_modules_are_complete": _build_check(
            loaded_required_skills == ["battle_layout", "turn_queue", "command_menu"]
            and all(entry.get("exists") is True for entry in pack_modules.get("required_skills", [])),
            actual=loaded_required_skills,
        ),
        "review_validation_delta_modules_are_complete": _build_check(
            loaded_review_extensions == ["jrpg_reviewer"]
            and loaded_validation_extensions == ["jrpg_validator"]
            and loaded_delta_policies == ["jrpg_delta_policy"],
            actual={
                "review_extensions": loaded_review_extensions,
                "validation_extensions": loaded_validation_extensions,
                "delta_policies": loaded_delta_policies,
            },
        ),
        "greenfield_and_smoke_share_greenfield_mode": _build_check(
            greenfield_handoff.get("handoff_mode") == "greenfield_bootstrap"
            and smoke_handoff.get("handoff_mode") == "greenfield_bootstrap",
            actual={
                "greenfield_mode": greenfield_handoff.get("handoff_mode", ""),
                "smoke_mode": smoke_handoff.get("handoff_mode", ""),
            },
        ),
        "brownfield_keeps_delta_intent": _build_check(
            brownfield_handoff.get("delta_context", {}).get("delta_intent") == "append_actor",
            actual=brownfield_handoff.get("delta_context", {}),
        ),
    }

    return {
        "report_type": "phase7_jrpg_pack_consistency",
        "generated_at": datetime.now().isoformat(),
        "shared_manifest_path": manifest_required_skills,
        "checks": checks,
        "overall_status": "passed" if all(item["passed"] for item in checks.values()) else "failed",
    }


def write_jrpg_pack_consistency_report(
    report_dir: str,
    summary_name: str,
    payload: Dict[str, Any],
) -> Dict[str, str]:
    """写出 JRPG pack 一致性报告。"""
    output_root = Path(report_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"{summary_name}.json"
    md_path = output_root / f"{summary_name}.md"

    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)

    with open(md_path, "w", encoding="utf-8") as file:
        file.write(_render_jrpg_consistency_markdown(payload))

    return {
        "json_path": str(json_path),
        "md_path": str(md_path),
        "overall_status": payload["overall_status"],
    }


def write_phase7_archive_preflight_checklist(
    report_dir: str,
    summary_name: str,
    checklist_items: Iterable[Tuple[str, bool, str]],
) -> str:
    """写出 Phase 7 归档前检查表。"""
    output_root = Path(report_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    md_path = output_root / f"{summary_name}.md"

    lines = [
        "# Phase 7 归档前检查表",
        "",
        f"- 生成时间：{datetime.now().isoformat()}",
        "",
    ]
    for title, passed, evidence in checklist_items:
        marker = "[x]" if passed else "[ ]"
        lines.append(f"- {marker} {title}")
        lines.append(f"  证据：{evidence}")
    lines.append("")
    lines.append(
        "- 归档准入规则：只有全部条目完成后，才允许归档根目录 `task.md` 并同步更新 `SystemTestCases.md` 与 `run_system_tests.py`。"
    )

    with open(md_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    return str(md_path)


def _snapshot_manifest_complete(snapshot_manifest: Dict[str, Any], execution_report_path: str) -> bool:
    """检查 snapshot manifest 是否满足 Phase 7 最小审计要求。"""
    required_keys = {"baseline_ref", "digest", "source_report", "created_at"}
    if not required_keys.issubset(snapshot_manifest.keys()):
        return False
    return snapshot_manifest.get("source_report", "") == execution_report_path


def _promotion_status_complete(promotion_status: Dict[str, Any], snapshot_ref: str) -> bool:
    """检查 promotion 状态是否和 execution_report 对齐。"""
    if not promotion_status:
        return False
    if promotion_status.get("snapshot_ref", "") != snapshot_ref:
        return False
    if len(promotion_status.get("transitions", [])) < 2:
        return False
    if not promotion_status.get("audit_note", ""):
        return False
    return promotion_status.get("current_state", "") in {"approved", "reviewed"}


def _resolve_effective_pack_id(handoff: Dict[str, Any]) -> str:
    """解析 handoff 的有效 pack_id，兼容 brownfield delta trace 未回填的情况。"""
    trace_pack_id = handoff.get("dynamic_spec_tree", {}).get("generation_trace", {}).get("skill_pack_id", "")
    if trace_pack_id:
        return trace_pack_id

    manifest_path = handoff.get("metadata", {}).get("skill_pack_manifest", "")
    if manifest_path:
        pack_name = Path(manifest_path).resolve().parent.name
        if pack_name:
            return f"genre-{pack_name}"
    return ""


def _build_check(passed: bool, *, actual: Any) -> Dict[str, Any]:
    """构建统一检查结果。"""
    return {
        "passed": bool(passed),
        "actual": actual,
    }


def _render_governance_audit_markdown(payload: Dict[str, Any]) -> str:
    """渲染治理审计 Markdown。"""
    lines = [
        "# Phase 7 治理审计摘要",
        "",
        f"- 名称：{payload['summary_name']}",
        f"- 生成时间：{payload['generated_at']}",
        f"- 总状态：{payload['overall_status']}",
        "",
    ]
    for entry in payload.get("entries", []):
        lines.append(f"## {entry['entry_name']}")
        lines.append("")
        lines.append(f"- execution_report：{entry['execution_report_path']}")
        lines.append(f"- snapshot_ref：{entry.get('snapshot_ref', '')}")
        lines.append(f"- 总状态：{entry['overall_status']}")
        for check_name, check in entry.get("checks", {}).items():
            marker = "PASS" if check.get("passed") else "FAIL"
            lines.append(f"- {check_name}: {marker}")
        lines.append("")
    return "\n".join(lines)


def _render_jrpg_consistency_markdown(payload: Dict[str, Any]) -> str:
    """渲染 JRPG 一致性 Markdown。"""
    lines = [
        "# Phase 7 JRPG Pack 一致性报告",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 总状态：{payload['overall_status']}",
        f"- Manifest：{payload.get('shared_manifest_path', '')}",
        "",
    ]
    for check_name, check in payload.get("checks", {}).items():
        marker = "PASS" if check.get("passed") else "FAIL"
        lines.append(f"- {check_name}: {marker}")
    return "\n".join(lines)
