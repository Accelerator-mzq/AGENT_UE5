# AGENTS.md — Mvpv4TestCodex 项目

> 目标引擎版本：UE5.5.4 | 文档版本：v0.3
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

### 2.2 工具层级启用状态

| 工具层级 | 本项目状态 | 说明 |
|---------|-----------|------|
| L1 语义工具 | ✅ 启用 | 默认主干，所有 4 个写接口 + 7 个反馈接口 |
| L2 编辑器服务工具 | ✅ 启用 | 构建/测试/验证 |
| L3 UI 工具 | ✅ 启用 | 受约束使用，遵守插件 AGENTS.md §4.3 规则 |

> 如果某个项目需要禁用 L3，在此处标注 `❌ 禁用` 即可。

### 2.3 本项目写操作范围

当前开发阶段无特殊范围限制，所有已定义的写接口均可使用。

### 2.4 聊天面板文件引用格式

- 在聊天面板中引用本地文件时，链接目标必须使用“以 `/` 开头的 Windows 本地绝对路径”，例如 `/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md#L1`。
- 不要使用 `D:/...`、`d:/...` 或普通网页 URL 写法，否则 VS Code 聊天面板会把它当成浏览器链接。
- 推荐显示文字格式：`文件名 (line N)`。
- 推荐链接目标格式：`/D:/.../文件#L行号`。

### 2.5 附加文档路径

Agent 在本项目中需要参考的设计文档均位于插件内部：

| 文档 | 路径 |
|------|------|
| 插件说明 | `Plugins/AgentBridge/README.md` |
| 通用 Agent 规则 | `Plugins/AgentBridge/AGENTS.md` |
| UE5 能力映射 | `Plugins/AgentBridge/Docs/ue5_capability_map.md` |
| 总体架构 | `Plugins/AgentBridge/Docs/architecture_overview.md` |
| MVP 边界 | `Plugins/AgentBridge/Docs/mvp_scope.md` |
| 工具契约 | `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` |
| 字段规范 | `Plugins/AgentBridge/Docs/field_specification_v0_1.md` |
| 反馈接口清单 | `Plugins/AgentBridge/Docs/feedback_interface_catalog.md` |
| 写-读映射关系 | `Plugins/AgentBridge/Docs/feedback_write_mapping.md` |
| Bridge 实现方案 | `Plugins/AgentBridge/Docs/bridge_implementation_plan.md` |
| 冒烟测试方案 | `Plugins/AgentBridge/Docs/mvp_smoke_test_plan.md` |
| 接口验证与错误处理 | `Plugins/AgentBridge/Docs/bridge_verification_and_error_handling.md` |
| Orchestrator 设计 | `Plugins/AgentBridge/Docs/orchestrator_design.md` |

---

## 3. 当前推进状态

### 已完成

- ✅ 本地 schema / example / validate 校验链跑通
- ✅ task.md 1-20 全部跑通
- ✅ Bridge 三通道架构实装（C++ Plugin 核心 + Python + Remote Control API）
- ✅ L1/L2/L3 三层受控工具体系全部实装
- ✅ 验证层实装于 UE5 Automation Test Framework（L1 Simple Test + L2 Spec + L3 Functional Test）
- ✅ Gauntlet CI/CD 测试配置

### 当前最高优先级

1. ⬜ spawn_actor → get_actor_state → get_actor_bounds 端到端闭环
2. ⬜ Agent → Editor 通信方案落地（Remote Control API HTTP）
3. ⬜ Orchestrator 实现（参考 UE5 Gauntlet 编排模式）
4. ⬜ Phase 2 扩展接口开发

### 当前已知卡点

- Agent→Editor 通信方案需选型落地（推荐 Remote Control API HTTP）
- Orchestrator 尚未实现
- Phase 2 反馈接口（get_material_assignment 等）的 Tool Contract 待补充

---

## 4. 推荐阅读顺序

Agent 进入本项目的推荐阅读顺序：

1. 本文件（`AGENTS.md`）— 了解项目特定规则和当前状态
2. `Plugins/AgentBridge/README.md` — 了解插件定义、架构和功能清单
3. `Plugins/AgentBridge/AGENTS.md` — 了解通用 Agent 规则
4. `Plugins/AgentBridge/Docs/ue5_capability_map.md` — 了解 UE5 官方能力映射
5. `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` — 了解工具契约
6. `task.md` — 了解当前任务清单
