"""
Lowering v2 - Stage 6 (v2.0)

职责：
  - 将 Cross Review v2 审核后的 reviewed_dynamic_spec_tree 下沉为 Build IR v2
  - 为每个 build step 生成 naming_resolution_log
  - 强制体现 GDD-First 命名优先级与“C++ 主逻辑 + Blueprint 薄层”
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


PROJECT_MODULE_NAME = Path(__file__).resolve().parents[4].name

# family 别名归一化。
FAMILY_ALIASES: Dict[str, str] = {
    "start_screen": "start_screen_spec",
    "main_menu": "main_menu_spec",
    "settings": "settings_spec",
    "pause_menu": "pause_spec",
    "results": "results_spec",
    "hud": "hud_spec",
}

# baseline family 到 UE 目录/命名的稳定映射。
BASELINE_FAMILY_CONFIG: Dict[str, Dict[str, str]] = {
    "start_screen_spec": {"widget": "StartScreen", "group": "UI"},
    "main_menu_spec": {"widget": "MainMenu", "group": "UI"},
    "settings_spec": {"widget": "Settings", "group": "UI"},
    "pause_spec": {"widget": "PauseMenu", "group": "UI"},
    "results_spec": {"widget": "Results", "group": "UI"},
    "hud_spec": {"widget": "HUD", "group": "UI"},
    "input_foundation_spec": {"cpp": "InputFoundation", "group": "Systems"},
    "audio_foundation_spec": {"cpp": "AudioFoundation", "group": "Systems"},
    "platform_foundation_spec": {"cpp": "PlatformFoundation", "group": "Systems"},
}

# gameplay family 到默认实体名称的稳定映射。
GAMEPLAY_FAMILY_CONFIG: Dict[str, Dict[str, str]] = {
    "board_topology_spec": {"cpp": "Board", "group": "Board"},
    "tile_system_spec": {"cpp": "TileSystem", "group": "Board"},
    "turn_flow_spec": {"cpp": "TurnLoop", "group": "Gameplay"},
    "dice_rule_spec": {"cpp": "Dice", "group": "Gameplay"},
    "property_economy_spec": {"cpp": "Economy", "group": "Gameplay"},
    "player_management_spec": {"cpp": "PlayerManagement", "group": "Gameplay"},
    "jail_rule_spec": {"cpp": "Jail", "group": "Gameplay"},
}


def _now_iso() -> str:
    """返回 UTC ISO 时间戳。"""
    return datetime.now(timezone.utc).isoformat()


def _normalize_spec_tree(spec_tree: Dict[str, Any]) -> Dict[str, Any]:
    """归一化 family 名称。"""
    normalized: Dict[str, Any] = {}
    for family, spec in spec_tree.items():
        normalized[FAMILY_ALIASES.get(family, family)] = spec
    return normalized


def _slug_to_pascal(text: str) -> str:
    """把 snake_case / kebab-case 转成 PascalCase。"""
    parts = [part for part in text.replace("-", "_").split("_") if part]
    return "".join(part[:1].upper() + part[1:] for part in parts) or "Generated"


def _infer_project_token(root_skill_contract: Dict[str, Any]) -> str:
    """推导项目语义 token，用于命名。"""
    contract_id = str(root_skill_contract.get("contract_id", ""))
    parts = contract_id.split(".")
    if len(parts) >= 2 and parts[1]:
        return _slug_to_pascal(parts[1])
    source_path = root_skill_contract.get("source_gdd", {}).get("file_path", "")
    stem = Path(source_path).stem.replace("GDD_", "")
    return _slug_to_pascal(stem) or "Project"


def _family_profile(
    family: str,
    family_source: Dict[str, Any],
) -> Dict[str, str]:
    """为 family 计算 lowering 配置。"""
    domain_type = family_source.get("domain_type", "")
    if domain_type == "baseline":
        profile = BASELINE_FAMILY_CONFIG.get(family, {})
        if "widget" in profile:
            return {
                "domain_type": "baseline",
                "group": profile.get("group", "UI"),
                "build_action": "create_widget_blueprint",
                "entity_name": profile["widget"],
            }
        return {
            "domain_type": "baseline",
            "group": profile.get("group", "Systems"),
            "build_action": "create_cpp_class",
            "entity_name": profile.get("cpp", _slug_to_pascal(family.replace("_spec", ""))),
        }

    profile = GAMEPLAY_FAMILY_CONFIG.get(family, {})
    return {
        "domain_type": "gameplay",
        "group": profile.get("group", "Gameplay"),
        "build_action": "create_cpp_class",
        "entity_name": profile.get("cpp", _slug_to_pascal(family.replace("_spec", ""))),
    }


def _naming_candidate_bundle(
    family: str,
    profile: Dict[str, str],
    root_skill_contract: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    生成 class_name / file_path / asset_path 的命名候选。

    tier 定义：
      1 = GDD 显式命名
      2 = GDD 风格推导
      3 = 项目规范
      4 = 默认回退
    """
    project_token = _infer_project_token(root_skill_contract)
    naming_hints = root_skill_contract.get("naming_hints", {})
    explicit_name = naming_hints.get(family)

    if explicit_name:
        base_name = str(explicit_name)
        tier = 1
        evidence = f"Root Skill Contract naming_hints['{family}']"
    elif project_token != "Project":
        base_name = f"{project_token}{profile['entity_name']}"
        tier = 2
        evidence = f"依据 contract_id 推导项目风格命名：{project_token}"
    elif family in GAMEPLAY_FAMILY_CONFIG or family in BASELINE_FAMILY_CONFIG:
        base_name = profile["entity_name"]
        tier = 3
        evidence = f"依据项目规范与 family 映射生成：{family}"
    else:
        base_name = _slug_to_pascal(family.replace("_spec", ""))
        tier = 4
        evidence = f"按 family 默认回退命名：{family}"

    if profile["build_action"] == "create_widget_blueprint":
        class_name = f"U{base_name}Widget"
        asset_name = f"WBP_{base_name}"
        asset_path = f"/Game/{PROJECT_MODULE_NAME}/UI/Widgets/{asset_name}"
        file_path = f"Source/{PROJECT_MODULE_NAME}/UI/{base_name}Widget.h"
    else:
        class_name = f"A{base_name}"
        asset_name = f"BP_{base_name}"
        asset_path = f"/Game/{PROJECT_MODULE_NAME}/Blueprints/{profile['group']}/{asset_name}"
        file_path = f"Source/{PROJECT_MODULE_NAME}/{profile['group']}/{base_name}.h"

    alternatives = []
    if project_token != "Project":
        alternatives.append(profile["entity_name"])
    if base_name != _slug_to_pascal(family.replace("_spec", "")):
        alternatives.append(_slug_to_pascal(family.replace("_spec", "")))

    # 过滤重复备选项。
    dedup_alternatives = [item for item in dict.fromkeys(alternatives) if item != base_name]

    return {
        "class_name": {
            "resolved": class_name,
            "tier": tier,
            "evidence": evidence,
            "alternatives_considered": [f"A{item}" if profile["build_action"] != "create_widget_blueprint" else f"U{item}Widget" for item in dedup_alternatives],
        },
        "file_path": {
            "resolved": file_path,
            "tier": 3,
            "evidence": f"项目规范：Source/{PROJECT_MODULE_NAME}/{profile['group']}/",
            "alternatives_considered": [],
        },
        "asset_path": {
            "resolved": asset_path,
            "tier": 3,
            "evidence": f"项目规范：/Game/{PROJECT_MODULE_NAME}/ 按 UE5 前缀落盘",
            "alternatives_considered": [],
        },
    }


def _check_dependency_closure(
    family_source_map: Dict[str, Dict[str, Any]],
    skill_graph: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """检查 Skill Graph 依赖闭合情况。"""
    warnings: List[Dict[str, Any]] = []
    node_map = {node.get("instance_id", ""): node for node in skill_graph.get("nodes", [])}
    existing_skill_ids = {
        source.get("skill_instance_id", "")
        for source in family_source_map.values()
        if source.get("skill_instance_id")
    }

    for edge in skill_graph.get("edges", []):
        if edge.get("type") != "dependency":
            continue
        from_id = edge.get("from", "")
        to_id = edge.get("to", "")
        if to_id not in existing_skill_ids:
            continue
        if from_id in existing_skill_ids:
            continue
        warnings.append(
            {
                "type": "dependency_gap",
                "from": from_id,
                "to": to_id,
                "message": f"依赖未闭合：{to_id} 需要 {from_id}，但 Stage 4 产物中未出现该 skill。",
                "from_domain_type": node_map.get(from_id, {}).get("domain_type", ""),
            }
        )
    return warnings


def _build_step_dependencies(
    skill_instance_id: str,
    build_step_by_skill: Dict[str, str],
    skill_graph: Dict[str, Any],
) -> List[str]:
    """把 skill graph 的 dependency 转为 build step depends_on。"""
    depends_on: List[str] = []
    for edge in skill_graph.get("edges", []):
        if edge.get("type") != "dependency":
            continue
        if edge.get("to") != skill_instance_id:
            continue
        source_step = build_step_by_skill.get(edge.get("from", ""))
        if source_step:
            depends_on.append(source_step)
    return sorted(dict.fromkeys(depends_on))


def _generate_build_step(
    family: str,
    spec: Dict[str, Any],
    family_source: Dict[str, Any],
    naming_resolution_log: Dict[str, Any],
    step_index: int,
) -> Dict[str, Any]:
    """为单个 family 生成 Build IR step。"""
    profile = _family_profile(family, family_source)
    skill_instance_id = family_source.get("skill_instance_id", "")
    class_name = naming_resolution_log["class_name"]["resolved"]
    file_path = naming_resolution_log["file_path"]["resolved"]
    asset_path = naming_resolution_log["asset_path"]["resolved"]

    implementation_layer = "cpp" if profile["build_action"] == "create_cpp_class" else "blueprint"
    tool_preference = "cpp_code" if implementation_layer == "cpp" else "mcp_bridge"

    return {
        "step_id": f"bir_{step_index:03d}_{family}",
        "action": profile["build_action"],
        "source_skill_instance_id": skill_instance_id,
        "source_families": [family],
        "implementation_layer": implementation_layer,
        "target": {
            "class_name": class_name,
            "file_path": file_path,
            "asset_path": asset_path,
        },
        "params": {
            "spec": spec,
            "domain_type": family_source.get("domain_type", ""),
            "required_elements": spec.get("required_elements", []),
            "selected_realization": spec.get("selected_realization", {}),
        },
        "constraints_applied": sorted(
            key
            for key in spec.keys()
            if key in {"locked_constraints", "tile_count", "layout_shape", "movement_direction", "corner_tiles"}
        ),
        "execution_hints": {
            "tool_preference": tool_preference,
            "thin_blueprint_bridge": implementation_layer == "cpp",
            "contains_provisional": False,
        },
        "naming_resolution_log": naming_resolution_log,
    }


def _generate_validation_points(build_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """为 Build IR 生成最小验证点。"""
    validations: List[Dict[str, Any]] = []
    for step in build_steps:
        step_id = step["step_id"]
        if step["implementation_layer"] == "cpp":
            validations.append(
                {
                    "validation_id": f"val_{step_id}_cpp",
                    "after_step": step_id,
                    "check_type": "cpp_symbol_exists",
                    "description": f"验证 {step['target']['class_name']} 已创建并可编译。",
                    "expected": True,
                }
            )
            validations.append(
                {
                    "validation_id": f"val_{step_id}_bp_bridge",
                    "after_step": step_id,
                    "check_type": "blueprint_bridge_exists",
                    "description": f"验证 {step['target']['asset_path']} 作为薄层 Blueprint 桥接资源存在。",
                    "expected": True,
                }
            )
        else:
            validations.append(
                {
                    "validation_id": f"val_{step_id}_asset",
                    "after_step": step_id,
                    "check_type": "asset_exists",
                    "description": f"验证 {step['target']['asset_path']} 已生成。",
                    "expected": True,
                }
            )
    return validations


def _make_naming_sidecar_entries(build_steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从 build steps 抽取 naming_resolution_log sidecar。"""
    entries: List[Dict[str, Any]] = []
    for step in build_steps:
        entries.append(
            {
                "ir_action_id": step["step_id"],
                "action": step["action"],
                "source_skill_instance_id": step.get("source_skill_instance_id", ""),
                "naming_resolution_log": step["naming_resolution_log"],
            }
        )
    return entries


def _summarize_tiers(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    """统计 naming log 的 tier 分布。"""
    counter: Counter[str] = Counter()
    for entry in entries:
        naming_log = entry.get("naming_resolution_log", {})
        for field_value in naming_log.values():
            tier = str(field_value.get("tier", ""))
            if tier:
                counter[tier] += 1
    return dict(sorted(counter.items()))


def create_build_ir_v2(
    cross_review_report: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    skill_graph: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, Any]:
    """生成 Build IR v2 与 naming_resolution_log。"""
    contract_id = cross_review_report.get("source_contract_id") or root_skill_contract.get("contract_id", "")
    review_id = cross_review_report.get("review_id", "")
    spec_tree = _normalize_spec_tree(cross_review_report.get("reviewed_dynamic_spec_tree", {}))
    family_source_map = cross_review_report.get("family_source_map", {})
    dependency_warnings = _check_dependency_closure(family_source_map, skill_graph)

    build_steps: List[Dict[str, Any]] = []
    build_step_by_skill: Dict[str, str] = {}
    bound_families: List[str] = []
    partially_bound_families: List[str] = []

    for index, family in enumerate(sorted(spec_tree.keys()), start=1):
        spec = spec_tree[family]
        family_source = family_source_map.get(
            family,
            {
                "skill_instance_id": family.replace("_spec", ""),
                "domain_type": "gameplay" if family in GAMEPLAY_FAMILY_CONFIG else "baseline",
            },
        )
        naming_log = _naming_candidate_bundle(family, _family_profile(family, family_source), root_skill_contract)
        build_step = _generate_build_step(family, spec, family_source, naming_log, index)
        build_steps.append(build_step)
        build_step_by_skill[family_source.get("skill_instance_id", "")] = build_step["step_id"]

        if build_step["implementation_layer"] in {"cpp", "blueprint"}:
            bound_families.append(family)
        else:
            partially_bound_families.append(family)

    for step in build_steps:
        skill_instance_id = step.get("source_skill_instance_id", "")
        step["depends_on"] = _build_step_dependencies(skill_instance_id, build_step_by_skill, skill_graph)
        if any(item.get("source_skill_instance_id") == skill_instance_id for item in cross_review_report.get("provisional_items", [])):
            step["execution_hints"]["contains_provisional"] = True

    validation_ir = _generate_validation_points(build_steps)
    naming_entries = _make_naming_sidecar_entries(build_steps)
    ir_id = (
        f"ir.{contract_id.replace('rsc.', '')}"
        if contract_id
        else f"ir.build.{_now_iso()[:10]}"
    )

    build_ir = {
        "ir_version": "2.0",
        "ir_id": ir_id,
        "source_review_id": review_id,
        "source_contract_id": contract_id,
        "phase_scope": phase_scope,
        "build_steps": build_steps,
        "validation_ir": validation_ir,
        "lowering_report": {
            "families_received": sorted(spec_tree.keys()),
            "families_bound": bound_families,
            "families_partially_bound": partially_bound_families,
            "unbound_requirements": [warning["message"] for warning in dependency_warnings],
            "dependency_closure_warnings": dependency_warnings,
            "cpp_step_count": sum(1 for step in build_steps if step["implementation_layer"] == "cpp"),
            "blueprint_step_count": sum(1 for step in build_steps if step["implementation_layer"] == "blueprint"),
            "baseline_step_count": sum(
                1
                for family in spec_tree.keys()
                if family_source_map.get(family, {}).get("domain_type") == "baseline"
            ),
            "gameplay_step_count": sum(
                1
                for family in spec_tree.keys()
                if family_source_map.get(family, {}).get("domain_type") == "gameplay"
            ),
        },
        "recovery_hints": [],
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.LoweringV2.v2",
            "project_module": PROJECT_MODULE_NAME,
        },
    }

    naming_resolution_log = {
        "log_version": "1.0",
        "source_ir_id": ir_id,
        "entries": naming_entries,
        "summary": {
            "total_actions": len(naming_entries),
            "resolved_fields": sum(len(entry.get("naming_resolution_log", {})) for entry in naming_entries),
            "by_tier": _summarize_tiers(naming_entries),
        },
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.LoweringV2.NamingResolver.v2",
        },
    }

    return {
        "build_ir": build_ir,
        "naming_resolution_log": naming_resolution_log,
    }
