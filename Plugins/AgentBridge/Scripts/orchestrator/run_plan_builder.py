"""
Run Plan Builder
从 Handoff 生成 Run Plan
"""

import uuid
from typing import Dict, Any, List


def build_run_plan_from_handoff(handoff: Dict[str, Any]) -> Dict[str, Any]:
    """
    从 Handoff 生成 Run Plan

    Args:
        handoff: Reviewed Handoff 字典

    Returns:
        Run Plan 字典
    """
    # 生成 run_plan_id
    handoff_id = handoff.get("handoff_id", "unknown")
    project_name = handoff_id.split('.')[1] if '.' in handoff_id else "unknown"
    run_plan_id = f"runplan.{project_name}.{uuid.uuid4().hex[:8]}"

    # 提取 dynamic_spec_tree
    dynamic_spec_tree = handoff.get("dynamic_spec_tree", {})
    scene_spec = dynamic_spec_tree.get("scene_spec", {})
    actors = scene_spec.get("actors", [])

    # 生成 workflow_sequence
    workflow_sequence = build_workflow_sequence(actors, handoff.get("handoff_mode"))

    # 生成 validation_checkpoints
    validation_checkpoints = build_validation_checkpoints(workflow_sequence)

    # 组装 Run Plan
    run_plan = {
        "run_plan_version": "2.0",
        "run_plan_id": run_plan_id,
        "source_handoff_id": handoff.get("handoff_id"),
        "mode": handoff.get("handoff_mode"),
        "status": "planned",
        "context": {
            "project_name": handoff.get("project_context", {}).get("project_name"),
            "execution_mode": handoff.get("handoff_mode")
        },
        "workflow_sequence": workflow_sequence,
        "validation_checkpoints": validation_checkpoints,
        "recovery_policies": {},
        "reporting": {
            "output_path": "ProjectState/Reports/"
        },
        "metadata": {
            "generated_from_handoff": handoff.get("handoff_id"),
            "generator": "AgentBridge.Orchestrator.v0.1"
        }
    }

    return run_plan


def build_workflow_sequence(actors: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    """
    从 actors 列表生成 workflow_sequence

    Args:
        actors: Actor 列表
        mode: 执行模式

    Returns:
        Workflow 序列
    """
    workflow_sequence = []

    for i, actor in enumerate(actors):
        step_id = f"spawn_{actor.get('actor_name', f'actor_{i}')}"

        workflow_step = {
            "step_id": step_id,
            "workflow_type": "spawn_actor",
            "params": {
                "actor_name": actor.get("actor_name"),
                "actor_class": actor.get("actor_class"),
                "transform": actor.get("transform")
            }
        }

        # 添加依赖关系（简单实现：后面的 Actor 依赖前面的）
        if i > 0:
            workflow_step["depends_on"] = [f"spawn_{actors[0].get('actor_name')}"]

        workflow_sequence.append(workflow_step)

    return workflow_sequence


def build_validation_checkpoints(workflow_sequence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    生成验证检查点

    Args:
        workflow_sequence: Workflow 序列

    Returns:
        验证检查点列表
    """
    if not workflow_sequence:
        return []

    # 最小实现：在最后一个步骤后添加验证
    last_step = workflow_sequence[-1]

    return [
        {
            "checkpoint_id": "validate_all_actors_spawned",
            "after_step": last_step.get("step_id"),
            "validation_type": "actor_count_check"
        }
    ]


if __name__ == "__main__":
    # 测试代码
    test_handoff = {
        "handoff_id": "handoff.tictactoe.prototype.001",
        "handoff_mode": "greenfield_bootstrap",
        "project_context": {
            "project_name": "Mvpv4TestCodex"
        },
        "dynamic_spec_tree": {
            "scene_spec": {
                "actors": [
                    {
                        "actor_name": "Board",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [0, 0, 0],
                            "rotation": [0, 0, 0],
                            "relative_scale3d": [1, 1, 1]
                        }
                    }
                ]
            }
        }
    }

    run_plan = build_run_plan_from_handoff(test_handoff)
    print(f"Run Plan ID: {run_plan['run_plan_id']}")
    print(f"Workflow 步骤数: {len(run_plan['workflow_sequence'])}")
