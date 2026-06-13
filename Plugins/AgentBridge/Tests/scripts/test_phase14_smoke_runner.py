# -*- coding: utf-8 -*-
"""DMP-41~47: 冒烟 runner——环境自检/报告解析/v0 回归段/环境故障归因分离/main 桩测。"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "runner", PLUGIN_ROOT / "Scripts" / "demo_smoke" / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_index(d, failed=0):
    """向指定目录写 UE Automation index.json(供 _ue_report 与 main 桩测共用)。"""
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.json").write_text(json.dumps(
        {"succeeded": 3, "succeededWithWarnings": 0, "failed": failed, "notRun": 0,
         "tests": [{"fullTestPath": "X.Smoke.FullLoop", "state": "Success" if not failed else "Fail"}]}),
        encoding="utf-8")
    return d


def _ue_report(tmp, failed=0):
    return _write_index(tmp / "ue_report", failed=failed)


def _fake_env(r, tmp, monkeypatch):
    """构造让 precheck 通过的假环境:假 editor 文件 + 假项目根(含 .uproject)。"""
    editor = tmp / "UnrealEditor-Cmd.exe"
    editor.write_text("", encoding="utf-8")
    fake_root = tmp / "proj"
    fake_root.mkdir(parents=True, exist_ok=True)
    (fake_root / "Fake.uproject").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(r, "PROJECT_ROOT", fake_root)
    return editor


class TestSmokeRunner:
    def test_dmp41_precheck_missing_editor_is_env_error(self, workspace_tmp_path):
        r = _load()
        out = r.precheck(editor_cmd=workspace_tmp_path / "no_editor.exe",
                         uproject=workspace_tmp_path / "no.uproject")
        assert out["ok"] is False and out["kind"] == "environment"

    def test_dmp42_parse_ue_report_pass(self, workspace_tmp_path):
        r = _load()
        report = r.build_smoke_report(_ue_report(workspace_tmp_path), v0_regression="n/a",
                                      screenshots=[])
        assert report["status"] == "pass" and report["counts"]["failed"] == 0

    def test_dmp43_parse_ue_report_fail(self, workspace_tmp_path):
        r = _load()
        report = r.build_smoke_report(_ue_report(workspace_tmp_path, failed=1),
                                      v0_regression="n/a", screenshots=[])
        assert report["status"] == "fail"

    def test_dmp44_missing_index_json_is_env_error_not_fail(self, workspace_tmp_path):
        r = _load()
        with pytest.raises(r.EnvironmentFault):
            r.build_smoke_report(workspace_tmp_path / "empty", v0_regression="n/a", screenshots=[])

    def test_dmp45_run_automation_timeout_is_env_fault_main_exit3(self, workspace_tmp_path, monkeypatch):
        """DMP-45: commandlet 超时 → EnvironmentFault → main 返回 3(不计自修轮)。"""
        r = _load()
        editor = _fake_env(r, workspace_tmp_path, monkeypatch)

        def _timeout_run(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="UnrealEditor-Cmd", timeout=1800)

        monkeypatch.setattr(r.subprocess, "run", _timeout_run)
        out = workspace_tmp_path / "smoke_report.json"
        monkeypatch.setattr(sys, "argv", ["runner.py", "--filter", "X.Smoke",
                                          "--out", str(out), "--editor-cmd", str(editor)])
        assert r.main() == 3

    def test_dmp46_v0_fail_main_pass_exits_1(self, workspace_tmp_path, monkeypatch, capsys):
        """DMP-46: v0 回归段破 + 主段过 → 退出码 1 且打印 [FAIL]。"""
        r = _load()
        editor = _fake_env(r, workspace_tmp_path, monkeypatch)

        def _fake_run(editor_cmd, uproject, test_filter, report_dir, log_path):
            # regression_1 段(原 v0 段)写失败报告,主段写通过报告
            # Phase 15 多段回归重构后目录名从 "v0" 改为 "regression_1"
            _write_index(Path(report_dir), failed=1 if Path(report_dir).name == "regression_1" else 0)

        monkeypatch.setattr(r, "run_automation", _fake_run)
        out = workspace_tmp_path / "smoke_report.json"
        monkeypatch.setattr(sys, "argv", ["runner.py", "--filter", "X.Smoke",
                                          "--v0-filter", "X.Smoke.V0",
                                          "--out", str(out), "--editor-cmd", str(editor)])
        assert r.main() == 1
        assert "[FAIL]" in capsys.readouterr().out

    def test_dmp47_both_pass_exit0_and_report_v0_pass(self, workspace_tmp_path, monkeypatch):
        """DMP-47: 双段全过 → 退出码 0 且落盘报告 v0_regression=="pass"。"""
        r = _load()
        editor = _fake_env(r, workspace_tmp_path, monkeypatch)

        def _fake_run(editor_cmd, uproject, test_filter, report_dir, log_path):
            _write_index(Path(report_dir), failed=0)

        monkeypatch.setattr(r, "run_automation", _fake_run)
        out = workspace_tmp_path / "smoke_report.json"
        monkeypatch.setattr(sys, "argv", ["runner.py", "--filter", "X.Smoke",
                                          "--v0-filter", "X.Smoke.V0",
                                          "--out", str(out), "--editor-cmd", str(editor)])
        assert r.main() == 0
        saved = json.loads(out.read_text(encoding="utf-8"))
        assert saved["v0_regression"] == "pass"
