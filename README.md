# Mvpv4TestCodex

> 基于 UE5.5.4 的 AI Agent 辅助开发实验项目

## 项目简介

本项目是 AGENT_UE5 框架的落地实验仓库。核心能力由 **AgentBridge 插件** 提供：一套面向不同 UE5 项目的通用 Agent 开发框架插件。

项目层负责：

- 输入源（`ProjectInputs/`）
- 运行实例（`ProjectState/`）
- 项目层运行时代码（`Source/Mvpv4TestCodex/`）
- 阶段治理与文档（`Docs/`、根目录 `task.md`）

插件层负责：

- Skill Compiler Plane
- Reviewed Handoff / Run Plan
- Execution Orchestrator
- L1/L2/L3 受控工具体系
- Static Base / Contracts / Genre Packs
- 验证、报告与恢复框架

插件详细说明见 [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)。

## 当前阶段

当前处于 **Phase 7 — 准备期（待定义）**：

- `Phase 6` 的完整 Spec Tree、`runtime_playable`、真实 UE5 smoke 与截图证据已完成归档
- 当前重点是冻结下一阶段目标、边界与测试编号策略
- `preview_static` / `runtime_playable` 基线继续保留，作为下一阶段输入
- 历史 `Phase 6` 任务见 [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)

## 常用命令

```bash
# Schema 校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# Greenfield 最小闭环（preview_static）
python Scripts/run_greenfield_demo.py

# Brownfield 最小闭环（append/new-actor）
python Scripts/run_brownfield_demo.py

# Phase 6 playable runtime（runtime_playable）
python Scripts/run_boardgame_playable_demo.py
```

## 当前目录结构

```text
Mvpv4TestCodex/
├── AGENTS.md
├── README.md
├── task.md                              ← 当前阶段任务入口（Phase 7 准备期）
├── Scripts/
│   ├── run_greenfield_demo.py
│   ├── run_brownfield_demo.py
│   ├── run_boardgame_playable_demo.py
│   └── validation/
│       ├── capture_editor_evidence.py
│       └── *.ps1
├── Source/
│   └── Mvpv4TestCodex/
│       └── BoardgamePrototypeBoardActor.*
├── ProjectInputs/
├── ProjectState/
│   ├── Handoffs/
│   ├── Reports/
│   ├── RuntimeConfigs/
│   ├── Snapshots/
│   └── Evidence/
│       └── Phase6/
├── Docs/
└── Plugins/
    └── AgentBridge/
```

## 文档入口

推荐按以下顺序阅读：

1. [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md)
2. [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
3. [Docs/Current/01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)
4. [Docs/Current/02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md)
5. [Docs/Current/05_Implementation_Boundary.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/05_Implementation_Boundary.md)
6. [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
7. [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)

## 当前约定

- 根目录 `task.md` 是当前阶段唯一任务入口
- `Phase 6` 已归档到 [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)
- `Phase 6` 已验证通过的用例已补录到 [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)
- `ProjectState/Snapshots/` 继续只放 baseline / state snapshot
- `Phase 6` 历史证据归档副本位于 [phase6_evidence_2026-04-02](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/reports/AgentBridgeEvidence/phase6_evidence_2026-04-02)
