"""
Cross Review v2 - Stage 5 (v2.0)

职责：
  - 对 Stage 4 产物做统一审查
  - 检查 Constraint 保持性、Blueprint 薄层原则、Baseline 覆盖情况
  - 检查跨域 naming / realization 冲突
  - 产出 reviewed_dynamic_spec_tree，供 Lowering v2 使用
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple


# Baseline capability 到 spec family 的稳定映射。
# Phase 11 当前阶段先使用固定映射，避免把 baseline 语义散落到多处。
BASELINE_CAPABILITY_TO_FAMILY: Dict[str, str] = {
    "baseline-start-screen": "start_screen_spec",
    "baseline-main-menu": "main_menu_spec",
    "baseline-settings": "settings_spec",
    "baseline-pause": "pause_spec",
    "baseline-results": "results_spec",
    "baseline-hud": "hud_spec",
    "baseline-input-foundation": "input_foundation_spec",
    "baseline-audio-foundation": "audio_foundation_spec",
    "baseline-platform-foundation": "platform_foundation_spec",
}

# Monopoly Phase 11 当前 required gameplay 能力到 family 的稳定映射。
GAMEPLAY_CAPABILITY_TO_FAMILY: Dict[str, str] = {
    "gameplay-board-topology": "board_topology_spec",
    "gameplay-tile-system": "tile_system_spec",
    "gameplay-turn-loop": "turn_flow_spec",
    "gameplay-dice": "dice_rule_spec",
    "gameplay-economy": "property_economy_spec",
    "gameplay-player-management": "player_management_spec",
    "gameplay-jail": "jail_rule_spec",
}

LOGIC_KEYWORDS = (
    "logic",
    "规则",
    "回合",
    "状态机",
    "calculation",
    "计算",
    "经济",
    "bankruptcy",
    "jail",
    "turn",
)


def _now_iso() -> str:
    """返回 UTC ISO 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def _collect_fragments(stage4_output: Dict[str, Any]) -> List[Dict[str, Any]]:
    """统一读取 Stage 4 fragments。"""
    fragments = stage4_output.get("skill_fragments", [])
    return fragments if isinstance(fragments, list) else []


def _iter_fragment_families(fragments: List[Dict[str, Any]]) -> Iterable[Tuple[Dict[str, Any], str, Dict[str, Any]]]:
    """遍历 fragment 中的所有 family/spec。"""
    for fragment in fragments:
        spec_fragments = fragment.get("spec_fragments", {})
        if not isinstance(spec_fragments, dict):
            continue
        for family_name, spec in spec_fragments.items():
            if isinstance(spec, dict):
                yield fragment, family_name, spec


def _lookup_path_value(data: Dict[str, Any], dotted_path: str) -> Any:
    """按 board.tile_count 这种路径读取嵌套值；找不到时返回 None。"""
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _lookup_constraint_value(spec: Dict[str, Any], field_path: str) -> Any:
    """
    在 spec 中查找 constraint 对应字段。

    当前 fragment 里既可能保留嵌套结构，也可能把字段摊平成 tile_count 这种形式，
    所以这里先尝试完整路径，再尝试最后一个 token。
    """
    value = _lookup_path_value(spec, field_path)
    if value is not None:
        return value
    leaf_key = field_path.split(".")[-1]
    return spec.get(leaf_key)


def check_constraint_preservation(
    root_skill_contract: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """检查 fragment 是否擅自改写了 Root Skill Contract 的 Constraint。"""
    constraint_fields = root_skill_contract.get("constraint_fields", {})
    issues: List[Dict[str, Any]] = []
    checked_fields = 0

    for fragment, family_name, spec in _iter_fragment_families(fragments):
        fragment_id = fragment.get("skill_instance_id", "")
        for field_path, constraint_def in constraint_fields.items():
            expected_value = constraint_def.get("value")
            actual_value = _lookup_constraint_value(spec, field_path)
            if actual_value is None:
                continue

            checked_fields += 1
            if actual_value != expected_value:
                issues.append(
                    {
                        "issue_id": f"issue.constraint.{fragment_id}.{family_name}.{checked_fields}",
                        "check_type": "constraint_preservation",
                        "severity": "blocker",
                        "fragment_id": fragment_id,
                        "family": family_name,
                        "field_path": field_path,
                        "expected": expected_value,
                        "actual": actual_value,
                        "message": (
                            f"Constraint 字段 {field_path} 在 {fragment_id}/{family_name} 中被改写，"
                            f"期望 {expected_value!r}，实际 {actual_value!r}"
                        ),
                    }
                )

    summary = {
        "total_constraints": len(constraint_fields),
        "checked_fields": checked_fields,
        "violations": len(issues),
        "preserved_count": max(checked_fields - len(issues), 0),
        "status": "preserved" if not issues else "violated",
    }
    return issues, summary


def check_blueprint_thin_layer(fragments: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """用保守启发式检查是否出现“把逻辑塞进 Blueprint”的信号。"""
    issues: List[Dict[str, Any]] = []
    suspect_fragments = set()

    for fragment in fragments:
        fragment_id = fragment.get("skill_instance_id", "")
        decisions = fragment.get("design_decision_log", [])
        if not isinstance(decisions, list):
            continue

        for index, decision in enumerate(decisions, start=1):
            text = " ".join(
                str(decision.get(key, ""))
                for key in ("topic", "context", "chosen", "rationale")
            ).lower()
            if "blueprint" not in text:
                continue
            if not any(keyword in text for keyword in LOGIC_KEYWORDS):
                continue

            suspect_fragments.add(fragment_id)
            issues.append(
                {
                    "issue_id": f"issue.bp_thin_layer.{fragment_id}.{index}",
                    "check_type": "bp_thickness_warning",
                    "severity": "warning",
                    "fragment_id": fragment_id,
                    "message": (
                        f"{fragment_id} 的设计决策可能把核心逻辑放进 Blueprint："
                        f"{decision.get('chosen', '')}"
                    ),
                }
            )

    summary = {
        "warnings": len(issues),
        "suspect_fragments": sorted(suspect_fragments),
        "status": "clean" if not issues else "review_needed",
    }
    return issues, summary


def _expected_baseline_families(root_skill_contract: Dict[str, Any]) -> List[str]:
    """从 Root Skill Contract 计算应当出现的 required baseline families。"""
    families: List[str] = []
    for capability in root_skill_contract.get("baseline_capabilities", []):
        if capability.get("activation") != "required":
            continue
        family = BASELINE_CAPABILITY_TO_FAMILY.get(capability.get("capability_id", ""))
        if family:
            families.append(family)
    return sorted(set(families))


def _expected_required_gameplay_families(root_skill_contract: Dict[str, Any]) -> List[str]:
    """从 Root Skill Contract 计算最小可玩闭环 required gameplay families。"""
    families: List[str] = []
    for capability in root_skill_contract.get("gameplay_capabilities", []):
        if capability.get("activation") != "required":
            continue
        family = GAMEPLAY_CAPABILITY_TO_FAMILY.get(capability.get("capability_id", ""))
        if family:
            families.append(family)
    return sorted(set(families))


def check_baseline_completeness(
    root_skill_contract: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """检查 required baseline families 是否都已被 fragment 发出。缺失视为 blocker。"""
    expected_families = _expected_baseline_families(root_skill_contract)
    emitted_families = {
        family
        for fragment in fragments
        for family in fragment.get("emitted_families", [])
        if isinstance(family, str)
    }

    issues: List[Dict[str, Any]] = []
    missing_families: List[str] = []
    for family in expected_families:
        if family in emitted_families:
            continue
        missing_families.append(family)
        issues.append(
            {
                "issue_id": f"issue.baseline.{family}",
                "check_type": "baseline_completeness",
                "severity": "blocker",
                "family": family,
                "message": f"缺少 required baseline family: {family}",
            }
        )

    summary = {
        "required": len(expected_families),
        "present": len(expected_families) - len(missing_families),
        "missing": missing_families,
        "status": "complete" if not missing_families else "incomplete",
    }
    return issues, summary


def check_minimum_playability_completeness(
    root_skill_contract: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """检查最小可玩闭环 required gameplay families 是否都已被 fragment 发出。"""
    expected_families = _expected_required_gameplay_families(root_skill_contract)
    emitted_families = {
        family
        for fragment in fragments
        for family in fragment.get("emitted_families", [])
        if isinstance(family, str)
    }

    issues: List[Dict[str, Any]] = []
    missing_families: List[str] = []
    for family in expected_families:
        if family in emitted_families:
            continue
        missing_families.append(family)
        issues.append(
            {
                "issue_id": f"issue.minimum_playability.{family}",
                "check_type": "minimum_playability",
                "severity": "blocker",
                "family": family,
                "message": f"缺少最小可玩闭环 required gameplay family: {family}",
            }
        )

    summary = {
        "required": len(expected_families),
        "present": len(expected_families) - len(missing_families),
        "missing": missing_families,
        "status": "complete" if not missing_families else "incomplete",
    }
    return issues, summary


def check_cross_domain_conflicts(
    converged_realization_pack: Dict[str, Any],
    fragments: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """检查跨域 naming / realization 冲突。"""
    issues: List[Dict[str, Any]] = []

    # 1. realization 冲突：直接读取 convergence 的一致性检查结果。
    consistency = converged_realization_pack.get("cross_dimension_consistency", {})
    realization_conflicts = consistency.get("conflicts", [])
    for index, conflict in enumerate(realization_conflicts, start=1):
        issues.append(
            {
                "issue_id": f"issue.realization_conflict.{index}",
                "check_type": "cross_domain_realization_conflict",
                "severity": "warning",
                "dimensions": conflict.get("dimensions", []),
                "message": conflict.get("description", "发现跨域 realization 冲突"),
            }
        )

    # 2. naming 冲突：多个 fragment 输出同一个 family，Lowering 会无法稳定落名。
    family_to_fragments: Dict[str, List[str]] = defaultdict(list)
    for fragment in fragments:
        fragment_id = fragment.get("skill_instance_id", "")
        for family in fragment.get("emitted_families", []):
            if isinstance(family, str):
                family_to_fragments[family].append(fragment_id)

    naming_conflicts = []
    for family, owners in sorted(family_to_fragments.items()):
        if len(owners) <= 1:
            continue
        naming_conflicts.append({"family": family, "owners": owners})
        issues.append(
            {
                "issue_id": f"issue.naming_conflict.{family}",
                "check_type": "cross_domain_naming_conflict",
                "severity": "warning",
                "family": family,
                "message": f"family {family} 被多个 fragment 同时发出：{', '.join(owners)}",
            }
        )

    summary = {
        "realization_conflicts": len(realization_conflicts),
        "naming_conflicts": len(naming_conflicts),
        "naming_conflict_families": [item["family"] for item in naming_conflicts],
        "status": "clean" if not issues else "review_needed",
    }
    return issues, summary


def check_phase_scope(
    fragments: List[Dict[str, Any]],
    phase_scope: str,
) -> Dict[str, Any]:
    """检查 fragment 是否超出当前 Phase 边界。"""
    violations: List[str] = []
    for fragment in fragments:
        fragment_id = fragment.get("skill_instance_id", "")
        fragment_scope = fragment.get("phase_scope", "")
        if fragment_scope and fragment_scope != phase_scope:
            violations.append(
                f"{fragment_id}: fragment.phase_scope={fragment_scope}, session.target_phase={phase_scope}"
            )
    return {
        "in_scope_confirmed": len(violations) == 0,
        "out_of_scope_violations": violations,
    }


def _build_reviewed_dynamic_spec_tree(
    fragments: List[Dict[str, Any]],
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], List[Dict[str, Any]]]:
    """
    构造 reviewed_dynamic_spec_tree，同时保留 family 来源映射。

    Lowering v2 需要知道每个 family 来自哪个 skill instance，
    这样才能稳定生成 build step 与命名日志。
    """
    spec_tree: Dict[str, Any] = {}
    family_source_map: Dict[str, Dict[str, Any]] = {}
    overwrite_issues: List[Dict[str, Any]] = []

    for fragment, family_name, spec in _iter_fragment_families(fragments):
        fragment_id = fragment.get("skill_instance_id", "")
        if family_name in spec_tree:
            overwrite_issues.append(
                {
                    "issue_id": f"issue.family_overwrite.{family_name}",
                    "check_type": "cross_domain_naming_conflict",
                    "severity": "warning",
                    "family": family_name,
                    "message": f"family {family_name} 被重复写入，后写入 fragment={fragment_id} 覆盖前值",
                }
            )

        spec_tree[family_name] = spec
        family_source_map[family_name] = {
            "skill_instance_id": fragment_id,
            "template_id": fragment.get("template_id", ""),
            "domain_type": fragment.get("domain_type", ""),
            "status": fragment.get("status", ""),
        }

    return spec_tree, family_source_map, overwrite_issues


def _collect_capability_gaps(fragments: List[Dict[str, Any]]) -> List[str]:
    """统一拉平 capability gaps。"""
    capability_gaps: List[str] = []
    for fragment in fragments:
        for gap in fragment.get("capability_gaps", []):
            if isinstance(gap, str):
                capability_gaps.append(gap)
            elif isinstance(gap, dict):
                capability_gaps.append(gap.get("description", str(gap)))
    return capability_gaps


def _summarize_design_decisions(fragments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """统计 design_decision_log，用于 review 和后续 handoff。"""
    decisions = []
    provisional_count = 0
    high_impact_count = 0
    by_skill = Counter()

    for fragment in fragments:
        fragment_id = fragment.get("skill_instance_id", "")
        for decision in fragment.get("design_decision_log", []):
            decisions.append(decision)
            by_skill[fragment_id] += 1
            if decision.get("provisional"):
                provisional_count += 1
            if decision.get("impact") == "high":
                high_impact_count += 1

    return {
        "total_decisions": len(decisions),
        "provisional_decisions": provisional_count,
        "high_impact_decisions": high_impact_count,
        "by_skill_instance": dict(sorted(by_skill.items())),
    }


def create_cross_review_report_v2(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    skill_graph: Dict[str, Any],
    stage4_output: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, Any]:
    """生成 Cross Review Report v2。"""
    fragments = _collect_fragments(stage4_output)
    converged_pack = stage4_output.get("converged_realization_pack", {})
    contract_id = root_skill_contract.get("contract_id", "")
    gate_id = clarification_gate_report.get("gate_id", clarification_gate_report.get("source_contract_id", ""))
    graph_id = skill_graph.get("graph_id", "")

    constraint_issues, constraint_summary = check_constraint_preservation(root_skill_contract, fragments)
    bp_issues, bp_summary = check_blueprint_thin_layer(fragments)
    baseline_issues, baseline_summary = check_baseline_completeness(root_skill_contract, fragments)
    playability_issues, _playability_summary = check_minimum_playability_completeness(root_skill_contract, fragments)
    cross_domain_issues, cross_domain_summary = check_cross_domain_conflicts(converged_pack, fragments)
    phase_scope_check = check_phase_scope(fragments, phase_scope)
    spec_tree, family_source_map, overwrite_issues = _build_reviewed_dynamic_spec_tree(fragments)

    all_issues = (
        constraint_issues
        + bp_issues
        + baseline_issues
        + playability_issues
        + cross_domain_issues
        + overwrite_issues
    )

    phase_scope_issues: List[Dict[str, Any]] = []
    for index, violation in enumerate(phase_scope_check.get("out_of_scope_violations", []), start=1):
        phase_scope_issues.append(
            {
                "issue_id": f"issue.phase_scope.{index}",
                "check_type": "phase_scope",
                "severity": "blocker",
                "message": violation,
            }
        )
    all_issues.extend(phase_scope_issues)

    review_checks = [
        {
            "check_id": "crv2_constraint_preservation",
            "check_name": "constraint_preservation",
            "result": "pass" if not constraint_issues else "fail",
            "issues_count": len(constraint_issues),
            "description": "Constraint Field 在下游 fragment 中保持不变。",
        },
        {
            "check_id": "crv2_blueprint_thin_layer",
            "check_name": "blueprint_thin_layer",
            "result": "pass" if not bp_issues else "warning",
            "issues_count": len(bp_issues),
            "description": "核心玩法逻辑应落在 C++，Blueprint 只承担薄层桥接。",
        },
        {
            "check_id": "crv2_baseline_coverage",
            "check_name": "baseline_coverage",
            "result": "pass" if not baseline_issues else "fail",
            "issues_count": len(baseline_issues),
            "description": "required baseline families 应全部出现。",
        },
        {
            "check_id": "crv2_minimum_playability",
            "check_name": "minimum_playability",
            "result": "pass" if not playability_issues else "fail",
            "issues_count": len(playability_issues),
            "description": "最小可玩闭环 required gameplay families 应全部出现。",
        },
        {
            "check_id": "crv2_cross_domain_conflict",
            "check_name": "cross_domain_conflict",
            "result": "pass" if not cross_domain_issues and not overwrite_issues else "warning",
            "issues_count": len(cross_domain_issues) + len(overwrite_issues),
            "description": "检测跨域 naming / realization 冲突。",
        },
        {
            "check_id": "crv2_phase_scope",
            "check_name": "phase_scope",
            "result": "pass" if phase_scope_check["in_scope_confirmed"] else "fail",
            "issues_count": len(phase_scope_issues),
            "description": "所有 fragment 必须处于当前 phase scope 内。",
        },
    ]

    has_blocker = any(check["result"] == "fail" for check in review_checks)
    has_warning = any(check["result"] == "warning" for check in review_checks)
    if has_blocker:
        review_status = "blocked"
    elif has_warning:
        review_status = "approved_with_warnings"
    else:
        review_status = "approved"

    design_decision_summary = _summarize_design_decisions(fragments)
    capability_gaps = _collect_capability_gaps(fragments)
    input_fragment_ids = [fragment.get("skill_instance_id", "") for fragment in fragments if fragment.get("skill_instance_id")]
    review_id = (
        f"cr.{contract_id.replace('rsc.', '')}"
        if contract_id
        else f"cr.review.{_now_iso()[:10]}"
    )

    return {
        "review_id": review_id,
        "review_version": "v2",
        "source_contract_id": contract_id,
        "source_gate_id": gate_id,
        "source_graph_id": graph_id,
        "input_fragment_ids": input_fragment_ids,
        "review_status": review_status,
        "review_checks": review_checks,
        "issues_found": all_issues,
        "phase_scope_check": phase_scope_check,
        "constraint_preservation_summary": constraint_summary,
        "bp_thin_layer_summary": bp_summary,
        "baseline_coverage_summary": baseline_summary,
        "cross_domain_conflict_summary": cross_domain_summary,
        "design_decision_log_summary": design_decision_summary,
        "family_source_map": family_source_map,
        "reviewed_dynamic_spec_tree": spec_tree,
        "capability_gap_list": capability_gaps,
        "provisional_items": clarification_gate_report.get("provisional_items", []),
        "lowering_ready": review_status != "blocked",
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.CrossReviewV2.v2",
            "phase_scope": phase_scope,
        },
    }
