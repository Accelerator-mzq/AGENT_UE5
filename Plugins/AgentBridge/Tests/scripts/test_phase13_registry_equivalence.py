# -*- coding: utf-8 -*-
"""SKS-01: Stage 3 注册表数据化前后，基线 skill_graph 等价。

对应 Phase 13 spec §3 第 5 条与验收判据 1。

输入来源与 make_golden_skill_graph.py 保持一致:
  ProjectState/runs/run-20260417-051444-a2b8/root_skill_contract.json
  ProjectState/runs/run-20260417-051444-a2b8/clarification_gate_report.json
(Schemas/examples 的 contract 只含 5 个 required 节点，不足以覆盖全量 16 节点对照)
"""
import importlib.util
import json
from pathlib import Path

# 插件根目录: Plugins/AgentBridge
PLUGIN_ROOT = Path(__file__).resolve().parents[2]

# 与 make_golden_skill_graph.py 使用相同的 ProjectState run 快照
RUN_DIR = (
    Path(__file__).resolve().parents[4]  # 项目根
    / "ProjectState"
    / "runs"
    / "run-20260417-051444-a2b8"
)

GOLDEN = PLUGIN_ROOT / "Tests" / "golden" / "skill_graph_baseline_golden.json"

# 从输出中剥除的易变字段
VOLATILE_METADATA_KEYS = {"generated_at", "source_run_id"}


def _load_module(name: str, path: Path):
    """用 importlib 独立加载模块，绕开包相对导入。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize(graph: dict) -> dict:
    """剥离易变字段，并断言 capability_gaps 在基线输入下必须为空后剥离。"""
    out = json.loads(json.dumps(graph, ensure_ascii=False))
    for key in VOLATILE_METADATA_KEYS:
        out.get("metadata", {}).pop(key, None)
    # capability_gaps 是改造新增字段，基线输入下必须为空，比对前剥离
    gaps = out.get("metadata", {}).pop("capability_gaps", [])
    assert gaps == [], f"基线输入下 capability_gaps 应为空，实际: {gaps}"
    return out


class TestRegistryEquivalence:
    def test_sks01_baseline_skill_graph_unchanged(self):
        """SKS-01: 基线 Monopoly 输入产出与 golden 逐项一致。"""
        planning = _load_module(
            "skill_graph_planning",
            PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
        )
        contract = json.loads(
            (RUN_DIR / "root_skill_contract.json").read_text(encoding="utf-8")
        )
        gate = json.loads(
            (RUN_DIR / "clarification_gate_report.json").read_text(encoding="utf-8")
        )

        # run_id=None 避免写入易变 run_id
        graph = planning.create_skill_graph(contract, gate, run_id=None)
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))

        assert _normalize(graph) == golden
