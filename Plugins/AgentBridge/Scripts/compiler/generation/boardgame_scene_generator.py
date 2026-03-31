"""
Boardgame Scene Generator
在 Static Base 约束下生成最小 boardgame dynamic spec tree。
"""

import copy
from typing import Any, Dict, List


def generate_boardgame_dynamic_spec_tree(
    design_input: Dict[str, Any],
    routing_context: Dict[str, Any],
    static_spec_context: Dict[str, Any],
    pack_manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """生成 boardgame prototype 所需的 dynamic spec tree。"""
    loaded_specs = static_spec_context.get("loaded_specs", {})

    world_build_spec = _build_world_build_spec(design_input, loaded_specs)
    boardgame_spec = _build_boardgame_spec(design_input, routing_context, loaded_specs, pack_manifest)
    validation_spec = _build_validation_spec(design_input, loaded_specs)
    scene_spec = {
        "actors": _build_scene_actors(design_input, world_build_spec),
    }

    return {
        "world_build_spec": world_build_spec,
        "boardgame_spec": boardgame_spec,
        "validation_spec": validation_spec,
        "scene_spec": scene_spec,
        "generation_trace": {
            "generator": "AgentBridge.Compiler.Phase4.BoardgameSceneGenerator",
            "activated_skill_packs": routing_context.get("activated_skill_packs", []),
            "static_spec_ids": sorted(list(loaded_specs.keys())),
            "skill_pack_id": pack_manifest.get("pack_id", "unknown"),
        },
    }


def _build_world_build_spec(
    design_input: Dict[str, Any],
    loaded_specs: Dict[str, Any],
) -> Dict[str, Any]:
    """基于 WorldBuildStaticSpec 模板实例化场景构建节点。"""
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
    """实例化 boardgame 类型 spec。"""
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


def _build_validation_spec(
    design_input: Dict[str, Any],
    loaded_specs: Dict[str, Any],
) -> Dict[str, Any]:
    """合并通用校验基座和 boardgame 校验基座。"""
    base_template = copy.deepcopy(loaded_specs["ValidationStaticSpec"]["template"])
    boardgame_template = copy.deepcopy(loaded_specs["BoardgameValidationStaticSpec"]["template"])

    required_checks = []
    for check in base_template["data"].get("required_checks", []):
        if check not in required_checks:
            required_checks.append(check)
    for check in boardgame_template["data"].get("required_checks", []):
        if check not in required_checks:
            required_checks.append(check)

    return {
        "spec_id": "BoardgameValidationStaticSpec",
        "version": boardgame_template.get("version", "1.0"),
        "data": {
            "required_checks": required_checks,
            "prototype_closure": boardgame_template["data"].get("prototype_closure", []),
            "preview_policy": copy.deepcopy(design_input.get("prototype_preview", {})),
            "severity_policy": copy.deepcopy(base_template["data"].get("severity_policy", {})),
            "notes": base_template["data"].get("notes", []) + boardgame_template["data"].get("notes", []),
        },
    }


def _build_scene_actors(
    design_input: Dict[str, Any],
    world_build_spec: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """把 richer spec 投影为当前 orchestrator 可消费的 scene_spec.actors。"""
    board = design_input.get("board", {})
    piece_catalog = design_input.get("piece_catalog", [])
    preview_policy = design_input.get("prototype_preview", {})
    actor_defaults = world_build_spec.get("data", {}).get("actor_defaults", {})

    actors = [_build_board_actor(board, actor_defaults)]
    actors.extend(_build_preview_piece_actors(board, piece_catalog, preview_policy))
    return actors


def _build_board_actor(board: Dict[str, Any], actor_defaults: Dict[str, Any]) -> Dict[str, Any]:
    """构建棋盘 Actor。"""
    total_size = board.get("total_size_cm", [300.0, 300.0])
    board_location = board.get("location", [0.0, 0.0, 0.0])
    scale_z = actor_defaults.get("board_scale_z", 0.1)

    return {
        "actor_name": board.get("board_name", "Board"),
        "actor_class": actor_defaults.get("actor_class", "/Script/Engine.StaticMeshActor"),
        "transform": {
            "location": [float(board_location[0]), float(board_location[1]), float(board_location[2])],
            "rotation": [0.0, 0.0, 0.0],
            "relative_scale3d": [
                float(total_size[0]) / 100.0,
                float(total_size[1]) / 100.0,
                float(scale_z),
            ],
        },
    }


def _build_preview_piece_actors(
    board: Dict[str, Any],
    piece_catalog: List[Dict[str, Any]],
    preview_policy: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """按照预览策略生成示例棋子 Actor。"""
    if not preview_policy.get("generate_preview", False):
        return []

    piece_counts = preview_policy.get("piece_counts", {})
    actors: List[Dict[str, Any]] = []

    for piece_type_index, piece in enumerate(piece_catalog):
        symbol = piece.get("symbol", "")
        target_count = int(piece_counts.get(symbol, 0))
        for piece_instance_index in range(target_count):
            actors.append(
                {
                    "actor_name": f"{piece.get('actor_name_prefix', f'Piece{symbol}')}_{piece_instance_index + 1}",
                    "actor_class": piece.get("actor_class", "/Script/Engine.StaticMeshActor"),
                    "transform": {
                        "location": _compute_preview_location(
                            board,
                            piece_type_index,
                            piece_instance_index,
                        ),
                        "rotation": [0.0, 0.0, 0.0],
                        "relative_scale3d": _compute_piece_scale(piece),
                    },
                }
            )

    return actors


def _compute_preview_location(
    board: Dict[str, Any],
    piece_type_index: int,
    piece_instance_index: int,
) -> List[float]:
    """生成示例棋子的默认摆放位置。"""
    board_location = board.get("location", [0.0, 0.0, 0.0])
    cell_size = board.get("cell_size_cm", [100.0, 100.0])

    x_direction = -1.0 if piece_type_index % 2 == 0 else 1.0
    y_direction = -1.0 if piece_type_index % 2 == 0 else 1.0
    y_offset = float(piece_instance_index) * float(cell_size[1]) * 0.75

    return [
        float(board_location[0]) + x_direction * float(cell_size[0]),
        float(board_location[1]) + y_direction * float(cell_size[1]) + y_offset,
        float(board_location[2]) + 50.0,
    ]


def _compute_piece_scale(piece: Dict[str, Any]) -> List[float]:
    """将尺寸厘米换算为 StaticMeshActor 的相对缩放。"""
    dimensions = piece.get("dimensions_cm", [50.0, 50.0, 50.0])
    return [
        float(dimensions[0]) / 100.0,
        float(dimensions[1]) / 100.0,
        float(dimensions[2]) / 100.0,
    ]
