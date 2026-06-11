# -*- coding: utf-8 -*-
"""SKS-03: capability gap 显式记录,不再静默丢弃;synthesized 节点带依赖边入图。"""
import importlib.util
import json
import logging
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
INPUTS = PLUGIN_ROOT / "Tests" / "golden" / "inputs"


def _load_planning():
    spec = importlib.util.spec_from_file_location(
        "skill_graph_planning",
        PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs():
    contract = json.loads((INPUTS / "root_skill_contract.json").read_text(encoding="utf-8"))
    gate = json.loads((INPUTS / "clarification_gate_report.json").read_text(encoding="utf-8"))
    return contract, gate


# 测试注入用注册表:只有两个条目,迫使其余 capability 全部成 gap
MINI_REGISTRY = {
    "gameplay-board-topology": {
        "instance_id": "skill-board-topology",
        "template_id": "monopoly.board_topology.phase1",
        "convergence_priority": 1,
        "related_clarification_items": [],
        "planning_notes": ["棋盘拓扑是 Monopoly 主链的起点，先锁定 28 格、角格索引与移动方向。"],
        "template_source": "plugin_skill_template",
        "fragment_family": "board_topology_spec",
        "depends_on_capabilities": [],
    },
    "gameplay-auction": {
        "instance_id": "skill-auction",
        "template_id": "synthesized.gameplay-auction.v1",
        "convergence_priority": 9,
        "related_clarification_items": [],
        "planning_notes": ["合成节点"],
        "template_source": "synthesized",
        "fragment_family": "property_economy_spec",
        "depends_on_capabilities": ["gameplay-board-topology"],
    },
}


class TestGapRecording:
    def test_sks03_unmapped_capability_recorded_not_dropped(self):
        """SKS-03: 注册表查不到的 required capability 进 metadata.capability_gaps。"""
        planning = _load_planning()
        contract, gate = _inputs()
        contract.setdefault("gameplay_capabilities", []).append(
            {"capability_id": "gameplay-stock-market", "activation": "required",
             "allows_design_space_discovery": True}
        )
        graph = planning.create_skill_graph(contract, gate, run_id=None, registry=MINI_REGISTRY)
        gaps = graph["metadata"]["capability_gaps"]
        gap_ids = {g["capability_id"] for g in gaps}
        assert "gameplay-stock-market" in gap_ids
        # 反向断言:注册表查得到的能力不应被记 gap(防"全记 gap 也能过")
        assert "gameplay-board-topology" not in gap_ids
        for gap in gaps:
            assert gap["reason"] == "no_template"
            assert gap["domain_type"] in ("gameplay", "baseline")

    def test_sks03b_synthesized_node_enters_graph_with_declared_edge(self):
        """SKS-03b: 注册表含 synthesized 条目时,节点入图且依赖边被换算。"""
        planning = _load_planning()
        contract, gate = _inputs()
        contract.setdefault("gameplay_capabilities", []).append(
            {"capability_id": "gameplay-auction", "activation": "required",
             "allows_design_space_discovery": True}
        )
        graph = planning.create_skill_graph(contract, gate, run_id=None, registry=MINI_REGISTRY)
        nodes = {n["instance_id"]: n for n in graph["nodes"]}
        assert "skill-auction" in nodes
        assert nodes["skill-auction"]["template_source"] == "synthesized"
        assert any(
            e["from"] == "skill-board-topology" and e["to"] == "skill-auction"
            and e["type"] == "dependency"
            for e in graph["edges"]
        )
        # 顺序不变量:边换算必须发生在 _build_relationship_maps 之前,
        # 否则 edges 还在但节点 dependencies 不会回填
        assert "skill-board-topology" in nodes["skill-auction"]["dependencies"]

    def test_sks03d_synthesized_baseline_keeps_template_source(self):
        """SKS-03d(终审 I-1): synthesized 模板认领 baseline capability 时,
        路径启发式不得覆盖注册表的 template_source——evidence promote 守卫只认
        == "synthesized",一旦被覆盖成 future_baseline_template 守卫即被绕过,
        且会被误列为"模板未落地"。"""
        planning = _load_planning()
        contract, gate = _inputs()
        # 深拷贝 MINI_REGISTRY,追加一条 synthesized 条目认领 fixture 中真实存在的
        # baseline capability(baseline-hud 在 root_skill_contract.json 中 activation=required)
        registry = json.loads(json.dumps(MINI_REGISTRY, ensure_ascii=False))
        registry["baseline-hud"] = {
            "instance_id": "skill-hud-synth",
            "template_id": "synthesized.baseline-hud.v1",
            "convergence_priority": 5,
            "related_clarification_items": [],
            "planning_notes": ["合成 baseline 节点"],
            "template_source": "synthesized",
            "fragment_family": "ui_widget_spec",
            "depends_on_capabilities": [],
        }
        graph = planning.create_skill_graph(contract, gate, run_id=None, registry=registry)
        nodes = {n["instance_id"]: n for n in graph["nodes"]}
        assert "skill-hud-synth" in nodes
        node = nodes["skill-hud-synth"]
        # 守卫不变量:注册表声明 synthesized 必须原样进图(spec §4.4 试制章)
        assert node["template_source"] == "synthesized"
        # synthesized 不是"未来 baseline 占位模板",不得进 missing_baseline_templates
        assert "synthesized.baseline-hud.v1" not in graph["metadata"]["missing_baseline_templates"]
        # planning_notes 不得出现"模板未落地"警告(那是 future_baseline_template 专属)
        assert not any("未落地" in note for note in node["planning_notes"])

    def test_sks03c_unknown_declared_dependency_warned_not_silently_skipped(self, caplog):
        """SKS-03c: manifest 声明的依赖名注册表查不到(写错)时显式告警,且不生成边。"""
        planning = _load_planning()
        contract, gate = _inputs()
        contract.setdefault("gameplay_capabilities", []).append(
            {"capability_id": "gameplay-auction", "activation": "required",
             "allows_design_space_discovery": True}
        )
        # 深拷贝 MINI_REGISTRY,把 auction 的依赖改成不存在的名字(模拟 manifest 错别字)
        registry = json.loads(json.dumps(MINI_REGISTRY, ensure_ascii=False))
        registry["gameplay-auction"]["depends_on_capabilities"] = ["gameplay-typo-dep"]
        with caplog.at_level(logging.WARNING):
            graph = planning.create_skill_graph(contract, gate, run_id=None, registry=registry)
        # 告警必须出现,且带写错的依赖名与声明它的节点 instance_id(便于定位 manifest)
        assert "gameplay-typo-dep" in caplog.text
        assert "skill-auction" in caplog.text
        # 写错的依赖不应生成任何指向 skill-auction 的依赖边
        assert not any(
            e["to"] == "skill-auction" and e["type"] == "dependency"
            for e in graph["edges"]
        )
