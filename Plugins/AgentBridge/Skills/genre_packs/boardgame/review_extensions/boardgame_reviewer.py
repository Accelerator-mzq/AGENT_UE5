"""
Boardgame Reviewer
执行 boardgame pack 特有的编译期审查。
"""

from __future__ import annotations

from typing import Any, Dict, List


def review_dynamic_spec_tree(
    design_input: Dict[str, Any],
    dynamic_spec_tree: Dict[str, Any],
    routing_context: Dict[str, Any],
    analysis_context: Dict[str, Any],
) -> Dict[str, Any]:
    """对 boardgame 特有节点做审查。"""
    errors: List[str] = []
    warnings: List[str] = []
    capability_gaps = {
        "required_static_templates": [],
        "unresolved_refs": [],
        "unsupported_gdd_sections": [],
        "missing_patch_contracts": [],
        "missing_migration_contracts": [],
        "unsupported_regression_checks": [],
    }
    notes: List[str] = []

    required_nodes = [
        "board_layout_spec",
        "piece_movement_spec",
        "turn_flow_spec",
        "decision_ui_spec",
        "runtime_wiring_spec",
    ]
    for node_name in required_nodes:
        if node_name not in dynamic_spec_tree:
            errors.append(f"缺少 boardgame 必需节点: {node_name}")

    board_layout_spec = dynamic_spec_tree.get("board_layout_spec", {}).get("data", {})
    turn_flow_spec = dynamic_spec_tree.get("turn_flow_spec", {}).get("data", {})
    decision_ui_spec = dynamic_spec_tree.get("decision_ui_spec", {}).get("data", {})
    runtime_wiring_spec = dynamic_spec_tree.get("runtime_wiring_spec", {}).get("data", {})
    scene_actors = dynamic_spec_tree.get("scene_spec", {}).get("actors", [])

    if board_layout_spec.get("grid_size") != design_input.get("board", {}).get("grid_size"):
        errors.append("board_layout_spec.grid_size 与 GDD 棋盘尺寸不一致")

    player_order = turn_flow_spec.get("player_order", [])
    piece_symbols = [piece.get("symbol") for piece in design_input.get("piece_catalog", [])]
    if player_order != piece_symbols:
        errors.append("turn_flow_spec.player_order 与 piece_catalog 不一致")

    if decision_ui_spec.get("display_mode") != "minimal_status_text":
        warnings.append("decision_ui_spec 未使用最小状态显示模式")

    if runtime_wiring_spec.get("projection_profile") == "runtime_playable":
        runtime_actor_names = [actor.get("actor_name") for actor in scene_actors]
        if "BoardRuntimeActor" not in runtime_actor_names:
            errors.append("runtime_playable 模式下 scene_spec 缺少 BoardRuntimeActor")

    delta_context = analysis_context.get("delta_context", {})
    if routing_context.get("mode") == "brownfield_expansion" and delta_context.get("delta_intent") == "patch_existing_content":
        for required_contract in ["TurnFlowPatchContract", "DecisionUIPatchContract"]:
            if required_contract not in delta_context.get("contract_refs", []):
                capability_gaps["missing_patch_contracts"].append(required_contract)
                errors.append(f"Brownfield turn/ui patch 缺少 genre contract: {required_contract}")

    notes.append("boardgame reviewer 已检查完整 spec tree 与最小 runtime wiring。")
    return {
        "errors": errors,
        "warnings": warnings,
        "capability_gaps": capability_gaps,
        "notes": notes,
    }

