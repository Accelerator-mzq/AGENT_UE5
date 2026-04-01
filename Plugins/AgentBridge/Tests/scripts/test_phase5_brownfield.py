# -*- coding: utf-8 -*-
"""
Phase 5 Brownfield 编译链测试
覆盖 project_state_intake、baseline snapshot、delta 分析、Contract registry、Brownfield Handoff 与 simulated E2E。
"""

import json
import os
import subprocess
import sys

import pytest


class TestPhase5Brownfield:
    """Phase 5 最小 Brownfield 链路测试。"""

    def test_cp19_project_state_intake_returns_phase5_snapshot(self, compiler_module):
        """CP-19: project_state_intake 至少返回兼容字段和 Phase 5 元数据。"""
        from compiler.intake import get_project_state_snapshot

        snapshot = get_project_state_snapshot()

        assert {"project_name", "actor_count", "is_empty", "actors"}.issubset(snapshot.keys())
        assert {
            "has_existing_content",
            "has_baseline",
            "baseline_refs",
            "registry_refs",
            "known_issues_summary",
            "metadata",
            "current_project_state_digest",
        }.issubset(snapshot.keys())
        assert snapshot["metadata"]["source"] == "mock_fallback"

    def test_cp20_baseline_builder_serializes_snapshot(self, compiler_module, tmp_path):
        """CP-20: baseline_builder 可构建并保存 baseline snapshot。"""
        from compiler.analysis import build_and_save_baseline_snapshot, load_baseline_snapshot

        project_state = _build_synthetic_project_state()
        snapshot, snapshot_path = build_and_save_baseline_snapshot(
            project_state=project_state,
            design_input={"game_type": "boardgame"},
            output_dir=str(tmp_path),
        )
        loaded = load_baseline_snapshot(snapshot_path)

        assert os.path.exists(snapshot_path)
        assert snapshot["baseline_id"].startswith("baseline.boardgame.")
        assert loaded["snapshot_ref"] == snapshot_path
        assert len(loaded["current_project_model"]["actors"]) == 2

    def test_cp21_delta_scope_reports_no_change(self, compiler_module, tmp_path):
        """CP-21: delta_scope_analyzer 能识别 no_change。"""
        from compiler.analysis import analyze_delta_scope, build_baseline_snapshot
        from compiler.generation.boardgame_scene_generator import generate_boardgame_dynamic_spec_tree
        from compiler.generation.static_base_loader import load_phase4_static_specs

        design_input = _load_default_design_input()
        baseline_snapshot = build_baseline_snapshot(_build_target_project_state())
        static_spec_context = load_phase4_static_specs()
        full_target_tree = generate_boardgame_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "greenfield_bootstrap",
                "genre": "boardgame",
                "target_stage": "prototype",
                "activated_skill_packs": ["genre-boardgame"],
            },
            static_spec_context=static_spec_context,
            pack_manifest={"pack_id": "genre-boardgame", "version": "0.1.0"},
        )

        delta_context = analyze_delta_scope(
            design_input=design_input,
            baseline_snapshot=baseline_snapshot,
            target_scene_actors=full_target_tree["scene_spec"]["actors"],
        )

        assert delta_context["delta_intent"] == "no_change"
        assert delta_context["append_specs"] == []

    def test_cp22_delta_scope_reports_append_actor(self, compiler_module):
        """CP-22: delta_scope_analyzer 能识别 append_actor。"""
        from compiler.analysis import analyze_delta_scope, build_baseline_snapshot
        from compiler.generation.boardgame_scene_generator import generate_boardgame_dynamic_spec_tree
        from compiler.generation.static_base_loader import load_phase4_static_specs

        design_input = _load_default_design_input()
        baseline_snapshot = build_baseline_snapshot(_build_synthetic_project_state())
        static_spec_context = load_phase4_static_specs()
        full_target_tree = generate_boardgame_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "greenfield_bootstrap",
                "genre": "boardgame",
                "target_stage": "prototype",
                "activated_skill_packs": ["genre-boardgame"],
            },
            static_spec_context=static_spec_context,
            pack_manifest={"pack_id": "genre-boardgame", "version": "0.1.0"},
        )

        delta_context = analyze_delta_scope(
            design_input=design_input,
            baseline_snapshot=baseline_snapshot,
            target_scene_actors=full_target_tree["scene_spec"]["actors"],
        )

        assert delta_context["delta_intent"] == "append_actor"
        assert [item["actor_name"] for item in delta_context["append_specs"]] == ["PieceO_1"]

    def test_cp23_contract_registry_loads(self, compiler_module):
        """CP-23: Contract registry 与 3 类 Common Contract 可加载。"""
        from compiler.analysis import load_contract_bundle, load_contract_registry

        registry = load_contract_registry()
        contract_ids = [entry["contract_id"] for entry in registry["contracts"]]
        assert contract_ids == [
            "SpecPatchContractModel",
            "MigrationContractModel",
            "RegressionValidationContractModel",
        ]

        patch_bundle = load_contract_bundle("SpecPatchContractModel", registry=registry)
        regression_bundle = load_contract_bundle("RegressionValidationContractModel", registry=registry)
        assert patch_bundle["template"]["contract_kind"] == "patch"
        assert regression_bundle["schema"]["title"] == "RegressionValidationContractModel"

    def test_cp24_brownfield_handoff_contains_baseline_and_delta_context(self, compiler_module, project_root, tmp_path):
        """CP-24: Brownfield Handoff 含 baseline_context / delta_context / tree_type=delta，并通过 Schema 校验。"""
        jsonschema = pytest.importorskip("jsonschema")
        from compiler.handoff import build_handoff
        from compiler.intake import read_gdd

        gdd_path = os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")
        schema_path = os.path.join(
            project_root,
            "Plugins",
            "AgentBridge",
            "Schemas",
            "reviewed_handoff.schema.json",
        )
        design_input = read_gdd(gdd_path)
        handoff = build_handoff(
            design_input=design_input,
            mode="brownfield_expansion",
            project_state=_build_synthetic_project_state(),
            snapshot_output_dir=str(tmp_path),
        )

        with open(schema_path, "r", encoding="utf-8") as file:
            schema = json.load(file)
        jsonschema.validate(handoff, schema)

        assert handoff["status"] == "reviewed"
        assert handoff["baseline_context"]["baseline_id"].startswith("baseline.boardgame.")
        assert handoff["delta_context"]["delta_intent"] == "append_actor"
        assert handoff["dynamic_spec_tree"]["tree_type"] == "delta"
        assert [actor["actor_name"] for actor in handoff["dynamic_spec_tree"]["scene_spec"]["actors"]] == ["PieceO_1"]

    def test_e2e20_brownfield_phase5_simulated(self, project_root):
        """E2E-20: Brownfield simulated 端到端可跑通，且只追加 PieceO_1。"""
        demo_script = os.path.join(project_root, "Scripts", "run_brownfield_demo.py")
        result = subprocess.run(
            [sys.executable, demo_script],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined_output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, combined_output
        assert "append_actor" in combined_output
        assert "PieceO_1" in combined_output
        assert "succeeded" in combined_output


def _load_default_design_input():
    """读取默认井字棋 GDD。"""
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    gdd_path = os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")

    from compiler.intake import read_gdd

    return read_gdd(gdd_path)


def _build_synthetic_project_state():
    """构造 baseline 为 Board + PieceX_1 的项目状态。"""
    return {
        "project_name": "Mvpv4TestCodex",
        "engine_version": "UE5.5.4",
        "current_level": "/Game/Maps/TestMap",
        "actor_count": 2,
        "is_empty": False,
        "actors": [
            {
                "actor_name": "Board",
                "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.Board",
                "class": "/Script/Engine.StaticMeshActor",
                "transform": {
                    "location": [0.0, 0.0, 0.0],
                    "rotation": [0.0, 0.0, 0.0],
                    "relative_scale3d": [3.0, 3.0, 0.1],
                },
                "tags": [],
            },
            {
                "actor_name": "PieceX_1",
                "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.PieceX_1",
                "class": "/Script/Engine.StaticMeshActor",
                "transform": {
                    "location": [-100.0, -100.0, 50.0],
                    "rotation": [0.0, 0.0, 0.0],
                    "relative_scale3d": [0.5, 0.5, 0.5],
                },
                "tags": [],
            },
        ],
        "has_existing_content": True,
        "has_baseline": False,
        "baseline_refs": [],
        "registry_refs": [],
        "known_issues_summary": [],
        "metadata": {"source": "pytest_synthetic"},
        "current_project_state_digest": "pytest-synthetic",
        "dirty_assets": [],
        "map_check_summary": {"map_errors": [], "map_warnings": []},
    }


def _build_target_project_state():
    """构造与默认目标完全一致的项目状态。"""
    target_state = _build_synthetic_project_state()
    target_state["actor_count"] = 3
    target_state["actors"] = target_state["actors"] + [
        {
            "actor_name": "PieceO_1",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.PieceO_1",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [100.0, 100.0, 50.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [0.5, 0.5, 0.5],
            },
            "tags": [],
        }
    ]
    return target_state
