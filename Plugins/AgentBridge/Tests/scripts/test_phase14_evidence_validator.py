# -*- coding: utf-8 -*-
"""DMP-21~30: 证据校验——分级必交/路径存在/冒烟 pass/增量 hash 守门/文档引用对账。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _story(ec="Logic", batch="v0", kind="capability"):
    return {"story_id": "story-x", "batch_id": batch, "story_kind": kind, "evidence_class": ec}


def _touch(root, rel, content="x"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return rel


def _smoke(root, status="pass", v0reg="n/a"):
    return _touch(root, "smoke_report.json",
                  json.dumps({"status": status, "v0_regression": v0reg, "suites": []}))


class TestEvidenceValidator:
    def test_dmp21_logic_requires_test_and_smoke(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        out = ev.validate_evidence(_story("Logic"), {"files_changed": []}, workspace_tmp_path)
        assert out["status"] == "rejected"
        assert any("test_report" in e for e in out["errors"]) and any("smoke_report" in e for e in out["errors"])

    def test_dmp22_visual_requires_screenshots(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        out = ev.validate_evidence(_story("Visual"), {"files_changed": []}, workspace_tmp_path)
        assert out["status"] == "rejected" and any("screenshots" in e for e in out["errors"])

    def test_dmp23_referenced_paths_must_exist(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": ["ghost.cpp"], "test_report": "no.json", "smoke_report": "no2.json"}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out["status"] == "rejected" and any("ghost.cpp" in e for e in out["errors"])

    def test_dmp24_smoke_report_must_be_pass(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, status="fail")}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out["status"] == "rejected" and any("smoke" in e for e in out["errors"])

    def test_dmp25_logic_happy_path_verified(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path)}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out == {"status": "verified", "errors": []}

    def test_dmp26_increment_requires_baseline(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, v0reg="pass")}
        out = ev.validate_evidence(_story("Logic", batch="increment-1"), evidence,
                                   workspace_tmp_path, baseline=None)
        assert out["status"] == "rejected" and any("baseline" in e.lower() for e in out["errors"])

    def test_dmp27_increment_hash_guard_detects_tampering(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        rel = _touch(workspace_tmp_path, "Plugins/DemoX/SmokeTest.cpp", "original")
        baseline = ev.freeze_v0_baseline(workspace_tmp_path, workspace_tmp_path, [rel])
        (workspace_tmp_path / rel).write_text("tampered", encoding="utf-8")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, v0reg="pass")}
        out = ev.validate_evidence(_story("Logic", batch="increment-1"), evidence,
                                   workspace_tmp_path, baseline=baseline)
        assert out["status"] == "rejected" and any("hash" in e.lower() for e in out["errors"])

    def test_dmp28_increment_requires_v0_regression_pass(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        rel = _touch(workspace_tmp_path, "Plugins/DemoX/SmokeTest.cpp")
        baseline = ev.freeze_v0_baseline(workspace_tmp_path, workspace_tmp_path, [rel])
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, v0reg="fail")}
        out = ev.validate_evidence(_story("Logic", batch="increment-1"), evidence,
                                   workspace_tmp_path, baseline=baseline)
        assert out["status"] == "rejected" and any("v0" in e for e in out["errors"])

    def test_dmp29_doc_story_reference_check(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        plugin = workspace_tmp_path / "Plugins" / "DemoX"
        _touch(workspace_tmp_path, "Plugins/DemoX/Source/DemoX/Core.h", "class ADemoActor {};")
        doc = _touch(workspace_tmp_path, "Plugins/DemoX/Docs/arch.md",
                     "架构含 `ADemoActor` 与 `AGhostActor`。")
        evidence = {"files_changed": [doc], "doc_paths": [doc]}
        out = ev.validate_evidence(_story("Config", kind="documentation"), evidence,
                                   workspace_tmp_path, plugin_root=plugin)
        assert out["status"] == "rejected"
        assert any("AGhostActor" in e for e in out["errors"])
        assert not any("ADemoActor" in e for e in out["errors"])

    def test_dmp30_freeze_baseline_writes_sha256_file(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        rel = _touch(workspace_tmp_path, "s.cpp", "abc")
        baseline = ev.freeze_v0_baseline(workspace_tmp_path, workspace_tmp_path, [rel])
        on_disk = json.loads((workspace_tmp_path / "v0_smoke_baseline.json").read_text(encoding="utf-8"))
        assert on_disk == baseline and rel.replace("\\", "/") in on_disk["files"]
        assert len(list(on_disk["files"].values())[0]) == 64

    def test_dmp30a_smoke_report_non_dict_json_rejected_not_crash(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _touch(workspace_tmp_path, "smoke_report.json", "[1, 2]")}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out["status"] == "rejected"
        assert any("格式错误" in e for e in out["errors"])

    def test_dmp30b_smoke_report_json_null_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _touch(workspace_tmp_path, "smoke_report.json", "null")}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out["status"] == "rejected"
        assert any("NoneType" in e for e in out["errors"])

    def test_dmp30c_doc_reference_prefix_substring_not_matched(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        plugin = workspace_tmp_path / "Plugins" / "DemoX"
        _touch(workspace_tmp_path, "Plugins/DemoX/Source/DemoX/Core.h", "class AFooBar {};")
        doc = _touch(workspace_tmp_path, "Plugins/DemoX/Docs/arch.md", "引用 `AFoo` 与 `AFooBar`。")
        evidence = {"files_changed": [doc], "doc_paths": [doc]}
        out = ev.validate_evidence(_story("Config", kind="documentation"), evidence,
                                   workspace_tmp_path, plugin_root=plugin)
        assert any("AFoo " in e or "类 AFoo 在" in e for e in out["errors"])
        assert not any("AFooBar" in e for e in out["errors"])

    def test_dmp30d_unknown_evidence_class_rejected_not_crash(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        out = ev.validate_evidence({"story_id": "story-x", "batch_id": "v0",
                                    "story_kind": "capability", "evidence_class": "Bogus"},
                                   {"files_changed": []}, workspace_tmp_path)
        assert out["status"] == "rejected" and any("evidence_class" in e for e in out["errors"])

    def test_dmp30e_doc_reference_matches_ue_api_macro_form(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        plugin = workspace_tmp_path / "Plugins" / "DemoX"
        _touch(workspace_tmp_path, "Plugins/DemoX/Source/DemoX/Core.h",
               "class DEMOX_API ARealActor : public AActor {};")
        doc = _touch(workspace_tmp_path, "Plugins/DemoX/Docs/arch.md", "核心类 `ARealActor`。")
        evidence = {"files_changed": [doc], "doc_paths": [doc]}
        out = ev.validate_evidence(_story("Config", kind="documentation"), evidence,
                                   workspace_tmp_path, plugin_root=plugin)
        assert out["status"] == "verified", out["errors"]
