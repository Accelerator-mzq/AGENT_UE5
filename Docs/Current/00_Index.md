# 当前阶段文档索引

> 阶段名称：Phase 11 — Skill-First Design Compiler Framework
> 状态：Completed / 已完成
> 启动日期：2026-04-15
> 收尾日期：2026-04-17
> 文档版本：L1-Phase11-archive-v1
> 当前阶段任务入口（归档跳转页）：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
> Phase 11 收尾总览：[18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)
> Phase 11 归档任务：[task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task11_phase11.md)
> Phase 10 归档任务：[task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md)

## 当前口径

Phase 11 已完成收尾。项目当前稳定基线是在 Phase 10 已完成的 MCP 认知桥接层与 Compiler Pipeline 编排之上，建立了 Skill-First Design Compiler Framework、Phase 11 v2 run 治理、Baseline Domain 模板体系，以及 UE5 运行时最小可玩性验证链。

Phase 11 的阶段事实已经归档到 [task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task11_phase11.md)；根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 现在只作为归档跳转页存在。最终收尾结论以 [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)、[phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md) 和 [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md) 为准。

## 本目录文件

| 文件 | 当前用途 |
|------|----------|
| [01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md) | Phase 11 完成后的项目稳定基线。 |
| [02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md) | Phase 11 已完成目标、门禁结果与残留说明。 |
| [03_Active_Backlog.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/03_Active_Backlog.md) | 历史活动 backlog，现仅作追溯参考。 |
| [04_Open_Risks.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/04_Open_Risks.md) | 历史风险记录，现仅作追溯参考。 |
| [05_Implementation_Boundary.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/05_Implementation_Boundary.md) | 当前仍生效的实施边界。 |
| [06_Current_Task_List.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/06_Current_Task_List.md) | 当前任务入口与归档说明；当前为 Phase 11 归档跳转口径。 |
| [07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md) | Reports / Evidence / Snapshots 的落盘规则。 |
| [08_Phase8_Retrospective_And_Phase9_Checklist.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Phase8_Retrospective_And_Phase9_Checklist.md) | Phase 8 复盘与防回归参考。 |
| [10_Phase8_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/10_Phase8_Closeout.md) | Phase 8 收尾结论、证据和归档口径。 |
| [11_Phase9_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/11_Phase9_Closeout.md) | Phase 9 收尾结论、证据与软归档口径。 |
| [12_MCP_Repositioning.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/12_MCP_Repositioning.md) | MCP 重定位背景文档。 |
| [14_MCP_Cognitive_Bridge_Anchor.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md) | MCP 认知桥接层总口径声明；Phase 11 继续遵守其边界约束。 |
| [15_Skill_Spec_Handoff_Chain.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/15_Skill_Spec_Handoff_Chain.md) | Skill / Spec / Handoff 四层主链定义；Phase 11 在其上扩展为 Design Compiler 主链。 |
| [16_MCP_Repositioning_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/16_MCP_Repositioning_Plan.md) | MCP 重定位方案 v3，作为 MCP 边界与执行主干参考。 |
| [17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md) | Phase 10 收尾结论、交付物、端到端证据与遗留说明。 |
| [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md) | Phase 11 收尾结论、证据归档、残留风险与后续建议。 |

## Phase 11 框架级规范（已吸收至插件层）

Phase 11 的 16 份设计文档已完成整理：
- **框架级规范**（8 份）已吸收进 `Plugins/AgentBridge/Docs/`，作为长期框架 canonical 文档
- **原始设计包**（16 份）已整体归档到 `Docs/History/Phase11_Design_Pack/`

插件层新增的框架文档：

| 文档 | 摘要 |
|------|------|
| `Plugins/AgentBridge/Docs/root_skill_contract_standard.md` | Root Skill Contract 标准、10 个问题、产物结构 |
| `Plugins/AgentBridge/Docs/universal_baseline_standard.md` | Universal Game Baseline Standard 与最低实现标准 |
| `Plugins/AgentBridge/Docs/baseline_realization_policy.md` | Baseline 三类域与 realization 规则 |
| `Plugins/AgentBridge/Docs/clarification_gate_rules.md` | Clarification Gate 4 档决策、provisional 传播、fast_mode 保护 |
| `Plugins/AgentBridge/Docs/constraint_variant_policy.md` | Constraint / Variant 标注策略、下游保持性与 bounds 传播 |
| `Plugins/AgentBridge/Docs/design_space_discovery.md` | Design Space Discovery、Realization Candidates、Convergence |
| `Plugins/AgentBridge/Docs/skill_graph_and_domain_skill.md` | Skill Graph、Domain Skill 四重职责、SkillTemplates / Skills 分层 |
| `Plugins/AgentBridge/Docs/run_isolation_compare_promote.md` | Run 隔离、compare、promote、fast_mode run 治理 |
| `Plugins/AgentBridge/Docs/agent_interaction_protocol.md` | Stage 4 Agent 交互协议、三路生成策略 |

历史设计包（含索引、架构、命名规范、Schema 变更表、实施计划、交接文档）：[Docs/History/Phase11_Design_Pack/](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Phase11_Design_Pack/)

## 当前事实来源

- 当前阶段任务入口（归档跳转页）：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- Phase 11 归档任务：[task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task11_phase11.md)
- Phase 11 收尾总览：[18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)
- Phase 11 功能覆盖报告：[phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md)
- Phase 11 最终验收报告：[task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
- Phase 10 收尾总览：[17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md)
- Phase 10 归档任务：[task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md)

## 当前附加规则

- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 当前是归档跳转页，不再承载 Phase 11 全量正文。
- Phase 11 历史任务正文固定为 [task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task11_phase11.md)。
- Phase 11 的运行时最小可玩性已通过 Editor game 与 staged standalone 双路径验证。
- MCP 当前可见注册数为 `53`，其中 `49` 个为正式主工具，`4` 个为兼容 alias；Phase 11 旧规划中的 `50` 属于实施前 planning 口径，收尾以当前实现事实为准。
- 下一阶段启动前，应优先阅读 [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md) 与 [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)。
