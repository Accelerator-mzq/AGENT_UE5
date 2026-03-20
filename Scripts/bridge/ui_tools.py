"""
ui_tools.py
===========
AGENT + UE5 可操作層 — L3 UI 工具（Automation Driver 执行后端）。

工具优先级：L1 语义工具 > L2 编辑器服务工具 > L3 UI 工具。
仅当 L1 语义工具无法覆盖时使用。

三通道实现：
  通道 C: C++ Plugin（推荐，AgentBridgeSubsystem 的 UITool 接口）
  通道 A/B: 不适用（L3 依赖 Automation Driver，只能在 Editor 进程内执行）
  Mock: 返回模拟成功响应

每次 L3 操作后，必须通过 L1 工具做独立验证。
L3 返回值与 L1 验证返回值做交叉比对——两者一致才判定 success。

使用判定条件（全部满足才允许使用）：
  1. L1 无对应 API
  2. 操作可结构化（路径/名称，非坐标）
  3. 结果可验证（有对应的 L1 读回接口）
  4. 操作可逆或低风险
  5. Spec 中显式标注 execution_method: ui_tool
  6. 已封装为 AgentBridge 接口
"""

from __future__ import annotations
from typing import Optional, Dict, Any, List

from bridge_core import (
    get_channel, BridgeChannel,
    make_response, make_error, safe_execute,
    validate_required_string, call_cpp_plugin,
)


# ============================================================
# L3 → C++ Plugin 函数名映射
# ============================================================

_CPP_UI_TOOL_MAP = {
    "click_detail_panel_button": "ClickDetailPanelButton",
    "type_in_detail_panel_field": "TypeInDetailPanelField",
    "drag_asset_to_viewport": "DragAssetToViewport",
    "is_automation_driver_available": "IsAutomationDriverAvailable",
}


# ============================================================
# 通道分发
# ============================================================

def _dispatch_ui_tool(tool_name: str, cpp_params: Optional[Dict] = None) -> dict:
    """L3 UI 工具的通道分发。

    L3 工具依赖 Automation Driver，只能在 Editor 进程内执行。
    因此只支持通道 C（C++ Plugin）和 Mock 模式。
    通道 A/B 不适用——返回错误提示。
    """
    channel = get_channel()

    if channel == BridgeChannel.MOCK:
        return _mock_ui_tool_response(tool_name, cpp_params)

    if channel == BridgeChannel.CPP_PLUGIN:
        cpp_func = _CPP_UI_TOOL_MAP.get(tool_name)
        if not cpp_func:
            return make_response(
                status="failed",
                summary=f"No C++ mapping for L3 tool: {tool_name}",
                data={},
                errors=[make_error("INVALID_ARGS", f"Unknown L3 tool: {tool_name}")]
            )
        return call_cpp_plugin(cpp_func, cpp_params)

    # 通道 A / B 不支持 L3
    return make_response(
        status="failed",
        summary=f"L3 UI tools require channel CPP_PLUGIN, current: {channel.value}",
        data={"tool_layer": "L3_UITool"},
        errors=[make_error("INVALID_ARGS",
                          "L3 UI tools depend on Automation Driver and can only run "
                          "via C++ Plugin (channel CPP_PLUGIN). "
                          "Use set_channel(BridgeChannel.CPP_PLUGIN) first.")]
    )


def _mock_ui_tool_response(tool_name: str, params: Optional[Dict] = None) -> dict:
    """Mock 模式下的 L3 工具返回值。"""
    data = {
        "operation": tool_name,
        "executed": True,
        "ui_idle_after": True,
        "duration_seconds": 0.5,
        "tool_layer": "L3_UITool",
    }
    if params:
        data.update({k: v for k, v in params.items() if isinstance(v, (str, int, float, bool))})
    return make_response(
        status="success",
        summary=f"Mock L3: {tool_name}",
        data=data,
    )


# ============================================================
# L3 接口
# ============================================================

def is_automation_driver_available() -> bool:
    """检查 Automation Driver 是否可用。

    返回 bool，不是 dict（这是查询性质的辅助函数）。
    Mock 模式下返回 True。
    """
    channel = get_channel()
    if channel == BridgeChannel.MOCK:
        return True
    if channel == BridgeChannel.CPP_PLUGIN:
        resp = call_cpp_plugin("IsAutomationDriverAvailable")
        # RC API 返回 bool 类型的 ReturnValue
        if isinstance(resp, bool):
            return resp
        if isinstance(resp, dict) and "ReturnValue" in resp:
            return bool(resp["ReturnValue"])
        return False
    return False


def click_detail_panel_button(
    actor_path: str,
    button_label: str,
    dry_run: bool = False,
) -> dict:
    """在 Actor 的 Detail Panel 中点击按钮。

    L3 UI 工具——仅当无直接 API 时使用。
    调用后必须通过 L1 get_actor_state 或 get_component_state 验证状态变更。

    参数：
        actor_path: 目标 Actor 完整路径
        button_label: 按钮显示文本（精确匹配）
        dry_run: 仅校验参数和 Driver 可用性

    返回：
        FBridgeResponse 格式（tool_layer: L3_UITool）
    """
    err = validate_required_string(actor_path, "actor_path")
    if err:
        return err
    err = validate_required_string(button_label, "button_label")
    if err:
        return err

    return _dispatch_ui_tool("click_detail_panel_button", {
        "ActorPath": actor_path,
        "ButtonLabel": button_label,
        "bDryRun": dry_run,
    })


def type_in_detail_panel_field(
    actor_path: str,
    property_path: str,
    value: str,
    dry_run: bool = False,
) -> dict:
    """在 Detail Panel 的属性输入框中输入值。

    L3 UI 工具——用于非反射属性或需要 UI 触发的属性。
    调用后必须通过 L1 get_actor_state 验证属性值变更。

    参数：
        actor_path: 目标 Actor 完整路径
        property_path: 属性路径（如 "StaticMeshComponent.StaticMesh"）
        value: 要输入的值（字符串形式）
        dry_run: 仅校验参数和 Driver 可用性
    """
    err = validate_required_string(actor_path, "actor_path")
    if err:
        return err
    err = validate_required_string(property_path, "property_path")
    if err:
        return err
    err = validate_required_string(value, "value")
    if err:
        return err

    return _dispatch_ui_tool("type_in_detail_panel_field", {
        "ActorPath": actor_path,
        "PropertyPath": property_path,
        "Value": value,
        "bDryRun": dry_run,
    })


def drag_asset_to_viewport(
    asset_path: str,
    drop_location: list,
    dry_run: bool = False,
) -> dict:
    """将 Content Browser 中的资产拖拽到 Viewport 指定位置。

    L3 UI 工具——走 Editor 原生 OnDropped 流程（触发自动碰撞/命名/贴地）。
    与 L1 spawn_actor 的区别：spawn_actor 不触发这些 Editor 默认行为。
    调用后必须通过 L1 list_level_actors + get_actor_state 验证。

    参数：
        asset_path: 资产路径（如 /Game/Meshes/SM_Chair）
        drop_location: 世界坐标 [x, y, z]
        dry_run: 仅校验参数和 Driver 可用性
    """
    err = validate_required_string(asset_path, "asset_path")
    if err:
        return err

    if not isinstance(drop_location, (list, tuple)) or len(drop_location) != 3:
        return make_response(
            status="validation_error",
            summary="drop_location must be [x, y, z]",
            data={},
            errors=[make_error("INVALID_ARGS", "drop_location must be a list of 3 numbers")]
        )

    return _dispatch_ui_tool("drag_asset_to_viewport", {
        "AssetPath": asset_path,
        "DropLocation": {
            "X": drop_location[0],
            "Y": drop_location[1],
            "Z": drop_location[2],
        },
        "bDryRun": dry_run,
    })


# ============================================================
# L3 → L1 交叉比对辅助（Python 端）
# ============================================================

def cross_verify_ui_operation(
    l3_response: dict,
    l1_verify_func,
    l1_verify_args: Optional[dict] = None,
) -> dict:
    """L3→L1 交叉比对：拿 L3 返回值与 L1 独立读回做比对。

    参数：
        l3_response: L3 UI 工具的返回值（dict）
        l1_verify_func: L1 验证函数（callable，如 query_tools.get_actor_state）
        l1_verify_args: L1 验证函数的参数（dict，如 {"actor_path": "xxx"}）

    返回：
        {
            "final_status": "success" / "mismatch" / "failed",
            "consistent": bool,
            "l3_response": {...},
            "l1_response": {...},
            "mismatches": ["field: L3=x, L1=y", ...]
        }
    """
    result = {
        "final_status": "failed",
        "consistent": False,
        "l3_response": l3_response,
        "l1_response": {},
        "mismatches": [],
    }

    # L3 本身失败
    if l3_response.get("status") not in ("success", "warning"):
        result["mismatches"].append(f"L3 operation failed: {l3_response.get('summary', '')}")
        return result

    # 执行 L1 独立读回
    try:
        if l1_verify_args:
            l1_response = l1_verify_func(**l1_verify_args)
        else:
            l1_response = l1_verify_func()
    except Exception as e:
        result["mismatches"].append(f"L1 verification raised exception: {e}")
        return result

    result["l1_response"] = l1_response

    # L1 失败
    if l1_response.get("status") not in ("success", "warning"):
        result["mismatches"].append(f"L1 verification failed: {l1_response.get('summary', '')}")
        return result

    # 两者都成功——做字段级比对
    l3_data = l3_response.get("data", {})
    l1_data = l1_response.get("data", {})
    mismatches = []

    # DragAssetToViewport 特殊比对：
    # 检查 L3 声称的 actors_created 是否在 L1 的 actor 列表中
    if "actors_created" in l3_data and l3_data["actors_created"] > 0:
        l3_created = l3_data.get("created_actors", [])
        l1_actors = l1_data.get("actors", [])
        l1_paths = {a.get("actor_path", "") for a in l1_actors} if isinstance(l1_actors, list) else set()

        for ca in l3_created:
            ca_path = ca.get("actor_path", "") if isinstance(ca, dict) else ""
            if ca_path and ca_path not in l1_paths:
                mismatches.append(f"L3 created actor '{ca_path}' not found in L1 actor list")

    result["mismatches"] = mismatches
    result["consistent"] = len(mismatches) == 0
    result["final_status"] = "success" if len(mismatches) == 0 else "mismatch"

    return result
