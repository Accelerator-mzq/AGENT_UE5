# -*- coding: utf-8 -*-
"""
Phase 7 治理闭环 + JRPG 第二类型包测试
覆盖 task.md 中定义的 SS-14~SS-20 / CP-32~CP-40 / E2E-29~E2E-36。
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class TestPhase7GovernanceAndJRPG:
    """Phase 7 最小闭环测试。"""

    def test_ss14_base_domain_registry_discovers_ten_domains(self):
        """SS-14: base domain registry 可发现 10 个域。"""
        from Plugins.AgentBridge.Skills.base_domains import load_base_domain_registry

        registry = load_base_domain_registry()
        domain_ids = [entry["domain_id"] for entry in registry["domains"]]

        assert domain_ids == [
            "design_project_state_intake",
            "baseline_understanding",
            "delta_scope_analysis",
            "product_scope",
            "runtime_gameplay",
            "world_level",
            "presentation_asset",
            "config_platform",
            "qa_validation",
            "planning_governance",
        ]
        assert len(registry["domains"]) == 10
        assert all(entry["exists"] is True for entry in registry["domains"])

    def test_ss15_governance_base_domains_load(self):
        """SS-15: qa_validation 与 planning_governance 域可真实加载。"""
        from Plugins.AgentBridge.Skills.base_domains import load_base_domain_modules

        modules = load_base_domain_modules(["qa_validation", "planning_governance"])
        qa_module = modules["domain_map"]["qa_validation"]["module"]
        governance_module = modules["domain_map"]["planning_governance"]["module"]

        assert qa_module is not None
        assert governance_module is not None
        assert qa_module.build_domain_descriptor()["capabilities"] == [
            "validation_checkpoints",
            "regression_summary",
        ]
        assert governance_module.build_domain_descriptor()["capabilities"] == [
            "recovery_policy",
            "promotion_status",
        ]

    def test_ss16_jrpg_manifest_is_complete(self, project_root):
        """SS-16: JRPG manifest 字段完整且可解析。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_manifest

        manifest = load_pack_manifest(_jrpg_manifest_path(project_root))

        assert manifest["pack_id"] == "genre-jrpg"
        assert manifest["status"] == "phase7_governance_minimal"
        assert manifest["required_skills"] == ["battle_layout", "turn_queue", "command_menu"]
        assert manifest["review_extensions"] == ["jrpg_reviewer"]
        assert manifest["validation_extensions"] == ["jrpg_validator"]
        assert manifest["delta_policy"]["provider"] == "jrpg_delta_policy"
        assert "qa_validation" in manifest["dependencies"]["base_domains"]
        assert "planning_governance" in manifest["dependencies"]["base_domains"]
        assert "jrpg_spec" in manifest["outputs"]["typical_specs"]

    def test_ss17_jrpg_required_skills_load(self, compiler_module, project_root):
        """SS-17: JRPG required skills 可加载。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_manifest, load_pack_modules

        manifest = load_pack_manifest(_jrpg_manifest_path(project_root))
        modules = load_pack_modules(manifest)

        assert [entry["module_id"] for entry in modules["required_skills"]] == [
            "battle_layout",
            "turn_queue",
            "command_menu",
        ]
        assert all(entry["exists"] is True for entry in modules["required_skills"])
        assert all(entry["module"] is not None for entry in modules["required_skills"])

    def test_ss18_jrpg_review_validation_and_delta_modules_load(self, compiler_module, project_root):
        """SS-18: JRPG review / validation / delta policy 模块可加载。"""
        from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_manifest, load_pack_modules

        manifest = load_pack_manifest(_jrpg_manifest_path(project_root))
        modules = load_pack_modules(manifest)

        assert [entry["module_id"] for entry in modules["review_extensions"]] == ["jrpg_reviewer"]
        assert [entry["module_id"] for entry in modules["validation_extensions"]] == ["jrpg_validator"]
        assert [entry["module_id"] for entry in modules["delta_policies"]] == ["jrpg_delta_policy"]
        assert all(entry["module"] is not None for entry in modules["review_extensions"])
        assert all(entry["module"] is not None for entry in modules["validation_extensions"])
        assert all(entry["module"] is not None for entry in modules["delta_policies"])

    def test_ss19_governance_schema_and_contract_bundle_are_readable(self, compiler_module, project_root):
        """SS-19: governance 相关 schema / contract bundle 可读取。"""
        from compiler.analysis import load_contract_bundle, load_contract_registry

        run_plan_schema_path = os.path.join(
            project_root, "Plugins", "AgentBridge", "Schemas", "run_plan.schema.json"
        )
        reviewed_handoff_schema_path = os.path.join(
            project_root, "Plugins", "AgentBridge", "Schemas", "reviewed_handoff.schema.json"
        )

        with open(run_plan_schema_path, "r", encoding="utf-8") as file:
            run_plan_schema = json.load(file)
        with open(reviewed_handoff_schema_path, "r", encoding="utf-8") as file:
            reviewed_handoff_schema = json.load(file)

        registry = load_contract_registry()
        regression_bundle = load_contract_bundle("RegressionValidationContractModel", registry=registry)

        assert "validation_checkpoints" in run_plan_schema["properties"]
        assert "recovery_policy_ref" in run_plan_schema["properties"]
        assert "governance_context" in reviewed_handoff_schema["properties"]
        assert regression_bundle["manifest"]["contract_id"] == "RegressionValidationContractModel"
        assert os.path.exists(regression_bundle["manifest_path"])
        assert os.path.exists(regression_bundle["template_path"])
        assert os.path.exists(regression_bundle["schema_path"])

    def test_ss20_jrpg_router_activation_hits_second_pack(self, compiler_module, project_root):
        """SS-20: JRPG router activation 可命中第二类型包。"""
        from compiler.intake import read_gdd
        from Plugins.AgentBridge.Skills.genre_packs._core import resolve_active_pack

        design_input = read_gdd(_jrpg_gdd_path(project_root))
        selected_pack = resolve_active_pack(
            design_input=design_input,
            routing_context={"mode": "greenfield_bootstrap", "genre": "jrpg"},
        )

        assert selected_pack["pack_id"] == "genre-jrpg"
        assert selected_pack["router_result"]["matched"] is True
        assert "genre-jrpg" in selected_pack["router_result"]["activated_pack_ids"]

    def test_cp32_run_plan_contains_validation_checkpoints(self, compiler_module, project_root):
        """CP-32: run_plan 含 validation_checkpoints[]。"""
        from orchestrator.run_plan_builder import build_run_plan_from_handoff

        handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
        run_plan = build_run_plan_from_handoff(handoff)

        assert run_plan["status"] == "planned"
        assert len(run_plan["validation_checkpoints"]) >= 2
        assert any(
            checkpoint["checkpoint_id"] == "validate_scene_actor_count"
            for checkpoint in run_plan["validation_checkpoints"]
        )

    def test_cp33_run_plan_contains_recovery_policy_ref(self, compiler_module, project_root):
        """CP-33: run_plan 含 recovery_policy_ref。"""
        from orchestrator.run_plan_builder import build_run_plan_from_handoff

        handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
        run_plan = build_run_plan_from_handoff(handoff)

        assert run_plan["recovery_policy_ref"].startswith("recovery.jrpg.")
        assert run_plan["recovery_policies"]["on_validation_failure"] == "review_handoff_and_retry"

    def test_cp34_execution_report_contains_regression_summary(
        self, compiler_module, project_root, workspace_tmp_path
    ):
        """CP-34: 执行报告含 regression_summary。"""
        _, result = _execute_jrpg_handoff_simulated(project_root, workspace_tmp_path)
        regression_summary = result["execution_report"]["regression_summary"]

        assert regression_summary["status"] == "captured"
        assert regression_summary["delta_intent"] == "greenfield_bootstrap"
        assert "BattleArena" in regression_summary["added_actor_names"]

    def test_cp35_execution_report_contains_snapshot_ref(
        self, compiler_module, project_root, workspace_tmp_path
    ):
        """CP-35: 执行报告含 snapshot_ref。"""
        _, result = _execute_jrpg_handoff_simulated(project_root, workspace_tmp_path)
        snapshot_ref = result["execution_report"]["snapshot_ref"]

        assert snapshot_ref
        assert os.path.exists(snapshot_ref)
        with open(snapshot_ref, "r", encoding="utf-8") as file:
            snapshot_manifest = json.load(file)
        assert {"baseline_ref", "digest", "source_report", "created_at"}.issubset(snapshot_manifest.keys())

    def test_cp36_execution_report_contains_promotion_status(
        self, compiler_module, project_root, workspace_tmp_path
    ):
        """CP-36: 执行报告含 promotion_status。"""
        _, result = _execute_jrpg_handoff_simulated(project_root, workspace_tmp_path)
        promotion_status = result["execution_report"]["promotion_status"]

        assert promotion_status["current_state"] == "approved"
        assert promotion_status["snapshot_ref"]
        assert len(promotion_status["transitions"]) >= 2
        assert promotion_status["audit_note"]

    def test_cp37_base_domains_are_written_back_to_governance_context(self, compiler_module, project_root):
        """CP-37: base domains 激活结果可写回治理上下文。"""
        handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")

        assert handoff["governance_context"]["phase"] == "Phase 7"
        assert handoff["governance_context"]["governance_lane"] == "phase7_minimal"
        assert handoff["governance_context"]["base_domain_refs"] == [
            "product_scope",
            "runtime_gameplay",
            "presentation_asset",
            "qa_validation",
            "planning_governance",
        ]
        assert handoff["metadata"]["base_domain_refs"] == handoff["governance_context"]["base_domain_refs"]

    def test_cp38_jrpg_greenfield_compile_generates_minimal_spec_tree(self, compiler_module, project_root):
        """CP-38: JRPG Greenfield compile 生成最小 spec tree。"""
        from compiler.generation import generate_dynamic_spec_tree
        from compiler.intake import read_gdd

        design_input = read_gdd(_jrpg_gdd_path(project_root))
        result = generate_dynamic_spec_tree(
            design_input=design_input,
            routing_context={
                "mode": "greenfield_bootstrap",
                "genre": "jrpg",
                "target_stage": "vertical_slice",
                "activated_skill_packs": ["genre-jrpg"],
                "projection_profile": "preview_static",
            },
            projection_profile="preview_static",
        )
        tree = result["dynamic_spec_tree"]
        actor_names = [actor["actor_name"] for actor in tree["scene_spec"]["actors"]]

        assert {
            "world_build_spec",
            "jrpg_spec",
            "battle_layout_spec",
            "turn_queue_spec",
            "command_menu_spec",
            "runtime_wiring_spec",
            "validation_spec",
            "scene_spec",
            "generation_trace",
        }.issubset(tree.keys())
        assert actor_names == ["BattleArena", "HeroUnit_1", "EnemyUnit_1", "CommandMenuAnchor"]
        assert tree["generation_trace"]["skill_pack_id"] == "genre-jrpg"

    def test_cp39_missing_governance_prerequisites_block_plan(self, compiler_module, project_root):
        """CP-39: 缺失治理前置项时计划层可阻断。"""
        from orchestrator.run_plan_builder import build_run_plan_from_handoff

        handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
        handoff["governance_context"]["base_domain_refs"] = []
        handoff["metadata"]["base_domain_refs"] = []

        run_plan = build_run_plan_from_handoff(handoff)

        assert run_plan["status"] == "failed"
        assert any("base_domain_refs" in blocker for blocker in run_plan["context"]["planning_blockers"])
        assert run_plan["recovery_policy_ref"].startswith("recovery.jrpg.")

    def test_cp40_jrpg_brownfield_delta_expresses_minimal_increment(self, compiler_module, project_root):
        """CP-40: JRPG Brownfield delta 可表达最小增量。"""
        handoff = _build_jrpg_handoff(
            project_root,
            mode="brownfield_expansion",
            project_state=_build_synthetic_jrpg_project_state(),
        )
        delta_tree = handoff["dynamic_spec_tree"]
        delta_actor_names = [actor["actor_name"] for actor in delta_tree["scene_spec"]["actors"]]

        assert handoff["status"] == "reviewed"
        assert delta_tree["tree_type"] == "delta"
        assert handoff["delta_context"]["delta_intent"] == "append_actor"
        assert delta_actor_names == ["EnemyUnit_1", "CommandMenuAnchor"]
        assert "jrpg-battle-loop-smoke-check" in handoff["delta_context"]["required_regression_checks"]

    def test_e2e29_governance_simulated_succeeds(self, project_root):
        """E2E-29: governance simulated 成功。"""
        result = _run_python_script(project_root, "run_greenfield_demo.py", "simulated")
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, output
        assert "Handoff ID:" in output
        assert "execution_report_" in output
        assert "succeeded" in output

    def test_e2e30_failure_path_returns_recovery_suggestion(self, compiler_module, project_root):
        """E2E-30: 治理失败路径能返回 recovery suggestion。"""
        from orchestrator.run_plan_builder import build_run_plan_from_handoff

        handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
        handoff["governance_context"]["base_domain_refs"] = []
        handoff["metadata"]["base_domain_refs"] = []

        run_plan = build_run_plan_from_handoff(handoff)

        assert run_plan["status"] == "failed"
        assert run_plan["recovery_policy_ref"].startswith("recovery.jrpg.")
        assert run_plan["recovery_policies"]["on_blocked"] == "require_manual_governance_review"

    def test_e2e31_snapshot_manifest_is_written_in_simulated_path(
        self, compiler_module, project_root, workspace_tmp_path
    ):
        """E2E-31: simulated 路径能写出 snapshot manifest。"""
        _, result = _execute_jrpg_handoff_simulated(project_root, workspace_tmp_path)
        snapshot_ref = result["execution_report"]["snapshot_ref"]

        assert snapshot_ref
        assert os.path.exists(snapshot_ref)

    def test_e2e32_promotion_audit_is_written_in_simulated_path(
        self, compiler_module, project_root, workspace_tmp_path
    ):
        """E2E-32: simulated 路径能留下 minimal promotion 审计。"""
        _, result = _execute_jrpg_handoff_simulated(project_root, workspace_tmp_path)
        promotion_status = result["execution_report"]["promotion_status"]

        assert promotion_status["current_state"] == "approved"
        assert len(promotion_status["transitions"]) >= 2
        assert promotion_status["audit_note"] == "Phase 7 最小 promotion 审计记录"

    def test_e2e33_jrpg_simulated_compile_generates_handoff(self, project_root):
        """E2E-33: JRPG simulated 编译成功。"""
        result = _run_python_script(
            project_root,
            "run_jrpg_turn_based_demo.py",
            "simulated",
            "greenfield_bootstrap",
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, output
        assert "Handoff ID:" in output
        assert "reviewed" in output
        assert "Draft Handoff:" in output

    def test_e2e34_jrpg_simulated_execution_succeeds(self, project_root):
        """E2E-34: JRPG simulated 端到端成功。"""
        result = _run_python_script(
            project_root,
            "run_jrpg_turn_based_demo.py",
            "simulated",
            "greenfield_bootstrap",
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, output
        assert "execution_report_" in output
        assert "succeeded" in output

    def test_e2e35_jrpg_real_ue5_smoke_succeeds_and_writes_evidence(self, project_root):
        """E2E-35: JRPG 真实 UE5 smoke 成功并写出 6 张证据图。"""
        result = _run_python_script(
            project_root,
            "run_jrpg_turn_based_demo.py",
            "bridge_rc_api",
            "greenfield_bootstrap",
        )
        output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, output

        smoke_report_path = _extract_report_path_from_output(output, "PHASE7_SMOKE_REPORT")
        acceptance_report_path = _extract_report_path_from_output(output, "PHASE7_ACCEPTANCE_REPORT")

        assert smoke_report_path and os.path.exists(smoke_report_path), output
        assert acceptance_report_path and os.path.exists(acceptance_report_path), output

        smoke_report = _load_json(smoke_report_path)
        acceptance_report = _load_json(acceptance_report_path)
        check_details = acceptance_report["checks"]["E2E-35"]["details"]

        assert smoke_report["report_type"] == "phase7_jrpg_runtime_smoke"
        assert smoke_report["bridge_mode"] == "bridge_rc_api"
        assert smoke_report["mode"] == "greenfield_bootstrap"
        assert smoke_report["rc_ready"] is True
        assert smoke_report["overall_status"] == "passed"
        assert smoke_report["layout_assertions"]["overall_passed"] is True
        assert smoke_report["structure_assertions"]["overall_passed"] is True

        for actor_name in ["BattleArena", "HeroUnit_1", "EnemyUnit_1", "CommandMenuAnchor"]:
            assert smoke_report["actor_presence"][actor_name]["status"] == "passed"

        assert acceptance_report["report_type"] == "phase7_jrpg_runtime_acceptance"
        assert acceptance_report["overall_status"] == "passed"
        assert acceptance_report["checks"]["E2E-35"]["status"] == "passed"

        for key in [
            "overview_oblique",
            "topdown_alignment",
            "actor_battlearena_closeup",
            "actor_herounit_1_closeup",
            "actor_enemyunit_1_closeup",
            "actor_commandmenuanchor_closeup",
        ]:
            screenshot_path = check_details["screenshots"][key]
            assert screenshot_path and os.path.exists(screenshot_path)

        assert check_details["note_path"] and os.path.exists(check_details["note_path"])
        assert check_details["log_path"] and os.path.exists(check_details["log_path"])

    def test_e2e36_boardgame_regression_entries_remain_runnable(self, project_root):
        """E2E-36: boardgame 回归仍保持可跑。"""
        greenfield, greenfield_reports = _run_python_script_and_collect_reports(
            project_root,
            "run_greenfield_demo.py",
            "simulated",
        )
        brownfield, brownfield_reports = _run_python_script_and_collect_reports(
            project_root,
            "run_brownfield_demo.py",
            "simulated",
        )
        playable, playable_reports = _run_python_script_and_collect_reports(
            project_root,
            "run_boardgame_playable_demo.py",
            "simulated",
        )

        assert greenfield.returncode == 0, f"{greenfield.stdout}\n{greenfield.stderr}"
        assert brownfield.returncode == 0, f"{brownfield.stdout}\n{brownfield.stderr}"
        assert playable.returncode == 0, f"{playable.stdout}\n{playable.stderr}"

        greenfield_execution_report = _find_single_report(
            greenfield_reports, "execution_report_handoff.boardgame.prototype."
        )
        brownfield_execution_report = _find_single_report(
            brownfield_reports, "execution_report_handoff.boardgame.prototype."
        )
        playable_execution_report = _find_single_report(
            playable_reports, "execution_report_handoff.boardgame.prototype."
        )

        for report_path in [
            greenfield_execution_report,
            brownfield_execution_report,
            playable_execution_report,
        ]:
            report = _load_json(report_path)
            assert report["report_type"] == "execution_report"
            assert report["execution_status"] == "succeeded"
            assert report["regression_summary"]["status"] == "captured"
            assert report["snapshot_ref"] and os.path.exists(report["snapshot_ref"])
            assert report["promotion_status"]["current_state"] == "approved"
            assert report["promotion_status"]["snapshot_ref"] and os.path.exists(
                report["promotion_status"]["snapshot_ref"]
            )
            assert len(report["promotion_status"]["transitions"]) >= 2

        playable_acceptance_report = _find_single_report(playable_reports, "phase6_runtime_acceptance_")
        playable_acceptance = _load_json(playable_acceptance_report)
        assert playable_acceptance["report_type"] == "phase6_runtime_acceptance"
        assert playable_acceptance["overall_status"] == "passed"

    def test_phase7_governance_audit_summary_can_cover_execution_report(
        self, compiler_module, project_root, workspace_tmp_path
    ):
        """Phase 7 附加校验：治理审计摘要可统一覆盖 snapshot 与 promotion。"""
        from Scripts.validation.phase7_governance_audit import write_governance_audit_summary

        _, result = _execute_jrpg_handoff_simulated(project_root, workspace_tmp_path)
        written = write_governance_audit_summary(
            str(workspace_tmp_path / "reports"),
            "phase7_pytest_governance_audit",
            [("jrpg_simulated", result["report_path"], None)],
        )

        assert os.path.exists(written["json_path"])
        assert os.path.exists(written["md_path"])
        audit_payload = _load_json(written["json_path"])
        assert audit_payload["report_type"] == "phase7_governance_audit_summary"
        assert audit_payload["overall_status"] == "passed"
        assert audit_payload["entries"][0]["checks"]["snapshot_manifest_complete"]["passed"] is True
        assert audit_payload["entries"][0]["checks"]["promotion_status_complete"]["passed"] is True

    def test_phase7_jrpg_pack_consistency_payload_is_stable(self, compiler_module, project_root):
        """Phase 7 附加校验：JRPG pack 一致性负载能证明三条入口复用同一骨架。"""
        from compiler.intake import read_gdd
        from Plugins.AgentBridge.Skills.genre_packs._core import (
            load_pack_manifest,
            load_pack_modules,
            resolve_active_pack,
        )
        from Scripts.validation.phase7_governance_audit import build_jrpg_pack_consistency_payload

        greenfield_handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
        brownfield_handoff = _build_jrpg_handoff(
            project_root,
            mode="brownfield_expansion",
            project_state=_build_synthetic_jrpg_project_state(),
        )
        smoke_handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
        design_input = read_gdd(_jrpg_gdd_path(project_root))
        router_results = {
            "greenfield": resolve_active_pack(design_input=design_input, routing_context=greenfield_handoff["routing_context"]),
            "brownfield": resolve_active_pack(design_input=design_input, routing_context=brownfield_handoff["routing_context"]),
            "smoke": resolve_active_pack(design_input=design_input, routing_context=smoke_handoff["routing_context"]),
        }
        pack_manifest = load_pack_manifest(_jrpg_manifest_path(project_root))
        pack_modules = load_pack_modules(pack_manifest)

        payload = build_jrpg_pack_consistency_payload(
            greenfield_handoff=greenfield_handoff,
            brownfield_handoff=brownfield_handoff,
            smoke_handoff=smoke_handoff,
            router_results=router_results,
            pack_modules=pack_modules,
        )

        assert payload["report_type"] == "phase7_jrpg_pack_consistency"
        assert payload["overall_status"] == "passed"
        assert payload["checks"]["all_paths_use_same_pack_id"]["passed"] is True
        assert payload["checks"]["router_always_hits_jrpg_pack"]["passed"] is True


def _jrpg_manifest_path(project_root: str) -> str:
    """返回 JRPG pack manifest 路径。"""
    return os.path.join(
        project_root,
        "Plugins",
        "AgentBridge",
        "Skills",
        "genre_packs",
        "jrpg",
        "pack_manifest.yaml",
    )


def _jrpg_gdd_path(project_root: str) -> str:
    """返回 JRPG GDD 路径。"""
    return os.path.join(project_root, "ProjectInputs", "GDD", "jrpg_turn_based_v1.md")


def _build_jrpg_handoff(project_root: str, mode: str, project_state: dict | None = None) -> dict:
    """构建 JRPG handoff，供 Phase 7 测试复用。"""
    from compiler.handoff import build_handoff
    from compiler.intake import read_gdd

    design_input = read_gdd(_jrpg_gdd_path(project_root))
    effective_project_state = project_state or {
        "project_name": "Mvpv4TestCodex",
        "engine_version": "UE5.5.4",
        "current_level": "/Game/Maps/TestMap",
        "actor_count": 0,
        "is_empty": True,
        "actors": [],
        "has_existing_content": False,
        "has_baseline": False,
        "baseline_refs": [],
        "registry_refs": [],
        "known_issues_summary": [],
        "current_project_state_digest": f"pytest-{mode}",
    }

    return build_handoff(
        design_input=design_input,
        mode=mode,
        project_state=effective_project_state,
        target_stage="vertical_slice",
        projection_profile="preview_static",
    )


def _execute_jrpg_handoff_simulated(project_root: str, workspace_tmp_path: Path) -> tuple[dict, dict]:
    """执行 JRPG simulated handoff，并返回 handoff 与结果。"""
    from compiler.handoff import serialize_handoff
    from orchestrator.handoff_runner import run_from_handoff

    handoff = _build_jrpg_handoff(project_root, mode="greenfield_bootstrap")
    draft_dir = workspace_tmp_path / "handoffs" / "draft"
    approved_dir = workspace_tmp_path / "handoffs" / "approved"
    report_dir = workspace_tmp_path / "reports"
    draft_dir.mkdir(parents=True, exist_ok=True)
    approved_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)

    serialize_handoff(handoff, str(draft_dir), "yaml")
    approved_handoff = dict(handoff)
    approved_handoff["status"] = "approved_for_execution"
    approved_path = serialize_handoff(approved_handoff, str(approved_dir), "yaml")

    result = run_from_handoff(
        approved_path,
        report_output_dir=str(report_dir),
        bridge_mode="simulated",
    )
    return handoff, result


def _build_synthetic_jrpg_project_state() -> dict:
    """构造 JRPG Brownfield baseline。"""
    actors = [
        {
            "actor_name": "BattleArena",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.BattleArena",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [0.0, 0.0, 0.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [6.0, 6.0, 0.2],
            },
            "tags": ["Baseline"],
        },
        {
            "actor_name": "HeroUnit_1",
            "actor_path": "/Game/Maps/TestMap.TestMap:PersistentLevel.HeroUnit_1",
            "class": "/Script/Engine.StaticMeshActor",
            "transform": {
                "location": [-180.0, 0.0, 50.0],
                "rotation": [0.0, 0.0, 0.0],
                "relative_scale3d": [0.8, 0.8, 1.6],
            },
            "tags": ["Baseline"],
        },
    ]
    return {
        "project_name": "Mvpv4TestCodex",
        "engine_version": "UE5.5.4",
        "current_level": "/Game/Maps/TestMap",
        "actor_count": len(actors),
        "is_empty": False,
        "actors": actors,
        "has_existing_content": True,
        "has_baseline": False,
        "baseline_refs": [],
        "registry_refs": [],
        "known_issues_summary": [],
        "current_project_state_digest": "pytest-jrpg-brownfield",
    }


def _run_python_script(project_root: str, script_name: str, *args: str) -> subprocess.CompletedProcess:
    """统一运行项目层 demo 脚本。"""
    script_path = os.path.join(project_root, "Scripts", script_name)
    return subprocess.run(
        [sys.executable, script_path, *args],
        cwd=project_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_python_script_and_collect_reports(
    project_root: str,
    script_name: str,
    *args: str,
) -> tuple[subprocess.CompletedProcess, list[str]]:
    """运行 demo 脚本，并收集本次新增的 report 文件。"""
    dated_report_dir = os.path.join(
        project_root,
        "ProjectState",
        "Reports",
        datetime.now().strftime("%Y-%m-%d"),
    )
    os.makedirs(dated_report_dir, exist_ok=True)

    before_files = {
        os.path.join(dated_report_dir, file_name)
        for file_name in os.listdir(dated_report_dir)
        if file_name.endswith(".json")
    }
    result = _run_python_script(project_root, script_name, *args)
    after_files = {
        os.path.join(dated_report_dir, file_name)
        for file_name in os.listdir(dated_report_dir)
        if file_name.endswith(".json")
    }
    new_files = sorted(list(after_files - before_files), key=os.path.getmtime)
    return result, new_files


def _find_single_report(report_paths: list[str], file_name_prefix: str) -> str:
    """从本轮新增报告里按前缀挑出唯一目标文件。"""
    matches = [
        report_path
        for report_path in report_paths
        if os.path.basename(report_path).startswith(file_name_prefix)
    ]
    assert matches, f"未找到报告前缀: {file_name_prefix}，已有: {report_paths}"
    assert len(matches) == 1, f"报告前缀匹配不唯一: {file_name_prefix}，命中: {matches}"
    return matches[0]


def _extract_report_path_from_output(output: str, marker: str) -> str:
    """从 demo 脚本标准输出中提取结构化报告路径。"""
    match = re.search(rf"{marker}=(.+)", output)
    if not match:
        return ""
    return match.group(1).strip()


def _load_json(file_path: str) -> dict:
    """读取 JSON 文件。"""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
