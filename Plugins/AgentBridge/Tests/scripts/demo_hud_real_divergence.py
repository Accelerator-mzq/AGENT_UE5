"""真实编译 demo：用 Heuristic Fallback 跑一次非 fast_mode 的 Stage 4，
产出修复后 baseline HUD 的真发散 fragment（含 selected_realization）。

只读运行核心编译逻辑（不改任何核心代码），加载现成 Stage 1-3 产物作为输入，
把 HUD fragment 落盘到 ProjectState/Reports/<today>/ 作为端到端证据。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Compiler.stages import domain_skill_runtime as dsr  # noqa: E402

# 用现成完整 run 的 Stage 1-3 产物作为输入（这些是真实 GDD 编译出的上游）
SRC_RUN = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260417-051444-a2b8"
OUT_DIR = PROJECT_ROOT / "ProjectState" / "Reports" / "2026-05-29"


def _load(name: str) -> dict:
    return json.loads((SRC_RUN / name).read_text(encoding="utf-8"))


def main() -> int:
    root_skill_contract = _load("root_skill_contract.json")
    clarification_gate_report = _load("clarification_gate_report.json")
    skill_graph = _load("skill_graph.json")

    # 非 fast_mode + 无 llm_client + allow_heuristic_fallback=True → HeuristicFallbackProvider
    # 这样 HUD（allows_design_space_discovery=True）会真正走 Discovery/Candidates/Convergence
    result = dsr.run_domain_skill_runtime(
        skill_graph=skill_graph,
        root_skill_contract=root_skill_contract,
        clarification_gate_report=clarification_gate_report,
        phase_scope="phase11_hud_real_divergence_demo",
        fast_mode=False,
        allow_heuristic_fallback=True,
        llm_client=None,
    )

    print("Stage 4 status:", result.get("status"))

    fragments = result.get("skill_fragments", [])
    hud = next(
        (f for f in fragments if f.get("skill_instance_id") == "skill-baseline-hud"),
        None,
    )
    if hud is None:
        print("ERROR: 未找到 skill-baseline-hud fragment")
        return 1

    spec = next(iter(hud.get("spec_fragments", {}).values()), {})
    selected = spec.get("selected_realization")
    print("HUD status:", hud.get("status"))
    print("HUD spec_fragments.selected_realization 是否存在:", "selected_realization" in spec)
    print("HUD selected_realization:", json.dumps(selected, ensure_ascii=False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "hud_real_divergence_fragment.json"
    out_path.write_text(json.dumps(hud, ensure_ascii=False, indent=2), encoding="utf-8")
    print("HUD fragment 已落盘:", out_path)

    # 断言：修复后真发散下 HUD 的 selected_realization 必须非空
    if not selected:
        print("FAIL: selected_realization 为空——发散未落地")
        return 1
    print("PASS: HUD 真发散结果已落入 spec_fragments.selected_realization")
    return 0


if __name__ == "__main__":
    sys.exit(main())
