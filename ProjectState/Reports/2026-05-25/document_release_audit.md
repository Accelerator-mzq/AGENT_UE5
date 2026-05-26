# Document Release Audit — docs/phase11-doc-governance-cleanup @ 8ca1421

> 运行时间: 2026-05-25T16:03:00+00:00
> 比较基准: 84f00ab336ee51dc3204b101ed700286993690be (origin/main)
> 触发事件: manual (Task 12 首次正式 document-release)

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| document-release 跨平台门禁系统 | AGENTS.md §3.8 已加 / CLAUDE.md 任务收尾流程已加 / README.md 未改(留 backlog) / task.md 未改 / 00_Index.md 未改 | 03_Active_Backlog.md — 5 条 backlog 候选已记录于本 audit.md（待用户确认后写入） | 未涉及框架层 | ProjectState/Reports/2026-05-25/document_release_audit.md (本文件) + document_release_install_smoke_test.md + doc_release_skipped.log |

## Documentation health

- README.md: Needs user decision — 工作流章节未追加，留 backlog（document-release 门禁链说明）
- AGENTS.md: Updated — §3.8 任务收尾流程（document-release 规则锚点）
- CLAUDE.md: Updated — 任务收尾流程章节插入，包含 [skip-doc] 用法说明
- task.md: Current — 阶段未切换，无需重写
- Docs/Current/00_Index.md: Current — 阶段索引不变，本变更为工作流层改进
- Layer B (01_Project_Baseline.md / 02_Current_Phase_Goals.md): Current — 基线/阶段目标 unchanged，本变更是 Phase 11 之后的工作流改进
- Layer B Backlog (03_Active_Backlog.md): Needs user decision — 5 条 backlog 候选已在下方记录，待用户确认后写入 03_Active_Backlog.md
- Layer C (Plugins/AgentBridge/Docs + Schemas): Read-only — 本变更不动框架层
- ProjectState/Reports: Updated — 本 audit.md + document_release_install_smoke_test.md + doc_release_skipped.log（已存在）
- Archive (Docs/History): Read-only — 未触碰

## 跑过的命令清单

### Step 12.1 §7.2 自检

1. skill 主入口检查
   ```
   python -c "import os; p='.claude/skills/document-release/SKILL.md'; print('skill OK' if os.path.exists(p) else 'MISSING')"
   ```
   输出: `skill OK`  exit 0  → PASS

2. sync_skills --check
   ```
   python Scripts/sync_skills.py --check
   ```
   输出: (无 stderr，exit 0)  → PASS

3. check 无 marker → BLOCK
   ```
   python Scripts/hooks/doc_release_gate.py check --action commit --branch test --head abc --simulate-staged src/foo.py --dry-run
   ```
   输出: `[document-release gate] 阻止 commit: 原因: marker not found for branch test ...`  exit 2  → PASS

4. trivial 白名单 → PASS
   ```
   python Scripts/hooks/doc_release_gate.py check --action commit --branch test --head abc --simulate-staged Saved/foo.tmp --dry-run
   ```
   输出: (无输出，exit 0)  → PASS

5. write-marker 拒绝坏 evidence
   ```
   python Scripts/hooks/doc_release_gate.py write-marker --branch test --head abc --simulate-staged src/foo.py --evidence TestArtifacts/bad.md --dry-run
   ```
   输出: `[document-release] 拒绝写 marker: evidence 缺少必需区块: ## Coverage Map`  exit 2  → PASS

6. 全部单元测试
   ```
   python -m pytest Scripts/hooks/tests/ -v
   ```
   输出: 35 passed in 0.75s  exit 0  → PASS（实际 35 个，超过任务书记载的 28 个）

### Step 12.2 §7.3 端到端 Verify

```
python -c "import os; print('SKILL canonical:', os.path.exists('.claude/skills/document-release/SKILL.md')); ..."
```
- SKILL canonical: True
- SKILL mirror: True
- settings: True
- opencode plugin: True

```
python Scripts/sync_skills.py --check   # exit 0
python -m pytest Scripts/hooks/tests/ -q  # 35 passed
```

## Backlog 候选 (待用户确认后写入 03_Active_Backlog.md)

- **audit.md 自动生成器**: Task 12 后续。来源：spec §7.4 已知非目标。规模：中，可选 CI 集成。
- **cc_notify_wrapper.py 单元测试**: Task 8 review 提出的测试缺口。规模：小，3 个分支测试。
- **sync_skills.py 生产路径鲁棒性**: Task 5 review 发现 Path.cwd() 依赖，建议改 Path(__file__).parents[1] + 适配测试注入。规模：小。
- **README.md 工作流章节追加**: 当前 README 未提及 superpowers + document-release 门禁链，future 用户视角应当补一节。规模：小。
- **CI 集成校验 marker**: spec §7.4 已知非目标，留待 CI 启用后实施。规模：中。

## 评估

- 28 个 [skip-doc] commit 链中：全部用 [skip-doc] 放行，符合实施期约束
- 35 个单元测试 passed（任务书记录 28，实际增加至 35，全绿）
- git hook + 平台 hook 双闸已部署（pre-commit / pre-push / Claude Code PreToolUse / OpenCode tool.execute.before）
- skill 双路径（.claude / .agents）SHA 一致（sync_skills --check exit 0）
- 首次 marker 即将通过本 audit 写入

## Source

由 Task 12（`Docs/superpowers/plans/2026-05-25-document-release-port-implementation.md`）触发，作为门禁系统的首个正式 document-release 运行证据。
