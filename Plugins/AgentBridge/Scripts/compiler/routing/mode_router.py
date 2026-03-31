"""
Mode Router
根据配置和项目状态判断模式

模式解析优先级（基于 Greenfield_Brownfield_模式切换规则_v2）：

  优先级 1: Explicit User Override (force_mode)
    - 开发者在插件入口显式指定，系统不应推翻
  优先级 2: Project / Profile Preset (default_mode)
    - 项目级 preset 中的默认模式配置
  优先级 3: Auto Detection Fallback
    - 仅当 default_mode == "auto" 时，根据项目状态自动判定

核心原则：显式选择 > 自动判断。模式误判带来的不是回答偏差，而是施工路径偏差。
"""

from typing import Dict, Any

# 合法模式值
VALID_MODES = ["greenfield_bootstrap", "brownfield_expansion"]


def determine_mode(config: Dict[str, Any], project_state: Dict[str, Any]) -> str:
    """
    判断模式

    按三级优先级解析：
    1. Explicit User Override (force_mode)
    2. Project / Profile Preset (default_mode)
    3. Auto Detection Fallback

    Args:
        config: 模式配置（来自 mode_override.yaml）
        project_state: 项目现状快照

    Returns:
        模式字符串：greenfield_bootstrap 或 brownfield_expansion
    """
    # 优先级 1: Explicit User Override
    # 开发者显式指定，系统不应推翻
    force_mode = config.get("force_mode")
    if force_mode:
        if force_mode in VALID_MODES:
            return force_mode
        else:
            raise ValueError(f"无效的 force_mode: {force_mode}，合法值: {VALID_MODES}")

    # 优先级 2: Project / Profile Preset
    default_mode = config.get("default_mode", "auto")

    if default_mode in VALID_MODES:
        return default_mode

    # 优先级 3: Auto Detection Fallback
    # 仅当 default_mode == "auto" 时进入自动判定
    if default_mode == "auto":
        return auto_detect_mode(config, project_state)

    raise ValueError(f"无效的 default_mode: {default_mode}，合法值: {VALID_MODES + ['auto']}")


def auto_detect_mode(config: Dict[str, Any], project_state: Dict[str, Any]) -> str:
    """
    自动检测模式

    Args:
        config: 模式配置
        project_state: 项目现状快照

    Returns:
        检测到的模式
    """
    detection_rules = config.get("mode_detection_rules", {})
    empty_threshold = detection_rules.get("empty_project_threshold", 0)

    # 检查项目是否为空
    actor_count = project_state.get("actor_count", 0)

    if actor_count <= empty_threshold:
        # 空项目 → Greenfield
        return "greenfield_bootstrap"
    else:
        # 非空项目 → Brownfield
        return "brownfield_expansion"


def load_mode_config(config_path: str) -> Dict[str, Any]:
    """
    加载模式配置

    Args:
        config_path: 配置文件路径

    Returns:
        配置字典
    """
    import yaml
    import os

    if not os.path.exists(config_path):
        # 返回默认配置
        return {
            "default_mode": "auto",
            "force_mode": None,
            "mode_detection_rules": {
                "empty_project_threshold": 0,
                "require_baseline": False
            }
        }

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


if __name__ == "__main__":
    # 测试代码
    test_config = {
        "default_mode": "auto",
        "force_mode": None,
        "mode_detection_rules": {
            "empty_project_threshold": 0
        }
    }

    test_project_state = {
        "actor_count": 0,
        "is_empty": True
    }

    mode = determine_mode(test_config, test_project_state)
    print(f"检测到的模式: {mode}")
