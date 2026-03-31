# -*- coding: utf-8 -*-
"""
MVP 回归系统测试
对应 SystemTestCases.md 中 PY-01 ~ PY-10, E2E-05, E2E-11

确保新开发不破坏已有 MVP 功能

运行方式：pytest test_mvp_regression.py -v
"""
import ast
import os
import glob
import sys
import pytest


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
        pytest.skip("待实现 — 需确认 bridge_core.py 可导入")

    def test_py03_mock_query_interfaces(self, bridge_module):
        """PY-03: Mock 模式 7 个 L1 查询接口返回 success"""
        pytest.skip("待实现")

    def test_py04_mock_write_interfaces(self, bridge_module):
        """PY-04: Mock 模式 4 个 L1 写接口返回 success"""
        pytest.skip("待实现")

    def test_py05_mock_ui_interfaces(self, bridge_module):
        """PY-05: Mock 模式 3 个 L3 UI 接口返回 success + tool_layer=L3_UITool"""
        pytest.skip("待实现")

    def test_py06_validate_empty_string(self, bridge_module):
        """PY-06: validate_required_string 空串返回 validation_error"""
        pytest.skip("待实现")

    def test_py07_validate_valid_string(self, bridge_module):
        """PY-07: validate_required_string 有效值返回 None"""
        pytest.skip("待实现")

    def test_py08_call_cpp_plugin_signature(self, bridge_module):
        """PY-08: call_cpp_plugin 函数签名正确"""
        pytest.skip("待实现")

    def test_py09_cpp_query_map_count(self, bridge_module):
        """PY-09: _CPP_QUERY_MAP 有 7 个映射"""
        pytest.skip("待实现")

    def test_py10_cpp_write_map_count(self, bridge_module):
        """PY-10: _CPP_WRITE_MAP 有 4 个映射"""
        pytest.skip("待实现")


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
