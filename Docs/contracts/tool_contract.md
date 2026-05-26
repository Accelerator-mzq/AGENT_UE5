# Tool Contract — L1/L2/L3 工具协议

> 版本: v1.0(从 <code>Plugins/AgentBridge/Docs/tool&#95;contract&#95;v0&#95;1.md</code> 抽取消化,旧文件已归 `Docs/archive/plugins/tool_contract_v0_1.md`)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1
> 关联 FEATURE_INVENTORY: Docs/FEATURE_INVENTORY.md F-BRG-* / F-MCP-* 族

本文是 AgentBridge 工具体系的契约定义。每个工具是对一个或多个 UE5 官方 API 的结构化封装,在 UE 原生 API 之上叠加参数校验、统一响应、错误码、Schema 对齐与读回闭环。所有工具返回值必须符合 `Plugins/AgentBridge/Schemas/` 中对应 JSON Schema。

## 1. 分层定义

Agent 在选择工具时必须按 **L1 > L2 > L3** 优先级,L3 仅在 L1 无对应 API 且操作可被 L1 读回时使用。

| 层级 | 名称 | 用途 | 输入约束 | 输出约束 | 失败行为 | 典型代表 | 证据源 |
|---|---|---|---|---|---|---|---|
| **L1** | 语义工具 | 项目状态查询 + 核心写入(actor / asset / level) | 稳定路径(`actor_path` / `asset_path` / `level_path`);写工具支持 `dry_run: true` | 必须可读回:写工具返回 `created_objects` / `modified_objects` / `deleted_objects` / `actual_*` / `dirty_assets` | 返回 `status=failed` + `errors[]`,不抛异常 | get_actor_state / spawn_actor / set_actor_transform / import_assets | Schemas/feedback/*, Schemas/write_feedback/* |
| **L2** | 编辑器服务工具 | 验证 / 构建 / 测试 / 保存 / Undo | 默认作用于当前编辑器上下文;UAT 类工具走外部进程 | 返回布尔结果 + 报告路径 + 计数(passed/failed/saved/...) | `build_success=false` / `failed_assets[]` 非空 / Undo 栈空时 `status=warning` | run_map_check / build_project / run_automation_tests / save_named_assets / undo_last_transaction | Schemas/common/, Artifacts/*.log |
| **L3** | UI 工具 | Detail Panel 点击 / 输入 / Viewport 拖拽,仅当 L1 无覆盖 | 必须显式 `execution_method: ui_tool`;统一走 `start_ui_operation` / `query_ui_operation` 异步壳 | 返回 `tool_layer="L3_UITool"` + `ui_idle_after` + `executed`;调用方必须接 L1 读回比对 | 与 L1 读回不一致 → `status=mismatch` + `mismatches[]` | click_detail_panel_button / type_in_detail_panel_field / drag_asset_to_viewport | AutomationDriverAdapter 日志 + L1 读回 |

L3 启用前提:L1 无对应 API + 操作可结构化 + 可通过 L1 验证 + 可逆或低风险 + Spec 显式标注 + 已封装为 AgentBridge 接口。

## 2. L1 语义工具

### 2.1 查询子族(只读、无风险)

| 工具名 | 目的 | UE5 依赖(摘要) | 关键返回字段 |
|---|---|---|---|
| `get_current_project_state` | 项目 + 编辑器上下文 | `FPaths` + `UKismetSystemLibrary::GetEngineVersion` + `UEditorLevelLibrary::GetEditorWorld` | `project_name` / `uproject_path` / `engine_version` / `current_level` / `editor_mode` |
| `list_level_actors` | 列出关卡 Actor | `UEditorLevelLibrary::GetAllLevelActors` | `actors[]`(每条含 `actor_name` / `actor_path` / `class`) |
| `get_actor_state` | 单 Actor 核心状态(transform/collision/tags) | `AActor::GetActorLocation/Rotation/Scale3D` + `UPrimitiveComponent` 碰撞 API + `AActor::Tags` | `transform` / `collision`(含 `collision_box_extent`)/ `tags` |
| `get_actor_bounds` | Actor 世界包围盒 | `AActor::GetActorBounds` → `FBoxSphereBounds` | `world_bounds_origin` + `world_bounds_extent` |
| `get_asset_metadata` | 单资产元数据 | `UEditorAssetLibrary::DoesAssetExist` + `FindAssetData` + `UStaticMesh::GetBoundingBox` | `exists` / `class` / `mesh_asset_bounds`(StaticMesh 时) |
| `get_dirty_assets` | 当前未保存 Package 列表 | `UEditorLoadingAndSavingUtils::GetDirtyContentPackages` | `dirty_assets[]` |
| `get_editor_log_tail` | 最近编辑器日志尾部 | `FOutputDevice` / Editor Log 系统 | `lines[]` |

### 2.2 写入子族(低/中风险、支持 dry_run、必须读回)

| 工具名 | 目的 | UE5 依赖(摘要) | 风险 | 读回闭环 |
|---|---|---|---|---|
| `import_assets` | 外部源导入到 `/Game/...` | `UAssetToolsHelpers::GetAssetTools` + `FAssetImportTask` | 低-中 | → `get_asset_metadata` → `get_dirty_assets` → `get_editor_log_tail` |
| `create_blueprint_child` | 从父类创建 Blueprint 子类 | `UBlueprintFactory` + `UAssetTools::CreateAsset` | 中 | → `get_asset_metadata`(确认 class)→ `get_dirty_assets` |
| `spawn_actor` | 在关卡生成 Actor | `UEditorLevelLibrary::SpawnActorFromClass` + `SetActorLabel` + `SetActorScale3D` | 中 | → `list_level_actors` → `get_actor_state` → `get_actor_bounds` → `get_dirty_assets` |
| `set_actor_transform` | 修改 Actor 位置/旋转/缩放 | `AActor::SetActorLocationAndRotation` + `SetActorScale3D` | 中 | 必须返回 `old_transform` + `actual_transform`;→ `get_actor_state` 二次确认 |
| `set_actor_collision`(Phase 2) | 修改碰撞配置 | `UPrimitiveComponent::SetCollisionProfileName` + `SetCollisionEnabled` + `UBoxComponent::SetBoxExtent` | 中 | → `get_actor_state`(collision 子字段) |
| `assign_material`(Phase 2) | 分配组件材质槽 | `UMeshComponent::SetMaterial` / `SetMaterialByName` | 中 | → `get_material_assignment` |

## 3. L2 编辑器服务工具

### 3.1 验证子族

| 工具名 | 目的 | UE5 依赖 | 通道 | 关键返回 |
|---|---|---|---|---|
| `run_map_check` | 运行内置 MAP CHECK | Editor `MAP CHECK` Console Command | A/C | `map_errors[]` / `map_warnings[]` |
| `validate_actor_inside_bounds`(Phase 2) | AABB 包含判定 | `AActor::GetActorBounds` + `FBox::IsInside` | A/B/C | `inside_bounds: bool` |
| `validate_actor_non_overlap`(Phase 2) | Actor 重叠检测 | `UWorld::OverlapMultiByChannel` / `UPrimitiveComponent::GetOverlappingActors` | A/B/C | `has_overlap: bool` / `overlaps[]` |
| `capture_viewport_screenshot` | 视口快照(产物采集,不自动判定) | `FViewport::ReadPixels` + `FImageUtils::PNGCompressImageArray` | C | `output_path` / `file_exists` / `file_size` |

### 3.2 构建 / 测试 / 保存 / 回滚子族

| 工具名 | 目的 | UE5 依赖 | 通道 | 关键返回 |
|---|---|---|---|---|
| `build_project` | 构建 Editor/Game Target | UAT `BuildCookRun` / `BuildTarget`(外部 C# 进程) | D | `build_success` / `build_log_path` |
| `run_automation_tests` | 跑 UE Automation Test Framework | `FAutomationTestBase` + Console `Automation RunTests`;CI 走 Commandlet 或 UAT `-editortest -RunAutomationTest` | A/C/D | `passed` / `failed` / `report_path` |
| `save_named_assets` | 保存指定脏资产(优先于 save_all) | `UEditorAssetLibrary::SaveLoadedAssets` / `UEditorLoadingAndSavingUtils::SavePackages` | A/B/C | `saved_assets[]` / `failed_assets[]` |
| `undo_last_transaction` | 远程触发 UE 原生 Undo | `GEditor->UndoTransaction()` | C | `requested_steps` / `undone_steps` / `fully_undone`;栈空 → `warning` |

> 注:legacy `RunUAT RunAutomationTests` 入口已被项目治理脚本禁用,统一改走 `BuildCookRun -editortest -RunAutomationTest=<Filter>`。

## 4. L3 UI 工具

异步任务壳契约:`start_ui_operation` 仅做参数校验 + 入队 + 立即返回 `operation_id`;`query_ui_operation` 轮询 `pending / running / success / failed`;终态后必须由调用方接 L1 读回。

| 工具名 | 目的 | UE5 依赖(执行后端) | 必备 L1 读回 |
|---|---|---|---|
| `click_detail_panel_button` | 点击 Detail Panel 按钮(`Add Component` / `Reset to Default` 等) | AutomationDriver(异步壳调度);Editor 官方按钮路径 | `get_actor_state` / `get_component_state` |
| `type_in_detail_panel_field` | 在属性输入框设值并显式提交(走 PostEditChangeProperty) | AutomationDriver(异步壳);属性行可编辑控件 | `get_actor_state`(属性值) |
| `drag_asset_to_viewport` | Content Browser → Viewport 拖拽(走 `DropObjectsAtCoordinates`,触发自动碰撞/命名/贴地) | Editor 官方 `DropObjectsAtCoordinates`(不裸鼠标) | `list_level_actors`(数量增加)+ `get_actor_state`(位置容差 100cm) |

**L3 → L1 交叉比对契约**:每次 L3 操作后通过 `CrossVerifyUIOperation(L3Response, L1VerifyFunc, L1VerifyParams)` 比对,返回 `FBridgeUIVerification { final_status, consistent, mismatches[] }`。一致 → `success`;不一致 → `mismatch` + 字段级 diff。

## 5. 调用约束

### 5.1 标准外壳

```json
{ "tool": "<name>", "args": { ... } }   // 请求
{ "status": "...", "summary": "...", "data": { ... }, "warnings": [], "errors": [] }   // 响应
```

### 5.2 执行通道枚举

| 通道 | 后端 | 适用 |
|---|---|---|
| A | Python Editor Scripting(`unreal` 模块) | 进程内调用 |
| B | Remote Control HTTP API | 远程,支持 `generateTransaction` |
| C | Commandlet / CLI / C++ Plugin 内部 | 无 GUI 批处理;L3 UI 工具专用通道 |
| D | UAT(`BuildCookRun` / `BuildTarget`) | 外部进程编排 |

### 5.3 同步 / 异步 / 超时 / Idempotency

| 维度 | 约束 |
|---|---|
| 同步 | L1 查询、L1 写、L2 验证、L2 保存 — 单次 RC 请求内完成 |
| 异步 | L3 UI 工具一律走 `start_ui_operation` / `query_ui_operation` 壳,避免 RC 同步链等 UI |
| 超时 | UAT 类(通道 D)由 `uat_runner` 显式 timeout 控制;L3 由 `query_ui_operation` 状态机超时 |
| Idempotency | 写工具同 `args` 重复调用应满足:dry_run=true 始终无副作用;dry_run=false 返回 `mismatch` 而非二次写入(由 `dirty_assets` + 读回判定) |
| Undo | 通道 B 走 `generateTransaction`;通道 C 走 `FScopedTransaction`;`undo_last_transaction` 是显式逆向 |

### 5.4 通用约束

- 禁止隐藏写:工具不得修改声明范围外对象;
- 稳定路径:返回标识统一用 `actor_path` / `asset_path` / `level_path`;
- 读回义务:所有写工具必须返回足够字段供 L1 二次验证;
- 中/高风险写工具必须支持 `dry_run: true`;
- L3 必须接 L1 交叉比对,不允许"声称成功就完事"。

## 6. 错误约定

### 6.1 status 枚举

| 值 | 含义 |
|---|---|
| `success` | 执行成功 + 验证通过 |
| `warning` | 执行成功但有非阻塞警告(如 Undo 栈空) |
| `failed` | 执行失败 |
| `mismatch` | 执行完成但读回值不符合预期(L3 交叉比对常用) |
| `validation_error` | 参数 / Spec 校验未通过,未执行 |

### 6.2 错误对象结构(`errors[]` 元素)

```json
{ "code": "ASSET_NOT_FOUND", "message": "...", "details": { ... } }
```

必填字段:`code`(SCREAMING_SNAKE_CASE)+ `message`;`details` 选填但应携带定位信息(asset_path / actor_path / property_name 等)。

### 6.3 错误码族

| 族 | 错误码 | 触发场景 |
|---|---|---|
| 输入族 | `INVALID_ARGS` / `VALIDATION_FAILED` / `DRY_RUN_REQUIRED` | args schema 未通过 / 中高风险未声明 dry_run |
| 寻址族 | `ASSET_NOT_FOUND` / `ACTOR_NOT_FOUND` / `LEVEL_NOT_FOUND` / `CLASS_NOT_FOUND` | 目标对象不存在 |
| 权限族 | `PROPERTY_NOT_ALLOWED` / `WRITE_SCOPE_EXCEEDED` | 越界写 / 不允许的属性 |
| 执行族 | `EDITOR_NOT_READY` / `BUILD_FAILED` / `SAVE_FAILED` / `READBACK_FAILED` | Editor 未就绪 / UAT 失败 / 保存失败 / 读回失败 |

### 6.4 传播规则

- 工具内部异常必须捕获并降级为 `status=failed` + `errors[]`,不允许向 Bridge 上抛栈;
- `warnings[]` 不阻断 success;`errors[]` 非空必须使 `status ∈ {failed, validation_error, mismatch}`;
- 编排层(Orchestrator / verifier)收到 `mismatch` 时按 Spec 决定是否标记任务失败,不擅自重试。

## 7. UE 5.7 Migration Notes

以下迁移记号来自 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`。**P1 confirmed**(reviewer=msc)条目需在 5.7 升级前直接下手;BC-019 是 **P2 suspected**(reviewer=pending-msc)但通道 B 全量受影响,故在本契约表列出供下游 LLD 关注,实际裁决留 5.7 实测阶段。每条标注影响层级 + 迁移行动。

P1 confirmed(必须迁移):

- **[UE57-BC-008] `EditorScriptingUtilities` Module Dependency**(P1 confirmed)→ 影响层级:**L1(查询/写)、L3(部分 UI 依赖)** → 迁移行动:`AgentBridge.Build.cs` / `AgentBridgeTests.Build.cs` / `AgentBridge.uplugin` 移除 `EditorScriptingUtilities` 私有依赖;调用迁到 `UEditorActorSubsystem` / `ULevelEditorSubsystem` / `UEditorAssetSubsystem`。5.6 已 deprecated,5.7 不保证保留模块。
- **[UE57-BC-016] `unreal.EditorLevelLibrary` (Python)**(P1 confirmed)→ 影响层级:**L1 查询(`list_level_actors` / `get_current_project_state`)+ L1 写(`spawn_actor` / `set_actor_transform`)** → 迁移行动:`MCP/server.py` + `Scripts/bridge/query_tools.py` + `write_tools.py` 中 `unreal.EditorLevelLibrary.*` 全部改为 `unreal.UnrealEditorSubsystem` / `unreal.LevelEditorSubsystem` / `unreal.EditorActorSubsystem`;调用面以 `get_editor_world` / `new_level` / `get_all_level_actors` / `load_level` / `get_game_world` 为重点。
- **[UE57-BC-017] `unreal.EditorAssetLibrary` (Python)**(P1 confirmed)→ 影响层级:**L1 写(`import_assets` / `create_blueprint_child`)+ L2 保存(`save_named_assets`)** → 迁移行动:`MCP/server.py` + `query_tools.py` 中 `load_asset` / `save_asset` / `load_blueprint_class` 改为 `unreal.EditorAssetSubsystem.*`;同时复核 `get_asset_metadata` 中 `DoesAssetExist` / `FindAssetData` 调用。

P2 suspected(高影响、待 5.7 实测裁决):

- **[UE57-BC-019] RemoteControl HTTP Endpoints (`/remote/object/call`, `/remote/object/property`, `/remote/batch`)**(P2 suspected, pending-msc)→ 影响层级:**L1/L2 通道 B 全部** → 迁移行动:5.7 实测验证 30010 端点保留性 + JSON 序列化形态;若 Field 字段名或 Property Path 解析规则有变,更新 `Scripts/bridge/remote_control_client.py` 的请求构造与 `query_tools.py` 注释中"UE5.5.4 下 ActorPath 走 /remote/object/property"口径;关注 5.7 新增 Preset HTTP API + Rundown Server 是否引入对现有调用的副作用。

补充关联 P1 confirmed 条目(影响 Build / 工程根,与 L1/L2 工具间接相关):

- **[UE57-BC-010] `IncludeOrderVersion = Unreal5_5`**(P1 confirmed)→ 影响层级:**Build(全部 C++ 工具)** → `Source/Mvpv4TestCodex.Target.cs:12` + `Source/Mvpv4TestCodexEditor.Target.cs:11` 改为 `Unreal5_6` 或 `Unreal5_7`。
- **[UE57-BC-012] `.uproject EngineAssociation "5.5"`**(P1 confirmed)→ 影响层级:**Build / Launcher** → `Mvpv4TestCodex.uproject:3` 改为 `"5.7"`。
- **[UE57-BC-025] 硬编码 `UE_5.5` 引擎路径**(P1 confirmed)→ 影响层级:**L2 build_project / run_automation_tests 入口脚本** → `run_system_tests.py` + `task14a_phase11_standalone_smoke.py` + `start_ue_editor_*.ps1` 共 7 处 `UE_5.5` 批量替换为 `UE_5.7`,或抽出到 `$env:UE_INSTALL_ROOT`。

其他 P2/P3 条目(BC-001/002/004/005/006/011/014/015/020/022/023 等)留 5.7 实测阶段裁决,本契约表暂不下决断。

### 7.1 迁移落点指引

按本契约文件的章节回看:

- **§2 L1 查询/写工具** 全部受 BC-016/017 影响,需在 5.7 编辑器内逐工具实测 `unreal.*Subsystem` 替代后的返回字段是否与现有 Schema 兼容;若字段名变更需同步更新 `Schemas/feedback/*` 与 `Schemas/write_feedback/*`。
- **§3 L2 验证/构建工具** 主要受 BC-008(C++ 编译期)+ BC-019(RC 通道 B)+ BC-025(脚本入口路径)影响,迁移顺序建议:先解 BC-010/012/025 让工程能在 5.7 下加载,再处理 BC-008 编译错误,最后实测 BC-019 端点行为。
- **§4 L3 UI 工具** 暂未发现 P1 confirmed 条目;但 BC-004(`FSlateApplication::Tick/SetCursorPos`)为 P2 suspected,L3 套件须在 5.7 重跑整套用例验证 Slate input 注入路径稳定性。
- **§5/§6 调用约束与错误约定** 与本次升级无直接耦合,但若 BC-019 引入新的 RC 错误形态,需在 `errors[]` 错误码族(§6.3)中补充新族(如 `RC_PROTOCOL_MISMATCH`)。
