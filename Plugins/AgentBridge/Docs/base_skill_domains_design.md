# Base Skill Domains Design

> 状态：Phase 7 历史快照，不再代表 Phase 11 当前主链
> 范围：Phase 7 时期的基础域 registry / loader / 两个真实域 + 八个骨架域

## 当前定位

本文保留为 **Phase 7 历史方案快照**，用于解释早期 `Skills/base_domains/` 的 registry / loader / 治理域设计来源。

它不再描述 Phase 11 当前的正式事实。当前 Phase 11 请优先参考：

- [skill_graph_and_domain_skill.md](skill_graph_and_domain_skill.md)
- [universal_baseline_standard.md](universal_baseline_standard.md)
- [baseline_realization_policy.md](baseline_realization_policy.md)
- [reviewed_handoff_design.md](reviewed_handoff_design.md)
- [compiler_design.md](compiler_design.md)

## 目标

`Skills/base_domains/` 在 Phase 7 不再是占位目录，而是统一承载跨类型包的基础能力域。

本期目标：

1. 提供稳定的 registry
2. 提供统一 module loader
3. 真实实现两个治理相关基础域
4. 为未来多类型扩展保留统一域 ID

## 当前 10 个基础域

按固定顺序注册：

1. `design_project_state_intake`
2. `baseline_understanding`
3. `delta_scope_analysis`
4. `product_scope`
5. `runtime_gameplay`
6. `world_level`
7. `presentation_asset`
8. `config_platform`
9. `qa_validation`
10. `planning_governance`

## 当前真实实现

### qa_validation

当前真实提供：

- `build_domain_descriptor()`
- `build_validation_checkpoints(run_plan_context)`
- `build_regression_summary(handoff, execution_result)`

### planning_governance

当前真实提供：

- `build_domain_descriptor()`
- `build_recovery_policy(run_plan_context)`
- `build_promotion_status(handoff, execution_result, snapshot_ref)`

## 当前骨架域

以下 8 个域在 Phase 7 只要求：

- 可注册
- 可加载
- 具备统一 descriptor

不要求在本期完成深度业务实现：

- `design_project_state_intake`
- `baseline_understanding`
- `delta_scope_analysis`
- `product_scope`
- `runtime_gameplay`
- `world_level`
- `presentation_asset`
- `config_platform`

## registry 与 loader 约定

### registry.py

负责：

- 定义固定域顺序
- 扫描每个域模块文件是否存在
- 输出 `domain_map`

### loader.py

负责：

- 按域 ID 列表加载模块
- 支持“从 pack manifest 的 `dependencies.base_domains` 解析必需域”
- 统一输出：
  - `registry`
  - `loaded_domains`
  - `domain_map`

## 与 Genre Pack 的关系

Phase 7 以后，类型包不再只声明自己内部模块，还要显式声明依赖的基础域：

```yaml
dependencies:
  base_domains:
    - qa_validation
    - planning_governance
```

当前约束：

- `boardgame` 已补齐治理域依赖
- `jrpg` 作为第二个类型包，必须显式声明治理域依赖

## 与 Handoff / Run Plan 的关系（Phase 7 历史口径）

以下关系描述的是 Phase 7 时期的 handoff / run_plan 治理上下文，不是 Phase 11 当前默认主路径。
Phase 11 当前正式交接物请以 `reviewed_handoff_v3` 与 `run_id` 工作区模型为准。

基础域会通过以下路径写回治理上下文：

- `handoff.governance_context.base_domain_refs`
- `handoff.metadata.base_domain_refs`
- `run_plan.metadata.base_domain_refs`

这意味着治理链路不再依赖“脚本内部猜测当前能力”，而是依赖 pack 明确声明的基础域激活结果。

## 边界

Phase 7 不做：

- 把 10 个域全部做成复杂插件体系
- 动态热插拔基础域
- 为每个基础域单独建立独立 schema

## 验收口径

满足以下条件即可判定 Phase 7 的 Base Skill Domains 最小真实化完成：

1. registry 能发现 10 个固定域
2. `qa_validation` 与 `planning_governance` 能真实加载
3. 类型包能通过 `dependencies.base_domains` 激活基础域
4. Handoff / Run Plan / Execution Report 能消费这些域提供的治理能力
