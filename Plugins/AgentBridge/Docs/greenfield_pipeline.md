# Greenfield E2E 管线

> 文档版本：v0.4.0（Phase 5 口径）

## 1. 概述

Greenfield 管线用于从零构建新样板。到当前阶段为止：

- StaticBase 已落地
- 自动 Dynamic Spec 生成已落地
- Cross-Spec Review 已落地
- `Scripts/run_greenfield_demo.py` 支持 `simulated / bridge_python / bridge_rc_api`

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
```

## 4. 当前限制

- 仅支持 boardgame 类型 GDD
- Handoff 审批仍为文件流转
- 当前主开发焦点已转入 Brownfield；Greenfield 主要承担回归基线职责
