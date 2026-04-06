# Phase 9 — AgentBridge MCP Server 正式化与文档切换

> 归档状态：历史任务副本
> 归档日期：2026-04-06
> 当前收尾文档：[11_Phase9_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/11_Phase9_Closeout.md)
> 当前正式入口仍为：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)

> 状态：已完成
> 启动日期：2026-04-06
> 阶段目标：使 `.mcp.json` 中配置的 `agentbridge` MCP Server 真正可用，并完成 Phase 9 文档切换
> 上一阶段任务：[task8_phase8.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task8_phase8.md)
> 方案文档归档：[Phase9_MCP_Implementation_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md)

---

## 1. Phase 8 后期验证遗留处理原则

1. Phase 8 收尾期不立刻切换 MCP 方案，是为了避免在 late validation 阶段引入新的外部接入链路，影响运行时验收稳定性。
2. Phase 9 才承担 MCP 切换与补验证责任，同时必须保住 Phase 8 已确认的运行时与回归基线。
3. Phase 9 验证顺序固定为：
   - 先保住 Phase 8 Python 基线回归
   - 再验证 MCP 协议级 `initialize / tools/list / tools/call`
   - 再验证 Claude Code `/mcp` 集成
   - 最后在有 Editor 时做真实工具调用冒烟
4. 任何“Phase 9 已成功”的结论，都必须同时附带代码实现证据与验证证据。

## 2. 核心约束

- **不修改** `Plugins/AgentBridge/Scripts/bridge/*.py`
- **不修改** `Plugins/AgentBridge/Scripts/orchestrator/*.py`
- **不修改** `Plugins/AgentBridge/Source/`
- **不修改** `Plugins/AgentBridge/AgentBridgeTests/`
- **不修改** 稳定 Schema：`Plugins/AgentBridge/Schemas/common/`、`feedback/`、`write_feedback/`
- 代码主改动仅落在：
  - `Plugins/AgentBridge/MCP/tool_definitions.py`
  - `Plugins/AgentBridge/MCP/server.py`
- 文档切换允许修改：
  - 根目录 `task.md`、`README.md`
  - `Docs/Current/*`
  - `Plugins/AgentBridge/README.md`
  - `Plugins/AgentBridge/MCP/README.md`
  - `Plugins/AgentBridge/Docs/architecture_overview.md`
- 所有新增或修改代码必须带中文注释
- MCP SDK 固定为 `mcp==1.26.0`

## 3. 任务总览

1. TASK 01：修正 `tool_definitions.py` 参数名并新增 `to_json_schema()`
2. TASK 02：在 `server.py` 中补全 5 个 service 工具和 6 个 Layer 2 工具
3. TASK 03：实现 MCP Server 核心，包括 `TOOL_DISPATCH`、`dispatch_tool()`、`create_mcp_server()` 和 stdio 入口
4. TASK 04：完成本地静态验证、协议级验证、无 Editor 分发验证与 Phase 8 基线回归验证
5. TASK 05：切换根目录任务入口、`Docs/Current`、README 与插件说明文档到 Phase 9 口径

## 4. 当前进展

- TASK 01：已完成
- TASK 02：已完成
- TASK 03：已完成
- TASK 04：已完成
  - 已完成：参数对齐、Schema 转换、`create_mcp_server()` 构造、28 工具注册、stdio `initialize / tools/list / tools/call`
  - 已完成：`validate_examples.py --strict`
  - 已完成：系统测试 Stage 1 / 4 / 5 / 6 / 7 串行验证，覆盖 `--no-editor` 等价范围
  - 已完成：Claude Code `/mcp` 人工确认 `agentbridge connected`，28 tools
  - 已完成：有 Editor 的 live smoke，`get_current_project_state` 与 `list_level_actors` 均返回真实工程 `Mvpv4TestCodex` / `/Game/Maps/L_MonopolyBoard`
- TASK 05：已完成

## 5. 实施要点

### 5.1 tool_definitions.py

- 对齐以下 6 个条目与 Bridge 签名：
  - `list_level_actors`
  - `run_map_check`
  - `import_assets`
  - `create_blueprint_child`
  - `set_actor_collision`
  - `assign_material`
- 新增：
  - `to_json_schema(tool_def: dict) -> dict`

### 5.2 server.py

- 保留并复用：
  - `make_response()`
  - `wrap_bridge_query()`
  - `wrap_bridge_write()`
  - 已存在的 `create_level()` / `create_material()` / `create_widget_blueprint()` / `run_editor_python()`
- 新增实现：
  - Service：`capture_screenshot` / `save_named_assets` / `build_project` / `run_automation_tests` / `undo_last_transaction`
  - Layer 2：`create_material_instance` / `set_blueprint_defaults` / `configure_gamemode_bp` / `configure_world_settings` / `open_level` / `save_all`
- 新增：
  - `TOOL_DISPATCH`
  - `dispatch_tool()`
  - `create_mcp_server()`
  - `main()`
- `call_tool` 必须通过 `run_in_executor` 调用同步工具，避免阻塞事件循环

### 5.3 文档切换

- Phase 9 当前事实入口统一为：
  - [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
  - [00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
  - [README.md](/D:/UnrealProjects/Mvpv4TestCodex/README.md)
- Phase 9 实施前方案已归档到 [Phase9_MCP_Implementation_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase9_MCP_Implementation_Plan.md)，根目录不再保留并列方案文档
- [08_Phase8_Retrospective_And_Phase9_Checklist.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Phase8_Retrospective_And_Phase9_Checklist.md) 中所有仍指向根目录旧 `task.md` 的历史链接，统一改为 [task8_phase8.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task8_phase8.md)

## 6. 验证命令

### 6.1 参数与静态验证

```powershell
python -m py_compile Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py
```

```powershell
@'
import sys, inspect
sys.path.insert(0, 'Plugins/AgentBridge/Scripts/bridge')
sys.path.insert(0, 'Plugins/AgentBridge/MCP')
import query_tools, write_tools
from tool_definitions import LAYER1_QUERY_TOOLS, LAYER1_WRITE_TOOLS

for name, defn in LAYER1_QUERY_TOOLS.items():
    func = getattr(query_tools, name, None)
    if func is None:
        continue
    print(name, list(inspect.signature(func).parameters.keys()), list(defn.get('params', {}).keys()))

for name, defn in LAYER1_WRITE_TOOLS.items():
    func = getattr(write_tools, name, None)
    if func is None:
        continue
    print(name, list(inspect.signature(func).parameters.keys()), list(defn.get('params', {}).keys()))
'@ | python -
```

### 6.2 协议级 MCP 验证（PowerShell 兼容）

```powershell
@'
import asyncio
import os
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

PROJECT_ROOT = r'd:\UnrealProjects\Mvpv4TestCodex'

async def main():
    server_params = StdioServerParameters(
        command='python',
        args=['Plugins/AgentBridge/MCP/server.py'],
        cwd=PROJECT_ROOT,
        env={**os.environ, 'PYTHONPATH': 'Plugins/AgentBridge/Scripts/bridge'},
    )
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            init_result = await session.initialize()
            print('server=', init_result.serverInfo.name)
            tools_result = await session.list_tools()
            print('tool_count=', len(tools_result.tools))
            call_result = await session.call_tool('get_current_project_state', {})
            print('project_state_is_error=', call_result.isError)

asyncio.run(main())
'@ | python -
```

### 6.3 Phase 8 基线回归

```powershell
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

```powershell
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor
```

说明：
- 若全量 `--no-editor` 耗时过长，可拆分 `--stage=5`、`--stage=6`、`--stage=7` 先验证 Python 基线
- `--stage=4` 为 Commandlet 长时验证，单独记录结论

## 7. 当前验收口径

- `tool_definitions.py` 与 Bridge 签名保持 1:1 一致
- `server.py` 可以构造真实 `Server("agentbridge")`
- `list_tools` 返回 28 个工具
- `tools/call` 可返回结构化 `CallToolResult`
- 无 Editor 时，依赖 UE Editor 的本地工具返回 `failed`，不崩溃
- Phase 8 Python 基线回归不被 MCP 改造破坏
- Claude Code `/mcp` 已人工确认 `agentbridge connected`
- 有 Editor 的 live smoke 已通过，真实返回 `Mvpv4TestCodex` 与 `/Game/Maps/L_MonopolyBoard`
- `--no-editor` 等价范围已通过串行 Stage 1 / 4 / 5 / 6 / 7 留证补齐
