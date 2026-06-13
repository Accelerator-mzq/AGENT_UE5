# -*- coding: utf-8 -*-
"""PRX amend 组:呈现批/反馈批追加——锚点/幂等/链式依赖/确定性/CLI。"""
import importlib.util
import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    """动态加载 Compiler/demo_plan 自包含模块(与 test_phase14_* 同款模式)。"""
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PATHS = {
    "gdd_path": "ProjectInputs/GDD/x.md",
    "contract_path": "ProjectState/runs/r/root_skill_contract.json",
    "skill_graph_path": "ProjectState/runs/r/skill_graph.json",
    "construction_manifest_path": "ProjectInputs/ConstructionManifest/demo_plugin_standards.md",
    "ladder_path": "ProjectInputs/PresentationLadder/test_ladder.json",
    "feedback_dir": "ProjectState/runs/r/feedback",
    "doc_extra_paths": [],
}


def _plan_and_stories(verified_batches, pending_batches=()):
    """构造现状 plan + stories_by_id:verified_batches 全 verified,pending_batches 留批。"""
    batches, stories = [], {}
    for bid in list(verified_batches) + list(pending_batches):
        sid, did = f"story-{bid}-a", f"story-{bid}-docs"
        status = "verified" if bid in verified_batches else "pending"
        stories[sid] = {"story_id": sid, "status": status}
        stories[did] = {"story_id": did, "status": status}
        batches.append({"batch_id": bid, "story_ids": [sid, did]})
    plan = {"plan_schema_version": "1.0.0", "run_id": "r", "source_graph_id": "g",
            "manifest_version": "1.1.0", "batches": batches}
    return plan, stories


def _ladder_story(slug, claims=None):
    return {"story_slug": slug, "summary": "x", "evidence_class": "Integration",
            "requirements": ["req-1"], "interaction_claims": claims or []}


def _ladder(rung_stories=None):
    """rung_stories: {rung_id: [story...]};缺省三 rung 各一 story,rung3 带 supersedes。"""
    rung_stories = rung_stories or {1: [_ladder_story("s1a")], 2: [_ladder_story("s2a")],
                                    3: [_ladder_story("s3a")]}
    return {"ladder_schema_version": "1.0.0", "ladder_id": "ladder-test",
            "target_plugin_root": "Plugins/DemoX",
            "rungs": [{"rung_id": rid, "title": f"R{rid}", "gdd_anchors": [f"3.{rid}"],
                       "supersedes": (["Plugins/DemoX/Tests/R2Impl.cpp"] if rid == 3 else []),
                       "stories": stories}
                      for rid, stories in sorted(rung_stories.items())]}


class TestPresentationAmend:
    def test_p15a01_appends_three_presentation_batches(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "increment-1"], ["increment-2"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        ids = [b["batch_id"] for b in out["plan"]["batches"]]
        assert ids == ["v0", "increment-1", "increment-2",
                       "presentation-1", "presentation-2", "presentation-3"]

    def test_p15a02_story_ids_derived_from_slug(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        sids = {s["story_id"] for s in out["new_stories"]}
        assert "story-presentation-1-s1a" in sids and "story-presentation-1-docs" in sids

    def test_p15a03_first_story_anchored_on_last_verified_doc(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "increment-1"], ["increment-2"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        first = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-1-s1a"][0]
        assert first["depends_on"] == ["story-increment-1-docs"]

    def test_p15a04_pending_increment_does_not_block_or_anchor(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "increment-1"], ["increment-2"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        all_deps = {d for s in out["new_stories"] for d in s["depends_on"]}
        assert "story-increment-2-docs" not in all_deps and "story-increment-2-a" not in all_deps

    def test_p15a05_sequential_chain_within_batch(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        ladder = _ladder({1: [_ladder_story("first"), _ladder_story("second")]})
        out = a.build_presentation_amend(plan, st, ladder, "1.2.0", _PATHS)
        second = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-1-second"][0]
        assert second["depends_on"] == ["story-presentation-1-first"]

    def test_p15a06_doc_story_last_depends_members(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        ladder = _ladder({1: [_ladder_story("first"), _ladder_story("second")]})
        out = a.build_presentation_amend(plan, st, ladder, "1.2.0", _PATHS)
        batch = [b for b in out["plan"]["batches"] if b["batch_id"] == "presentation-1"][0]
        assert batch["story_ids"][-1] == "story-presentation-1-docs"
        doc = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-1-docs"][0]
        assert set(doc["depends_on"]) == {"story-presentation-1-first", "story-presentation-1-second"}

    def test_p15a07_idempotent_existing_batches_skipped(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "presentation-1"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        new_ids = [b["batch_id"] for b in out["plan"]["batches"]]
        assert new_ids.count("presentation-1") == 1
        first2 = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-2-s2a"][0]
        assert first2["depends_on"] == ["story-presentation-1-docs"]

    def test_p15a08_materials_carry_ladder_supersedes_manifest(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        s3 = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-3-s3a"][0]
        assert s3["materials"]["ladder_rung_path"] == _PATHS["ladder_path"]
        assert s3["materials"]["supersedes_paths"] == ["Plugins/DemoX/Tests/R2Impl.cpp"]
        assert s3["manifest_version"] == "1.2.0"
        assert s3["story_kind"] == "presentation"
        assert s3["story_schema_version"] == "1.1.0"

    def test_p15a09_deterministic_rung_order_input_invariant(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        ladder = _ladder()
        shuffled = dict(ladder)
        shuffled["rungs"] = list(reversed(ladder["rungs"]))
        assert a.build_presentation_amend(plan, st, ladder, "1.2.0", _PATHS) == \
               a.build_presentation_amend(plan, st, shuffled, "1.2.0", _PATHS)

    def test_p15a10_no_verified_base_fails_closed(self):
        a = _load("amend")
        plan, st = _plan_and_stories([], ["v0"])
        with pytest.raises(ValueError, match="基底"):
            a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)


def _entry(fid, status="open", phenomenon="现象X", expectation="期望Y"):
    return {"feedback_schema_version": "1.0.0", "feedback_id": fid, "window_id": "w1",
            "phenomenon": phenomenon, "expectation": expectation, "severity": "major",
            "related_rung": None, "related_capability": None, "status": status}


class TestFeedbackAmend:
    def test_p15a11_feedback_one_story_per_entry_plus_doc(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "presentation-1"])
        out = a.build_feedback_amend(plan, st, [_entry("fb-w1-01"), _entry("fb-w1-02")],
                                     "1.2.0", _PATHS)
        batch = out["plan"]["batches"][-1]
        assert batch["batch_id"] == "feedback-1"
        assert batch["story_ids"] == ["story-feedback-1-fb-w1-01", "story-feedback-1-fb-w1-02",
                                      "story-feedback-1-docs"]
        s1 = [s for s in out["new_stories"] if s["story_id"] == "story-feedback-1-fb-w1-01"][0]
        assert s1["story_kind"] == "feedback"
        assert s1["depends_on"] == ["story-presentation-1-docs"]
        assert s1["materials"]["feedback_path"] == f"{_PATHS['feedback_dir']}/fb-w1-01.json"
        assert any("现象X" in c for c in s1["acceptance_criteria"])
        # 批内链式依赖:第二条依赖第一条(防"全依赖 anchor"退化),doc 依赖全部成员
        s2 = [s for s in out["new_stories"] if s["story_id"] == "story-feedback-1-fb-w1-02"][0]
        assert s2["depends_on"] == ["story-feedback-1-fb-w1-01"]
        doc = [s for s in out["new_stories"] if s["story_id"] == "story-feedback-1-docs"][0]
        assert set(doc["depends_on"]) == {"story-feedback-1-fb-w1-01", "story-feedback-1-fb-w1-02"}

    def test_p15a12_feedback_batch_numbering_increments(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "feedback-1"])
        out = a.build_feedback_amend(plan, st, [_entry("fb-w2-01")], "1.2.0", _PATHS)
        assert out["plan"]["batches"][-1]["batch_id"] == "feedback-2"

    def test_p15a13_feedback_sorted_and_no_open_fails_closed(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        out = a.build_feedback_amend(
            plan, st, [_entry("fb-w1-02"), _entry("fb-w1-01")], "1.2.0", _PATHS)
        story_ids = out["plan"]["batches"][-1]["story_ids"]
        assert story_ids[0] == "story-feedback-1-fb-w1-01"
        assert story_ids[1] == "story-feedback-1-fb-w1-02"
        with pytest.raises(ValueError, match="open"):
            a.build_feedback_amend(plan, st, [_entry("fb-w1-01", status="resolved")],
                                   "1.2.0", _PATHS)
