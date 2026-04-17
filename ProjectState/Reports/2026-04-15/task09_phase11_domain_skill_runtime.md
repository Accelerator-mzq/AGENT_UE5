# TASK 09 Evidence — Domain Skill Runtime、Discovery、Candidates、Convergence、Fragment v2

日期：2026-04-15

## 任务范围

- 新增 [discovery_engine.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/discovery_engine.py)，实现每个 Discovery-capable 节点的设计维度发现与 locked_dimensions 提取。
- 新增 [realization_generator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/realization_generator.py)，为每个维度生成候选方向、trade-off 与复杂度标记。
- 新增 [convergence_engine.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/convergence_engine.py)，实现 candidate 选择、rationale、rejected_alternatives、provisional 标记。
- 新增 [domain_skill_runtime.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py)，按 dependency 顺序执行 Domain Skill Runtime，并生成 Fragment v2。
- 更新 [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)，使 v2 Stage 4 `prepare_stage/save_stage` 支持：
  - 真实 Stage 4 生成逻辑
  - `design_space_report.json`
  - `realization_candidates.json`
  - `converged_realization_pack.json`
  - `skill_fragments/*.json`
  的多产物校验与落盘。
- 生成最终证据 run：
  - [design_space_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/design_space_report.json)
  - [realization_candidates.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/realization_candidates.json)
  - [converged_realization_pack.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/converged_realization_pack.json)
  - [skill_fragments](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/skill_fragments)
- 更新 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 的 TASK 09 状态与 M6 进度。

## 实现摘要

- Stage 4 现在按 Skill Graph dependency 顺序执行全部 16 个节点。
- Gameplay 与 realization_eligible baseline（HUD）执行完整四重职责：
  - 约束识别
  - Design Space Discovery
  - Realization Candidate Generation
  - Convergence + Fragment Generation
- 当前 Discovery-capable 节点共 8 个：
  - 7 个 gameplay
  - 1 个 realization_eligible baseline（HUD）
- 每个 Discovery-capable 节点固定生成 3 个维度，因此最终产出：
  - 24 个 discovery dimensions
  - 24 组 candidate groups
  - 24 个 converged choices
- presence_only baseline 生成最小 Fragment，并在 assumptions 中记录 basis。
- clarification_gated / retained clarification 的 provisional 值会继续传到 Fragment 的 `design_decision_log`，当前已有 5 个 fragment 带 provisional 决策。
- Stage 4 总览 JSON 采用“per skill 合并”形式：
  - 顶层对象继续兼容现有 schema
  - 额外通过 `entries`、`lifecycle_records`、`final_status_map` 提供整批运行信息
- Stage 4 save 逻辑已扩展为多产物模式：
  - 逐个 JSON 使用对应 schema 校验
  - `skill_fragments/*.json` 使用 `skill_fragment_v2.schema.json` 批量校验

## 代表性产物

- Gameplay fragment（含 provisional 决策）：
  [skill-player-management.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/skill_fragments/skill-player-management.json)
- Presence-only baseline fragment（空 log + basis）：
  [skill-baseline-start-screen.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/skill_fragments/skill-baseline-start-screen.json)
- Realization-eligible baseline fragment（HUD，完整 Discovery -> Candidates -> Convergence）：
  [skill-baseline-hud.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-221500-a909/skill_fragments/skill-baseline-hud.json)

## 验证结果

语法验证：

```text
PY_COMPILE_OK
```

最终 run 保存验证：

```text
STAGE1_SAVE=saved
STAGE2_SAVE=saved
STAGE3_SAVE=saved
STAGE4_SAVE=saved
RUN_ID=run-20260415-221500-a909
FRAGMENT_FILES=16
DISCOVERY_ENTRY_COUNT=8
FINAL_STATUS_COUNT=16
PROVISIONAL_FRAGMENT_COUNT=5
HUD_FULL_FLOW=True
SETTINGS_EMPTY=True
CANDIDATE_GROUPS=24
CONVERGED_CHOICES=24
```

针对 TASK 09 验收项的定向检查：

```text
LOCKED_OK=True
CANDIDATE_OK=True
CONVERGED_OK=True
HUD_FULL_FLOW=True
PRESENCE_EMPTY_LOG=True
FAILED_COUNT=0
FRAGMENT_FILES=16
PROVISIONAL_FRAGMENT_COUNT=5
```

严格示例验证：

```text
Checked examples       : 19
Passed                 : 19
Failed                 : 0
Reference-only skipped : 0
Unmapped examples      : 0
Missing schema targets : 0

[SUCCESS] 全部 example 校验通过，本地校验链正常。
```

## 关键验收项

- `design_space_report.json` 非空：通过。
- `realization_candidates.json` 非空：通过。
- `converged_realization_pack.json` 非空：通过。
- `skill_fragments/*.json` 存在：通过，当前共 16 个。
- 每个运行过的 Skill Instance 都有 lifecycle status：通过，`final_status_map` 共 16 项，`lifecycle_records` 保留状态过程。
- failed 节点必须有 failure_reason：通过，当前 `FAILED_COUNT=0`。
- 每个 gameplay 与 realization_eligible baseline 节点均完成四重职责：通过，当前 Discovery-capable 节点共 8 个。
- Discovery 不是从固定枚举 options 里选择：通过，维度由节点职责 + Variant / Constraint 字段组合发现，并写入 `discovery_method`。
- `locked_dimensions` 与 Root Skill Contract Constraint Fields 一致：通过。
- 所有 realization candidate 满足 Variant bounds：通过，`CANDIDATE_OK=True`。
- Convergence 每个选择都有 rationale、rejected_alternatives、provisional：通过。
- 至少一个 gameplay fragment 的 `design_decision_log` 非空：通过，当前 7 个 gameplay fragment 全部非空。
- design_decision_log 不记录纯格式/命名选择：通过，当前记录内容均为布局、反馈、提示、身份表达等非平凡决策。
- presence_only baseline fragment 可为空 log，但必须说明 basis：通过。
- realization_eligible baseline 进入完整 Discovery -> Candidates -> Convergence：通过，HUD fragment 已验证。
- `validate_examples.py --strict` 通过：通过。

## 结论

TASK 09 当前范围已完成。Stage 4 已具备真实运行、聚合产物落盘和 Fragment v2 生成能力，后续可以进入 TASK 10：Cross Review v2、Build IR v2、naming_resolution_log、Handoff v3。
