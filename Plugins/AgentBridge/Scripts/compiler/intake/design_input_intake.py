"""
Design Input Intake
读取项目层 GDD，提取关键信息
"""

import os
from typing import Dict, Any


def read_gdd(gdd_path: str) -> Dict[str, Any]:
    """
    读取 GDD 文件，提取关键信息

    Args:
        gdd_path: GDD 文件路径

    Returns:
        标准化的设计输入包
    """
    if not os.path.exists(gdd_path):
        raise FileNotFoundError(f"GDD 文件不存在: {gdd_path}")

    with open(gdd_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 最小实现：从 markdown 提取游戏类型
    game_type = extract_game_type(content)
    scene_requirements = extract_scene_requirements(content)

    return {
        "game_type": game_type,
        "scene_requirements": scene_requirements,
        "raw_content": content,
        "source_file": gdd_path
    }


def extract_game_type(content: str) -> str:
    """从 GDD 内容提取游戏类型"""
    # 简单实现：查找 "游戏类型" 章节
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '游戏类型' in line or 'Game Type' in line.lower():
            # 下一行通常是类型
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if 'boardgame' in next_line.lower() or '棋盘' in next_line:
                    return "boardgame"

    # 默认返回
    return "unknown"


def extract_scene_requirements(content: str) -> list:
    """从 GDD 内容提取场景需求"""
    # 最小实现：返回空列表
    # 后续可以补充更复杂的解析逻辑
    return []


def read_gdd_from_directory(gdd_dir: str) -> Dict[str, Any]:
    """
    从目录读取 GDD（支持多个文件）

    Args:
        gdd_dir: GDD 目录路径

    Returns:
        合并后的设计输入包
    """
    if not os.path.isdir(gdd_dir):
        raise NotADirectoryError(f"GDD 目录不存在: {gdd_dir}")

    # 查找所有 .md 文件
    gdd_files = [f for f in os.listdir(gdd_dir) if f.endswith('.md')]

    if not gdd_files:
        raise FileNotFoundError(f"GDD 目录中没有找到 .md 文件: {gdd_dir}")

    # 读取第一个 GDD 文件（最小实现）
    first_gdd = os.path.join(gdd_dir, gdd_files[0])
    return read_gdd(first_gdd)


if __name__ == "__main__":
    # 测试代码
    test_gdd_path = "../../ProjectInputs/GDD/boardgame_tictactoe_v1.md"
    if os.path.exists(test_gdd_path):
        result = read_gdd(test_gdd_path)
        print(f"游戏类型: {result['game_type']}")
        print(f"场景需求: {result['scene_requirements']}")
