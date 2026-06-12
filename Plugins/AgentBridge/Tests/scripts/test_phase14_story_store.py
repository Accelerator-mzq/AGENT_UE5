# -*- coding: utf-8 -*-
"""DMP-13~20: story 状态机——fetch/submit 流转、依赖门、幂等重入、.part 事务、velocity。"""
import importlib.util
import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _story(sid, deps=None, status="pending"):
    return {"story_schema_version": "1.0.0", "story_id": sid, "batch_id": "v0",
            "story_kind": "capability", "capability_id": f"cap-{sid}", "instance_id": sid,
            "evidence_class": "Logic", "depends_on": deps or [],
            "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                          "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                          "template_dir": None, "construction_manifest_path": "m.md", "extra_paths": []},
            "acceptance_criteria": ["x"], "status": status, "attempts": 0, "manifest_version": "1.0.0"}


@pytest.fixture
def run_dir(workspace_tmp_path):
    """构造假 run 目录:demo_plan.json + stories/。"""
    stories = [_story("story-a"), _story("story-b", deps=["story-a"])]
    plan = {"plan_schema_version": "1.0.0", "run_id": "run-test", "source_graph_id": "g",
            "manifest_version": "1.0.0",
            "batches": [{"batch_id": "v0", "story_ids": ["story-a", "story-b"]}]}
    (workspace_tmp_path / "stories").mkdir()
    (workspace_tmp_path / "demo_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    for s in stories:
        (workspace_tmp_path / "stories" / f"{s['story_id']}.json").write_text(
            json.dumps(s, ensure_ascii=False), encoding="utf-8")
    return workspace_tmp_path


class TestStoryStore:
    def test_dmp13_fetch_next_respects_plan_order_and_deps(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        story = store.fetch(None)
        assert story["story_id"] == "story-a" and story["status"] == "in_progress"

    def test_dmp14_dependent_story_blocked_until_dep_verified(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        with pytest.raises(ValueError, match="前置"):
            store.fetch("story-b")

    def test_dmp15_fetch_in_progress_is_idempotent_reentry(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        first = store.fetch(None)
        again = store.fetch(first["story_id"])
        assert again["status"] == "in_progress" and again["attempts"] == first["attempts"]

    def test_dmp16_submit_pass_marks_verified_and_archives_evidence(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        out = store.submit("story-a", {"files_changed": ["x.cpp"]},
                           {"status": "verified", "errors": []})
        assert out["status"] == "verified"
        on_disk = json.loads((run_dir / "stories" / "story-a.json").read_text(encoding="utf-8"))
        assert on_disk["status"] == "verified" and on_disk["evidence"] == {"files_changed": ["x.cpp"]}

    def test_dmp17_submit_reject_returns_in_progress_and_bumps_attempts(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        out = store.submit("story-a", {}, {"status": "rejected", "errors": ["缺 smoke_report"]})
        assert out["status"] == "in_progress" and out["attempts"] == 1
        assert out["submit_errors"] == ["缺 smoke_report"]

    def test_dmp18_verified_unlocks_dependent(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        store.submit("story-a", {"files_changed": []}, {"status": "verified", "errors": []})
        nxt = store.fetch(None)
        assert nxt["story_id"] == "story-b"

    def test_dmp19_atomic_write_no_part_residue(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        assert not list((run_dir / "stories").glob("*.part"))

    def test_dmp20_velocity_appends_fetch_and_submit_events(self, run_dir):
        ss = _load("story_store")
        vel = _load("velocity")
        store = ss.StoryStore(run_dir)
        story = store.fetch(None)
        vel.append_event(run_dir, {"kind": "fetch", "story_id": story["story_id"]})
        vel.append_event(run_dir, {"kind": "submit", "story_id": story["story_id"], "result": "verified"})
        log = json.loads((run_dir / "velocity_log.json").read_text(encoding="utf-8"))
        assert [e["kind"] for e in log["events"]] == ["fetch", "submit"]
        assert all("ts" in e for e in log["events"])
