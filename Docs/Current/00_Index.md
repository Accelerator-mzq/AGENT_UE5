# 当前阶段文档索引

> 阶段名称：Phase 8 — Skill-First Compiler Reset + MonopolyGame 垂直切片
> 状态：Active
> 启动日期：2026-04-03
> 文档版本：L1-Phase8-v1

## 本目录文件

| 文件 | 摘要 |
|------|------|
| 01_Project_Baseline.md | 当前项目基线（含 Phase 8 已产出事实） |
| 02_Current_Phase_Goals.md | Phase 8 阶段目标与成功标准 |
| 03_Active_Backlog.md | Phase 8 待办与进展 |
| 04_Open_Risks.md | Phase 8 当前风险 |
| 05_Implementation_Boundary.md | Phase 8 实施边界 |
| 06_Current_Task_List.md | 任务入口说明 |
| 07_Evidence_And_Artifacts.md | Reports / Evidence / Snapshots 的落盘约定 |

## 当前事实来源

- 当前阶段任务入口：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- Phase 8 统一方案：[typed-petting-porcupine.md](/D:/UnrealProjects/Mvpv4TestCodex/PhaseDoc/typed-petting-porcupine.md)
- Phase 8 交接文档：[Phase8_M3_Handover_to_Execution_Agent.md](/D:/UnrealProjects/Mvpv4TestCodex/PhaseDoc/Phase8_M3_Handover_to_Execution_Agent.md)
- Phase 8 详细设计：[Phase8_DD1_Schema_and_Interface_Spec.md](/D:/UnrealProjects/Mvpv4TestCodex/PhaseDoc/Phase8_DD1_Schema_and_Interface_Spec.md) / [Phase8_DD3_Lowering_Map_and_CPP_Design.md](/D:/UnrealProjects/Mvpv4TestCodex/PhaseDoc/Phase8_DD3_Lowering_Map_and_CPP_Design.md)
- Phase 8 Compiler 产物：`ProjectState/phase8/`
- 上一阶段归档任务：[task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)
- 框架级规范：`Plugins/AgentBridge/Docs/` + `Schemas/` + `Compiler/` + `SkillTemplates/` + `MCP/`

## 当前附加规则

- `Phase 8` 正式开发期，当前处于 M3（垂直切片执行）阶段。
- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 是 Phase 8 唯一任务入口。
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 保持 `230` 条口径，Phase 8 测试编号待 M4 统一补录。
- Phase 6 的 Playable Runtime 验收基线已归档到 `Docs/History/`，Phase 8 使用新的 12 点验收标准。
