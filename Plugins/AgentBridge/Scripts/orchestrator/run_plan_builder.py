"""
Run Plan Builder
从 Handoff 生成 Run Plan
"""

import uuid
from typing import Dict, Any, List

# 与 handoff_runner 同样的兼容策略:
# - 以包模块方式加载时(orchestrator.run_plan_builder), relative import 生效
# - 以裸模块方式加载时, fallback 到平铺路径
try:
    from .recovery_planner import build_recovery_plan
    from .validation_inserter import insert_validation_checkpoints
except ImportError:
    from recovery_planner import build_recovery_plan
    from validation_inserter import insert_validation_checkpoints


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
    project_name = handoff.get("project_context", {}).get("project_name", "unknown").lower()
    mode_token = _normalize_mode_token(handoff.get("handoff_mode", "prototype"))
    run_plan_id = f"runplan.{project_name}.{mode_token}.{uuid.uuid4().hex[:8]}"

    # 提取 dynamic_spec_tree
    dynamic_spec_tree = handoff.get("dynamic_spec_tree", {})
    scene_spec = dynamic_spec_tree.get("scene_spec", {})
    actors = scene_spec.get("actors", [])

    # 生成 workflow_sequence
    workflow_sequence = build_workflow_sequence(actors, handoff.get("handoff_mode"))

    # 生成 validation_checkpoints
    validation_checkpoints = insert_validation_checkpoints(workflow_sequence, handoff)
    recovery_bundle = build_recovery_plan(handoff, workflow_sequence)
    planning_blockers = list(recovery_bundle.get("blockers", []))
    if workflow_sequence and not validation_checkpoints:
        planning_blockers.append("缺少 validation_checkpoints，无法进入治理闭环")
    if not recovery_bundle.get("policy_ref"):
        planning_blockers.append("缺少 recovery_policy_ref，无法进入执行阶段")

    # 组装 Run Plan
    run_plan = {
        "run_plan_version": "2.0",
        "run_plan_id": run_plan_id,
        "source_handoff_id": handoff.get("handoff_id"),
        "mode": handoff.get("handoff_mode"),
        "status": "planned" if not planning_blockers else "failed",
        "context": {
            "project_name": handoff.get("project_context", {}).get("project_name"),
            "execution_mode": handoff.get("handoff_mode"),
            "planning_blockers": planning_blockers,
        },
        "workflow_sequence": workflow_sequence,
        "validation_checkpoints": validation_checkpoints,
        "recovery_policy_ref": recovery_bundle.get("policy_ref", ""),
        "recovery_policies": recovery_bundle.get("policies", {}),
        "reporting": {
            "output_path": "ProjectState/Reports/"
        },
        "metadata": {
            "generated_from_handoff": handoff.get("handoff_id"),
            "generator": "AgentBridge.Orchestrator.v0.7",
            "base_domain_refs": handoff.get("governance_context", {}).get("base_domain_refs", []),
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
                "transform": actor.get("transform"),
                "runtime_config_ref": actor.get("runtime_config_ref", ""),
                "post_spawn_actions": actor.get("post_spawn_actions", []),
                "projection_profile": actor.get("projection_profile", ""),
            }
        }

        # 添加依赖关系（简单实现：后面的 Actor 依赖前面的）
        if i > 0:
            workflow_step["depends_on"] = [f"spawn_{actors[0].get('actor_name')}"]

        workflow_sequence.append(workflow_step)

    return workflow_sequence


def _normalize_mode_token(mode: str) -> str:
    """把执行模式压缩成 run_plan_id 可读片段。"""
    if mode == "brownfield_expansion":
        return "brownfield"
    if mode == "greenfield_bootstrap":
        return "greenfield"
    return "prototype"


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
