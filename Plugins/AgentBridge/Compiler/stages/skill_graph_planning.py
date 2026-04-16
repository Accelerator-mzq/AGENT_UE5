"""
Phase 11 Skill Graph Planning stage.

职责：
  - 从 Root Skill Contract 与 Clarification Gate 派生 Skill Graph
  - 规划 Gameplay / Baseline 节点、依赖边、耦合边、收敛顺序边
  - 只输出“谁先做、谁关联、谁收敛优先”，不提前写死 realization 结果
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set


GAMEPLAY_NODE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "gameplay-board-topology": {
        "instance_id": "skill-board-topology",
        "template_id": "monopoly.board_topology.phase1",
        "convergence_priority": 1,
        "related_clarification_items": [],
        "planning_notes": [
            "棋盘拓扑是 Monopoly 主链的起点，先锁定 28 格、角格索引与移动方向。",
        ],
        "template_source": "plugin_skill_template",
    },
    "gameplay-tile-system": {
        "instance_id": "skill-tile-system",
        "template_id": "monopoly.tile_event_dispatch.phase1",
        "convergence_priority": 2,
        "related_clarification_items": ["cg-card-events-phase1"],
        "planning_notes": [
            "Tile System 负责格子类型、事件分发矩阵与 Phase 1 留空事件槽位。",
        ],
        "template_source": "plugin_skill_template",
    },
    "gameplay-turn-loop": {
        "instance_id": "skill-turn-loop",
        "template_id": "monopoly.turn_and_dice_flow.phase1",
        "convergence_priority": 3,
        "related_clarification_items": ["cg-max-game-length"],
        "planning_notes": [
            "Turn Loop 组织掷骰、移动、过起点奖励与回合切换，是 gameplay 主骨架。",
        ],
        "template_source": "plugin_skill_template",
    },
    "gameplay-dice": {
        "instance_id": "skill-dice",
        "template_id": "monopoly.turn_and_dice_flow.phase1",
        "convergence_priority": 2,
        "related_clarification_items": ["cg-dice-roll-feedback"],
        "planning_notes": [
            "Dice 节点单独保留，方便后续把规则语义与表现反馈拆开处理。",
        ],
        "template_source": "plugin_skill_template",
    },
    "gameplay-economy": {
        "instance_id": "skill-economy",
        "template_id": "monopoly.property_economy.phase1",
        "convergence_priority": 4,
        "related_clarification_items": [],
        "planning_notes": [
            "Economy 负责购买、租金、支付与颜色组翻倍，不在此阶段选择具体表现方案。",
        ],
        "template_source": "plugin_skill_template",
    },
    "gameplay-player-management": {
        "instance_id": "skill-player-management",
        "template_id": "monopoly.jail_and_bankruptcy.phase1",
        "convergence_priority": 5,
        "related_clarification_items": ["cg-max-game-length", "cg-player-token-visual-style"],
        "planning_notes": [
            "Player Management 负责玩家顺序、存活状态、淘汰与最终胜者归属。",
        ],
        "template_source": "plugin_skill_template",
    },
    "gameplay-jail": {
        "instance_id": "skill-jail",
        "template_id": "monopoly.jail_and_bankruptcy.phase1",
        "convergence_priority": 5,
        "related_clarification_items": [],
        "planning_notes": [
            "Jail 作为独立节点保留，便于后续把入狱、出狱与破产关系拆分审查。",
        ],
        "template_source": "plugin_skill_template",
    },
}

BASELINE_NODE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "baseline-start-screen": {
        "instance_id": "skill-baseline-start-screen",
        "template_id": "baseline.start_screen.presence_only",
        "convergence_priority": 6,
        "related_clarification_items": [],
        "planning_notes": [
            "Start Screen 只规划入口能力，不在 Skill Graph 中决定具体实现形态。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-main-menu": {
        "instance_id": "skill-baseline-main-menu",
        "template_id": "baseline.main_menu.presence_only",
        "convergence_priority": 6,
        "related_clarification_items": [],
        "planning_notes": [
            "Main Menu 保持 presence_only，后续只验证入口流转与必要按钮能力。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-settings": {
        "instance_id": "skill-baseline-settings",
        "template_id": "baseline.settings.presence_only",
        "convergence_priority": 5,
        "related_clarification_items": ["cg-platform-persistence", "cg-platform-foundation-boundary"],
        "planning_notes": [
            "Settings 必须保留六项最低控件，但不在本阶段决定持久化实现细节。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-pause": {
        "instance_id": "skill-baseline-pause",
        "template_id": "baseline.pause.presence_only",
        "convergence_priority": 5,
        "related_clarification_items": [],
        "planning_notes": [
            "Pause 与 turn loop、input foundation 有耦合，但当前仍只做能力规划。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-results": {
        "instance_id": "skill-baseline-results",
        "template_id": "baseline.results.presence_only",
        "convergence_priority": 6,
        "related_clarification_items": ["cg-max-game-length"],
        "planning_notes": [
            "Results 依赖胜负与淘汰语义，保留与 player management 的强关联。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-hud": {
        "instance_id": "skill-baseline-hud",
        "template_id": "baseline.hud.realization_eligible",
        "convergence_priority": 4,
        "related_clarification_items": ["cg-hud-layout-style", "cg-dice-roll-feedback"],
        "planning_notes": [
            "HUD 是 realization_eligible baseline，允许进入后续 Design Space Discovery。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-input-foundation": {
        "instance_id": "skill-baseline-input-foundation",
        "template_id": "baseline.input_foundation.presence_only",
        "convergence_priority": 5,
        "related_clarification_items": [],
        "planning_notes": [
            "Input Foundation 只提供通用输入底座，不提前决定具体交互映射细节。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-audio-foundation": {
        "instance_id": "skill-baseline-audio-foundation",
        "template_id": "baseline.audio_foundation.presence_only",
        "convergence_priority": 5,
        "related_clarification_items": [],
        "planning_notes": [
            "Audio Foundation 先保证音量控制与基础 SFX/BGM 能力存在。",
        ],
        "template_source": "future_baseline_template",
    },
    "baseline-platform-foundation": {
        "instance_id": "skill-baseline-platform-foundation",
        "template_id": "baseline.platform_foundation.clarification_gated",
        "convergence_priority": 6,
        "related_clarification_items": ["cg-platform-foundation-boundary", "cg-platform-persistence"],
        "planning_notes": [
            "Platform Foundation 当前受 Clarification Gate 约束，只保留节点与边界，不发散实现。",
        ],
        "template_source": "future_baseline_template",
    },
}

EDGE_BLUEPRINTS: List[Dict[str, str]] = [
    {
        "from": "skill-board-topology",
        "to": "skill-tile-system",
        "type": "dependency",
        "reason": "tile system 需要先知道棋盘拓扑、角格索引与格子顺序。",
    },
    {
        "from": "skill-dice",
        "to": "skill-turn-loop",
        "type": "dependency",
        "reason": "turn loop 需要骰子规则语义，才能建立回合状态推进。",
    },
    {
        "from": "skill-board-topology",
        "to": "skill-turn-loop",
        "type": "dependency",
        "reason": "移动规则依赖棋盘路线与起点、监狱、前往监狱等关键位置。",
    },
    {
        "from": "skill-tile-system",
        "to": "skill-economy",
        "type": "dependency",
        "reason": "经济系统要先知道地产、税务、机会等格子类型与事件入口。",
    },
    {
        "from": "skill-turn-loop",
        "to": "skill-economy",
        "type": "dependency",
        "reason": "经济结算嵌在回合流转中，需要先有回合与移动语义。",
    },
    {
        "from": "skill-turn-loop",
        "to": "skill-player-management",
        "type": "dependency",
        "reason": "玩家轮转、淘汰与胜负判定依赖回合推进语义。",
    },
    {
        "from": "skill-economy",
        "to": "skill-player-management",
        "type": "dependency",
        "reason": "破产与胜负收敛建立在资金与支付结果之上。",
    },
    {
        "from": "skill-turn-loop",
        "to": "skill-jail",
        "type": "dependency",
        "reason": "入狱、出狱与三连双规则依赖回合和掷骰流程。",
    },
    {
        "from": "skill-player-management",
        "to": "skill-jail",
        "type": "dependency",
        "reason": "监狱状态属于玩家状态机的一部分。",
    },
    {
        "from": "skill-baseline-start-screen",
        "to": "skill-baseline-main-menu",
        "type": "dependency",
        "reason": "主菜单默认从 Start Screen 入口进入。",
    },
    {
        "from": "skill-baseline-main-menu",
        "to": "skill-baseline-settings",
        "type": "dependency",
        "reason": "Settings 默认由 Main Menu 和 Pause 进入，先保留主菜单入口。",
    },
    {
        "from": "skill-baseline-main-menu",
        "to": "skill-baseline-input-foundation",
        "type": "dependency",
        "reason": "输入底座需覆盖菜单确认/取消等基础行为。",
    },
    {
        "from": "skill-baseline-settings",
        "to": "skill-baseline-audio-foundation",
        "type": "dependency",
        "reason": "音频基础能力需要 Settings 提供控制入口。",
    },
    {
        "from": "skill-baseline-settings",
        "to": "skill-baseline-platform-foundation",
        "type": "dependency",
        "reason": "平台基础能力与窗口模式、分辨率、退出处理绑定。",
    },
    {
        "from": "skill-turn-loop",
        "to": "skill-baseline-hud",
        "type": "dependency",
        "reason": "HUD 要展示当前回合、当前玩家与阶段状态，必须依赖回合流转。",
    },
    {
        "from": "skill-economy",
        "to": "skill-baseline-hud",
        "type": "dependency",
        "reason": "HUD 常驻展示玩家资金，依赖经济语义。",
    },
    {
        "from": "skill-player-management",
        "to": "skill-baseline-hud",
        "type": "dependency",
        "reason": "HUD 需要引用玩家状态与当前玩家标识。",
    },
    {
        "from": "skill-baseline-input-foundation",
        "to": "skill-baseline-pause",
        "type": "dependency",
        "reason": "Pause 需要依赖 pause_input / menu_cancel 等输入底座。",
    },
    {
        "from": "skill-baseline-settings",
        "to": "skill-baseline-pause",
        "type": "dependency",
        "reason": "Pause 菜单默认包含 Settings 入口。",
    },
    {
        "from": "skill-player-management",
        "to": "skill-baseline-results",
        "type": "dependency",
        "reason": "Results 需要胜者与被淘汰玩家状态。",
    },
    {
        "from": "skill-economy",
        "to": "skill-baseline-results",
        "type": "dependency",
        "reason": "若胜负由破产或资金状态决定，Results 需要经济结算结果。",
    },
    {
        "from": "skill-board-topology",
        "to": "skill-baseline-hud",
        "type": "coupling",
        "reason": "HUD 布局与棋盘可读性互相影响，需要协调遮挡边界。",
    },
    {
        "from": "skill-tile-system",
        "to": "skill-baseline-hud",
        "type": "coupling",
        "reason": "HUD 与格子信息、购买/租金/监狱弹窗有接口耦合。",
    },
    {
        "from": "skill-turn-loop",
        "to": "skill-dice",
        "type": "coupling",
        "reason": "骰子规则与回合推进强耦合，但仍保留为两个规划节点。",
    },
    {
        "from": "skill-economy",
        "to": "skill-jail",
        "type": "coupling",
        "reason": "保释金、罚金和破产判定会影响监狱流程。",
    },
    {
        "from": "skill-tile-system",
        "to": "skill-jail",
        "type": "coupling",
        "reason": "前往监狱格与监狱探访格属于 tile system 与 jail 的交叉区域。",
    },
    {
        "from": "skill-baseline-pause",
        "to": "skill-baseline-hud",
        "type": "coupling",
        "reason": "暂停时 HUD 的显示/隐藏与输入锁定需协调。",
    },
    {
        "from": "skill-baseline-settings",
        "to": "skill-baseline-audio-foundation",
        "type": "coupling",
        "reason": "音量控制与设置页控件存在双向耦合。",
    },
    {
        "from": "skill-baseline-settings",
        "to": "skill-baseline-platform-foundation",
        "type": "coupling",
        "reason": "窗口模式与分辨率选择会影响平台基础能力边界。",
    },
    {
        "from": "skill-baseline-results",
        "to": "skill-baseline-hud",
        "type": "coupling",
        "reason": "结果页与 HUD 在游戏结束时需要协调信息交接。",
    },
    {
        "from": "skill-baseline-input-foundation",
        "to": "skill-baseline-hud",
        "type": "coupling",
        "reason": "HUD 的操作反馈需要共享基础输入约定。",
    },
    {
        "from": "skill-board-topology",
        "to": "skill-tile-system",
        "type": "convergence_order",
        "reason": "先收敛棋盘拓扑，再收敛格子系统。",
    },
    {
        "from": "skill-tile-system",
        "to": "skill-turn-loop",
        "type": "convergence_order",
        "reason": "格子系统先于回合事件分发收敛。",
    },
    {
        "from": "skill-turn-loop",
        "to": "skill-economy",
        "type": "convergence_order",
        "reason": "先稳定回合流，再细化购买、租金与支付路径。",
    },
    {
        "from": "skill-economy",
        "to": "skill-player-management",
        "type": "convergence_order",
        "reason": "玩家淘汰与胜负判断建立在经济收敛之后。",
    },
    {
        "from": "skill-player-management",
        "to": "skill-jail",
        "type": "convergence_order",
        "reason": "监狱是玩家状态机的特化分支，建议稍后收敛。",
    },
    {
        "from": "skill-jail",
        "to": "skill-baseline-hud",
        "type": "convergence_order",
        "reason": "先稳定监狱与回合状态，再决定 HUD 的最终表达。",
    },
    {
        "from": "skill-baseline-start-screen",
        "to": "skill-baseline-main-menu",
        "type": "convergence_order",
        "reason": "前台入口先于主菜单流转收敛。",
    },
    {
        "from": "skill-baseline-main-menu",
        "to": "skill-baseline-settings",
        "type": "convergence_order",
        "reason": "主菜单先于设置入口收敛。",
    },
    {
        "from": "skill-baseline-settings",
        "to": "skill-baseline-pause",
        "type": "convergence_order",
        "reason": "Pause 依赖设置入口与输入基础，建议后收敛。",
    },
    {
        "from": "skill-baseline-hud",
        "to": "skill-baseline-results",
        "type": "convergence_order",
        "reason": "HUD 稳定后再收敛结束态结果表达更清晰。",
    },
]


def _swap_prefix(raw_value: str, source_prefix: str, target_prefix: str) -> str:
    """把 contract 风格 ID 转成 graph / gate 风格 ID。"""
    if raw_value.startswith(source_prefix):
        return target_prefix + raw_value[len(source_prefix):]
    return raw_value


def _index_gate_items(clarification_gate_report: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """把 Clarification Gate item 按 item_id 建索引。"""
    indexed: Dict[str, Dict[str, Any]] = {}
    for item in clarification_gate_report.get("items", []):
        item_id = item.get("item_id", "")
        if item_id:
            indexed[item_id] = item
    return indexed


def _filter_edges(node_ids: Set[str]) -> List[Dict[str, str]]:
    """只保留两端节点都存在的边。"""
    return [
        edge
        for edge in EDGE_BLUEPRINTS
        if edge["from"] in node_ids and edge["to"] in node_ids
    ]


def _build_relationship_maps(edges: List[Dict[str, str]]) -> tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """从边集合反推每个节点的 dependencies / coupling。"""
    dependency_map: Dict[str, List[str]] = {}
    coupling_map: Dict[str, Set[str]] = {}

    for edge in edges:
        edge_type = edge.get("type")
        source_id = edge.get("from", "")
        target_id = edge.get("to", "")
        if edge_type == "dependency":
            dependency_map.setdefault(target_id, []).append(source_id)
        elif edge_type == "coupling":
            coupling_map.setdefault(source_id, set()).add(target_id)
            coupling_map.setdefault(target_id, set()).add(source_id)

    ordered_dependency_map = {node_id: values for node_id, values in dependency_map.items()}
    ordered_coupling_map = {node_id: sorted(values) for node_id, values in coupling_map.items()}
    return ordered_dependency_map, ordered_coupling_map


def _ordered_node_ids(nodes: List[Dict[str, Any]]) -> Dict[str, int]:
    """为节点建立稳定排序索引。"""
    return {node["instance_id"]: index for index, node in enumerate(nodes)}


def _annotate_node(
    node: Dict[str, Any],
    dependency_map: Dict[str, List[str]],
    coupling_map: Dict[str, List[str]],
    order_map: Dict[str, int],
) -> Dict[str, Any]:
    """把依赖与耦合关系回填到节点上。"""
    instance_id = node["instance_id"]
    dependencies = sorted(dependency_map.get(instance_id, []), key=lambda item: order_map.get(item, 10_000))
    coupling = sorted(coupling_map.get(instance_id, []), key=lambda item: order_map.get(item, 10_000))
    node["dependencies"] = dependencies
    node["coupling"] = coupling
    return node


def _build_gameplay_nodes(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """从 Root Skill Contract 派生 Gameplay 节点。"""
    gate_item_map = _index_gate_items(clarification_gate_report)
    retained_clarifications = set(clarification_gate_report.get("retained_clarifications", []))
    nodes: List[Dict[str, Any]] = []

    for capability in root_skill_contract.get("gameplay_capabilities", []):
        if capability.get("activation") != "required":
            continue

        capability_id = capability.get("capability_id", "")
        config = GAMEPLAY_NODE_CONFIGS.get(capability_id)
        if not config:
            continue

        related_item_ids = [item_id for item_id in config.get("related_clarification_items", []) if item_id in gate_item_map]
        gated_item_ids = [item_id for item_id in related_item_ids if item_id in retained_clarifications]

        planning_notes = list(config.get("planning_notes", []))
        for item_id in related_item_ids:
            item = gate_item_map[item_id]
            planning_notes.append(f"{item.get('topic', item_id)} -> {item.get('decision', '')}")

        nodes.append(
            {
                "instance_id": config["instance_id"],
                "capability_id": capability_id,
                "template_id": config["template_id"],
                "domain_type": "gameplay",
                "status": "pending",
                "allows_design_space_discovery": bool(capability.get("allows_design_space_discovery", True)),
                "convergence_priority": config["convergence_priority"],
                "template_source": config["template_source"],
                "planning_notes": planning_notes,
                "related_clarification_items": related_item_ids,
                "gated_by_clarification_items": gated_item_ids,
            }
        )

    return nodes


def _build_baseline_nodes(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """从 Root Skill Contract 派生 Baseline 节点。"""
    gate_item_map = _index_gate_items(clarification_gate_report)
    retained_clarifications = set(clarification_gate_report.get("retained_clarifications", []))
    nodes: List[Dict[str, Any]] = []

    for capability in root_skill_contract.get("baseline_capabilities", []):
        if capability.get("activation") != "required":
            continue

        capability_id = capability.get("capability_id", "")
        config = BASELINE_NODE_CONFIGS.get(capability_id)
        if not config:
            continue

        related_item_ids = [item_id for item_id in config.get("related_clarification_items", []) if item_id in gate_item_map]
        gated_item_ids = [item_id for item_id in related_item_ids if item_id in retained_clarifications]

        realization_class = capability.get("realization_class", "presence_only")
        allows_design_space_discovery = realization_class == "realization_eligible"

        planning_notes = list(config.get("planning_notes", []))
        planning_notes.append(f"baseline_item={capability.get('baseline_item', capability_id)}")
        for item_id in related_item_ids:
            item = gate_item_map[item_id]
            planning_notes.append(f"{item.get('topic', item_id)} -> {item.get('decision', '')}")

        nodes.append(
            {
                "instance_id": config["instance_id"],
                "capability_id": capability_id,
                "template_id": config["template_id"],
                "domain_type": "baseline",
                "status": "pending",
                "allows_design_space_discovery": allows_design_space_discovery,
                "convergence_priority": config["convergence_priority"],
                "template_source": config["template_source"],
                "planning_notes": planning_notes,
                "related_clarification_items": related_item_ids,
                "gated_by_clarification_items": gated_item_ids,
            }
        )

    return nodes


def create_skill_graph(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    run_id: str | None = None,
) -> Dict[str, Any]:
    """生成 Skill Graph。"""
    generated_at = datetime.now(timezone.utc).isoformat()
    gameplay_nodes = _build_gameplay_nodes(root_skill_contract, clarification_gate_report)
    baseline_nodes = _build_baseline_nodes(root_skill_contract, clarification_gate_report)
    nodes = gameplay_nodes + baseline_nodes
    node_ids = {node["instance_id"] for node in nodes}
    edges = _filter_edges(node_ids)
    dependency_map, coupling_map = _build_relationship_maps(edges)
    order_map = _ordered_node_ids(nodes)

    annotated_nodes = [
        _annotate_node(node, dependency_map, coupling_map, order_map)
        for node in nodes
    ]

    source_contract_id = root_skill_contract.get("contract_id", "")
    return {
        "graph_version": "1.0",
        "graph_id": _swap_prefix(source_contract_id, "rsc.", "sg."),
        "source_contract_id": source_contract_id,
        "source_gate_id": _swap_prefix(source_contract_id, "rsc.", "cg."),
        "nodes": annotated_nodes,
        "edges": edges,
        "metadata": {
            "total_gameplay_skills": len(gameplay_nodes),
            "total_baseline_skills": len(baseline_nodes),
            "total_edges": len(edges),
            "generated_at": generated_at,
            "generator": "AgentBridge.Compiler.SkillGraph.v1",
            "source_run_id": run_id,
            "retained_clarifications": clarification_gate_report.get("retained_clarifications", []),
            "provisional_item_count": len(clarification_gate_report.get("provisional_items", [])),
            "template_boundary_note": (
                "Skill Graph 只引用 template_id；运行时 Skill Instance 将在 TASK 09 创建，"
                "不会回写 Plugins/AgentBridge/SkillTemplates/。"
            ),
        },
    }


def save_skill_graph(skill_graph: Dict[str, Any], output_path: str | Path) -> str:
    """保存 Skill Graph JSON。"""
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as file:
        json.dump(skill_graph, file, ensure_ascii=False, indent=2)
    return str(target_path)
