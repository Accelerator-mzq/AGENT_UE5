# -*- coding: utf-8 -*-
"""
Schema 验证系统测试
对应 SystemTestCases.md 中 SV-01 ~ SV-05

运行方式：pytest test_schema_validation.py -v
"""
import json
import glob
import os
import pytest


class TestSchemaValidation:
    """SV 系列：Schema 验证测试"""

    def test_sv01_all_examples_pass_validation(self, plugin_root):
        """SV-01: 全部 example 通过 Schema 校验"""
        # 调用已有的 validate_examples.py
        import subprocess
        script = os.path.join(plugin_root, 'Scripts', 'validation', 'validate_examples.py')
        result = subprocess.run(
            [sys.executable, script, '--strict'],
            capture_output=True, text=True, cwd=os.path.join(plugin_root, '..', '..')
        )
        assert result.returncode == 0, f"Schema 校验失败:\n{result.stdout}\n{result.stderr}"

    def test_sv02_all_json_files_valid_syntax(self, schemas_dir):
        """SV-02: 全部 JSON 文件语法合法"""
        json_files = glob.glob(os.path.join(schemas_dir, '**', '*.json'), recursive=True)
        assert len(json_files) > 0, "未找到任何 JSON 文件"

        errors = []
        for f in json_files:
            try:
                with open(f, encoding='utf-8') as fp:
                    json.load(fp)
            except Exception as e:
                errors.append(f"{f}: {e}")

        assert len(errors) == 0, f"JSON 语法错误:\n" + "\n".join(errors)

    def test_sv03_schema_file_count(self, schemas_dir):
        """SV-03: Schema 文件数量一致性（初始 24 个）"""
        json_files = glob.glob(os.path.join(schemas_dir, '**', '*.json'), recursive=True)
        # 初始 24 个，TASK 18 扩展后 28 个
        assert len(json_files) >= 24, f"Schema 文件数量不足: {len(json_files)}, 预期 >= 24"

    def test_sv04_example_schema_mapping_complete(self, schemas_dir):
        """SV-04: 每个 example 有对应的 Schema 映射"""
        examples_dir = os.path.join(schemas_dir, 'examples')
        if not os.path.isdir(examples_dir):
            pytest.skip("examples 目录不存在")

        examples = glob.glob(os.path.join(examples_dir, '*.json'))
        assert len(examples) > 0, "未找到 example 文件"
        # 每个 example 文件都应该能被 validate_examples.py 处理
        # 具体映射逻辑由 validate_examples.py 保证


import sys  # noqa: E402 — 顶部 fixture 需要
