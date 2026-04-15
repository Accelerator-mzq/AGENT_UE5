# AGENT_UE5 Schema 与产物参考

## 1. Schema 变更总表

### 1.1 第一批（管线骨架）— 7 个新 Schema

| Schema | 文件名 | 来源文档 | 说明 |
|--------|--------|---------|------|
| Root Skill Contract | `root_skill_contract.schema.json` | 02 | 能力骨架 + 约束容器 + 启用边界 |
| Clarification Gate Report | `clarification_gate_report.schema.json` | 05 | 4 档决策 + provisional + fast_mode 策略 |
| Skill Graph | `skill_graph.schema.json` | 08 | 节点 + 边 + 收敛顺序 |
| Design Space Report | `design_space_report.schema.json` | 07 | 发现维度 + 约束来源 + 耦合标注 |
| Realization Candidates | `realization_candidates.schema.json` | 07 | 候选方向 + trade-off |
| Converged Realization Pack | `converged_realization_pack.schema.json` | 07 | 收敛选择 + rationale |
| Skill Fragment v2 | `skill_fragment_v2.schema.json` | 07/08 | 原 skill_fragment + design_decision_log 字段 |

### 1.2 第二批（Discovery + Realization + Review）— 5 个新/升级 Schema

| Schema | 文件名 | 来源文档 | 说明 |
|--------|--------|---------|------|
| Cross Review Report v2 | `cross_review_report_v2.schema.json` | 01 | 原版 + 跨域 realization 冲突 + Constraint 保持性 + BP 薄层检查 |
| Build IR v2 | `build_ir_v2.schema.json` | 01/10 | 原版 + naming_resolution_log + provisional_warning + Baseline 步骤 |
| Reviewed Handoff v3 | `reviewed_handoff_v3.schema.json` | 01 | v2 + run_id + design_directions + constraint_variant_summary + baseline_coverage + provisional_items |
| Naming Resolution Log | `naming_resolution_log.schema.json` | 10 | resolved + tier + evidence（Build IR 内嵌或独立） |
| Design Decision Log | `design_decision_log.schema.json` | 07 | decision_id + topic + chosen + rationale + impact |

### 1.3 Defer — 2 个 Schema

| Schema | 文件名 | 来源文档 | 说明 |
|--------|--------|---------|------|
| Run Comparison | `run_comparison.schema.json` | 09 | 跨 run 比较产物 |
| Batch Manifest | `batch_manifest.schema.json` | 09 | promote 后的 batch 元数据 |

---

## 2. 旧 Schema 兼容策略

### 2.1 保留不删的 Schema

以下 Phase 10 Schema 保留不删，用于 `session_version: "1.0"` 的旧管线：

| Schema | 文件名 | 状态 |
|--------|--------|------|
| GDD Projection | `gdd_projection.schema.json` | 保留（v1.0 Stage 1 输出） |
| Planner Output | `planner_output.schema.json` | 保留（v1.0 Stage 2 输出） |
| Reviewed Handoff v2 | `reviewed_handoff_v2.schema.json` | 保留（v1.0 最终输出） |
| Skill Fragment v1 | `skill_fragment.schema.json` | 保留（v1.0 Fragment 格式） |
| Cross Review Report v1 | `cross_review_report.schema.json` | 保留（v1.0 Review 输出） |
| Build IR v1 | `build_ir.schema.json` | 保留（v1.0 Lowering 输出） |

### 2.2 版本路由

Schema 选择通过 `session_version` 路由：

```
session_version == "1.0" (或缺失):
  -> gdd_projection.schema.json
  -> planner_output.schema.json
  -> skill_fragment.schema.json
  -> cross_review_report.schema.json
  -> build_ir.schema.json
  -> reviewed_handoff_v2.schema.json

session_version == "2.0":
  -> root_skill_contract.schema.json
  -> clarification_gate_report.schema.json
  -> skill_graph.schema.json
  -> design_space_report.schema.json
  -> realization_candidates.schema.json
  -> converged_realization_pack.schema.json
  -> skill_fragment_v2.schema.json
  -> cross_review_report_v2.schema.json
  -> build_ir_v2.schema.json
  -> reviewed_handoff_v3.schema.json
```

不做跨版本产物格式转换。v1.0 session 始终使用 v1 Schema，v2.0 session 始终使用 v2 Schema。

---

## 3. MCP 工具变更

### 3.1 工具总数

Phase 10: 42 个 -> Phase 11: 47 个（+5 净增）

### 3.2 MCP 前端（认知桥接层）变更

#### 重命名（4 个）

| 旧名 | 新名 | 说明 |
|------|------|------|
| `compiler_intake_prepare` | `compiler_root_skill_prepare` | 对应新 Stage 1: Root Skill Contract |
| `compiler_intake_save` | `compiler_root_skill_save` | 对应新 Stage 1 |
| `compiler_plan_prepare` | `compiler_skill_graph_prepare` | 对应新 Stage 3: Skill Graph Planning |
| `compiler_plan_save` | `compiler_skill_graph_save` | 对应新 Stage 3 |

旧名在过渡期保留为别名（alias），功能等价。

#### 新增（2 个）

| 工具 | 说明 |
|------|------|
| `compiler_clarification_prepare` | 准备 Clarification Gate 输入 |
| `compiler_clarification_save` | 保存 Clarification Gate 输出 |

#### 保留不变

| 工具 | 说明 |
|------|------|
| `compiler_create_session` | 保留，增加 `session_version` 和 `run_id` 字段 |
| `compiler_get_session_status` | 保留，增加新阶段状态 |

### 3.3 MCP 后端（证据判定层）变更

#### 新增（3 个）

| 工具 | 说明 |
|------|------|
| `evidence_create_batch` | 从指定 run 创建 batch |
| `evidence_compare_runs` | 比较两个 run 的产物差异 |
| `evidence_promote_run` | promote run 到 batch |

#### 保留不变

Phase 10 的所有 evidence 工具保留不变。

---

## 4. 产物目录结构

### 4.1 Phase 11 (v2.0) 单次 Run 的完整产物

```
ProjectState/runs/{run_id}/
  metadata.json
  root_skill_contract.json          # Stage 1
  clarification_gate_report.json    # Stage 2
  skill_graph.json                  # Stage 3
  design_space_report.json          # Stage 4 (per skill, 合并)
  realization_candidates.json       # Stage 4 (per skill, 合并)
  converged_realization_pack.json   # Stage 4 (per skill, 合并)
  skill_fragments/                  # Stage 4 (per skill)
    skill-board-topology.json
    skill-tile-system.json
    skill-turn-loop.json
    skill-economy.json
    skill-player-management.json
    skill-dice.json
    skill-baseline-start-screen.json
    skill-baseline-main-menu.json
    skill-baseline-settings.json
    skill-baseline-pause.json
    skill-baseline-results.json
    skill-baseline-hud.json
  cross_review_report.json          # Stage 5
  build_ir.json                     # Stage 6
  reviewed_handoff_v3.json          # Stage 7
  naming_resolution_log.json        # Stage 6 附属
```

### 4.2 Phase 10 (v1.0) 产物（不变）

```
ProjectState/phase10/
  gdd_projection.json               # Stage 1
  planner_output.json               # Stage 2
  skill_fragments/                   # Stage 3
    skill-board.json
    ...
  cross_review_report.json          # Stage 4
  build_ir.json                     # Stage 5
  reviewed_handoff_v2.json          # 最终输出
```

---

## 5. pipeline_orchestrator.py 变更要点

### 5.1 Stage Map

```python
# Phase 10 (保留)
STAGE_NAME_MAP_V1 = {
    1: "design_intake",
    2: "planner",
    3: "skill_runtime",
    4: "cross_review",
    5: "lowering"
}

# Phase 11 (新增)
STAGE_NAME_MAP_V2 = {
    1: "root_skill_contract",
    2: "clarification_gate",
    3: "skill_graph_planning",
    4: "domain_skill_runtime",
    5: "cross_domain_review",
    6: "lowering",
    7: "handoff_assembly"
}
```

### 5.2 路由逻辑

```python
def get_stage_map(session):
    if getattr(session, 'session_version', '1.0') == '2.0':
        return STAGE_NAME_MAP_V2
    return STAGE_NAME_MAP_V1
```

### 5.3 Artifact Map

每个 Stage 对应的输入/输出 Schema 通过 STAGE_ARTIFACT_MAP_V1 / V2 分别定义，路由逻辑同上。
