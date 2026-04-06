# 实施边界

> 阶段：Phase 9 — MCP Server 正式化与文档切换

## 允许改动

- `Plugins/AgentBridge/MCP/tool_definitions.py`
- `Plugins/AgentBridge/MCP/server.py`
- 根目录 `AGENTS.md`、`README.md`、`CLAUDE.md`、`task.md`
- `Docs/Current/*` 的 Phase 9 口径维护
- `Plugins/AgentBridge/README.md`
- `Plugins/AgentBridge/AGENTS.md`
- `Plugins/AgentBridge/MCP/README.md`
- `Plugins/AgentBridge/Docs/architecture_overview.md`
- `ProjectState/Reports/` 下新增本轮验证证据

## 不允许改动

- `Plugins/AgentBridge/Source/` 下已稳定的插件 C++ 核心
- `Plugins/AgentBridge/Scripts/bridge/` 下已稳定的 Bridge 客户端
- `Plugins/AgentBridge/Scripts/orchestrator/` 下已稳定的 Orchestrator 核心
- `Plugins/AgentBridge/AgentBridgeTests/` 下所有测试文件
- `Plugins/AgentBridge/Schemas/common/`、`feedback/`、`write_feedback/` 下已稳定的 Schema
- `Docs/History/` 中已归档历史事实正文

## Phase 9 固定口径

- Phase 8 late validation 未切换 MCP，是已确认的历史前提，不得在 Phase 9 文档中改写。
- Phase 9 默认先保基线，再切 MCP，再做 live smoke。
- Claude `/mcp` 与有 Editor 的调用冒烟未验证前，不得宣称 Phase 9 全部完成。
