# Reviewed Handoff 机制设计

> 文档版本：v0.4.0 | 适用范围：AgentBridge 插件 Reviewed Handoff 机制

---

## 1. 定位

Reviewed Handoff 是 Skill Compiler Plane 向 Execution Orchestrator Plane 的**唯一正式交接物**。

它是一份结构化的 YAML 文档，包含编译前端的全部输出：项目上下文、路由决策、动态 Spec 树、审查摘要和能力缺口。Orchestrator 消费 Reviewed Handoff 生成 Run Plan 并执行，不回读 GDD。

### 1.1 核心原则

- **单一交接点**：Compiler 和 Orchestrator 之间只通过 Reviewed Handoff 通信
- **Compiler 职责到此为止**：Handoff 提交后，后续执行由 Orchestrator 全权负责
- **必须通过 Schema 校验**：`Schemas/reviewed_handoff.schema.json` 是格式权威
- **审批流程**：draft → 审批 → approved，未审批的 Handoff 不进入执行

---

## 2. Schema 概述

Schema 路径：`Schemas/reviewed_handoff.schema.json`

### 2.1 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `handoff_version` | string | Schema 版本（如 "0.1"） |
| `handoff_id` | string | 唯一标识符 |
| `handoff_mode` | enum | "greenfield" / "brownfield" |
| `status` | enum | "draft" / "reviewed" / "approved" / "rejected" |
| `project_context` | object | 项目上下文（项目名、引擎版本、目标关卡） |
| `baseline_context` | object | 基线上下文（Brownfield 专用，Greenfield 为 null） |
| `routing_context` | object | 模式路由结果 |
| `delta_context` | object | 增量上下文（Brownfield 专用，Greenfield 为 null） |
| `dynamic_spec_tree` | object | 动态 Spec 树（核心内容） |
| `review_summary` | object | 审查摘要 |
| `capability_gaps` | array | 能力缺口列表 |
| `governance_context` | object | 治理上下文 |
| `metadata` | object | 元数据（时间戳、来源等） |

### 2.2 dynamic_spec_tree

Handoff 的核心内容。包含从设计输入编译出的结构化 Spec：

- `tree_type`："full"（Greenfield）/ "delta"（Brownfield）
- `specs`：Spec 列表，每个 Spec 包含 spec_id、domain、actors、constraints 等

---

## 3. 双模式差异

| 维度 | Greenfield | Brownfield |
|------|-----------|------------|
| `handoff_mode` | "greenfield" | "brownfield" |
| `baseline_context` | null | 包含当前基线信息 |
| `delta_context` | null | 包含增量意图和范围 |
| `dynamic_spec_tree.tree_type` | "full" | "delta" |
| Spec 操作类型 | 全部为 create | 包含 create / patch / expand |

---

## 4. 生命周期

```
Compiler 输出
    ↓
ProjectState/Handoffs/draft/handoff_xxx.yaml    ← status: "draft"
    ↓
人工审批（当前为手工移动文件）
    ↓
ProjectState/Handoffs/approved/handoff_xxx.yaml  ← status: "approved"
    ↓
Orchestrator 读取 approved Handoff
    ↓
Run Plan Builder → Run Plan → Handoff Runner → Bridge → UE5
```

---

## 5. 文件存放规范

| 阶段 | 路径 | 说明 |
|------|------|------|
| 草稿 | `ProjectState/Handoffs/draft/` | Compiler 输出，待审批 |
| 已审批 | `ProjectState/Handoffs/approved/` | 审批通过，可执行 |

文件命名：`handoff_{handoff_id}_{timestamp}.yaml`

实例在项目层，格式和生成机制在插件层。

---

## 6. 校验方式

```bash
# 校验 Handoff 文件是否符合 Schema
cd Plugins/AgentBridge/Scripts
python validation/test_handoff_schema.py
```

---

## 7. 与 Run Plan 的关系

Reviewed Handoff 是 Run Plan Builder 的输入：

```
Reviewed Handoff（approved）
    ↓
run_plan_builder.py
    ↓
Run Plan（符合 run_plan.schema.json）
    ↓
handoff_runner.py → Bridge → UE5
```

Run Plan 是 Handoff 的执行计划视图，包含有序的 workflow_sequence、validation_checkpoints 和 recovery_policies。

---

## 8. 参考

- Schema：`Schemas/reviewed_handoff.schema.json`
- 示例：`Schemas/examples/reviewed_handoff_greenfield.example.json`
- 构建器：`Scripts/compiler/handoff/handoff_builder.py`
- 序列化：`Scripts/compiler/handoff/handoff_serializer.py`
- 校验：`Scripts/validation/test_handoff_schema.py`
