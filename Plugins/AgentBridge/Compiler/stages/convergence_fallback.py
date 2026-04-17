"""
Phase 11 Convergence Engine.

职责：
  - 从 realization_candidates 中为每个设计维度选择一个候选方向
  - 选择必须基于显式比较，而不是预设偏好直选
  - 输出 rationale、rejected_alternatives 与跨维度一致性检查
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple


COMPONENT_LABELS = {
    "bounds_fit": "边界满足度",
    "coupling_fit": "耦合对齐度",
    "phase_fit": "阶段贴合度",
    "risk_fit": "风险控制度",
    "complexity_fit": "实现复杂度",
}


def _selection_signals(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """读取候选的选择信号。"""
    return candidate.get("selection_signals", {})


def _principle(candidate: Dict[str, Any]) -> str:
    """读取候选生成原则。"""
    return _selection_signals(candidate).get("generation_principle", candidate.get("candidate_key", "balanced"))


def _bounds_fit(candidate: Dict[str, Any]) -> float:
    """候选是否满足 Variant bounds。"""
    return 1.0 if candidate.get("satisfies_bounds", False) else 0.0


def _coupling_fit(candidate_group: Dict[str, Any], candidate: Dict[str, Any]) -> float:
    """根据耦合密度评估候选适配度。"""
    principle = _principle(candidate)
    has_coupling = bool(candidate_group.get("coupled_dimensions", []))
    if has_coupling:
        return {
            "coupling_first": 1.0,
            "balanced": 0.9,
            "constraint_first": 0.8,
            "expressive": 0.65,
        }.get(principle, 0.8)
    return {
        "balanced": 0.92,
        "expressive": 0.88,
        "constraint_first": 0.84,
        "coupling_first": 0.8,
    }.get(principle, 0.82)


def _phase_fit(node: Dict[str, Any], candidate_group: Dict[str, Any], candidate: Dict[str, Any], phase_scope: str) -> float:
    """评估候选与当前阶段的贴合度。"""
    del phase_scope  # 当前阶段仍是 Phase 1 原型导向，先保留接口，便于后续扩展。
    principle = _principle(candidate)
    design_freedom = candidate_group.get("design_freedom", "medium")
    domain_type = node.get("domain_type", "gameplay")

    if domain_type == "baseline":
        return {
            "balanced": 1.0,
            "constraint_first": 0.96,
            "coupling_first": 0.92,
            "expressive": 0.7,
        }.get(principle, 0.85)

    if design_freedom == "high":
        return {
            "balanced": 1.0,
            "expressive": 0.9,
            "coupling_first": 0.9,
            "constraint_first": 0.88,
        }.get(principle, 0.85)

    return {
        "balanced": 1.0,
        "coupling_first": 0.96,
        "constraint_first": 0.94,
        "expressive": 0.74,
    }.get(principle, 0.85)


def _risk_fit(node: Dict[str, Any], candidate_group: Dict[str, Any], candidate: Dict[str, Any]) -> float:
    """如果节点仍受 clarification 或耦合风险影响，优先更保守的候选。"""
    principle = _principle(candidate)
    has_gate_pressure = bool(node.get("gated_by_clarification_items", [])) or bool(candidate_group.get("source_clarification_items", []))
    if has_gate_pressure:
        return {
            "constraint_first": 1.0,
            "coupling_first": 0.95,
            "balanced": 0.8,
            "expressive": 0.55,
        }.get(principle, 0.75)
    return {
        "balanced": 0.95,
        "constraint_first": 0.9,
        "coupling_first": 0.88,
        "expressive": 0.84,
    }.get(principle, 0.82)


def _complexity_fit(candidate: Dict[str, Any]) -> float:
    """当前阶段偏向低到中等复杂度。"""
    complexity = candidate.get("estimated_complexity", "medium")
    return {
        "low": 1.0,
        "medium": 0.82,
        "high": 0.58,
    }.get(complexity, 0.75)


def _score_candidate(
    node: Dict[str, Any],
    candidate_group: Dict[str, Any],
    candidate: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, float]:
    """生成候选评分明细。"""
    score_breakdown = {
        "bounds_fit": _bounds_fit(candidate),
        "coupling_fit": _coupling_fit(candidate_group, candidate),
        "phase_fit": _phase_fit(node, candidate_group, candidate, phase_scope),
        "risk_fit": _risk_fit(node, candidate_group, candidate),
        "complexity_fit": _complexity_fit(candidate),
    }
    score_breakdown["total"] = round(
        score_breakdown["bounds_fit"] * 0.35
        + score_breakdown["coupling_fit"] * 0.2
        + score_breakdown["phase_fit"] * 0.2
        + score_breakdown["risk_fit"] * 0.15
        + score_breakdown["complexity_fit"] * 0.1,
        4,
    )
    return score_breakdown


def _best_components(score_breakdown: Dict[str, float], top_n: int = 2) -> List[str]:
    """返回分数最高的几个组件名。"""
    components = [
        (name, value)
        for name, value in score_breakdown.items()
        if name != "total"
    ]
    components.sort(key=lambda item: (-item[1], item[0]))
    return [item[0] for item in components[:top_n]]


def _worst_component(score_breakdown: Dict[str, float]) -> str:
    """返回分数最低的组件名。"""
    components = [
        (name, value)
        for name, value in score_breakdown.items()
        if name != "total"
    ]
    components.sort(key=lambda item: (item[1], item[0]))
    return components[0][0] if components else "phase_fit"


def _build_rationale(
    candidate_group: Dict[str, Any],
    chosen_candidate: Dict[str, Any],
    chosen_scores: Dict[str, float],
    runner_up_scores: Dict[str, float] | None,
) -> str:
    """根据评分结果生成收敛理由。"""
    dimension_name = candidate_group.get("dimension_name", candidate_group.get("dimension_id", "当前维度"))
    best_components = _best_components(chosen_scores)
    component_text = "、".join(COMPONENT_LABELS.get(name, name) for name in best_components)
    margin_text = ""
    if runner_up_scores:
        margin = round(chosen_scores["total"] - runner_up_scores["total"], 3)
        margin_text = f"；相对次优方案保有 {margin:.3f} 的总分优势"
    return (
        f"{dimension_name} 选择 {chosen_candidate.get('name', '')}，"
        f"因为它在 {component_text} 上更贴合当前节点与阶段目标{margin_text}。"
    )


def _build_rejections(
    chosen_candidate: Dict[str, Any],
    candidate_group: Dict[str, Any],
    scored_candidates: List[Tuple[Dict[str, Any], Dict[str, float]]],
) -> List[Dict[str, str]]:
    """为未选中的候选生成拒绝理由。"""
    rejections: List[Dict[str, str]] = []
    chosen_total = next(
        scores["total"]
        for candidate, scores in scored_candidates
        if candidate.get("candidate_id") == chosen_candidate.get("candidate_id")
    )
    for candidate, scores in scored_candidates:
        if candidate.get("candidate_id") == chosen_candidate.get("candidate_id"):
            continue
        weakest_component = _worst_component(scores)
        rejection_reason = (
            f"{candidate.get('name', '')} 在 {COMPONENT_LABELS.get(weakest_component, weakest_component)} 上更弱，"
            f"总分 {scores['total']:.3f} 低于已选方案的 {chosen_total:.3f}。"
        )
        rejections.append(
            {
                "candidate_id": candidate.get("candidate_id", ""),
                "rejection_reason": rejection_reason,
            }
        )
    return rejections


def _pick_candidate(
    node: Dict[str, Any],
    candidate_group: Dict[str, Any],
    phase_scope: str,
) -> Tuple[Dict[str, Any], Dict[str, float], List[Tuple[Dict[str, Any], Dict[str, float]]]]:
    """从候选组中选出总分最高的候选。"""
    scored_candidates: List[Tuple[Dict[str, Any], Dict[str, float]]] = []
    for candidate in candidate_group.get("candidates", []):
        scored_candidates.append(
            (
                candidate,
                _score_candidate(node, candidate_group, candidate, phase_scope),
            )
        )

    scored_candidates.sort(
        key=lambda item: (
            -item[1]["total"],
            item[0].get("candidate_id", ""),
        )
    )
    if not scored_candidates:
        return {}, {}, []
    chosen_candidate, chosen_scores = scored_candidates[0]
    return chosen_candidate, chosen_scores, scored_candidates


def _consistency_conflicts(
    chosen_by_dimension: Dict[str, Dict[str, Any]],
    candidate_groups: Dict[str, Dict[str, Any]],
) -> Tuple[List[str], List[str]]:
    """对已收敛的维度执行轻量跨维度一致性检查。"""
    conflicts: List[str] = []
    involved_dimensions: List[str] = []
    visited_pairs = set()

    for dimension_id, chosen_candidate in chosen_by_dimension.items():
        group = candidate_groups.get(dimension_id, {})
        for coupled_dimension in group.get("coupled_dimensions", []):
            if coupled_dimension not in chosen_by_dimension:
                continue
            pair_key = tuple(sorted([dimension_id, coupled_dimension]))
            if pair_key in visited_pairs:
                continue
            visited_pairs.add(pair_key)

            left_signals = _selection_signals(chosen_candidate)
            right_signals = _selection_signals(chosen_by_dimension[coupled_dimension])
            aggressiveness_gap = abs(left_signals.get("aggressiveness", 1) - right_signals.get("aggressiveness", 1))
            coordination_gap = abs(left_signals.get("coordination_bias", 1) - right_signals.get("coordination_bias", 1))

            if aggressiveness_gap >= 2 and coordination_gap >= 1:
                left_name = group.get("dimension_name", dimension_id)
                right_name = candidate_groups.get(coupled_dimension, {}).get("dimension_name", coupled_dimension)
                conflicts.append(
                    f"{left_name} 与 {right_name} 的收敛姿态差异过大，需人工确认是否还能保持统一体验。"
                )
                involved_dimensions.extend([dimension_id, coupled_dimension])

    return conflicts, list(dict.fromkeys(involved_dimensions))


def create_converged_realization_pack(
    node: Dict[str, Any],
    realization_candidates: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, Any]:
    """为单个 Skill Instance 生成基于评分比较的 converged realization pack。"""
    generated_at = datetime.now(timezone.utc).isoformat()
    provisional = bool(node.get("gated_by_clarification_items"))
    converged_choices: List[Dict[str, Any]] = []
    chosen_by_dimension: Dict[str, Dict[str, Any]] = {}
    candidate_group_map = {
        candidate_group.get("dimension_id", ""): candidate_group
        for candidate_group in realization_candidates.get("candidates", [])
    }

    for candidate_group in realization_candidates.get("candidates", []):
        chosen_candidate, chosen_scores, scored_candidates = _pick_candidate(
            node=node,
            candidate_group=candidate_group,
            phase_scope=phase_scope,
        )
        if not chosen_candidate:
            continue

        runner_up_scores = scored_candidates[1][1] if len(scored_candidates) > 1 else None
        requires_human_confirmation = provisional
        if runner_up_scores and (chosen_scores["total"] - runner_up_scores["total"]) < 0.07:
            requires_human_confirmation = True

        chosen_by_dimension[candidate_group.get("dimension_id", "")] = chosen_candidate
        converged_choices.append(
            {
                "dimension_id": candidate_group.get("dimension_id", ""),
                "chosen_candidate": chosen_candidate.get("candidate_id", ""),
                "rationale": _build_rationale(
                    candidate_group,
                    chosen_candidate,
                    chosen_scores,
                    runner_up_scores,
                ),
                "rejected_alternatives": _build_rejections(
                    chosen_candidate,
                    candidate_group,
                    scored_candidates,
                ),
                "human_confirmation_needed": requires_human_confirmation,
                "provisional": provisional,
                "chosen_candidate_name": chosen_candidate.get("name", ""),
                "chosen_candidate_description": chosen_candidate.get("description", ""),
                "design_freedom": candidate_group.get("design_freedom", "medium"),
                "score_breakdown": chosen_scores,
                "selection_summary": {
                    "generation_principle": _principle(chosen_candidate),
                    "source_variant_fields": list(candidate_group.get("source_variant_fields", [])),
                    "source_clarification_items": list(candidate_group.get("source_clarification_items", [])),
                },
            }
        )

    conflicts, involved_dimensions = _consistency_conflicts(chosen_by_dimension, candidate_group_map)
    if involved_dimensions:
        for choice in converged_choices:
            if choice.get("dimension_id", "") in involved_dimensions:
                choice["human_confirmation_needed"] = True

    return {
        "pack_version": "1.0",
        "skill_instance_id": realization_candidates.get("skill_instance_id", ""),
        "source_candidates": "realization_candidates.json",
        "converged_choices": converged_choices,
        "cross_dimension_consistency": {
            "checked": True,
            "conflicts": conflicts,
        },
        "metadata": {
            "generated_at": generated_at,
            "generator": "AgentBridge.Compiler.Convergence.v2",
            "converged_choice_count": len(converged_choices),
            "human_confirmation_needed": any(choice.get("human_confirmation_needed", False) for choice in converged_choices),
        },
    }
