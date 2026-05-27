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
    """直接调 LLMBatchExecutor + BudgetTracker 跑 7 dimension 真 LLM 验收。

    最小化合理 fixture:不拉 Stages 1-3,直接构造 7 个 Stage 4 candidates 的 batch 输入,
    用真 router/policy 调 LLM,落盘 evidence。

    返回(成功路径):
      {
        "run_id": str,
        "promotable": bool,
        "per_dim_count": int,
        "per_dim_status": list[str],
        "per_dim_attempts": list[int],
        "per_dim_durations_ms": list[int],
        "design_space_report_path": str,
        "llm_usage_path": str,
        "aggregation_path": str,
      }
    """
    # 延迟 import:这些模块只有真跑路径才需要(skip-real-llm 路径不进此函数)
    import asyncio
    from pydantic import BaseModel
    from Plugins.AgentBridge.Compiler.stages.candidates_batch_orchestrator import (
        LLMBatchExecutor, RetryPolicySpec,
    )
    from Plugins.AgentBridge.Compiler.observability.secrets import redact_mapping

    # ----- 1. Schema:LLM 单 dim 输出契约 -----
    class CandidatesDimOutput(BaseModel):
        # 单 dimension 的 LLM 输出 schema(只校 shape,不强约束候选数量)
        dimension_id: str
        candidates: list[dict]

    # ----- 2. Fixture:7 个 dimension(Monopoly 风格,与 Phase 11 主链贴近)-----
    dim_specs = [
        ("dim-board-layout-001", "棋盘世界布局", "Monopoly 风格 28 格环形棋盘的几何与可读性"),
        ("dim-board-spacing-002", "格子间距", "玩家筹码与移动路径的间距策略"),
        ("dim-camera-view-003", "镜头视角", "默认观战镜头(俯视/45度/自由)"),
        ("dim-hud-layout-004", "HUD 布局", "玩家面板、骰子、按钮的屏幕占位"),
        ("dim-piece-style-005", "棋子风格", "玩家筹码的几何风格(卡通/写实/低多边形)"),
        ("dim-tile-decoration-006", "格子装饰", "tile 的视觉元素丰富度"),
        ("dim-color-palette-007", "色彩调色板", "全局主色调与对比策略"),
    ]
    dimensions: list[dict[str, Any]] = []
    for dim_id, dim_name, desc in dim_specs:
        user_content = (
            f"你是 UE5 游戏设计 agent。请为下面这个设计维度生成 2-3 个候选方向。\n\n"
            f"维度 ID:{dim_id}\n"
            f"维度名:{dim_name}\n"
            f"维度描述:{desc}\n\n"
            f"约束:满足 must_satisfy=[关卡内可读 / 玩家不混淆],不得违反 must_not=[屏幕拥挤 / 路径不清]。\n\n"
            f"输出 JSON,只包含 dimension_id 和 candidates 数组。每个 candidate 包含 candidate_id, name, description。\n"
            f"严格只返回一个 JSON object,不要 markdown 包裹。"
        )
        dimensions.append({
            "dimension_id": dim_id,
            "prompt_messages": [
                {"role": "system", "content": (
                    "你是 UE5 设计编译器内置的 candidates generator agent。"
                    "你的任务:为给定的设计维度生成多个候选方向。"
                    "永远只输出符合 schema 的 JSON object,不要解释、不要 markdown。"
                )},
                {"role": "user", "content": user_content},
            ],
        })

    # ----- 3. 跑 LLMBatchExecutor -----
    executor = LLMBatchExecutor()
    # 默认 max_attempts=3 + exponential backoff + jitter (100,500),对齐 design doc §4.2
    retry_policy = RetryPolicySpec()
    concurrency = int(policy.extra.get("concurrency", {}).get("candidates_batch", 3))

    print(
        f"  跑 7 dim batch:concurrency={concurrency}, "
        f"max_attempts={retry_policy.max_attempts}, model={policy.preferred_models[0]}"
    )
    print("  调真 LLM,预计 30-90 秒...")

    report = asyncio.run(executor.run_candidates_batch(
        dimensions=dimensions,
        router=router,
        policy=policy,
        schema=CandidatesDimOutput,
        retry_policy=retry_policy,
        concurrency=concurrency,
    ))

    # ----- 4. evidence 落盘到 ProjectState/runs/{run_id}/ -----
    run_dir = PROJECT_ROOT / "ProjectState" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    # 4a. design_space_report.json — 模拟 Phase 11 主链输出格式
    design_space_report = {
        "report_version": "1.0",
        "skill_instance_id": "phase12-llm-internal-reopen-acceptance",
        "discovery_dimensions": [
            {
                "dimension_id": d["dimension_id"],
                "name": d["dimension_id"],
                "constraint_source": "variant",
                "variant_bounds": {"must_satisfy": [], "must_not": []},
                "design_freedom": "high",
            }
            for d in dimensions
        ],
        "locked_dimensions": [],
        "metadata": {
            "generated_at": datetime.datetime.now().isoformat() + "Z",
            "generator": "AgentBridge.Phase12.LLMBatchExecutor.AcceptanceRun",
        },
        "per_dimension_batch_metadata": [
            {
                "dimension_id": b.dimension_id,
                "model": b.model or "unknown",
                "attempt_count": b.attempt_count,
                "duration_ms": b.duration_ms,
                "usage": b.usage or {},
                "status": b.status,
                "error_class": b.error_class,
                "raw_response_id": b.raw_response_id,
            }
            for b in report.per_dimension
        ],
    }
    dsr_path = run_dir / "design_space_report.json"
    dsr_path.write_text(
        json.dumps(design_space_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 4b. stage4_agent_traces/llm_internal/dim_*.json
    traces_dir = run_dir / "stage4_agent_traces" / "llm_internal"
    traces_dir.mkdir(parents=True, exist_ok=True)
    for i, b in enumerate(report.per_dimension):
        # 防御性脱敏:即便 ProviderCall 没明显放 api_key 在 messages 里,
        # 落盘前还是过一次 redact_mapping 防意外
        trace = {
            "dimension_id": b.dimension_id,
            "model": b.model,
            "attempt_count": b.attempt_count,
            "duration_ms": b.duration_ms,
            "usage": b.usage,
            "status": b.status,
            "error_class": b.error_class,
            "raw_response_id": b.raw_response_id,
            "parsed_payload": b.parsed_payload,
            "prompt_messages": [
                redact_mapping(m) if isinstance(m, dict) else m
                for m in b.prompt_messages
            ],
        }
        (traces_dir / f"dim_{i+1}.json").write_text(
            json.dumps(trace, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # 4c. aggregation.json
    aggregation = {
        "aggregation_id": report.aggregation_id,
        "run_id": run_id,
        "promotable": report.promotable,
        "partial": report.partial,
        "per_dim_count": len(report.per_dimension),
        "per_dim_success": sum(1 for b in report.per_dimension if b.status == "success"),
        "per_dim_failed": sum(1 for b in report.per_dimension if b.status == "failed"),
    }
    aggregation_path = traces_dir / "aggregation.json"
    aggregation_path.write_text(
        json.dumps(aggregation, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    # 4d. llm_usage.json — BudgetTracker observe-only dump
    bt = BudgetTracker(observe_only=True)
    for b in report.per_dimension:
        if b.usage:
            bt.record(
                dimension_id=b.dimension_id,
                model=b.model or "unknown",
                # 暂不算 cost(observe-only),只透传 token usage
                cost_usd=0.0,
                usage={
                    "prompt": int(b.usage.get("prompt", 0)),
                    "completion": int(b.usage.get("completion", 0)),
                    "total": int(b.usage.get("total", 0)),
                },
            )
    usage_path = run_dir / "llm_usage.json"
    bt.dump_evidence(usage_path)

    print(f"  run_dir 产物落盘:{run_dir}")
    print(
        f"  promotable={report.promotable}, "
        f"per_dim_success={aggregation['per_dim_success']}/7"
    )

    return {
        "run_id": run_id,
        "promotable": report.promotable,
        "per_dim_count": len(report.per_dimension),
        "per_dim_status": [b.status for b in report.per_dimension],
        "per_dim_attempts": [b.attempt_count for b in report.per_dimension],
        "per_dim_durations_ms": [b.duration_ms for b in report.per_dimension],
        "design_space_report_path": str(dsr_path.relative_to(PROJECT_ROOT)),
        "llm_usage_path": str(usage_path.relative_to(PROJECT_ROOT)),
        "aggregation_path": str(aggregation_path.relative_to(PROJECT_ROOT)),
    }


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
