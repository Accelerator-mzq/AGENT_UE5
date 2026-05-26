# 文档发布门禁 document-release 跨平台移植设计

> 创建日期：2026-05-25
> 状态：Design / 待实施
> 适用平台：Claude Code · OpenCode (anomalyco/opencode) · Codex CLI · 任何使用本仓库的 git 客户端
> 关联工作流：Superpowers（brainstorming / writing-plans / executing-plans / verification-before-completion / finishing-a-development-branch）
> 来源：gstack 的 `document-release`（MIT）→ ForgeUE 的本地化版本（位于 `D:\ClaudeProject\ForgeUE_codex\.agents\skills\document-release\SKILL.md`）→ 本文档对 Mvpv4TestCodex 项目的本地化重写

---

## 1. 背景与目标

### 1.1 当前痛点
Mvpv4TestCodex 当前文档体系采用「项目层（`AGENTS.md` / `CLAUDE.md` / `task.md` / `Docs/Current/*`）+ 插件层（`Plugins/AgentBridge/Docs/*` / `Plugins/AgentBridge/Schemas/*`）+ 证据层（`ProjectState/Reports/<date>/`）」三段拓扑，文件数量已超过 50 份。每次新需求或行为变更涉及 5–10 份文档同步，依靠人或 AI 自觉记得，**漏改率高且难以审计**。

### 1.2 目标
1. 把 ForgeUE 的 `document-release` skill **本地化重写** 后落入本项目。
2. 让 skill 成为 Superpowers 收尾链的**强制门禁**：commit / push / merge 之前若没跑过它，应被拦下。
3. 同一套机制能在 **Claude Code · OpenCode (anomalyco/opencode) · Codex CLI** 三平台一致工作。
4. 提供 **逃生通道**，避免 trivial 改动（构建产物 / typo + skip 标记 / `--no-verify`）被无脑拦截。

### 1.3 非目标 / YAGNI
- 不实现 `audit.md` 草稿的自动生成脚本（ForgeUE 也没有；留 backlog）。
- 不集成 CI / GitHub Actions（目前无 CI 触发场景）。
- 不集成 Linear / Jira / 远程任务系统（本项目无对应外部系统）。
- 不修改 `Plugins/AgentBridge/` 内部 AGENTS.md 及通用框架规则（避免污染框架层）。
- 不引入 Node.js / Bun 作为强制依赖；OpenCode plugin 用 TypeScript 写但只 spawn Python 脚本，Python 是单一事实来源。

---

## 2. 架构总览

### 2.1 同心圆架构

```
┌─ 硬底座(跨平台、跨 IDE、跨 CLI 全生效) ─────────────────────────┐
│ .git/hooks/pre-commit & pre-push  →  Scripts/hooks/doc_release_gate.py │
└──────────────────────────────────────────────────────────────────┘
        ↑ 第二道闸:各平台早期拦截/提示(体验层,非安全层)
┌──────────────────────────────────────────────────────────────────┐
│ Claude Code: .claude/settings.json                                │
│   PreToolUse(Bash) git commit/push/merge → gate.py check          │
│   PreToolUse(Write|Edit) task.md / Closeout / Reports → 软提示    │
│                                                                    │
│ OpenCode:    .opencode/plugins/doc-release-gate.ts                │
│   tool.execute.before(bash) → spawn gate.py check                 │
│   tool.execute.before(write|edit) → 软提示                        │
│                                                                    │
│ Codex:       无平台 hook (Codex CLI 不支持)                        │
│   AGENTS.md 规则 + skill description 软引导                       │
│   硬约束完全由 git hook 兜底                                       │
└──────────────────────────────────────────────────────────────────┘
        ↑ skill 内容(单源 + 一处副本)
┌──────────────────────────────────────────────────────────────────┐
│ 主入口: .claude/skills/document-release/SKILL.md  (canonical)    │
│   • Claude Code 原生加载                                          │
│   • OpenCode 默认搜索路径已含,自动加载                            │
│                                                                    │
│ 副本:   .agents/skills/document-release/SKILL.md                  │
│   • Codex superpowers 插件加载                                    │
│   • OpenCode 兼容路径也覆盖                                        │
│                                                                    │
│ 同步:   Scripts/sync_skills.py                                    │
│   写时 SHA256 校验;gate.py check 顺便比对,不一致 BLOCK            │
└──────────────────────────────────────────────────────────────────┘
        ↑ 规则锚点
┌──────────────────────────────────────────────────────────────────┐
│ AGENTS.md (Codex + OpenCode 主读) + CLAUDE.md (Claude 主读)       │
│ 两份内容语义对齐:声明"任务收尾流程链"+"hook 已硬约束 commit/push" │
└──────────────────────────────────────────────────────────────────┘
```

### 2.2 文件落点总览

| 组件 | 路径 | git 追踪 | 角色 |
|---|---|---|---|
| skill 主入口 | `.claude/skills/document-release/SKILL.md` | ✅ | Canonical；Claude Code 原生 + OpenCode 兼容加载 |
| skill 副本 | `.agents/skills/document-release/SKILL.md` | ✅ | Codex 加载点；与主入口由同步脚本保持一致 |
| 同步脚本 | `Scripts/sync_skills.py` | ✅ | canonical → 副本同步与一致性校验 |
| 门禁脚本 | `Scripts/hooks/doc_release_gate.py` | ✅ | 跨平台 Python 入口；被三类 hook 共同调用 |
| Claude hook 配置 | `.claude/settings.json` | ✅ | PreToolUse(Bash) + PreToolUse(Write\|Edit) |
| OpenCode plugin | `.opencode/plugins/doc-release-gate.ts` | ✅ | `tool.execute.before` 事件回调 |
| git pre-commit | `.git/hooks/pre-commit` | ❌（git 不追踪 hook） | 由安装脚本部署，调 gate.py |
| git pre-push | `.git/hooks/pre-push` | ❌ | 同上 |
| hook 安装器 | `Scripts/hooks/install_git_hooks.py` | ✅ | 把 pre-commit / pre-push 复制/链接进 `.git/hooks/` |
| marker | `ProjectState/RuntimeConfigs/doc-release-markers/<branch>.json` | ❌（必须 .gitignore） | 记录最近一次合格运行 |
| 审计报告 | `ProjectState/Reports/<YYYY-MM-DD>/document_release_audit.md` | ✅ | skill 每次运行产物，证据用 |
| 跳过日志 | `ProjectState/Reports/<YYYY-MM-DD>/doc_release_skipped.log` | ✅ | 逃生通道使用记录 |
| 项目规则 anchor | `AGENTS.md` §3.8 新增 / `CLAUDE.md` 新增"任务收尾流程" | ✅ | B 层软约束 |

### 2.3 关键设计决策记录
1. **Python 单一事实来源**：所有平台的 hook 最终都 spawn `Scripts/hooks/doc_release_gate.py`；OpenCode 的 TS plugin 是壳，不复制逻辑。理由：本项目已全栈 Python（`pytest.ini`），跨平台、易测试，避免 TS/PS/JS 多语言重复实现。
2. **canonical 路径选 `.claude/skills/`**：因为 OpenCode 已主动兼容这条路径，相当于一份内容覆盖两个平台。Codex 那一份用同步脚本生成。
3. **git hook 是唯一硬约束**：Codex CLI 不支持 PreToolUse 类拦截，平台 hook 不能在 Codex 上生效；只有 git hook 与编辑器/agent 无关，是真正的安全底座。
4. **marker 落在 `ProjectState/RuntimeConfigs/`**：该目录语义就是「运行时配置」，本项目已存在；不污染源码区，不入 git。
5. **审计证据落 `ProjectState/Reports/<date>/`**：该目录已是本项目所有阶段验收 / 覆盖报告的官方落点，与 ForgeUE 的 `demo_artifacts/<date>/` 同位。

---

## 3. 文档拓扑映射

skill 内部用以下四层映射替换 ForgeUE 源 skill 的「五件套 + contracts + backlog」。

### Layer A — 项目级入口与治理

| Surface | Path | Role |
|---|---|---|
| 用户入口 | `README.md` | 项目概述、快速入口、文档导航 |
| Codex/OpenCode 规则 | `AGENTS.md` | 项目级 Agent 规则（与 CLAUDE.md 语义对齐） |
| Claude 规则 | `CLAUDE.md` | Claude Code 项目规则 |
| 当前阶段入口 | `task.md` | 当前阶段任务书或归档跳转页 |
| 当前阶段索引 | `Docs/Current/00_Index.md` | 阶段文档总索引 |

### Layer B — 当前阶段事实

| 源 skill 概念 | 本项目落点 | 备注 |
|---|---|---|
| `SRS.md` 顶层需求 | `Docs/Current/01_Project_Baseline.md` + `Docs/Current/02_Current_Phase_Goals.md` | 双文件：基线 + 阶段目标 |
| `HLD/LLD` 设计 | `Plugins/AgentBridge/Docs/architecture_overview.md` + 9 份 Phase 11 框架规范文档 | 插件层 canonical |
| `test_spec.md` | `Plugins/AgentBridge/Tests/SystemTestCases.md` | 系统测试用例总表 |
| `acceptance_report.md` | `ProjectState/Reports/<date>/*acceptance*.md` | 按阶段生成 |
| `CHANGELOG.md` | `Docs/Current/0X_Closeout.md`（按阶段递增） | 本项目无独立 CHANGELOG；Closeout 充当增量记录 |
| `backlog/active` + `archived` | `Docs/Current/03_Active_Backlog.md` + `04_Open_Risks.md`；归档进 `Docs/History/Tasks/`、`Docs/Current/0X_Closeout.md` | 不建独立 archived 文件 |
| `INDEX.md` | `Docs/Current/00_Index.md` | 已有 |
| 实施边界 | `Docs/Current/05_Implementation_Boundary.md` | 本项目特有，必审 |

### Layer C — 插件层框架（行为变更时必审）

| Surface | Path | Role |
|---|---|---|
| 插件入口 | `Plugins/AgentBridge/README.md` | 框架定义 |
| 通用 Agent 规则 | `Plugins/AgentBridge/AGENTS.md` | 与项目级 AGENTS.md 互补；**document-release 默认不修改它** |
| 框架文档 | `Plugins/AgentBridge/Docs/*.md` | tool contract / field spec / feedback / 9 份 Phase 11 规范 |
| Schema 契约 | `Plugins/AgentBridge/Schemas/*.json` | 等同于 ForgeUE 的 `docs/contracts/**` |
| 系统测试 | `Plugins/AgentBridge/Tests/SystemTestCases.md` + `Plugins/AgentBridge/Tests/run_system_tests.py` | 测试登记 |

### Layer D — 证据 / 历史（read-only by default）

| Surface | Path | Role |
|---|---|---|
| 阶段证据 | `ProjectState/Reports/<YYYY-MM-DD>/` | 等同 `demo_artifacts/<date>/` |
| 运行证据 | `ProjectState/Evidence/`、`Handoffs/`、`runs/`、`Snapshots/` | 阶段产物 |
| 历史归档 | `Docs/History/**` | 只读，不重写 |
| 决策记录 | `Docs/Decisions/`（如有） | 决策追溯 |

### Coverage Map 模板

skill 每次运行必须输出此表，并写入 `ProjectState/Reports/<today>/document_release_audit.md`：

```text
变更点                          A 入口  B 阶段事实  C 框架  D 证据落盘
<新增/变更的能力或概念>         path    path        path    path/none
```

判定规则：
- 零覆盖 = critical gap，必须补
- 只有 A / D 没有 B / C = doc debt，强烈建议补
- D 缺失但 A/B/C 齐全 = 评审性变更，可记录在 audit.md 末尾

### audit.md 文件结构约定

`ProjectState/Reports/<today>/document_release_audit.md` 是 skill 最终产物，也是 `gate.py write-marker` 写 marker 前会强制校验的证据文件。**必须包含**以下两个 H2 区块（缺一即拒绝写 marker）：

```markdown
# Document Release Audit — <branch> @ <HEAD short SHA>

> 运行时间: <ISO 8601>
> 比较基准: <merge-base>
> 触发事件: <commit / push / merge / manual>

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| <变更 1> | <path or NONE> | ... | ... | ... |

## Documentation health

- README.md: Updated / Current / Needs user decision — <detail>
- AGENTS.md: ...
- CLAUDE.md: ...
- Layer B (Docs/Current 五件套等价): ...
- Layer C (Plugins/AgentBridge/Docs + Schemas): ...
- Backlog (Docs/Current/03_Active_Backlog.md, 04_Open_Risks.md): ...
- ProjectState/Reports 落盘: ...
- Archive (Docs/History): Read-only — <detail>

## Skipped / deferred items

<可选; 列出 Ask first 的待决项与原因>
```

其余区块（如 Backlog 详细变更、跑过的命令清单）按需追加，但不是必填。

### 从源 skill 删除 / 改写的条款

| 源条款 | 本项目处理 |
|---|---|
| Codex Linear sync 全节 | **整段删除**；本项目无 Linear |
| `CHANGELOG.md` 编辑规则 | 替换为「Closeout 增量条目规则」 |
| `docs/contracts/**` 一对一 | 改为 `Plugins/AgentBridge/Schemas/` + `Plugins/AgentBridge/Docs/{tool_contract,field_specification,feedback_interface_catalog}.md` 双源 |
| `demo_artifacts/<date>/` | 替换为 `ProjectState/Reports/<date>/` |
| `docs/archive/**` | 替换为 `Docs/History/**` |

---

## 4. 触发流程与 hook 行为

### 4.1 主流程链（与平台无关）

```text
implementation / fix
 → superpowers:verification-before-completion          (实现已 verify)
 → document-release (本 skill)
   ① Preflight     git status / git merge-base HEAD origin/main / git diff <base>...HEAD --stat
   ② Coverage Map  扫描新增/变更的能力,填 A/B/C/D 四层覆盖矩阵
   ③ Audit         按 Layer A→D 顺序 audit,标 Auto-update / Ask first
   ④ Backlog       检查 Docs/Current/03_Active_Backlog.md + 04_Open_Risks.md
   ⑤ Apply         小补丁多步;不删历史;不动 CLAUDE.md §"绝对不要修改的文件"清单
   ⑥ Verify        grep 旧路径/旧概念;必要时跑 pytest -q
   ⑦ Final report  写 ProjectState/Reports/<today>/document_release_audit.md,
                  调 gate.py write-marker 落 marker
 → superpowers:verification-before-completion          (对 doc 改动再 verify)
 → superpowers:finishing-a-development-branch         (merge / push)
```

### 4.2 hook 行为矩阵（各平台与 git 底座）

| 层 | 平台 / 入口 | 触发条件 | 行为 | 拦截方式 |
|---|---|---|---|---|
| 平台 | Claude Code: `PreToolUse(Bash)` | 命令匹配 `^\s*git\s+(commit\|push\|merge)\b` | spawn `gate.py check --action=<commit\|push\|merge>` | 脚本 exit 非零 → hook 返回阻塞 |
| 平台 | Claude Code: `PreToolUse(Write\|Edit)` | 写入路径匹配 `task.md` / `Docs/Current/*_Closeout.md` / `ProjectState/Reports/**` | spawn `gate.py notify --path=<path>` | 永不阻塞，仅 stderr 提示 |
| 平台 | OpenCode: `tool.execute.before(bash)` | `input.tool === "bash"` 且 command 匹配同上正则 | spawn `gate.py check` | plugin 抛错 → tool 调用失败 |
| 平台 | OpenCode: `tool.execute.before(write\|edit)` | 路径匹配同 Claude | spawn `gate.py notify` | 不阻塞 |
| 平台 | Codex CLI | **不可用** | — | — |
| 底座 | `.git/hooks/pre-commit` | 任意 `git commit` 调用 | spawn `gate.py check --action=commit` | 脚本 exit 非零 → commit 被 git 自身阻塞 |
| 底座 | `.git/hooks/pre-push` | 任意 `git push` 调用 | spawn `gate.py check --action=push` | 同上 |

**结论**：
- Claude Code / OpenCode 用户走的是「平台 hook（早提示）+ git hook（兜底）」双闸；
- Codex 用户走的是「AGENTS.md 规则 + skill description（软引导）+ git hook（兜底）」单闸；
- 直接命令行 git 用户也被 git hook 保护。
- 任何客户端都不存在「绕过」路径，除非走逃生通道（§4.4）。

### 4.3 `gate.py check` 内部判断

```text
1. 读取当前 branch / HEAD SHA / staged-files 列表(commit/push 上下文取 staged or HEAD..HEAD~1)
2. 计算 staged_files_hash = sha256(sorted(staged_paths) || "\n" || sorted(diff stats))
3. 检查 skill 主入口与副本 SHA256 是否一致:
     - 主入口 .claude/skills/document-release/SKILL.md 必须存在;不存在 → BLOCK,要求安装
     - 副本 .agents/skills/document-release/SKILL.md:
         · 存在但内容不一致 → BLOCK,要求跑 sync_skills.py
         · 不存在 → stderr 警告(Codex 用户将无法加载 skill),但不阻塞;
           write-marker 接口同时落一行警告到 doc_release_skipped.log
4. 读取 ProjectState/RuntimeConfigs/doc-release-markers/<branch>.json
5. 若 marker 不存在 → BLOCK
6. 若 marker.head_sha != HEAD 且 staged_files_hash != marker.staged_files_hash → BLOCK
7. 若 marker.timestamp 距今超过 24h → BLOCK(防止跨日陈旧 marker)
8. 若 marker.audit_evidence_path 指向的文件不存在 → BLOCK
9. 否则 PASS,return 0
```

注：步骤 3 中副本不存在不阻塞，是为了让纯 Claude Code 用户也能用门禁；但首次安装后正常状态应当是两份都存在且一致，sync_skills.py 是治理工具。

### 4.4 逃生通道（按强度排序）

| 通道 | 触发条件 | 行为 |
|---|---|---|
| **白名单 trivial** | staged diff **完全限定**在 `Saved/**` / `Intermediate/**` / `DerivedDataCache/**` / `Binaries/**` / `Build/**` / `.codex/**` / `*.lock` 任一组合内 | 自动 PASS，不写 marker，不记日志 |
| **`[skip-doc]` 标记** | commit message 首行包含 `[skip-doc]` | PASS + 在 `ProjectState/Reports/<today>/doc_release_skipped.log` 记一行 |
| **`--no-verify`** | 用户显式 `git commit --no-verify` 或 `git push --no-verify` | git 自身跳过 hook；gate.py 监听 reflog 在事后补写 `doc_release_skipped.log` |

**白名单不含 `*.md`**：文档 typo 修正也必须走 skill，因为 README/AGENTS/CLAUDE 的 typo 也可能涉及语义。真正 trivial 的 typo 应该用 `[skip-doc]`。

### 4.5 `gate.py write-marker` 接口

```text
入参:
  --branch=<current branch>
  --head=<HEAD sha>
  --staged-files-hash=<sha256>
  --evidence=ProjectState/Reports/<today>/document_release_audit.md
强制校验:
  1. evidence 文件必须存在
  2. evidence 必须包含 "## Coverage Map" 区块且非空
  3. evidence 必须包含 "## Documentation health" 区块且非空
  4. 这两项任一不满足 → 拒绝写 marker,exit 非零
```

**意义**：skill 必须真的填了 coverage map 和 health summary 才能放行——这是防止"假跑一次蒙混过关"的关键。Claude / OpenCode / Codex 都不能手动写 marker，只能通过这个接口。

### 4.6 规则锚点写入位置

- **`AGENTS.md` 新增 §3.8**（紧挨"§3 文档治理规则"）："任务收尾流程"小节，明文列出 4.1 的流程链，并声明 hook 已强制 commit / push。
- **`CLAUDE.md` 新增"任务收尾流程"小节**（位于"当前阶段"之前）：内容与 AGENTS.md 语义对齐。
- **`Plugins/AgentBridge/AGENTS.md` 不修改**——它是通用插件规则，不绑定项目级 hook。

---

## 5. Hard Boundaries

| Boundary | 本项目化说明 |
|---|---|
| 禁止文件删除 | 不跑 `rm -rf` / `Remove-Item -Recurse` / `git rm`；删除请求需用户明示 |
| 禁止重写历史 | `Docs/History/**`、`ProjectState/Reports/<past_date>/`（非今天的）只读 |
| 禁止改"绝对不要修改的文件" | 严格遵守 `CLAUDE.md` §"绝对不要修改的文件"清单（C++ 核心 / Bridge 客户端 / Orchestrator 核心 / 已稳定 Schema / 测试体系）——只 audit 不修改 |
| 禁止重写 `task.md` | task.md 当前是归档跳转页；阶段切换才允许重写，且必须先有 user 确认 |
| 禁止重写 Closeout | `Docs/Current/*_Closeout.md` 写入需要用户明示当前阶段已切换/收尾 |
| 禁止 version bump | 本项目无版本号工作流 |
| 禁止改 PR title / body | 同源 skill |
| 禁止硬编码测试计数 | 当前测试登记数（如 "240"）必须由命令实时输出，不固化进 doc |
| 禁止跨项目路径写入 | 严格遵守 `CLAUDE.md` "项目外写入限制"——`D:\UnrealProjects\Mvpv4TestCodex` 之外只读 |
| 不动 `Plugins/AgentBridge/AGENTS.md` | 插件通用规则，不被项目级 skill 修改 |
| 禁止重写 `CHANGELOG.md` | 本项目根目录不应出现 `CHANGELOG.md`；如外部脚本生成了也不允许由本 skill 改写 |

---

## 6. 跨平台落地矩阵

| 资产 | 文件 | Claude Code | OpenCode | Codex | git CLI 直接 |
|---|---|---|---|---|---|
| skill 主入口 | `.claude/skills/document-release/SKILL.md` | ✅ 原生 | ✅ 兼容 | — | — |
| skill 副本 | `.agents/skills/document-release/SKILL.md` | — | ✅ 兼容 | ✅ 原生 | — |
| Claude hooks | `.claude/settings.json` | ✅ | — | — | — |
| OpenCode plugin | `.opencode/plugins/doc-release-gate.ts` | — | ✅ | — | — |
| git hooks（底座） | `.git/hooks/pre-commit` + `pre-push` | ✅ | ✅ | ✅ | ✅ |
| gate 脚本 | `Scripts/hooks/doc_release_gate.py` | ✅ | ✅ | ✅ | ✅ |
| 项目规则 | `AGENTS.md` | 兜底读 | ✅ | ✅ | — |
| Claude 规则 | `CLAUDE.md` | ✅ | 兜底读 | — | — |
| skill 同步 | `Scripts/sync_skills.py` | — | — | — | 手动或由 pre-commit 顺带触发 |

**强约束层次**：
- Claude Code · OpenCode · git CLI 直接用户：**双闸**（平台 hook + git hook）
- Codex 用户：**单闸**（仅 git hook）— 受 Codex CLI 自身能力上限决定

---

## 7. 验证证据与落盘

### 7.1 git 追踪 vs `.gitignore`

实施时需在 `.gitignore` 增加：
```
# document-release marker(运行时状态,不入仓库)
ProjectState/RuntimeConfigs/doc-release-markers/
```
其他 `ProjectState/Reports/<date>/document_release_audit.md` 与 `doc_release_skipped.log` **追踪**（作为证据）。

### 7.2 实施完成后人工自检命令

```powershell
# 1. skill 主入口可被发现
python -c "import os; p='.claude/skills/document-release/SKILL.md'; print('OK' if os.path.exists(p) else 'MISSING')"

# 2. skill 副本与主入口一致
python Scripts/sync_skills.py --check

# 3. gate 脚本 dry-run
python Scripts/hooks/doc_release_gate.py check --action=commit --dry-run

# 4. marker 写入接口拒绝缺字段的 evidence
python Scripts/hooks/doc_release_gate.py write-marker --evidence=/dev/null  # 期望 exit 非零

# 5. trivial 白名单生效
python Scripts/hooks/doc_release_gate.py check --action=commit --simulate-staged="Saved/foo.tmp"  # 期望 exit 0

# 6. git hook 已安装
ls .git/hooks/pre-commit .git/hooks/pre-push

# 7. Claude settings hook 配置正确
python -c "import json; cfg=json.load(open('.claude/settings.json')); print('OK' if 'PreToolUse' in cfg.get('hooks',{}) else 'MISSING')"

# 8. OpenCode plugin 编译通过(若有 bun)
test -f .opencode/plugins/doc-release-gate.ts && echo OK
```

### 7.3 端到端 smoke test（每平台各跑一次）

```text
共同前置: 当前分支干净,无未跑过的 doc-release marker

T1. 修改 README.md 一句话
T2. 试 git commit -m "test: doc change"        → 期望: BLOCK + 提示跑 document-release
T3. 通过相应平台调用 document-release skill     → 期望: 在 ProjectState/Reports/<today>/ 出现 audit.md + marker 写入成功
T4. 重试 git commit                             → 期望: PASS
T5. 仅改 Saved/foo.tmp                          → 试 git commit
                                                → 期望: PASS(trivial 白名单)
T6. 修改 task.md                                → 期望: 平台 hook 软提示;Codex 无提示
T7. git commit -m "[skip-doc] WIP"              → 期望: PASS + skipped.log 多一行
T8. git commit --no-verify                       → 期望: PASS + skipped.log 多一行(事后补写)

按平台跑:
  Claude Code  跑 T1-T8 全部
  OpenCode     跑 T1-T8 全部
  Codex CLI    跳过 T6(无平台 hook); 其余跑
  git CLI 直接 跑 T2/T4/T5/T7/T8(无 skill 入口,T3 跳过)
```

### 7.4 已知非目标 / Backlog

- audit.md 自动生成脚本（方案 C 内容，留至 Backlog）
- CI 集成校验 marker（无 CI 触发）
- Linear / Jira / Codex 远程任务同步
- 自动渲染 Coverage Map 的图形界面

---

## 8. 实施输出清单（待 writing-plans 拆分）

下列为实施阶段需要交付的资产清单，**writing-plans skill 将基于此节产出详细实施计划**。本设计不规定步骤顺序与拆分粒度。

### 8.1 新增文件
1. `.claude/skills/document-release/SKILL.md`（canonical skill 内容）
2. `.agents/skills/document-release/SKILL.md`（由 sync 生成；首次手动）
3. `.claude/settings.json`（Claude hook 配置）
4. `.opencode/plugins/doc-release-gate.ts`（OpenCode plugin）
5. `Scripts/hooks/doc_release_gate.py`（核心 gate 脚本）
6. `Scripts/hooks/install_git_hooks.py`（git hook 安装器）
7. `Scripts/hooks/pre-commit`（被安装器复制到 `.git/hooks/`）
8. `Scripts/hooks/pre-push`（同上）
9. `Scripts/sync_skills.py`（skill 主入口 ↔ 副本一致性同步）

### 8.2 修改文件
1. `AGENTS.md` — 新增 §3.8 任务收尾流程
2. `CLAUDE.md` — 新增"任务收尾流程"小节
3. `.gitignore` — 增加 marker 目录忽略
4. `README.md` — 在 AI 工作流相关章节（如有）追加 document-release 角色说明；如无则跳过

### 8.3 不动文件（仅 audit）
- `Plugins/AgentBridge/AGENTS.md`
- `CLAUDE.md` §"绝对不要修改的文件"清单内的所有文件
- `Docs/History/**`
- `Docs/Current/*` 现有内容（除非任务确实变更其覆盖语义，由用户单独审批）

---

## 9. 来源与许可

本设计来源于：
1. gstack 项目的 `document-release` skill（MIT License）
2. ForgeUE_codex 项目的本地化版本（`D:\ClaudeProject\ForgeUE_codex\.agents\skills\document-release\SKILL.md`，约定继承 MIT）
3. 本文档对 Mvpv4TestCodex 项目的进一步本地化重写

最终交付的 SKILL.md 文件需在末尾保留 source note，链回上述两个上游来源。

---

## 10. 设计 review log

| 日期 | 评审人 | 结论 |
|---|---|---|
| 2026-05-25 | msc | §1 架构与文件落点 — 同意 |
| 2026-05-25 | msc | §2 文档拓扑映射 — 同意 |
| 2026-05-25 | msc | §3 触发流程与 hook 行为 — 同意 |
| 2026-05-25 | msc | §4 Hard Boundaries + §5 验证证据 — 同意（要求扩展跨平台） |
| 2026-05-25 | msc | §6 跨平台落地矩阵（Claude Code / OpenCode anomalyco / Codex 三平台 + git 底座） — 同意 |
