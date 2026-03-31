# CLAUDE.md — Mvpv4TestCodex 项目

> 本文件供 Claude Code / Codex / 其他 AI Agent 在进入本项目时自动读取。
> 最后更新：2026-03-31

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
3. `Docs/Current/05_Implementation_Boundary.md` — 实施边界
4. `Docs/History/Tasks/task2_phase4.md` — Phase 4 任务清单（已归档）
5. `Plugins/AgentBridge/README.md` — 插件说明
6. `Plugins/AgentBridge/AGENTS.md` — 通用 Agent 规则

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

### 新增的 Compiler 框架（插件层）
- `Plugins/AgentBridge/Scripts/compiler/` — Skill Compiler Plane 主体
- `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` — Handoff 执行入口
- `Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py` — Run Plan 生成器

### 新增的 Schema（插件层）
- `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json`
- `Plugins/AgentBridge/Schemas/run_plan.schema.json`

### 占位目录（插件层）
- `Plugins/AgentBridge/Skills/` — Skill 体系
- `Plugins/AgentBridge/Specs/StaticBase/` — 静态基座
- `Plugins/AgentBridge/Specs/Contracts/` — Patch / Migration Contract

### 项目层
- `ProjectInputs/` — 项目输入源（GDD / Presets / Baselines）
- `ProjectState/` — 项目运行实例（Handoffs / Reports / Snapshots）
- `Docs/` — 项目治理文档

## 关键技术栈

- UE5.5.4 + C++ Editor Plugin（UEditorSubsystem）
- Python 3.x + pyyaml + jsonschema
- Remote Control API（HTTP REST，端口 30010）
- UE5 Automation Test Framework

## 常用命令

```bash
# Schema 校验（验证现有 MVP 不破坏）
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 系统测试：一键执行全部 9 个 Stage（134 条用例）
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

Phase 5 — Brownfield Baseline Understanding + Contracts（进行中）
上一阶段：Phase 4 — Static Spec Base + 自动 Dynamic Spec 生成（已归档）
详见 `Docs/Current/00_Index.md` 与 `Docs/History/Tasks/task2_phase4.md`
