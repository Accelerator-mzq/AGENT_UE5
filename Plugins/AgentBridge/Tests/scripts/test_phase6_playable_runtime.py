# -*- coding: utf-8 -*-
"""
Phase 6 Playable Runtime 测试
覆盖 genre pack core、完整 spec tree、runtime_playable handoff 与 simulated E2E。
"""

import json
import os
import subprocess
import sys

import pytest


class TestPhase6PlayableRuntime:
    """Phase 6 最小 playable runtime 链路测试。"""

    def test_ss08_pack_registry_and_modules_load(self, compiler_module):
        """SS-08: _core registry 能发现 boardgame pack，且模块可加载。"""
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
        """SS-09: boardgame manifest 覆盖 Phase 6 关键字段。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_registry

        manifest = load_pack_registry()["pack_map"]["genre-boardgame"]
        assert manifest["status"] == "phase6_playable_runtime"
        assert manifest["delta_policy"]["provider"] == "boardgame_delta_policy"
        assert manifest["review_extensions"] == ["boardgame_reviewer"]
        assert manifest["validation_extensions"] == ["boardgame_validator"]

    def test_ss10_genre_contracts_load(self, compiler_module):
        """SS-10: Genre contract 已登记并可加载。"""
        from compiler.analysis import load_contract_bundle, load_contract_registry

        registry = load_contract_registry()
        contract_ids = {entry["contract_id"] for entry in registry["contracts"]}
        assert {"TurnFlowPatchContract", "DecisionUIPatchContract"}.issubset(contract_ids)

        turn_bundle = load_contract_bundle("TurnFlowPatchContract", registry=registry)
        ui_bundle = load_contract_bundle("DecisionUIPatchContract", registry=registry)
        assert turn_bundle["template"]["target_spec"] == "turn_flow_spec"
        assert ui_bundle["schema"]["title"] == "DecisionUIPatchContract"

    def test_cp25_preview_static_generates_full_spec_tree(self, compiler_module, project_root):
        """CP-25: 默认 preview_static 仍生成完整树，并保持旧 preview actor 投影。"""
        from compiler.generation import generate_dynamic_spec_tree
        from compiler.intake import read_gdd

        design_input = read_gdd(os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md"))
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
        """CP-26: runtime_playable handoff 生成 runtime config，并投影到 runtime actor。"""
        from compiler.handoff import build_handoff
        from compiler.intake import get_project_state_snapshot, read_gdd

        design_input = read_gdd(os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md"))
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

    def test_cp27_reviewer_blocks_missing_turn_nodes(self, compiler_module):
        """CP-27: 缺失回合/UI/runtime 节点时 reviewer 必须阻断。"""
        from compiler.review import review_dynamic_spec_tree

        result = review_dynamic_spec_tree(
            design_input={
                "piece_catalog": [{"symbol": "X"}, {"symbol": "O"}],
                "prototype_preview": {"generate_preview": True, "piece_counts": {"X": 1, "O": 1}},
                "parsing_notes": {"unsupported_sections": []},
            },
            dynamic_spec_tree={
                "scene_spec": {"actors": []},
                "generation_trace": {"projection_profile": "preview_static"},
            },
            static_spec_context={"loaded_specs": {}, "required_spec_ids": []},
            routing_context={"mode": "greenfield_bootstrap", "genre": "boardgame"},
        )
        assert result["status"] == "blocked"
        assert any("turn_flow_spec" in error for error in result["errors"])

    def test_e2e22_playable_demo_simulated(self, project_root):
        """E2E-22: playable demo 的 simulated 模式可跑通。"""
        demo_script = os.path.join(project_root, "Scripts", "run_boardgame_playable_demo.py")
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
        assert "BoardRuntimeActor" in combined_output
        assert "succeeded" in combined_output
