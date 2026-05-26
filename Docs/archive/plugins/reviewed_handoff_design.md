# Reviewed Handoff 机制设计

> 文档版本：v1.0.0 | 适用范围：AgentBridge 插件 Reviewed Handoff 机制

---

## 1. 定位

Reviewed Handoff 是 Skill Compiler Plane 向 Execution Orchestrator Plane 的**唯一正式交接物**。

在 Phase 11 当前口径下，正式交接版本为 **Reviewed Handoff v3**。它承担三层职责：

1. 作为 Compiler 的最终边界，汇总 Stage 1-7 的结果
2. 作为 Execution 的正式输入，提供可执行的 Build IR 与摘要化设计信息
3. 作为 run 级审计产物，保留 run_id、provisional、design decision 摘要与审批结论

### 1.1 版本演进

| 版本 | Schema | 核心结构 | 当前状态 |
|------|--------|---------|---------|
| **v1**（v0.1-v0.7） | `reviewed_handoff.schema.json` | 以 `dynamic_spec_tree.scene_spec.actors` 为中心 | 历史链路，兼容保留 |
| **v2**（v0.8-v0.10） | `reviewed_handoff_v2.schema.json` | 以 `reviewed_dynamic_spec_tree` + `build_ir` 为中心 | 历史链路，兼容保留 |
| **v3**（Phase 11） | `reviewed_handoff_v3.schema.json` | 以 `run_id + design_directions_summary + build_ir + approval` 为中心 | **当前正式版本** |

v1 / v2 继续保留用于历史回归、旧样例理解与兼容验证；当前主开发与主验收均以 v3 为准。

### 1.2 核心原则

- **单一交接点**：Compiler 和 Execution 之间只通过 Reviewed Handoff 通信
- **Compiler 边界明确**：Handoff 生成后，后续执行由 Orchestrator / Execution Agent 负责
- **必须通过 Schema 校验**：对应版本 schema 是格式权威
- **run 级可追溯**：当前正式版本必须携带 `run_id`
- **摘要优先**：v3 面向执行层暴露摘要化设计信息，而不是把全部中间态原样塞进 Handoff

---

## 2. 当前正式版本：Reviewed Handoff v3

### 2.1 Schema 路径

- 正式 schema：`Plugins/AgentBridge/Schemas/reviewed_handoff_v3.schema.json`
- 示例文件：`Plugins/AgentBridge/Schemas/examples/phase11_reviewed_handoff_v3.example.json`

### 2.2 顶层结构

v3 的顶层必填字段为：

- `handoff_meta`
- `run_id`
- `project_context`
- `selected_skill_instances`
- `design_directions_summary`
- `constraint_variant_summary`
- `baseline_coverage_summary`
- `provisional_items`
- `design_decision_log_summary`
- `cross_review_summary`
- `lowering_summary`
- `build_ir`
- `approval`
- `metadata`

其中最关键的 Phase 11 新增点有：

- `run_id`
  - 将 handoff 与 `ProjectState/runs/{run_id}/` 工作区绑定
- `design_directions_summary`
  - 汇总每个 Skill Instance 在 Discovery / Candidates / Convergence 后的最终方向选择
- `baseline_coverage_summary`
  - 汇总 Baseline 能力覆盖情况
- `provisional_items`
  - 把 Clarification Gate 的临时默认项正式带入下游交接
- `design_decision_log_summary`
  - 汇总 Fragment 中的重要设计决策，而不是只保留最终静态结果
- `approval`
  - 明确 `approved / approved_with_warnings / blocked`

### 2.3 v3 与 v2 的关键差异

相较 v2，v3 的变化重点不是“字段换名字”，而是交接对象发生了变化：

- 从“以 reviewed spec tree 为中心”升级为“以 run 级编译结果摘要为中心”
- 从“Compiler 内部视角”升级为“Execution 可直接消费的边界视角”
- 从“只看 Build IR 是否存在”升级为“同时携带 design directions / provisional / approval / lowering summary”
- 从“阶段性产物集合”升级为“最终运行工作区中的正式交接物”

---

## 3. 生命周期

当前 Phase 11 的默认生命周期如下：

```text
GDD
→ Session v2 / run_id 创建
→ Stage 1 Root Skill Contract
→ Stage 2 Clarification Gate
→ Stage 3 Skill Graph Planning
→ Stage 4 Domain Skill Runtime
→ Stage 5 Cross Review v2
→ Stage 6 Lowering / Build IR v2
→ Stage 7 Handoff Assembly
→ ProjectState/runs/{run_id}/reviewed_handoff_v3.json
→ Execution Orchestrator 消费
```

与旧链路不同，当前默认流程不再把 `draft/approved` 文件夹流转作为主路径；审查结果已经内嵌到：

- `cross_review_summary`
- `approval`

如果某次 run 被治理流程 promote，对应的 handoff 会随 run / batch 一起进入归档体系，但 run 工作区本身仍保留。

---

## 4. 文件存放

### 4.1 当前正式位置

当前正式 handoff 落位于：

`ProjectState/runs/{run_id}/reviewed_handoff_v3.json`

它与以下同 run 产物并列存在：

- `root_skill_contract.json`
- `clarification_gate_report.json`
- `skill_graph.json`
- `design_space_report.json`
- `realization_candidates.json`
- `converged_realization_pack.json`
- `skill_fragments/*.json`
- `cross_review_report.json`
- `build_ir.json`
- `naming_resolution_log.json`

### 4.2 历史位置

以下位置属于历史链路保留：

- `ProjectState/Handoffs/draft/`
- `ProjectState/Handoffs/approved/`

它们仍可用于读取旧样例或兼容回归，但不再代表 Phase 11 的默认落位。

---

## 5. 校验方式

当前 v3 的校验方式包括：

```bash
# 校验 schema 示例
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 校验历史 handoff schema 测试脚本
python Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py
```

其中：

- `validate_examples.py --strict` 更适合作为当前 Phase 11 文档与 schema 的主验证入口
- `test_handoff_schema.py` 仍可保留用于旧 handoff 结构兼容检查

---

## 6. 与 Run Plan 的关系

Run Plan 在当前项目中属于**旧链路/兼容概念**，不再是 Phase 11 默认主路径的中心对象。

当前关系应理解为：

- `reviewed_handoff_v3.json` 是 Compiler 到 Execution 的正式边界
- Execution 侧可以基于它生成或推导自己的执行计划
- 但文档不再把 `run_plan_builder.py` 视为当前唯一消费端

换句话说，**Reviewed Handoff v3 是当前正式输入；Run Plan 是可能的下游视图，而不是当前设计中心。**

---

## 7. 历史兼容说明

以下内容保留为历史兼容语义：

- `reviewed_handoff.schema.json`
- `reviewed_handoff_v2.schema.json`
- `legacy_compatibility.scene_spec`
- `ProjectState/Handoffs/draft/approved/`
- `run_plan_builder.py -> handoff_runner.py` 旧式执行链

这些对象仍可在历史 demo、回归测试、旧文档追溯时出现，但不应再写成当前事实描述。

---

## 8. 参考

- 当前架构总览：`architecture_overview.md`
- 当前 compiler 主链：`compiler_design.md`
- 当前 schema：`Plugins/AgentBridge/Schemas/reviewed_handoff_v3.schema.json`
- 当前 schema 示例：`Plugins/AgentBridge/Schemas/examples/phase11_reviewed_handoff_v3.example.json`
- 当前 handoff 组装实现：`Plugins/AgentBridge/Compiler/stages/handoff_v3.py`
- 当前主编排实现：`Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py`
