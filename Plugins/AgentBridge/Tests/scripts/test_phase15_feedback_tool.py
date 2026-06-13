# -*- coding: utf-8 -*-
"""PRX 反馈工具组:demo_feedback_log 三处注册 + 落盘 + 序号 + 校验拒绝 + velocity + resolved 流转 e2e。"""
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _import_mcp(name):
    """以包内文件方式加载 MCP 模块(test_phase14_mcp_tools 同款)。"""
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    spec = importlib.util.spec_from_file_location(name, PLUGIN_ROOT / "MCP" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _entry(**over):
    base = {"window_id": "w1", "phenomenon": "拍卖面板当前价不刷新",
            "expectation": "出价后当前价即时刷新", "severity": "major",
            "related_rung": 1, "related_capability": None}
    base.update(over)
    return base


class TestFeedbackTool:
    def test_p15f01_tool_definitions_registered(self):
        td = _import_mcp("tool_definitions")
        assert "demo_feedback_log" in td.COMPILER_FRONTEND_TOOLS

    def test_p15f02_tool_count_is_58(self):
        td = _import_mcp("tool_definitions")
        assert td.TOOL_COUNT == 58

    def test_p15f03_server_dispatch_registered(self):
        src = (PLUGIN_ROOT / "MCP" / "server.py").read_text(encoding="utf-8")
        assert '"demo_feedback_log"' in src

    def test_p15f04_log_writes_entry_open_with_sequential_id(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        out = ct.demo_feedback_log(session_path=str(workspace_tmp_path), entry=_entry())
        assert out["status"] == "success"
        assert out["data"]["feedback_id"] == "fb-w1-01"
        saved = json.loads((workspace_tmp_path / "feedback" / "fb-w1-01.json")
                           .read_text(encoding="utf-8"))
        assert saved["status"] == "open" and saved["feedback_schema_version"] == "1.0.0"

    def test_p15f05_second_entry_increments_seq(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        ct.demo_feedback_log(session_path=str(workspace_tmp_path), entry=_entry())
        out = ct.demo_feedback_log(session_path=str(workspace_tmp_path),
                                   entry=_entry(phenomenon="第二条"))
        assert out["data"]["feedback_id"] == "fb-w1-02"

    def test_p15f06_invalid_entry_failed(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        out = ct.demo_feedback_log(session_path=str(workspace_tmp_path),
                                   entry=_entry(severity="urgent"))
        assert out["status"] == "failed"
        assert out["errors"]
        assert not list((workspace_tmp_path / "feedback").glob("*.json"))

    def test_p15f07_velocity_event_appended(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        ct.demo_feedback_log(session_path=str(workspace_tmp_path), entry=_entry())
        log = json.loads((workspace_tmp_path / "velocity_log.json").read_text(encoding="utf-8"))
        assert any(e.get("kind") == "feedback_log" and e.get("feedback_id") == "fb-w1-01"
                   for e in log["events"])

    def test_p15f08_submit_feedback_story_marks_entry_resolved(self, workspace_tmp_path):
        """e2e:登记反馈 → 切批后 feedback story submit verified → 反馈条目 status=resolved
        (覆盖 Task 8 在 demo_story_submit 里加的 feedback→resolved 流转,补 Task 8 复审 I-1 缺口)。"""
        ct = _import_mcp("compiler_tools")
        tmp = workspace_tmp_path
        # 登记一条反馈(status=open)
        ct.demo_feedback_log(session_path=str(tmp), entry=_entry())
        # 构造一个已切批的 feedback story(in_progress,materials.feedback_path 指向条目)
        (tmp / "stories").mkdir(parents=True, exist_ok=True)
        story = {"story_schema_version": "1.1.0", "story_id": "story-feedback-1-fb-w1-01",
                 "batch_id": "feedback-1", "story_kind": "feedback", "evidence_class": "Integration",
                 "depends_on": [],
                 "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                               "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                               "template_dir": None, "construction_manifest_path": "m.md",
                               "feedback_path": "feedback/fb-w1-01.json", "supersedes_paths": [],
                               "extra_paths": []},
                 "acceptance_criteria": ["修复"], "status": "in_progress", "attempts": 0,
                 "manifest_version": "1.2.0"}
        plan = {"plan_schema_version": "1.1.0", "run_id": "r", "source_graph_id": "g",
                "manifest_version": "1.2.0",
                "batches": [{"batch_id": "feedback-1", "story_ids": ["story-feedback-1-fb-w1-01"]}]}
        (tmp / "demo_plan.json").write_text(json.dumps(plan), encoding="utf-8")
        (tmp / "stories" / "story-feedback-1-fb-w1-01.json").write_text(json.dumps(story), encoding="utf-8")
        # 冻结层(空 files,满足守门批"有 frozen_layers"前提且 hash 检查零文件通过)
        (tmp / "frozen_baselines.json").write_text(
            json.dumps({"layers": {"contract": {"files": {}}}}), encoding="utf-8")
        # 冒烟报告:pass + 回归 pass(守门批要求)
        smoke = tmp / "smoke.json"
        smoke.write_text(json.dumps({"status": "pass", "v0_regression": "pass"}), encoding="utf-8")
        # submit(feedback story 无 interaction_claims → 行为门放行;Integration 必交 files_changed+smoke_report)
        out = ct.demo_story_submit(session_path=str(tmp), story_id="story-feedback-1-fb-w1-01",
                                   evidence={"files_changed": ["smoke.json"], "smoke_report": "smoke.json"},
                                   project_root=str(tmp))
        assert out["status"] == "success", out
        assert out["data"]["story_status"] == "verified", out["data"]
        entry = json.loads((tmp / "feedback" / "fb-w1-01.json").read_text(encoding="utf-8"))
        assert entry["status"] == "resolved"
