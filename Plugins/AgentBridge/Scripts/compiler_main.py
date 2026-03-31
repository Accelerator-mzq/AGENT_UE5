"""
Compiler 主入口
端到端运行：GDD → Handoff
"""

import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from compiler.intake import read_gdd_from_directory, get_project_state_snapshot
from compiler.routing import determine_mode, load_mode_config
from compiler.handoff import build_handoff, serialize_handoff


def run_compiler(
    gdd_dir: str,
    mode_config_path: str,
    output_dir: str,
    output_format: str = "yaml"
):
    """
    运行 Compiler：GDD → Handoff

    Args:
        gdd_dir: GDD 目录路径
        mode_config_path: 模式配置文件路径
        output_dir: Handoff 输出目录
        output_format: 输出格式（yaml / json）
    """
    print("=" * 60)
    print("AgentBridge Skill Compiler")
    print("=" * 60)

    # 1. 读取 GDD
    print("\n[1/5] 读取 GDD...")
    design_input = read_gdd_from_directory(gdd_dir)
    print(f"  游戏类型: {design_input['game_type']}")
    print(f"  来源文件: {design_input['source_file']}")

    # 2. 获取项目现状
    print("\n[2/5] 获取项目现状...")
    project_state = get_project_state_snapshot()
    print(f"  项目名称: {project_state['project_name']}")
    print(f"  Actor 数量: {project_state['actor_count']}")
    print(f"  是否为空: {project_state['is_empty']}")

    # 3. 判断模式
    print("\n[3/5] 判断模式...")
    mode_config = load_mode_config(mode_config_path)
    mode = determine_mode(mode_config, project_state)
    print(f"  检测到的模式: {mode}")

    # 4. 构建 Handoff
    print("\n[4/5] 构建 Handoff...")
    handoff = build_handoff(design_input, mode, project_state)
    print(f"  Handoff ID: {handoff['handoff_id']}")
    print(f"  Handoff Mode: {handoff['handoff_mode']}")
    print(f"  Actor 数量: {len(handoff['dynamic_spec_tree']['scene_spec']['actors'])}")

    # 5. 保存 Handoff
    print("\n[5/5] 保存 Handoff...")
    output_file = serialize_handoff(handoff, output_dir, output_format)
    print(f"  保存到: {output_file}")

    print("\n" + "=" * 60)
    print("✅ Compiler 运行完成")
    print("=" * 60)

    return handoff


if __name__ == "__main__":
    # 默认路径（相对于 input/ 目录）
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.dirname(script_dir)

    gdd_dir = os.path.join(input_dir, "ProjectInputs", "GDD")
    mode_config_path = os.path.join(input_dir, "ProjectInputs", "Presets", "mode_override.yaml")
    output_dir = os.path.join(input_dir, "ProjectState", "Handoffs", "draft")

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 运行
    try:
        handoff = run_compiler(gdd_dir, mode_config_path, output_dir, output_format="yaml")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
