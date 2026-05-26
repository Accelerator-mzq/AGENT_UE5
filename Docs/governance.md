# Governance — 文档治理与 Agent 行为规则索引

> 版本: v1.0(2026-05-26)
> 关联 spec: `Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md` v1.1 §4.8
> 上游: 项目根 `AGENTS.md` §3 + `CLAUDE.md` + `.claude/skills/document-release/SKILL.md` + `Scripts/hooks/`
> 文档定位: **入口型文档**,本文不复述 `AGENTS.md` / `CLAUDE.md` 规则,只索引指向

---

## 1. 文档生产规则

### 1.1 document-release 强制门禁

任何 commit / push 触发前,git hooks(`Scripts/hooks/doc_release_gate.py`)联合 Claude Code / Codex 的 PreToolUse hook 一起,强制要求文档与代码改动同步释放:

- **pre-commit**:`Scripts/hooks/doc_release_gate.py check --action commit --trivial-only`(`.git/hooks/pre-commit`),只对 trivial 白名单做快速放行,非 trivial 文件留给 commit-msg 完整校验
- **commit-msg**:`Scripts/hooks/doc_release_gate.py check --action commit --commit-msg "$MSG"`(`.git/hooks/commit-msg`),检查 [skip-doc] 标记 / marker 文件 / 非 trivial 改动是否伴随文档同步
- **pre-push**:`.git/hooks/pre-push` 二次校验,阻拦无 marker 的非 trivial 改动被推送到远端
- **Claude Code / Codex PreToolUse**:`.claude/settings.json` + `.agents/settings.json` 的 PreToolUse hook 在 Edit/Write/Bash 类工具调用前做对应校验

完整契约见 `Docs/archive/superpowers/specs/2026-05-25-document-release-port-design.md`(已归档)与 `.claude/skills/document-release/SKILL.md`(权威源)。

### 1.2 三种逃生通道

非 trivial 改动若不需要 document-release 同步,**三选一**逃生(优先级从高到低):

1. **`[skip-doc]` commit message 标记**:在 commit message 开头加 `[skip-doc]`,doc_release_gate 跳过 marker 校验,但会写入 `ProjectState/Reports/<YYYY-MM-DD>/doc_release_skipped.log` 审计日志(`Scripts/hooks/doc_release_gate.py:222-229,302-306`)
2. **trivial 路径白名单**:`Scripts/hooks/doc_release_gate.py:171-175` 定义 `TRIVIAL_PREFIXES = ("Saved/", "Intermediate/", "DerivedDataCache/", "Binaries/", "Build/", ".codex/")` + `TRIVIAL_SUFFIXES = (".lock",)`,所有 staged 文件落入白名单 → 自动放行不写 marker
3. **`--no-verify`**(最末手段):仅在用户明确请求时使用;不写日志、不留审计痕迹,会被 AGENTS.md §3.8 视为违规

### 1.3 双路径 Skill 同步

`.claude/skills/document-release/SKILL.md` 与 `.agents/skills/document-release/SKILL.md` 是 Claude Code 与 Codex 的双前端 skill 入口,**内容必须一致**(由 `Scripts/sync_skills.py` 维护)。Skill 内容更新时双路径同步执行,任何单边修改在 SHA inline 校验时会被发现。

---

## 2. 文档信任分层

| 层 | 性质 | 路径示例 | 何时引用 |
|----|------|---------|---------|
| L0 | 项目根 anchor(不动) | `README.md` / `AGENTS.md` / `CLAUDE.md` / `task.md` | 入口规则,所有 Agent 必读 |
| L1 | 当前权威(本次重组主体) | `Docs/{INDEX,FEATURE_INVENTORY,governance}.md` + `Docs/{requirements,design,testing,acceptance,contracts}/*` | 五件套等价物 + 契约 + 索引 |
| L2 | Canonical 契约 | `Plugins/AgentBridge/Schemas/*` + `Plugins/AgentBridge/MCP/tool_definitions.py` | 机器可读契约源,代码即权威 |
| L3 | Phase 历史 | `Docs/archive/history/Tasks/*` + `archive/history/Phase11_Design_Pack/*` | 追溯历史决策 |
| L4 | 旧文档 archive | `Docs/archive/{current,decisions,proposals,superpowers,plugins}/*` | 反向映射目标,链路追溯 |
| L5 | Evidence | `ProjectState/Reports/<date>/*` + `ProjectState/Evidence/<run_id>/*` | 验收证据,不直接消化进 L1 |

**冲突解决规则**:L2(代码) > L1(文档) > L3-L5(历史)。文档与代码不一致时,以代码为准并修订 L1。

---

## 3. 阶段切换信号

- Phase 切换由 `task.md` 顶层重定向 + `Docs/INDEX.md`(原 <code>Docs/Current/00&#95;Index.md</code>,本次重组后归 `Docs/INDEX.md`)同步更新触发
- Phase 收尾产物归档到 `Docs/archive/current/` 或 `Docs/archive/history/`,同时在 `Docs/archive/README.md` 反向映射表登记
- 新 Phase 启动:更新 `task.md` 入口 + 创建对应 Phase 子目录(若需)+ 在 INDEX 加跳转
- Phase 切换时,inventory CSV(`Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv`)新增对应行,标 `archive-only` 或 `need-consume`

---

## 4. Agent 行为规则索引(链回不复述)

完整规则见对应文档,本节只列索引锚点:

| 主题 | 权威源 |
|------|--------|
| 项目级 Agent 规则 | `AGENTS.md` 全文 |
| Claude Code 私有规则 | `CLAUDE.md` 全文 |
| Codex 私有规则 | `.codex/AGENTS.md`(若有) |
| 中文回复偏好 | `~/.claude/CLAUDE.md`(用户全局) |
| 绝对不修改文件清单 | `CLAUDE.md` §"绝对不要修改的文件" |
| 项目外写入限制 | `CLAUDE.md` §"项目外写入限制" |
| document-release 收尾流程 | `AGENTS.md` §3.8 |
| L1/L2/L3 工具协议 | `Docs/contracts/tool_contract.md` §1-§6 |
| 字段命名规范 | `Docs/contracts/field_specification.md` §1-§4 |

**关键原则**(摘自 AGENTS.md / CLAUDE.md,不复述细则):
- Agent 必须读 `AGENTS.md` + `CLAUDE.md` + `task.md` + `Docs/INDEX.md` 后再开始任何写操作
- 项目内写入仅限 `D:\UnrealProjects\Mvpv4TestCodex\` 子树;项目外路径默认只读
- 非 trivial 改动必须走 `superpowers:document-release` skill 或显式 [skip-doc]

---

## 5. Git Hooks 一览

完整脚本见 `Scripts/hooks/`,本节只列入口:

| Hook | 触发时机 | 脚本路径 | 关键逻辑 |
|------|---------|---------|---------|
| pre-commit | `git commit` 前 | `Scripts/hooks/doc_release_gate.py check --action commit --trivial-only` | trivial 白名单快速放行 |
| commit-msg | `git commit` 写 message 时 | `Scripts/hooks/doc_release_gate.py check --action commit --commit-msg` | [skip-doc] 标记 / marker 校验 |
| pre-push | `git push` 前 | `Scripts/hooks/doc_release_gate.py check --action push` | 远端推送前二次校验 |

**Hook 安装**:`python Scripts/hooks/install_git_hooks.py`(F-HOOK-02)从 `Scripts/hooks/templates/` 复制 3 个 hook 到 `.git/hooks/`,确保跨开发者环境一致。

**Claude Code 通知**:`Scripts/hooks/cc_notify_wrapper.py` 是 Claude Code 通知 hook 的包装器,用于在文档释放门禁触发时给 Claude Code 发通知。

---

## 6. 项目根目录的 anchor 文件契约

项目根 4 个 anchor 文件**不参与本次文档重组**,只更新内容引用:

| 文件 | 角色 | 不可改的边界 |
|------|------|-------------|
| `README.md` | 项目对外简介 | 顶层 ≤ 5 段;不引入 Phase 编号细节 |
| `AGENTS.md` | Agent 行为规则 | §1-§3 框架不动,只在 §3.8/§4 等增量章节内更新 |
| `CLAUDE.md` | Claude Code 私有规则 | 用户配置区段(代码风格 / 反馈偏好)不动 |
| `task.md` | 当前阶段唯一开发驱动入口 | Phase 收尾时切换为跳转页;新 Phase 启动后切回正式任务书 |

四个 anchor 内的硬编码路径(如 <code>Docs/Current/00&#95;Index.md</code> → `Docs/INDEX.md`、<code>Docs/Current/05&#95;Implementation&#95;Boundary.md</code> → `Docs/requirements/SRS.md#6.5`)在 Phase 4(链接重写)统一更新;Phase 4 已实地化(2026-05-26)。

---

## 关联文档

- 上游入口:`AGENTS.md` / `CLAUDE.md` / `README.md` / `task.md`(项目根 4 anchor)
- 文档体系:`Docs/INDEX.md`(Task 1.19 落地)/ `Docs/FEATURE_INVENTORY.md`
- 治理 hook:`Scripts/hooks/{doc_release_gate,install_git_hooks,cc_notify_wrapper}.py`
- Skill 源:`.claude/skills/document-release/SKILL.md` + `.agents/skills/document-release/SKILL.md`(`Scripts/sync_skills.py` 同步)
- 历史:`Docs/archive/decisions/ADR-001-Doc-Governance.md` + `ADR-002-Task-And-Evidence-Archiving.md`(原 `Docs/Decisions/` 归档)
