"""
AgentBridge MCP Server — 主入口

通过 stdio 传输协议暴露 UE5 Editor 能力给 Claude Code。

架构：
  Claude Code (stdio) → MCP Server → Bridge 三通道 → UE5 Editor

启动方式：
  由 .mcp.json 配置，Claude Code 自动通过 stdio 启动。

依赖：
  - mcp (pip install mcp)
  - Plugins/AgentBridge/Scripts/bridge/ （已有 Bridge 工具）
"""

import sys
import os
import json
import logging

# 添加 Bridge 模块路径
BRIDGE_DIR = os.path.join(os.path.dirname(__file__), '..', 'Scripts', 'bridge')
sys.path.insert(0, os.path.abspath(BRIDGE_DIR))

# 添加本目录
MCP_DIR = os.path.dirname(__file__)
sys.path.insert(0, MCP_DIR)

logger = logging.getLogger("agentbridge-mcp")


def make_response(status: str, summary: str, data=None, warnings=None, errors=None) -> dict:
    """构造统一响应格式（与 tool_contract_v0_1.md §2.2 一致）"""
    return {
        "status": status,
        "summary": summary,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or []
    }


# ============================================================
# Layer 1: Bridge 已有工具包装
# ============================================================

def wrap_bridge_query(tool_name: str, **kwargs) -> dict:
    """包装 Bridge 查询工具调用"""
    try:
        import query_tools
        func = getattr(query_tools, tool_name, None)
        if func is None:
            return make_response("failed", f"未找到查询工具: {tool_name}",
                                 errors=[f"TOOL_NOT_FOUND: {tool_name}"])
        return func(**kwargs)
    except Exception as e:
        return make_response("failed", f"查询工具执行失败: {tool_name}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])


def wrap_bridge_write(tool_name: str, **kwargs) -> dict:
    """包装 Bridge 写入工具调用"""
    try:
        import write_tools
        func = getattr(write_tools, tool_name, None)
        if func is None:
            return make_response("failed", f"未找到写入工具: {tool_name}",
                                 errors=[f"TOOL_NOT_FOUND: {tool_name}"])
        return func(**kwargs)
    except Exception as e:
        return make_response("failed", f"写入工具执行失败: {tool_name}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])


# ============================================================
# Layer 2: Channel A 资产创建工具
# ============================================================

def create_level(level_name: str, level_path: str = None, template: str = None) -> dict:
    """创建新关卡（通过 Python Editor Scripting）"""
    from naming import validate_asset_name, make_full_asset_path
    valid, corrected, msg = validate_asset_name("level", level_name)
    if not valid:
        level_name = corrected
        logger.warning(f"关卡名称已自动修正: {msg}")

    full_path = make_full_asset_path("level", level_name, level_path)

    # 实际执行由 py_channel 处理
    try:
        from py_channel import execute_editor_python
        script = f"""
import unreal
editor = unreal.EditorLevelLibrary
# 创建新关卡
editor.new_level('{full_path}')
"""
        result = execute_editor_python(script)
        return make_response("success", f"关卡 {level_name} 创建成功",
                             data={"level_path": full_path})
    except Exception as e:
        return make_response("failed", f"创建关卡失败: {str(e)}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])


def create_material(material_name: str, material_path: str = None,
                    base_color: list = None) -> dict:
    """创建材质母版"""
    from naming import validate_asset_name, make_full_asset_path
    valid, corrected, msg = validate_asset_name("material", material_name)
    if not valid:
        material_name = corrected

    full_path = make_full_asset_path("material", material_name, material_path)

    try:
        from py_channel import execute_editor_python
        color_str = str(base_color) if base_color else "[1,1,1,1]"
        script = f"""
import unreal
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.MaterialFactoryNew()
material = asset_tools.create_asset('{material_name}', '{material_path or "/Game/Materials"}', unreal.Material, factory)
"""
        result = execute_editor_python(script)
        return make_response("success", f"材质 {material_name} 创建成功",
                             data={"material_path": full_path})
    except Exception as e:
        return make_response("failed", f"创建材质失败: {str(e)}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])


def create_widget_blueprint(widget_name: str, widget_path: str = None,
                            parent_class: str = None) -> dict:
    """创建 Widget Blueprint"""
    from naming import validate_asset_name, make_full_asset_path
    valid, corrected, msg = validate_asset_name("widget", widget_name)
    if not valid:
        widget_name = corrected

    full_path = make_full_asset_path("widget", widget_name, widget_path)

    try:
        from py_channel import execute_editor_python
        script = f"""
import unreal
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.WidgetBlueprintFactory()
widget = asset_tools.create_asset('{widget_name}', '{widget_path or "/Game/UI"}', unreal.WidgetBlueprint, factory)
"""
        result = execute_editor_python(script)
        return make_response("success", f"Widget {widget_name} 创建成功",
                             data={"widget_path": full_path})
    except Exception as e:
        return make_response("failed", f"创建 Widget 失败: {str(e)}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])


# ============================================================
# Layer 3: 通用兜底
# ============================================================

def run_editor_python(script: str, timeout_ms: int = 30000) -> dict:
    """执行任意 Python Editor Scripting 脚本"""
    try:
        from py_channel import execute_editor_python
        result = execute_editor_python(script, timeout_ms=timeout_ms)
        return make_response("success", "脚本执行完成", data={"result": result})
    except Exception as e:
        return make_response("failed", f"脚本执行失败: {str(e)}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])


# ============================================================
# MCP Server 注册（骨架）
# ============================================================

def create_mcp_server():
    """
    创建 MCP Server 实例。
    实际 MCP SDK 集成在 M2 实施时完成。
    此处为骨架定义，列出所有工具注册点。
    """
    # TODO: M2 阶段接入 mcp SDK
    # from mcp.server import Server
    # server = Server("agentbridge")
    #
    # 注册 Layer 1 查询工具
    # for tool_name in LAYER1_QUERY_TOOLS:
    #     server.register_tool(tool_name, wrap_bridge_query)
    #
    # 注册 Layer 1 写入工具
    # for tool_name in LAYER1_WRITE_TOOLS:
    #     server.register_tool(tool_name, wrap_bridge_write)
    #
    # 注册 Layer 2 资产创建工具
    # server.register_tool("create_level", create_level)
    # server.register_tool("create_material", create_material)
    # server.register_tool("create_widget_blueprint", create_widget_blueprint)
    # ...
    #
    # 注册 Layer 3 兜底
    # server.register_tool("run_editor_python", run_editor_python)
    #
    # return server
    pass


if __name__ == "__main__":
    from tool_definitions import ALL_TOOLS, TOOL_COUNT
    print(f"AgentBridge MCP Server — {TOOL_COUNT} 个工具已定义")
    print("Layer 1 (Bridge):  7 query + 6 write + 5 service = 18")
    print("Layer 2 (Assets):  9 tools")
    print("Layer 3 (Fallback): 1 tool")
    print(f"Total: {TOOL_COUNT}")
    print("\n工具列表:")
    for name, defn in ALL_TOOLS.items():
        print(f"  {name}: {defn['description']}")
