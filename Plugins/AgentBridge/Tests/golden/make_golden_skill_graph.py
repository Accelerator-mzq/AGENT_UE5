# -*- coding: utf-8 -*-
"""生成 Stage 3 等价回归的 golden 快照。

输入来源说明:
  Schemas/examples/phase11_root_skill_contract.example.json 仅含 2 个 gameplay + 3 个 baseline
  能力(共 5 个 required 节点)，明显少于预期的 ~16 节点，因此按计划备选方案改用真实成功
  run 的快照作输入。原始来源: ProjectState/runs/run-20260417-051444-a2b8/(该目录被
  .gitignore 忽略，fresh clone 不可用)，已拷贝为 tracked fixture 落在本目录 inputs/ 下:
    Tests/golden/inputs/root_skill_contract.json      (7 gameplay + 9 baseline = 16 required)
    Tests/golden/inputs/clarification_gate_report.json

改造前跑一次生成对照组;改造后测试断言输出不变。

注意: 本脚本的 normalize 逻辑必须与
  Tests/scripts/test_phase13_registry_equivalence.py 的 _normalize 保持一致
(包括剥离 VOLATILE_METADATA_KEYS 和 capability_gaps)，否则改造后重跑生成会产出
与测试不等价的 golden。改其中一处时必须同步改另一处。
"""
import importlib.util
import json
import sys
from pathlib import Path

# 插件根目录: Plugins/AgentBridge
PLUGIN_ROOT = Path(__file__).resolve().parents[2]

# tracked fixture 输入目录(原始来源见模块 docstring)
INPUTS_DIR = Path(__file__).resolve().parent / "inputs"

GOLDEN = Path(__file__).resolve().parent / "skill_graph_baseline_golden.json"

# 需要从输出中剥除的易变字段(时间戳 / run_id)
VOLATILE_METADATA_KEYS = {"generated_at", "source_run_id"}

# 基线输入下预期的最少节点数;低于该值视为输入异常,拒绝落盘
MIN_EXPECTED_NODES = 16


def load_module(name: str, path: Path):
    """用 importlib 独立加载模块,绕开包相对导入。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(graph: dict) -> dict:
    """剥离易变字段(时间戳/run_id),其余全保留。

    必须与 test_phase13_registry_equivalence.py 的 _normalize 保持一致。
    """
    out = json.loads(json.dumps(graph, ensure_ascii=False))
    for key in VOLATILE_METADATA_KEYS:
        out.get("metadata", {}).pop(key, None)
    # capability_gaps 是 Phase 13 改造新增字段,基线输入下必须为空,剥离前先断言
    gaps = out.get("metadata", {}).pop("capability_gaps", [])
    assert gaps == [], f"基线输入下 capability_gaps 应为空，实际: {gaps}"
    return out


def main():
    # 加载 Stage 3 模块
    planning = load_module(
        "skill_graph_planning",
        PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
    )

    # 读取 tracked fixture 输入
    contract_path = INPUTS_DIR / "root_skill_contract.json"
    gate_path = INPUTS_DIR / "clarification_gate_report.json"

    if not contract_path.exists():
        print(f"ERROR: 找不到 contract fixture: {contract_path}", file=sys.stderr)
        sys.exit(1)
    if not gate_path.exists():
        print(f"ERROR: 找不到 gate fixture: {gate_path}", file=sys.stderr)
        sys.exit(1)

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))

    # 调用 create_skill_graph,run_id=None 避免写入易变 run_id
    graph = planning.create_skill_graph(contract, gate, run_id=None)
    normalized = normalize(graph)

    # 验证节点数;过少说明输入异常,直接非零退出且不落盘,防止误生成的 golden 被提交
    node_count = len(normalized.get("nodes", []))
    print(f"节点数: {node_count}")
    if node_count < MIN_EXPECTED_NODES:
        print(
            f"ERROR: 节点数 {node_count} < 预期最少 {MIN_EXPECTED_NODES}，"
            "输入 capability 不完整，拒绝写入 golden。",
            file=sys.stderr,
        )
        sys.exit(1)

    # 落盘
    GOLDEN.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"golden written: {GOLDEN}")


if __name__ == "__main__":
    main()
