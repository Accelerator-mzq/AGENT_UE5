# Reviewed Handoff 机制设计

> 文档版本：v0.8.0 | 适用范围：AgentBridge 插件 Reviewed Handoff 机制

---

## 1. 定位

Reviewed Handoff 是 Skill Compiler Plane 向 Execution Orchestrator Plane 的**唯一正式交接物**。

### 1.1 版本演进

| 版本 | Schema | 核心结构 | 适用范围 |
|------|--------|---------|---------|
| **v1**（v0.1–v0.7） | `reviewed_handoff.schema.json` | 以 `dynamic_spec_tree.scene_spec.actors` 为中心 | boardgame/JRPG 旧链路 |
| **v2**（v0.8+） | `reviewed_handoff_v2.schema.json` | 以 `reviewed_dynamic_spec_tree`（按 family 组织）为中心 + Build IR | Phase 8 Skill-First 新链路 |

v2 通过 `legacy_compatibility.scene_spec` 可选字段提供 v1 回退兼容。

### 1.2 核心原则（v1/v2 共享）

- **单一交接点**：Compiler 和 Execution 之间只通过 Reviewed Handoff 通信
- **Compiler 职责到此为止**：Handoff 提交后，后续执行由 Orchestrator / Execution Agent 全权负责
- **必须通过 Schema 校验**：对应版本的 Schema 是格式权威
- **审批流程**：v1 draft → approved；v2 Compiler auto-approve（审查嵌入 Cross-Review 阶段）

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
