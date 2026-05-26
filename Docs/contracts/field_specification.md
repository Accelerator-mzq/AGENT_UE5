# Field Specification — 共享字段规范

> 版本: v1.0(从 Plugins/AgentBridge/Docs/field_specification_v0_1.md 抽取消化)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1
> 关联 FEATURE_INVENTORY: Docs/FEATURE_INVENTORY.md F-SCH-03(共享基础 Schema 族)

本文规范"用户需求 → 设计文档 → Agent 执行"链路上每一层允许出现的字段。原则:用户层可保留语义抽象,设计层负责消歧义,执行层只允许明确、单义、可校验、可读回的字段名,且字段名直接映射自 UE5 C++ API 属性名(不另立翻译层)。

字段分三层:用户语义层(模糊词表)、设计规范层(已消歧的 Spec 结构)、执行技术层(机器稳定操作)。本文档表格主要约束执行技术层,设计层/用户层只作映射来源说明。

## 1. 共享字段类型(transform / bounds / collision / material 等)

执行技术层字段按语义族组织。每个族对应 Plugins/AgentBridge/Schemas/common/ 下一份 Schema,字段名 = UE5 C++ API 属性名(C++ Plugin 在 `BridgeTypes.h` 以 USTRUCT 实现)。

| 字段族 | 关键字段 | 单位 / 格式 | UE5 C++ 源 | Schema 文件 | 引用方(Schema / 工具) |
|---|---|---|---|---|---|
| Transform | `location` `[x,y,z]` / `rotation` `[pitch,yaw,roll]` / `relative_scale3d` `[x,y,z]` | cm / degrees / 倍率 | `AActor::GetActorLocation` / `GetActorRotation` / `GetActorScale3D` | `common/transform.schema.json` | `spawn_actor` / `set_actor_transform` / `get_actor_state` |
| Bounds | `world_bounds_origin` / `world_bounds_extent` / `mesh_asset_bounds` | cm(extent 为半径) | `AActor::GetActorBounds` + `UStaticMesh::GetBoundingBox` | `common/bounds.schema.json` | `get_actor_bounds` / `get_asset_metadata` |
| Collision | `collision_enabled` / `collision_profile_name` / `collision_box_extent` / `collision_capsule_radius` / `collision_capsule_half_height` / `generate_overlap_events` / `can_affect_navigation` | string / FName / cm(half-extent) / bool | `UPrimitiveComponent::GetCollisionEnabled` / `GetCollisionProfileName` / `UBoxComponent::GetUnscaledBoxExtent` | `common/collision.schema.json` | `get_actor_state` / `set_actor_collision` |
| Material | `material_slot_assignment.{component_name, slot_name, material_path}` / `material_readback.*` | string(资产路径)/ FName | `UMeshComponent::SetMaterial` / `SetMaterialByName` | `common/material.schema.json` | `assign_material` / `get_material_assignment` |
| Object Identity | `id` / `class` / `object_type` / `target_level` / `package_path` | 文档内唯一 ID / UE 类路径 / "actor\|asset" / `/Game/Maps/...` / `/Game/...` | UE 资产管理器 + Level Editor | `common/primitives.schema.json` | 全部 L1 写工具(必填) |
| Error / Status | `status` ∈ `{success,warning,failed,mismatch,validation_error}` / `summary` / `warnings[]` / `errors[]` | enum / string / 数组 | n/a(框架自定) | `common/error.schema.json` | 全部 L1/L2 工具反馈外壳 |
| Mesh / Component | `static_mesh` / `skeletal_mesh` / `component_name` / `component_class` / `attach_parent` / `relative_location` / `relative_rotation` / `relative_scale3d` | 资产路径 / FName / FName | `UStaticMeshComponent` / `USkeletalMeshComponent` + `USceneComponent::AttachToComponent` | 嵌入各工具 schema(无独立 common 文件) | `spawn_actor` / `set_actor_transform`(组件级) |
| Navigation | `can_affect_navigation` / `nav_obstacle` / `walkable_path_width` | bool / bool / cm | `UPrimitiveComponent::CanEverAffectNavigation` | 嵌入 collision.schema.json | `get_actor_state` |

容差比对统一走 `FBridgeTransform::NearlyEquals(Other, LocationTol, RotationTol, ScaleTol)`,**不允许** Python verifier 自建比对逻辑。Lighting / Camera 字段为后续扩展,本版仅在 `capture_viewport_screenshot` 的 camera 参数中允许出现。

## 2. 命名规范(GDD-First + UE5 路径)

字段名一律使用 snake_case;路径使用 UE5 标准格式。三层分别允许的命名:

| 领域 | 规则 | 合规示例 | 反例(禁止) |
|---|---|---|---|
| 字段命名风格 | snake_case;字段名等于 UE5 API 属性名转 snake_case;不引入翻译别名 | `relative_scale3d` / `collision_profile_name` / `world_bounds_extent` | `RelativeScale3D`(驼峰)/ `scale`(简写)/ `cb_extent`(缩写) |
| C++ 类型命名 | UE 引擎 PascalCase + `F`/`U`/`A` 前缀;Schema 用 snake_case,但 UE5 C++ 源(`BridgeTypes.h`)保留 PascalCase | `FBridgeTransform` / `FBridgeReply` / `UAgentBridgeSubsystem` | `bridge_transform`(snake)/ `FBT`(简写) |
| 单义性 | 一个字段只表达一种含义,模糊词不进入执行层 | `relative_scale3d` 表缩放 / `world_bounds_extent` 表占地 | `size`(可能指缩放/占地/碰撞)/ `position`(与 location 混淆)/ `center`(与 origin 混淆) |
| 单位约定 | 长度统一 cm;角度统一 degrees;缩放统一倍率;extent 表半径(half-extent) | `location: [452.0, -298.0, 0.0]` cm / `rotation: [0,15,0]` deg | `location_m: 4.52`(米)/ `rotation_rad`(弧度) |
| 关卡路径 | `/Game/Maps/<Name>.<Name>:PersistentLevel.<actor_label>` | `/Game/Maps/TestMap.TestMap:PersistentLevel.crate_cluster_a` | `TestMap.crate_a`(缺前缀)/ Windows 物理路径 |
| 资产路径 | `/Game/<Category>/<Sub>/<AssetName>.<AssetName>` 或不带后缀的对象路径 | `/Game/Meshes/SM_Crate` / `/Game/Materials/M_Crate.M_Crate` | `Content/Meshes/SM_Crate.uasset`(物理路径)/ `SM_Crate`(无 `/Game/`) |
| 用户语义层词表 | 必须落在受控枚举:placement / size_profile / density / facing 各自的固定词集 | `size_profile: large` / `placement: center_of_room` | `big` / `proper` / `a bit left`(自由文本) |
| 设计层 → 执行层映射 | 默认规则必须落 `defaults:` 段(`size_profile_to_scale` / `density_to_spacing`),执行时不发明 | `size_profile_to_scale.large = [1.25,1.25,1.25]` | 临时拍脑袋 `scale: [1.2,1.2,1.2]` |
| 相对/世界坐标 | 世界为默认;组件级必须显式 `relative_*` 前缀 | `relative_location` / `relative_rotation` / `relative_scale3d` | 同名 `location` 既当世界又当相对 |

## 3. Schema 规则(版本化、扩展性、严格校验)

Schema 是字段规范的机器可读形式。校验入口分布在 Bridge / Compiler / validation 工具链。

| 规则 | 强制度 | 校验入口 | 失败行为 |
|---|---|---|---|
| 所有 `common/*.schema.json` 必须 jsonschema draft-07 + `additionalProperties:false` | 必须 | `Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` | 任一示例不符 → 退出码非 0,阻断 commit |
| 执行层字段必须显式列入对应 schema(transform/bounds/collision/material/primitives/error 六族) | 必须 | `validate_examples.py` + 各工具 schema `$ref` 引用 common/ | 字段未注册 → schema validation error,工具拒绝执行 |
| 数值字段使用三元数组 `[x,y,z]`(transform/bounds);不允许标量缩写 | 必须 | transform.schema.json + bounds.schema.json `minItems:3 maxItems:3` | 标量或长度错 → schema 报错 |
| 禁止字段名清单(`size` / `position` / `center` / `big` / `small` / `proper` / `near` / `far` 等)不得作为字段名或自由文本值进入执行层 | 必须 | Compiler 静态检查 + Schema `additionalProperties:false` 阻断 | 命中 → Clarification Gate 触发追问或阻断 |
| 写操作返回值必须含写后读回(`actual_transform` / `actual_bounds` / `actual_collision`) | 必须 | `Schemas/write_feedback/*` + Bridge 自动附带读回 | 缺失 → `status=validation_error` |
| 容差比对走 C++ `FBridgeTransform::NearlyEquals`,Python 端只调不实现 | 必须 | Bridge 调用 C++ USTRUCT,不再用 verifier.py 自建 | Python 自建比对 → code review 拒收 |
| Schema 版本化:每份 schema 在 `$id` 中标版本,破坏性变更升大版本(如 `reviewed_handoff_v2.schema.json`) | 必须 | `validate_examples.py --strict` + reviewed_handoff_v2 已是先例 | 旧版本生产数据 → 用 reviewed_handoff.schema.json 校验保留兼容路径 |
| 扩展字段(Lighting / Camera / 其他后续族)必须先进 schema 再被工具使用,不允许"先用后补" | 必须 | Code Review + commit pre-merge schema check | 工具引用未注册字段 → CI 阻断 |
| 默认规则(`size_profile_to_scale` / `density_to_spacing`)必须写入 spec / handoff,不允许执行时临时发明 | 必须 | Compiler Clarification Gate(`Plugins/AgentBridge/Scripts/compiler/`) | 缺失默认 → 触发澄清,阻断执行 |
| 缺失即阻断:关键字段无法唯一确定 → 触发追问 / 用已声明默认 / 阻断 | 必须 | Clarification Gate + Bridge 入参校验 | 模糊位置 / 多候选锚点 / 互相矛盾约束 → `status=validation_error` + 补全提示 |

## 4. 字段引用追踪

同一字段在多个 Schema / 工具 / C++ 结构体中出现时,必须保持完全一致(字段名、类型、单位、数组长度)。本表跟踪关键字段的全部出现位置,作为重命名 / 单位变更 / 类型升级的影响面参考。

| 字段 | 出现位置 | 一致性要求 |
|---|---|---|
| `location` | `common/transform.schema.json` / `set_actor_transform` 入参 / `spawn_actor` 入参 / `actual_transform` 返回 / C++ `FBridgeTransform::Location` / Python `query_tools.py` ActorPath 读回(RC `/remote/object/property`) | 全部 `[float,float,float]`(长度 3)+ 单位 cm + 世界坐标(组件级用 `relative_location`) |
| `rotation` | `common/transform.schema.json` / `set_actor_transform` / `spawn_actor` / `actual_transform` / C++ `FBridgeTransform::Rotation` | 顺序固定 `[pitch, yaw, roll]` + 单位 degrees;**禁止**改为 `[yaw, pitch, roll]` 或弧度 |
| `relative_scale3d` | `common/transform.schema.json` / 全部 transform 工具 / C++ `FBridgeTransform::RelativeScale3D` / 组件级 `attach_parent` 上下文 | 倍率值(1.0 = 原始);设计层 `size_profile` 必须先映射成此字段才能进执行层 |
| `world_bounds_origin` / `world_bounds_extent` | `common/bounds.schema.json` / `get_actor_bounds` 返回 / `actual_bounds` 返回 / spec `placement_rule` 占地计算输入 | 单位 cm;`extent` 永远是 half-extent(半径),不是直径 |
| `collision_box_extent` / `collision_capsule_radius` / `collision_capsule_half_height` | `common/collision.schema.json` / `get_actor_state.collision` / `set_actor_collision` 入参 | 单位 cm + half-extent;仅在对应组件类(BoxComponent / CapsuleComponent)时出现,跨组件不复用 |
| `collision_profile_name` / `collision_enabled` | `common/collision.schema.json` / `get_actor_state.collision` / `set_actor_collision` / C++ `UPrimitiveComponent` 调用 | FName 字符串(如 `BlockAll`)/ `ECollisionEnabled` enum 字符串;UE5 内置预设名必须照抄 |
| `can_affect_navigation` | `common/collision.schema.json` / nav 子段 / `get_actor_state` | bool;`nav_obstacle` 是衍生字段,不与本字段同名 |
| `status` | `common/error.schema.json` / 全部 L1/L2 工具反馈外壳 | enum `{success, warning, failed, mismatch, validation_error}`,不允许新增值未注册到 error.schema.json |
| `dirty_assets` | `feedback/*` / 写工具返回 / `get_dirty_assets` 返回 / `UEditorLoadingAndSavingUtils::GetDirtyContentPackages` Python 绑定 | 字符串数组,元素为 Package 路径(`/Game/Maps/TestMap`),无 `.uasset` 后缀 |
| `actor_path` | `feedback/*.created_objects[]` / `list_level_actors` 返回 / `get_actor_state` 入参 / RC HTTP `/remote/object/property` 入参 | 完整 LevelStreaming 路径 `/Game/Maps/<Name>.<Name>:PersistentLevel.<label>`;**禁止**简写 |
| `package_path` / `asset_path` | `feedback/*` / `get_asset_metadata` / `import_assets` / `create_blueprint_child` | `/Game/...` 开头的对象路径;不允许文件系统物理路径 |

## 5. UE 5.7 Migration Notes

UE 5.5.4 → 5.7 升级中,与字段命名 / Schema / 资产路径直接相关的 breaking change 已在 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 登记。下表列出对本规范有影响的条目,标注 P1 confirmed / P2 suspected 来源。

| BC ID | 影响面 | 对本规范的具体后果 | 标签 |
|---|---|---|---|
| UE57-BC-008 | `EditorScriptingUtilities` 模块 5.6 已 deprecated,5.7 可能完全移除;影响 `AgentBridge.Build.cs` PrivateDeps | C++ 端访问 `world_bounds_*` / `actual_transform` 读回路径如果绕道 EditorScriptingUtilities 需迁到 `UEditorActorSubsystem` / `ULevelEditorSubsystem`,**字段名本身不变**,但 schema 字段的"读回入口"注释段需要刷新 | (P1 confirmed, reviewer=msc) |
| UE57-BC-016 | `unreal.EditorLevelLibrary` Python binding 5.6 deprecated → `unreal.UnrealEditorSubsystem` / `LevelEditorSubsystem` / `EditorActorSubsystem` | `actor_path` / `location` / `rotation` 在 Python 侧的取值入口从 `EditorLevelLibrary.get_all_level_actors` 等迁移到 Subsystem;字段名不变,但本规范 §4 "出现位置"列中 Python 调用点的方法名要在 5.7 适配时同步刷新 | (P1 confirmed, reviewer=msc) |
| UE57-BC-017 | `unreal.EditorAssetLibrary` 5.6 deprecated → `unreal.EditorAssetSubsystem`;影响 `load_asset` / `save_asset` / `load_blueprint_class` | `package_path` / `asset_path` 字段值格式不变(仍 `/Game/...`),但读 / 写 / save 的 Python 入口要替换;**返回结构若 5.7 改 field 命名**(例如 `does_asset_exist` 的返回 struct),需要 §4 引用追踪表增列 | (P1 confirmed, reviewer=msc) |
| UE57-BC-019 | Remote Control HTTP API(`/remote/object/call` / `/remote/object/property` / `/remote/batch`)5.6→5.7 端点预期保留,但 JSON 序列化形态(Field 名 / Property Path 解析规则)可能变 | 若 5.7 改 Property Path 解析(例如 `RelativeLocation` → `relative_location` 或反过来),`location` / `rotation` / `relative_scale3d` 通过 RC HTTP 读回的 Property Path 字符串要同步更新,**但 Schema 字段名不变**(本规范要求 snake_case,Schema 不跟 UE C++ PascalCase 走) | (P2 suspected, reviewer=pending-msc) |
| UE57-BC-022 | `.uproject` Plugins[] 字段:`ModelingToolsEditorMode` + `RemoteControlWebInterface`(含 5.4 时代 `MarketplaceURL`) | 不直接影响 Schema 字段名,但 `.uproject` 字段结构是项目级字段规范的延伸;5.7 若移除 `MarketplaceURL` 写法,需在本规范追加 ".uproject 插件入口字段约定"子节(本版未覆盖) | (P2 suspected, reviewer=pending-msc) |
| UE57-BC-015 | Config Layer(`Default*.ini`)5.5→5.7 无明显 breaking key,但 5.7 Editor 加载时可能 warning 个别废弃节 | 与字段规范交集小;仅当 ini key 被字段引用(例如 `EnhancedInput` 默认类路径被 spec 引用为 `class` 字段值)时才需要在 §4 表中追列 | (P2 suspected, reviewer=pending-msc) |

**迁移落地原则**:本规范的字段名(snake_case)不跟随 UE5 C++ API 改名同步变;只有当 schema 自身需要重命名 / 拆字段 / 改类型时,才升级 schema 版本号(参考 `reviewed_handoff_v2.schema.json` 先例)。Python / C++ 读回入口变更属于"实现层适配",在工具实现里改,不污染本规范。
