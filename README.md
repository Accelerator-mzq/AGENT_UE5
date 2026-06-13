# Mvpv4TestCodex

> 目标引擎版本：UE5.5.4
> 当前状态：Phase 15 呈现增量轴 + 反馈回流通道机制层完成(2026-06-13,验收期进行中);Phase 14 Demo-First 增量主链实施 + 验收全部完成(2026-06-12,C1-C6 全闭环,msc v1 终裁通过);Phase 13 / 12 / 11 已归档
> 当前正式口径：根 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)(Phase 14 任务书) + [phase14_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md) + [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/acceptance/acceptance_report.md#1)

## 项目简介

`Mvpv4TestCodex` 是基于 `AgentBridge` 插件的 UE5 工程，用来验证从设计输入到 Compiler、Handoff、关卡落地、运行时验证、证据裁决与文档治理的完整闭环。

Phase 11 在 Phase 10 的 MCP 认知桥接层与 Compiler Pipeline 编排之上，建立了 Skill-First Design Compiler Framework、Run 治理、Baseline Domain 模板体系与 UE5 运行时最小可玩性验证链：

```text
GDD -> Root Skill Contract -> Clarification Gate -> Skill Graph Planning
    -> Domain Skill Runtime (MCP Agent / LLM Internal / Heuristic Fallback)
    -> Cross Review v2 -> Build IR v2 -> Reviewed Handoff v3
    -> UE5 关卡 -> 运行时证据 -> MCP 后端裁决
```

## 当前入口

- 当前阶段任务书(Phase 14,已完成):[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- 当前阶段索引:[00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/INDEX.md)
- Phase 14 设计 spec:[2026-06-11-phase14-demo-first-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md)
- Phase 14 验收 runbook:[phase14_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md)
- Phase 13 设计 spec:[2026-06-10-phase13-skill-synthesis-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md)
- Phase 13 验收 runbook:[phase13_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md)
- Phase 11 收尾总览:[18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/acceptance/acceptance_report.md#1)
- Phase 11 归档任务:[task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task11_phase11.md)
- Phase 11 最终验收:[task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
- 插件入口:[Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)
- 系统测试总表:[SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)

## Phase 14 完成结果(Demo-First 增量主链,2026-06-12)

- demo_plan 切批机制:`Plugins/AgentBridge/Compiler/demo_plan/` 五模块(planner 拓扑序切批 / story_store 状态机 / evidence_validator 证据门含 hash 守门 / velocity / manifest_loader)
- MCP 工具对 `demo_story_fetch/submit`(工具数 55→`57`)+ `demo_plan`/`demo_story` Schema(strict `30/30`,Phase 15 已升至 `32/32`)+ CLI `demo_plan_main.py` + 冒烟 runner(退出码 0/1/3 归因分离)
- 可玩 demo:`Plugins/Demo_MonopolyAuction/`(authored 关卡 + 键盘可玩 + 拍卖增量,**项目层产物,不属 AgentBridge 框架**);施工规范 `ProjectInputs/ConstructionManifest/demo_plugin_standards.md` 1.1.0
- 系统测试 `15 stage / 466 case`(Stage 14 DMP-01~56 + Stage 15 PRX-01~46)
- 验收状态:C1-C6 全闭环,经 1 次 PIVOT(可玩定义缝)+ 1 次试玩反馈修复轮,msc v1 终裁**通过**;详见 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 与 [phase14_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md)

## Phase 13 完成结果(Skill 合成主链,2026-06-11)

- Stage 3 注册表数据化:三张硬编码表删除,模板 `manifest.yaml` `capability_bindings` 自描述,`registry_scan` 扫描建映射
- capability gap 显式化:库外能力写入 `skill_graph.metadata.capability_gaps`,零静默丢弃
- S3.5 合成环节:MCP 工具对 `compiler_skill_synthesis_prepare/save`(工具数 53→`55`)+ 机器校验 + 人审双 gate,合成包落 `SkillTemplates/synthesized/` 隔离区
- GDD 覆盖矩阵 + anchor 留痕 + promote 双守卫(synthesized 消费 / 未解决 gap → `PROMOTE_REJECTED`)
- 系统测试当时为 `13 stage / 364 case`(Stage 13 SKS-01~94,含终审修复 +5);`--strict` 当时为 `28/28`(当前为 `14 stage / 420`、`30/30`,见上方 Phase 14 完成结果)
- 验收状态:runbook 判据 1-12 已全部闭环(2026-06-11,含真机 / 双端 / JRPG stretch),详见 [phase13_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md)

## Phase 11 完成结果

- Phase 11 收尾时 MCP 工具总数为 `53`：Bridge `28` + Compiler 前端 `10`（含 Stage 4 交互式工具）+ Evidence 后端 `11` + 兼容 alias `4`（当前为 `55`，见上方 Phase 13 完成结果）
- Phase 11 v2 主链已落地：Root Skill Contract → Clarification Gate → Skill Graph Planning → Domain Skill Runtime → Cross Review v2 → Build IR v2 → Reviewed Handoff v3
- `session_version 1.0 / 2.0` 共存，引入 `run_id`、`fast_mode`、`generator_provider` 与 `promotable` 治理字段
- Stage 4 三路生成策略：`mcp_agent` 主路径、`llm` 内置路径（已接入，高负载验收暂缓）、`heuristic_fallback` 显式后备
- Run compare/promote、fast_mode 不可 promote、Baseline Domain Skill Template 全套已交付
- Schema 严格校验 `validate_examples.py --strict` 当时为 `26/26` 通过（当前 `28/28`）
- UE 运行时最小可玩性已通过 Editor game 与 staged standalone 双路径验证

关键证据：

- [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
- [phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md)
- [task_phase11_system_test_alignment.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task_phase11_system_test_alignment.md)

## 历史阶段

- Phase 6：[task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task4_phase6.md)
- Phase 7 准备期：[task5_phase7_preparation.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task5_phase7_preparation.md)
- Phase 7：[task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task6_phase7.md)
- Phase 8：[task8_phase8.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task8_phase8.md)
- Phase 9：[task9_phase9.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task9_phase9.md)
- Phase 10：[task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task10_phase10.md)
- Phase 11：[task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task11_phase11.md)

## 常用命令

```powershell
# Schema example 严格校验（30/30）
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 系统测试：一键执行全部 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py

# 系统测试：交互模式（选择 Stage）
python Plugins/AgentBridge/Tests/run_system_tests.py --interactive

# 系统测试：无编辑器模式
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# 启动 MCP Server
python Plugins/AgentBridge/MCP/server.py
```

## 当前约定

- `Docs/INDEX.md` 及其指向的 L1 文档体系(SRS / HLD / LLD / contracts / testing / acceptance)是当前项目口径的最高优先级。
- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 现在是 Phase 14 任务书(已完成),是当前阶段唯一开发驱动入口。
- Phase 11 的正式完成口径以 [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/acceptance/acceptance_report.md#1) 和 [task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task11_phase11.md) 为准。
- MCP 当前可见工具注册数为 `58`，其中 `54` 个为正式主工具、`4` 个为兼容 alias(2026-06-12 Phase 14 +`demo_story_fetch/submit`;2026-06-13 Phase 15 +`demo_feedback_log`)。

## Phase 15 机制层完成结果(呈现增量轴 + 反馈回流通道,2026-06-13)

- **机制层(插件层)**:planner amend(amend.py 切呈现/反馈批)+ evidence_validator 行为校验门禁 BL-05 + 冻结分层 frozen_baselines / supersedes + MCP demo_feedback_log(工具数 57→58)+ smoke runner BL-04 + Schema +2 入 strict(30→32)+ demo_story/demo_plan 升 1.1.0
- **项目层产物**:阶梯实例 ProjectInputs/Ladder/monopoly_demo_ladder.json + 施工规范 ProjectInputs/ConstructionManifest/demo_plugin_standards.md 升 1.2.0
- **系统测试**:Stage 15 PRX-01~46 登记,系统测试 420→466(15 stage)
- **验收状态**:机制层完成(最终整体复审 Ready to merge),验收期未启动(demo 三 rung 无人值守 + 试玩两窗口);spec/plan 见 Docs/superpowers/specs/2026-06-12-phase15-presentation-axis.md 与 Docs/superpowers/plans/2026-06-12-phase15-presentation-axis.md
- 权威数字(实测,2026-06-13):pytest `-k phase15` **46** / `-k phase14` **56** / 系统测试 **466**(15 stage)/ Schema examples strict **32/32** / MCP 工具 **58**
- 证据:[phase15_mechanism_verification.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-13/phase15_mechanism_verification.md)
