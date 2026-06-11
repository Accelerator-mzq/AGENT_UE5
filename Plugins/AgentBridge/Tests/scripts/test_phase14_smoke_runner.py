# -*- coding: utf-8 -*-
"""DMP-41~44: 冒烟 runner——环境自检/报告解析/v0 回归段/环境故障归因分离。"""
import importlib.util
import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "runner", PLUGIN_ROOT / "Scripts" / "demo_smoke" / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ue_report(tmp, failed=0):
    d = tmp / "ue_report"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.json").write_text(json.dumps(
        {"succeeded": 3, "succeededWithWarnings": 0, "failed": failed, "notRun": 0,
         "tests": [{"fullTestPath": "X.Smoke.FullLoop", "state": "Success" if not failed else "Fail"}]}),
        encoding="utf-8")
    return d


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
