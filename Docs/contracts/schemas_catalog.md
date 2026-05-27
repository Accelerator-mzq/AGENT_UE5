# Schemas Catalog — 42 主 Schema 字段级索引(+ 27 examples 附录)

> 版本: v1.1(2026-05-27 ForgeUE real-ue milestone 增 `forgeue_import_evidence` schema + 1 example)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1
> 关联 FEATURE_INVENTORY: Docs/FEATURE_INVENTORY.md F-SCH-* 族
> 验收门禁: 每行 5 字段完整(文件/用途/版本/引用方/关键字段清单)
> 数字注脚: spec v1.1 §3.2 写"64 Schema",2026-05-26 实测 67(41+26),2026-05-27 ForgeUE milestone 后实测 69(42+27);实测为准。

> 路径基准: 所有 `文件` 列条目均相对 `Plugins/AgentBridge/Schemas/`。
> 引用方采集方法: 在 `Plugins/AgentBridge/{Scripts,Compiler,MCP,SkillTemplates,Tests,AgentBridgeTests}` 与根 `Scripts/` 下,对每个 schema basename 做内容搜索(`.py` + `.json`),排除 schema 自身与 examples 数据。每行给出 ≤3 个代表性引用,完整命中数见行尾括号。
> 关键字段清单: 取顶层 `properties` 的前 8 个 key;若顶层只有 `$defs`(common 库)则标注 "$defs 库:..." 列出 def 名;若是 manifest 则取 manifest 顶层 key。

## 主表(42 主 Schema)

| 文件 | 用途 | 版本 | 引用方 | 关键字段清单 |
|------|------|------|--------|--------------|
| batch_manifest.schema.json | Phase 11 batch promote 后写入的治理元数据 | v1 | Scripts/validation/validate_examples.py; MCP/evidence_tools.py; Tests/scripts/task12_phase11_run_governance_validation.py (3) | manifest_version, batch_id, source_run_id, created_at, promoted_at, active, promoted_by, promoted_artifacts... |
| build_ir.schema.json | Lowering Pipeline 输出的构建中间表示 | v1 | Compiler/lowering/lowering.py; Compiler/lowering/__init__.py; Compiler/pipeline/pipeline_orchestrator.py (3) | ir_version, ir_id, source_review_id, phase_scope, build_steps, validation_ir, lowering_report, recovery_hints... |
| build_ir_v2.schema.json | Stage 6 Build IR v2,内嵌 naming_resolution_log | v2 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | ir_version, ir_id, source_review_id, source_contract_id, phase_scope, build_steps, validation_ir, lowering_report... |
| clarification_gate_report.schema.json | Phase 11 Clarification Gate 决策记录 | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | gate_version, source_contract_id, items, provisional_items, blocking_items, fast_mode, clarification_gate_policy, retained_clarifications... |
| common/bounds.schema.json | UE5 包围盒结构定义 | v1 | Schemas/feedback/asset/get_asset_metadata.response.schema.json; Schemas/versions/v0.1_manifest.json; Schemas/write_feedback/write_operation_feedback.response.schema.json (3) | world_bounds_origin, world_bounds_extent |
| common/collision.schema.json | UE5.5.4 碰撞状态结构定义 | v1 | Schemas/feedback/actor/get_actor_state.response.schema.json; Schemas/versions/v0.1_manifest.json; Schemas/write_feedback/write_operation_feedback.response.schema.json (3) | collision_profile_name, collision_enabled, generate_overlap_events, collision_box_extent, collision_capsule_radius, collision_capsule_half_height, can_affect_navigation |
| common/error.schema.json | 统一 warnings/errors 数组结构定义 | v1 | Schemas/feedback/actor/get_actor_bounds.response.schema.json; Schemas/feedback/actor/get_actor_state.response.schema.json; Schemas/feedback/actor/get_component_state.response.schema.json (11) | $defs 库: warning_item, error_item, warnings_array, errors_array |
| common/material.schema.json | UE5.5.4 材质槽位分配结构定义 | v1 | Schemas/feedback/actor/get_material_assignment.response.schema.json; Schemas/versions/v0.1_manifest.json; Schemas/write_feedback/write_operation_feedback.response.schema.json (3) | component_name, slot_name, material_path |
| common/primitives.schema.json | AGENT+UE5 基础类型(所有 Schema 底层依赖) | v1 | Scripts/bridge/bridge_core.py; Schemas/common/bounds.schema.json; Schemas/common/collision.schema.json (16) | $defs 库: status, vector3, rotator, string_array, non_empty_string, path_string |
| common/transform.schema.json | UE5 Actor Transform 结构定义 | v1 | Schemas/feedback/actor/get_actor_state.response.schema.json; Schemas/versions/v0.1_manifest.json; Schemas/write_feedback/write_operation_feedback.response.schema.json (3) | location, rotation, relative_scale3d |
| compiler_session.schema.json | Compiler Pipeline Orchestrator 会话状态文件 | v1(兼容 Phase10 v1.0/Phase11 v2.0) | Compiler/pipeline/session.py; Tests/run_system_tests.py (2) | session_id, created_at, gdd_path, target_phase, output_dir, current_stage, stage_outputs, status... |
| converged_realization_pack.schema.json | Phase 11 Convergence 最终选择产物 | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | pack_version, skill_instance_id, source_candidates, converged_choices, cross_dimension_consistency, metadata |
| cross_review_report.schema.json | Cross-Spec Review 阶段统一审查报告 | v1 | Compiler/cross_review/cross_review.py; Compiler/cross_review/__init__.py; Compiler/pipeline/pipeline_orchestrator.py (3) | review_id, review_version, input_fragment_ids, review_status, review_checks, issues_found, phase_scope_check, reviewed_dynamic_spec_tree... |
| cross_review_report_v2.schema.json | Stage 5 跨域冲突与 Blueprint 薄层审查 | v2 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | review_id, review_version, source_contract_id, source_gate_id, source_graph_id, input_fragment_ids, review_status, review_checks... |
| design_decision_log.schema.json | Stage 4 非平凡设计选择结构化日志 | v1 | Scripts/validation/validate_examples.py (1) | log_version, source_kind, source_id, entries, metadata |
| design_space_report.schema.json | Phase 11 Design Space Discovery 产物 | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | report_version, skill_instance_id, source_contract_id, source_graph_id, discovery_dimensions, locked_dimensions, metadata |
| evidence_manifest.schema.json | Phase 10 MCP 后端证据裁决标准化清单 | v1 | Scripts/evidence/evidence_manager.py (1) | run_id, created_at, test_type, test_scope, evidence_items, summary, status |
| feedback/actor/get_actor_bounds.response.schema.json | Actor 世界包围盒查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/actor/get_actor_state.response.schema.json | Actor 核心状态(transform/collision/tags)查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/actor/get_component_state.response.schema.json | Actor 指定组件相对变换查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/actor/get_material_assignment.response.schema.json | Actor MeshComponent 材质槽位查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/asset/get_asset_metadata.response.schema.json | 单资产元数据查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/asset/get_dirty_assets.response.schema.json | 未保存脏资产列表查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/level/list_level_actors.response.schema.json | 关卡 Actor 列表查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/project/get_current_project_state.response.schema.json | 当前项目与编辑器上下文查询反馈 | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| feedback/validation/run_map_check.response.schema.json | 地图检查结果反馈(MapCheck) | v1 | Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (2) | status, summary, data, warnings, errors |
| forgeue_import_evidence.schema.json | ForgeUE manifest 真机导入每条 asset 的逐条证据(bridge_python / bridge_rc_api 写盘) | v1 | Scripts/validation/validate_examples.py; Scripts/orchestrator/forgeue_manifest_importer.py; Scripts/run_forgeue_real_smoke.py (3) | asset_entry_id, op_id, asset_kind, bridge_mode, status, timestamp, source_uri_abs, uasset_object_path... |
| gdd_projection.schema.json | Design Intake 从 GDD 提取的结构化投影 | v1 | Compiler/intake/design_intake.py; Compiler/intake/__init__.py; Compiler/pipeline/pipeline_orchestrator.py (3) | projection_version, projection_id, source_gdd, game_identity, phase_scope, design_domains, implementation_hints, ambiguities... |
| naming_resolution_log.schema.json | Build IR v2 命名审计 sidecar | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | log_version, source_ir_id, entries, summary, metadata |
| planner_output.schema.json | Planner / Routing Agent 结构化输出 | v1 | Compiler/pipeline/pipeline_orchestrator.py; Compiler/planner/planner.py; Compiler/planner/__init__.py (3) | planner_meta, project_intent, routing_decision, selected_skill_instances, dynamic_spec_targets, execution_strategy, capability_gaps, review_focuses... |
| realization_candidates.schema.json | Phase 11 Realization Candidate Generation 产物 | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | candidates_version, skill_instance_id, source_design_space_report, candidates, metadata |
| reviewed_handoff.schema.json | Compiler→Orchestrator 正式交接物(v1) | v1 | Scripts/validation/test_handoff_schema.py; Scripts/validation/validate_examples.py; Tests/scripts/test_compiler_plane_foundation.py (7) | handoff_version, handoff_id, handoff_mode, status, project_context, baseline_context, routing_context, delta_context... |
| reviewed_handoff_v2.schema.json | Skill-First Compiler→Orchestrator 交接物(v2) | v2 | Compiler/pipeline/pipeline_orchestrator.py (1) | handoff_meta, project_context, planner_summary, selected_skill_instances, reviewed_dynamic_spec_tree, cross_review_summary, lowering_summary, build_ir... |
| reviewed_handoff_v3.schema.json | Stage 7 面向执行层的最终 handoff | v3 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | handoff_meta, run_id, project_context, selected_skill_instances, design_directions_summary, constraint_variant_summary, baseline_coverage_summary, provisional_items... |
| root_skill_contract.schema.json | Phase 11 能力骨架/约束容器/Phase 启用边界 | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (4) | contract_version, contract_id, source_gdd, game_identity, phase_scope, constraint_fields, variant_fields, soft_intents... |
| run_comparison.schema.json | 跨 run 治理比较产物(六类差异) | v1 | Scripts/validation/validate_examples.py; MCP/evidence_tools.py; Tests/scripts/task12_phase11_run_governance_validation.py (3) | comparison_version, comparison_id, run_a_id, run_b_id, compared_at, summary, details, metadata |
| run_plan.schema.json | Orchestrator 基于 Reviewed Handoff 生成的执行计划 | v1 | Scripts/validation/test_handoff_schema.py; Scripts/validation/validate_examples.py; Tests/scripts/test_phase7_governance_and_jrpg.py (4) | run_plan_version, run_plan_id, source_handoff_id, mode, status, context, workflow_sequence, validation_checkpoints... |
| skill_fragment.schema.json | 单个 Skill Instance 运行时输出产物(v1) | v1 | Compiler/pipeline/pipeline_orchestrator.py; Compiler/skill_runtime/skill_runtime.py; Compiler/skill_runtime/__init__.py (3) | skill_instance_id, template_id, phase_scope, status, emitted_families, spec_fragments, assumptions, open_questions... |
| skill_fragment_v2.schema.json | Phase 11 Domain Skill 输出(含 design_decision_log) | v2 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (5) | fragment_version, skill_instance_id, template_id, domain_type, phase_scope, status, emitted_families, spec_fragments... |
| skill_graph.schema.json | Phase 11 Domain Skill 依赖/耦合/收敛顺序 | v1 | Scripts/validation/validate_examples.py; Compiler/pipeline/pipeline_orchestrator.py; Tests/scripts/task11_phase11_mcp_e2e.py (5) | graph_version, graph_id, source_contract_id, source_gate_id, nodes, edges, metadata |
| versions/v0.1_manifest.json | v0.1 Schema 清单 manifest(列出 common/stable/experimental/examples 分组) | v0.1 | (暂无外部引用 — manifest 类自描述文件,Phase 2 验证脚本索引中纳入) | version, engine_version, description, common_schemas, stable_schemas, experimental_schemas, examples |
| write_feedback/write_operation_feedback.response.schema.json | 通用写操作反馈结构(spawn/transform/import 等) | v1 | Scripts/bridge/write_tools.py; Scripts/validation/validate_examples.py; Schemas/versions/v0.1_manifest.json (3) | status, summary, data, warnings, errors |

## 附录 A: examples/ 示例数据(27 份)

`Plugins/AgentBridge/Schemas/examples/` 下是用于 Schema 验证 + 单元测试的 fixture 数据,**非契约本体**,不进主表。完整 27 份按文件名与对应 Schema 映射如下:

| example 文件 | 对应主 Schema |
|---|---|
| get_actor_bounds.example.json | feedback/actor/get_actor_bounds.response.schema.json |
| get_actor_state.example.json | feedback/actor/get_actor_state.response.schema.json |
| get_asset_metadata.example.json | feedback/asset/get_asset_metadata.response.schema.json |
| get_component_state.example.json | feedback/actor/get_component_state.response.schema.json |
| get_current_project_state.example.json | feedback/project/get_current_project_state.response.schema.json |
| get_dirty_assets.example.json | feedback/asset/get_dirty_assets.response.schema.json |
| forgeue_import_evidence_example.json | forgeue_import_evidence.schema.json |
| get_material_assignment.example.json | feedback/actor/get_material_assignment.response.schema.json |
| list_level_actors.example.json | feedback/level/list_level_actors.response.schema.json |
| phase11_batch_manifest.example.json | batch_manifest.schema.json |
| phase11_build_ir_v2.example.json | build_ir_v2.schema.json |
| phase11_clarification_gate_report.example.json | clarification_gate_report.schema.json |
| phase11_converged_realization_pack.example.json | converged_realization_pack.schema.json |
| phase11_cross_review_report_v2.example.json | cross_review_report_v2.schema.json |
| phase11_design_decision_log.example.json | design_decision_log.schema.json |
| phase11_design_space_report.example.json | design_space_report.schema.json |
| phase11_naming_resolution_log.example.json | naming_resolution_log.schema.json |
| phase11_realization_candidates.example.json | realization_candidates.schema.json |
| phase11_reviewed_handoff_v3.example.json | reviewed_handoff_v3.schema.json |
| phase11_root_skill_contract.example.json | root_skill_contract.schema.json |
| phase11_run_comparison.example.json | run_comparison.schema.json |
| phase11_skill_fragment_v2.example.json | skill_fragment_v2.schema.json |
| phase11_skill_graph.example.json | skill_graph.schema.json |
| reviewed_handoff_greenfield.example.json | reviewed_handoff.schema.json |
| run_map_check.example.json | feedback/validation/run_map_check.response.schema.json |
| run_plan_greenfield.example.json | run_plan.schema.json |
| write_operation_feedback.example.json | write_feedback/write_operation_feedback.response.schema.json |

## 附录 B: 行数自检

- 主 catalog 数据行数实测: **42**(已在主表逐行列出,2026-05-26 41 + 2026-05-27 ForgeUE +1 = 42)
- examples 附录数据行数实测: **27**(已在附录 A 逐行列出,2026-05-26 26 + 2026-05-27 ForgeUE +1 = 27)
- 合计 **69**(spec v1.1 §3.2 写 64,实测 +5,以实测为准)
- 自检命令(Windows PowerShell 等价 / Git-Bash):
  - `find Plugins/AgentBridge/Schemas -name "*.json" -not -path "*/examples/*" | wc -l` → 42
  - `find Plugins/AgentBridge/Schemas/examples -name "*.json" | wc -l` → 27
- 引用方采集方法: 在 `Plugins/AgentBridge/{Scripts,Compiler,MCP,SkillTemplates,Tests,AgentBridgeTests}` 与根 `Scripts/` 下扫描 `*.py` + `*.json`(共 176 个候选文件),逐 schema basename 做字面包含搜索,排除 schema 自身和 examples 数据
- Schema 字段读取方法: 直接读取每个 `.schema.json` 顶层 `properties` 取前 8 个 key;若顶层只有 `$defs`(common 库)则列出 def 名;manifest 文件取其顶层 key
