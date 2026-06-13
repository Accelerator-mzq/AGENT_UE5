# -*- coding: utf-8 -*-
"""DMP-33~38a: MCP 工具对——注册三处齐全、fetch 载荷、submit 校验闭环、工具数 58。

返回形状契约(2026-06-12 审查修订):统一 _make_response 五键
{"status","summary","data","warnings","errors"}——
  - 工具调用成功(含 story 被业务拒绝回 in_progress)→ status="success"(文件惯例词值)
  - 异常 → status="failed"(server.py 据 status=="failed" 置 MCP isError)
  - manifest 版本告警走 warnings[](镜像 Phase 13 save 用 warnings 承载提示的先例)
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _import_mcp(name):
    """以包内文件方式加载 MCP 模块。先看项目里既有 test_phase13 的 MCP 测试怎么加载(grep tool_definitions),
    若有现成 helper/conftest fixture 就镜像之;否则用本函数。"""
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "MCP" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_run(tmp, manifest_root):
    """假 run 目录 + 假施工规范。"""
    story = {"story_schema_version": "1.0.0", "story_id": "story-a", "batch_id": "v0",
             "story_kind": "capability", "capability_id": "cap-a", "instance_id": "skill-a",
             "evidence_class": "Config", "depends_on": [],
             "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                           "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                           "template_dir": None, "construction_manifest_path": "m.md", "extra_paths": []},
             "acceptance_criteria": ["x"], "status": "pending", "attempts": 0,
             "manifest_version": "1.0.0"}
    plan = {"plan_schema_version": "1.0.0", "run_id": "run-test", "source_graph_id": "g",
            "manifest_version": "1.0.0",
            "batches": [{"batch_id": "v0", "story_ids": ["story-a"]}]}
    (tmp / "stories").mkdir(parents=True)
    (tmp / "demo_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (tmp / "stories" / "story-a.json").write_text(json.dumps(story), encoding="utf-8")
    mdir = manifest_root / "ProjectInputs" / "ConstructionManifest"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "demo_plugin_standards.md").write_text(
        "manifest_version: 1.0.0\n# 规范\n", encoding="utf-8")


class TestMcpDemoTools:
    def test_dmp33_tool_definitions_registered(self):
        td = _import_mcp("tool_definitions")
        assert "demo_story_fetch" in td.COMPILER_FRONTEND_TOOLS
        assert "demo_story_submit" in td.COMPILER_FRONTEND_TOOLS

    def test_dmp34_tool_count_is_58(self):
        td = _import_mcp("tool_definitions")
        assert td.TOOL_COUNT == 58

    def test_dmp35_server_dispatch_has_both(self):
        src = (PLUGIN_ROOT / "MCP" / "server.py").read_text(encoding="utf-8")
        assert '"demo_story_fetch"' in src and '"demo_story_submit"' in src

    def test_dmp36_fetch_returns_story_and_manifest(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        out = ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                                  project_root=str(workspace_tmp_path))
        assert out["status"] == "success"
        assert out["data"]["story"]["story_id"] == "story-a"
        assert "manifest_version: 1.0.0" in out["data"]["construction_manifest"]
        # 版本一致时无告警;告警通道统一为 warnings[],data 不再带 manifest_warning 键
        assert out["warnings"] == []
        assert "manifest_warning" not in out["data"]

    def test_dmp37_submit_reject_then_pass_loop(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                            project_root=str(workspace_tmp_path))
        bad = ct.demo_story_submit(session_path=str(workspace_tmp_path), story_id="story-a",
                                   evidence={}, project_root=str(workspace_tmp_path))
        # 业务拒绝是重试闭环信号,工具调用本身成功:status 仍为 success,不触发 MCP isError
        assert bad["status"] == "success" and bad["data"]["story_status"] == "in_progress"
        assert bad["data"]["errors"]
        doc = workspace_tmp_path / "Plugins" / "DemoX" / "Docs" / "d.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("无引用", encoding="utf-8")
        rel = str(doc.relative_to(workspace_tmp_path)).replace("\\", "/")
        good = ct.demo_story_submit(session_path=str(workspace_tmp_path), story_id="story-a",
                                    evidence={"files_changed": [rel], "doc_paths": [rel],
                                              "plugin_root": "Plugins/DemoX"},
                                    project_root=str(workspace_tmp_path))
        assert good["status"] == "success"
        assert good["data"]["story_status"] == "verified"

    def test_dmp38_fetch_manifest_version_mismatch_warns(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        mpath = workspace_tmp_path / "ProjectInputs" / "ConstructionManifest" / "demo_plugin_standards.md"
        mpath.write_text("manifest_version: 2.0.0\n# 规范\n", encoding="utf-8")
        out = ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                                  project_root=str(workspace_tmp_path))
        assert out["status"] == "success"
        assert out["warnings"] and any("版本不符" in w for w in out["warnings"])
        assert "manifest_warning" not in out["data"]

    def test_dmp38a_plugin_root_escape_rejected(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                            project_root=str(workspace_tmp_path))
        out = ct.demo_story_submit(session_path=str(workspace_tmp_path), story_id="story-a",
                                   evidence={"files_changed": [], "doc_paths": [],
                                             "plugin_root": "../outside"},
                                   project_root=str(workspace_tmp_path))
        assert out["status"] == "success" and out["data"]["story_status"] == "in_progress"
        assert any("越界" in e for e in out["data"]["errors"])
