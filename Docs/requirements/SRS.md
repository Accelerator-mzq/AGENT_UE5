# SRS — Mvpv4TestCodex 系统需求规格说明

> 版本: v1.0(2026-05-26)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §4.1
> 关联 FEATURE_INVENTORY: Docs/FEATURE_INVENTORY.md(F-* ID 全量 108 行 · 15 family;2026-06-11 Phase 13 +3 行)
> 关联契约: Docs/contracts/{tool_contract, field_specification, schemas_catalog, mcp_tools_catalog}.md
> 关联 UE 5.7 扫描: Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md
> 写作约束: 只写"做什么",不写"怎么做";实现细节落 design/LLD/0X_*.md(Task 1.7-1.13)

## 0. 文档元信息

本 SRS 是 Mvpv4TestCodex 项目的需求基线总入口。它把项目层与插件层全部功能、端到端链路、数据契约、非功能要求、外部接口与 UE 5.5.4 → 5.7 迁移面汇总为单一权威清单。每个模块小节均按统一模板组织(用途 / 对外接口 / 功能列表 / 数据契约 / 测试覆盖 / 详细实现 / UE 5.7 迁移记号),所有 F-* ID 均与 FEATURE_INVENTORY 主表逐项对齐。本文不重复 Current/* 与插件层 Docs/* 的叙述,仅以契约语言概括事实。

## 1. 项目定位与范围

### 1.1 项目定位

Mvpv4TestCodex 是一个以 AgentBridge 插件为通用 Agent 开发框架的 UE5 工程,采用"项目层(输入 / 配置 / 实例 / 治理)+ 插件层(通用编译 / 执行 / 验证机制)"双层结构。AgentBridge 不只是工具接口插件,而是包含 Compiler Plane(7 阶段 Skill-First 主链)、Reviewed Handoff 交接物机制、Orchestrator 执行编排、L1/L2/L3 受控工具体系、Run 治理与证据裁决的完整框架。本工程截至 2026-04-17 已完成 Phase 11 收尾,主链由 Root Skill Contract → Clarification Gate → Skill Graph Planning → Domain Skill Runtime → Cross Review v2 → Build IR v2 → Reviewed Handoff v3 构成(当时实测 strict 26/26、MCP 53 工具),Monopoly 与 boardgame 端到端 run 已完成验收并落盘 ProjectState/runs/run-20260417-051425-aad0。其后 Phase 12(2026-05-27)重开 LLM Internal 路径,Phase 13(2026-06-11)落地 Skill 合成主链(Stage 3 注册表数据化 + capability gap 显式化 + S3.5 合成环节 + GDD 覆盖矩阵 + promote 守卫);当前实测口径:strict 28/28、MCP 55 工具(51 正式 + 4 兼容 alias)。

### 1.2 目标引擎版本

当前基线 UE5.5.4;本 SRS 同时记录 UE5.5.4 → UE5.7 升级所需的 breaking change 面(详见 §8 与扫描 spec)。

### 1.3 文档覆盖范围

项目层全部(`ProjectInputs/` / `ProjectState/` / `Scripts/` / 根 `Source/` / 根 `task.md` 等) + 插件层全部(`Plugins/AgentBridge/` 下 Source / Scripts / Compiler / MCP / Schemas / SkillTemplates / Tests / AgentBridgeTests / Docs),共 15 个 F-* family、108 个 F-* ID。

### 1.4 阅读顺序

建议按 §1 → §2 → §3(模块详表)→ §4(链路)→ §5(契约)→ §6(非功能)→ §7(外部接口)→ §8(UE 5.7 迁移)读;深入实现细节请按 §3 各模块"详细实现"指向的 LLD 文件继续。

## 2. 系统总体概览(短,详见 HLD)

### 2.1 双层架构

项目层负责"具体某个项目的输入、状态、产物、治理实例";插件层负责"通用机制"。GDD 实例在项目层,GDD 解析机制在插件层。具体而言:`ProjectInputs/` 装具体 GDD 与 Preset(F-INP-01 / F-INP-02);`ProjectState/` 装 Evidence / Reports / runs / snapshots 等运行时产物(F-RT-03 / F-RT-04 / F-RT-05);项目根 `Source/` 装项目级 C++ 入口(目前只有 Target.cs 与 Editor Target);项目根 `Scripts/` 装项目级辅助脚本(可玩 demo、资产生成、Hook);项目根 `Plugins/AgentBridge/` 整棵插件层。插件层内部再分 `Source/`(C++)、`Scripts/`(Python Bridge + Orchestrator + 老 Compiler)、`Compiler/`(Phase 8 之后的新编译器骨架)、`MCP/`(MCP Server 主体)、`Schemas/`(全部 JSON Schema)、`SkillTemplates/`(Baseline 6 + Genre Pack)、`AgentBridgeTests/`(C++ Automation Test 插件)、`Tests/`(Python 系统测试套件)。

### 2.2 核心链路一图

```
GDD → MCP 前端 Stage 1-3 认知分解 → Compiler Core Stage 4-7 结构化生成
    → Reviewed Handoff v3 → Orchestrator → A(Python) / B(Remote Control) / C(C++ Plugin)
    → UE 编辑器 / Standalone 运行时 → 官方 Automation/Gauntlet 测试主干
    → MCP 后端证据裁决 → pass / fail / escalate;Run 治理 compare/promote/batch
```

### 2.3 工具体系层级 L1 / L2 / L3

L1 语义工具(查询 + 写入 + 反馈,必读回);L2 编辑器服务工具(构建 / 测试 / 保存 / Undo / 截图);L3 UI 自动化工具(仅当 L1 无对应 API 时启用,必须接 L1 读回交叉比对)。Agent 必须按 L1 > L2 > L3 优先级选择,详见 `Docs/contracts/tool_contract.md`。

### 2.4 三层信任(L0 / L1 当前 / L2 Canonical / L3-L5 历史)

L1 = 项目当前权威 Current/* + 插件层 Docs/* + 本 SRS 与新结构 contracts/;L2 = 已稳定的代码与 Schema 主体(`Plugins/AgentBridge/Source` / `Scripts/bridge` / `Compiler` / `MCP` / `Schemas/common`);L3-L5 = 已归档的 History/* 与 archive/*(仅追溯,不参与当前裁决)。Phase 11 / Phase 12 已 Completed,Phase 13(Skill 合成主链)实施完成、验收 runbook 判据 1-4 闭环(5-12 待执行,见根 `task.md`),本 SRS 持续作为总基线滚动更新。

## 3. 模块功能需求(核心)

### 3.1 C++ 编辑器子系统 [F-CPP-*]

- **用途**: 在 UE Editor 进程内提供 Agent 主入口、Commandlet CLI 入口、UAT 包装、Automation Driver 适配以及共享 USTRUCT 类型,是 Bridge / Orchestrator 与 UE 引擎之间的 C++ 桥接层。
- **对外接口**: `UAgentBridgeSubsystem` / `UAgentBridgeCommandlet` / `FUATRunner` / `FAutomationDriverAdapter` / `BridgeTypes.h` USTRUCT 族 / `FAgentBridgeModule`。
- **功能列表**:
  - F-CPP-01 `UAgentBridgeSubsystem` — Editor 启动期自动实例化的 UEditorSubsystem 主入口,挂载 Tick、跨语言桥接、模块协调。
  - F-CPP-02 `UAgentBridgeCommandlet` — 无窗口 CLI 入口,提供 `-run=AgentBridge` 形式的 commandlet 调度。
  - F-CPP-03 `FUATRunner` — UAT `BuildCookRun` 的同步/异步进程包装,内部以 `FProcHandle` 管理子进程。
  - F-CPP-04 `FAutomationDriverAdapter` — 包装 `FAutomationDriverModule`,为 L3 UI 自动化族提供异步壳。
  - F-CPP-05 `BridgeTypes` — `FAgentBridgeReply` / `FAgentBridgeRequest` / `FBridgeTransform` 等共享 USTRUCT 类型,容差比对 `NearlyEquals` 在此实现。
  - F-CPP-06 `FAgentBridgeModule` — `IModuleInterface` 实现,负责加载/卸载钩子与 `AGENTBRIDGE_API` 导出注册。
- **数据契约**: → `contracts/field_specification.md`(BridgeTypes 共享字段族) + `contracts/tool_contract.md`(L1/L2/L3 调用约束)。
- **测试覆盖**: → `testing/test_spec.md` §C++ L1/L2/L3 套件(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/01_cpp_subsystem.md`(待 Task 1.7 落地)。
- **UE 5.7 迁移记号**: 涉及 UE57-BC-008(P1 confirmed,EditorScriptingUtilities 模块依赖)、UE57-BC-010(P1 confirmed,`IncludeOrderVersion = Unreal5_5`)、UE57-BC-012(P1 confirmed,`.uproject EngineAssociation "5.5"`);P2 suspected:UE57-BC-001 / 002 / 004 / 005 / 006 / 011 / 014。

### 3.2 Bridge 工具体系 [F-BRG-*]

- **用途**: Python 侧的 L1 / L3 工具实现 + Remote Control HTTP 客户端 + UAT 包装 + UE Editor helpers + 项目配置 + 通信主体。是 Agent → UE 引擎"做什么"的执行落地层,所有调用必须符合 Schema 反馈契约。
- **对外接口**: `query_tools.py` / `write_tools.py` / `ui_tools.py` / `remote_control_client.py` / `uat_runner.py` / `ue_helpers.py` / `project_config.py` / `bridge_core.py` 模块函数族,及对应 feedback / write_feedback response Schema。
- **功能列表**:
  - F-BRG-01 L1 查询接口族 — `get_actors / get_actor_components / get_actor_property` 等约 12 个查询工具,只读、必带 status / summary / data / warnings / errors 反馈外壳。
  - F-BRG-02 L1 写接口族 — `set_actor_property / spawn_actor / destroy_actor` 等约 4 个写工具,支持 `dry_run: true`,返回必带 `actual_*` 读回。
  - F-BRG-03 L1 反馈接口族 — 10 份反馈契约(actor/asset/level/project/validation 五子目录 + write_feedback)。
  - F-BRG-04 L3 UI 自动化族 — UI 工具入口,封装 `FAutomationDriverAdapter`,统一走异步壳并接 L1 读回交叉比对。
  - F-BRG-05 Remote Control HTTP 客户端 — 端口 30010 的 PUT/GET 包装,`/remote/object/call` 与 `/remote/object/property` 与 `/remote/batch`。
  - F-BRG-06 UAT 包装器 Python 侧 — `RunUAT BuildCookRun -editortest -RunAutomationTest=...`,对应 C++ F-CPP-03。
  - F-BRG-07 UE 资产/关卡 helpers — `unreal.*` Editor Python API 的辅助封装。
  - F-BRG-08 项目配置解析 — 项目路径、UE 安装路径、RC 端口等运行时配置加载。
  - F-BRG-09 `bridge_core` 通信主体 — Bridge 客户端核心通信循环与命令分发。
- **数据契约**: → `contracts/tool_contract.md`(L1/L2/L3) + `contracts/field_specification.md`(共享字段族) + `contracts/schemas_catalog.md`(feedback/* 与 write_feedback/*)。
- **测试覆盖**: → `testing/test_spec.md` §L1/L2/L3 套件 + 系统测试 Stage 1-3(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/02_bridge.md`(待 Task 1.8 落地)。
- **UE 5.7 迁移记号**: 涉及 UE57-BC-016(P1 confirmed,`unreal.EditorLevelLibrary` deprecated → UnrealEditorSubsystem)、UE57-BC-017(P1 confirmed,`unreal.EditorAssetLibrary` deprecated → EditorAssetSubsystem);P2 suspected:UE57-BC-019(RemoteControl HTTP 端点格式)、UE57-BC-018(其他 `unreal.*` binding 综合)、UE57-BC-020(UAT BuildCookRun 调用形态)。

### 3.3 Orchestrator [F-ORC-*]

- **用途**: 在 Compiler 已经输出 Reviewed Handoff 之后,把 Build IR / Build Steps / Validation IR 落到 UE 执行通道,并组装运行报告与证据。负责 Spec 加载、Plan 生成、通道路由、Handoff 执行、对标校验、报告生成与故障恢复规划。
- **对外接口**: `orchestrator.py` / `plan_generator.py` / `run_plan_builder.py` / `spec_reader.py` / `verifier.py` / `report_generator.py` / `recovery_planner.py` / `handoff_runner.py` / `validation_inserter.py` / `forgeue_manifest_importer.py`。
- **功能列表**:
  - F-ORC-01 主体编排 + 通道选择 — Orchestrator 主循环、Editor 在线 vs Standalone Staged 通道路由。
  - F-ORC-02 Plan 生成 — Spec → Plan 转换 + RunPlan 构建。
  - F-ORC-03 Spec 读取 — YAML / JSON Spec 加载与字段解析。
  - F-ORC-04 验证与对标 — Plan 执行结果对照 Spec 期望值校验。
  - F-ORC-05 报告生成 — 运行报告 / 证据落盘组装。
  - F-ORC-06 故障恢复规划 — 失败 Step 重试 / 回滚策略生成。
  - F-ORC-07 Handoff 执行 — `reviewed_handoff` 执行 + validation 插桩。
  - F-ORC-08 ForgeUE manifest 导入 — ForgeUE 产出 manifest → reviewed_handoff 桥接。
- **数据契约**: → `contracts/schemas_catalog.md`(reviewed_handoff* / build_ir* / run_plan / planner_output / evidence_manifest)。
- **测试覆盖**: → `testing/test_spec.md` §系统测试 Stage 5-10(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/03_orchestrator.md`(待 Task 1.9 落地)。
- **UE 5.7 迁移记号**: 无 P1 confirmed 直接影响项;通过 F-CPP-03 / F-BRG-06 间接受 UE57-BC-020(P2 suspected)波及。

### 3.4 Compiler [F-CMP-*]

- **用途**: 编译前端骨架,从 GDD 经 7 阶段主链生成 Reviewed Handoff v3。包含 Phase 11 Skill-First 新主链(Stage 1-7)、Stage 4 三路生成策略(MCP Agent / LLM Internal / Heuristic Fallback)、以及 Phase 8/9 留用的 Legacy v1 五阶段管线(供 boardgame / JRPG 回归)。
- **对外接口**: `Plugins/AgentBridge/Compiler/pipeline/`(主入口) + `Compiler/stages/*.py`(各 Stage 节点) + `Compiler/{intake,planner,skill_runtime,cross_review,lowering}/`(Legacy v1) + Phase 8 之前的 `Plugins/AgentBridge/Scripts/compiler/` 子模块。
- **功能列表**:
  - F-CMP-01 Legacy Compiler analysis 子模块 — Phase 8 之前的脚本侧分析阶段。
  - F-CMP-02 Legacy Compiler generation 子模块 — Phase 8 之前的脚本侧生成阶段。
  - F-CMP-03 Legacy Compiler handoff 子模块 — Phase 8 之前的脚本侧 handoff 构建。
  - F-CMP-04 Legacy Compiler intake 子模块 — Phase 8 之前的脚本侧输入接入。
  - F-CMP-05 Legacy Compiler review 子模块 — Phase 8 之前的脚本侧跨审。
  - F-CMP-06 Legacy Compiler routing 子模块 — Phase 8 之前的脚本侧路由。
  - F-CMP-07 Phase 11 Pipeline 主入口 `Compiler/pipeline/`。
  - F-CMP-08 Stage 1 `root_skill_contract` 生成。
  - F-CMP-09 Stage 2 Clarification Gate(澄清门)。
  - F-CMP-10 Stage 3 Skill Graph Planning(技能图规划)。
  - F-CMP-11 Stage 4 路 A — Design Space Discovery 回退。
  - F-CMP-12 Stage 4 路 B — Realization 回退。
  - F-CMP-13 Stage 4 路 C — Convergence 回退。
  - F-CMP-14 Stage 通用 Agent Protocol — LLM Agent 协议封装。
  - F-CMP-15 Stage 通用 LLM Provider Framework — LiteLLM + Instructor 统一接入(`Compiler/providers/`)+ capability 路由 + observe-only budget(`Compiler/runtime/budget_tracker.py`)+ Stage 4 Candidates 分批(`Compiler/stages/candidates_batch_orchestrator.py`)。Phase 12 重开(2026-05-27,7/7 真 LLM 验收 PASS),旧 `llm_client.py` 已 deprecate。
  - F-CMP-16 Stage 7 Handoff v3 — `reviewed_handoff_v3` 输出。
  - F-CMP-17 Stage 5 Cross Review v2 — Cross-Domain 跨审 v2。
  - F-CMP-18 Stage 6 Lowering v2 — Build IR v2 下降。
  - F-CMP-19 Stage 4 Domain Skill Runtime — Domain Skill 运行时承载。
  - F-CMP-20 Legacy v1 Pipeline — Framework cross_review 节点(Phase 8/9 v1 五阶段管线 Stage 4),由 `pipeline_orchestrator.STAGE_NAME_MAP_V1` 调度。
  - F-CMP-21 Legacy v1 Pipeline — Framework intake 节点(Stage 1 design_intake),v1 管线入口。
  - F-CMP-22 Legacy v1 Pipeline — Framework lowering 节点(Stage 5),v1 管线 Build IR 下降。
  - F-CMP-23 Legacy v1 Pipeline — Framework planner 节点(Stage 2),v1 管线规划。
  - F-CMP-24 Legacy v1 Pipeline — Framework skill_runtime 节点(Stage 3),v1 管线 Skill 运行时,Phase 8/9 期 boardgame / JRPG 回归仍使用全套 F-CMP-20..24。
  - F-CMP-25 S3.5 Skill 合成链(Phase 13)— Stage 3 注册表数据化(`registry_scan` 扫描 manifest `capability_bindings` + 占位数据 + synthesized approved)+ capability gap 显式化(`skill_graph.metadata.capability_gaps`)+ 合成校验器(`synthesis_validator`)+ 合成 prepare/save/审阅清单(`skill_synthesis`,MCP 工具对 `compiler_skill_synthesis_prepare/save`)。`allow_skill_synthesis` 默认 false,默认行为与现状一致。
  - F-CMP-26 GDD 覆盖矩阵(Phase 13)— `gdd_coverage` 模块,markdown 结构切分 + anchor 认领,claimed / unclaimed / container 三态,矩阵 sidecar 随 Stage 1 保存落盘;防固化四守则(切分零语义 / 裁决 run 级 / 只靠 anchor / 格式假设显式)。
- **数据契约**: → `contracts/schemas_catalog.md`(root_skill_contract / clarification_gate_report / skill_graph / design_space_report / realization_candidates / converged_realization_pack / cross_review_report_v2 / build_ir_v2 / naming_resolution_log / reviewed_handoff_v3 / compiler_session / planner_output / gdd_projection / skill_fragment_v2 / design_decision_log / gdd_coverage_matrix)。
- **测试覆盖**: → `testing/test_spec.md` §Stage 1-7 各阶段 + Legacy v1 回归(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/04_compiler.md`(待 Task 1.10 落地)。
- **UE 5.7 迁移记号**: 无 P1 confirmed 直接影响项(Compiler 主体为纯 Python,未触 UE C++ API);若 Stage 6 lowering 输出涉及 UE 类路径,需通过 F-BRG/F-RT 间接对齐 UE57-BC-016/017。

### 3.5 MCP Server [F-MCP-*]

- **用途**: 把 AgentBridge 工具体系暴露为标准 MCP 协议(stdio)。前端 Stage 1-3 认知分解 + 后端证据裁决 + Run 治理是 MCP 主价值;Bridge L1/L2/L3 工具(共 28 个)作为可选 passthrough 外部适配层保留。MCP 在本框架中的定位是认知桥接层,不是流程主干层(详见 `Docs/design/HLD.md#4`)。
- **对外接口**: `Plugins/AgentBridge/MCP/{server, naming, tool_definitions, py_channel, rc_channel, compiler_tools, evidence_tools}.py` 等模块导出的 55 个 MCP 工具(51 正式 + 4 兼容 alias;Phase 13 增 `compiler_skill_synthesis_prepare/save` 合成工具对)。
- **功能列表**:
  - F-MCP-01 Bridge L1 查询族(MCP 暴露)— 12 工具,封装 F-BRG-01。
  - F-MCP-02 Bridge L1 写族(MCP 暴露)— 4 工具,封装 F-BRG-02。
  - F-MCP-03 Bridge L1 反馈族(MCP 暴露)— 7 工具,封装 F-BRG-03。
  - F-MCP-04 Bridge L2 编辑器服务族 — 编辑器级闭环服务(spawn+verify 等)。
  - F-MCP-05 Bridge L3 UI 族(MCP 暴露)— UI 自动化工具,封装 F-BRG-04。
  - F-MCP-06 前端 Stage 1 Root Skill Contract 族 — prepare / save Root Skill Contract MCP 工具。
  - F-MCP-07 前端 Stage 2 Clarification Gate 族 — 澄清门交互 MCP 工具。
  - F-MCP-08 前端 Stage 3 Skill Graph Planning 族 — SkillGraph 规划交互 MCP 工具。
  - F-MCP-09 前端 Stage 4 节点交互族 — Discovery / Realization / Convergence 三路节点交互。
  - F-MCP-10 后端 Evidence 读写族 — ProjectState/Evidence 读写 MCP 工具。
  - F-MCP-11 后端 Run 治理族 — compare / promote / batch 等 Run 治理 MCP 工具。
  - F-MCP-12 兼容 alias 族 — 4 个向后兼容 alias 工具。
  - F-MCP-13 MCP Server 主入口 — MCP 协议 server + 命名空间路由。
- **数据契约**: → `contracts/mcp_tools_catalog.md`(55 工具字段级签名表) + `contracts/schemas_catalog.md`(compiler_session / evidence_manifest / run_comparison / batch_manifest)。
- **测试覆盖**: → `testing/test_spec.md` §MCP E2E + 系统测试 Stage 6-10(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/05_mcp_server.md`(待 Task 1.11 落地)。
- **UE 5.7 迁移记号**: 涉及 UE57-BC-016 / 017(P1 confirmed,`MCP/server.py` 大量 `unreal.EditorLevelLibrary` / `EditorAssetLibrary` 调用);P2 suspected:UE57-BC-019(RC HTTP 端点)、UE57-BC-018(其他 `unreal.*` binding)。

### 3.6 Skill & Template 体系 [F-SKL-*]

- **用途**: 承载 SkillGraph 数据结构、Domain Skill Runtime、Baseline 6 Skill 模板与类型扩展包(Genre Pack)。是 Compiler Stage 3-4 的语义骨架与模板基底。Phase 13 起模板 `manifest.yaml` 增 `capability_bindings` 自描述块(Stage 3 注册表数据源),并增 `SkillTemplates/registry_placeholders.yaml` 占位数据与 `SkillTemplates/synthesized/` 合成隔离区(仅 `review_status: approved` 被消费)。
- **对外接口**: `Plugins/AgentBridge/Compiler/skill_runtime/` + `Compiler/stages/domain_skill_runtime.py` + `Plugins/AgentBridge/SkillTemplates/baseline/` + `SkillTemplates/genre_packs/` + `SkillTemplates/{registry_placeholders.yaml,synthesized/}`。
- **功能列表**:
  - F-SKL-01 SkillGraph 数据结构 — SkillGraph / SkillNode 数据模型与序列化,对应 `Schemas/skill_graph.schema.json`。
  - F-SKL-02 Domain Skill Runtime — Domain Skill 运行时实现,与 F-CMP-19 互为代码源/语义。
  - F-SKL-03 Baseline 6 Skill 模板 — hud / main_menu / pause / results / settings / start_screen,Universal Game Baseline Standard。
  - F-SKL-04 Genre Pack — Boardgame 类型扩展包(boardgame_core / turn_flow / dice_resolution / tile_event 等)。
- **数据契约**: → `contracts/schemas_catalog.md`(skill_graph / skill_fragment / skill_fragment_v2)。
- **测试覆盖**: → `testing/test_spec.md` §Baseline Template + Genre Pack 系统测试(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/06_skills_and_templates.md`(待 Task 1.12 落地)。
- **UE 5.7 迁移记号**: 无 P1 confirmed 直接影响项(模板本体为 YAML / JSON,不触 UE C++ API);通过 F-CMP / F-BRG 间接受 UE57-BC-016 / 017 波及。

### 3.7 运行时与证据 [F-RT-* / F-TST-* / F-HOOK-* / F-INP-* / F-DEMO-* / F-VAL-*]

- **用途**: 把 Compiler → Orchestrator → UE 执行的全链路落地到具体运行时环境(Editor 在线 / Standalone Staged),并组织证据落盘、报告生成、Run 隔离、测试套件、释放门禁、输入实例与可玩 demo。
- **对外接口**: `Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py`(run 入口) + `MCP/evidence_tools.py` + `ProjectState/{Evidence,Reports,runs}/` + `Scripts/hooks/` + `Scripts/validation/` + `Plugins/AgentBridge/AgentBridgeTests/` + `Plugins/AgentBridge/Tests/` + `ProjectInputs/` + 根 `Scripts/run_*_demo.py`。

#### 3.7.1 核心运行时 [F-RT-*]

  - F-RT-01 UE Editor 在线引导关卡 — UE Editor 在线模式下的关卡启动 + Spec 引导执行;与 Bridge 通信通道(CPP_PLUGIN / REMOTE_CONTROL / MOCK)概念正交。
  - F-RT-02 Standalone Staged 运行时 — 打包脱离 Editor 的 Standalone Staged 模式;由 UAT BuildCookRun 产出可独立运行目标。
  - F-RT-03 Evidence 落盘 — `ProjectState/Evidence` 目录证据组织规范。
  - F-RT-04 Reports 生成 — `ProjectState/Reports` 报告生成与落盘。
  - F-RT-05 Run Workspace 隔离 — 每 `run_id` 一份独立 workspace,`ProjectState/runs/`。

#### 3.7.2 测试体系 [F-TST-*]

  - F-TST-01 L1 测试族 — C++ L1 接口测试 3 份(Query / Write / UITool)。
  - F-TST-02 L2 闭环测试族 — C++ L2 编辑器闭环 Spec 测试 2 份。
  - F-TST-03 L3 FunctionalTest + Gauntlet 控制器 — C++ L3 关卡级 FunctionalTest Actor + Gauntlet 控制器。
  - F-TST-04 系统测试套件 — Phase 8/9/10 共 10 个 Stage,登记 240 条系统测试 + fixtures + scripts。

#### 3.7.3 Hook 与门禁 [F-HOOK-*]

  - F-HOOK-01 document-release gate — 文档释放门禁主体 + 自测套件。
  - F-HOOK-02 Git hooks 安装与 CC 通知 — Git hooks 安装器 + Claude Code 通知 wrapper + commit-msg / pre-commit / pre-push 模板。

#### 3.7.4 输入实例 [F-INP-*]

  - F-INP-01 GDD 实例输入族 — Boardgame TicTacToe / Monopoly / JRPG 三份 GDD 实例。
  - F-INP-02 Compiler Profile / Mode Override 预设 — `ProjectInputs/Presets/{compiler_profile, mode_override}.yaml`。

#### 3.7.5 可运行 demo [F-DEMO-*]

> 注:F-DEMO-01 已并入 F-CHN-MODE-01/02(见 §4.4 模式路由),本子节只列剩余 2 行 F-DEMO-02/03。

  - F-DEMO-02 可运行游戏 demo 族 — Boardgame Playable + JRPG Turn-Based + Phase 7 P1 收敛三份脚本。
  - F-DEMO-03 资产生成 / Skills 同步辅助族 — Monopoly 资产批量生成脚本 + Skills 同步辅助。

#### 3.7.6 治理校验 [F-VAL-*]

  - F-VAL-01 Plugin/Project 治理校验脚本族 — `validate_no_legacy_automation_entrypoints` / `phase7_governance_audit` / `stage_plugin_release` 等。
  - F-VAL-02 Schema 校验脚本族 — `validate_examples.py` / `test_handoff_schema.py`,当前 `--strict` 26/26 通过。
  - F-VAL-03 Evidence / Functional Map 生成 — Editor 证据捕获 + Task15 Functional Map 生成。

- **数据契约**: → `contracts/schemas_catalog.md`(evidence_manifest / batch_manifest / run_comparison) + `contracts/field_specification.md`(naming / 路径规范)。
- **测试覆盖**: → `testing/test_spec.md` §C++ L1/L2/L3 + 系统测试 240 条 + Hook 自测套件(待 Task 1.15 落地)。
- **详细实现**: → `design/LLD/07_runtime_and_evidence.md`(待 Task 1.13 落地)。
- **UE 5.7 迁移记号**: 涉及 UE57-BC-025(P1 confirmed,`run_system_tests.py` / `task14a_phase11_standalone_smoke.py` / `start_ue_editor_*.ps1` 共 7 处硬编码 `UE_5.5` 路径);P2 suspected:UE57-BC-020(UAT BuildCookRun 调用形态)、UE57-BC-022(`.uproject Plugins[]` 中 ModelingToolsEditorMode + RemoteControlWebInterface)、UE57-BC-023(`AgentBridge.uplugin Plugins[]` 中 EditorScriptingUtilities + Gauntlet)。

## 4. 端到端链路(横切)

### 4.1 7 阶段主链 v2 [F-CHN-*]

Phase 11 Skill-First Design Compiler Framework 的正式主链:

- F-CHN-01 Stage 1 — Root Skill Contract — GDD → 根技能契约(含 Universal Baseline Merge),输出 `root_skill_contract.schema.json` 实例。
- F-CHN-02 Stage 2 — Clarification Gate — 4 档决策(blocking / provisional / soft / closed) + provisional 传播 + fast_mode 高风险保护,输出 `clarification_gate_report.schema.json`。
- F-CHN-03 Stage 3 — Skill Graph Planning — Gameplay + Baseline Domain Skills 规划,输出 `skill_graph.schema.json`;Phase 13 起节点配置由注册表扫描(模板 manifest `capability_bindings` 自描述)构建,库外 required capability 显式记入 `metadata.capability_gaps`。
- F-CHN-03.5(条件环节)S3.5 — Skill Synthesis(Phase 13,F-CMP-25)— `capability_gaps` 非空且 `allow_skill_synthesis=true` 时,逐 gap 经 MCP `compiler_skill_synthesis_prepare/save` 由 agent 现场合成 6 文件 SkillTemplate 包,机器校验 + 人审 gate(`review_status: approved`)双 gate 后重跑 Stage 3 清空 gap;默认(开关关闭)跳过合成、gap 保留且 run 不可 promote。fast_mode 下无条件跳过。
- F-CHN-04 Stage 4 — Design / Realization / Convergence — 三路设计 / 实现化 / 收敛(见 §4.2)。
- F-CHN-05 Stage 5 — Cross Review v2 — 跨域冲突 + Blueprint 薄层审查,输出 `cross_review_report_v2.schema.json`。
- F-CHN-06 Stage 6 — Lowering v2 — Reviewed Dynamic Spec Tree → Build IR v2(含 `naming_resolution_log` sidecar)。
- F-CHN-07 Stage 7 — Handoff v3 — Build IR v2 → `reviewed_handoff_v3`,Compiler→Execution 唯一边界。

链路标准表述:Skill 决定生成什么 spec;Static Spec 决定 spec 长什么样;Dynamic Spec 决定当前项目实际生成了什么(结构受 Static Spec 约束,内容由 AI Agent 填充);Reviewed Handoff 决定执行层正式消费什么。

### 4.2 Stage 4 三路生成策略 [F-CHN-S4-*]

- F-CHN-S4-01 路 A — Design Space Discovery — 在 Static Spec 边界内枚举设计维度,输出 `design_space_report.schema.json`。
- F-CHN-S4-02 路 B — Realization — 在 Design Space 上生成具体候选,输出 `realization_candidates.schema.json`。
- F-CHN-S4-03 路 C — Convergence — 跨维度收敛挑选最终方案,输出 `converged_realization_pack.schema.json`。

Stage 4 同时支持三种 generator_provider:`mcp_agent`(主路径,Agent 通过 prepare/save 交互)、`heuristic_fallback`(显式确定性后备,用于 CI / fast_mode)、`llm`(pipeline 内嵌 LLM API,接入完成,高负载验收暂缓)。

### 4.3 Run 治理 [F-GOV-*]

- F-GOV-01 `run_id` 生命周期 — 生成 / 绑定 / 终结全周期治理。
- F-GOV-02 `fast_mode` 不可 promote — fast_mode 运行禁止 promote。
- F-GOV-03 `generator_provider` 影响 `is_promotable` — CompilerSession 上 generator_provider 字段决定 is_promotable。
- F-GOV-04 compare / promote 工具 — `evidence_compare_runs` / `evidence_promote_run` MCP 入口,输出 `run_comparison.schema.json` / `batch_manifest.schema.json`。
- F-GOV-05 synthesized / gap promote 守卫(Phase 13)— run 含 `template_source=synthesized` 节点或 `skill_graph.metadata.capability_gaps` 非空 → `PROMOTE_REJECTED`(与 heuristic_fallback 同级保守);skill_graph 损坏 fail-closed 同样拒绝。落点 `MCP/evidence_tools.py`。

### 4.4 模式路由 [F-CHN-MODE-*]

- F-CHN-MODE-01 Greenfield — 全新项目模式路由,全量编译 → Full Dynamic Spec Tree;入口脚本 `Scripts/run_greenfield_demo.py`。
- F-CHN-MODE-02 Brownfield — 存量项目模式路由,基线理解 + 差量编译 → Delta Dynamic Spec Tree;入口 `forgeue_manifest_importer.py`。
- F-CHN-MODE-03 Playable Runtime — 可运行游戏 demo 模式路由(boardgame / JRPG 等可玩 demo 脚本入口);与 BridgeChannel(CPP_PLUGIN / REMOTE_CONTROL / MOCK)概念正交。

### 4.5 Clarification + Constraint / Variant 决策

Clarification Gate(F-CHN-02 / F-CMP-09)对高风险与必填项执行 4 档决策:`blocking` 必须先解(否则阻断 promote)、`provisional` 自动传播但需后续确认、`soft` 仅记录、`closed` 已经被 GDD 显式回答。Constraint 字段进入 Static Spec 强约束,Variant 字段进入 Dynamic Spec 可选维度,二者由 Root Skill Contract(F-CHN-01)与 Design Space Discovery(F-CHN-S4-01)联合决定。fast_mode 运行禁止自动默认 `high` / `critical` 级 Clarification 项(F-GOV-02)。Clarification Gate 的最终报告(`clarification_gate_report.schema.json`)同时承担三种作用:对 Compiler 后续 Stage 提供已敲定的字段值;对 Run 治理提供 `is_promotable` 的输入条件之一;对人工评审提供 provisional 项的 audit trail。任何在 Stage 1 / 2 期间无法被 Clarification Gate 收敛的高风险字段,必须升格为 `blocking`,阻断后续 Stage 3-7 直至人工补全。

## 5. 数据契约总览

### 5.1 Schema 体系

- F-SCH-01 主链 v3 Schema 集 — 9 份(`root_skill_contract` → `reviewed_handoff_v3`)。
- F-SCH-02 v1/v2 兼容 Schema — `reviewed_handoff` / `reviewed_handoff_v2` / `build_ir` / `cross_review_report` / `skill_fragment` / `skill_fragment_v2`。
- F-SCH-03 共享基础 Schema — `common/{bounds,collision,error,material,primitives,transform}.schema.json`。
- F-SCH-04 反馈契约 Schema — `feedback/{actor,asset,level,project,validation}/` + `write_feedback/`。
- F-SCH-05 治理 Schema — `compiler_session` / `naming_resolution_log` / `design_decision_log` / `run_comparison` / `batch_manifest` / `evidence_manifest` / `gdd_coverage_matrix`(Phase 13)/ `provider_call` + `retry_policy`(Phase 12)。
- F-SCH-06 Examples 与版本清单 — `Schemas/examples/` + `Schemas/versions/` + 早期辅助(`gdd_projection` / `planner_output` / `run_plan`)。

完整清单(45 主 Schema + 28 examples = 73)详见 `contracts/schemas_catalog.md`。

### 5.2 MCP 工具体系

55 个 MCP 工具(51 正式 + 4 兼容 alias)的字段级签名表见 `contracts/mcp_tools_catalog.md`;权威源是 `Plugins/AgentBridge/MCP/tool_definitions.py` 的 `len(ALL_TOOLS) == 55` 实测。

### 5.3 Reviewed Handoff 主契约

Reviewed Handoff 是 Compiler → Execution 的唯一正式边界,有三代演进:v1(`reviewed_handoff.schema.json`,Phase 4-7,handoff_mode + delta_context)、v2(`reviewed_handoff_v2.schema.json`,Phase 8/9,Skill-First 6 阶段产物)、v3(`reviewed_handoff_v3.schema.json`,Phase 11,7 阶段主链 + `run_id` + provisional_items + baseline_coverage_summary)。当前权威版本为 v3,v1/v2 保留兼容路径以支持 boardgame / JRPG 回归。

### 5.4 共享字段规范

执行技术层字段一律 snake_case + UE5 路径,字段名 = UE5 C++ API 属性名(不另立翻译层);单位长度 cm、角度 degrees、extent 表 half-extent;严禁字段 `size` / `position` / `center` / `big` / `small` / `proper` / `near` / `far` 等模糊词。详见 `contracts/field_specification.md`。

## 6. 非功能需求

### 6.1 校验强度

- Schema 校验:`Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`,当前 `28/28` 通过;任一示例不符 → 退出码非 0,阻断 commit。
- 系统测试:`Plugins/AgentBridge/Tests/run_system_tests.py`,登记 364 条系统测试(13 stage / 17 测试类);L1/L2/L3 共约 26 条 C++ Automation 测试独立计数,不计入 364。
- Schema 必须使用 `additionalProperties: false`,字段未注册即拒绝执行。
- 容差比对统一走 C++ `FBridgeTransform::NearlyEquals`,Python 端只调不实现。

### 6.2 命名规范

GDD-First 命名 + UE5 标准路径。关卡路径 `/Game/Maps/<Name>.<Name>:PersistentLevel.<actor_label>`,资产路径 `/Game/<Category>/<Sub>/<AssetName>.<AssetName>`。Stage 6 输出的命名审计 sidecar `naming_resolution_log.schema.json` 记录所有命名解析与冲突。

### 6.3 可观测性

`ProjectState/Evidence/`(原始证据,截图 / 日志 / 序列化对象)、`ProjectState/Reports/`(报告文件,中文 Markdown)、`ProjectState/runs/<run_id>/`(每 run 独立 workspace + snapshots)、`ProjectState/snapshots/`(快照清单);所有 run-level 输出必须由 `evidence_manifest.schema.json` 索引。每条 Reports 记录必须以日期目录组织(`ProjectState/Reports/YYYY-MM-DD/`),并在 commit message 与 `task.md` 中互相引用,形成"代码改动 → 验证证据 → 任务节点"三向闭环。L3 UI 工具的 AutomationDriver 日志、L2 Build / Automation 测试的 build_log_path / report_path、截图工具的 PNG 与 metadata,均归 Evidence 目录管理。

### 6.4 文档治理

`task.md` 是当前阶段唯一开发驱动入口;Phase 收尾时切换为跳转页;文档释放门禁(F-HOOK-01)在 commit/push 前强制执行,逃生通道为 `[skip-doc]` 标记 / trivial 白名单 / `--no-verify`(后者仅在用户明确要求时使用)。详见 `governance.md`(待 Task 1.17 落地)。

### 6.5 安全 / 边界

项目层默认可写;`Plugins/AgentBridge/Source/AgentBridge/{Public,Private}/*` C++ 核心、`Scripts/bridge/*.py` Bridge 客户端、`Scripts/orchestrator/*.py` Orchestrator 核心、`AgentBridgeTests/` 测试体系、`Schemas/{common,feedback,write_feedback}/` 已稳定 Schema 默认只读(任何修改前必须先取得用户授权,详见 CLAUDE.md "绝对不要修改的文件"清单);项目目录外路径默认只读。任何在 L1/L2/L3 工具之上的写操作必须支持 `dry_run: true` 形式预检并返回 `created_objects` / `modified_objects` / `deleted_objects` / `actual_*` 读回字段,以便 Verifier(F-ORC-04)交叉比对;L3 UI 工具必须显式 `execution_method: ui_tool` 标记并在 Spec 中声明,避免被误用为日常写工具入口。Run 治理(F-GOV-*)规则:fast_mode run 永不可 promote;`generator_provider == "heuristic_fallback"` run 不可作为基线;只有 Stage 4 走 `mcp_agent` 或人工核准的 `llm` 路径的 run 才可作为 promotable candidate。

## 7. 外部接口

### 7.1 Remote Control HTTP API

端口 30010,主要端点 `/remote/object/call`(BlueprintCallable / UFUNCTION 调用)、`/remote/object/property`(读写 UPROPERTY)、`/remote/batch`(批量执行)。需要 UE Editor 实例已加载 `RemoteControl` + `RemoteControlWebInterface` 插件,详见 F-BRG-05。

### 7.2 UAT CLI

`RunUAT BuildCookRun -project=... -run -editortest -RunAutomationTest=<Filter>` 为唯一官方 Automation 入口;legacy `RunUAT RunAutomationTests` token 已被 `validate_no_legacy_automation_entrypoints.ps1`(F-VAL-01)主动禁用。Standalone Staged 走 `BuildCookRun -build -cook -stage` 标准流水线。

### 7.3 MCP stdio 协议

MCP Server(F-MCP-13)走 stdio 通道,55 个工具按命名空间组织(bridge_l1_* / bridge_l2_* / compiler_prepare_* / compiler_save_* / evidence_* / run_* 等);兼容 alias(F-MCP-12)4 个保留旧名映射。

### 7.4 Agent 接入面

支持 Claude Code(主)、Codex CLI、Gemini CLI 三类 Agent 客户端通过 MCP 协议接入;Agent 在 Stage 1-3 直接与 MCP 前端交互,在 Stage 4-7 通过 Compiler Core 内部 prepare/save 调度参与(不通过 MCP 对外工具)。证据裁决后由 MCP 后端返回 pass / fail / escalate。MCP 工具命名空间规范:Bridge passthrough 类工具走 `bridge_l1_*` / `bridge_l2_*` / `bridge_l3_*` 前缀;前端 Stage 1-3 走 `compiler_prepare_*` / `compiler_save_*` 配对前缀,Stage 4 节点交互走 `compiler_stage4_prepare_*` / `compiler_stage4_save_*`;后端 Evidence / Run 治理走 `evidence_*` / `run_*` 前缀;兼容 alias 仅保留 4 个旧名以避免外部脚本失效。Agent 客户端调用 MCP 工具时,工具输入参数会经 Schema 校验,输出经反馈 Schema(`status` / `summary` / `data` / `warnings` / `errors`)统一封装。

## 8. UE 5.7 迁移说明(汇总)

### 8.1 Breaking change 总览表(由 Phase 0 扫描产出)

来源 spec:`Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`。25 条 breaking change 候选已分桶 P1(7 条已裁决:1 false-positive + 6 confirmed)/ P2(12 条)/ P3(6 条)。

| 优先级 | 裁决 | ID 列表 |
|--------|------|---------|
| P1 false-positive | msc 已裁 | UE57-BC-007 |
| P1 confirmed | msc 已裁 | UE57-BC-008 / UE57-BC-010 / UE57-BC-012 / UE57-BC-016 / UE57-BC-017 / UE57-BC-025 |
| P2 suspected | pending-msc(本次新追加 3 条 reviewer 标记 P2 高优先) | UE57-BC-015 / UE57-BC-019 / UE57-BC-022 |
| P2 suspected(其余) | pending-msc | UE57-BC-001 / 002 / 004 / 005 / 006 / 011 / 014 / 020 / 023 |
| P3 suspected | pending-msc | UE57-BC-003 / 009 / 013 / 018 / 021 / 024 |

P1 6 条 confirmed 是升 5.7 必须修复的硬阻断点;P2/P3 共 18 条等 P1 跑通后再实测裁决。**UE57-BC-019(Remote Control HTTP 端点)严格保持 P2 suspected,reviewer pending-msc**,不归入 P1 confirmed(Task 1.1 教训)。

### 8.2 按模块迁移要点

- **F-CPP-* / 项目层 C++**: 修 UE57-BC-008(改用 `UEditorActorSubsystem` / `ULevelEditorSubsystem` 替代 `EditorScriptingUtilities` 模块依赖)、UE57-BC-010(`IncludeOrderVersion.Unreal5_5` → `Unreal5_6` 或 `Unreal5_7`)、UE57-BC-012(`.uproject EngineAssociation` 改 `"5.7"`)。
- **F-BRG-* / F-MCP-* / Python 层**: 修 UE57-BC-016(`unreal.EditorLevelLibrary.*` → `unreal.UnrealEditorSubsystem` / `LevelEditorSubsystem` / `EditorActorSubsystem`)、UE57-BC-017(`unreal.EditorAssetLibrary.*` → `unreal.EditorAssetSubsystem`)。
- **F-RT-* / F-VAL-* / Script 层**: 修 UE57-BC-025(`run_system_tests.py` / `task14a_phase11_standalone_smoke.py` / `start_ue_editor_*.ps1` 中 `UE_5.5` 路径 → `UE_5.7` 或抽到 `$env:UE_INSTALL_ROOT` 环境变量)。
- **配置 / 资产**: UE57-BC-015(Config Layer)与资产层 Blueprint / Niagara 节点级 deprecation 需 5.7 Editor 实测,P2 suspected。
- **Remote Control / UAT / Plugin**: UE57-BC-019(RC HTTP 端点)、UE57-BC-020(UAT BuildCookRun)、UE57-BC-022(uproject Plugins[])、UE57-BC-023(uplugin Plugins[])均 P2 suspected,等 P1 修完后跑 `validate_examples.py` + `run_system_tests.py` 看连带影响。

---

## 附录

### A. 术语表

- **Skill** — 能力语义单元,从 GDD 走向 Spec 的上游认知中间层,负责回答"这个游戏需要哪些能力 / 如何拆 / 如何映射到 spec family"。
- **Static Spec** — Spec family 的固定骨架,schema / contract / template / defaults 载体,框架预存。
- **Dynamic Spec** — 当前项目实例化的 spec 结果,结构受 Static Spec 约束,字段值由 AI Agent 基于 GDD 上下文填充。
- **Reviewed Handoff** — Compiler Plane → Execution Plane 的唯一正式交接物;Reviewed Dynamic Spec Tree + Build IR + metadata 的封装。
- **Run** — 一次 Compiler+Execution 端到端运行,以 `run_id` 标识,workspace 隔离在 `ProjectState/runs/<run_id>/`。
- **Stage** — 主链阶段(1-7),由 Compiler Pipeline Orchestrator 顺序调度。
- **Domain** — 在 Skill Graph 中,Skill 归属的能力领域(gameplay / hud / settings / level_transition / ...);跨 Domain 冲突由 Cross Review v2 兜底。
- **Generator Provider** — Stage 4 节点生成策略提供方,枚举 `mcp_agent` / `heuristic_fallback` / `llm`,决定 `is_promotable`。
- **Bridge Channel** — Bridge 客户端通信通道(`CPP_PLUGIN` / `REMOTE_CONTROL` / `MOCK`),与 Mode Routing 概念正交。
- **L1 / L2 / L3** — 工具体系层级:L1 语义工具(读 + 写 + 反馈)、L2 编辑器服务工具(构建 / 测试 / 保存 / Undo)、L3 UI 自动化工具(仅 L1 无对应 API 时启用)。
- **fast_mode** — 高速 CI 模式,跳过 high / critical Clarification 项,运行结果不可 promote(F-GOV-02)。
- **Promotion** — 把一次 run 的产物从 candidate 升格为基线产物(F-GOV-04 `evidence_promote_run`),受 F-GOV-02 / F-GOV-03 治理规则约束。

### B. 与旧文档映射(简表,详表 → archive/README.md)

> 第一列旧文档为 Phase 4 重写前的源路径(物理已搬入 `Docs/archive/`),用 `<code>` HTML 标签包裹避开 link_precheck 扫描;机器化反向映射见 `Docs/redirects.json`。

| 旧文档(已搬迁) | 已消化到本 SRS 的章节 |
|--------|----------------------|
| <code>Docs/Current/01&#95;Project&#95;Baseline.md</code> | §1.1 / §1.2 / §2.4 |
| <code>Docs/Current/02&#95;Current&#95;Phase&#95;Goals.md</code> | §2.4(Phase 11 Completed 口径)|
| <code>Docs/Current/05&#95;Implementation&#95;Boundary.md</code> | §6.5 |
| <code>Docs/Current/07&#95;Evidence&#95;And&#95;Artifacts.md</code> | §6.3 |
| <code>Docs/Current/14&#95;MCP&#95;Cognitive&#95;Bridge&#95;Anchor.md</code> | §3.5 / §4.1 / §4.4 |
| <code>Docs/Current/15&#95;Skill&#95;Spec&#95;Handoff&#95;Chain.md</code> | §4.1 / §4.2 / §5.3 / 附录 A |
| <code>Docs/Current/18&#95;Phase11&#95;Closeout.md</code> | §2.4 / §4.1 / §4.3 |
| <code>Plugins/AgentBridge/Docs/architecture&#95;overview.md</code> | §2.1 / §2.2 / §3.1 / §3.5 |
| <code>Plugins/AgentBridge/Docs/feedback&#95;interface&#95;catalog.md</code> | §3.2 / §5.1 / §5.4(经 `contracts/mcp_tools_catalog.md` 中转)|
| <code>Plugins/AgentBridge/Docs/feedback&#95;write&#95;mapping.md</code> | §3.2 / §5.1(经 `contracts/mcp_tools_catalog.md` 中转)|
| <code>Plugins/AgentBridge/Docs/skills&#95;and&#95;specs&#95;overview.md</code> | §3.6 / §4.1 |
| <code>Plugins/AgentBridge/Docs/ue5&#95;capability&#95;map.md</code> | §3.2 / §3.5 / §6.2 |

完整 108 份旧文档反向映射详见 `Docs/archive/README.md` 与 `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv`。
