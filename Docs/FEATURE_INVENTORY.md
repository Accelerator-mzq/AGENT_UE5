# Mvpv4TestCodex — Feature Inventory(多源交叉矩阵)

> 版本: v1.1(2026-05-26,内容评审修订)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §3
> 验收门禁底座: 每行 F-* ID 必须能在 SRS/LLD 锚点 grep 命中
> 状态: 骨架 v1.1,主文档锚点 + UE 5.7 状态待 Phase 1 / Phase 1.18 回填
> v1.1 修订要点:F-CMP-20..24 正名为 Legacy v1 Pipeline、F-GOV-03/04 证据源指向真实代码、F-RT-01/02 + F-CHN-MODE-03 不再混淆 BridgeChannel 与 Mode、新增 F-VAL/F-TST/F-HOOK/F-INP/F-DEMO 五类目共 ~13 行

## 类目扩展说明(v1.1 新增)

v1.1 在原 11 类(C++ / Bridge / Orchestrator / Compiler / MCP / Skill / Runtime / Chain / Governance / Schema)基础上补 5 个工程化类:

- **F-VAL** Validation Scripts — Schema 与治理校验脚本族
- **F-TST** Test — C++ L1/L2/L3 测试 + Python 系统测试套件
- **F-HOOK** Hook — document-release gate + Git hooks 安装
- **F-INP** Input — ProjectInputs 下的 GDD/Preset 实例输入
- **F-DEMO** Demo — 可运行 demo 与资产生成脚本族

## 矩阵主表

| ID | 功能名 | 简述 | 模块归属 | 主文档锚点 | 证据源 | 测试覆盖 | UE 5.7 状态 |
|----|--------|------|----------|------------|--------|----------|-------------|
| F-CPP-01 | UAgentBridgeSubsystem | UEditorSubsystem 主入口,Editor 启动挂载 Tick / Python 跨语言桥接 | C++ | TBD | Plugins/AgentBridge/Source/AgentBridge/Public/AgentBridgeSubsystem.h + Private/AgentBridgeSubsystem.cpp | TBD | TBD |
| F-CPP-02 | UAgentBridgeCommandlet | UCommandlet 子类,无窗口模式执行 Agent 任务入口 | C++ | TBD | Plugins/AgentBridge/Source/AgentBridge/Public/AgentBridgeCommandlet.h + Private/AgentBridgeCommandlet.cpp | TBD | TBD |
| F-CPP-03 | FUATRunner | UAT BuildCookRun 同步/异步包装,内部用 FProcHandle | C++ | TBD | Plugins/AgentBridge/Source/AgentBridge/Public/UATRunner.h + Private/UATRunner.cpp | TBD | TBD |
| F-CPP-04 | FAutomationDriverAdapter | 包装 FAutomationDriverModule 提供给 UI 自动化族 | C++ | TBD | Plugins/AgentBridge/Source/AgentBridge/Public/AutomationDriverAdapter.h + Private/AutomationDriverAdapter.cpp | TBD | TBD |
| F-CPP-05 | BridgeTypes 共享类型 | FAgentBridgeReply / FAgentBridgeRequest 等 USTRUCT 定义 | C++ | TBD | Plugins/AgentBridge/Source/AgentBridge/Public/BridgeTypes.h | TBD | TBD |
| F-CPP-06 | FAgentBridgeModule | IModuleInterface 实现,模块加载/卸载钩子 + AGENTBRIDGE_API 导出注册 | C++ | TBD | Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeModule.cpp | TBD | TBD |
| F-BRG-01 | L1 查询接口族 | get_actors/get_actor_components/get_actor_property 等 ~12 查询工具 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/query_tools.py | TBD | TBD |
| F-BRG-02 | L1 写接口族 | set_actor_property/spawn_actor/destroy_actor 等 ~4 写工具 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/write_tools.py | TBD | TBD |
| F-BRG-03 | L1 反馈接口族 | 实测 9 份 feedback response schema(actor/asset/level/project/validation)+ 1 份 write_feedback 共 10 份反馈契约 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/{query_tools,write_tools}.py + Schemas/feedback/{actor,asset,level,project,validation}/*.response.schema.json + Schemas/write_feedback/write_operation_feedback.response.schema.json | TBD | TBD |
| F-BRG-04 | L3 UI 自动化族 | UI 自动化驱动入口,封装 FAutomationDriverAdapter 调用 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/ui_tools.py | TBD | TBD |
| F-BRG-05 | Remote Control HTTP 客户端 | 30010 端口 PUT/GET 包装,RC API 通信主体 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/remote_control_client.py | TBD | TBD |
| F-BRG-06 | UAT 包装器 Python 侧 | Python 侧 UAT 调用封装,对应 C++ F-CPP-03 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/uat_runner.py | TBD | TBD |
| F-BRG-07 | UE 资产/关卡 helpers | UE Editor Python API 辅助封装(资产/关卡操作通用) | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/ue_helpers.py | TBD | TBD |
| F-BRG-08 | 项目配置解析 | 项目路径/UE 安装路径/RC 端口等运行时配置加载 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/project_config.py | TBD | TBD |
| F-BRG-09 | bridge_core 通信主体 | Bridge 客户端核心通信循环 + 命令分发 | Bridge | TBD | Plugins/AgentBridge/Scripts/bridge/bridge_core.py | TBD | TBD |
| F-ORC-01 | 主体编排 + 通道选择 | Orchestrator 主循环 / Editor vs Standalone 通道路由 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py | TBD | TBD |
| F-ORC-02 | Plan 生成 | Spec → Plan 转换 + RunPlan 构建 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/{plan_generator,run_plan_builder}.py | TBD | TBD |
| F-ORC-03 | Spec 读取 | YAML/JSON Spec 加载 + 字段解析 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py | TBD | TBD |
| F-ORC-04 | 验证与对标 | Plan 执行结果对照 Spec 期望值校验 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/verifier.py | TBD | TBD |
| F-ORC-05 | 报告生成 | 运行报告/证据落盘组装 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/report_generator.py | TBD | TBD |
| F-ORC-06 | 故障恢复规划 | 失败 Step 重试/回滚策略生成 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/recovery_planner.py | TBD | TBD |
| F-ORC-07 | Handoff 执行 | reviewed_handoff 执行 + validation 插桩 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/{handoff_runner,validation_inserter}.py | TBD | TBD |
| F-ORC-08 | ForgeUE manifest 导入 | ForgeUE 产出 manifest → reviewed_handoff 桥接 | Orchestrator | TBD | Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py | TBD | TBD |
| F-CMP-01 | Legacy Compiler — analysis | Legacy 编译器分析子模块(Phase 8 之前) | Compiler | TBD | Plugins/AgentBridge/Scripts/compiler/analysis/ | TBD | TBD |
| F-CMP-02 | Legacy Compiler — generation | Legacy 编译器生成子模块 | Compiler | TBD | Plugins/AgentBridge/Scripts/compiler/generation/ | TBD | TBD |
| F-CMP-03 | Legacy Compiler — handoff | Legacy handoff 构建子模块 | Compiler | TBD | Plugins/AgentBridge/Scripts/compiler/handoff/ | TBD | TBD |
| F-CMP-04 | Legacy Compiler — intake | Legacy 输入接入子模块 | Compiler | TBD | Plugins/AgentBridge/Scripts/compiler/intake/ | TBD | TBD |
| F-CMP-05 | Legacy Compiler — review | Legacy 跨审子模块 | Compiler | TBD | Plugins/AgentBridge/Scripts/compiler/review/ | TBD | TBD |
| F-CMP-06 | Legacy Compiler — routing | Legacy 路由子模块 | Compiler | TBD | Plugins/AgentBridge/Scripts/compiler/routing/ | TBD | TBD |
| F-CMP-07 | Phase 11 Pipeline 主入口 | Skill-First 编译框架顶层入口 | Compiler | TBD | Plugins/AgentBridge/Compiler/pipeline/ | TBD | TBD |
| F-CMP-08 | Stage — root_skill_contract | Stage 1 Root Skill Contract 生成 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/root_skill_contract.py | TBD | TBD |
| F-CMP-09 | Stage 2 — 澄清门/Clarification Gate | Stage 2 — 用户必填项澄清门 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/clarification_gate.py | TBD | TBD |
| F-CMP-10 | Stage 3 — 技能图规划/Skill Graph Planning | Stage 3 — SkillGraph 规划 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py | TBD | TBD |
| F-CMP-11 | Stage 4 路 A — 设计空间发现/Discovery Fallback | Stage 4 路 A — Design Space Discovery 回退 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/discovery_fallback.py | TBD | TBD |
| F-CMP-12 | Stage 4 路 B — 实现化/Realization Fallback | Stage 4 路 B — Realization 回退 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/realization_fallback.py | TBD | TBD |
| F-CMP-13 | Stage 4 路 C — 收敛/Convergence Fallback | Stage 4 路 C — Convergence 回退 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/convergence_fallback.py | TBD | TBD |
| F-CMP-14 | Stage 通用 — Agent 协议/Agent Protocol | Stage 通用 — LLM Agent 协议封装 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/agent_protocol.py | TBD | TBD |
| F-CMP-15 | Stage 通用 — LLM 客户端/LLM Client | Stage 通用 — LLM 客户端(OpenAI/Claude 等 provider 抽象) | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/llm_client.py | TBD | TBD |
| F-CMP-16 | Stage 7 — Handoff v3 输出/Handoff v3 | Stage 7 — reviewed_handoff v3 生成 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/handoff_v3.py | TBD | TBD |
| F-CMP-17 | Stage 5 — 跨审 v2/Cross Review v2 | Stage 5 — Cross Domain Review v2 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/cross_review_v2.py | TBD | TBD |
| F-CMP-18 | Stage 6 — 下降 v2/Lowering v2 | Stage 6 — Build IR v2 下降 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/lowering_v2.py | TBD | TBD |
| F-CMP-19 | Stage 4 — 领域技能运行时/Domain Skill Runtime | Stage 4 — Domain Skill 运行时承载 | Compiler | TBD | Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py | TBD | TBD |
| F-CMP-20 | Framework — cross_review (Legacy v1 Pipeline) | Phase 8/9 v1 五阶段管线 Stage 4 节点;由 pipeline_orchestrator STAGE_NAME_MAP_V1 调度 | Compiler | TBD | Plugins/AgentBridge/Compiler/cross_review/ + Compiler/pipeline/pipeline_orchestrator.py(STAGE_NAME_MAP_V1) | TBD | TBD |
| F-CMP-21 | Framework — intake (Legacy v1 Pipeline) | Phase 8/9 v1 五阶段管线 Stage 1 design_intake 节点;由 pipeline_orchestrator STAGE_NAME_MAP_V1 调度 | Compiler | TBD | Plugins/AgentBridge/Compiler/intake/ + Compiler/pipeline/pipeline_orchestrator.py(STAGE_NAME_MAP_V1) | TBD | TBD |
| F-CMP-22 | Framework — lowering (Legacy v1 Pipeline) | Phase 8/9 v1 五阶段管线 Stage 5 lowering 节点;由 pipeline_orchestrator STAGE_NAME_MAP_V1 调度 | Compiler | TBD | Plugins/AgentBridge/Compiler/lowering/ + Compiler/pipeline/pipeline_orchestrator.py(STAGE_NAME_MAP_V1) | TBD | TBD |
| F-CMP-23 | Framework — planner (Legacy v1 Pipeline) | Phase 8/9 v1 五阶段管线 Stage 2 planner 节点;由 pipeline_orchestrator STAGE_NAME_MAP_V1 调度 | Compiler | TBD | Plugins/AgentBridge/Compiler/planner/ + Compiler/pipeline/pipeline_orchestrator.py(STAGE_NAME_MAP_V1) | TBD | TBD |
| F-CMP-24 | Framework — skill_runtime (Legacy v1 Pipeline) | Phase 8/9 v1 五阶段管线 Stage 3 skill_runtime 节点;由 pipeline_orchestrator STAGE_NAME_MAP_V1 调度 | Compiler | TBD | Plugins/AgentBridge/Compiler/skill_runtime/ + Compiler/pipeline/pipeline_orchestrator.py(STAGE_NAME_MAP_V1) | TBD | TBD |
| F-MCP-01 | Bridge L1 查询族(MCP 暴露) | catalog 12 工具,封装 F-BRG-01 | MCP | TBD | Plugins/AgentBridge/MCP/{tool_definitions,py_channel}.py | TBD | TBD |
| F-MCP-02 | Bridge L1 写族(MCP 暴露) | 4 工具,封装 F-BRG-02 | MCP | TBD | Plugins/AgentBridge/MCP/{tool_definitions,py_channel}.py | TBD | TBD |
| F-MCP-03 | Bridge L1 反馈族(MCP 暴露) | 7 工具,封装 F-BRG-03 | MCP | TBD | Plugins/AgentBridge/MCP/{tool_definitions,py_channel}.py | TBD | TBD |
| F-MCP-04 | Bridge L2 编辑器服务族 | 编辑器级闭环服务(spawn+verify 等) | MCP | TBD | Plugins/AgentBridge/MCP/{tool_definitions,rc_channel}.py | TBD | TBD |
| F-MCP-05 | Bridge L3 UI 族(MCP 暴露) | UI 自动化工具,封装 F-BRG-04 | MCP | TBD | Plugins/AgentBridge/MCP/{tool_definitions,rc_channel}.py | TBD | TBD |
| F-MCP-06 | 前端 Stage 1 Root Skill Contract 族 | prepare/save Root Skill Contract MCP 工具 | MCP | TBD | Plugins/AgentBridge/MCP/compiler_tools.py + Compiler/stages/root_skill_contract.py | TBD | TBD |
| F-MCP-07 | 前端 Stage 2 Clarification Gate 族 | 澄清门交互 MCP 工具 | MCP | TBD | Plugins/AgentBridge/MCP/compiler_tools.py + Compiler/stages/clarification_gate.py | TBD | TBD |
| F-MCP-08 | 前端 Stage 3 Skill Graph Planning 族 | SkillGraph 规划交互 MCP 工具 | MCP | TBD | Plugins/AgentBridge/MCP/compiler_tools.py + Compiler/stages/skill_graph_planning.py | TBD | TBD |
| F-MCP-09 | 前端 Stage 4 节点交互族 | Discovery/Realization/Convergence 三路节点交互 | MCP | TBD | Plugins/AgentBridge/MCP/compiler_tools.py + Compiler/stages/{discovery,realization,convergence}_fallback.py | TBD | TBD |
| F-MCP-10 | 后端 Evidence 读写族 | ProjectState/Evidence 读写 MCP 工具 | MCP | TBD | Plugins/AgentBridge/MCP/evidence_tools.py | TBD | TBD |
| F-MCP-11 | 后端 Run 治理族 | compare/promote 等 Run 治理 MCP 工具 | MCP | TBD | Plugins/AgentBridge/MCP/compiler_tools.py | TBD | TBD |
| F-MCP-12 | 兼容 alias 族 | 4 个向后兼容 alias 工具 | MCP | TBD | Plugins/AgentBridge/MCP/{tool_definitions,server}.py | TBD | TBD |
| F-MCP-13 | MCP Server 主入口 | MCP 协议 server + 命名空间路由(F-MCP-* 入口) | MCP | TBD | Plugins/AgentBridge/MCP/{server,naming}.py | TBD | TBD |
| F-SKL-01 | SkillGraph 数据结构 | SkillGraph / SkillNode 数据模型 + 序列化 | Skill | TBD | Plugins/AgentBridge/Compiler/skill_runtime/ + Schemas/skill_graph.schema.json | TBD | TBD |
| F-SKL-02 | Domain Skill Runtime | Domain Skill 运行时实现 | Skill | TBD | Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py | TBD | TBD |
| F-SKL-03 | Baseline 6 Skill 模板 | hud/main_menu/pause/results/settings/start_screen 6 基线模板 | Skill | TBD | Plugins/AgentBridge/SkillTemplates/baseline/{hud,main_menu,pause,results,settings,start_screen}/ | TBD | TBD |
| F-SKL-04 | Genre Pack — Boardgame | Boardgame 类型扩展包 | Skill | TBD | Plugins/AgentBridge/SkillTemplates/genre_packs/boardgame/ | TBD | TBD |
| F-RT-01 | UE Editor 在线引导关卡 | UE Editor 在线模式下的关卡启动 + Spec 引导执行;注意 Bridge 通信通道(CPP_PLUGIN/REMOTE_CONTROL/MOCK)与本概念正交 | Runtime | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py(run 入口) | TBD | TBD |
| F-RT-02 | Standalone Staged 运行时 | 打包脱离 Editor 的 Standalone staged 模式运行时;由 UAT BuildCookRun 产出可独立运行的目标 | Runtime | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py + Plugins/AgentBridge/Source/AgentBridge/Private/UATRunner.cpp + Scripts/bridge/uat_runner.py | TBD | TBD |
| F-RT-03 | Evidence 落盘 | ProjectState/Evidence 目录证据组织规范 | Runtime | TBD | Plugins/AgentBridge/MCP/evidence_tools.py + ProjectState/Evidence/ | TBD | TBD |
| F-RT-04 | Reports 生成 | ProjectState/Reports 报告生成与落盘 | Runtime | TBD | Plugins/AgentBridge/Scripts/orchestrator/report_generator.py + ProjectState/Reports/ | TBD | TBD |
| F-RT-05 | Run Workspace 隔离 | 每 run_id 独立 workspace 隔离 | Runtime | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py + ProjectState/runs/ | TBD | TBD |
| F-CHN-01 | 主链 Stage 1 — Root Skill Contract | 主链第 1 阶段:根技能契约 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/root_skill_contract.py + Schemas/root_skill_contract.schema.json | TBD | TBD |
| F-CHN-02 | 主链 Stage 2 — Clarification Gate | 主链第 2 阶段:澄清门 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/clarification_gate.py + Schemas/clarification_gate_report.schema.json | TBD | TBD |
| F-CHN-03 | 主链 Stage 3 — Skill Graph Planning | 主链第 3 阶段:技能图规划 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py + Schemas/skill_graph.schema.json | TBD | TBD |
| F-CHN-04 | 主链 Stage 4 — Design / Realization / Convergence | 主链第 4 阶段:三路设计/实现/收敛 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/{discovery,realization,convergence}_fallback.py | TBD | TBD |
| F-CHN-05 | 主链 Stage 5 — Cross Review v2 | 主链第 5 阶段:跨审 v2 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/cross_review_v2.py + Schemas/cross_review_report_v2.schema.json | TBD | TBD |
| F-CHN-06 | 主链 Stage 6 — Lowering v2 | 主链第 6 阶段:Build IR 下降 v2 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/lowering_v2.py + Schemas/build_ir_v2.schema.json | TBD | TBD |
| F-CHN-07 | 主链 Stage 7 — Handoff v3 | 主链第 7 阶段:reviewed_handoff v3 输出 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/handoff_v3.py + Schemas/reviewed_handoff_v3.schema.json | TBD | TBD |
| F-CHN-S4-01 | Stage 4 路 A — Design Space Discovery | Stage 4 设计空间发现路径 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/discovery_fallback.py + Schemas/design_space_report.schema.json | TBD | TBD |
| F-CHN-S4-02 | Stage 4 路 B — Realization | Stage 4 实现化路径 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/realization_fallback.py + Schemas/realization_candidates.schema.json | TBD | TBD |
| F-CHN-S4-03 | Stage 4 路 C — Convergence | Stage 4 收敛路径 | Chain | TBD | Plugins/AgentBridge/Compiler/stages/convergence_fallback.py + Schemas/converged_realization_pack.schema.json | TBD | TBD |
| F-CHN-MODE-01 | 模式路由 — Greenfield | 全新项目模式路由 | Chain | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py + Scripts/run_greenfield_demo.py | TBD | TBD |
| F-CHN-MODE-02 | 模式路由 — Brownfield | 存量项目模式路由 | Chain | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py + forgeue_manifest_importer.py | TBD | TBD |
| F-CHN-MODE-03 | 模式路由 — Playable Runtime | 可运行游戏 demo 模式路由(对应 boardgame / jrpg 等可玩 demo 脚本入口);与 BridgeChannel 概念正交 | Chain | TBD | Scripts/run_boardgame_playable_demo.py + Scripts/run_jrpg_turn_based_demo.py + Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py | TBD | TBD |
| F-GOV-01 | run_id 生命周期 | run_id 生成/绑定/终结全周期治理 | Governance | TBD | Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py + MCP/compiler_tools.py | TBD | TBD |
| F-GOV-02 | fast_mode 不可 promote | fast_mode 运行禁止 promote 的治理规则 | Governance | TBD | Plugins/AgentBridge/MCP/compiler_tools.py + Schemas/compiler_session.schema.json | TBD | TBD |
| F-GOV-03 | generator_provider 影响 is_promotable | generator_provider 字段在 CompilerSession 上决定 is_promotable 的治理规则 | Governance | TBD | Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py + Plugins/AgentBridge/Compiler/pipeline/session.py + Schemas/compiler_session.schema.json | TBD | TBD |
| F-GOV-04 | compare/promote 工具 | Run 比较与晋升 MCP 工具入口(evidence_compare_runs / evidence_promote_run) | Governance | TBD | Plugins/AgentBridge/MCP/evidence_tools.py + Plugins/AgentBridge/MCP/server.py + Plugins/AgentBridge/MCP/tool_definitions.py + Schemas/run_comparison.schema.json | TBD | TBD |
| F-SCH-01 | 主链 v3 Schema 集 | 主链 v3 共 9 份核心 Schema(Root Skill Contract → Reviewed Handoff v3) | Schema | TBD | Plugins/AgentBridge/Schemas/{root_skill_contract,skill_graph,design_space_report,realization_candidates,converged_realization_pack,clarification_gate_report,cross_review_report_v2,build_ir_v2,reviewed_handoff_v3}.schema.json | TBD | TBD |
| F-SCH-02 | v1/v2 兼容 Schema | 主链 v1/v2 兼容契约(reviewed_handoff/build_ir/cross_review/skill_fragment) | Schema | TBD | Plugins/AgentBridge/Schemas/{reviewed_handoff,reviewed_handoff_v2,build_ir,cross_review_report,skill_fragment,skill_fragment_v2}.schema.json | TBD | TBD |
| F-SCH-03 | 共享基础 Schema | common/ 6 份基础类型(bounds/collision/error/material/primitives/transform) | Schema | TBD | Plugins/AgentBridge/Schemas/common/{bounds,collision,error,material,primitives,transform}.schema.json | TBD | TBD |
| F-SCH-04 | 反馈契约 Schema | feedback/ 5 子目录 + write_feedback/ 1 反馈契约 | Schema | TBD | Plugins/AgentBridge/Schemas/feedback/{actor,asset,level,project,validation}/ + write_feedback/ | TBD | TBD |
| F-SCH-05 | 治理 Schema | Run 治理 / 命名解析 / 设计决策 / 批次 / 证据清单契约 | Schema | TBD | Plugins/AgentBridge/Schemas/{compiler_session,naming_resolution_log,design_decision_log,run_comparison,batch_manifest,evidence_manifest}.schema.json | TBD | TBD |
| F-SCH-06 | Examples 与版本清单 | 样例集合 + 版本清单 + 早期辅助 Schema | Schema | TBD | Plugins/AgentBridge/Schemas/examples/ + Plugins/AgentBridge/Schemas/versions/ + Plugins/AgentBridge/Schemas/{gdd_projection,planner_output,run_plan}.schema.json | TBD | TBD |
| F-VAL-01 | Plugin/Project 治理校验脚本族 | Scripts/validation/ 下 validate_no_legacy_automation_entrypoints / phase7_governance_audit / stage_plugin_release 等治理校验脚本 | Validation | TBD | Plugins/AgentBridge/Scripts/validation/*.{py,ps1} | TBD | TBD |
| F-VAL-02 | Schema 校验脚本族 | Schema 与 Handoff 契约校验 | Validation | TBD | Plugins/AgentBridge/Scripts/validation/{validate_examples,test_handoff_schema}.py | TBD | TBD |
| F-VAL-03 | Evidence / Functional Map 生成 | Editor 证据捕获 + Task15 Functional Map 生成 | Validation | TBD | Scripts/validation/{capture_editor_evidence,create_task15_functional_map,capture_phase5_evidence,phase7_governance_audit}.py | TBD | TBD |
| F-TST-01 | L1 测试族(Query/Write/UITool) | C++ L1 接口测试 3 份 | Test | TBD | Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/L1_{Query,Write,UITool}Tests.cpp | TBD | TBD |
| F-TST-02 | L2 闭环测试族 | C++ L2 编辑器闭环 Spec 测试 2 份 | Test | TBD | Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/{L2_ClosedLoopSpecs,L2_UIToolClosedLoopSpec}.spec.cpp | TBD | TBD |
| F-TST-03 | L3 FunctionalTest + Gauntlet 控制器 | C++ L3 关卡级 FunctionalTest Actor 与 Gauntlet 控制器 | Test | TBD | Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/L3_FunctionalTestActor.cpp + AgentBridgeGauntletController.cpp | TBD | TBD |
| F-TST-04 | 系统测试套件(240 条) | Phase 8/9/10 10 个 Stage 共 240 条系统测试 + fixtures + scripts | Test | TBD | Plugins/AgentBridge/Tests/run_system_tests.py + Plugins/AgentBridge/Tests/SystemTestCases.md + Plugins/AgentBridge/Tests/{scripts,fixtures}/ | TBD | TBD |
| F-HOOK-01 | document-release gate | document-release 释放门禁主体 + 自测 | Hook | TBD | Scripts/hooks/doc_release_gate.py + Scripts/hooks/tests/ | TBD | TBD |
| F-HOOK-02 | Git hooks 安装与 CC 通知 | Git hooks 安装器 + Claude Code 通知 wrapper + commit-msg/pre-commit/pre-push 模板 | Hook | TBD | Scripts/hooks/install_git_hooks.py + Scripts/hooks/cc_notify_wrapper.py + Scripts/hooks/{commit-msg,pre-commit,pre-push} | TBD | TBD |
| F-INP-01 | GDD 实例输入族 | Boardgame TicTacToe / Monopoly / JRPG 三份 GDD 实例输入 | Input | TBD | ProjectInputs/GDD/{boardgame_tictactoe_v1,GDD_MonopolyGame,jrpg_turn_based_v1}.md | TBD | TBD |
| F-INP-02 | Compiler Profile / Mode Override 预设 | Compiler Profile 与 Mode Override 预设 YAML | Input | TBD | ProjectInputs/Presets/{compiler_profile,mode_override}.yaml | TBD | TBD |
| F-DEMO-02 | 可运行游戏 demo 族 | Boardgame Playable + JRPG Turn-Based + Phase 7 P1 收敛三份可运行 demo 脚本 | Demo | TBD | Scripts/run_boardgame_playable_demo.py + Scripts/run_jrpg_turn_based_demo.py + Scripts/run_phase7_p1_convergence.py | TBD | TBD |
| F-DEMO-03 | 资产生成 / Skills 同步辅助族 | Monopoly 资产批量生成脚本 + Skills 同步辅助 | Demo | TBD | Scripts/phase8_generate_monopoly_assets.py + Scripts/sync_skills.py | TBD | TBD |

> 说明:F-DEMO-01(Greenfield / Brownfield 演示族)概念已并入 F-CHN-MODE-01/02,故 F-DEMO 系列从 F-DEMO-02 起。

## 验收门禁(摘自关联 spec v1.1 §3.2 / §8)

| 证据源 | 数量 | 细粒度门禁 |
|--------|------|------------|
| 代码公开符号 | `TBD: Phase 1 grep 后回填` | 每符号 ≥ 1 F-* 或 catalog 行引用 |
| MCP 工具 | 53 | mcp_tools_catalog 53 行 + 每行 6 字段完整 |
| Schema | `TBD: Phase 1 实测清点(根 .json + common + feedback + write_feedback + 子目录)` [^schema-count] | schemas_catalog 实测行数 + 每行 5 字段完整 |
| 测试用例 | 266(系统测试套件 240 + L1/L2/L3 共 ≈26 C++ 测试) | test_spec 266 行 + 每行 5 字段(含当前 pass/fail/skip) |
| 旧文档 | 108(详见 inventory CSV / archive/README.md) | redirects.json 每份有 old→new 映射 |

[^schema-count]: spec 写的 64 与 reviewer 实测(Schemas 根 25 + common 6 + feedback 8 + write_feedback 1 ≈ 40)偏差较大,留待 Phase 1 复核确认。
