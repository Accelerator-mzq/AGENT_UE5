"""
端到端运行脚本
Brownfield + Boardgame + Reviewed Delta Handoff 最小闭环。
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "Plugins", "AgentBridge", "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from compiler.handoff import build_handoff, serialize_handoff
from compiler.intake import read_gdd_from_directory
from bridge.project_config import get_dated_project_reports_dir, iter_report_files
from orchestrator.handoff_runner import run_from_handoff


def run_brownfield_demo(
    bridge_mode: str = "simulated",
    capture_evidence: bool = True,
) -> Dict[str, Any]:
    """
    运行 Brownfield append/new-actor 最小闭环。

    模板约束：
    - baseline 已有 Board + PieceX_1
    - 目标设计要求 Board + PieceX_1 + PieceO_1
    - delta tree 只应生成 PieceO_1
    """
    gdd_dir = os.path.join(PROJECT_ROOT, "ProjectInputs", "GDD")
    handoff_draft_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Handoffs", "draft")
    handoff_approved_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Handoffs", "approved")
    report_dir = str(get_dated_project_reports_dir())

    for directory in [handoff_draft_dir, handoff_approved_dir, report_dir]:
        os.makedirs(directory, exist_ok=True)

    print("=" * 60)
    print("Brownfield + Boardgame + Delta Handoff 最小闭环")
    print("=" * 60)

    design_input = read_gdd_from_directory(gdd_dir)
    project_state = _build_demo_project_state()

    print("\n[1/4] 使用 Brownfield 模板 baseline...")
    print(f"  当前关卡: {project_state['current_level']}")
    print(f"  当前 Actor: {[actor['actor_name'] for actor in project_state['actors']]}")

    print("\n[2/4] 构建 Brownfield Handoff...")
    handoff = build_handoff(
        design_input=design_input,
        mode="brownfield_expansion",
        project_state=project_state,
    )
    print(f"  Handoff ID: {handoff['handoff_id']}")
    print(f"  Handoff 状态: {handoff['status']}")
    print(f"  Delta Intent: {handoff.get('delta_context', {}).get('delta_intent', '')}")
    print(f"  Delta Actors: {[actor['actor_name'] for actor in handoff['dynamic_spec_tree']['scene_spec']['actors']]}")

    draft_path = serialize_handoff(handoff, handoff_draft_dir, "yaml")
    print(f"  Draft: {draft_path}")

    if handoff.get("status") == "blocked":
        raise RuntimeError("Brownfield Handoff 被 review 阻断，无法进入执行阶段。")

    print("\n[3/4] 自动审批到 approved_for_execution...")
    approved_handoff = dict(handoff)
    approved_handoff["status"] = "approved_for_execution"
    approved_path = serialize_handoff(approved_handoff, handoff_approved_dir, "yaml")
    print(f"  Approved: {approved_path}")

    print("\n[4/4] 执行 Handoff...")
    result = run_from_handoff(
        approved_path,
        report_output_dir=report_dir,
        bridge_mode=bridge_mode,
    )
    print(f"  执行状态: {result['status']}")

    # Phase 6 统一把真实截图证据收敛到 capture_editor_evidence。
    if capture_evidence and bridge_mode == "bridge_rc_api" and result.get("status") == "succeeded":
        _try_capture_evidence(
            approved_path=approved_path,
            report_dir=report_dir,
            handoff=handoff,
            design_input=design_input,
        )

    return result


def _build_demo_project_state() -> Dict[str, Any]:
    """构造 Brownfield append-only 模板的 baseline 项目状态。"""
    actors = [
        {
            "actor_name": "Board",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.Board",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [3.0, 3.0, 0.1],
            },
            "tags": ["Baseline"],
        },
        {
            "actor_name": "PieceX_1",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.PieceX_1",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [-100.0, -100.0, 50.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [0.5, 0.5, 0.5],
            },
            "tags": ["Baseline", "PreviewPiece"],
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
        "metadata": {
            "source": "synthetic_brownfield_demo",
        },
        "current_project_state_digest": "synthetic-brownfield-demo",
        "dirty_assets": [],
        "map_check_summary": {"map_errors": [], "map_warnings": []},
    }


def _try_capture_evidence(
    approved_path: str,
    report_dir: str,
    handoff: Dict[str, Any],
    design_input: Dict[str, Any],
) -> None:
    """在真实 UE5 环境里采集 Phase 6 统一截图证据。"""
    try:
        from validation.capture_editor_evidence import capture_editor_scene_evidence

        latest_report = _find_latest_report(report_dir, handoff["handoff_id"])
        capture_result = capture_editor_scene_evidence(
            phase_name="Phase6",
            task_id="task_phase6_brownfield_demo",
            scenario="append_piece_o",
            actor_names=["Board", "PieceX_1", "PieceO_1"],
            handoff_path=approved_path,
            report_path=latest_report,
            board_center=list(design_input.get("board", {}).get("location", [0.0, 0.0, 0.0])),
        )
        print(f"  证据说明: {capture_result['note_path']}")
        print(f"  证据日志: {capture_result['log_path']}")
    except Exception as exc:
        print(f"  [警告] 截图证据采集失败: {exc}")


def _find_latest_report(report_dir: str, handoff_id: str) -> str:
    """找到当前 handoff 对应的最新执行报告。"""
    candidates = []
    for report_path in iter_report_files(report_dir):
        if handoff_id in report_path.name and report_path.suffix == ".json":
            candidates.append(str(report_path))
    if not candidates:
        return ""
    return max(candidates, key=os.path.getmtime)


if __name__ == "__main__":
    selected_mode = "simulated"
    if len(sys.argv) > 1:
        selected_mode = sys.argv[1]

    result = run_brownfield_demo(bridge_mode=selected_mode)
    sys.exit(0 if result.get("status") == "succeeded" else 1)
