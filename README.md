# Mvpv4TestCodex

> 目标引擎版本：UE5.5.4
> 当前状态：Phase 9 已完成 / AgentBridge MCP Server 已正式接入

## 项目简介

`Mvpv4TestCodex` 是基于 `AgentBridge` 插件的 UE5 工程，用于验证从设计输入到编译、handoff、执行、回归、治理与证据留存的完整开发链路。

已归档阶段：

- Phase 6： [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)
- Phase 7 准备期： [task5_phase7_preparation.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task5_phase7_preparation.md)
- Phase 7： [task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)
- Phase 8： [task8_phase8.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task8_phase8.md)

## 当前入口

- 当前索引： [00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- 当前阶段任务与完成记录： [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- Phase 9 收尾总览： [11_Phase9_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/11_Phase9_Closeout.md)
- Phase 9 历史任务副本： [task9_phase9.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task9_phase9.md)
- Phase 9 验证证据： [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)
- Phase 9 实施前方案归档： [Phase9_MCP_Implementation_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md)
- 插件入口： [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)

## Phase 9 完成结果

- `Plugins/AgentBridge/MCP/` 已从 Phase 8 占位骨架升级为真实可工作的 stdio MCP Server
- `agentbridge` 已可通过 Claude Code `/mcp` 连接，并注册全部 28 个工具
- 有 Editor 的 live smoke 已返回真实工程 `Mvpv4TestCodex` 和真实关卡 `/Game/Maps/L_MonopolyBoard`
- Stage 1 / 4 / 5 / 6 / 7 已串行通过，完成 `--no-editor` 等价覆盖留证

## 常用命令

```powershell
# MCP 代码静态校验
python -m py_compile Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py

# Schema 示例校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 无 Editor 等价验证入口
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# Claude Code 通过 .mcp.json 自动启动的 MCP Server
python Plugins/AgentBridge/MCP/server.py
```

## 目录结构

```text
Mvpv4TestCodex/
├── AGENTS.md
├── README.md
├── CLAUDE.md
├── task.md
├── Scripts/
├── Source/
├── ProjectInputs/
├── ProjectState/
├── Docs/
└── Plugins/
    └── AgentBridge/
```

## 当前约定

- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 是 Phase 9 正式任务入口与完成记录
- Phase 9 实施前方案已归档到 [Phase9_MCP_Implementation_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md)
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 当前统一登记为 `240` 条用例
- 当前 Phase 9 收口证据见 [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)
- Phase 9 软归档口径见 [11_Phase9_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/11_Phase9_Closeout.md) 与 [phase9_archive_preflight_checklist_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_archive_preflight_checklist_2026-04-06.md)
