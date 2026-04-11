# 项目基线

> 文档版本：L1-Phase10-v1

## 1. 当前事实

- `Phase 6`、`Phase 7`、`Phase 8`、`Phase 9` 已完成并归档，当前阶段为 `Phase 10 已完成`，总览见 [17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md)。
- 插件层系统测试当前统一登记为 `10 个 Stage / 240 条用例`，其中 MCP 集成基线已同步到 `42` 个工具，证据见 [mcp_count_baseline_fix.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/mcp_count_baseline_fix.md)。
- 当前 Phase 10 唯一正式任务入口仍为 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)，但其状态已切换为“全部完成”。

## 2. Phase 10 产出事实

- 已在 [Plugins/AgentBridge/Compiler/pipeline/session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py) 与 [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py) 建立 Compiler Pipeline Orchestrator，覆盖 `session 管理 / 5-stage 编排 / Stage 间产物传递 / Reviewed Handoff v2 组装`。
- 已新增 [compiler_session.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/compiler_session.schema.json)，将 Session 持久化格式纳入显式 Schema 约束。
- MCP 已扩展为 `42` 个工具：`28` 个 Bridge Passthrough、`6` 个 Compiler 前端工具、`8` 个 Evidence 后端工具，验证依据见 [mcp_count_baseline_fix.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/mcp_count_baseline_fix.md) 与 [system_test_report_2026-04-11_202214.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/reports/2026-04-11/system_test_report_2026-04-11_202214.json)。
- 测试证据已标准化为 `run_id + evidence_manifest + screenshots/logs/reports/state` 目录结构，相关实现位于 [Plugins/AgentBridge/Scripts/evidence](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/evidence)。
- MonopolyGame 的 Phase 10 全链路产物已落盘到 [ProjectState/phase10](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/phase10)，包含 `12` 个核心 JSON：`session + gdd_projection + planner_output + 6 个 skill fragments + cross_review_report + build_ir + reviewed_handoff_v2`，执行摘要见 [task06_pipeline_execution_summary.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task06_pipeline_execution_summary.json)。
- 已通过 Build IR 在 UE5 Editor 中从空白关卡创建 `L_MonopolyBoard_Pipeline`，未复制 `L_MonopolyBoard` 作为推荐路径，验证见 [task07_build_ir_level_realization_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task07_build_ir_level_realization_validation.md)。
- 运行时验证证据 run_id 为 `2026-04-11_fa5c8bec`，MCP 后端裁决结果为 `pass`，`19/19` 个验证点通过、`11` 个证据项齐全，验证见 [task08_runtime_evidence_judgment_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task08_runtime_evidence_judgment_validation.md)。
- 无编辑器验收口径已切换为 `Stage 分段等价验证`，当前结果为 `6/6 passed`，证据见 [task08_no_editor_equivalent_regression.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/phase10/task08_no_editor_equivalent_regression.json)。

## 3. 当前已确认的项目真相

- MCP 前端边界固定为 `Stage 1-2`，`Stage 3-5` 继续由 Compiler Core 调度，MCP 后端边界固定为“证据读取 + 裁决 + 摘要导出”，裁决依据见 [14_MCP_Cognitive_Bridge_Anchor.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md)。
- `run_automation_tests` 的 live call 已切换为 C++ Plugin 通道，不再依赖旧的 `/remote/script/run` 路径，验证见 [run_automation_tests_after_fix.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/run_automation_tests_after_fix.json)。
- `validate_examples.py --strict` 仍是每个 TASK 的基线回归命令，并在 Phase 10 末尾继续保持通过，综合说明见 [no_editor_strategy_fix.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/no_editor_strategy_fix.json)。
- monolithic `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor` 作为长链路参考命令保留，但 Phase 10 的官方验收与自动化收口口径已改为“分段等价验证”，说明见 [no_editor_equivalent_strategy.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/no_editor_equivalent_strategy.md)。
