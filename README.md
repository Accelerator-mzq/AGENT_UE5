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

当前处于 **Phase 6 — 完整 Spec Tree + 可玩 Runtime**：

- 从 [boardgame_tictactoe_v1.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/boardgame_tictactoe_v1.md) 自动编译完整 boardgame Spec Tree
- 保留 `preview_static` 投影，继续兼容 Phase 4/5 Greenfield/Brownfield 回归
- 新增 `runtime_playable` 投影，生成最小可玩井字棋 runtime
- 使用项目层 `BoardgamePrototypeBoardActor` 作为运行时承载体
- 截图证据统一走 [capture_editor_evidence.py](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py)

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
├── task.md                              ← 当前阶段任务入口（Phase 6）
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

- 根目录 `task.md` 是 Phase 6 当前唯一任务入口
- Phase 6 测试用例先只写在 `task.md`，不提前回写 `SystemTestCases.md`
- `ProjectState/Snapshots/` 只放 baseline / state snapshot
- `ProjectState/Evidence/Phase6/` 放 Phase 6 当前截图、日志与说明
- Phase 6 结束后，`task.md` 归档到 `Docs/History/Tasks/task4_phase6.md`
