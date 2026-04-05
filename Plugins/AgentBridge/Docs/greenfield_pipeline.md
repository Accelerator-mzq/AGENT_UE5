# Greenfield E2E 管线

> 文档版本：v0.8.0（Phase 8 口径）

## 1. 概述

Greenfield 管线用于从零构建新样板。

Phase 8 引入 **Skill-First 主链**作为新的 Greenfield 链路，旧链路保留用于 boardgame/JRPG 回归。

历史：
- Phase 4–7：旧链路（intake → routing → generation → review → handoff → run_plan → execution）
- Phase 8：新链路（Intake → Planner → SkillRuntime → CrossReview → Lowering → Execution）

## 2. Phase 8 新链路（Skill-First）

```text
ProjectInputs/GDD/GDD_MonopolyGame.md
→ Compiler/intake/design_intake.py          → ProjectState/phase8/gdd_projection.json
→ Compiler/planner/planner.py               → ProjectState/phase8/planner_output.json
→ Compiler/skill_runtime/skill_runtime.py   → ProjectState/phase8/skill_fragments/*.json
→ Compiler/cross_review/cross_review.py     → ProjectState/phase8/cross_review_report.json
→ Compiler/lowering/lowering.py             → ProjectState/phase8/build_ir.json
→ Handoff Assembly                           → ProjectState/phase8/reviewed_handoff_v2.json
→ Execution Agent（按 Build IR 的 14 步执行）
→ Source/Mvpv4TestCodex/ C++ 代码
```

## 3. 旧链路（v0.5.0–v0.7.0，仍保留）

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

## 3. 运行方式

```bash
# simulated
python Scripts/run_greenfield_demo.py

# RC API
python Scripts/run_greenfield_demo.py bridge_rc_api

# Phase 6 / Phase 7 相关独立入口
python Scripts/run_boardgame_playable_demo.py
python Scripts/run_jrpg_turn_based_demo.py
```

## 4. 当前限制

- 当前支持 `boardgame` 与 `jrpg` 两类 GDD
- Handoff 审批仍为文件流转
- 当前主开发焦点已转入完整 Spec Tree + playable runtime；Greenfield 主要承担回归基线职责
- 本文档聚焦 `preview_static` 链路，`runtime_playable` 另见 `boardgame_playable_pipeline.md`
