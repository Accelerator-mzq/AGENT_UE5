# 项目基线

> 文档版本：L1-Phase9-v2

## 1. 当前事实

- `Phase 6` 已完成并归档，历史任务见 [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)。
- `Phase 7` 已完成并归档，历史任务见 [task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)。
- `Phase 8` 已完成并归档，收尾总览见 [10_Phase8_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/10_Phase8_Closeout.md)。
- `Phase 9` 已完成，目标为 `Plugins/AgentBridge/MCP/` 的真实可执行化与文档切换，结论见 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)。
- 插件层系统测试总表当前统一登记为 `240` 条用例。

## 2. Phase 8 已归档事实

- Skill-First 6 阶段 Compiler 主链已落地。
- Reviewed Handoff v2 与 Build IR 14 目标对象已落地。
- MonopolyGame 是 Phase 8 唯一垂直切片测试案例。
- MCP 子目录在 Phase 8 已落地目录、工具定义和基础骨架，但当时未切换为正式接入链路。

## 3. Phase 9 完成口径

- `Plugins/AgentBridge/MCP/tool_definitions.py` 维护 28 个工具定义，并负责参数到 `inputSchema` 的转换。
- `Plugins/AgentBridge/MCP/server.py` 当前承担：
  - 28 个工具的分发路由
  - stdio MCP server 创建与启动
  - 本地 service 工具与 Layer 2 资产工具实现
- `.mcp.json` 继续使用 `python Plugins/AgentBridge/MCP/server.py` 作为 `agentbridge` 的启动入口。
- Phase 9 实施前方案已归档到 [Phase9_MCP_Implementation_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md)。

## 4. 当前已确认的项目真相

- Phase 8 的运行时复盘与防回归规则继续生效，见 [08_Phase8_Retrospective_And_Phase9_Checklist.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Phase8_Retrospective_And_Phase9_Checklist.md)。
- Phase 9 切换 MCP 时，没有破坏 Phase 6/7/8 的 Python 基线回归，证据见 [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)。
- Claude Code `/mcp` 已人工确认 `agentbridge connected`，有 Editor 的 live smoke 也已通过。
