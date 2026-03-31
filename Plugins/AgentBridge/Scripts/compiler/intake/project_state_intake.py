"""
Project State Intake
调用现有查询接口，获取项目现状
"""

from typing import Dict, Any


def get_project_state_snapshot() -> Dict[str, Any]:
    """
    获取项目现状快照

    Returns:
        标准化的项目现状快照
    """
    # 注意：这里需要调用 AgentBridge 现有的查询接口
    # 第一阶段最小实现：返回模拟数据
    # 后续需要真正调用 bridge.query_tools

    try:
        # TODO: 调用现有接口
        # from bridge.query_tools import get_current_project_state, list_level_actors
        # project_state = get_current_project_state()
        # actors = list_level_actors()

        # 最小实现：模拟返回
        project_state = {
            "project_name": "Mvpv4TestCodex",
            "engine_version": "5.5.4",
            "current_level": "/Game/Maps/TestMap"
        }

        actors = {
            "actors": []  # 空项目
        }

        return {
            "project_name": project_state.get("project_name"),
            "engine_version": project_state.get("engine_version"),
            "current_level": project_state.get("current_level"),
            "actor_count": len(actors.get("actors", [])),
            "is_empty": len(actors.get("actors", [])) == 0,
            "actors": actors.get("actors", [])
        }

    except Exception as e:
        # 如果调用失败，返回默认值
        return {
            "project_name": "Unknown",
            "engine_version": "Unknown",
            "current_level": "Unknown",
            "actor_count": 0,
            "is_empty": True,
            "actors": [],
            "error": str(e)
        }


def check_baseline_exists(baseline_path: str) -> bool:
    """
    检查是否存在 baseline

    Args:
        baseline_path: Baseline 目录路径

    Returns:
        是否存在 baseline
    """
    import os

    if not os.path.exists(baseline_path):
        return False

    # 检查目录中是否有文件
    files = os.listdir(baseline_path)
    return len(files) > 0


if __name__ == "__main__":
    # 测试代码
    snapshot = get_project_state_snapshot()
    print(f"项目名称: {snapshot['project_name']}")
    print(f"Actor 数量: {snapshot['actor_count']}")
    print(f"是否为空项目: {snapshot['is_empty']}")
