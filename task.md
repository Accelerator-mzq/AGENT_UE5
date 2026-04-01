# Phase 6 — Genre Skill Packs 完整化 当前任务入口

> 目标引擎版本：UE5.5.4  
> 阶段定位：Phase 6  
> 当前阶段入口：[Docs/Current/06_Phase6_Task_List.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/06_Phase6_Task_List.md)  
> 上一阶段归档：[task3_phase5.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task3_phase5.md)

## 使用说明

1. 根目录 `task.md` 继续作为当前阶段唯一任务入口。
2. 当前文件先作为 Phase 6 入口版任务清单；正式详细开发计划可在此基础上继续细化。
3. Phase 6 测试用例先维护在本文件中，不提前写入 `Plugins/AgentBridge/Tests/SystemTestCases.md`。
4. `ProjectState/Snapshots/` 只保存 baseline / state snapshot；当前阶段运行证据统一写入 `ProjectState/Evidence/Phase6/`。
5. 真实 UE5 截图取证的可复用方法继续参照 [editor_screenshot_evidence_workflow.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md)。

## 当前主目标

- 落地 `Skills/genre_packs/_core/` 的最小可用机制
- 让 `boardgame` 类型包从 manifest 骨架走向可用编译驱动力
- 为 `boardgame` 补齐 `required_skills / review_extensions / validation_extensions / delta_policy`
- 为 `Specs/Contracts/Genres/Boardgame/` 落地首批 genre contract
- 保持 Phase 5 的 Greenfield / Brownfield 最小闭环不回归

## 当前任务总览

阶段 1：Phase 6 文档与边界对齐（01）  
阶段 2：Genre Pack Core 盘点与拆解（02）  
阶段 3：Boardgame 类型包现状核对（03）  
阶段 4：输出 Phase 6 正式开发计划（04）

---

## TASK 01：完成 Phase 6 文档切换与当前规则对齐

目标：把项目层入口文档、当前期规则和历史归档引用全部切到 Phase 6 口径。  
前置依赖：无

先读这些文件：
- [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md)
- [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [Docs/Current/07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md)
- [task3_phase5.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task3_phase5.md)

涉及文件：
- `README.md`
- `AGENTS.md`
- `Docs/Current/00_Index.md`
- `Docs/Current/01_Project_Baseline.md`
- `Docs/Current/02_Current_Phase_Goals.md`
- `Docs/Current/03_Active_Backlog.md`
- `Docs/Current/04_Open_Risks.md`
- `Docs/Current/05_Implementation_Boundary.md`
- `Docs/Current/06_Phase6_Task_List.md`
- `Docs/Current/07_Evidence_And_Artifacts.md`

Step 1：确认 Phase 5 已归档，Phase 6 已成为当前 Active 阶段。  
Step 2：把 `ProjectState/Evidence/Phase6/` 写成当前阶段工作目录。  
Step 3：把 `task3_phase5.md` 登记为上一阶段归档入口。  
Step 4：更新 README/AGENTS 中仍然残留的 Phase 5 当前口径。  

【验收标准】
- `Docs/Current/00_Index.md` 显示 Phase 6 为 Active
- `Docs/Current/06_Phase6_Task_List.md` 可正常指向根目录 `task.md`
- `Docs/Current/07_Evidence_And_Artifacts.md` 已改为 Phase 6 规则

【证据要求】
- 在 `ProjectState/Reports/` 写一份 Phase 6 入口切换记录

---

## TASK 02：完成 Genre Pack Core 现状盘点与拆解

目标：把 `_core` 目录从“占位”切到“明确可落地任务”，形成 Phase 6 的最小开发分解。  
前置依赖：TASK 01 完成

先读这些文件：
- [AGENT_UE5_Development_Roadmap.md](/D:/ClaudeProject/fenxi-claude/AGENT_UE5_Development_Roadmap.md)
- [Plugins/AgentBridge/Skills/genre_packs/_core/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Skills/genre_packs/_core/README.md)
- [skills_and_specs_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/skills_and_specs_overview.md)

涉及文件：
- `Plugins/AgentBridge/Skills/genre_packs/_core/`
- `Docs/Current/03_Active_Backlog.md`
- 根目录 `task.md`

Step 1：确认 `_core` 当前尚缺 `manifest_loader / router_base / registry`。  
Step 2：明确这些模块各自的输入、输出和依赖。  
Step 3：将 Phase 6 正式开发计划中需要的 `_core` 子任务拆清楚。  

【验收标准】
- 能清楚列出 `_core` 最小落地清单
- 不把 `_core` 和 Base Skill Domains 混做一件事

【证据要求】
- 将拆解结果写回后续正式 Phase 6 任务清单或阶段记录

---

## TASK 03：完成 Boardgame 类型包现状核对

目标：核对 `boardgame` pack 从 manifest 到目录结构还有哪些缺口，明确 Phase 6 的真实起点。  
前置依赖：TASK 02 完成

先读这些文件：
- [pack_manifest.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Skills/genre_packs/boardgame/pack_manifest.yaml)
- [skills_and_specs_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/skills_and_specs_overview.md)
- [01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)

涉及文件：
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/`
- `Docs/Current/03_Active_Backlog.md`
- 根目录 `task.md`

Step 1：核对 `required_skills / review_extensions / validation_extensions / delta_policy` 是否仍只是最小声明。  
Step 2：明确 Phase 6 首先应补哪 3 个 required_skills。  
Step 3：明确哪些内容属于 genre contract，哪些仍应留在 Common Contracts。  

【验收标准】
- 能明确 boardgame pack 当前“已存在的骨架”和“尚未实现的能力”
- 不把 Phase 5 已闭环能力重复当成 Phase 6 新任务

【证据要求】
- 将盘点结果写回后续正式 Phase 6 任务清单或阶段记录

---

## TASK 04：输出 Phase 6 正式开发计划

目标：在完成入口切换和现状盘点后，输出一份可执行的 Phase 6 正式任务清单。  
前置依赖：TASK 03 完成

先读这些文件：
- [Docs/Current/02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md)
- [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)
- [task3_phase5.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task3_phase5.md)

涉及文件：
- 根目录 `task.md`
- `Docs/Current/06_Phase6_Task_List.md`

Step 1：把 `_core`、boardgame pack、genre contract、回归与证据治理整理成正式 TASK。  
Step 2：确保每个 TASK 有“先读这些文件 / 涉及文件 / 验收标准 / 证据要求”。  
Step 3：确保 Phase 6 测试策略仍遵守“先在 task.md，归档时再补录到 SystemTestCases”的规则。  

【验收标准】
- 根目录 `task.md` 被升级为正式 Phase 6 任务清单
- 当前文档、当前任务和插件入口之间口径一致

【证据要求】
- 在 `ProjectState/Reports/` 写一份 Phase 6 任务清单生成记录
