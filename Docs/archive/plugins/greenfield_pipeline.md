# Greenfield E2E 管线（Phase 8 历史快照）

> 文档版本：v0.8.0（历史口径）
> 说明：本文件保留为 Phase 8 Greenfield 链路快照，不再代表 Phase 11 当前主链。

## 1. 定位

本文件记录的是 **Phase 8 时期** 的 Greenfield E2E 管线，用于：

- 回顾 Skill-First 主链首次落地时的结构
- 对照 `reviewed_handoff_v2` 时代的产物组织方式
- 为历史回归脚本和旧测试样例提供背景

当前 Phase 11 主链请改看：

- `architecture_overview.md`
- `compiler_design.md`
- `root_skill_contract_standard.md`
- `skill_graph_and_domain_skill.md`

## 2. 历史背景

Phase 8 首次引入 Skill-First 主链，替代更早的：

`intake -> routing -> generation -> review -> handoff -> run_plan -> execution`

当时的新链路重点是：

- 将 GDD 投影为结构化中间产物
- 通过 Skill Runtime 生成 Fragment
- 组装 `reviewed_handoff_v2.json`
- 用 Monopoly 垂直切片验证端到端闭环

这条链路对理解 Phase 11 的来源仍有价值，但已经不是当前推荐入口。

## 3. Phase 8 历史链路

```text
ProjectInputs/GDD/GDD_MonopolyGame.md
→ Compiler/intake/design_intake.py          → ProjectState/phase8/gdd_projection.json
→ Compiler/planner/planner.py               → ProjectState/phase8/planner_output.json
→ Compiler/skill_runtime/skill_runtime.py   → ProjectState/phase8/skill_fragments/*.json
→ Compiler/cross_review/cross_review.py     → ProjectState/phase8/cross_review_report.json
→ Compiler/lowering/lowering.py             → ProjectState/phase8/build_ir.json
→ Handoff Assembly                          → ProjectState/phase8/reviewed_handoff_v2.json
→ Execution Agent（按 Build IR 的 14 步执行）
→ Source/Mvpv4TestCodex/ C++ 代码
```

需要特别注意：

- 这里的 `build_ir.json` 指的是 **Build IR v1**
- 这里的 `reviewed_handoff_v2.json` 指的是 **Reviewed Handoff v2**
- 这里的产物目录 `ProjectState/phase8/` 不等同于 Phase 11 的 `ProjectState/runs/{run_id}/`

## 4. 更早旧链路（v0.5.0-v0.7.0）

```text
ProjectInputs/GDD/
→ design_input_intake.py
→ project_state_intake.py
→ mode_router.py（→ greenfield_bootstrap）
→ handoff_builder.py
→ ProjectState/Handoffs/draft/
→ approved/
→ run_plan_builder.py
→ handoff_runner.py
→ Bridge
→ UE5
→ ProjectState/Reports/
```

这条链路只保留为更早历史回归说明。

## 5. 历史运行方式

以下入口仍可用于历史回归或旧样例复现，但**不是当前主开发入口**：

```bash
# simulated
python Scripts/run_greenfield_demo.py

# RC API
python Scripts/run_greenfield_demo.py bridge_rc_api

# Phase 6 / Phase 7 相关独立入口
python Scripts/run_boardgame_playable_demo.py
python Scripts/run_jrpg_turn_based_demo.py
```

## 6. 历史限制

在 Phase 8 / 旧链路语境下，这份管线有以下限制：

- 主要服务于 `boardgame` 与 `jrpg` 历史 demo
- Handoff 仍围绕旧审批/旧执行模型组织
- 产物模型仍以 `reviewed_handoff_v2` 和旧 `build_ir` 为中心
- 不具备 Phase 11 的 `run_id` 隔离、compare/promote、Stage 4 三路生成、Reviewed Handoff v3 等机制

## 7. 当前对应关系

如果你需要把本页中的概念映射到当前 Phase 11，可以按下面理解：

- `design_intake + planner` → Root Skill Contract / Clarification Gate / Skill Graph Planning
- `skill_runtime` → Domain Skill Runtime
- `cross_review` → Cross Review v2
- `lowering` → Lowering / Build IR v2
- `reviewed_handoff_v2` → Reviewed Handoff v3
- `ProjectState/phase8/` → `ProjectState/runs/{run_id}/`

也就是说，这份文档现在最合适的角色是**历史演进参考页**，而不是“当前怎么做”的说明页。
