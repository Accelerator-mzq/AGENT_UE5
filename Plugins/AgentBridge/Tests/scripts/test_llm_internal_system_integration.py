# -*- coding: utf-8 -*-
"""Phase 12 L2-C 系统集成测试 — LLM Internal Reopen 接入 Phase 11 主链。

设计依据:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §6 验收口径。

F4 follow-up (2026-05-27):把原 T16 4 个 pytest.skip 占位 case 全部填实测试,
全部 offline、不打真 LLM。

case 选型说明
=============
原 T16 占位 docstring 假设"7 success vs 6+1 fail 决定 promotable",这是误读 —
`CompilerSession.is_promotable` 实际只看 `fast_mode` 与 `generator_provider == "heuristic_fallback"`,
**不读 design_space_report**。Case 4 改为 unit 测 `is_promotable` 的 4 种 generator_provider 状态。

Case 1 / 3 走 `run_domain_skill_runtime` 入口验:
  - router+policy 注入路径 → provider_type="llm" 且 status≠refused(不被 Phase 12 新模块污染)
  - allow_heuristic_fallback=True 路径 → provider_type="heuristic_fallback" 且 status≠refused
  - 用空 skill_graph 跳过实际 discovery_capable_node,避免 fixture 复刻 task11 的 751 行

Case 1 内还附带直跑 `LLMBatchExecutor.run_candidates_batch` 7/7 验证 LLM Internal 核心路径
(7 dim per_dimension_batch_metadata 全 success),用 FakeAdapter 完全 offline。

Case 2 验 MCP agent 路径**离线场景**下 `resolve_provider` 语义未被 Phase 12 新模块污染
(offline 无 MCP backend 无法真跑 mcp_agent;改成验"无 router/llm_client + 禁 heuristic →
必须 raise ProviderNotAvailable",这是 mcp_agent 工作流不被 silent fall-through 到 LLM batch
的关键不变量)。
"""

import asyncio

import pytest
from pydantic import BaseModel

# 项目 convention:从项目根 (pytest.ini pythonpath=.) 用全路径 import
from Plugins.AgentBridge.Compiler.pipeline.session import CompilerSession
from Plugins.AgentBridge.Compiler.providers.capability_router import (
    CapabilityRouter,
    ProviderPolicy,
)
from Plugins.AgentBridge.Compiler.providers.fake_adapter import (
    FakeAdapter,
    FakeModelProgram,
)
from Plugins.AgentBridge.Compiler.stages import agent_protocol
from Plugins.AgentBridge.Compiler.stages.candidates_batch_orchestrator import (
    AggregatedReport,
    LLMBatchExecutor,
    RetryPolicySpec,
)
from Plugins.AgentBridge.Compiler.stages.domain_skill_runtime import (
    run_domain_skill_runtime,
)


# --- 共享最小 fixture -------------------------------------------------------
# Stage 4 入口接收三个产物:skill_graph / root_skill_contract / clarification_gate_report
# 用空 nodes 让 discovery_capable_nodes 为空,避免触发 run_agent_stage4_for_node 三阶段链路
# (那需要 llm_client 老路径,FakeAdapter+router 只覆盖 candidates 子阶段)。

def _minimal_skill_graph() -> dict:
    """最小合法 skill_graph(nodes 空 → discovery_capable_nodes 也空)。"""
    return {"nodes": [], "edges": []}


def _minimal_root_skill_contract() -> dict:
    """最小合法 root_skill_contract。"""
    return {
        "constraints": [],
        "variants": [],
        "skill_instance_id": "test-skill",
    }


def _minimal_clarification_gate_report() -> dict:
    """最小合法 clarification_gate_report。"""
    return {"provisional_items": [], "blocking_items": []}


# --- Case 1 -----------------------------------------------------------------

class _CandSchema(BaseModel):
    """Case 1 用 LLMBatchExecutor 子测的 candidates 最小 schema(对齐 candidates_batch 单元测试)。"""
    dimension_id: str
    candidates: list[str]


def test_phase11_e2e_llm_internal_with_fake_router() -> None:
    """LLM Internal 路径系统集成:router+policy 注入 + LLMBatchExecutor 7/7 success。

    本 case 分两步:
      Step A: 调 run_domain_skill_runtime 入口注 router+policy(用空 skill_graph),
              验证入口接收 Phase 12 新签名不爆 + generator_provider_type="llm"
              + status="completed"(说明 LLM 路径在 Stage 4 主链不被 Phase 12 新模块污染)。
      Step B: 直接驱动 LLMBatchExecutor.run_candidates_batch 跑 7 dim FakeAdapter,
              验证 LLM Internal 核心路径产出 per_dimension_batch_metadata 7/7 全 success。

    设计权衡:不走 run_domain_skill_runtime 内部 discovery→candidates→convergence 完整三阶段
    (那需要 llm_client 老路径,fixture 需复刻 task11 的 750+ 行),
    Step A+B 联合证明"入口接收 router 不爆"+"内部 batch executor 跑通"两个关键不变量。
    """
    # ---- Step A: run_domain_skill_runtime 入口接收 router+policy ----
    fa_a = FakeAdapter()
    fa_a.program("m", outputs=[FakeModelProgram(schema_value={"dimension_id": "noop", "candidates": []})])
    router_a = CapabilityRouter()
    router_a.register(fa_a)
    policy_a = ProviderPolicy(preferred_models=["m"])

    result = run_domain_skill_runtime(
        skill_graph=_minimal_skill_graph(),
        root_skill_contract=_minimal_root_skill_contract(),
        clarification_gate_report=_minimal_clarification_gate_report(),
        phase_scope="phase11",
        fast_mode=False,
        allow_heuristic_fallback=False,  # 拒 heuristic — 必须走 LLM 路径
        llm_client=None,
        router=router_a,
        policy=policy_a,
        batch_concurrency=3,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.001),
    )

    # 入口不应 refused — router+policy 路径已注册即可被 resolve_provider 接受
    assert result["status"] != "refused", (
        f"Stage 4 router+policy 路径被 refused: {result.get('failure_reason')}"
    )
    # generator_provider_type 应为 llm(确认未 silent fall-through 到 heuristic)
    assert result["generator_provider_type"] == "llm", (
        f"非 llm provider_type: {result.get('generator_provider_type')}"
    )
    # acceptance_errors 应空(空 nodes 时 discovery_capable_nodes 也空,跳过验收)
    assert result["acceptance_errors"] == [], (
        f"非空 acceptance_errors: {result['acceptance_errors']}"
    )

    # ---- Step B: 直接驱动 LLMBatchExecutor 7/7 success ----
    fa_b = FakeAdapter()
    fa_b.program("m", outputs=[
        FakeModelProgram(schema_value={"dimension_id": f"d{i+1}", "candidates": [f"c{i+1}"]})
        for i in range(7)
    ])
    router_b = CapabilityRouter()
    router_b.register(fa_b)
    policy_b = ProviderPolicy(preferred_models=["m"], fallback_models=[])

    dims = [
        {"dimension_id": f"d{i+1}", "prompt_messages": [{"role": "user", "content": f"d{i+1}"}]}
        for i in range(7)
    ]
    executor = LLMBatchExecutor()
    report: AggregatedReport = asyncio.run(executor.run_candidates_batch(
        dimensions=dims,
        router=router_b,
        policy=policy_b,
        schema=_CandSchema,
        retry_policy=RetryPolicySpec(jitter_ms=(0, 1), backoff_base_s=0.001),
        concurrency=3,
    ))

    # 7/7 全 success — LLM Internal 核心路径打通的硬指标
    assert len(report.per_dimension) == 7, f"per_dimension 数 ≠ 7: {len(report.per_dimension)}"
    assert all(b.status == "success" for b in report.per_dimension), (
        f"非全 success: {[(b.dimension_id, b.status, b.error_class) for b in report.per_dimension]}"
    )
    assert report.promotable is True, "7/7 success 时 promotable 必须 True"
    assert report.partial is False, "7/7 success 时 partial 必须 False"


# --- Case 2 -----------------------------------------------------------------

def test_phase11_e2e_mcp_agent_still_works() -> None:
    """MCP agent 路径在 Phase 12 新模块加入后不被污染(offline 验 resolve_provider 不变量)。

    设计:offline 没有 MCP backend,无法真跑 mcp_agent 完整链路。改成验**关键不变量**:
      - 不传 router / 不传 llm_client / allow_heuristic_fallback=False
        → resolve_provider 必须 raise ProviderNotAvailable
      - 这条不变量保证 Phase 12 LLM 新模块不会 silent fall-through 让 mcp_agent 路径
        变成"无 LLM 配置时偷偷走 batch executor",这才是 mcp_agent 工作流不被污染的基础

    真 mcp_agent 链路验证已在 task11_phase11_mcp_e2e.py 覆盖(751 行,需 MCP server),
    本 case 不复刻。
    """
    # 关键 negative:resolve_provider 在没 router/llm_client + 禁 heuristic 时必须 raise
    with pytest.raises(agent_protocol.ProviderNotAvailable):
        agent_protocol.resolve_provider(
            allow_heuristic_fallback=False,
            llm_client=None,
            router=None,
            policy=None,
        )

    # 同样的 negative 走 run_domain_skill_runtime 入口 — Stage 4 应 refuse,不能 silent 走 LLM 路径
    refused = run_domain_skill_runtime(
        skill_graph=_minimal_skill_graph(),
        root_skill_contract=_minimal_root_skill_contract(),
        clarification_gate_report=_minimal_clarification_gate_report(),
        phase_scope="phase11",
        fast_mode=False,
        allow_heuristic_fallback=False,
        llm_client=None,
        router=None,
        policy=None,
    )
    assert refused["status"] == "refused", (
        f"无 LLM 配置 + 禁 heuristic 时 Stage 4 必须 refuse,实际 status={refused['status']}"
    )
    # failure_reason 中应包含 "LLM provider" / "allow_heuristic_fallback" 字样
    fr = refused.get("failure_reason", "")
    assert "LLM" in fr or "heuristic" in fr.lower(), (
        f"refuse failure_reason 与 LLM provider 决策无关:{fr!r}"
    )


# --- Case 3 -----------------------------------------------------------------

def test_phase11_e2e_heuristic_fallback_still_works() -> None:
    """heuristic_fallback 路径在 Phase 12 新模块加入后仍然 work(不被污染)。

    设计:不传 router / 不传 llm_client + allow_heuristic_fallback=True → 必须走
    HeuristicFallbackProvider,且 generator_provider_type 在 Stage 4 返回中报为
    "heuristic_fallback"。空 skill_graph 让 discovery_capable_nodes 空,跳过 evaluator 调用,
    本 case 仅验"provider 解析 + status 不 refused" 这两个最小不变量。
    """
    result = run_domain_skill_runtime(
        skill_graph=_minimal_skill_graph(),
        root_skill_contract=_minimal_root_skill_contract(),
        clarification_gate_report=_minimal_clarification_gate_report(),
        phase_scope="phase11",
        fast_mode=False,
        allow_heuristic_fallback=True,  # 关键:允许 heuristic fallback
        llm_client=None,
        router=None,
        policy=None,
    )

    # 不应 refused — allow_heuristic_fallback=True 时 resolve_provider 必返 HeuristicFallbackProvider
    assert result["status"] != "refused", (
        f"allow_heuristic_fallback=True 时仍 refused: {result.get('failure_reason')}"
    )
    # generator_provider_type 必须为 heuristic_fallback(被 Phase 12 新模块污染的迹象就是
    # 这里偷偷变成 "llm")
    assert result["generator_provider_type"] == "heuristic_fallback", (
        f"heuristic 路径 generator_provider_type 错位: {result.get('generator_provider_type')}"
    )
    # acceptance_errors 应空(空 nodes 跳过验收)
    assert result["acceptance_errors"] == [], (
        f"非空 acceptance_errors: {result['acceptance_errors']}"
    )


# --- Case 4 -----------------------------------------------------------------

def test_compiler_session_is_promotable_logic_llm_path(tmp_path) -> None:
    """`CompilerSession.is_promotable` 在四种 generator_provider 状态下的正确决策。

    is_promotable 当前实现 (pipeline/session.py:150-156):
      - fast_mode=True → False(任何 provider 都不能 promote)
      - generator_provider == "heuristic_fallback" → False(确定性引擎产物不可 promote)
      - 其他(llm / mcp_agent / None) → True
    is_promotable **不**读 design_space_report 内容,所以原 T16 占位的"7 success vs 6 success
    决定 promotable"假设是错误的,本 case 按真实实现验证。
    """
    def _make(gp: str | None, fast: bool = False) -> CompilerSession:
        """构造一个最小合法 CompilerSession;output_dir 必须存在(tmp_path)。"""
        return CompilerSession(
            session_id="test-session-id",
            created_at="2026-05-27T00:00:00+00:00",
            gdd_path=str(tmp_path / "test.md"),
            target_phase="phase11",
            output_dir=str(tmp_path),
            session_version="2.0",
            generator_provider=gp,
            fast_mode=fast,
        )

    # llm 路径 → True(LLM 产出的 run 可 promote)
    assert _make("llm").is_promotable is True
    # mcp_agent 路径 → True(MCP Agent 产出的 run 也可 promote)
    assert _make("mcp_agent").is_promotable is True
    # heuristic_fallback 路径 → 固化 False(防确定性 fallback 产物被误 promote)
    assert _make("heuristic_fallback").is_promotable is False
    # fast_mode=True 即便 generator=llm 也 False(fast_mode 跳过 Stage 4 验收 → 不可 promote)
    assert _make("llm", fast=True).is_promotable is False
    # generator_provider 未设 → True(默认乐观,Phase 11 早期 session 兼容)
    assert _make(None).is_promotable is True
    # fast_mode + 未设 generator_provider → False(fast_mode 优先)
    assert _make(None, fast=True).is_promotable is False
