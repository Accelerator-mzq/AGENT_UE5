# Run Isolation, Compare & Promote

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/09_Run_Isolation_Compare_Promote.md

## 1. 定义

Run Isolation 确保每轮管线执行的产物独立存储，支持跨 run 比较、选择性吸收和可追溯性。

核心目标：
- 每次管线执行不覆盖前次结果
- 可以比较两次 run 的差异
- 可以将某次 run 正式吸收（promote）为项目基线
- fast_mode run 与正式 run 隔离

---

## 2. 三层结构

### 2.1 Base Project（项目基础层）
项目根目录下的稳定内容（Source/、Content/、Plugins/、ProjectInputs/、Config/），只在 promote 时被更新。

### 2.2 Run Workspace（运行工作区）
每次管线执行的独立产物空间：`ProjectState/runs/{run_id}/`

`run_id` 格式：`run-{yyyyMMdd}-{HHmmss}-{short_hash}`

### 2.3 Artifact Layer（产物归档层）
经过 promote 的 run 归档为 batch：`ProjectState/batches/{batch_id}/`

`batch_id` 格式：`batch-{yyyyMMdd}-{sequence}`

---

## 3. Run Metadata

每个 run 必须记录元数据（run_id、session_id、session_version、fast_mode、status、pipeline_stages_completed、gdd_source、gdd_hash、provisional_count、constraint_violations、promotable）。

### 3.1 promotable 判定

以下条件使 run 不可 promote（`promotable: false`）：

| 条件 | 原因 |
|------|------|
| `fast_mode: true` | fast_mode 跳过 Design Space Discovery，产物不完整 |
| `status != "completed"` | 未完成的 run 不可 promote |
| `constraint_violations > 0` | 存在约束违反 |
| `pipeline_stages_completed` 不完整 | 管线未跑完全部阶段 |

---

## 4. Compare（跨 Run 比较）

比较维度：Constraint 保持性、Realization 差异、Fragment 差异、Design Decision 差异、Build IR 差异、Naming 差异、Provisional 变化。

---

## 5. Promote（正式吸收）

### 5.1 流程

选择 run_id → 检查 promotable == true → 创建 batch_id → 复制产物 → 生成 promotion_report.json → 更新 Base Project（如需要）

### 5.2 Promote 是单向操作

- Promote 后不可撤销（但可以 promote 另一个 run 覆盖）
- Promote 不删除原始 run（保留可追溯性）
- 同一时间只有一个 active batch

---

## 6. fast_mode Run 的特殊处理

| 属性 | 正式 Run | fast_mode Run |
|------|---------|--------------|
| Design Space Discovery | 完整执行 | 跳过 |
| promotable | 是（如果完成） | **否** |
| 用途 | 正式产出 | 调试/CI/快速验证 |

---

## 7. MCP 工具支持

Phase 11 在 MCP 后端新增 3 个 Run 治理工具：

| 工具 | 功能 |
|------|------|
| `evidence_create_batch` | 从指定 run 创建 batch |
| `evidence_compare_runs` | 比较两个 run 的产物差异 |
| `evidence_promote_run` | promote run 到 batch 并更新 Base Project |

这三个工具属于 MCP 后端（证据判定层），不属于 MCP 前端。
