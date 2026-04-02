# 项目基线

> 文档版本：L1-ArchiveBridge-v1

## 1. 当前事实

- `Phase 6` 已完成并归档，历史任务见 [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)。
- `Phase 7` 已完成并归档，历史任务见 [task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)。
- `Phase 7` 历史证据副本已归档到 [phase7_evidence_2026-04-02](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/reports/AgentBridgeEvidence/phase7_evidence_2026-04-02)。
- 插件层系统总表与系统测试入口当前统一为 `230` 条口径：
  - [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)
  - [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py)

## 2. 已确认的项目真相

- `preview_static` 与 `runtime_playable` 仍是当前稳定基线，后续阶段应以它们作为回归基础。
- `JRPG Turn-Based` 已作为第二个 genre pack 落地，并在 Phase 7 中完成 simulated、治理闭环与真机 smoke 验证。
- Snapshot、Promotion、治理审计和 JRPG pack 一致性都已有可审计证据，不再属于未落地能力。

## 3. 归档后的当前状态

- 当前处于“下一阶段待规划”过渡态，而不是新的活跃开发阶段。
- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 只保留当前事实、归档指针和下一阶段规划前的固定规则。
- 新阶段开始前，默认不再修改阶段编号体系；如需新增用例，必须同时规划总表和系统测试入口的同步策略。
