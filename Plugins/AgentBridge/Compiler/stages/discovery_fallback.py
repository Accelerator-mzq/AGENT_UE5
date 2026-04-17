"""
Phase 11 Discovery Engine.

职责：
  - 根据节点职责、Root Skill Contract、Clarification Gate 与 Skill Graph 上下文，
    发现当前域的可设计维度与锁定维度
  - 保留启发式角色画像，但不允许把维度、候选或默认选择提前写死
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


# 节点职责画像只描述“这个节点通常关心什么”，不直接提供维度答案。
NODE_ROLE_PROFILES: Dict[str, Dict[str, Any]] = {
    "skill-board-topology": {
        "role_label": "棋盘拓扑",
        "locked_fields": [
            "board.tile_count",
            "board.layout_shape",
            "board.movement_direction",
            "board.corner_indices",
        ],
        "relevant_variant_fields": [
            "board.world_layout_dimensions",
            "board.tile_visual_style",
            "hud.layout_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-tile-system": {
        "role_label": "格子系统",
        "locked_fields": [
            "board.tile_count",
            "board.corner_indices",
            "property.full_color_group_rent_multiplier",
        ],
        "relevant_variant_fields": [
            "board.tile_visual_style",
            "player_token.visual_style",
            "popup.presentation_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-turn-loop": {
        "role_label": "回合主循环",
        "locked_fields": [
            "dice.count",
            "dice.sides",
            "dice.doubles_extra_turn",
            "dice.triple_doubles_jail",
            "economy.start_bonus",
        ],
        "relevant_variant_fields": [
            "dice.roll_feedback",
            "popup.presentation_style",
            "hud.layout_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-dice": {
        "role_label": "骰子规则",
        "locked_fields": [
            "dice.count",
            "dice.sides",
            "dice.doubles_extra_turn",
            "dice.triple_doubles_jail",
        ],
        "relevant_variant_fields": [
            "dice.roll_feedback",
            "popup.presentation_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-economy": {
        "role_label": "经济系统",
        "locked_fields": [
            "economy.starting_cash",
            "economy.start_bonus",
            "property.full_color_group_rent_multiplier",
        ],
        "relevant_variant_fields": [
            "popup.presentation_style",
            "board.tile_visual_style",
            "player_token.visual_style",
            "hud.layout_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-player-management": {
        "role_label": "玩家管理",
        "locked_fields": [
            "game.player_count_range",
            "game.win_condition",
            "game.match_length_minutes",
        ],
        "relevant_variant_fields": [
            "player_token.visual_style",
            "hud.layout_style",
            "popup.presentation_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-jail": {
        "role_label": "监狱规则",
        "locked_fields": [
            "jail.visit_tile_index",
            "jail.bail_cost",
            "jail.max_turns",
        ],
        "relevant_variant_fields": [
            "popup.presentation_style",
            "hud.layout_style",
            "dice.roll_feedback",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
    "skill-baseline-hud": {
        "role_label": "HUD",
        "locked_fields": [
            "ui.required_hud_fields",
            "game.player_count_range",
        ],
        "relevant_variant_fields": [
            "hud.layout_style",
            "dice.roll_feedback",
            "frontend.visual_theme",
            "player_token.visual_style",
        ],
        "min_dimensions": 2,
        "max_dimensions": 4,
    },
}


# 字段透镜是“观察维度的方式”，不是直接产出的维度列表。
FIELD_DISCOVERY_LENSES: Dict[str, List[Dict[str, Any]]] = {
    "board.world_layout_dimensions": [
        {
            "lens_key": "spatial_readability",
            "intent": "空间占位与完整可见",
            "design_freedom": "high",
            "priority": 30,
        },
        {
            "lens_key": "view_framing",
            "intent": "镜头框取与留白平衡",
            "design_freedom": "medium",
            "priority": 22,
        },
    ],
    "board.tile_visual_style": [
        {
            "lens_key": "semantic_coding",
            "intent": "类型区分与语义识别",
            "design_freedom": "high",
            "priority": 28,
        },
        {
            "lens_key": "anchor_emphasis",
            "intent": "关键状态的层级强调",
            "design_freedom": "medium",
            "priority": 18,
        },
    ],
    "player_token.visual_style": [
        {
            "lens_key": "identity_surface",
            "intent": "玩家身份区分与归属表达",
            "design_freedom": "high",
            "priority": 24,
        }
    ],
    "hud.layout_style": [
        {
            "lens_key": "information_footprint",
            "intent": "信息占位与棋盘遮挡平衡",
            "design_freedom": "high",
            "priority": 26,
        },
        {
            "lens_key": "focus_priority",
            "intent": "关键状态优先级排序",
            "design_freedom": "medium",
            "priority": 19,
        },
    ],
    "popup.presentation_style": [
        {
            "lens_key": "decision_surface",
            "intent": "决策界面的打断强度",
            "design_freedom": "high",
            "priority": 25,
        },
        {
            "lens_key": "event_notice_weight",
            "intent": "事件反馈的显著性",
            "design_freedom": "medium",
            "priority": 17,
        },
    ],
    "dice.roll_feedback": [
        {
            "lens_key": "reveal_rhythm",
            "intent": "结果揭示节奏与反馈重量",
            "design_freedom": "high",
            "priority": 27,
        },
        {
            "lens_key": "rule_event_emphasis",
            "intent": "规则节点的强化反馈",
            "design_freedom": "medium",
            "priority": 16,
        },
    ],
    "frontend.visual_theme": [
        {
            "lens_key": "theme_readability",
            "intent": "视觉主题与可读性平衡",
            "design_freedom": "medium",
            "priority": 14,
        }
    ],
    "audio.feedback_style": [
        {
            "lens_key": "audio_notice_weight",
            "intent": "音频反馈与信息清晰度平衡",
            "design_freedom": "medium",
            "priority": 14,
        }
    ],
}


# Clarification item 只提供字段关联，不直接规定 Discovery 结果。
CLARIFICATION_FIELD_HINTS: Dict[str, List[str]] = {
    "cg-hud-layout-style": ["hud.layout_style"],
    "cg-dice-roll-feedback": ["dice.roll_feedback"],
    "cg-player-token-visual-style": ["player_token.visual_style"],
    "cg-card-events-phase1": ["popup.presentation_style", "board.tile_visual_style"],
}


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


def _merge_variant_bounds(root_skill_contract: Dict[str, Any], variant_fields: List[str]) -> Dict[str, List[str]]:
    """把多个 Variant Field 的 bounds 合并成一个维度边界。"""
    must_satisfy: List[str] = []
    must_not: List[str] = []
    all_variants = root_skill_contract.get("variant_fields", {})
    for field_path in variant_fields:
        bounds = all_variants.get(field_path, {}).get("bounds", {})
        must_satisfy.extend(bounds.get("must_satisfy", []))
        must_not.extend(bounds.get("must_not", []))
    return {
        "must_satisfy": _unique_strings(must_satisfy),
        "must_not": _unique_strings(must_not),
    }


def _related_gate_items(node: Dict[str, Any], clarification_gate_report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """查找与当前节点相关的 Clarification Gate items。"""
    indexed = {
        item.get("item_id", ""): item
        for item in clarification_gate_report.get("items", [])
    }
    related_ids = _unique_strings(
        list(node.get("related_clarification_items", []))
        + list(node.get("gated_by_clarification_items", []))
    )
    return [
        indexed[item_id]
        for item_id in related_ids
        if item_id in indexed
    ]


def _profile_for(node: Dict[str, Any]) -> Dict[str, Any]:
    """读取节点职责画像；未知节点使用保守默认值。"""
    return NODE_ROLE_PROFILES.get(
        node.get("instance_id", ""),
        {
            "role_label": node.get("instance_id", "未知节点"),
            "locked_fields": [],
            "relevant_variant_fields": [],
            "min_dimensions": 2,
            "max_dimensions": 4,
        },
    )


def _variant_fields_for_node(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
) -> List[str]:
    """为当前节点收集相关的 Variant Field。"""
    profile = _profile_for(node)
    all_variants = root_skill_contract.get("variant_fields", {})
    candidate_fields: List[str] = list(profile.get("relevant_variant_fields", []))

    for gate_item in _related_gate_items(node, clarification_gate_report):
        candidate_fields.extend(
            CLARIFICATION_FIELD_HINTS.get(gate_item.get("item_id", ""), [])
        )

    return [
        field_path
        for field_path in _unique_strings(candidate_fields)
        if field_path in all_variants
    ]


def _lens_blueprints_for_fields(variant_fields: List[str]) -> List[Dict[str, Any]]:
    """从字段透镜生成待筛选的维度蓝图。"""
    blueprints: List[Dict[str, Any]] = []
    for field_path in variant_fields:
        for lens in FIELD_DISCOVERY_LENSES.get(field_path, []):
            blueprints.append(
                {
                    "lens_key": lens["lens_key"],
                    "intent": lens["intent"],
                    "design_freedom": lens["design_freedom"],
                    "priority": lens["priority"],
                    "source_variant_fields": [field_path],
                }
            )
    return blueprints


def _deduplicate_lens_blueprints(blueprints: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 lens_key 合并来源字段与优先级。"""
    merged: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for blueprint in blueprints:
        lens_key = blueprint["lens_key"]
        if lens_key not in merged:
            merged[lens_key] = {
                "lens_key": lens_key,
                "intent": blueprint["intent"],
                "design_freedom": blueprint["design_freedom"],
                "priority": blueprint["priority"],
                "source_variant_fields": list(blueprint["source_variant_fields"]),
            }
            order.append(lens_key)
            continue

        merged_entry = merged[lens_key]
        merged_entry["source_variant_fields"] = _unique_strings(
            merged_entry["source_variant_fields"] + blueprint["source_variant_fields"]
        )
        merged_entry["priority"] = max(merged_entry["priority"], blueprint["priority"])
        if merged_entry["design_freedom"] != "high" and blueprint["design_freedom"] == "high":
            merged_entry["design_freedom"] = "high"

    return [merged[key] for key in order]


def _fallback_dimension_blueprint(variant_fields: List[str]) -> Dict[str, Any]:
    """当透镜不足以覆盖最少维度数时，补一个跨字段综合维度。"""
    return {
        "lens_key": "cross_field_balance",
        "intent": "跨字段综合协调",
        "design_freedom": "medium",
        "priority": 12,
        "source_variant_fields": list(variant_fields),
    }


def _select_dimension_blueprints(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """根据字段透镜与节点画像选出最终的维度蓝图。"""
    profile = _profile_for(node)
    variant_fields = _variant_fields_for_node(node, root_skill_contract, clarification_gate_report)
    blueprints = _deduplicate_lens_blueprints(_lens_blueprints_for_fields(variant_fields))

    blueprints.sort(
        key=lambda item: (
            -item.get("priority", 0),
            item.get("lens_key", ""),
        )
    )

    max_dimensions = int(profile.get("max_dimensions", 4))
    selected = blueprints[:max_dimensions]

    min_dimensions = int(profile.get("min_dimensions", 2))
    if variant_fields and len(selected) < min_dimensions:
        selected.append(_fallback_dimension_blueprint(variant_fields))

    return selected[:max_dimensions]


def _build_locked_dimensions(
    root_skill_contract: Dict[str, Any],
    locked_fields: List[str],
    skill_instance_id: str,
) -> List[Dict[str, Any]]:
    """把相关 Constraint Fields 转成 locked_dimensions。"""
    locked_dimensions: List[Dict[str, Any]] = []
    constraint_fields = root_skill_contract.get("constraint_fields", {})
    for index, field_path in enumerate(locked_fields, start=1):
        constraint = constraint_fields.get(field_path)
        if not constraint:
            continue
        locked_dimensions.append(
            {
                "dimension_id": f"locked-{skill_instance_id}-{index:02d}",
                "name": field_path,
                "constraint_source": "constraint",
                "locked_value": constraint.get("value"),
                "reason": constraint.get("gdd_ref", ""),
                "source_constraint_field": field_path,
            }
        )
    return locked_dimensions


def _dimension_name(node: Dict[str, Any], blueprint: Dict[str, Any]) -> str:
    """根据节点角色与维度意图生成维度名。"""
    role_label = _profile_for(node).get("role_label", node.get("instance_id", "当前节点"))
    return f"{role_label}的{blueprint.get('intent', '设计取舍')}"


def _gdd_hints_for_dimension(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    source_variant_fields: List[str],
) -> List[str]:
    """汇总维度的 GDD / planning / clarification 线索。"""
    hints: List[str] = []
    for field_path in source_variant_fields:
        variant = root_skill_contract.get("variant_fields", {}).get(field_path, {})
        gdd_ref = variant.get("gdd_ref")
        if gdd_ref:
            hints.append(gdd_ref)

    hints.extend(node.get("planning_notes", []))
    for gate_item in _related_gate_items(node, clarification_gate_report):
        reason = gate_item.get("reason") or gate_item.get("impact") or gate_item.get("topic")
        if reason:
            hints.append(reason)
    return _unique_strings(hints)


def _design_freedom(
    blueprint: Dict[str, Any],
    gate_items: List[Dict[str, Any]],
    node: Dict[str, Any],
) -> str:
    """根据蓝图、clarification 风险和耦合密度修正设计自由度。"""
    current = blueprint.get("design_freedom", "medium")
    if current not in {"low", "medium", "high"}:
        current = "medium"

    has_high_risk = any(item.get("risk_level") in {"high", "critical"} for item in gate_items)
    has_coupling = bool(node.get("coupling", []))

    if current == "high" and has_high_risk:
        return "medium"
    if current == "high" and has_coupling:
        return "medium"
    return current


def _discovery_basis(
    node: Dict[str, Any],
    blueprint: Dict[str, Any],
    source_variant_fields: List[str],
    gate_items: List[Dict[str, Any]],
) -> str:
    """生成维度发现依据，便于后续审计。"""
    role_label = _profile_for(node).get("role_label", node.get("instance_id", "当前节点"))
    field_summary = "、".join(source_variant_fields) if source_variant_fields else "无显式变体字段"
    gate_summary = (
        "；相关 clarification: " + "、".join(item.get("item_id", "") for item in gate_items)
        if gate_items else ""
    )
    return f"{role_label}围绕 {field_summary} 合成出“{blueprint.get('intent', '')}”这一设计张力{gate_summary}。"


def _build_discovery_dimensions(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """构造上下文驱动的 discovery dimensions。"""
    blueprints = _select_dimension_blueprints(node, root_skill_contract, clarification_gate_report)
    gate_items = _related_gate_items(node, clarification_gate_report)
    skill_instance_id = node.get("instance_id", "")

    discovery_dimensions: List[Dict[str, Any]] = []
    for blueprint in blueprints:
        source_variant_fields = list(blueprint.get("source_variant_fields", []))
        dimension_id = f"dim-{skill_instance_id}-{blueprint.get('lens_key', 'dimension')}"
        discovery_dimensions.append(
            {
                "dimension_id": dimension_id,
                "name": _dimension_name(node, blueprint),
                "constraint_source": "variant",
                "variant_bounds": _merge_variant_bounds(root_skill_contract, source_variant_fields),
                "gdd_hints": _gdd_hints_for_dimension(
                    node,
                    root_skill_contract,
                    clarification_gate_report,
                    source_variant_fields,
                ),
                "coupled_dimensions": [],
                "design_freedom": _design_freedom(blueprint, gate_items, node),
                "source_variant_fields": source_variant_fields,
                "source_clarification_items": [
                    item.get("item_id", "")
                    for item in gate_items
                ],
                "source_dependencies": list(node.get("dependencies", [])),
                "source_coupling": list(node.get("coupling", [])),
                "dimension_intent": blueprint.get("intent", ""),
                "discovery_basis": _discovery_basis(
                    node,
                    blueprint,
                    source_variant_fields,
                    gate_items,
                ),
            }
        )

    # 同一节点内发现的维度默认互相影响，因此互相建立耦合引用。
    dimension_ids = [item["dimension_id"] for item in discovery_dimensions]
    for item in discovery_dimensions:
        item["coupled_dimensions"] = [
            other_id
            for other_id in dimension_ids
            if other_id != item["dimension_id"]
        ]

    return discovery_dimensions


def create_design_space_report(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    source_graph_id: str,
) -> Dict[str, Any]:
    """为单个 Skill Instance 生成上下文驱动的 Discovery 结果。"""
    generated_at = datetime.now(timezone.utc).isoformat()
    skill_instance_id = node.get("instance_id", "")
    profile = _profile_for(node)
    discovery_dimensions = _build_discovery_dimensions(
        node=node,
        root_skill_contract=root_skill_contract,
        clarification_gate_report=clarification_gate_report,
    )
    locked_dimensions = _build_locked_dimensions(
        root_skill_contract,
        profile.get("locked_fields", []),
        skill_instance_id,
    )

    return {
        "report_version": "1.0",
        "skill_instance_id": skill_instance_id,
        "source_contract_id": root_skill_contract.get("contract_id", ""),
        "source_graph_id": source_graph_id,
        "discovery_dimensions": discovery_dimensions,
        "locked_dimensions": locked_dimensions,
        "metadata": {
            "generated_at": generated_at,
            "generator": "AgentBridge.Compiler.DesignSpaceDiscovery.v2",
            "discovery_method": "context_synthesized_from_role_profile_variant_bounds_and_coupling",
            "dimension_count": len(discovery_dimensions),
            "locked_dimension_count": len(locked_dimensions),
        },
    }
