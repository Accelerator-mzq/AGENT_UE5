"""
AgentBridge MCP Server — 主入口。

通过 stdio 传输协议暴露 UE5 Editor 能力给 Claude Code。

架构：
  Claude Code (stdio) → MCP Server → Bridge 三通道 → UE5 Editor

启动方式：
  由 .mcp.json 配置，Claude Code 自动通过 stdio 启动。
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

# 添加 Bridge 模块路径
BRIDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "Scripts", "bridge")
sys.path.insert(0, os.path.abspath(BRIDGE_DIR))

# 添加本目录
MCP_DIR = os.path.dirname(__file__)
sys.path.insert(0, MCP_DIR)

from tool_definitions import (  # noqa: E402
    ALL_TOOLS,
    COMPILER_FRONTEND_TOOLS,
    EVIDENCE_JUDGE_TOOLS,
    LAYER1_QUERY_TOOLS,
    LAYER1_SERVICE_TOOLS,
    LAYER1_WRITE_TOOLS,
    LAYER2_ASSET_TOOLS,
    LAYER3_TOOLS,
    to_json_schema,
)
import compiler_tools  # noqa: E402
import evidence_tools  # noqa: E402

logger = logging.getLogger("agentbridge-mcp")


def _configure_bridge_channel() -> tuple[str, list[str]]:
    """为 MCP 进程设置默认 Bridge 通道，避免误用 Mock 示例数据。"""
    warnings = []

    try:
        from bridge_core import BridgeChannel, get_channel, set_channel
    except Exception as exc:
        return "unknown", [f"Bridge 通道初始化失败: {str(exc)}"]

    env_channel = os.environ.get("AGENTBRIDGE_MCP_CHANNEL", "").strip().lower()
    channel_map = {
        "mock": BridgeChannel.MOCK,
        "remote_control": BridgeChannel.REMOTE_CONTROL,
        "rc": BridgeChannel.REMOTE_CONTROL,
        "cpp_plugin": BridgeChannel.CPP_PLUGIN,
        "cpp": BridgeChannel.CPP_PLUGIN,
    }

    if env_channel:
        target_channel = channel_map.get(env_channel)
        if target_channel is None:
            warnings.append(f"未知的 AGENTBRIDGE_MCP_CHANNEL={env_channel}，已回退到 cpp_plugin。")
            target_channel = BridgeChannel.CPP_PLUGIN
    else:
        # UE5.5.4 下 EditorLevelLibrary.GetEditorWorld 不能稳定通过 RC 远程调用。
        # MCP 默认改走项目主干的 C++ Subsystem 通道，避免 live smoke 命中 HTTP 400。
        target_channel = BridgeChannel.CPP_PLUGIN

    set_channel(target_channel)
    return get_channel().value, warnings


ACTIVE_MCP_CHANNEL, MCP_CHANNEL_WARNINGS = _configure_bridge_channel()


def make_response(status: str, summary: str, data=None, warnings=None, errors=None) -> dict:
    """构造统一响应格式（与 tool_contract_v0_1.md §2.2 一致）。"""
    return {
        "status": status,
        "summary": summary,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _python_literal(value: Any) -> str:
    """把 Python 值安全嵌入到远端执行脚本中。"""
    return repr(value)


def _merge_editor_result(data: dict | None, editor_result: Any) -> dict:
    """把底层编辑器返回值附加到统一 data 字段中。"""
    merged = dict(data or {})
    if editor_result is not None:
        merged["editor_result"] = editor_result
    return merged


def _run_editor_python_tool(
    script: str,
    success_summary: str,
    failure_prefix: str,
    data: dict | None = None,
    warnings: list[str] | None = None,
    timeout_ms: int = 30000,
) -> dict:
    """统一执行 Python Editor Scripting，并转换为 MCP 标准返回。"""
    try:
        from py_channel import execute_editor_python

        editor_result = execute_editor_python(script, timeout_ms=timeout_ms)
        return make_response(
            "success",
            success_summary,
            data=_merge_editor_result(data, editor_result),
            warnings=warnings,
        )
    except Exception as exc:
        return make_response(
            "failed",
            f"{failure_prefix}: {str(exc)}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
            warnings=warnings,
        )


def _build_execute_console_command_script(command: str) -> str:
    """在编辑器当前世界执行一条控制台命令。"""
    return f"""
import unreal

world = unreal.EditorLevelLibrary.get_editor_world()
if world is None:
    raise RuntimeError("当前没有可用的编辑器世界")

unreal.SystemLibrary.execute_console_command(world, {_python_literal(command)})
"""


def _extract_object_path(search_result: Any) -> str | None:
    """尽量从 RC 搜索结果里抽取首个对象路径。"""
    if isinstance(search_result, str) and search_result:
        return search_result

    if isinstance(search_result, list):
        for item in search_result:
            object_path = _extract_object_path(item)
            if object_path:
                return object_path
        return None

    if not isinstance(search_result, dict):
        return None

    for key in ("objectPath", "ObjectPath", "path", "Path", "actorPath", "ActorPath"):
        value = search_result.get(key)
        if isinstance(value, str) and value:
            return value

    for key in ("Actors", "actors", "Results", "results", "Items", "items"):
        value = search_result.get(key)
        object_path = _extract_object_path(value)
        if object_path:
            return object_path

    return None


def _build_name_warnings(valid: bool, message: str) -> list[str]:
    """名称被自动修正时，把提示转成统一 warnings。"""
    return [] if valid else [message]


# ============================================================
# Layer 1: Bridge 已有工具包装
# ============================================================

def wrap_bridge_query(tool_name: str, **kwargs) -> dict:
    """包装 Bridge 查询工具调用。"""
    try:
        import query_tools

        func = getattr(query_tools, tool_name, None)
        if func is None:
            return make_response(
                "failed",
                f"未找到查询工具: {tool_name}",
                errors=[f"TOOL_NOT_FOUND: {tool_name}"],
            )
        result = func(**kwargs)
        if MCP_CHANNEL_WARNINGS:
            result["warnings"] = list(MCP_CHANNEL_WARNINGS) + list(result.get("warnings", []))
        return result
    except Exception as exc:
        return make_response(
            "failed",
            f"查询工具执行失败: {tool_name}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def wrap_bridge_write(tool_name: str, **kwargs) -> dict:
    """包装 Bridge 写入工具调用。"""
    try:
        import write_tools

        func = getattr(write_tools, tool_name, None)
        if func is None:
            return make_response(
                "failed",
                f"未找到写入工具: {tool_name}",
                errors=[f"TOOL_NOT_FOUND: {tool_name}"],
            )
        result = func(**kwargs)
        if MCP_CHANNEL_WARNINGS:
            result["warnings"] = list(MCP_CHANNEL_WARNINGS) + list(result.get("warnings", []))
        return result
    except Exception as exc:
        return make_response(
            "failed",
            f"写入工具执行失败: {tool_name}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


# ============================================================
# Layer 2: Channel A 资产创建工具
# ============================================================

def create_level(level_name: str, level_path: str = None, template: str = None) -> dict:
    """创建新关卡（通过 Python Editor Scripting）。"""
    from naming import make_full_asset_path, validate_asset_name

    valid, corrected_name, message = validate_asset_name("level", level_name)
    target_name = corrected_name if corrected_name else level_name
    target_dir = level_path or "/Game/Maps"
    full_path = make_full_asset_path("level", target_name, level_path)
    warnings = _build_name_warnings(valid, message)

    script = f"""
import unreal

created = unreal.EditorLevelLibrary.new_level({_python_literal(full_path)})
if created is False:
    raise RuntimeError("创建关卡返回 False")
"""
    return _run_editor_python_tool(
        script,
        f"关卡创建成功: {full_path}",
        "创建关卡失败",
        data={
            "level_name": target_name,
            "level_path": full_path,
            "target_dir": target_dir,
            "template": template or "Empty Level",
        },
        warnings=warnings,
    )


def create_material(material_name: str, material_path: str = None, base_color: list = None) -> dict:
    """创建材质母版。"""
    from naming import make_full_asset_path, validate_asset_name

    valid, corrected_name, message = validate_asset_name("material", material_name)
    target_name = corrected_name if corrected_name else material_name
    target_dir = material_path or "/Game/Materials"
    full_path = make_full_asset_path("material", target_name, material_path)
    warnings = _build_name_warnings(valid, message)
    if base_color is not None:
        warnings.append("当前实现仅创建材质资产，未自动写入 BaseColor 节点图。")

    script = f"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.MaterialFactoryNew()
material = asset_tools.create_asset(
    {_python_literal(target_name)},
    {_python_literal(target_dir)},
    unreal.Material,
    factory,
)
if material is None:
    raise RuntimeError("材质创建失败")

unreal.EditorAssetLibrary.save_asset({_python_literal(full_path)})
"""
    return _run_editor_python_tool(
        script,
        f"材质创建成功: {full_path}",
        "创建材质失败",
        data={
            "material_name": target_name,
            "material_path": full_path,
            "base_color": base_color,
        },
        warnings=warnings,
    )


def create_material_instance(
    instance_name: str,
    parent_material: str,
    instance_path: str = None,
    scalar_params: dict = None,
    vector_params: dict = None,
) -> dict:
    """创建材质实例并可选写入材质参数。"""
    from naming import make_full_asset_path, validate_asset_name

    valid, corrected_name, message = validate_asset_name("material_instance", instance_name)
    target_name = corrected_name if corrected_name else instance_name
    target_dir = instance_path or "/Game/Materials/Instances"
    full_path = make_full_asset_path("material_instance", target_name, instance_path)
    warnings = _build_name_warnings(valid, message)

    script = f"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.MaterialInstanceConstantFactoryNew()
instance = asset_tools.create_asset(
    {_python_literal(target_name)},
    {_python_literal(target_dir)},
    unreal.MaterialInstanceConstant,
    factory,
)
if instance is None:
    raise RuntimeError("材质实例创建失败")

parent_material = unreal.EditorAssetLibrary.load_asset({_python_literal(parent_material)})
if parent_material is None:
    raise RuntimeError("父材质不存在")

instance.set_editor_property("parent", parent_material)

for param_name, param_value in {_python_literal(scalar_params or {})}.items():
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance,
        param_name,
        float(param_value),
    )

for param_name, param_value in {_python_literal(vector_params or {})}.items():
    if not isinstance(param_value, (list, tuple)) or len(param_value) != 4:
        raise RuntimeError(f"向量参数 {{param_name}} 必须是 4 元数组")
    color = unreal.LinearColor(*param_value)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance,
        param_name,
        color,
    )

unreal.EditorAssetLibrary.save_asset({_python_literal(full_path)})
"""
    return _run_editor_python_tool(
        script,
        f"材质实例创建成功: {full_path}",
        "创建材质实例失败",
        data={
            "instance_name": target_name,
            "instance_path": full_path,
            "parent_material": parent_material,
            "scalar_params": scalar_params or {},
            "vector_params": vector_params or {},
        },
        warnings=warnings,
    )


def create_widget_blueprint(
    widget_name: str,
    widget_path: str = None,
    parent_class: str = None,
) -> dict:
    """创建 Widget Blueprint。"""
    from naming import make_full_asset_path, validate_asset_name

    valid, corrected_name, message = validate_asset_name("widget", widget_name)
    target_name = corrected_name if corrected_name else widget_name
    target_dir = widget_path or "/Game/UI"
    full_path = make_full_asset_path("widget", target_name, widget_path)
    warnings = _build_name_warnings(valid, message)

    script = f"""
import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.WidgetBlueprintFactory()
widget = asset_tools.create_asset(
    {_python_literal(target_name)},
    {_python_literal(target_dir)},
    unreal.WidgetBlueprint,
    factory,
)
if widget is None:
    raise RuntimeError("Widget Blueprint 创建失败")

unreal.EditorAssetLibrary.save_asset({_python_literal(full_path)})
"""
    return _run_editor_python_tool(
        script,
        f"Widget Blueprint 创建成功: {full_path}",
        "创建 Widget Blueprint 失败",
        data={
            "widget_name": target_name,
            "widget_path": full_path,
            "parent_class": parent_class or "UserWidget",
        },
        warnings=warnings,
    )


def set_blueprint_defaults(blueprint_path: str, property_name: str, property_value: Any) -> dict:
    """设置 Blueprint 默认值。"""
    script = f"""
import unreal

def resolve_value(value):
    if isinstance(value, str) and value.startswith("/"):
        blueprint_class = unreal.EditorAssetLibrary.load_blueprint_class(value)
        if blueprint_class is not None:
            return blueprint_class

        if not value.endswith("_C"):
            blueprint_class = unreal.EditorAssetLibrary.load_blueprint_class(value + "_C")
            if blueprint_class is not None:
                return blueprint_class

        loaded_class = unreal.load_class(None, value)
        if loaded_class is not None:
            return loaded_class

        loaded_asset = unreal.EditorAssetLibrary.load_asset(value)
        if loaded_asset is not None:
            return loaded_asset
    return value

blueprint_class = unreal.EditorAssetLibrary.load_blueprint_class({_python_literal(blueprint_path)})
if blueprint_class is None and not {_python_literal(blueprint_path)}.endswith("_C"):
    blueprint_class = unreal.EditorAssetLibrary.load_blueprint_class({_python_literal(blueprint_path + "_C")})
if blueprint_class is None:
    raise RuntimeError("Blueprint 类不存在")

default_object = unreal.get_default_object(blueprint_class)
resolved_value = resolve_value({_python_literal(property_value)})
default_object.set_editor_property({_python_literal(property_name)}, resolved_value)
unreal.EditorAssetLibrary.save_asset({_python_literal(blueprint_path)})
"""
    return _run_editor_python_tool(
        script,
        f"Blueprint 默认值设置成功: {blueprint_path}.{property_name}",
        "设置 Blueprint 默认值失败",
        data={
            "blueprint_path": blueprint_path,
            "property_name": property_name,
            "property_value": property_value,
        },
    )


def configure_gamemode_bp(
    gamemode_path: str,
    default_pawn_class: str = None,
    player_controller_class: str = None,
    game_state_class: str = None,
    player_state_class: str = None,
    hud_class: str = None,
) -> dict:
    """批量配置 GameMode Blueprint 的核心类引用。"""
    property_mapping = {
        "DefaultPawnClass": default_pawn_class,
        "PlayerControllerClass": player_controller_class,
        "GameStateClass": game_state_class,
        "PlayerStateClass": player_state_class,
        "HUDClass": hud_class,
    }

    applied = []
    errors = []

    for property_name, property_value in property_mapping.items():
        if property_value is None:
            continue

        result = set_blueprint_defaults(gamemode_path, property_name, property_value)
        if result.get("status") != "success":
            errors.extend(result.get("errors", []))
        else:
            applied.append(
                {
                    "property_name": property_name,
                    "property_value": property_value,
                }
            )

    if errors:
        return make_response(
            "failed",
            f"GameMode Blueprint 配置失败: {gamemode_path}",
            data={"applied": applied},
            errors=errors,
        )

    return make_response(
        "success",
        f"GameMode Blueprint 配置成功: {gamemode_path}",
        data={
            "gamemode_path": gamemode_path,
            "applied": applied,
        },
    )


def configure_world_settings(gamemode_override: str = None, default_gamemode: str = None) -> dict:
    """通过 RC API 设置当前关卡 World Settings。"""
    if gamemode_override is None and default_gamemode is None:
        return make_response(
            "validation_error",
            "至少提供一个 World Settings 配置项",
            errors=["INVALID_ARGS: gamemode_override/default_gamemode 至少提供一个"],
        )

    try:
        import rc_channel

        if not rc_channel.check_connection():
            raise RuntimeError("Remote Control API 未连接")

        search_result = rc_channel.search_actors(query="WorldSettings", class_name="WorldSettings")
        object_path = _extract_object_path(search_result)
        if not object_path:
            raise RuntimeError("未找到 WorldSettings Actor 路径")

        writes = []
        if gamemode_override is not None:
            result = rc_channel.set_property(
                object_path,
                "DefaultGameMode",
                gamemode_override,
                generate_transaction=True,
            )
            writes.append({"property": "DefaultGameMode", "result": result})

        if default_gamemode is not None:
            result = rc_channel.set_property(
                object_path,
                "GlobalDefaultGameMode",
                default_gamemode,
                generate_transaction=True,
            )
            writes.append({"property": "GlobalDefaultGameMode", "result": result})

        return make_response(
            "success",
            "World Settings 配置成功",
            data={
                "world_settings_path": object_path,
                "writes": writes,
            },
        )
    except Exception as exc:
        return make_response(
            "failed",
            f"配置 World Settings 失败: {str(exc)}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def open_level(level_path: str) -> dict:
    """打开指定关卡。"""
    script = f"""
import unreal

opened = unreal.EditorLevelLibrary.load_level({_python_literal(level_path)})
if opened is False:
    raise RuntimeError("打开关卡返回 False")
"""
    return _run_editor_python_tool(
        script,
        f"关卡打开成功: {level_path}",
        "打开关卡失败",
        data={"level_path": level_path},
    )


def save_all() -> dict:
    """保存所有脏包。"""
    script = """
import unreal

saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
if saved is False:
    raise RuntimeError("保存脏包返回 False")
"""
    return _run_editor_python_tool(
        script,
        "保存所有脏资产成功",
        "保存所有脏资产失败",
    )


# ============================================================
# Layer 1 Service: 编辑器级服务工具
# ============================================================

def capture_screenshot(output_path: str = None) -> dict:
    """截取当前编辑器视口截图。"""
    target_path = output_path or "Saved/Screenshots/mcp_screenshot.png"
    script = f"""
import unreal

unreal.AutomationLibrary.take_high_res_screenshot(
    1920,
    1080,
    {_python_literal(target_path)},
)
"""
    return _run_editor_python_tool(
        script,
        f"截图完成: {target_path}",
        "截图失败",
        data={"output_path": target_path},
    )


def save_named_assets(asset_paths: list) -> dict:
    """保存指定资产列表。"""
    if not asset_paths:
        return make_response(
            "validation_error",
            "asset_paths 不能为空",
            errors=["INVALID_ARGS: asset_paths 不能为空"],
        )

    script = f"""
import unreal

failed_assets = []
for asset_path in {_python_literal(asset_paths)}:
    saved = unreal.EditorAssetLibrary.save_asset(asset_path)
    if saved is False:
        failed_assets.append(asset_path)

if failed_assets:
    raise RuntimeError("以下资产保存失败: " + ", ".join(failed_assets))
"""
    return _run_editor_python_tool(
        script,
        "指定资产保存成功",
        "保存指定资产失败",
        data={"asset_paths": asset_paths},
    )


def build_project(target: str = None) -> dict:
    """在编辑器内触发编译相关控制台命令。"""
    target_name = target or "Editor"
    command = "CompileAllBlueprints"
    script = _build_execute_console_command_script(command)
    return _run_editor_python_tool(
        script,
        f"编译命令已触发: {target_name}",
        "触发编译命令失败",
        data={
            "target": target_name,
            "command": command,
        },
    )


def run_automation_tests(test_filter: str = None) -> dict:
    """在编辑器内触发 Automation Test。"""
    target_filter = test_filter or "Project.AgentBridge"
    command = f"Automation RunTests {target_filter}"
    script = _build_execute_console_command_script(command)
    return _run_editor_python_tool(
        script,
        f"Automation Test 已触发: {target_filter}",
        "触发 Automation Test 失败",
        data={
            "test_filter": target_filter,
            "command": command,
        },
    )


def run_automation_tests_via_cpp_plugin(test_filter: str = None) -> dict:
    """通过 C++ Subsystem 触发 Automation Test，避免依赖旧脚本路由。"""
    target_filter = test_filter or "Project.AgentBridge"
    command = f"Automation RunTests {target_filter}"

    try:
        from bridge_core import call_cpp_plugin

        # 直接走项目主干的 C++ Subsystem 通道，规避 /remote/script/run 在当前 RC 配置下缺失的问题。
        editor_result = call_cpp_plugin(
            "RunAutomationTests",
            {
                "Filter": target_filter,
                "ReportPath": "",
            },
        )
        return make_response(
            editor_result.get("status", "failed"),
            editor_result.get("summary", f"Automation Test 触发失败: {target_filter}"),
            data=_merge_editor_result(
                {
                    "test_filter": target_filter,
                    "command": command,
                    "execution_channel": "cpp_plugin",
                },
                editor_result.get("data"),
            ),
            warnings=editor_result.get("warnings", []),
            errors=editor_result.get("errors", []),
        )
    except Exception as exc:
        return make_response(
            "failed",
            f"触发 Automation Test 失败: {str(exc)}",
            data={
                "test_filter": target_filter,
                "command": command,
                "execution_channel": "cpp_plugin",
            },
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def undo_last_transaction() -> dict:
    """撤销上一次编辑器事务。"""
    command = "TRANSACTION UNDO"
    script = _build_execute_console_command_script(command)
    return _run_editor_python_tool(
        script,
        "撤销事务成功",
        "撤销事务失败",
        data={"command": command},
    )


# ============================================================
# Layer 3: 通用兜底
# ============================================================

def run_editor_python(script: str, timeout_ms: int = 30000) -> dict:
    """执行任意 Python Editor Scripting 脚本。"""
    return _run_editor_python_tool(
        script,
        "脚本执行完成",
        "脚本执行失败",
        timeout_ms=timeout_ms,
    )


# ============================================================
# 工具分发
# ============================================================

TOOL_DISPATCH: dict[str, tuple[str, Any]] = {}
TOOL_DISPATCH.update({name: ("query", name) for name in LAYER1_QUERY_TOOLS})
TOOL_DISPATCH.update({name: ("write", name) for name in LAYER1_WRITE_TOOLS})
TOOL_DISPATCH.update(
    {
        "capture_screenshot": ("local", capture_screenshot),
        "save_named_assets": ("local", save_named_assets),
        "build_project": ("local", build_project),
        "run_automation_tests": ("local", run_automation_tests_via_cpp_plugin),
        "undo_last_transaction": ("local", undo_last_transaction),
        "create_level": ("local", create_level),
        "create_material": ("local", create_material),
        "create_material_instance": ("local", create_material_instance),
        "create_widget_blueprint": ("local", create_widget_blueprint),
        "set_blueprint_defaults": ("local", set_blueprint_defaults),
        "configure_gamemode_bp": ("local", configure_gamemode_bp),
        "configure_world_settings": ("local", configure_world_settings),
        "open_level": ("local", open_level),
        "save_all": ("local", save_all),
        "run_editor_python": ("local", run_editor_python),
    }
)
TOOL_DISPATCH.update(
    {
        "compiler_create_session": ("compiler", compiler_tools.compiler_create_session),
        "compiler_root_skill_prepare": ("compiler", compiler_tools.compiler_root_skill_prepare),
        "compiler_root_skill_save": ("compiler", compiler_tools.compiler_root_skill_save),
        "compiler_intake_prepare": ("compiler", compiler_tools.compiler_intake_prepare),
        "compiler_intake_save": ("compiler", compiler_tools.compiler_intake_save),
        "compiler_clarification_prepare": ("compiler", compiler_tools.compiler_clarification_prepare),
        "compiler_clarification_save": ("compiler", compiler_tools.compiler_clarification_save),
        "compiler_skill_graph_prepare": ("compiler", compiler_tools.compiler_skill_graph_prepare),
        "compiler_skill_graph_save": ("compiler", compiler_tools.compiler_skill_graph_save),
        "compiler_plan_prepare": ("compiler", compiler_tools.compiler_plan_prepare),
        "compiler_plan_save": ("compiler", compiler_tools.compiler_plan_save),
        "compiler_get_session_status": ("compiler", compiler_tools.compiler_get_session_status),
        "compiler_stage4_node_prepare": ("compiler", compiler_tools.compiler_stage4_node_prepare),
        "compiler_stage4_node_save": ("compiler", compiler_tools.compiler_stage4_node_save),
        "compiler_skill_synthesis_prepare": ("compiler", compiler_tools.compiler_skill_synthesis_prepare),
        "compiler_skill_synthesis_save": ("compiler", compiler_tools.compiler_skill_synthesis_save),
        "demo_story_fetch": ("compiler", compiler_tools.demo_story_fetch),
        "demo_story_submit": ("compiler", compiler_tools.demo_story_submit),
    }
)
TOOL_DISPATCH.update(
    {
        "evidence_load_manifest": ("evidence", evidence_tools.evidence_load_manifest),
        "evidence_load_screenshots": ("evidence", evidence_tools.evidence_load_screenshots),
        "evidence_load_logs": ("evidence", evidence_tools.evidence_load_logs),
        "evidence_load_report": ("evidence", evidence_tools.evidence_load_report),
        "evidence_judge_acceptance": ("evidence", evidence_tools.evidence_judge_acceptance),
        "evidence_decide_escalation": ("evidence", evidence_tools.evidence_decide_escalation),
        "evidence_export_summary": ("evidence", evidence_tools.evidence_export_summary),
        "evidence_list_runs": ("evidence", evidence_tools.evidence_list_runs),
        "evidence_compare_runs": ("evidence", evidence_tools.evidence_compare_runs),
        "evidence_create_batch": ("evidence", evidence_tools.evidence_create_batch),
        "evidence_promote_run": ("evidence", evidence_tools.evidence_promote_run),
    }
)


def dispatch_tool(tool_name: str, arguments: dict | None) -> dict:
    """根据 TOOL_DISPATCH 路由表分发工具调用。"""
    route = TOOL_DISPATCH.get(tool_name)
    if route is None:
        return make_response(
            "failed",
            f"未知工具: {tool_name}",
            errors=[f"TOOL_NOT_FOUND: {tool_name}"],
        )

    kind, target = route
    safe_arguments = arguments or {}

    try:
        if kind == "query":
            return wrap_bridge_query(target, **safe_arguments)
        if kind == "write":
            return wrap_bridge_write(target, **safe_arguments)
        if kind == "local":
            return target(**safe_arguments)
        if kind == "compiler":
            return target(**safe_arguments)
        if kind == "evidence":
            return target(**safe_arguments)

        return make_response(
            "failed",
            f"未知路由类型: {kind}",
            errors=[f"TOOL_EXECUTION_FAILED: 未知路由类型 {kind}"],
        )
    except Exception as exc:
        return make_response(
            "failed",
            f"工具执行失败: {tool_name}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


# ============================================================
# MCP Server 注册
# ============================================================

def create_mcp_server():
    """创建并注册 AgentBridge MCP Server。"""
    from mcp import types
    from mcp.server.lowlevel import Server

    server = Server("agentbridge")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        """列出全部工具定义。"""
        return [
            types.Tool(
                name=name,
                description=tool_def.get("description"),
                inputSchema=to_json_schema(tool_def),
            )
            for name, tool_def in ALL_TOOLS.items()
        ]

    @server.call_tool()
    async def handle_call_tool(tool_name: str, arguments: dict):
        """在线程池中执行同步工具，避免阻塞 MCP 事件循环。"""
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, dispatch_tool, tool_name, arguments or {})
        text = json.dumps(result, ensure_ascii=False, indent=2)
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)],
            structuredContent=result,
            isError=result.get("status") == "failed",
        )

    return server


async def main():
    """以 stdio 方式运行 MCP Server。"""
    from mcp.server.stdio import stdio_server

    server = create_mcp_server()
    init_options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    asyncio.run(main())
