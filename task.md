# Phase 7 — 治理闭环 + JRPG 第二类型包任务清单

> 目标引擎版本：UE5.5.4
> 阶段定位：Phase 7 正式开发期
> 上一阶段归档：[task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)
> 准备期归档：[task5_phase7_preparation.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task5_phase7_preparation.md)
> 当前阶段索引：[00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)

## 本期固定规则

1. 根目录 `task.md` 继续作为当前阶段唯一任务入口。
2. `Phase 7` 新测试只维护在本文件，不提前写入 [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)。
3. [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 在本期开发期间保持 `206` 条口径不动。
4. Snapshot 默认写入 `ProjectState/Snapshots/YYYY-MM-DD/`，报告默认写入按日目录。
5. 所有新代码都要带中文注释。

## 使用说明

1. 每个 TASK 都先按“先读这些文件”建立上下文，再实施。
2. 每个 TASK 的【验收标准】全部满足后，才算该 TASK 完成。
3. 本期真实测试编号只在本文维护，阶段结束归档时再统一补录进总表。
4. 如需追溯准备期，只查看 [task5_phase7_preparation.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task5_phase7_preparation.md)。

## 核心约束

- 不提前扩写 [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)
- 不提前扩写 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 的编号范围
- 不重写稳定 Bridge 三通道主体
- 治理闭环先做最小可用版本，不做完整审批流水线
- 第二个类型包固定为 `JRPG Turn-Based`，不同时扩多个新 pack

## 测试编号约定（仅本期使用）

- `SS-14~SS-20`：结构 / 模块 / 契约级测试
- `CP-32~CP-40`：编译期 / 治理期测试
- `E2E-29~E2E-36`：端到端与 smoke 验证

## TASK 01：完成 Phase 7 文档切换与入口统一

目标：把项目层和插件层入口统一切到“Phase 7 正式开发期”口径。
前置依赖：无

先读这些文件：
- [00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)
- [README.md](/D:/UnrealProjects/Mvpv4TestCodex/README.md)
- [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)

涉及文件：
- `Docs/Current/*`
- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `Plugins/AgentBridge/README.md`
- `Plugins/AgentBridge/Docs/*`

Step 1：归档准备期任务并更新历史索引。
Step 2：把 `Docs/Current/*` 切换到正式开发期口径。
Step 3：同步项目层和插件层入口文档中的旧阶段描述。

【验收标准】
- `Docs/Current/*` 不再出现“Phase 7 准备期”口径
- 根目录 `task.md` 成为正式开发期任务入口
- 准备期任务已归档到 [task5_phase7_preparation.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task5_phase7_preparation.md)

## TASK 02：落地 Validation Inserter 最小闭环

目标：让 `run_plan` 能自动插入最小验证检查点。
前置依赖：TASK 01 完成

先读这些文件：
- [AGENT_UE5_Development_Roadmap.md](/D:/UnrealProjects/Mvpv4TestCodex/PhaseDoc/AGENT_UE5_Development_Roadmap.md)
- [run_plan.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/run_plan.schema.json)
- [run_plan_builder.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py)

涉及文件：
- `Plugins/AgentBridge/Scripts/orchestrator/validation_inserter.py`
- `Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py`
- `Plugins/AgentBridge/Schemas/run_plan.schema.json`

Step 1：定义 validation checkpoint 的最小结构。
Step 2：按 workflow / projection / base domains 自动插入检查点。
Step 3：把插点结果写回 `run_plan`。

【验收标准】
- `CP-32`：`run_plan` 含 `validation_checkpoints[]`
- `CP-39`：缺失治理前置项时能在计划层表达阻断原因

## TASK 03：落地 Recovery Planner 最小闭环

目标：让 `run_plan` 带最小恢复策略引用与策略内容。
前置依赖：TASK 02 完成

先读这些文件：
- [run_plan_builder.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py)
- [handoff_runner.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py)

涉及文件：
- `Plugins/AgentBridge/Scripts/orchestrator/recovery_planner.py`
- `Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py`
- `Plugins/AgentBridge/Schemas/run_plan.schema.json`

Step 1：定义最小恢复策略模型。
Step 2：按模式与治理域生成 `recovery_policy_ref`。
Step 3：把策略映射写回 `run_plan`。

【验收标准】
- `CP-33`：`run_plan` 含 `recovery_policy_ref`
- `E2E-30`：失败路径能返回最小恢复建议

## TASK 04：落地 Actor 级 Regression 与 Freeze / Snapshot

目标：让执行报告具备 Actor 级回归摘要，并生成最小 snapshot manifest。
前置依赖：TASK 03 完成

先读这些文件：
- [baseline_builder.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/compiler/analysis/baseline_builder.py)
- [handoff_runner.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py)
- [07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md)

涉及文件：
- `Plugins/AgentBridge/Scripts/compiler/analysis/baseline_builder.py`
- `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py`
- `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json`

Step 1：把 Snapshot 输出改为按日期目录。
Step 2：生成最小 snapshot manifest。
Step 3：把 `regression_summary` 与 `snapshot_ref` 写入执行报告。

【验收标准】
- `CP-34`：执行报告含 `regression_summary`
- `CP-35`：执行报告含 `snapshot_ref`
- `E2E-31`：simulated 路径可生成 snapshot manifest

## TASK 05：落地 Minimal Promotion 治理流

目标：提供最小的 `draft -> reviewed -> approved` 状态推进与审计记录。
前置依赖：TASK 04 完成

先读这些文件：
- [reviewed_handoff.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json)
- [handoff_runner.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py)

涉及文件：
- `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py`
- `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json`

Step 1：定义最小 promotion 状态表达。
Step 2：在执行成功后写出 promotion 审计。
Step 3：把 `promotion_status` 回填到执行报告。

【验收标准】
- `CP-36`：执行报告含 `promotion_status`
- `E2E-32`：simulated 路径能留下 promotion 审计记录

## TASK 06：把 Base Skill Domains 从占位目录升级为真实 registry

目标：为治理闭环和多类型扩展提供真正可复用的骨架。
前置依赖：TASK 05 完成

先读这些文件：
- [skills_and_specs_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/skills_and_specs_overview.md)
- [README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Skills/base_domains/README.md)

涉及文件：
- `Plugins/AgentBridge/Skills/base_domains/`
- `Plugins/AgentBridge/Docs/base_skill_domains_design.md`

Step 1：建立 registry / loader / 公共接口。
Step 2：真实实现 `qa_validation` 与 `planning_governance`。
Step 3：补齐其余 8 个域的可加载骨架。

【验收标准】
- `SS-14`：base domain registry 可发现 10 个域
- `SS-15`：`qa_validation` / `planning_governance` 可真实加载
- `CP-37`：base domains 能参与治理计划生成

## TASK 07：实现第二个 Genre Pack：JRPG Turn-Based

目标：让第二个 pack 从 GDD 走通 Greenfield / Brownfield 最小闭环。
前置依赖：TASK 06 完成

先读这些文件：
- [genre_pack_core_design.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/genre_pack_core_design.md)
- [compiler_design.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/compiler_design.md)
- [boardgame_tictactoe_v1.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/boardgame_tictactoe_v1.md)

涉及文件：
- `Plugins/AgentBridge/Skills/genre_packs/jrpg/`
- `Plugins/AgentBridge/Scripts/compiler/intake/design_input_intake.py`
- `Plugins/AgentBridge/Scripts/compiler/generation/spec_generation_dispatcher.py`
- `Plugins/AgentBridge/Scripts/compiler/generation/jrpg_scene_generator.py`
- `Scripts/run_jrpg_turn_based_demo.py`
- `ProjectInputs/GDD/jrpg_turn_based_v1.md`

Step 1：新增 `jrpg` pack manifest 与模块目录。
Step 2：让 Intake / Generator / Review / Delta 能识别 `jrpg`。
Step 3：提供最小 demo 入口。

【验收标准】
- `SS-16`：JRPG manifest 合法且字段完整
- `SS-17`：JRPG required skills 可加载
- `SS-18`：JRPG review / validation / delta policy 可加载
- `CP-38`：JRPG Greenfield compile 生成最小 spec tree
- `CP-40`：JRPG Brownfield delta 能表达最小增量
- `E2E-34`：JRPG simulated 端到端成功

## TASK 08：完成 Phase 7 测试、回归与验证记录

目标：补齐本期测试入口，并为阶段开发提供可审计证据。
前置依赖：TASK 07 完成

先读这些文件：
- [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)

涉及文件：
- `Plugins/AgentBridge/Tests/scripts/test_phase7_governance_and_jrpg.py`
- `ProjectState/Reports/`

Step 1：新增 Phase 7 pytest。
Step 2：运行 simulated demo / pytest 定向回归。
Step 3：把结果写入 `ProjectState/Reports/`。

【验收标准】
- `SS-14~SS-20` 全部通过
- `CP-32~CP-40` 全部通过
- `E2E-29`：governance simulated 成功
- `E2E-30`：recovery simulated 成功
- `E2E-31`：freeze / snapshot simulated 成功
- `E2E-32`：promotion simulated 成功
- `E2E-33`：JRPG simulated 编译成功
- `E2E-34`：JRPG simulated 执行成功
- `E2E-35`：JRPG 真实 UE5 smoke 成功并留存 6 张证据图
- `E2E-36`：boardgame 回归仍保持可跑

## 当前阶段测试清单（仅本期维护）

### SS

- `SS-14`：base domain registry 可发现 10 个域
- `SS-15`：`qa_validation` 与 `planning_governance` 域可真实加载
- `SS-16`：JRPG manifest 字段完整且可解析
- `SS-17`：JRPG required skills 可加载
- `SS-18`：JRPG review / validation / delta policy 模块可加载
- `SS-19`：governance 相关 schema / contract bundle 可读取
- `SS-20`：JRPG router activation 可命中第二类型包

### CP

- `CP-32`：`run_plan` 含 `validation_checkpoints[]`
- `CP-33`：`run_plan` 含 `recovery_policy_ref`
- `CP-34`：执行报告含 `regression_summary`
- `CP-35`：执行报告含 `snapshot_ref`
- `CP-36`：执行报告含 `promotion_status`
- `CP-37`：base domains 激活结果可写回治理上下文
- `CP-38`：JRPG Greenfield compile 生成最小 spec tree
- `CP-39`：缺失治理前置项时计划层可阻断
- `CP-40`：JRPG Brownfield delta 可表达最小增量

### E2E

- `E2E-29`：`python Scripts/run_greenfield_demo.py simulated` 可生成治理增强版 run plan / execution report
- `E2E-30`：治理失败路径能返回 recovery suggestion
- `E2E-31`：simulated 路径能写出 snapshot manifest
- `E2E-32`：simulated 路径能留下 minimal promotion 审计
- `E2E-33`：`python Scripts/run_jrpg_turn_based_demo.py simulated` 可生成 JRPG handoff
- `E2E-34`：`python Scripts/run_jrpg_turn_based_demo.py simulated` 可执行成功
- `E2E-35`：JRPG 真实 UE5 smoke 成功，关键 Actor 布局与结构级 battle loop 校验通过
- `E2E-36`：`boardgame` Greenfield / Brownfield / playable 回归入口仍存在

## 当前进展（2026-04-02）

- `P0` 已完成，证据见 [phase7_bootstrap_implementation_2026-04-02.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-02/phase7_bootstrap_implementation_2026-04-02.md)
- `E2E-35 / E2E-36` 已完成首轮落证，证据见 [phase7_e2e35_e2e36_validation_2026-04-02.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-02/phase7_e2e35_e2e36_validation_2026-04-02.md)
- 当前进入 `P1` 收敛期，开发顺序固定为：
  1. 三轮稳定性回归
  2. Snapshot / Promotion 审计摘要
  3. JRPG pack 跨入口一致性报告
  4. 归档前检查表
- 归档前检查入口见 [phase7_archive_preflight_checklist_2026-04-02.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-02/phase7_archive_preflight_checklist_2026-04-02.md)
