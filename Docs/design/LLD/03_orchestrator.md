# LLD/03 — Orchestrator Python 详细设计

> 版本: v1 (2026-05-26)
> 范围: AgentBridge Plugin Orchestrator Python 层 11 个模块
> 上游: `Docs/design/HLD.md` §2/§3 + `Docs/requirements/SRS.md` §3.3 + `Docs/FEATURE_INVENTORY.md` F-ORC-01..08
> 契约: `Docs/contracts/tool_contract.md` §2 + `Docs/contracts/schemas_catalog.md`(reviewed_handoff / run_plan / planner_output)
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

本 LLD 覆盖 `Plugins/AgentBridge/Scripts/orchestrator/` 下 11 个 Python 模块(对应 `FEATURE_INVENTORY` F-ORC-01..08),它们共同承担 AgentBridge 框架"Python 侧执行编排层"的全部能力:对 MCP / CLI / 手工调用入口暴露**两条并行主链 —— Spec 主链(`orchestrator.run`)与 Handoff 主链(`handoff_runner.run_from_handoff`)**,前者按 YAML Spec 直接走 Plan → 执行 → 验证 → 报告闭环、后者按 Reviewed Handoff v3 走 Run Plan → 执行 → 报告 + snapshot/promotion 治理回填闭环。两条链共用 Bridge 通道枚举(`PYTHON_EDITOR` / `REMOTE_CONTROL` / `CPP_PLUGIN` / `MOCK`)与同一组 L1/L3 工具,但 Spec 主链 channel 走 `BridgeChannel` enum,Handoff 主链 channel 走 `bridge_mode` 字符串(`simulated` / `bridge_python` / `bridge_rc_api`),两套通道命名空间互不交叉。11 模块共 2491 行,统一通过 `safe_execute` 异常包装 + `make_response` 响应壳 + ProjectState/Reports 落盘三层收敛。本文档聚焦内部分层、关键函数签名、数据流与状态机、扩展点、已知约束与 UE 5.7 迁移变更点,目标是让接手者无需通读 2491 行就能精准定位修改点与评估成本。

## 2. 内部分层

| 模块 | 角色 | F-ORC ID | 文件 (行数) |
|---|---|---|---|
| `__init__.py` | 包入口(空模块标识) | — | `Plugins/AgentBridge/Scripts/orchestrator/__init__.py` (6) |
| `orchestrator.py` | Spec 主链主体:通道选择 + Plan 执行 + 验证 + 报告主循环 | F-ORC-01 | `Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py` (593) |
| `plan_generator.py` | Spec → Plan(CREATE/UPDATE/UI_TOOL/SKIP)对比 | F-ORC-02 | `Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py` (89) |
| `run_plan_builder.py` | Handoff → Run Plan(workflow_sequence + checkpoints) | F-ORC-02 | `Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py` (156) |
| `spec_reader.py` | YAML Spec 读取 + 标准化 + 深度校验 | F-ORC-03 | `Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py` (309) |
| `verifier.py` | 写后读回比对 + L1/L3 容差分桶 | F-ORC-04 | `Plugins/AgentBridge/Scripts/orchestrator/verifier.py` (241) |
| `report_generator.py` | Plan/执行/验证三元组 → 结构化报告 + 落盘 | F-ORC-05 | `Plugins/AgentBridge/Scripts/orchestrator/report_generator.py` (242) |
| `recovery_planner.py` | 治理域 → recovery policy 生成(回退到最小策略) | F-ORC-06 | `Plugins/AgentBridge/Scripts/orchestrator/recovery_planner.py` (57) |
| `handoff_runner.py` | Handoff 主链主体:Run Plan 执行 + snapshot/promotion 回填 | F-ORC-07 | `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` (581) |
| `validation_inserter.py` | qa_validation 域 → validation_checkpoints 插桩 | F-ORC-07 | `Plugins/AgentBridge/Scripts/orchestrator/validation_inserter.py` (49) |
| `forgeue_manifest_importer.py` | ForgeUE manifest.json + import_plan.json 桥接 | F-ORC-08 | `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py` (168) |

按职责自上而下分四层:**主入口层** `orchestrator.run` / `handoff_runner.run_from_handoff` 两条并行主入口,各持一条独立的状态机;**规划与读取层** `spec_reader` / `plan_generator` / `run_plan_builder` 把"用户输入"(YAML Spec / Reviewed Handoff)翻译为可执行单元(Plan / Run Plan);**验证与报告层** `verifier` / `report_generator` 对执行结果做结构化比对并落盘,`recovery_planner` / `validation_inserter` 通过 Skills/base_domains 模块在 Run Plan 上插治理脚手架;**扩展导入层** `forgeue_manifest_importer` 把外部资产工具链产物接入 Handoff 主链的 `import_assets` workflow,作为 F-ORC-08 单独的横向桥接点。`validation_inserter` 与 `recovery_planner` 都是 Handoff 主链专属、由 `run_plan_builder.build_run_plan_from_handoff` 单次调用,故本 LLD §3 将二者并入 handoff_runner 系列叙述。

## 3. 关键类/函数签名

> 仅列与外部协议、通道切换、状态机驱动、迁移强相关的函数,**不 dump 整文件**;完整方法表参见对应 `.py` 文件 `^def ` 抓取。每个签名后 1 行中文用途(<=20 字)。

### 3.1 `orchestrator.py`(F-ORC-01,Spec 主链)

```python
def run(spec_path: str, channel: BridgeChannel = BridgeChannel.CPP_PLUGIN, report_path: str | None = None) -> dict[str, Any]  # Spec 主链入口
def main(argv: list[str] | None = None) -> int  # CLI 入口,默认报告落 Saved/AgentBridge/orchestrator/
def _execute_plan_item(plan_item, target_level, channel, resolved_actor_paths) -> dict[str, Any]  # 单 Plan 条目执行→执行/验证双结果
def _execute_ui_tool(actor_spec, resolved_actor_paths) -> tuple[dict, str|None, dict|None]  # L3 调度 + L3→L1 交叉比对
def _verify_semantic_actor(actor_spec, actor_path, execution_result, channel) -> dict[str, Any]  # L1 写后读回校验(MOCK 走 spec 构造)
def _resolve_ui_actor_path(actor_path, resolved_actor_paths) -> str | None  # 解析 `@actor_id` 前序引用
def _build_failed_report(spec_path, reason, errors) -> dict[str, Any]  # 进入 Plan 前的失败兜底报告
```

### 3.2 `plan_generator.py` + `run_plan_builder.py`(F-ORC-02)

```python
# plan_generator.py
ACTION_CREATE = "CREATE"; ACTION_UPDATE = "UPDATE"; ACTION_SKIP = "SKIP"; ACTION_UI_TOOL = "UI_TOOL"  # Plan 动作枚举
def generate_plan(spec_actors: list[dict], existing_actors: list[dict]) -> list[dict[str, Any]]  # Spec ↔ 现状 diff → CREATE/UPDATE/UI_TOOL
def _index_existing_actors(existing_actors) -> dict[str, dict[str, Any]]  # 按 actor_name 建索引

# run_plan_builder.py
def build_run_plan_from_handoff(handoff: dict) -> dict[str, Any]  # Handoff → Run Plan(状态机入口)
def build_workflow_sequence(actors: list, mode: str) -> list[dict[str, Any]]  # actors → spawn_actor 步骤序列(线性依赖)
def _normalize_mode_token(mode: str) -> str  # handoff_mode → run_plan_id token
```

### 3.3 `spec_reader.py`(F-ORC-03)

```python
TOP_LEVEL_KEYS = ("spec_version","scene","defaults","layout","anchors","actors","validation")  # Spec 七顶层键
SUPPORTED_EXECUTION_METHODS = {"semantic","ui_tool"}  # Actor 执行方式
def read_spec(spec_path: str) -> dict[str, Any]  # YAML → 标准化 dict,缺 scene/actors 抛错
def validate_spec(spec: dict) -> tuple[bool, list[str]]  # 深度校验(scene_id / target_level=/Game/ / id 不重复 / transform 三元组)
def get_actors_by_execution_method(spec) -> dict[str, list[dict[str, Any]]]  # semantic/ui_tool 分组
def _validate_transform(transform, owner) -> list[str]  # location/rotation/relative_scale3d 三元校验
def _validate_ui_action(ui_action, owner) -> list[str]  # UI_ACTION_REQUIRED_FIELDS 表驱动
```

### 3.4 `verifier.py`(F-ORC-04)

```python
DEFAULT_TOLERANCES = {"location":0.01,"rotation":0.01,"relative_scale3d":0.001,"world_bounds_extent":1.0}  # L1 默认容差
L3_TOLERANCES = {"location":100.0}  # L3 UI 工具放宽容差(写后位置可能漂移)
def verify_transform(expected, actual, tolerances=None) -> dict[str, Any]  # 9 分量逐字段 abs(delta) 比对
def verify_actor_state(expected_spec, actual_response, execution_method="semantic") -> dict[str, Any]  # transform+class+collision 一次性校验
def _verify_collision(expected_collision, actual_collision) -> tuple[list[dict], list[str]]  # collision_profile + extent 校验
```

### 3.5 `report_generator.py`(F-ORC-05)

```python
def generate_report(spec_path, plan, execution_results, verification_results, dirty_assets=None, map_check=None) -> dict[str, Any]  # 三元组 → 结构化报告
def save_report(report, output_path: str) -> None  # 相对路径自动落 ProjectState/Reports/<YYYY-MM-DD>/
def format_summary(report) -> str  # 控制台单块文本摘要
def _compute_overall_status(actor_entries) -> str  # failed > mismatch > success/skipped 优先级
def _compute_actor_final_status(actor_entry) -> str  # 单 Actor exec/verify 合并
```

### 3.6 `recovery_planner.py`(F-ORC-06)

```python
def build_recovery_plan(handoff, workflow_sequence) -> dict[str, Any]  # 治理域 governance_module.build_recovery_policy 优先,缺省回退最小策略
# 最小策略:{policy_ref: "recovery.<game_type>.<mode>.minimal", policies: {on_step_failure:"rebuild_handoff", on_validation_failure:"manual_governance_review"}, blockers: [...]}
```

### 3.7 `handoff_runner.py` + `validation_inserter.py`(F-ORC-07)

```python
# handoff_runner.py
def run_from_handoff(handoff_path: str, report_output_dir: str=None, bridge_mode: str="simulated") -> dict[str, Any]  # Handoff 主链入口
def load_handoff(handoff_path: str) -> dict[str, Any]  # YAML/JSON 双格式读
def execute_run_plan(run_plan, bridge_mode="simulated") -> dict[str, Any]  # workflow_sequence 逐步分发
def execute_spawn_actor(params, bridge_mode) -> dict[str, Any]  # simulated / bridge_python / bridge_rc_api 三通道
def execute_post_spawn_actions(spawn_result, params, bridge_mode) -> list[dict[str, Any]]  # call_function 占位符解析
def execute_set_actor_transform(params, bridge_mode) -> dict[str, Any]  # 仅 simulated 已落地
def build_execution_report(handoff, run_plan, result) -> dict[str, Any]  # report_type=execution_report,含 promotion_status 占位
def save_execution_report(report, output_dir: str) -> str  # 默认目录自动加日期层
def _write_execution_snapshot_manifest(handoff, report, report_path) -> str  # 写最小 snapshot manifest
def _build_minimal_promotion_status(handoff, result, snapshot_ref) -> dict[str, Any]  # 治理域 governance_module 优先

# validation_inserter.py
def insert_validation_checkpoints(workflow_sequence, handoff) -> list[dict[str, Any]]  # qa_validation 域优先,缺省末尾插 actor_count_check
```

### 3.8 `forgeue_manifest_importer.py`(F-ORC-08)

```python
_SUPPORTED_BRIDGE_MODES = ("simulated","bridge_python","bridge_rc_api")  # 三通道枚举(独立于 Spec 主链 BridgeChannel)
def parse_manifest(manifest_path: str) -> dict[str, Any]  # schema_version=="1.0.0" 强制校验
def parse_import_plan(plan_path: str) -> dict[str, Any]  # operations[] 结构校验
def import_from_manifest(*, manifest_path, plan_path=None, bridge_mode="simulated") -> dict[str, Any]  # 主入口;simulated/bridge_python 全通,bridge_rc_api 外部入口 raise NotImplementedError(必须由 RC endpoint 触发)
# 5+1 种 asset_kind 内核 helper(2026-05-27 实现):
def _import_asset_by_kind(asset, manifest_root, overwrite_existing, *, bridge_mode) -> dict[str, Any]  # 真机 dispatch 内核(只在 UE Editor Python 环境调)
def _importer_path_texture / _importer_path_sound / _importer_path_mesh  # importer kinds: AssetTools.import_asset_tasks + Factory
def _creator_path_material / _creator_path_media  # creator kinds: AssetTools.create_asset + FactoryNew + 资产实例 set_editor_property
def main(argv: list[str] | None = None) -> int  # 独立 CLI:--manifest --plan --bridge-mode
```

## 4. 数据流与状态机

### 4.1 Spec 主链(Greenfield 模式,F-CHN-MODE-01)

```
CLI/MCP → orchestrator.run(spec_path, channel=CPP_PLUGIN)
  └─set_channel(CPP_PLUGIN)
  └─spec_reader.read_spec → validate_spec  # 失败 → _build_failed_report → return
  └─get_current_project_state() / list_level_actors(target_level)  # 失败 → 同上兜底
  └─plan_generator.generate_plan(spec.actors, current_actors)
      → [{action:CREATE|UPDATE|UI_TOOL, execution_method:semantic|ui_tool, ...}]
  └─for plan_item in plan:
       safe_execute(_execute_plan_item, timeout=30)
         ├─CREATE → write_tools.spawn_actor → _verify_semantic_actor(get_actor_state 读回)
         ├─UPDATE → write_tools.set_actor_transform → _verify_semantic_actor
         └─UI_TOOL → _execute_ui_tool(L3 dispatch + cross_verify_ui_operation L3→L1)
  └─get_dirty_assets() / run_map_check(target_level)
  └─report_generator.generate_report → save_report(report_path)
```

`resolved_actor_paths` 是流内 actor_id → actor_path 的解析缓存,UI_TOOL 步骤通过 `@actor_id` 语法引用前序 semantic 步骤创建的 Actor,这是单 Spec 内的"前向引用"机制。

### 4.2 Handoff 主链(Brownfield/Greenfield 通用,F-ORC-07)

```
handoff_runner.run_from_handoff(handoff_path, bridge_mode="bridge_rc_api")  # 示例传 bridge_rc_api;函数默认 "simulated"(见 handoff_runner.py:55)
  └─load_handoff (yaml/json)
  └─run_plan_builder.build_run_plan_from_handoff
       ├─build_workflow_sequence(actors)  # 线性依赖:第 i 步 depends_on=[第 0 步]
       ├─validation_inserter.insert_validation_checkpoints  # qa_validation 域插桩
       └─recovery_planner.build_recovery_plan  # planning_governance 域插桩
       → run_plan {status: "planned" | "failed"(有 blockers)}
  └─execute_run_plan(run_plan, bridge_mode)
       for step in workflow_sequence:
         ├─spawn_actor → execute_post_spawn_actions(call_function + __RUNTIME_CONFIG_REF__ 占位替换)
         ├─set_actor_transform(仅 simulated)
         └─import_assets → forgeue_manifest_importer.import_from_manifest
       → {status: succeeded | failed, step_results: [...]}
  └─build_execution_report → save_execution_report(自动加日期层)
  └─_write_execution_snapshot_manifest → snapshot_ref
  └─_build_minimal_promotion_status(governance 域 → promotion_status)
  └─_rewrite_execution_report(覆写补齐治理字段)
```

### 4.3 Handoff 执行状态机(F-ORC-07)

> **注**:下图状态命名(`Pending` / `Loaded` / `Planned` / `Running` / `Succeeded` / `Failed` / `Reported`)是 LLD 抽象,**源码中不存在对应 enum**。代码层仅有两个字段承载:`run_plan.status: "planned" | "failed"`(规划阶段)+ execution 结果 `status: "succeeded" | "failed"`(执行阶段)。LLD 状态名用于读者理解整体流程,grep 源码不会命中。


```
   ┌──────────┐  load_handoff  ┌──────────┐  build_run_plan  ┌────────┐
   │  Pending │ ────────────▶ │ Loaded   │ ───────────────▶│ Planned │
   └──────────┘                └──────────┘                  └────────┘
                                                                  │
                                       (planning_blockers != [])  │ status=planned
                                                ▼                  ▼
                                          ┌──────────┐       execute_run_plan
                                          │  Failed  │              │
                                          └──────────┘              ▼
                                                                ┌──────────┐
                                                                │ Running  │
                                                                └──────────┘
                                                                      │
                                            ┌──────── all step success ┴── any step fail ────────┐
                                            ▼                                                     ▼
                                       ┌──────────┐  snapshot+promotion  ┌──────────┐
                                       │Succeeded │ ──────────────────▶ │ Reported │
                                       └──────────┘                      └──────────┘
```

`planning_blockers` 在 `build_run_plan_from_handoff` 阶段就会让 run_plan.status 落 `failed`(典型触发:缺 base_domain_refs / 缺 validation_checkpoints / 缺 recovery_policy_ref),不进入 Running。

### 4.4 Recovery 状态机(F-ORC-06,最小回退路径)

```
Step Failure  ──── on_step_failure="rebuild_handoff" ────▶  返回上游 Compiler 重建 Handoff
                                                                    │
Validation Failure ── on_validation_failure="manual_governance_review" ▶  Escalate 到人工治理
```

当 `governance_module.build_recovery_policy` 可用(由 `governance_context.base_domain_refs` 触发 `load_base_domain_modules`)时,policy_ref 与 policies 由治理域决定;不可用则回退到上面两段式最小策略,policy_ref 命名为 `recovery.<game_type>.<mode>.minimal`。

### 4.5 ForgeUE manifest 导入(F-ORC-08)

```
forgeue_manifest_importer.import_from_manifest(manifest_path, plan_path, bridge_mode)
  ├─parse_manifest(强制 schema_version == "1.0.0")
  ├─parse_import_plan(可选,operations 必须是 list)
  └─bridge_mode dispatch:
      ├─simulated → 逐 asset _simulate_asset(无副作用,仅回 entry/artifact/kind/path)
      ├─bridge_python → 逐 asset _import_asset_by_kind 内核(UE Editor Python 环境内调 unreal.AssetTools)
      │     ├─texture/sprite_sheet → _importer_path_texture(import_asset_tasks + 后置 _apply_texture_properties on Texture2D 实例)
      │     ├─sound_wave → _importer_path_sound(SoundFactory 默认行为)
      │     ├─static_mesh → _importer_path_mesh(FBX/GLTF/OBJ dispatch;FbxImportUI 塞 AssetImportTask.options)
      │     ├─material → _creator_path_material(MaterialFactoryNew + MaterialEditingLibrary 4 expression PBR 五字段)
      │     └─file_media_source → _creator_path_media(FileMediaSourceFactoryNew + set file_path)
      └─bridge_rc_api → 外部入口 NotImplementedError("必须由 RC endpoint 触发");Editor 内 Content/Python/forgeue_rc_endpoint.py 的 PythonScripted UCLASS AgentBridgeForgeUEEndpoint 通过 RC HTTP 触发后调 bridge_python 通路
```

**真机 bridge 实现状态(2026-05-27 milestone)**:5+1 种 asset_kind helper 全部实现真机功能,bridge_python 直接在 UE Editor Python Console 触发;bridge_rc_api 通过 `Plugins/AgentBridge/Content/Python/forgeue_rc_endpoint.py` 注册 PythonScripted UCLASS `AgentBridgeForgeUEEndpoint`(`@unreal.uclass()` + `@unreal.ufunction(meta=dict(BlueprintCallable=""))`)+ `Content/Python/init_unreal.py` 自动加载 hook 实现 RC HTTP 远程触发。RC 调用真实路径 `/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint` + `import_assets_from_manifest`(snake_case)。L3 真机 smoke 6/6 PASS,evidence:`ProjectState/Reports/2026-05-27/forgeue_real_smoke/`。

被 `handoff_runner.execute_run_plan` 内 `workflow_type=="import_assets"` 分支直接 import 调用,这是 F-ORC-08 与 F-ORC-07 的唯一耦合点。

## 5. 扩展点

- **新增 Spec 执行方式**(在 semantic / ui_tool 之外):`spec_reader.SUPPORTED_EXECUTION_METHODS` 添加新值,`plan_generator` 增加新 `action`,`orchestrator._execute_plan_item` 增加新分支,`verifier.verify_actor_state` 的容差表 `L3_TOLERANCES` 旁补对应桶,`report_generator._extract_cross_verification` 决定是否保留交叉验证字段。
- **新增 Handoff bridge_mode**:`handoff_runner.execute_spawn_actor` / `execute_set_actor_transform` / `_execute_actor_function` 三处 if/elif 链同步扩,同时在 `forgeue_manifest_importer._SUPPORTED_BRIDGE_MODES` 追加新值(命名空间应保持一致,避免 simulated 在两套命名下含义漂移)。
- **新增 verifier 比对策略**:`verifier._VECTOR_COMPONENTS` 增加新向量字段(如 `velocity`),`_COLLISION_SCALAR_FIELDS` 增加新标量,`DEFAULT_TOLERANCES` 同步增容差键;高级策略(例如百分比容差、相对误差)需要新增 `verify_*` 函数族而非改 `verify_transform`。
- **新增 report 格式**:`report_generator.save_report` 默认输出 JSON,如需 markdown/HTML,新增 `render_report_markdown(report) -> str` 与 `save_report_markdown(report, path)`,不要污染 `generate_report` 的内部 dict 结构。
- **新增 transport 通道**(WebSocket/gRPC):透过 `BridgeChannel` enum 扩(由 bridge_core 提供),Orchestrator 侧只需在 `orchestrator.run` 的 `set_channel` 入参验收,不需要改主循环;Handoff 主链则需在 `handoff_runner.execute_*` 添加新 `bridge_mode` 分支。
- **新增治理域**:`recovery_planner` / `validation_inserter` / `handoff_runner._build_regression_summary` / `_build_minimal_promotion_status` 四处都通过 `load_base_domain_modules` + `hasattr` 探测可选治理函数,新治理域只要在 base_domains 实现对应 `build_recovery_policy` / `build_validation_checkpoints` / `build_regression_summary` / `build_promotion_status` 即可被自动拾取。

## 6. 已知约束与陷阱

- **handoff_runner 严格契约**:输入 Handoff 必须符合 Reviewed Handoff v3 schema(`Schemas/reviewed_handoff.schema.json` + `Schemas/reviewed_handoff_v2.schema.json` 双轨),`load_handoff` 不做 schema 校验,**违例字段会在 `build_run_plan_from_handoff` 阶段静默 default 空值**(如 `dynamic_spec_tree.scene_spec.actors=[]` 导致 workflow_sequence 为空 → planning_blockers 触发);上游 Compiler 必须先跑 `validation/test_handoff_schema.py` 才能落 approved/。
- **verifier 容差对齐 C++ 硬规则**:`DEFAULT_TOLERANCES.location=0.01` / `rotation=0.01` 对齐 `Docs/contracts/field_specification.md` §3 硬规则与 C++ `FBridgeTransform::NearlyEquals` 默认容差;**禁止在 verifier 单边放宽容差而不同步 C++** —— L3_TOLERANCES.location=100.0 是 UI 拖拽语义专属,只在 `execution_method=="ui_tool"` 时生效。
- **MOCK 通道下 verifier 走 spec 自构造**:`orchestrator._verify_semantic_actor` 在 `channel == BridgeChannel.MOCK` 时直接用 `_build_mock_actor_state(actor_spec, actor_path)` 构造读回值,而**不**调 `get_actor_state` —— 这是为了避免 generic example JSON 干扰流程级测试,但意味着 MOCK 通道下的 verify 永远是恒等比对,**不能用于验收**,只能用于 Orchestrator 流程自身的单元测试。
- **spec_reader 路径分隔符**:`_resolve_spec_path` 同时支持绝对路径与 `Specs/` 相对路径,Windows 反斜杠由 `pathlib.Path` 自然吸收;**但 `target_level` 必须以 `/Game/` 开头**(UE Asset Path 形态),这条规则 `validate_spec` 强制,违例会在 `validate_spec` 阶段早期失败。
- **safe_execute 在 Windows 上不支持超时**:`orchestrator._execute_plan_item` 用 `safe_execute(timeout=30)` 包裹,但 `bridge_core.safe_execute` 的 `signal.SIGALRM` 仅 Unix 可用 —— Windows 实测 timeout 失效,长卡顿步骤需要靠 C++ 端或 RC HTTP timeout 兜底,Orchestrator 不能假设 30s 一定回。
- **双轨证据落盘**:Spec 主链 report 落 `ProjectState/Reports/<YYYY-MM-DD>/`(走 `report_generator.save_report` + `get_dated_reports_dir`),Handoff 主链 execution_report + snapshot manifest 落 `ProjectState/Reports/<YYYY-MM-DD>/`(走 `handoff_runner.save_execution_report` + `get_dated_project_reports_dir`,**两个 helper 不同**,前者来自 bridge.project_config,后者来自同名但作用域为"项目级 reports"的 helper)。新增报告类型时必须先确认目标 helper 是 `dated_reports_dir` 还是 `dated_project_reports_dir`,搞反会让证据落到错误目录。
- **forgeue_manifest_importer 强校验 schema_version**:`parse_manifest` 硬断 `schema_version == "1.0.0"`,ForgeUE_codex 上游若往 2.x 演进必须**先**改本文件再升级 ForgeUE,这是上游版本与本桥接的硬耦合点。

## 7. UE 5.7 迁移变更点

> 引用 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 / §4(P1 7 条裁决:1 false-positive + 6 confirmed;P2/P3 全部 suspected,留 5.7 实测裁决)。**P1 confirmed 范围严格限于 msc 已裁决条目**,其余按 P2/P3 标 suspected;**BC-019 严格 P2 suspected 不升级**(Task 1.1/1.2/1.5/1.6/1.7/1.8 教训)。每条按 "[BC-NNN] api_or_key (P? 状态) → 影响 → 迁移行动" 三段式列出。

- **[BC-008] EditorScriptingUtilities 模块依赖 — P1 confirmed (reviewer=msc)**
  影响:Orchestrator 自身不直依赖该模块,但 Spec 主链经 `bridge.write_tools` / `bridge.query_tools` 调到 C++ Subsystem,Subsystem 内部经 `AgentBridge.Build.cs` 链到 EditorScriptingUtilities;链路上的 `orchestrator._execute_plan_item` → `spawn_actor` / `set_actor_transform` / `get_actor_state` 全部命中。
  迁移行动:本模块自身无改动,但跑 Spec 主链 e2e 验证前必须先解决 BC-008(Build.cs PrivateDeps 替换 / Subsystem 迁移到 `UEditorActorSubsystem`),否则 `bridge_python` / `bridge_rc_api` 通道一律 fail。

- **[BC-015] Config Layer 综合 — P2 suspected (reviewer=pending-msc)**
  影响:Orchestrator 自身不直读 Config,但 `bridge.project_config.get_project_root` 通过 `.uproject` 上溯 + env `UE_PROJECT_ROOT` 解析,Orchestrator 的 `spec_reader._resolve_spec_path` / `report_generator.save_report` / `handoff_runner.save_execution_report` 均依赖该 helper。
  迁移行动:5.7 Editor 实测打开工程看 Config 加载警告;若某 ini 节被废弃,大概率是 `DefaultEngine.ini` 的 Renderer 段,Orchestrator 路径解析逻辑不受影响。**严格 P2 suspected**。

- **[BC-019] RemoteControl HTTP 端点 `/remote/object/*` — P2 suspected (reviewer=pending-msc)**
  影响:Spec 主链通道 B(REMOTE_CONTROL)+ Handoff 主链 `bridge_mode="bridge_rc_api"` 全部经 `bridge.remote_control_client` 走 RC HTTP;`handoff_runner.execute_spawn_actor` 的 bridge_rc_api 分支显式拼 `object_path=/Script/AgentBridge.Default__AgentBridgeSubsystem` + `function_name=SpawnActor` + RC `call_function`,`_normalize_rc_call_response` 处理 `ReturnValue` + `data.JsonString` 双层包。
  迁移行动:UE 5.6/5.7 release notes 未提及 endpoint 移除,**预期向后兼容**;5.7 新增 Preset HTTP API + Rundown Server 可能引入 JSON 形态微调,迁移后需在 5.7 Editor 跑 `handoff_runner` 的 bridge_rc_api 链单元 + `curl http://localhost:30010/remote/info` 健康探测。**严格 P2 suspected,5.7 实测后才升级裁决**(Task 1.1/1.2/1.5/1.6/1.7/1.8 统一教训)。

- **[BC-020] UAT `BuildCookRun -editortest` 调用形态 — P2 suspected (reviewer=pending-msc)**
  影响:Orchestrator 自身不直接 spawn UAT,但 Handoff 主链 + Spec 主链的"系统测试 / Gauntlet 验收"链路通过外层 `run_system_tests.py` → `bridge.uat_runner` → `BuildCookRun -editortest -RunAutomationTest=AgentBridge` 触发;失败时 `recovery_planner` 的 `on_validation_failure="manual_governance_review"` 兜底。
  迁移行动:UE 5.6/5.7 BuildCookRun 参数面预期向后兼容,legacy `RunUAT RunAutomationTests` 已被 `validate_no_legacy_automation_entrypoints.ps1` 主动禁用;5.7 实测可直接 `RunUAT BuildCookRun -editortest -RunAutomationTest=AgentBridge`。**严格 P2 suspected**。

- **[BC-021] `validate_no_legacy_automation_entrypoints.ps1` token 检测 — P2 suspected (reviewer=pending-msc)**
  影响:该治理脚本对 Orchestrator 间接生效 —— 若新增 Handoff workflow_type 用 legacy `RunAutomationTests`,会被该检测器 fail,导致 `recovery_planner` 的 `planning_blockers` 路径触发;Orchestrator 不直读它,但 ChangeSet level Validation 会拦。
  迁移行动:检测器是项目内部治理,不受 UE 升级影响;若 5.7 BuildCookRun 参数名变化,需同步该脚本的 Suggestion 文案。**严格 P2 suspected**。

- **[BC-025] 硬编码 `UE_5.5` 引擎路径 — P1 confirmed (reviewer=msc)**
  影响:Orchestrator 自身不含 `UE_5.5` 字面量,但被 `run_system_tests.py:18,727-730` + `start_ue_editor_*.ps1:3,104-105` 七处硬编码路径通过 `engine_dir` 参数透传到 `bridge.uat_runner.UATRunner`,进而影响 Handoff 主链 + Spec 主链的 UAT 执行链。
  迁移行动:本模块自身无需改动,但调用链上游的 7 处 `UE_5.5` 字面量须批量替换 `UE_5.5` → `UE_5.7`,或抽到 `$env:UE_INSTALL_ROOT` 让 UATRunner 透明拾取。

### 迁移优先级与回归路径

按优先级排序:**P1 confirmed 两条(BC-008 / BC-025)是 5.7 Orchestrator 跑通 e2e 的必要条件**,前者影响 Subsystem 调用链(Spec 主链 + Handoff 主链 bridge_python/bridge_rc_api 全链),后者影响 UAT 系统测试入口;**P2 suspected 四条(BC-015 / BC-019 / BC-020 / BC-021)严格留 5.7 实测裁决**,不在编译期就直接升 P1。回归路径:Spec 主链先跑 `python Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py <spec.yaml> --channel mock` 看流程闭合,再切 `--channel cpp_plugin` 看真实通道;Handoff 主链先跑 `python -c "from orchestrator.handoff_runner import run_from_handoff; run_from_handoff('<handoff.yaml>', bridge_mode='simulated')"` 看 simulated 通路,再切 `bridge_rc_api`。MOCK / simulated 通道保留作为脱离 Editor 的回归基线。

---

**关联文件**: `Docs/design/HLD.md` §2/§3 / `Docs/requirements/SRS.md` §3.3 / `Docs/FEATURE_INVENTORY.md` F-ORC-01..08 / `Docs/contracts/tool_contract.md` §2 / `Docs/contracts/schemas_catalog.md`(reviewed_handoff / run_plan / planner_output)/ `Docs/contracts/field_specification.md` §3(verifier 容差硬规则)/ `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4 / `Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json` + `Schemas/run_plan.schema.json` + `Schemas/planner_output.schema.json`
