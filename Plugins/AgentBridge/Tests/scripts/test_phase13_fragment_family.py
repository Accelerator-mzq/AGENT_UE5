# -*- coding: utf-8 -*-
"""SKS-04: FRAGMENT_FAMILY_MAP 由注册表派生,与原 16 条硬编码一致。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_16 = {
    "skill-board-topology": "board_topology_spec",
    "skill-tile-system": "tile_system_spec",
    "skill-turn-loop": "turn_flow_spec",
    "skill-dice": "dice_rule_spec",
    "skill-economy": "property_economy_spec",
    "skill-player-management": "player_management_spec",
    "skill-jail": "jail_rule_spec",
    "skill-baseline-start-screen": "start_screen_spec",
    "skill-baseline-main-menu": "main_menu_spec",
    "skill-baseline-settings": "settings_spec",
    "skill-baseline-pause": "pause_spec",
    "skill-baseline-results": "results_spec",
    "skill-baseline-hud": "hud_spec",
    "skill-baseline-input-foundation": "input_foundation_spec",
    "skill-baseline-audio-foundation": "audio_foundation_spec",
    "skill-baseline-platform-foundation": "platform_foundation_spec",
}


def test_sks04_family_map_derived_equals_legacy():
    spec = importlib.util.spec_from_file_location(
        "registry_scan", PLUGIN_ROOT / "Compiler" / "stages" / "registry_scan.py"
    )
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    registry = rs.scan_capability_registry(PLUGIN_ROOT / "SkillTemplates")
    derived = {
        cfg["instance_id"]: cfg["fragment_family"]
        for cfg in registry.values() if cfg.get("fragment_family")
    }
    assert derived == EXPECTED_16
