# AGENTS.md — Mvpv4TestCodex 项目

> 目标引擎版本：UE5.5.4 | 文档版本：v0.6（Phase 6）
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

本项目采用”项目层 + 插件层”双层架构：

| 层次 | 职责 | 位置 |
|------|------|------|
| **项目层** | 输入源、配置、实例、治理 | 工程根目录 |
| **插件层** | 通用编译、执行、验证框架 | Plugins/AgentBridge/ |

**关键约束**：
- 项目层保存实例，插件层提供机制
- Compiler / Handoff / Orchestrator 主体在插件层，不在项目层
- 项目层通过 `ProjectInputs/Presets/` 提供配置，不重写框架逻辑

### 2.3 工具层级启用状态

| 工具层级 | 本项目状态 | 说明 |
|---------|-----------|------|
| L1 语义工具 | ✅ 启用 | 默认主干，所有 4 个写接口 + 7 个反馈接口 |
| L2 编辑器服务工具 | ✅ 启用 | 构建/测试/验证 |
| L3 UI 工具 | ✅ 启用 | 受约束使用，遵守插件 AGENTS.md §4.3 规则 |

### 2.4 本项目写操作范围

当前开发阶段无特殊范围限制，所有已定义的写接口均可使用。

### 2.5 聊天面板文件引用格式

- 在聊天面板中引用本地文件时，链接目标必须使用”以 `/` 开头的 Windows 本地绝对路径”，例如 `/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md#L1`。
- 不要使用 `D:/...`、`d:/...` 或普通网页 URL 写法，否则 VS Code 聊天面板会把它当成浏览器链接。

### 2.6 附加文档路径

Agent 在本项目中需要参考的文档：

**项目层文档**：

| 文档 | 路径 |
|------|------|
| 当前阶段索引 | `Docs/Current/00_Index.md` |
| 项目基线 | `Docs/Current/01_Project_Baseline.md` |
| 当前阶段目标 | `Docs/Current/02_Current_Phase_Goals.md` |
| 实施边界 | `Docs/Current/05_Implementation_Boundary.md` |
| 当前任务 | 根目录 `task.md`（Phase 6 当前任务） |

**插件层文档**：

| 文档 | 路径 |
|------|------|
| 插件说明 | `Plugins/AgentBridge/README.md` |
| 通用 Agent 规则 | `Plugins/AgentBridge/AGENTS.md` |
| 总体架构 | `Plugins/AgentBridge/Docs/architecture_overview.md` |
| 工具契约 | `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` |
| 字段规范 | `Plugins/AgentBridge/Docs/field_specification_v0_1.md` |
| 反馈接口清单 | `Plugins/AgentBridge/Docs/feedback_interface_catalog.md` |
| Compiler 框架 | `Plugins/AgentBridge/Scripts/compiler/` |
| Handoff Schema | `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json` |
| Run Plan Schema | `Plugins/AgentBridge/Schemas/run_plan.schema.json` |
| 系统测试用例总表 | `Plugins/AgentBridge/Tests/SystemTestCases.md` |
| 系统测试入口 | `Plugins/AgentBridge/Tests/run_system_tests.py` |

---

## 3. 文档治理规则

### 3.1 文档分层

本项目文档分为三个信任层级：

- **L0 入口 + L1 当前生效**（`AGENTS.md` / `Docs/Current/`）：当前开发依据
- **L2 Canonical**（`Plugins/AgentBridge/` 下 Docs / Schemas / Specs / Scripts/compiler/）：长期框架规范
- **L3–L5**（`Docs/History/` / `Decisions/` / `Proposals/`）：按需参考，不作为默认依据

### 3.2 阅读顺序

Agent 进入本项目后，按以下顺序阅读：

1. `AGENTS.md`（本文件）— 规则和导航
2. `Docs/Current/00_Index.md` — 当前阶段索引
3. `Docs/Current/01_Project_Baseline.md` — 项目基线
4. `Docs/Current/02_Current_Phase_Goals.md` — 本期目标
5. `Docs/Current/05_Implementation_Boundary.md` — 实施边界
6. `Docs/History/Tasks/task3_phase5.md` — Phase 5 任务清单（已归档）
7. `Plugins/AgentBridge/README.md` — 插件定义（首次进入必读）
8. `Plugins/AgentBridge/AGENTS.md` — 通用 Agent 规则（首次进入必读）
9. 与当前任务相关的 `Docs/Current/*` 和 `Plugins/AgentBridge/Docs/*`

步骤 1–6 为必读。步骤 7–8 首次进入必读，后续按需复查。

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

- 在项目根任意新增并列的”总设计文档”
- 在未更新 `Docs/Current/` 基线前，直接把临时设计写进 `Plugins/AgentBridge/Docs/`
- 将阶段性的计划或任务写进插件 canonical 目录
- 把未经评审的设计直接写入 `Docs/Current/01_Project_Baseline.md`

新增能力的文档归属：

- 项目阶段相关的结论 → `Docs/Current/`
- 框架级的接口/规范变更 → `Plugins/AgentBridge/Docs/`（须与插件版本升级同步）
- 未定稿的设计提案 → `Docs/Proposals/`
- 关键决策记录 → `Docs/Decisions/`

### 3.6 阶段切换

当 Agent 检测到以下信号时，视为发生了阶段切换：

- `Docs/Current/00_Index.md` 中的阶段名称变更
- 当前阶段任务清单被归档并创建新清单
- 被明确告知进入新阶段

阶段切换后，必须重新完整阅读步骤 1–6 的全部文件，不可依赖上一期的缓存记忆。

### 3.7 附加说明

- `Plugins/AgentBridge/Roadmap/Archive/` 下的内容为历史开发计划，不作为当前开发依据
- 设计文档均位于插件内部，完整列表见第 2.6 节
