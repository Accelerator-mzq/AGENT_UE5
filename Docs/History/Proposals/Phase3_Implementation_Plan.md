# Phase 3 实施方案：Greenfield + Boardgame + Reviewed Handoff 最小闭环

> 状态：approved
> 日期：2026-03-30

## 1. 实施目标

在现有 AgentBridge 执行链不失稳的前提下，打通：

```
GDD → Compiler → Handoff(draft) → 审批 → Orchestrator → Bridge 执行 → Report
```

## 2. 分层原则

- 项目层 = 输入与实例层（ProjectInputs / ProjectState / Docs）
- 插件层 = 通用编译与执行框架层（Scripts/compiler / Scripts/orchestrator / Schemas / Skills / Specs）

Compiler 主体、Handoff 机制、Orchestrator 桥接全部在**插件层**实现。
项目层只提供 GDD 文件、Preset 配置、保存 Handoff 实例和 Report。

## 3. 交付件来源

所有第一阶段交付件已预生成在本工程外部的 `input/` 目录中。
本方案的 TASK 就是将这些交付件部署到正式位置并验证。

交付件路径：`D:\ClaudeProject\fenxi-claude\input\`

## 4. 部署目标映射

### 4.1 项目层（本工程根目录）

| 来源（input/） | 目标位置 |
|---------------|---------|
| `ProjectInputs/GDD/boardgame_tictactoe_v1.md` | `ProjectInputs/GDD/boardgame_tictactoe_v1.md` |
| `ProjectInputs/Presets/mode_override.yaml` | `ProjectInputs/Presets/mode_override.yaml` |
| `ProjectInputs/Presets/compiler_profile.yaml` | `ProjectInputs/Presets/compiler_profile.yaml` |
| `ProjectState/` 目录结构 | `ProjectState/Handoffs/draft/` + `approved/` + `Reports/` + `Snapshots/` |

### 4.2 插件层（Plugins/AgentBridge/）

| 来源（input/） | 目标位置 |
|---------------|---------|
| `Schemas/reviewed_handoff.schema.json` | `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json` |
| `Schemas/run_plan.schema.json` | `Plugins/AgentBridge/Schemas/run_plan.schema.json` |
| `Schemas/examples/reviewed_handoff_greenfield.example.json` | `Plugins/AgentBridge/Schemas/examples/reviewed_handoff_greenfield.example.json` |
| `Schemas/examples/run_plan_greenfield.example.json` | `Plugins/AgentBridge/Schemas/examples/run_plan_greenfield.example.json` |
| `Scripts/compiler/` 整个目录 | `Plugins/AgentBridge/Scripts/compiler/` |
| `Scripts/compiler_main.py` | `Plugins/AgentBridge/Scripts/compiler_main.py` |
| `Scripts/orchestrator/handoff_runner.py` | `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` |
| `Scripts/orchestrator/run_plan_builder.py` | `Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py` |
| `Scripts/validation/test_handoff_schema.py` | `Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py` |
| `Skills/` 整个目录 | `Plugins/AgentBridge/Skills/` |
| `Specs/` 整个目录 | `Plugins/AgentBridge/Specs/` |

### 4.3 端到端入口

| 来源（input/） | 目标位置 |
|---------------|---------|
| `run_greenfield_demo.py` | 项目根目录 `run_greenfield_demo.py` |

## 5. 禁止事项

- 不修改 `Source/AgentBridge/` 中的任何 C++ 文件
- 不修改 `Scripts/bridge/` 中的任何现有文件
- 不修改 `Scripts/orchestrator/orchestrator.py`（保留现有入口）
- 不修改 `Scripts/orchestrator/plan_generator.py`
- 不修改 `AgentBridgeTests/` 中的任何测试文件
- 不修改 `Schemas/common/`、`Schemas/feedback/`、`Schemas/write_feedback/` 中的现有 Schema
- 不删除任何现有文件

## 6. 验收标准

### A. 不破坏现有 MVP
- 现有 C++ 代码可编译（零 error）
- 现有 Automation Test 全部通过
- 现有 `python validate_examples.py --strict` 全部通过
- 现有 Bridge 接口可通过 curl 调用

### B. Handoff 最小闭环成立
- `python run_greenfield_demo.py` 端到端跑通（simulated 模式）
- Handoff 实例通过 `python test_handoff_schema.py` 校验
- Report 输出到 ProjectState/Reports/

### C. 项目层/插件层边界成立
- 项目层无 compiler 主体代码
- 插件层无项目私有 GDD / Handoff 实例
