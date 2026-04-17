# TASK 12 Phase 11 Run Governance Validation

## Summary

- `evidence_compare_runs` 已跑通，并生成结构化 comparison 产物。
- `evidence_create_batch` 已跑通，可从 promotable run 创建 batch。
- `evidence_promote_run` 已跑通，可创建 active batch 并更新治理层 baseline 指针。
- fast_mode run promote 已明确拒绝。
- failed run 的 `execution_log.json` 在拒绝 promote 后仍被保留。

## Evidence

- Compare 输出：[run_comparison.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task12_validation_outputs/run_comparison.json)
- Batch A manifest：[manifest.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/batch-20260417-001/manifest.json)
- Batch A report：[promotion_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/batch-20260417-001/promotion_report.json)
- Batch B manifest：[manifest.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/batch-20260417-002/manifest.json)
- Batch B report：[promotion_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/batch-20260417-002/promotion_report.json)
- active batch 指针：[active_batch.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/active_batch.json)
- current promoted 指针：[current_promoted_batch.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/current_promoted_batch.json)
- fast_mode fixture metadata：[metadata.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-230000-fa57/metadata.json)
- failed fixture execution_log：[execution_log.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-230100-fa58/execution_log.json)

## Checks

- comparison 六类差异字段齐全：`['constraint_differences', 'realization_differences', 'fragment_differences', 'build_ir_differences', 'naming_differences', 'provisional_changes']`
- Batch A active 状态：`False`
- Batch B active 状态：`True`
- 当前 active batch：`batch-20260417-002`
- 3 个治理工具可见：`True`
- promote 后原始 run A 仍存在：`True`
- promote 后原始 run B 仍存在：`True`
- fast_mode 拒绝错误：`PROMOTE_REJECTED: fast_mode run 不可 promote`
- failed run 拒绝错误：`PROMOTE_REJECTED: run 状态不是 completed，而是 failed`

## Notes

- 当前 `evidence_promote_run` 的 Base Project 更新采用治理层 baseline 指针方式，不直接回写 `Source/` 或 `Content/`。
- promote 后原始 run 目录未被删除。
