# Mvpv4TestCodex

> 基于 UE5.5.4 的 AI Agent 辅助开发实验项目

## 项目简介

本项目是 AGENT_UE5 框架的落地实验仓库。核心能力由 **AgentBridge 插件** 提供 — 一套面向不同 UE5 项目的**通用 Agent 开发框架插件**。

AgentBridge 不只是工具接口插件，而是包含**通用编译前端（Skill Compiler Plane）、交接物机制（Reviewed Handoff）、执行编排（Orchestrator）、验证与恢复框架**的完整 Agent 框架。

**项目层（本工程）** 负责提供输入、配置、实例和治理。
**插件层（AgentBridge）** 负责提供通用编译与执行框架。

→ 插件详细文档：[`Plugins/AgentBridge/README.md`](Plugins/AgentBridge/README.md)

## 快速开始

### 前置要求

- Unreal Engine 5.5.4
- Visual Studio 2022 / Xcode / clang（C++ 编译）
- Python 3.x + pyyaml + jsonschema

### 构建与运行

1. 克隆本仓库
2. 打开 `Mvpv4TestCodex.uproject`
3. 确认 AgentBridge 插件在 Edit → Plugins 中已启用
4. 编译项目（Build → Build Solution）
5. 运行 Schema 校验：
   ```bash
   python Plugins/AgentBridge/Scripts/validation/validate_examples.py
   ```
6. 运行 Greenfield 最小闭环（simulated 模式）：
   ```bash
   python run_greenfield_demo.py
   ```

### 项目结构

```
Mvpv4TestCodex/
├── AGENTS.md                        ← 本项目的 Agent 行为规则
├── README.md                        ← 本文件
├── task1.md                         ← 当前阶段任务清单（Phase 3）
├── run_greenfield_demo.py           ← 端到端运行入口
│
├── ProjectInputs/                   ← ★ 项目输入源
│   ├── GDD/                         ← 游戏设计文档
│   ├── Presets/                     ← 项目级配置（模式/编译器）
│   └── Baselines/                   ← 项目基线
│
├── ProjectState/                    ← ★ 项目运行实例
│   ├── Handoffs/                    ← Reviewed Handoff 实例
│   │   ├── draft/
│   │   └── approved/
│   ├── Reports/                     ← 执行报告
│   └── Snapshots/                   ← 项目快照
│
├── Docs/                            ← 项目治理文档
│   ├── Current/                     ← 当前阶段生效文档
│   ├── History/                     ← 历史归档
│   ├── Decisions/                   ← 决策记录（ADR）
│   └── Proposals/                   ← 设计草案
│
├── Content/                         ← UE5 资产
├── Config/                          ← UE5 配置
├── Source/                          ← 游戏代码
│
└── Plugins/
    └── AgentBridge/                 ← ★ 通用 Agent 框架插件
        ├── Source/                   ← C++ 核心（Subsystem / 工具接口）
        ├── Scripts/
        │   ├── compiler/            ← Skill Compiler Plane 主体
        │   ├── orchestrator/        ← Run Plan / Workflow / Recovery
        │   ├── bridge/              ← 三通道客户端
        │   └── validation/          ← 校验脚本
        ├── Schemas/                 ← JSON Schema（Handoff / Run Plan / 工具接口）
        ├── Skills/                  ← Skill 体系（Base Domains / Genre Packs）
        ├── Specs/                   ← 静态基座 / Contract / 模板
        ├── Docs/                    ← 框架级设计文档
        └── Gauntlet/                ← CI/CD 测试配置
```

## 分层原则

| 层次 | 职责 | 位置 |
|------|------|------|
| **项目层** | 输入源、配置、实例、治理 | 工程根目录 |
| **插件层** | 通用编译、执行、验证框架 | Plugins/AgentBridge/ |

- 项目层保存实例，插件层提供机制
- GDD 文件在项目层，GDD 解析机制在插件层
- Handoff 实例在项目层，Handoff 格式和生成器在插件层

## AI Agent 开发指引

如果你是 AI Agent 或使用 AI Agent 参与本项目开发，请按以下顺序阅读：

1. **[`AGENTS.md`](AGENTS.md)** — 本项目的 Agent 行为规则与文档治理规则
2. **[`Docs/Current/00_Index.md`](Docs/Current/00_Index.md)** — 当前阶段文档索引
3. **[`Docs/Current/01_Project_Baseline.md`](Docs/Current/01_Project_Baseline.md)** — 项目基线
4. **[`Docs/Current/05_Implementation_Boundary.md`](Docs/Current/05_Implementation_Boundary.md)** — 实施边界
5. **[`task1.md`](task1.md)** — 当前任务清单
6. **[`Plugins/AgentBridge/README.md`](Plugins/AgentBridge/README.md)** — AgentBridge 插件说明
7. **[`Plugins/AgentBridge/AGENTS.md`](Plugins/AgentBridge/AGENTS.md)** — 通用 Agent 规则

## 当前进度

### Phase 1-2（已完成）
- ✅ 三层受控工具体系（L1/L2/L3）全部实装
- ✅ Bridge 三通道架构（C++ Plugin + Python + Remote Control API）
- ✅ UE5 Automation Test 验证层
- ✅ Schema 校验链

### Phase 3（进行中）
- ✅ Skill Compiler Plane 最小框架
- ✅ Reviewed Handoff Schema + Builder
- ✅ Run Plan Schema + Builder
- ✅ Orchestrator Handoff Runner 桥接
- ✅ Greenfield + Boardgame simulated 模式跑通
- ⬜ UE5 真实调用联调
- ⬜ Brownfield 能力（占位，后续实装）

## 相关链接

- 项目仓库：https://github.com/Accelerator-mzq/AGENT_UE5
