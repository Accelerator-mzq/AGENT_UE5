# AgentBridge — UE5 通用 Agent 开发框架插件

> 插件版本：v0.7.0
> 文档口径：Phase 7 已归档
> 目标引擎版本：UE5.5.4

## 1. 插件定义

`AgentBridge` 是面向 UE5 项目的通用 Agent 开发框架插件，提供：

- Skill Compiler Plane
- Reviewed Handoff
- Execution Orchestrator
- L1 / L2 / L3 受控工具体系
- 写后读回、Schema 校验、回归与证据留存

项目层负责输入、实例和治理；插件层负责通用编译、执行与验证框架。

## 2. 当前实现状态

### 已稳定

- C++ Editor Plugin + Bridge 三通道
- L1 / L2 / L3 工具体系
- Reviewed Handoff / Run Plan / Handoff Runner
- Greenfield / Brownfield / Playable Runtime 主链

### 最近已完成阶段

- `Scripts/orchestrator/`：validation inserter / recovery planner / minimal promotion / regression summary 已在 Phase 7 落地
- `Skills/base_domains/`：registry / loader / `qa_validation` / `planning_governance` 已在 Phase 7 落地
- `Skills/genre_packs/jrpg/`：第二个真实类型包已在 Phase 7 落地
- `Scripts/run_jrpg_turn_based_demo.py`：已作为 Phase 7 JRPG 主入口归档留证

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
├── Schemas/
├── Specs/
├── Skills/
├── Docs/
├── Tests/
└── Gauntlet/
```

## 4. 推荐阅读顺序

1. 本文件
2. `Docs/architecture_overview.md`
3. `AGENTS.md`
4. `Docs/tool_contract_v0_1.md`
5. `Docs/compiler_design.md`
6. `Docs/reviewed_handoff_design.md`
7. `Docs/greenfield_pipeline.md`
8. `Docs/skills_and_specs_overview.md`
9. `Docs/editor_screenshot_evidence_workflow.md`
10. `Docs/genre_pack_core_design.md`
11. `Docs/boardgame_playable_pipeline.md`
12. `Tests/SystemTestCases.md`

## 5. 当前边界

- Greenfield 主链必须保持稳定
- Brownfield 当前只真正支持 append / new-actor 最小闭环
- `patch / replace / migrate` 当前只做到表达、校验与阻断
- 项目级 `task.md` 在阶段进行中作为任务入口，阶段结束后归档到 `Docs/History/Tasks/`
- Phase 7 归档后，[SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 已同步到 `230` 条总表口径
