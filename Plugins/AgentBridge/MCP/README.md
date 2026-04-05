# AgentBridge MCP Server

Model Context Protocol Server，让 Claude Code 通过 MCP 协议调用 UE5 Editor。

## 架构

```
Claude Code (stdio) → MCP Server → Bridge 三通道 → UE5 Editor
                                  ├── Channel B: Remote Control API (HTTP:30010)
                                  ├── Channel A: Python Editor Scripting
                                  └── Channel C: C++ Plugin
```

## 工具分层

### Layer 1：Bridge 已有工具（15 个，复用 tool_contract_v0_1.md）
直接包装 `bridge/query_tools.py` 和 `bridge/write_tools.py`。

### Layer 2：新增 Channel A 资产创建工具（9 个）
通过 Python Editor Scripting 创建 UE5 资产。

### Layer 3：通用兜底（1 个）
`run_editor_python` — 执行任意 Python Editor Scripting 脚本。

## 启动方式

```bash
# Claude Code 通过 .mcp.json 自动启动
python Plugins/AgentBridge/MCP/server.py
```

## 统一响应格式

所有工具统一返回 tool_contract_v0_1.md 定义的格式：
```json
{
  "status": "success|warning|failed|mismatch|validation_error",
  "summary": "操作结果摘要",
  "data": {},
  "warnings": [],
  "errors": []
}
```
