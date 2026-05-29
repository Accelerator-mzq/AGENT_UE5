"""
Phase 11 Domain Skill Runtime.

职责：
  - 按 Skill Graph dependency 顺序运行节点
  - 为 Gameplay 与 realization_eligible Baseline 节点执行四重职责
  - 为 presence_only / clarification_gated baseline 生成最小 fragment
  - 聚合输出 Stage 4 的三份总览 JSON 与 skill_fragments/*
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import agent_protocol
from ..skill_runtime import skill_runtime


FRAGMENT_FAMILY_MAP = {
    "skill-board-topology": "board_topology_spec",
    "skill-tile-system": "tile_system_spec",
    "skill-turn-loop": "turn_flow_spec",
    "skill-dice": "dice_rule_spec",
    "skill-economy": "property_economy_spec",
    "skill-player-management": "player_management_spec",
    "skill-jail": "jail_rule_spec",
    "skill-baseline-start-screen": "start_screen_spec",
    "skill-baseline-main-menu": "main_menu_spec",
    "skill-baseline-settings": "settings_spec",
    "skill-baseline-pause": "pause_spec",
    "skill-baseline-results": "results_spec",
    "skill-baseline-hud": "hud_spec",
    "skill-baseline-input-foundation": "input_foundation_spec",
    "skill-baseline-audio-foundation": "audio_foundation_spec",
    "skill-baseline-platform-foundation": "platform_foundation_spec",
}

MCP_AGENT_SIDECAR_DIR = "stage4_mcp_agent_sidecar"


def _now_iso() -> str:
    """统一当前时间格式。"""
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: Dict[str, Any]) -> str:
    """以 UTF-8 写入 JSON 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(path)


def _read_json(path: Path) -> Dict[str, Any]:
    """读取 JSON 文件，不存在时返回空字典。"""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _mcp_sidecar_root(output_dir: str | Path) -> Path:
    """返回 MCP Agent Stage 4 sidecar 根目录。"""
    return Path(output_dir) / MCP_AGENT_SIDECAR_DIR


def _mcp_node_state_path(output_dir: str | Path, node_id: str) -> Path:
    """返回单节点持久化 state 路径。"""
    return _mcp_sidecar_root(output_dir) / "node_states" / f"{node_id}.json"


def _mcp_phase_trace_path(output_dir: str | Path, node_id: str, phase: str) -> Path:
    """返回单节点单阶段 trace 路径。"""
    return _mcp_sidecar_root(output_dir) / "node_traces" / node_id / f"{phase}.json"


def _mcp_aggregate_root(output_dir: str | Path) -> Path:
    """返回聚合产物目录。"""
    return _mcp_sidecar_root(output_dir) / "aggregates"


def load_mcp_node_state(output_dir: str | Path, node_id: str) -> Dict[str, Any]:
    """读取已持久化的 MCP 节点状态。"""
    return _read_json(_mcp_node_state_path(output_dir, node_id))


def _capability_map(root_skill_contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """把 capability_id 映射成对象，方便 baseline fragment 查询。"""
    mapping: Dict[str, Dict[str, Any]] = {}
    for capability in root_skill_contract.get("baseline_capabilities", []):
        mapping[capability.get("capability_id", "")] = capability
    for capability in root_skill_contract.get("gameplay_capabilities", []):
        mapping[capability.get("capability_id", "")] = capability
    return mapping


def _constraint_values(root_skill_contract: Dict[str, Any], field_paths: List[str]) -> Dict[str, Any]:
    """抽取特定 Constraint Field 的锁定值。"""
    values: Dict[str, Any] = {}
    all_constraints = root_skill_contract.get("constraint_fields", {})
    for field_path in field_paths:
        constraint = all_constraints.get(field_path)
        if not constraint:
            continue
        values[field_path] = constraint.get("value")
    return values


def _find_gate_items(
    clarification_gate_report: Dict[str, Any],
    item_ids: List[str],
) -> List[Dict[str, Any]]:
    """按 item_id 查找 Clarification Gate items。"""
    indexed = {
        item.get("item_id", ""): item
        for item in clarification_gate_report.get("items", [])
    }
    return [
        indexed[item_id]
        for item_id in item_ids
        if item_id in indexed
    ]


def _find_provisional_items(
    clarification_gate_report: Dict[str, Any],
    item_ids: List[str],
) -> List[Dict[str, Any]]:
    """按 item_id 查找 provisional_items。"""
    indexed = {
        item.get("item_id", ""): item
        for item in clarification_gate_report.get("provisional_items", [])
    }
    return [
        indexed[item_id]
        for item_id in item_ids
        if item_id in indexed
    ]


def _topological_execution_order(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """按 dependency + convergence_priority 计算稳定执行顺序。"""
    remaining = {
        node["instance_id"]: {
            "node": node,
            "dependencies": set(node.get("dependencies", [])),
        }
        for node in nodes
    }
    completed: List[str] = []
    ordered_nodes: List[Dict[str, Any]] = []

    while remaining:
        ready = [
            entry["node"]
            for entry in remaining.values()
            if entry["dependencies"].issubset(set(completed))
        ]
        if not ready:
            # 兜底防环：按 convergence_priority 和 instance_id 强行输出剩余节点。
            ready = [entry["node"] for entry in remaining.values()]

        ready.sort(
            key=lambda node: (
                node.get("convergence_priority", 999),
                node.get("instance_id", ""),
            )
        )
        for node in ready:
            instance_id = node.get("instance_id", "")
            ordered_nodes.append(node)
            completed.append(instance_id)
            remaining.pop(instance_id, None)

    return ordered_nodes


def _dimension_name_map(design_space_report: Dict[str, Any]) -> Dict[str, str]:
    """把 dimension_id 映射成名字。"""
    return {
        item.get("dimension_id", ""): item.get("name", item.get("dimension_id", ""))
        for item in design_space_report.get("discovery_dimensions", [])
    }


def _decision_impact(design_freedom: str) -> str:
    """把 design_freedom 转成 design_decision_log 的 impact。"""
    if design_freedom == "high":
        return "high"
    if design_freedom == "low":
        return "low"
    return "medium"


def _build_review_hints(node: Dict[str, Any]) -> List[str]:
    """为 fragment 生成 review hints。"""
    hints = []
    if node.get("coupling"):
        hints.append(
            "与以下耦合节点一起检查接口一致性: " + ", ".join(node.get("coupling", []))
        )
    if node.get("gated_by_clarification_items"):
        hints.append(
            "该节点依赖 retained clarification，后续 Cross Review 需重点检查 provisional 传播。"
        )
    return hints


def _build_converged_decision_log(
    node: Dict[str, Any],
    design_space_report: Dict[str, Any],
    converged_pack: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """把 converged choices 转成 design_decision_log。"""
    dimension_names = _dimension_name_map(design_space_report)
    design_logs: List[Dict[str, Any]] = []
    # 兼容 MCP Agent 路径的 convergence_decisions 命名，避免 fragment 组装时丢失收敛信息。
    convergence_choices = converged_pack.get("converged_choices") or converged_pack.get("convergence_decisions", [])
    for index, choice in enumerate(convergence_choices, start=1):
        dimension_id = choice.get("dimension_id", "")
        design_logs.append(
            {
                "decision_id": f"ddl-{node.get('instance_id', 'skill')}-{index:02d}",
                "topic": dimension_names.get(dimension_id, dimension_id),
                "context": f"{node.get('instance_id', '')} 在 Discovery 后对该维度进行了收敛选择。",
                "chosen": choice.get(
                    "chosen_candidate_name",
                    choice.get("chosen_candidate", choice.get("selected_candidate_id", "")),
                ),
                "rationale": choice.get("rationale", ""),
                "alternatives": [
                    f"{item.get('candidate_id', '')}: {item.get('rejection_reason', '')}"
                    for item in choice.get("rejected_alternatives", [])
                ],
                "provisional": bool(choice.get("provisional", False)),
                "fast_mode_default": False,
                "impact": _decision_impact(choice.get("design_freedom", "medium")),
            }
        )
    return design_logs


def _build_presence_assumptions(
    node: Dict[str, Any],
    capability: Dict[str, Any],
    fast_mode: bool = False,
) -> List[Dict[str, str]]:
    """为 presence_only baseline 生成 assumptions。"""
    assumptions = [
        {
            "assumption": "采用 presence_only 最低实现标准。",
            "basis": f"Root Skill Contract 标注 {capability.get('baseline_item', node.get('capability_id', ''))} 为 {capability.get('realization_class', 'presence_only')}。",
        }
    ]
    if fast_mode:
        assumptions.append(
            {
                "assumption": "当前 run 处于 fast_mode，Stage 4 设计空间探索已显式跳过。",
                "basis": "该模式用于调试与 CI 快速验证，产物默认不可 promote。",
            }
        )
    return assumptions


def _resolve_template_prompts(template_id: str) -> Dict[str, str]:
    """
    根据 template_id 查找 SkillTemplate 目录并加载 prompt 文件。

    查找路径：
      Plugins/AgentBridge/SkillTemplates/genre_packs/{genre}/{subgenre}/{template_dir}/
      Plugins/AgentBridge/SkillTemplates/baseline/{template_dir}/

    找不到时返回空 prompt dict（HeuristicFallbackProvider 不依赖 prompt）。
    """
    from pathlib import Path

    plugin_dir = Path(__file__).resolve().parents[2]
    templates_root = plugin_dir / "SkillTemplates"

    # 搜索 genre_packs 和 baseline 下的所有目录
    for manifest_path in templates_root.rglob("manifest.yaml"):
        try:
            import yaml
            with manifest_path.open("r", encoding="utf-8") as f:
                manifest = yaml.safe_load(f) or {}
            if manifest.get("template_id") == template_id:
                return agent_protocol.load_template_prompts(manifest_path.parent)
        except Exception:
            continue

    # 未找到模板，返回空 prompts
    return {
        "system_prompt": "",
        "domain_prompt": "",
        "evaluator_prompt": "",
        "manifest": {},
        "manifest_raw": "",
        "input_selector": {},
        "input_selector_raw": "",
    }


def _family_name(node: Dict[str, Any]) -> str:
    """返回当前节点的 emitted family 名。"""
    return FRAGMENT_FAMILY_MAP.get(
        node.get("instance_id", ""),
        node.get("instance_id", "skill").replace("skill-", "").replace("-", "_") + "_spec",
    )


def _selected_realization_from_converged(converged_pack: Dict[str, Any] | None) -> Dict[str, Any]:
    """从 converged_pack 提取 dimension_id -> chosen 候选 的映射。

    兼容 converged_choices / convergence_decisions 两种键，
    以及 chosen_candidate_name / chosen_candidate / selected_candidate_id 三种候选字段。
    与 _build_gameplay_spec_fragment 行内逻辑保持一致，供 baseline 复用。
    当前仅新增、暂不替换 _build_gameplay_spec_fragment 行内块（保持 gameplay 路径不变）；Task 2 起由 baseline 路径调用。
    """
    if not converged_pack:
        return {}
    convergence_choices = (
        converged_pack.get("converged_choices")
        or converged_pack.get("convergence_decisions", [])
    )
    return {
        choice.get("dimension_id", ""): choice.get(
            "chosen_candidate_name",
            choice.get("chosen_candidate", choice.get("selected_candidate_id", "")),
        )
        for choice in convergence_choices
    }


def _build_gameplay_spec_fragment(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    converged_pack: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
) -> Dict[str, Any]:
    """为 gameplay 节点构建 spec_fragments。"""
    instance_id = node.get("instance_id", "")
    family_name = _family_name(node)
    retained_items = _find_gate_items(
        clarification_gate_report,
        node.get("related_clarification_items", []),
    )
    provisional_items = _find_provisional_items(
        clarification_gate_report,
        node.get("gated_by_clarification_items", []),
    )

    convergence_choices = converged_pack.get("converged_choices") or converged_pack.get("convergence_decisions", [])
    dimension_choices = {
        choice.get("dimension_id", ""): choice.get(
            "chosen_candidate_name",
            choice.get("chosen_candidate", choice.get("selected_candidate_id", "")),
        )
        for choice in convergence_choices
    }

    field_map: Dict[str, List[str]] = {
        "skill-board-topology": [
            "board.tile_count",
            "board.layout_shape",
            "board.movement_direction",
            "board.corner_indices",
        ],
        "skill-tile-system": [
            "board.tile_count",
            "board.corner_indices",
            "property.full_color_group_rent_multiplier",
        ],
        "skill-turn-loop": [
            "dice.count",
            "dice.sides",
            "dice.doubles_extra_turn",
            "dice.triple_doubles_jail",
            "economy.start_bonus",
        ],
        "skill-dice": [
            "dice.count",
            "dice.sides",
            "dice.doubles_extra_turn",
            "dice.triple_doubles_jail",
        ],
        "skill-economy": [
            "economy.starting_cash",
            "economy.start_bonus",
            "property.full_color_group_rent_multiplier",
        ],
        "skill-player-management": [
            "game.player_count_range",
            "game.win_condition",
            "game.match_length_minutes",
        ],
        "skill-jail": [
            "jail.visit_tile_index",
            "jail.bail_cost",
            "jail.max_turns",
        ],
    }

    spec = {
        "capability_id": node.get("capability_id", ""),
        "template_id": node.get("template_id", ""),
        "locked_constraints": _constraint_values(root_skill_contract, field_map.get(instance_id, [])),
        "selected_realization": dimension_choices,
        "clarification_inputs": [
            {
                "item_id": item.get("item_id", ""),
                "decision": item.get("decision", ""),
                "topic": item.get("topic", ""),
            }
            for item in retained_items
        ],
        "dependencies": list(node.get("dependencies", [])),
        "coupling": list(node.get("coupling", [])),
    }

    # 为关键 Monopoly 节点补更语义化的字段，方便后续 TASK 10/11 消费。
    # 使用 _cv() 安全提取 Constraint Field 值，缺失时返回 None。
    def _cv(field_path: str):
        return root_skill_contract.get("constraint_fields", {}).get(field_path, {}).get("value")

    if instance_id == "skill-board-topology":
        spec.update(
            {
                "tile_count": _cv("board.tile_count"),
                "layout_shape": _cv("board.layout_shape"),
                "movement_direction": _cv("board.movement_direction"),
                "corner_tiles": _cv("board.corner_indices"),
            }
        )
    elif instance_id == "skill-tile-system":
        spec.update(
            {
                "tile_count": _cv("board.tile_count"),
                "phase1_empty_event_policy": "chance/community no-op",
                "color_group_rent_multiplier": _cv("property.full_color_group_rent_multiplier"),
            }
        )
    elif instance_id == "skill-turn-loop":
        spec.update(
            {
                "turn_core": "roll -> move -> resolve tile -> evaluate doubles -> next player",
                "start_bonus": _cv("economy.start_bonus"),
                "provisional_stalemate_policy": provisional_items[0].get("provisional_value", "") if provisional_items else "",
            }
        )
    elif instance_id == "skill-dice":
        spec.update(
            {
                "dice_count": _cv("dice.count"),
                "dice_sides": _cv("dice.sides"),
                "doubles_extra_turn": _cv("dice.doubles_extra_turn"),
                "triple_doubles_jail": _cv("dice.triple_doubles_jail"),
            }
        )
    elif instance_id == "skill-economy":
        spec.update(
            {
                "starting_cash": _cv("economy.starting_cash"),
                "start_bonus": _cv("economy.start_bonus"),
                "full_color_group_rent_multiplier": _cv("property.full_color_group_rent_multiplier"),
            }
        )
    elif instance_id == "skill-player-management":
        spec.update(
            {
                "player_count_range": _cv("game.player_count_range"),
                "win_condition": _cv("game.win_condition"),
                "provisional_round_limit": provisional_items[0].get("provisional_value", "") if provisional_items else "",
            }
        )
    elif instance_id == "skill-jail":
        spec.update(
            {
                "jail_tile_index": _cv("jail.visit_tile_index"),
                "bail_cost": _cv("jail.bail_cost"),
                "max_jail_turns": _cv("jail.max_turns"),
            }
        )

    return {family_name: spec}


def _build_baseline_spec_fragment(
    node: Dict[str, Any],
    capability: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    converged_pack: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """为 baseline 节点构建最小 spec_fragments。"""
    family_name = _family_name(node)
    spec = {
        "capability": capability.get("baseline_item", node.get("capability_id", "")),
        "realization_class": capability.get("realization_class", "presence_only"),
        "required_elements": capability.get("required_elements", []),
        "required_controls": capability.get("required_controls", []),
        "activation": capability.get("activation", "required"),
    }

    provisional_items = _find_provisional_items(
        clarification_gate_report,
        node.get("gated_by_clarification_items", []),
    )
    if provisional_items:
        spec["provisional_defaults"] = [
            {
                "item_id": item.get("item_id", ""),
                "value": item.get("provisional_value", ""),
            }
            for item in provisional_items
        ]

    if node.get("instance_id") == "skill-baseline-hud":
        spec["required_elements"] = capability.get("required_elements", [])
        spec["notes"] = "HUD 为 realization_eligible baseline，后续可结合 gameplay state 细化。"
    if node.get("instance_id") == "skill-baseline-settings":
        spec["persistence"] = "session_only"
    if node.get("instance_id") == "skill-baseline-platform-foundation":
        spec["platform_scope"] = "desktop_local_runtime"

    # realization_eligible baseline 与 gameplay 对称：把发散收敛结果写入 spec。
    if capability.get("realization_class") == "realization_eligible":
        selected_realization = _selected_realization_from_converged(converged_pack)
        if selected_realization:
            spec["selected_realization"] = selected_realization

    return {family_name: spec}


def _build_presence_fragment(
    node: Dict[str, Any],
    capability: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    phase_scope: str,
    fast_mode: bool = False,
    root_skill_contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """为 presence_only / fast_mode 默认路径生成 fragment。"""
    provisional_items = _find_provisional_items(
        clarification_gate_report,
        node.get("gated_by_clarification_items", []),
    )
    domain_type = node.get("domain_type", "baseline")
    design_decision_log = []
    if fast_mode:
        design_decision_log.append(
            {
                "decision_id": f"ddl-{node.get('instance_id', 'baseline')}-fast-mode",
                "topic": "fast_mode 默认实现",
                "context": "当前 run 以 fast_mode 执行，Discovery / Candidates / Convergence 被显式跳过。",
                "chosen": "presence_only_default",
                "rationale": "优先保证调试与 CI 的最小可运行闭环，同时明确该 fragment 不能作为 promoted baseline。",
                "alternatives": [],
                "provisional": True,
                "fast_mode_default": True,
                "impact": "medium",
            }
        )
    if provisional_items:
        for item in provisional_items:
            decision_index = len(design_decision_log) + 1
            design_decision_log.append(
                {
                    "decision_id": f"ddl-{node.get('instance_id', 'baseline')}-{decision_index:02d}",
                    "topic": item.get("topic", ""),
                    "context": "当前 baseline 域仍受 Clarification Gate 约束，先使用 provisional default 保持主链可运行。",
                    "chosen": str(item.get("provisional_value", "")),
                    "rationale": "继续推进 Phase 11 主链，同时保留后续重做与追溯能力。",
                    "alternatives": [],
                    "provisional": True,
                    "fast_mode_default": fast_mode,
                    "impact": "high",
                }
            )

    status = "completed"
    if domain_type == "gameplay" and root_skill_contract is not None:
        spec_fragments = _build_gameplay_spec_fragment(
            node=node,
            root_skill_contract=root_skill_contract,
            converged_pack={},
            clarification_gate_report=clarification_gate_report,
        )
        assumptions = [
            {
                "assumption": "当前 gameplay 节点按 fast_mode 最小约束输出。",
                "basis": "保留 locked_constraints、dependencies 与 clarification 输入，但跳过 design space 探索。",
            }
        ]
        if fast_mode:
            assumptions.append(
                {
                    "assumption": "selected_realization 在 fast_mode 下保持为空。",
                    "basis": "该模式只验证编译链路可执行性，不产出可 promote 的收敛设计决策。",
                }
            )
    else:
        spec_fragments = _build_baseline_spec_fragment(node, capability, clarification_gate_report)
        assumptions = _build_presence_assumptions(node, capability, fast_mode=fast_mode)

    return {
        "fragment_version": "2.0",
        "skill_instance_id": node.get("instance_id", ""),
        "template_id": node.get("template_id", ""),
        "domain_type": domain_type,
        "phase_scope": phase_scope,
        "status": status,
        "emitted_families": [_family_name(node)],
        "spec_fragments": spec_fragments,
        "design_decision_log": design_decision_log,
        "assumptions": assumptions,
        "open_questions": [
            item.get("topic", "")
            for item in _find_gate_items(
                clarification_gate_report,
                node.get("gated_by_clarification_items", []),
            )
        ],
        "review_hints": _build_review_hints(node),
        "capability_gaps": [],
        "confidence": {
            "coverage": 0.92 if not provisional_items else 0.75,
            "consistency": 0.95 if not provisional_items else 0.8,
        },
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.DomainSkillRuntime.v1",
            "template_version": "1.0",
            "fast_mode_default": fast_mode,
        },
    }


def _build_discovered_fragment(
    node: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    design_space_report: Dict[str, Any],
    converged_pack: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, Any]:
    """为 gameplay / realization_eligible baseline 节点生成完整 fragment。"""
    is_baseline = node.get("domain_type") == "baseline"
    design_decision_log = _build_converged_decision_log(node, design_space_report, converged_pack)
    spec_fragments = (
        _build_baseline_spec_fragment(node, {"baseline_item": "HUD", "realization_class": "realization_eligible", "required_elements": root_skill_contract["constraint_fields"]["ui.required_hud_fields"]["value"]}, clarification_gate_report)
        if is_baseline
        else _build_gameplay_spec_fragment(node, root_skill_contract, converged_pack, clarification_gate_report)
    )

    retained_gate_items = _find_gate_items(
        clarification_gate_report,
        node.get("related_clarification_items", []),
    )
    provisional_items = _find_provisional_items(
        clarification_gate_report,
        node.get("gated_by_clarification_items", []),
    )

    assumptions = []
    if provisional_items:
        for item in provisional_items:
            assumptions.append(
                {
                    "assumption": str(item.get("provisional_value", "")),
                    "basis": f"{item.get('topic', '')} 当前仍为 clarification_required，先采用 provisional default。",
                }
            )

    return {
        "fragment_version": "2.0",
        "skill_instance_id": node.get("instance_id", ""),
        "template_id": node.get("template_id", ""),
        "domain_type": node.get("domain_type", "gameplay"),
        "phase_scope": phase_scope,
        "status": "completed",
        "emitted_families": [_family_name(node)],
        "spec_fragments": spec_fragments,
        "design_decision_log": design_decision_log,
        "assumptions": assumptions,
        "open_questions": [item.get("topic", "") for item in retained_gate_items if item.get("decision") == "clarification_required"],
        "review_hints": _build_review_hints(node),
        "capability_gaps": [],
        "confidence": {
            "coverage": 0.9 if not provisional_items else 0.82,
            "consistency": 0.9 if not provisional_items else 0.83,
        },
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.DomainSkillRuntime.v1",
            "template_version": "1.0",
        },
    }


def _aggregate_design_space(
    entries: List[Dict[str, Any]],
    root_skill_contract: Dict[str, Any],
    skill_graph: Dict[str, Any],
    lifecycle_records: List[Dict[str, Any]],
    execution_order: List[str],
    final_status_map: Dict[str, str],
) -> Dict[str, Any]:
    """把 per-skill design space 合并成 Stage 4 总览对象。"""
    return {
        "report_version": "1.0",
        "skill_instance_id": "skill-aggregate-design-space",
        "source_contract_id": root_skill_contract.get("contract_id", ""),
        "source_graph_id": skill_graph.get("graph_id", ""),
        "discovery_dimensions": [
            dimension
            for entry in entries
            for dimension in entry.get("discovery_dimensions", [])
        ],
        "locked_dimensions": [
            dimension
            for entry in entries
            for dimension in entry.get("locked_dimensions", [])
        ],
        "entries": entries,
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.DesignSpaceDiscovery.v1",
            "entry_count": len(entries),
            "execution_order": execution_order,
            "lifecycle_records": lifecycle_records,
            "final_status_map": final_status_map,
        },
    }


def _aggregate_candidates(
    entries: List[Dict[str, Any]],
    lifecycle_records: List[Dict[str, Any]],
    execution_order: List[str],
    final_status_map: Dict[str, str],
) -> Dict[str, Any]:
    """把 per-skill realization candidates 合并成 Stage 4 总览对象。"""
    return {
        "candidates_version": "1.0",
        "skill_instance_id": "skill-aggregate-realization-candidates",
        "source_design_space_report": "design_space_report.json",
        "candidates": [
            candidate_group
            for entry in entries
            for candidate_group in entry.get("candidates", [])
        ],
        "entries": entries,
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.RealizationCandidates.v1",
            "entry_count": len(entries),
            "execution_order": execution_order,
            "lifecycle_records": lifecycle_records,
            "final_status_map": final_status_map,
        },
    }


def _aggregate_converged_pack(
    entries: List[Dict[str, Any]],
    lifecycle_records: List[Dict[str, Any]],
    execution_order: List[str],
    final_status_map: Dict[str, str],
) -> Dict[str, Any]:
    """把 per-skill converged packs 合并成 Stage 4 总览对象。"""
    conflicts = [
        conflict
        for entry in entries
        for conflict in entry.get("cross_dimension_consistency", {}).get("conflicts", [])
    ]
    return {
        "pack_version": "1.0",
        "skill_instance_id": "skill-aggregate-converged-pack",
        "source_candidates": "realization_candidates.json",
        "converged_choices": [
            choice
            for entry in entries
            for choice in entry.get("converged_choices", [])
        ],
        "cross_dimension_consistency": {
            "checked": True,
            "conflicts": conflicts,
        },
        "entries": entries,
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.Convergence.v1",
            "entry_count": len(entries),
            "execution_order": execution_order,
            "lifecycle_records": lifecycle_records,
            "final_status_map": final_status_map,
        },
    }


def _lifecycle_record(
    node: Dict[str, Any],
    status: str,
    mode: str,
    execution_index: int,
    failure_reason: str = "",
) -> Dict[str, Any]:
    """构造 lifecycle record。"""
    record = {
        "skill_instance_id": node.get("instance_id", ""),
        "domain_type": node.get("domain_type", ""),
        "status": status,
        "mode": mode,
        "execution_index": execution_index,
        "allows_design_space_discovery": bool(node.get("allows_design_space_discovery", False)),
    }
    if failure_reason:
        record["failure_reason"] = failure_reason
    return record


def _collect_coupled_summaries(
    node: Dict[str, Any],
    converged_entries: List[Dict[str, Any]],
    status_map: Dict[str, str],
) -> Dict[str, Any]:
    """收集当前节点的耦合域已收敛方向摘要。"""
    summaries: Dict[str, Any] = {}
    coupling_ids = node.get("coupling", [])
    for entry in converged_entries:
        entry_id = entry.get("skill_instance_id", "")
        if entry_id in coupling_ids and status_map.get(entry_id) == "completed":
            summaries[entry_id] = {
                "converged_choices_count": len(entry.get("converged_choices", [])),
                "has_conflicts": len(entry.get("cross_dimension_consistency", {}).get("conflicts", [])) > 0,
            }
    return summaries


def _build_failed_fragment(node: Dict[str, Any], failure_reason: str) -> Dict[str, Any]:
    """为失败的节点生成占位 fragment。"""
    instance_id = node.get("instance_id", "")
    family = _family_name(node)
    return {
        "fragment_version": "2.0",
        "skill_instance_id": instance_id,
        "template_id": node.get("template_id", ""),
        "status": "failed",
        "failure_reason": failure_reason,
        "emitted_families": [family],
        "spec_fragments": {},
        "design_decision_log": [],
        "assumptions": [],
        "open_questions": [{"question": f"节点执行失败: {failure_reason}", "severity": "high"}],
        "capability_gaps": [],
        "confidence": {"coverage": 0.0, "consistency": 0.0},
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.DomainSkillRuntime.v1",
            "template_version": "1.0",
        },
    }


def _extract_selected_realization(fragment: Dict[str, Any]) -> Dict[str, Any]:
    """从 fragment 中提取 selected_realization，供 Stage 4 验收使用。"""
    spec_fragments = fragment.get("spec_fragments", {})
    if not isinstance(spec_fragments, dict):
        return {}

    for spec in spec_fragments.values():
        if not isinstance(spec, dict):
            continue
        selected = spec.get("selected_realization", {})
        if isinstance(selected, dict):
            return selected
    return {}


def _validate_stage4_node_acceptance(
    design_space_report: Dict[str, Any],
    realization_candidates: Dict[str, Any],
    converged_pack: Dict[str, Any],
    fragment: Dict[str, Any],
) -> List[str]:
    """对 discovery-capable 节点执行更严格的 Stage 4 验收。"""
    errors: List[str] = []

    if design_space_report.get("parse_error"):
        errors.append("design_space_report 出现 parse_error。")
    if not design_space_report.get("discovery_dimensions"):
        errors.append("discovery_dimensions 不能为空。")

    if realization_candidates.get("parse_error"):
        errors.append("realization_candidates 出现 parse_error。")
    if not realization_candidates.get("candidates"):
        errors.append("candidates 不能为空。")

    converged_choices = converged_pack.get("converged_choices") or converged_pack.get("convergence_decisions", [])
    if converged_pack.get("parse_error"):
        errors.append("converged_realization_pack 出现 parse_error。")
    if not converged_choices:
        errors.append("converged_choices 不能为空。")

    selected_realization = _extract_selected_realization(fragment)
    if not selected_realization:
        errors.append("fragment.selected_realization 不能为空。")

    return errors


def run_domain_skill_runtime(
    skill_graph: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    phase_scope: str,
    fast_mode: bool = False,
    allow_heuristic_fallback: bool = True,
    llm_client: Any = None,
    *,
    router: Any = None,                  # Phase 12 新路径:CapabilityRouter
    policy: Any = None,                  # ProviderPolicy
    batch_concurrency: int = 3,
    retry_policy: Any = None,            # F1 follow-up:RetryPolicySpec(仅作用于 router 路径)
) -> Dict[str, Any]:
    """
    执行 Stage 4 Domain Skill Runtime。

    Generator 驱动策略（方案 B: Prompt-First）：
      - 有 router + policy → LLMProvider(router, policy, batch_concurrency) — Phase 12 新路径
      - 有 llm_client → LLMProvider（SkillTemplate prompt 驱动）— 老路径
      - 无 llm_client 且 allow_heuristic_fallback=True → HeuristicFallbackProvider
      - 无 llm_client 且 allow_heuristic_fallback=False → 拒绝执行
    """
    # 解析 Generator provider（Doc 14 §4 硬约束）
    try:
        provider = agent_protocol.resolve_provider(
            allow_heuristic_fallback=allow_heuristic_fallback,
            llm_client=llm_client,
            router=router,
            policy=policy,
            batch_concurrency=batch_concurrency,
            retry_policy=retry_policy,
        )
    except agent_protocol.ProviderNotAvailable as exc:
        return {
            "status": "refused",
            "failure_reason": str(exc),
            "design_space_report": {},
            "realization_candidates": {},
            "converged_realization_pack": {},
            "skill_fragments": [],
            "stage4_agent_traces": [],
        }

    capability_map = _capability_map(root_skill_contract)
    ordered_nodes = _topological_execution_order(skill_graph.get("nodes", []))
    execution_order = [node.get("instance_id", "") for node in ordered_nodes]

    design_space_entries: List[Dict[str, Any]] = []
    candidate_entries: List[Dict[str, Any]] = []
    converged_entries: List[Dict[str, Any]] = []
    fragments: List[Dict[str, Any]] = []
    lifecycle_records: List[Dict[str, Any]] = []
    all_traces: List[Dict[str, Any]] = []
    status_map: Dict[str, str] = {}
    discovery_capable_nodes = [
        node
        for node in ordered_nodes
        if node.get("allows_design_space_discovery", False) and not fast_mode
    ]

    for execution_index, node in enumerate(ordered_nodes, start=1):
        instance_id = node.get("instance_id", "")
        dependency_statuses = [
            status_map.get(dependency_id, "pending")
            for dependency_id in node.get("dependencies", [])
        ]
        if any(status != "completed" for status in dependency_statuses):
            lifecycle_records.append(
                _lifecycle_record(
                    node,
                    status="failed",
                    mode="dependency_blocked",
                    execution_index=execution_index,
                    failure_reason="dependencies_not_completed",
                )
            )
            status_map[instance_id] = "failed"
            fragments.append(
                {
                    "fragment_version": "2.0",
                    "skill_instance_id": instance_id,
                    "template_id": node.get("template_id", ""),
                    "domain_type": node.get("domain_type", ""),
                    "phase_scope": phase_scope,
                    "status": "failed",
                    "emitted_families": [],
                    "spec_fragments": {},
                    "design_decision_log": [],
                    "assumptions": [],
                    "open_questions": [],
                    "review_hints": _build_review_hints(node),
                    "capability_gaps": [],
                    "failure_reason": "dependencies_not_completed",
                    "confidence": {
                        "coverage": 0.0,
                        "consistency": 0.0,
                    },
                    "metadata": {
                        "generated_at": _now_iso(),
                        "generator": "AgentBridge.Compiler.DomainSkillRuntime.v1",
                        "template_version": "1.0",
                    },
                }
            )
            continue

        lifecycle_records.append(
            _lifecycle_record(
                node,
                status="running",
                mode=(
                    "discovery"
                    if node.get("allows_design_space_discovery", False) and not fast_mode
                    else ("fast_mode_default" if fast_mode else "presence_only")
                ),
                execution_index=execution_index,
            )
        )

        capability = capability_map.get(node.get("capability_id", ""), {})
        if node.get("allows_design_space_discovery", False) and not fast_mode:
            # 构建 Context Bundle（Doc 14 §3）
            context_bundle = agent_protocol.build_context_bundle(
                node=node,
                root_skill_contract=root_skill_contract,
                clarification_gate_report=clarification_gate_report,
                skill_graph=skill_graph,
                coupled_domain_summaries=_collect_coupled_summaries(
                    node, converged_entries, status_map
                ),
            )

            # 加载 SkillTemplate prompt（Doc 14 §6: prompt 文件是 Generator 唯一驱动源）
            template_id = node.get("template_id", "")
            template_prompts = _resolve_template_prompts(template_id)

            # 执行三阶段 Agent 协议（Provider 驱动的 Generator-Evaluator 门控）
            agent_result = agent_protocol.run_agent_stage4_for_node(
                node=node,
                context_bundle=context_bundle,
                template_prompts=template_prompts,
                provider=provider,
                root_skill_contract=root_skill_contract,
                clarification_gate_report=clarification_gate_report,
                skill_graph=skill_graph,
                max_retries=2,
                phase_scope=phase_scope,
            )

            # 收集 trace（审计 sidecar）
            node_traces = agent_result.get("traces", [])
            all_traces.extend(node_traces)

            if agent_result.get("status") == "failed":
                status_map[instance_id] = "failed"
                lifecycle_records.append(
                    _lifecycle_record(
                        node,
                        status="failed",
                        mode="agent_protocol",
                        execution_index=execution_index,
                        failure_reason=agent_result.get("failure_reason", "unknown"),
                    )
                )
                # 生成失败占位 fragment
                fragments.append(_build_failed_fragment(node, agent_result.get("failure_reason", "")))
                continue

            design_space_report = agent_result["design_space_report"]
            realization_candidates = agent_result["realization_candidates"]
            converged_pack = agent_result["converged_realization_pack"]

            fragment = _build_discovered_fragment(
                node=node,
                root_skill_contract=root_skill_contract,
                clarification_gate_report=clarification_gate_report,
                design_space_report=design_space_report,
                converged_pack=converged_pack,
                phase_scope=phase_scope,
            )

            node_acceptance_errors = _validate_stage4_node_acceptance(
                design_space_report=design_space_report,
                realization_candidates=realization_candidates,
                converged_pack=converged_pack,
                fragment=fragment,
            )
            if node_acceptance_errors:
                failure_reason = "stage4_acceptance_failed: " + " | ".join(node_acceptance_errors)
                status_map[instance_id] = "failed"
                lifecycle_records.append(
                    _lifecycle_record(
                        node,
                        status="failed",
                        mode="agent_protocol",
                        execution_index=execution_index,
                        failure_reason=failure_reason,
                    )
                )
                fragments.append(_build_failed_fragment(node, failure_reason))
                continue

            design_space_entries.append(design_space_report)
            candidate_entries.append(realization_candidates)
            converged_entries.append(converged_pack)
            fragments.append(fragment)
            status_map[instance_id] = "completed"
            lifecycle_records.append(
                _lifecycle_record(
                    node,
                    status="completed",
                    mode="agent_protocol",
                    execution_index=execution_index,
                )
            )
        else:
            fragment = _build_presence_fragment(
                node=node,
                capability=capability,
                clarification_gate_report=clarification_gate_report,
                phase_scope=phase_scope,
                fast_mode=fast_mode,
                root_skill_contract=root_skill_contract,
            )
            fragments.append(fragment)
            status_map[instance_id] = "completed"
            lifecycle_records.append(
                _lifecycle_record(
                    node,
                    status="completed",
                    mode="presence_only" if not fast_mode else "fast_mode_default",
                    execution_index=execution_index,
                )
            )

    acceptance_errors: List[str] = []
    if discovery_capable_nodes:
        if not design_space_entries:
            acceptance_errors.append("LLM/MCP Discovery 验收失败：design_space entries 为空。")
        if not candidate_entries:
            acceptance_errors.append("LLM/MCP Candidates 验收失败：candidates entries 为空。")
        if not converged_entries:
            acceptance_errors.append("LLM/MCP Convergence 验收失败：converged entries 为空。")

        completed_discovery_fragments = [
            fragment
            for fragment in fragments
            if fragment.get("status") == "completed"
            and _extract_selected_realization(fragment)
        ]
        if not completed_discovery_fragments:
            acceptance_errors.append("Stage 4 验收失败：所有 discovery-capable fragment 的 selected_realization 均为空。")

        fragments_with_decision_log = [
            fragment
            for fragment in completed_discovery_fragments
            if fragment.get("design_decision_log")
        ]
        if not fragments_with_decision_log:
            acceptance_errors.append("Stage 4 验收失败：所有 discovery-capable fragment 的 design_decision_log 均为空。")

    status = "validation_failed" if acceptance_errors else "completed"
    stage4_promotable = (not fast_mode) and provider.provider_type != "heuristic_fallback"
    design_space_report = _aggregate_design_space(
        entries=design_space_entries,
        root_skill_contract=root_skill_contract,
        skill_graph=skill_graph,
        lifecycle_records=lifecycle_records,
        execution_order=execution_order,
        final_status_map=status_map,
    )
    design_space_report.setdefault("metadata", {})
    design_space_report["metadata"]["generator_type"] = "fast_mode_default" if fast_mode else provider.provider_type
    design_space_report["metadata"]["promotable"] = stage4_promotable
    design_space_report["metadata"]["fast_mode_skipped"] = fast_mode
    design_space_report["metadata"]["clarification_gate_policy"] = clarification_gate_report.get(
        "clarification_gate_policy",
        "",
    )

    realization_candidates = _aggregate_candidates(
        entries=candidate_entries,
        lifecycle_records=lifecycle_records,
        execution_order=execution_order,
        final_status_map=status_map,
    )
    realization_candidates.setdefault("metadata", {})
    realization_candidates["metadata"]["generator_type"] = "fast_mode_default" if fast_mode else provider.provider_type
    realization_candidates["metadata"]["promotable"] = stage4_promotable
    realization_candidates["metadata"]["fast_mode_skipped"] = fast_mode
    realization_candidates["metadata"]["clarification_gate_policy"] = clarification_gate_report.get(
        "clarification_gate_policy",
        "",
    )

    converged_realization_pack = _aggregate_converged_pack(
        entries=converged_entries,
        lifecycle_records=lifecycle_records,
        execution_order=execution_order,
        final_status_map=status_map,
    )
    converged_realization_pack.setdefault("metadata", {})
    converged_realization_pack["metadata"]["generator_type"] = "fast_mode_default" if fast_mode else provider.provider_type
    converged_realization_pack["metadata"]["promotable"] = stage4_promotable
    converged_realization_pack["metadata"]["fast_mode_skipped"] = fast_mode
    converged_realization_pack["metadata"]["clarification_gate_policy"] = clarification_gate_report.get(
        "clarification_gate_policy",
        "",
    )

    return {
        "status": status,
        "design_space_report": design_space_report,
        "realization_candidates": realization_candidates,
        "converged_realization_pack": converged_realization_pack,
        "skill_fragments": fragments,
        "lifecycle_records": lifecycle_records,
        "execution_order": execution_order,
        "final_status_map": status_map,
        "stage4_agent_traces": all_traces,
        "generator_provider_type": provider.provider_type,
        "acceptance_errors": acceptance_errors,
    }


# ---------------------------------------------------------------------------
# MCP Interactive Mode: 逐节点 prepare/save（Agent 即 Generator）
# ---------------------------------------------------------------------------

VALID_STAGE4_PHASES = {"discovery", "candidates", "convergence"}


def _normalize_mcp_discovery_output(node: Dict[str, Any], output: Dict[str, Any]) -> Dict[str, Any]:
    """把 MCP Agent 的 discovery 输出归一化到 design_space_report 条目结构。"""
    raw_dimensions = output.get("discovery_dimensions") or output.get("open_dimensions") or []
    raw_locked = output.get("locked_dimensions", []) or []

    discovery_dimensions = []
    for item in raw_dimensions:
        dimension_id = item.get("dimension_id") or item.get("field_path") or ""
        discovery_dimensions.append(
            {
                "dimension_id": dimension_id,
                "name": item.get("name", dimension_id),
                "description": item.get("description", ""),
                "constraint_source": "variant",
                "variant_bounds": item.get("variant_bounds", {"must_satisfy": [], "must_not": []}),
                "gdd_hints": item.get("gdd_hints", []),
                "coupled_dimensions": item.get("coupled_dimensions", []),
                "design_freedom": item.get("design_freedom", "medium"),
                "exploration_range": item.get("exploration_range", ""),
            }
        )

    locked_dimensions = []
    for item in raw_locked:
        dimension_id = item.get("dimension_id") or item.get("field_path") or ""
        locked_dimensions.append(
            {
                "dimension_id": dimension_id,
                "name": item.get("name", dimension_id),
                "constraint_source": "constraint",
                "locked_value": item.get("locked_value"),
                "reason": item.get("reason", f"{dimension_id} 为锁定约束"),
                "field_path": item.get("field_path", dimension_id),
            }
        )

    metadata = dict(output.get("metadata", {}))
    metadata.setdefault("generated_at", _now_iso())
    metadata.setdefault("generator", "AgentBridge.Compiler.MCPAgent.Discovery.v1")
    metadata["generator_type"] = "mcp_agent"
    metadata["promotable"] = True

    return {
        "report_version": "1.0",
        "skill_instance_id": node.get("instance_id", ""),
        "template_id": node.get("template_id", ""),
        "discovery_dimensions": discovery_dimensions,
        "locked_dimensions": locked_dimensions,
        "metadata": metadata,
    }


def _normalize_mcp_candidates_output(node: Dict[str, Any], output: Dict[str, Any]) -> Dict[str, Any]:
    """把 MCP Agent 的 candidates 输出归一化到 realization_candidates 条目结构。"""
    raw_groups = output.get("candidates") or output.get("dimensions") or []
    normalized_groups = []
    for group in raw_groups:
        normalized_candidates = []
        for candidate in group.get("candidates", []) or []:
            trade_offs = candidate.get("trade_offs")
            if not isinstance(trade_offs, dict):
                trade_off_text = candidate.get("trade_off", "")
                trade_offs = {
                    "pros": [trade_off_text] if trade_off_text else [],
                    "cons": [],
                }
            normalized_candidates.append(
                {
                    "candidate_id": candidate.get("candidate_id", ""),
                    "name": candidate.get("name", candidate.get("candidate_id", "")),
                    "description": candidate.get("description", ""),
                    "trade_offs": {
                        "pros": trade_offs.get("pros", []),
                        "cons": trade_offs.get("cons", []),
                    },
                    "satisfies_bounds": candidate.get("satisfies_bounds", True),
                    "estimated_complexity": candidate.get(
                        "estimated_complexity",
                        candidate.get("complexity_tier", "medium"),
                    ),
                    "compatible_with": candidate.get("compatible_with", []),
                    "conflicts_with": candidate.get("conflicts_with", []),
                }
            )
        normalized_groups.append(
            {
                "dimension_id": group.get("dimension_id", ""),
                "candidates": normalized_candidates,
            }
        )

    metadata = dict(output.get("metadata", {}))
    metadata.setdefault("generated_at", _now_iso())
    metadata.setdefault("generator", "AgentBridge.Compiler.MCPAgent.Candidates.v1")
    metadata["generator_type"] = "mcp_agent"
    metadata["promotable"] = True

    return {
        "candidates_version": "1.0",
        "skill_instance_id": node.get("instance_id", ""),
        "template_id": node.get("template_id", ""),
        "source_design_space_report": "design_space_report.json",
        "candidates": normalized_groups,
        "metadata": metadata,
    }


def _normalize_mcp_convergence_output(node: Dict[str, Any], output: Dict[str, Any]) -> Dict[str, Any]:
    """把 MCP Agent 的 convergence 输出归一化到 converged_realization_pack 条目结构。"""
    raw_choices = output.get("converged_choices") or output.get("convergence_decisions") or []
    normalized_choices = []
    for choice in raw_choices:
        normalized_choices.append(
            {
                "dimension_id": choice.get("dimension_id", ""),
                "chosen_candidate": choice.get(
                    "chosen_candidate",
                    choice.get("selected_candidate_id", ""),
                ),
                "chosen_candidate_name": choice.get("chosen_candidate_name", ""),
                "rationale": choice.get("rationale", ""),
                "rejected_alternatives": choice.get("rejected_alternatives", []),
                "human_confirmation_needed": choice.get(
                    "human_confirmation_needed",
                    bool(choice.get("provisional", False)),
                ),
                "provisional": bool(choice.get("provisional", False)),
                "design_freedom": choice.get("design_freedom", "medium"),
            }
        )

    metadata = dict(output.get("metadata", {}))
    metadata.setdefault("generated_at", _now_iso())
    metadata.setdefault("generator", "AgentBridge.Compiler.MCPAgent.Convergence.v1")
    metadata["generator_type"] = "mcp_agent"
    metadata["promotable"] = True

    return {
        "pack_version": "1.0",
        "skill_instance_id": node.get("instance_id", ""),
        "template_id": node.get("template_id", ""),
        "source_candidates": "realization_candidates.json",
        "converged_choices": normalized_choices,
        "cross_dimension_consistency": output.get(
            "cross_dimension_consistency",
            {"checked": True, "conflicts": []},
        ),
        "design_decision_log": output.get("design_decision_log", []),
        "metadata": metadata,
    }


def _build_mcp_sidecar_aggregates(
    output_dir: str | Path,
    skill_graph: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
) -> Dict[str, Any]:
    """根据已保存的节点状态重建 MCP Agent sidecar 聚合产物。"""
    ordered_nodes = _topological_execution_order(skill_graph.get("nodes", []))
    execution_order = [node.get("instance_id", "") for node in ordered_nodes]

    design_space_entries: List[Dict[str, Any]] = []
    candidate_entries: List[Dict[str, Any]] = []
    converged_entries: List[Dict[str, Any]] = []
    fragments: List[Dict[str, Any]] = []
    lifecycle_records: List[Dict[str, Any]] = []
    final_status_map: Dict[str, str] = {}

    for execution_index, node in enumerate(ordered_nodes, start=1):
        node_id = node.get("instance_id", "")
        state = load_mcp_node_state(output_dir, node_id)
        discovery_entry = state.get("discovery")
        candidates_entry = state.get("candidates")
        converged_entry = state.get("convergence")
        fragment = state.get("fragment")

        if isinstance(discovery_entry, dict) and discovery_entry:
            design_space_entries.append(discovery_entry)
        if isinstance(candidates_entry, dict) and candidates_entry:
            candidate_entries.append(candidates_entry)
        if isinstance(converged_entry, dict) and converged_entry:
            converged_entries.append(converged_entry)
        if isinstance(fragment, dict) and fragment:
            fragments.append(fragment)

        if fragment:
            final_status_map[node_id] = "completed"
            lifecycle_records.append(
                _lifecycle_record(
                    node,
                    status="completed",
                    mode="mcp_agent",
                    execution_index=execution_index,
                )
            )
        elif discovery_entry or candidates_entry or converged_entry:
            final_status_map[node_id] = "running"
            lifecycle_records.append(
                _lifecycle_record(
                    node,
                    status="running",
                    mode="mcp_agent_partial",
                    execution_index=execution_index,
                )
            )
        else:
            final_status_map[node_id] = "pending"

    aggregate_root = _mcp_aggregate_root(output_dir)
    saved_files: Dict[str, Any] = {}

    if design_space_entries:
        saved_files["design_space_report"] = _write_json(
            aggregate_root / "design_space_report.json",
            _aggregate_design_space(
                entries=design_space_entries,
                root_skill_contract=root_skill_contract,
                skill_graph=skill_graph,
                lifecycle_records=lifecycle_records,
                execution_order=execution_order,
                final_status_map=final_status_map,
            ),
        )
    if candidate_entries:
        saved_files["realization_candidates"] = _write_json(
            aggregate_root / "realization_candidates.json",
            _aggregate_candidates(
                entries=candidate_entries,
                lifecycle_records=lifecycle_records,
                execution_order=execution_order,
                final_status_map=final_status_map,
            ),
        )
    if converged_entries:
        saved_files["converged_realization_pack"] = _write_json(
            aggregate_root / "converged_realization_pack.json",
            _aggregate_converged_pack(
                entries=converged_entries,
                lifecycle_records=lifecycle_records,
                execution_order=execution_order,
                final_status_map=final_status_map,
            ),
        )

    fragment_root = aggregate_root / "skill_fragments"
    fragment_root.mkdir(parents=True, exist_ok=True)
    for stale_file in fragment_root.glob("*.json"):
        stale_file.unlink()
    fragment_files = []
    for fragment in fragments:
        skill_instance_id = fragment.get("skill_instance_id", "skill_fragment")
        fragment_files.append(skill_runtime.save_fragment(fragment, skill_instance_id, str(fragment_root)))
    if fragment_files:
        saved_files["skill_fragments"] = fragment_files

    summary_payload = {
        "generated_at": _now_iso(),
        "mode": "mcp_agent_sidecar",
        "execution_order": execution_order,
        "completed_nodes": [
            node_id for node_id, status in final_status_map.items()
            if status == "completed"
        ],
        "partial_nodes": [
            node_id for node_id, status in final_status_map.items()
            if status == "running"
        ],
        "saved_files": saved_files,
    }
    saved_files["summary"] = _write_json(aggregate_root / "summary.json", summary_payload)
    return saved_files


def prepare_node_phase(
    node_id: str,
    phase: str,
    skill_graph: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    phase_scope: str = "",
    node_state: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    为单个节点的指定阶段准备 Agent 所需的全部输入。

    返回:
      - status: "ready_for_agent" | "skipped" | "error"
      - prompts: SkillTemplate prompt 文件内容（system/domain/evaluator）
      - context_bundle: 结构化上下文（structural + semantic 两层）
      - output_schema: 期望的输出结构
      - instructions: Agent 应遵循的生成指引
      - node_info: 当前节点元数据
    """
    if phase not in VALID_STAGE4_PHASES:
        return {"status": "error", "error": f"非法 phase: {phase}，允许值: {VALID_STAGE4_PHASES}"}

    # 查找节点
    node = None
    for n in skill_graph.get("nodes", []):
        if n.get("instance_id") == node_id:
            node = n
            break
    if not node:
        return {"status": "error", "error": f"节点 {node_id} 不在 skill_graph 中"}

    # presence_only 节点不需要 Agent 交互
    if not node.get("allows_design_space_discovery", False):
        return {
            "status": "skipped",
            "reason": f"节点 {node_id} 为 presence_only，无需 Agent 交互",
            "node_info": {"instance_id": node_id, "domain_type": node.get("domain_type")},
        }

    # 加载 SkillTemplate prompts
    template_id = node.get("template_id", "")
    template_prompts = _resolve_template_prompts(template_id)

    # 构建 Context Bundle（Doc 14 §3）
    context_bundle = agent_protocol.build_context_bundle(
        node=node,
        root_skill_contract=root_skill_contract,
        clarification_gate_report=clarification_gate_report,
        skill_graph=skill_graph,
        coupled_domain_summaries={},  # MCP 模式由 Agent 自行管理跨节点依赖
    )

    # 按 phase 构建生成指引
    if phase == "discovery":
        instructions = (
            "你是 Design Space Discovery 专家。\n"
            "请阅读以下 SkillTemplate prompt 和 Context Bundle，\n"
            "为当前节点**主动发现**可设计维度。\n\n"
            "要求：\n"
            "1. 识别 locked_dimensions（来自 Constraint Fields，不可改变）\n"
            "2. 发现 discovery_dimensions（允许发散创造的维度）\n"
            "3. 每个维度需说明 dimension_id、description、探索范围\n"
            "4. 不要从固定列表中选择——真正发现有意义的设计维度\n"
            "5. 输出 JSON 结构，包含 node_id、locked_dimensions、discovery_dimensions"
        )
        output_hint = {
            "node_id": node_id,
            "locked_dimensions": [
                {"field_path": "示例", "locked_value": "示例", "reason": "示例"}
            ],
            "discovery_dimensions": [
                {"dimension_id": "示例", "name": "示例", "description": "示例", "exploration_range": "示例"}
            ],
        }
    elif phase == "candidates":
        instructions = (
            "你是 Realization Candidate 生成专家。\n"
            "基于 Discovery 阶段发现的 open_dimensions，\n"
            "为每个维度生成 2-4 个候选方向。\n\n"
            "要求：\n"
            "1. 每个候选方向需有 candidate_id、description、trade_off 分析\n"
            "2. 候选必须满足 Variant bounds 约束\n"
            "3. 标注 complexity_tier（low/medium/high）\n"
            "4. 体现真正的设计多样性，不要只做微调变体\n"
            "5. 输出 JSON 结构，包含 node_id、candidates（每个维度含 candidates 数组）"
        )
        discovery_output = (node_state or {}).get("discovery", {})
        output_hint = {
            "node_id": node_id,
            "candidates": [
                {
                    "dimension_id": "示例",
                    "candidates": [
                        {"candidate_id": "示例", "name": "示例", "description": "示例", "trade_offs": {"pros": [], "cons": []}, "estimated_complexity": "medium"}
                    ],
                }
            ],
        }
        context_bundle["semantic"]["discovery_result"] = discovery_output
    else:  # convergence
        instructions = (
            "你是 Design Convergence 决策专家。\n"
            "基于 Candidates 阶段生成的候选方向，\n"
            "为每个维度选择最终方向。\n\n"
            "要求：\n"
            "1. 每个维度选择一个 candidate，并提供 rationale\n"
            "2. 记录 rejected_alternatives 及拒绝理由\n"
            "3. 使用 provisional 值的决策标记 provisional: true\n"
            "4. 生成 design_decision_log 记录非平凡决策\n"
            "5. 输出 JSON 结构，包含 node_id、converged_choices、design_decision_log"
        )
        candidates_output = (node_state or {}).get("candidates", {})
        output_hint = {
            "node_id": node_id,
            "converged_choices": [
                {
                    "dimension_id": "示例",
                    "chosen_candidate": "示例",
                    "rationale": "示例",
                    "rejected_alternatives": [],
                    "provisional": False,
                }
            ],
            "design_decision_log": [],
        }
        context_bundle["semantic"]["candidates_result"] = candidates_output

    return {
        "status": "ready_for_agent",
        "phase": phase,
        "node_info": {
            "instance_id": node_id,
            "template_id": template_id,
            "domain_type": node.get("domain_type"),
            "capability_id": node.get("capability_id", ""),
            "allows_design_space_discovery": True,
        },
        "prompts": {
            "system_prompt": template_prompts.get("system_prompt", ""),
            "domain_prompt": template_prompts.get("domain_prompt", ""),
            "evaluator_prompt": template_prompts.get("evaluator_prompt", ""),
        },
        "context_bundle": context_bundle,
        "instructions": instructions,
        "output_hint": output_hint,
        "phase_scope": phase_scope,
    }


def save_node_phase(
    node_id: str,
    phase: str,
    output: Dict[str, Any],
    skill_graph: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    phase_scope: str = "",
    node_state: Dict[str, Any] | None = None,
    output_dir: str | Path | None = None,
) -> Dict[str, Any]:
    """
    保存 Agent 为单个节点某阶段生成的输出。

    对输出做基本结构校验，成功后返回 node_state 供下一阶段使用。
    当 convergence 阶段保存后，自动生成该节点的 Fragment v2。
    """
    if phase not in VALID_STAGE4_PHASES:
        return {"status": "error", "error": f"非法 phase: {phase}"}

    node = None
    for n in skill_graph.get("nodes", []):
        if n.get("instance_id") == node_id:
            node = n
            break
    if not node:
        return {"status": "error", "error": f"节点 {node_id} 不在 skill_graph 中"}

    # 初始化或继承 node_state
    state = dict(node_state or {})

    # 基本校验
    validation_errors = []
    normalized_output: Dict[str, Any]
    if phase == "discovery":
        raw_dimensions = output.get("discovery_dimensions") or output.get("open_dimensions")
        if not raw_dimensions and not output.get("locked_dimensions"):
            validation_errors.append("discovery 输出必须包含 discovery_dimensions/open_dimensions 或 locked_dimensions")
        normalized_output = _normalize_mcp_discovery_output(node, output)
        state["discovery"] = normalized_output
    elif phase == "candidates":
        raw_groups = output.get("candidates") or output.get("dimensions")
        if not raw_groups:
            validation_errors.append("candidates 输出必须包含 candidates/dimensions 数组")
        else:
            for dim in raw_groups:
                if not dim.get("candidates"):
                    validation_errors.append(f"维度 {dim.get('dimension_id', '?')} 缺少 candidates")
        normalized_output = _normalize_mcp_candidates_output(node, output)
        state["candidates"] = normalized_output
    elif phase == "convergence":
        raw_choices = output.get("converged_choices") or output.get("convergence_decisions")
        if not raw_choices:
            validation_errors.append("convergence 输出必须包含 converged_choices/convergence_decisions")
        normalized_output = _normalize_mcp_convergence_output(node, output)
        state["convergence"] = normalized_output

    if validation_errors:
        return {
            "status": "validation_failed",
            "errors": validation_errors,
            "node_state": state,
        }

    result: Dict[str, Any] = {
        "status": "saved",
        "phase": phase,
        "node_id": node_id,
        "node_state": state,
        "normalized_output": normalized_output,
    }

    # convergence 完成后自动生成 Fragment
    if phase == "convergence":
        discovery = state.get("discovery", {})
        candidates = state.get("candidates", {})
        convergence = state.get("convergence", {})

        design_space_entry = discovery
        candidates_entry = candidates
        converged_entry = convergence

        # 生成 Fragment
        fragment = _build_discovered_fragment(
            node=node,
            root_skill_contract=root_skill_contract,
            clarification_gate_report=clarification_gate_report,
            design_space_report=design_space_entry,
            converged_pack=converged_entry,
            phase_scope=phase_scope,
        )

        result["fragment"] = fragment
        result["design_space_entry"] = design_space_entry
        result["candidates_entry"] = candidates_entry
        result["converged_entry"] = converged_entry
        result["next_step"] = "节点完成。继续处理下一个节点，或全部完成后调用 Stage 5。"
        state["fragment"] = fragment
    else:
        next_phase = "candidates" if phase == "discovery" else "convergence"
        result["next_step"] = f"请调用 compiler_stage4_node_prepare(phase='{next_phase}') 继续"

    # 有 output_dir 时，将 MCP Agent 中间态持久化到 sidecar，便于审计和双跑差异比较。
    if output_dir:
        trace_payload = {
            "node_id": node_id,
            "phase": phase,
            "saved_at": _now_iso(),
            "raw_output": output,
            "normalized_output": normalized_output,
            "node_state_snapshot": state,
        }
        trace_path = _write_json(_mcp_phase_trace_path(output_dir, node_id, phase), trace_payload)
        node_state_path = _write_json(_mcp_node_state_path(output_dir, node_id), state)
        sidecar_saved_files = _build_mcp_sidecar_aggregates(
            output_dir=output_dir,
            skill_graph=skill_graph,
            root_skill_contract=root_skill_contract,
        )
        result["sidecar"] = {
            "trace_path": trace_path,
            "node_state_path": node_state_path,
            "saved_files": sidecar_saved_files,
        }

    return result
