# TASK 03 Evidence — Pipeline Orchestrator v1/v2 路由

日期：2026-04-15

## 任务范围

- 更新 [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)，将原 Phase 10 五阶段路由拆分为 v1/v2 双路由。
- 保留 v1 五阶段 prepare/save 行为。
- 新增 v2 七阶段 stage map 与 artifact map。
- 确保 public 入口 `prepare_stage`、`save_stage`、`run_stage`、`run_pipeline`、`assemble_handoff` 均按 `session_version` 路由。

## 实现摘要

- 新增 `STAGE_NAME_MAP_V1` / `STAGE_ARTIFACT_MAP_V1`，旧 `STAGE_NAME_MAP` / `STAGE_ARTIFACT_MAP` 保留为 v1 alias。
- 新增 `STAGE_NAME_MAP_V2`，覆盖：
  - Stage 1 `root_skill_contract`
  - Stage 2 `clarification_gate`
  - Stage 3 `skill_graph_planning`
  - Stage 4 `domain_skill_runtime`
  - Stage 5 `cross_domain_review`
  - Stage 6 `lowering`
  - Stage 7 `handoff_assembly`
- 新增 `STAGE_ARTIFACT_MAP_V2`，覆盖 `metadata.json`、`root_skill_contract.json`、`clarification_gate_report.json`、`skill_graph.json`、`design_space_report.json`、`realization_candidates.json`、`converged_realization_pack.json`、`skill_fragments/`、`cross_review_report.json`、`build_ir.json`、`reviewed_handoff_v3.json`、`naming_resolution_log.json`。
- 新增 `get_stage_name_map()`、`get_stage_artifact_map()`、`get_max_stage()`。
- v2 输出根目录路由到 `ProjectState/runs/{run_id}/`。
- v2 Schema 尚未由 TASK 04/10 创建时，prepare/save 返回结构化 `schema_missing`，不伪造成功。

## 验证结果

专项 Orchestrator 验证：

```text
TASK03_ORCHESTRATOR_TESTS=passed
```

覆盖项：

- v1 `get_max_stage()` 返回 5。
- v1 Stage 1-5 `prepare_stage` / `save_stage` 通过。
- v1 Stage 7 返回 `invalid_stage`。
- v2 `get_max_stage()` 返回 7。
- v2 Stage 7 可识别为 `handoff_assembly`，缺少 Stage 6 产物时返回 `missing_input` 而不是 `invalid_stage`。
- v2 Stage 1 在 Schema 尚未存在时返回 `schema_missing`，等待 TASK 04 补齐。
- v2 artifact map 覆盖 TASK 03 要求的全部 12 类产物。

语法验证：

```text
python -m py_compile Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py
python -m py_compile Plugins/AgentBridge/Compiler/pipeline/session.py
```

严格示例验证：

```text
Checked examples       : 12
Passed                 : 12
Failed                 : 0
Reference-only skipped : 0
Unmapped examples      : 0
Missing schema targets : 0

[SUCCESS] 全部 example 校验通过，本地校验链正常。
```

执行命令：

```powershell
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

## 结论

TASK 03 验收标准已满足。M2 已完成：TASK 02 已完成 Session v2 字段扩展，TASK 03 已完成 Pipeline v2 路由骨架。
