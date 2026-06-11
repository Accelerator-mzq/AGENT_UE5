"""
Phase 11 Skill Graph Planning stage.

职责：
  - 从 Root Skill Contract 与 Clarification Gate 派生 Skill Graph
  - 规划 Gameplay / Baseline 节点、依赖边、耦合边、收敛顺序边
  - 只输出“谁先做、谁关联、谁收敛优先”，不提前写死 realization 结果

Phase 13 改造：
  - 原 GAMEPLAY_NODE_CONFIGS / BASELINE_NODE_CONFIGS 两张硬编码表删除，
    节点配置改由 registry_scan.scan_capability_registry() 数据扫描提供
  - 注册表查不到模板的 required capability 不再静默丢弃，
    显式记入 metadata.capability_gaps
  - manifest capability_binding 声明的 depends_on_capabilities 换算为依赖边
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set

logger = logging.getLogger(__name__)

PLUGIN_DIR = Path(__file__).resolve().parents[2]
BASELINE_TEMPLATES_ROOT = PLUGIN_DIR / "SkillTemplates" / "baseline"
STANDARD_TEMPLATE_FILES = {
    "manifest.yaml",
    "system_prompt.md",
    "domain_prompt.md",
    "evaluator_prompt.md",
    "input_selector.yaml",
    "output_schema.json",
}


def _load_registry_scan():
    """加载 registry_scan:包内相对导入优先,独立加载(测试场景)时按路径回退。

    等价回归测试用 importlib 无包上下文加载本模块,裸相对导入会抛
    ImportError: attempted relative import with no known parent package,
    因此必须保留按文件路径加载兄弟模块的回退分支。
    """
    try:
        from . import registry_scan  # type: ignore
        return registry_scan
    except ImportError:
        import importlib.util
        path = Path(__file__).resolve().parent / "registry_scan.py"
        spec = importlib.util.spec_from_file_location("registry_scan", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


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


def _baseline_template_dir(template_id: str) -> Path:
    """根据 baseline template_id 解析模板目录。"""
    parts = template_id.split(".")
    if len(parts) < 3 or parts[0] != "baseline":
        return BASELINE_TEMPLATES_ROOT / "__missing__"
    return BASELINE_TEMPLATES_ROOT / parts[1]


def _resolve_baseline_template_source(template_id: str) -> str:
    """解析 baseline template 是已落地模板还是未来占位模板。"""
    template_dir = _baseline_template_dir(template_id)
    if not template_dir.is_dir():
        return "future_baseline_template"

    existing_files = {path.name for path in template_dir.iterdir() if path.is_file()}
    if STANDARD_TEMPLATE_FILES.issubset(existing_files):
        return "plugin_skill_template"
    return "future_baseline_template"


def _missing_baseline_template_warning(template_id: str) -> str:
    """为缺失 baseline template 生成统一 warning 文案。"""
    return (
        f"Baseline Template 未落地：{template_id}。"
        "Skill Graph 已保留节点，但运行时应以 warning 方式提示该模板仍待补齐。"
    )


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
    registry: Dict[str, Dict[str, Any]],
    gaps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """从 Root Skill Contract 派生 Gameplay 节点;注册表查不到的能力记入 gaps。"""
    gate_item_map = _index_gate_items(clarification_gate_report)
    retained_clarifications = set(clarification_gate_report.get("retained_clarifications", []))
    nodes: List[Dict[str, Any]] = []

    for capability in root_skill_contract.get("gameplay_capabilities", []):
        if capability.get("activation") != "required":
            continue

        capability_id = capability.get("capability_id", "")
        config = registry.get(capability_id)
        if not config:
            # Phase 13: 不再静默丢弃,显式记录 capability gap
            gaps.append(
                {
                    "capability_id": capability_id,
                    "domain_type": "gameplay",
                    "reason": "no_template",
                    "source_anchor": capability.get("source_anchor", ""),
                }
            )
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
    registry: Dict[str, Dict[str, Any]],
    gaps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """从 Root Skill Contract 派生 Baseline 节点;注册表查不到的能力记入 gaps。"""
    gate_item_map = _index_gate_items(clarification_gate_report)
    retained_clarifications = set(clarification_gate_report.get("retained_clarifications", []))
    nodes: List[Dict[str, Any]] = []

    for capability in root_skill_contract.get("baseline_capabilities", []):
        if capability.get("activation") != "required":
            continue

        capability_id = capability.get("capability_id", "")
        config = registry.get(capability_id)
        if not config:
            # Phase 13: 不再静默丢弃,显式记录 capability gap
            gaps.append(
                {
                    "capability_id": capability_id,
                    "domain_type": "baseline",
                    "reason": "no_template",
                    "source_anchor": capability.get("source_anchor", ""),
                }
            )
            continue

        related_item_ids = [item_id for item_id in config.get("related_clarification_items", []) if item_id in gate_item_map]
        gated_item_ids = [item_id for item_id in related_item_ids if item_id in retained_clarifications]

        realization_class = capability.get("realization_class", "presence_only")
        allows_design_space_discovery = realization_class == "realization_eligible"
        # 终审 I-1: synthesized 模板以注册表声明为准,不走路径启发式——启发式只认
        # baseline.* 正式库目录,会把 synthesized.<cap>.v1 误判成 future_baseline_template,
        # 导致 evidence promote 守卫(只认 == "synthesized")被绕过且误报"模板未落地"。
        # 正式库 baseline 仍走运行时启发式(等价 golden 不变)。
        if config["template_source"] == "synthesized":
            template_source = "synthesized"
        else:
            template_source = _resolve_baseline_template_source(config["template_id"])

        planning_notes = list(config.get("planning_notes", []))
        planning_notes.append(f"baseline_item={capability.get('baseline_item', capability_id)}")
        for item_id in related_item_ids:
            item = gate_item_map[item_id]
            planning_notes.append(f"{item.get('topic', item_id)} -> {item.get('decision', '')}")
        # "未落地"警告只属于 future_baseline_template(占位模板);synthesized 不该触发
        if template_source == "future_baseline_template":
            planning_notes.append(_missing_baseline_template_warning(config["template_id"]))

        nodes.append(
            {
                "instance_id": config["instance_id"],
                "capability_id": capability_id,
                "template_id": config["template_id"],
                "domain_type": "baseline",
                "status": "pending",
                "allows_design_space_discovery": allows_design_space_discovery,
                "convergence_priority": config["convergence_priority"],
                "template_source": template_source,
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
    registry: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """生成 Skill Graph。

    参数:
        registry: capability_id → 节点配置映射;缺省时由 registry_scan 数据扫描提供
            (测试可注入迷你注册表)。
    """
    generated_at = datetime.now(timezone.utc).isoformat()
    if registry is None:
        registry = _load_registry_scan().scan_capability_registry()

    capability_gaps: List[Dict[str, Any]] = []
    gameplay_nodes = _build_gameplay_nodes(
        root_skill_contract, clarification_gate_report, registry, capability_gaps
    )
    baseline_nodes = _build_baseline_nodes(
        root_skill_contract, clarification_gate_report, registry, capability_gaps
    )
    nodes = gameplay_nodes + baseline_nodes
    node_ids = {node["instance_id"] for node in nodes}
    edges = _filter_edges(node_ids)

    # Phase 13: manifest capability_binding 声明的依赖换算成 instance 级依赖边。
    # 必须在 _build_relationship_maps 之前追加,否则新边不会回填到节点 dependencies。
    # 基线输入下正式库条目 depends_on_capabilities 全空,不产生新边(等价保持)。
    capability_to_instance = {cid: cfg["instance_id"] for cid, cfg in registry.items()}
    for node in nodes:
        declared = registry.get(node["capability_id"], {}).get("depends_on_capabilities", [])
        for dep_capability in declared:
            dep_instance = capability_to_instance.get(dep_capability)
            if dep_instance is None:
                # 依赖名在注册表查不到:大概率是 manifest 写错,显式告警不静默吞掉
                # (告警惯例对齐 registry_scan._scan_manifest_bindings)
                logger.warning(
                    "skill_graph_planning: 节点 %s 声明的依赖能力 %s 在注册表中不存在,"
                    "疑似 manifest depends_on_capabilities 写错,该依赖边跳过",
                    node["instance_id"],
                    dep_capability,
                )
                continue
            if dep_instance not in node_ids:
                # 依赖能力在注册表中但未入图(activation 过滤),属预期,保持静默
                continue
            edges.append(
                {
                    "from": dep_instance,
                    "to": node["instance_id"],
                    "type": "dependency",
                    "reason": f"manifest capability_binding 声明依赖 {dep_capability}。",
                }
            )

    dependency_map, coupling_map = _build_relationship_maps(edges)
    order_map = _ordered_node_ids(nodes)
    baseline_template_nodes = [node for node in baseline_nodes if node.get("template_id", "").startswith("baseline.")]
    available_baseline_templates = [
        node.get("template_id", "")
        for node in baseline_template_nodes
        if node.get("template_source") == "plugin_skill_template"
    ]
    missing_baseline_templates = [
        node.get("template_id", "")
        for node in baseline_template_nodes
        if node.get("template_source") != "plugin_skill_template"
    ]

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
            "available_baseline_templates": available_baseline_templates,
            "missing_baseline_templates": missing_baseline_templates,
            "missing_baseline_template_warnings": [
                _missing_baseline_template_warning(template_id)
                for template_id in missing_baseline_templates
            ],
            "capability_gaps": capability_gaps,
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
