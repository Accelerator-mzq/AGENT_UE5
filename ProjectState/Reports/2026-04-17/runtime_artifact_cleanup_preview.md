# 运行产物治理预览

## 1. 已执行且未删除文件的动作

本次仅完成 `.gitignore` 调整，没有执行任何删除操作。

已调整的规则目标：

1. 将根级 `reports/` 改为仅忽略仓库根目录下的 `/reports/`，避免误伤 `ProjectState/Reports/` 正式证据。
2. 新增忽略运行工作区目录：
   - `ProjectState/StagedBuilds/`
   - `ProjectState/batches/`
   - `ProjectState/runs/`
   - `ProjectState/phase11_task09_refactor_session/`

## 2. 当前 dry-run 结果

以下内容来自 `git clean -ndX` 预览，仅表示“如果执行清理，会删除这些忽略且未跟踪的本地文件/目录”，当前尚未执行：

- `ProjectState/StagedBuilds/`
- `ProjectState/batches/active_batch.json`
- `ProjectState/batches/batch-20260416-003/`
- `ProjectState/batches/batch-20260416-004/promoted_artifacts/`
- `ProjectState/batches/batch-20260416-004/promotion_report.json`
- `ProjectState/batches/batch-20260417-001/`
- `ProjectState/batches/batch-20260417-002/`
- `ProjectState/batches/current_promoted_batch.json`
- `ProjectState/phase11_task09_refactor_session/`
- `ProjectState/runs/run-20260415-100748-c290/`
- `ProjectState/runs/run-20260415-160606-a606/`
- `ProjectState/runs/run-20260415-180000-a701/`
- `ProjectState/runs/run-20260415-183000-a707/`
- `ProjectState/runs/run-20260415-191500-a707/`
- `ProjectState/runs/run-20260415-201500-a808/`
- `ProjectState/runs/run-20260415-202000-a808/`
- `ProjectState/runs/run-20260415-214500-a909/`
- `ProjectState/runs/run-20260415-221500-a909/`
- `ProjectState/runs/run-20260416-083303-d90b/`
- `ProjectState/runs/run-20260416-083508-1afe/`
- `ProjectState/runs/run-20260416-083638-92d3/`
- `ProjectState/runs/run-20260416-083716-1968/`
- `ProjectState/runs/run-20260416-085301-c9aa/`
- `ProjectState/runs/run-20260416-090933-95c2/`
- `ProjectState/runs/run-20260416-092018-f6b8/`
- `ProjectState/runs/run-20260416-141159-6cd1/`
- `ProjectState/runs/run-20260416-141416-69cc/`
- `ProjectState/runs/run-20260416-141449-80b3/`
- `ProjectState/runs/run-20260416-141502-7f49/`
- `ProjectState/runs/run-20260416-142558-7f47/`
- `ProjectState/runs/run-20260416-142757-47c4/`
- `ProjectState/runs/run-20260416-151230-24f6/`
- `ProjectState/runs/run-20260416-151231-75fa/`
- `ProjectState/runs/run-20260416-151328-a58b/`
- `ProjectState/runs/run-20260416-151329-eb4c/`
- `ProjectState/runs/run-20260416-152245-6dba/clarification_gate_report.json`
- `ProjectState/runs/run-20260416-152245-6dba/converged_realization_pack.json`
- `ProjectState/runs/run-20260416-152245-6dba/design_space_report.json`
- `ProjectState/runs/run-20260416-152245-6dba/realization_candidates.json`
- `ProjectState/runs/run-20260416-152245-6dba/root_skill_contract.json`
- `ProjectState/runs/run-20260416-152245-6dba/session.json`
- `ProjectState/runs/run-20260416-152245-6dba/skill_fragments/`
- `ProjectState/runs/run-20260416-230000-fa57/`
- `ProjectState/runs/run-20260416-230100-fa58/`
- `ProjectState/runs/run-20260417-051425-aad0/`
- `ProjectState/runs/run-20260417-051436-b190/`
- `ProjectState/runs/run-20260417-051436-ee3d/`
- `ProjectState/runs/run-20260417-051444-a2b8/`
- `ProjectState/runs/task07-smoke/`

## 3. 文件系统规模快照

以下是对应目录在本地磁盘上的当前规模快照，仅用于帮助评估清理收益；它不等同于 `git clean` 实际会删除的精确文件数：

- `ProjectState/StagedBuilds/`：`63` 个文件，`63` 个目录
- `ProjectState/batches/`：`118` 个文件，`12` 个目录
- `ProjectState/runs/`：`519` 个文件，`97` 个目录
- `ProjectState/phase11_task09_refactor_session/`：`1` 个文件，`0` 个目录

## 4. 当前副作用与说明

由于此前 `.gitignore` 使用了过宽的 `reports/` 规则，`ProjectState/Reports/` 中大量历史未跟踪报告一直被隐藏。现在修正后，这些旧报告会重新出现在 `git status` 中。

这不是新增文件，也不是删除动作，只是忽略规则恢复为更精确后的正常暴露。

## 5. 后续建议

下一步建议二选一：

1. 只确认删除本报告第 2 节中列出的运行现场文件/目录。
2. 先补第二轮 `ProjectState/Reports/` 分级 ignore 规则，再决定是否清理历史报告噪音。

## 6. 第二轮 `ProjectState/Reports` 分级 ignore 已补充

本轮新增了局部规则文件：

- `ProjectState/Reports/.gitignore`

规则分为 4 组：

1. 整目录收敛早期历史日期目录：
   - `2026-04-01/`
   - `2026-04-02/`
   - `2026-04-05/`
   - `2026-04-06/`
   - `2026-04-11/`
2. 收敛 `ProjectState/Reports/` 根目录 loose 历史文件：
   - `git_phase8_checkpoint_to_1_0_20260405.md`
   - `phase8_execution_summary_20260405.md`
   - `phase8_hud_input_fix_20260405.md`
   - `phase8_m3_asset_generation_20260405.json`
   - `vscode_rc_info.json`
3. 收敛批跑/回放/诊断噪音：
   - `execution_report_*.json`
   - `phase6_runtime_*.json`
   - `phase7_jrpg_*.json`
   - `phase7_p1_round*_{governance_audit,summary}.json`
   - `phase7_p1_round*_pytest.xml`
   - `phase7_p1_stability_summary_*.json`
   - `stage4_*` 诊断 JSON
   - `llm_*` 诊断 Markdown
4. 收敛 2026-04-16 下几份重复验证产物：
   - `task10_validation_outputs/phase11_build_ir_v2.example.json`
   - `task10_validation_outputs/phase11_cross_review_report_v2.example.json`
   - `task10_validation_outputs/phase11_design_decision_log.example.json`
   - `task14a_baseline_domain_runtime_validation.md`
   - `task14a_ue_runtime_playability_validation.md`
   - `task14a_ue_smoke_test_log.md`

## 7. 第二轮规则生效后的可见结果

执行 `git status --short -- ProjectState/Reports .gitignore` 后，目前与本轮动作直接相关、仍然可见的条目只剩：

- `M .gitignore`
- `?? ProjectState/Reports/.gitignore`
- `?? ProjectState/Reports/2026-04-17/runtime_artifact_cleanup_preview.md`

说明第二轮规则已经把此前大量 `ProjectState/Reports` 历史噪音收敛下去了；当前没有执行任何删除动作。
