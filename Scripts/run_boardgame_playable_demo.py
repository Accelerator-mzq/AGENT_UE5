"""
端到端运行脚本
Phase 6：boardgame GDD -> 完整 Spec Tree -> playable runtime。
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "Plugins", "AgentBridge", "Scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from compiler.handoff import build_handoff, serialize_handoff
from compiler.intake import get_project_state_snapshot, read_gdd_from_directory
from orchestrator.handoff_runner import run_from_handoff


def run_boardgame_playable_demo(
    bridge_mode: str = "simulated",
    capture_evidence: bool = True,
) -> Dict[str, Any]:
    """运行 Phase 6 playable runtime 最小闭环。"""
    gdd_dir = os.path.join(PROJECT_ROOT, "ProjectInputs", "GDD")
    handoff_draft_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Handoffs", "draft")
    handoff_approved_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Handoffs", "approved")
    report_dir = os.path.join(PROJECT_ROOT, "ProjectState", "Reports")

    for directory in [handoff_draft_dir, handoff_approved_dir, report_dir]:
        os.makedirs(directory, exist_ok=True)

    print("=" * 60)
    print("Boardgame Playable Runtime Demo")
    print("=" * 60)

    design_input = read_gdd_from_directory(gdd_dir)
    project_state = get_project_state_snapshot()

    print("\n[1/4] 构建 Phase 6 playable handoff...")
    handoff = build_handoff(
        design_input=design_input,
        mode="greenfield_bootstrap",
        project_state=project_state,
        target_stage="prototype_playable",
        projection_profile="runtime_playable",
    )
    print(f"  Handoff ID: {handoff['handoff_id']}")
    print(f"  Handoff 状态: {handoff['status']}")
    print(f"  Runtime Config: {handoff.get('metadata', {}).get('runtime_config_ref', '')}")
    print(f"  Spec 节点: {sorted(handoff['dynamic_spec_tree'].keys())}")

    draft_path = serialize_handoff(handoff, handoff_draft_dir, "yaml")
    print(f"  Draft: {draft_path}")

    if handoff.get("status") == "blocked":
        raise RuntimeError("Playable runtime handoff 被 review 阻断，无法进入执行阶段。")

    print("\n[2/4] 自动审批到 approved_for_execution...")
    approved_handoff = dict(handoff)
    approved_handoff["status"] = "approved_for_execution"
    approved_path = serialize_handoff(approved_handoff, handoff_approved_dir, "yaml")
    print(f"  Approved: {approved_path}")

    print("\n[3/4] 执行 runtime_playable 投影...")
    result = run_from_handoff(
        approved_path,
        report_output_dir=report_dir,
        bridge_mode=bridge_mode,
    )
    print(f"  执行状态: {result['status']}")

    smoke_report_path = _run_runtime_smoke(
        result=result,
        bridge_mode=bridge_mode,
        report_dir=report_dir,
    )
    if smoke_report_path:
        print(f"  Runtime Smoke: {smoke_report_path}")

    if capture_evidence and bridge_mode == "bridge_rc_api" and result.get("status") == "succeeded":
        _try_capture_phase6_evidence(
            approved_path=approved_path,
            report_path=smoke_report_path or _find_latest_report(report_dir, handoff["handoff_id"]),
            design_input=design_input,
        )

    print("\n[4/4] 完成。")
    return result


def _run_runtime_smoke(result: Dict[str, Any], bridge_mode: str, report_dir: str) -> str:
    """对 runtime actor 执行最小烟雾测试，并写报告。"""
    actor_path = _find_runtime_actor_path(result)
    if not actor_path:
        return ""

    report = {
        "report_type": "phase6_runtime_smoke",
        "generated_at": datetime.now().isoformat(),
        "bridge_mode": bridge_mode,
        "actor_path": actor_path,
        "moves": [],
        "runtime_state": {},
    }

    if bridge_mode == "bridge_rc_api":
        from bridge.remote_control_client import call_function

        for row, col in [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2)]:
            response = call_function(actor_path, "ApplyMoveByCell", {"Row": row, "Col": col})
            report["moves"].append({"row": row, "col": col, "response": response})
        state_response = call_function(actor_path, "GetBoardRuntimeState", {})
        report["runtime_state"] = state_response
    else:
        report["moves"] = [
            {"row": row, "col": col, "response": {"status": "simulated"}}
            for row, col in [(0, 0), (1, 1), (0, 1), (2, 2), (0, 2)]
        ]
        report["runtime_state"] = {"ReturnValue": "{\"result_state\":\"simulated\"}"}

    output_path = os.path.join(
        report_dir,
        f"phase6_runtime_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=2, ensure_ascii=False)
    return output_path


def _find_runtime_actor_path(result: Dict[str, Any]) -> str:
    """从执行结果中找到 runtime actor。"""
    for step in result.get("step_results", []):
        step_result = step.get("result", {})
        if step_result.get("actor_name") == "BoardRuntimeActor":
            return step_result.get("actor_path", "")
    return ""


def _try_capture_phase6_evidence(
    approved_path: str,
    report_path: str,
    design_input: Dict[str, Any],
) -> None:
    """在真实 UE5 环境中采集 Phase 6 截图证据。"""
    try:
        from validation.capture_editor_evidence import capture_editor_scene_evidence

        capture_result = capture_editor_scene_evidence(
            phase_name="Phase6",
            task_id="task_phase6_boardgame_playable_demo",
            scenario="runtime_playable",
            actor_names=["BoardRuntimeActor", "PieceX_1", "PieceO_1", "PieceX_2", "PieceO_2", "PieceX_3"],
            handoff_path=approved_path,
            report_path=report_path,
            board_center=list(design_input.get("board", {}).get("location", [0.0, 0.0, 0.0])),
        )
        print(f"  证据说明: {capture_result['note_path']}")
        print(f"  证据日志: {capture_result['log_path']}")
    except Exception as exc:
        print(f"  [警告] Phase 6 截图证据采集失败: {exc}")


def _find_latest_report(report_dir: str, handoff_id: str) -> str:
    """找到 handoff 对应的最新执行报告。"""
    candidates: List[str] = []
    if os.path.isdir(report_dir):
        for file_name in os.listdir(report_dir):
            if handoff_id in file_name and file_name.endswith(".json"):
                candidates.append(os.path.join(report_dir, file_name))
    if not candidates:
        return ""
    return max(candidates, key=os.path.getmtime)


if __name__ == "__main__":
    selected_mode = "simulated"
    if len(sys.argv) > 1:
        selected_mode = sys.argv[1]

    result = run_boardgame_playable_demo(bridge_mode=selected_mode)
    sys.exit(0 if result.get("status") == "succeeded" else 1)
