# CLAUDE.md — Mvpv4TestCodex 项目

> 本文件供 Claude Code / Codex / 其他 AI Agent 在进入本项目时自动读取。
> 最后更新：2026-04-06

## 项目概述

UE5.5.4 项目，使用 AgentBridge 插件作为通用 Agent 开发框架。
AgentBridge 不只是工具接口插件，而是包含编译前端（Skill Compiler Plane）、交接物机制（Reviewed Handoff）、执行编排（Orchestrator）、受控工具体系（L1/L2/L3）的完整框架。

## 分层原则

- **项目层**（本工程根目录）：输入源、配置、实例、治理
- **插件层**（Plugins/AgentBridge/）：通用编译、执行、验证框架
- 项目层保存实例，插件层提供机制
- Compiler / Handoff / Orchestrator 主体在插件层，不在项目层

## 进入项目后的阅读顺序

1. `AGENTS.md` — 项目级 Agent 规则
2. `Docs/Current/00_Index.md` — 当前阶段索引
3. `Docs/Current/10_Phase8_Closeout.md` — Phase 8 收尾总览
4. `Docs/Current/01_Project_Baseline.md` — 项目基线
5. `Docs/Current/05_Implementation_Boundary.md` — 实施边界
6. `task.md` — 当前阶段正式任务入口与完成记录
7. `Plugins/AgentBridge/README.md` — 插件说明
8. `Plugins/AgentBridge/AGENTS.md` — 通用 Agent 规则
9. `Docs/History/Tasks/task8_phase8.md` — Phase 8 历史任务（需要追溯时）

## 绝对不要修改的文件

以下文件属于稳定核心，任何修改都可能破坏已验证的 MVP：

### C++ 核心
- `Plugins/AgentBridge/Source/AgentBridge/Private/*.cpp`
- `Plugins/AgentBridge/Source/AgentBridge/Public/*.h`

### Bridge 客户端
- `Plugins/AgentBridge/Scripts/bridge/bridge_core.py`
- `Plugins/AgentBridge/Scripts/bridge/query_tools.py`
- `Plugins/AgentBridge/Scripts/bridge/write_tools.py`
- `Plugins/AgentBridge/Scripts/bridge/remote_control_client.py`
- `Plugins/AgentBridge/Scripts/bridge/ui_tools.py`
- `Plugins/AgentBridge/Scripts/bridge/ue_helpers.py`
- `Plugins/AgentBridge/Scripts/bridge/project_config.py`
- `Plugins/AgentBridge/Scripts/bridge/uat_runner.py`

### Orchestrator 核心
- `Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py`
- `Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py`
- `Plugins/AgentBridge/Scripts/orchestrator/verifier.py`
- `Plugins/AgentBridge/Scripts/orchestrator/report_generator.py`
- `Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py`

### 测试体系
- `Plugins/AgentBridge/AgentBridgeTests/` 下所有文件

### 已稳定的 Schema
- `Plugins/AgentBridge/Schemas/common/`
- `Plugins/AgentBridge/Schemas/feedback/`
- `Plugins/AgentBridge/Schemas/write_feedback/`

## 可以修改的文件

### Legacy Compiler 框架（插件层）
- `Plugins/AgentBridge/Scripts/compiler/`
- `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py`
- `Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py`

### Schema（插件层）
- `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json`
- `Plugins/AgentBridge/Schemas/run_plan.schema.json`
- `Plugins/AgentBridge/Schemas/gdd_projection.schema.json`
- `Plugins/AgentBridge/Schemas/planner_output.schema.json`
- `Plugins/AgentBridge/Schemas/skill_fragment.schema.json`
- `Plugins/AgentBridge/Schemas/cross_review_report.schema.json`
- `Plugins/AgentBridge/Schemas/build_ir.schema.json`
- `Plugins/AgentBridge/Schemas/reviewed_handoff_v2.schema.json`

### Phase 8 新增骨架（插件层）
- `Plugins/AgentBridge/Compiler/`
- `Plugins/AgentBridge/SkillTemplates/`
- `Plugins/AgentBridge/MCP/`

### 项目层
- `ProjectInputs/`
- `ProjectState/`
- `Docs/`
- 根目录 `task.md`

## 项目外写入限制

- 默认允许增删改的范围仅限于项目根目录 `D:\UnrealProjects\Mvpv4TestCodex` 及其子目录。
- 项目目录外的路径默认只允许读取、检查、诊断，不允许直接新增、删除、修改。
- 如果任务确实需要改动项目目录外路径，必须先向用户说明目标路径、具体动作和原因，并在得到明确允许后再执行。

## 关键技术栈

- UE5.5.4 + C++ Editor Plugin（UEditorSubsystem）
- Python 3.x + pyyaml + jsonschema
- Remote Control API（HTTP REST，端口 30010）
- UE5 Automation Test Framework

## 常用命令

```bash
# Schema 校验（验证现有 MVP 不破坏）
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 系统测试：一键执行全部 9 个 Stage（当前登记 230 条）
python Plugins/AgentBridge/Tests/run_system_tests.py

# 系统测试：交互模式（选择 Stage）
python Plugins/AgentBridge/Tests/run_system_tests.py --interactive

# 系统测试：仅纯 Python Stage（不需要 Editor）
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# Greenfield 端到端运行（simulated 模式）
python Scripts/run_greenfield_demo.py

# Handoff Schema 校验
cd Plugins/AgentBridge/Scripts
python validation/test_handoff_schema.py

# Compiler 单独运行
cd Plugins/AgentBridge/Scripts
python compiler_main.py
```

## 代码风格

- Python：中文注释
- C++：中文注释
- YAML/JSON：中文 description
- 文档：中文

## 当前阶段

Phase 9 已完成 — MCP Server 正式化与文档切换
当前主入口：`task.md`
当前索引：`Docs/Current/00_Index.md`
Phase 9 验证证据：`ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md`
Phase 9 实施前方案归档：`Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md`
