# -*- coding: utf-8 -*-
"""Phase 12 L2-C 系统集成测试 — LLM Internal Reopen 接入 Phase 11 主链。

设计依据:Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md §6 验收口径。

本文件 4 个 e2e case 当前**占位**:
- 用 pytest.skip 标记,不阻塞 Stage 12 跑通(SKIPPED ≠ FAILED)
- T18 真 LLM 验收时,或 Phase 13 后续 fixture 阶段,填具体 assert + fixture
- 骨架步骤已写在每个 case 的 docstring 里,便于后续接手
"""

import pytest


def test_phase11_e2e_llm_internal_with_fake_router(tmp_path) -> None:
    """完整 Phase 11 主链 generator_provider=llm 用 FakeAdapter 走通(占位)。

    实施期步骤(T18 真 LLM 验收前补完):
      1. 构造 FakeAdapter 注册 7 dim schema_value 输出
      2. 装配 CapabilityRouter + ProviderPolicy
      3. 构造 CompilerSession(generator_provider="llm")
      4. 调 pipeline_orchestrator 入口至 Stage 4 Candidates
      5. assert run_id 下 design_space_report.json 存在
      6. assert per_dimension_batch_metadata 7 条全 status="success"
      7. assert session.is_promotable() is True
    """
    pytest.skip("T16 占位 — T18 真 LLM 验收阶段补 Phase 11 主链 fixture")


def test_phase11_e2e_mcp_agent_still_works() -> None:
    """同主链跑 mcp_agent,确认 LLM 新模块不污染 MCP Agent 路径(占位)。

    实施期步骤:
      1. CompilerSession(generator_provider="mcp_agent")
      2. 调主链 — 不应触碰 providers/litellm_adapter / candidates_batch_orchestrator
      3. assert evidence 落 stage4_mcp_agent_sidecar/
      4. assert promotable=True
    """
    pytest.skip("T16 占位 — 验 mcp_agent 路径回归,T18 阶段补 fixture")


def test_phase11_e2e_heuristic_fallback_still_works() -> None:
    """同主链跑 heuristic,确认确定性引擎不被新模块污染(占位)。

    实施期步骤:
      1. CompilerSession(generator_provider="heuristic_fallback", allow_heuristic_fallback=True)
      2. 调主链 — 走 agent_protocol.HeuristicFallbackProvider._default_evaluator
      3. assert evidence 落 stage4_agent_traces/heuristic/
      4. assert promotable=False(固化)
    """
    pytest.skip("T16 占位 — 验 heuristic_fallback 路径回归,T18 阶段补 fixture")


def test_compiler_session_is_promotable_logic_llm_path() -> None:
    """is_promotable 在 LLM 路径 + 7/7 PASS / partial fail 两种场景下的判定(占位)。

    实施期步骤:
      1. session = CompilerSession(generator_provider="llm")
      2. 注入 stage_outputs 含 design_space_report.per_dimension_batch_metadata 7 条全 success
      3. assert session.is_promotable() is True
      4. 注入同字段 6 success + 1 failed
      5. assert session.is_promotable() is False
    """
    pytest.skip("T16 占位 — 验 is_promotable LLM 路径决策,T18 阶段补 fixture")
