"""
Phase 8 资产生成脚本。

用途：
1. 创建 `/Game/Maps/L_MonopolyBoard`
2. 创建 5 个 Widget Blueprint 壳资产
3. 给地图设置 Monopoly 专用 GameMode
4. 写出结构化证据报告，便于后续验收引用
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import unreal


MAP_ASSET_PATH = "/Game/Maps/L_MonopolyBoard"
MAP_DIR = "/Game/Maps"
UI_DIR = "/Game/UI"
REPORT_PATH = os.path.join(
    unreal.Paths.project_dir(),
    "ProjectState",
    "Reports",
    "phase8_m3_asset_generation_20260405.json",
)

WIDGET_SPECS = [
    ("WBP_GameHUD", "MGameHUDWidget"),
    ("WBP_DicePopup", "MPopupWidget"),
    ("WBP_BuyPopup", "MPopupWidget"),
    ("WBP_InfoPopup", "MPopupWidget"),
    ("WBP_JailPopup", "MPopupWidget"),
]


def log(message: str) -> None:
    unreal.log(f"[Phase8Assets] {message}")


def ensure_directory(asset_dir: str) -> None:
    if not unreal.EditorAssetLibrary.does_directory_exist(asset_dir):
        unreal.EditorAssetLibrary.make_directory(asset_dir)


def delete_asset_if_exists(asset_path: str) -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)


def set_editor_property_safe(target, property_names, value) -> str:
    for property_name in property_names:
        try:
            target.set_editor_property(property_name, value)
            return property_name
        except Exception:
            continue
    return ""


def create_widget_blueprint(asset_name: str, parent_class_name: str) -> dict:
    asset_path = f"{UI_DIR}/{asset_name}"
    delete_asset_if_exists(asset_path)

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    factory = unreal.WidgetBlueprintFactory()
    parent_class = getattr(unreal, parent_class_name).static_class()
    parent_property = set_editor_property_safe(factory, ["ParentClass", "parent_class"], parent_class)

    widget_asset = asset_tools.create_asset(asset_name, UI_DIR, unreal.WidgetBlueprint, factory)
    if widget_asset is None:
        raise RuntimeError(f"创建 Widget Blueprint 失败: {asset_path}")

    unreal.EditorAssetLibrary.save_asset(asset_path, only_if_is_dirty=False)
    return {
        "asset_path": asset_path,
        "parent_class": parent_class_name,
        "factory_parent_property": parent_property or "unresolved",
    }


def create_level() -> dict:
    delete_asset_if_exists(MAP_ASSET_PATH)
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_editor.new_level(MAP_ASSET_PATH):
        raise RuntimeError(f"创建地图失败: {MAP_ASSET_PATH}")

    editor_world_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_world_subsystem.get_editor_world()
    if world is None:
        raise RuntimeError("无法获取当前编辑器 World")

    world_settings = world.get_world_settings()
    game_mode_class = unreal.MMonopolyGameMode.static_class()
    property_name = set_editor_property_safe(world_settings, ["default_game_mode", "DefaultGameMode"], game_mode_class)

    unreal.EditorAssetLibrary.save_asset(MAP_ASSET_PATH, only_if_is_dirty=False)

    return {
        "map_path": MAP_ASSET_PATH,
        "world_settings_property": property_name or "unresolved",
        "spawned_actors": [],
    }


def write_report(payload: dict) -> None:
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump(payload, report_file, ensure_ascii=False, indent=2)


def main() -> None:
    ensure_directory(MAP_DIR)
    ensure_directory(UI_DIR)

    report = {
        "generated_at": datetime.now().isoformat(),
        "map": {},
        "widgets": [],
        "status": "failed",
        "errors": [],
    }

    try:
        log("开始创建地图")
        report["map"] = create_level()

        log("开始创建 Widget Blueprint")
        for asset_name, parent_class_name in WIDGET_SPECS:
            report["widgets"].append(create_widget_blueprint(asset_name, parent_class_name))

        report["status"] = "success"
    except Exception as exc:
        report["errors"].append(str(exc))
        unreal.log_error(f"[Phase8Assets] {exc}")
        raise
    finally:
        write_report(report)
        log(f"报告已写入: {REPORT_PATH}")


if __name__ == "__main__":
    main()
