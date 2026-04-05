"""
MCP Server 工具定义 — 所有工具的参数、返回值、错误码规范。

分三层：
  Layer 1: Bridge 已有工具（15 个）— 包装 query_tools + write_tools
  Layer 2: 新增 Channel A 资产创建工具（9 个）
  Layer 3: 通用兜底（1 个）

所有工具统一返回 tool_contract_v0_1.md 格式：
  {status, summary, data, warnings, errors}

错误码复用 tool_contract_v0_1.md §3 定义：
  INVALID_ARGS, ACTOR_NOT_FOUND, ASSET_NOT_FOUND,
  EDITOR_NOT_READY, TOOL_EXECUTION_FAILED, CHANNEL_UNAVAILABLE,
  PERMISSION_DENIED, TIMEOUT, UNKNOWN_ERROR
"""

# ============================================================
# Layer 1: Bridge 已有工具（复用）
# ============================================================

LAYER1_QUERY_TOOLS = {
    "get_current_project_state": {
        "description": "获取当前 UE5 项目状态（项目名、引擎版本、当前关卡等）",
        "params": {},
        "returns": "项目状态对象"
    },
    "list_level_actors": {
        "description": "列出当前关卡中的所有 Actor",
        "params": {
            "class_filter": {"type": "string", "required": False, "description": "可选类名过滤"}
        },
        "returns": "Actor 列表"
    },
    "get_actor_state": {
        "description": "获取指定 Actor 的完整状态（transform、组件、属性等）",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"}
        },
        "returns": "Actor 状态对象"
    },
    "get_actor_bounds": {
        "description": "获取指定 Actor 的包围盒",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"}
        },
        "returns": "包围盒数据"
    },
    "get_asset_metadata": {
        "description": "获取指定资产的元数据",
        "params": {
            "asset_path": {"type": "string", "required": True, "description": "资产路径"}
        },
        "returns": "资产元数据"
    },
    "get_dirty_assets": {
        "description": "获取所有未保存的脏资产列表",
        "params": {},
        "returns": "脏资产列表"
    },
    "run_map_check": {
        "description": "运行当前关卡的 Map Check，检查错误和警告",
        "params": {},
        "returns": "Map Check 结果"
    },
}

LAYER1_WRITE_TOOLS = {
    "spawn_actor": {
        "description": "在当前关卡中生成 Actor",
        "params": {
            "level_path": {"type": "string", "required": False, "description": "关卡路径（默认当前）"},
            "actor_class": {"type": "string", "required": True, "description": "Actor 类路径"},
            "actor_name": {"type": "string", "required": True, "description": "Actor 名称"},
            "transform": {
                "type": "object", "required": True,
                "description": "Transform {location: [x,y,z], rotation: [p,y,r], relative_scale3d: [x,y,z]}"
            },
            "dry_run": {"type": "boolean", "required": False, "description": "模拟执行不实际创建"}
        },
        "returns": "含 actual_transform 的反馈",
        "error_codes": ["INVALID_ARGS", "EDITOR_NOT_READY", "TOOL_EXECUTION_FAILED"]
    },
    "set_actor_transform": {
        "description": "修改指定 Actor 的 Transform",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"},
            "transform": {"type": "object", "required": True, "description": "新 Transform"},
            "dry_run": {"type": "boolean", "required": False}
        },
        "returns": "含 actual_transform 的反馈",
        "error_codes": ["ACTOR_NOT_FOUND", "INVALID_ARGS"]
    },
    "import_assets": {
        "description": "导入外部资产到 UE5 项目",
        "params": {
            "source_path": {"type": "string", "required": True},
            "destination_path": {"type": "string", "required": True}
        },
        "returns": "导入结果"
    },
    "create_blueprint_child": {
        "description": "创建指定父类的 Blueprint 子类",
        "params": {
            "parent_class": {"type": "string", "required": True, "description": "父类路径"},
            "blueprint_name": {"type": "string", "required": True, "description": "新 BP 名称"},
            "destination_path": {"type": "string", "required": True, "description": "保存路径"}
        },
        "returns": "创建的 Blueprint 路径"
    },
    "set_actor_collision": {
        "description": "设置 Actor 碰撞配置",
        "params": {
            "actor_path": {"type": "string", "required": True},
            "collision_preset": {"type": "string", "required": True}
        },
        "returns": "碰撞设置结果"
    },
    "assign_material": {
        "description": "给 Actor 指定材质",
        "params": {
            "actor_path": {"type": "string", "required": True},
            "material_path": {"type": "string", "required": True},
            "slot_index": {"type": "integer", "required": False, "description": "材质槽索引（默认 0）"}
        },
        "returns": "材质赋值结果"
    },
}

LAYER1_SERVICE_TOOLS = {
    "capture_screenshot": {
        "description": "截取当前视口截图",
        "params": {
            "output_path": {"type": "string", "required": False, "description": "保存路径"}
        },
        "returns": "截图文件路径"
    },
    "save_named_assets": {
        "description": "保存指定资产",
        "params": {
            "asset_paths": {"type": "array", "required": True, "description": "资产路径列表"}
        },
        "returns": "保存结果"
    },
    "build_project": {
        "description": "编译 C++ 项目",
        "params": {
            "target": {"type": "string", "required": False, "description": "编译目标（默认 Editor）"}
        },
        "returns": "编译结果（成功/失败/错误列表）",
        "error_codes": ["EDITOR_NOT_READY", "TOOL_EXECUTION_FAILED"]
    },
    "run_automation_tests": {
        "description": "运行 UE5 Automation Test",
        "params": {
            "test_filter": {"type": "string", "required": False, "description": "测试过滤器"}
        },
        "returns": "测试结果"
    },
    "undo_last_transaction": {
        "description": "撤销上一次 Transaction",
        "params": {},
        "returns": "撤销结果"
    },
}


# ============================================================
# Layer 2: 新增 Channel A 资产创建工具
# ============================================================

LAYER2_ASSET_TOOLS = {
    "create_level": {
        "description": "创建新关卡",
        "params": {
            "level_name": {"type": "string", "required": True, "description": "关卡名称（如 L_BoardLevel）"},
            "level_path": {"type": "string", "required": False, "description": "保存路径（默认 /Game/Maps/）"},
            "template": {"type": "string", "required": False, "description": "模板（默认 Empty Level）"}
        },
        "returns": "创建的关卡路径",
        "error_codes": ["INVALID_ARGS", "EDITOR_NOT_READY", "TOOL_EXECUTION_FAILED"],
        "channel": "A",
        "notes": "通过 Python Editor Scripting 的 unreal.EditorLevelLibrary 实现"
    },
    "create_material": {
        "description": "创建材质母版",
        "params": {
            "material_name": {"type": "string", "required": True, "description": "材质名称（如 M_TileBase）"},
            "material_path": {"type": "string", "required": False, "description": "保存路径（默认 /Game/Materials/）"},
            "base_color": {"type": "array", "required": False, "description": "基础颜色 [R, G, B, A]（0-1 范围）"}
        },
        "returns": "创建的材质路径",
        "channel": "A",
        "notes": "通过 unreal.AssetToolsHelpers + unreal.MaterialFactoryNew 实现"
    },
    "create_material_instance": {
        "description": "创建材质实例",
        "params": {
            "instance_name": {"type": "string", "required": True, "description": "实例名称（如 MI_Brown）"},
            "parent_material": {"type": "string", "required": True, "description": "父材质路径"},
            "instance_path": {"type": "string", "required": False, "description": "保存路径"},
            "scalar_params": {"type": "object", "required": False, "description": "标量参数 {name: value}"},
            "vector_params": {"type": "object", "required": False, "description": "向量参数 {name: [R,G,B,A]}"}
        },
        "returns": "创建的材质实例路径",
        "channel": "A"
    },
    "create_widget_blueprint": {
        "description": "创建 Widget Blueprint（UMG）",
        "params": {
            "widget_name": {"type": "string", "required": True, "description": "Widget 名称（如 WBP_GameHUD）"},
            "widget_path": {"type": "string", "required": False, "description": "保存路径（默认 /Game/UI/）"},
            "parent_class": {"type": "string", "required": False, "description": "父类（默认 UserWidget）"}
        },
        "returns": "创建的 Widget Blueprint 路径",
        "channel": "A",
        "notes": "通过 Python Editor Scripting 创建，具体 UI 布局需在蓝图编辑器中完成"
    },
    "set_blueprint_defaults": {
        "description": "设置 Blueprint 的默认属性值",
        "params": {
            "blueprint_path": {"type": "string", "required": True, "description": "Blueprint 路径"},
            "property_name": {"type": "string", "required": True, "description": "属性名"},
            "property_value": {"type": "any", "required": True, "description": "属性值"}
        },
        "returns": "设置结果",
        "channel": "A"
    },
    "configure_gamemode_bp": {
        "description": "配置 GameMode Blueprint 的核心设置",
        "params": {
            "gamemode_path": {"type": "string", "required": True, "description": "GameMode BP 路径"},
            "default_pawn_class": {"type": "string", "required": False},
            "player_controller_class": {"type": "string", "required": False},
            "game_state_class": {"type": "string", "required": False},
            "player_state_class": {"type": "string", "required": False},
            "hud_class": {"type": "string", "required": False}
        },
        "returns": "配置结果",
        "channel": "A",
        "notes": "通过 set_blueprint_defaults 设置 GameMode 各默认类引用"
    },
    "configure_world_settings": {
        "description": "配置当前关卡的 World Settings",
        "params": {
            "gamemode_override": {"type": "string", "required": False, "description": "GameMode 覆盖类"},
            "default_gamemode": {"type": "string", "required": False}
        },
        "returns": "配置结果",
        "channel": "B",
        "notes": "通过 Remote Control API 设置 WorldSettings 属性"
    },
    "open_level": {
        "description": "打开指定关卡",
        "params": {
            "level_path": {"type": "string", "required": True, "description": "关卡资产路径"}
        },
        "returns": "打开结果",
        "channel": "A"
    },
    "save_all": {
        "description": "保存所有脏资产",
        "params": {},
        "returns": "保存结果",
        "channel": "A"
    },
}


# ============================================================
# Layer 3: 通用兜底
# ============================================================

LAYER3_TOOLS = {
    "run_editor_python": {
        "description": "在 UE5 Editor 中执行任意 Python 脚本",
        "params": {
            "script": {"type": "string", "required": True, "description": "Python 脚本内容"},
            "timeout_ms": {"type": "integer", "required": False, "description": "超时毫秒数（默认 30000）"}
        },
        "returns": "脚本执行结果（stdout + return value）",
        "channel": "A",
        "notes": "兜底工具，仅在 Layer 1/2 工具无法覆盖时使用"
    },
}


# ============================================================
# 工具总表
# ============================================================

ALL_TOOLS = {}
ALL_TOOLS.update(LAYER1_QUERY_TOOLS)
ALL_TOOLS.update(LAYER1_WRITE_TOOLS)
ALL_TOOLS.update(LAYER1_SERVICE_TOOLS)
ALL_TOOLS.update(LAYER2_ASSET_TOOLS)
ALL_TOOLS.update(LAYER3_TOOLS)

TOOL_COUNT = len(ALL_TOOLS)
# 预期：7(query) + 6(write) + 5(service) + 9(asset) + 1(fallback) = 28
