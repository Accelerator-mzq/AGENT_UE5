# TASK 05 Evidence — MCP 前端工具重命名、alias 与 Clarification 工具

日期：2026-04-15

## 任务范围

- 更新 [compiler_tools.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/compiler_tools.py)，新增 Phase 11 前端工具函数并保留旧名 alias。
- 更新 [tool_definitions.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/tool_definitions.py)，让新工具在 MCP `list_tools` 中可见。
- 更新 [server.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/MCP/server.py)，将新工具接入 dispatch。
- 更新 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 与 [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)，同步 Phase 11 flat alias layout 的工具数量与清单口径。
- 更新 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 的 TASK 05 与 M4 状态。

## 实现摘要

- `compiler_create_session` 支持可选 `session_version`、`run_id`、`fast_mode`。
- 新增 Phase 11 工具：
  - `compiler_root_skill_prepare`
  - `compiler_root_skill_save`
  - `compiler_clarification_prepare`
  - `compiler_clarification_save`
  - `compiler_skill_graph_prepare`
  - `compiler_skill_graph_save`
- 保留旧名 alias：
  - `compiler_intake_prepare/save`：v1 为 GDD Projection，v2 等价 Root Skill。
  - `compiler_plan_prepare/save`：v1 为 Planner，v2 等价 Skill Graph。
- MCP `ALL_TOOLS` 当前为 48 个。原因：当前实现是 flat visible alias layout，旧名 alias 也作为可见工具保留；文档中的 47 是“重命名不额外计数 + 后续 evidence 新增 3 个”的逻辑口径。

## 验证结果

工具注册与可见性：

```text
TASK05_TOOL_REGISTRATION=passed
TASK05_TOOL_VISIBILITY=passed
TASK05_TOOL_COUNT=48
TASK05_COMPILER_FRONTEND_COUNT=12
```

工具调用验证：

```text
TASK05_COMPILER_TOOL_CALLS=passed
```

覆盖项：

- v1 session 可创建。
- v1 `compiler_intake_prepare/save` 可调用。
- v1 `compiler_plan_prepare` 可调用并返回 `planner`。
- v2 session 可创建，并保留指定 `run_id`。
- v2 `compiler_root_skill_prepare/save` 可调用并保存 `root_skill_contract.json`。
- v2 `compiler_intake_prepare/save` alias 等价 Root Skill。
- v2 `compiler_clarification_prepare/save` 可调用并保存 `clarification_gate_report.json`。
- v2 `compiler_skill_graph_prepare/save` 可调用并保存 `skill_graph.json`。
- v2 `compiler_plan_prepare/save` alias 等价 Skill Graph。
- `server.dispatch_tool("compiler_get_session_status", ...)` 可读取 v2 session 状态。

语法验证：

```text
python -m py_compile Plugins/AgentBridge/MCP/compiler_tools.py Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py Plugins/AgentBridge/Tests/run_system_tests.py
```

严格示例验证：

```text
Checked examples       : 19
Passed                 : 19
Failed                 : 0
Reference-only skipped : 0
Unmapped examples      : 0
Missing schema targets : 0

[SUCCESS] 全部 example 校验通过，本地校验链正常。
```

执行命令：

```powershell
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

## 结论

TASK 05 验收标准已满足。M4 已完成：MCP 前端新工具可见、可调用，旧工具名仍保留为 alias，Clarification prepare/save 已接入。
