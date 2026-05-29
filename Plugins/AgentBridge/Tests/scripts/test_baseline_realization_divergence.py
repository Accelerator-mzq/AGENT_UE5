"""Baseline realization_eligible 发散落地修复 —— 离线回归测试。

house style：手写断言 + __main__ 运行器，python 直接跑。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Compiler.stages import domain_skill_runtime as dsr  # noqa: E402


def test_selected_realization_from_converged_maps_choices():
    """converged_choices / convergence_decisions 都能被提取成 dimension->choice 映射。"""
    converged_pack = {
        "converged_choices": [
            {"dimension_id": "dim-a", "chosen_candidate_name": "方案甲"},
            {"dimension_id": "dim-b", "chosen_candidate": "方案乙"},
        ]
    }
    result = dsr._selected_realization_from_converged(converged_pack)
    assert result == {"dim-a": "方案甲", "dim-b": "方案乙"}, result


def test_selected_realization_from_converged_empty():
    """空 pack 返回空 dict，不抛异常。"""
    assert dsr._selected_realization_from_converged({}) == {}
    assert dsr._selected_realization_from_converged(None) == {}


def test_selected_realization_from_converged_uses_fallback_key():
    """仅含 convergence_decisions 备用键时也能提取。"""
    converged_pack = {
        "convergence_decisions": [
            {"dimension_id": "dim-c", "chosen_candidate_name": "方案丙"},
        ]
    }
    assert dsr._selected_realization_from_converged(converged_pack) == {"dim-c": "方案丙"}


def test_selected_realization_from_converged_third_level_fallback():
    """choice 仅含 selected_candidate_id 时走第三级回退。"""
    converged_pack = {
        "converged_choices": [
            {"dimension_id": "dim-d", "selected_candidate_id": "cand-7"},
        ]
    }
    assert dsr._selected_realization_from_converged(converged_pack) == {"dim-d": "cand-7"}


def test_baseline_eligible_emits_selected_realization():
    """realization_eligible baseline 节点：带 converged_pack 时写入 selected_realization。"""
    node = {"instance_id": "skill-baseline-hud", "capability_id": "baseline-hud"}
    capability = {
        "baseline_item": "HUD",
        "realization_class": "realization_eligible",
        "required_elements": ["current_player", "turn_number"],
    }
    converged_pack = {
        "converged_choices": [
            {"dimension_id": "dim-hud-density", "chosen_candidate_name": "紧凑列表密度"},
        ]
    }
    fragments = dsr._build_baseline_spec_fragment(
        node, capability, {}, converged_pack=converged_pack
    )
    spec = next(iter(fragments.values()))
    assert spec.get("selected_realization") == {"dim-hud-density": "紧凑列表密度"}, spec


def test_baseline_presence_only_no_selected_realization():
    """presence_only baseline：即使误传 converged_pack 也不写 selected_realization。"""
    node = {"instance_id": "skill-baseline-main-menu", "capability_id": "baseline-main-menu"}
    capability = {
        "baseline_item": "Main Menu",
        "realization_class": "presence_only",
        "required_elements": ["New Game", "Quit"],
    }
    fragments = dsr._build_baseline_spec_fragment(
        node, capability, {}, converged_pack={"converged_choices": [
            {"dimension_id": "x", "chosen_candidate_name": "y"}]}
    )
    spec = next(iter(fragments.values()))
    assert "selected_realization" not in spec, spec


def test_baseline_eligible_without_converged_pack_no_field():
    """realization_eligible 但未传 converged_pack（默认 None）时不写 selected_realization。"""
    node = {"instance_id": "skill-baseline-hud", "capability_id": "baseline-hud"}
    capability = {
        "baseline_item": "HUD",
        "realization_class": "realization_eligible",
        "required_elements": ["current_player", "turn_number"],
    }
    fragments = dsr._build_baseline_spec_fragment(node, capability, {})
    spec = next(iter(fragments.values()))
    assert "selected_realization" not in spec, spec


ALL_TESTS = [
    test_selected_realization_from_converged_maps_choices,
    test_selected_realization_from_converged_empty,
    test_selected_realization_from_converged_uses_fallback_key,
    test_selected_realization_from_converged_third_level_fallback,
    test_baseline_eligible_emits_selected_realization,
    test_baseline_presence_only_no_selected_realization,
    test_baseline_eligible_without_converged_pack_no_field,
]


def main() -> int:
    failures = []
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures.append((fn.__name__, repr(exc)))
            print(f"FAIL {fn.__name__}: {exc!r}")
    if failures:
        print(f"\n{len(failures)} failed / {len(ALL_TESTS)} total")
        return 1
    print(f"\nAll {len(ALL_TESTS)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
