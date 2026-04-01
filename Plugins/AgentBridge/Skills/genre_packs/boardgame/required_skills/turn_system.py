"""
Turn System Skill
负责补充回合流、决策 UI 与 runtime wiring。
"""

from __future__ import annotations

from typing import Any, Dict, List


def apply_skill(compilation_state: Dict[str, Any]) -> Dict[str, Any]:
    """生成 turn_flow_spec / decision_ui_spec / runtime_wiring_spec。"""
    design_input = compilation_state["design_input"]
    nodes = compilation_state["nodes"]
    projection_profile = compilation_state.get("projection_profile", "preview_static")

    piece_symbols = [piece.get("symbol", "") for piece in design_input.get("piece_catalog", []) if piece.get("symbol")]
    victory_patterns = _build_victory_patterns(design_input.get("board", {}).get("grid_size", [3, 3]))
    default_first_player = piece_symbols[0] if piece_symbols else "X"

    nodes["turn_flow_spec"] = {
        "spec_id": "TurnFlowSpec",
        "version": "1.0",
        "data": {
            "turn_model": "alternating_turns",
            "first_player": default_first_player,
            "player_order": piece_symbols,
            "turn_transition": "advance_after_valid_move",
            "terminal_conditions": ["win", "draw"],
            "victory_patterns": victory_patterns,
        },
    }
    nodes["decision_ui_spec"] = {
        "spec_id": "DecisionUISpec",
        "version": "1.0",
        "data": {
            "display_mode": "minimal_status_text",
            "fields": ["current_player", "game_result", "move_count"],
            "interaction_hint": "click_board_to_place_piece",
        },
    }
    nodes["runtime_wiring_spec"] = {
        "spec_id": "RuntimeWiringSpec",
        "version": "1.0",
        "data": {
            "projection_profile": projection_profile,
            "board_runtime_actor_class": "/Script/Mvpv4TestCodex.BoardgamePrototypeBoardActor",
            "input_binding": "click_board_cell",
            "runtime_config_ref": "",
            "runtime_functions": [
                "LoadRuntimeConfigFromFile",
                "ApplyMoveByCell",
                "GetBoardRuntimeState",
                "ResetBoard",
            ],
        },
    }

    validation_spec = nodes.setdefault("validation_spec", {"data": {}})
    validation_data = validation_spec.setdefault("data", {})
    validation_data.setdefault("required_checks", [])
    validation_data.setdefault("runtime_smoke_checks", [])
    validation_data.setdefault("notes", [])

    for check in [
        "boardgame-turn-smoke-check",
        "boardgame-decision-ui-smoke-check",
        "boardgame-core-loop-closure-check",
    ]:
        if check not in validation_data["runtime_smoke_checks"]:
            validation_data["runtime_smoke_checks"].append(check)

    trace = nodes.setdefault("generation_trace", {})
    trace.setdefault("required_skills", [])
    if "turn_system" not in trace["required_skills"]:
        trace["required_skills"].append("turn_system")
    return compilation_state


def _build_victory_patterns(grid_size: List[int]) -> List[List[List[int]]]:
    """为 3x3 类棋盘生成横竖斜胜利模式。"""
    width = int(grid_size[0]) if grid_size else 3
    height = int(grid_size[1]) if len(grid_size) > 1 else width
    patterns: List[List[List[int]]] = []

    for row in range(height):
        patterns.append([[row, col] for col in range(width)])
    for col in range(width):
        patterns.append([[row, col] for row in range(height)])

    diagonal_size = min(width, height)
    patterns.append([[index, index] for index in range(diagonal_size)])
    patterns.append([[index, diagonal_size - index - 1] for index in range(diagonal_size)])
    return patterns

