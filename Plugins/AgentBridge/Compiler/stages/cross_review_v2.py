"""
Cross-Domain Convergence Review v2 — Stage 5 (v2.0)

Phase 10 原有检查 + Phase 11 新增：
  - 跨域 realization 冲突检测
  - Constraint 保持性检查（Constraint Field 值在下游未被篡改）
  - Blueprint 薄层原则检查
  - Baseline 完整性检查
  - 设计连贯性评估
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Constraint 保持性检查
# ---------------------------------------------------------------------------

def check_constraint_preservation(
    root_skill_contract: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    验证所有 Fragment 中引用的 Constraint Field 值是否与 Root Skill Contract 一致。
    返回违反列表。
    """
    constraint_fields = root_skill_contract.get("constraint_fields", {})
    violations: List[Dict[str, Any]] = []

    for fragment in fragments:
        instance_id = fragment.get("skill_instance_id", "")
        spec_fragments = fragment.get("spec_fragments", {})

        for family_name, spec in spec_fragments.items():
            if not isinstance(spec, dict):
                continue
            # 检查 spec 中是否引用了 constraint 字段且值不一致
            for field_path, constraint_def in constraint_fields.items():
                field_key = field_path.split(".")[-1]
                if field_key in spec:
                    expected = constraint_def.get("value")
                    actual = spec[field_key]
                    if expected is not None and actual != expected:
                        violations.append({
                            "check_type": "constraint_preservation",
                            "severity": "error",
                            "fragment_id": instance_id,
                            "family": family_name,
                            "field": field_path,
                            "expected": expected,
                            "actual": actual,
                            "message": f"Constraint '{field_path}' 在 {instance_id}/{family_name} 中被修改: "
                                       f"期望 {expected}, 实际 {actual}",
                        })

    return violations


# ---------------------------------------------------------------------------
# Blueprint 薄层原则检查
# ---------------------------------------------------------------------------

def check_blueprint_thin_layer(
    fragments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    检查 Fragment 中是否有违反 Blueprint 薄层原则的指标。
    返回警告列表。
    """
    warnings: List[Dict[str, Any]] = []

    for fragment in fragments:
        instance_id = fragment.get("skill_instance_id", "")
        design_log = fragment.get("design_decision_log", [])

        for decision in design_log:
            # 检查决策是否涉及把逻辑放入 Blueprint
            chosen = str(decision.get("chosen", "")).lower()
            if "blueprint" in chosen and any(
                kw in chosen for kw in ["逻辑", "logic", "计算", "calculation", "状态机", "state machine"]
            ):
                warnings.append({
                    "check_type": "bp_thickness_warning",
                    "severity": "warning",
                    "fragment_id": instance_id,
                    "decision_id": decision.get("decision_id", ""),
                    "message": f"决策 '{decision.get('topic', '')}' 可能违反 Blueprint 薄层原则: "
                               f"'{decision.get('chosen', '')}' 涉及在 Blueprint 中实现逻辑",
                })

    return warnings


# ---------------------------------------------------------------------------
# Baseline 完整性检查
# ---------------------------------------------------------------------------

REQUIRED_BASELINE_FAMILIES = [
    "start_screen_spec",
    "main_menu_spec",
    "settings_spec",
    "pause_menu_spec",
    "results_spec",
    "hud_spec",
]


def check_baseline_completeness(
    fragments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """检查是否所有必需 Baseline 项都有对应 Fragment。"""
    emitted_families = set()
    for fragment in fragments:
        for family in fragment.get("emitted_families", []):
            emitted_families.add(family)

    missing: List[Dict[str, Any]] = []
    for family in REQUIRED_BASELINE_FAMILIES:
        if family not in emitted_families:
            missing.append({
                "check_type": "baseline_completeness",
                "severity": "warning",
                "family": family,
                "message": f"必需 Baseline 项 '{family}' 缺少对应 Fragment",
            })

    return missing


# ---------------------------------------------------------------------------
# 跨域 Realization 冲突检测
# ---------------------------------------------------------------------------

def check_cross_domain_conflicts(
    converged_realization_pack: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """检查收敛结果中跨维度的一致性冲突。"""
    conflicts: List[Dict[str, Any]] = []

    consistency = converged_realization_pack.get("cross_dimension_consistency", {})
    for conflict in consistency.get("conflicts", []):
        conflicts.append({
            "check_type": "cross_domain_realization_conflict",
            "severity": "warning",
            "dimensions": conflict.get("dimensions", []),
            "message": conflict.get("description", "跨域 realization 冲突"),
        })

    return conflicts


# ---------------------------------------------------------------------------
# Phase 边界检查
# ---------------------------------------------------------------------------

def check_phase_scope(
    fragments: List[Dict[str, Any]],
    phase_scope: str,
) -> Dict[str, Any]:
    """检查所有 Fragment 是否在 Phase 边界内。"""
    violations: List[str] = []

    for fragment in fragments:
        instance_id = fragment.get("skill_instance_id", "")
        # 检查 fragment 的 phase_scope 是否匹配
        fragment_scope = fragment.get("metadata", {}).get("phase_scope", phase_scope)
        if fragment_scope != phase_scope and fragment_scope != "":
            violations.append(
                f"{instance_id}: fragment phase_scope '{fragment_scope}' != session '{phase_scope}'"
            )

    return {
        "in_scope_confirmed": len(violations) == 0,
        "out_of_scope_violations": violations,
    }


# ---------------------------------------------------------------------------
# 主入口：生成 Cross-Review Report v2
# ---------------------------------------------------------------------------

def create_cross_review_report_v2(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    skill_graph: Dict[str, Any],
    stage4_output: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, Any]:
    """
    Stage 5 v2.0: 生成 Cross-Domain Convergence Review Report。

    输入: 全部前序产物
    输出: cross_review_report v2 (含 reviewed_dynamic_spec_tree)
    """
    fragments = stage4_output.get("skill_fragments", [])
    converged_pack = stage4_output.get("converged_realization_pack", {})

    # 执行全部检查
    all_issues: List[Dict[str, Any]] = []

    # 1. Constraint 保持性
    constraint_issues = check_constraint_preservation(root_skill_contract, fragments)
    all_issues.extend(constraint_issues)

    # 2. Blueprint 薄层
    bp_issues = check_blueprint_thin_layer(fragments)
    all_issues.extend(bp_issues)

    # 3. Baseline 完整性
    baseline_issues = check_baseline_completeness(fragments)
    all_issues.extend(baseline_issues)

    # 4. 跨域冲突
    cross_domain_issues = check_cross_domain_conflicts(converged_pack)
    all_issues.extend(cross_domain_issues)

    # 5. Phase 边界
    phase_check = check_phase_scope(fragments, phase_scope)

    # 构建 reviewed_dynamic_spec_tree（合并所有 fragments）
    spec_tree: Dict[str, Any] = {}
    input_fragment_ids: List[str] = []
    for fragment in fragments:
        fid = fragment.get("skill_instance_id", "")
        input_fragment_ids.append(fid)
        for family, spec in fragment.get("spec_fragments", {}).items():
            spec_tree[family] = spec

    # 构建 review_checks
    review_checks: List[Dict[str, Any]] = []

    review_checks.append({
        "check_name": "constraint_preservation",
        "result": "pass" if not constraint_issues else "fail",
        "issues_count": len(constraint_issues),
        "description": "Constraint Field 值在下游 Fragment 中保持不变",
    })

    review_checks.append({
        "check_name": "blueprint_thin_layer",
        "result": "pass" if not bp_issues else "warning",
        "issues_count": len(bp_issues),
        "description": "核心逻辑在 C++，Blueprint 仅承载薄层",
    })

    review_checks.append({
        "check_name": "baseline_completeness",
        "result": "pass" if not baseline_issues else "warning",
        "issues_count": len(baseline_issues),
        "description": "所有必需 Baseline 项都有 Fragment",
    })

    review_checks.append({
        "check_name": "cross_domain_consistency",
        "result": "pass" if not cross_domain_issues else "warning",
        "issues_count": len(cross_domain_issues),
        "description": "跨域 Realization 选择互相兼容",
    })

    review_checks.append({
        "check_name": "phase_scope",
        "result": "pass" if phase_check["in_scope_confirmed"] else "fail",
        "issues_count": len(phase_check["out_of_scope_violations"]),
        "description": "所有 Fragment 在当前 Phase 边界内",
    })

    # 综合判定
    has_errors = any(c["result"] == "fail" for c in review_checks)
    has_warnings = any(c["result"] == "warning" for c in review_checks)

    if has_errors:
        review_status = "blocked"
    elif has_warnings:
        review_status = "approved_with_warnings"
    else:
        review_status = "approved"

    # 能力缺口
    capability_gaps: List[str] = []
    for fragment in fragments:
        for gap in fragment.get("capability_gaps", []):
            if isinstance(gap, str):
                capability_gaps.append(gap)
            elif isinstance(gap, dict):
                capability_gaps.append(gap.get("description", str(gap)))

    contract_id = root_skill_contract.get("contract_id", "")
    review_id = f"cr.{contract_id.replace('rsc.', '')}" if contract_id else f"cr.review.{_now_iso()[:10]}"

    return {
        "review_id": review_id,
        "review_version": "v2",
        "source_contract_id": contract_id,
        "input_fragment_ids": input_fragment_ids,
        "review_status": review_status,
        "review_checks": review_checks,
        "issues_found": all_issues,
        "phase_scope_check": phase_check,
        "constraint_preservation_summary": {
            "total_constraints": len(root_skill_contract.get("constraint_fields", {})),
            "violations": len(constraint_issues),
            "status": "preserved" if not constraint_issues else "violated",
        },
        "bp_thin_layer_summary": {
            "warnings": len(bp_issues),
            "status": "clean" if not bp_issues else "review_needed",
        },
        "baseline_coverage_summary": {
            "required": len(REQUIRED_BASELINE_FAMILIES),
            "present": len(REQUIRED_BASELINE_FAMILIES) - len(baseline_issues),
            "missing": [i["family"] for i in baseline_issues],
        },
        "reviewed_dynamic_spec_tree": spec_tree,
        "capability_gap_list": capability_gaps,
        "lowering_ready": review_status != "blocked",
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.CrossReviewV2.v1",
            "phase_scope": phase_scope,
        },
    }
