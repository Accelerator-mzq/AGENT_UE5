# -*- coding: utf-8 -*-
"""PRX smoke runner 组:BL-04 errorMessage 透传 + 冻结层多段回归聚合。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    """动态加载 runner.py 模块,避免相对导入冲突。"""
    spec = importlib.util.spec_from_file_location(
        "runner", PLUGIN_ROOT / "Scripts" / "demo_smoke" / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSmokeRunnerP15:
    def test_p15r01_suites_carry_error_messages(self, workspace_tmp_path):
        """BL-04:suites 中每条测试携带 Error 类型 entry 的 message 列表。"""
        r = _load_runner()
        index = {"succeeded": 0, "failed": 1, "notRun": 0,
                 "tests": [{"fullTestPath": "DemoX.Smoke.A", "state": "Fail",
                            "entries": [
                                {"event": {"type": "Error", "message": "Assertion failed: X"}},
                                {"event": {"type": "Info", "message": "noise"}}]}]}
        (workspace_tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        report = r.build_smoke_report(workspace_tmp_path, "n/a", [])
        assert report["suites"][0]["errors"] == ["Assertion failed: X"]

    def test_p15r02_aggregate_all_pass(self):
        """聚合函数:全部 pass → pass。"""
        r = _load_runner()
        assert r.aggregate_regression(["pass", "pass"]) == "pass"

    def test_p15r03_aggregate_any_fail(self):
        """聚合函数:任一非 pass → fail。"""
        r = _load_runner()
        assert r.aggregate_regression(["pass", "fail"]) == "fail"

    def test_p15r04_aggregate_empty_is_na(self):
        """聚合函数:空列表 → n/a。"""
        r = _load_runner()
        assert r.aggregate_regression([]) == "n/a"

    def test_p15r05_collect_filters_merges_v0_and_regression(self):
        """collect_regression_filters:合并 --v0-filter 与多个 --regression-filter,v0 在前。"""
        r = _load_runner()
        parser = r.build_parser()
        args = parser.parse_args(["--filter", "X", "--out", "o.json",
                                  "--v0-filter", "A", "--regression-filter", "B",
                                  "--regression-filter", "C"])
        assert r.collect_regression_filters(args) == ["A", "B", "C"]

    def test_p15r06_null_entries_and_event_do_not_crash(self, workspace_tmp_path):
        r = _load_runner()
        # 失败用例偶发 entries=null / event=null,errors 透传须防御不崩
        index = {"succeeded": 0, "failed": 1, "notRun": 0,
                 "tests": [{"fullTestPath": "DemoX.Smoke.Null", "state": "Fail", "entries": None},
                           {"fullTestPath": "DemoX.Smoke.NoneEvt", "state": "Fail",
                            "entries": [{"event": None}]}]}
        (workspace_tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        report = r.build_smoke_report(workspace_tmp_path, "n/a", [])
        assert report["suites"][0]["errors"] == []
        assert report["suites"][1]["errors"] == []
