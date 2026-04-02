"""
端到端运行脚本
Greenfield + Boardgame + Reviewed Handoff 最小闭环
"""

import os
import sys

# 项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 路径适配：必须导入插件层 Scripts，支持 from compiler.xxx / orchestrator.xxx
scripts_dir = os.path.join(project_root, "Plugins", "AgentBridge", "Scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from compiler.handoff import serialize_handoff
from compiler.intake import get_project_state_snapshot, read_gdd_from_directory
from compiler.routing import determine_mode, load_mode_config
from compiler.handoff import build_handoff
from bridge.project_config import get_dated_project_reports_dir
from orchestrator.handoff_runner import run_from_handoff


def run_greenfield_demo(bridge_mode: str = "simulated"):
    """
    运行 Greenfield + Boardgame 最小闭环。

    Args:
        bridge_mode: Bridge 调用模式
            - "simulated": 模拟执行（默认）
            - "bridge_python": 调用现有 Python Bridge
            - "bridge_rc_api": 调用 Remote Control API
    """
    gdd_dir = os.path.join(project_root, "ProjectInputs", "GDD")
    mode_config_path = os.path.join(project_root, "ProjectInputs", "Presets", "mode_override.yaml")
    handoff_draft_dir = os.path.join(project_root, "ProjectState", "Handoffs", "draft")
    handoff_approved_dir = os.path.join(project_root, "ProjectState", "Handoffs", "approved")
    report_dir = str(get_dated_project_reports_dir())

    for directory in [handoff_draft_dir, handoff_approved_dir, report_dir]:
        os.makedirs(directory, exist_ok=True)

    print("=" * 60)
    print("Greenfield + Boardgame + Handoff 最小闭环")
    print("=" * 60)

    print("\n[阶段 1] Compiler：读取 GDD → 判定模式 → 生成 Handoff")

    print("\n[1/5] 读取 GDD...")
    design_input = read_gdd_from_directory(gdd_dir)
    print(f"  游戏类型: {design_input['game_type']}")
    print(f"  Feature Tags: {design_input.get('feature_tags', [])}")

    print("\n[2/5] 获取项目现状...")
    project_state = get_project_state_snapshot()
    print(f"  是否为空项目: {project_state['is_empty']}")

    print("\n[3/5] 判定模式...")
    mode_config = load_mode_config(mode_config_path)
    mode = determine_mode(mode_config, project_state)
    print(f"  检测到的模式: {mode}")

    print("\n[4/5] 构建 Handoff...")
    handoff = build_handoff(design_input, mode, project_state)
    actor_count = len(handoff["dynamic_spec_tree"]["scene_spec"]["actors"])
    rich_nodes = sorted(key for key in handoff["dynamic_spec_tree"].keys() if key != "scene_spec")
    print(f"  Handoff ID: {handoff['handoff_id']}")
    print(f"  Handoff 状态: {handoff['status']}")
    print(f"  Actor 数量: {actor_count}")
    print(f"  Richer Spec 节点: {rich_nodes}")
    print(f"  Review 摘要: {handoff.get('review_summary', {}).get('review_notes', '')}")

    print("\n[5/5] 保存 Handoff (draft)...")
    draft_path = serialize_handoff(handoff, handoff_draft_dir, "yaml")
    print(f"  保存到: {draft_path}")

    if handoff.get("status") == "blocked":
        raise RuntimeError("Cross-Spec Review 未通过，已阻止进入执行阶段。")

    print("\n[阶段 2] 审批：将 Handoff 从 draft 进入 approved_for_execution")

    approved_handoff = dict(handoff)
    approved_handoff["status"] = "approved_for_execution"
    approved_path = serialize_handoff(approved_handoff, handoff_approved_dir, "yaml")
    print(f"  已自动审批: {approved_path}")

    print("\n[阶段 3] Orchestrator：读取 approved Handoff → 生成 Run Plan → 执行")
    print(f"  Bridge 模式: {bridge_mode}")

    result = run_from_handoff(
        approved_path,
        report_output_dir=report_dir,
        bridge_mode=bridge_mode,
    )

    print("\n" + "=" * 60)
    print("执行结果汇总")
    print("=" * 60)
    print(f"  执行状态: {result['status']}")
    print(f"  步骤数: {len(result.get('step_results', []))}")

    for step in result.get("step_results", []):
        step_status = step.get("result", {}).get("status", "unknown")
        icon = "[OK]" if step_status == "success" else "[FAIL]"
        print(f"  {icon} {step['step_id']}: {step_status}")

    print(f"\n  Draft Handoff: {draft_path}")
    print(f"  Approved Handoff: {approved_path}")
    print(f"  报告目录: {report_dir}")
    print("=" * 60)

    return result


if __name__ == "__main__":
    mode = "simulated"
    if len(sys.argv) > 1:
        mode = sys.argv[1]

    result = run_greenfield_demo(bridge_mode=mode)
    sys.exit(0 if result.get("status") == "succeeded" else 1)
