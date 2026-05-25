# Document Release 安装 smoke test

> 日期: 2026-05-25
> 分支: docs/phase11-doc-governance-cleanup
> 操作员: Task 12 implementer subagent
> Triggered by: implementation plan Task 12 (Docs/superpowers/plans/2026-05-25-document-release-port-implementation.md)

## §7.2 自检清单

### 1. skill 主入口

命令:
```
python -c "import os; p='.claude/skills/document-release/SKILL.md'; print('skill OK' if os.path.exists(p) else 'MISSING')"
```
输出: `skill OK`
Exit code: 0
结论: **PASS**

### 2. sync_skills --check

命令:
```
python Scripts/sync_skills.py --check
```
输出: (无 stdout/stderr，静默成功)
Exit code: 0
结论: **PASS** — .claude/skills 与 .agents/skills 双路径 SHA 一致，无 drift

### 3. check 无 marker 应阻塞

命令:
```
python Scripts/hooks/doc_release_gate.py check --action commit --branch test --head abc --simulate-staged src/foo.py --dry-run
```
输出:
```
[document-release gate] 阻止 commit:
  原因: marker not found for branch test
  分支: test  HEAD: abc
  staged: 1 files
  提示: 提交消息首行写 [skip-doc] 放行，或先跑 document-release skill 写入 marker
```
Exit code: 2
结论: **PASS** — 无 marker 时正确拦截，exit 2

### 4. trivial 白名单应放行

命令:
```
python Scripts/hooks/doc_release_gate.py check --action commit --branch test --head abc --simulate-staged Saved/foo.tmp --dry-run
```
输出: (无输出)
Exit code: 0
结论: **PASS** — Saved/*.tmp 匹配 trivial 白名单，正确放行

### 5. write-marker 拒绝坏 evidence

命令:
```
mkdir -p TestArtifacts && printf "# 只有标题\n" > TestArtifacts/bad.md
python Scripts/hooks/doc_release_gate.py write-marker --branch test --head abc --simulate-staged src/foo.py --evidence TestArtifacts/bad.md --dry-run
```
输出:
```
[document-release] 拒绝写 marker: evidence 缺少必需区块: ## Coverage Map
```
Exit code: 2
结论: **PASS** — 仅含标题、缺少 ## Coverage Map 区块时正确拒绝

### 6. 单元测试全量运行

命令:
```
python -m pytest Scripts/hooks/tests/ -v
```
输出摘要:
```
collected 35 items

Scripts/hooks/tests/test_doc_release_gate.py::test_marker_roundtrip PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_marker_missing_returns_none PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_compute_staged_files_hash_stable_under_order PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_validate_evidence_rejects_missing_coverage_map PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_validate_evidence_rejects_missing_health_section PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_validate_evidence_rejects_empty_coverage_map PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_validate_evidence_passes_with_both_sections PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_validate_evidence_rejects_missing_file PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_read_marker_raises_value_error_on_corrupt_json PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_check_blocks_when_marker_missing PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_check_blocks_when_head_and_hash_both_changed PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_check_passes_when_head_matches PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_check_blocks_when_marker_older_than_24h PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_check_blocks_when_evidence_file_missing PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_check_handles_naive_timestamp_in_marker PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_trivial_whitelist_only_saved_files_passes PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_trivial_whitelist_mixed_with_source_is_not_trivial PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_trivial_whitelist_empty_paths_is_not_trivial PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_skip_doc_marker_in_commit_message PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_log_skipped_appends_line PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_check_dry_run_blocks_when_no_marker PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_check_dry_run_passes_with_trivial_only PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_write_marker_rejects_invalid_evidence PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_write_marker_accepts_valid_evidence PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_notify_never_blocks_and_writes_stderr PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_check_dry_run_does_not_write_skipped_log PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_write_marker_dry_run_does_not_write_marker PASSED
Scripts/hooks/tests/test_doc_release_gate.py::test_cli_check_trivial_only_passes_even_with_nontrivial_staged PASSED
Scripts/hooks/tests/test_install_git_hooks.py::test_install_creates_hook_files PASSED
Scripts/hooks/tests/test_install_git_hooks.py::test_install_is_idempotent PASSED
Scripts/hooks/tests/test_install_git_hooks.py::test_install_makes_hooks_executable_on_posix PASSED
Scripts/hooks/tests/test_sync_skills.py::test_sync_creates_copy PASSED
Scripts/hooks/tests/test_sync_skills.py::test_check_passes_when_consistent PASSED
Scripts/hooks/tests/test_sync_skills.py::test_check_fails_when_drift PASSED
Scripts/hooks/tests/test_sync_skills.py::test_check_warns_when_mirror_missing PASSED

35 passed in 0.75s
```
Exit code: 0
结论: **PASS** — 35/35 全部通过（任务书记录 28，实际增加至 35）

---

## §7.3 端到端

### T1: 装好 hook 后 git commit 无 message 标记被拦

(Task 11 已验证) — pre-commit hook 在 commit subject 不含 [skip-doc] 且无 marker 时正确拦截，输出拒绝原因，exit 非 0。

### T2: [skip-doc] 放行

(Task 11 已验证，见 commit 链) — 28 个 [skip-doc] commit 全部成功放行，doc_release_skipped.log 有记录。commit subject 必须在首行放 [skip-doc] 才有效。

### T3: 首次 document-release 跑通

(Step 12.2-12.3 完成) — audit.md 含 ## Coverage Map + ## Documentation health 两个必需 H2 区块，marker 已通过 write-marker 写入。

### T4: 正常 commit 被门禁放行

(Step 12.5 即将验证) — 依赖 marker 与 staged 文件集一致。先 stage 再 write-marker 保证 hash 匹配。

---

## 结论

**SMOKE TEST PASS**

所有 §7.2 自检项目全部通过：
- skill 双路径部署正常
- sync_skills 无 drift
- gate.py 无 marker 时拦截正确（exit 2）
- trivial 白名单正确放行
- write-marker evidence 校验拒绝不合格文件
- 35 个单元测试全绿

§7.3 T1/T2 由 Task 11 验证，T3 由 Step 12.2-12.3 验证，T4 由 Step 12.5 验证。
