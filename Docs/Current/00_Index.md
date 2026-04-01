# 当前阶段文档索引

> 阶段名称：Phase 6 — Genre Skill Packs 完整化
> 状态：Active
> 起始日期：2026-04-01
> 文档版本：L1-Phase6-v1

## 本目录文件

| 文件 | 摘要 |
|------|------|
| 01_Project_Baseline.md | 进入 Phase 6 时的项目事实、已闭环能力与当前起点 |
| 02_Current_Phase_Goals.md | Phase 6 目标、成功标准与本期不做 |
| 03_Active_Backlog.md | 当前待办、门禁与延后项 |
| 04_Open_Risks.md | 当前风险、已缓解项与待验证假设 |
| 05_Implementation_Boundary.md | 本阶段允许范围与保护清单 |
| 06_Phase6_Task_List.md | 当前任务入口索引（指向根目录 task.md） |
| 07_Evidence_And_Artifacts.md | Snapshots / Evidence / Reports 的职责边界 |

## 当前事实来源

- 项目级基线：本目录全部文件
- 当前任务：根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- 上一阶段归档：[task3_phase5.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task3_phase5.md)
- 框架级规范：`Plugins/AgentBridge/Docs/` + `Schemas/` + `Specs/`

## 本阶段额外规则

- Phase 5 用例已补录进 `Plugins/AgentBridge/Tests/SystemTestCases.md`
- Phase 6 测试用例先维护在根目录 `task.md`，不提前写入 `SystemTestCases.md`
- `ProjectState/Snapshots/` 只保存 baseline / state snapshot
- `ProjectState/Evidence/Phase6/` 保存当前阶段截图、日志与人工核验说明
- Phase 5 证据已归档到 `Docs/History/reports/AgentBridgeEvidence/phase5_evidence_2026-04-01/`
- UE5 Editor 截图取证的可复用方法见：
  `Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md`

## 禁止默认读取

- `Docs/History/*`：历史归档，不作为默认开发输入
- `Docs/Proposals/` 中未批准文件：候选草案，不作为当前事实
- `Plugins/AgentBridge/Roadmap/Archive/`：历史路线图，不代表当前安排
