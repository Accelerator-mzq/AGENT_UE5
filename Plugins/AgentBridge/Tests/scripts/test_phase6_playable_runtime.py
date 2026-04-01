# -*- coding: utf-8 -*-
"""
Phase 6 Playable Runtime 测试
覆盖 genre pack core、完整 spec tree、runtime_playable handoff 与当前阶段 demo 入口。
"""

import json
import os
import subprocess
import sys


class TestPhase6PlayableRuntime:
    """Phase 6 最小 playable runtime 链路测试。"""

    def test_ss08_pack_registry_and_modules_load(self, compiler_module):
        """SS-08: _core registry 能发现 genre-boardgame，且 required skills 可加载。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_modules, load_pack_registry

        registry = load_pack_registry()
        pack_ids = [pack["pack_id"] for pack in registry["packs"]]
        assert "genre-boardgame" in pack_ids

        pack_manifest = registry["pack_map"]["genre-boardgame"]
        modules = load_pack_modules(pack_manifest)
        assert [entry["module_id"] for entry in modules["required_skills"]] == [
            "board_layout",
            "piece_movement",
            "turn_system",
        ]
        assert all(entry["module"] is not None for entry in modules["required_skills"])

    def test_ss09_boardgame_manifest_is_phase6_complete(self):
        """SS-09: boardgame manifest 覆盖完整 Phase 6 字段。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_registry

        manifest = load_pack_registry()["pack_map"]["genre-boardgame"]
        assert manifest["status"] == "phase6_playable_runtime"
        assert manifest["delta_policy"]["provider"] == "boardgame_delta_policy"
        assert manifest["review_extensions"] == ["boardgame_reviewer"]
        assert manifest["validation_extensions"] == ["boardgame_validator"]

    def test_ss10_required_skills_modules_load(self, compiler_module):
        """SS-10: 3 个 required skills 可加载。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_modules, load_pack_registry

        pack_manifest = load_pack_registry()["pack_map"]["genre-boardgame"]
        modules = load_pack_modules(pack_manifest)

        assert [entry["module_id"] for entry in modules["required_skills"]] == [
            "board_layout",
            "piece_movement",
            "turn_system",
        ]
        assert all(entry["exists"] is True for entry in modules["required_skills"])
        assert all(entry["module"] is not None for entry in modules["required_skills"])

    def test_ss11_review_validation_and_delta_policy_modules_load(self, compiler_module):
        """SS-11: review / validation / delta policy 模块可加载。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_modules, load_pack_registry

        pack_manifest = load_pack_registry()["pack_map"]["genre-boardgame"]
        modules = load_pack_modules(pack_manifest)

        assert [entry["module_id"] for entry in modules["review_extensions"]] == ["boardgame_reviewer"]
        assert [entry["module_id"] for entry in modules["validation_extensions"]] == ["boardgame_validator"]
        assert [entry["module_id"] for entry in modules["delta_policies"]] == ["boardgame_delta_policy"]
        assert all(entry["module"] is not None for entry in modules["review_extensions"])
        assert all(entry["module"] is not None for entry in modules["validation_extensions"])
        assert all(entry["module"] is not None for entry in modules["delta_policies"])

    def test_ss12_genre_contracts_registered_in_contract_registry(self, compiler_module):
        """SS-12: Genre contracts 已登记到 contract registry。"""
        from compiler.analysis import load_contract_registry

        registry = load_contract_registry()
        contract_ids = {entry["contract_id"] for entry in registry["contracts"]}

        assert {"TurnFlowPatchContract", "DecisionUIPatchContract"}.issubset(contract_ids)

    def test_ss13_common_and_genre_contract_bundles_load(self, compiler_module):
        """SS-13: Common + Genre contract bundle 均可加载。"""
        from compiler.analysis import load_contract_bundle, load_contract_registry

        registry = load_contract_registry()

        common_bundle = load_contract_bundle("SpecPatchContractModel", registry=registry)
        regression_bundle = load_contract_bundle("RegressionValidationContractModel", registry=registry)
        turn_bundle = load_contract_bundle("TurnFlowPatchContract", registry=registry)
        ui_bundle = load_contract_bundle("DecisionUIPatchContract", registry=registry)

        assert common_bundle["manifest"]["contract_id"] == "SpecPatchContractModel"
        assert regression_bundle["manifest"]["contract_id"] == "RegressionValidationContractModel"
        assert turn_bundle["manifest"]["contract_id"] == "TurnFlowPatchContract"
        assert ui_bundle["manifest"]["contract_id"] == "DecisionUIPatchContract"

    def test_cp25_preview_static_generates_full_spec_tree(self, compiler_module, project_root):
        """CP-25: 默认 preview_static 已生成完整 10 节点 Spec Tree。"""
        from compiler.generation import generate_dynamic_spec_tree
        from compiler.intake import read_gdd

        design_input = read_gdd(_default_gdd_path(project_root))
        result = generate_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "greenfield_bootstrap",
                "genre": "boardgame",
                "target_stage": "prototype",
                "activated_skill_packs": ["genre-boardgame"],
                "projection_profile": "preview_static",
            },
            projection_profile="preview_static",
        )
        tree = result["dynamic_spec_tree"]

        assert {
            "world_build_spec",
            "boardgame_spec",
            "board_layout_spec",
            "piece_movement_spec",
            "turn_flow_spec",
            "decision_ui_spec",
            "runtime_wiring_spec",
            "validation_spec",
            "scene_spec",
            "generation_trace",
        }.issubset(tree.keys())
        assert [actor["actor_name"] for actor in tree["scene_spec"]["actors"]] == ["Board", "PieceX_1", "PieceO_1"]
        assert tree["generation_trace"]["projection_profile"] == "preview_static"

    def test_cp26_runtime_playable_handoff_writes_runtime_config(self, compiler_module, project_root):
        """CP-26: runtime_playable 生成 runtime actor 投影与 runtime config。"""
        from compiler.handoff import build_handoff
        from compiler.intake import get_project_state_snapshot, read_gdd

        design_input = read_gdd(_default_gdd_path(project_root))
        handoff = build_handoff(
            design_input=design_input,
            mode="greenfield_bootstrap",
            project_state=get_project_state_snapshot(),
            target_stage="prototype_playable",
            projection_profile="runtime_playable",
        )
        runtime_config_ref = handoff["metadata"]["runtime_config_ref"]
        runtime_actor = handoff["dynamic_spec_tree"]["scene_spec"]["actors"][0]

        assert handoff["status"] == "reviewed"
        assert runtime_actor["actor_name"] == "BoardRuntimeActor"
        assert runtime_actor["actor_class"] == "/Script/Mvpv4TestCodex.BoardgamePrototypeBoardActor"
        assert os.path.exists(runtime_config_ref)
        with open(runtime_config_ref, "r", encoding="utf-8") as file:
            runtime_config = json.load(file)
        assert runtime_config["handoff_id"] == handoff["handoff_id"]
        assert runtime_config["turn_flow_spec"]["spec_id"] == "TurnFlowSpec"

    def test_cp27_runtime_actor_exposes_minimum_callable_interfaces(self, project_root):
        """CP-27: runtime actor 需要的最小 callable 接口已落地。"""
        header_path = os.path.join(
            project_root,
            "Source",
            "Mvpv4TestCodex",
            "BoardgamePrototypeBoardActor.h",
        )
        with open(header_path, "r", encoding="utf-8") as file:
            header_text = file.read()

        assert "bool LoadRuntimeConfigFromFile(" in header_text
        assert "bool ApplyMoveByCell(" in header_text
        assert "FString GetBoardRuntimeState() const" in header_text
        assert "void ResetBoard()" in header_text

    def test_cp28_reviewer_blocks_missing_phase6_runtime_nodes(self, compiler_module, project_root):
        """CP-28: 缺失 turn_flow_spec / decision_ui_spec / runtime_wiring_spec 时 reviewer 阻断。"""
        from compiler.generation import generate_dynamic_spec_tree
        from compiler.intake import read_gdd
        from compiler.review import review_dynamic_spec_tree

        design_input = read_gdd(_default_gdd_path(project_root))
        generation_result = generate_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "greenfield_bootstrap",
                "genre": "boardgame",
                "target_stage": "prototype",
                "activated_skill_packs": ["genre-boardgame"],
                "projection_profile": "preview_static",
            },
            projection_profile="preview_static",
        )
        dynamic_spec_tree = json.loads(json.dumps(generation_result["dynamic_spec_tree"]))
        for node_name in ["turn_flow_spec", "decision_ui_spec", "runtime_wiring_spec"]:
            dynamic_spec_tree.pop(node_name, None)

        result = review_dynamic_spec_tree(
            design_input=design_input,
            dynamic_spec_tree=dynamic_spec_tree,
            static_spec_context=generation_result["static_spec_context"],
            routing_context={"mode": "greenfield_bootstrap", "genre": "boardgame"},
            analysis_context=generation_result["analysis_context"],
        )

        assert result["status"] == "blocked"
        assert any("turn_flow_spec" in error for error in result["errors"])
        assert any("decision_ui_spec" in error for error in result["errors"])
        assert any("runtime_wiring_spec" in error for error in result["errors"])

    def test_cp29_brownfield_patch_without_genre_contracts_is_blocked(self, compiler_module, project_root):
        """CP-29: Brownfield turn/ui patch 缺少 genre contract 时 reviewer 阻断。"""
        from compiler.analysis import build_baseline_snapshot
        from compiler.generation import generate_dynamic_spec_tree
        from compiler.intake import read_gdd
        from compiler.review import review_dynamic_spec_tree

        design_input = read_gdd(_default_gdd_path(project_root))
        baseline_snapshot = build_baseline_snapshot(_build_synthetic_project_state())
        generation_result = generate_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "brownfield_expansion",
                "genre": "boardgame",
                "target_stage": "prototype",
                "activated_skill_packs": ["genre-boardgame"],
                "projection_profile": "preview_static",
            },
            baseline_snapshot=baseline_snapshot,
            projection_profile="preview_static",
        )

        analysis_context = dict(generation_result["analysis_context"])
        analysis_context["delta_context"] = dict(generation_result["analysis_context"]["delta_context"])
        analysis_context["delta_context"]["delta_intent"] = "patch_existing_content"
        analysis_context["delta_context"]["contract_refs"] = [
            "SpecPatchContractModel",
            "RegressionValidationContractModel",
        ]

        result = review_dynamic_spec_tree(
            design_input=design_input,
            dynamic_spec_tree=generation_result["dynamic_spec_tree"],
            static_spec_context=generation_result["static_spec_context"],
            routing_context={"mode": "brownfield_expansion", "genre": "boardgame"},
            analysis_context=analysis_context,
        )

        assert result["status"] == "blocked"
        assert any("TurnFlowPatchContract" in error for error in result["errors"])
        assert any("DecisionUIPatchContract" in error for error in result["errors"])

    def test_cp30_delta_policy_flows_into_brownfield_trace_and_regression_focus(self, compiler_module, project_root):
        """CP-30: delta policy 能影响 Brownfield delta trace 与 regression focus。"""
        from compiler.analysis import build_baseline_snapshot
        from compiler.generation import generate_dynamic_spec_tree
        from compiler.intake import read_gdd

        design_input = read_gdd(_default_gdd_path(project_root))
        baseline_snapshot = build_baseline_snapshot(_build_synthetic_project_state())
        generation_result = generate_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "brownfield_expansion",
                "genre": "boardgame",
                "target_stage": "prototype",
                "activated_skill_packs": ["genre-boardgame"],
                "projection_profile": "preview_static",
            },
            baseline_snapshot=baseline_snapshot,
            projection_profile="preview_static",
        )

        delta_context = generation_result["analysis_context"]["delta_context"]
        generation_trace = generation_result["dynamic_spec_tree"]["generation_trace"]

        assert delta_context["delta_policy"]["regression_focus"] == [
            "existing_actor_presence",
            "boardgame-turn-smoke-check",
            "boardgame-decision-ui-smoke-check",
            "boardgame-core-loop-closure-check",
        ]
        assert generation_trace["delta_policy"]["high_risk_breakpoints"] == [
            "turn_flow_changed",
            "decision_ui_changed",
            "runtime_wiring_changed",
        ]
        assert "boardgame-turn-smoke-check" in delta_context["required_regression_checks"]
        assert "boardgame-core-loop-closure-check" in delta_context["required_regression_checks"]

    def test_cp31_contract_registry_common_and_genre_paths_are_readable(self, compiler_module):
        """CP-31: 合同 registry 中 Common + Genre 路径均可读取。"""
        from compiler.analysis import load_contract_bundle, load_contract_registry

        registry = load_contract_registry()
        contract_root = registry["contract_root"]
        selected_ids = [
            "SpecPatchContractModel",
            "RegressionValidationContractModel",
            "TurnFlowPatchContract",
            "DecisionUIPatchContract",
        ]

        for contract_id in selected_ids:
            bundle = load_contract_bundle(contract_id, registry=registry)
            assert os.path.exists(os.path.join(contract_root, bundle["entry"]["template_ref"]))
            assert os.path.exists(os.path.join(contract_root, bundle["entry"]["schema_ref"]))
            assert os.path.exists(bundle["manifest_path"])
            assert os.path.exists(bundle["template_path"])
            assert os.path.exists(bundle["schema_path"])

    def test_e2e23_brownfield_demo_simulated(self, project_root):
        """E2E-23: python Scripts/run_brownfield_demo.py simulated 成功。"""
        result = _run_script(project_root, "run_brownfield_demo.py")
        combined_output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, combined_output
        assert "append_actor" in combined_output
        assert "PieceO_1" in combined_output
        assert "succeeded" in combined_output

    def test_e2e24_playable_demo_simulated(self, project_root):
        """E2E-24: python Scripts/run_boardgame_playable_demo.py simulated 成功。"""
        result = _run_script(project_root, "run_boardgame_playable_demo.py")
        combined_output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, combined_output
        assert "BoardRuntimeActor" in combined_output
        assert "succeeded" in combined_output


def _default_gdd_path(project_root):
    """返回默认井字棋 GDD 路径。"""
    return os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")


def _build_synthetic_project_state():
    """构造 Brownfield baseline：只包含 Board + PieceX_1。"""
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


def _run_script(project_root, script_name):
    """统一运行项目层 demo 脚本，减少重复 subprocess 模板。"""
    demo_script = os.path.join(project_root, "Scripts", script_name)
    return subprocess.run(
        [sys.executable, demo_script],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
