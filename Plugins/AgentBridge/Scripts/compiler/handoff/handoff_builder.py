"""
Handoff Builder
组装 Reviewed Handoff。
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from compiler.analysis import (
    build_and_save_baseline_snapshot,
    get_default_contract_root,
    get_default_snapshot_dir,
)
from compiler.generation import generate_dynamic_spec_tree, load_skill_pack_manifest
from compiler.review import review_dynamic_spec_tree


def build_handoff(
    design_input: Dict[str, Any],
    mode: str,
    project_state: Optional[Dict[str, Any]] = None,
    static_base_root: Optional[str] = None,
    pack_manifest_path: Optional[str] = None,
    snapshot_output_dir: Optional[str] = None,
    contract_root: Optional[str] = None,
) -> Dict[str, Any]:
    """
    组装 Reviewed Handoff。

    Args:
        design_input: 设计输入包（来自 design_input_intake）
        mode: 模式（greenfield_bootstrap / brownfield_expansion）
        project_state: 项目现状快照（可选）
        static_base_root: StaticBase 根目录（可选）
        pack_manifest_path: 类型包 manifest 路径（可选）
        snapshot_output_dir: Brownfield baseline snapshot 输出目录（可选）
        contract_root: Contracts 根目录（可选）

    Returns:
        Reviewed Handoff 字典
    """
    project_state = project_state or {}
    game_type = design_input.get("game_type", "unknown")
    pack_manifest = load_skill_pack_manifest(game_type, pack_manifest_path)
    activated_skill_packs = [pack_manifest.get("pack_id", game_type)]
    routing_context = {
        "mode": mode,
        "genre": game_type,
        "target_stage": "prototype",
        "activated_skill_packs": activated_skill_packs,
    }

    baseline_snapshot = {}
    baseline_snapshot_path = ""
    if mode == "brownfield_expansion":
        baseline_snapshot, baseline_snapshot_path = build_and_save_baseline_snapshot(
            project_state=project_state,
            design_input=design_input,
            output_dir=snapshot_output_dir or get_default_snapshot_dir(),
        )

    generation_result = generate_dynamic_spec_tree(
        design_input=design_input,
        routing_context=routing_context,
        static_base_root=static_base_root,
        pack_manifest_path=pack_manifest_path,
        baseline_snapshot=baseline_snapshot,
        contract_root=contract_root or get_default_contract_root(),
    )
    dynamic_spec_tree = generation_result["dynamic_spec_tree"]
    static_spec_context = generation_result["static_spec_context"]
    analysis_context = generation_result.get("analysis_context", {})

    # 生成器内部也会写 trace，这里同步覆盖成最终 routing_context，避免前后不一致。
    if isinstance(dynamic_spec_tree.get("generation_trace"), dict):
        dynamic_spec_tree["generation_trace"]["activated_skill_packs"] = activated_skill_packs

    review_result = review_dynamic_spec_tree(
        design_input=design_input,
        dynamic_spec_tree=dynamic_spec_tree,
        static_spec_context=static_spec_context,
        routing_context=routing_context,
        analysis_context=analysis_context,
    )

    handoff_id = generate_handoff_id(game_type)
    status = review_result.get("status", "blocked")
    project_context = {
        "project_name": project_state.get("project_name", "Unknown"),
        "game_type": game_type,
        "target_platform": "Win64",
        "current_level": project_state.get("current_level", ""),
        "has_existing_content": project_state.get("has_existing_content", False),
    }
    delta_context = analysis_context.get("delta_context", {})
    contract_registry = analysis_context.get("contract_registry", {})

    handoff = {
        "handoff_version": "1.0",
        "handoff_id": handoff_id,
        "handoff_mode": mode,
        "status": status,
        "project_context": project_context,
        "routing_context": routing_context,
        "dynamic_spec_tree": dynamic_spec_tree,
        "review_summary": {
            "reviewed": bool(review_result.get("reviewed", False)),
            "reviewer": review_result.get("reviewer", ""),
            "review_notes": review_result.get("review_notes", ""),
        },
        "capability_gaps": review_result.get("capability_gaps", {}),
        "governance_context": {
            "phase": "Phase 5",
            "static_base_registry_ref": static_spec_context.get("registry", {}).get("registry_path", ""),
            "required_static_specs": static_spec_context.get("required_spec_ids", []),
            "contract_registry_ref": contract_registry.get("registry_path", ""),
        },
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "AgentBridge.Compiler.v0.5",
            "source_gdd": design_input.get("source_file"),
            "source_files": design_input.get("source_files", []),
            "skill_pack_manifest": pack_manifest.get("manifest_path", ""),
            "source_project_state_digest": project_state.get("current_project_state_digest", ""),
            "baseline_snapshot_ref": baseline_snapshot_path,
        },
    }

    if mode == "brownfield_expansion":
        handoff["baseline_context"] = {
            "baseline_id": baseline_snapshot.get("baseline_id", ""),
            "snapshot_ref": baseline_snapshot.get("snapshot_ref", baseline_snapshot_path),
            "frozen_baseline_ref": baseline_snapshot.get("snapshot_ref", baseline_snapshot_path),
            "existing_spec_registry_ref": contract_registry.get("registry_path", ""),
            "current_project_state_digest": project_state.get("current_project_state_digest", ""),
        }
        handoff["delta_context"] = {
            "delta_intent": delta_context.get("delta_intent", ""),
            "affected_domains": delta_context.get("affected_domains", []),
            "affected_specs": delta_context.get("affected_specs", []),
            "required_regression_checks": delta_context.get("required_regression_checks", []),
            "delta_scope": delta_context.get("delta_scope", {}),
            "contract_refs": delta_context.get("contract_refs", []),
            "unsupported_items": delta_context.get("unsupported_items", []),
        }

    return handoff


def generate_handoff_id(game_type: str) -> str:
    """生成 handoff_id。"""
    short_uuid = uuid.uuid4().hex[:8]
    return f"handoff.{game_type}.prototype.{short_uuid}"


def build_minimal_spec_tree(design_input: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    兼容旧接口。

    Phase 4 起该函数不再手工写死 3 Actor，而是直接复用自动生成链。
    """
    routing_context = {
        "mode": mode,
        "genre": design_input.get("game_type", "unknown"),
        "target_stage": "prototype",
        "activated_skill_packs": [design_input.get("game_type", "unknown")],
    }
    generation_result = generate_dynamic_spec_tree(
        design_input=design_input,
        routing_context=routing_context,
    )
    return generation_result["dynamic_spec_tree"]


if __name__ == "__main__":
    test_design_input = {
        "game_type": "boardgame",
        "feature_tags": ["boardgame", "prototype_preview"],
        "board": {
            "board_name": "Board",
            "board_type": "3x3 网格",
            "grid_size": [3, 3],
            "cell_size_cm": [100, 100],
            "total_size_cm": [300, 300],
            "location": [0.0, 0.0, 0.0],
            "material": "简单平面",
        },
        "piece_catalog": [
            {
                "piece_id": "piece_x",
                "symbol": "X",
                "actor_name_prefix": "PieceX",
                "dimensions_cm": [50.0, 50.0, 50.0],
                "actor_class": "/Script/Engine.StaticMeshActor",
            },
            {
                "piece_id": "piece_o",
                "symbol": "O",
                "actor_name_prefix": "PieceO",
                "dimensions_cm": [50.0, 50.0, 50.0],
                "actor_class": "/Script/Engine.StaticMeshActor",
            },
        ],
        "rules": {
            "rule_summary": ["3x3 棋盘", "回合制"],
            "turn_model": "turn_based",
            "victory_condition": "连成 3 个",
        },
        "initial_layout": {
            "board_location": [0.0, 0.0, 0.0],
            "starts_empty": True,
        },
        "prototype_preview": {
            "generate_preview": True,
            "source": "default",
            "piece_counts": {"X": 1, "O": 1},
        },
        "technical_requirements": {
            "target_engine_version": "UE5.5.4",
            "actor_class": "/Script/Engine.StaticMeshActor",
        },
        "source_file": "test.md",
    }

    handoff = build_handoff(test_design_input, "greenfield_bootstrap")
    print(f"Handoff ID: {handoff['handoff_id']}")
    print(f"Status: {handoff['status']}")
    print(f"Actors: {len(handoff['dynamic_spec_tree']['scene_spec']['actors'])}")
