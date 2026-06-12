![1776348092078](image/AGENTS/1776348092078.png)# AGENTS.md — Mvpv4TestCodex 项目

> 目标引擎版本：UE5.5.4 | 文档版本：v1.7（Phase 14 任务书口径,2026-06-12）
>
> 本文件定义 **本项目** 的 AI Agent 行为规则。
> 通用的 AgentBridge 插件规则见 → `Plugins/AgentBridge/AGENTS.md`

---

## 1. 通用规则（引用）

本项目使用 AgentBridge 插件，Agent 必须遵守插件通用规则：

→ **`Plugins/AgentBridge/AGENTS.md`** — 包含核心规则、禁止模糊字段清单、工具使用规则（L1/L2/L3）、执行流程、读回验证规则、Spec 校验规则、报告规则、执行通道规则、能力边界

Agent 进入本项目后，应先阅读上述文件了解 AgentBridge 的完整行为框架。

---

## 2. 本项目特定规则

### 2.1 项目原则

- C++ 为主，Blueprint 为薄层（资产绑定、可视化拼装、数据配置、动画/UI 桥接）
- 编辑器是受控执行环境，不是可自由点击的 GUI
- 优先使用结构化工具调用
- 所有结果必须可验证、可审计
- 当前目标引擎版本为 UE5.5.4，所有能力描述基于此版本的真实 API

### 2.2 分层原则

本项目采用“项目层 + 插件层”双层架构：

| 层次 | 职责 | 位置 |
|------|------|------|
| **项目层** | 输入源、配置、实例、治理 | 工程根目录 |
| **插件层** | 通用编译、执行、验证框架 | `Plugins/AgentBridge/` |

**关键约束**：
- 项目层保存实例，插件层提供机制
- Compiler / Handoff / Orchestrator 主体在插件层，不在项目层
- 项目层通过 `ProjectInputs/Presets/` 提供配置，不重写框架逻辑

### 2.3 工具层级启用状态

| 工具层级 | 本项目状态 | 说明 |
|---------|-----------|------|
| L1 语义工具 | ✅ 启用 | 默认主干，所有 4 个写接口 + 7 个反馈接口 |
| L2 编辑器服务工具 | ✅ 启用 | 构建 / 测试 / 验证 |
| L3 UI 工具 | ✅ 启用 | 受约束使用，遵守插件 AGENTS.md §4.3 规则 |

### 2.4 本项目写操作范围

当前开发阶段的默认增删改范围仅限于项目根目录 `D:\UnrealProjects\Mvpv4TestCodex` 及其子目录。

- 项目目录内：允许按任务需要执行新增、删除、修改。
- 项目目录外：默认只允许读取、检查、收集信息；任何新增、删除、修改都必须先获得用户明确允许后才能执行。
- 如任务确实需要改动项目目录外路径，Agent 必须先说明目标路径、具体动作和原因，再等待用户确认。

### 2.5 聊天面板文件引用格式

- 在聊天面板中引用本地文件时，链接目标必须使用“以 `/` 开头的 Windows 本地绝对路径”，例如 `/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md#L1`
- 不要使用 `D:/...`、`d:/...` 或普通网页 URL 写法，否则 VS Code 聊天面板会把它当成浏览器链接。

### 2.6 附加文档路径

Agent 在本项目中需要参考的文档：

**项目层文档**：

| 文档 | 路径 |
|------|------|
| 当前阶段索引 | `Docs/INDEX.md` |
| Phase 11 收尾总览 | `Docs/acceptance/acceptance_report.md#1` |
| Phase 10 收尾总览 | `Docs/archive/current/17_Phase10_Closeout.md` |
| Phase 8 收尾总览 | `Docs/archive/current/10_Phase8_Closeout.md` |
| 项目基线 | `Docs/requirements/SRS.md#1` |
| 当前阶段目标 | `Docs/acceptance/acceptance_report.md#1` |
| 实施边界 | `Docs/requirements/SRS.md#6.5` |
| 当前阶段任务 | 根目录 `task.md`（当前为 Phase 14 Demo-First 增量主链任务书,已完成） |
| Phase 14 设计 spec | `Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md` |
| Phase 14 验收 runbook | `ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md` |
| Phase 13 设计 spec | `Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md` |
| Phase 13 验收 runbook | `ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md` |
| Phase 11 历史任务 | `Docs/archive/history/Tasks/task11_phase11.md` |
| MCP 总口径锚定 | `Docs/design/HLD.md#4` |
| 四层主链定义 | `Docs/requirements/SRS.md#4` |
| MCP 重定位方案 | `Docs/design/HLD.md#4` |
| Phase 9 MCP 实施方案归档 | `Docs/archive/history/Proposals/Phase9_MCP_Implementation_Plan.md` |
| Phase 8 历史任务 | `Docs/archive/history/Tasks/task8_phase8.md` |
| Phase 8 统一方案 | `Docs/archive/history/Proposals/Phase8_Plan_Original.md` |
| Phase 8 交接文档 | `Docs/archive/history/Proposals/Phase8_M3_Handover_to_Execution_Agent.md` |
| Phase 8 DD-1 | `Docs/archive/history/Proposals/Phase8_DD1_Schema_and_Interface_Spec.md` |
| Phase 8 DD-3 | `Docs/archive/history/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md` |

**插件层文档**：

| 文档 | 路径 |
|------|------|
| 插件说明 | `Plugins/AgentBridge/README.md` |
| 通用 Agent 规则 | `Plugins/AgentBridge/AGENTS.md` |
| 总体架构 | `Docs/design/HLD.md#1-2` |
| 工具契约 | `Docs/contracts/tool_contract.md` |
| 字段规范 | `Docs/contracts/field_specification.md` |
| 反馈接口清单 | `Docs/requirements/SRS.md#3.2` |
| Compiler 框架（旧） | `Plugins/AgentBridge/Scripts/compiler/` |
| Compiler 骨架（Phase 8） | `Plugins/AgentBridge/Compiler/` |
| Skill Template Pack | `Plugins/AgentBridge/SkillTemplates/` |
| MCP Server | `Plugins/AgentBridge/MCP/` |
| Handoff Schema v1 | `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json` |
| Handoff Schema v2 | `Plugins/AgentBridge/Schemas/reviewed_handoff_v2.schema.json` |
| Phase 8 新增 Schema | `Plugins/AgentBridge/Schemas/{gdd_projection,planner_output,skill_fragment,cross_review_report,build_ir}.schema.json` |
| Run Plan Schema | `Plugins/AgentBridge/Schemas/run_plan.schema.json` |
| Phase 11 框架规范 | `Plugins/AgentBridge/Docs/` 下 8 份新文档（详见 `Docs/INDEX.md`） |
| Phase 11 设计包归档 | `Docs/History/Phase11_Design_Pack/`（16 份原始设计文档） |
| 系统测试用例总表 | `Plugins/AgentBridge/Tests/SystemTestCases.md` |
| 系统测试入口 | `Plugins/AgentBridge/Tests/run_system_tests.py` |

---

## 3. 文档治理规则

### 3.1 文档分层

本项目文档分为三个信任层级：

- **L0 入口 + L1 当前生效**（`AGENTS.md` / `Docs/Current/`）：当前项目口径
- **L2 Canonical**（`Plugins/AgentBridge/` 下 Docs / Schemas / Specs / Scripts/compiler/）：长期框架规范
- **L3–L5**（`Docs/History/` / `Decisions/` / `Proposals/`）：按需参考，不作为默认依据

### 3.2 阅读顺序

Agent 进入本项目后，按以下顺序阅读：

1. `AGENTS.md`（本文件）— 规则和导航
2. `Docs/INDEX.md` — 当前阶段索引
3. `Docs/design/HLD.md#4` — MCP 总口径（优先裁决依据）
4. `Docs/requirements/SRS.md#4` — 四层主链定义
5. `Docs/design/HLD.md#4` — MCP 重定位方案
6. `Docs/acceptance/acceptance_report.md#1` — Phase 11 收尾总览
7. `Docs/requirements/SRS.md#1` — 项目基线
8. `Docs/acceptance/acceptance_report.md#1` — 阶段目标与完成状态
9. `Docs/requirements/SRS.md#6.5` — 实施边界
10. 根目录 `task.md` — 当前入口页；若下一阶段尚未建立，则这里是归档跳转页
11. `Plugins/AgentBridge/README.md` — 插件定义（首次进入必读）
12. `Plugins/AgentBridge/AGENTS.md` — 通用 Agent 规则（首次进入必读）
13. `Docs/archive/current/17_Phase10_Closeout.md` — 需要追溯 Phase 10 收尾事实时阅读
14. `Docs/archive/history/Tasks/task8_phase8.md` — 需要追溯 Phase 8 历史任务时阅读
15. `Docs/archive/history/Proposals/Phase9_MCP_Implementation_Plan.md` — 需要追溯 Phase 9 实施前方案时阅读
16. 与当前任务相关的 `Docs/Current/*` 和 `Plugins/AgentBridge/Docs/*`

步骤 1–10 为必读。步骤 11–12 首次进入必读，后续按需复查。步骤 13–15 仅在追溯历史任务或实施前方案时阅读。

### 3.3 文档权威优先级

1. `Docs/Current/*`（最高——当前项目基线）
2. `Plugins/AgentBridge/Docs/*`（长期框架真相）
3. `Docs/Decisions/*`（决策背景）
4. `Docs/Proposals/*`（候选方案）
5. `Docs/History/*`（历史追溯）

如果历史文档与当前文档冲突，以当前文档为准。

### 3.4 读取禁止行为

Agent 默认不得：

- 扫描整个 `Docs/History/` 作为背景输入
- 将 `Docs/Proposals/` 中未批准的草案当作正式规则
- 将历史阶段的待办事项直接作为当前任务执行
- 混合引用不同阶段的结论而不标注来源

### 3.5 写入规则

Agent 不得：

- 在项目根任意新增并列的“总设计文档”
- 在未更新 `Docs/Current/` 基线前，直接把临时设计写进 `Plugins/AgentBridge/Docs/`
- 将阶段性的计划或任务写进插件 canonical 目录
- 把未经评审的设计直接写入 `Docs/requirements/SRS.md#1`

新增能力的文档归属：

- 项目阶段相关的结论 → `Docs/Current/`
- 框架级的接口 / 规范变更 → `Plugins/AgentBridge/Docs/`（须与插件版本升级同步）
- 未定稿的设计提案 → `Docs/Proposals/`
- 关键决策记录 → `Docs/Decisions/`

### 3.6 阶段切换

当 Agent 检测到以下信号时，视为发生了阶段切换：

- `Docs/INDEX.md` 中的阶段名称变更
- 当前阶段任务清单被归档并创建新清单
- 被明确告知进入新阶段

阶段切换后，必须重新完整阅读步骤 1–6 的全部文件，不可依赖上一期的缓存记忆。

### 3.7 附加说明

- `Plugins/AgentBridge/Roadmap/Archive/` 下的内容为历史开发计划，不作为当前开发依据
- 框架级设计文档主要位于插件内部；阶段设计、交接和历史任务文档位于项目层 `Docs/History/`
- 根目录 `MCP实现方案.md` 已归档为 `Docs/archive/history/Proposals/Phase9_MCP_Implementation_Plan.md`
- 根目录 `task_temp.md` 已删除，不再作为任何阶段的正式入口

### 3.8 任务收尾流程

非 trivial 改动(改变行为 / backlog / 当前文档 / 契约 / 测试 / 示例 / 验收证据)必须按以下链条收尾:

```
implementation / fix
 → superpowers:verification-before-completion
 → document-release  (Mvpv4TestCodex 本地 skill)
 → superpowers:verification-before-completion (对 doc 改动再 verify)
 → superpowers:finishing-a-development-branch (merge / push)
```

`document-release` 是**强制门禁**:`git commit / push / merge` 之前必须跑过它,否则 git pre-commit/pre-push hook 以及 Claude Code / OpenCode 平台 hook 会拦下来。逃生通道:

- staged 文件全部落在 `Saved/` / `Intermediate/` / `DerivedDataCache/` / `Binaries/` / `Build/` / `.codex/` / `*.lock` 内 → 自动放行,不写 marker
- commit message 首行写 `[skip-doc]` → 跳过,但记录到 `ProjectState/Reports/<today>/doc_release_skipped.log`
- `git commit --no-verify` → git 自身跳过 hook,skipped.log 不会自动记录(用户应自觉为后续 PR 描述说明跳过原因)

skill 完整规范见 `.claude/skills/document-release/SKILL.md`(canonical) 和 `.agents/skills/document-release/SKILL.md`(Codex 副本);设计依据见 `Docs/archive/superpowers/specs/2026-05-25-document-release-port-design.md`。
