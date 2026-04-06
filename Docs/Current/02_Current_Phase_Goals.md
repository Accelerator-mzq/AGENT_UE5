# 当前阶段目标

> 状态：Phase 9 已完成

## 1. 当前目标

1. 将 `Plugins/AgentBridge/MCP/` 从 Phase 8 占位骨架升级为真实可工作的 stdio MCP Server。
2. 让 `agentbridge` 注册全部 28 个工具，并支持 query / write / local 三类分发路径。
3. 保住 Phase 8 late validation 之后的 Python 回归基线，不因 MCP 切换破坏现有能力。
4. 完成项目入口、`Docs/Current/` 与插件说明文档的 Phase 9 口径切换。

## 2. 当前成功标准

- `tool_definitions.py` 与 Bridge 函数签名完全对齐：**已达成**
- `create_mcp_server()` 可返回真实 `Server("agentbridge")`：**已达成**
- `list_tools` 可返回 28 个 `types.Tool`：**已达成**
- stdio `initialize / tools/list / tools/call` 协议链路可用：**已达成**
- `validate_examples.py --strict` 通过：**已达成**
- Phase 8 Python 基线回归通过：**已达成**
说明：已通过串行 Stage 1 / 4 / 5 / 6 / 7 补齐 `--no-editor` 等价覆盖，证据见 [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)。
- Claude Code `/mcp` 显示 `agentbridge connected`：**已达成**
- 有 Editor 的真实工具调用 live smoke 通过：**已达成**
说明：`get_current_project_state` 与 `list_level_actors` 已返回真实工程 `Mvpv4TestCodex` 和真实关卡 `/Game/Maps/L_MonopolyBoard`，证据见 [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)。

## 3. 当前约束

- Phase 9 不扩展联网多人。
- Phase 9 不新增第三个 genre pack。
- Phase 9 不改 Bridge / Orchestrator / 稳定 Schema / 插件核心 C++。
- Phase 9 必须显式吸收 Phase 8 late validation 的防回归要求。
