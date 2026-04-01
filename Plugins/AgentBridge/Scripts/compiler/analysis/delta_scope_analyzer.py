"""
Delta Scope Analyzer
对 baseline snapshot 与目标设计输入做最小差量分析。
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional


SUPPORTED_DOMAINS = [
    "world",
    "runtime",
    "ui",
    "audio",
    "config",
    "validation",
    "governance",
]


def analyze_delta_scope(
    design_input: Dict[str, Any],
    baseline_snapshot: Dict[str, Any],
    target_scene_actors: Optional[List[Dict[str, Any]]] = None,
    target_dynamic_spec_tree: Optional[Dict[str, Any]] = None,
    delta_policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    比较 baseline 与目标场景，输出最小 delta_context。

    当前 Phase 5 只真正支持 append/new-actor 的执行闭环；
    patch / replace / migrate 仅做到识别、表达和阻断。
    """
    baseline_actors = baseline_snapshot.get("current_spec_baseline", {}).get("scene_spec", {}).get("actors", [])
    target_actors = target_scene_actors or []

    baseline_by_name = {
        actor.get("actor_name", ""): actor
        for actor in baseline_actors
        if actor.get("actor_name")
    }
    target_by_name = {
        actor.get("actor_name", ""): actor
        for actor in target_actors
        if actor.get("actor_name")
    }

    append_specs = []
    patch_specs = []
    replace_specs = []
    deprecated_specs = []

    for actor_name, target_actor in target_by_name.items():
        baseline_actor = baseline_by_name.get(actor_name)
        if baseline_actor is None:
            append_specs.append(
                {
                    "spec_family": "scene_spec",
                    "actor_name": actor_name,
                    "operation": "append_actor",
                    "target_actor": copy.deepcopy(target_actor),
                }
            )
            continue

        if _actor_changed(baseline_actor, target_actor):
            patch_specs.append(
                {
                    "spec_family": "scene_spec",
                    "actor_name": actor_name,
                    "operation": "patch_actor",
                    "baseline_actor": copy.deepcopy(baseline_actor),
                    "target_actor": copy.deepcopy(target_actor),
                }
            )

    for actor_name, baseline_actor in baseline_by_name.items():
        if actor_name not in target_by_name:
            replace_specs.append(
                {
                    "spec_family": "scene_spec",
                    "actor_name": actor_name,
                    "operation": "remove_or_replace_actor",
                    "baseline_actor": copy.deepcopy(baseline_actor),
                }
            )
            deprecated_specs.append(
                {
                    "spec_family": "scene_spec",
                    "actor_name": actor_name,
                    "reason": "目标设计输入中不再包含该 Actor",
                }
            )

    unsupported_items = []
    potential_breakpoints = []
    required_regression_checks = []
    contract_refs = []
    delta_policy = delta_policy or {}
    target_dynamic_spec_tree = target_dynamic_spec_tree or {}

    if patch_specs or replace_specs:
        delta_intent = "patch_existing_content"
        unsupported_items.extend(
            [
                "Phase 5 当前仅执行 append/new-actor；patch / replace 仍处于表达与阻断阶段",
            ]
        )
        potential_breakpoints.extend(
            [
                "已有 Actor 需要变更或替换，当前执行层无法安全自动落地",
            ]
        )
        required_regression_checks.extend(
            [
                "existing_actor_preserved",
                "map_check_clean",
            ]
        )
        contract_refs = [
            "SpecPatchContractModel",
            "MigrationContractModel",
            "RegressionValidationContractModel",
        ]
    elif append_specs:
        delta_intent = "append_actor"
        required_regression_checks.extend(
            [
                "existing_actor_presence",
                "new_actor_presence",
                "map_check_clean",
            ]
        )
        contract_refs = [
            "SpecPatchContractModel",
            "RegressionValidationContractModel",
        ]
    else:
        delta_intent = "no_change"
        required_regression_checks.append("baseline_actor_presence")
        contract_refs = ["RegressionValidationContractModel"]

    affected_specs = _build_affected_specs(append_specs, patch_specs, replace_specs)
    if _has_runtime_sensitive_specs(target_dynamic_spec_tree):
        affected_specs.extend(["turn_flow_spec", "decision_ui_spec", "runtime_wiring_spec"])
        required_regression_checks.extend(delta_policy.get("regression_focus", []))
        if patch_specs or replace_specs:
            contract_refs.extend(["TurnFlowPatchContract", "DecisionUIPatchContract"])
            potential_breakpoints.extend(delta_policy.get("high_risk_breakpoints", []))
    affected_domains = _build_affected_domains(affected_specs)

    return {
        "delta_intent": delta_intent,
        "delta_scope": {
            "baseline_actor_count": len(baseline_actors),
            "target_actor_count": len(target_actors),
            "append_count": len(append_specs),
            "patch_count": len(patch_specs),
            "replace_count": len(replace_specs),
        },
        "affected_domains": affected_domains,
        "affected_specs": sorted(set(affected_specs)),
        "patch_specs": patch_specs,
        "expand_specs": [],
        "replace_specs": replace_specs,
        "append_specs": append_specs,
        "deprecated_specs": deprecated_specs,
        "potential_breakpoints": sorted(set(potential_breakpoints)),
        "required_regression_checks": sorted(set(required_regression_checks)),
        "unsupported_items": unsupported_items,
        "baseline_actor_refs": sorted(baseline_by_name.keys()),
        "contract_refs": sorted(set(contract_refs)),
        "delta_policy": delta_policy,
    }


def _actor_changed(baseline_actor: Dict[str, Any], target_actor: Dict[str, Any]) -> bool:
    """比较 Actor 的 class / transform 是否变化。"""
    if (baseline_actor.get("actor_class") or baseline_actor.get("class")) != (
        target_actor.get("actor_class") or target_actor.get("class")
    ):
        return True

    return baseline_actor.get("transform", {}) != target_actor.get("transform", {})


def _build_affected_specs(
    append_specs: List[Dict[str, Any]],
    patch_specs: List[Dict[str, Any]],
    replace_specs: List[Dict[str, Any]],
) -> List[str]:
    """根据差量内容推导受影响 spec。"""
    affected_specs = []
    if append_specs or patch_specs or replace_specs:
        affected_specs.extend(["scene_spec", "validation_spec"])
    if append_specs:
        affected_specs.append("boardgame_spec")
    return sorted(set(affected_specs))


def _build_affected_domains(affected_specs: List[str]) -> List[str]:
    """根据受影响 spec 推导域。"""
    domains = []
    if "scene_spec" in affected_specs:
        domains.append("world")
    if "validation_spec" in affected_specs:
        domains.append("validation")
    if "boardgame_spec" in affected_specs:
        domains.append("governance")
    if "turn_flow_spec" in affected_specs or "runtime_wiring_spec" in affected_specs:
        domains.append("runtime")
    if "decision_ui_spec" in affected_specs:
        domains.append("ui")
    return [domain for domain in domains if domain in SUPPORTED_DOMAINS]


def _has_runtime_sensitive_specs(target_dynamic_spec_tree: Dict[str, Any]) -> bool:
    """判断目标树是否包含回合/UI/runtime 节点。"""
    return any(
        node_name in target_dynamic_spec_tree
        for node_name in ["turn_flow_spec", "decision_ui_spec", "runtime_wiring_spec"]
    )
