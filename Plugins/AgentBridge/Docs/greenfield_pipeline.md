# Greenfield E2E 管线

> 文档版本：v0.5.0（Phase 6 口径）

## 1. 概述

Greenfield 管线用于从零构建新样板。到当前阶段为止：

- StaticBase 已落地
- 自动 Dynamic Spec 生成已落地
- Cross-Spec Review 已落地
- `Scripts/run_greenfield_demo.py` 支持 `simulated / bridge_python / bridge_rc_api`
- Phase 6 新增 `projection_profile`，默认仍为 `preview_static`
- Phase 6 的 playable runtime 主验收由 `Scripts/run_boardgame_playable_demo.py` 承担，不替换本文件描述的 Greenfield 回归链路

## 2. 当前链路

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

# Phase 6 playable runtime（独立入口）
python Scripts/run_boardgame_playable_demo.py
```

## 4. 当前限制

- 仅支持 boardgame 类型 GDD
- Handoff 审批仍为文件流转
- 当前主开发焦点已转入完整 Spec Tree + playable runtime；Greenfield 主要承担回归基线职责
- 本文档聚焦 `preview_static` 链路，`runtime_playable` 另见 `boardgame_playable_pipeline.md`
