# 当前阶段文档索引

> 阶段名称：Phase 9 - MCP Server 正式化与文档切换
> 状态：Completed
> 启动日期：2026-04-06
> 文档版本：L1-Phase9-v2

## 本目录文件

| 文件 | 摘要 |
|------|------|
| 01_Project_Baseline.md | 当前项目基线，含 Phase 8 已归档事实与 Phase 9 当前实现口径 |
| 02_Current_Phase_Goals.md | Phase 9 当前目标、成功标准与执行状态 |
| 03_Active_Backlog.md | Phase 9 当前进行中事项与待补验证项 |
| 04_Open_Risks.md | Phase 9 当前风险与处理方向 |
| 05_Implementation_Boundary.md | Phase 9 实施边界 |
| 06_Current_Task_List.md | 当前任务入口说明 |
| 07_Evidence_And_Artifacts.md | Reports / Evidence / Snapshots 的落盘规则 |
| 08_Phase8_Retrospective_And_Phase9_Checklist.md | Phase 8 复盘与 Phase 9 防回归清单 |
| 10_Phase8_Closeout.md | Phase 8 收尾结论、证据和归档口径 |
| 11_Phase9_Closeout.md | Phase 9 收尾结论、证据与软归档口径 |

## 当前事实来源

- 当前阶段任务：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- MCP 方案归档：[Phase9_MCP_Implementation_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md)
- Phase 8 收尾总览：[10_Phase8_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/10_Phase8_Closeout.md)
- Phase 9 收尾总览：[11_Phase9_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/11_Phase9_Closeout.md)
- Phase 8 历史任务：[task8_phase8.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task8_phase8.md)
- Phase 9 历史任务：[task9_phase9.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task9_phase9.md)
- 插件入口：[Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)
- MCP 子目录说明：[Plugins/AgentBridge/MCP/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/README.md)
- Phase 9 验证证据：[phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)
- Phase 9 归档检查表：[phase9_archive_preflight_checklist_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_archive_preflight_checklist_2026-04-06.md)

## 当前附加规则

- Phase 9 启动后，根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 恢复为正式任务入口。
- Phase 8 late validation 期间未切换 MCP，Phase 9 负责完成切换与补验证。
- Phase 9 验证顺序固定为：保住 Phase 8 基线回归 → MCP 协议级验证 → Claude `/mcp` 集成 → 有 Editor 的真实调用冒烟。
- [08_Phase8_Retrospective_And_Phase9_Checklist.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Phase8_Retrospective_And_Phase9_Checklist.md) 仍是 Phase 9 防回归约束的权威来源之一。
