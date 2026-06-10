# -*- coding: utf-8 -*-
"""SKS-02/SKS-08: 注册表扫描与 synthesized 审批过滤。"""
import importlib.util
import logging
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REAL_TEMPLATES_ROOT = PLUGIN_ROOT / "SkillTemplates"

# SKS-04 锁定的 16 个 fragment_family 值(与原 FRAGMENT_FAMILY_MAP 硬编码一致)
EXPECTED_16_FAMILIES = {
    "board_topology_spec", "tile_system_spec", "turn_flow_spec", "dice_rule_spec",
    "property_economy_spec", "player_management_spec", "jail_rule_spec",
    "start_screen_spec", "main_menu_spec", "settings_spec", "pause_spec",
    "results_spec", "hud_spec", "input_foundation_spec", "audio_foundation_spec",
    "platform_foundation_spec",
}


def _load():
    spec = importlib.util.spec_from_file_location(
        "registry_scan", PLUGIN_ROOT / "Compiler" / "stages" / "registry_scan.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestRegistryScan:
    def test_sks02_real_templates_cover_all_16_capabilities(self):
        """SKS-02: 真实模板树扫描出与原硬编码表相同的 16 个 capability。"""
        rs = _load()
        registry = rs.scan_capability_registry(REAL_TEMPLATES_ROOT)
        expected = {
            "gameplay-board-topology", "gameplay-tile-system", "gameplay-turn-loop",
            "gameplay-dice", "gameplay-economy", "gameplay-player-management",
            "gameplay-jail", "baseline-start-screen", "baseline-main-menu",
            "baseline-settings", "baseline-pause", "baseline-results", "baseline-hud",
            "baseline-input-foundation", "baseline-audio-foundation",
            "baseline-platform-foundation",
        }
        assert set(registry.keys()) == expected
        # 抽查双绑定模板:turn-loop 与 dice 同指一个 template_id
        assert registry["gameplay-turn-loop"]["template_id"] == "monopoly.turn_and_dice_flow.phase1"
        assert registry["gameplay-dice"]["template_id"] == "monopoly.turn_and_dice_flow.phase1"
        # 占位节点来自 registry_placeholders.yaml
        assert registry["baseline-input-foundation"]["template_id"] == "baseline.input_foundation.presence_only"

    def test_sks08_synthesized_requires_approved(self, tmp_path):
        """SKS-08: synthesized 区模板仅 review_status=approved 才入映射。"""
        rs = _load()
        syn = tmp_path / "synthesized" / "gameplay-auction"
        syn.mkdir(parents=True)
        manifest = {
            "template_id": "synthesized.gameplay-auction.v1",
            "review_status": "pending_review",
            "capability_bindings": [{
                "capability_id": "gameplay-auction",
                "instance_id": "skill-auction",
                "convergence_priority": 9,
                "related_clarification_items": [],
                "planning_notes": ["合成测试节点"],
                "fragment_family": "property_economy_spec",
            }],
        }
        (syn / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        registry = rs.scan_capability_registry(tmp_path)
        assert "gameplay-auction" not in registry  # 未审批,不可见

        manifest["review_status"] = "approved"
        (syn / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        registry = rs.scan_capability_registry(tmp_path)
        assert registry["gameplay-auction"]["template_source"] == "synthesized"

    def test_sks08b_official_wins_regardless_of_scan_order(self, tmp_path):
        """SKS-08b: synthesized 目录按 rglob 字母序先被扫到时,正式库同名 capability 仍必须获胜。

        回归场景:synthesized/aaa_cap 字母序排在 zzz_official 之前,
        单遍扫描的"先扫到的赢"语义会让 approved synthesized 错误压过正式库。
        """
        rs = _load()
        # synthesized 区:approved,字母序在前(aaa_cap)
        syn = tmp_path / "synthesized" / "aaa_cap"
        syn.mkdir(parents=True)
        syn_manifest = {
            "template_id": "synthesized.test-cap.v1",
            "review_status": "approved",
            "capability_bindings": [{
                "capability_id": "test-cap",
                "instance_id": "syn-inst",
                "convergence_priority": 9,
                "related_clarification_items": [],
                "planning_notes": ["synthesized 抢跑节点"],
                "fragment_family": "test_spec",
            }],
        }
        (syn / "manifest.yaml").write_text(
            yaml.safe_dump(syn_manifest, allow_unicode=True), encoding="utf-8"
        )
        # 正式库:无 review_status 字段,字母序在后(zzz_official)
        official = tmp_path / "zzz_official" / "test_cap"
        official.mkdir(parents=True)
        official_manifest = {
            "template_id": "official.test-cap.v1",
            "capability_bindings": [{
                "capability_id": "test-cap",
                "instance_id": "official-inst",
                "convergence_priority": 1,
                "related_clarification_items": [],
                "planning_notes": ["正式库节点"],
                "fragment_family": "test_spec",
            }],
        }
        (official / "manifest.yaml").write_text(
            yaml.safe_dump(official_manifest, allow_unicode=True), encoding="utf-8"
        )
        registry = rs.scan_capability_registry(tmp_path)
        # 正式库必须获胜,与扫描顺序无关
        assert registry["test-cap"]["instance_id"] == "official-inst"
        assert registry["test-cap"]["template_source"] == "plugin_skill_template"

    def test_binding_missing_required_field_skipped_with_warning(self, tmp_path, caplog):
        """缺必填字段的 binding 条目应跳过并告警(带文件路径+缺失字段),不崩溃,其余条目正常。"""
        rs = _load()
        tpl = tmp_path / "broken_tpl"
        tpl.mkdir(parents=True)
        manifest = {
            "template_id": "official.broken.v1",
            "capability_bindings": [
                {  # 缺 convergence_priority → 应跳过并 warning,不得 KeyError
                    "capability_id": "cap-broken",
                    "instance_id": "inst-broken",
                    "fragment_family": "broken_spec",
                },
                {  # 完整条目 → 应正常入表
                    "capability_id": "cap-ok",
                    "instance_id": "inst-ok",
                    "convergence_priority": 3,
                    "fragment_family": "ok_spec",
                },
            ],
        }
        (tpl / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        with caplog.at_level(logging.WARNING):
            registry = rs.scan_capability_registry(tmp_path)  # 不应抛 KeyError
        # 缺字段条目不入表,完整条目正常
        assert "cap-broken" not in registry
        assert registry["cap-ok"]["instance_id"] == "inst-ok"
        # 告警须包含文件路径与缺失字段名,便于定位
        warning_text = " ".join(r.getMessage() for r in caplog.records)
        assert "convergence_priority" in warning_text
        assert "manifest.yaml" in warning_text

    def test_family_whitelist_real_tree_covers_all_16(self):
        """execution_family_whitelist 对真实树:含 player_management_spec 且 16 个 family 全为子集。"""
        rs = _load()
        whitelist = rs.execution_family_whitelist(REAL_TEMPLATES_ROOT)
        assert "player_management_spec" in whitelist
        assert EXPECTED_16_FAMILIES <= whitelist

    def test_family_whitelist_includes_binding_only_family(self, tmp_path):
        """只出现在 binding fragment_family、不在宿主 can_emit_families 的 family 也被收录。"""
        rs = _load()
        tpl = tmp_path / "host_tpl"
        tpl.mkdir(parents=True)
        manifest = {
            "template_id": "official.host.v1",
            "can_emit_families": ["host_family_spec"],
            "capability_bindings": [{
                "capability_id": "cap-host",
                "instance_id": "inst-host",
                "convergence_priority": 1,
                # binding 专属 family,宿主 can_emit_families 不含它(对应 player_management_spec 场景)
                "fragment_family": "binding_only_spec",
            }],
        }
        (tpl / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        whitelist = rs.execution_family_whitelist(tmp_path)
        assert "host_family_spec" in whitelist
        assert "binding_only_spec" in whitelist
