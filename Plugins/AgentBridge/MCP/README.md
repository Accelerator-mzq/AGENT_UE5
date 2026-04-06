# AgentBridge MCP Server

Claude Code 通过 stdio 启动的 Model Context Protocol Server，用于把 UE5 Editor 能力暴露为可调用工具。

## 架构

```text
Claude Code (stdio)
  → AgentBridge MCP Server
    → Bridge 查询 / 写入工具
    → 本地 Service / Layer 2 工具
    → UE5 Editor
       ├── Channel A: Python Editor Scripting
       ├── Channel B: Remote Control API
       └── Channel C: C++ Plugin
```

## 当前状态

- 工具总数：28
- Layer 1 Query：7
- Layer 1 Write：6
- Layer 1 Service：5
- Layer 2 Asset：9
- Layer 3 Fallback：1
- 启动方式：stdio
- 当前入口：`python Plugins/AgentBridge/MCP/server.py`
- 当前默认主干：MCP server 内部优先走 `cpp_plugin` 通道，必要时再分发到 A/B/C 三通道

## 关键文件

- `server.py`：stdio MCP server、工具分发与本地工具实现
- `tool_definitions.py`：28 个工具定义与 `inputSchema` 转换
- `naming.py`：资产命名与默认路径规则
- `py_channel.py`：Channel A
- `rc_channel.py`：Channel B

## 统一响应格式

所有工具统一返回：

```json
{
  "status": "success|warning|failed|mismatch|validation_error",
  "summary": "操作结果摘要",
  "data": {},
  "warnings": [],
  "errors": []
}
```

## 本地验证要点

```powershell
python -m py_compile Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
python Plugins/AgentBridge/MCP/server.py
```

## 已完成验证

- Claude Code `/mcp` 已人工确认 `agentbridge connected`，工具数为 28
- 有 Editor 的 live smoke 已通过，真实返回 `Mvpv4TestCodex` / `/Game/Maps/L_MonopolyBoard`
- Stage 1 / 4 / 5 / 6 / 7 已串行通过，完成 `--no-editor` 等价覆盖
- 统一验证证据见 [phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)
