"""
UE5 Editor 截图证据采集脚本
负责把运行截图与说明写入 ProjectState/Evidence/<Phase>/。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PLUGIN_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "Plugins", "AgentBridge", "Scripts")
if PLUGIN_SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, PLUGIN_SCRIPTS_DIR)

from bridge.remote_control_client import call_function


_AGENT_BRIDGE_SUBSYSTEM = "/Script/AgentBridge.Default__AgentBridgeSubsystem"
_DEFAULT_SCREENSHOT_RESOLUTION: Tuple[int, int] = (1280, 720)
_WORKFLOW_DOC_REF = os.path.join(
    PROJECT_ROOT,
    "Plugins",
    "AgentBridge",
    "Docs",
    "editor_screenshot_evidence_workflow.md",
)


def get_evidence_root(phase_name: str, project_root: Optional[str] = None) -> str:
    """返回当前阶段的证据工作目录。"""
    resolved_project_root = project_root or PROJECT_ROOT
    return os.path.join(resolved_project_root, "ProjectState", "Evidence", phase_name)


def ensure_evidence_dirs(phase_name: str, project_root: Optional[str] = None) -> Dict[str, str]:
    """确保当前阶段证据目录存在。"""
    evidence_root = get_evidence_root(phase_name, project_root)
    directories = {
        "root": evidence_root,
        "screenshots": os.path.join(evidence_root, "screenshots"),
        "logs": os.path.join(evidence_root, "logs"),
        "notes": os.path.join(evidence_root, "notes"),
    }
    for directory in directories.values():
        os.makedirs(directory, exist_ok=True)
    return directories


def capture_editor_scene_evidence(
    phase_name: str,
    task_id: str,
    scenario: str,
    actor_names: List[str],
    handoff_path: str,
    report_path: str,
    board_center: Optional[List[float]] = None,
    rc_info_path: Optional[str] = None,
    screenshot_resolution: Tuple[int, int] = _DEFAULT_SCREENSHOT_RESOLUTION,
) -> Dict[str, Any]:
    """采集当前阶段固定两视角截图。"""
    directories = ensure_evidence_dirs(phase_name)
    resolved_board_center = board_center or [0.0, 0.0, 0.0]
    current_level = _get_current_level_path()
    captured_items: List[Dict[str, Any]] = []

    for view_config in _build_view_configs(resolved_board_center):
        captured_items.append(
            _capture_single_view(
                phase_name=phase_name,
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

    note_path = write_evidence_note(
        phase_name=phase_name,
        task_id=task_id,
        scenario=scenario,
        handoff_path=handoff_path,
        report_path=report_path,
        actor_names=actor_names,
        captured_items=captured_items,
        directories=directories,
        current_level=current_level,
        rc_info_path=rc_info_path or "",
    )

    result = {
        "status": "success",
        "generated_at": datetime.now().isoformat(),
        "phase": phase_name,
        "workflow_ref": _WORKFLOW_DOC_REF,
        "current_level": current_level,
        "handoff_path": handoff_path,
        "report_path": report_path,
        "rc_info_path": rc_info_path or "",
        "captured_items": captured_items,
        "note_path": note_path,
    }
    phase_prefix = phase_name.lower()
    log_path = os.path.join(directories["logs"], f"{phase_prefix}_{task_id}_{scenario}_capture.json")
    with open(log_path, "w", encoding="utf-8") as file:
        json.dump(result, file, indent=2, ensure_ascii=False)

    result["log_path"] = log_path
    return result


def write_evidence_note(
    phase_name: str,
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
    """写入截图证据说明。"""
    directories = directories or ensure_evidence_dirs(phase_name)
    phase_prefix = phase_name.lower()
    note_path = os.path.join(directories["notes"], f"{phase_prefix}_{task_id}_{scenario}_evidence.md")
    lines = [
        f"# {phase_name} 证据说明：{task_id} / {scenario}",
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
    """生成固定视角。"""
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
                # 棋类顶视图优先让棋盘占据画面主体，保留少量边缘余量即可。
                float(board_center[2]) + 340.0,
            ],
            "camera_rotation": [-90.0, 0.0, 0.0],
        },
    ]


def _capture_single_view(
    phase_name: str,
    directories: Dict[str, str],
    current_level: str,
    task_id: str,
    scenario: str,
    view: str,
    camera_location: List[float],
    camera_rotation: List[float],
    screenshot_resolution: Tuple[int, int],
) -> Dict[str, Any]:
    """通过编辑器活动视口采集单张截图。"""
    screenshot_name = f"{phase_name.lower()}_{task_id}_{scenario}_{view}"
    capture_result = _capture_high_res_screenshot_from_viewport(
        screenshot_name=screenshot_name,
        camera_location=camera_location,
        camera_rotation=camera_rotation,
        screenshot_resolution=screenshot_resolution,
        view=view,
    )
    source_output_path = capture_result["source_output_path"]

    evidence_path = os.path.join(directories["screenshots"], f"{screenshot_name}.png")
    shutil.copy2(source_output_path, evidence_path)
    return {
        "view": view,
        "camera_location": camera_location,
        "camera_rotation": camera_rotation,
        "camera_actor_path": capture_result.get("camera_actor_path", ""),
        "capture_backend": capture_result["capture_backend"],
        "task_object_path": capture_result["task_object_path"],
        "source_output_path": source_output_path,
        "evidence_path": evidence_path,
        "evidence_file_size": os.path.getsize(evidence_path),
        "evidence_sha256": _calculate_file_sha256(evidence_path),
    }


def _capture_high_res_screenshot_from_viewport(
    screenshot_name: str,
    camera_location: List[float],
    camera_rotation: List[float],
    screenshot_resolution: Tuple[int, int],
    view: str,
) -> Dict[str, str]:
    """调用项目内专用关卡视口截图接口。

    该接口在同一个同步调用里完成：
    - 设置目标机位
    - 可选关闭动态阴影
    - 读取关卡视口像素
    - 恢复视口状态
    """
    response = call_function(
        _AGENT_BRIDGE_SUBSYSTEM,
        "CaptureLevelViewportScreenshot",
        {
            "ScreenshotName": screenshot_name,
            "CameraLocation": {"X": camera_location[0], "Y": camera_location[1], "Z": camera_location[2]},
            "CameraRotation": {"Pitch": camera_rotation[0], "Yaw": camera_rotation[1], "Roll": camera_rotation[2]},
            "bUseGameView": True,
            "bDisableDynamicShadows": view == "topdown_alignment",
            "bUseUnlitView": view == "topdown_alignment",
        },
    )
    normalized = _normalize_cpp_response(response)
    if normalized.get("status") not in ("success", "warning"):
        raise RuntimeError(f"关卡视口截图失败：{response}")
    data = normalized.get("data", {})
    output_path = data.get("output_path", "")
    if not isinstance(output_path, str) or not output_path or not os.path.exists(output_path):
        raise RuntimeError(f"关卡视口截图未返回有效输出路径：{response}")
    return {
        "camera_actor_path": "（活动视口机位）",
        "capture_backend": "AgentBridgeSubsystem.CaptureLevelViewportScreenshot",
        "task_object_path": "（同步视口截图）",
        "source_output_path": output_path,
    }


def _get_current_level_path() -> str:
    """读取当前关卡。"""
    response = call_function(_AGENT_BRIDGE_SUBSYSTEM, "GetCurrentProjectState", {})
    normalized = _normalize_cpp_response(response)
    current_level = normalized.get("data", {}).get("current_level", "")
    if not current_level:
        raise RuntimeError("无法读取当前关卡路径，不能生成截图证据。")
    return current_level


def _calculate_file_sha256(file_path: str) -> str:
    """计算截图文件的 SHA256。"""
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
    parser = argparse.ArgumentParser(description="采集当前阶段的 UE5 Editor 截图证据。")
    parser.add_argument("--phase", required=True, help="阶段名，例如 Phase6")
    parser.add_argument("--task-id", required=True, help="任务标识")
    parser.add_argument("--scenario", required=True, help="场景标识")
    parser.add_argument("--handoff-path", required=True, help="对应的 approved handoff 路径")
    parser.add_argument("--report-path", required=True, help="对应的执行报告路径")
    parser.add_argument("--rc-info-path", default="", help="RC 启动信息路径，可为空")
    parser.add_argument("--actors", nargs="+", required=True, help="应入镜的 Actor 名称列表")
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
    result = capture_editor_scene_evidence(
        phase_name=arguments.phase,
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
