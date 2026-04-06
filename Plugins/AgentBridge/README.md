# AgentBridge — UE5 通用 Agent 开发框架插件

> 插件版本：v0.8.0
> 文档口径：Phase 9 已完成
> 目标引擎版本：UE5.5.4

## 1. 插件定义

`AgentBridge` 是面向 UE5 项目的通用 Agent 开发框架插件，提供：

- Skill Compiler Plane
- Reviewed Handoff
- Execution Orchestrator
- L1 / L2 / L3 受控工具体系
- 写后读回、Schema 校验、回归与证据留存
- Claude Code 可接入的 MCP Server

项目层负责输入、实例和治理；插件层负责通用编译、执行与验证框架。

## 2. 当前实现状态

### 已稳定

- C++ Editor Plugin + Bridge 三通道
- L1 / L2 / L3 工具体系
- Reviewed Handoff / Run Plan / Handoff Runner
- Greenfield / Brownfield / Playable Runtime 主链

### 已完成阶段沉淀

- `Scripts/orchestrator/`：validation inserter / recovery planner / minimal promotion / regression summary 已在 Phase 7 落地
- `Skills/base_domains/`：registry / loader / `qa_validation` / `planning_governance` 已在 Phase 7 落地
- `Skills/genre_packs/jrpg/`：第二个真实类型包已在 Phase 7 落地
- `Compiler/`：Phase 8 Skill-First 6 阶段骨架已落地
- `SkillTemplates/`：Phase 8 Monopoly Template Pack 已落地
- `MCP/`：Phase 9 已从占位骨架升级为可工作的 stdio MCP Server 实现
- Claude Code `/mcp` 已人工确认 `agentbridge connected`，工具数为 28
- 有 Editor 的 live smoke 已通过，真实返回 `Mvpv4TestCodex` / `/Game/Maps/L_MonopolyBoard`
- `Tests/SystemTestCases.md` / `run_system_tests.py` 当前统一登记为 `240` 条总表口径

## 3. 目录结构

```text
AgentBridge/
├── README.md
├── AGENTS.md
├── Source/
├── Scripts/
│   ├── compiler/
│   ├── orchestrator/
│   ├── bridge/
│   └── validation/
├── Compiler/
├── Schemas/
├── Specs/
├── Skills/
├── SkillTemplates/
├── MCP/
├── Docs/
├── Tests/
└── Gauntlet/
```

## 4. 当前阅读顺序

1. 本文件
2. `Docs/architecture_overview.md`
3. `AGENTS.md`
4. `Docs/tool_contract_v0_1.md`
5. `Docs/compiler_design.md`
6. `MCP/README.md`
7. `Tests/SystemTestCases.md`

## 5. 当前边界

- Greenfield 主链必须保持稳定
- Brownfield 当前只真正支持 append / new-actor 最小闭环
- `patch / replace / migrate` 当前只做到表达、校验与阻断
- 项目级当前正式任务入口是 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- Phase 9 收尾与软归档口径见 [11_Phase9_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/11_Phase9_Closeout.md) 与 [task9_phase9.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task9_phase9.md)
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 当前统一登记为 `240` 条用例
- Phase 9 验证证据见 [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)
