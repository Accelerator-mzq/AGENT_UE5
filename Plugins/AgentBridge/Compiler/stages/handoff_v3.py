"""
Handoff Assembly v3 - Stage 7 (v2.0)

职责：
  - 汇总 Stage 1-6 产物
  - 输出面向执行层的 Reviewed Handoff v3
  - 强化 Phase 11 关注的 run_id / design_directions / provisional / design_decision_log 摘要
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import re
from typing import Any, Dict, List


def _now_iso() -> str:
    """返回 UTC ISO 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def _safe_token(value: str, fallback: str) -> str:
    """把任意字符串规整成 handoff id 可接受的 token。"""
    token = re.sub(r"[^a-z0-9_]+", "_", value.lower()).strip("_")
    return token or fallback


def _collect_fragments(stage4_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """统一读取 Stage 4 fragments。"""
    fragments = stage4_output.get("skill_fragments", [])
    return fragments if isinstance(fragments, list) else []


def _collect_provisional_items(clarification_gate_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """统一读取 provisional_items。"""
    items = clarification_gate_report.get("provisional_items", [])
    return items if isinstance(items, list) else []


def _build_skill_instance_summary(
    skill_graph: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """构造 skill instance 摘要。"""
    fragment_map = {
        fragment.get("skill_instance_id", ""): fragment
        for fragment in fragments
        if fragment.get("skill_instance_id")
    }
    summaries: List[Dict[str, Any]] = []

    for node in skill_graph.get("nodes", []):
        instance_id = node.get("instance_id", "")
        fragment = fragment_map.get(instance_id, {})
        summaries.append(
            {
                "skill_instance_id": instance_id,
                "template_id": node.get("template_id", ""),
                "domain_type": node.get("domain_type", ""),
                "status": fragment.get("status", node.get("status", "pending")),
                "emitted_families": fragment.get("emitted_families", []),
                "capability_gaps": fragment.get("capability_gaps", []),
            }
        )
    return summaries


def _collect_design_directions(stage4_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """从 converged_realization_pack 汇总设计方向。"""
    converged_pack = stage4_output.get("converged_realization_pack", {})
    entries = converged_pack.get("entries", [])
    summary: List[Dict[str, Any]] = []

    for entry in entries:
        directions = []
        for choice in entry.get("converged_choices", []):
            directions.append(
                {
                    "dimension_id": choice.get("dimension_id", ""),
                    "chosen_candidate": choice.get("chosen_candidate", ""),
                    "chosen_candidate_name": choice.get("chosen_candidate_name", ""),
                    "rationale": choice.get("rationale", ""),
                    "provisional": bool(choice.get("provisional", False)),
                }
            )
        summary.append(
            {
                "skill_instance_id": entry.get("skill_instance_id", ""),
                "template_id": entry.get("template_id", ""),
                "directions": directions,
            }
        )
    return summary


def _collect_design_decision_log_summary(fragments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """统计 design_decision_log 概况。"""
    total_decisions = 0
    provisional_decisions = 0
    high_impact_decisions = 0
    by_skill = Counter()

    for fragment in fragments:
        skill_instance_id = fragment.get("skill_instance_id", "")
        for decision in fragment.get("design_decision_log", []):
            total_decisions += 1
            by_skill[skill_instance_id] += 1
            if decision.get("provisional"):
                provisional_decisions += 1
            if decision.get("impact") == "high":
                high_impact_decisions += 1

    return {
        "total_decisions": total_decisions,
        "provisional_decisions": provisional_decisions,
        "high_impact_decisions": high_impact_decisions,
        "skills_with_decisions": len(by_skill),
        "by_skill_instance": dict(sorted(by_skill.items())),
    }


def _collect_capability_gaps(
    cross_review_report: Dict[str, Any],
    fragments: List[Dict[str, Any]],
    build_ir: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """汇总 capability gaps。"""
    gaps: List[Dict[str, Any]] = []

    for gap in cross_review_report.get("capability_gap_list", []):
        gaps.append({"source": "cross_review", "description": str(gap), "severity": "degraded"})

    for fragment in fragments:
        for gap in fragment.get("capability_gaps", []):
            if isinstance(gap, dict):
                gaps.append(
                    {
                        "source": "skill_fragment",
                        "description": gap.get("description", str(gap)),
                        "severity": gap.get("severity", "degraded"),
                    }
                )
            else:
                gaps.append({"source": "skill_fragment", "description": str(gap), "severity": "degraded"})

    for warning in build_ir.get("lowering_report", {}).get("unbound_requirements", []):
        gaps.append({"source": "lowering", "description": str(warning), "severity": "degraded"})

    return gaps


def _constraint_variant_summary(
    root_skill_contract: Dict[str, Any],
    cross_review_report: Dict[str, Any],
    stage4_output: Dict[str, Any],
) -> Dict[str, Any]:
    """汇总 constraint / variant 情况。"""
    converged_pack = stage4_output.get("converged_realization_pack", {})
    converged_entries = converged_pack.get("entries", [])
    explored_variants = sum(len(entry.get("converged_choices", [])) for entry in converged_entries)

    return {
        "constraint_count": len(root_skill_contract.get("constraint_fields", {})),
        "variant_count": len(root_skill_contract.get("variant_fields", {})),
        "preserved_constraints": cross_review_report.get("constraint_preservation_summary", {}).get("preserved_count", 0),
        "violated_constraints": cross_review_report.get("constraint_preservation_summary", {}).get("violations", 0),
        "explored_variant_directions": explored_variants,
    }


def assemble_handoff_v3(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    skill_graph: Dict[str, Any],
    stage4_output: Dict[str, Any],
    cross_review_report: Dict[str, Any],
    build_ir: Dict[str, Any],
    naming_resolution_log: Dict[str, Any],
    session_meta: Dict[str, Any],
) -> Dict[str, Any]:
    """组装 Reviewed Handoff v3。"""
    fragments = _collect_fragments(stage4_output)
    project_name = root_skill_contract.get("source_gdd", {}).get("file_path", "")
    project_name = project_name.split("\\")[-1].replace("GDD_", "").replace(".md", "") or "UnknownProject"

    run_id = session_meta.get("run_id", "")
    session_id = session_meta.get("session_id", "")
    approval_status = cross_review_report.get("review_status", "approved")
    provisional_items = _collect_provisional_items(clarification_gate_report)
    blocked_reasons = [
        issue.get("message", "")
        for issue in cross_review_report.get("issues_found", [])
        if issue.get("severity") == "blocker"
    ]

    design_directions_summary = _collect_design_directions(stage4_output)
    design_decision_log_summary = _collect_design_decision_log_summary(fragments)
    baseline_coverage_summary = cross_review_report.get("baseline_coverage_summary", {})
    constraint_variant_summary = _constraint_variant_summary(
        root_skill_contract,
        cross_review_report,
        stage4_output,
    )

    handoff_id = f"handoff.{_safe_token(project_name, 'project')}.{_safe_token((run_id or session_id)[:12], 'run')}"

    return {
        "handoff_meta": {
            "handoff_version": "3.0",
            "handoff_id": handoff_id,
            "schema_version": "3.0",
            "created_at": _now_iso(),
            "target_phase": session_meta.get("target_phase", ""),
            "build_goal": root_skill_contract.get("build_goal", "playable_template"),
            "run_id": run_id,
            "session_version": session_meta.get("session_version", "2.0"),
            "fast_mode": bool(session_meta.get("fast_mode", False)),
        },
        "run_id": run_id,
        "project_context": {
            "project_name": project_name,
            "game_type": root_skill_contract.get("game_identity", {}).get("game_type", ""),
            "subgenre": root_skill_contract.get("game_identity", {}).get("subgenre", ""),
            "target_phase": session_meta.get("target_phase", ""),
            "source_contract_id": root_skill_contract.get("contract_id", ""),
        },
        "selected_skill_instances": _build_skill_instance_summary(skill_graph, fragments),
        "design_directions_summary": design_directions_summary,
        "constraint_variant_summary": constraint_variant_summary,
        "baseline_coverage_summary": baseline_coverage_summary,
        "provisional_items": provisional_items,
        "design_decision_log_summary": design_decision_log_summary,
        "cross_review_summary": {
            "review_id": cross_review_report.get("review_id", ""),
            "status": approval_status,
            "issues_found": len(cross_review_report.get("issues_found", [])),
            "review_checks": cross_review_report.get("review_checks", []),
            "cross_domain_conflict_summary": cross_review_report.get("cross_domain_conflict_summary", {}),
            "bp_thin_layer_summary": cross_review_report.get("bp_thin_layer_summary", {}),
        },
        "lowering_summary": {
            "ir_id": build_ir.get("ir_id", ""),
            "build_step_count": len(build_ir.get("build_steps", [])),
            "validation_point_count": len(build_ir.get("validation_ir", [])),
            "families_bound": build_ir.get("lowering_report", {}).get("families_bound", []),
            "families_partially_bound": build_ir.get("lowering_report", {}).get("families_partially_bound", []),
            "unbound_requirements": build_ir.get("lowering_report", {}).get("unbound_requirements", []),
            "naming_resolution_summary": naming_resolution_log.get("summary", {}),
        },
        "build_ir": {
            "ir_id": build_ir.get("ir_id", ""),
            "build_steps": build_ir.get("build_steps", []),
            "inline": True,
        },
        "validation_ir": {
            "validations": build_ir.get("validation_ir", []),
            "inline": True,
        },
        "naming_resolution_log": {
            "entries": naming_resolution_log.get("entries", []),
            "summary": naming_resolution_log.get("summary", {}),
            "inline": True,
        },
        "capability_gaps": _collect_capability_gaps(cross_review_report, fragments, build_ir),
        "approval": {
            "approval_status": approval_status,
            "approver": "auto",
            "blocked_reasons": blocked_reasons,
            "notes": "Reviewed Handoff v3 由 Compiler Pipeline v2 自动组装。",
        },
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.HandoffV3.v2",
            "source_contract_id": root_skill_contract.get("contract_id", ""),
            "source_review_id": cross_review_report.get("review_id", ""),
            "source_ir_id": build_ir.get("ir_id", ""),
            "session_id": session_id,
            "run_id": run_id,
            "gdd_path": session_meta.get("gdd_path", ""),
        },
    }
