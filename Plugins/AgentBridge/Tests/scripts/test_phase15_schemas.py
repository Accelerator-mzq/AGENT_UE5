# -*- coding: utf-8 -*-
"""PRX schema 组:demo_story/demo_plan 1.1.0 升版 + 新 schema(阶梯/反馈)+ 实例校验。

注:本文件 Task 1 先落 4 条(p15s01~04),Task 2 追加 p15s05~06,Task 11 追加 p15s07。
"""
import json
from pathlib import Path

import jsonschema
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = PLUGIN_ROOT / "Schemas"


def _schema(name):
    """读插件层 schema 文件。"""
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _story(**over):
    """最小合法 demo_story(1.1.0),over 覆盖字段。

    防坑:默认 story_kind=presentation(非 capability);capability 测试须显式传
    story_kind='capability' 并补 capability_id / instance_id(schema if/then 强制)。
    """
    base = {
        "story_schema_version": "1.1.0", "story_id": "story-x", "batch_id": "v0",
        "story_kind": "presentation", "evidence_class": "Integration", "depends_on": [],
        "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                      "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                      "template_dir": None, "construction_manifest_path": "m.md", "extra_paths": []},
        "acceptance_criteria": ["x"], "status": "pending", "attempts": 0,
        "manifest_version": "1.2.0",
    }
    base.update(over)
    return base


class TestStorySchema110:
    def test_p15s01_story_accepts_feedback_kind(self):
        schema = _schema("demo_story.schema.json")
        jsonschema.validate(_story(story_kind="feedback", batch_id="feedback-1"), schema)

    def test_p15s02_story_accepts_presentation_batch_id(self):
        schema = _schema("demo_story.schema.json")
        jsonschema.validate(_story(batch_id="presentation-3"), schema)

    def test_p15s03_story_rejects_unknown_batch_id(self):
        schema = _schema("demo_story.schema.json")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(_story(batch_id="rung-1"), schema)

    def test_p15s04_interaction_claims_shape_enforced(self):
        schema = _schema("demo_story.schema.json")
        jsonschema.validate(
            _story(interaction_claims=[{"input": "Space", "behavior": "推进回合"}]), schema)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(_story(interaction_claims=[{"input": "Space"}]), schema)
