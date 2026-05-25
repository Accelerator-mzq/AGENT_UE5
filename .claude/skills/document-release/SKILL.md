---
name: document-release
description: Use when Mvpv4TestCodex documentation must be synchronized as the mandatory release gate before git commit/push, including AGENTS, CLAUDE, README, task.md, Docs/Current 五件套等价物、Plugins/AgentBridge/Docs 框架文档、Schemas 契约、Docs/Current/03_Active_Backlog.md backlog、ProjectState/Reports 证据落盘和 Docs/History 归档引用。
license: MIT
compatibility: claude-code, opencode, codex
metadata:
  source: gstack(MIT) → ForgeUE/document-release → Mvpv4TestCodex
  spec: Docs/superpowers/specs/2026-05-25-document-release-port-design.md
---

# Document Release (Mvpv4TestCodex)

## Overview

本 skill 是 Mvpv4TestCodex 的发布门禁文档同步 skill。它把已验证的交付物事实同步到当前文档,把历史归档作为证据,把不确定的文档欠债显式暴露,而不是猜测。

`document-release` 是 Superpowers 收尾链的**强制门禁**:`git commit / push / merge` 之前必须跑过它(由 git pre-commit/pre-push hook 与 Claude/OpenCode 平台 hook 共同保证)。

## Hard Boundaries

- 不跑 `rm -rf` / `Remove-Item -Recurse` / `git rm`,任何删除请求需用户明示。
- `Docs/History/**` 与历史日期的 `ProjectState/Reports/<past_date>/` **只读**,不重写。
- 严格遵守 `CLAUDE.md` §"绝对不要修改的文件"清单(C++ 核心 / Bridge 客户端 / Orchestrator 核心 / 已稳定 Schema / 测试体系)——只 audit 不修改。
- `task.md` / `Docs/Current/*_Closeout.md` 默认只读;需要重写必须先得到用户明示当前已进入新阶段或正在收尾。
- 本项目无版本号工作流,不做 version bump。
- 不改 PR title / body。
- 不硬编码测试计数(如"240"),改由命令实时输出。
- 不跨项目目录写入(仅限 `D:\UnrealProjects\Mvpv4TestCodex` 及子目录)。
- 不修改 `Plugins/AgentBridge/AGENTS.md`(它是通用框架规则)。
- 本项目根目录不应存在 `CHANGELOG.md`;如外部脚本生成也不允许由本 skill 改写。

## When To Use

- 用户要求 update docs / sync documentation / 描述刚刚发生了什么变更
- 用户要求 add / complete / retire backlog 条目
- 改了需求 / 架构 / 测试 / 验收 / Bridge / Orchestrator / MCP / 工作流 / agent 规则
- 校验现有文档是否仍与代码 / 示例 / 测试 / 当前工作流一致
- 实现完一个特性 / 一次迁移后准备文档证据
- **任何会改变行为、backlog、当前文档、契约、测试、示例或验收证据的非小改动**

仅 typo / 注释 / 不影响行为的文档改动可跳过本 skill,但需 commit message 首行写 `[skip-doc]`。

## Mvpv4TestCodex Documentation Map

把"当前文档面"分为四层。每层都可能因变更而需要更新:

### Layer A — 项目级入口与治理
| Surface | Path | Role |
|---|---|---|
| 用户入口 | `README.md` | 项目概述、快速入口、文档导航 |
| Codex/OpenCode 规则 | `AGENTS.md` | 项目级 Agent 规则 |
| Claude 规则 | `CLAUDE.md` | Claude Code 项目规则 |
| 当前阶段入口 | `task.md` | 阶段任务书或归档跳转页 |
| 当前阶段索引 | `Docs/Current/00_Index.md` | 阶段文档总索引 |

### Layer B — 当前阶段事实
| 概念 | 本项目落点 |
|---|---|
| 需求基线 | `Docs/Current/01_Project_Baseline.md` + `02_Current_Phase_Goals.md` |
| 设计 | `Plugins/AgentBridge/Docs/*.md`(全部框架文档,随阶段递增) |
| 测试 | `Plugins/AgentBridge/Tests/SystemTestCases.md` |
| 验收 | `ProjectState/Reports/<date>/*acceptance*.md` |
| 增量(CHANGELOG 替代) | `Docs/Current/0X_Closeout.md` |
| Backlog active + archived | `Docs/Current/03_Active_Backlog.md` + `04_Open_Risks.md`;归档进 `Docs/History/Tasks/`、`0X_Closeout.md` |
| 实施边界 | `Docs/Current/05_Implementation_Boundary.md` |
| 架构 / MCP 锚定 | `Docs/Current/12_*` / `14_*` / `15_*` / `16_*` 与历代 `0X_Closeout.md`(随阶段演进,以 `00_Index.md` 为准) |

### Layer C — 插件层框架(行为变更时必审)
| Surface | Path |
|---|---|
| 插件入口 | `Plugins/AgentBridge/README.md` |
| 通用 Agent 规则 | `Plugins/AgentBridge/AGENTS.md`(只读) |
| 框架文档 | `Plugins/AgentBridge/Docs/*.md` |
| Schema 契约 | `Plugins/AgentBridge/Schemas/*.json` |
| 系统测试 | `Plugins/AgentBridge/Tests/SystemTestCases.md` |

### Layer D — 证据 / 历史(默认只读)
| Surface | Path |
|---|---|
| 阶段证据 | `ProjectState/Reports/<YYYY-MM-DD>/` |
| 运行证据 | `ProjectState/Evidence/`、`Handoffs/`、`runs/`、`Snapshots/` |
| 历史归档 | `Docs/History/**` |
| 决策记录 | `Docs/Decisions/`(如有) |

## Workflow

### Mandatory placement
```
implementation / fix
 → superpowers:verification-before-completion
 → document-release (本 skill)
 → superpowers:verification-before-completion
 → superpowers:finishing-a-development-branch
```

### Step 1: Preflight
```powershell
git branch --show-current
git status --short --branch
git merge-base HEAD origin/main
git diff <base>...HEAD --stat
git diff <base>...HEAD --name-only
git log <base>..HEAD --oneline
```
若 `origin/main` 不可用,依次回退到 `origin/master`、本地 `main`、近期 commits。在最终报告中标注实际 base。

### Step 2: Build coverage map
列出本次变更涉及的能力 / 配置 / 工具 / Schema / 工作流 / agent 规则。

填入表格:
```
变更点                          A 入口  B 阶段事实  C 框架  D 证据落盘
<变更的能力或概念>              path    path        path    path/none
```

零覆盖 = critical gap。只有 A/D 没有 B/C = doc debt。

### Step 3: Audit by layer
按 Layer A → B → C → D 顺序逐项审。每项标 Auto-update / Ask first。
- Auto-update: 已被代码/测试/已有文档证实的事实变更
- Ask first: 架构理由、移除区块、移动 backlog、产品语言含糊处

### Step 4: Backlog rules
- 新的延期工作 → 加到 `Docs/Current/03_Active_Backlog.md`
- 完成或被取代的条目 → 询问用户后移到 `Docs/History/Tasks/` 或写入 `0X_Closeout.md`
- 不静默删除 active 条目;不从 `Docs/History/` 重建 backlog

### Step 5: Apply safe updates
小补丁,多步;每改一个文件留一行 summary。

### Step 6: Verify
```powershell
# 旧路径/旧概念扫一遍
rg -n "<旧概念或旧路径>" README.md AGENTS.md CLAUDE.md Docs Plugins/AgentBridge/Docs -S

# 必要时跑 schema 校验或系统测试登记
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```
如果改动牵涉到测试/示例/契约,跑相应测试;否则注明"未跑测试,因 doc-only"。

### Step 7: Final report — 写 audit.md
**必须**写入 `ProjectState/Reports/<today>/document_release_audit.md`,且必须包含以下两个 H2 区块,否则 marker 写入接口会拒绝:

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
- Layer B: ...
- Layer C: ...
- Backlog: ...
- ProjectState/Reports: ...
- Archive: Read-only — <detail>
```

### Step 8: Write marker (强制)
最后一步必须调:
```powershell
python Scripts/hooks/doc_release_gate.py write-marker `
  --evidence ProjectState/Reports/<today>/document_release_audit.md
```
该接口会强制校验 audit.md 含上述两个 H2 区块;不合格则拒绝写 marker,从而阻塞后续 git commit/push。

## Common Mistakes

| Mistake | Fix |
|---|---|
| 只改 README,忘了 Layer B 五件套等价物 | 按 Layer A→B→C→D 顺序审 |
| 把 `Docs/History/**` 当作 current truth | History 是证据,改 current docs 而不是改 history |
| 忘 backlog | 检查 `Docs/Current/03_Active_Backlog.md` + `04_Open_Risks.md` |
| 编造或硬编码测试计数 | 跑命令实时取数 |
| 用删除命令清理 | 不删除,改由用户明示 |
| 改 `Plugins/AgentBridge/AGENTS.md` | 它是框架通用规则,不动 |

## Source Note

This skill is adapted from gstack's MIT-licensed `document-release` workflow (via ForgeUE_codex 项目的本地化),with Mvpv4TestCodex-specific documentation topology and safety boundaries.
