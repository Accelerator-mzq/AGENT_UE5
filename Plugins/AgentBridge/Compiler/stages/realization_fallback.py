"""
Phase 11 Realization Candidate Generator.

职责：
  - 从 design_space_report 为每个维度生成至少 2 个候选方向
  - 候选由当前维度的上下文现生成，而不是从固定答案库中选取
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


PRINCIPLE_LABELS: Dict[str, str] = {
    "constraint_first": "约束优先",
    "balanced": "均衡整合",
    "expressive": "表达增强",
    "coupling_first": "耦合优先",
}


def _build_candidate_id(dimension_id: str, principle: str) -> str:
    """为候选生成稳定 id。"""
    return f"rc-{dimension_id}-{principle}"


def _unique_strings(items: List[str]) -> List[str]:
    """保持顺序去重。"""
    seen = set()
    ordered: List[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _first_text(items: List[str], fallback: str) -> str:
    """返回第一个可读文本。"""
    return items[0] if items else fallback


def _candidate_principles(dimension: Dict[str, Any]) -> List[str]:
    """根据维度自由度与风险上下文决定候选原则。"""
    design_freedom = dimension.get("design_freedom", "medium")
    has_coupling = bool(dimension.get("coupled_dimensions", []))
    has_gate_pressure = bool(dimension.get("source_clarification_items", []))

    principles = ["constraint_first", "balanced"]
    if design_freedom == "high":
        principles.append("coupling_first" if has_gate_pressure else "expressive")
    elif design_freedom == "medium" and (has_coupling or has_gate_pressure):
        principles.append("coupling_first")

    return _unique_strings(principles)


def _complexity_for(principle: str) -> str:
    """给候选估算实现复杂度。"""
    if principle == "constraint_first":
        return "low"
    if principle == "expressive":
        return "high"
    return "medium"


def _selection_signals(principle: str) -> Dict[str, Any]:
    """提供给 Convergence 使用的轻量评分信号。"""
    if principle == "constraint_first":
        return {
            "generation_principle": principle,
            "aggressiveness": 0,
            "coordination_bias": 1,
            "clarity_bias": 2,
        }
    if principle == "balanced":
        return {
            "generation_principle": principle,
            "aggressiveness": 1,
            "coordination_bias": 1,
            "clarity_bias": 1,
        }
    if principle == "coupling_first":
        return {
            "generation_principle": principle,
            "aggressiveness": 0,
            "coordination_bias": 2,
            "clarity_bias": 1,
        }
    return {
        "generation_principle": principle,
        "aggressiveness": 2,
        "coordination_bias": 0,
        "clarity_bias": 0,
    }


def _candidate_name(dimension: Dict[str, Any], principle: str) -> str:
    """生成与当前维度相关的候选名称。"""
    return f"{dimension.get('name', '当前维度')}·{PRINCIPLE_LABELS.get(principle, principle)}"


def _candidate_description(dimension: Dict[str, Any], principle: str) -> str:
    """生成候选描述。"""
    dimension_name = dimension.get("name", "当前设计维度")
    intent = dimension.get("dimension_intent", dimension_name)
    bounds = dimension.get("variant_bounds", {})
    must_satisfy = _first_text(bounds.get("must_satisfy", []), "当前阶段约束")
    coupled = bool(dimension.get("coupled_dimensions", []))

    if principle == "constraint_first":
        return (
            f"围绕 {dimension_name}，先把“{must_satisfy}”做成稳定基线，"
            f"优先保证 {intent} 的清晰与可审计。"
        )
    if principle == "balanced":
        return (
            f"围绕 {dimension_name}，在 {intent}、边界满足和实现成本之间做折中，"
            "让当前阶段既可验证又保留后续细化空间。"
        )
    if principle == "coupling_first":
        return (
            f"围绕 {dimension_name}，优先让本域与耦合域保持一致，"
            f"把 {intent} 放在跨域协调可控的前提下推进。"
        )
    coupled_text = "，并接受更高的跨域协调成本" if coupled else ""
    return (
        f"围绕 {dimension_name}，在不突破边界的前提下强化 {intent} 的存在感，"
        f"换取更强的辨识和反馈重量{coupled_text}。"
    )


def _trade_offs(dimension: Dict[str, Any], principle: str) -> Dict[str, List[str]]:
    """为当前候选生成 pros / cons。"""
    bounds = dimension.get("variant_bounds", {})
    must_satisfy = _first_text(bounds.get("must_satisfy", []), "当前设计边界")
    must_not = _first_text(bounds.get("must_not", []), "明显越界风险")
    intent = dimension.get("dimension_intent", dimension.get("name", "当前设计维度"))
    has_coupling = bool(dimension.get("coupled_dimensions", []))

    if principle == "constraint_first":
        return {
            "pros": _unique_strings(
                [
                    f"更稳定地满足“{must_satisfy}”",
                    "实现与评审成本较低",
                    "对 provisional 风险更保守",
                ]
            ),
            "cons": _unique_strings(
                [
                    f"{intent} 的表达张力较保守",
                    "后续做强表现时需要再次调整",
                ]
            ),
        }
    if principle == "balanced":
        return {
            "pros": _unique_strings(
                [
                    f"在 {intent} 与整体清晰度之间更均衡",
                    "更适合作为当前阶段的默认收口方向",
                    "后续跨域 review 更容易对齐",
                ]
            ),
            "cons": _unique_strings(
                [
                    "没有单一目标最优",
                    "仍需要在细部实现上继续做取舍",
                ]
            ),
        }
    if principle == "coupling_first":
        return {
            "pros": _unique_strings(
                [
                    "跨域接口与信息节奏更容易对齐",
                    "对高风险 clarification 更友好",
                    "更适合当前有耦合压力的节点",
                ]
            ),
            "cons": _unique_strings(
                [
                    "本域个性表达会被整体一致性压住",
                    "局部体验未必最强",
                ]
            ),
        }
    coupling_cost = "耦合协调成本更高" if has_coupling else "实现成本更高"
    return {
        "pros": _unique_strings(
            [
                f"{intent} 的可感知度更强",
                "更容易形成记忆点和差异化",
                "在正式模式下更能体现设计表达",
            ]
        ),
        "cons": _unique_strings(
            [
                f"更容易逼近“{must_not}”这类边界",
                coupling_cost,
            ]
        ),
    }


def _build_candidate(
    dimension: Dict[str, Any],
    principle: str,
) -> Dict[str, Any]:
    """为单个维度构建一个候选。"""
    return {
        "candidate_id": _build_candidate_id(dimension.get("dimension_id", "dim"), principle),
        "name": _candidate_name(dimension, principle),
        "description": _candidate_description(dimension, principle),
        "trade_offs": _trade_offs(dimension, principle),
        "satisfies_bounds": True,
        "estimated_complexity": _complexity_for(principle),
        "compatible_with": [],
        "conflicts_with": [],
        "candidate_key": principle,
        "selection_signals": _selection_signals(principle),
    }


def create_realization_candidates(
    design_space_report: Dict[str, Any],
) -> Dict[str, Any]:
    """为单个 Skill Instance 生成上下文驱动的 realization candidates。"""
    generated_at = datetime.now(timezone.utc).isoformat()
    skill_instance_id = design_space_report.get("skill_instance_id", "")
    candidate_groups: List[Dict[str, Any]] = []

    for dimension in design_space_report.get("discovery_dimensions", []):
        principles = _candidate_principles(dimension)
        built_candidates = [
            _build_candidate(dimension, principle)
            for principle in principles
        ]

        all_candidate_ids = [candidate["candidate_id"] for candidate in built_candidates]
        for candidate in built_candidates:
            candidate["conflicts_with"] = [
                candidate_id
                for candidate_id in all_candidate_ids
                if candidate_id != candidate["candidate_id"]
            ]

        candidate_groups.append(
            {
                "dimension_id": dimension.get("dimension_id", ""),
                "dimension_name": dimension.get("name", ""),
                "design_freedom": dimension.get("design_freedom", "medium"),
                "coupled_dimensions": list(dimension.get("coupled_dimensions", [])),
                "source_variant_fields": list(dimension.get("source_variant_fields", [])),
                "source_clarification_items": list(dimension.get("source_clarification_items", [])),
                "dimension_intent": dimension.get("dimension_intent", ""),
                "selection_context": {
                    "discovery_basis": dimension.get("discovery_basis", ""),
                    "source_dependencies": list(dimension.get("source_dependencies", [])),
                    "source_coupling": list(dimension.get("source_coupling", [])),
                },
                "candidates": built_candidates,
            }
        )

    return {
        "candidates_version": "1.0",
        "skill_instance_id": skill_instance_id,
        "source_design_space_report": "design_space_report.json",
        "candidates": candidate_groups,
        "metadata": {
            "generated_at": generated_at,
            "generator": "AgentBridge.Compiler.RealizationCandidates.v2",
            "candidate_group_count": len(candidate_groups),
        },
    }
