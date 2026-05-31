"""HUD 多专家协商 —— 纯逻辑单元测试（house style，离线可跑）。"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Tests.scripts import hud_multiexpert_core as core  # noqa: E402


def test_merge_dedup_and_records_proposers():
    """三专家维度合并：按 dimension_id 去重，proposed_by 记录提出者，保持首次出现顺序。"""
    lists = [
        ("ux-designer", [{"dimension_id": "hud.info_density", "name": "信息密度"},
                          {"dimension_id": "hud.player_display", "name": "玩家展示"}]),
        ("ui-programmer", [{"dimension_id": "hud.info_density", "name": "信息密度"},
                           {"dimension_id": "hud.refresh_rate", "name": "刷新频率"}]),
        ("art-director", [{"dimension_id": "hud.layout", "name": "布局"}]),
    ]
    merged = core.merge_discovered_dimensions(lists)
    ids = [d["dimension_id"] for d in merged]
    assert ids == ["hud.info_density", "hud.player_display", "hud.refresh_rate", "hud.layout"], ids
    by_id = {d["dimension_id"]: d for d in merged}
    assert by_id["hud.info_density"]["proposed_by"] == ["ux-designer", "ui-programmer"], by_id["hud.info_density"]
    assert by_id["hud.layout"]["proposed_by"] == ["art-director"]


def test_resolve_owner_priority_and_fallback():
    """owner = proposed_by 中按 priority 顺序的第一个；空 proposed_by 取 priority[0]。"""
    priority = ["ux-designer", "ui-programmer", "art-director"]
    assert core.resolve_owner(["ui-programmer", "ux-designer"], priority) == "ux-designer"
    assert core.resolve_owner(["art-director"], priority) == "art-director"
    assert core.resolve_owner([], priority) == "ux-designer"


def test_detect_convergence_agreement_and_abstain():
    """全表态者取值一致 → converged；不一致 → 否；弃权者不计入。"""
    stances = {
        "ux-designer":   {"d1": "A", "d2": "X"},
        "ui-programmer": {"d1": "A", "d2": "Y"},
        "art-director":  {"d1": "A"},  # 对 d2 弃权
    }
    res = core.detect_convergence(stances)
    assert res["d1"]["converged"] is True, res["d1"]
    assert res["d1"]["choices"] == {"ux-designer": "A", "ui-programmer": "A", "art-director": "A"}
    assert res["d2"]["converged"] is False, res["d2"]
    assert res["d2"]["choices"] == {"ux-designer": "X", "ui-programmer": "Y"}


def test_detect_convergence_single_voice_is_converged():
    """仅一方表态（其余弃权）视为趋同。"""
    stances = {"ux-designer": {"d3": "Z"}, "ui-programmer": {}, "art-director": {}}
    res = core.detect_convergence(stances)
    assert res["d3"]["converged"] is True, res["d3"]


def test_weighted_majority_owner_weight_and_tie():
    """owner 票权重 2 可压倒单票；普通多数胜出；空 choices 返回 None。"""
    assert core.weighted_majority_fallback(
        {"ux-designer": "A", "ui-programmer": "B", "art-director": "B"}, "ux-designer") == "A"
    assert core.weighted_majority_fallback(
        {"ux-designer": "B", "ui-programmer": "A", "art-director": "A"}, "ux-designer") == "B"
    assert core.weighted_majority_fallback(
        {"ux-designer": "A", "ui-programmer": "A", "art-director": "A"}, "art-director") == "A"
    assert core.weighted_majority_fallback({}, "ux-designer") is None
    # owner(art-director)未表态，A/B 各 1 票平票 → 取字典序最小 "A"
    assert core.weighted_majority_fallback(
        {"ux-designer": "B", "ui-programmer": "A"}, "art-director") == "A"


def test_compare_dimension_coverage():
    """对比两组维度 id：分出 only_in_multi / only_in_single / common，均排序。"""
    res = core.compare_dimension_coverage(
        multi_dim_ids=["hud.layout", "hud.info_density", "hud.refresh_rate"],
        single_dim_ids=["hud.info_density", "hud.layout"],
    )
    assert res["only_in_multi"] == ["hud.refresh_rate"], res
    assert res["only_in_single"] == [], res
    assert res["common"] == ["hud.info_density", "hud.layout"], res


def test_assemble_arbitration_normal():
    """全部 resolved：selected 取 final_choice，gaps 空。"""
    merged = [{"dimension_id": "hud.a", "proposed_by": ["ux-designer"]},
              {"dimension_id": "hud.b", "proposed_by": ["art-director"]}]
    arbitration = {
        "hud.a": {"final_choice": "方案A", "integration_note": "三方一致", "unresolved": False},
        "hud.b": {"final_choice": "方案B", "integration_note": "采纳美术", "unresolved": False},
    }
    stances = {"ux-designer": {"hud.a": "x", "hud.b": "y"}}
    selected, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    assert selected == {"hud.a": "方案A", "hud.b": "方案B"}, selected
    assert gaps == [], gaps


def test_assemble_arbitration_unresolved():
    """unresolved=true：selected 仍取 final_choice，但该维度进 gaps 附三方立场。"""
    merged = [{"dimension_id": "hud.a", "proposed_by": ["ux-designer"]}]
    arbitration = {"hud.a": {"final_choice": "总监择优X", "integration_note": "UX与美术对立", "unresolved": True}}
    stances = {"ux-designer": {"hud.a": "全显示"}, "art-director": {"hud.a": "极简"}}
    selected, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    assert selected == {"hud.a": "总监择优X"}, selected
    assert len(gaps) == 1, gaps
    assert gaps[0]["dimension_id"] == "hud.a"
    assert gaps[0]["resolved_by"] == "arbiter_unresolved"
    assert gaps[0]["integration_note"] == "UX与美术对立"
    assert gaps[0]["stances"] == {"ux-designer": "全显示", "art-director": "极简"}


def test_assemble_arbitration_missing():
    """合并维度在 arbitration 中缺失：selected 兜底空串 + gap 标 arbiter_missing。"""
    merged = [{"dimension_id": "hud.a", "proposed_by": ["ux-designer"]},
              {"dimension_id": "hud.missing", "proposed_by": ["ui-programmer"]}]
    arbitration = {"hud.a": {"final_choice": "方案A", "integration_note": "", "unresolved": False}}
    stances = {"ui-programmer": {"hud.missing": "我的主张"}}
    selected, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    assert selected == {"hud.a": "方案A", "hud.missing": ""}, selected
    assert len(gaps) == 1, gaps
    assert gaps[0]["dimension_id"] == "hud.missing"
    assert gaps[0]["resolved_by"] == "arbiter_missing"
    assert gaps[0]["stances"] == {"ui-programmer": "我的主张"}


ALL_TESTS = [
    test_merge_dedup_and_records_proposers,
    test_resolve_owner_priority_and_fallback,
    test_detect_convergence_agreement_and_abstain,
    test_detect_convergence_single_voice_is_converged,
    test_weighted_majority_owner_weight_and_tie,
    test_compare_dimension_coverage,
    test_assemble_arbitration_normal,
    test_assemble_arbitration_unresolved,
    test_assemble_arbitration_missing,
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
