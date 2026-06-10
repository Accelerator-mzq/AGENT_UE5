# -*- coding: utf-8 -*-
"""生成 Stage 3 等价回归的 golden 快照。

输入来源说明:
  Schemas/examples/phase11_root_skill_contract.example.json 仅含 2 个 gameplay + 3 个 baseline
  能力(共 5 个 required 节点)，明显少于预期的 ~16 节点，因此按计划备选方案:
  使用 ProjectState/runs/run-20260417-051444-a2b8/ 下的真实成功 run 快照作为确定性输入。
  该 run 含全量 7 gameplay + 9 baseline = 16 required 能力。

改造前跑一次生成对照组;改造后测试断言输出不变。
"""
import importlib.util
import json
import sys
from pathlib import Path

# 插件根目录: Plugins/AgentBridge
PLUGIN_ROOT = Path(__file__).resolve().parents[2]

# 使用 ProjectState run 快照作为确定性输入(见模块注释)
RUN_DIR = (
    Path(__file__).resolve().parents[4]  # 项目根
    / "ProjectState"
    / "runs"
    / "run-20260417-051444-a2b8"
)

GOLDEN = Path(__file__).resolve().parent / "skill_graph_baseline_golden.json"

# 需要从输出中剥除的易变字段(时间戳 / run_id)
VOLATILE_METADATA_KEYS = {"generated_at", "source_run_id"}


def load_module(name: str, path: Path):
    """用 importlib 独立加载模块,绕开包相对导入。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(graph: dict) -> dict:
    """剥离易变字段(时间戳/run_id),其余全保留。"""
    out = json.loads(json.dumps(graph, ensure_ascii=False))
    for key in VOLATILE_METADATA_KEYS:
        out.get("metadata", {}).pop(key, None)
    return out


def main():
    # 加载 Stage 3 模块
    planning = load_module(
        "skill_graph_planning",
        PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
    )

    # 读取确定性输入快照
    contract_path = RUN_DIR / "root_skill_contract.json"
    gate_path = RUN_DIR / "clarification_gate_report.json"

    if not contract_path.exists():
        print(f"ERROR: 找不到 contract 文件: {contract_path}", file=sys.stderr)
        sys.exit(1)
    if not gate_path.exists():
        print(f"ERROR: 找不到 gate 文件: {gate_path}", file=sys.stderr)
        sys.exit(1)

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))

    # 调用 create_skill_graph,run_id=None 避免写入易变 run_id
    graph = planning.create_skill_graph(contract, gate, run_id=None)
    normalized = normalize(graph)

    # 验证节点数
    node_count = len(normalized.get("nodes", []))
    print(f"节点数: {node_count}")
    if node_count < 10:
        print(
            f"WARNING: 节点数 {node_count} 明显偏少，请检查输入 capability 是否完整。",
            file=sys.stderr,
        )

    # 落盘
    GOLDEN.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"golden written: {GOLDEN}")


if __name__ == "__main__":
    main()
