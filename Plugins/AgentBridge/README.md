# AgentBridge - UE5 通用 Agent 开发框架插件

> 插件版本：v0.9.0
> 文档口径：Phase 11 已完成
> 目标引擎版本：UE5.5.4

## 1. 插件定义

`AgentBridge` 是面向 UE5 项目的通用 Agent 开发框架插件，提供：

- Skill Compiler Plane（Phase 11 升级为 Skill-First Design Compiler）
- Reviewed Handoff（v3，含 naming_resolution_log 与 design_decision_log）
- Execution Orchestrator
- L1 / L2 / L3 受控工具体系
- 写后读回、Schema 校验、回归与证据留存
- Claude Code 可接入的 MCP Server
- MCP 认知桥接层（前端 Stage 1-3 + 后端证据裁决）
- Stage 4 三路生成策略（MCP Agent / LLM Internal / Heuristic Fallback）
- Run 治理（run_id、compare、promote、fast_mode）

项目层负责输入、实例与治理；插件层负责通用编译、执行、验证与证据框架。

## 2. 当前实现状态

### 已稳定

- C++ Editor Plugin + Bridge 三通道
- L1 / L2 / L3 工具体系
- Reviewed Handoff / Run Plan / Handoff Runner
- Greenfield / Brownfield / Playable Runtime 主链
- Phase 9 MCP stdio Server

### Phase 10 已完成能力

- `Compiler/pipeline/` 的 `session.py` 与 `pipeline_orchestrator.py` 基础框架
- `Schemas/compiler_session.schema.json` Session 契约
- Phase 10 MCP 前端认知分解工具与后端证据裁决工具
- MonopolyGame 端到端 Pipeline 闭环

### Phase 11 已完成能力

- `session_version 1.0 / 2.0` 共存路由，引入 `run_id`、`fast_mode`、`generator_provider` 与 `promotable` 治理字段
- Phase 11 v2 主链：Root Skill Contract → Clarification Gate → Skill Graph Planning → Domain Skill Runtime → Cross Review v2 → Build IR v2 → Reviewed Handoff v3
- Stage 4 三路生成策略：`mcp_agent` 主路径、`llm` 内置路径（已接入，高负载验收暂缓）、`heuristic_fallback` 显式后备
- MCP 前端工具升级：新增 clarification_prepare/save、stage4_node_prepare/save、root_skill_prepare/save、skill_graph_prepare/save
- MCP 后端新增 Run 治理工具：evidence_create_batch、evidence_compare_runs、evidence_promote_run
- Phase 11 Schema 集新增/升级 12 个，`validate_examples.py --strict` 为 `26/26` 通过
- Baseline Domain Skill Template 全套（`SkillTemplates/baseline/`）
- UE 运行时最小可玩性已通过 Editor game 与 staged standalone 双路径验证
- 当前 MCP 工具总数为 `53`（`49` 正式主工具 + `4` 兼容 alias）

关键证据：

- [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)
- [task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
- [phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md)

## 3. 目录结构

```text
AgentBridge/
├── README.md
├── AGENTS.md
├── Source/
├── Scripts/
│   ├── bridge/
│   ├── compiler/
│   ├── orchestrator/
│   ├── evidence/
│   └── validation/
├── Compiler/
├── Schemas/
├── Specs/
├── Skills/
├── SkillTemplates/
├── MCP/
├── Docs/
├── Tests/
└── Gauntlet/
```

## 4. 推荐阅读顺序

1. 本文件
2. [architecture_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/architecture_overview.md)
3. [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/AGENTS.md)
4. [tool_contract_v0_1.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/tool_contract_v0_1.md)
5. [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)

## 5. 常用命令

```powershell
# Schema example 严格校验（26/26）
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

## 6. 当前边界

- MCP 前端边界固定为 Stage 1-3（Root Skill Contract、Clarification Gate、Skill Graph Planning），Stage 4-7 由 Compiler Core 调度。
- Stage 4 Domain Skill Runtime 支持三路生成：`mcp_agent`（MCP 交互式 prepare/save）、`llm`（pipeline 内置 LLM API）、`heuristic_fallback`（确定性后备）。
- MCP 后端负责证据读取、`pass / fail / escalate` 裁决、Run compare/promote 治理，不直接控制 PIE、不模拟输入。
- `fast_mode` run 不可 promote，`generator_provider` 影响 `is_promotable` 属性。
