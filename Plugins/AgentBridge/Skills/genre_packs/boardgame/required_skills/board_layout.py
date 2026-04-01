"""
Board Layout Skill
负责生成棋盘布局相关 spec 节点。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List


def apply_skill(compilation_state: Dict[str, Any]) -> Dict[str, Any]:
    """生成 world_build_spec / boardgame_spec / board_layout_spec。"""
    design_input = compilation_state["design_input"]
    loaded_specs = compilation_state["static_spec_context"]["loaded_specs"]
    nodes = compilation_state["nodes"]
    routing_context = compilation_state["routing_context"]
    pack_manifest = compilation_state["pack_manifest"]

    nodes["world_build_spec"] = _build_world_build_spec(design_input, loaded_specs)
    nodes["boardgame_spec"] = _build_boardgame_spec(design_input, routing_context, loaded_specs, pack_manifest)
    nodes["board_layout_spec"] = _build_board_layout_spec(design_input)

    _append_trace(nodes, "board_layout")
    return compilation_state


def _build_world_build_spec(design_input: Dict[str, Any], loaded_specs: Dict[str, Any]) -> Dict[str, Any]:
    """从静态基座实例化世界构建节点。"""
    template = copy.deepcopy(loaded_specs["WorldBuildStaticSpec"]["template"])
    board = design_input.get("board", {})
    technical_requirements = design_input.get("technical_requirements", {})

    template["data"]["board"] = {
        "board_type": board.get("board_type", "grid_board"),
        "grid_size": board.get("grid_size", [3, 3]),
        "cell_size_cm": board.get("cell_size_cm", [100, 100]),
        "total_size_cm": board.get("total_size_cm", [300, 300]),
        "location": board.get("location", [0.0, 0.0, 0.0]),
        "material": board.get("material", "DefaultBoardMaterial"),
    }
    template["data"]["actor_defaults"]["actor_class"] = technical_requirements.get(
        "actor_class",
        "/Script/Engine.StaticMeshActor",
    )
    return template


def _build_boardgame_spec(
    design_input: Dict[str, Any],
    routing_context: Dict[str, Any],
    loaded_specs: Dict[str, Any],
    pack_manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """实例化 boardgame 根 spec。"""
    template = copy.deepcopy(loaded_specs["BoardgameStaticSpec"]["template"])
    template["data"]["board"] = copy.deepcopy(design_input.get("board", {}))
    template["data"]["piece_catalog"] = copy.deepcopy(design_input.get("piece_catalog", []))
    template["data"]["preview_policy"] = copy.deepcopy(design_input.get("prototype_preview", {}))
    template["data"]["rules"] = copy.deepcopy(design_input.get("rules", {}))
    template["data"]["initial_layout"] = copy.deepcopy(design_input.get("initial_layout", {}))
    template["data"]["feature_tags"] = list(design_input.get("feature_tags", []))
    template["data"]["skill_pack"] = {
        "pack_id": pack_manifest.get("pack_id", "unknown"),
        "version": pack_manifest.get("version", "unknown"),
        "activated_skill_packs": routing_context.get("activated_skill_packs", []),
    }
    return template


def _build_board_layout_spec(design_input: Dict[str, Any]) -> Dict[str, Any]:
    """生成棋盘布局 spec。"""
    board = design_input.get("board", {})
    grid_size = board.get("grid_size", [3, 3])
    cell_size = board.get("cell_size_cm", [100, 100])
    board_location = board.get("location", [0.0, 0.0, 0.0])

    cell_anchors: List[Dict[str, Any]] = []
    origin_x = float(board_location[0]) - (float(grid_size[0]) * float(cell_size[0])) / 2.0 + float(cell_size[0]) / 2.0
    origin_y = float(board_location[1]) - (float(grid_size[1]) * float(cell_size[1])) / 2.0 + float(cell_size[1]) / 2.0

    for row in range(int(grid_size[1])):
        for col in range(int(grid_size[0])):
            cell_anchors.append(
                {
                    "row": row,
                    "col": col,
                    "world_location": [
                        origin_x + float(col) * float(cell_size[0]),
                        origin_y + float(row) * float(cell_size[1]),
                        float(board_location[2]) + 50.0,
                    ],
                    "cell_id": f"cell_{row}_{col}",
                }
            )

    return {
        "spec_id": "BoardLayoutSpec",
        "version": "1.0",
        "data": {
            "grid_size": grid_size,
            "cell_size_cm": cell_size,
            "board_origin": board_location,
            "cell_anchors": cell_anchors,
            "occupancy_rule": "single_piece_per_cell",
        },
    }


def _append_trace(nodes: Dict[str, Any], skill_id: str) -> None:
    """记录 skill 执行轨迹。"""
    trace = nodes.setdefault("generation_trace", {})
    trace.setdefault("required_skills", [])
    if skill_id not in trace["required_skills"]:
        trace["required_skills"].append(skill_id)

