# -*- coding: utf-8 -*-
"""SKS-03: capability gap 显式记录,不再静默丢弃;synthesized 节点带依赖边入图。"""
import importlib.util
import json
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
