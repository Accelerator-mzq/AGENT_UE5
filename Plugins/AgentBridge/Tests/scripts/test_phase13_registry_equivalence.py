# -*- coding: utf-8 -*-
"""SKS-01: Stage 3 注册表数据化前后，基线 skill_graph 等价。

对应 Phase 13 spec §3 第 5 条与验收判据 1。

输入来源与 Tests/golden/make_golden_skill_graph.py 保持一致:
  Tests/golden/inputs/root_skill_contract.json       (tracked fixture)
  Tests/golden/inputs/clarification_gate_report.json (tracked fixture)
原始来源: ProjectState/runs/run-20260417-051444-a2b8/(被 .gitignore 忽略,故拷为 fixture)。
(Schemas/examples 的 contract 只含 5 个 required 节点，不足以覆盖全量 16 节点对照)

注意: 本文件的 _normalize 逻辑必须与 make_golden_skill_graph.py 的 normalize 保持一致
(包括剥离 VOLATILE_METADATA_KEYS 和 capability_gaps)。改其中一处时必须同步改另一处。
"""
import importlib.util
import json
from pathlib import Path

# 插件根目录: Plugins/AgentBridge
PLUGIN_ROOT = Path(__file__).resolve().parents[2]

GOLDEN_DIR = PLUGIN_ROOT / "Tests" / "golden"

# 与 make_golden_skill_graph.py 使用相同的 tracked fixture 输入
INPUTS_DIR = GOLDEN_DIR / "inputs"

GOLDEN = GOLDEN_DIR / "skill_graph_baseline_golden.json"

# 从输出中剥除的易变字段
VOLATILE_METADATA_KEYS = {"generated_at", "source_run_id"}


def _load_module(name: str, path: Path):
    """用 importlib 独立加载模块，绕开包相对导入。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize(graph: dict) -> dict:
    """剥离易变字段，并断言 capability_gaps 在基线输入下必须为空后剥离。

    必须与 make_golden_skill_graph.py 的 normalize 保持一致。
    """
    out = json.loads(json.dumps(graph, ensure_ascii=False))
    for key in VOLATILE_METADATA_KEYS:
        out.get("metadata", {}).pop(key, None)
    # capability_gaps 是 Phase 13 改造新增字段，基线输入下必须为空，比对前剥离
    gaps = out.get("metadata", {}).pop("capability_gaps", [])
    assert gaps == [], f"基线输入下 capability_gaps 应为空，实际: {gaps}"
    return out


def _build_actual_graph() -> dict:
    """加载 Stage 3 模块并用 fixture 输入生成 normalize 后的实际 skill_graph。"""
    planning = _load_module(
        "skill_graph_planning",
        PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
    )
    contract = json.loads(
        (INPUTS_DIR / "root_skill_contract.json").read_text(encoding="utf-8")
    )
    gate = json.loads(
        (INPUTS_DIR / "clarification_gate_report.json").read_text(encoding="utf-8")
    )
    # run_id=None 避免写入易变 run_id
    graph = planning.create_skill_graph(contract, gate, run_id=None)
    return _normalize(graph)


def _load_golden() -> dict:
    """读取 golden 对照组。"""
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


class TestRegistryEquivalence:
    """SKS-01: 分层断言定位差异 + 整体相等权威闸门。"""

    def test_sks01_metadata_equivalent(self):
        """先比 metadata,失败时直接看到统计字段差异。"""
        actual = _build_actual_graph()
        golden = _load_golden()
        assert actual.get("metadata") == golden.get("metadata")

    def test_sks01_edges_equivalent(self):
        """再比 edges 全集(含顺序)。"""
        actual = _build_actual_graph()
        golden = _load_golden()
        assert actual.get("edges") == golden.get("edges")

    def test_sks01_node_order_and_ids_equivalent(self):
        """节点顺序与 instance_id 序列一致(顺序影响 dependencies/coupling 排序,必须锁定)。"""
        actual = _build_actual_graph()
        golden = _load_golden()
        actual_ids = [node["instance_id"] for node in actual.get("nodes", [])]
        golden_ids = [node["instance_id"] for node in golden.get("nodes", [])]
        assert actual_ids == golden_ids

    def test_sks01_each_node_equivalent(self):
        """按 instance_id 建索引逐节点比对,失败信息带节点 id。"""
        actual = _build_actual_graph()
        golden = _load_golden()
        actual_by_id = {node["instance_id"]: node for node in actual.get("nodes", [])}
        golden_by_id = {node["instance_id"]: node for node in golden.get("nodes", [])}
        assert set(actual_by_id) == set(golden_by_id), (
            f"节点 id 集合不一致: 多出={sorted(set(actual_by_id) - set(golden_by_id))}, "
            f"缺失={sorted(set(golden_by_id) - set(actual_by_id))}"
        )
        for instance_id, golden_node in golden_by_id.items():
            assert actual_by_id[instance_id] == golden_node, (
                f"节点 {instance_id} 与 golden 不一致"
            )

    def test_sks01_baseline_skill_graph_unchanged(self):
        """权威闸门: 基线 Monopoly 输入产出与 golden 整体逐项一致。"""
        actual = _build_actual_graph()
        golden = _load_golden()
        assert actual == golden
