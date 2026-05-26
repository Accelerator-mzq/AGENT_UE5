# LLD/02 — Bridge Python 详细设计

> 版本: v1 (2026-05-26)
> 范围: AgentBridge Plugin Bridge Python 封装层 9 个模块
> 上游: `Docs/design/HLD.md` §模块拓扑 + `Docs/requirements/SRS.md` §3.2 + `Docs/FEATURE_INVENTORY.md` F-BRG-01..09
> 契约: `Docs/contracts/tool_contract.md` §2-§4(L1/L3 协议) + `Docs/contracts/mcp_tools_catalog.md` F-MCP-01..05
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

本 LLD 覆盖 `Plugins/AgentBridge/Scripts/bridge/` 下 9 个 Python 模块(对应 `FEATURE_INVENTORY` F-BRG-01..09),它们共同承担 AgentBridge 框架"Python 侧封装层"的全部能力:对 Agent / MCP / Orchestrator 暴露**统一的 L1 语义工具与 L3 UI 工具调用入口**,对底层透明地切换三条 transport 通道(`PYTHON_EDITOR` 进程内 unreal 模块 / `REMOTE_CONTROL` HTTP 30010 / `CPP_PLUGIN` 通过 RC 反射调 Subsystem)外加一条 `MOCK` 调试通道。9 个模块共 2987 行,统一通过 `bridge_core` 的响应壳、错误码、参数校验、通道分发与 `safe_execute` 异常包装收敛;F-BRG-03(L1 反馈接口族)是契约族,实际实现散在 query_tools/write_tools 内,故本 LLD §3 只列工具入口,反馈 schema 索引参见关联文件区。本文档聚焦内部分层、关键函数签名、数据流、扩展点、已知约束与 UE 5.7 迁移变更点,目的是让接手者能在不阅读 2987 行 Python 源码全文的前提下,准确定位修改位置并评估改动成本。

## 2. 内部分层

| 模块 | 角色 | F-BRG ID | 文件 (行数) |
|---|---|---|---|
| `__init__.py` | 包入口(空模块标识) | — | `Plugins/AgentBridge/Scripts/bridge/__init__.py` (6) |
| `bridge_core.py` | 通信主体:通道枚举 + 响应构造 + 校验 + Mock + 通道 C 客户端 | F-BRG-09 | `Plugins/AgentBridge/Scripts/bridge/bridge_core.py` (373) |
| `query_tools.py` | L1 查询接口族(9 工具,7 主入口 + 2 扩展) | F-BRG-01 | `Plugins/AgentBridge/Scripts/bridge/query_tools.py` (593) |
| `write_tools.py` | L1 写接口族(6 工具,均带 dry_run + Transaction) | F-BRG-02 | `Plugins/AgentBridge/Scripts/bridge/write_tools.py` (684) |
| (反馈契约)| L1 反馈接口族(schema 索引,实现散在上面两模块) | F-BRG-03 | `Schemas/feedback/*.response.schema.json` + `Schemas/write_feedback/` |
| `ui_tools.py` | L3 UI 自动化(异步原型 + 交叉比对) | F-BRG-04 | `Plugins/AgentBridge/Scripts/bridge/ui_tools.py` (620) |
| `remote_control_client.py` | RC HTTP 30010 客户端(call/property/batch) | F-BRG-05 | `Plugins/AgentBridge/Scripts/bridge/remote_control_client.py` (206) |
| `uat_runner.py` | UAT 子进程包装(Python 侧),对应 C++ FUATRunner | F-BRG-06 | `Plugins/AgentBridge/Scripts/bridge/uat_runner.py` (245) |
| `ue_helpers.py` | 通道 A 专用资产/关卡 helpers(unreal 模块直调) | F-BRG-07 | `Plugins/AgentBridge/Scripts/bridge/ue_helpers.py` (135) |
| `project_config.py` | 项目根目录 / Schemas 目录 / Reports 目录解析器 | F-BRG-08 | `Plugins/AgentBridge/Scripts/bridge/project_config.py` (125) |

按职责自上而下分三层:**通信主体** `bridge_core` 提供响应壳 / 通道枚举 / 通道分发与 Mock 注册表 —— 它不感知具体工具,只负责"把任意工具的调用路由到三条 transport 之一";**语义工具层** `query_tools` / `write_tools` / `ui_tools` 是真正干活的层,L1 工具用 `_dispatch` / `_dispatch_write` 走 `bridge_core` 的通道分发,L3 工具走 `_dispatch_ui_tool` 默认 `CPP_PLUGIN` 通道;**Transport / 辅助层** `remote_control_client`(HTTP)、`uat_runner`(subprocess)、`ue_helpers`(unreal 模块直调)、`project_config`(路径解析)被上面两层按需调用。F-BRG-03(反馈契约族)不是单独模块,是横切在 query/write 工具内的响应 schema 集合,实际产生方就是 query_tools / write_tools 的 `make_response` 调用。

## 3. 关键类/函数签名

> 仅列与外部协议、通道切换、迁移强相关的函数,**不 dump 整文件**;完整方法表参见对应 `.py` 文件 `^def ` 抓取。每个签名后 1 行中文用途(<=20 字)。

### 3.1 `bridge_core.py`(F-BRG-09)

```python
class BridgeChannel(Enum): PYTHON_EDITOR | REMOTE_CONTROL | CPP_PLUGIN | MOCK  # 通道枚举,默认 MOCK
def set_channel(channel: BridgeChannel) -> None  # 切换全局执行通道(get_channel 对称)
def make_response(status, summary, data, warnings=None, errors=None) -> dict  # 统一响应壳构造
def safe_execute(func, *args, timeout: float = 0, **kwargs) -> dict  # 异常→failed 包装
def call_cpp_plugin(function_name: str, parameters: Optional[Dict] = None) -> dict  # 通道 C 入口
def validate_required_string(value, field_name: str) -> Optional[dict]  # 必填字符串校验
def validate_transform(transform: dict) -> Optional[dict]  # Transform 三段校验
def get_mock_response(tool_name: str) -> dict  # 读 examples/ 的预定义 JSON
```

### 3.2 `query_tools.py`(F-BRG-01)

```python
def _dispatch(tool_name, func_python, func_rc, *args, cpp_params=None, **kwargs) -> dict  # 通道分发器
def get_current_project_state() -> dict  # 工程上下文(路径/版本/PIE 状态)
def list_level_actors(level_path=None, class_filter=None) -> dict  # 关卡 Actor 列表
def get_actor_state(actor_path: str) -> dict  # Transform/Collision/Tags 三合一
def get_actor_bounds(actor_path: str) -> dict  # 包围盒读取
def get_asset_metadata(asset_path: str) -> dict  # 资产元数据
def get_dirty_assets() -> dict  # 未保存资产清单
def get_component_state(actor_path, component_name) -> dict  # 子组件 Transform 读取(run_map_check 同构)
def get_material_assignment(actor_path: str) -> dict  # 材质槽位读取
```

### 3.3 `write_tools.py`(F-BRG-02)

```python
def _dispatch_write(tool_name, func_python, func_rc, *args, cpp_params=None, **kwargs) -> dict  # 写通道分发
def spawn_actor(level_path, actor_class, actor_name, transform: dict, dry_run: bool = False) -> dict  # 生成 Actor
def set_actor_transform(actor_path: str, transform: dict, dry_run: bool = False) -> dict  # 修改 Transform
def import_assets(source_dir: str, dest_path: str, replace_existing: bool = False, dry_run: bool = False) -> dict  # 批量导入资产
def create_blueprint_child(parent_class: str, package_path: str, dry_run: bool = False) -> dict  # 创建子蓝图
def set_actor_collision(actor_path, profile_name, collision_enabled=None, can_affect_navigation=None, dry_run=False) -> dict  # 碰撞设置
def assign_material(actor_path: str, material_path: str, slot_index: int = 0, dry_run: bool = False) -> dict  # 材质指派
```

### 3.4 `ui_tools.py`(F-BRG-04)

```python
def _dispatch_ui_tool(tool_name: str, cpp_params: Optional[Dict] = None) -> dict  # L3 默认走 CPP_PLUGIN
def is_automation_driver_available() -> bool  # 探测 AutomationDriver 可用性
def click_detail_panel_button(actor_path, button_label, dry_run=False) -> dict  # Detail Panel 按钮点击
def type_in_detail_panel_field(actor_path, property_path, value, dry_run=False) -> dict  # Detail Panel 输入
def drag_asset_to_viewport(asset_path, drop_location, dry_run=False) -> dict  # 资产拖入视口
def start_ui_operation(operation_type, actor_path, target, value="", timeout_seconds=10.0, dry_run=False) -> dict  # 异步原型入口
def query_ui_operation(operation_id: str) -> dict  # 异步轮询查询
def cross_verify_ui_operation(l3_response, l1_verify_func, l1_verify_args=None) -> dict  # L3→L1 交叉比对
```

### 3.5 `remote_control_client.py`(F-BRG-05)

```python
class RemoteControlConfig: host/port/base_url  # HTTP 配置(默认 localhost:30010,configure() 改全局)
def call_function(object_path, function_name, parameters=None, generate_transaction=False) -> dict  # PUT /remote/object/call
def get_property(object_path: str, property_name: str) -> dict  # PUT /remote/object/property READ
def set_property(object_path, property_name, property_value, generate_transaction=False) -> dict  # PUT /remote/object/property WRITE
def batch(requests: List[dict]) -> List[dict]  # PUT /remote/batch
def check_connection() -> bool  # /remote/info 健康探测
```

### 3.6 `uat_runner.py`(F-BRG-06)

```python
@dataclass class UATRunResult: launched/completed/exit_code/stdout/stderr  # 运行结果
class UATRunner:
    def __init__(self, project_path: str = "", engine_dir: str = "")  # 构造期自动探测 RunUAT
    def build_cook_run(self, platform_name="Win64", configuration="Development", sync=True) -> UATRunResult  # BuildCookRun
    def run_automation_tests(self, test_filter="Project.AgentBridge", report_path="", sync=True) -> UATRunResult  # editortest 自动化
    def run_gauntlet(self, test_config_name="AgentBridge.AllTests", sync=True) -> UATRunResult  # Gauntlet 会话
    def run_custom(self, uat_command: str, sync=True) -> UATRunResult  # 任意 UAT 命令
```

### 3.7 `ue_helpers.py`(F-BRG-07)

```python
def find_actor_by_path(actor_path: str) -> Optional["unreal.Actor"]  # 路径匹配查 Actor
def read_transform(actor) -> dict  # FVector/FRotator/FVector → 统一 dict(read_collision/read_tags 同构)
def check_editor_ready() -> Optional[dict]  # World 存在 + 非 PIE 校验
```

### 3.8 `project_config.py`(F-BRG-08)

```python
def get_project_root() -> pathlib.Path  # .uproject 目录(env UE_PROJECT_ROOT / 上溯搜索)
def get_schemas_dir() -> pathlib.Path  # Schemas/ 路径(bridge_core 用,get_plugin_root 子项)
def get_dated_project_reports_dir(target_date=None) -> pathlib.Path  # ProjectState/Reports/<YYYY-MM-DD>/
```

## 4. 数据流

### 4.1 L1 查询数据流(通道 C,推荐路径)

```
Agent / MCP
  └─query_tools.get_actor_state("/Game/.../Actor.0")
      ├─validate_required_string(actor_path)
      └─_dispatch("get_actor_state", _python, _rc, cpp_params={"ActorPath": ...})
          └─call_cpp_plugin("GetActorState", cpp_params)
              └─remote_control_client.call_function(
                  "/Script/AgentBridge.Default__AgentBridgeSubsystem",
                  "GetActorState", {"ActorPath": ...}, generate_transaction=False)
                  └─PUT http://localhost:30010/remote/object/call
                      └─C++ UAgentBridgeSubsystem::GetActorState() → FBridgeResponse
                  ◀─ JSON {ReturnValue:{status,summary,data,...}}
              ◀─ _normalize_cpp_plugin_return_value(展开 FJsonObjectWrapper)
          ◀─ dict
      ◀─ dict
```

### 4.2 L1 写数据流(通道 C,含 dry_run)

```
write_tools.set_actor_transform(ActorPath, T, dry_run=False)
  ├─validate_required_string(actor_path) / validate_transform(T)
  └─_dispatch_write("set_actor_transform", ..., cpp_params={ActorPath, Transform, bDryRun})
      └─call_cpp_plugin("SetActorTransform", cpp_params)
          └─C++ Subsystem::SetActorTransform()
              ├─dry_run=True → 直接返回成功,不进 FScopedTransaction
              └─dry_run=False → FScopedTransaction + Actor->Modify() + 写后读回
```

`dry_run=True` 时 C++ 端不调用任何 `Modify()`、`bTransaction` 字段保持 `false`,Python 端透传该字段供 Orchestrator 识别此次调用未消耗 Undo Stack。

### 4.3 RC HTTP 备用路径(通道 B,直接调引擎 API)

```
query_tools._get_actor_state_rc(actor_path)
  └─remote_control_client.get_property(
        object_path=actor_path, property_name="RelativeLocation")
      └─PUT http://localhost:30010/remote/object/property (access=READ_ACCESS)
```

通道 B 直接调 UE5 原生 API,**不经过 AgentBridge Subsystem**,故不享受 C++ 端的参数校验与统一响应;query_tools 注释明确"UE5.5.4 下 ActorPath 走 /remote/object/property 直读"。

### 4.4 UAT 子进程数据流

```
uat_runner.UATRunner().build_cook_run(platform_name="Win64", configuration="Development", sync=True)
  ├─_detect_run_uat_path() — 环境变量 UE_ENGINE_DIR 或硬编码 fallback
  ├─args = 'BuildCookRun -project=... -platform=Win64 -clientconfig=Development -build -cook -stage -pak -unattended -utf8output'
  └─subprocess.run(f'"{run_uat_path}" {args}', shell=True, capture_output=True, timeout=3600)
      └─UATRunResult { launched=True, completed=True, exit_code, stdout, stderr }
```

### 4.5 L3 UI 数据流(异步原型)

```
ui_tools.click_detail_panel_button(actor_path, button_label, dry_run=False)
  └─_run_async_ui_operation("click_detail_panel_button", actor_path, target=button_label, ...)
      ├─_dispatch_ui_tool("start_ui_operation", {OperationType, ActorPath, Target, ...})
      │   └─call_cpp_plugin("StartUIOperation", ...) → operation_id
      ├─轮询 _dispatch_ui_tool("query_ui_operation", {OperationId})
      │   └─call_cpp_plugin("QueryUIOperation") → state ∈ {pending,running,success,failed}
      └─cross_verify_ui_operation(l3_response, l1_verify_func=get_actor_state, ...)
          └─字段级 diff → final_status ∈ {success, mismatch, failed}
```

L3 链路与 L1 最大差别是必须经 `cross_verify_ui_operation` 二次读回 L1 —— UI 模拟无法直接知道编辑器真实状态,只能通过 L1 语义层独立读回值再做字段级 diff,这也是 `mismatch` 状态枚举的根本来源。

## 5. 扩展点

- **新增 L1 query 工具**:在 `query_tools.py` 加 `def <new_tool>(args) -> dict`,内部走 `_dispatch` 分发并提供 `_<new_tool>_python` / `_<new_tool>_rc` 两个底层实现;同步在 `_CPP_QUERY_MAP` 注册 C++ 函数名(如 `"new_tool": "NewTool"`),C++ 端 `UAgentBridgeSubsystem` 加对应 `UFUNCTION(BlueprintCallable)`;Schema 端在 `Schemas/feedback/` 同步加 response schema,`Schemas/examples/` 加 example JSON 并在 `bridge_core.MOCK_MAP` 注册 Mock 映射。
- **新增 L1 write 工具**:同上,改 `write_tools._CPP_WRITE_MAP` + `_dispatch_write`,**必须显式接受 `dry_run` 参数**并在 cpp_params 内塞 `bDryRun`;C++ 端必须包 `FScopedTransaction`,Python 端无需额外处理 Transaction。
- **新增 transport 通道**(WebSocket / gRPC):在 `BridgeChannel` 枚举追加值,改 `_dispatch` / `_dispatch_write` / `_dispatch_ui_tool` 的 if/elif 链;通道客户端实现独立到新模块(如 `websocket_client.py`),不污染 `remote_control_client.py`。
- **dry_run / scope 参数扩展**:当前 dry_run 是单 bool,若要扩展为 `scope ∈ {validate_only, plan_only, apply}` 三档,需在 `validate_required_string` 旁补 `validate_scope`,所有 write 工具的 cpp_params 改传 `scope` 字符串,C++ 端枚举映射同步。
- **`ue_helpers` 复用规则**:仅当函数**同时被两个或以上 query/write 工具调用**才下沉到 `ue_helpers`(典型如 `find_actor_by_path` / `read_transform`);单 query 内部用一次的工具函数留在原文件 `_<tool>_python` 私有函数内,避免 helpers 膨胀。

## 6. 已知约束与陷阱

- **默认通道 MOCK,生产必须显式切换**:`bridge_core.ACTIVE_CHANNEL = BridgeChannel.MOCK`(bridge_core.py:66),Mock 返回 `Schemas/examples/` 预定义 JSON,**仅用于开发调试,不能用于验收**。生产路径必须通过 MCP `server.py` 的 `AGENTBRIDGE_MCP_CHANNEL` 环境变量切换到 `CPP_PLUGIN`(推荐)或 `REMOTE_CONTROL`(备用)。
- **通道 B 不能稳定调用 EditorLevelLibrary**:UE 5.5.4 实测 `EditorLevelLibrary.GetEditorWorld()` 经 RC 反射调用会返回 null / 报错,所以 query_tools.py 通道 B 实现绕道走 `/remote/object/property` 直读 `RelativeLocation` 等公开属性,而不是通过 `call_function` 调 `EditorLevelLibrary::GetEditorWorld`。该约束与 BC-016 P1 confirmed 强相关 —— 升 5.7 后 EditorLevelLibrary 若完全移除,通道 B 实现要同步迁移到 `UnrealEditorSubsystem` / `EditorActorSubsystem`。
- **`get_component_state` 通道 B 不可用**:`_get_component_state_rc` 直接返回 `failed` + 错误提示"Use channel C (cpp_plugin)" —— 因为 RC 不支持递归遍历组件树,这是 RC HTTP API 的固有限制,不是本框架的 bug。
- **`safe_execute` 在 Windows 上不支持超时**:`signal.SIGALRM` 仅 Unix 可用,Windows 下 `signal.alarm` 调用 `AttributeError` 被静默吞掉,timeout 参数等于失效;需要硬超时的场景必须走子进程隔离(如 `uat_runner` 用 `subprocess.run(timeout=...)` 而非 `safe_execute(timeout=...)`)。
- **`call_cpp_plugin` 路径硬编码**:`subsystem_path = "/Script/AgentBridge.Default__AgentBridgeSubsystem"`(bridge_core.py:202),若 C++ Subsystem 类名重命名必须同步改;且 RC 必须能反射到 `Default__` CDO 才能调到 BlueprintCallable 函数,这是 UE RC API 的固定路径形态。
- **`_unwrap_fjsonobjectwrapper` 双层解包**:C++ 端 `FBridgeResponse::Data` 是 `TSharedPtr<FJsonObject>`,经 RC 序列化后变成 `{"JsonString": "..."}` 形态,Python 端必须二次解析 `data.JsonString` 才能拿到真正的 dict;凡是新增"返回 data 字段嵌套对象"的 C++ 工具,Python 侧调用方都依赖此函数透明展开。
- **Windows stdin 默认 GBK**:Python 进程默认 `locale.getpreferredencoding()` 在中文 Windows 是 `cp936`,所有 JSON 解析必须显式 `encoding="utf-8"`;`bridge_core.get_mock_response` 已显式 `example_path.read_text(encoding="utf-8")`,新增 IO 代码须遵循。
- **`uat_runner` 硬编码 1 小时超时**:`subprocess.run(timeout=3600)`(uat_runner.py:185),长打包/全套自动化场景可能不够 —— 5.7 大规模 cook 时需要按平台调整或改异步(`sync=False`)模式让外层 Orchestrator 自己管轮询。

## 7. UE 5.7 迁移变更点

> 引用 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 / §4(P1 7 条裁决:1 false-positive + 6 confirmed;P2/P3 全部 suspected,留 5.7 实测裁决)。**P1 confirmed 范围严格限于 msc 已裁决 6 条**,其余按 P2/P3 标 suspected;**BC-019 严格 P2 suspected 不升级**(Task 1.1/1.2/1.5/1.6/1.7 教训)。每条按 "[BC-NNN] api_or_key (P? 状态) → 影响文件:行号 → 迁移行动" 三段式列出。

- **[BC-016] `unreal.EditorLevelLibrary` Python 绑定 — P1 confirmed (reviewer=msc)**
  影响:`query_tools.py:91-97`(`get_editor_world` / `get_game_world`)、`query_tools.py:145`(`new_level`)、`query_tools.py:205,346,583`(`get_all_level_actors` / `load_level`),以及 `write_tools.py` 内同名调用 + `ue_helpers.py:32,46,108,118,124`(`get_all_level_actors` / `get_editor_world` / `get_game_world`)。
  迁移行动:5.6 起 `unreal.EditorLevelLibrary.*` 标 deprecated → 替换为 `unreal.UnrealEditorSubsystem.get_editor_world()` / `unreal.LevelEditorSubsystem.load_level()` / `unreal.EditorActorSubsystem.get_all_level_actors()`;`ue_helpers.find_actor_by_path` / `find_actor_by_label` / `check_editor_ready` 三个函数是密集命中点,迁移时统一改 helpers 即可让上游 query/write 工具被动 fix。

- **[BC-017] `unreal.EditorAssetLibrary` Python 绑定 — P1 confirmed (reviewer=msc)**
  影响:`query_tools.py:346`(get_asset_metadata 中 `load_asset`)+ `write_tools.py` import_assets 链路对 `save_asset` / `load_blueprint_class` 的调用 + MCP `server.py` 多处(本 LLD 不直触)。
  迁移行动:5.6 起 deprecated → 替换为 `unreal.EditorAssetSubsystem.load_asset()` / `EditorAssetSubsystem.save_asset()` 等;迁移测试用 `python -c "import unreal; unreal.EditorAssetSubsystem.load_asset('/Game/...')"` 在 5.7 Editor Console 验证。

- **[BC-025] 硬编码 `UE_5.5` 引擎路径 — P1 confirmed (reviewer=msc)**
  影响:`uat_runner.py:_detect_run_uat_path()` 在 `engine_dir` 未传时回退到 `UE_ENGINE_DIR` 环境变量,本身不含 `UE_5.5` 硬编码;但调用方 `run_system_tests.py:18,727-730` 与 `start_ue_editor_*.ps1` 硬编码 `UE_5.5` 路径,会通过 `engine_dir` 参数透传进 UATRunner。
  迁移行动:本模块自身无需改动,但调用链上游的 `UE_5.5` 字面量必须批量替换 `UE_5.5` → `UE_5.7`(7 处),或统一抽到 `$env:UE_INSTALL_ROOT` 让 UATRunner 透明拾取。

- **[BC-019] RemoteControl HTTP 端点 `/remote/object/*` — P2 suspected (reviewer=pending-msc)**
  影响:`remote_control_client.py:2,14,30,104-140`(`call_function` / `get_property` / `set_property` / `batch` 全部依赖 PUT 到 `/remote/object/*` 与 `/remote/batch`)+ `query_tools.py:113,163,221,223,292,346,383,583`(通道 B 备用路径全调 RC)+ `bridge_core.py:60,199`(`call_cpp_plugin` 经 RC 反射调 Subsystem)。
  迁移行动:UE 5.6/5.7 release notes 未提及 endpoint 移除,**预期向后兼容**;但 5.7 新增 Preset HTTP API + Rundown Server,JSON 序列化形态有微调可能,需在 5.7 Editor 跑 `query_tools` 单元链 + `curl http://localhost:30010/remote/info` 验证。**严格 P2 suspected,5.7 实测后才能升级裁决**。

- **[BC-020] UAT `BuildCookRun -editortest` 调用形态 — P2 suspected (reviewer=pending-msc)**
  影响:`uat_runner.py:79-97`(`build_cook_run` 命令拼接)+ `uat_runner.py:99-125`(`run_automation_tests` 使用 `BuildCookRun -run -editortest -RunAutomationTest=`)+ `uat_runner.py:127-142`(`run_gauntlet`)+ `uat_runner.py:144-147`(`run_custom`)+ `uat_runner.py:167-210`(`_execute_uat` subprocess.run + Popen)+ `uat_runner.py:212-231`(`_detect_run_uat_path`)。
  迁移行动:UE 5.6/5.7 BuildCookRun 参数面预期向后兼容,legacy `RunUAT RunAutomationTests` 入口已被项目内部 `validate_no_legacy_automation_entrypoints.ps1` 主动禁用;5.7 实测可直接 `RunUAT BuildCookRun -editortest -RunAutomationTest=AgentBridge` 验证。

- **[BC-018] `unreal.*` 其他 binding(非 ESU 系列)— P2 suspected (reviewer=pending-msc)**
  影响:`query_tools.py:91-95`(`unreal.Paths.get_project_file_path` / `unreal.SystemLibrary.get_engine_version`)+ `ue_helpers.py` 范围内 `unreal.Actor` / `unreal.ActorComponent` 类型使用 + `write_tools.py` 对 `AssetToolsHelpers` / `MaterialFactoryNew` 等的调用。
  迁移行动:5.6 release notes 未见这些非 ESU 系列 binding 的 deprecation 提及,**大概率稳定**;5.7 实测跑 `python Plugins/AgentBridge/Tests/run_system_tests.py` 完整套件,若某个 `unreal.*` AttributeError 再单独定位。

### 迁移优先级与回归路径

按优先级排序:**P1 confirmed 三条(BC-016 / BC-017 / BC-025)是 5.7 Python 链路 functional 通过的必要条件**,必须先改;其中 BC-016/BC-017 集中在 `ue_helpers.py` + `query_tools.py` + `write_tools.py` 三个文件,改完跑 `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor` 看 Python 单测套件是否过门。**P2 suspected 三条(BC-019 / BC-020 / BC-018)严格留 5.7 实测裁决**,不在编译期就直接升 P1,这是 Task 1.1/1.2/1.5/1.6/1.7 的统一教训。回归路径:L1 query/write 走 `_dispatch` 通道 C 路径优先,L3 UI 走 `start_ui_operation` + `query_ui_operation` 异步原型;Mock 通道(`AGENTBRIDGE_MCP_CHANNEL=mock`)保留作为脱离 Editor 的回归基线。

---

**关联文件**: `Docs/design/HLD.md` §模块拓扑 / `Docs/requirements/SRS.md` §3.2 / `Docs/FEATURE_INVENTORY.md` F-BRG-01..09 / `Docs/contracts/tool_contract.md` §2-§4(L1/L3 协议) / `Docs/contracts/mcp_tools_catalog.md` F-MCP-01..05 / `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4 / `Plugins/AgentBridge/Schemas/feedback/` + `Schemas/write_feedback/`(F-BRG-03 反馈契约族 schema 索引)
