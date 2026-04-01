# -*- coding: utf-8 -*-
"""
Orchestrator 端到端系统测试。

对应 SystemTestCases.md 中的 ORC-01 ~ ORC-37。
测试策略分为两层：
1. 纯函数层：直接验证 spec_reader / plan_generator / verifier / report_generator。
2. 主编排层：对 bridge 依赖做最小必要的 monkeypatch，验证编排契约本身。
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest


_EXPECTED_TOP_LEVEL_KEYS = {
    "spec_version",
    "scene",
    "defaults",
    "layout",
    "anchors",
    "actors",
    "validation",
}


@pytest.fixture
def orc_modules(orchestrator_module):
    """按依赖顺序重新加载 orchestrator 相关模块，避免测试间状态污染。"""
    if orchestrator_module not in sys.path:
        sys.path.insert(0, orchestrator_module)

    loaded = {}
    for module_name in ("spec_reader", "plan_generator", "verifier", "report_generator"):
        loaded[module_name] = _import_or_reload(module_name)

    # orchestrator 依赖前面四个模块，最后重载可以保证引用的是最新实现。
    loaded["orchestrator"] = _import_or_reload("orchestrator")
    return SimpleNamespace(**loaded)


@pytest.fixture
def template_spec_path(plugin_root):
    """返回插件自带的场景模板 Spec。"""
    return Path(plugin_root) / "Specs" / "templates" / "scene_spec_template.yaml"


def _import_or_reload(module_name: str):
    """优先重载已导入模块，保证 monkeypatch 回滚后引用一致。"""
    if module_name in sys.modules:
        return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)


def _load_orchestrator_package_module(orchestrator_dir: Path, submodule_name: str):
    """把 orchestrator 目录按包加载，供 handoff_runner 的相对导入使用。"""
    package_name = "_pytest_orchestrator_pkg"
    package_init = orchestrator_dir / "__init__.py"

    if package_name not in sys.modules:
        package_spec = importlib.util.spec_from_file_location(
            package_name,
            package_init,
            submodule_search_locations=[str(orchestrator_dir)],
        )
        package_module = importlib.util.module_from_spec(package_spec)
        sys.modules[package_name] = package_module
        assert package_spec.loader is not None
        package_spec.loader.exec_module(package_module)

    full_module_name = f"{package_name}.{submodule_name}"
    module_path = orchestrator_dir / f"{submodule_name}.py"
    if full_module_name in sys.modules:
        del sys.modules[full_module_name]

    module_spec = importlib.util.spec_from_file_location(full_module_name, module_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[full_module_name] = module
    assert module_spec.loader is not None
    module_spec.loader.exec_module(module)
    return module


def _make_transform(
    location: list[float] | None = None,
    rotation: list[float] | None = None,
    relative_scale3d: list[float] | None = None,
) -> dict:
    """构造最小合法 transform。"""
    return {
        "location": list(location or [0.0, 0.0, 0.0]),
        "rotation": list(rotation or [0.0, 0.0, 0.0]),
        "relative_scale3d": list(relative_scale3d or [1.0, 1.0, 1.0]),
    }


def _make_semantic_actor(
    actor_id: str,
    location: list[float] | None = None,
    execution_method: str | None = "semantic",
) -> dict:
    """构造 L1 semantic Actor。"""
    actor = {
        "id": actor_id,
        "class": "/Script/Engine.StaticMeshActor",
        "object_type": "actor",
        "target_level": "/Game/Maps/TestMap",
        "transform": _make_transform(location=location),
    }
    if execution_method is not None:
        actor["execution_method"] = execution_method
    return actor


def _make_ui_actor(actor_id: str, ui_type: str = "drag_asset_to_viewport") -> dict:
    """构造 L3 ui_tool Actor。"""
    actor = {
        "id": actor_id,
        "object_type": "ui_action",
        "target_level": "/Game/Maps/TestMap",
        "execution_method": "ui_tool",
    }

    if ui_type == "drag_asset_to_viewport":
        actor["class"] = "/Game/Meshes/SM_Chair"
        actor["ui_action"] = {
            "type": "drag_asset_to_viewport",
            "asset_path": "/Game/Meshes/SM_Chair",
            "drop_location": [120.0, 80.0, 0.0],
        }
    elif ui_type == "click_detail_panel_button":
        actor["ui_action"] = {
            "type": "click_detail_panel_button",
            "actor_path": "/Game/Maps/TestMap.TargetActor",
            "button_label": "Add Component",
        }
    elif ui_type == "type_in_detail_panel_field":
        actor["ui_action"] = {
            "type": "type_in_detail_panel_field",
            "actor_path": "/Game/Maps/TestMap.TargetActor",
            "property_path": "transform.location.x",
            "value": "128.0",
        }
    else:
        actor["ui_action"] = {"type": ui_type}

    return actor


def _build_spec(
    actors: list[dict],
    validation_rules: list[dict] | None = None,
) -> dict:
    """构造最小合法 Spec。"""
    return {
        "spec_version": "ue5_agent_spec_v0_1",
        "scene": {
            "scene_id": "pytest_scene",
            "target_level": "/Game/Maps/TestMap",
        },
        "defaults": {},
        "layout": {},
        "anchors": {},
        "actors": actors,
        "validation": {
            "rules": list(validation_rules or []),
        },
    }


def _write_spec(workspace_tmp_path, file_name: str, spec: dict) -> Path:
    """把 Spec 以 JSON 形式写成 .yaml，便于 PyYAML 直接读取。"""
    spec_path = workspace_tmp_path / file_name
    spec_path.write_text(
        json.dumps(spec, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return spec_path


def _make_existing_actor(actor_name: str, actor_path: str | None = None) -> dict:
    """构造当前关卡中已存在的 Actor 信息。"""
    return {
        "actor_name": actor_name,
        "actor_path": actor_path or f"/Game/Maps/TestMap.{actor_name}",
        "class": "/Script/Engine.StaticMeshActor",
    }


def _build_minimal_handoff(actors: list[dict]) -> dict:
    """构造 handoff_runner / run_plan_builder 所需的最小 Handoff。"""
    normalized_actors = []
    for actor in actors:
        normalized_actors.append(
            {
                "actor_name": actor.get("id", actor.get("actor_name", "Actor")),
                "actor_class": actor.get("class", "/Script/Engine.StaticMeshActor"),
                "transform": actor.get("transform", _make_transform()),
            }
        )

    return {
        "handoff_version": "1.0",
        "handoff_id": "handoff.pytest.prototype.001",
        "handoff_mode": "greenfield_bootstrap",
        "status": "approved_for_execution",
        "project_context": {
            "project_name": "Mvpv4TestCodex",
            "game_type": "boardgame",
            "target_platform": "Win64",
        },
        "dynamic_spec_tree": {
            "scene_spec": {
                "actors": normalized_actors,
            }
        },
    }


class TestSpecReader:
    """ORC-01 ~ ORC-06: Spec Reader 测试。"""

    def test_orc01_read_spec_parses_template(self, orc_modules, template_spec_path):
        """ORC-01: read_spec 解析模板 Spec 返回 7 个顶层字段。"""
        spec = orc_modules.spec_reader.read_spec(str(template_spec_path))

        assert set(spec.keys()) == _EXPECTED_TOP_LEVEL_KEYS
        assert len(spec["actors"]) >= 1

    def test_orc02_validate_spec_template_passes(self, orc_modules, template_spec_path):
        """ORC-02: validate_spec 模板通过。"""
        spec = orc_modules.spec_reader.read_spec(str(template_spec_path))
        is_valid, errors = orc_modules.spec_reader.validate_spec(spec)

        assert is_valid is True
        assert errors == []

    def test_orc03_validate_spec_missing_required(self, orc_modules):
        """ORC-03: validate_spec 缺必填字段返回 False。"""
        spec = _build_spec([_make_semantic_actor("MissingSceneId")])
        del spec["scene"]["scene_id"]

        is_valid, errors = orc_modules.spec_reader.validate_spec(spec)

        assert is_valid is False
        assert any("scene.scene_id" in error for error in errors)

    def test_orc04_execution_method_default(self, orc_modules, workspace_tmp_path):
        """ORC-04: execution_method 默认值为 semantic。"""
        actor = _make_semantic_actor("DefaultSemantic", execution_method=None)
        spec_path = _write_spec(
            workspace_tmp_path,
            "orc04_execution_method_default.yaml",
            _build_spec([actor]),
        )

        spec = orc_modules.spec_reader.read_spec(str(spec_path))

        assert spec["actors"][0]["execution_method"] == "semantic"

    def test_orc05_actors_grouping(self, orc_modules):
        """ORC-05: get_actors_by_execution_method 分组。"""
        spec = _build_spec(
            [
                _make_semantic_actor("Semantic_A"),
                _make_semantic_actor("Semantic_B"),
                _make_ui_actor("UI_A", "drag_asset_to_viewport"),
                _make_ui_actor("UI_B", "click_detail_panel_button"),
            ]
        )

        groups = orc_modules.spec_reader.get_actors_by_execution_method(spec)

        assert len(groups["semantic"]) == 2
        assert len(groups["ui_tool"]) == 2

    def test_orc06_duplicate_actor_id(self, orc_modules):
        """ORC-06: 重复 actor_id 校验失败。"""
        spec = _build_spec(
            [
                _make_semantic_actor("DuplicatedActor"),
                _make_semantic_actor("DuplicatedActor"),
            ]
        )

        is_valid, errors = orc_modules.spec_reader.validate_spec(spec)

        assert is_valid is False
        assert any("Actor id 重复" in error for error in errors)


class TestPlanGenerator:
    """ORC-07 ~ ORC-10: Plan Generator 测试。"""

    def test_orc07_empty_existing_all_create(self, orc_modules):
        """ORC-07: 全新场景时 semantic 全部 CREATE，ui_tool 保持 UI_TOOL。"""
        spec_actors = [
            _make_semantic_actor("PlanCreate_A"),
            _make_semantic_actor("PlanCreate_B"),
            _make_ui_actor("PlanUI_A"),
        ]

        plan = orc_modules.plan_generator.generate_plan(spec_actors, existing_actors=[])

        assert plan[0]["action"] == orc_modules.plan_generator.ACTION_CREATE
        assert plan[1]["action"] == orc_modules.plan_generator.ACTION_CREATE
        assert plan[2]["action"] == orc_modules.plan_generator.ACTION_UI_TOOL

    def test_orc08_partial_existing_update(self, orc_modules):
        """ORC-08: 已存在 Actor 走 UPDATE，且 existing_actor_path 正确。"""
        spec_actors = [_make_semantic_actor("ExistingActor")]
        existing_actors = [_make_existing_actor("ExistingActor", "/Game/Maps/TestMap.ExistingActor")]

        plan = orc_modules.plan_generator.generate_plan(spec_actors, existing_actors)

        assert len(plan) == 1
        assert plan[0]["action"] == orc_modules.plan_generator.ACTION_UPDATE
        assert plan[0]["existing_actor_path"] == "/Game/Maps/TestMap.ExistingActor"

    def test_orc09_ui_tool_unaffected(self, orc_modules):
        """ORC-09: ui_tool Actor 不受 existing 影响，始终保持 UI_TOOL。"""
        spec_actors = [_make_ui_actor("UIOnlyActor", "drag_asset_to_viewport")]
        existing_actors = [_make_existing_actor("UIOnlyActor", "/Game/Maps/TestMap.UIOnlyActor")]

        plan = orc_modules.plan_generator.generate_plan(spec_actors, existing_actors)

        assert plan[0]["action"] == orc_modules.plan_generator.ACTION_UI_TOOL
        assert plan[0]["execution_method"] == "ui_tool"

    def test_orc10_plan_entry_fields_complete(self, orc_modules):
        """ORC-10: plan entry 字段完整。"""
        plan = orc_modules.plan_generator.generate_plan(
            [_make_semantic_actor("PlanFieldsActor")],
            existing_actors=[],
        )

        assert set(plan[0].keys()) == {
            "actor_spec",
            "action",
            "execution_method",
            "existing_actor_path",
            "reason",
        }
        assert plan[0]["reason"] != ""


class TestVerifier:
    """ORC-11 ~ ORC-15: Verifier 测试。"""

    def test_orc11_exact_match(self, orc_modules):
        """ORC-11: verify_transform 精确匹配返回 success。"""
        expected = _make_transform()
        actual = _make_transform()

        result = orc_modules.verifier.verify_transform(expected, actual)

        assert result["status"] == "success"
        assert result["mismatches"] == []

    def test_orc12_out_of_tolerance(self, orc_modules):
        """ORC-12: verify_transform 超出容差返回 mismatch。"""
        expected = _make_transform()
        actual = _make_transform(location=[0.02, 0.0, 0.0])

        result = orc_modules.verifier.verify_transform(expected, actual)

        assert result["status"] == "mismatch"
        assert any("location.X" in mismatch for mismatch in result["mismatches"])

    def test_orc13_l3_wide_tolerance(self, orc_modules):
        """ORC-13: L3 宽容差下 50cm 偏差仍判定 success。"""
        expected = _make_transform()
        actual = _make_transform(location=[50.0, 0.0, 0.0])

        result = orc_modules.verifier.verify_transform(
            expected,
            actual,
            orc_modules.verifier.L3_TOLERANCES,
        )

        assert result["status"] == "success"
        assert result["mismatches"] == []

    def test_orc14_checks_fields_complete(self, orc_modules):
        """ORC-14: checks 列表字段完整。"""
        result = orc_modules.verifier.verify_transform(_make_transform(), _make_transform())
        first_check = result["checks"][0]

        assert set(first_check.keys()) == {
            "field",
            "expected",
            "actual",
            "delta",
            "tolerance",
            "pass",
        }

    def test_orc15_auto_select_tolerance(self, orc_modules):
        """ORC-15: verify_actor_state 自动按 execution_method 选择容差。"""
        expected_spec = _make_semantic_actor("ToleranceActor")
        actual_response = {
            "transform": _make_transform(location=[50.0, 0.0, 0.0]),
            "class": expected_spec["class"],
            "collision": {},
            "tags": [],
        }

        semantic_result = orc_modules.verifier.verify_actor_state(
            expected_spec=expected_spec,
            actual_response=actual_response,
            execution_method="semantic",
        )
        ui_result = orc_modules.verifier.verify_actor_state(
            expected_spec=expected_spec,
            actual_response=actual_response,
            execution_method="ui_tool",
        )

        assert semantic_result["status"] == "mismatch"
        assert ui_result["status"] == "success"


def _make_plan_entry(
    actor_spec: dict,
    action: str,
    execution_method: str,
    existing_actor_path: str | None = None,
    reason: str = "pytest",
) -> dict:
    """构造 generate_report 所需的 plan 条目。"""
    return {
        "actor_spec": actor_spec,
        "action": action,
        "execution_method": execution_method,
        "existing_actor_path": existing_actor_path,
        "reason": reason,
    }


def _make_execution_result(
    actor_id: str,
    action: str,
    execution_method: str,
    status: str,
    actor_path: str | None = None,
    summary: str = "",
    cross_verification: dict | None = None,
) -> dict:
    """构造 generate_report 所需的执行结果。"""
    return {
        "actor_id": actor_id,
        "action": action,
        "execution_method": execution_method,
        "status": status,
        "actor_path": actor_path or f"/Game/Maps/TestMap.{actor_id}",
        "summary": summary,
        "cross_verification": cross_verification,
    }


def _make_verification_result(
    status: str,
    mismatches: list[str] | None = None,
    summary: str = "",
    cross_verification: dict | None = None,
) -> dict:
    """构造 generate_report 所需的验证结果。"""
    result = {
        "status": status,
        "checks": [],
        "mismatches": list(mismatches or []),
        "summary": summary,
    }
    if cross_verification is not None:
        result["cross_verification"] = cross_verification
    return result


def _build_report(report_generator, rows: list[dict]) -> dict:
    """根据简化行描述批量生成报告。"""
    plan = []
    execution_results = []
    verification_results = []

    for index, row in enumerate(rows, start=1):
        execution_method = row.get("execution_method", "semantic")
        actor_spec = row.get("actor_spec")
        if actor_spec is None:
            actor_spec = (
                _make_ui_actor(f"UIActor_{index}")
                if execution_method == "ui_tool"
                else _make_semantic_actor(f"Actor_{index}")
            )

        actor_id = actor_spec["id"]
        action = row.get("action", "UI_TOOL" if execution_method == "ui_tool" else "CREATE")
        cross_verification = row.get("cross_verification")

        plan.append(
            _make_plan_entry(
                actor_spec=actor_spec,
                action=action,
                execution_method=execution_method,
                existing_actor_path=row.get("existing_actor_path"),
            )
        )
        execution_results.append(
            _make_execution_result(
                actor_id=actor_id,
                action=action,
                execution_method=execution_method,
                status=row.get("exec_status", "success"),
                actor_path=row.get("actor_path"),
                summary=row.get("exec_summary", ""),
                cross_verification=cross_verification,
            )
        )
        verification_results.append(
            _make_verification_result(
                status=row.get("verify_status", "success"),
                mismatches=row.get("mismatches"),
                summary=row.get("verify_summary", ""),
                cross_verification=cross_verification,
            )
        )

    return report_generator.generate_report(
        spec_path="/Game/Specs/pytest_scene.yaml",
        plan=plan,
        execution_results=execution_results,
        verification_results=verification_results,
        dirty_assets=[],
        map_check={"map_errors": 0, "map_warnings": 0},
    )


class TestReportGenerator:
    """ORC-16 ~ ORC-23: Report Generator 测试。"""

    def test_orc16_all_success(self, orc_modules):
        """ORC-16: 全部 success 时 overall_status=success。"""
        report = _build_report(
            orc_modules.report_generator,
            [
                {"exec_status": "success", "verify_status": "success"},
                {"exec_status": "success", "verify_status": "success"},
            ],
        )

        assert report["overall_status"] == "success"

    def test_orc17_has_mismatch(self, orc_modules):
        """ORC-17: 有 mismatch 且无 failed 时 overall_status=mismatch。"""
        report = _build_report(
            orc_modules.report_generator,
            [
                {"exec_status": "success", "verify_status": "success"},
                {
                    "exec_status": "success",
                    "verify_status": "mismatch",
                    "mismatches": ["location.X mismatch"],
                },
            ],
        )

        assert report["overall_status"] == "mismatch"

    def test_orc18_has_failed_highest_priority(self, orc_modules):
        """ORC-18: 有 failed 时 overall_status=failed，优先级高于 mismatch。"""
        report = _build_report(
            orc_modules.report_generator,
            [
                {
                    "exec_status": "success",
                    "verify_status": "mismatch",
                    "mismatches": ["location.X mismatch"],
                },
                {
                    "exec_status": "failed",
                    "verify_status": "failed",
                    "exec_summary": "spawn failed",
                    "verify_summary": "spawn failed",
                },
            ],
        )

        assert report["overall_status"] == "failed"

    def test_orc19_summary_count_correct(self, orc_modules):
        """ORC-19: summary 计数正确。"""
        report = _build_report(
            orc_modules.report_generator,
            [
                {"exec_status": "success", "verify_status": "success"},
                {
                    "exec_status": "success",
                    "verify_status": "mismatch",
                    "mismatches": ["mismatch"],
                },
                {
                    "exec_status": "failed",
                    "verify_status": "failed",
                    "exec_summary": "failed",
                },
                {
                    "action": "SKIP",
                    "exec_status": "skipped",
                    "verify_status": "skipped",
                },
            ],
        )

        assert report["summary"]["total"] == 4
        assert report["summary"]["passed"] == 1
        assert report["summary"]["mismatched"] == 1
        assert report["summary"]["failed"] == 1
        assert report["summary"]["skipped"] == 1

    def test_orc20_actors_entry_fields(self, orc_modules):
        """ORC-20: actors entry 字段完整。"""
        report = _build_report(
            orc_modules.report_generator,
            [{"exec_status": "success", "verify_status": "success"}],
        )
        actor_entry = report["actors"][0]

        assert {
            "actor_id",
            "action",
            "execution_method",
            "exec_status",
            "verify_status",
            "mismatches",
        }.issubset(actor_entry.keys())

    def test_orc21_save_report_writes_file(self, orc_modules, workspace_tmp_path):
        """ORC-21: save_report 能写出合法 JSON 文件。"""
        report = _build_report(
            orc_modules.report_generator,
            [{"exec_status": "success", "verify_status": "success"}],
        )
        output_path = workspace_tmp_path / "orc21_report.json"

        orc_modules.report_generator.save_report(report, str(output_path))

        saved = json.loads(output_path.read_text(encoding="utf-8"))
        assert saved["overall_status"] == "success"

    def test_orc22_report_has_timestamp(self, orc_modules):
        """ORC-22: 报告含 ISO 8601 时间戳。"""
        report = _build_report(
            orc_modules.report_generator,
            [{"exec_status": "success", "verify_status": "success"}],
        )

        parsed = datetime.fromisoformat(report["timestamp"].replace("Z", "+00:00"))

        assert parsed.tzinfo is not None

    def test_orc23_l3_cross_verification(self, orc_modules):
        """ORC-23: L3 actor entry 含 cross_verification 字段。"""
        cross_verification = {
            "final_status": "success",
            "consistent": True,
            "l3_response": {"status": "success"},
            "l1_response": {"status": "success"},
            "mismatches": [],
        }
        report = _build_report(
            orc_modules.report_generator,
            [
                {
                    "execution_method": "ui_tool",
                    "actor_spec": _make_ui_actor("UICrossVerify"),
                    "exec_status": "success",
                    "verify_status": "success",
                    "cross_verification": cross_verification,
                }
            ],
        )

        assert report["actors"][0]["cross_verification"] == cross_verification


def _success_response(summary: str, data: dict | None = None) -> dict:
    """生成统一 success 响应。"""
    return {
        "status": "success",
        "summary": summary,
        "data": dict(data or {}),
        "warnings": [],
        "errors": [],
    }


def _minimal_cli_report(overall_status: str, spec_path: str) -> dict:
    """构造 main() 打印摘要所需的最小报告。"""
    return {
        "spec_path": spec_path,
        "timestamp": "2026-04-01T00:00:00Z",
        "overall_status": overall_status,
        "summary": {
            "total": 1,
            "passed": 1 if overall_status == "success" else 0,
            "mismatched": 0,
            "failed": 0 if overall_status == "success" else 1,
            "skipped": 0,
        },
        "actors": [],
        "dirty_assets": [],
        "map_check": {
            "map_errors": 0,
            "map_warnings": 0,
        },
    }


def _patch_common_runtime(monkeypatch, orchestrator, existing_actors: list[dict] | None = None):
    """统一打桩主编排依赖的查询接口。"""
    monkeypatch.setattr(
        orchestrator,
        "get_current_project_state",
        lambda: _success_response(
            "Project ready",
            {
                "project_name": "Mvpv4TestCodex",
                "current_level": "/Game/Maps/TestMap",
            },
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "list_level_actors",
        lambda level_path=None, class_filter=None: _success_response(
            "Actors ready",
            {"actors": list(existing_actors or [])},
        ),
    )
    monkeypatch.setattr(
        orchestrator,
        "get_dirty_assets",
        lambda: _success_response("Dirty assets ready", {"dirty_assets": []}),
    )
    monkeypatch.setattr(
        orchestrator,
        "run_map_check",
        lambda level_path=None: _success_response(
            "Map check ready",
            {"map_errors": 0, "map_warnings": 0},
        ),
    )


class TestOrchestratorMain:
    """ORC-24 ~ ORC-31: Orchestrator 主编排测试。"""

    def test_orc24_mock_e2e_4_actors(self, orc_modules, workspace_tmp_path):
        """ORC-24: Mock 模式 E2E 可生成 4 个 actor 的成功报告。"""
        spec = _build_spec(
            [
                _make_semantic_actor("MockSemantic_A"),
                _make_semantic_actor("MockSemantic_B"),
                _make_ui_actor("MockUI_Drag", "drag_asset_to_viewport"),
                _make_ui_actor("MockUI_Click", "click_detail_panel_button"),
            ]
        )
        spec_path = _write_spec(workspace_tmp_path, "orc24_mock_e2e.yaml", spec)
        report_path = workspace_tmp_path / "orc24_report.json"

        report = orc_modules.orchestrator.run(
            spec_path=str(spec_path),
            channel=orc_modules.orchestrator.BridgeChannel.MOCK,
            report_path=str(report_path),
        )

        saved = json.loads(report_path.read_text(encoding="utf-8"))
        assert report["overall_status"] == "success"
        assert len(report["actors"]) == 4
        assert saved["overall_status"] == "success"

    def test_orc25_channel_c_e2e(self, orc_modules, workspace_tmp_path, monkeypatch):
        """ORC-25: Channel C 语义路径可完成 create + readback + verify。"""
        orchestrator = orc_modules.orchestrator
        spec = _build_spec([_make_semantic_actor("CppPluginActor", location=[10.0, 20.0, 30.0])])
        spec_path = _write_spec(workspace_tmp_path, "orc25_cpp_plugin.yaml", spec)
        report_path = workspace_tmp_path / "orc25_report.json"
        actor_specs = {actor["id"]: actor for actor in spec["actors"]}
        spawn_calls = []

        _patch_common_runtime(monkeypatch, orchestrator, existing_actors=[])

        def fake_spawn_actor(level_path, actor_class, actor_name, transform, dry_run=False):
            spawn_calls.append(actor_name)
            return _success_response(
                "Spawned",
                {
                    "created_objects": [
                        {
                            "actor_name": actor_name,
                            "actor_path": f"/Game/Maps/TestMap.{actor_name}",
                        }
                    ]
                },
            )

        def fake_get_actor_state(actor_path):
            actor_name = actor_path.rsplit(".", 1)[-1]
            actor_spec = actor_specs[actor_name]
            return _success_response(
                "Readback",
                {
                    "actor_name": actor_name,
                    "actor_path": actor_path,
                    "class": actor_spec["class"],
                    "target_level": "/Game/Maps/TestMap",
                    "transform": actor_spec["transform"],
                    "collision": {},
                    "tags": [],
                },
            )

        monkeypatch.setattr(orchestrator, "spawn_actor", fake_spawn_actor)
        monkeypatch.setattr(orchestrator, "get_actor_state", fake_get_actor_state)

        report = orchestrator.run(
            spec_path=str(spec_path),
            channel=orchestrator.BridgeChannel.CPP_PLUGIN,
            report_path=str(report_path),
        )

        assert report["overall_status"] == "success"
        assert spawn_calls == ["CppPluginActor"]
        assert report["actors"][0]["final_status"] == "success"

    def test_orc26_l3_dispatch(self, orc_modules, monkeypatch):
        """ORC-26: UI_TOOL 条目会分发到 _UI_TOOL_DISPATCH。"""
        orchestrator = orc_modules.orchestrator
        dispatched = {}

        def fake_drag_asset_to_viewport(**kwargs):
            dispatched["kwargs"] = kwargs
            return _success_response(
                "L3 drag ok",
                {"created_actors": [{"actor_path": "/Game/Maps/TestMap.DraggedActor"}]},
            )

        monkeypatch.setitem(
            orchestrator._UI_TOOL_DISPATCH,
            "drag_asset_to_viewport",
            fake_drag_asset_to_viewport,
        )
        monkeypatch.setattr(
            orchestrator,
            "cross_verify_ui_operation",
            lambda **kwargs: {
                "final_status": "success",
                "consistent": True,
                "l3_response": kwargs["l3_response"],
                "l1_response": {"status": "success"},
                "mismatches": [],
            },
        )

        actor_spec = _make_ui_actor("DispatchActor", "drag_asset_to_viewport")
        plan_item = _make_plan_entry(
            actor_spec=actor_spec,
            action=orc_modules.plan_generator.ACTION_UI_TOOL,
            execution_method="ui_tool",
        )

        step_result = orchestrator._execute_plan_item(
            plan_item=plan_item,
            target_level="/Game/Maps/TestMap",
            channel=orchestrator.BridgeChannel.CPP_PLUGIN,
            resolved_actor_paths={},
        )

        assert dispatched["kwargs"]["asset_path"] == "/Game/Meshes/SM_Chair"
        assert step_result["execution_result"]["action"] == orc_modules.plan_generator.ACTION_UI_TOOL
        assert step_result["verification_result"]["status"] == "success"

    def test_orc27_l3_cross_verify(self, orc_modules, monkeypatch):
        """ORC-27: L3 操作成功后会触发 cross_verify_ui_operation。"""
        orchestrator = orc_modules.orchestrator
        cross_verify_calls = []

        monkeypatch.setitem(
            orchestrator._UI_TOOL_DISPATCH,
            "click_detail_panel_button",
            lambda **kwargs: _success_response("L3 click ok", {"actor_path": kwargs["actor_path"]}),
        )

        def fake_cross_verify(**kwargs):
            cross_verify_calls.append(kwargs)
            return {
                "final_status": "success",
                "consistent": True,
                "l3_response": kwargs["l3_response"],
                "l1_response": {"status": "success"},
                "mismatches": [],
            }

        monkeypatch.setattr(orchestrator, "cross_verify_ui_operation", fake_cross_verify)

        actor_spec = _make_ui_actor("CrossVerifyActor", "click_detail_panel_button")
        plan_item = _make_plan_entry(
            actor_spec=actor_spec,
            action=orc_modules.plan_generator.ACTION_UI_TOOL,
            execution_method="ui_tool",
        )

        step_result = orchestrator._execute_plan_item(
            plan_item=plan_item,
            target_level="/Game/Maps/TestMap",
            channel=orchestrator.BridgeChannel.CPP_PLUGIN,
            resolved_actor_paths={},
        )

        assert len(cross_verify_calls) == 1
        assert cross_verify_calls[0]["l1_verify_args"] == {
            "actor_path": "/Game/Maps/TestMap.TargetActor"
        }
        assert step_result["verification_result"]["cross_verification"]["consistent"] is True

    def test_orc28_single_failure_no_interrupt(self, orc_modules, workspace_tmp_path, monkeypatch):
        """ORC-28: 单个 Actor 失败不会中断后续 Actor。"""
        orchestrator = orc_modules.orchestrator
        spec = _build_spec(
            [
                _make_semantic_actor("BrokenActor"),
                _make_semantic_actor("HealthyActor"),
            ]
        )
        spec_path = _write_spec(workspace_tmp_path, "orc28_continue_on_failure.yaml", spec)
        actor_specs = {actor["id"]: actor for actor in spec["actors"]}
        spawn_calls = []

        _patch_common_runtime(monkeypatch, orchestrator, existing_actors=[])

        def fake_spawn_actor(level_path, actor_class, actor_name, transform, dry_run=False):
            spawn_calls.append(actor_name)
            if actor_name == "BrokenActor":
                raise RuntimeError("Broken actor spawn failed")
            return _success_response(
                "Spawned",
                {
                    "created_objects": [
                        {
                            "actor_name": actor_name,
                            "actor_path": f"/Game/Maps/TestMap.{actor_name}",
                        }
                    ]
                },
            )

        def fake_get_actor_state(actor_path):
            actor_name = actor_path.rsplit(".", 1)[-1]
            actor_spec = actor_specs[actor_name]
            return _success_response(
                "Readback",
                {
                    "actor_name": actor_name,
                    "actor_path": actor_path,
                    "class": actor_spec["class"],
                    "target_level": "/Game/Maps/TestMap",
                    "transform": actor_spec["transform"],
                    "collision": {},
                    "tags": [],
                },
            )

        monkeypatch.setattr(orchestrator, "spawn_actor", fake_spawn_actor)
        monkeypatch.setattr(orchestrator, "get_actor_state", fake_get_actor_state)

        report = orchestrator.run(
            spec_path=str(spec_path),
            channel=orchestrator.BridgeChannel.CPP_PLUGIN,
            report_path=None,
        )

        assert spawn_calls == ["BrokenActor", "HealthyActor"]
        assert report["actors"][0]["final_status"] == "failed"
        assert report["actors"][1]["final_status"] == "success"

    def test_orc29_execution_methods_count(self, orc_modules):
        """ORC-29: summary.execution_methods 统计 semantic / ui_tool 数量正确。"""
        report = _build_report(
            orc_modules.report_generator,
            [
                {"execution_method": "semantic"},
                {"execution_method": "semantic"},
                {"execution_method": "ui_tool", "actor_spec": _make_ui_actor("CountUI")},
            ],
        )

        assert report["summary"]["execution_methods"]["semantic"] == 2
        assert report["summary"]["execution_methods"]["ui_tool"] == 1

    def test_orc30_cli_params(self, orc_modules, workspace_tmp_path, monkeypatch):
        """ORC-30: CLI 参数会被正确解析并传入 run()。"""
        orchestrator = orc_modules.orchestrator
        spec_path = _write_spec(
            workspace_tmp_path,
            "orc30_cli_params.yaml",
            _build_spec([_make_semantic_actor("CliActor")]),
        )
        report_path = workspace_tmp_path / "orc30_cli_report.json"
        captured = {}

        def fake_run(spec_path, channel, report_path):
            captured["spec_path"] = spec_path
            captured["channel"] = channel
            captured["report_path"] = report_path
            Path(report_path).write_text(
                json.dumps(_minimal_cli_report("success", spec_path), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return _minimal_cli_report("success", spec_path)

        monkeypatch.setattr(orchestrator, "run", fake_run)

        exit_code = orchestrator.main(
            [
                str(spec_path),
                "--channel",
                "mock",
                "--report",
                str(report_path),
            ]
        )

        assert exit_code == 0
        assert captured["spec_path"] == str(spec_path)
        assert captured["channel"] == orchestrator.BridgeChannel.MOCK
        assert captured["report_path"] == str(report_path)
        assert report_path.exists()

    def test_orc31_exit_code(self, orc_modules, workspace_tmp_path, monkeypatch):
        """ORC-31: main() 会把 success 映射到 0，把 failed 映射到 1。"""
        orchestrator = orc_modules.orchestrator
        spec_path = _write_spec(
            workspace_tmp_path,
            "orc31_exit_code.yaml",
            _build_spec([_make_semantic_actor("ExitCodeActor")]),
        )

        monkeypatch.setattr(
            orchestrator,
            "run",
            lambda spec_path, channel, report_path: _minimal_cli_report("success", spec_path),
        )
        success_code = orchestrator.main([str(spec_path)])

        monkeypatch.setattr(
            orchestrator,
            "run",
            lambda spec_path, channel, report_path: _minimal_cli_report("failed", spec_path),
        )
        failed_code = orchestrator.main([str(spec_path)])

        assert success_code == 0
        assert failed_code == 1


class TestRunPlanBuilderAndHandoffRunner:
    """ORC-32 ~ ORC-37: Run Plan Builder 与 Handoff Runner 测试。"""

    def test_orc32_run_plan_builder_importable(self, orc_modules):
        """ORC-32: run_plan_builder 可导入。"""
        orchestrator_dir = Path(orc_modules.orchestrator.__file__).resolve().parent
        run_plan_builder = _load_orchestrator_package_module(orchestrator_dir, "run_plan_builder")

        assert callable(run_plan_builder.build_run_plan_from_handoff)

    def test_orc33_handoff_runner_importable(self, orc_modules):
        """ORC-33: handoff_runner 可导入。"""
        orchestrator_dir = Path(orc_modules.orchestrator.__file__).resolve().parent
        handoff_runner = _load_orchestrator_package_module(orchestrator_dir, "handoff_runner")

        assert callable(handoff_runner.run_from_handoff)

    def test_orc34_build_run_plan_from_handoff_generates_sequence(self, orc_modules):
        """ORC-34: build_run_plan_from_handoff 可生成 workflow_sequence。"""
        orchestrator_dir = Path(orc_modules.orchestrator.__file__).resolve().parent
        run_plan_builder = _load_orchestrator_package_module(orchestrator_dir, "run_plan_builder")
        handoff = _build_minimal_handoff([_make_semantic_actor("BoardActor")])
        run_plan = run_plan_builder.build_run_plan_from_handoff(handoff)

        assert len(run_plan["workflow_sequence"]) == 1
        assert run_plan["workflow_sequence"][0]["step_id"] == "spawn_BoardActor"

    def test_orc35_run_plan_source_handoff_id_matches(self, orc_modules):
        """ORC-35: Run Plan 的 source_handoff_id 与输入 handoff_id 一致。"""
        orchestrator_dir = Path(orc_modules.orchestrator.__file__).resolve().parent
        run_plan_builder = _load_orchestrator_package_module(orchestrator_dir, "run_plan_builder")
        handoff = _build_minimal_handoff([_make_semantic_actor("SourceActor")])
        run_plan = run_plan_builder.build_run_plan_from_handoff(handoff)

        assert run_plan["source_handoff_id"] == handoff["handoff_id"]

    def test_orc36_run_plan_workflow_type_is_spawn_actor(self, orc_modules):
        """ORC-36: workflow_sequence 的 workflow_type 为 spawn_actor。"""
        orchestrator_dir = Path(orc_modules.orchestrator.__file__).resolve().parent
        run_plan_builder = _load_orchestrator_package_module(orchestrator_dir, "run_plan_builder")
        handoff = _build_minimal_handoff([_make_semantic_actor("WorkflowActor")])
        run_plan = run_plan_builder.build_run_plan_from_handoff(handoff)

        assert run_plan["workflow_sequence"][0]["workflow_type"] == "spawn_actor"

    def test_orc37_handoff_runner_simulated_e2e(self, orc_modules, workspace_tmp_path):
        """ORC-37: handoff_runner 在 simulated 模式下可完整执行 3 步。"""
        orchestrator_dir = Path(orc_modules.orchestrator.__file__).resolve().parent
        handoff_runner = _load_orchestrator_package_module(orchestrator_dir, "handoff_runner")
        handoff_path = workspace_tmp_path / "orc37_handoff.json"
        report_dir = workspace_tmp_path / "reports"
        handoff = _build_minimal_handoff(
            [
                _make_semantic_actor("Board"),
                _make_semantic_actor("PieceX_1", location=[-100.0, -100.0, 50.0]),
                _make_semantic_actor("PieceO_1", location=[100.0, 100.0, 50.0]),
            ]
        )
        handoff_path.write_text(
            json.dumps(handoff, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        result = handoff_runner.run_from_handoff(
            str(handoff_path),
            report_output_dir=str(report_dir),
            bridge_mode="simulated",
        )

        report_files = sorted(report_dir.glob("execution_report_*.json"))
        assert result["status"] == "succeeded"
        assert len(result["step_results"]) == 3
        assert all(step["result"]["status"] == "success" for step in result["step_results"])
        assert report_files, "未生成 execution_report"

        saved_report = json.loads(report_files[-1].read_text(encoding="utf-8"))
        assert saved_report["execution_status"] == "succeeded"
        assert saved_report["summary"]["succeeded"] == 3
