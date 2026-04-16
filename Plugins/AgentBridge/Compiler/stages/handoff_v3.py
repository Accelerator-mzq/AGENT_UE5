"""
Handoff Assembly v3 — Stage 7 (v2.0)

职责：
  组装全部管线产物为最终 Reviewed Handoff v3。
  这是 v2.0 管线的终端阶段，将 Stage 1-6 的全部产物整合为
  一份可由 Orchestrator/Agent 执行的交接物。

输入：
  - root_skill_contract（Stage 1）
  - clarification_gate_report（Stage 2）
  - skill_graph（Stage 3）
  - stage4_output（Stage 4: fragments + design artifacts）
  - cross_review_report v2（Stage 5）
  - build_ir v2 + naming_resolution_log（Stage 6）

输出：
  - reviewed_handoff_v3.json

设计原则：
  - Handoff 是只读视图，不修改上游产物
  - provisional 标记从 Clarification Gate 传播到 Handoff
  - Constraint 值在 Handoff 中保持不变
  - fast_mode run 在 Handoff 中标记但不阻塞组装
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _collect_provisional_chain(
    clarification_gate_report: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    追踪 provisional 标记从 Clarification Gate 到 Fragments 的传播链。
    返回传播摘要。
    """
    provisional_items = clarification_gate_report.get("provisional_items", [])
    provisional_ids = {item.get("item_id", "") for item in provisional_items}

    # 在 fragments 中检查 provisional 引用
    propagated_to_fragments: List[Dict[str, Any]] = []
    for fragment in fragments:
        assumptions = fragment.get("assumptions", [])
        for assumption in assumptions:
            if assumption.get("provisional", False):
                propagated_to_fragments.append({
                    "fragment_id": fragment.get("skill_instance_id", ""),
                    "assumption": assumption.get("description", ""),
                    "source_item": assumption.get("source_clarification_id", ""),
                })

    return {
        "total_provisional_at_gate": len(provisional_items),
        "provisional_item_ids": list(provisional_ids),
        "propagated_to_fragments": propagated_to_fragments,
        "all_provisional_resolved": len(provisional_items) == 0,
    }


def _build_skill_instance_summary(
    skill_graph: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """从 Skill Graph 和 Fragments 构建 skill instance 状态摘要。"""
    fragment_map: Dict[str, Dict[str, Any]] = {}
    for fragment in fragments:
        fid = fragment.get("skill_instance_id", "")
        if fid:
            fragment_map[fid] = fragment

    summaries: List[Dict[str, Any]] = []
    for node in skill_graph.get("nodes", []):
        instance_id = node.get("instance_id", "")
        fragment = fragment_map.get(instance_id, {})

        summaries.append({
            "skill_instance_id": instance_id,
            "template_id": node.get("template_id", ""),
            "domain_type": node.get("domain_type", ""),
            "status": fragment.get("status", "pending"),
            "emitted_families": fragment.get("emitted_families", []),
            "confidence": fragment.get("confidence", {}),
            "capability_gaps": fragment.get("capability_gaps", []),
        })

    return summaries


def _collect_all_capability_gaps(
    cross_review_report: Dict[str, Any],
    fragments: List[Dict[str, Any]],
    build_ir: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """从 review、fragments、build_ir 汇总能力缺口。"""
    gaps: List[Dict[str, Any]] = []

    for gap in cross_review_report.get("capability_gap_list", []):
        if isinstance(gap, str):
            gaps.append({"source": "review", "description": gap, "severity": "degraded"})
        elif isinstance(gap, dict):
            gaps.append({
                "source": "review",
                "description": gap.get("description", str(gap)),
                "severity": gap.get("severity", "degraded"),
            })

    for fragment in fragments:
        for gap in fragment.get("capability_gaps", []):
            if isinstance(gap, str):
                gaps.append({"source": "skill", "description": gap, "severity": "degraded"})
            elif isinstance(gap, dict):
                gaps.append({
                    "source": "skill",
                    "description": gap.get("description", str(gap)),
                    "severity": gap.get("severity", "degraded"),
                })

    for gap_str in build_ir.get("lowering_report", {}).get("capability_gaps", []):
        gaps.append({"source": "lowering", "description": gap_str, "severity": "degraded"})

    return gaps


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
    """
    Stage 7 v2.0: 组装 Reviewed Handoff v3。

    session_meta 应包含:
      - session_id, run_id, target_phase, gdd_path, fast_mode, session_version
    """
    contract_id = root_skill_contract.get("contract_id", "")
    fragments = stage4_output.get("skill_fragments", [])
    ir_id = build_ir.get("ir_id", "")
    review_id = cross_review_report.get("review_id", "")

    # 项目名从 contract 推断
    project_name = root_skill_contract.get("project_identity", {}).get("project_name", "")
    if not project_name:
        project_name = contract_id.replace("rsc.", "").split(".")[0] if contract_id else "UnknownProject"

    game_type = root_skill_contract.get("project_identity", {}).get("game_type", "")
    subgenre = root_skill_contract.get("project_identity", {}).get("subgenre", "")

    # 审批状态
    review_status = cross_review_report.get("review_status", "approved")
    if review_status not in {"approved", "approved_with_warnings", "blocked"}:
        review_status = "approved"

    # 阻塞原因
    blocked_reasons: List[str] = []
    for issue in cross_review_report.get("issues_found", []):
        if issue.get("severity") == "error":
            blocked_reasons.append(issue.get("message", ""))

    # provisional 传播追踪
    provisional_chain = _collect_provisional_chain(clarification_gate_report, fragments)

    # Skill instance 摘要
    skill_instances = _build_skill_instance_summary(skill_graph, fragments)

    # Cross-review 摘要
    review_checks = cross_review_report.get("review_checks", [])
    review_focus_coverage = {
        check.get("check_name", f"check_{i:02d}"): check.get("result", "pass")
        for i, check in enumerate(review_checks, start=1)
    }
    remaining_warnings = [
        check.get("description", check.get("check_name", ""))
        for check in review_checks
        if check.get("result") == "warning"
    ]

    # 能力缺口汇总
    capability_gaps = _collect_all_capability_gaps(cross_review_report, fragments, build_ir)

    # fast_mode 标记
    fast_mode = session_meta.get("fast_mode", False)
    session_id = session_meta.get("session_id", "")
    run_id = session_meta.get("run_id", "")
    target_phase = session_meta.get("target_phase", "phase1_local_multiplayer")

    handoff_id = f"handoff.{project_name.lower()}.{run_id[:8] if run_id else session_id[:8]}"

    return {
        "handoff_meta": {
            "handoff_version": "3.0",
            "handoff_id": handoff_id,
            "schema_version": "3.0",
            "created_at": _now_iso(),
            "target_phase": target_phase,
            "build_goal": root_skill_contract.get("build_goal", "playable_template"),
            "fast_mode": fast_mode,
            "session_version": "2.0",
        },
        "project_context": {
            "project_name": project_name,
            "game_type": game_type,
            "subgenre": subgenre,
            "target_phase": target_phase,
            "source_contract_id": contract_id,
        },
        "clarification_summary": {
            "total_items": len(clarification_gate_report.get("items", [])),
            "decisions_breakdown": clarification_gate_report.get("items_by_decision_summary", {}),
            "provisional_chain": provisional_chain,
            "retained_clarifications": clarification_gate_report.get("retained_clarifications", []),
        },
        "skill_graph_summary": {
            "total_nodes": len(skill_graph.get("nodes", [])),
            "total_edges": len(skill_graph.get("edges", [])),
            "gameplay_skills": sum(1 for n in skill_graph.get("nodes", []) if n.get("domain_type") == "gameplay"),
            "baseline_skills": sum(1 for n in skill_graph.get("nodes", []) if n.get("domain_type") == "baseline"),
        },
        "selected_skill_instances": skill_instances,
        "design_space_summary": {
            "design_space_report": stage4_output.get("design_space_report", {}),
            "converged_realization_pack": stage4_output.get("converged_realization_pack", {}),
        },
        "reviewed_dynamic_spec_tree": cross_review_report.get("reviewed_dynamic_spec_tree", {}),
        "cross_review_summary": {
            "status": review_status,
            "issues_found": len(cross_review_report.get("issues_found", [])),
            "remaining_warnings": remaining_warnings,
            "review_focus_coverage": review_focus_coverage,
            "constraint_preservation": cross_review_report.get("constraint_preservation_summary", {}),
            "bp_thin_layer": cross_review_report.get("bp_thin_layer_summary", {}),
            "baseline_coverage": cross_review_report.get("baseline_coverage_summary", {}),
        },
        "lowering_summary": {
            "ir_id": ir_id,
            "families_bound": build_ir.get("lowering_report", {}).get("families_bound", []),
            "families_partially_bound": build_ir.get("lowering_report", {}).get("families_partially_bound", []),
            "unbound_requirements": build_ir.get("lowering_report", {}).get("unbound_requirements", []),
            "build_step_count": len(build_ir.get("build_steps", [])),
            "validation_point_count": len(build_ir.get("validation_ir", [])),
            "naming_resolution_summary": naming_resolution_log.get("summary", {}),
        },
        "build_ir": {
            "ir_id": ir_id,
            "build_steps": build_ir.get("build_steps", []),
            "inline": True,
        },
        "validation_ir": {
            "validations": build_ir.get("validation_ir", []),
            "inline": True,
        },
        "naming_resolution_log": {
            "entries": naming_resolution_log.get("entries", []),
            "inline": True,
        },
        "capability_gaps": capability_gaps,
        "approval": {
            "approval_status": review_status,
            "approver": "auto",
            "blocked_reasons": blocked_reasons,
            "fast_mode_warning": "fast_mode run 不可 promote" if fast_mode else None,
            "notes": "由 Compiler pipeline orchestrator v2 自动组装 Reviewed Handoff v3。",
        },
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.HandoffV3.v1",
            "source_contract_id": contract_id,
            "source_review_id": review_id,
            "source_ir_id": ir_id,
            "session_id": session_id,
            "run_id": run_id,
            "gdd_path": session_meta.get("gdd_path", ""),
        },
    }
