"""
Boardgame Scene Generator
在 Static Base + Genre Pack 约束下生成完整 boardgame dynamic spec tree。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional


def generate_boardgame_dynamic_spec_tree(
    design_input: Dict[str, Any],
    routing_context: Dict[str, Any],
    static_spec_context: Dict[str, Any],
    pack_manifest: Dict[str, Any],
    pack_modules: Optional[Dict[str, Any]] = None,
    projection_profile: str = "preview_static",
) -> Dict[str, Any]:
    """生成 boardgame prototype/playable 所需的完整 dynamic spec tree。"""
    loaded_specs = static_spec_context.get("loaded_specs", {})
    pack_modules = pack_modules or {}

    nodes: Dict[str, Any] = {
        "validation_spec": _build_validation_spec(design_input, loaded_specs),
        "generation_trace": {
            "generator": "AgentBridge.Compiler.Phase6.BoardgameSceneGenerator",
            "activated_skill_packs": routing_context.get("activated_skill_packs", []),
            "static_spec_ids": sorted(list(loaded_specs.keys())),
            "skill_pack_id": pack_manifest.get("pack_id", "unknown"),
            "projection_profile": projection_profile,
            "required_skills": [],
            "review_extensions": [
                entry.get("module_id", "") for entry in pack_modules.get("review_extensions", [])
            ],
            "validation_extensions": [
                entry.get("module_id", "") for entry in pack_modules.get("validation_extensions", [])
            ],
            "missing_modules": [],
        },
    }
    compilation_state = {
        "design_input": design_input,
        "routing_context": routing_context,
        "static_spec_context": static_spec_context,
        "pack_manifest": pack_manifest,
        "pack_modules": pack_modules,
        "projection_profile": projection_profile,
        "nodes": nodes,
    }

    for skill_entry in pack_modules.get("required_skills", []):
        module = skill_entry.get("module")
        if module is None or not hasattr(module, "apply_skill"):
            nodes["generation_trace"]["missing_modules"].append(skill_entry.get("module_id", ""))
            continue
        module.apply_skill(compilation_state)

    delta_policy = {}
    for delta_entry in pack_modules.get("delta_policies", []):
        module = delta_entry.get("module")
        if module is None or not hasattr(module, "build_delta_policy"):
            continue
        delta_policy = module.build_delta_policy(design_input, routing_context)
        break
    if delta_policy:
        nodes["generation_trace"]["delta_policy"] = delta_policy

    for validator_entry in pack_modules.get("validation_extensions", []):
        module = validator_entry.get("module")
        if module is None or not hasattr(module, "build_validation_markers"):
            continue
        _merge_validation_markers(
            nodes["validation_spec"],
            module.build_validation_markers(compilation_state),
        )

    nodes["scene_spec"] = {
        "actors": _build_scene_actors(
            design_input=design_input,
            world_build_spec=nodes.get("world_build_spec", {}),
            nodes=nodes,
            projection_profile=projection_profile,
        ),
    }
    return nodes


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
            "runtime_smoke_checks": [],
            "validation_markers": [],
        },
    }


def _build_scene_actors(
    design_input: Dict[str, Any],
    world_build_spec: Dict[str, Any],
    nodes: Dict[str, Any],
    projection_profile: str,
) -> List[Dict[str, Any]]:
    """把 richer spec 投影为当前 orchestrator 可消费的 scene_spec.actors。"""
    if projection_profile == "runtime_playable":
        return [_build_runtime_board_actor(design_input, nodes)]

    board = design_input.get("board", {})
    piece_catalog = design_input.get("piece_catalog", [])
    preview_policy = design_input.get("prototype_preview", {})
    actor_defaults = world_build_spec.get("data", {}).get("actor_defaults", {})

    actors = [_build_board_actor(board, actor_defaults)]
    actors.extend(_build_preview_piece_actors(board, piece_catalog, preview_policy))
    return actors


def _build_runtime_board_actor(design_input: Dict[str, Any], nodes: Dict[str, Any]) -> Dict[str, Any]:
    """生成可玩 runtime 路径的棋盘 Actor。"""
    board = design_input.get("board", {})
    total_size = board.get("total_size_cm", [300.0, 300.0])
    board_location = board.get("location", [0.0, 0.0, 0.0])
    runtime_wiring_spec = nodes.get("runtime_wiring_spec", {}).get("data", {})

    return {
        "actor_name": "BoardRuntimeActor",
        "actor_class": runtime_wiring_spec.get(
            "board_runtime_actor_class",
            "/Script/Mvpv4TestCodex.BoardgamePrototypeBoardActor",
        ),
        "transform": {
            "location": [float(board_location[0]), float(board_location[1]), float(board_location[2])],
            "rotation": [0.0, 0.0, 0.0],
            "relative_scale3d": [
                float(total_size[0]) / 100.0,
                float(total_size[1]) / 100.0,
                0.1,
            ],
        },
        "projection_profile": "runtime_playable",
        "runtime_config_ref": "__RUNTIME_CONFIG_REF__",
        "post_spawn_actions": [
            {
                "action_type": "call_function",
                "function_name": "LoadRuntimeConfigFromFile",
                "parameters": {
                    "RuntimeConfigPath": "__RUNTIME_CONFIG_REF__",
                },
            }
        ],
    }


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


def _merge_validation_markers(validation_spec: Dict[str, Any], markers: Dict[str, Any]) -> None:
    """把 validator 输出合并进 validation_spec。"""
    validation_data = validation_spec.setdefault("data", {})
    for key in ["required_checks", "runtime_smoke_checks", "validation_markers", "notes"]:
        validation_data.setdefault(key, [])

    for key in ["required_checks", "runtime_smoke_checks", "validation_markers", "notes"]:
        for item in markers.get(key, []):
            if item not in validation_data[key]:
                validation_data[key].append(item)
