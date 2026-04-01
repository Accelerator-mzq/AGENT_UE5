# -*- coding: utf-8 -*-
"""
Compiler / Skills / Specs 基础测试
对应 SystemTestCases.md 中 CP-01 ~ CP-11, SS-01 ~ SS-07
"""

import json
import os
import subprocess
import sys

import pytest
import yaml


class TestCompilerPlaneFoundation:
    """CP-01 ~ CP-11：Compiler Plane 基础能力。"""

    def test_cp01_compiler_intake_imports(self, compiler_module):
        """CP-01: compiler.intake 可导入。"""
        from compiler.intake import get_project_state_snapshot, read_gdd, read_gdd_from_directory

        assert callable(read_gdd)
        assert callable(read_gdd_from_directory)
        assert callable(get_project_state_snapshot)

    def test_cp02_compiler_routing_imports(self, compiler_module):
        """CP-02: compiler.routing 可导入。"""
        from compiler.routing import determine_mode, load_mode_config

        assert callable(determine_mode)
        assert callable(load_mode_config)

    def test_cp03_compiler_handoff_imports(self, compiler_module):
        """CP-03: compiler.handoff 可导入。"""
        from compiler.handoff import build_handoff, serialize_handoff

        assert callable(build_handoff)
        assert callable(serialize_handoff)

    def test_cp04_project_state_intake_imports(self, compiler_module):
        """CP-04: project_state_intake 入口可导入。"""
        from compiler.intake import get_project_state_snapshot

        assert callable(get_project_state_snapshot)

    def test_cp05_design_input_extracts_game_type(self, compiler_module, project_root):
        """CP-05: GDD 提取出的 game_type 为 boardgame。"""
        from compiler.intake import read_gdd

        design_input = read_gdd(_default_gdd_path(project_root))
        assert design_input["game_type"] == "boardgame"

    def test_cp06_mode_router_auto_detects_greenfield(self, compiler_module):
        """CP-06: 空项目 + auto 时走 greenfield。"""
        from compiler.routing import determine_mode

        mode = determine_mode(_auto_mode_config(), _empty_project_state())
        assert mode == "greenfield_bootstrap"

    def test_cp07_mode_router_auto_detects_brownfield(self, compiler_module):
        """CP-07: 非空项目 + auto 时走 brownfield。"""
        from compiler.routing import determine_mode

        mode = determine_mode(_auto_mode_config(), _non_empty_project_state())
        assert mode == "brownfield_expansion"

    def test_cp08_mode_router_force_mode_overrides_auto(self, compiler_module):
        """CP-08: force_mode 必须高于 auto 检测。"""
        from compiler.routing import determine_mode

        mode = determine_mode(
            {
                "default_mode": "auto",
                "force_mode": "greenfield_bootstrap",
                "mode_detection_rules": {"empty_project_threshold": 0},
            },
            _non_empty_project_state(),
        )
        assert mode == "greenfield_bootstrap"

    def test_cp09_handoff_builder_generates_three_actor_handoff(self, compiler_module, project_root):
        """CP-09: Greenfield Handoff 默认生成 Board + PieceX_1 + PieceO_1。"""
        from compiler.handoff import build_handoff
        from compiler.intake import read_gdd

        handoff = build_handoff(
            read_gdd(_default_gdd_path(project_root)),
            "greenfield_bootstrap",
            _empty_project_state(),
        )
        actors = handoff["dynamic_spec_tree"]["scene_spec"]["actors"]

        assert len(actors) == 3
        assert [actor["actor_name"] for actor in actors] == ["Board", "PieceX_1", "PieceO_1"]

    def test_cp10_generated_handoff_passes_schema(self, compiler_module, project_root):
        """CP-10: 生成的 Handoff 可以通过 reviewed_handoff schema。"""
        jsonschema = pytest.importorskip("jsonschema")
        from compiler.handoff import build_handoff
        from compiler.intake import read_gdd

        handoff = build_handoff(
            read_gdd(_default_gdd_path(project_root)),
            "greenfield_bootstrap",
            _empty_project_state(),
        )
        schema_path = os.path.join(
            project_root,
            "Plugins",
            "AgentBridge",
            "Schemas",
            "reviewed_handoff.schema.json",
        )
        with open(schema_path, "r", encoding="utf-8") as file:
            schema = json.load(file)

        jsonschema.validate(handoff, schema)

    def test_cp11_compiler_main_end_to_end(self, compiler_module, project_root, workspace_tmp_path):
        """CP-11: compiler_main 端到端可输出 handoff 文件。"""
        from compiler_main import run_compiler

        output_dir = str(workspace_tmp_path / "handoffs")
        os.makedirs(output_dir, exist_ok=True)
        handoff, output_file = run_compiler(
            gdd_dir=os.path.join(project_root, "ProjectInputs", "GDD"),
            mode_config_path=os.path.join(project_root, "ProjectInputs", "Presets", "mode_override.yaml"),
            output_dir=output_dir,
            output_format="yaml",
        )

        assert handoff["handoff_id"].startswith("handoff.")
        assert os.path.exists(output_file)
        assert output_file.endswith(".yaml")


class TestSkillsAndSpecsFoundation:
    """SS-01 ~ SS-07：Skills & Specs 基础结构校验。"""

    def test_ss01_skills_directory_structure_complete(self, project_root):
        """SS-01: Skills 根结构存在。"""
        skills_root = os.path.join(project_root, "Plugins", "AgentBridge", "Skills")
        assert os.path.isdir(os.path.join(skills_root, "base_domains"))
        assert os.path.isdir(os.path.join(skills_root, "genre_packs"))

    def test_ss02_pack_manifest_yaml_loads(self, project_root):
        """SS-02: pack_manifest.yaml 可正常解析。"""
        manifest_path = _boardgame_manifest_path(project_root)
        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = yaml.safe_load(file)

        assert isinstance(manifest, dict)
        assert manifest["pack_id"] == "genre-boardgame"

    def test_ss03_pack_manifest_pack_id_matches(self, project_root):
        """SS-03: pack_manifest.yaml 的 pack_id 正确。"""
        manifest_path = _boardgame_manifest_path(project_root)
        with open(manifest_path, "r", encoding="utf-8") as file:
            manifest = yaml.safe_load(file)

        assert manifest["pack_id"] == "genre-boardgame"

    def test_ss04_specs_extension_directories_exist(self, project_root):
        """SS-04: StaticBase / Contracts 目录存在。"""
        specs_root = os.path.join(project_root, "Plugins", "AgentBridge", "Specs")
        assert os.path.isdir(os.path.join(specs_root, "StaticBase"))
        assert os.path.isdir(os.path.join(specs_root, "Contracts"))

    def test_ss05_static_base_registry_complete(self, project_root):
        """SS-05: StaticBase registry 至少登记 10 个静态基座且含 phase4_enabled。"""
        registry_path = os.path.join(
            project_root,
            "Plugins",
            "AgentBridge",
            "Specs",
            "StaticBase",
            "Registry",
            "spec_type_registry.yaml",
        )
        with open(registry_path, "r", encoding="utf-8") as file:
            registry = yaml.safe_load(file)

        static_specs = registry["static_specs"]
        assert len(static_specs) == 10
        assert all("phase4_enabled" in item for item in static_specs)

    def test_ss06_all_static_base_templates_are_valid_yaml(self, project_root):
        """SS-06: 10 个静态基座模板都能被 yaml.safe_load 解析。"""
        template_paths = _collect_files(
            project_root,
            "Plugins",
            "AgentBridge",
            "Specs",
            "StaticBase",
            suffix="template.yaml",
        )
        assert len(template_paths) == 10

        for template_path in template_paths:
            with open(template_path, "r", encoding="utf-8") as file:
                assert yaml.safe_load(file) is not None

    def test_ss07_all_static_base_schemas_are_valid_json(self, project_root):
        """SS-07: 10 个静态基座 schema 都能被 json.load 解析。"""
        schema_paths = _collect_files(
            project_root,
            "Plugins",
            "AgentBridge",
            "Specs",
            "StaticBase",
            suffix="schema.json",
        )
        assert len(schema_paths) == 10

        for schema_path in schema_paths:
            with open(schema_path, "r", encoding="utf-8") as file:
                assert isinstance(json.load(file), dict)


def _default_gdd_path(project_root):
    """返回默认 GDD 路径。"""
    return os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")


def _boardgame_manifest_path(project_root):
    """返回 boardgame pack manifest 路径。"""
    return os.path.join(
        project_root,
        "Plugins",
        "AgentBridge",
        "Skills",
        "genre_packs",
        "boardgame",
        "pack_manifest.yaml",
    )


def _collect_files(project_root, *parts, suffix):
    """收集指定目录下的目标文件。"""
    root = os.path.join(project_root, *parts)
    collected = []
    for current_root, _, files in os.walk(root):
        for file_name in files:
            if file_name == suffix:
                collected.append(os.path.join(current_root, file_name))
    return sorted(collected)


def _auto_mode_config():
    """构造默认 auto 模式配置。"""
    return {
        "default_mode": "auto",
        "force_mode": None,
        "mode_detection_rules": {
            "empty_project_threshold": 0,
            "require_baseline": False,
        },
    }


def _empty_project_state():
    """构造空项目快照。"""
    return {
        "project_name": "Mvpv4TestCodex",
        "actor_count": 0,
        "is_empty": True,
        "has_existing_content": False,
        "has_baseline": False,
        "actors": [],
    }


def _non_empty_project_state():
    """构造非空项目快照。"""
    return {
        "project_name": "Mvpv4TestCodex",
        "actor_count": 2,
        "is_empty": False,
        "has_existing_content": True,
        "has_baseline": False,
        "actors": [
            {"actor_name": "Board"},
            {"actor_name": "PieceX_1"},
        ],
    }
