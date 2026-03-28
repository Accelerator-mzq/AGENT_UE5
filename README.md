# Mvpv4TestCodex

> 基于 UE5.5.4 的 AI Agent 辅助开发实验项目

## 项目简介

本项目是 AGENT + UE5 可操作层 MVP 方案的落地实验仓库，探索 AI Agent 在可控边界内参与 UE5 开发流程的方案。

核心能力由 **AgentBridge 插件** 提供 — 一套位于 AI Agent 与 UE5 官方能力之间的受控编排层，通过"结构化 Spec → 受控工具 → 写后读回 → 结构化验证"闭环实现可控的 AI 辅助开发。

→ 插件详细文档：[`Plugins/AgentBridge/README.md`](Plugins/AgentBridge/README.md)

## 快速开始

### 前置要求

- Unreal Engine 5.5.4
- Visual Studio 2022 / Xcode / clang（C++ 编译）
- Python 3.x（Schema 校验和 Bridge 客户端）

### 构建与运行

1. 克隆本仓库
2. 打开 `Mvpv4TestCodex.uproject`（或你的项目 `.uproject` 文件）
3. 确认 AgentBridge 插件在 Edit → Plugins 中已启用
4. 编译项目（Build → Build Solution）
5. 运行 Schema 校验验证环境：
   ```bash
   python Plugins/AgentBridge/Scripts/validation/validate_examples.py
   ```

### 项目结构

```
Mvpv4TestCodex/
├── AGENTS.md                        ← 本项目的 Agent 行为规则
├── README.md                        ← 本文件
├── task.md                          ← 编码 Agent 任务清单（task 1-20 已跑通）
│
├── Content/                         ← UE5 资产
├── Config/                          ← UE5 配置
├── Source/                          ← 游戏代码（如有）
│
└── Plugins/
    ├── AgentBridge/                  ← ★ 核心插件（受控编排层）
    │   ├── README.md                ← 插件说明（架构 / 接口 / 安装）
    │   ├── AGENTS.md                ← 通用 Agent 规则
    │   ├── Source/                  ← C++ 实现
    │   ├── Docs/                   ← 设计文档（11 个）
    │   ├── Schemas/                ← JSON Schema（24 个）
    │   ├── Scripts/                ← Python 客户端 + 校验
    │   ├── Specs/                  ← Spec 模板
    │   ├── Gauntlet/               ← CI/CD 测试配置
    │   ├── Roadmap/                ← 路线图
    │
    │   └── AgentBridgeTests/        ← 嵌套测试插件（按需注入）
```

## AI Agent 开发指引

如果你是 AI Agent 或使用 AI Agent 参与本项目开发，请按以下顺序阅读：

1. **[`AGENTS.md`](AGENTS.md)** — 本项目的 Agent 行为规则（包含项目特定配置和当前状态）
2. **[`Plugins/AgentBridge/README.md`](Plugins/AgentBridge/README.md)** — AgentBridge 插件说明
3. **[`Plugins/AgentBridge/AGENTS.md`](Plugins/AgentBridge/AGENTS.md)** — 通用 Agent 规则
4. **[`task.md`](task.md)** — 当前任务清单

## 当前进度

- ✅ task.md 1-20 全部跑通
- ✅ 三层受控工具体系（L1/L2/L3）全部实装
- ✅ Bridge 三通道架构（C++ Plugin + Python + Remote Control API）
- ✅ UE5 Automation Test 验证层
- ⬜ 端到端闭环验证
- ⬜ Phase 2 扩展接口

## 相关链接

- 项目仓库：https://github.com/Accelerator-mzq/AGENT_UE5
