"""
Compiler 主入口
端到端运行：GDD → Handoff
"""

import os
import sys

# 添加路径，支持 from compiler.xxx 导入。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compiler.intake import get_project_state_snapshot, read_gdd_from_directory
from compiler.routing import determine_mode, load_mode_config
from compiler.handoff import build_handoff, serialize_handoff


def get_project_root() -> str:
    """返回项目根目录。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_root = os.path.abspath(os.path.join(script_dir, ".."))
    return os.path.abspath(os.path.join(plugin_root, "..", ".."))


def run_compiler(
    gdd_dir: str,
    mode_config_path: str,
    output_dir: str,
    output_format: str = "yaml",
):
    """
    运行 Compiler：GDD → Handoff。
    """
    print("=" * 60)
    print("AgentBridge Skill Compiler")
    print("=" * 60)

    print("\n[1/5] 读取 GDD...")
    design_input = read_gdd_from_directory(gdd_dir)
    print(f"  游戏类型: {design_input['game_type']}")
    print(f"  来源文件: {design_input['source_file']}")
    print(f"  Feature Tags: {design_input.get('feature_tags', [])}")

    print("\n[2/5] 获取项目现状...")
    project_state = get_project_state_snapshot()
    print(f"  项目名称: {project_state['project_name']}")
    print(f"  Actor 数量: {project_state['actor_count']}")
    print(f"  是否为空: {project_state['is_empty']}")

    print("\n[3/5] 判断模式...")
    mode_config = load_mode_config(mode_config_path)
    mode = determine_mode(mode_config, project_state)
    print(f"  检测到的模式: {mode}")

    print("\n[4/5] 构建 Handoff...")
    handoff = build_handoff(design_input, mode, project_state)
    scene_actors = handoff["dynamic_spec_tree"]["scene_spec"]["actors"]
    rich_nodes = sorted(key for key in handoff["dynamic_spec_tree"].keys() if key != "scene_spec")
    print(f"  Handoff ID: {handoff['handoff_id']}")
    print(f"  Handoff Mode: {handoff['handoff_mode']}")
    print(f"  Handoff Status: {handoff['status']}")
    print(f"  Actor 数量: {len(scene_actors)}")
    print(f"  Richer Spec 节点: {rich_nodes}")

    print("\n[5/5] 保存 Handoff...")
    output_file = serialize_handoff(handoff, output_dir, output_format)
    print(f"  保存到: {output_file}")

    print("\n" + "=" * 60)
    print("Compiler 运行完成")
    print("=" * 60)

    return handoff, output_file


if __name__ == "__main__":
    project_root = get_project_root()
    gdd_dir = os.path.join(project_root, "ProjectInputs", "GDD")
    mode_config_path = os.path.join(project_root, "ProjectInputs", "Presets", "mode_override.yaml")
    output_dir = os.path.join(project_root, "ProjectState", "Handoffs", "draft")

    os.makedirs(output_dir, exist_ok=True)

    try:
        handoff, _ = run_compiler(gdd_dir, mode_config_path, output_dir, output_format="yaml")
        sys.exit(0 if handoff.get("status") != "blocked" else 1)
    except Exception as exc:
        print(f"\n错误: {str(exc)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
