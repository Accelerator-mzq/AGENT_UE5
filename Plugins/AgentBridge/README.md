# AgentBridge - UE5 通用 Agent 开发框架插件

> 插件版本：v0.8.0
> 文档口径：Phase 10 已完成
> 目标引擎版本：UE5.5.4

## 1. 插件定义

`AgentBridge` 是面向 UE5 项目的通用 Agent 开发框架插件，提供：

- Skill Compiler Plane
- Reviewed Handoff
- Execution Orchestrator
- L1 / L2 / L3 受控工具体系
- 写后读回、Schema 校验、回归与证据留存
- Claude Code 可接入的 MCP Server
- Phase 10 新增的 MCP 认知桥接层与 Evidence 裁决层

项目层负责输入、实例与治理；插件层负责通用编译、执行、验证与证据框架。

## 2. 当前实现状态

### 已稳定

- C++ Editor Plugin + Bridge 三通道
- L1 / L2 / L3 工具体系
- Reviewed Handoff / Run Plan / Handoff Runner
- Greenfield / Brownfield / Playable Runtime 主链
- Phase 9 MCP stdio Server

### Phase 10 已完成能力

- `Compiler/pipeline/` 已提供 `session.py` 与 `pipeline_orchestrator.py`
- `Schemas/compiler_session.schema.json` 已固定 Phase 10 Session 契约
- `MCP/compiler_tools.py` 已注册 6 个前端认知分解工具
- `Scripts/evidence/` 已提供 `run_id` 与 `evidence_manifest` 标准化能力
- `MCP/evidence_tools.py` 已注册 8 个后端证据裁决工具
- `ProjectState/phase10/` 已完成 MonopolyGame 从 GDD 到 `reviewed_handoff_v2` 的 12 个核心 JSON 落地
- `L_MonopolyBoard_Pipeline` 已完成 Build IR 驱动创建与运行时验证
- 当前 MCP 工具总数稳定为 `42`

关键证据：

- [17_Phase10_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/17_Phase10_Closeout.md)
- [task09_final_acceptance_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task09_final_acceptance_validation.md)
- [live_smoke_get_current_project_state_2026-04-11.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/live_smoke_get_current_project_state_2026-04-11.md)

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
# Schema example 校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# Phase 10 相关系统测试
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=7,9,10

# 单独验证 MCP 集成层
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=10

# 启动 MCP Server
python Plugins/AgentBridge/MCP/server.py
```

## 6. 当前边界

- MCP 前端边界固定为 Stage 1-2 认知分解，不越权执行 Stage 3-5。
- Stage 3-5 由 Compiler Core 调度。
- MCP 后端只做证据读取与 `pass / fail / escalate` 裁决，不直接控制 PIE、不模拟输入。
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 当前统一登记 `248` 条系统测试。
