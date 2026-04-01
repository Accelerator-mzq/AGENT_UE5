# Mvpv4TestCodex

> 基于 UE5.5.4 的 AI Agent 辅助开发实验项目

## 项目简介

本项目是 AGENT_UE5 框架的落地实验仓库。核心能力由 **AgentBridge 插件** 提供：一套面向不同 UE5 项目的通用 Agent 开发框架插件。

项目层负责：

- 输入源（`ProjectInputs/`）
- 运行实例（`ProjectState/`）
- 阶段治理与文档（`Docs/`、根目录 `task.md`）

插件层负责：

- Skill Compiler Plane
- Reviewed Handoff / Run Plan
- Execution Orchestrator
- L1/L2/L3 受控工具体系
- 验证、报告与恢复框架

插件详细文档见 [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)。

## 快速开始

### 前置要求

- Unreal Engine 5.5.4
- Visual Studio 2022 / Xcode / clang
- Python 3.x
- Python 依赖：`pyyaml`、`jsonschema`、`pytest`

### 常用命令

```bash
# Schema 校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# Greenfield 最小闭环（simulated）
python Scripts/run_greenfield_demo.py

# Brownfield 最小闭环（simulated）
python Scripts/run_brownfield_demo.py
```

## 当前目录结构

```text
Mvpv4TestCodex/
├── AGENTS.md
├── README.md
├── task.md                              ← 当前阶段任务入口（Phase 5）
├── Scripts/
│   ├── run_greenfield_demo.py           ← 项目层 Greenfield E2E 入口
│   ├── run_brownfield_demo.py           ← 项目层 Brownfield E2E 入口
│   └── validation/
│       ├── capture_phase5_evidence.py   ← Phase 5 截图证据辅助脚本
│       └── *.ps1
├── ProjectInputs/
│   ├── GDD/
│   ├── Presets/
│   └── Baselines/                       ← 人工/冻结 baseline 输入（可选）
├── ProjectState/
│   ├── Handoffs/
│   ├── Reports/
│   ├── Snapshots/                       ← baseline/state snapshot
│   └── Evidence/
│       └── Phase5/                      ← 当前阶段运行截图/日志/说明
├── Docs/
│   ├── Current/
│   ├── History/
│   ├── Decisions/
│   └── Proposals/
└── Plugins/
    └── AgentBridge/
```

## 当前进度

### Phase 1-2（已完成）

- 三层受控工具体系（L1/L2/L3）
- Bridge 三通道架构
- UE5 Automation Test / Automation Spec / Functional Testing
- Schema 校验链

### Phase 3（已完成）

- Skill Compiler Plane 最小框架
- Reviewed Handoff / Run Plan
- Greenfield 最小闭环

### Phase 4（已完成）

- Static Spec Base（10 个静态基座）
- 自动 Dynamic Spec 生成链
- Cross-Spec Review
- `Scripts/run_greenfield_demo.py` simulated / `bridge_rc_api` 闭环

### Phase 5（进行中）

- Brownfield Baseline Understanding
- Delta Scope Analysis
- Contracts 最小体系
- 截图证据目录与阶段归档规则

## 文档入口

推荐按以下顺序阅读：

1. [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md)
2. [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
3. [Docs/Current/01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)
4. [Docs/Current/05_Implementation_Boundary.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/05_Implementation_Boundary.md)
5. [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
6. [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)

## 当前约定

- 根目录 `task.md` 是当前阶段唯一任务入口；阶段结束后归档到 `Docs/History/Tasks/`
- `ProjectState/Snapshots/` 只放 baseline / state snapshot，不混放截图证据
- `ProjectState/Evidence/Phase5/` 用于 Phase 5 当前运行证据；阶段结束后整期归档
