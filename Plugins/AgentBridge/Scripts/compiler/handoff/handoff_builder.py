"""
Handoff Builder
组装 Reviewed Handoff
"""

import uuid
from datetime import datetime
from typing import Dict, Any


def build_handoff(
    design_input: Dict[str, Any],
    mode: str,
    project_state: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    组装 Reviewed Handoff

    Args:
        design_input: 设计输入包（来自 design_input_intake）
        mode: 模式（greenfield_bootstrap / brownfield_expansion）
        project_state: 项目现状快照（可选）

    Returns:
        Reviewed Handoff 字典
    """
    # 生成 handoff_id
    handoff_id = generate_handoff_id(design_input.get("game_type", "unknown"))

    # 构建 project_context
    project_context = {
        "project_name": project_state.get("project_name", "Unknown") if project_state else "Unknown",
        "game_type": design_input.get("game_type"),
        "target_platform": "Win64"
    }

    # 构建 routing_context
    # 基于 Reviewed_Dynamic_Spec_Tree_交接模型_v2：
    # routing_context 应包含 mode / genre / target_stage / activated_skill_packs
    # 第一阶段只填充 mode / genre / activated_skill_packs，target_stage 留空
    routing_context = {
        "mode": mode,
        "genre": design_input.get("game_type"),
        "target_stage": "prototype",
        "activated_skill_packs": [design_input.get("game_type")]
    }

    # 构建 dynamic_spec_tree（最小实现）
    dynamic_spec_tree = build_minimal_spec_tree(design_input, mode)

    # 组装 Handoff
    handoff = {
        "handoff_version": "1.0",
        "handoff_id": handoff_id,
        "handoff_mode": mode,
        "status": "draft",
        "project_context": project_context,
        "routing_context": routing_context,
        "dynamic_spec_tree": dynamic_spec_tree,
        "review_summary": {
            "reviewed": False,
            # Schema 约束 reviewer/review_notes 为 string，这里用空字符串占位
            "reviewer": "",
            "review_notes": ""
        },
        "capability_gaps": {},
        "governance_context": {},
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "AgentBridge.Compiler.v0.1",
            "source_gdd": design_input.get("source_file")
        }
    }

    # 如果是 Brownfield，添加 baseline_context 和 delta_context
    # 基于 Reviewed_Dynamic_Spec_Tree_交接模型_v2：
    # baseline_context 应包含 baseline_id / snapshot_ref / frozen_baseline_ref / existing_spec_registry_ref
    # delta_context 应包含 delta_intent / affected_domains / affected_specs / required_regression_checks
    # 第一阶段只做空占位，完整实现待 Brownfield 实装阶段
    if mode == "brownfield_expansion":
        handoff["baseline_context"] = {
            # Brownfield 占位字段先提供空字符串，避免与 schema 的 string 类型冲突
            "baseline_id": "",
            "snapshot_ref": "",
            "frozen_baseline_ref": "",
            "existing_spec_registry_ref": ""
        }
        handoff["delta_context"] = {
            "delta_intent": "",
            "affected_domains": [],
            "affected_specs": [],
            "required_regression_checks": []
        }

    return handoff


def generate_handoff_id(game_type: str) -> str:
    """生成 handoff_id"""
    short_uuid = uuid.uuid4().hex[:8]
    return f"handoff.{game_type}.prototype.{short_uuid}"


def build_minimal_spec_tree(design_input: Dict[str, Any], mode: str) -> Dict[str, Any]:
    """
    构建最小 Spec Tree

    第一阶段：手工构造简单的 scene_spec
    后续阶段：从 design_input 自动生成
    """
    game_type = design_input.get("game_type")

    if game_type == "boardgame":
        # 井字棋最小场景
        return {
            "scene_spec": {
                "actors": [
                    {
                        "actor_name": "Board",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [0, 0, 0],
                            "rotation": [0, 0, 0],
                            "relative_scale3d": [3, 3, 0.1]
                        }
                    },
                    {
                        "actor_name": "PieceX_1",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [-100, -100, 50],
                            "rotation": [0, 0, 0],
                            "relative_scale3d": [0.5, 0.5, 0.5]
                        }
                    },
                    {
                        "actor_name": "PieceO_1",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [100, 100, 50],
                            "rotation": [0, 0, 0],
                            "relative_scale3d": [0.5, 0.5, 0.5]
                        }
                    }
                ]
            }
        }
    else:
        # 默认空场景
        return {
            "scene_spec": {
                "actors": []
            }
        }


if __name__ == "__main__":
    # 测试代码
    test_design_input = {
        "game_type": "boardgame",
        "scene_requirements": [],
        "source_file": "test.md"
    }

    test_mode = "greenfield_bootstrap"

    handoff = build_handoff(test_design_input, test_mode)
    print(f"Handoff ID: {handoff['handoff_id']}")
    print(f"Mode: {handoff['handoff_mode']}")
    print(f"Actors: {len(handoff['dynamic_spec_tree']['scene_spec']['actors'])}")
