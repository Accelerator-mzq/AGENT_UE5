"""
Brownfield Delta Generator
把完整目标 spec tree 投影为可执行的最小 delta tree。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List


def generate_brownfield_delta_tree(
    full_target_tree: Dict[str, Any],
    baseline_snapshot: Dict[str, Any],
    delta_context: Dict[str, Any],
    contract_registry: Dict[str, Any],
) -> Dict[str, Any]:
    """生成 Brownfield delta tree。"""
    baseline_actors = baseline_snapshot.get("current_spec_baseline", {}).get("scene_spec", {}).get("actors", [])
    baseline_by_name = {
        actor.get("actor_name", ""): actor
        for actor in baseline_actors
        if actor.get("actor_name")
    }

    target_actors = full_target_tree.get("scene_spec", {}).get("actors", [])
    new_scene_actors: List[Dict[str, Any]] = []
    for actor in target_actors:
        actor_name = actor.get("actor_name", "")
        if actor_name and actor_name not in baseline_by_name:
            new_scene_actors.append(copy.deepcopy(actor))

    delta_tree = {
        "tree_type": "delta",
        "delta_operations": _build_delta_operations(delta_context),
        "baseline_actor_refs": delta_context.get(
            "baseline_actor_refs",
            sorted(baseline_by_name.keys()),
        ),
        "contract_refs": list(delta_context.get("contract_refs", [])),
        "scene_spec": {"actors": new_scene_actors},
        "boardgame_spec": copy.deepcopy(full_target_tree.get("boardgame_spec", {})),
        "validation_spec": _build_delta_validation_spec(
            full_target_tree=full_target_tree,
            delta_context=delta_context,
            contract_registry=contract_registry,
        ),
        "generation_trace": {
            "generator": "AgentBridge.Compiler.Phase5.BrownfieldDeltaGenerator",
            "baseline_id": baseline_snapshot.get("baseline_id", ""),
            "delta_intent": delta_context.get("delta_intent", ""),
            "contract_registry_ref": contract_registry.get("registry_path", ""),
        },
    }

    if "world_build_spec" in full_target_tree:
        delta_tree["world_build_spec"] = copy.deepcopy(full_target_tree["world_build_spec"])

    return delta_tree


def _build_delta_operations(delta_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """将分析结果投影为执行/治理可读的 delta operation 列表。"""
    delta_intent = delta_context.get("delta_intent", "")
    append_specs = delta_context.get("append_specs", [])
    patch_specs = delta_context.get("patch_specs", [])
    replace_specs = delta_context.get("replace_specs", [])

    if delta_intent == "no_change":
        return [
            {
                "operation": "no_change",
                "target_spec": "scene_spec",
                "reason": "目标设计与 baseline 一致，无需新增 Actor",
            }
        ]

    operations = []
    for append_spec in append_specs:
        operations.append(
            {
                "operation": "append_actor",
                "target_spec": append_spec.get("spec_family", "scene_spec"),
                "actor_name": append_spec.get("actor_name", ""),
            }
        )
    for patch_spec in patch_specs:
        operations.append(
            {
                "operation": "patch_actor",
                "target_spec": patch_spec.get("spec_family", "scene_spec"),
                "actor_name": patch_spec.get("actor_name", ""),
                "blocked": True,
            }
        )
    for replace_spec in replace_specs:
        operations.append(
            {
                "operation": "replace_actor",
                "target_spec": replace_spec.get("spec_family", "scene_spec"),
                "actor_name": replace_spec.get("actor_name", ""),
                "blocked": True,
            }
        )

    return operations


def _build_delta_validation_spec(
    full_target_tree: Dict[str, Any],
    delta_context: Dict[str, Any],
    contract_registry: Dict[str, Any],
) -> Dict[str, Any]:
    """生成 Brownfield 场景下的最小验证节点。"""
    base_validation_spec = copy.deepcopy(full_target_tree.get("validation_spec", {}))
    data = base_validation_spec.setdefault("data", {})
    existing_checks = list(data.get("required_checks", []))

    for check in delta_context.get("required_regression_checks", []):
        if check not in existing_checks:
            existing_checks.append(check)

    data["required_checks"] = existing_checks
    data["delta_intent"] = delta_context.get("delta_intent", "")
    data["contract_refs"] = list(delta_context.get("contract_refs", []))
    data["contract_registry_ref"] = contract_registry.get("registry_path", "")
    return base_validation_spec
