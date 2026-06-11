# -*- coding: utf-8 -*-
"""SKS-04: fragment family 映射由注册表惰性派生,与原 16 条硬编码一致。"""
import importlib.util
import sys
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


def test_sks04_module_builder_equals_legacy():
    """锁被改模块本身:包导入 domain_skill_runtime,断言其惰性构建函数输出与 16 条硬编码一致。"""
    plugin_root_str = str(PLUGIN_ROOT)
    inserted = plugin_root_str not in sys.path
    if inserted:
        sys.path.insert(0, plugin_root_str)
    try:
        from Compiler.stages import domain_skill_runtime as d
        assert d._build_fragment_family_map() == EXPECTED_16
    finally:
        if inserted:
            sys.path.remove(plugin_root_str)
