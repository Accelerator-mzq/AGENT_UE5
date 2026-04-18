# Schema 对齐验证报告

## 1. 结论

- Design Pack 显式声明的 schema 数：`20`
- `Plugins/AgentBridge/Schemas/` 实际存在的 schema 数：`24`

本报告以 `Docs/History/Phase11_Design_Pack/11_Schema_and_Artifact_Reference.md` 作为逐文件声明源；
`Docs/Current/18_Phase11_Closeout.md` 只作为“Phase 11 Schema 集已验通”的摘要来源，不承担逐文件清单职责。

## 2. 对齐表

| Schema | 文档声明 | 文件存在 | 状态 | 备注 |
|--------|---------|---------|------|------|
| `batch_manifest.schema.json` | `defer` | `✅` | `对齐` | Design Pack defer 项，但当前代码已实现 |
| `build_ir.schema.json` | `旧版兼容保留` | `✅` | `对齐` | 历史兼容保留 |
| `build_ir_v2.schema.json` | `第二批` | `✅` | `对齐` | 第二批 |
| `clarification_gate_report.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |
| `compiler_session.schema.json` | `—` | `✅` | `未声明` | 文件存在，但未在 Phase 11 Design Pack 清单中显式声明 |
| `converged_realization_pack.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |
| `cross_review_report.schema.json` | `旧版兼容保留` | `✅` | `对齐` | 历史兼容保留 |
| `cross_review_report_v2.schema.json` | `第二批` | `✅` | `对齐` | 第二批 |
| `design_decision_log.schema.json` | `第二批` | `✅` | `对齐` | 第二批 |
| `design_space_report.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |
| `evidence_manifest.schema.json` | `—` | `✅` | `未声明` | 文件存在，但未在 Phase 11 Design Pack 清单中显式声明 |
| `gdd_projection.schema.json` | `旧版兼容保留` | `✅` | `对齐` | 历史兼容保留 |
| `naming_resolution_log.schema.json` | `第二批` | `✅` | `对齐` | 第二批 |
| `planner_output.schema.json` | `旧版兼容保留` | `✅` | `对齐` | 历史兼容保留 |
| `realization_candidates.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |
| `reviewed_handoff.schema.json` | `—` | `✅` | `未声明` | 文件存在，但未在 Phase 11 Design Pack 清单中显式声明 |
| `reviewed_handoff_v2.schema.json` | `旧版兼容保留` | `✅` | `对齐` | 历史兼容保留 |
| `reviewed_handoff_v3.schema.json` | `第二批` | `✅` | `对齐` | 第二批 |
| `root_skill_contract.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |
| `run_comparison.schema.json` | `defer` | `✅` | `对齐` | Design Pack defer 项，但当前代码已实现 |
| `run_plan.schema.json` | `—` | `✅` | `未声明` | 文件存在，但未在 Phase 11 Design Pack 清单中显式声明 |
| `skill_fragment.schema.json` | `旧版兼容保留` | `✅` | `对齐` | 历史兼容保留 |
| `skill_fragment_v2.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |
| `skill_graph.schema.json` | `第一批` | `✅` | `对齐` | 第一批 |

## 3. 汇总

- 文档声明但文件缺失：`0`
- 文件存在但未在 Design Pack 清单中显式声明：`4`

其中“未声明”不一定是错误，可能属于：

- 更早阶段遗留 schema
- 与 Phase 11 主链无直接关系的辅助 schema
- 收尾后实现补齐但未回写 Design Pack 的文件
