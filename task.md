# AGENT + UE5 可操作层 — 编码 Agent 任务清单

> 目标引擎版本：UE5.5.4 | 文档版本：v0.3
> 架构：C++ Editor Plugin 核心 + Python 轻量客户端 + 三层受控工具体系（L1 语义 > L2 服务 > L3 UI）+ 10 个 UE5 官方模块全部实装

---

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent
2. 每个 TASK 内附「先读这些文件」列表——编码 Agent 应在动手前先读完
3. 每个 TASK 末尾有【验收标准】——全部通过才可进入下一个 TASK
4. 标注 [UE5 环境] 需要 UE5.5.4 Editor 运行；[C++ 编译] 需要 VS2022/Xcode/clang
5. 未标注的任务可在纯 Python 环境中完成

## 任务总览

阶段 1 基础（01-02）> 阶段 2 C++ Plugin 核心（03-06）> 阶段 3 UE5 原生测试（07-08）> 阶段 4 Python+Orchestrator（09-14）> 阶段 5 高级验证+CI/CD（15-18）> 阶段 6 集成（19-20）

## 核心架构

C++ Plugin 是"权威实现"。Python 是"客户端"。测试用 UE5 Automation Test。CI/CD 用 Gauntlet。三通道：A=Python / B=RC API / C=C++ Plugin（推荐）。

三层受控工具体系：
- **L1 语义工具**（默认主干）：C++ API 直接操作引擎对象，确定性最高
- **L2 编辑器服务工具**：构建/测试/验证/截图等工程服务
- **L3 UI 工具**（仅 fallback）：Automation Driver 模拟 UI 输入，仅当 L1 无能力时使用，操作后必须通过 L1 做独立读回交叉比对
---
---

# 阶段 1：基础

---

## TASK 01：初始化项目目录结构

```
目标：将 v0.3 交付包解压到项目根目录，确认全部 76 个文件就位且目录结构正确。

前置依赖：无

先读这些文件：
- README.md（§1-2：项目定位 + 三层受控工具体系概述）
- AGENTS.md（§1-5：Agent 规则 + 工具分层 + 非目标清单）
读完应掌握：本项目做什么（受控工具调用）、不做什么（无边界 GUI 自动化）、三层体系 L1>L2>L3

Step 1: 解压 v0.3 交付包到项目根目录

Step 2: 确认以下目录结构完整

  ProjectRoot/
  ├── AGENTS.md                            ← Agent 规则文档
  ├── README.md                            ← 项目说明
  ├── task.md                              ← 本文件（编码 Agent 任务清单）
  │
  ├── Docs/                                ← 11 个设计文档
  │   ├── architecture_overview.md         ← 系统架构全图（三层体系 + 10 模块 + 通道架构）
  │   ├── bridge_implementation_plan.md    ← Bridge 实现方案（L1-L3 接口总表 + Transaction）
  │   ├── bridge_verification_and_error_handling.md ← 错误码映射 + 边界条件 + L3 错误码
  │   ├── feedback_interface_catalog.md    ← 反馈接口清单（A1-A8 + B1-B7 + D1-D4）
  │   ├── feedback_write_mapping.md        ← 写-读闭环映射关系
  │   ├── field_specification_v0_1.md      ← 字段规范（transform/collision/bounds）
  │   ├── mvp_scope.md                     ← 功能边界（做/不做）
  │   ├── mvp_smoke_test_plan.md           ← 测试方案（L1×11 + L3.UITool×4 + L2×5 + L3 + 容差标准）
  │   ├── orchestrator_design.md           ← Orchestrator 编排设计（含 L3 execution_method 分发）
  │   ├── tool_contract_v0_1.md            ← 工具契约（§3-7.5 全部接口的 Args/Response/UE5 依赖）
  │   └── ue5_capability_map.md            ← 10 个 UE5 官方模块与本方案的映射
  │
  ├── Schemas/                             ← 24 个 JSON（Schema + example + 版本清单）
  │   ├── common/                          ← 6 个共用 Schema
  │   │   ├── primitives.schema.json       ← status 枚举 / 基础类型
  │   │   ├── transform.schema.json        ← location/rotation/relative_scale3d
  │   │   ├── bounds.schema.json           ← world_bounds_origin/extent
  │   │   ├── collision.schema.json        ← collision_profile_name/enabled/box_extent
  │   │   ├── error.schema.json            ← {code, message, details}
  │   │   └── material.schema.json         ← material_path/slot_index
  │   ├── feedback/                        ← 7 个反馈 Schema（按类型分子目录）
  │   │   ├── actor/                       ← get_actor_state / get_actor_bounds
  │   │   ├── asset/                       ← get_asset_metadata / get_dirty_assets
  │   │   ├── level/                       ← list_level_actors
  │   │   ├── project/                     ← get_current_project_state
  │   │   └── validation/                  ← run_map_check
  │   ├── write_feedback/                  ← 1 个写反馈 Schema
  │   │   └── write_operation_feedback.response.schema.json
  │   ├── examples/                        ← 8 个 example JSON（用于 Schema 校验链）
  │   │   ├── get_current_project_state.example.json
  │   │   ├── list_level_actors.example.json
  │   │   ├── get_actor_state.example.json
  │   │   ├── get_actor_bounds.example.json
  │   │   ├── get_asset_metadata.example.json
  │   │   ├── get_dirty_assets.example.json
  │   │   ├── run_map_check.example.json
  │   │   └── write_operation_feedback.example.json
  │   ├── versions/
  │   │   └── v0.1_manifest.json
  │   └── README.md
  │
  ├── Scripts/
  │   ├── bridge/                          ← 8 个 Python Bridge 客户端
  │   │   ├── __init__.py                  ← 包初始化（三层模块注释）
  │   │   ├── bridge_core.py               ← 通道切换 + 统一响应 + call_cpp_plugin
  │   │   ├── remote_control_client.py     ← HTTP 客户端（通道 B/C 共用）
  │   │   ├── query_tools.py               ← L1 查询工具（三通道分发）
  │   │   ├── write_tools.py               ← L1 写工具（三通道分发）
  │   │   ├── ui_tools.py                  ← L3 UI 工具（Automation Driver，通道 C + Mock）
  │   │   ├── ue_helpers.py                ← 通道 A 辅助
  │   │   └── uat_runner.py                ← L2 UAT 封装
  │   └── validation/
  │       └── validate_examples.py         ← Schema 校验脚本
  │
  ├── Specs/
  │   ├── templates/
  │   │   └── scene_spec_template.yaml     ← Spec 模板（含 execution_method: semantic/ui_tool）
  │   └── README.md
  │
  ├── Plugins/
  │   ├── AgentBridge/                     ← 12 个 C++ 文件（核心 Plugin）
  │   │   ├── AgentBridge.uplugin
  │   │   └── Source/AgentBridge/
  │   │       ├── AgentBridge.Build.cs
  │   │       ├── Public/
  │   │       │   ├── BridgeTypes.h                ← 类型定义 + L3 交叉比对
  │   │       │   ├── AgentBridgeSubsystem.h       ← Subsystem 声明（L1+L3 接口）
  │   │       │   ├── AgentBridgeCommandlet.h      ← Commandlet 声明
  │   │       │   ├── UATRunner.h                  ← UAT 封装声明
  │   │       │   └── AutomationDriverAdapter.h    ← L3 Automation Driver 封装
  │   │       └── Private/
  │   │           ├── AgentBridgeSubsystem.cpp     ← Subsystem 实现（1322 行）
  │   │           ├── AgentBridgeModule.cpp         ← 模块注册
  │   │           ├── AgentBridgeCommandlet.cpp     ← Commandlet 实现
  │   │           ├── UATRunner.cpp                 ← UAT 封装实现
  │   │           └── AutomationDriverAdapter.cpp   ← L3 封装实现
  │   │
  │   └── AgentBridgeTests/                ← 12 个 C++ 文件（测试 Plugin）
  │       ├── AgentBridgeTests.uplugin
  │       └── Source/AgentBridgeTests/
  │           ├── AgentBridgeTests.Build.cs
  │           └── Private/
  │               ├── AgentBridgeTestsModule.cpp
  │               ├── L1_QueryTests.cpp            ← 7 个 L1 查询测试
  │               ├── L1_WriteTests.cpp            ← 4 个 L1 写测试
  │               ├── L1_UIToolTests.cpp           ← 4 个 L3.UITool 测试
  │               ├── L2_ClosedLoopSpecs.spec.cpp  ← 3 个 BDD 闭环 Spec
  │               ├── L2_UIToolClosedLoopSpec.spec.cpp ← 2 个 L3 交叉比对闭环
  │               ├── L3_FunctionalTestActor.h     ← Functional Test 声明
  │               ├── L3_FunctionalTestActor.cpp   ← Functional Test 实现
  │               ├── AgentBridgeGauntletController.h   ← Gauntlet Controller
  │               └── AgentBridgeGauntletController.cpp
  │
  ├── Gauntlet/
  │   └── AgentBridge.TestConfig.cs        ← CI/CD 配置（AllTests/SmokeTests/SpecExecution）
  │
  └── roadmap/
      ├── mvp_roadmap.md                   ← 8 周路线图
      └── weekly_tasks.md                  ← 周任务清单

Step 3: 验证文件数量

  find . -type f | wc -l
  # 预期输出：76

Step 4: 验证关键文件可读

  head -5 AGENTS.md
  # 预期：看到 "# AGENT + UE5 可操作层 — Agent 协作规则"

  head -5 README.md
  # 预期：看到 "# AGENT + UE5 可操作层"

  head -5 Docs/architecture_overview.md
  # 预期：看到 "# 系统架构概述" + 版本号 v0.3

  head -5 Plugins/AgentBridge/Source/AgentBridge/Public/BridgeTypes.h
  # 预期：看到 C++ 头文件注释

Step 5: 验证目录逐项文件数

  echo "Docs:" && find Docs -type f | wc -l           # 预期：11
  echo "Schemas:" && find Schemas -type f | wc -l      # 预期：24
  echo "Scripts/bridge:" && find Scripts/bridge -type f | wc -l  # 预期：8
  echo "AgentBridge:" && find Plugins/AgentBridge -type f | wc -l  # 预期：12
  echo "AgentBridgeTests:" && find Plugins/AgentBridgeTests -type f | wc -l  # 预期：12

【验收标准】
- find . -type f | wc -l 输出 76
- Docs/ 11 个 / Schemas/ 24 个 / Scripts/bridge/ 8 个
- Plugins/AgentBridge/ 12 个 / Plugins/AgentBridgeTests/ 12 个
- AGENTS.md / README.md / architecture_overview.md 头部可正常阅读
- 无缺失文件（上述目录树中的每个文件都存在）
```

---

## TASK 02：验证 Schema 校验链

```
目标：确认 8 个 example JSON 全部能通过对应 Schema 的校验。
这是整个项目的"返回值合同"验证——后续所有 Bridge 接口的返回值必须符合这些 Schema。

前置依赖：TASK 01 完成（全部文件就位）

先读这些文件：
- Schemas/README.md（Schema 目录结构 + 版本说明）
- Schemas/common/primitives.schema.json（status 枚举 + 基础类型——理解什么是"有效返回值"）
- Scripts/validation/validate_examples.py（校验脚本——理解映射逻辑）
读完应掌握：Schema 目录的组织方式、每个 example 对应哪个 Schema、校验脚本的映射表

Step 1: 安装依赖

  pip install jsonschema pyyaml

Step 2: 运行 Schema 校验

  cd ProjectRoot
  python Scripts/validation/validate_examples.py --strict

  预期输出：
    Checking Schemas/examples/get_current_project_state.example.json ... OK
    Checking Schemas/examples/list_level_actors.example.json ... OK
    Checking Schemas/examples/get_actor_state.example.json ... OK
    Checking Schemas/examples/get_actor_bounds.example.json ... OK
    Checking Schemas/examples/get_asset_metadata.example.json ... OK
    Checking Schemas/examples/get_dirty_assets.example.json ... OK
    Checking Schemas/examples/run_map_check.example.json ... OK
    Checking Schemas/examples/write_operation_feedback.example.json ... OK
    Checked examples       : 8
    Passed                 : 8
    Failed                 : 0
    [SUCCESS] 全部 example 校验通过，本地校验链正常。

Step 3: 理解 Schema 映射关系

  8 个 example → Schema 映射：
  | example 文件 | 对应 Schema | 校验内容 |
  |---|---|---|
  | get_current_project_state.example.json | feedback/project/*.schema.json | project_name / engine_version / editor_mode |
  | list_level_actors.example.json | feedback/level/*.schema.json | actors 数组（actor_name / actor_path / class） |
  | get_actor_state.example.json | feedback/actor/*.schema.json | transform / collision / tags |
  | get_actor_bounds.example.json | feedback/actor/*.schema.json | world_bounds_origin / extent |
  | get_asset_metadata.example.json | feedback/asset/*.schema.json | exists / class / mesh_asset_bounds |
  | get_dirty_assets.example.json | feedback/asset/*.schema.json | dirty_assets 数组 |
  | run_map_check.example.json | feedback/validation/*.schema.json | map_errors / map_warnings |
  | write_operation_feedback.example.json | write_feedback/*.schema.json | created_objects / actual_transform / dirty_assets |

  所有 Schema 共用 common/ 下的类型定义（通过 $ref 引用）：
  - common/primitives.schema.json → status 枚举（success/warning/failed/mismatch/validation_error）
  - common/transform.schema.json → location[3] / rotation[3] / relative_scale3d[3]
  - common/bounds.schema.json → world_bounds_origin[3] / world_bounds_extent[3]
  - common/collision.schema.json → collision_profile_name / collision_enabled / collision_box_extent[3]
  - common/error.schema.json → {code, message, details}

Step 4: 如果校验失败的诊断步骤

  失败时脚本会输出：
    FAIL: Schemas/examples/xxx.example.json
    Error: 'yyy' is a required property

  诊断：
  a) 检查 example JSON 中是否缺少必填字段
  b) 检查 $ref 引用路径是否指向存在的 Schema 文件
  c) 检查 common/ 下 6 个共用 Schema 是否完整
  d) 检查 example 中 status 值是否为 5 个有效值之一

Step 5: 验证 Schema 文件自身的 JSON 合法性（可选）

  python -c "
  import json, glob
  for f in sorted(glob.glob('Schemas/**/*.json', recursive=True)):
      try:
          json.load(open(f))
          print(f'OK: {f}')
      except Exception as e:
          print(f'FAIL: {f} — {e}')
  "
  # 预期：全部 OK，无 FAIL

【验收标准】
- validate_examples.py --strict 返回 exit code 0
- 输出 "Checked examples: 8 / Passed: 8 / Failed: 0"
- 全部 24 个 JSON 文件是合法 JSON（无语法错误）
- 理解了 example → Schema 映射关系（后续 TASK 中新增接口需要同步新增 example + Schema）
```
---
---

# 阶段 2：C++ Plugin 核心

---

## TASK 03：创建 AgentBridge C++ Plugin 骨架 [UE5 环境 + C++ 编译]

```
目标：创建 AgentBridge C++ Editor Plugin 的基础结构（.uplugin + Build.cs + BridgeTypes.h + Module.cpp），
确认编译通过并在 Editor 中加载。这是全部后续 TASK 的基础——类型定义、错误码、响应外壳、辅助函数都在这里。

前置依赖：TASK 02 完成（Schema 校验链通过）

先读这些文件：
- Docs/architecture_overview.md（§2 架构全图 + §3 十模块实装表 + §3.5 三层工具体系）
  读完应掌握：AgentBridge Plugin 在架构中的位置（Agent → Orchestrator → 通道 C → Plugin → UE5 API）
- Docs/bridge_implementation_plan.md（§3 Plugin 代码结构 + §4 BridgeTypes 映射表）
  读完应掌握：C++ 类型如何映射到 Schema（EBridgeStatus ↔ primitives.schema.json 的 status 枚举）
- Schemas/common/primitives.schema.json（status 枚举定义——BridgeTypes.h 必须与之一致）

涉及文件（4 个，全部在 Plugins/AgentBridge/ 下）：

═══════════════════════════════════════════════════════
文件 1: Plugins/AgentBridge/AgentBridge.uplugin
═══════════════════════════════════════════════════════

JSON 格式的 Plugin 描述符。关键字段：

  {
    "FileVersion": 3,
    "FriendlyName": "AgentBridge",
    "Description": "AGENT + UE5 可操作层 — Bridge 封装层 C++ Editor Plugin",
    "Category": "Editor",
    "Modules": [
      {
        "Name": "AgentBridge",
        "Type": "Editor",            ← 仅 Editor 环境加载（不进入打包）
        "LoadingPhase": "PostEngineInit"  ← GEditor 已初始化后加载
      }
    ],
    "Plugins": [
      { "Name": "EditorScriptingUtilities", "Enabled": true },  ← UEditorLevelLibrary
      { "Name": "RemoteControl", "Enabled": true },             ← RC API 端点暴露
      { "Name": "PythonScriptPlugin", "Enabled": true }         ← Python 互调
    ]
  }

═══════════════════════════════════════════════════════
文件 2: Plugins/AgentBridge/Source/AgentBridge/AgentBridge.Build.cs
═══════════════════════════════════════════════════════

C# 构建配置。19 个模块依赖，按三层分类：

  PublicDependencyModuleNames（其他模块可引用）：
    Core / CoreUObject / Engine / Json / JsonUtilities

  PrivateDependencyModuleNames（仅本模块内部使用）：
    L1 相关：UnrealEd / EditorScriptingUtilities / RemoteControl / PythonScriptPlugin
    L2 相关：HTTP / AutomationController / Gauntlet / Serialization
    L3 相关：AutomationDriver / ContentBrowser / Slate / SlateCore / EditorStyle / InputCore

═══════════════════════════════════════════════════════
文件 3: Plugins/AgentBridge/Source/AgentBridge/Public/BridgeTypes.h
═══════════════════════════════════════════════════════

全部类型定义。这是整个 Plugin 的"类型基础"——后续全部接口的参数和返回值都基于这些类型。

UENUM（2 个）：

  EBridgeStatus（5 值，对应 Schemas/common/primitives.schema.json 的 status 枚举）：
    Success / Warning / Failed / Mismatch / ValidationError
  辅助函数：BridgeStatusToString(Status) → "success" / "warning" / "failed" / "mismatch" / "validation_error"

  EBridgeErrorCode（12 值，对应 Docs/tool_contract_v0_1.md §2.4 + §6.5）：
    None / InvalidArgs / ActorNotFound / AssetNotFound / ClassNotFound /
    EditorNotReady / ToolExecutionFailed / Timeout / PermissionDenied /
    DriverNotAvailable / WidgetNotFound / UIOperationTimeout（后 3 个为 L3 专用）
  辅助函数：BridgeErrorCodeToString(Code) → "INVALID_ARGS" / "ACTOR_NOT_FOUND" / ...

USTRUCT（5 个）：

  FBridgeError：{ Code(FString), Message(FString), Details(FString), ToJson() }
    对应 Schemas/common/error.schema.json

  FBridgeTransform：
    字段：Location(FVector) / Rotation(FRotator) / RelativeScale3D(FVector)
    方法：
      static FromActor(const AActor*) → 从 Actor 读取 Transform
      ToJson() → {"location":[x,y,z], "rotation":[p,y,r], "relative_scale3d":[x,y,z]}
      NearlyEquals(Other, LocTol=0.01, RotTol=0.01, ScaleTol=0.001) → bool
    对应 Schemas/common/transform.schema.json

  FBridgeObjectRef：{ ActorName(FString), ActorPath(FString), AssetPath(FString), ToJson() }

  FBridgeResponse（统一响应外壳——全部接口的返回值）：
    字段：Status(EBridgeStatus) / Summary(FString) / Data(TSharedPtr<FJsonObject>) /
          Warnings(TArray<FString>) / Errors(TArray<FBridgeError>) / bTransaction(bool)
    方法：
      IsSuccess() → Status == Success || Warning
      ToJsonString() → 序列化为 JSON 字符串（通过 RC API 返回给调用者）
    对应 Schemas/common/primitives.schema.json 的响应外壳定义

  FBridgeUIVerification（L3→L1 交叉比对结果）：
    字段：UIToolResponse / SemanticVerifyResponse / bConsistent / Mismatches(TArray<FString>)
    方法：GetFinalStatus() / GetFinalSummary() / ToJson()

AgentBridge 命名空间辅助函数（10 个）：

  响应构造（4 个）：
    MakeSuccess(Summary, Data) → FBridgeResponse
    MakeFailed(Summary, ErrorCode, Message) → FBridgeResponse
    MakeValidationError(FieldName, Message) → FBridgeResponse
    MakeMismatch(Summary, Data) → FBridgeResponse

  前置校验（3 个）：
    IsEditorReady(OutError) → bool（检查 GEditor 非 null + 不在 PIE + World 存在）
    ValidateTransform(Transform, OutError) → bool（零缩放检查）
    ValidateRequiredString(Value, FieldName, OutError) → bool（空字符串检查）

  L3 专用（3 个）：
    MakeDriverNotAvailable() → FBridgeResponse
    MakeWidgetNotFound(WidgetDescription) → FBridgeResponse
    MakeUIVerification(UIToolResp, SemanticResp, bConsistent, Mismatches) → FBridgeUIVerification

═══════════════════════════════════════════════════════
文件 4: Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeModule.cpp
═══════════════════════════════════════════════════════

模块注册文件。极简——仅注册模块并输出加载日志：

  #include "Modules/ModuleManager.h"
  class FAgentBridgeModule : public IModuleInterface
  {
      void StartupModule() override
      {
          UE_LOG(LogTemp, Log, TEXT("[AgentBridge] Plugin loaded, version 0.3.0"));
      }
  };
  IMPLEMENT_MODULE(FAgentBridgeModule, AgentBridge)

═══════════════════════════════════════════════════════
验证步骤
═══════════════════════════════════════════════════════

Step 1: 在 Editor 中启用 AgentBridge Plugin
  Edit → Plugins → 搜索 "AgentBridge" → Enable → 重启 Editor

Step 2: 编译项目
  Build → Build Solution（Visual Studio）
  或 Editor 自动编译（如果开启了 Live Coding）

Step 3: 检查 Output Log
  Window → Developer Tools → Output Log
  搜索 "[AgentBridge]"
  预期：看到 "[AgentBridge] Plugin loaded, version 0.3.0"

Step 4: 验证类型可用（在另一个模块中 #include）
  在任意 Editor 模块中添加：
    #include "BridgeTypes.h"
    FBridgeResponse TestResp = AgentBridge::MakeSuccess(TEXT("test"), nullptr);
  编译通过 = 类型导出正确

Step 5: 验证 Remote Control API 可见
  确认 Remote Control API Plugin 已启用：Edit → Plugins → Remote Control API
  启动后通过 curl 测试连通性：
    curl http://localhost:30010/remote/info
  预期：返回 JSON（说明 RC API HTTP Server 已启动）

【验收标准】
- 编译零 error / 零 warning（或仅有引擎自身的 warning）
- Editor Output Log 出现 "[AgentBridge] Plugin loaded, version 0.3.0"
- BridgeTypes.h 中的 USTRUCT/UENUM 可在其他模块中 #include 使用
- EBridgeStatus 有 5 个值，EBridgeErrorCode 有 12 个值（含 3 个 L3 专用）
- FBridgeTransform::NearlyEquals 可调用（用于后续 TASK 的容差比对）
- curl http://localhost:30010/remote/info 返回有效 JSON（RC API 可用）
```

---

## TASK 04：实现 AgentBridgeSubsystem 查询接口（7 个）[UE5 环境 + C++ 编译]

```
目标：创建 UAgentBridgeSubsystem（继承 UEditorSubsystem），实现 7 个 L1 语义查询接口。
全部接口标记 UFUNCTION(BlueprintCallable)，自动通过 Remote Control API 暴露给外部调用者。

前置依赖：TASK 03 完成（BridgeTypes.h 编译通过）

先读这些文件：
- Docs/bridge_implementation_plan.md（§5.1 L1 查询接口总表——每个接口的 UE5 API 依赖）
  读完应掌握：7 个接口各自调用哪些 UE5 API
- Docs/tool_contract_v0_1.md（§3 L1 查询工具——每个接口的 Args / Response / Preconditions）
  读完应掌握：每个接口的输入参数、返回值字段、错误处理规则
- Schemas/feedback/ 目录下 7 个 Schema 文件
  读完应掌握：每个接口返回的 data 字段结构（C++ 构造的 JSON 必须与 Schema 一致）
- Schemas/examples/ 目录下对应的 7 个 example JSON
  读完应掌握：返回值的具体样例（调试时可对照）

涉及文件（2 个）：

═══════════════════════════════════════════════════════
文件 1: Plugins/AgentBridge/Source/AgentBridge/Public/AgentBridgeSubsystem.h
═══════════════════════════════════════════════════════

继承 UEditorSubsystem，声明 7 个查询接口：

  UCLASS()
  class AGENTBRIDGE_API UAgentBridgeSubsystem : public UEditorSubsystem
  {
      GENERATED_BODY()
  public:
      // L1 查询接口（Category="AgentBridge|Query"）
      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse GetCurrentProjectState();

      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse ListLevelActors(const FString& ClassFilter = TEXT(""));

      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse GetActorState(const FString& ActorPath);

      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse GetActorBounds(const FString& ActorPath);

      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse GetAssetMetadata(const FString& AssetPath);

      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse GetDirtyAssets();

      UFUNCTION(BlueprintCallable, Category="AgentBridge|Query")
      FBridgeResponse RunMapCheck();

  private:
      AActor* FindActorByPath(const FString& ActorPath) const;
      UWorld* GetEditorWorld() const;
      TSharedPtr<FJsonObject> ReadCollisionToJson(const AActor* Actor) const;
      TArray<TSharedPtr<FJsonValue>> ReadTagsToJsonArray(const AActor* Actor) const;
  };

═══════════════════════════════════════════════════════
文件 2: Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeSubsystem.cpp
═══════════════════════════════════════════════════════

7 个查询接口的实现。每个接口遵循统一模式：
  参数校验（ValidateRequiredString）→ IsEditorReady 检查 → UE5 API 调用 → 构造 FBridgeResponse

------- 接口 1: GetCurrentProjectState() -------
  UE5 API: FPaths::GetProjectFilePath() + FApp::GetBuildVersion() + GetEditorWorld()->GetMapName()
  Schema: Schemas/feedback/project/get_current_project_state.response.schema.json
  返回 data 字段:
    project_name:   FString — FPaths::GetProjectFilePath() 的文件名部分
    uproject_path:  FString — 完整 .uproject 路径
    engine_version: FString — FApp::GetBuildVersion()
    current_level:  FString — GetEditorWorld()->GetMapName()
    editor_mode:    FString — "edit"（非 PIE 时）
  参数校验: 无（无输入参数）
  错误处理: IsEditorReady 失败 → EDITOR_NOT_READY

------- 接口 2: ListLevelActors(ClassFilter) -------
  UE5 API: UEditorLevelLibrary::GetAllLevelActors() + TActorIterator
  Schema: Schemas/feedback/level/list_level_actors.response.schema.json
  返回 data 字段:
    actors: TArray — 每个元素 { actor_name, actor_path, class }
  参数: ClassFilter（可选，空=返回全部 Actor）
  实现: 遍历 TActorIterator<AActor>(World)，如 ClassFilter 非空则按类名过滤

------- 接口 3: GetActorState(ActorPath) -------
  UE5 API: AActor::GetActorLocation/Rotation/Scale3D() + UPrimitiveComponent + AActor::Tags
  Schema: Schemas/feedback/actor/get_actor_state.response.schema.json
  返回 data 字段:
    actor_name:   FString — Actor->GetActorNameOrLabel()
    actor_path:   FString — Actor->GetPathName()
    class:        FString — Actor->GetClass()->GetPathName()
    target_level: FString — Actor->GetLevel()->GetOuter()->GetName()
    transform:    FJsonObject — FBridgeTransform::FromActor(Actor).ToJson()
    collision:    FJsonObject — ReadCollisionToJson(Actor)
    tags:         TArray — ReadTagsToJsonArray(Actor)
  参数校验:
    ActorPath 空字符串 → ValidateRequiredString → validation_error + INVALID_ARGS
  错误处理:
    FindActorByPath 返回 nullptr → failed + ACTOR_NOT_FOUND

------- 接口 4: GetActorBounds(ActorPath) -------
  UE5 API: AActor::GetActorBounds(false, Origin, Extent)
  Schema: Schemas/feedback/actor/get_actor_bounds.response.schema.json
  返回 data 字段:
    actor_path:          FString
    world_bounds_origin: [X, Y, Z] — Origin
    world_bounds_extent: [X, Y, Z] — Extent（半径）
  参数校验: ValidateRequiredString(ActorPath)
  错误处理: ACTOR_NOT_FOUND

------- 接口 5: GetAssetMetadata(AssetPath) -------
  UE5 API: UEditorAssetLibrary::DoesAssetExist() + FindAssetData() + UStaticMesh::GetBoundingBox()
  Schema: Schemas/feedback/asset/get_asset_metadata.response.schema.json
  返回 data 字段:
    asset_path:       FString
    exists:           bool — DoesAssetExist()
    class:            FString — AssetData.AssetClassPath（仅 exists=true 时）
    mesh_asset_bounds: [X, Y, Z] — GetBoundingBox().GetExtent()（仅 StaticMesh）
  参数校验: ValidateRequiredString(AssetPath)
  错误处理: 资产不存在不是错误——返回 success + exists=false

------- 接口 6: GetDirtyAssets() -------
  UE5 API: FEditorFileUtils::GetDirtyContentPackages() 或 遍历 Package 脏状态
  Schema: Schemas/feedback/asset/get_dirty_assets.response.schema.json
  返回 data 字段:
    dirty_assets: TArray<FString> — 脏资产路径列表
  参数校验: 无
  错误处理: 无（空列表也是合法返回）

------- 接口 7: RunMapCheck() -------
  UE5 API: GEditor->Exec(World, TEXT("MAP CHECK"))
  Schema: Schemas/feedback/validation/run_map_check.response.schema.json
  返回 data 字段:
    level_path:   FString — 当前关卡路径
    map_errors:   int32 — 地图错误数
    map_warnings: int32 — 地图警告数
  参数校验: 无
  错误处理: IsEditorReady 失败 → EDITOR_NOT_READY

------- 内部辅助方法 -------
  FindActorByPath(ActorPath):
    遍历 TActorIterator<AActor>(GetEditorWorld())，匹配 GetPathName() == ActorPath
    未找到返回 nullptr

  GetEditorWorld():
    GEditor->GetEditorWorldContext().World()
    GEditor 为 null 或 World 为 null 时返回 nullptr

  ReadCollisionToJson(Actor):
    获取 RootComponent 的 UPrimitiveComponent
    读取 CollisionProfileName / CollisionEnabled / BoxExtent / CanAffectNavigation
    如无 PrimitiveComponent 则返回空 JSON Object

  ReadTagsToJsonArray(Actor):
    遍历 Actor->Tags，转为 FJsonValueString 数组

═══════════════════════════════════════════════════════
验证步骤
═══════════════════════════════════════════════════════

Step 1: 编译通过

Step 2: 确认 Remote Control API Plugin 已启用
  Edit → Plugins → 搜索 "Remote Control" → 确认 Enabled

Step 3: 用 curl 逐个测试（Editor 运行中，端口 30010）

  测试 GetCurrentProjectState:
    curl -X PUT http://localhost:30010/remote/object/call \
      -H "Content-Type: application/json" \
      -d '{"objectPath":"/Script/AgentBridge.Default__AgentBridgeSubsystem",
           "functionName":"GetCurrentProjectState"}'
    预期: JSON 含 "status":"success" + data.project_name 非空

  测试 ListLevelActors:
    curl -X PUT http://localhost:30010/remote/object/call \
      -H "Content-Type: application/json" \
      -d '{"objectPath":"/Script/AgentBridge.Default__AgentBridgeSubsystem",
           "functionName":"ListLevelActors"}'
    预期: JSON 含 data.actors 数组

  测试 GetActorState（正常）:
    先从 ListLevelActors 返回值中取一个 actor_path
    curl -X PUT ... -d '{"objectPath":"...","functionName":"GetActorState",
      "parameters":{"ActorPath":"<实际actor_path>"}}'
    预期: data 含 transform / collision / tags

  测试 GetActorState（空参数 → validation_error）:
    curl -X PUT ... -d '{"objectPath":"...","functionName":"GetActorState",
      "parameters":{"ActorPath":""}}'
    预期: "status":"validation_error" + errors[0].code == "INVALID_ARGS"

  测试 GetActorState（不存在 → ACTOR_NOT_FOUND）:
    curl -X PUT ... -d '{"objectPath":"...","functionName":"GetActorState",
      "parameters":{"ActorPath":"/Game/Maps/TestMap.NonExistentActor"}}'
    预期: "status":"failed" + errors[0].code == "ACTOR_NOT_FOUND"

  测试 GetDirtyAssets:
    curl ... "functionName":"GetDirtyAssets"
    预期: data.dirty_assets 为数组（可能为空）

  测试 RunMapCheck:
    curl ... "functionName":"RunMapCheck"
    预期: data.map_errors 为整数

Step 4: 将返回的 JSON 与 Schema example 对照
  对比 curl 返回值的字段名/类型与 Schemas/examples/ 中对应的 example JSON

【验收标准】
- 编译零 error
- 7 个接口全部可通过 curl / RC API 调用并返回有效 JSON
- 全部接口返回的 JSON 中含 "status":"success" 和 "data" 对象
- GetActorState("") → status="validation_error" + INVALID_ARGS
- GetActorState("/Non/Existent") → status="failed" + ACTOR_NOT_FOUND
- GetAssetMetadata 对不存在资产返回 success + exists=false（不是 error）
- ListLevelActors 返回的每个 actor 含 actor_name / actor_path / class 三个字段
- GetCurrentProjectState 返回的 engine_version 包含 "5.5"（确认读到了真实引擎版本）
```

---

## TASK 05：实现写接口 + 验证接口 + 构建接口 [UE5 环境 + C++ 编译]

```
目标：在 AgentBridgeSubsystem 中追加 4 个 L1 写接口（全部 FScopedTransaction + 写后读回）+
3 个 L2 验证接口 + 1 个 L2 构建接口 + 2 个 L2 辅助接口，共 10 个接口。
写接口是本系统中最关键的部分——"能写 + 能回滚 + 能读回"三位一体。

前置依赖：TASK 04 完成（查询接口通过 RC API 可调用）

先读这些文件：
- Docs/bridge_implementation_plan.md（§5.2 L1 写接口 + §6 Transaction 管理）
  读完应掌握：FScopedTransaction 的作用域语义、写后读回为什么必须用 FBridgeTransform::FromActor
- Docs/tool_contract_v0_1.md（§4 L1 写工具核心——每个写接口的 Args / Response / Preconditions）
  读完应掌握：每个写接口的必填参数、返回值中必须包含 actual_transform 和 dirty_assets
- Docs/feedback_write_mapping.md（§4 核心闭环 + §8 回滚能力）
  读完应掌握：写-读映射关系（spawn_actor 后应调用 get_actor_state + get_actor_bounds 验证）

涉及文件：在 AgentBridgeSubsystem.h 中追加声明，在 AgentBridgeSubsystem.cpp 中追加实现。

═══════════════════════════════════════════════════════
L1 写接口（4 个，Category="AgentBridge|Write"）
全部使用 FScopedTransaction——Ctrl+Z 可撤销
═══════════════════════════════════════════════════════

------- 写接口 1: SpawnActor -------
  UFUNCTION(BlueprintCallable, Category="AgentBridge|Write")
  FBridgeResponse SpawnActor(
      const FString& LevelPath,          // 目标关卡路径
      const FString& ActorClass,         // UE 类路径（如 /Script/Engine.StaticMeshActor）
      const FString& ActorName,          // Actor 标签名
      const FBridgeTransform& Transform, // 位置/旋转/缩放
      bool bDryRun = false               // dry_run=true 时不实际执行
  );

  实现步骤：
  1. ValidateRequiredString × 3（LevelPath / ActorClass / ActorName）
  2. ValidateTransform（零缩放检查）
  3. IsEditorReady（GEditor 非 null + 不在 PIE）
  4. if (bDryRun) → 返回 success + 参数预览（不修改 World）
  5. FScopedTransaction Transaction(TEXT("AgentBridge: Spawn <ActorName>"))
  6. UEditorLevelLibrary::SpawnActorFromClass(Class, Location, Rotation)
  7. NewActor->SetActorLabel(ActorName)
  8. NewActor->SetActorScale3D(Transform.RelativeScale3D)
  9. 写后读回：FBridgeTransform ActualTransform = FBridgeTransform::FromActor(NewActor)
     关键：从 UE5 API 重新读取，不是复制输入参数
  10. 返回 data: { created_objects: [{actor_name, actor_path}], actual_transform, dirty_assets, bTransaction: true }

  UE5 API: UEditorLevelLibrary::SpawnActorFromClass() + AActor::SetActorLabel + SetActorScale3D
  Schema: Schemas/write_feedback/write_operation_feedback.response.schema.json
  错误处理: ClassNotFound（LoadClass 失败）/ EditorNotReady / InvalidArgs

------- 写接口 2: SetActorTransform -------
  UFUNCTION(BlueprintCallable, Category="AgentBridge|Write")
  FBridgeResponse SetActorTransform(
      const FString& ActorPath,
      const FBridgeTransform& Transform,
      bool bDryRun = false
  );

  实现步骤：
  1. ValidateRequiredString(ActorPath) + ValidateTransform
  2. FindActorByPath(ActorPath) → Actor 不存在返回 ACTOR_NOT_FOUND
  3. 先读 old_transform：FBridgeTransform::FromActor(Actor)（修改前快照）
  4. if (bDryRun) → 返回 success + old_transform 预览
  5. Actor->Modify()（标记修改，支持 Undo 系统）
  6. FScopedTransaction Transaction(TEXT("AgentBridge: SetTransform <ActorPath>"))
  7. Actor->SetActorLocationAndRotation(Transform.Location, Transform.Rotation)
  8. Actor->SetActorScale3D(Transform.RelativeScale3D)
  9. 写后读回：FBridgeTransform ActualTransform = FBridgeTransform::FromActor(Actor)
  10. 返回 data: { modified_objects, old_transform, actual_transform, dirty_assets, bTransaction: true }

------- 写接口 3: ImportAssets -------
  UFUNCTION(BlueprintCallable, Category="AgentBridge|Write")
  FBridgeResponse ImportAssets(
      const FString& SourceDir,           // 源文件目录（如 D:/Assets/Meshes）
      const FString& DestPath,            // 目标内容路径（如 /Game/ImportedMeshes）
      bool bReplaceExisting = false,
      bool bDryRun = false
  );

  实现：扫描 SourceDir 中的 .fbx/.obj/.png/.tga/.wav → IAssetTools::ImportAssetTasks
  返回 data: { created_objects: [{asset_path}], dirty_assets }

------- 写接口 4: CreateBlueprintChild -------
  UFUNCTION(BlueprintCallable, Category="AgentBridge|Write")
  FBridgeResponse CreateBlueprintChild(
      const FString& ParentClass,        // 父类路径（如 /Script/Engine.Actor）
      const FString& PackagePath,        // 新 BP 保存路径（如 /Game/Blueprints/BP_MyActor）
      bool bDryRun = false
  );

  实现：LoadClass 验证父类 → UBlueprintFactory + IAssetTools::CreateAsset
  错误处理：父类不存在 → CLASS_NOT_FOUND
  返回 data: { created_objects: [{asset_path}], dirty_assets }

FScopedTransaction 核心模式（全部 4 个写接口统一）：
  {
      FScopedTransaction Transaction(FText::FromString(TEXT("AgentBridge: <操作描述>")));
      // ... 写操作 ...
      // 作用域结束时自动提交 Transaction
      // 异常时自动回滚
  }
  用户在 Editor 中 Ctrl+Z → 整个写操作一步撤销

═══════════════════════════════════════════════════════
L2 验证接口（3 个，Category="AgentBridge|Validate"）
═══════════════════════════════════════════════════════

------- 验证接口 1: ValidateActorInsideBounds -------
  FBridgeResponse ValidateActorInsideBounds(
      const FString& ActorPath,
      const FVector& BoundsOrigin,     // 包围盒中心
      const FVector& BoundsExtent      // 包围盒半径
  );
  UE5 API: AActor::GetActorBounds → FBox::IsInside
  返回 status: 在范围内 → success / 不在范围内 → mismatch

------- 验证接口 2: ValidateActorNonOverlap -------
  FBridgeResponse ValidateActorNonOverlap(const FString& ActorPath);
  UE5 API: UWorld::OverlapMultiByChannel()
  返回 data: { has_overlap: bool, overlapping_actors: [...] }

------- 验证接口 3: RunAutomationTests -------
  FBridgeResponse RunAutomationTests(const FString& Filter, const FString& ReportPath = "");
  UE5 API: GEditor->Exec "Automation RunTests <Filter>"
  返回 data: { filter, command }

═══════════════════════════════════════════════════════
L2 构建 + 辅助接口（3 个）
═══════════════════════════════════════════════════════

  BuildProject(Platform="Win64", Configuration="Development", bDryRun=false)
    Category="AgentBridge|Build"
    通过 FPlatformProcess::CreateProc 启动 UAT 子进程

  SaveNamedAssets(AssetPaths)
    Category="AgentBridge|Utility"
    UEditorAssetLibrary::SaveLoadedAssets

  CaptureViewportScreenshot(ScreenshotName)
    Category="AgentBridge|Utility"
    FScreenshotRequest → 输出到 Saved/Screenshots/

═══════════════════════════════════════════════════════
验证步骤
═══════════════════════════════════════════════════════

Step 1: 编译通过

Step 2: 通过 RC API 测试 SpawnActor
  curl -X PUT http://localhost:30010/remote/object/call \
    -H "Content-Type: application/json" \
    -d '{"objectPath":"/Script/AgentBridge.Default__AgentBridgeSubsystem",
         "functionName":"SpawnActor",
         "parameters":{
           "LevelPath":"/Game/Maps/TestMap",
           "ActorClass":"/Script/Engine.StaticMeshActor",
           "ActorName":"TestCube_01",
           "Transform":{"Location":{"X":100,"Y":200,"Z":0},"Rotation":{"Pitch":0,"Yaw":0,"Roll":0},"RelativeScale3D":{"X":1,"Y":1,"Z":1}},
           "bDryRun":false
         }}'
  预期: status=success + data.created_objects 非空 + data.actual_transform 与输入一致（容差内）

Step 3: 验证 Undo
  在 Editor 中 Ctrl+Z → Actor 应消失
  再调用 ListLevelActors 确认 Actor 不在列表中

Step 4: 测试 dry_run
  同上 curl，但 bDryRun=true
  预期: status=success + 但 Actor 不出现在关卡中（ListLevelActors 不含该 Actor）

Step 5: 测试参数校验
  SpawnActor ActorClass="" → validation_error + INVALID_ARGS
  SetActorTransform ActorPath="/Non/Existent" → failed + ACTOR_NOT_FOUND
  CreateBlueprintChild ParentClass="/Non/Existent" → failed + CLASS_NOT_FOUND

Step 6: 验证写后读回容差
  SpawnActor 返回的 actual_transform.location 与输入 Transform.Location 的差值 ≤ 0.01cm
  SpawnActor 返回的 actual_transform.relative_scale3d 与输入的差值 ≤ 0.001

【验收标准】
- 编译零 error
- SpawnActor via RC API → Actor 出现 → Ctrl+Z → Actor 消失（FScopedTransaction 生效）
- SpawnActor bDryRun=true → Actor 不出现（World 未修改）
- actual_transform 与输入一致：location ≤ 0.01cm / scale ≤ 0.001
- SetActorTransform 返回 old_transform（修改前值）+ actual_transform（修改后值）
- 空参数 → validation_error / 不存在对象 → ACTOR_NOT_FOUND / CLASS_NOT_FOUND
- ValidateActorNonOverlap 返回 has_overlap 布尔值 + overlapping_actors 列表
- 全部写接口返回 bTransaction: true
```

---

## TASK 06：实现 Commandlet + UATRunner [UE5 环境 + C++ 编译]

```
目标：实现无头执行入口（UAgentBridgeCommandlet）和 UAT 子进程封装（FUATRunner）。
Commandlet 使系统可在命令行无 GUI 环境中执行 Spec / 测试 / 单工具。
UATRunner 封装 UAT 的 BuildCookRun / RunTests / RunGauntlet 命令。
两者组合打通 CI/CD 执行路径：Gauntlet → Editor → Commandlet → Subsystem。

前置依赖：TASK 05 完成（全部 Bridge 接口可用）

先读这些文件：
- Docs/architecture_overview.md（§7 执行层架构）
  读完应掌握：Commandlet 在执行层中的位置（CLI → Commandlet → Subsystem → UE5 API）
- Docs/bridge_implementation_plan.md（§8 执行模式——三种 Commandlet 模式的参数语法）
  读完应掌握：-Spec / -RunTests / -Tool 三种模式的输入/输出/退出码规范
- Docs/ue5_capability_map.md（§4.2.1 Commandlet + §4.2.2 UAT）
  读完应掌握：UE5 Commandlet 的生命周期 + UAT 的进程模型

涉及文件（4 个）：

═══════════════════════════════════════════════════════
文件 1: Plugins/AgentBridge/Source/AgentBridge/Public/AgentBridgeCommandlet.h
═══════════════════════════════════════════════════════

  UCLASS()
  class AGENTBRIDGE_API UAgentBridgeCommandlet : public UCommandlet
  {
      GENERATED_BODY()
  public:
      UAgentBridgeCommandlet();
      virtual int32 Main(const FString& Params) override;

  private:
      void ParseParams(const FString& Params);
      int32 RunSpec();             // 模式 1: 执行 Spec YAML
      int32 RunTests();            // 模式 2: 运行 Automation Test
      int32 RunSingleTool();       // 模式 3: 执行单个工具
      void WriteReport(const FString& JsonContent);

      FString SpecPath;            // -Spec=xxx.yaml
      FString TestFilter;          // -RunTests=Project.AgentBridge.L1
      FString ToolName;            // -Tool=ListLevelActors
      FString ReportPath;          // -Report=report.json
  };

═══════════════════════════════════════════════════════
文件 2: Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeCommandlet.cpp
═══════════════════════════════════════════════════════

构造函数：
  设置 HelpUsage 和 HelpParamNames（-Spec / -RunTests / -Tool / -Report）
  IsEditor = true, IsClient = false, IsServer = false

Main(Params) 主入口：
  1. ParseParams(Params) → 解析命令行参数到成员变量
  2. 优先级判定：
     if (!SpecPath.IsEmpty())     → ExitCode = RunSpec()
     else if (!TestFilter.IsEmpty()) → ExitCode = RunTests()
     else if (!ToolName.IsEmpty())   → ExitCode = RunSingleTool()
     else → UE_LOG(Error, "No mode specified") + ExitCode = 2
  3. if (!ReportPath.IsEmpty()) → WriteReport(结果 JSON)
  4. return ExitCode

三种模式的实现：

  模式 1: RunSpec()
    通过 IPythonScriptPlugin 调用 Python Orchestrator：
      IPythonScriptPlugin::ExecPythonCommand(
        FString::Printf(TEXT("from orchestrator import run; run('%s')"), *SpecPath))
    解析 Orchestrator 返回的报告 JSON → 判定 ExitCode
    Spec 解析依赖 Python 的 pyyaml 库（C++ 无 YAML 解析器）

  模式 2: RunTests()
    调用 Subsystem->RunAutomationTests(TestFilter, ReportPath)
    等待测试完成 → 解析结果 → ExitCode

  模式 3: RunSingleTool()
    建立工具名→Subsystem 方法的分发表：
      "GetCurrentProjectState" → Subsystem->GetCurrentProjectState()
      "ListLevelActors" → Subsystem->ListLevelActors()
      "GetDirtyAssets" → Subsystem->GetDirtyAssets()
      ... 全部 15 个 L1/L2 接口
    未匹配的工具名 → ExitCode = 2

退出码规范：
  0 = 成功（全部 Actor status=success 或 全部测试 PASS）
  1 = mismatch 或 warning（有 Actor 不符合预期但非致命）
  2 = failed 或参数错误（执行失败 / 未指定模式 / 工具名不存在）

═══════════════════════════════════════════════════════
文件 3: Plugins/AgentBridge/Source/AgentBridge/Public/UATRunner.h
═══════════════════════════════════════════════════════

  struct FUATRunResult
  {
      bool bLaunched = false;      // UAT 进程是否启动成功
      bool bCompleted = false;     // 是否已完成（同步模式下始终 true/false）
      int32 ExitCode = -1;         // UAT 退出码
      FString CommandLine;         // 实际执行的命令行
      FString StdOut;              // 标准输出（同步模式）
      FString StdErr;              // 标准错误（同步模式）
      FString ErrorMessage;        // 启动失败时的错误描述
      bool IsSuccess() const { return bLaunched && bCompleted && ExitCode == 0; }
  };

  class AGENTBRIDGE_API FUATRunner
  {
  public:
      FUATRunner();

      bool IsUATAvailable() const;   // RunUAT.bat/sh 是否存在

      FUATRunResult BuildCookRun(     // 编译 + 烹饪 + 打包
          const FString& Platform = "Win64",
          const FString& Configuration = "Development",
          bool bSync = false           // true=阻塞等待, false=启动即返回
      );

      FUATRunResult RunAutomationTests(  // 通过 UAT 运行测试
          const FString& Filter,
          const FString& ReportPath = "",
          bool bSync = false
      );

      FUATRunResult RunGauntlet(       // 启动 Gauntlet 测试会话
          const FString& TestConfigName,  // 如 "AgentBridge.AllTests"
          bool bSync = false
      );

      FUATRunResult RunCustomCommand(  // 任意 UAT 命令
          const FString& Command,
          bool bSync = false
      );

  private:
      FString DetectRunUATPath() const;  // 自动检测 RunUAT.bat/sh 路径
      FUATRunResult ExecuteUAT(const FString& Args, bool bSync);  // 底层执行
      FString RunUATPath;               // 缓存的 RunUAT 路径
  };

═══════════════════════════════════════════════════════
文件 4: Plugins/AgentBridge/Source/AgentBridge/Private/UATRunner.cpp
═══════════════════════════════════════════════════════

  DetectRunUATPath():
    从 FPaths::EngineDir() 推导：
      Windows: Engine/Build/BatchFiles/RunUAT.bat
      Mac/Linux: Engine/Build/BatchFiles/RunUAT.sh
    路径不存在 → RunUATPath 为空

  IsUATAvailable():
    return !RunUATPath.IsEmpty() && FPaths::FileExists(RunUATPath)

  ExecuteUAT(Args, bSync):
    FPlatformProcess::CreateProc(RunUATPath, Args, ...)
    bSync=true → FPlatformProcess::WaitForProc + 读 stdout/stderr
    bSync=false → 立即返回 bLaunched=true, bCompleted=false

  BuildCookRun(Platform, Configuration, bSync):
    Args = FString::Printf("-BuildCookRun -project=%s -platform=%s -clientconfig=%s -cook -stage -pak",
        FPaths::GetProjectFilePath(), Platform, Configuration)
    return ExecuteUAT(Args, bSync)

  RunGauntlet(TestConfigName, bSync):
    Args = FString::Printf("RunGauntlet -project=%s -Test=%s -unattended",
        FPaths::GetProjectFilePath(), TestConfigName)
    return ExecuteUAT(Args, bSync)

═══════════════════════════════════════════════════════
验证步骤
═══════════════════════════════════════════════════════

Step 1: 编译通过

Step 2: 测试 Commandlet 模式 3（最简单——单工具执行）
  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -Tool=GetCurrentProjectState -Unattended -NoPause
  预期: 输出包含 project_name 的 JSON + exit code 0

  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -Tool=ListLevelActors -Unattended -NoPause
  预期: 输出包含 actors 数组的 JSON + exit code 0

  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -Tool=GetDirtyAssets -Unattended -NoPause
  预期: 输出包含 dirty_assets 的 JSON + exit code 0

Step 3: 测试无效参数
  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -Tool=NonExistentTool -Unattended -NoPause
  预期: exit code 2

  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -Unattended -NoPause
  预期: exit code 2（无模式指定）

Step 4: 测试报告输出
  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -Tool=GetCurrentProjectState -Report=test_report.json -Unattended -NoPause
  检查 test_report.json 是否存在且为合法 JSON

Step 5: 验证 UATRunner 可用性
  在 Editor 中通过 C++ 或 Python 调用：
    FUATRunner Runner;
    bool bAvailable = Runner.IsUATAvailable();
    // 预期: true（RunUAT.bat/sh 路径可找到）

Step 6: 测试 Commandlet 模式 2（运行测试——需要 TASK 07 完成后才有测试可运行）
  UE5Editor-Cmd.exe MyProject.uproject -run=AgentBridge -RunTests=Project.AgentBridge.L1 -Unattended -NoPause
  预期: 运行 L1 测试 → exit code 0（全部通过）或 exit code 1（有失败）

【验收标准】
- 编译零 error
- Commandlet -Tool=GetCurrentProjectState → JSON 输出 + exit code 0
- Commandlet -Tool=ListLevelActors → JSON 含 actors 数组 + exit code 0
- Commandlet -Tool=NonExistentTool → exit code 2
- Commandlet 无参数 → exit code 2 + 日志提示 "No mode specified"
- Commandlet -Report=xxx.json → 报告文件存在且为合法 JSON
- UATRunner.IsUATAvailable() 返回 true（RunUAT.bat/sh 路径正确）
- FUATRunResult 结构体的 IsSuccess() 方法可正确判定（bLaunched + bCompleted + ExitCode==0）
```
---
---

# 阶段 3：UE5 原生测试

---

## TASK 07：创建 AgentBridgeTests Plugin + L1 测试（11 个）[UE5 环境 + C++ 编译]

```
目标：创建 AgentBridgeTests 测试 Plugin 并注册 11 个 L1 Simple Automation Test。
L1 测试是最基础的测试层——逐个接口验证参数校验、错误路径、dry_run、实际执行、返回值结构。
写测试还验证 FScopedTransaction（Ctrl+Z 可撤销）和写后读回容差。

前置依赖：TASK 05 完成（全部 Bridge 接口可用）

先读这些文件：
- Docs/mvp_smoke_test_plan.md（§2 三层测试体系 + §4 L1 设计模式和清单）
  读完应掌握：L1 测试的注册方式（IMPLEMENT_SIMPLE_AUTOMATION_TEST 宏）、Test Flag 含义、
  每个测试应覆盖的场景（参数校验 / dry_run / 正常执行 / 错误路径）
- Docs/tool_contract_v0_1.md（§3-5 全部接口的 Args / Response）
  读完应掌握：每个接口的预期返回值字段——测试断言的依据
- Docs/bridge_verification_and_error_handling.md（§6 错误码映射 + §7 边界条件）
  读完应掌握：什么输入应触发哪个错误码（INVALID_ARGS / ACTOR_NOT_FOUND 等）

涉及文件（5 个）：

═══════════════════════════════════════════════════════
文件 1: Plugins/AgentBridgeTests/AgentBridgeTests.uplugin
═══════════════════════════════════════════════════════

  {
    "Modules": [{ "Name": "AgentBridgeTests", "Type": "Editor", "LoadingPhase": "Default" }],
    "Plugins": [
      { "Name": "AgentBridge", "Enabled": true },        ← 被测试目标
      { "Name": "FunctionalTesting", "Enabled": true }   ← L3 Functional Test 基类
    ],
    "EnabledByDefault": false,    ← 仅测试时启用
    "CanContainContent": true     ← FTEST_ 测试地图
  }

═══════════════════════════════════════════════════════
文件 2: Plugins/AgentBridgeTests/Source/AgentBridgeTests/AgentBridgeTests.Build.cs
═══════════════════════════════════════════════════════

  PrivateDependencyModuleNames:
    AgentBridge / UnrealEd / EditorScriptingUtilities /
    AutomationController / AutomationDriver / FunctionalTesting /
    Json / JsonUtilities / Gauntlet

═══════════════════════════════════════════════════════
文件 3: Plugins/AgentBridgeTests/Source/AgentBridgeTests/Private/AgentBridgeTestsModule.cpp
═══════════════════════════════════════════════════════

  IMPLEMENT_MODULE(FAgentBridgeTestsModule, AgentBridgeTests)
  // 极简——仅注册模块

═══════════════════════════════════════════════════════
文件 4: Plugins/AgentBridgeTests/Source/AgentBridgeTests/Private/L1_QueryTests.cpp
═══════════════════════════════════════════════════════

7 个查询接口的 L1 测试。全部使用 IMPLEMENT_SIMPLE_AUTOMATION_TEST 宏。
Test Flag: EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter

获取 Subsystem 的标准方式（每个测试开头）：
  UAgentBridgeSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>();

------- T1-01: Project.AgentBridge.L1.Query.GetCurrentProjectState -------
  调用: Subsystem->GetCurrentProjectState()
  断言:
    - status == "success"
    - data 含 project_name（非空）
    - data 含 engine_version（包含 "5.5"）
    - data 含 current_level
    - data 含 editor_mode（"editing" 或 "pie"）

------- T1-02: Project.AgentBridge.L1.Query.ListLevelActors -------
  调用: Subsystem->ListLevelActors()
  断言:
    - status == "success"
    - data.actors 为数组
    - 每个 actor 含 actor_name / actor_path / class 三个字段
  注意: 空关卡下 actors 可以是空数组，但字段结构必须正确

------- T1-03: Project.AgentBridge.L1.Query.GetActorState -------
  正常路径:
    先从 ListLevelActors 取一个 actor_path → GetActorState(actor_path)
    断言: data 含 actor_name / actor_path / class / transform / collision / tags
    如果关卡无 Actor → AddWarning + 跳过正常路径测试
  错误路径 1: GetActorState("") → status="validation_error" + errors[0].code="INVALID_ARGS"
  错误路径 2: GetActorState("/Game/Maps/TestMap.NonExistent") → status="failed" + ACTOR_NOT_FOUND

------- T1-04: Project.AgentBridge.L1.Query.GetActorBounds -------
  正常路径: GetActorBounds(有效 actor_path)
    断言: data 含 world_bounds_origin[3] + world_bounds_extent[3]
  错误路径: GetActorBounds("") → validation_error

------- T1-05: Project.AgentBridge.L1.Query.GetAssetMetadata -------
  正常路径: GetAssetMetadata("/Engine/BasicShapes/Cube")
    断言: exists=true + class 非空
  不存在: GetAssetMetadata("/Game/NonExistent/Asset")
    断言: status="success"（不是 error！）+ exists=false
  错误路径: GetAssetMetadata("") → validation_error

------- T1-06: Project.AgentBridge.L1.Query.GetDirtyAssets -------
  调用: Subsystem->GetDirtyAssets()
  断言: status="success" + data.dirty_assets 为数组（可能为空）

------- T1-07: Project.AgentBridge.L1.Query.RunMapCheck -------
  调用: Subsystem->RunMapCheck()
  断言: status="success" + data 含 map_errors(int) + map_warnings(int)

═══════════════════════════════════════════════════════
文件 5: Plugins/AgentBridgeTests/Source/AgentBridgeTests/Private/L1_WriteTests.cpp
═══════════════════════════════════════════════════════

4 个写接口的 L1 测试。每个测试覆盖完整的写操作生命周期。

写测试的标准清理模式：
  // 测试结束时 Undo 清理——不在测试地图留残留
  if (GEditor) GEditor->UndoTransaction();

------- T1-08: Project.AgentBridge.L1.Write.SpawnActor -------
  覆盖场景（6 个子测试）：

  1) 参数校验：
     SpawnActor("", class, name, transform) → validation_error（空 LevelPath）
     SpawnActor(level, "", name, transform) → validation_error（空 ActorClass）
     SpawnActor(level, class, name, zeroScaleTransform) → validation_error（零缩放）

  2) dry_run：
     SpawnActor(..., bDryRun=true) → status=success + Actor 不在关卡中
     验证：ListLevelActors 不含该 actor_name

  3) 实际执行：
     SpawnActor(TestMap, StaticMeshActor, "TestCube_01", {loc:[1000,2000,0], rot:[0,0,0], scale:[1,1,1]})
     断言:
       - status == "success"
       - data.created_objects 数组含 1 个元素
       - created_objects[0] 含 actor_name + actor_path
       - data.actual_transform 存在
       - bTransaction == true

  4) 写后读回容差：
     actual_transform.location.X ≈ 1000.0（容差 0.01）
     actual_transform.location.Y ≈ 2000.0（容差 0.01）
     用 TestNearlyEqual(Actual, Expected, 0.01f)

  5) dirty_assets：
     data.dirty_assets 非空（Spawn 后关卡变脏）

  6) Undo 清理：
     GEditor->UndoTransaction()
     ListLevelActors → 确认 "TestCube_01" 不在列表中

------- T1-09: Project.AgentBridge.L1.Write.SetActorTransform -------
  覆盖场景（5 个子测试）：

  1) 参数校验：
     SetActorTransform("", transform) → validation_error

  2) Actor 不存在：
     SetActorTransform("/Non/Existent", transform) → failed + ACTOR_NOT_FOUND

  3) dry_run：
     先 SpawnActor 创建测试 Actor → SetActorTransform(path, newTransform, bDryRun=true)
     断言: data 含 old_transform（当前值快照）+ Actor 位置未改变

  4) 实际执行：
     SetActorTransform(path, newTransform)
     断言: data.old_transform ≠ data.actual_transform + actual_transform ≈ newTransform（容差 0.01）

  5) Undo 清理：
     GEditor->UndoTransaction()（撤销 SetActorTransform）
     GEditor->UndoTransaction()（撤销 SpawnActor）

------- T1-10: Project.AgentBridge.L1.Write.ImportAssets -------
  覆盖场景（2 个子测试）：

  1) 参数校验：
     ImportAssets("", destPath) → validation_error
     ImportAssets(sourceDir, "") → validation_error

  2) dry_run：
     ImportAssets(sourceDir, destPath, false, bDryRun=true) → success + 无实际导入
     注意：CI 环境可能无测试资源文件——dry_run 不需要实际文件

------- T1-11: Project.AgentBridge.L1.Write.CreateBlueprintChild -------
  覆盖场景（4 个子测试）：

  1) 参数校验：
     CreateBlueprintChild("", packagePath) → validation_error
     CreateBlueprintChild(parentClass, "") → validation_error

  2) 不存在的父类：
     CreateBlueprintChild("/Script/NonExistent.Class", path) → failed + CLASS_NOT_FOUND

  3) dry_run：
     CreateBlueprintChild("/Script/Engine.Actor", "/Game/Test/BP_Test", bDryRun=true) → success

  4) 实际创建 + Undo：
     CreateBlueprintChild("/Script/Engine.Actor", "/Game/Test/BP_TestChild")
     断言: data.created_objects 含 asset_path
     Undo: GEditor->UndoTransaction()

═══════════════════════════════════════════════════════
验证步骤
═══════════════════════════════════════════════════════

Step 1: 编译通过（AgentBridgeTests Plugin + AgentBridge Plugin 同时启用）

Step 2: 在 Session Frontend 中确认测试可见
  Window → Developer Tools → Session Frontend → Automation 标签
  展开 Project → AgentBridge → L1
  预期树结构：
    Project.AgentBridge
    ├── L1
    │   ├── Query
    │   │   ├── GetCurrentProjectState    (T1-01)
    │   │   ├── ListLevelActors           (T1-02)
    │   │   ├── GetActorState             (T1-03)
    │   │   ├── GetActorBounds            (T1-04)
    │   │   ├── GetAssetMetadata          (T1-05)
    │   │   ├── GetDirtyAssets            (T1-06)
    │   │   └── RunMapCheck               (T1-07)
    │   └── Write
    │       ├── SpawnActor                (T1-08)
    │       ├── SetActorTransform         (T1-09)
    │       ├── ImportAssets              (T1-10)
    │       └── CreateBlueprintChild      (T1-11)

Step 3: Run All → 全部绿灯
  在 Session Frontend 中选中 Project.AgentBridge.L1 → Run Selected
  预期: 11 个测试全部 PASS（绿色）
  注意: 如果测试地图为空关卡，T1-03/T1-04 会 AddWarning + 跳过正常路径（不是 FAIL）

Step 4: Console 命令验证
  在 Editor Console 中输入：
    Automation RunTests Project.AgentBridge.L1
  预期: 全部通过

Step 5: 验证错误路径不是误报
  确认 T1-03 中 GetActorState("") 确实返回 validation_error（不是 success）
  确认 T1-11 中 CreateBlueprintChild 不存在父类确实返回 CLASS_NOT_FOUND（不是 success）

【验收标准】
- 编译零 error
- Session Frontend 中可见 11 个 L1 测试（Query 7 + Write 4）
- Run All → 全部绿灯（或 AddWarning 但不 FAIL）
- Console "Automation RunTests Project.AgentBridge.L1" 全部通过
- T1-03 GetActorState 空参数确实返回 validation_error
- T1-03 GetActorState 不存在路径确实返回 ACTOR_NOT_FOUND
- T1-05 GetAssetMetadata 不存在资产返回 success + exists=false（不是 error）
- T1-08 SpawnActor bTransaction=true + actual_transform 容差 ≤ 0.01
- T1-08 SpawnActor Undo 后 Actor 消失
- T1-09 SetActorTransform 返回 old_transform ≠ actual_transform
- T1-11 CreateBlueprintChild 不存在父类返回 CLASS_NOT_FOUND
```

---

## TASK 08：实现 L2 Automation Spec（3 个 BDD 闭环）[UE5 环境 + C++ 编译]

```
目标：实现 3 个 L2 闭环验证 Automation Spec。

前置依赖：TASK 07 完成

先读：Docs/mvp_smoke_test_plan.md（第 5 节）

创建 L2_ClosedLoopSpecs.spec.cpp，使用 BEGIN_DEFINE_SPEC 宏。
Test Flag: EditorContext + SmokeFilter

a) SpawnReadbackLoop（5 个 It）
   BeforeEach→SpawnActor / It→验证 location/rotation/scale 容差 + bounds + dirty
   AfterEach→Undo
b) TransformModifyLoop（3 个 It）
   It→验证 old_transform / It→readback 新值 / It→Undo 后恢复原值
c) ImportMetadataLoop（2 个 It）
   It→GetAssetMetadata exists=true / It→GetDirtyAssets（无测试资源时 skip）

容差：location ≤ 0.01, rotation ≤ 0.01, scale ≤ 0.001

【验收标准】
- Session Frontend 可见 3 个 L2 Spec
- "Automation RunTests Project.AgentBridge.L2" 全部通过
```
---
---

# 阶段 4：Python 客户端 + Orchestrator

> Python 不再是 Bridge 核心——它是 C++ Plugin 的轻量客户端 + Spec 解析器 + 编排器。

---

## TASK 09：Python 三通道客户端 [无需 UE5 环境]

```
目标：确认 Python 三通道客户端正确（MOCK / PYTHON_EDITOR / REMOTE_CONTROL / CPP_PLUGIN）。

前置依赖：TASK 06 完成

先读：Docs/bridge_implementation_plan.md（第 7 节：Python 客户端层）

确认以下文件内容正确（已在交付包中提供）：
- bridge_core.py: BridgeChannel 含 CPP_PLUGIN + call_cpp_plugin() + safe_execute(timeout)
- query_tools.py: _CPP_QUERY_MAP + _dispatch 4 通道 + cpp_params
- write_tools.py: _CPP_WRITE_MAP + _dispatch_write 4 通道 + Transform 格式转换
- remote_control_client.py / ue_helpers.py / uat_runner.py

【测试】Mock 模式全部接口返回 success；BridgeChannel 含 4 个枚举值

【验收标准】
- Mock 模式 11 个接口全部返回 success
- BridgeChannel 包含 CPP_PLUGIN
```

---

## TASK 10：实现 Spec 读取器 [无需 UE5 环境]

```
目标：实现 YAML Spec 解析。

前置依赖：TASK 09 完成

先读：Specs/templates/scene_spec_template.yaml / Docs/orchestrator_design.md（第 3 节）

创建 Scripts/orchestrator/spec_reader.py:
- read_spec(spec_path) → dict（读取 YAML，解析 scene/defaults/anchors/actors）
- validate_spec(spec_dict) → (bool, list[str])（验证必填字段）

依赖：pip install pyyaml

【验收标准】
- read_spec 可读取模板 Spec
- validate_spec 对模板返回 (True, [])
- 缺少必填字段返回 (False, [错误描述])
```

---

## TASK 11：实现计划生成器 [无需 UE5 环境]

```
目标：将 Spec 转为工具调用计划。

前置依赖：TASK 10 完成

先读：Docs/orchestrator_design.md（第 4 节）

创建 Scripts/orchestrator/plan_generator.py:
- generate_plan(spec_dict, current_actors) → list[dict]
  CREATE（不存在）→ spawn_actor + get_actor_state
  UPDATE（已存在）→ set_actor_transform + get_actor_state

【验收标准】
- 空 actor 列表 → 全部 CREATE
- 已有 actor → 对应 UPDATE，新的 CREATE
```

---

## TASK 12：实现验证器 [无需 UE5 环境]

```
目标：执行结果的容差验证。

前置依赖：TASK 11 完成

先读：Docs/mvp_smoke_test_plan.md（第 5.5 节容差标准）

创建 Scripts/orchestrator/verifier.py:
- verify_transform(expected, actual, tolerances) → {status, mismatches}
  容差与 C++ FBridgeTransform::NearlyEquals 一致：loc≤0.01, rot≤0.01, scale≤0.001
- verify_actor_state(expected_spec, actual_response) → dict

【验收标准】
- 完全匹配 → success；超差 → mismatch + mismatches 列表；容差内 → success
```

---

## TASK 13：实现报告生成器 [无需 UE5 环境]

```
目标：结构化执行报告。

前置依赖：TASK 12 完成

先读：Docs/orchestrator_design.md（第 6 节）

创建 Scripts/orchestrator/report_generator.py:
- generate_report(spec, plan, exec_results, verify_results) → dict
  格式：{spec_path, overall_status, total/passed/failed/mismatched, actors:[], dirty_assets, map_check}
- save_report(report, output_path)

【验收标准】
- overall_status 正确（全 success→success, 有 mismatch→mismatch, 有 failed→failed）
- 报告可写入 JSON 文件
```

---

## TASK 14：实现 Orchestrator 主编排 + 跑通完整流程 [UE5 环境]

```
目标：串联 Spec→计划→执行→验证→报告，默认通过通道 C 调用 C++ Plugin。

前置依赖：TASK 09-13 + TASK 06

先读：Docs/orchestrator_design.md（第 5 节）

创建 Scripts/orchestrator/orchestrator.py:
- run(spec_path, channel=BridgeChannel.CPP_PLUGIN, report_path=None) → dict
  流程：set_channel → read_spec → get_current_project_state → list_level_actors →
  generate_plan → 循环(写接口→读回→verify) → run_map_check + get_dirty_assets →
  generate_report + save_report

错误处理：单个 Actor 失败不中断全部；safe_execute(timeout=30)

【测试】用模板 Spec 执行 run()，检查报告 JSON

【验收标准】
- 通道 C 调用全部接口返回正确 JSON
- 报告 overall_status 为 success 或 mismatch
- 单个失败不中断后续
```
---
---

# 阶段 5：高级验证 + CI/CD

---

## TASK 15：实现 L3 Functional Test [UE5 环境 + C++ 编译]

```
目标：L3 完整 Demo——FTEST_ 测试地图中执行完整 Spec 验证。

前置依赖：TASK 08 + TASK 14

先读：Docs/mvp_smoke_test_plan.md（第 6 节）

创建 L3_FunctionalTestActor.h + .cpp (AAgentBridgeFunctionalTest 继承 AFunctionalTest)
可配置：SpecPath / Tolerances / bUndoAfterTest / BuiltInActorCount

手动操作：创建 FTEST_WarehouseDemo 地图，放置 AAgentBridgeFunctionalTest Actor

【验收标准】
- Session Frontend → Run Level Test → FTEST_WarehouseDemo → 通过
```

---

## TASK 16：实现 Gauntlet CI/CD 编排 [UE5 环境 + C++ 编译]

```
目标：打通 Gauntlet CI/CD 流水线。

前置依赖：TASK 15 完成

先读：Docs/architecture_overview.md（第 8 节）

创建：
1. Gauntlet/AgentBridge.TestConfig.cs（AllTests/SmokeTests/SpecExecution 三种配置）
2. AgentBridgeGauntletController.h + .cpp（OnInit 解析参数 → OnTick 触发测试+轮询 → EndTest）

【验收标准】
- RunUAT RunGauntlet -Test=AgentBridge.SmokeTests → exit code 0
- Gauntlet 自动 启动Editor → 运行测试 → 收集结果 → 停止Editor
```

---

## TASK 17：实现 Phase 2 接口 [UE5 环境 + C++ 编译]

```
目标：追加碰撞/材质写入 + 组件反馈接口。

前置依赖：TASK 05

在 Subsystem 追加：
a) SetActorCollision(ActorPath, ProfileName, ...) + FScopedTransaction
b) AssignMaterial(ActorPath, MaterialPath, SlotIndex) + FScopedTransaction
c) GetComponentState(ActorPath, ComponentName)
d) GetMaterialAssignment(ActorPath)

同步更新 Python 客户端 _CPP_MAP。

【验收标准】
- SetActorCollision 修改碰撞 + Ctrl+Z 撤销
- AssignMaterial 指定材质 + 读回确认
```

---

## TASK 18：扩展 Schema + validate_all [无需 UE5 环境]

```
目标：为 Phase 2 创建 Schema + example，全量校验通过。

前置依赖：TASK 17

创建 Phase 2 的 Schema + example JSON，更新 validate_examples.py 映射表。

【验收标准】
- validate_examples.py --strict 从 8/8 扩展为 10/10 通过
```
---
---

# 阶段 6：集成

---

## TASK 19：完整 Demo 端到端测试 [UE5 环境 + C++ 编译]

```
目标：验证系统从 Spec 到执行到验证到报告的完整链路。

前置依赖：全部 TASK 01-18

执行 7 个验证步骤：
1. Schema 校验：validate_examples.py --strict → 全部通过
2. L1+L2+L3.UITool 全部绿灯：Session Frontend Run All → 20 个测试全绿（L1×11 + L3.UITool×4 + L2×5）
3. L3 Functional Test：FTEST_WarehouseDemo → 通过
4. Orchestrator 端到端：10 Actor Demo Spec → overall_status = success
5. Commandlet 无头执行：-run=AgentBridge -Spec=demo.yaml → exit 0
6. Gauntlet CI/CD：RunUAT RunGauntlet -Test=AgentBridge.AllTests → exit 0
7. 三通道一致性：通道 A/B/C 对同一 Actor 的 get_actor_state 返回值一致

【验收标准】
- 全部 7 个步骤通过
- Schema 10/10 / L1+L2 20 个绿灯 / L3 通过 / Orchestrator success
- Commandlet exit 0 / Gauntlet exit 0 / 三通道一致
```

---

## TASK 20：实现 L3 UI 工具接口 + Automation Driver 集成 [UE5 环境 + C++ 编译]

```
目标：实现 3 个 L3 UI 工具接口 + Automation Driver 封装层 + L3→L1 交叉比对 + 测试。

前置依赖：TASK 07 完成（AgentBridgeTests Plugin 可用）

先读这些文件：
- Docs/architecture_overview.md（§3.5 三层受控工具体系）
- Docs/tool_contract_v0_1.md（§7.5 L3 UI 工具契约）
- Docs/ue5_capability_map.md（§4.3.4 Automation Driver）

创建以下文件：

1. Plugins/AgentBridge/Source/AgentBridge/Public/AutomationDriverAdapter.h
   FAutomationDriverAdapter 封装层（将 Automation Driver 底层操作封装为语义级接口）
   公开方法：IsAvailable / ClickDetailPanelButton / TypeInDetailPanelField / DragAssetToViewport / WaitForUIIdle
   内部方法：GetOrCreateDriver / SelectActorAndOpenDetails / FindWidgetByLabel / FindAssetInContentBrowser / WorldToScreen

2. Plugins/AgentBridge/Source/AgentBridge/Private/AutomationDriverAdapter.cpp
   全部实现（含 IAutomationDriver::FindElement + CreateSequence + By::Text 定位）

3. 在 BridgeTypes.h 中追加：
   - 3 个 L3 错误码：DriverNotAvailable / WidgetNotFound / UIOperationTimeout
   - FBridgeUIVerification 结构体（L3→L1 交叉比对：UIToolResponse + SemanticVerifyResponse + bConsistent + Mismatches + GetFinalStatus）
   - 3 个辅助函数：MakeDriverNotAvailable / MakeWidgetNotFound / MakeUIVerification

4. 在 AgentBridgeSubsystem.h/.cpp 中追加：
   - ClickDetailPanelButton(ActorPath, ButtonLabel, bDryRun) — Category="AgentBridge|UITool"
   - TypeInDetailPanelField(ActorPath, PropertyPath, Value, bDryRun) — Category="AgentBridge|UITool"
   - DragAssetToViewport(AssetPath, DropLocation, bDryRun) — Category="AgentBridge|UITool"
   - IsAutomationDriverAvailable() — Category="AgentBridge|UITool"
   - CrossVerifyUIOperation(UIToolResponse, L1VerifyFunc, L1VerifyParams) — private 交叉比对
   - UIOperationResultToResponse(OperationName, UIResult) — private 转换辅助

5. 在 AgentBridge.Build.cs 中追加 AutomationDriver 模块依赖

6. Plugins/AgentBridgeTests/.../L1_UIToolTests.cpp
   4 个 L1 测试：
   - T1-12: IsAutomationDriverAvailable（可用性查询 + 与 Adapter 一致性）
   - T1-13: ClickDetailPanelButton（参数校验×2 + dry_run + Actor 不存在）
   - T1-14: TypeInDetailPanelField（参数校验×3 + dry_run）
   - T1-15: DragAssetToViewport（参数校验 + dry_run + 实际执行 + L3→L1 交叉比对）
   Driver 不可用时 graceful degradation（AddWarning + return true，不阻塞 CI）

7. Plugins/AgentBridgeTests/.../L2_UIToolClosedLoopSpec.spec.cpp
   2 个 L2 Automation Spec：
   - LT-04: DragAssetToViewportLoop（5 个 It：L3 执行成功 + L1 Actor 数增加 + L3/L1 交叉比对 consistent + L1 GetActorState 位置容差 100cm + Undo 恢复）
   - LT-05: TypeInFieldLoop（3 个 It：L1 基线读回 + L3 执行不崩溃 + L3 操作后 L1 仍可用）

8. Scripts/bridge/ui_tools.py
   L3 Python 客户端：_CPP_UI_TOOL_MAP 映射 + 三通道分发（仅 CPP_PLUGIN + MOCK）+ cross_verify_ui_operation 辅助

L3 测试核心模式：
  L3 UI 操作 → L3 返回值
  L1 独立读回 → L1 返回值
  交叉比对两者 → 一致=success, 不一致=mismatch（含字段级差异）

L3 容差标准（区别于 L1 的 0.01cm）：
  location: ≤ 100cm（UI 操作精度低于 API 调用）

【测试】
1. 编译通过（含 AutomationDriver 模块依赖）
2. Session Frontend 可见 4 个 L3.UITool 测试 + 2 个 L2.UITool Spec
3. IsAutomationDriverAvailable 可调用且返回确定值
4. ClickDetailPanelButton 空参数返回 validation_error
5. DragAssetToViewport dry_run 返回 tool_layer=L3_UITool
6. 如 Driver 可用：DragAssetToViewport 实际执行 → CrossVerifyUIOperation consistent=true
7. 如 Driver 不可用：L3 测试 AddWarning + return true（不阻塞）

【验收标准】
- 编译零 error
- Session Frontend：L3.UITool 4 个 + L2.UITool 2 个 可见
- Driver 可用时：DragAssetToViewport → L1 ListLevelActors 验证 Actor 出现 → 交叉比对 consistent
- Driver 不可用时：全部 L3 测试 graceful degradation（SKIP，不 FAIL）
- Python Mock 模式：ui_tools.py 全部 3 个接口返回 success
```

---
---

# 附录：任务依赖关系图

```
阶段 1
TASK 01 (目录结构) → TASK 02 (Schema 校验)
  ↓
阶段 2（C++ Plugin 核心）
TASK 03 (Plugin 骨架) → TASK 04 (查询接口 7个) → TASK 05 (写+验证+构建) → TASK 06 (Commandlet+UAT)
  ↓                                                                            ↓
阶段 3（测试）                                                          阶段 4（Python+Orchestrator）
TASK 07 (L1×11) → TASK 08 (L2×3)                                       TASK 09 → 10 → 11 → 12 → 13 → TASK 14 [UE5]
  ↓                    ↓                                                                                ↓
  ├── TASK 20 (L3 UI 工具 + Automation Driver)  ← 依赖 TASK 07                                         │
  │                    ↓                                                                                │
  └────────────────────┴────────────── 汇合 ──────────────────────────────────────────────────────────────┘
                                         ↓
阶段 5（高级验证+CI/CD）
TASK 15 (L3 Functional) → TASK 16 (Gauntlet) → TASK 17 (Phase 2) → TASK 18 (Schema 扩展)
  ↓
阶段 6
TASK 19 (完整 Demo 端到端，含 L3 UI 工具验证)
```

环境要求汇总：
- 无需 UE5：TASK 01-02, 09-13, 18
- 需要 UE5 + C++：TASK 03-08, 14-17, 19-20
- 并行提示：TASK 09-14（Python）可与 TASK 07-08（测试 Plugin）并行开发
- 并行提示：TASK 20（L3 UI 工具）可与 TASK 09-14（Python）并行开发（依赖 TASK 07）
