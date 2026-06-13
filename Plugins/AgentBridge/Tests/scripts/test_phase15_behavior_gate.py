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


def _report(root: Path, suites, rel="test_report.json") -> str:
    """test_report 与冒烟报告同形({suites:[{name,state}]})。"""
    return _touch(root, rel, json.dumps({"suites": suites}))


def _readme(root: Path, plugin_rel: str, keys) -> Path:
    """写 plugin README,含『## 键位』节。返回 plugin 绝对根。"""
    lines = ["# Demo", "", "## 键位", ""] + [f"- [{k}] 某操作" for k in keys] + ["", "## 其他", "x"]
    p = root / plugin_rel / "README.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")
    return root / plugin_rel


_CLAIM = [{"input": "Space", "behavior": "推进回合"}]


class TestInteractionClaims:
    # 行为校验与批前缀无关;用 batch_id="v0"(非守门批)隔离被测变量,
    # 避免空 frozen_layers 触发守门批"冻结基线缺失"拒绝干扰断言
    def _story_claims(self):
        return _story(batch_id="v0", claims=_CLAIM)

    def _evidence(self, root, suites, keys=("Space",)):
        # plugin_root 经独立参数传入(各测试 plugin_root=plugin),不放进 evidence 字典
        smoke = _smoke(root)
        return {"files_changed": [smoke], "smoke_report": smoke,
                "screenshots": [_touch(root, "shot.png")],
                "test_report": _report(root, suites)}, _readme(root, "Plugins/DemoX", keys)

    def test_p15b03_claim_without_passing_case_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(workspace_tmp_path, suites=[])
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("InteractionSemantics.Space" in e for e in out["errors"])

    def test_p15b04_claim_with_failing_case_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "fail"}])
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"

    def test_p15b05_claim_with_passing_case_and_readme_passes(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "Success"}])
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "verified", out["errors"]

    def test_p15b06_readme_key_without_behavior_case_rejected(self, workspace_tmp_path):
        # C4 教训本尊:README 宣称 [Enter] 但没有对应 InteractionSemantics 用例
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "Success"}],
            keys=("Space", "Enter"))
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("InteractionSemantics.Enter" in e for e in out["errors"])

    def test_p15b07_claim_missing_from_readme_or_no_section_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        # 7a: README 键位节没宣称 claim 的键
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "Success"}],
            keys=())
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("未宣称" in e for e in out["errors"])
        # 7b: README 缺『## 键位』节
        (workspace_tmp_path / "Plugins" / "DemoX" / "README.md").write_text("# 无键位节", encoding="utf-8")
        out2 = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                    plugin_root=plugin, frozen_layers={})
        assert out2["status"] == "rejected"
        assert any("缺『## 键位』节" in e for e in out2["errors"])


class TestFrozenLayers:
    def test_p15b08_frozen_layer_modified_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        guarded = _touch(workspace_tmp_path, "Plugins/DemoX/Tests/ContractTests.cpp", "v1")
        layer = ev.freeze_layer(workspace_tmp_path, workspace_tmp_path,
                                "presentation-contract-rung1", [guarded])
        assert layer["files"][guarded]
        (workspace_tmp_path / guarded).write_text("v2-tampered", encoding="utf-8")
        smoke = _smoke(workspace_tmp_path)
        frozen = json.loads((workspace_tmp_path / "frozen_baselines.json").read_text(encoding="utf-8"))
        out = ev.validate_evidence(
            _story(batch_id="presentation-2"),
            {"files_changed": [smoke], "smoke_report": smoke,
             "screenshots": [_touch(workspace_tmp_path, "s.png")]},
            workspace_tmp_path, frozen_layers=frozen["layers"])
        assert out["status"] == "rejected"
        assert any("presentation-contract-rung1" in e and "被修改" in e for e in out["errors"])

    def test_p15b09_supersedes_exempts_declared_file(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        guarded = _touch(workspace_tmp_path, "Plugins/DemoX/Tests/R2Impl.cpp", "v1")
        ev.freeze_layer(workspace_tmp_path, workspace_tmp_path, "rung2-impl", [guarded])
        (workspace_tmp_path / guarded).unlink()  # rung3 退役该实现用例文件
        smoke = _smoke(workspace_tmp_path)
        frozen = json.loads((workspace_tmp_path / "frozen_baselines.json").read_text(encoding="utf-8"))
        out = ev.validate_evidence(
            _story(batch_id="presentation-3", supersedes=[guarded]),
            {"files_changed": [smoke], "smoke_report": smoke,
             "screenshots": [_touch(workspace_tmp_path, "s.png")]},
            workspace_tmp_path, frozen_layers=frozen["layers"])
        assert out["status"] == "verified", out["errors"]

    def test_p15b10_gated_batch_requires_regression_pass_and_some_baseline(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        # 10a: 守门批但回归段 fail → 拒
        smoke_bad = _smoke(workspace_tmp_path, rel="bad.json", regression="fail")
        out = ev.validate_evidence(
            _story(batch_id="feedback-1", kind="feedback"),
            {"files_changed": [smoke_bad], "smoke_report": smoke_bad},
            workspace_tmp_path, frozen_layers={"l": {"files": {}}})
        assert out["status"] == "rejected"
        assert any("回归" in e for e in out["errors"])
        # 10b: 守门批但既无 baseline 也无 frozen_layers → 拒
        smoke_ok = _smoke(workspace_tmp_path, rel="ok.json")
        out2 = ev.validate_evidence(
            _story(batch_id="feedback-1", kind="feedback"),
            {"files_changed": [smoke_ok], "smoke_report": smoke_ok},
            workspace_tmp_path, baseline=None, frozen_layers=None)
        assert out2["status"] == "rejected"
        assert any("冻结基线" in e for e in out2["errors"])
