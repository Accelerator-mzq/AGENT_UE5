# AGENT_UE5 Phase 11 实施任务书

## 1. 分批策略

实施分三批，按依赖关系排序：

- **第一批**：管线骨架 — 让 v2.0 管线能跑通（空壳可以，但路径完整）
- **第二批**：Design + Realization — 让管线产出有实际意义的设计内容
- **Defer**：Run 治理 + 高级功能 — 不影响核心管线的辅助功能

---

## 2. 第一批：管线骨架（14 项）

| # | 任务 | 涉及文件 | 依赖 | 复杂度 |
|---|------|---------|------|--------|
| 1.1 | Session v2 字段扩展 | `Compiler/pipeline/session.py` | 无 | 低 |
| 1.2 | STAGE_NAME_MAP_V2 定义 | `Compiler/pipeline/pipeline_orchestrator.py` | 1.1 | 低 |
| 1.3 | STAGE_ARTIFACT_MAP_V2 定义 | `Compiler/pipeline/pipeline_orchestrator.py` | 1.2 | 低 |
| 1.4 | session_version 路由逻辑 | `Compiler/pipeline/pipeline_orchestrator.py` | 1.1-1.3 | 中 |
| 1.5 | root_skill_contract.schema.json | `Schemas/` | 无 | 中 |
| 1.6 | clarification_gate_report.schema.json | `Schemas/` | 无 | 中 |
| 1.7 | skill_graph.schema.json | `Schemas/` | 无 | 中 |
| 1.8 | design_space_report.schema.json | `Schemas/` | 无 | 中 |
| 1.9 | realization_candidates.schema.json | `Schemas/` | 无 | 中 |
| 1.10 | converged_realization_pack.schema.json | `Schemas/` | 无 | 中 |
| 1.11 | skill_fragment_v2.schema.json | `Schemas/` | 无 | 低 |
| 1.12 | MCP 前端工具重命名 + 别名 | `MCP/tools/` | 1.4 | 低 |
| 1.13 | compiler_clarification_prepare/save | `MCP/tools/` | 1.6 | 中 |
| 1.14 | compiler_create_session 增加 session_version/run_id | `MCP/tools/` | 1.1 | 低 |

### 第一批完成标志

- `session_version: "2.0"` 的 session 可以创建
- 7 个新 Schema 文件存在且通过 jsonschema 校验
- pipeline_orchestrator 可以按 V2 stage map 路由
- MCP 前端 6 个工具（含 2 个新增）可以调用（哪怕 handler 是 stub）
- 旧 v1.0 管线不受影响

---

## 3. 第二批：Discovery + Realization（12 项）

| # | 任务 | 涉及文件 | 依赖 | 复杂度 |
|---|------|---------|------|--------|
| 2.1 | Root Skill Contract 生成逻辑 | `Compiler/stages/root_skill_contract.py` | 1.4, 1.5 | 高 |
| 2.2 | Clarification Gate 执行逻辑 | `Compiler/stages/clarification_gate.py` | 1.4, 1.6 | 高 |
| 2.3 | Skill Graph Planning 逻辑 | `Compiler/stages/skill_graph_planning.py` | 1.4, 1.7 | 高 |
| 2.4 | Domain Skill Runtime 框架 | `Compiler/stages/domain_skill_runtime.py` | 2.3 | 高 |
| 2.5 | Design Space Discovery 引擎 | `Compiler/stages/discovery_engine.py` | 2.4, 1.8 | 高 |
| 2.6 | Realization Candidate Generator | `Compiler/stages/realization_generator.py` | 2.5, 1.9 | 高 |
| 2.7 | Convergence 引擎 | `Compiler/stages/convergence_engine.py` | 2.6, 1.10 | 高 |
| 2.8 | Cross-Domain Review v2 | `Compiler/stages/cross_review_v2.py` | 2.4 | 高 |
| 2.9 | Build IR v2 + naming_resolution_log | `Compiler/stages/lowering_v2.py` | 2.8 | 高 |
| 2.10 | Handoff v3 Assembly | `Compiler/stages/handoff_v3.py` | 2.9 | 中 |
| 2.11 | cross_review_report_v2.schema.json | `Schemas/` | 无 | 中 |
| 2.12 | build_ir_v2.schema.json + reviewed_handoff_v3.schema.json | `Schemas/` | 无 | 中 |

### 第二批完成标志

- 完整 v2.0 管线可以端到端跑通（GDD -> Handoff v3）
- 每个 Stage 产出符合对应 Schema
- Design Space Discovery 产出非空维度
- Realization Candidates 产出非空候选
- design_decision_log 非空
- naming_resolution_log 非空
- Cross-Domain Review 包含 Constraint 保持性检查 + BP 薄层检查

---

## 4. Defer：Run 治理 + 高级功能（7 项）

| # | 任务 | 涉及文件 | 依赖 | 复杂度 |
|---|------|---------|------|--------|
| D.1 | run_comparison.schema.json | `Schemas/` | 无 | 低 |
| D.2 | batch_manifest.schema.json | `Schemas/` | 无 | 低 |
| D.3 | evidence_create_batch 工具 | `MCP/tools/` | D.2 | 中 |
| D.4 | evidence_compare_runs 工具 | `MCP/tools/` | D.1 | 中 |
| D.5 | evidence_promote_run 工具 | `MCP/tools/` | D.2, D.3 | 中 |
| D.6 | fast_mode 完整实现 | `Compiler/pipeline/` | 第二批全部 | 高 |
| D.7 | Baseline Domain Skill Template 全套 | `SkillTemplates/baseline/` | 第二批全部 | 高 |

### Defer 项不阻塞核心管线

这些功能增强管线的可管理性和可追溯性，但核心管线（GDD -> Handoff）不依赖它们。

---

## 5. 关键路径

```
1.1 (Session v2)
  -> 1.2-1.4 (Orchestrator v2)
    -> 2.1 (Root Skill Contract)
      -> 2.2 (Clarification Gate)
        -> 2.3 (Skill Graph)
          -> 2.4 (Domain Skill Runtime)
            -> 2.5-2.7 (Discovery/Realization/Convergence)
              -> 2.8 (Cross Review v2)
                -> 2.9 (Build IR v2)
                  -> 2.10 (Handoff v3)
```

Schema 创建（1.5-1.11, 2.11-2.12）可与对应 Stage 逻辑并行。
MCP 工具变更（1.12-1.14）可与 Schema 并行。

---

## 6. 实施约束

### 6.1 不可修改的文件

参见 `CLAUDE.md` 中"绝对不要修改的文件"列表。Phase 11 实施不涉及这些文件。

### 6.2 新文件位置

| 类型 | 位置 |
|------|------|
| 新 Schema | `Plugins/AgentBridge/Schemas/` |
| 新 Stage 逻辑 | `Plugins/AgentBridge/Compiler/stages/` |
| Baseline Templates | `Plugins/AgentBridge/SkillTemplates/baseline/` |
| MCP 工具 | `Plugins/AgentBridge/MCP/tools/` |
| Session 修改 | `Plugins/AgentBridge/Compiler/pipeline/session.py` |
| Orchestrator 修改 | `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py` |

### 6.3 测试策略

- 每个新 Schema：jsonschema 校验 + 示例文件校验
- 每个新 Stage：单元测试 + 与前后 Stage 的集成测试
- 端到端：`run_system_tests.py` 扩展覆盖 v2.0 管线
- 兼容性：确认 v1.0 管线测试仍全部通过
