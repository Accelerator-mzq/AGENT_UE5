"""
Phase 5 证据采集脚本
负责把 UE5 运行截图与说明写入 ProjectState/Evidence/Phase5/。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLUGIN_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "Plugins", "AgentBridge", "Scripts")
if PLUGIN_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_SCRIPTS_DIR)

from bridge.remote_control_client import call_function


_AGENT_BRIDGE_SUBSYSTEM = "/Script/AgentBridge.Default__AgentBridgeSubsystem"
_AUTOMATION_BP_LIBRARY = "/Script/FunctionalTesting.Default__AutomationBlueprintFunctionLibrary"
_HIGH_RES_SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "Saved", "Screenshots", "WindowsEditor")
_DEFAULT_SCREENSHOT_RESOLUTION: Tuple[int, int] = (1280, 720)
_AUTOMATION_TASK_TIMEOUT_SECONDS = 45.0
_SCREENSHOT_READY_TIMEOUT_SECONDS = 20.0
_WORKFLOW_DOC_REF = os.path.join(
    PROJECT_ROOT,
    "Plugins",
    "AgentBridge",
    "Docs",
    "editor_screenshot_evidence_workflow.md",
)


def get_phase5_evidence_root(project_root: Optional[str] = None) -> str:
    """返回 Phase 5 当前证据工作目录。"""
    resolved_project_root = project_root or PROJECT_ROOT
    return os.path.join(resolved_project_root, "ProjectState", "Evidence", "Phase5")


def ensure_phase5_evidence_dirs(project_root: Optional[str] = None) -> Dict[str, str]:
    """确保证据目录存在。"""
    evidence_root = get_phase5_evidence_root(project_root)
    directories = {
        "root": evidence_root,
        "screenshots": os.path.join(evidence_root, "screenshots"),
        "logs": os.path.join(evidence_root, "logs"),
        "notes": os.path.join(evidence_root, "notes"),
    }
    for directory in directories.values():
        os.makedirs(directory, exist_ok=True)
    return directories


def capture_phase5_scene_evidence(
    task_id: str,
    scenario: str,
    actor_names: List[str],
    handoff_path: str,
    report_path: str,
    board_center: Optional[List[float]] = None,
    rc_info_path: Optional[str] = None,
    screenshot_resolution: Tuple[int, int] = _DEFAULT_SCREENSHOT_RESOLUTION,
) -> Dict[str, Any]:
    """
    采集 Phase 5 场景证据。

    当前固定采集两张图：
    - overview_oblique：3/4 俯视总览
    - topdown_alignment：近似顶视图
    """
    directories = ensure_phase5_evidence_dirs()
    resolved_board_center = board_center or [0.0, 0.0, 0.0]
    resolved_rc_info_path = rc_info_path or find_latest_phase5_rc_info_report()
    current_level = _get_current_level_path()
    captured_items: List[Dict[str, Any]] = []

    for view_config in _build_view_configs(resolved_board_center):
        captured_items.append(
            _capture_single_view(
                directories=directories,
                current_level=current_level,
                task_id=task_id,
                scenario=scenario,
                view=view_config["view"],
                camera_location=view_config["camera_location"],
                camera_rotation=view_config["camera_rotation"],
                screenshot_resolution=screenshot_resolution,
            )
        )

    note_path = write_phase5_evidence_note(
        task_id=task_id,
        scenario=scenario,
        handoff_path=handoff_path,
        report_path=report_path,
        actor_names=actor_names,
        captured_items=captured_items,
        directories=directories,
        current_level=current_level,
        rc_info_path=resolved_rc_info_path,
    )

    result = {
        "status": "success",
        "generated_at": datetime.now().isoformat(),
        "phase": "Phase5",
        "workflow_ref": _WORKFLOW_DOC_REF,
        "current_level": current_level,
        "handoff_path": handoff_path,
        "report_path": report_path,
        "rc_info_path": resolved_rc_info_path or "",
        "captured_items": captured_items,
        "note_path": note_path,
    }
    log_path = os.path.join(directories["logs"], f"phase5_{task_id}_{scenario}_capture.json")
    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    result["log_path"] = log_path
    return result


def find_latest_phase5_rc_info_report(project_root: Optional[str] = None) -> str:
    """查找最新的 Phase 5 RC 启动信息文件。"""
    resolved_project_root = project_root or PROJECT_ROOT
    report_dir = os.path.join(resolved_project_root, "ProjectState", "Reports")
    if not os.path.isdir(report_dir):
        return ""

    candidates = []
    for file_name in os.listdir(report_dir):
        if file_name.startswith("phase5_rc_info") and file_name.endswith(".json"):
            candidates.append(os.path.join(report_dir, file_name))

    if not candidates:
        return ""
    return max(candidates, key=os.path.getmtime)


def write_phase5_evidence_note(
    task_id: str,
    scenario: str,
    handoff_path: str,
    report_path: str,
    actor_names: List[str],
    captured_items: List[Dict[str, Any]],
    directories: Optional[Dict[str, str]] = None,
    current_level: str = "",
    rc_info_path: str = "",
) -> str:
    """写入本次截图证据的说明文档。"""
    directories = directories or ensure_phase5_evidence_dirs()
    note_path = os.path.join(directories["notes"], f"phase5_{task_id}_{scenario}_evidence.md")
    lines = [
        f"# Phase 5 证据说明：{task_id} / {scenario}",
        "",
        f"- 生成时间：{datetime.now().isoformat()}",
        f"- 工作流文档：{_WORKFLOW_DOC_REF}",
        f"- 当前关卡：{current_level}",
        f"- RC 启动信息：{rc_info_path or '未提供'}",
        f"- Handoff：{handoff_path}",
        f"- Report：{report_path}",
        f"- 画面中应可见的 Actor：{', '.join(actor_names)}",
        "",
        "## 截图清单",
    ]
    for item in captured_items:
        lines.extend(
            [
                f"- 视图：{item['view']}",
                f"- 目标文件：{item['evidence_path']}",
                f"- 原始输出：{item['source_output_path']}",
                f"- 截图后端：{item.get('capture_backend', '')}",
                f"- CameraActor：{item.get('camera_actor_path', '')}",
                f"- 截图任务：{item.get('task_object_path', '')}",
                f"- 相机位置：{item['camera_location']}",
                f"- 相机旋转：{item['camera_rotation']}",
                f"- 文件大小：{item.get('evidence_file_size', 0)}",
                f"- SHA256：{item.get('evidence_sha256', '')}",
                "",
            ]
        )

    with open(note_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

    return note_path


def _build_view_configs(board_center: Sequence[float]) -> List[Dict[str, Any]]:
    """生成固定视角配置。"""
    return [
        {
            "view": "overview_oblique",
            "camera_location": [
                float(board_center[0]) - 650.0,
                float(board_center[1]) - 650.0,
                float(board_center[2]) + 450.0,
            ],
            "camera_rotation": [-25.0, 45.0, 0.0],
        },
        {
            "view": "topdown_alignment",
            "camera_location": [
                float(board_center[0]),
                float(board_center[1]),
                float(board_center[2]) + 1400.0,
            ],
            "camera_rotation": [-90.0, 0.0, 0.0],
        },
    ]


def _capture_single_view(
    directories: Dict[str, str],
    current_level: str,
    task_id: str,
    scenario: str,
    view: str,
    camera_location: List[float],
    camera_rotation: List[float],
    screenshot_resolution: Tuple[int, int],
) -> Dict[str, Any]:
    """通过 CameraActor + HighResScreenshot 采集一张固定角度截图。"""
    screenshot_name = f"phase5_{task_id}_{scenario}_{view}"
    capture_result = _capture_high_res_screenshot_with_camera(
        screenshot_name=screenshot_name,
        current_level=current_level,
        camera_location=camera_location,
        camera_rotation=camera_rotation,
        screenshot_resolution=screenshot_resolution,
    )
    source_output_path = capture_result["source_output_path"]

    evidence_path = os.path.join(directories["screenshots"], f"{screenshot_name}.png")
    if not os.path.exists(source_output_path):
        raise RuntimeError(f"截图原始文件不存在，无法复制到证据目录：{source_output_path}")
    shutil.copy2(source_output_path, evidence_path)

    evidence_file_size = os.path.getsize(evidence_path)
    evidence_sha256 = _calculate_file_sha256(evidence_path)
    return {
        "view": view,
        "camera_location": camera_location,
        "camera_rotation": camera_rotation,
        "camera_actor_path": capture_result["camera_actor_path"],
        "capture_backend": capture_result["capture_backend"],
        "task_object_path": capture_result["task_object_path"],
        "source_output_path": source_output_path,
        "evidence_path": evidence_path,
        "evidence_file_size": evidence_file_size,
        "evidence_sha256": evidence_sha256,
    }


def _capture_high_res_screenshot_with_camera(
    screenshot_name: str,
    current_level: str,
    camera_location: List[float],
    camera_rotation: List[float],
    screenshot_resolution: Tuple[int, int],
) -> Dict[str, str]:
    """
    使用临时 CameraActor + AutomationBlueprintFunctionLibrary 采集高分截图。

    这样可以绕开“视口相机”和“截图视口”不同步的问题。
    """
    capture_started_at = time.time()
    camera_actor_path = _spawn_temporary_camera_actor(
        level_path=current_level,
        actor_name=f"{screenshot_name}_ShotCam_{uuid.uuid4().hex[:8]}",
        camera_location=camera_location,
        camera_rotation=camera_rotation,
    )
    task_object_path = _start_high_res_screenshot_task(
        screenshot_name=screenshot_name,
        camera_actor_path=camera_actor_path,
        screenshot_resolution=screenshot_resolution,
    )
    _wait_for_automation_editor_task(task_object_path)
    output_path = _wait_for_high_res_screenshot(screenshot_name, capture_started_at)
    return {
        "camera_actor_path": camera_actor_path,
        "capture_backend": "AutomationBlueprintFunctionLibrary.TakeHighResScreenshot",
        "task_object_path": task_object_path,
        "source_output_path": output_path,
    }


def _get_current_level_path() -> str:
    """读取当前编辑器关卡路径。"""
    response = call_function(_AGENT_BRIDGE_SUBSYSTEM, "GetCurrentProjectState", {})
    normalized = _normalize_cpp_response(response)
    current_level = normalized.get("data", {}).get("current_level", "")
    if not current_level:
        raise RuntimeError("无法读取当前关卡路径，不能生成 Phase 5 截图证据。")
    return current_level


def _spawn_temporary_camera_actor(
    level_path: str,
    actor_name: str,
    camera_location: List[float],
    camera_rotation: List[float],
) -> str:
    """生成一个仅用于取证的 CameraActor。"""
    response = call_function(
        _AGENT_BRIDGE_SUBSYSTEM,
        "SpawnActor",
        {
            "LevelPath": level_path,
            "ActorClass": "/Script/Engine.CameraActor",
            "ActorName": actor_name,
            "Transform": {
                "Location": {
                    "X": camera_location[0],
                    "Y": camera_location[1],
                    "Z": camera_location[2],
                },
                "Rotation": {
                    "Pitch": camera_rotation[0],
                    "Yaw": camera_rotation[1],
                    "Roll": camera_rotation[2],
                },
                "RelativeScale3D": {"X": 1.0, "Y": 1.0, "Z": 1.0},
            },
            "bDryRun": False,
        },
    )
    normalized = _normalize_cpp_response(response)
    created_objects = normalized.get("data", {}).get("created_objects", [])
    if not created_objects:
        raise RuntimeError("CameraActor 生成失败，无法继续截图取证。")

    camera_actor_path = created_objects[0].get("actor_path", "")
    if not camera_actor_path:
        raise RuntimeError("CameraActor 已创建，但返回结果缺少 actor_path。")
    return camera_actor_path


def _start_high_res_screenshot_task(
    screenshot_name: str,
    camera_actor_path: str,
    screenshot_resolution: Tuple[int, int],
) -> str:
    """启动高分截图任务并返回 AutomationEditorTask 对象路径。"""
    response = call_function(
        _AUTOMATION_BP_LIBRARY,
        "TakeHighResScreenshot",
        {
            "ResX": screenshot_resolution[0],
            "ResY": screenshot_resolution[1],
            "Filename": screenshot_name,
            "Camera": {"objectPath": camera_actor_path},
            "Delay": 0.2,
            "bForceGameView": True,
        },
    )
    task_object_path = response.get("ReturnValue", "")
    if not isinstance(task_object_path, str) or not task_object_path:
        raise RuntimeError(f"高分截图任务未返回 AutomationEditorTask 路径：{response}")
    return task_object_path


def _wait_for_automation_editor_task(task_object_path: str) -> None:
    """轮询 AutomationEditorTask，直到任务完成。"""
    deadline = time.time() + _AUTOMATION_TASK_TIMEOUT_SECONDS
    last_state: Dict[str, Any] = {}
    last_error: Optional[Exception] = None

    while time.time() < deadline:
        try:
            valid_response = call_function(task_object_path, "IsValidTask", {})
            done_response = call_function(task_object_path, "IsTaskDone", {})
            last_state = {
                "valid": bool(valid_response.get("ReturnValue", False)),
                "done": bool(done_response.get("ReturnValue", False)),
            }
            if last_state["valid"] and last_state["done"]:
                return
        except Exception as exc:
            # 某些任务对象在接近完成时可能被引擎清理；先记住异常，继续等待落盘。
            last_error = exc

        time.sleep(0.5)

    if last_error is not None:
        raise RuntimeError(f"高分截图任务超时且轮询异常：{task_object_path} / {last_error}") from last_error
    raise RuntimeError(f"高分截图任务超时：{task_object_path} / {last_state}")


def _wait_for_high_res_screenshot(screenshot_name: str, capture_started_at: float) -> str:
    """等待高分截图文件实际落盘，并确保不是旧文件。"""
    deadline = time.time() + _SCREENSHOT_READY_TIMEOUT_SECONDS
    expected_path = os.path.join(_HIGH_RES_SCREENSHOT_DIR, f"{screenshot_name}.png")

    while time.time() < deadline:
        candidate = _find_recent_screenshot_file(screenshot_name, capture_started_at, expected_path)
        if candidate:
            return candidate
        time.sleep(0.25)

    raise RuntimeError(f"高分截图未按时落盘：{expected_path}")


def _find_recent_screenshot_file(
    screenshot_name: str,
    capture_started_at: float,
    expected_path: str,
) -> str:
    """查找本次截图任务生成的最新文件。"""
    if os.path.exists(expected_path) and os.path.getmtime(expected_path) >= capture_started_at - 0.01:
        return expected_path

    saved_screenshot_root = os.path.join(PROJECT_ROOT, "Saved", "Screenshots")
    if not os.path.isdir(saved_screenshot_root):
        return ""

    target_file_name = f"{screenshot_name}.png"
    latest_match = ""
    latest_mtime = 0.0
    for root, _, files in os.walk(saved_screenshot_root):
        for file_name in files:
            if file_name != target_file_name:
                continue
            candidate_path = os.path.join(root, file_name)
            candidate_mtime = os.path.getmtime(candidate_path)
            if candidate_mtime >= capture_started_at - 0.01 and candidate_mtime >= latest_mtime:
                latest_match = candidate_path
                latest_mtime = candidate_mtime

    return latest_match


def _calculate_file_sha256(file_path: str) -> str:
    """计算文件 SHA256，作为证据指纹。"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(1024 * 1024)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def _normalize_cpp_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """统一 C++ 插件经 RC API 返回的结构。"""
    if "ReturnValue" in response and isinstance(response["ReturnValue"], dict):
        response = response["ReturnValue"]

    data = response.get("data")
    if isinstance(data, dict) and isinstance(data.get("JsonString"), str):
        try:
            response = dict(response)
            response["data"] = json.loads(data["JsonString"])
        except Exception:
            pass

    return response


def _parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="采集 Phase 5 的 UE5 Editor 截图证据。")
    parser.add_argument("--task-id", required=True, help="任务标识，例如 task_phase5_brownfield_demo")
    parser.add_argument("--scenario", required=True, help="场景标识，例如 append_piece_o")
    parser.add_argument("--handoff-path", required=True, help="对应的 approved handoff 路径")
    parser.add_argument("--report-path", required=True, help="对应的执行报告路径")
    parser.add_argument("--rc-info-path", default="", help="RC 启动信息路径，可为空")
    parser.add_argument(
        "--actors",
        nargs="+",
        required=True,
        help="画面中应可见的 Actor 名称列表，例如 Board PieceX_1 PieceO_1",
    )
    parser.add_argument(
        "--board-center",
        nargs=3,
        type=float,
        default=[0.0, 0.0, 0.0],
        metavar=("X", "Y", "Z"),
        help="棋盘中心位置，默认 0 0 0",
    )
    parser.add_argument("--res-x", type=int, default=_DEFAULT_SCREENSHOT_RESOLUTION[0], help="截图宽度")
    parser.add_argument("--res-y", type=int, default=_DEFAULT_SCREENSHOT_RESOLUTION[1], help="截图高度")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = _parse_args()
    result = capture_phase5_scene_evidence(
        task_id=arguments.task_id,
        scenario=arguments.scenario,
        actor_names=list(arguments.actors),
        handoff_path=arguments.handoff_path,
        report_path=arguments.report_path,
        board_center=list(arguments.board_center),
        rc_info_path=arguments.rc_info_path or None,
        screenshot_resolution=(arguments.res_x, arguments.res_y),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
