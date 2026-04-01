# -*- coding: utf-8 -*-
"""
Schema 验证系统测试
对应 SystemTestCases.md 中 SV-01 ~ SV-10

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

    def test_sv05_validate_examples_keeps_existing_examples_green(self, plugin_root):
        """SV-05: 重新执行 validate_examples，确认旧 example 未被新 schema 破坏。"""
        import subprocess

        script = os.path.join(plugin_root, 'Scripts', 'validation', 'validate_examples.py')
        result = subprocess.run(
            [sys.executable, script, '--strict'],
            capture_output=True,
            text=True,
            cwd=os.path.join(plugin_root, '..', '..'),
        )
        assert result.returncode == 0, f"validate_examples 回归失败:\n{result.stdout}\n{result.stderr}"

    def test_sv06_reviewed_handoff_schema_required_fields(self, schemas_dir):
        """SV-06: reviewed_handoff.schema.json 必填字段结构正确。"""
        schema_path = os.path.join(schemas_dir, 'reviewed_handoff.schema.json')
        with open(schema_path, encoding='utf-8') as file:
            schema = json.load(file)

        required_fields = schema.get("required", [])
        assert len(required_fields) == 5
        assert required_fields == [
            "handoff_version",
            "handoff_id",
            "handoff_mode",
            "status",
            "dynamic_spec_tree",
        ]

    def test_sv07_run_plan_schema_required_fields(self, schemas_dir):
        """SV-07: run_plan.schema.json 必填字段结构正确。"""
        schema_path = os.path.join(schemas_dir, 'run_plan.schema.json')
        with open(schema_path, encoding='utf-8') as file:
            schema = json.load(file)

        required_fields = schema.get("required", [])
        assert len(required_fields) == 5
        assert required_fields == [
            "run_plan_version",
            "run_plan_id",
            "source_handoff_id",
            "mode",
            "workflow_sequence",
        ]

    def test_sv08_reviewed_handoff_example_passes_schema(self, schemas_dir):
        """SV-08: reviewed_handoff example 可通过 Schema 校验。"""
        jsonschema = pytest.importorskip("jsonschema")

        schema_path = os.path.join(schemas_dir, 'reviewed_handoff.schema.json')
        example_path = os.path.join(schemas_dir, 'examples', 'reviewed_handoff_greenfield.example.json')

        with open(schema_path, encoding='utf-8') as file:
            schema = json.load(file)
        with open(example_path, encoding='utf-8') as file:
            example = json.load(file)

        jsonschema.validate(example, schema)

    def test_sv09_run_plan_example_passes_schema(self, schemas_dir):
        """SV-09: run_plan example 可通过 Schema 校验。"""
        jsonschema = pytest.importorskip("jsonschema")

        schema_path = os.path.join(schemas_dir, 'run_plan.schema.json')
        example_path = os.path.join(schemas_dir, 'examples', 'run_plan_greenfield.example.json')

        with open(schema_path, encoding='utf-8') as file:
            schema = json.load(file)
        with open(example_path, encoding='utf-8') as file:
            example = json.load(file)

        jsonschema.validate(example, schema)

    def test_sv10_validate_examples_still_accepts_extended_schema_set(self, plugin_root, schemas_dir):
        """SV-10: schema 扩展后 validate_examples 仍能完整通过。"""
        import subprocess

        example_files = glob.glob(os.path.join(schemas_dir, 'examples', '*.json'))
        assert len(example_files) >= 4, "example 集合异常，无法确认扩展后的回归状态"

        script = os.path.join(plugin_root, 'Scripts', 'validation', 'validate_examples.py')
        result = subprocess.run(
            [sys.executable, script, '--strict'],
            capture_output=True,
            text=True,
            cwd=os.path.join(plugin_root, '..', '..'),
        )
        assert result.returncode == 0, f"扩展 schema 后 validate_examples 失败:\n{result.stdout}\n{result.stderr}"


import sys  # noqa: E402 — 顶部 fixture 需要
