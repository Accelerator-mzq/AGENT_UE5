> 归档状态：Phase 11 历史任务副本
> 归档日期：2026-04-17
> 根目录当前入口：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
> Phase 11 收尾总览：[18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)
> 最终验收报告：[task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
> 归档发布记录：[phase11_archive_publish.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_archive_publish.md)

# Phase 11 — Skill-First Design Compiler Framework

> 目标引擎版本：UE5.5.4
> 阶段定位：Phase 11 已完成 / 收尾归档期
> 当前正式入口：本文件
> Phase 11 文档索引：[00_Phase11_Document_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/00_Phase11_Document_Index.md)
> Phase 11 交接文档：[13_Claude_Handoff_and_Reading_Order.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/13_Claude_Handoff_and_Reading_Order.md)
> Phase 11 实施任务书：[12_Implementation_Taskbook.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/12_Implementation_Taskbook.md)
> Phase 11 Schema 参考：[11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md)
> Phase 10 归档任务：[task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md)

---

## 使用说明

1. 根目录 `task.md` 是 Phase 11 当前阶段唯一开发驱动入口。
2. 每个 TASK 都必须逐个执行，不得跳过前置依赖。
3. 每个 TASK 内附“先读这些文件”，编码 Agent 动手前必须读完。
4. 每个 TASK 末尾有“验收标准”，全部通过才可进入下一个 TASK。
5. 每次宣称成功或完成，必须附对应证据文件链接。
6. PROJECT_ROOT = `D:\UnrealProjects\Mvpv4TestCodex\`。
7. PLUGIN_DIR = `Plugins/AgentBridge/`。
8. COMPILER_DIR = `Plugins/AgentBridge/Compiler/`。
9. MCP_DIR = `Plugins/AgentBridge/MCP/`。
10. SCHEMAS_DIR = `Plugins/AgentBridge/Schemas/`。

## 核心约束

- 不修改 [CLAUDE.md](/D:/UnrealProjects/Mvpv4TestCodex/CLAUDE.md) 中列出的“绝对不要修改的文件”，除非单独说明原因并获得确认。
- 不删除 Phase 10 旧 Schema：`gdd_projection.schema.json`、`planner_output.schema.json`、`skill_fragment.schema.json`、`cross_review_report.schema.json`、`build_ir.schema.json`、`reviewed_handoff_v2.schema.json`。
- 不删除旧 MCP 工具名；`compiler_intake_prepare/save` 和 `compiler_plan_prepare/save` 必须作为 alias 保留。
- `session_version` 缺失时必须视为 `"1.0"`，不得强行迁移旧 session。
- v1.0 与 v2.0 只做路由选择，不做跨版本产物格式转换。
- MCP 前端只覆盖 Root Skill Contract、Clarification Gate、Skill Graph Planning；Design Space Discovery 及后续属于 Compiler Core。
- C++ 为主，Blueprint 为薄层；Phase 11 Review 必须检查 Blueprint 薄层原则。
- 所有新增或修改代码必须带中文注释。
- 所有本地文件引用必须使用 `/D:/...` Markdown link 格式。

## 本期固定规则

1. Phase 11 第一轮主输入固定为 [GDD_MonopolyGame.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/GDD_MonopolyGame.md)。
2. TASK 11 的端到端验收目标分两层：生成完整 `ProjectState/runs/{run_id}/` v2 产物，并验证这些产物支撑 Monopoly 最小可玩闭环。
3. TASK 12-14 是第三批后置治理任务，不阻塞 TASK 11 的 Handoff v3 端到端与最小可玩闭环验收，但阻塞 Phase 11 最终完成声明。
4. TASK 14A 是 UE 运行时最小可玩性与 Baseline Domain 专项验收，未完成前不得宣称“真实游戏已可玩”。
5. TASK 15 之前不得宣称 Phase 11 完成。
6. 每个主干 TASK 完成后必须运行 `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`。
7. `Docs/Phase11/` 下每个新增功能都必须在本文件的“Phase 11 文档包功能覆盖矩阵”中有 TASK 落点。
8. TASK 15 最终验收必须输出 Phase 11 文档包功能覆盖报告，逐项说明已覆盖、证据文件、残留风险。

## Phase 11 文档包功能覆盖矩阵

| 文档 | 新增能力 / 约束 | task.md 覆盖 | 必须证据 |
|------|-----------------|--------------|----------|
| [00_Phase11_Document_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/00_Phase11_Document_Index.md) | 主链、发散创造位置、不发散位置、Phase 11 要解决的 10 类问题 | TASK 01、TASK 09A、TASK 09B、TASK 10、TASK 15 | `phase11_feature_coverage_report.md` |
| [01_Phase11_Unified_Architecture.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/01_Phase11_Unified_Architecture.md) | 7 阶段主链、MCP 前后端边界、MCP 工具收尾口径（53 可见 / 49 主工具 / 4 alias）、v1/v2 兼容、Run 隔离、GDD-First 命名 | TASK 02、TASK 03、TASK 05、TASK 10、TASK 12、TASK 15 | Session/Orchestrator/MCP/Final 验收报告 |
| [02_Root_Skill_Contract_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/02_Root_Skill_Contract_Standard.md) | Root Skill Contract 10 个问题、产物结构、Constraint/Variant 标注 | TASK 04、TASK 06、TASK 10、TASK 11 | `root_skill_contract.json`、TASK 06 报告 |
| [03_Universal_Baseline_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/03_Universal_Baseline_Standard.md) | Universal Baseline 分类、presence_only 最低标准、Settings 六项底线、realization_eligible 升级规则 | TASK 06、TASK 09B、TASK 10、TASK 11、TASK 14、TASK 14A、TASK 15 | `baseline_coverage_report`、TASK 14 报告、TASK 14A 运行时报告 |
| [04_Baseline_Realization_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/04_Baseline_Realization_Policy.md) | Baseline 三类域、模板结构、Baseline Fragment、Start Screen 能力级定义 | TASK 06、TASK 08、TASK 09B、TASK 14、TASK 14A | Baseline Fragment、模板报告、运行时验收报告 |
| [05_Clarification_Gate_Rules.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/05_Clarification_Gate_Rules.md) | 4 档决策、provisional 传播、fast_mode 高风险保护、人类参与点 | TASK 07、TASK 10、TASK 13 | `clarification_gate_report.json`、Handoff v3 provisional 汇总 |
| [06_Constraint_vs_Variant_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/06_Constraint_vs_Variant_Policy.md) | Constraint/Variant 判据、不可拆分、下游保持性、Variant bounds 传播 | TASK 06、TASK 09B、TASK 10、TASK 11 | Constraint 保持性报告、bounds 校验 |
| [07_Design_Space_Discovery_and_Realization.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/07_Design_Space_Discovery_and_Realization.md) | Discovery、Candidates、Convergence、design_decision_log、质量检查、fast_mode 行为 | TASK 09B、TASK 11、TASK 13 | Discovery/Candidates/Convergence 报告 |
| [08_Skill_Graph_and_Domain_Skill.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md) | Skill Graph 节点/边、Domain Skill 四重职责、Baseline/GamePlay 同构、SkillTemplates vs Skills、生命周期 | TASK 08、TASK 09B、TASK 14、TASK 14A | `skill_graph.json`、runtime 生命周期报告、UE 运行时验收报告 |
| [09_Run_Isolation_Compare_Promote.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/09_Run_Isolation_Compare_Promote.md) | Run Workspace、metadata、promotable、Compare、Promote、fast_mode 隔离、清理策略 | TASK 02、TASK 11、TASK 12、TASK 13 | Run metadata、comparison、batch、promotion 报告 |
| [10_Naming_and_Path_Convention.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/10_Naming_and_Path_Convention.md) | GDD-First 四层命名、UE5 路径/前缀、naming_resolution_log、C++ 主逻辑 + Blueprint 薄层、命名冲突 | TASK 10、TASK 11、TASK 15 | `naming_resolution_log.json`、Cross Review 报告 |
| [11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md) | 14 个 Schema、MCP 工具变更、v2 Run 产物目录、Stage/Artifact Map | TASK 04、TASK 05、TASK 10、TASK 11、TASK 12、TASK 15 | Schema 校验、MCP tools/list、E2E run 目录 |
| [12_Implementation_Taskbook.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/12_Implementation_Taskbook.md) | 分批策略、关键路径、实施约束、测试策略 | TASK 01-15 | TASK 证据报告汇总 |
| [13_Claude_Handoff_and_Reading_Order.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/13_Claude_Handoff_and_Reading_Order.md) | 强制阅读顺序、不可跳过前置、绝对不可做、常见陷阱 | 每个 TASK 的”先读这些文件”、TASK 15 | `phase11_feature_coverage_report.md` |
| [14_Agent_Interaction_Protocol.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/14_Agent_Interaction_Protocol.md) | Prompt-First 硬约束、GeneratorProvider 抽象、Generator-Evaluator gate、Context Bundle、LLM/Heuristic 三路决策、SkillTemplate prompt 结构 | TASK 09A、TASK 09B、TASK 10、TASK 11、TASK 13、TASK 14 | Provider 类型记录、promotable 判定、Stage 4 执行报告 |

## 里程碑定义

| 里程碑 | 内容 | 对应 TASK | 状态 |
|--------|------|-----------|------|
| M1 | 文档切换与任务入口重建 | TASK 01 | ✅ 已完成 |
| M2 | Session v2 + Pipeline v2 路由 | TASK 02-03 | ✅ 已完成 |
| M3 | Phase 11 Schema 第一批 | TASK 04 | ✅ 已完成 |
| M4 | MCP 前端工具重命名、alias 与 Clarification 工具 | TASK 05 | ✅ 已完成 |
| M5 | Root Skill / Clarification / Skill Graph 真实生成 | TASK 06-08 | ✅ 已完成 |
| M6 | LLM Client 接入 + Domain Skill Runtime + Design Space / Realization / Convergence | TASK 09A-09B | ✅ 当前阶段已完成（LLM Internal 暂缓，待 llm_client 框架升级后重开） |
| M7 | Cross Review v2 + Build IR v2 + Handoff v3 | TASK 10 | ✅ 已完成 |
| M8 | Monopoly GDD v2 端到端 run 与最小可玩闭环验收 | TASK 11 | ✅ 已完成 |
| M9 | Defer 治理项：run compare/promote、完整 fast_mode、Baseline Template 全套 | TASK 12-14 | ✅ 已完成 |
| M9A | UE 运行时最小可玩性与 Baseline Domain 验收 | TASK 14A | ✅ 已完成 |
| M10 | 最终验收、证据归档、文档收尾 | TASK 15 | ✅ 已完成 |

## 任务总览

第一批：阶段口径与 v2 骨架（TASK 01-05）  
第二批：Design Compiler 主链真实生成（TASK 06-11）  
第三批：后置治理与高级能力（TASK 12-14）  
第四批：UE 运行时验收（TASK 14A）  
第五批：最终验收与文档收尾（TASK 15）

---

# 第一批：阶段口径与 v2 管线骨架

## TASK 01：Phase 11 文档切换与任务入口重建

状态：✅ 已完成  
证据：[task01_phase11_document_switch.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task01_phase11_document_switch.md)

目标：将项目根目录 `task.md` 切换为 Phase 11 当前阶段唯一任务入口，并同步当前阶段文档口径。

前置依赖：无。

先读这些文件：
- [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md)
- [CLAUDE.md](/D:/UnrealProjects/Mvpv4TestCodex/CLAUDE.md)
- [00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [00_Phase11_Document_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/00_Phase11_Document_Index.md)
- [13_Claude_Handoff_and_Reading_Order.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/13_Claude_Handoff_and_Reading_Order.md)
- [task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task10_phase10.md)

涉及文件：
- [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [Docs/Current/02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md)

Step：
1. 重建 `task.md`，写入使用说明、核心约束、里程碑、任务总览与 TASK 01-15。
2. 建立 Phase 11 文档包功能覆盖矩阵，确保 `Docs/Phase11/00-13` 每份文档都有 TASK 落点。
3. 将 `Docs/Current/00_Index.md` 从 Phase 10 Completed 口径更新为 Phase 11 Active 口径。
4. 将 `Docs/Current/02_Current_Phase_Goals.md` 更新为 Phase 11 当前目标。
5. 在 `ProjectState/Reports/<date>/` 下生成 Phase 11 文档切换报告。

验收标准：
- `task.md` 不再是 Phase 10 占位页。
- `task.md` 包含 TASK 01-15。
- `task.md` 包含 Phase 11 文档包功能覆盖矩阵。
- `Docs/Phase11/00-13` 每份文档都能在覆盖矩阵中找到 TASK 落点。
- TASK 12-14 已写入，不再被隐藏为“暂不实现”。
- `Docs/Current/00_Index.md` 指向 Phase 11 当前入口。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 02：Session v2 字段扩展与 `compiler_session.schema.json` 兼容升级

状态：✅ 已完成  
证据：[task02_phase11_session_v2_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task02_phase11_session_v2_validation.md)

目标：扩展 Compiler Session，使同一套 session 机制同时支持 Phase 10 v1.0 与 Phase 11 v2.0。

前置依赖：TASK 01 完成。

先读这些文件：
- [session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py)
- [compiler_session.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/compiler_session.schema.json)
- [01_Phase11_Unified_Architecture.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/01_Phase11_Unified_Architecture.md)
- [09_Run_Isolation_Compare_Promote.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/09_Run_Isolation_Compare_Promote.md)

涉及文件：
- [session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py)
- [compiler_session.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/compiler_session.schema.json)

Step：
1. 新增 `session_version`，默认 `"1.0"`。
2. 新增 `run_id`，v2.0 session 必须有，格式为 `run-{yyyyMMdd}-{HHmmss}-{short_hash}`。
3. 新增 `fast_mode`，默认 `false`。
4. 新增 `generator_provider`（可选，枚举 `"llm"` / `"mcp_agent"` / `"heuristic_fallback"`），Stage 4 完成后由 pipeline_orchestrator 自动写入，影响 `is_promotable` 判定。
5. v1.0 最大 stage 仍为 5，v2.0 最大 stage 为 7。
6. 升级 Schema，使旧 session 可 load，新 session 可校验。

验收标准：
- v1.0 session 创建、保存、load 全部通过。
- v2.0 session 创建、保存、load 全部通过。
- v2.0 session 自动生成或接受合法 `run_id`，非法 `run_id` 会被拒绝或写入明确错误。
- 缺失 `session_version` 的旧 session 不报错。
- `compiler_session.schema.json` 同时兼容旧字段与新字段。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 03：Pipeline Orchestrator v1/v2 stage map 与 artifact map 路由

状态：✅ 已完成  
证据：[task03_phase11_pipeline_v2_routing.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task03_phase11_pipeline_v2_routing.md)

目标：在 `pipeline_orchestrator.py` 中增加 Phase 11 v2.0 七阶段路由，同时保持 Phase 10 v1.0 五阶段不变。

前置依赖：TASK 02 完成。

先读这些文件：
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)
- [01_Phase11_Unified_Architecture.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/01_Phase11_Unified_Architecture.md)
- [11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md)

涉及文件：
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)

Step：
1. 保留并命名 v1 映射：`STAGE_NAME_MAP_V1`、`STAGE_ARTIFACT_MAP_V1`。
2. 新增 v2 阶段：`root_skill_contract`、`clarification_gate`、`skill_graph_planning`、`domain_skill_runtime`、`cross_domain_review`、`lowering`、`handoff_assembly`。
3. 新增 v2 artifact map，输出到 `ProjectState/runs/{run_id}/`。
4. 新增 `get_stage_name_map()`、`get_stage_artifact_map()`、`get_max_stage()`。
5. 所有 prepare/save/run/assemble 入口按 `session_version` 路由。

验收标准：
- v1 五阶段 prepare/save 不回归。
- v2 七阶段路由可识别。
- v2 stage 7 合法，v1 stage 7 非法。
- v2 artifact map 覆盖 metadata、root_skill_contract、clarification_gate_report、skill_graph、design_space_report、realization_candidates、converged_realization_pack、skill_fragments、cross_review_report、build_ir、reviewed_handoff_v3、naming_resolution_log。
- 旧产物格式不被转换。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 04：新增第一批 7 个 Schema，并补充示例校验

状态：✅ 已完成  
证据：[task04_phase11_schema_batch1_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task04_phase11_schema_batch1_validation.md)

目标：新增 Phase 11 第一批管线骨架 Schema，让 v2.0 各阶段产物有明确结构约束。

前置依赖：TASK 02 可并行，TASK 03 前后均可执行。

先读这些文件：
- [02_Root_Skill_Contract_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/02_Root_Skill_Contract_Standard.md)
- [05_Clarification_Gate_Rules.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/05_Clarification_Gate_Rules.md)
- [07_Design_Space_Discovery_and_Realization.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/07_Design_Space_Discovery_and_Realization.md)
- [08_Skill_Graph_and_Domain_Skill.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md)
- [11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md)

涉及文件：
- `Plugins/AgentBridge/Schemas/root_skill_contract.schema.json`
- `Plugins/AgentBridge/Schemas/clarification_gate_report.schema.json`
- `Plugins/AgentBridge/Schemas/skill_graph.schema.json`
- `Plugins/AgentBridge/Schemas/design_space_report.schema.json`
- `Plugins/AgentBridge/Schemas/realization_candidates.schema.json`
- `Plugins/AgentBridge/Schemas/converged_realization_pack.schema.json`
- `Plugins/AgentBridge/Schemas/skill_fragment_v2.schema.json`
- `Plugins/AgentBridge/Schemas/examples/phase11_*.example.json`

Step：
1. 创建 7 个 draft-07 Schema。
2. 每个 Schema 只约束核心结构，避免过度设计。
3. 每个 Schema 至少创建一个 Monopoly 上下文 example。
4. 接入或补充 Phase 11 Schema 校验脚本。

验收标准：
- 7 个新 Schema 文件存在。
- 7 个 example 文件存在。
- 每个 example 均通过对应 Schema 校验。
- 旧 Schema 文件全部保留。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 05：MCP 前端工具重命名、旧名 alias、Clarification prepare/save

状态：✅ 已完成  
证据：[task05_phase11_mcp_frontend_tools.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task05_phase11_mcp_frontend_tools.md)

目标：将 MCP 前端从 Phase 10 的 intake/plan 命名升级到 Phase 11 的 root_skill/clarification/skill_graph 命名，同时保留旧名 alias。

前置依赖：TASK 02-04 完成。

先读这些文件：
- [compiler_tools.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/compiler_tools.py)
- [tool_definitions.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/tool_definitions.py)
- [server.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/server.py)
- [01_Phase11_Unified_Architecture.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/01_Phase11_Unified_Architecture.md)

涉及文件：
- [compiler_tools.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/compiler_tools.py)
- [tool_definitions.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/tool_definitions.py)
- [server.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/server.py)

Step：
1. `compiler_create_session` 支持可选 `session_version` 和 `run_id`。
2. 新增 `compiler_root_skill_prepare/save`。
3. 新增 `compiler_clarification_prepare/save`。
4. 新增 `compiler_skill_graph_prepare/save`。
5. 保留 `compiler_intake_prepare/save` 和 `compiler_plan_prepare/save` 作为 alias。
6. 更新 MCP 注册与 dispatch。

验收标准：
- 新工具名可见、可调用。
- 旧工具名仍可见、可调用。
- `compiler_create_session` 可创建 v1 与 v2 session。
- MCP 前端 6 个工具可见、可调用：root_skill prepare/save、clarification prepare/save、skill_graph prepare/save。
- `compiler_intake_prepare/save` 与 `compiler_plan_prepare/save` alias 功能等价。
- MCP 工具总数在收尾时已按实现事实完成对齐：当前 `TOOL_DISPATCH` 与 `ALL_TOOLS` 均为 `53` 个可见工具，其中 `49` 个为正式主工具，`4` 个为兼容 alias。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

# 第二批：Design Compiler 主链真实生成

## TASK 06：Root Skill Contract 生成逻辑

状态：✅ 已完成  
证据：[task06_phase11_root_skill_contract_generation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task06_phase11_root_skill_contract_generation.md)

目标：实现 Phase 11 Stage 1 的真实 Root Skill Contract 生成逻辑，不只返回空模板。

前置依赖：TASK 02-05 完成。

先读这些文件：
- [02_Root_Skill_Contract_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/02_Root_Skill_Contract_Standard.md)
- [03_Universal_Baseline_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/03_Universal_Baseline_Standard.md)
- [04_Baseline_Realization_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/04_Baseline_Realization_Policy.md)
- [06_Constraint_vs_Variant_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/06_Constraint_vs_Variant_Policy.md)
- [GDD_MonopolyGame.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/GDD_MonopolyGame.md)

涉及文件：
- `Plugins/AgentBridge/Compiler/stages/root_skill_contract.py`
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)

Step：
1. 创建 root_skill_contract stage 模块。
2. 从 GDD 提取游戏类型、玩家人数、胜负条件、棋盘格子数、回合制核心循环。
3. 标注 Constraint Fields 与 Variant Fields。
4. 合并 Universal Baseline，标注 presence_only / realization_eligible / clarification_gated。
5. 回答 Root Skill Contract 标准中的 10 个问题，并写入可审计字段。
6. 对 Universal Baseline 的 7 类基础能力建立覆盖记录：启动入口、前台壳层、设置配置、输入基础、HUD/Popup/结果表达、音频基础、平台基础。
7. 输出并校验 `root_skill_contract.json`。

验收标准：
- `root_skill_contract.json` 非空。
- `constraint_fields` 非空。
- `variant_fields` 非空。
- Root Skill Contract 的 10 个问题均有明确答案或 clarification 标记。
- `baseline_capabilities` 覆盖 Universal Baseline 7 类基础能力。
- Start Screen、Main Menu、Settings、Pause、Results、HUD 六个最低 Baseline 项均存在。
- Settings 明确包含 Master Volume、SFX Volume、Window Mode、Resolution、Apply、Back 六项不可删减底线。
- 每个 Baseline 项均标注 presence_only / realization_eligible / clarification_gated，且升级只能 presence_only -> realization_eligible。
- 所有设计元素已标注 Constraint 或 Variant。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 07：Clarification Gate 执行逻辑与 provisional 传播

状态：✅ 已完成  
证据：[task07_phase11_clarification_gate.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task07_phase11_clarification_gate.md)

目标：实现 Phase 11 Stage 2 的 Clarification Gate，对缺失、含糊、冲突、高风险项做 4 档处置。

前置依赖：TASK 06 完成。

先读这些文件：
- [05_Clarification_Gate_Rules.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/05_Clarification_Gate_Rules.md)
- [06_Constraint_vs_Variant_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/06_Constraint_vs_Variant_Policy.md)
- `Plugins/AgentBridge/Schemas/root_skill_contract.schema.json`

涉及文件：
- `Plugins/AgentBridge/Compiler/stages/clarification_gate.py`
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)

Step：
1. 创建 clarification_gate stage 模块。
2. 实现 `accept_as_explicit`、`accept_with_safe_default`、`send_to_design_space_discovery`、`clarification_required`。
3. 实现 low / medium / high / critical 风险分级。
4. high 保持 clarification_required，critical 阻塞。
5. provisional 值写入下游 input_context，并规定 Fragment、Build IR、Handoff v3 的传播字段。

验收标准：
- `clarification_gate_report.json` 非空。
- items 覆盖 Monopoly GDD 中的缺失或含糊项。
- 4 档决策至少覆盖 2 种实际结果。
- high/critical 不被 fast_mode 自动默认。
- provisional_items 可被下游读取。
- 使用 provisional 值的 Fragment 必须在 `design_decision_log` 标记 `provisional: true`。
- 使用 provisional 值的 Build IR action 必须在 execution_hints 标记 `contains_provisional: true`。
- Handoff v3 必须汇总所有 `provisional_items`。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 08：Skill Graph Planning 逻辑

状态：✅ 已完成  
证据：[task08_phase11_skill_graph_planning.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task08_phase11_skill_graph_planning.md)

目标：实现 Phase 11 Stage 3 的 Skill Graph Planning，从 Root Skill Contract 与 Clarification Gate 派生 Domain Skill 图。

前置依赖：TASK 07 完成。

先读这些文件：
- [08_Skill_Graph_and_Domain_Skill.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md)
- [04_Baseline_Realization_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/04_Baseline_Realization_Policy.md)
- `Plugins/AgentBridge/Schemas/skill_graph.schema.json`

涉及文件：
- `Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py`
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)

Step：
1. 创建 skill_graph_planning stage 模块。
2. 生成 gameplay skills：board_topology、tile_system、turn_loop、economy、dice、player_management。
3. 生成 baseline skills：start_screen、main_menu、settings、pause、results、hud。
4. 生成 dependency、coupling、convergence_order 三类边。
5. 为每个节点写入 `template_id`、`allows_design_space_discovery`、`convergence_priority`、依赖、耦合。
6. 区分 SkillTemplates（插件层模板）与 Skill Instance（运行时对象），不得把项目实例写回模板目录。
7. 输出并校验 `skill_graph.json`。

验收标准：
- `skill_graph.json` 非空。
- gameplay nodes 数量 >= 6。
- baseline nodes 数量 >= 6。
- edges 非空，且包含 dependency、coupling、convergence_order。
- 每个节点均包含 `template_id`、`allows_design_space_discovery`、`convergence_priority`。
- presence_only baseline 节点 `allows_design_space_discovery = false`。
- realization_eligible baseline 节点 `allows_design_space_discovery = true`。
- Skill Graph 只描述“谁先做、谁关联、谁收敛优先”，不得包含具体 realization 选择。
- 不包含提前写死的 realization 字段。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 09A：LLM Internal 路径接入（llm_client 实现）

状态：✅ 已完成  
证据：[task09a_phase11_llm_internal.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09a_phase11_llm_internal.md)

目标：实现多 provider 兼容的 LLM 客户端，使 LLM Internal 路径可用，为 TASK 09B 的三路 Generator 验证提供基础。

前置依赖：TASK 08 完成。

先读这些文件：
- [14_Agent_Interaction_Protocol.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/14_Agent_Interaction_Protocol.md)（§4.0 三条路径、§4.1 调用流程）
- `Plugins/AgentBridge/Compiler/stages/agent_protocol.py`（LLMProvider 类：399-520 行，resolve_provider 函数：592-616 行）
- `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py`（Stage 4 调用处，当前 llm_client=None，约 684 行）

涉及文件：
- `Plugins/AgentBridge/Compiler/stages/llm_client.py`（新增：UnifiedLLMClient + load_llm_client_from_config）
- `Plugins/AgentBridge/Config/llm_config.example.yaml`（新增：配置模板，提交到仓库）
- `Plugins/AgentBridge/Config/llm_config.yaml`（新增：实际配置，含 API key，gitignore）
- `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py`（修改：llm_client=None → llm_client=load_llm_client_from_config()）
- `Plugins/AgentBridge/Compiler/pipeline/session.py`（修改：VALID_GENERATOR_PROVIDERS 扩展加入 "mcp_agent"）
- [.gitignore](/D:/UnrealProjects/Mvpv4TestCodex/.gitignore)（修改：添加 llm_config.yaml 忽略规则）

### 配置文件规格

**路径**：`Plugins/AgentBridge/Config/llm_config.yaml`（实际配置，含 API key，**必须 gitignore**）
**模板**：`Plugins/AgentBridge/Config/llm_config.example.yaml`（提交到仓库，不含真实 key）

```yaml
# llm_config.example.yaml — LLM Internal 路径配置模板
# 复制为 llm_config.yaml 并填入真实 API key 后使用

# provider 类型：anthropic / openai / openai_compatible
provider: "anthropic"

# API key（必填）
api_key: "YOUR_API_KEY_HERE"

# 模型名（可配置，按 provider 不同填写对应模型 ID）
model: "claude-sonnet-4-20250514"

# 可选：自定义 API base URL（仅 openai_compatible 需要）
# 用于接入本地模型（Ollama, vLLM, LM Studio 等）或第三方代理
# base_url: "http://localhost:11434/v1"

# 可选：生成参数
max_tokens: 8192
temperature: 0.7
```

**三种 provider 配置示例**：

```yaml
# Anthropic（Claude 系列）
provider: "anthropic"
api_key: "sk-ant-api03-..."
model: "claude-sonnet-4-20250514"

# OpenAI（GPT 系列）
provider: "openai"
api_key: "sk-..."
model: "gpt-4o"

# OpenAI 兼容接口（本地模型、第三方代理等）
provider: "openai_compatible"
api_key: "not-needed"
model: "llama3"
base_url: "http://localhost:11434/v1"
```

### 客户端代码接口规格

**文件**：`Plugins/AgentBridge/Compiler/stages/llm_client.py`

```python
class UnifiedLLMClient:
    """统一 LLM 客户端 — 兼容 Anthropic / OpenAI / OpenAI-Compatible。"""

    def __init__(self, provider, api_key, model, base_url=None, max_tokens=8192, temperature=0.7):
        ...

    def call(self, messages: list[dict]) -> str:
        """
        调用 LLM。

        参数:
          messages: [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]

        返回:
          LLM 生成的文本（str）

        内部按 provider 类型分发：
          - anthropic: 用 anthropic.Anthropic().messages.create()
                       注意 Anthropic API 的 system 不在 messages 里，需提取到 system 参数
          - openai / openai_compatible: 用 openai.OpenAI().chat.completions.create()
                       openai_compatible 需传 base_url
        """
        ...


def load_llm_client_from_config(config_path: str | Path = None) -> UnifiedLLMClient | None:
    """
    从配置文件加载 LLM 客户端。

    查找顺序：
      1. 显式传入的 config_path
      2. AGENT_BRIDGE_LLM_CONFIG 环境变量
      3. Plugins/AgentBridge/Config/llm_config.yaml（相对于插件目录）

    配置文件不存在或 api_key 为占位符时返回 None（不报错，让 resolve_provider 走后续路径）。
    """
    ...
```

**依赖管理**：`anthropic` 和 `openai` 是可选依赖，缺包不报错：
```python
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
```

配置了 `provider: "anthropic"` 但未安装 `anthropic` 包时，`load_llm_client_from_config()` 应返回 None 并打印警告。

### 接入点

**`pipeline_orchestrator.py`** Stage 4 调用处（当前约 684 行）：

```python
# 当前代码
llm_client=None,

# 改为
from ..stages.llm_client import load_llm_client_from_config
llm_client=load_llm_client_from_config(),
```

### generator_provider 值扩展

`session.py` 中 `VALID_GENERATOR_PROVIDERS` 从 `{"llm", "heuristic_fallback"}` 扩展为：

```python
VALID_GENERATOR_PROVIDERS = {"llm", "mcp_agent", "heuristic_fallback"}
```

`is_promotable` 判定不变：只有 `heuristic_fallback` 为 False。

Step：
1. 创建 `Plugins/AgentBridge/Config/llm_config.example.yaml`，按上述配置文件规格。
2. 创建 `Plugins/AgentBridge/Compiler/stages/llm_client.py`，按上述客户端代码接口规格实现 `UnifiedLLMClient` + `load_llm_client_from_config`。
3. 修改 `pipeline_orchestrator.py` Stage 4 调用处，按上述接入点说明替换 `llm_client=None`。
4. 修改 `session.py`，按上述 generator_provider 值扩展说明扩展 `VALID_GENERATOR_PROVIDERS`。
5. 修改 `.gitignore`，添加 `Plugins/AgentBridge/Config/llm_config.yaml`。
6. 验证：无配置文件时行为不变（走 heuristic fallback）；有有效配置时走 LLMProvider 路径。

验收标准：
- `llm_config.example.yaml` 存在且已提交，包含 anthropic / openai / openai_compatible 三种配置示例。
- `llm_config.yaml` 被 `.gitignore` 忽略。
- `llm_client.py` 支持 anthropic / openai / openai_compatible 三种 provider。
- 缺少对应 SDK 包时 `load_llm_client_from_config()` 返回 None，不报错。
- 配置文件不存在时 `load_llm_client_from_config()` 返回 None，不报错。
- `pipeline_orchestrator.py` 调用 `load_llm_client_from_config()` 替代硬编码 `None`。
- 有有效配置时 Stage 4 走 LLMProvider，产物 metadata 标记 `generator_type: "llm"`, `promotable: true`。
- 无配置时 MCP Agent 路径和 Heuristic Fallback 路径不受影响。
- `VALID_GENERATOR_PROVIDERS` 包含 `"mcp_agent"`。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 09B：Domain Skill Runtime、Discovery、Candidates、Convergence、Fragment v2

状态：✅ 当前阶段已完成（LLM Internal 暂缓，待 llm_client 框架升级后重开）  
证据：[task09b_phase11_three_provider_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09b_phase11_three_provider_validation.md)  
补充诊断：[stage4_candidates_prompt_vs_provider_diagnostic.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic.md)  
补充双跑：[mcp_agent_dual_run_variation_test.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/mcp_agent_dual_run_variation_test.md)  
旧证据：[task09_phase11_domain_skill_runtime.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-15/task09_phase11_domain_skill_runtime.md)（历史版本，不完整，缺 LLM Internal 和 MCP Agent 路径验证）

> **当前阶段完成结论**：MCP Agent 与 Heuristic Fallback 已通过；LLM Internal 已完成接入与诊断，但当前 `llm_client` / LLM Internal 链路不足以稳定承载高负载 `Candidates` prompt，按当前治理口径暂不继续测试，待后续 `llm_client` 框架升级后重开严格验收。
> 
> **本次正式验收已覆盖**：
> - `MCP Agent` 路径：至少一次成功运行，`generator_provider = "mcp_agent"`，`promotable = true`
> - `Heuristic Fallback` 路径：至少一次成功运行，`generator_provider = "heuristic_fallback"`，`promotable = false`
> - Stage 4 四类主产物：`design_space_report.json`、`realization_candidates.json`、`converged_realization_pack.json`、`skill_fragments/*.json`
> - `LLM Internal` 路径：当前只保留接入证据与高负载诊断证据；暂停原因见补充诊断报告，不再继续追加正式 run 证据

目标：实现 Domain Skill Runtime，使每个 Skill Instance 能按职责执行 Discovery、Candidates、Convergence，并生成 Fragment v2。

前置依赖：TASK 08 完成，TASK 09A 完成。

先读这些文件：
- [03_Universal_Baseline_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/03_Universal_Baseline_Standard.md)
- [04_Baseline_Realization_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/04_Baseline_Realization_Policy.md)
- [06_Constraint_vs_Variant_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/06_Constraint_vs_Variant_Policy.md)
- [07_Design_Space_Discovery_and_Realization.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/07_Design_Space_Discovery_and_Realization.md)
- [08_Skill_Graph_and_Domain_Skill.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md)
- [14_Agent_Interaction_Protocol.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/14_Agent_Interaction_Protocol.md)
- [15_Claude_Code_Handoff_to_Codex.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/15_Claude_Code_Handoff_to_Codex.md)

涉及文件：
- `Plugins/AgentBridge/Compiler/stages/agent_protocol.py`（GeneratorProvider 抽象 + LLMProvider + HeuristicFallbackProvider）
- `Plugins/AgentBridge/Compiler/stages/llm_client.py`（TASK 09A 产出）
- `Plugins/AgentBridge/Compiler/stages/discovery_fallback.py`（原 discovery_engine.py，降级为 heuristic fallback）
- `Plugins/AgentBridge/Compiler/stages/realization_fallback.py`（原 realization_generator.py，降级为 heuristic fallback）
- `Plugins/AgentBridge/Compiler/stages/convergence_fallback.py`（原 convergence_engine.py，降级为 heuristic fallback）
- `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`（含 `prepare_node_phase` / `save_node_phase` MCP 交互入口）
- `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py`
- [compiler_tools.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/compiler_tools.py)（+`compiler_stage4_node_prepare` / `compiler_stage4_node_save`）
- [tool_definitions.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/tool_definitions.py)（+2 工具定义）
- [server.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/server.py)（+2 工具注册）
- `ProjectState/Reports/<date>/task09_phase11_domain_skill_runtime.md`

Step：
1. ~~新增 `agent_protocol.py`~~ ✅ 已完成（Claude Code）。
2. ~~新增 `discovery_fallback.py`~~ ✅ 已完成（Codex + Claude Code 重命名）。
3. ~~新增 `realization_fallback.py`~~ ✅ 已完成（Codex + Claude Code 重命名）。
4. ~~新增 `convergence_fallback.py`~~ ✅ 已完成（Codex + Claude Code 重命名）。
5. ~~新增 `domain_skill_runtime.py`~~ ✅ 已完成（Codex + Claude Code 增加 MCP 入口）。
6. ~~更新 `pipeline_orchestrator.py`~~ ✅ 已完成（Claude Code）。
7. ~~新增 MCP 交互式工具~~ ✅ 已完成（Claude Code）。
8. ~~更新 `tool_definitions.py` 和 `server.py`~~ ✅ 已完成（Claude Code）。
9. 运行三路 Generator 验证：
   - 9a. LLM Internal 路径：当前暂停继续测试；保留接入证据与高负载诊断报告，待 `llm_client` 框架升级后，按严格口径重新开启 `generator_type: "llm"` + `promotable: true` 回归验收。
   - 9b. MCP Agent 路径：调用 `compiler_stage4_node_prepare` → Agent 生成 → `compiler_stage4_node_save`，验证 `generator_type: "mcp_agent"` + `promotable: true`。
   - 9c. Heuristic Fallback 路径：无配置 + `allow_heuristic_fallback=True`，验证 `generator_type: "heuristic_fallback"` + `promotable: false`。
10. 更新 TASK 09 证据报告，覆盖当前已完成路径与 `LLM Internal` 暂停依据。

验收标准：
- `design_space_report.json` 非空。
- `realization_candidates.json` 非空。
- `converged_realization_pack.json` 非空。
- `skill_fragments/*.json` 存在。
- 每个运行过的 Skill Instance 都有 lifecycle status，failed 节点必须有 `failure_reason`。
- 每个 gameplay 与 realization_eligible baseline 节点均完成 Domain Skill 四重职责。
- Discovery 不是从固定枚举 options 里选择；报告必须体现 Agent 主动发现维度。
- locked_dimensions 与 Root Skill Contract 的 Constraint Fields 一致。
- 所有 realization candidate 必须满足 Variant bounds。
- Convergence 的每个选择必须有 rationale、rejected_alternatives、provisional 标记。
- 至少一个 gameplay fragment 的 `design_decision_log` 非空。
- design_decision_log 只记录非平凡决策，不记录纯格式/命名选择。
- presence_only baseline fragment 可为空 log，但必须说明 basis。
- realization_eligible baseline 进入完整 Discovery -> Candidates -> Convergence。
- **Prompt-First 硬约束**：SkillTemplate prompt 文件是 Generator 唯一设计知识来源，代码不得硬编码维度/候选/收敛逻辑。
- **GeneratorProvider 三路决策**：有 LLM → LLMProvider；无 LLM + allow_fallback → HeuristicFallbackProvider；无 LLM + 不允许 fallback → ProviderNotAvailable 拒绝 Stage 4。
- **Heuristic fallback 自动降级标记**：heuristic_fallback 运行的产物必须标记 `generator_type: "heuristic_fallback"` 且 `promotable: false`。
- **Generator-Evaluator gate**：Stage 4 每个阶段（Discovery/Candidates/Convergence）均通过 AgentPhaseRunner 的 Gen→Eval 循环执行，max_retries=2。
- `generator_provider_type` 记录到 session，影响 `is_promotable` 判定。
- **MCP 交互式工具**：`compiler_stage4_node_prepare` 返回 SkillTemplate prompts + Context Bundle + 生成指引；`compiler_stage4_node_save` 校验 Agent 输出，convergence 完成后自动生成 Fragment。
- **MCP Agent 模式**：通过 MCP 工具逐节点交互时，metadata 标记 `generator_type: "mcp_agent"`，`promotable: true`。
- **LLM Internal 模式**：通过 `llm_config.yaml` 配置 LLM client，pipeline 内嵌调用时，metadata 标记 `generator_type: "llm"`，`promotable: true`。
- **当前阶段暂停口径**：`LLM Internal` 当前不再继续测试，也不作为本轮 TASK 09B 继续追加 run 的条件；恢复条件是后续 `llm_client` 框架升级完成，并重新开启严格回归。
- **严格 LLM Internal 验收（恢复测试后执行）**：只要任一 Stage 4 entry 出现 `parse_error`，就不能算 LLM Internal 验收通过。
- **严格内容非空校验（恢复测试后执行）**：`LLM Internal` 必须同时满足 `discovery_dimensions` 非空、`candidates` 非空、`converged_choices` 非空。
- **严格 fragment 校验（恢复测试后执行）**：discovery-capable fragment 的 `selected_realization` 不能为空，且至少部分 discovery-capable fragment 的 `design_decision_log` 非空。
- **当前证据要求**：证据报告必须覆盖 MCP Agent、Heuristic Fallback 两条已完成路径，并附 `LLM Internal` 暂停诊断依据。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 10：Cross Review v2、Build IR v2、naming_resolution_log、Handoff v3

目标：实现 Phase 11 Stage 5-7，将 Fragment v2 收敛为 Reviewed Dynamic Spec Tree，再 lowering 为 Build IR v2，最后组装 Reviewed Handoff v3。

前置依赖：TASK 09B 完成。

先读这些文件：
- [01_Phase11_Unified_Architecture.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/01_Phase11_Unified_Architecture.md)
- [10_Naming_and_Path_Convention.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/10_Naming_and_Path_Convention.md)
- [11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md)
- [14_Agent_Interaction_Protocol.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/14_Agent_Interaction_Protocol.md)

涉及文件：
- `Plugins/AgentBridge/Compiler/stages/cross_review_v2.py`
- `Plugins/AgentBridge/Compiler/stages/lowering_v2.py`
- `Plugins/AgentBridge/Compiler/stages/handoff_v3.py`
- `Plugins/AgentBridge/Schemas/cross_review_report_v2.schema.json`
- `Plugins/AgentBridge/Schemas/build_ir_v2.schema.json`
- `Plugins/AgentBridge/Schemas/reviewed_handoff_v3.schema.json`
- `Plugins/AgentBridge/Schemas/naming_resolution_log.schema.json`
- `Plugins/AgentBridge/Schemas/design_decision_log.schema.json`

状态：✅ 已完成  
证据：[task10_phase11_review_lowering_handoff_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task10_phase11_review_lowering_handoff_validation.md)

Step：
1. Cross Review v2 检查跨域 realization 冲突、设计连贯性、Baseline 覆盖、Constraint 保持性、Blueprint 薄层原则。
2. Build IR v2 生成 gameplay 与 baseline build steps。
3. 每个 build step 必须包含 naming_resolution_log。
4. naming_resolution_log 按 GDD-First 四层优先级记录 resolved、tier、evidence、alternatives_considered。
5. Build IR v2 遵循 UE5 Content 路径、资产前缀、C++ 类名前缀规范。
6. Cross Review v2 检查 Blueprint 薄层阈值：逻辑节点数、循环逻辑、条件分支深度，并输出 `bp_thickness_warning`。
7. Cross Review v2 检查 Universal Baseline 覆盖，缺失最低 Baseline 项时输出 blocker。
8. Handoff v3 汇总 run_id、design_directions_summary、constraint_variant_summary、baseline_coverage_summary、provisional_items、design_decision_log_summary。

验收标准：
- 5 个第二批 Schema 存在并有 example：cross_review_report_v2、build_ir_v2、reviewed_handoff_v3、naming_resolution_log、design_decision_log。
- `cross_review_report.json` 包含 Constraint 保持性检查。
- `cross_review_report.json` 包含 Blueprint 薄层检查。
- `cross_review_report.json` 包含 Baseline 覆盖检查，缺失 Universal Baseline 最低项时为 blocker。
- `cross_review_report.json` 能检测跨域命名冲突与 realization 冲突。
- `build_ir.json` 每个 action 都有 naming_resolution_log。
- 每个 naming_resolution_log 至少包含 `resolved`、`tier`、`evidence`，tier 只能为 1-4。
- Tier 1 命名不可被下游修改；Tier 2-4 命名可记录替代方案。
- Build IR 的资产路径与前缀符合 [10_Naming_and_Path_Convention.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/10_Naming_and_Path_Convention.md)。
- Build IR 中核心玩法逻辑必须落到 C++，Blueprint 仅承载资产绑定、布局、简单事件响应。
- `reviewed_handoff_v3.json` 包含 `baseline_coverage_summary`、`constraint_variant_summary`、`provisional_items`、`design_decision_log_summary`。
- `reviewed_handoff_v3.json` 通过 schema 校验。
- provisional_items 可追踪。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 11：Monopoly GDD v2 端到端 run、产物与最小可玩闭环验收

目标：使用 [GDD_MonopolyGame.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/GDD_MonopolyGame.md) 跑通 Phase 11 v2.0 完整主链，并验证核心产物完整、非空、可追溯，且能支撑 Monopoly Phase 1 最小可玩闭环。

前置依赖：TASK 10 完成。

先读这些文件：
- [GDD_MonopolyGame.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/GDD_MonopolyGame.md)
- [09_Run_Isolation_Compare_Promote.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/09_Run_Isolation_Compare_Promote.md)
- [11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md)
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)

涉及文件：
- `ProjectState/runs/{run_id}/`
- `ProjectState/Reports/<date>/task11_phase11_e2e_validation.md`
- `ProjectState/Reports/<date>/task11_phase11_playability_validation.md`
- `ProjectState/Reports/<date>/task11_phase11_baseline_coverage_validation.md`

状态：✅ 已完成（compiler-level playability validation）  
证据：[task11_phase11_e2e_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task11_phase11_e2e_validation.md) / [task11_phase11_playability_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task11_phase11_playability_validation.md) / [task11_phase11_baseline_coverage_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task11_phase11_baseline_coverage_validation.md)

Step：
1. 创建 `session_version: "2.0"` 且 `fast_mode: false` 的 session。
2. 输出目录固定为 `ProjectState/runs/{run_id}`。
3. 写入 run metadata：run_id、session_id、session_version、fast_mode、generator_provider、created_at、completed_at、status、pipeline_stages_completed、constraint_violations、provisional_items、promotable。
4. 执行 Stage 1-7。
5. 执行 Compiler E2E 校验：metadata/root_skill/clarification/skill_graph/design_space/candidates/converged/fragments/cross_review/build_ir/naming_log/handoff_v3 齐全。
6. 校验关键内容非空：design_space_report、realization_candidates、design_decision_log、naming_resolution_log。
7. 执行 Monopoly 最小可玩闭环覆盖校验，建立 GDD 需求到 skill_graph、skill_fragments、build_ir、reviewed_handoff_v3 的映射矩阵。
8. 校验最小可玩闭环至少覆盖：28 格棋盘、2-4 玩家、初始资金 1500、2D6 掷骰、顺时针移动、经过起点 +200、地产购买/放弃、租金支付、税务扣款、入狱、破产、胜利、HUD 资金/回合显示、基础弹窗交互。
9. 校验 Universal Baseline 壳层闭环：Start Screen -> Main Menu -> Settings / New Game -> Gameplay -> Pause -> Results -> Return to Menu。
10. 校验 `build_ir.json` 包含可落地实现步骤，覆盖“掷骰 -> 移动 -> 触发格子 -> 资金变化或购买决策 -> 切换玩家”的一轮闭环。
11. 校验 `cross_review_report.json` 将缺失最小可玩闭环、Universal Baseline 最低项、Constraint 保持性判定为 blocker，而不是普通 warning。
12. 如果 TASK 11 已生成或修改 UE 游戏实现代码，运行最小 gameplay smoke test；如果本 TASK 只生成编译器产物，报告必须明确写为“compiler-level playability validation”，不得宣称实际游戏已经可玩。
13. 生成 TASK 11 E2E 验收报告、最小可玩闭环验收报告、Baseline 覆盖验收报告。

验收标准：
- `ProjectState/runs/{run_id}/` 存在。
- `run_id` 格式符合 `run-{yyyyMMdd}-{HHmmss}-{short_hash}`。
- `metadata.json` 存在并包含完整 run metadata。
- `metadata.json` 中 `fast_mode = false`、`generator_provider` 已记录，且完成后 `promotable = true`，除非报告给出 blocker 原因。
- Stage 1-7 全部产物存在。
- 每个产物通过对应 Schema 校验。
- `skill_fragments/` 至少包含 6 个 gameplay fragment 与 6 个 baseline fragment。
- `design_space_report` 非空。
- `realization_candidates` 非空。
- `design_decision_log` 非空。
- `naming_resolution_log` 非空。
- `reviewed_handoff_v3.json` 存在并通过校验。
- `task11_phase11_e2e_validation.md` 包含 Compiler E2E 验收结果。
- `task11_phase11_playability_validation.md` 包含 Monopoly 最小可玩闭环覆盖矩阵。
- `task11_phase11_baseline_coverage_validation.md` 包含 Universal Baseline 覆盖矩阵。
- 覆盖矩阵必须把 GDD 中的核心玩法需求映射到至少一个 `skill_graph` 节点、`skill_fragment`、`build_ir` action 或 `reviewed_handoff_v3` 章节。
- `skill_graph` 或下游产物必须覆盖棋盘、格子、回合、骰子、移动、经济、玩家状态、胜负、HUD/交互。
- 覆盖矩阵必须包含 Universal Baseline 壳层流转：Start Screen、Main Menu、Settings、Pause、Results、HUD。
- Settings 覆盖 Master Volume、SFX Volume、Window Mode、Resolution、Apply、Back。
- `build_ir.json` 必须包含最小一轮玩法闭环的可实现步骤：掷骰、移动、格子事件、资金变化或购买决策、切换玩家。
- `cross_review_report.json` 对缺失最小可玩闭环的情况输出 blocker。
- `cross_review_report.json` 对缺失 Universal Baseline 最低项的情况输出 blocker。
- 若存在 UE gameplay smoke test 入口，必须模拟至少一轮“掷骰 -> 移动 -> 触发格子 -> 资金变化或购买决策 -> 切换玩家”并通过；若不存在，验收报告必须明确记录缺口，且不得宣称实际游戏已可玩。
- 若本 TASK 只验证 Compiler 产物而未验证 UE 侧实际运行，报告必须明确写为“compiler-level playability validation”，不得宣称“真实游戏已可玩”。
- `validate_examples.py --strict` 通过。
- 三份验收报告存在，并在成功声明中附链接。

---

# 第三批：后置治理与高级能力

## TASK 12：Run Compare / Promote 治理工具与 Schema

目标：实现 Phase 11 Run Governance：跨 run 比较、batch 创建、promote 吸收。

前置依赖：TASK 11 完成。

先读这些文件：
- [09_Run_Isolation_Compare_Promote.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/09_Run_Isolation_Compare_Promote.md)
- [11_Schema_and_Artifact_Reference.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/11_Schema_and_Artifact_Reference.md)
- [evidence_tools.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/evidence_tools.py)

涉及文件：
- `Plugins/AgentBridge/Schemas/run_comparison.schema.json`
- `Plugins/AgentBridge/Schemas/batch_manifest.schema.json`
- [evidence_tools.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/evidence_tools.py)
- [tool_definitions.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/tool_definitions.py)
- [server.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/server.py)

状态：✅ 已完成  
证据：[task12_phase11_run_governance_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task12_phase11_run_governance_validation.md) / [run_comparison.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task12_validation_outputs/run_comparison.json) / [batch-20260416-004/manifest.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/batches/batch-20260416-004/manifest.json)

Step：
1. 新增 run_comparison.schema.json 与 batch_manifest.schema.json。
2. 新增 `evidence_create_batch`、`evidence_compare_runs`、`evidence_promote_run`。
3. 实现 promotable 检查：fast_mode、status、constraint_violations、pipeline_stages_completed。
4. 实现 Compare 维度：Constraint 保持性、Realization 差异、Fragment 差异、Build IR 差异、Naming 差异、Provisional 变化。
5. 实现 Promote 单向流程：检查 promotable、创建 batch、复制 promoted_artifacts、生成 promotion_report、保留原始 run。
6. 实现 active batch 记录，同一时间只有一个 active batch。
7. 定义目录清理策略：正式 run 默认保留、fast_mode run 可配置保留最近 N 个、promoted batch 永久保留、failed run 保留 execution_log。
8. 输出 `ProjectState/batches/{batch_id}/manifest.json`、`promoted_artifacts/`、`promotion_report.json`。

验收标准：
- 2 个治理 Schema 存在并有 example。
- 3 个 evidence_* 工具可见、可调用。
- fast_mode run promote 被拒绝。
- completed 且 promotable 的 run 可创建 batch。
- `run_comparison.json` 至少覆盖 Constraint、Realization、Fragment、Build IR、Naming、Provisional 六类差异。
- Promote 后原始 `ProjectState/runs/{run_id}/` 不被删除。
- `batch_manifest.json` 记录 source_run_id、active 状态、promoted_at、promoted_artifacts。
- 同一时间只能有一个 active batch。
- failed run 保留 execution_log 用于诊断。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 13：完整 fast_mode 策略

目标：实现 Phase 11 fast_mode 的完整策略，使其可用于调试和 CI 快速验证，但不可 promote。

前置依赖：TASK 11 完成；建议 TASK 12 完成后执行。

先读这些文件：
- [05_Clarification_Gate_Rules.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/05_Clarification_Gate_Rules.md)
- [07_Design_Space_Discovery_and_Realization.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/07_Design_Space_Discovery_and_Realization.md)
- [09_Run_Isolation_Compare_Promote.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/09_Run_Isolation_Compare_Promote.md)

涉及文件：
- [session.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/session.py)
- [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)
- `Plugins/AgentBridge/Compiler/stages/clarification_gate.py`
- `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`
- `Plugins/AgentBridge/Tests/scripts/task13_phase11_fast_mode_validation.py`

状态：✅ 已完成  
证据：[task13_phase11_fast_mode_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task13_phase11_fast_mode_validation.md) / [task13_fast_mode_summary.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task13_validation_outputs/task13_fast_mode_summary.json) / [task13_fast_mode_gate_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task13_validation_outputs/task13_fast_mode_gate_report.json)

Step：
1. fast_mode 写入 session 与 run metadata。
2. low 自动 safe default，medium 自动 safe default 但 warning，high 保持 clarification_required，critical 阻塞。
3. Runtime 在 fast_mode 下跳过 Discovery / Candidates / Convergence。
4. Fragment 中标记 `fast_mode_default: true`。
5. fast_mode run 标记 `promotable: false`（通过 session.is_promotable 属性联动 fast_mode 与 generator_provider 双重判定）。
6. fast_mode run 进入可配置清理策略，但清理前必须保留 validation/report 证据。
7. `generator_provider = "heuristic_fallback"` 的 run 同样 `promotable: false`，与 fast_mode 共用 is_promotable 判定逻辑。

验收标准：
- fast_mode session 可创建、可执行。
- fast_mode run metadata 中 `promotable = false`。
- fast_mode run metadata 中 `fast_mode = true` 且记录 `clarification_gate_policy`。
- high/critical clarification 未被自动默认。
- Fragment 标记 fast_mode_default。
- fast_mode 下 Discovery / Candidates / Convergence 被跳过，报告明确标注该 run 不可 promote。
- medium 自动默认项必须带 `provisional_warning: true`。
- TASK 12 的 promote 工具拒绝 fast_mode run。
- `generator_provider = "heuristic_fallback"` 的 run 同样不可 promote（session.is_promotable = false）。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

## TASK 14：Baseline Domain Skill Template 全套

目标：补齐 Baseline Domain Skill Template 全套，使 Universal Baseline 不只是硬编码逻辑，而有正式模板层承载。

前置依赖：TASK 11 完成；TASK 13 可并行或之后执行。

先读这些文件：
- [03_Universal_Baseline_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/03_Universal_Baseline_Standard.md)
- [04_Baseline_Realization_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/04_Baseline_Realization_Policy.md)
- [08_Skill_Graph_and_Domain_Skill.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md)
- [14_Agent_Interaction_Protocol.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/14_Agent_Interaction_Protocol.md)（Prompt-First 原则 + SkillTemplate prompt 标准结构）

涉及文件：
- `Plugins/AgentBridge/SkillTemplates/baseline/start_screen/`
- `Plugins/AgentBridge/SkillTemplates/baseline/main_menu/`
- `Plugins/AgentBridge/SkillTemplates/baseline/settings/`
- `Plugins/AgentBridge/SkillTemplates/baseline/pause/`
- `Plugins/AgentBridge/SkillTemplates/baseline/results/`
- `Plugins/AgentBridge/SkillTemplates/baseline/hud/`
- `Plugins/AgentBridge/Tests/scripts/task14_phase11_baseline_template_validation.py`

状态：✅ 已完成  
证据：[task14_phase11_baseline_template_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task14_phase11_baseline_template_validation.md) / [task14_baseline_template_summary.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task14_validation_outputs/task14_baseline_template_summary.json) / [skill_graph.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-152245-6dba/skill_graph.json)

Step：
1. 每个 baseline 域创建 manifest.yaml、system_prompt.md、domain_prompt.md、evaluator_prompt.md、input_selector.yaml、output_schema.json。
2. presence_only 覆盖 Start Screen、Main Menu、Settings、Pause、Results。
3. realization_eligible 覆盖 HUD，并支持 gameplay 域输入。
4. Start Screen 模板采用能力级定义：展示项目标识、用户交互触发、导航到主菜单，不绑定唯一实现方式。
5. Main Menu 模板保留 New Game、Settings、Quit 三按钮及回调。
6. Settings 模板保留 Master Volume、SFX Volume、Window Mode、Resolution、Apply、Back 六项底线。
7. Pause 模板保留 ESC 入口、Resume、Settings、Quit to Menu、SetGamePaused(true)。
8. Results 模板保留胜者信息、Return to Menu、ShowResult()。
9. Skill Graph Planning 优先引用 Baseline Template，找不到模板时给 warning。
10. 建立 SkillTemplates 与 Skills 分层检查：模板目录不含项目实例数据，Skill Instance 只在 run 中动态生成。

验收标准：
- baseline/ 下至少 6 个域模板存在。
- 每个模板目录包含 6 个标准文件。
- Start Screen 模板包含项目标识、用户触发、进入主菜单能力。
- Main Menu 模板包含 New Game、Settings、Quit 三项。
- Settings 模板保留 6 个最低控件。
- Pause 模板包含 Resume、Settings、Quit to Menu 与暂停状态入口。
- Results 模板包含胜者信息与 Return to Menu。
- HUD 模板支持 gameplay 耦合输入。
- 每个 Baseline Fragment 结构包含 `template_id`、`status`、`emitted_families`、`spec_fragments`、`assumptions`、`confidence`。
- presence_only 模板与 realization_eligible 模板目录结构一致，只是执行策略不同。
- 模板目录不得写入 Monopoly 项目实例数据。
- Skill Graph 节点能引用模板 id。
- `validate_examples.py --strict` 通过。
- 证据报告存在，并在成功声明中附链接。

---

# 第四批：UE 运行时验收

## TASK 14A：UE 运行时最小可玩性与 Baseline Domain 验收

目标：在 UE 运行时环境中验证 Monopoly 最小玩法闭环，并逐项验证 TASK 14 交付的 Baseline Domain 相关功能入口与基本行为，确保 Phase 11 不只停留在 Compiler 产物正确，而具备实际运行层证据。

前置依赖：TASK 11、TASK 12、TASK 13、TASK 14 完成。

先读这些文件：
- [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- [03_Universal_Baseline_Standard.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/03_Universal_Baseline_Standard.md)
- [04_Baseline_Realization_Policy.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/04_Baseline_Realization_Policy.md)
- [08_Skill_Graph_and_Domain_Skill.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md)
- [10_Naming_and_Path_Convention.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/10_Naming_and_Path_Convention.md)
- [phase11_reviewed_handoff_v3.example.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task10_validation_outputs/phase11_reviewed_handoff_v3.example.json)
- [phase11_naming_resolution_log.example.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task10_validation_outputs/phase11_naming_resolution_log.example.json)

涉及文件：
- `ProjectState/Reports/<date>/task14a_ue_runtime_playability_validation.md`
- `ProjectState/Reports/<date>/task14a_baseline_domain_runtime_validation.md`
- `ProjectState/Reports/<date>/task14a_ue_smoke_test_log.md`
- `Saved/Logs/`
- `Binaries/`
- `Content/`

状态：✅ 已完成  
证据：[task14a_ue_runtime_playability_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_ue_runtime_playability_validation.md) / [task14a_baseline_domain_runtime_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_baseline_domain_runtime_validation.md) / [task14a_ue_smoke_test_log.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_ue_smoke_test_log.md) / [task14a_runtime_smoke_editor.log](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_runtime_smoke_editor.log) / [task14a_standalone_runtime_smoke_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_standalone_runtime_smoke_validation.md) / [task14a_standalone_smoke.log](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_standalone_smoke.log) / [task14a_blocker_runtime_impl.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_blocker_runtime_impl.md)

Step：
1. 基于 TASK 11 生成的 compiler 产物、TASK 10 的 handoff v3、TASK 14 的 Baseline Template 清单，整理 UE 运行时验收矩阵。
2. 明确本次验证入口：优先使用 UE Editor PIE 或 Standalone；若已具备自动化测试入口，优先复用现有入口。
3. 跑通最小玩法闭环：开始游戏 -> 掷骰 -> 移动 -> 触发格子 -> 资金变化或购买决策 -> 切换玩家。
4. 逐项验证 Baseline Domain 相关能力：Start Screen、Main Menu、Settings、Pause、Results、HUD。
5. Settings 至少验证 Master Volume、SFX Volume、Window Mode、Resolution、Apply、Back 六项底线入口与基本行为。
6. Pause 至少验证暂停入口、Resume、Settings、Quit to Menu。
7. Results 至少验证结果展示与 Return to Menu。
8. HUD 至少验证玩家/回合/资金等核心信息在运行时可见且能随最小玩法闭环变化。
9. 记录运行环境、启动方式、执行步骤、观察结果、日志路径、阻塞项；若验证失败，必须明确 blocker，不得降格写成“仅编译器层通过”。
10. 生成三份证据：UE 运行时可玩性报告、Baseline Domain 运行时报告、smoke test 日志摘要。

验收标准：
- 至少存在一份 UE 运行时验证记录，明确使用 PIE、Standalone 或其他实际运行入口。
- `task14a_ue_runtime_playability_validation.md` 存在，并记录最小玩法闭环的执行结果。
- `task14a_baseline_domain_runtime_validation.md` 存在，并逐项覆盖 Start Screen、Main Menu、Settings、Pause、Results、HUD。
- `task14a_ue_smoke_test_log.md` 存在，并记录运行环境、执行步骤、结果与日志位置。
- 最小玩法闭环至少完成一轮“掷骰 -> 移动 -> 触发格子 -> 资金变化或购买决策 -> 切换玩家”。
- Baseline Domain 六项能力至少完成入口验证，且不得以“理论可实现”替代实际运行观察。
- Settings 六项底线必须逐项记录结果：Master Volume、SFX Volume、Window Mode、Resolution、Apply、Back。
- 如果存在 blocker，必须明确写入报告，并阻塞 TASK 15 最终完成声明。
- 成功声明“真实游戏已可玩”前，必须先完成本 TASK 并附三份证据链接。

---

# 第五批：最终验收与文档收尾

## TASK 15：Phase 11 最终验收与文档收尾

状态：✅ 已完成  
证据：[phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md) / [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md) / [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)

目标：完成 Phase 11 全阶段验收，将 Current 文档、项目基线、任务入口和证据归档切换到 Phase 11 完成口径。

前置依赖：TASK 01-14、TASK 14A 全部完成。

先读这些文件：
- [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- [00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)
- [02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md)
- [12_Implementation_Taskbook.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Phase11/12_Implementation_Taskbook.md)

涉及文件：
- [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [Docs/Current/01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)
- [Docs/Current/02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md)
- `Docs/Current/18_Phase11_Closeout.md`
- `ProjectState/Reports/<date>/phase11_feature_coverage_report.md`
- [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
- [CLAUDE.md](/D:/UnrealProjects/Mvpv4TestCodex/CLAUDE.md)
- [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md)

Step：
1. 执行全量验证：v1 兼容、v2 端到端、Monopoly 最小可玩闭环、Universal Baseline 完整覆盖、MCP tools/list、fast_mode 不可 promote、Baseline Template 完整性。
2. 汇总 TASK 01-14、TASK 14A 证据报告。
3. 生成 Phase 11 文档包功能覆盖报告，逐项对应 `Docs/Phase11/00-13`。
4. 生成 Phase 11 final acceptance 报告。
5. 更新 Docs/Current 到 Phase 11 Completed 口径。
6. 新增 `18_Phase11_Closeout.md`。
7. 更新 `CLAUDE.md` / `AGENTS.md` 当前阶段描述。
8. 更新 `task.md` 中所有 TASK 与里程碑状态为完成。

验收标准：
- TASK 01-14、TASK 14A 均有证据报告。
- `phase11_feature_coverage_report.md` 存在。
- `phase11_feature_coverage_report.md` 对 `Docs/Phase11/00-13` 每份文档至少列出：新增功能、对应 TASK、证据文件、状态、残留风险。
- 覆盖报告不得出现未绑定 TASK 的 Phase 11 新增功能。
- Phase 11 final acceptance 报告存在。
- v1 兼容验证通过。
- v2 端到端验证通过，并包含 Monopoly 最小可玩闭环验收结论。
- Universal Game Baseline Standard 完整覆盖通过。
- MCP 工具数量与 Phase 11 目标一致。
- Defer 治理项全部完成。
- Docs/Current 更新为 Phase 11 完成口径。
- `18_Phase11_Closeout.md` 存在。
- 成功声明附所有关键证据链接。
