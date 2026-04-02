"""
端到端运行脚本：JRPG Turn-Based + Reviewed Handoff 最小闭环。

Phase 7 新增要求：
- simulated 继续作为快速回归入口
- bridge_rc_api 升级为真实 UE5 smoke
- 真实 smoke 需要结构级战斗闭环验证 + 6 张截图证据
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Tuple


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "Plugins", "AgentBridge", "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from bridge.project_config import get_dated_project_reports_dir
from compiler.handoff import build_handoff, serialize_handoff
from compiler.intake import read_gdd
from orchestrator.handoff_runner import run_from_handoff


_RC_ENDPOINT = "http://localhost:30010/remote/info"
_PHASE7_EVIDENCE_TASK_ID = "task_phase7_jrpg_turn_based_demo"
_PHASE7_EVIDENCE_SCENARIO = "bridge_rc_api_smoke"
_JRPG_MESH_CONFIG = {
    "BattleArena": "/Engine/BasicShapes/Plane.Plane",
    "HeroUnit_1": "/Engine/BasicShapes/Sphere.Sphere",
    "EnemyUnit_1": "/Engine/BasicShapes/Cone.Cone",
    "CommandMenuAnchor": "/Engine/BasicShapes/Cube.Cube",
}


def run_jrpg_turn_based_demo(
    bridge_mode: str = "simulated",
    mode: str = "greenfield_bootstrap",
) -> Dict[str, Any]:
    """运行 JRPG 最小闭环。"""
    gdd_path = os.path.join(PROJECT_ROOT, "ProjectInputs", "GDD", "jrpg_turn_based_v1.md")
    handoff_draft_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Handoffs", "draft")
    handoff_approved_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Handoffs", "approved")
    report_dir = str(get_dated_project_reports_dir())

    for directory in [handoff_draft_dir, handoff_approved_dir, report_dir]:
        os.makedirs(directory, exist_ok=True)

    print("=" * 60)
    print("JRPG Turn-Based + Handoff 最小闭环")
    print("=" * 60)

    design_input = read_gdd(gdd_path)
    project_state = _build_project_state(mode)

    print(f"  游戏类型: {design_input['game_type']}")
    print(f"  执行模式: {mode}")

    handoff = build_handoff(
        design_input=design_input,
        mode=mode,
        project_state=project_state,
        target_stage="vertical_slice",
        projection_profile="preview_static",
    )
    print(f"  Handoff ID: {handoff['handoff_id']}")
    print(f"  Handoff 状态: {handoff['status']}")
    print(f"  激活基础域: {handoff.get('governance_context', {}).get('base_domain_refs', [])}")

    draft_path = serialize_handoff(handoff, handoff_draft_dir, "yaml")
    approved_handoff = dict(handoff)
    approved_handoff["status"] = "approved_for_execution"
    approved_path = serialize_handoff(approved_handoff, handoff_approved_dir, "yaml")

    rc_boot_result: Dict[str, Any] = {}
    if bridge_mode == "bridge_rc_api":
        rc_boot_result = _ensure_rc_editor_ready(report_dir)
        if rc_boot_result.get("status") != "ready":
            failed_result = {
                "status": "failed",
                "step_results": [],
                "execution_report": {},
            }
            smoke_report_path = _write_phase7_smoke_report(
                report_dir=report_dir,
                bridge_mode=bridge_mode,
                mode=mode,
                handoff=approved_handoff,
                approved_path=approved_path,
                execution_report_path="",
                rc_boot_result=rc_boot_result,
                actor_presence={},
                layout_assertions={},
                structure_assertions=_build_structure_assertions(approved_handoff, {}, mode),
                visual_setup={},
                current_level="",
            )
            acceptance_report_path = _write_phase7_acceptance_report(
                bridge_mode=bridge_mode,
                smoke_report_path=smoke_report_path,
                evidence_result={},
                report_dir=report_dir,
            )
            failed_result["smoke_report_path"] = smoke_report_path
            failed_result["evidence_result"] = {}
            failed_result["phase7_smoke_acceptance_report_path"] = acceptance_report_path
            print(f"PHASE7_SMOKE_REPORT={smoke_report_path}")
            print(f"PHASE7_ACCEPTANCE_REPORT={acceptance_report_path}")
            print(f"  RC 启动失败: {rc_boot_result.get('error', '')}")
            return failed_result

    result = run_from_handoff(
        approved_path,
        report_output_dir=report_dir,
        bridge_mode=bridge_mode,
    )
    print(f"  执行状态: {result['status']}")
    print(f"  Draft Handoff: {draft_path}")
    print(f"  Approved Handoff: {approved_path}")
    print(f"  报告目录: {report_dir}")

    smoke_report_path = ""
    evidence_result: Dict[str, Any] = {}
    acceptance_report_path = ""

    if bridge_mode == "bridge_rc_api":
        smoke_report_path, smoke_report = _run_phase7_jrpg_runtime_smoke(
            result=result,
            bridge_mode=bridge_mode,
            mode=mode,
            handoff=approved_handoff,
            approved_path=approved_path,
            report_dir=report_dir,
            rc_boot_result=rc_boot_result,
        )
        evidence_result = _try_capture_phase7_evidence(
            approved_path=approved_path,
            smoke_report=smoke_report,
            report_path=smoke_report_path,
        )
        acceptance_report_path = _write_phase7_acceptance_report(
            bridge_mode=bridge_mode,
            smoke_report_path=smoke_report_path,
            evidence_result=evidence_result,
            report_dir=report_dir,
        )
        print(f"PHASE7_SMOKE_REPORT={smoke_report_path}")
        print(f"PHASE7_ACCEPTANCE_REPORT={acceptance_report_path}")

        acceptance_report = _load_json_file(acceptance_report_path)
        if acceptance_report.get("overall_status") != "passed":
            result["status"] = "failed"

    result["smoke_report_path"] = smoke_report_path
    result["evidence_result"] = evidence_result
    result["phase7_smoke_acceptance_report_path"] = acceptance_report_path
    return result


def _build_project_state(mode: str) -> Dict[str, Any]:
    """构建 JRPG demo 使用的项目现状。"""
    if mode != "brownfield_expansion":
        return {
            "project_name": "Mvpv4TestCodex",
            "engine_version": "UE5.5.4",
            "current_level": "/Game/Maps/TestMap",
            "actor_count": 0,
            "is_empty": True,
            "actors": [],
            "has_existing_content": False,
            "has_baseline": False,
            "baseline_refs": [],
            "registry_refs": [],
            "known_issues_summary": [],
            "current_project_state_digest": "jrpg-greenfield-demo",
        }

    actors = [
        {
            "actor_name": "BattleArena",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.BattleArena",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [6.0, 6.0, 0.2],
            },
            "tags": ["Baseline"],
        },
        {
            "actor_name": "HeroUnit_1",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.HeroUnit_1",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [-180.0, 0.0, 50.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [0.8, 0.8, 1.6],
            },
            "tags": ["Baseline"],
        },
    ]

    return {
        "project_name": "Mvpv4TestCodex",
        "engine_version": "UE5.5.4",
        "current_level": "/Game/Maps/TestMap",
        "actor_count": len(actors),
        "is_empty": False,
        "actors": actors,
        "has_existing_content": True,
        "has_baseline": False,
        "baseline_refs": [],
        "registry_refs": [],
        "known_issues_summary": [],
        "current_project_state_digest": "jrpg-brownfield-demo",
    }


def _ensure_rc_editor_ready(report_dir: str) -> Dict[str, Any]:
    """确保 RC Editor 会话可用；优先复用，必要时自动拉起。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rc_info_path = os.path.join(report_dir, f"phase7_jrpg_rc_info_{timestamp}.json")
    boot_log_path = os.path.join(report_dir, f"phase7_jrpg_rc_boot_{timestamp}.log")
    script_path = os.path.join(PROJECT_ROOT, "Scripts", "validation", "start_ue_editor_project.ps1")
    project_path = os.path.join(PROJECT_ROOT, "Mvpv4TestCodex.uproject")

    command = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script_path,
        "-ProjectPath",
        project_path,
        "-RcTimeoutSec",
        "300",
        "-RcOutputPath",
        rc_info_path,
    ]
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    log_lines = [
        f"[command] {' '.join(command)}",
        "",
        "[stdout]",
        completed.stdout or "",
        "",
        "[stderr]",
        completed.stderr or "",
    ]
    with open(boot_log_path, "w", encoding="utf-8") as file:
        file.write("\n".join(log_lines))

    if completed.returncode != 0:
        return {
            "status": "failed",
            "error": f"start_ue_editor_project.ps1 退出码={completed.returncode}",
            "boot_log_path": boot_log_path,
            "rc_info_path": rc_info_path,
            "rc_endpoint": _RC_ENDPOINT,
            "editor_boot_policy": "reuse_or_launch",
        }

    return {
        "status": "ready",
        "boot_log_path": boot_log_path,
        "rc_info_path": rc_info_path,
        "rc_endpoint": _RC_ENDPOINT,
        "editor_boot_policy": "reuse_or_launch",
    }


def _run_phase7_jrpg_runtime_smoke(
    result: Dict[str, Any],
    bridge_mode: str,
    mode: str,
    handoff: Dict[str, Any],
    approved_path: str,
    report_dir: str,
    rc_boot_result: Dict[str, Any],
) -> Tuple[str, Dict[str, Any]]:
    """执行 Phase 7 JRPG 真机 smoke。"""
    actor_paths = _find_actor_paths_from_result(result)
    visual_setup = _apply_jrpg_visuals(actor_paths)
    actor_presence, current_level = _collect_actor_runtime_state_v2(actor_paths)
    layout_assertions = _build_layout_assertions(actor_presence)
    structure_assertions = _build_structure_assertions(handoff, actor_presence, mode)

    report_path = _write_phase7_smoke_report(
        report_dir=report_dir,
        bridge_mode=bridge_mode,
        mode=mode,
        handoff=handoff,
        approved_path=approved_path,
        execution_report_path=result.get("report_path", ""),
        rc_boot_result=rc_boot_result,
        actor_presence=actor_presence,
        layout_assertions=layout_assertions,
        structure_assertions=structure_assertions,
        visual_setup=visual_setup,
        current_level=current_level,
    )
    return report_path, _load_json_file(report_path)


def _find_actor_paths_from_result(result: Dict[str, Any]) -> Dict[str, str]:
    """从执行结果中提取关键 ActorPath。"""
    actor_paths: Dict[str, str] = {}
    for step in result.get("step_results", []):
        step_result = step.get("result", {})
        actor_name = step_result.get("actor_name", "")
        actor_path = step_result.get("actor_path", "")
        if actor_name and actor_path:
            actor_paths[actor_name] = actor_path
    return actor_paths


def _apply_jrpg_visuals(actor_paths: Dict[str, str]) -> Dict[str, Any]:
    """给 JRPG 关键 Actor 绑定最小可视化 mesh，保证截图能看见对象。"""
    from bridge.remote_control_client import call_function

    results: Dict[str, Any] = {}
    for actor_name, actor_path in actor_paths.items():
        mesh_path = _JRPG_MESH_CONFIG.get(actor_name, "")
        if not mesh_path:
            results[actor_name] = {
                "status": "skipped",
                "reason": "未配置 mesh",
            }
            continue

        try:
            component_response = call_function(actor_path, "K2_GetRootComponent", {})
            component_path = component_response.get("ReturnValue", "")
            if not component_path:
                raise RuntimeError("未能解析根组件路径")

            set_mesh_response = call_function(
                component_path,
                "SetStaticMesh",
                {"NewMesh": mesh_path},
            )
            if not bool(set_mesh_response.get("ReturnValue", False)):
                raise RuntimeError(f"SetStaticMesh returned false: {mesh_path}")
            results[actor_name] = {
                "status": "passed",
                "actor_path": actor_path,
                "component_path": component_path,
                "mesh_path": mesh_path,
                "set_mesh_response": set_mesh_response,
            }
        except Exception as exc:
            results[actor_name] = {
                "status": "failed",
                "actor_path": actor_path,
                "mesh_path": mesh_path,
                "error": str(exc),
            }
    return results


def _collect_actor_runtime_state(actor_paths: Dict[str, str]) -> Tuple[Dict[str, Any], str]:
    """通过 L1 读回收集关键 Actor 的真实状态。"""
    from bridge.bridge_core import BridgeChannel, get_channel, set_channel
    from bridge.query_tools import get_actor_bounds, get_actor_state, list_level_actors

    previous_channel = get_channel()
    actor_presence: Dict[str, Any] = {}
    current_level = ""

    try:
        set_channel(BridgeChannel.CPP_PLUGIN)
        listed_actors_response = list_level_actors()
        listed_actors = listed_actors_response.get("data", {}).get("actors", [])
        current_level = listed_actors_response.get("data", {}).get("level_path", "")
        listed_paths_by_name = {
            actor.get("actor_name", ""): actor.get("actor_path", "")
            for actor in listed_actors
            if isinstance(actor, dict) and actor.get("actor_name")
        }

        for actor_name in _JRPG_MESH_CONFIG.keys():
            actor_path = actor_paths.get(actor_name, "") or listed_paths_by_name.get(actor_name, "")
            entry: Dict[str, Any] = {
                "actor_name": actor_name,
                "actor_path": actor_path,
                "listed_actor_path": listed_paths_by_name.get(actor_name, ""),
            }

            if not actor_path:
                entry["status"] = "failed"
                entry["error"] = "未找到 actor_path"
                actor_presence[actor_name] = entry
                continue

            state_response = get_actor_state(actor_path)
            bounds_response = get_actor_bounds(actor_path)
            entry["state_response"] = state_response
            entry["bounds_response"] = bounds_response
            entry["status"] = "passed"

            if state_response.get("status") != "success":
                entry["status"] = "failed"
                entry["error"] = state_response.get("summary", "GetActorState 失败")
            else:
                state_data = state_response.get("data", {})
                entry["actual_actor_name"] = state_data.get("actor_name", "")
                entry["transform"] = state_data.get("transform", {})

            if bounds_response.get("status") == "success":
                bounds_data = bounds_response.get("data", {})
                entry["bounds_origin"] = bounds_data.get("world_bounds_origin", [])
                entry["bounds_extent"] = bounds_data.get("world_bounds_extent", [])
            else:
                entry["bounds_origin"] = []
                entry["bounds_extent"] = []
                if entry["status"] == "passed":
                    entry["status"] = "failed"
                    entry["error"] = bounds_response.get("summary", "GetActorBounds 失败")

            actor_presence[actor_name] = entry
    finally:
        set_channel(previous_channel)

    return actor_presence, current_level


def _collect_actor_runtime_state_v2(actor_paths: Dict[str, str]) -> Tuple[Dict[str, Any], str]:
    """通过 RC 原生调用收集关键 Actor 的真实状态。

    Phase 7 JRPG smoke 生成的 Actor 使用 /Temp/Untitled_1... 路径。
    这里直接走 RC 原生调用，避免旧的 CPP_PLUGIN 路径解析把对象读偏。
    """
    from bridge.remote_control_client import call_function

    actor_presence: Dict[str, Any] = {}
    current_level = _read_current_level_via_rc()

    for actor_name in _JRPG_MESH_CONFIG.keys():
        actor_path = actor_paths.get(actor_name, "")
        entry: Dict[str, Any] = {
            "actor_name": actor_name,
            "actor_path": actor_path,
            "listed_actor_path": "",
        }

        if not actor_path:
            entry["status"] = "failed"
            entry["error"] = "未找到 actor_path"
            actor_presence[actor_name] = entry
            continue

        try:
            location_response = call_function(actor_path, "K2_GetActorLocation", {})
            rotation_response = call_function(actor_path, "K2_GetActorRotation", {})
            scale_response = call_function(actor_path, "GetActorScale3D", {})
            bounds_response = call_function(
                actor_path,
                "GetActorBounds",
                {"bOnlyCollidingComponents": False},
            )

            location = location_response.get("ReturnValue", {})
            rotation = rotation_response.get("ReturnValue", {})
            scale = scale_response.get("ReturnValue", {})
            origin = bounds_response.get("Origin", {})
            extent = bounds_response.get("BoxExtent", {})

            transform = {
                "location": [location.get("X", 0.0), location.get("Y", 0.0), location.get("Z", 0.0)],
                "rotation": [rotation.get("Pitch", 0.0), rotation.get("Yaw", 0.0), rotation.get("Roll", 0.0)],
                "relative_scale3d": [scale.get("X", 1.0), scale.get("Y", 1.0), scale.get("Z", 1.0)],
            }
            bounds_origin = [origin.get("X", 0.0), origin.get("Y", 0.0), origin.get("Z", 0.0)]
            bounds_extent = [extent.get("X", 0.0), extent.get("Y", 0.0), extent.get("Z", 0.0)]

            entry["state_response"] = {
                "status": "success",
                "summary": "Actor state fetched via Remote Control",
                "data": {
                    "actor_name": actor_name,
                    "actor_path": actor_path,
                    "class": "/Script/Engine.StaticMeshActor",
                    "target_level": current_level,
                    "transform": transform,
                    "collision": {},
                    "tags": [],
                },
            }
            entry["bounds_response"] = {
                "status": "success",
                "summary": "Actor bounds fetched via Remote Control",
                "data": {
                    "actor_path": actor_path,
                    "world_bounds_origin": bounds_origin,
                    "world_bounds_extent": bounds_extent,
                },
            }
            entry["status"] = "passed"
            entry["actual_actor_name"] = actor_name
            entry["transform"] = transform
            entry["bounds_origin"] = bounds_origin
            entry["bounds_extent"] = bounds_extent
        except Exception as exc:
            entry["status"] = "failed"
            entry["error"] = str(exc)
            entry["bounds_origin"] = []
            entry["bounds_extent"] = []

        actor_presence[actor_name] = entry

    return actor_presence, current_level


def _read_current_level_via_rc() -> str:
    """通过 RC 读取当前 Editor World 路径。"""
    from bridge.remote_control_client import call_function, EDITOR_LEVEL_LIB

    try:
        response = call_function(EDITOR_LEVEL_LIB, "GetEditorWorld", {})
        world_path = response.get("ReturnValue", "")
        return str(world_path) if world_path else ""
    except Exception:
        return ""


def _build_layout_assertions(actor_presence: Dict[str, Any]) -> Dict[str, Any]:
    """根据真实 Actor 位置验证 JRPG 最小布局。"""
    battle_location = _get_actor_location(actor_presence.get("BattleArena", {}))
    hero_location = _get_actor_location(actor_presence.get("HeroUnit_1", {}))
    enemy_location = _get_actor_location(actor_presence.get("EnemyUnit_1", {}))
    command_location = _get_actor_location(actor_presence.get("CommandMenuAnchor", {}))

    checks = {
        "arena_near_origin": {
            "passed": bool(battle_location)
            and abs(battle_location[0]) <= 5.0
            and abs(battle_location[1]) <= 5.0
            and abs(battle_location[2]) <= 5.0,
            "actual_location": battle_location,
        },
        "hero_on_left_side": {
            "passed": bool(hero_location) and bool(battle_location) and hero_location[0] < battle_location[0] - 10.0,
            "actual_location": hero_location,
        },
        "enemy_on_right_side": {
            "passed": bool(enemy_location) and bool(battle_location) and enemy_location[0] > battle_location[0] + 10.0,
            "actual_location": enemy_location,
        },
        "command_menu_below_arena": {
            "passed": bool(command_location)
            and bool(battle_location)
            and command_location[1] < battle_location[1] - 10.0,
            "actual_location": command_location,
        },
        "all_bounds_non_zero": {
            "passed": all(
                _has_non_zero_bounds(actor_presence.get(actor_name, {}))
                for actor_name in _JRPG_MESH_CONFIG.keys()
            ),
            "details": {
                actor_name: actor_presence.get(actor_name, {}).get("bounds_extent", [])
                for actor_name in _JRPG_MESH_CONFIG.keys()
            },
        },
    }
    return {
        "checks": checks,
        "overall_passed": all(item.get("passed", False) for item in checks.values()),
    }


def _build_structure_assertions(
    handoff: Dict[str, Any],
    actor_presence: Dict[str, Any],
    mode: str,
) -> Dict[str, Any]:
    """验证结构级战斗闭环已经进入 handoff/spec tree。"""
    dynamic_spec_tree = handoff.get("dynamic_spec_tree", {})
    scene_actor_names = [
        actor.get("actor_name", "")
        for actor in dynamic_spec_tree.get("scene_spec", {}).get("actors", [])
    ]
    turn_queue = dynamic_spec_tree.get("turn_queue_spec", {}).get("data", {}).get("queue_order", [])
    command_menu = dynamic_spec_tree.get("command_menu_spec", {}).get("data", {}).get("commands", [])
    runtime_wiring = dynamic_spec_tree.get("runtime_wiring_spec", {}).get("data", {})

    checks = {
        "mode_is_greenfield_bootstrap": {
            "passed": mode == "greenfield_bootstrap",
            "actual_mode": mode,
        },
        "turn_queue_spec_present": {
            "passed": "turn_queue_spec" in dynamic_spec_tree,
            "queue_order": turn_queue,
        },
        "command_menu_spec_present": {
            "passed": "command_menu_spec" in dynamic_spec_tree,
            "commands": command_menu,
        },
        "runtime_wiring_spec_present": {
            "passed": "runtime_wiring_spec" in dynamic_spec_tree,
            "runtime_wiring": runtime_wiring,
        },
        "scene_spec_declares_minimal_battle_actors": {
            "passed": scene_actor_names == list(_JRPG_MESH_CONFIG.keys()),
            "scene_actor_names": scene_actor_names,
        },
        "turn_queue_matches_scene": {
            "passed": turn_queue == ["HeroUnit_1", "EnemyUnit_1"],
            "queue_order": turn_queue,
        },
        "command_menu_matches_gdd": {
            "passed": command_menu == ["Attack", "Skill", "Defend"],
            "commands": command_menu,
        },
        "runtime_wiring_points_to_command_menu_anchor": {
            "passed": runtime_wiring.get("command_menu_actor_name", "") == "CommandMenuAnchor",
            "runtime_wiring": runtime_wiring,
        },
        "runtime_scene_matches_declared_actor_count": {
            "passed": sum(
                1 for actor_name in _JRPG_MESH_CONFIG.keys() if actor_presence.get(actor_name, {}).get("status") == "passed"
            ) == len(_JRPG_MESH_CONFIG),
            "runtime_actor_names": [
                actor_name
                for actor_name in _JRPG_MESH_CONFIG.keys()
                if actor_presence.get(actor_name, {}).get("status") == "passed"
            ],
        },
    }
    return {
        "checks": checks,
        "overall_passed": all(item.get("passed", False) for item in checks.values()),
    }


def _write_phase7_smoke_report(
    report_dir: str,
    bridge_mode: str,
    mode: str,
    handoff: Dict[str, Any],
    approved_path: str,
    execution_report_path: str,
    rc_boot_result: Dict[str, Any],
    actor_presence: Dict[str, Any],
    layout_assertions: Dict[str, Any],
    structure_assertions: Dict[str, Any],
    visual_setup: Dict[str, Any],
    current_level: str,
) -> str:
    """写出 Phase 7 JRPG 真机 smoke 结构化报告。"""
    report = {
        "report_type": "phase7_jrpg_runtime_smoke",
        "generated_at": datetime.now().isoformat(),
        "bridge_mode": bridge_mode,
        "mode": mode,
        "handoff_id": handoff.get("handoff_id", ""),
        "approved_handoff_path": approved_path,
        "execution_report_path": execution_report_path,
        "current_level": current_level,
        "rc_endpoint": rc_boot_result.get("rc_endpoint", _RC_ENDPOINT),
        "editor_boot_policy": rc_boot_result.get("editor_boot_policy", "reuse_or_launch"),
        "rc_info_path": rc_boot_result.get("rc_info_path", ""),
        "boot_log_path": rc_boot_result.get("boot_log_path", ""),
        "rc_ready": rc_boot_result.get("status") == "ready",
        "visual_setup": visual_setup,
        "actor_presence": actor_presence,
        "layout_assertions": layout_assertions,
        "structure_assertions": structure_assertions,
        "overall_status": "passed"
        if rc_boot_result.get("status") == "ready"
        and all(entry.get("status") == "passed" for entry in actor_presence.values())
        and layout_assertions.get("overall_passed", False)
        and structure_assertions.get("overall_passed", False)
        and all(entry.get("status") == "passed" for entry in visual_setup.values())
        else "failed",
    }

    output_path = os.path.join(
        report_dir,
        f"phase7_jrpg_runtime_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    return output_path


def _try_capture_phase7_evidence(
    approved_path: str,
    smoke_report: Dict[str, Any],
    report_path: str,
) -> Dict[str, Any]:
    """在真实 UE5 环境中采集 Phase 7 JRPG 截图证据。"""
    if smoke_report.get("overall_status") != "passed":
        return {
            "status": "failed",
            "error": "JRPG smoke 未通过，跳过截图采集",
        }

    try:
        from validation.capture_editor_evidence import capture_editor_scene_evidence

        actor_presence = smoke_report.get("actor_presence", {})
        capture_result = capture_editor_scene_evidence(
            phase_name="Phase7",
            task_id=_PHASE7_EVIDENCE_TASK_ID,
            scenario=_PHASE7_EVIDENCE_SCENARIO,
            actor_names=list(_JRPG_MESH_CONFIG.keys()),
            handoff_path=approved_path,
            report_path=report_path,
            board_center=_get_actor_location(actor_presence.get("BattleArena", {})) or [0.0, 0.0, 0.0],
            rc_info_path=smoke_report.get("rc_info_path", ""),
            custom_view_configs=_build_jrpg_view_configs(actor_presence),
        )
        print(f"  证据说明: {capture_result['note_path']}")
        print(f"  证据日志: {capture_result['log_path']}")
        return capture_result
    except Exception as exc:
        print(f"  [警告] Phase 7 JRPG 截图证据采集失败: {exc}")
        return {
            "status": "failed",
            "error": str(exc),
        }


def _build_jrpg_view_configs(actor_presence: Dict[str, Any]) -> List[Dict[str, Any]]:
    """构建 JRPG smoke 的 6 张证据图视角。"""
    battle_location = _get_actor_location(actor_presence.get("BattleArena", {})) or [0.0, 0.0, 0.0]
    hero_location = _get_actor_location(actor_presence.get("HeroUnit_1", {})) or [-180.0, 0.0, 50.0]
    enemy_location = _get_actor_location(actor_presence.get("EnemyUnit_1", {})) or [180.0, 0.0, 50.0]
    command_location = _get_actor_location(actor_presence.get("CommandMenuAnchor", {})) or [0.0, -260.0, 40.0]

    return [
        _build_view_config(
            "overview_oblique",
            _offset_location(battle_location, -820.0, -620.0, 520.0),
            battle_location,
            disable_dynamic_shadows=False,
            use_unlit_view=False,
        ),
        {
            "view": "topdown_alignment",
            "camera_location": [battle_location[0], battle_location[1], battle_location[2] + 820.0],
            "camera_rotation": [-90.0, 0.0, 0.0],
            "use_game_view": True,
            "disable_dynamic_shadows": True,
            "use_unlit_view": True,
        },
        _build_view_config(
            "actor_battlearena_closeup",
            _offset_location(battle_location, -420.0, -320.0, 260.0),
            battle_location,
        ),
        _build_view_config(
            "actor_herounit_1_closeup",
            _offset_location(hero_location, -220.0, -160.0, 180.0),
            hero_location,
        ),
        _build_view_config(
            "actor_enemyunit_1_closeup",
            _offset_location(enemy_location, 220.0, 160.0, 180.0),
            enemy_location,
        ),
        _build_view_config(
            "actor_commandmenuanchor_closeup",
            _offset_location(command_location, -220.0, -220.0, 140.0),
            command_location,
        ),
    ]


def _build_view_config(
    view_name: str,
    camera_location: List[float],
    target_location: List[float],
    disable_dynamic_shadows: bool = False,
    use_unlit_view: bool = False,
) -> Dict[str, Any]:
    """构建一个带朝向的视角配置。"""
    return {
        "view": view_name,
        "camera_location": camera_location,
        "camera_rotation": _build_look_at_rotation(camera_location, target_location),
        "use_game_view": True,
        "disable_dynamic_shadows": disable_dynamic_shadows,
        "use_unlit_view": use_unlit_view,
    }


def _build_look_at_rotation(camera_location: List[float], target_location: List[float]) -> List[float]:
    """把相机朝向目标位置，避免 closeup 截图偏离。"""
    delta_x = target_location[0] - camera_location[0]
    delta_y = target_location[1] - camera_location[1]
    delta_z = target_location[2] - camera_location[2]
    horizontal_distance = math.sqrt(delta_x * delta_x + delta_y * delta_y)

    yaw = math.degrees(math.atan2(delta_y, delta_x))
    pitch = math.degrees(math.atan2(delta_z, horizontal_distance if horizontal_distance > 1e-6 else 1e-6))
    return [pitch, yaw, 0.0]


def _offset_location(base_location: List[float], offset_x: float, offset_y: float, offset_z: float) -> List[float]:
    """对给定坐标加偏移。"""
    return [
        float(base_location[0]) + offset_x,
        float(base_location[1]) + offset_y,
        float(base_location[2]) + offset_z,
    ]


def _write_phase7_acceptance_report(
    bridge_mode: str,
    smoke_report_path: str,
    evidence_result: Dict[str, Any],
    report_dir: str,
) -> str:
    """收敛 E2E-35 的最终验收结论。"""
    smoke_report = _load_json_file(smoke_report_path)
    actor_presence = smoke_report.get("actor_presence", {})

    captured_items = evidence_result.get("captured_items", []) if isinstance(evidence_result, dict) else []
    screenshot_by_view = {
        item.get("view", ""): item.get("evidence_path", "")
        for item in captured_items
        if isinstance(item, dict)
    }
    required_views = [
        "overview_oblique",
        "topdown_alignment",
        "actor_battlearena_closeup",
        "actor_herounit_1_closeup",
        "actor_enemyunit_1_closeup",
        "actor_commandmenuanchor_closeup",
    ]
    evidence_files = [screenshot_by_view.get(view, "") for view in required_views]
    note_path = evidence_result.get("note_path", "") if isinstance(evidence_result, dict) else ""
    log_path = evidence_result.get("log_path", "") if isinstance(evidence_result, dict) else ""

    checks = {
        "E2E-35": {
            "name": "JRPG 真实 UE5 smoke 成功并产出完整证据链",
            "status": "passed"
            if (
                bridge_mode == "bridge_rc_api"
                and smoke_report.get("rc_ready") is True
                and smoke_report.get("overall_status") == "passed"
                and all(actor_presence.get(actor_name, {}).get("status") == "passed" for actor_name in _JRPG_MESH_CONFIG)
                and smoke_report.get("layout_assertions", {}).get("overall_passed") is True
                and smoke_report.get("structure_assertions", {}).get("overall_passed") is True
                and _all_paths_exist([note_path, log_path, *evidence_files])
            )
            else "failed",
            "details": {
                "bridge_mode": bridge_mode,
                "rc_ready": smoke_report.get("rc_ready", False),
                "smoke_report_path": smoke_report_path,
                "layout_assertions": smoke_report.get("layout_assertions", {}),
                "structure_assertions": smoke_report.get("structure_assertions", {}),
                "actor_presence": actor_presence,
                "note_path": note_path,
                "log_path": log_path,
                "screenshots": screenshot_by_view,
            },
        }
    }

    report = {
        "report_type": "phase7_jrpg_runtime_acceptance",
        "generated_at": datetime.now().isoformat(),
        "bridge_mode": bridge_mode,
        "overall_status": "passed" if checks["E2E-35"]["status"] == "passed" else "failed",
        "checks": checks,
    }

    output_path = os.path.join(
        report_dir,
        f"phase7_jrpg_runtime_acceptance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    return output_path


def _get_actor_location(actor_entry: Dict[str, Any]) -> List[float]:
    """从 actor_presence 条目里提取位置。"""
    transform = actor_entry.get("transform", {})
    location = transform.get("location", [])
    if isinstance(location, list) and len(location) == 3:
        return [float(location[0]), float(location[1]), float(location[2])]
    return []


def _has_non_zero_bounds(actor_entry: Dict[str, Any]) -> bool:
    """检查 bounds 是否已经读回到有效几何体。"""
    bounds_extent = actor_entry.get("bounds_extent", [])
    if not isinstance(bounds_extent, list) or len(bounds_extent) != 3:
        return False
    return any(abs(float(value)) > 1e-3 for value in bounds_extent)


def _all_paths_exist(paths: List[str]) -> bool:
    """检查一组证据文件是否全部存在。"""
    return all(path and os.path.exists(path) for path in paths)


def _load_json_file(file_path: str) -> Dict[str, Any]:
    """安全读取 JSON 文件。"""
    if not file_path or not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


if __name__ == "__main__":
    selected_bridge_mode = "simulated"
    selected_mode = "greenfield_bootstrap"
    if len(sys.argv) > 1:
        selected_bridge_mode = sys.argv[1]
    if len(sys.argv) > 2:
        selected_mode = sys.argv[2]

    result = run_jrpg_turn_based_demo(bridge_mode=selected_bridge_mode, mode=selected_mode)
    sys.exit(0 if result.get("status") == "succeeded" else 1)
