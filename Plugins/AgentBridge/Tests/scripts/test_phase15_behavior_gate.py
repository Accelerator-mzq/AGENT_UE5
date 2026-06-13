# -*- coding: utf-8 -*-
"""PRX 行为门禁组:BL-01 越界 / 呈现截图必交 / interaction_claims 对账 / 冻结分层 + supersedes。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    assert spec, f"找不到模块文件: {name}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _story(batch_id="presentation-1", kind="presentation", ec="Integration",
           claims=None, supersedes=None):
    """最小 story(validator 只读这些字段,无需全 schema 字段)。"""
    return {"story_id": "story-x", "batch_id": batch_id, "story_kind": kind,
            "evidence_class": ec, "interaction_claims": claims or [],
            "materials": {"supersedes_paths": supersedes or []}}


def _touch(root: Path, rel: str, text="x") -> str:
    """在 root 下落一个文件,返回相对路径(正斜杠)。"""
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return rel.replace("\\", "/")


def _smoke(root: Path, rel="smoke.json", status="pass", regression="pass") -> str:
    return _touch(root, rel, json.dumps({"status": status, "v0_regression": regression}))


class TestPathAndScreenshotGate:
    def test_p15b01_path_traversal_rejected(self, workspace_tmp_path):
        # workspace_tmp_path 是仓库内 TestArtifacts 子目录,../outside.txt 相对它确实越出该根
        ev = _load("evidence_validator")
        smoke = _smoke(workspace_tmp_path)
        out = ev.validate_evidence(
            _story(), {"files_changed": ["../outside.txt"], "smoke_report": smoke,
                       "screenshots": [_touch(workspace_tmp_path, "shot.png")]},
            workspace_tmp_path, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("越界" in e for e in out["errors"])

    def test_p15b02_presentation_requires_screenshots(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        smoke = _smoke(workspace_tmp_path)
        out = ev.validate_evidence(
            _story(), {"files_changed": [smoke], "smoke_report": smoke},
            workspace_tmp_path, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("screenshots" in e for e in out["errors"])
