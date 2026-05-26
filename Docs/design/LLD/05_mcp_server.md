# LLD/05 — MCP Server 子系统详细设计

> 版本: v1 (2026-05-26)
> 范围: `Plugins/AgentBridge/MCP/` 下 7 个 Python 模块,共 3198 行
> 上游: `Docs/design/HLD.md` §4 + `Docs/requirements/SRS.md` §3.5 + `Docs/FEATURE_INVENTORY.md` F-MCP-01..13
> 契约: `Docs/contracts/mcp_tools_catalog.md`(53 工具 catalog,字段级签名)+ `Docs/contracts/tool_contract.md` §2-§4(统一返回格式 / 错误码 / Bridge 三通道协议)
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

MCP Server 子系统是 AgentBridge 暴露给 Claude Code / 任意 MCP 兼容 Agent 的协议层,职责是把 Bridge / Compiler / Evidence 三块底层能力统一封装成 53 个 MCP 工具,通过 stdio 协议对外提供。代码层为 7 个 Python 模块、合计 3198 行:`server.py`(911 行)是 stdio 主入口 + 三通道初始化 + 工具 dispatch 路由表;`tool_definitions.py`(567 行)是 53 工具字典定义 + JSON Schema 转换;`compiler_tools.py`(433 行)是前端 Compiler Stage prepare/save 工具(14 工具,F-MCP-06/07/08/09);`evidence_tools.py`(1126 行)是后端 Evidence 读写 + Run 治理(11 工具,F-MCP-10/11);`py_channel.py`(65 行)/`rc_channel.py`(38 行)是 Python Editor Scripting 与 Remote Control HTTP 两条 transport 通道适配;`naming.py`(58 行)是资产命名 / 路径前缀规范 + alias 解析(F-MCP-12 alias 实质由 `tool_definitions.COMPILER_FRONTEND_TOOLS` 的 4 个旧名工具承载)。整体上 MCP Server 自身**不实现业务逻辑**,只做四件事:(1) 注册工具元数据(catalog)、(2) 校验入参 JSON Schema、(3) 路由到底层 query_tools / write_tools / compiler / evidence、(4) 统一返回 `{status, summary, data, warnings, errors}`。53 工具完整字段级签名见 `Docs/contracts/mcp_tools_catalog.md`,**本 LLD 不复述**。

## 2. 内部分层

| 模块 | 角色一句话 | F-MCP ID | 文件:行数 |
|---|---|---|---|
| MCP stdio 主入口 | 启动 stdio Server、初始化通道、注册 53 工具、dispatch 路由 | F-MCP-13 | `Plugins/AgentBridge/MCP/server.py`:911 |
| 53 工具字典定义 | 五大字典 + JSON Schema 转换,catalog 真源 | F-MCP-01..05 + F-MCP-06..09 + F-MCP-10/11 + F-MCP-12 | `Plugins/AgentBridge/MCP/tool_definitions.py`:567 |
| 前端 Compiler 工具适配 | 14 个 prepare/save/get_session_status 工具,封装 pipeline_orchestrator | F-MCP-06/07/08/09 | `Plugins/AgentBridge/MCP/compiler_tools.py`:433 |
| 后端 Evidence 工具适配 | 11 个 load/judge/list/compare/create_batch/promote_run | F-MCP-10/11 | `Plugins/AgentBridge/MCP/evidence_tools.py`:1126 |
| Python Editor 通道 (Channel A) | HTTP POST `/remote/script/run`,直接执行 Python Editor Scripting | F-MCP-* (transport) | `Plugins/AgentBridge/MCP/py_channel.py`:65 |
| Remote Control 通道 (Channel B) | 复用 `remote_control_client`,re-export 9 个函数 | F-MCP-* (transport) | `Plugins/AgentBridge/MCP/rc_channel.py`:38 |
| 命名 / 路径规范 | 资产前缀校验 + 默认路径拼接(`L_` / `M_` / `MI_` / `WBP_` 等) | F-MCP-12 (helper) | `Plugins/AgentBridge/MCP/naming.py`:58 |

> 53 工具的"字典定义"集中在 `tool_definitions.py`,但"实际函数体"分散三处:Layer 1 Query/Write 直接 wrap 进 `bridge.query_tools` / `bridge.write_tools`(通过 `server.wrap_bridge_query` / `wrap_bridge_write`);Layer 1 Service / Layer 2 Asset / Layer 3 在 `server.py` 内部定义(`create_level` / `create_material` 等 13 个 local 函数);Compiler 14 个 + Evidence 11 个分别落在 `compiler_tools.py` / `evidence_tools.py`。F-MCP-12 的 4 个 alias(`compiler_intake_prepare/save` + `compiler_plan_prepare/save`)在 `compiler_tools.py:200-264` 内部按 `session.session_version` 自动路由到 v1 Stage 2 或 v2 Stage 3。

## 3. 关键类/函数签名

> 仅列与协议层、路由分发、通道切换、治理判定强相关的函数,**不 dump 53 工具完整签名**,字段级签名见 `Docs/contracts/mcp_tools_catalog.md`。签名后 1 行中文用途(<=20 字)。

### 3.1 server.py 主入口(F-MCP-13)

```python
def _configure_bridge_channel() -> tuple[str, list[str]]  # 三通道选择 + warnings
ACTIVE_MCP_CHANNEL, MCP_CHANNEL_WARNINGS  # 模块级单例,启动期固化
def make_response(status, summary, data=None, warnings=None, errors=None) -> dict  # tool_contract §2.2 统一返回
def _run_editor_python_tool(script, success_summary, failure_prefix, data=None, warnings=None, timeout_ms=30000) -> dict  # Editor Python 执行统一封装
def wrap_bridge_query(tool_name: str, **kwargs) -> dict  # Layer 1 query dispatch wrap
def wrap_bridge_write(tool_name: str, **kwargs) -> dict  # Layer 1 write dispatch wrap
TOOL_DISPATCH: dict[str, tuple[str, Any]]  # 53 工具 → (kind, target) 路由表;kind ∈ {query, write, local, compiler, evidence}
def dispatch_tool(tool_name: str, arguments: dict | None) -> dict  # 唯一统一 dispatch 入口
def create_mcp_server()  # 创建 mcp.server.lowlevel.Server 并绑定 handle_list_tools / handle_call_tool
async def handle_list_tools() -> list[types.Tool]  # 列出 ALL_TOOLS,inputSchema 由 to_json_schema 转
async def handle_call_tool(tool_name, arguments) -> types.CallToolResult  # 线程池跑 dispatch_tool,避免阻塞事件循环
async def main()  # stdio_server() 异步 main
# Layer 2 Channel A 资产创建(代表性 5 个,完整 13 个见 server.py:235-760)
def create_level(level_name, level_path=None, template=None) -> dict  # 新关卡(EditorLevelLibrary.new_level)
def create_material(material_name, material_path=None, base_color=None) -> dict  # 材质母版(AssetToolsHelpers + MaterialFactoryNew)
def create_material_instance(instance_name, parent_material, ...) -> dict  # 材质实例 + 参数写入
def create_widget_blueprint(widget_name, ...) -> dict  # Widget BP(UMG)
def configure_world_settings(gamemode_override=None, default_gamemode=None) -> dict  # 走 RC API 写 WorldSettings
def run_editor_python(script: str, timeout_ms: int = 30000) -> dict  # Layer 3 兜底(任意 Python 脚本)
```

### 3.2 tool_definitions.py 53 工具 catalog(F-MCP-01..12)

```python
LAYER1_QUERY_TOOLS: dict  # 7 个 query 工具元数据(get_current_project_state / list_level_actors 等)
LAYER1_WRITE_TOOLS: dict  # 6 个 write 工具(spawn_actor / set_actor_transform / import_assets / ...)
LAYER1_SERVICE_TOOLS: dict  # 5 个 editor service(capture_screenshot / build_project / run_automation_tests / undo_last_transaction / save_named_assets)
LAYER2_ASSET_TOOLS: dict  # 9 个 Channel A/B 资产创建(create_level / create_material / configure_gamemode_bp / ...)
LAYER3_TOOLS: dict  # 1 个兜底(run_editor_python)
COMPILER_FRONTEND_TOOLS: dict  # 14 个 compiler stage(含 4 个 v1 alias)
EVIDENCE_JUDGE_TOOLS: dict  # 11 个 evidence load/judge/promote
ALL_TOOLS: dict  # 七大字典 update 合并,TOOL_COUNT = len(ALL_TOOLS) = 53
def to_json_schema(tool_def: dict) -> dict  # 内部 params 表 → MCP Tool.inputSchema JSON Schema
```

### 3.3 compiler_tools.py 14 工具(F-MCP-06/07/08/09)

```python
# 共用 helper
def _make_response(status, summary, data=None, warnings=None, errors=None) -> dict  # 统一返回
def _load_session(session_path: str) -> CompilerSession  # 读 session.json
def _prepare_stage_tool(action_name, session_path, stage_num) -> dict  # 通用 prepare 适配
def _save_stage_tool(action_name, session_path, filled_data, stage_num) -> dict  # 通用 save 适配
def _wrap_prepare_result(action_name, result: dict) -> dict  # prepare → MCP 格式
def _wrap_save_result(action_name, result: dict) -> dict  # save → MCP 格式
# Stage 入口(代表性 8 个,完整 14 个见 catalog)
def compiler_create_session(gdd_path, target_phase, output_dir, session_version="1.0", run_id=None, fast_mode=False) -> dict  # 新建会话
def compiler_root_skill_prepare(session_path: str) -> dict  # Stage 1 prepare(v2 主入口)
def compiler_root_skill_save(session_path, filled_data) -> dict  # Stage 1 save
def compiler_clarification_prepare(session_path: str) -> dict  # Stage 2 prepare
def compiler_skill_graph_prepare(session_path: str) -> dict  # Stage 3 prepare
def compiler_skill_graph_save(session_path, filled_data) -> dict  # Stage 3 save
def compiler_stage4_node_prepare(session_path, node_id, phase, node_state=None) -> dict  # Stage 4 单节点 prepare(MCP Agent 即 Generator)
def compiler_stage4_node_save(session_path, node_id, phase, output, node_state=None) -> dict  # Stage 4 单节点 save + 自动 Fragment 生成
def compiler_get_session_status(session_path: str) -> dict  # session 状态查询
# F-MCP-12 alias(v1/v2 自动路由,见 compiler_tools.py:200-264)
def compiler_intake_prepare(session_path)  # v1 → Stage 1 Intake;v2 → 等价 root_skill_prepare
def compiler_intake_save(session_path, filled_data)  # 同上 save
def compiler_plan_prepare(session_path)  # v1 → Stage 2 Planner;v2 → 等价 skill_graph_prepare(通过 _load_stage_for_plan_alias 判定)
def compiler_plan_save(session_path, filled_data)  # 同上 save
```

### 3.4 evidence_tools.py 11 工具 + 治理 helper(F-MCP-10/11)

```python
# 治理判定 helper(F-GOV-02/03 核心实现)
def _evaluate_promotable(snapshot: dict) -> dict  # promotable + reasons:fast_mode / heuristic_fallback / status != completed / 阶段不全 / constraint_violations > 0 / metadata.promotable == false 任一命中 → promotable=False
def _is_stage_completion_full(snapshot: dict) -> bool  # 按 session_version 校验 completed 阶段数
def _load_run_workspace_snapshot(run_id: str) -> dict  # 读 ProjectState/runs/{run_id}/ 全产物快照
def _build_run_comparison(snapshot_a, snapshot_b) -> dict  # 六维 diff(constraint/realization/fragment/build_ir/naming/provisional)
def _create_batch_from_snapshot(snapshot, promoted_by, notes, make_active, update_base_project) -> dict  # 真正的 promote 执行体
# 11 工具入口(代表性 6 个)
def evidence_load_manifest(run_id: str) -> dict  # 读 manifest.json
def evidence_load_screenshots(run_id: str) -> dict  # 列截图
def evidence_judge_acceptance(run_id: str, criteria: dict) -> dict  # pass/fail/escalate 初判
def evidence_compare_runs(run_a_id, run_b_id, output_path=None) -> dict  # 双 run 六维 diff
def evidence_create_batch(source_run_id, promoted_by="human_review", notes="", make_active=True) -> dict  # 创建 batch(不更新 baseline 指针)
def evidence_promote_run(source_run_id, promoted_by="human_review", notes="", make_active=True, update_base_project=True) -> dict  # promote + baseline 更新
# 完整 11 工具:load_manifest / load_screenshots / load_logs / load_report / judge_acceptance / decide_escalation / export_summary / list_runs / compare_runs / create_batch / promote_run(见 catalog)
```

### 3.5 py_channel.py / rc_channel.py(transport)

```python
# py_channel.py — Channel A(Python Editor Scripting via RC)
DEFAULT_RC_URL = "http://localhost:30010"
def execute_editor_python(script: str, rc_url: str = None, timeout_ms: int = 30000) -> dict  # POST /remote/script/run
def check_editor_connection(rc_url: str = None) -> bool  # GET /remote/info 探活

# rc_channel.py — Channel B(Remote Control HTTP)
# 直接 re-export bridge.remote_control_client 的 9 个函数:
#   configure / get_base_url / call_function / get_property / set_property / batch / search_actors / search_assets / check_connection
```

### 3.6 naming.py(F-MCP-12 helper)

```python
ASSET_PATHS  # /Game/Maps/ / /Game/Materials/ / /Game/UI/ ... 七类资产默认路径
ASSET_PREFIXES  # L_ / BP_ / M_ / MI_ / WBP_ / DA_ / T_ 七类前缀
def validate_asset_name(asset_type, name) -> tuple[bool, str, str]  # 返回 (is_valid, corrected_name, message)
def make_full_asset_path(asset_type, name, custom_path=None) -> str  # 拼完整资产路径
def get_default_path(asset_type: str) -> str  # 默认保存路径
```

## 4. 数据流与状态机

### 4.1 MCP stdio 协议总体数据流(F-MCP-13)

```
Claude Code / Agent
  └─ stdio JSON-RPC(initialize / tools/list / tools/call)
     └─ server.main → mcp.server.stdio.stdio_server() → server.run
        ├─ handle_list_tools()  → ALL_TOOLS.items() → [types.Tool(name, description, to_json_schema(tool_def))]
        └─ handle_call_tool(tool_name, arguments)
           └─ asyncio.run_in_executor(None, dispatch_tool, tool_name, arguments)  # 线程池跑同步工具
              └─ dispatch_tool 按 TOOL_DISPATCH[tool_name] = (kind, target) 分发
                 ├─ kind="query"    → wrap_bridge_query(target, **arguments)   → bridge.query_tools[target]
                 ├─ kind="write"    → wrap_bridge_write(target, **arguments)   → bridge.write_tools[target]
                 ├─ kind="local"    → target(**arguments)                       → server.py 内部 13 函数
                 ├─ kind="compiler" → target(**arguments)                       → compiler_tools.* 14 函数
                 └─ kind="evidence" → target(**arguments)                       → evidence_tools.* 11 函数
              → 统一返回 {status, summary, data, warnings, errors}
           → types.CallToolResult(content=[TextContent(JSON)], structuredContent=result, isError=(status=="failed"))
```

`MCP_CHANNEL_WARNINGS` 在 Layer 1 query/write 返回前被前置 prepend,确保启动期通道告警能透传给 Agent。

### 4.2 三通道初始化(server.py:45-77)

```
_configure_bridge_channel() 启动期单次执行:
  env_channel = os.environ["AGENTBRIDGE_MCP_CHANNEL"].strip().lower()
  channel_map = {
    "mock":            BridgeChannel.MOCK,
    "remote_control":  BridgeChannel.REMOTE_CONTROL,
    "rc":              BridgeChannel.REMOTE_CONTROL,
    "cpp_plugin":      BridgeChannel.CPP_PLUGIN,
    "cpp":             BridgeChannel.CPP_PLUGIN,
  }
  if env_channel ∈ channel_map → set_channel(channel_map[env_channel])
  elif env_channel != ""        → warnings + 回退 CPP_PLUGIN
  else                          → 默认 CPP_PLUGIN
  → set_channel(target) → ACTIVE_MCP_CHANNEL = get_channel().value
```

**关键约束**:`BridgeChannel` 第 4 值 `PYTHON_EDITOR` **不在 channel_map**(server.py:69-71 注释:UE 5.5.4 下 `EditorLevelLibrary.GetEditorWorld` 不能稳定通过 RC 远程调用,默认改走项目主干的 C++ Subsystem 通道,避免 live smoke 命中 HTTP 400)。这意味着 MCP 启动期**永远不会自动落到 PYTHON_EDITOR**,Python Editor Scripting 调用走的是 `py_channel.execute_editor_python` 的独立 HTTP 通道,不经过 `BridgeChannel` 状态机。

### 4.3 前端 Compiler 工具数据流(F-MCP-06/07/08/09)

```
Agent 调 compiler_create_session(gdd_path, target_phase, output_dir, session_version="2.0")
  → compiler_tools.compiler_create_session
    → Compiler.pipeline.session.create_session(...)
    → session.save() → ProjectState/runs/{run_id}/session.json

Agent 调 compiler_root_skill_prepare(session_path)
  → _prepare_stage_tool("Root Skill 准备", session_path, stage_num=1)
    → CompilerSession.load(session_path)
    → pipeline_orchestrator.prepare_stage(session, 1)
    → 返回 {template, schema, input_context}

Agent 用 Claude/GPT 创造性填写 template
Agent 调 compiler_root_skill_save(session_path, filled_data)
  → _save_stage_tool → pipeline_orchestrator.save_stage(session, 1, filled_data)
    → schema 校验 → 落盘 root_skill_contract.json → session.advance_stage()

Stage 4 特殊:逐节点 + 三 phase(discovery/candidates/convergence)
  → compiler_stage4_node_prepare(session_path, node_id, phase, node_state=None)
    → 加载 Stage 1/2/3 产物 → domain_skill_runtime.prepare_node_phase
    → 返回 SkillTemplate prompts + Context Bundle + 生成指引
  → Agent 创造性生成 output
  → compiler_stage4_node_save(session_path, node_id, phase, output, node_state)
    → domain_skill_runtime.save_node_phase
    → ≤ 2 轮质量重试 + ≤ 2 次 schema 修复(_validate_stage4_node_acceptance)
    → convergence 完成 → 自动生成 Fragment
    → session.generator_provider = "mcp_agent"(MCP Agent 即 Generator 模式)
```

### 4.4 后端 Evidence 工具数据流(F-MCP-10/11)

```
Agent 调 evidence_list_runs(date_filter=None)
  → evidence_manager.list_runs → 返回 ProjectState/Evidence/* 下全部 run_id

Agent 调 evidence_load_manifest / load_screenshots / load_logs / load_report
  → _get_run_dir(run_id) → ProjectState/Evidence/{run_id}/
  → 读 manifest.json / screenshots/ / logs/ / reports/

Agent 调 evidence_judge_acceptance(run_id, criteria) / evidence_decide_escalation
  → _derive_judgment(manifest, criteria) → pass/fail/escalate

Agent 调 evidence_compare_runs(run_a, run_b, output_path)
  → _load_run_workspace_snapshot 两次 → _build_run_comparison
    → 六维 diff:constraint / realization / fragment / build_ir / naming / provisional
    → 可选落盘 run_comparison.json(schema 校验)

Agent 调 evidence_promote_run(source_run_id, promoted_by, notes, make_active=True, update_base_project=True)
  → _load_run_workspace_snapshot(source_run_id)
  → _evaluate_promotable(snapshot) 治理判定:
      reasons = []
      if snapshot.fast_mode: reasons += "fast_mode run 不可 promote"               (F-GOV-02)
      if snapshot.status != "completed": reasons += ...
      if snapshot.constraint_violations > 0: reasons += ...
      if not _is_stage_completion_full(snapshot): reasons += "阶段不完整"
      if snapshot.generator_provider == "heuristic_fallback": reasons += ...      (F-GOV-03)
      if snapshot.metadata_promotable == false: reasons += ...
      → promotable = (len(reasons) == 0)
  → 通过 → _create_batch_from_snapshot:
      _next_batch_id() → batch-YYYYMMDD-NNN
      _copy_promoted_artifacts(run_dir, promoted_dir) → 12 类 PROMOTED_ARTIFACTS
      _save_batch_manifest + schema 校验
      _update_active_batch(batch_id, make_active=True) → batches/active_batch.json
      update_base_project=True → 更新 baseline 指针
  → 拒绝 → 返回 reasons,batch 不创建
```

### 4.5 工具命名 / alias 解析(F-MCP-12,naming.py + compiler_tools.py)

```
naming.py(资产前缀):
  validate_asset_name("level", "BoardLevel")
    → prefix = "L_"(ASSET_PREFIXES["level"])
    → 输入未带 L_ → (False, "L_BoardLevel", "建议命名:L_BoardLevel")
    → 调用方(create_level)自动 corrected_name + warnings 透传

compiler_tools.py(v1/v2 工具 alias):
  compiler_plan_prepare(session_path)
    → _load_stage_for_plan_alias(session_path)
      → session.session_version == "2.0" → return 3 (Skill Graph)
      → else                              → return 2 (Planner)
    → prepare_stage(session, stage_num)
```

## 5. 扩展点

- **新增 MCP 工具**:在 `tool_definitions.py` 七大字典(LAYER1_QUERY_TOOLS / LAYER1_WRITE_TOOLS / LAYER1_SERVICE_TOOLS / LAYER2_ASSET_TOOLS / LAYER3_TOOLS / COMPILER_FRONTEND_TOOLS / EVIDENCE_JUDGE_TOOLS)任一加 key + params + description;在 `server.TOOL_DISPATCH` 加 `(kind, target)` 路由项(kind ∈ {query, write, local, compiler, evidence});若 kind="local" 需在 server.py 内部加函数体,若 kind="compiler"/"evidence" 在对应模块加函数。**禁止**自定义 kind,否则 `dispatch_tool` 走 "未知路由类型" 失败分支。
- **新增 Bridge 通道**:在 `bridge_core.BridgeChannel` 加 enum 值;在 `server._configure_bridge_channel` 的 `channel_map` 加映射(短名 + 长名两条);评估是否需要新通道独立的 transport adapter(类似 `py_channel.py` / `rc_channel.py`)。
- **新增 v1/v2 工具 alias**:在 `tool_definitions.COMPILER_FRONTEND_TOOLS` 加 alias key;在 `compiler_tools.py` 加 alias 函数,内部按 `session.session_version` 路由到 v1/v2 对应 stage_num;**禁止**在 `tool_definitions` 同时声明两套 schema,alias 应共用主工具 schema。
- **新增资产命名前缀**:在 `naming.ASSET_PATHS` + `ASSET_PREFIXES` 同步加 asset_type 条目;受影响工具(`create_level` / `create_material` / ...)调用 `validate_asset_name(asset_type, name)` 自动生效,无需改 server.py。
- **新增 Evidence 治理判定维度**:在 `evidence_tools._evaluate_promotable` 的 reasons 列表加新规则;在 `_load_run_workspace_snapshot` 加新字段抽取;`evidence_promote_run` 自动消费,无需改 catalog。
- **工具入参 JSON Schema 验证**:`to_json_schema` 已支持 string / integer / boolean / array / object 五类,新增类型在 `type_map` 加映射即可。

## 6. 已知约束与陷阱

- **`channel_map` 只暴露 3 档(MOCK / REMOTE_CONTROL / CPP_PLUGIN)**:`BridgeChannel.PYTHON_EDITOR` **不在 MCP 启动期映射表**(server.py:69-71 注释明示),理由是 UE 5.5.4 下 `EditorLevelLibrary.GetEditorWorld` 不能稳定通过 RC 远程调用,默认改走项目主干的 C++ Subsystem 通道避免 live smoke 命中 HTTP 400。Python Editor Scripting 调用通过 `py_channel.execute_editor_python` 的独立 HTTP 通道(POST `/remote/script/run`),**不经过 `BridgeChannel` 状态机**。修改默认通道前必须先评估 5.5.4 → 5.7 后该约束是否仍成立。
- **MCP_CHANNEL_WARNINGS 仅在 Layer 1 query/write 透传**:`wrap_bridge_query` / `wrap_bridge_write` 在返回前把启动期通道告警 prepend 到 result.warnings;但 Layer 1 Service / Layer 2 / Layer 3 / Compiler / Evidence 路径**不透传**,Agent 可能错过通道初始化告警,排错时优先查 query/write 工具返回。
- **F-MCP-12 alias 4 个工具语义按 session_version 漂移**:`compiler_intake_prepare/save` 在 v1 是 Stage 1 Intake,在 v2 等价 Root Skill;`compiler_plan_prepare/save` 在 v1 是 Stage 2 Planner,在 v2 等价 Stage 3 Skill Graph(`compiler_tools._load_stage_for_plan_alias` 判定)。**Agent 不应假设 alias 工具固定指向某阶段**,必须先用 `compiler_get_session_status` 拿 session_version 才能解释返回 template 的 schema。
- **`evidence_promote_run` 拒绝六类 run**:`_evaluate_promotable` 同时检查 fast_mode(F-GOV-02)/ heuristic_fallback(F-GOV-03)/ status != completed / constraint_violations > 0 / 阶段不完整 / metadata.promotable=false 六个维度,**任一不满足就拒绝**。Agent 端必须先调 `evidence_compare_runs` / `evidence_judge_acceptance` 自检,直接调 `promote_run` 失败概率高。
- **`naming_resolution_log` 是 Stage 6 sidecar 而非 Stage 4 产物**:Evidence 工具读 `ProjectState/runs/{run_id}/naming_resolution_log.json` 是 lowering_v2 写的 sidecar(LLD/04 §6 已说明);MCP 后端只读不写,所有 GDD 名 → UE 路径解析记录在编译期就已完成。
- **stdio 编码默认 UTF-8**:Windows 默认 GBK 在 stdio 二进制流下会乱码 JSON-RPC,MCP SDK 内部已显式 UTF-8 处理,但 Python 子进程若被 `chcp 936` 的 cmd 启动可能仍踩坑。**`.mcp.json` 启动 Claude Code 必须用 UTF-8 终端**。
- **`handle_call_tool` 强制走线程池**:`asyncio.run_in_executor(None, dispatch_tool, ...)` 防止同步工具阻塞 stdio 事件循环;意味着任何工具内部**不应再创建 asyncio 子事件循环**,否则会 deadlock。
- **53 工具 catalog 数值与 `TOOL_COUNT` 漂移风险**:`tool_definitions.py:528` `TOOL_COUNT = len(ALL_TOOLS)`,当前注释写"51",实际 update 七字典后是 7+6+5+9+1+14+11 = 53。**改字典必须重新跑 `python -c "from MCP.tool_definitions import TOOL_COUNT; print(TOOL_COUNT)"` 同步 `Docs/contracts/mcp_tools_catalog.md` 标题**。

## 7. UE 5.7 迁移变更点

> 引用 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 / §4(P1 7 条裁决:1 false-positive + 6 confirmed;P2/P3 全部 suspected 留 5.7 实测裁决)。MCP Server 自身是协议层 / 路由层,**绝大多数 BC 通过 Bridge / Compiler 下游间接命中**,但 `server.py` 内部 Layer 2 Asset 工具直接 hardcode 了 `unreal.EditorLevelLibrary` / `unreal.EditorAssetLibrary` 字符串到 Python 脚本中,**是 BC-016 / BC-017 的直接命中点**。每条按 "[BC-NNN] api_or_key (P? 状态) → 影响 → 迁移行动" 三段式列出。**BC-019 严格 P2 suspected,不在 MCP LLD 阶段升 P1**(Task 1.1-1.10 统一教训)。

- **[BC-016] Python EditorLevelLibrary 调用 — P1 confirmed (reviewer=msc)**
  影响:`server.py` Layer 2 Asset 工具直接拼 Python 脚本字符串包含 `unreal.EditorLevelLibrary.new_level` / `load_level` / `get_editor_world`(server.py:137, 141, 248, 581 等);breaking changes scan §3 直接列点。`evidence_tools` / `compiler_tools` 不直接命中。
  迁移行动:把 server.py 中 Layer 2 Asset 工具拼接的 Python 字符串里 `unreal.EditorLevelLibrary.*` 整体替换为 `unreal.EditorLevelSubsystem` / `unreal.EditorActorSubsystem` / `unreal.UnrealEditorSubsystem`;`create_level` / `open_level` 是高频点。建议先在 5.7 Editor 跑 `python -c "import unreal; unreal.EditorLevelLibrary.get_editor_world()"` 看是否仍可用(若 deprecated warning 而非 removal,可保留向后兼容期)。

- **[BC-017] Python EditorAssetLibrary 调用 — P1 confirmed (reviewer=msc)**
  影响:`server.py` Layer 2 Asset 工具直接 hardcode `unreal.EditorAssetLibrary.save_asset` / `load_asset` / `load_blueprint_class`(server.py:292, 337, 360, 405, 427, 432, 440, 445, 447, 454, 640+ 多处);breaking changes scan §3 直接列点。
  迁移行动:把 `unreal.EditorAssetLibrary.*` 替换为 `unreal.EditorAssetSubsystem`;`create_material` / `create_material_instance` / `create_widget_blueprint` / `set_blueprint_defaults` 都需要改。5.7 后若 EditorAssetLibrary 直接 removal,Layer 2 全部工具需要同步改;若 deprecated warning,可保留一个 release cycle。

- **[BC-018] `unreal.*` 其他 binding 综合 — P2 suspected (reviewer=pending-msc)**
  影响:`server.py` Layer 2 Asset 工具还命中了 `AssetToolsHelpers` / `MaterialFactoryNew` / `MaterialInstanceConstantFactoryNew` / `MaterialEditingLibrary` / `WidgetBlueprintFactory` / `EditorLoadingAndSavingUtils` / `AutomationLibrary` / `SystemLibrary` / `LinearColor` / `load_class` / `get_default_object`(server.py:281, 282, 286, 326, 327, 331, 344, 353, 394, 395, 399, 436, 451, 598, 619 多处)。5.6 release notes 未见这些 binding 的 deprecation 提及。
  迁移行动:**严格 P2 suspected**;UE 5.7 Editor 实测 `python Plugins/AgentBridge/Tests/run_system_tests.py` 完整跑套件看 `unreal.*` 失败点,再决断;不在 MCP LLD 阶段升 P1。

- **[BC-019] RemoteControl HTTP 端点 `/remote/object/*` + `/remote/script/run` — P2 suspected (reviewer=pending-msc)**
  影响:`rc_channel.py` re-export `bridge.remote_control_client` 直接命中 `/remote/object/call` / `/remote/object/property` / `/remote/batch`;**`py_channel.py:33` 直接命中 `/remote/script/run`**(Channel A 唯一执行路径);`configure_world_settings` (server.py:521-573) 是 MCP 唯一直接 `import rc_channel` 的工具。UE 5.6/5.7 release notes 未提及 endpoint 移除。
  迁移行动:**严格 P2 suspected,不在 MCP LLD 阶段升 P1**(Task 1.1/1.2/1.5/1.6/1.7/1.8/1.9 教训);5.7 Editor 跑通后再决断。**注**:`py_channel` 是 Channel A 全部 Layer 2 工具的执行底座,若 endpoint 形态变化(JSON 序列化结构改变),Layer 2 13 个工具会**全部 grouped 失败**,这是 MCP Server 5.7 迁移的最大潜在风险点,但仍需 5.7 实测才能裁决,**当前严格 P2**。

- **[BC-022] `.uproject` Plugins[] enabled — P2 suspected (reviewer=pending-msc)**
  影响:MCP Server 自身不读 `.uproject`,但 `.mcp.json` 启动 MCP 进程时若工程未启用 `RemoteControl` / `PythonScriptPlugin` 插件,`py_channel.execute_editor_python` 会立即返回 HTTP 404。
  迁移行动:**严格 P2 suspected**;UE 5.7 打开本工程确认 `RemoteControl` / `RemoteControlWebInterface` / `PythonScriptPlugin` 都被正确加载即可,MCP 侧无改动。

- **[BC-023] `AgentBridge.uplugin` Plugins[] 依赖声明 — P2 suspected (reviewer=pending-msc)**
  影响:MCP Server 不读 `.uplugin`,但运行时依赖 `AgentBridge.uplugin` Plugins[] 正确声明 `EditorScriptingUtilities` / `RemoteControl` / `PythonScriptPlugin` / `Gauntlet` 四插件(scan §3.5);5.6 起 `EditorScriptingUtilities` 已 deprecated(与 BC-008 重叠)。
  迁移行动:**严格 P2 suspected**;UE 5.7 Editor 看插件依赖加载,若 `EditorScriptingUtilities` 5.7 removal 则需要在 `AgentBridge.uplugin` 移除该声明 + 评估 MCP Server 是否还能正常启动。

### 迁移优先级与回归路径

按优先级排序:**P1 confirmed 两条(BC-016 / BC-017)直接命中 server.py Layer 2 Asset 工具内嵌 Python 脚本字符串**,这是 MCP LLD 迁移的硬强制项,需要在 5.7 实测前先把 `unreal.EditorLevelLibrary.*` / `unreal.EditorAssetLibrary.*` 全部替换为对应 Subsystem;**P2 suspected 四条(BC-018 / BC-019 / BC-022 / BC-023)严格留 5.7 实测裁决**,其中 BC-019 是 MCP 最大潜在风险点(`py_channel` 是 Channel A 全部 Layer 2 工具的执行底座)但仍严格 P2,不在 LLD 阶段升级。回归路径:先跑 `python -c "from MCP.tool_definitions import TOOL_COUNT; print(TOOL_COUNT)"` 确认 53;再跑 `python -c "from MCP.server import TOOL_DISPATCH; print(len(TOOL_DISPATCH))"` 确认 dispatch 完整;5.7 Editor 打开后跑 `python Plugins/AgentBridge/Tests/run_system_tests.py` 完整 10 Stage 看 Channel A Layer 2 工具是否仍可执行;最后跑 `evidence_promote_run` 看治理链路是否正常。

---

**关联文件**: `Docs/design/HLD.md` §4 / `Docs/requirements/SRS.md` §3.5 / `Docs/FEATURE_INVENTORY.md` F-MCP-01..13 / `Docs/contracts/mcp_tools_catalog.md`(53 工具字段级签名)/ `Docs/contracts/tool_contract.md` §2-§4 / `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4 / `Plugins/AgentBridge/MCP/server.py`(911 行,F-MCP-13 主入口)/ `Plugins/AgentBridge/MCP/tool_definitions.py`(567 行,53 工具 catalog 真源)/ `Plugins/AgentBridge/MCP/compiler_tools.py`(433 行,14 工具)/ `Plugins/AgentBridge/MCP/evidence_tools.py`(1126 行,11 工具 + 治理判定)/ `Plugins/AgentBridge/MCP/py_channel.py`(65 行,Channel A)/ `Plugins/AgentBridge/MCP/rc_channel.py`(38 行,Channel B re-export)/ `Plugins/AgentBridge/MCP/naming.py`(58 行,资产前缀 + 路径)
