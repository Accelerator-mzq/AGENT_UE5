"""
Piece Movement Skill
负责补充落子规则与棋子移动语义。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List


def apply_skill(compilation_state: Dict[str, Any]) -> Dict[str, Any]:
    """生成 piece_movement_spec，并补充 boardgame rules。"""
    design_input = compilation_state["design_input"]
    nodes = compilation_state["nodes"]
    boardgame_spec = nodes.setdefault("boardgame_spec", {"data": {"rules": {}}})
    rules = boardgame_spec.setdefault("data", {}).setdefault("rules", {})

    movement_rules = {
        "movement_model": "placement_only",
        "allow_overwrite_occupied_cell": False,
        "alternate_piece_symbols": [piece.get("symbol", "") for piece in design_input.get("piece_catalog", [])],
        "piece_spawn_mode": "runtime_dynamic",
        "piece_catalog": copy.deepcopy(design_input.get("piece_catalog", [])),
    }

    rules.update(
        {
            "movement_model": movement_rules["movement_model"],
            "allow_overwrite_occupied_cell": movement_rules["allow_overwrite_occupied_cell"],
            "piece_spawn_mode": movement_rules["piece_spawn_mode"],
        }
    )

    nodes["piece_movement_spec"] = {
        "spec_id": "PieceMovementSpec",
        "version": "1.0",
        "data": movement_rules,
    }

    trace = nodes.setdefault("generation_trace", {})
    trace.setdefault("required_skills", [])
    if "piece_movement" not in trace["required_skills"]:
        trace["required_skills"].append("piece_movement")
    return compilation_state

