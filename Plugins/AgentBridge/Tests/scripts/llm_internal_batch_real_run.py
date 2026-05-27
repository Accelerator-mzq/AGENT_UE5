#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""真 LLM 端到端验收脚本 — Phase 12 LLM Internal Reopen 主验收。

跑 Phase 11 主链 generator_provider=llm,7 dimension 全 PASS 验证 promotable=True。

执行:
    python Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py --repeat 1

干跑 smoke(不调真 LLM,只测 acceptance machinery):
    python Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py --skip-real-llm

前置:
    Plugins/AgentBridge/Config/llm_config.yaml 含真 api_key(不在 git 中)。

产物:
    ProjectState/runs/{run_id}/design_space_report.json
    ProjectState/runs/{run_id}/llm_usage.json
    ProjectState/runs/{run_id}/stage4_agent_traces/llm_internal/dim_*.json
    ProjectState/runs/{run_id}/stage4_agent_traces/llm_internal/aggregation.json
    ProjectState/Reports/{date}/llm_internal_reopen_acceptance.md
    ProjectState/Reports/{date}/llm_internal_reopen_acceptance.json

实施依据:
    Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §6 验收口径
    Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md §17
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
import uuid
from pathlib import Path
from typing import Any


# Plugins/AgentBridge/Tests/scripts/llm_internal_batch_real_run.py
#   parents[0] = scripts
#   parents[1] = Tests
#   parents[2] = AgentBridge
#   parents[3] = Plugins
#   parents[4] = 项目根(D:/UnrealProjects/Mvpv4TestCodex)
PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 这些 import 仅在真跑模式下才会真正用到;干跑模式不依赖 router 也能跑完 acceptance machinery。
from Plugins.AgentBridge.Compiler.providers.model_registry import build_default_router  # noqa: E402
from Plugins.AgentBridge.Compiler.runtime.budget_tracker import BudgetTracker  # noqa: E402


# acceptance 产物的固定锚点(用于 acceptance.md 链接 + 失败时占位返回)
SPEC_REF = "Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md"
PLAN_REF = "Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md"


def build_acceptance_payload(
    *,
    spec_path: str,
    date: str,
    repeat: int,
    runs: list[dict],
) -> dict:
    """汇总 acceptance JSON payload。

    all_promotable 用于退出码判定:全 True 才视为整体 PASS。
    """
    return {
        "spec": spec_path,
        "plan": PLAN_REF,
        "date": date,
        "repeat": repeat,
        "all_promotable": all(r.get("promotable", False) for r in runs) if runs else False,
        "runs": runs,
    }


def render_acceptance_md(payload: dict) -> str:
    """生成 acceptance.md(简明摘要 + per-run 折叠)。"""
    md_lines = [
        f"# LLM Internal Reopen — Acceptance Report ({payload['date']})",
        "",
        f"- Spec: `{payload['spec']}`",
        f"- Plan: `{payload['plan']}`",
        f"- 跑了 {payload['repeat']} 轮,全部 promotable = **{payload['all_promotable']}**",
        "",
        "## Per-Run 摘要",
        "",
    ]
    if not payload.get("runs"):
        md_lines.append("(无 run 记录 — 可能干跑模式或 router 不可用)")
        md_lines.append("")
        return "\n".join(md_lines)

    for r in payload["runs"]:
        md_lines.append(f"### {r['run_id']}")
        md_lines.append(f"- promotable: **{r.get('promotable', False)}**")
        md_lines.append(f"- per_dim_count: {r.get('per_dim_count', 0)}")
        md_lines.append(f"- per_dim_status: {r.get('per_dim_status', [])}")
        md_lines.append(f"- design_space_report: `{r.get('design_space_report_path', '')}`")
        md_lines.append(f"- llm_usage: `{r.get('llm_usage_path', '')}`")
        if r.get("error"):
            md_lines.append(f"- error: `{r['error']}`")
        md_lines.append("")
    return "\n".join(md_lines)


def run_phase11_pipeline_with_llm(
    *,
    router: Any,
    policy: Any,
    run_id: str,
    reports_dir: Path,
) -> dict:
    """单 run 入口 — 触发 Phase 11 主链跑到 Stage 4,拿 per-dimension batch metadata。

    实施步骤(参 task11_phase11_mcp_e2e.py 范式):
      1. 创建 CompilerSession(generator_provider="llm")
      2. 加载 root_skill_contract + 其他前置 stage 产物(可用既有 fixture)
      3. 调 pipeline_orchestrator 跑到 Stage 4 + 注入 router/policy/budget_tracker
      4. 从 Stage 4 产物提取 design_space_report.per_dimension_batch_metadata
      5. 落盘 design_space_report.json + llm_usage.json + stage4_agent_traces/

    返回(成功路径):
      {
        "run_id": str,
        "promotable": bool,
        "per_dim_count": int,
        "per_dim_status": list[str],
        "design_space_report_path": str,
        "llm_usage_path": str,
      }

    本骨架先 raise NotImplementedError,T18 阶段补具体调用。
    """
    raise NotImplementedError(
        f"T18 实施期补完整 Phase 11 主链 fixture(参 task11_phase11_mcp_e2e.py)。"
        f" run_id={run_id} 产物应落 ProjectState/runs/{run_id}/。"
    )


def _build_failure_run_record(
    *,
    run_id: str,
    error_msg: str,
) -> dict:
    """构造失败路径的 run 记录(NotImplementedError / 真 LLM 调用异常等)。"""
    return {
        "run_id": run_id,
        "promotable": False,
        "per_dim_count": 0,
        "per_dim_status": [],
        "design_space_report_path": f"ProjectState/runs/{run_id}/design_space_report.json",
        "llm_usage_path": f"ProjectState/runs/{run_id}/llm_usage.json",
        "error": error_msg,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Phase 12 LLM Internal Reopen 真 LLM 验收脚本",
    )
    parser.add_argument("--repeat", type=int, default=1, help="跑几轮(默认 1)")
    parser.add_argument("--config", type=str, default=None, help="覆盖默认 llm_config.yaml 路径")
    parser.add_argument(
        "--skip-real-llm", action="store_true",
        help="跳过真 LLM 调用(干跑 acceptance machinery 用,T17 验收脚本本身的 smoke)",
    )
    args = parser.parse_args()

    # ---- 路径准备(reports_dir 无论 skip 与否都建,确保 smoke 时落 acceptance) ----
    today = datetime.date.today().isoformat()
    reports_dir = PROJECT_ROOT / "ProjectState" / "Reports" / today
    reports_dir.mkdir(parents=True, exist_ok=True)

    # ---- 装配 router/policy(--skip-real-llm 路径短路) ----
    router = None
    policy = None
    if not args.skip_real_llm:
        router_with_policy = build_default_router(args.config)
        if router_with_policy is None:
            print(
                "ERROR: llm_config.yaml 不可用 — 检查 api_key 是否非占位符,"
                "或加 --skip-real-llm 干跑",
                file=sys.stderr,
            )
            return 2
        router, policy = router_with_policy

    # ---- --skip-real-llm 路径:写一份空的 acceptance,exit 0 ----
    if args.skip_real_llm:
        print("⚠ 干跑模式 (--skip-real-llm):跳过真 LLM 调用 — 仅测脚本流程")
        payload = build_acceptance_payload(
            spec_path=SPEC_REF,
            date=today,
            repeat=0,
            runs=[],
        )
        # smoke 模式下 all_promotable 是 vacuous False,但退出码用专用分支:0
        acceptance_json = reports_dir / "llm_internal_reopen_acceptance.smoke.json"
        acceptance_md = reports_dir / "llm_internal_reopen_acceptance.smoke.md"
        acceptance_json.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        acceptance_md.write_text(render_acceptance_md(payload), encoding="utf-8")
        print(f"\n📋 Smoke acceptance written:")
        print(f"  {acceptance_md}")
        print(f"  {acceptance_json}")
        return 0

    # ---- 真跑路径:循环 repeat 轮 ----
    all_runs: list[dict] = []
    overall_ok = True
    for i in range(args.repeat):
        run_id = (
            f"run-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            f"-{uuid.uuid4().hex[:6]}"
        )
        print(f"\n=== 启动 run {i + 1}/{args.repeat}: {run_id} ===")

        try:
            run_result = run_phase11_pipeline_with_llm(
                router=router, policy=policy,
                run_id=run_id, reports_dir=reports_dir,
            )
        except NotImplementedError as exc:
            print(f"❌ T18 阶段未补完整 fixture: {exc}", file=sys.stderr)
            overall_ok = False
            run_result = _build_failure_run_record(
                run_id=run_id,
                error_msg=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 — 任意 Phase 11 异常都要落盘 + 转下一轮
            print(f"❌ Phase 11 主链失败: {type(exc).__name__}: {exc}", file=sys.stderr)
            overall_ok = False
            run_result = _build_failure_run_record(
                run_id=run_id,
                error_msg=f"{type(exc).__name__}: {exc}",
            )
        all_runs.append(run_result)

    # ---- 落 acceptance report ----
    acceptance_json = reports_dir / "llm_internal_reopen_acceptance.json"
    acceptance_md = reports_dir / "llm_internal_reopen_acceptance.md"

    payload = build_acceptance_payload(
        spec_path=SPEC_REF,
        date=today,
        repeat=args.repeat,
        runs=all_runs,
    )
    acceptance_json.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    acceptance_md.write_text(render_acceptance_md(payload), encoding="utf-8")

    print(f"\n📋 Acceptance reports written:")
    print(f"  {acceptance_md}")
    print(f"  {acceptance_json}")

    return 0 if (payload["all_promotable"] and overall_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
