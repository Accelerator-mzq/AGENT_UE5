# Governance Loop Minimal Design

> 状态：Phase 7 历史快照，不再代表 Phase 11 当前主链
> 范围：Phase 7 时期的最小治理闭环，不扩展为完整审批平台

## 当前定位

本文保留为 **Phase 7 历史方案快照**，用于解释早期治理闭环如何围绕 `run_plan`、`execution_report`、`snapshot_manifest` 和最小 promotion 审计搭建。

它不再描述 Phase 11 当前的正式事实。当前 Phase 11 请优先参考：

- [compiler_design.md](compiler_design.md)
- [reviewed_handoff_design.md](reviewed_handoff_design.md)
- [run_isolation_compare_promote.md](run_isolation_compare_promote.md)
- [architecture_overview.md](architecture_overview.md)

## 目标

Phase 7 的治理闭环只解决 5 件事：

1. 在 `run_plan` 中显式写出验证插点
2. 在失败路径中给出最小恢复建议
3. 在执行报告中输出结构级回归摘要
4. 在执行结束后冻结最小 snapshot manifest
5. 在执行报告中留下最小 promotion 审计

这条链路的目标不是替代现有 Orchestrator，而是在不重写主链的前提下，为 Greenfield / Brownfield / 第二类型包提供可追溯的治理壳层。

## 数据流（Phase 7 历史口径）

```text
Reviewed Handoff
  -> validation_inserter.py
  -> recovery_planner.py
  -> run_plan_builder.py
  -> handoff_runner.py
  -> execution_report + snapshot_manifest + promotion_status
```

## 最小接口增量（Phase 7 历史口径）

### Run Plan

- `validation_checkpoints[]`
- `recovery_policy_ref`
- `recovery_policies`
- `context.planning_blockers`

### Execution Report

- `regression_summary`
- `snapshot_ref`
- `promotion_status`

### Snapshot Manifest

落盘目录：

- `ProjectState/Snapshots/YYYY-MM-DD/`

最小字段：

- `baseline_ref`
- `digest`
- `source_report`
- `created_at`

## 模块职责

### validation_inserter.py

- 输入：`handoff + workflow_sequence`
- 输出：`validation_checkpoints[]`
- 默认策略：
  - Actor 数量检查
  - Actor 命名检查
  - delta / runtime 相关治理检查

### recovery_planner.py

- 输入：`handoff + workflow_sequence`
- 输出：
  - `recovery_policy_ref`
  - `recovery_policies`
  - `blockers`
- 最小目标：
  - 能区分 `greenfield_bootstrap` / `brownfield_expansion`
  - 能在缺少治理前置项时明确阻断原因

### handoff_runner.py

- 负责把治理字段真正写入执行结果
- 不重写执行主链，只在：
  - 生成执行报告
  - 保存执行报告
  - 回填 snapshot / promotion
  这三个点做增量接入

## Base Domains 的作用（Phase 7 历史口径）

以下描述的是 Phase 7 时期治理闭环如何消费 `qa_validation` 与 `planning_governance`，不是 Phase 11 当前默认主路径。

治理闭环不直接硬编码所有策略，而是优先走两个真实域：

- `qa_validation`
- `planning_governance`

当前约定如下：

- `qa_validation`
  - 生成 `validation_checkpoints`
  - 生成 `regression_summary`
- `planning_governance`
  - 生成 `recovery_policy`
  - 生成 `promotion_status`

其余 8 个基础域在 Phase 7 只提供统一 registry / loader / 可加载骨架，不要求完整治理能力。

## 边界（Phase 7 历史口径）

Phase 7 的治理闭环明确不做：

- 完整审批流引擎
- 像素级截图回归
- 多阶段多审批人状态机
- 热更新式恢复编排
- 自动重跑调度平台

## 验收口径（Phase 7 历史口径）

满足以下条件即可判定 Phase 7 治理闭环最小可用：

1. `run_plan` 能写出 `validation_checkpoints[]`
2. `run_plan` 能写出 `recovery_policy_ref`
3. 缺失治理前置项时，`run_plan.status` 会降为 `failed`
4. 执行报告能写出 `regression_summary`
5. 执行后能写出 `snapshot_manifest`
6. 执行报告能写出最小 `promotion_status`
