# 项目基线

> 文档版本：L1-Phase11-v1

## 1. 当前事实

- `Phase 6`、`Phase 7`、`Phase 8`、`Phase 9`、`Phase 10`、`Phase 11` 已完成并归档，当前稳定基线为 `Phase 11 已完成`，总览见 [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)。
- 当前正式阶段记录入口仍为 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)，但其状态已切换为“全部完成”。
- Phase 11 最终验收、功能覆盖与运行时证据已归档到 [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)、[phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md) 与 [task14a_standalone_runtime_smoke_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_standalone_runtime_smoke_validation.md)。

## 2. Phase 11 产出事实

- 已在 [session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py) 与 [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py) 建立 `session_version 1.0 / 2.0` 共存、`run_id`、`fast_mode`、`generator_provider` 与 `promotable` 路由，验证见 [task02_phase11_session_v2_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task02_phase11_session_v2_validation.md) 与 [task03_phase11_pipeline_v2_routing.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task03_phase11_pipeline_v2_routing.md)。
- 已形成 Phase 11 v2 主链：`Root Skill Contract -> Clarification Gate -> Skill Graph Planning -> Domain Skill Runtime -> Cross Review v2 -> Build IR v2 -> Reviewed Handoff v3`，关键收口验证见 [task10_phase11_review_lowering_handoff_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task10_phase11_review_lowering_handoff_validation.md)。
- 已新增并验通 Phase 11 Schema 示例集；当前 `validate_examples.py --strict` 结果为 `26/26` 通过，最终验收汇总见 [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)。
- MCP 当前可见工具注册数为 `53`，其中 `49` 个为正式主工具、`4` 个为兼容 alias；收尾时已将该事实写回 Current 文档与 Phase 11 架构/Schema 文档，前端工具升级证据见 [task05_phase11_mcp_frontend_tools.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task05_phase11_mcp_frontend_tools.md)。
- Stage 4 当前具备三路生成策略：`mcp_agent` 主路径、`heuristic_fallback` 显式后备、`llm` 集成但高负载验收暂缓；相关证据见 [task09a_phase11_llm_internal.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09a_phase11_llm_internal.md)、[task09b_phase11_three_provider_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09b_phase11_three_provider_validation.md) 与 [task09b_llm_internal_pause_sync.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09b_llm_internal_pause_sync.md)。
- Monopoly 的 Phase 11 编译级端到端 run 已再次验证，当前 compiler-level E2E run 为 [run-20260417-051425-aad0](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260417-051425-aad0)，证据见 [task11_phase11_e2e_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task11_phase11_e2e_validation.md)。
- Run compare/promote、完整 fast_mode、Baseline Template 全套已交付，证据见 [task12_phase11_run_governance_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task12_phase11_run_governance_validation.md)、[task13_phase11_fast_mode_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task13_phase11_fast_mode_validation.md) 与 [task14_phase11_baseline_template_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task14_phase11_baseline_template_validation.md)。
- UE 运行时最小可玩性与 Baseline Domain 已通过 Editor game 与 staged standalone 双路径验证，证据见 [task14a_ue_runtime_playability_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_ue_runtime_playability_validation.md)、[task14a_baseline_domain_runtime_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_baseline_domain_runtime_validation.md) 与 [task14a_standalone_runtime_smoke_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_standalone_runtime_smoke_validation.md)。

## 3. 当前已确认的项目真相

- MCP 前端边界固定为 `Stage 1-3`，`Stage 4-7` 由 Compiler Core 调度；MCP 后端边界固定为“证据读取 + 裁决 + 摘要导出”，高优先级治理口径仍以 [14_MCP_Cognitive_Bridge_Anchor.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md) 为准。
- `validate_examples.py --strict` 仍是每个主干 TASK 的基础回归命令；Phase 11 完成时仍保持通过，综合说明见 [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)。
- 标准的 UE5 运行时验收路径现在是 `Editor game` 与 `cooked/staged standalone`；`raw DebugGame + .uproject` 不再作为官方验收路径，说明见 [task14a_standalone_runtime_smoke_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_standalone_runtime_smoke_validation.md)。
- `LLM Internal` 已完成接入级实现，但高负载 prompt 稳定性与完整 TASK 09B 验收暂缓；当前 Phase 11 的正式主路径仍是 `MCP Agent`，该残留不阻塞本阶段收尾，详见 [task09b_llm_internal_pause_sync.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09b_llm_internal_pause_sync.md)。
