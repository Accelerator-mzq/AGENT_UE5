# 当前阶段目标

> 状态：Phase 11 Active / 正式开发期
> 阶段名称：Skill-First Design Compiler Framework
> 启动日期：2026-04-15
> 当前任务入口：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)

## 1. 阶段定位

Phase 11 的目标是把 Phase 10 已完成的 `GDD -> MCP 前端 -> Compiler Core -> Build IR -> UE5 关卡 -> 证据裁决` 链路，升级为 **Skill-First Design Compiler Framework**。

本阶段不只是把 GDD 翻译成执行产物，而是让 Agent 在明确 Constraint 与 Variant 边界后，通过 Domain Skill 发现设计空间、生成候选、收敛 realization，并将决策记录进可追溯产物。

Phase 11 的正式主链为：

```text
GDD
  -> Root Skill Contract + Universal Baseline Merge
  -> Clarification Gate
  -> Skill Graph Planning
  -> Domain Skill Runtime
  -> Design Space Discovery / Realization Candidates / Convergence
  -> Dynamic Spec Fragments
  -> Cross-Domain Convergence Review
  -> Build IR v2 + naming_resolution_log
  -> Reviewed Handoff v3
  -> Execution
```

## 2. 当前阶段目标

1. 将根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 切换为 Phase 11 唯一开发驱动入口。
2. 建立 `session_version: "2.0"`、`run_id`、`fast_mode` 与 v1/v2 Pipeline 路由。
3. 新增 Phase 11 第一批与第二批 Schema，保留 Phase 10 旧 Schema 兼容。
4. 完成 MCP 前端工具重命名、旧名 alias、Clarification prepare/save。
5. 实现 Root Skill Contract、Clarification Gate、Skill Graph Planning。
6. 实现 Domain Skill Runtime、Design Space Discovery、Realization Candidate Generation、Convergence 与 Skill Fragment v2。
7. 实现 Cross Review v2、Build IR v2、naming_resolution_log、Reviewed Handoff v3。
8. 使用 [GDD_MonopolyGame.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/GDD_MonopolyGame.md) 完成 v2 端到端 run，并验证 Monopoly 最小可玩闭环与 Universal Baseline 覆盖。
9. 实现 Run Compare / Promote、完整 fast_mode 策略、Baseline Domain Skill Template 全套。
10. 生成 Phase 11 文档包功能覆盖报告、最终验收报告，并在 TASK 15 后切换到 Phase 11 Completed 口径。

## 3. 关键验收门禁

- `Docs/Phase11/00-13` 中每份文档的新功能都必须在 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 中有 TASK 落点。
- TASK 11 必须生成完整 `ProjectState/runs/{run_id}/` v2 产物。
- TASK 11 必须验证 Monopoly 最小可玩闭环，而不只是验证 JSON 非空。
- Universal Game Baseline Standard 必须覆盖 Start Screen、Main Menu、Settings、Pause、Results、HUD，并验证 Settings 六项底线。
- Cross Review v2 必须检查 Constraint 保持性、Blueprint 薄层原则、Universal Baseline 覆盖、跨域命名与 realization 冲突。
- Build IR v2 每个 action 必须包含 `naming_resolution_log`。
- fast_mode run 必须不可 promote，且不得自动默认 high / critical Clarification 项。
- Defer 治理项 TASK 12-14 不阻塞 TASK 11 的端到端验收，但阻塞 Phase 11 最终完成声明。
- TASK 15 之前不得宣称 Phase 11 完成。

## 4. 当前约束

- [14_MCP_Cognitive_Bridge_Anchor.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md) 仍作为 MCP 边界的高优先级治理口径。
- [15_Skill_Spec_Handoff_Chain.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/15_Skill_Spec_Handoff_Chain.md) 仍作为 Skill / Spec / Handoff 主链关系的基础说明。
- [16_MCP_Repositioning_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/16_MCP_Repositioning_Plan.md) 仍作为 MCP 前端、Compiler Core、Execution、MCP 后端边界参考。
- Phase 10 的完成事实保留在 [17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md)，Phase 11 不得破坏 Phase 10 已验证能力。
- Phase 10 旧 Schema 不删除；v1.0 session 与 v2.0 session 只做路由选择，不做跨版本产物格式转换。
- 所有成功声明必须附证据文件链接。

## 5. 当前任务顺序

Phase 11 当前按 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 执行：

1. TASK 01：文档切换与任务入口重建。
2. TASK 02-03：Session v2 与 Pipeline v2 路由。
3. TASK 04-05：Schema 第一批与 MCP 前端工具升级。
4. TASK 06-08：Root Skill / Clarification / Skill Graph 真实生成。
5. TASK 09-10：Domain Skill Runtime、Design Space、Cross Review、Build IR、Handoff v3。
6. TASK 11：Monopoly GDD v2 端到端 run、产物与最小可玩闭环验收。
7. TASK 12-14：Run 治理、fast_mode、Baseline Template 全套。
8. TASK 15：最终验收与文档收尾。
