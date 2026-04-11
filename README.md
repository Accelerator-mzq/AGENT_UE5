# Mvpv4TestCodex

> 目标引擎版本：UE5.5.4
> 当前状态：Phase 10 已完成并归档
> 当前正式口径：[17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md)

## 项目简介

`Mvpv4TestCodex` 是基于 `AgentBridge` 插件的 UE5 工程，用来验证从设计输入到 Compiler、Handoff、关卡落地、运行时验证、证据裁决与文档治理的完整闭环。

Phase 10 已完成 MCP 认知桥接层与 Compiler Pipeline 编排，并用 MonopolyGame 真实输入跑通：

`GDD -> MCP 前端 Stage 1-2 -> Compiler Core Stage 3-5 -> Build IR -> UE5 关卡 -> 运行时证据 -> MCP 后端裁决`

## 当前入口

- 当前阶段索引：[00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- Phase 10 收尾总览：[17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md)
- Phase 10 归档任务单：[task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md)
- 根目录阶段入口占位页：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- 插件入口：[Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)
- 系统测试总表：[SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)

## Phase 10 完成结果

- MCP 工具总数为 `42`：Bridge `28` + Compiler 前端 `6` + Evidence 后端 `8`
- `ProjectState/phase10/` 已落地 `12` 个核心 JSON 产物
- `L_MonopolyBoard_Pipeline` 已作为 Pipeline 独立关卡完成创建与验证
- 标准化运行时证据目录已生成，最终裁决 `run_id=2026-04-11_fa5c8bec`，`judgment=pass`
- `SystemTestCases.md` 与 `run_system_tests.py` 当前统一登记为 `248` 条系统测试

关键证据：

- [task09_final_acceptance_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task09_final_acceptance_validation.md)
- [task08_runtime_evidence_judgment_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task08_runtime_evidence_judgment_validation.md)
- [task07_build_ir_level_realization_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task07_build_ir_level_realization_validation.md)

## 历史阶段

- Phase 6：[task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)
- Phase 7 准备期：[task5_phase7_preparation.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task5_phase7_preparation.md)
- Phase 7：[task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)
- Phase 8：[task8_phase8.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task8_phase8.md)
- Phase 9：[task9_phase9.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task9_phase9.md)
- Phase 10：[task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md)

## 常用命令

```powershell
# Schema example 严格校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 运行当前登记的关键 Phase 10 对齐 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=7,9,10

# 单独验证 MCP 集成层
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=10

# 启动 MCP Server
python Plugins/AgentBridge/MCP/server.py
```

## 当前约定

- `Docs/Current/*` 是当前项目口径的最高优先级。
- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 现在是 Phase 10 归档跳转页，不再承载完整任务定义。
- Phase 10 的正式完成口径以 [17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md) 和 [task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md) 为准。
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 当前已对齐为 `248` 条用例。
