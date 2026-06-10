# -*- coding: utf-8 -*-
"""SKS-02/SKS-08: 注册表扫描与 synthesized 审批过滤。"""
import importlib.util
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REAL_TEMPLATES_ROOT = PLUGIN_ROOT / "SkillTemplates"


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
