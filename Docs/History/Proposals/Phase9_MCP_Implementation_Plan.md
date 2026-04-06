# AgentBridge MCP Server 框架层补全方案（已实施归档）

> 归档状态：实施前方案归档
> 归档日期：2026-04-06
> 当前正式任务：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
> 当前验证证据：[phase9_mcp_validation_2026-04-06.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-06/phase9_mcp_validation_2026-04-06.md)

## Context

AgentBridge MCP Server 在 Phase 8 M2 阶段创建了骨架（28 个工具定义 + Channel 架构），但 `create_mcp_server()` 函数体只有 `pass`，`__main__` 只打印工具列表就退出。Claude Code 通过 `.mcp.json` 启动时进程立刻结束，MCP 连接失败。需要完成 SDK 集成使 28 个工具真正可用。

MCP SDK v1.26.0 已安装（`C:\Users\mzq\AppData\Roaming\Python\Python312\site-packages`）。Bridge 层（query_tools/write_tools/ui_tools）为稳定核心 **不可修改**。

---

## 一、现状诊断

### 1.1 可用基础设施

| 组件 | 路径 | 状态 |
|------|------|------|
| `.mcp.json` | 项目根目录 | ✅ 配置正确，command/args/cwd/env 齐全 |
| `tool_definitions.py` | `Plugins/AgentBridge/MCP/` | ✅ 28 个工具定义完整（但参数名有偏差，见 §2.1） |
| `naming.py` | `Plugins/AgentBridge/MCP/` | ✅ 资产命名校验可用 |
| `py_channel.py` | `Plugins/AgentBridge/MCP/` | ✅ Channel A（Python Editor Scripting）可用 |
| `rc_channel.py` | `Plugins/AgentBridge/MCP/` | ✅ Channel B（Remote Control API）可用 |
| `server.py` | `Plugins/AgentBridge/MCP/` | ❌ 骨架，`create_mcp_server()` = `pass` |
| Bridge query_tools | `Scripts/bridge/query_tools.py` | ✅ 9 个查询函数（**不可改**） |
| Bridge write_tools | `Scripts/bridge/write_tools.py` | ✅ 6 个写入函数（**不可改**） |
| Bridge ui_tools | `Scripts/bridge/ui_tools.py` | ✅ 7 个 UI 自动化函数（**不可改**） |
| MCP SDK | pip `mcp==1.26.0` | ✅ 已安装 |

### 1.2 缺失项

| 缺失 | 说明 |
|------|------|
| MCP Server 启动循环 | `server.py` 无 `Server` 实例、无 `stdio_server()` 启动 |
| 工具注册 | `@server.list_tools()` / `@server.call_tool()` 未实现 |
| 工具分发路由 | tool_name → Python 函数的映射表不存在 |
| JSON Schema 转换 | `tool_definitions.py` 的 `params` dict 未转为 MCP `inputSchema` |
| 5 个 Service 工具实现 | `capture_screenshot` / `save_named_assets` / `build_project` / `run_automation_tests` / `undo_last_transaction` 在 Bridge 层无实现 |
| 6 个 Layer 2 工具实现 | `create_material_instance` / `set_blueprint_defaults` / `configure_gamemode_bp` / `configure_world_settings` / `open_level` / `save_all` 无实现 |
| 参数名对齐 | `tool_definitions.py` 部分参数名与 Bridge 函数签名不一致 |

---

## 二、实施步骤（共 6 步）

### Step 1：修复 tool_definitions.py 参数名偏差

**目标**：让 `tool_definitions.py` 的 `params` key 与 Bridge 函数签名完全一致，因为 MCP `arguments` dict 的 key 会直接作为 `**kwargs` 传给 Bridge 函数。

**需要修改的条目**：

| 工具 | 当前参数名 | 应改为（匹配函数签名） |
|------|-----------|----------------------|
| `list_level_actors` | 缺 `level_path` | 加 `level_path: {type: string, required: false}` |
| `import_assets` | `source_path`, `destination_path` | `source_dir`, `dest_path`，加 `replace_existing`(bool) + `dry_run`(bool) |
| `create_blueprint_child` | `blueprint_name`, `destination_path` | 删 `blueprint_name`，改 `destination_path` → `package_path`，加 `dry_run`(bool) |
| `set_actor_collision` | `collision_preset` | 改为 `profile_name`，加 `collision_enabled`(string) + `can_affect_navigation`(bool) + `dry_run`(bool) |
| `assign_material` | 缺 `dry_run` | 加 `dry_run: {type: boolean, required: false}` |
| `run_map_check` | 缺 `level_path` | 加 `level_path: {type: string, required: false}` |

**同文件新增**：`to_json_schema(tool_def)` 函数，将内部 `params` dict 转为 MCP `inputSchema`（JSON Schema draft-07 格式）。

```python
def to_json_schema(tool_def: dict) -> dict:
    properties = {}
    required = []
    for name, spec in tool_def.get("params", {}).items():
        prop = {"description": spec.get("description", "")}
        ptype = spec.get("type", "string")
        type_map = {"string": "string", "integer": "integer", "boolean": "boolean",
                     "array": "array", "object": "object"}
        if ptype in type_map:
            prop["type"] = type_map[ptype]
        properties[name] = prop
        if spec.get("required", False):
            required.append(name)
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema
```

**涉及文件**：`Plugins/AgentBridge/MCP/tool_definitions.py`

---

### Step 2：实现 5 个 Service 工具

**目标**：这 5 个工具在 `tool_definitions.py` 有定义但 Bridge 层无实现，需在 `server.py` 中补充。

**位置**：在 `server.py` 现有 Layer 2 代码块之后新增 Service 代码块。

| 工具 | 实现方式 |
|------|----------|
| `capture_screenshot` | `py_channel.execute_editor_python` 调用 `unreal.AutomationLibrary.take_high_res_screenshot` |
| `save_named_assets` | `py_channel.execute_editor_python` 调用 `unreal.EditorAssetLibrary.save_asset` 循环 |
| `build_project` | `py_channel.execute_editor_python` 触发 `unreal.EditorLevelLibrary` 编译命令 |
| `run_automation_tests` | `py_channel.execute_editor_python` 调用 `unreal.AutomationLibrary` |
| `undo_last_transaction` | `py_channel.execute_editor_python` 执行撤销命令 |

每个函数签名必须与 `tool_definitions.py` 中修正后的参数名一致，返回 `make_response()` 格式。

**涉及文件**：`Plugins/AgentBridge/MCP/server.py`

---

### Step 3：实现 6 个缺失的 Layer 2 工具

**目标**：补全 `tool_definitions.py` 中定义但 `server.py` 未实现的 6 个 Layer 2 资产工具。

| 工具 | 实现方式 | Channel |
|------|----------|---------|
| `create_material_instance` | `py_channel` → `unreal.AssetToolsHelpers` + `MaterialInstanceConstantFactoryNew` | A |
| `set_blueprint_defaults` | `py_channel` → `unreal.EditorAssetLibrary.load_asset` + CDO 设置 | A |
| `configure_gamemode_bp` | 内部调 `set_blueprint_defaults` 多次 | A |
| `configure_world_settings` | `rc_channel.set_property` 设置 WorldSettings Actor | B |
| `open_level` | `py_channel` → `unreal.EditorLevelLibrary.load_level` | A |
| `save_all` | `py_channel` → `unreal.EditorLoadingAndSavingUtils.save_dirty_packages` | A |

**涉及文件**：`Plugins/AgentBridge/MCP/server.py`

---

### Step 4：实现 MCP Server 核心（最关键）

**目标**：在 `server.py` 中实现 `create_mcp_server()` + 工具分发 + `__main__` 启动。

#### 4.1 工具分发路由表

```python
TOOL_DISPATCH = {}

# Layer 1 Query → wrap_bridge_query
for name in LAYER1_QUERY_TOOLS:
    TOOL_DISPATCH[name] = ("query", name)

# Layer 1 Write → wrap_bridge_write
for name in LAYER1_WRITE_TOOLS:
    TOOL_DISPATCH[name] = ("write", name)

# Layer 1 Service → 本地函数（Step 2 实现）
TOOL_DISPATCH["capture_screenshot"] = ("local", capture_screenshot)
TOOL_DISPATCH["save_named_assets"] = ("local", save_named_assets)
TOOL_DISPATCH["build_project"] = ("local", build_project)
TOOL_DISPATCH["run_automation_tests"] = ("local", run_automation_tests)
TOOL_DISPATCH["undo_last_transaction"] = ("local", undo_last_transaction)

# Layer 2 Asset → 本地函数（已有 3 个 + Step 3 补 6 个）
TOOL_DISPATCH["create_level"] = ("local", create_level)
TOOL_DISPATCH["create_material"] = ("local", create_material)
TOOL_DISPATCH["create_material_instance"] = ("local", create_material_instance)
TOOL_DISPATCH["create_widget_blueprint"] = ("local", create_widget_blueprint)
TOOL_DISPATCH["set_blueprint_defaults"] = ("local", set_blueprint_defaults)
TOOL_DISPATCH["configure_gamemode_bp"] = ("local", configure_gamemode_bp)
TOOL_DISPATCH["configure_world_settings"] = ("local", configure_world_settings)
TOOL_DISPATCH["open_level"] = ("local", open_level)
TOOL_DISPATCH["save_all"] = ("local", save_all)

# Layer 3 Fallback
TOOL_DISPATCH["run_editor_python"] = ("local", run_editor_python)
```

#### 4.2 分发函数

```python
def dispatch_tool(tool_name: str, arguments: dict) -> dict:
    route = TOOL_DISPATCH.get(tool_name)
    if route is None:
        return make_response("failed", f"未知工具: {tool_name}",
                             errors=[f"TOOL_NOT_FOUND: {tool_name}"])
    kind, target = route
    try:
        if kind == "query":
            return wrap_bridge_query(target, **arguments)
        elif kind == "write":
            return wrap_bridge_write(target, **arguments)
        elif kind == "local":
            return target(**arguments)
    except Exception as e:
        return make_response("failed", f"工具执行失败: {tool_name}",
                             errors=[f"TOOL_EXECUTION_FAILED: {str(e)}"])
```

#### 4.3 MCP Server 实例

```python
def create_mcp_server():
    from mcp.server.lowlevel import Server
    from mcp import types
    from tool_definitions import ALL_TOOLS, to_json_schema

    server = Server("agentbridge")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(name=name, description=defn["description"],
                       inputSchema=to_json_schema(defn))
            for name, defn in ALL_TOOLS.items()
        ]

    @server.call_tool()
    async def handle_call_tool(tool_name: str, arguments: dict):
        import asyncio
        # Bridge 函数是同步的，用线程池避免阻塞事件循环
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, dispatch_tool, tool_name, arguments)
        text = json.dumps(result, ensure_ascii=False, indent=2)
        is_error = result.get("status") == "failed"
        return types.CallToolResult(
            content=[types.TextContent(type="text", text=text)],
            isError=is_error,
        )

    return server
```

#### 4.4 入口点（替换现有 `if __name__`）

```python
async def main():
    from mcp.server.stdio import stdio_server
    server = create_mcp_server()
    init_options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

**涉及文件**：`Plugins/AgentBridge/MCP/server.py`

---

### Step 5：异步/同步兼容处理

**风险**：Bridge 函数（query_tools/write_tools）是同步的，包含 HTTP 请求到 UE5 Editor（localhost:30010）。MCP handler 是 async 的。如果直接在 async handler 中调用同步 HTTP，会阻塞事件循环。

**方案**：Step 4.3 中已使用 `loop.run_in_executor(None, dispatch_tool, ...)` 在线程池中执行同步调用。

---

### Step 6：验证

#### 6.1 冒烟测试（不需要 UE5 Editor）

```bash
# 验证 server 能创建、工具能注册
cd D:/UnrealProjects/Mvpv4TestCodex
python -c "
import sys; sys.path.insert(0, 'Plugins/AgentBridge/Scripts/bridge')
sys.path.insert(0, 'Plugins/AgentBridge/MCP')
from server import create_mcp_server
server = create_mcp_server()
print('✅ Server 创建成功')
"
```

#### 6.2 MCP 协议测试

```bash
# 发送 JSON-RPC initialize + tools/list 请求
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | python Plugins/AgentBridge/MCP/server.py
```

预期：收到 JSON-RPC 响应，`result.capabilities.tools` 非空。

#### 6.3 Claude Code 集成测试

1. 重启 Claude Code（让它重新读取 `.mcp.json`）
2. 在对话中输入 `/mcp`，确认 `agentbridge` 出现在 MCP server 列表中
3. 尝试调用：请 Claude Code 使用 `get_current_project_state` 工具（需要 UE5 Editor 运行中）

#### 6.4 Mock 模式测试（可选）

Bridge 层有 Mock 通道，可在不启动 UE5 的情况下测试分发链路：
```python
# 在 bridge_core.py 中 ACTIVE_CHANNEL = BridgeChannel.MOCK
```
但由于 bridge_core.py 不可修改，可通过环境变量或运行时 patch 切换（仅测试时）。

---

## 三、文件修改清单

| 文件 | 操作 | Step |
|------|------|------|
| `Plugins/AgentBridge/MCP/tool_definitions.py` | 修改：修正 6 处参数名 + 新增 `to_json_schema()` | 1 |
| `Plugins/AgentBridge/MCP/server.py` | 重写：补 11 个工具实现 + TOOL_DISPATCH + create_mcp_server + main | 2-4 |

**不可修改的文件（约束重申）**：
- `Plugins/AgentBridge/Scripts/bridge/*.py`（全部）
- `Plugins/AgentBridge/Scripts/orchestrator/*.py`（全部）
- `Plugins/AgentBridge/AgentBridgeTests/`（全部）
- `Plugins/AgentBridge/Schemas/common/` + `feedback/` + `write_feedback/`

---

## 四、依赖与前置条件

| 依赖 | 状态 | 说明 |
|------|------|------|
| Python 3.12 | ✅ | 已安装 |
| `mcp==1.26.0` | ✅ | 已安装 |
| `pyyaml` | ✅ | Bridge 层依赖 |
| `jsonschema` | ✅ | Bridge 层依赖 |
| UE5 Editor 运行 | 可选 | 仅实际调用工具时需要（端口 30010） |

---

## 五、风险与缓解

| 风险 | 缓解 |
|------|------|
| Bridge 函数同步阻塞事件循环 | `run_in_executor` 线程池隔离 |
| 参数名不一致导致运行时 TypeError | Step 1 严格对齐 + Step 6 逐工具测试 |
| Service 工具（capture_screenshot 等）的 UE Python API 不稳定 | 用 try/except 包装，返回 `make_response("failed", ...)` |
| `configure_world_settings` 用 Channel B 而其他 Layer 2 用 Channel A | 在函数内部显式 import `rc_channel` 而非 `py_channel` |
| MCP SDK API 变化（1.26.0 → 未来版本） | 锁定版本，用 `from mcp.server.lowlevel import Server` 稳定入口 |
