# AGENT_UE5 Run Isolation, Compare & Promote
> 原始来源：Docs/History/Phase11_Design_Pack/09_Run_Isolation_Compare_Promote.md

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

项目根目录下的稳定内容，不随 run 变化：
- `Source/` — C++ 源码
- `Content/` — UE5 资产
- `Plugins/` — 插件
- `ProjectInputs/` — GDD 和输入文件
- `Config/` — 项目配置

Base Project 只在 promote 时被更新。

### 2.2 Run Workspace（运行工作区）

每次管线执行的独立产物空间：

```
ProjectState/
  runs/
    {run_id}/
      metadata.json          # run 元数据（时间、session_version、fast_mode 等）
      root_skill_contract.json
      clarification_gate_report.json
      skill_graph.json
      design_space_report.json
      realization_candidates.json
      converged_realization_pack.json
      skill_fragments/
        skill-board.json
        skill-turn.json
        skill-economy.json
        ...
      cross_review_report.json
      build_ir.json
      reviewed_handoff_v3.json
      naming_resolution_log.json
      execution_log.json      # 可选：执行阶段日志
```

`run_id` 格式：`run-{yyyyMMdd}-{HHmmss}-{short_hash}`

### 2.3 Artifact Layer（产物归档层）

经过 promote 的 run 归档为 batch：

```
ProjectState/
  batches/
    {batch_id}/
      manifest.json           # batch 元数据 + 来源 run_id
      promoted_artifacts/     # 从 run 复制的最终产物
        root_skill_contract.json
        build_ir.json
        reviewed_handoff_v3.json
        ...
      promotion_report.json   # promote 决策记录
```

`batch_id` 格式：`batch-{yyyyMMdd}-{sequence}`

---

## 3. Run Metadata

每个 run 必须记录以下元数据：

```json
{
  "run_id": "run-20260415-143022-a3f2",
  "session_id": "session-xxx",
  "session_version": "2.0",
  "fast_mode": false,
  "created_at": "2026-04-15T14:30:22Z",
  "completed_at": "2026-04-15T14:35:10Z",
  "status": "completed",
  "pipeline_stages_completed": [
    "root_skill_contract",
    "clarification_gate",
    "skill_graph",
    "domain_skill_runtime",
    "cross_review",
    "lowering",
    "handoff"
  ],
  "gdd_source": "ProjectInputs/GDD/GDD_MonopolyGame.md",
  "gdd_hash": "sha256:abc123...",
  "provisional_count": 2,
  "constraint_violations": 0,
  "promotable": true
}
```

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

### 4.1 比较维度

| 维度 | 比较内容 |
|------|---------|
| **Constraint 保持性** | 两个 run 的 Constraint Field 值是否一致 |
| **Realization 差异** | converged_realization_pack 的选择差异 |
| **Fragment 差异** | skill_fragments 的 spec 内容差异 |
| **Design Decision 差异** | design_decision_log 中的决策差异 |
| **Build IR 差异** | ir_actions 的数量和内容差异 |
| **Naming 差异** | naming_resolution_log 的解析结果差异 |
| **Provisional 变化** | provisional 项是否减少（表明确认进展） |

### 4.2 比较产物

```json
{
  "comparison_id": "cmp-run1-run2",
  "run_a": "run-20260415-143022-a3f2",
  "run_b": "run-20260415-160000-b7e1",
  "summary": {
    "constraint_consistent": true,
    "realization_changes": 3,
    "fragment_changes": 5,
    "decision_changes": 8,
    "ir_action_delta": "+2",
    "provisional_delta": "-1"
  },
  "details": [
    {
      "domain": "board_topology",
      "change_type": "realization_changed",
      "run_a_choice": "rectangular_loop_centered",
      "run_b_choice": "rectangular_loop_offset",
      "impact": "low"
    }
  ]
}
```

---

## 5. Promote（正式吸收）

### 5.1 Promote 流程

```
选择 run_id
  -> 检查 promotable == true
  -> 创建 batch_id
  -> 复制产物到 batches/{batch_id}/promoted_artifacts/
  -> 生成 promotion_report.json
  -> 更新 Base Project（如需要）
```

### 5.2 Promote 是单向操作

- Promote 后不可撤销（但可以 promote 另一个 run 覆盖）
- Promote 不删除原始 run（保留可追溯性）
- 同一时间只有一个 active batch

### 5.3 Promotion Report

```json
{
  "batch_id": "batch-20260415-001",
  "source_run_id": "run-20260415-143022-a3f2",
  "promoted_at": "2026-04-15T17:00:00Z",
  "promoted_by": "human_review",
  "artifacts_promoted": [
    "root_skill_contract.json",
    "build_ir.json",
    "reviewed_handoff_v3.json"
  ],
  "remaining_provisionals": ["cg-001"],
  "notes": "首次正式 promote，cg-001 待后续确认"
}
```

---

## 6. fast_mode Run 的特殊处理

| 属性 | 正式 Run | fast_mode Run |
|------|---------|--------------|
| Design Space Discovery | 完整执行 | 跳过 |
| Realization Candidates | 完整生成 | 使用默认/最简 |
| promotable | 是（如果完成） | **否** |
| 保留时间 | 永久（直到手动清理） | 可短期清理 |
| 用途 | 正式产出 | 调试/CI/快速验证 |

fast_mode run 的 metadata 中 `fast_mode: true` 且 `promotable: false`。

---

## 7. MCP 工具支持

Phase 11 在 MCP 后端新增 3 个 Run 治理工具：

| 工具 | 功能 |
|------|------|
| `evidence_create_batch` | 从指定 run 创建 batch（执行 promote） |
| `evidence_compare_runs` | 比较两个 run 的产物差异 |
| `evidence_promote_run` | promote run 到 batch 并更新 Base Project |

这三个工具属于 MCP 后端（证据判定层），不属于 MCP 前端（认知桥接层）。

---

## 8. 目录清理策略

- 正式 run：默认保留，手动清理
- fast_mode run：可配置自动清理（如保留最近 N 个）
- promoted batch：永久保留
- 未完成 run（status = "failed"）：保留 execution_log 用于诊断，产物可清理
