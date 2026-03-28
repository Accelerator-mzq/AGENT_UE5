import json
import os
import traceback

import unreal


# 说明：
# 1. 本脚本通过 UE 官方 -ExecutePythonScript= 入口执行。
# 2. 目标是创建 Task15 所需的 Functional Test 地图，并放置 AAgentBridgeFunctionalTest。
# 3. 脚本会输出结构化 JSON 报告，便于后续审计与回归复跑。

MAP_PATH = "/Game/Tests/FTEST_WarehouseDemo"
PLUGIN_RELATIVE_PATH = os.path.join("Plugins", "AgentBridge")
ACTOR_CLASS_PATH = "/Script/AgentBridgeTests.AgentBridgeFunctionalTest"
REPORT_RELATIVE_PATH = os.path.join(
    PLUGIN_RELATIVE_PATH,
    "reports",
    "task15_evidence_2026-03-26",
    "task15_functional_map_creation_report_2026-03-26.json",
)


def _ensure_dir_for_file(file_path: str) -> None:
    os.makedirs(os.path.dirname(file_path), exist_ok=True)


def _set_editor_property_with_fallbacks(target, candidates, value):
    errors = []
    for name in candidates:
        try:
            target.set_editor_property(name, value)
            return name
        except Exception as exc:  # noqa: BLE001 - UE Python 异常类型并不稳定
            errors.append(f"{name}: {exc}")
    raise RuntimeError(
        f"无法设置属性，候选={candidates}，错误={'; '.join(errors)}"
    )


def main():
    project_dir = unreal.Paths.project_dir()
    report_path = os.path.join(project_dir, REPORT_RELATIVE_PATH)
    _ensure_dir_for_file(report_path)

    result = {
        "status": "failed",
        "map_path": MAP_PATH,
        "actor_class_path": ACTOR_CLASS_PATH,
        "created": False,
        "deleted_existing_map": False,
        "saved": False,
        "actor_path": "",
        "actor_label": "",
        "property_bindings": {},
        "errors": [],
    }

    try:
        unreal.log("[Task15] 开始创建 Functional Test 地图")

        if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
            result["deleted_existing_map"] = bool(
                unreal.EditorAssetLibrary.delete_asset(MAP_PATH)
            )
            unreal.log(f"[Task15] 已删除旧地图：{MAP_PATH}")

        if not unreal.EditorLevelLibrary.new_level(MAP_PATH):
            raise RuntimeError(f"NewLevel 失败：{MAP_PATH}")

        actor_class = unreal.load_class(None, ACTOR_CLASS_PATH)
        if actor_class is None:
            raise RuntimeError(f"无法加载测试 Actor 类：{ACTOR_CLASS_PATH}")

        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            actor_class,
            unreal.Vector(0.0, 0.0, 0.0),
            unreal.Rotator(0.0, 0.0, 0.0),
        )
        if actor is None:
            raise RuntimeError("SpawnActorFromClass 返回空，未能放置 Functional Test Actor")

        actor.set_actor_label("AgentBridgeFunctionalTest")
        result["actor_label"] = actor.get_actor_label()
        result["actor_path"] = actor.get_path_name()

        # 配置为 Task15 验收要求的“内置模式”
        result["property_bindings"]["spec_path"] = _set_editor_property_with_fallbacks(
            actor,
            ["spec_path", "SpecPath"],
            "",
        )
        result["property_bindings"]["built_in_actor_count"] = _set_editor_property_with_fallbacks(
            actor,
            ["built_in_actor_count", "BuiltInActorCount"],
            5,
        )
        result["property_bindings"]["undo_after_test"] = _set_editor_property_with_fallbacks(
            actor,
            ["undo_after_test", "bUndoAfterTest", "b_undo_after_test"],
            True,
        )
        result["property_bindings"]["location_tolerance"] = _set_editor_property_with_fallbacks(
            actor,
            ["location_tolerance", "LocationTolerance"],
            0.01,
        )
        result["property_bindings"]["rotation_tolerance"] = _set_editor_property_with_fallbacks(
            actor,
            ["rotation_tolerance", "RotationTolerance"],
            0.01,
        )
        result["property_bindings"]["scale_tolerance"] = _set_editor_property_with_fallbacks(
            actor,
            ["scale_tolerance", "ScaleTolerance"],
            0.001,
        )

        result["saved"] = bool(unreal.EditorLevelLibrary.save_current_level())
        if not result["saved"]:
            raise RuntimeError("SaveCurrentLevel 返回 false")

        result["created"] = True
        result["status"] = "success"
        unreal.log(
            f"[Task15] Functional Test 地图创建完成：{MAP_PATH} | Actor={result['actor_path']}"
        )
    except Exception as exc:  # noqa: BLE001 - 需要把全部异常完整落入报告
        result["errors"].append(str(exc))
        result["errors"].append(traceback.format_exc())
        unreal.log_error(f"[Task15] 创建 Functional Test 地图失败：{exc}")
    finally:
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
