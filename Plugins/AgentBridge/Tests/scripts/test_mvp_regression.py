# -*- coding: utf-8 -*-
"""
MVP 回归系统测试
对应 SystemTestCases.md 中 PY-01 ~ PY-10, E2E-05, E2E-11

确保新开发不破坏已有 MVP 功能

运行方式：pytest test_mvp_regression.py -v
"""
import ast
import importlib
import inspect
import os
import glob
import sys
import pytest


def _load_bridge_modules():
    """统一加载 Bridge 相关模块，避免每个测试重复写导入逻辑。"""
    bridge_core = importlib.import_module("bridge_core")
    query_tools = importlib.import_module("query_tools")
    write_tools = importlib.import_module("write_tools")
    ui_tools = importlib.import_module("ui_tools")
    return bridge_core, query_tools, write_tools, ui_tools


def _run_in_mock_channel(callback):
    """在 Mock 通道中执行断言，结束后恢复原通道。"""
    bridge_core, _, _, _ = _load_bridge_modules()
    previous_channel = bridge_core.get_channel()
    bridge_core.set_channel(bridge_core.BridgeChannel.MOCK)
    try:
        return callback()
    finally:
        bridge_core.set_channel(previous_channel)


class TestPythonClientSyntax:
    """PY-01: Python 客户端文件语法检查"""

    def test_py01_all_bridge_files_no_syntax_error(self, scripts_dir):
        """PY-01: 7 个 bridge Python 文件无语法错误"""
        bridge_dir = os.path.join(scripts_dir, 'bridge')
        py_files = glob.glob(os.path.join(bridge_dir, '*.py'))
        assert len(py_files) > 0, f"未找到 bridge Python 文件: {bridge_dir}"

        errors = []
        for f in py_files:
            try:
                # 项目中存在带 BOM 的 Python 文件，这里用 utf-8-sig 避免误判。
                with open(f, encoding='utf-8-sig') as fp:
                    ast.parse(fp.read(), filename=f)
            except SyntaxError as e:
                errors.append(f"{f}: {e}")

        assert len(errors) == 0, "语法错误:\n" + "\n".join(errors)

    def test_py01_all_orchestrator_files_no_syntax_error(self, scripts_dir):
        """PY-01 扩展: orchestrator Python 文件无语法错误"""
        orc_dir = os.path.join(scripts_dir, 'orchestrator')
        py_files = glob.glob(os.path.join(orc_dir, '*.py'))
        assert len(py_files) > 0, f"未找到 orchestrator Python 文件: {orc_dir}"

        errors = []
        for f in py_files:
            try:
                # 项目中存在带 BOM 的 Python 文件，这里用 utf-8-sig 避免误判。
                with open(f, encoding='utf-8-sig') as fp:
                    ast.parse(fp.read(), filename=f)
            except SyntaxError as e:
                errors.append(f"{f}: {e}")

        assert len(errors) == 0, "语法错误:\n" + "\n".join(errors)


class TestPythonClientStructure:
    """PY-02 ~ PY-10: Python 客户端结构验证"""

    def test_py02_bridge_channel_enum(self, bridge_module):
        """PY-02: BridgeChannel 枚举有 4 个值"""
        bridge_core, _, _, _ = _load_bridge_modules()
        channel_values = [channel.value for channel in bridge_core.BridgeChannel]
        assert channel_values == [
            "python_editor",
            "remote_control",
            "cpp_plugin",
            "mock",
        ]

    def test_py03_mock_query_interfaces(self, bridge_module):
        """PY-03: Mock 模式 7 个 L1 查询接口返回 success"""
        def _assert_queries():
            _, query_tools, _, _ = _load_bridge_modules()
            results = [
                query_tools.get_current_project_state(),
                query_tools.list_level_actors(),
                query_tools.get_actor_state("/Game/Maps/TestMap.TestMap:PersistentLevel.Board"),
                query_tools.get_actor_bounds("/Game/Maps/TestMap.TestMap:PersistentLevel.Board"),
                query_tools.get_asset_metadata("/Game/Maps/TestMap"),
                query_tools.get_dirty_assets(),
                query_tools.run_map_check(),
            ]
            assert all(result["status"] == "success" for result in results)

        _run_in_mock_channel(_assert_queries)

    def test_py04_mock_write_interfaces(self, bridge_module):
        """PY-04: Mock 模式 4 个 L1 写接口返回 success"""
        transform = {
            "location": [0.0, 0.0, 0.0],
            "rotation": [0.0, 0.0, 0.0],
            "relative_scale3d": [1.0, 1.0, 1.0],
        }

        def _assert_writes():
            _, _, write_tools, _ = _load_bridge_modules()
            results = [
                write_tools.spawn_actor(
                    "/Game/Maps/TestMap",
                    "/Script/Engine.StaticMeshActor",
                    "PytestActor",
                    transform,
                ),
                write_tools.set_actor_transform(
                    "/Game/Maps/TestMap.TestMap:PersistentLevel.PytestActor",
                    transform,
                ),
                write_tools.import_assets(
                    "D:/UnrealProjects/Mvpv4TestCodex/TestResources/ImportTest",
                    "/Game/Imported",
                ),
                write_tools.create_blueprint_child(
                    "/Script/Engine.Actor",
                    "/Game/Pytest/BP_PytestChild",
                ),
            ]
            assert all(result["status"] == "success" for result in results)

        _run_in_mock_channel(_assert_writes)

    def test_py05_mock_ui_interfaces(self, bridge_module):
        """PY-05: Mock 模式 3 个 L3 UI 接口返回 success + tool_layer=L3_UITool"""
        def _assert_ui():
            _, _, _, ui_tools = _load_bridge_modules()
            results = [
                ui_tools.click_detail_panel_button(
                    "/Game/Maps/TestMap.TestMap:PersistentLevel.Board",
                    "Apply",
                    dry_run=True,
                ),
                ui_tools.type_in_detail_panel_field(
                    "/Game/Maps/TestMap.TestMap:PersistentLevel.Board",
                    "BoardSize",
                    "3",
                    dry_run=True,
                ),
                ui_tools.drag_asset_to_viewport(
                    "/Game/Meshes/SM_Test",
                    [0.0, 0.0, 0.0],
                    dry_run=True,
                ),
            ]
            assert all(result["status"] == "success" for result in results)
            assert all(result["data"]["tool_layer"] == "L3_UITool" for result in results)

        _run_in_mock_channel(_assert_ui)

    def test_py06_validate_empty_string(self, bridge_module):
        """PY-06: validate_required_string 空串返回 validation_error"""
        bridge_core, _, _, _ = _load_bridge_modules()
        result = bridge_core.validate_required_string("", "actor_path")
        assert result["status"] == "validation_error"
        assert result["errors"][0]["code"] == "INVALID_ARGS"

    def test_py07_validate_valid_string(self, bridge_module):
        """PY-07: validate_required_string 有效值返回 None"""
        bridge_core, _, _, _ = _load_bridge_modules()
        assert bridge_core.validate_required_string("valid", "actor_path") is None

    def test_py08_call_cpp_plugin_signature(self, bridge_module):
        """PY-08: call_cpp_plugin 函数签名正确"""
        bridge_core, _, _, _ = _load_bridge_modules()
        signature = inspect.signature(bridge_core.call_cpp_plugin)
        assert list(signature.parameters.keys()) == ["function_name", "parameters"]

    def test_py09_cpp_query_map_count(self, bridge_module):
        """PY-09: _CPP_QUERY_MAP 至少包含文档定义的 7 个核心查询映射。"""
        _, query_tools, _, _ = _load_bridge_modules()
        expected_keys = {
            "get_current_project_state",
            "list_level_actors",
            "get_actor_state",
            "get_actor_bounds",
            "get_asset_metadata",
            "get_dirty_assets",
            "run_map_check",
        }
        assert expected_keys.issubset(set(query_tools._CPP_QUERY_MAP.keys()))
        assert len(query_tools._CPP_QUERY_MAP) >= 7

    def test_py10_cpp_write_map_count(self, bridge_module):
        """PY-10: _CPP_WRITE_MAP 至少包含文档定义的 4 个核心写映射。"""
        _, _, write_tools, _ = _load_bridge_modules()
        expected_keys = {
            "spawn_actor",
            "set_actor_transform",
            "import_assets",
            "create_blueprint_child",
        }
        assert expected_keys.issubset(set(write_tools._CPP_WRITE_MAP.keys()))
        assert len(write_tools._CPP_WRITE_MAP) >= 4


class TestMVPRegression:
    """E2E-05, E2E-11: MVP 回归验证"""

    def test_e2e05_schema_full_validation(self, plugin_root):
        """E2E-05: Schema 全量验证（与 SV-01 相同，作为回归入口）"""
        import subprocess
        script = os.path.join(plugin_root, 'Scripts', 'validation', 'validate_examples.py')
        if not os.path.exists(script):
            pytest.skip("validate_examples.py 不存在")

        result = subprocess.run(
            [sys.executable, script, '--strict'],
            capture_output=True, text=True, cwd=os.path.join(plugin_root, '..', '..')
        )
        assert result.returncode == 0, f"回归验证失败:\n{result.stdout}\n{result.stderr}"
