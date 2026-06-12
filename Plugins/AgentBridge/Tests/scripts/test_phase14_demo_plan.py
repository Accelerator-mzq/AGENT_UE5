# -*- coding: utf-8 -*-
"""DMP-01~10: demo_plan 切批核心——拓扑序/批切分/文档 story/确定性/fail-closed。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    """动态加载 Compiler/demo_plan 下的自包含模块(与 test_phase13_* 同款模式)。"""
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _graph(nodes):
    return {"graph_version": "1.0", "graph_id": "graph-test-0001",
            "nodes": nodes, "edges": [], "metadata": {}}


def _node(iid, cap, domain="gameplay", deps=None, source="plugin_skill_template", template="tpl.x.v1"):
    return {"instance_id": iid, "capability_id": cap, "template_id": template,
            "domain_type": domain, "template_source": source,
            "dependencies": deps or [], "coupling": []}


def _contract(caps):
    """caps: [(capability_id, source_anchor)]。"""
    entries = [{"capability_id": c, "activation": "required", "source_anchor": a} for c, a in caps]
    return {"contract_id": "contract-test", "gameplay_capabilities": entries, "baseline_capabilities": []}


_PATHS = {
    "gdd_path": "ProjectInputs/GDD/x.md",
    "contract_path": "ProjectState/runs/r/root_skill_contract.json",
    "skill_graph_path": "ProjectState/runs/r/skill_graph.json",
    "construction_manifest_path": "ProjectInputs/ConstructionManifest/demo_plugin_standards.md",
}


class TestDemoPlanner:
    def test_dmp01_v0_batch_contains_all_library_nodes(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a"), _node("skill-b", "cap-b", deps=["skill-a"]),
                 _node("skill-s", "cap-s", source="synthesized")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-b", "S2"), ("cap-s", "S3")]),
                                "1.0.0", _PATHS)
        v0 = out["plan"]["batches"][0]
        assert v0["batch_id"] == "v0"
        assert "story-skill-a" in v0["story_ids"] and "story-skill-b" in v0["story_ids"]
        assert "story-skill-s" not in v0["story_ids"]

    def test_dmp02_each_synthesized_node_gets_own_increment_batch(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a"),
                 _node("skill-s1", "cap-s1", source="synthesized", deps=["skill-a"]),
                 _node("skill-s2", "cap-s2", source="synthesized", deps=["skill-a"])]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-s1", "S2"), ("cap-s2", "S3")]),
                                "1.0.0", _PATHS)
        ids = [b["batch_id"] for b in out["plan"]["batches"]]
        assert ids == ["v0", "increment-1", "increment-2"]

    def test_dmp03_batch_inner_topological_order(self):
        p = _load("planner")
        nodes = [_node("skill-b", "cap-b", deps=["skill-a"]), _node("skill-a", "cap-a")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-b", "S2")]), "1.0.0", _PATHS)
        sids = out["plan"]["batches"][0]["story_ids"]
        assert sids.index("story-skill-a") < sids.index("story-skill-b")

    def test_dmp04_doc_story_appended_last_per_batch(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a"), _node("skill-s", "cap-s", source="synthesized")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-s", "S2")]), "1.0.0", _PATHS)
        for batch in out["plan"]["batches"]:
            assert batch["story_ids"][-1] == f"story-{batch['batch_id']}-docs"
        doc = [s for s in out["stories"] if s["story_id"] == "story-v0-docs"][0]
        assert doc["story_kind"] == "documentation" and doc["evidence_class"] == "Config"
        assert set(doc["depends_on"]) == {"story-skill-a"}

    def test_dmp05_evidence_class_mapped_from_domain_type_only(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a", domain="gameplay"), _node("skill-h", "cap-h", domain="baseline")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-h", "S2")]), "1.0.0", _PATHS)
        by_id = {s["story_id"]: s for s in out["stories"]}
        assert by_id["story-skill-a"]["evidence_class"] == "Logic"
        assert by_id["story-skill-h"]["evidence_class"] == "Visual"

    def test_dmp06_anchor_from_contract_into_materials(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "2.1 某锚点")]), "1.0.0", _PATHS)
        story = out["stories"][0]
        assert story["materials"]["gdd_anchors"] == ["2.1 某锚点"]

    def test_dmp07_synthesized_template_dir_preresolved(self):
        p = _load("planner")
        nodes = [_node("skill-s", "cap-s", source="synthesized", template="synthesized.cap-s.v1")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-s", "S")]), "1.0.0", _PATHS)
        story = [s for s in out["stories"] if s.get("instance_id") == "skill-s"][0]
        assert story["materials"]["template_dir"] == "Plugins/AgentBridge/SkillTemplates/synthesized/cap-s"

    def test_dmp08_deterministic_same_input_same_output(self):
        p = _load("planner")
        nodes = [_node("skill-b", "cap-b"), _node("skill-a", "cap-a"), _node("skill-c", "cap-c")]
        a = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "1"), ("cap-b", "2"), ("cap-c", "3")]), "1.0.0", _PATHS)
        b = p.build_demo_plan(_graph(list(reversed(nodes))), _contract([("cap-c", "3"), ("cap-a", "1"), ("cap-b", "2")]), "1.0.0", _PATHS)
        assert a == b

    def test_dmp09_cycle_fails_closed(self):
        p = _load("planner")
        import pytest
        nodes = [_node("skill-a", "cap-a", deps=["skill-b"]), _node("skill-b", "cap-b", deps=["skill-a"])]
        with pytest.raises(ValueError):
            p.build_demo_plan(_graph(nodes), _contract([("cap-a", "1"), ("cap-b", "2")]), "1.0.0", _PATHS)

    def test_dmp10_manifest_version_stamped_on_plan_and_stories(self):
        p = _load("planner")
        out = p.build_demo_plan(_graph([_node("skill-a", "cap-a")]), _contract([("cap-a", "1")]), "9.9.9", _PATHS)
        assert out["plan"]["manifest_version"] == "9.9.9"
        assert all(s["manifest_version"] == "9.9.9" for s in out["stories"])


class TestManifestLoader:
    def test_dmp31_load_manifest_text_and_version(self, project_root):
        ml = _load("manifest_loader")
        text, version = ml.load_construction_manifest(project_root)
        # 只锚定语义化三段格式,不钉具体值——规范文本修订(如 1.0.1 命名派生澄清)不应破坏机制测试
        import re as _re
        assert _re.fullmatch(r"\d+\.\d+\.\d+", version) and "Plugin 骨架" in text

    def test_dmp32_missing_version_line_fails_closed(self, workspace_tmp_path):
        ml = _load("manifest_loader")
        bad = workspace_tmp_path / "m.md"
        bad.write_text("# 无版本行", encoding="utf-8")
        import pytest
        with pytest.raises(ValueError, match="manifest_version"):
            ml.load_construction_manifest(workspace_tmp_path, path=bad)

    def test_dmp32a_malformed_version_fails_closed(self, workspace_tmp_path):
        ml = _load("manifest_loader")
        bad = workspace_tmp_path / "m.md"
        bad.write_text("manifest_version: 1..\n# x", encoding="utf-8")
        import pytest
        with pytest.raises(ValueError, match="manifest_version"):
            ml.load_construction_manifest(workspace_tmp_path, path=bad)


class TestDemoPlanCli:
    def _seed(self, tmp, run_id="run-cli-test"):
        import json as _json
        graph = {"graph_version": "1.0", "graph_id": "g-1",
                 "nodes": [{"instance_id": "skill-a", "capability_id": "cap-a",
                            "template_id": "t.v1", "domain_type": "gameplay",
                            "template_source": "plugin_skill_template",
                            "dependencies": [], "coupling": []}],
                 "edges": [], "metadata": {"source_run_id": run_id, "capability_gaps": []}}
        contract = {"contract_id": "c-1", "source_gdd": "ProjectInputs/GDD/x.md",
                    "gameplay_capabilities": [{"capability_id": "cap-a", "activation": "required",
                                               "source_anchor": "1. 概述"}],
                    "baseline_capabilities": []}
        (tmp / "skill_graph.json").write_text(_json.dumps(graph), encoding="utf-8")
        (tmp / "root_skill_contract.json").write_text(_json.dumps(contract), encoding="utf-8")

    def _run_cli(self, tmp, project_root):
        import subprocess, sys
        cli = Path(project_root) / "Plugins" / "AgentBridge" / "Scripts" / "demo_plan_main.py"
        return subprocess.run([sys.executable, str(cli), "--run-dir", str(tmp)],
                              capture_output=True, text=True, cwd=project_root)

    def test_dmp39_cli_writes_plan_and_stories(self, workspace_tmp_path, project_root):
        import json as _json
        self._seed(workspace_tmp_path)
        result = self._run_cli(workspace_tmp_path, project_root)
        assert result.returncode == 0, result.stderr
        plan = _json.loads((workspace_tmp_path / "demo_plan.json").read_text(encoding="utf-8"))
        assert plan["run_id"] == "run-cli-test"
        assert (workspace_tmp_path / "stories" / "story-skill-a.json").exists()

    def test_dmp39b_cli_fails_friendly_on_missing_run_dir(self, workspace_tmp_path, project_root):
        result = self._run_cli(workspace_tmp_path / "nope", project_root)
        assert result.returncode == 2
        assert "[FAIL]" in result.stderr and "Traceback" not in result.stderr

    def test_dmp39a_cli_fails_closed_on_missing_run_id(self, workspace_tmp_path, project_root):
        import json as _json
        self._seed(workspace_tmp_path)
        graph = _json.loads((workspace_tmp_path / "skill_graph.json").read_text(encoding="utf-8"))
        del graph["metadata"]["source_run_id"]
        (workspace_tmp_path / "skill_graph.json").write_text(_json.dumps(graph), encoding="utf-8")
        result = self._run_cli(workspace_tmp_path, project_root)
        assert result.returncode != 0 and "source_run_id" in (result.stderr + result.stdout)

    def test_dmp40_cli_fails_closed_on_unresolved_gaps(self, workspace_tmp_path, project_root):
        import json as _json
        self._seed(workspace_tmp_path)
        graph = _json.loads((workspace_tmp_path / "skill_graph.json").read_text(encoding="utf-8"))
        graph["metadata"]["capability_gaps"] = [{"capability_id": "cap-gap", "reason": "x"}]
        (workspace_tmp_path / "skill_graph.json").write_text(_json.dumps(graph), encoding="utf-8")
        result = self._run_cli(workspace_tmp_path, project_root)
        assert result.returncode != 0 and "capability_gaps" in (result.stderr + result.stdout)
