"""
MCP 命名与路径规范。
MCP 创建资产时强制校验命名规范。
"""

# UE5 资产路径规范
ASSET_PATHS = {
    "level":             "/Game/Maps/",
    "blueprint":         "/Game/Blueprints/Core/",
    "material":          "/Game/Materials/",
    "material_instance": "/Game/Materials/Instances/",
    "widget":            "/Game/UI/",
    "data_asset":        "/Game/Data/",
    "texture":           "/Game/Textures/",
}

# 资产前缀规范
ASSET_PREFIXES = {
    "level":             "L_",
    "blueprint":         "BP_",
    "material":          "M_",
    "material_instance": "MI_",
    "widget":            "WBP_",
    "data_asset":        "DA_",
    "texture":           "T_",
}

# C++ 类命名规范（来自 GDD Part B）
CPP_CLASS_PREFIX = "M"  # 所有 Monopoly 游戏类用 M 前缀


def validate_asset_name(asset_type: str, name: str) -> tuple:
    """
    校验资产名称是否符合命名规范。
    返回 (is_valid, corrected_name, message)
    """
    prefix = ASSET_PREFIXES.get(asset_type)
    if prefix is None:
        return True, name, f"未知资产类型 {asset_type}，跳过前缀检查"

    if name.startswith(prefix):
        return True, name, "命名规范"
    else:
        corrected = f"{prefix}{name}"
        return False, corrected, f"建议命名：{corrected}（应以 {prefix} 开头）"


def get_default_path(asset_type: str) -> str:
    """获取资产类型的默认保存路径"""
    return ASSET_PATHS.get(asset_type, "/Game/Misc/")


def make_full_asset_path(asset_type: str, name: str, custom_path: str = None) -> str:
    """组合完整资产路径"""
    path = custom_path if custom_path else get_default_path(asset_type)
    if not path.endswith("/"):
        path += "/"
    return f"{path}{name}"
