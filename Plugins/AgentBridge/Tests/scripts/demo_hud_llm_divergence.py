"""真实 LLM 编译 demo：用 minimaxi 配置跑一次 HUD 节点的真实发散。

与 demo_hud_real_divergence.py(heuristic 兜底)对照：
本脚本传入真实 llm_client，HUD 走 LLM Provider 驱动的 Discovery/Candidates/Convergence，
产出"有设计语义"的发散 fragment，而非机械拼接。

需用带 anthropic SDK 的解释器运行：
  C:\\Python312\\python.exe Plugins/AgentBridge/Tests/scripts/demo_hud_llm_divergence.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Compiler.stages import domain_skill_runtime as dsr  # noqa: E402
from Plugins.AgentBridge.Compiler.stages.llm_client import load_llm_client_from_config  # noqa: E402

SRC_RUN = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260417-051444-a2b8"
OUT_DIR = PROJECT_ROOT / "ProjectState" / "Reports" / "2026-05-29"


def _load(name: str) -> dict:
    return json.loads((SRC_RUN / name).read_text(encoding="utf-8"))


def _only_hud_graph(graph: dict) -> dict:
    """裁剪 skill_graph 到只剩 HUD 节点：省 token、聚焦对比对象。

    HUD 的 dependencies 在裁剪后置空，避免拓扑排序找不到前置节点。
    """
    hud = None
    for n in graph.get("nodes", []):
        if n.get("instance_id") == "skill-baseline-hud":
            hud = dict(n)
            break
    if hud is None:
        raise RuntimeError("skill_graph 中找不到 skill-baseline-hud")
    hud["dependencies"] = []
    hud["coupling"] = []
    trimmed = dict(graph)
    trimmed["nodes"] = [hud]
    trimmed["edges"] = []
    return trimmed


def main() -> int:
    client = load_llm_client_from_config()
    if client is None:
        print("ERROR: llm_client 加载失败（需带 anthropic SDK 的解释器 + 有效配置）")
        return 1
    print("LLM client:", client.model, "| base_url:", client.base_url)

    root_skill_contract = _load("root_skill_contract.json")
    clarification_gate_report = _load("clarification_gate_report.json")
    skill_graph = _only_hud_graph(_load("skill_graph.json"))

    result = dsr.run_domain_skill_runtime(
        skill_graph=skill_graph,
        root_skill_contract=root_skill_contract,
        clarification_gate_report=clarification_gate_report,
        phase_scope="phase11_hud_llm_divergence_demo",
        fast_mode=False,
        allow_heuristic_fallback=False,   # 强制走 LLM，不许回退兜底
        llm_client=client,
    )

    print("Stage 4 status:", result.get("status"))
    fragments = result.get("skill_fragments", [])
    hud = next((f for f in fragments if f.get("skill_instance_id") == "skill-baseline-hud"), None)
    if hud is None:
        print("ERROR: 未找到 skill-baseline-hud fragment")
        print("raw result keys:", list(result.keys()))
        return 1

    spec = next(iter(hud.get("spec_fragments", {}).values()), {})
    print("HUD status:", hud.get("status"))
    print("selected_realization:", json.dumps(spec.get("selected_realization"), ensure_ascii=False, indent=2))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "hud_llm_divergence_fragment.json"
    out_path.write_text(json.dumps(hud, ensure_ascii=False, indent=2), encoding="utf-8")
    # 同时落盘三份总览，便于看 LLM 发现的原始维度/候选
    for key in ("design_space_report", "realization_candidates", "converged_realization_pack"):
        (OUT_DIR / f"hud_llm_{key}.json").write_text(
            json.dumps(result.get(key, {}), ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print("已落盘:", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
