# LLD/01 — C++ Subsystem 详细设计

> 版本: v1 (2026-05-26)
> 范围: AgentBridge Plugin C++ 核心层 6 个类
> 上游: `Docs/design/HLD.md` §模块拓扑 + `Docs/requirements/SRS.md` §3.1 + `Docs/FEATURE_INVENTORY.md` F-CPP-01..06
> 契约: `Docs/contracts/tool_contract.md` §2-§4(L1/L2/L3 协议) + `Docs/contracts/field_specification.md`(USTRUCT 字段规范)
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

本 LLD 覆盖 AgentBridge Plugin C++ 层 6 个核心结构(对应 `FEATURE_INVENTORY` F-CPP-01..06):一个 `UEditorSubsystem` 主入口、一个 `UCommandlet` 无窗口入口、一个 UAT 子进程包装 `FUATRunner`、一个 L3 UI 自动化适配器 `FAutomationDriverAdapter`、共享 USTRUCT 类型库 `BridgeTypes`、以及 IModuleInterface 实现 `FAgentBridgeModule`。它们共同承担 AgentBridge 框架在 UE5 编辑器进程内的所有原生执行面 —— 对外通过 `BlueprintCallable` 自动暴露给 Remote Control HTTP API 与 Python 桥接,对内通过 `FScopedTransaction` 纳入 UE5 Undo/Redo 体系。本文档聚焦内部分层、关键方法签名、数据流、扩展点、已知约束与 UE 5.7 迁移变更点,目的是让任何接手者能够在不阅读 6847 行 C++ 源码全文的前提下,准确定位修改位置并评估改动成本。

## 2. 内部分层

| 类名 | 角色 | F-CPP ID | 文件 |
|---|---|---|---|
| `UAgentBridgeSubsystem` | UEditorSubsystem 主入口,L1/L3 工具实现体 | F-CPP-01 | `AgentBridgeSubsystem.{h,cpp}`(523 + 2738 行) |
| `UAgentBridgeCommandlet` | UCommandlet 无窗口入口,`-run=AgentBridge` | F-CPP-02 | `AgentBridgeCommandlet.{h,cpp}`(55 + 742 行) |
| `FUATRunner` | UAT BuildCookRun / RunGauntlet 子进程包装 | F-CPP-03 | `UATRunner.{h,cpp}`(73 + 226 行) |
| `FAutomationDriverAdapter` | L3 UI 自动化适配(IAutomationDriverModule) | F-CPP-04 | `AutomationDriverAdapter.{h,cpp}`(257 + 1608 行) |
| `BridgeTypes`(USTRUCT 集) | 共享类型库(响应壳 / 错误码 / Transform) | F-CPP-05 | `BridgeTypes.h`(585 行) |
| `FAgentBridgeModule` | IModuleInterface 实现,启动日志 + 模块注册 | F-CPP-06 | `AgentBridgeModule.cpp`(40 行) |

按职责自上而下分四层:**主入口 / 无窗口入口** 是外部触发点,分别承担"编辑器进程内交互模式"与"批处理无窗口模式"两条执行通道;**工具执行体** 是真正干活的层 —— L1 语义工具(查询 9 个 + 写 6 个 + 验证 3 个 + 构建 1 个 + 辅助 6 个)全部在 `UAgentBridgeSubsystem` 内直接实现,L3 UI 工具委托给静态适配类 `FAutomationDriverAdapter`;**类型库** `BridgeTypes` 提供跨所有工具复用的统一响应壳与错误码;**模块加载** `FAgentBridgeModule` 承担 Plugin 生命周期钩子。值得注意的是,`UAgentBridgeSubsystem` 同时充当了 L1 实现体与 L3 协调者两个角色 —— 这是为了让 RC HTTP 端点能用一个 BlueprintCallable 函数同时覆盖语义执行与 UI 模拟,避免外部调用方分两次反射。

## 3. 关键类/函数签名

> 仅列与外部协议或迁移强相关的方法,**不 dump 整文件**;完整方法表参见对应 `.h` 文件。每个方法签名后 1 行中文用途说明,便于 IDE 检索后快速定位。

### 3.1 `UAgentBridgeSubsystem`(F-CPP-01)

```cpp
UCLASS()
class AGENTBRIDGE_API UAgentBridgeSubsystem : public UEditorSubsystem
```

- `virtual void Initialize(FSubsystemCollectionBase& Collection) override;` — Editor 启动期自动调用,打 v0.3.0 启动日志
- `virtual void Deinitialize() override;` — 清空 `PendingUIOperations` Map,避免残留 future
- `UFUNCTION(BlueprintCallable) FBridgeResponse GetCurrentProjectState();` — L1 查询入口,返回工程上下文
- `UFUNCTION(BlueprintCallable) FBridgeResponse ListLevelActors(const FString& ClassFilter);` — L1 查询,基于 `TActorIterator` 遍历 Editor World
- `UFUNCTION(BlueprintCallable) FBridgeResponse GetActorState(const FString& ActorPath);` — L1 查询,读 Transform/Collision/Tags
- `UFUNCTION(BlueprintCallable) FBridgeResponse SpawnActor(LevelPath, ActorClass, Name, FBridgeTransform, bDryRun);` — L1 写,FScopedTransaction 纳 Undo
- `UFUNCTION(BlueprintCallable) FBridgeResponse SetActorTransform(ActorPath, Transform, bDryRun);` — L1 写,Undo-friendly
- `UFUNCTION(BlueprintCallable) FBridgeResponse ImportAssets(SourceDir, DestPath, bReplace, bDryRun);` — L1 写,委托 `UAssetToolsHelpers`
- `UFUNCTION(BlueprintCallable) FBridgeResponse BuildProject(Platform, Configuration, bDryRun);` — L1 构建,内部走 `FUATRunner::BuildCookRun`
- `UFUNCTION(BlueprintCallable) FBridgeResponse ClickDetailPanelButton(ActorPath, ButtonLabel, bDryRun);` — L3 UI,委托 `FAutomationDriverAdapter`
- `UFUNCTION(BlueprintCallable) FBridgeResponse StartUIOperation(OpType, ActorPath, Target, Value, Timeout, bDryRun);` — L3 异步原型入口
- `UFUNCTION(BlueprintCallable) FBridgeResponse QueryUIOperation(const FString& OperationId);` — L3 异步轮询
- `FBridgeUIVerification CrossVerifyUIOperation(const FBridgeResponse& UIToolResponse, FString L1VerifyFunc, FString L1VerifyParams);` — L3→L1 交叉比对
- `private: AActor* FindActorByPath(const FString& ActorPath) const;` — 内部辅助,`TActorIterator` + 路径匹配
- `private: UWorld* GetEditorWorld() const;` — 内部辅助,`GEditor->GetEditorWorldContext().World()`

Subsystem 是本 LLD 的最重类(`.cpp` 共 2738 行,几乎涵盖了所有 L1/L3 工具实现);上面只列与外部协议、Schema 对齐、Transaction 边界、L3 异步链强相关的代表性 UFUNCTION,完整 25+ 个工具表参见 `AgentBridgeSubsystem.h`。

### 3.2 `UAgentBridgeCommandlet`(F-CPP-02)

```cpp
UCLASS()
class AGENTBRIDGE_API UAgentBridgeCommandlet : public UCommandlet
```

- `virtual int32 Main(const FString& Params) override;` — CLI 总入口,3 种模式分发(Spec/RunTests/Tool)
- `private: void ParseParams(const FString& Params);` — `FParse::Value` 抽 `-Spec=` / `-RunTests=` / `-Tool=` / `-Report=`
- `private: int32 RunSpec();` — Spec YAML 模式,委托 Python Orchestrator
- `private: int32 RunTests();` — 自动化测试模式,内部触发 `Automation RunTests <Filter>`
- `private: int32 RunSingleTool();` — 单工具模式,直接调 `UAgentBridgeSubsystem::<Tool>()`
- `private: static int32 StatusToExitCode(EBridgeStatus Status);` — 退出码映射(0=success / 1=warning|mismatch / 2=failed)
- `private: void WriteReport(const FString& JsonContent);` — 写 `-Report=` 指定路径的 JSON

Commandlet 是无窗口入口,三种模式互斥(Spec / RunTests / Tool),`Main` 函数按命令行参数分发,统一收尾走 `WriteReport` + 退出码映射;CI 仅通过 stdout 中的 `ResultJson=` 行采集结构化结果。

### 3.3 `FUATRunner`(F-CPP-03)

```cpp
class AGENTBRIDGE_API FUATRunner
```

- `FUATRunner();` — 构造期自动调用 `DetectRunUATPath()` 探测 `RunUAT.bat`
- `bool IsUATAvailable() const;` — 检查 `RunUATPath` 是否非空
- `FUATRunResult BuildCookRun(FString Platform, FString Configuration, bool bSync);` — 编译/烹饪/打包
- `FUATRunResult RunAutomationTests(FString Filter, FString ReportPath, bool bSync);` — UAT 路径运行自动化测试
- `FUATRunResult RunGauntlet(FString TestConfigName, bool bSync);` — 启动 Gauntlet 会话
- `FUATRunResult RunCustomCommand(FString Command, bool bSync);` — 任意 UAT 命令通道
- `private: FString DetectRunUATPath() const;` — 自动探测 `RunUAT.bat`/.sh
- `private: FUATRunResult ExecuteUAT(const FString& Args, bool bSync);` — 底层 `FPlatformProcess::CreateProc` 调度

UAT Runner 是非 UCLASS 的纯 C++ 类,所有方法返回 `FUATRunResult`(同步模式带退出码 / 异步模式仅 `bLaunched=true`);其上层 `BuildProject` / `RunAutomationTests` UFUNCTION 在 Subsystem 里封装。

### 3.4 `FAutomationDriverAdapter`(F-CPP-04)

```cpp
class AGENTBRIDGE_API FAutomationDriverAdapter // 静态方法集,不继承
```

- `static bool IsAvailable();` — `FModuleManager::Get().IsModuleLoaded("AutomationDriver")` 探测
- `static FUIOperationResult ClickDetailPanelButton(ActorPath, ButtonLabel, Timeout);` — L3 同步点击
- `static FUIOperationResult ClickDetailPanelButtonOffGameThread(ActorPath, ButtonLabel, Timeout);` — L3 异步版本,避开 RC 同步链 GameThread 死锁
- `static FUIOperationResult TypeInDetailPanelField(ActorPath, PropertyPath, Value, Timeout);` — L3 同步输入
- `static FUIOperationResult DragAssetToViewport(AssetPath, FVector DropLocation, Timeout);` — L3 拖拽,走 Editor 原生 OnDropped
- `static bool WaitForUIIdle(float TimeoutSeconds);` — 每次操作后必调,确保 UI Idle
- `private: static TSharedPtr<IAutomationDriver, ESPMode::ThreadSafe> GetOrCreateDriver();` — Driver 实例缓存
- `private: static bool SelectActorAndOpenDetails(const FString& ActorPath);` — Click/Type 共同前置
- `private: static TSharedPtr<SWidget> FindWidgetByLabel(TSharedPtr<SWidget> Root, FString Label);` — Slate 树文本匹配
- `private: static bool WorldToScreen(const FVector& WorldLoc, FVector2D& OutScreen);` — 世界→屏幕坐标转换

### 3.5 `BridgeTypes`(F-CPP-05)

```cpp
UENUM EBridgeStatus { Success, Warning, Failed, Mismatch, ValidationError };
UENUM EBridgeErrorCode { None, InvalidArgs, ActorNotFound, AssetNotFound, ClassNotFound,
                        EditorNotReady, ToolExecutionFailed, Timeout, PermissionDenied,
                        DriverNotAvailable, WidgetNotFound, UIOperationTimeout };
```

5 个 USTRUCT 主结构(完整字段表参见 `BridgeTypes.h`,此处只列签名行):

- `USTRUCT FBridgeError { FString Code/Message/Details; void SyncForRemote(); }` — 错误对象(双字段:大写内部 + 小写 RC 镜像)
- `USTRUCT FBridgeTransform { FVector Location; FRotator Rotation; FVector RelativeScale3D; static FromActor(AActor*); bool NearlyEquals(...); }` — Transform 读写 + 容差比对(默认位置 0.01cm,旋转 0.01°,缩放 0.001)
- `USTRUCT FBridgeObjectRef { FString ActorName/ActorPath/AssetPath; }` — 写操作引用(created/modified/deleted 列表元素)
- `USTRUCT FBridgeResponse { EBridgeStatus; FString Summary; TSharedPtr<FJsonObject> Data; TArray<FString> Warnings; TArray<FBridgeError> Errors; bool bTransaction; FString ToJsonString() const; }` — 统一响应壳,本框架对外协议核心
- `USTRUCT FBridgeUIVerification { FBridgeResponse UIToolResponse/SemanticVerifyResponse; bool bConsistent; TArray<FString> Mismatches; EBridgeStatus GetFinalStatus() const; }` — L3→L1 交叉比对结构
- `namespace AgentBridge::` 内 6 个全局辅助:`MakeSuccess/MakeFailed/MakeValidationError/MakeMismatch` 响应构造 + `IsEditorReady`(GEditor + 非 PIE + EditorWorld 三段校验)+ `ValidateTransform/ValidateRequiredString` 参数预校验

### 3.6 `FAgentBridgeModule`(F-CPP-06)

```cpp
class FAgentBridgeModule : public IModuleInterface
```

- `virtual void StartupModule() override;` — 输出 `[AgentBridge] Plugin loaded, version 0.3.0` 日志(LoadingPhase: PostEngineInit)
- `virtual void ShutdownModule() override;` — 卸载日志
- `IMPLEMENT_MODULE(FAgentBridgeModule, AgentBridge)` — 模块注册宏

## 4. 数据流

数据流分 5 个场景,涵盖 L1 查询同步链、L1 写入(含 dry_run + Transaction)、L3 UI(含交叉比对)、Commandlet 入口、UAT 子进程出口。

### 4.1 L1 查询数据流(典型同步链)

```
Python (query_tools.py)
  └─PUT /remote/object/call─▶ RC HTTP :30010
                              └─reflect─▶ UAgentBridgeSubsystem::GetActorState(ActorPath)
                                            ├─FindActorByPath (TActorIterator)
                                            ├─读 Transform/Collision/Tags
                                            └─MakeSuccess(...) ─▶ FBridgeResponse.ToJsonString()
                              ◀────────── JSON
  ◀──────── HTTP 200 ────────
```

查询链路完全只读,不进 Transaction;失败路径走 `MakeFailed`(`ACTOR_NOT_FOUND` / `EDITOR_NOT_READY` 等),响应壳 status 字段映射为 `failed` / `validation_error`,RC HTTP 仍返回 200,业务层据 status 字段判断。

### 4.2 L1 写数据流(含 dry_run + Transaction)

```
... ─▶ UAgentBridgeSubsystem::SetActorTransform(ActorPath, T, bDryRun)
        ├─IsEditorReady() (GEditor + 非 PIE + EditorWorld)
        ├─ValidateTransform(T)
        ├─bDryRun ? 直接返回成功(不改状态)
        ├─FScopedTransaction("AgentBridge: SetActorTransform")
        ├─Actor->Modify() + SetActorLocationAndRotation()
        └─bTransaction=true, MakeSuccess(...)
```

写工具的关键约束:`bDryRun=true` 时绝不进入 Transaction、不调用任何 `Modify()`,只做参数校验并返回 `summary` 注明"dry-run";同时 `bTransaction` 字段保持 `false`,让上层 Orchestrator 能识别此次调用未真正消耗 Undo Stack。

### 4.3 L3 UI 数据流(含交叉比对)

```
... ─▶ UAgentBridgeSubsystem::ClickDetailPanelButton(ActorPath, Label, bDryRun)
        ├─IsAutomationDriverAvailable() (FModuleManager 探测)
        ├─FAutomationDriverAdapter::ClickDetailPanelButton(...)
        │   ├─SelectActorAndOpenDetails (GEditor->SelectActor)
        │   ├─GetOrCreateDriver (IAutomationDriverModule::CreateDriver)
        │   ├─FindWidgetByLabel (Slate 树文本匹配)
        │   ├─DriverElement->Click()
        │   └─WaitForUIIdle()
        ├─UIOperationResultToResponse() ─▶ L3 response
        └─CrossVerifyUIOperation(L3resp, "GetActorState", ActorPath)
            ├─递归调 L1 GetActorState ─▶ L1 readback
            └─字段级 diff ─▶ FBridgeUIVerification.GetFinalStatus()
                            (success / mismatch / failed)
```

L3 链路与 L1 最大的差别是必须经过 `CrossVerifyUIOperation` 的二次读回 —— 因为 UI 模拟无法直接知道编辑器真实状态,只能通过 L1 语义层独立读回值再做字段级 diff,这也是 `EBridgeStatus::Mismatch` 状态枚举存在的根本原因。异步原型链(`StartUIOperation` / `QueryUIOperation`)把"等待 UI Idle"从 RC 同步请求中拆出来,改为客户端轮询,避免 GameThread 死锁(参见 §6)。

### 4.4 Commandlet 入口数据流

```
UE5Editor-Cmd.exe -run=AgentBridge -Tool=GetCurrentProjectState -Report=out.json
  └─UAgentBridgeCommandlet::Main(Params)
       ├─ParseParams (FParse::Value)
       ├─分发 RunSpec / RunTests / RunSingleTool
       │   └─RunSingleTool: GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>()->Tool()
       ├─StatusToExitCode(FBridgeResponse.Status) → ExitCode
       ├─WriteReport(LastResultJson) → out.json
       └─return ExitCode (0/1/2)
```

### 4.5 UAT 子进程数据流

```
UAgentBridgeSubsystem::BuildProject(Platform, Config, bDryRun)
  └─FUATRunner runner; runner.BuildCookRun(Platform, Config, bSync=false)
       ├─DetectRunUATPath()
       ├─拼接 args: -project=... -platform=Win64 -configuration=Development ...
       ├─ExecuteUAT: FPlatformProcess::CreateProc(RunUATPath, args, ...)
       └─FUATRunResult { bLaunched, bCompleted, ExitCode, StdOut, StdErr }
```

## 5. 扩展点

- **新增 L1 工具**:在 `UAgentBridgeSubsystem.h` 加一行 `UFUNCTION(BlueprintCallable, Category="AgentBridge|Query") FBridgeResponse <ToolName>(...);`,cpp 实现严格遵循 `IsEditorReady → 参数校验(ValidateRequiredString / 自定义)→ 业务执行 → MakeSuccess/MakeFailed` 四段式骨架;若是写工具还要在业务执行前包 `FScopedTransaction`,在最末 `SyncForRemote()` 之前设 `bTransaction=true`。Schema 端必须在 `Plugins/AgentBridge/Schemas/` 同步加入新工具的输入参数 schema 与反馈契约,否则 jsonschema 校验会拒绝。
- **新增 USTRUCT 字段**:在 `BridgeTypes.h` 内对应 USTRUCT 追加 `UPROPERTY(BlueprintReadWrite, Category = "AgentBridge")` 字段,小写镜像字段记得在 `SyncForRemote()` 中同步,`ToJson()` 内补 `SetStringField` / `SetArrayField` 等;若新增字段需要参与容差比对,要同步改 `NearlyEquals` 实现。
- **新增 Channel**:当前外部通道有 `PYTHON_EDITOR` / `REMOTE_CONTROL` / `CPP_PLUGIN` / `MOCK`(在 Bridge 侧定义);C++ 不直接感知 Channel —— 凡是标 `BlueprintCallable` 的 UFUNCTION 都会被 RC 自动暴露到 `/remote/object/call`。新增 WebSocket / gRPC 通道走 Plugin 侧 transport 适配,Subsystem 不需要改。
- **新增 Commandlet 参数**:在 `AgentBridgeCommandlet.h` 加成员变量,在 `ParseParams` 内加 `FParse::Value(*Params, TEXT("NewKey="), NewVar);`,在 `Main()` 内或对应模式函数(`RunSpec/RunTests/RunSingleTool`)内消费。退出码语义遵循 `StatusToExitCode` 既定 0/1/2 三档,**不要新增退出码档位** —— CI 与上层 Orchestrator 都按这三档分流。
- **新增 L3 UI 操作类型**:在 `FAutomationDriverAdapter` 内加 `static FUIOperationResult X(...)`,Subsystem 侧暴露 `UFUNCTION` 包装,内部统一走 `IsAutomationDriverAvailable → Adapter::X → UIOperationResultToResponse → CrossVerifyUIOperation` 流程。异步版本必须实现 `XOffGameThread` 或 `XAsyncPrototype` 双轨,避免阻塞 RC 同步链(参见 §6 GameThread 死锁陷阱)。

## 6. 已知约束与陷阱

- **UEditorSubsystem 生命周期约束**:`Initialize` 在 Editor 启动 + 模块 PostEngineInit 阶段调用,**不能在 game runtime 用**;Standalone/Server target 不会实例化该 Subsystem,这也是为何 `.uplugin` 标 `Type: Editor`。Commandlet 模式下 Subsystem 仍会被实例化(因为 Commandlet 也跑在 Editor 进程内),所以无窗口入口能复用全部 L1 工具。
- **`EditorLevelLibrary` 经 RC 不可远程稳定调用**:UE 5.5.4 实测 `EditorLevelLibrary.GetEditorWorld()` 经 RC 反射调用会返回 null,所以 Python 侧 `query_tools.py` 绕道走 `/remote/object/property` 直读 RelativeLocation。本约束与 BC-016/BC-017 P1 confirmed 强相关 —— 升 5.7 后 EditorLevelLibrary 若完全移除,Python 侧链路必须迁移到 `UnrealEditorSubsystem` / `EditorActorSubsystem`,届时该陷阱自动消失(同时也是迁移测试的回归基线)。
- **`IncludeOrderVersion = Unreal5_5` 编译约束**:Target.cs / EditorTarget.cs 硬编码该枚举,新增 5.6/5.7 引擎头文件包含顺序会触发 IWYU warning;迁移时需同步改枚举值(参见 §7 BC-010 详述)。
- **USTRUCT 反射限制**:`FBridgeResponse::Data` 用 `TSharedPtr<FJsonObject>` 而非嵌套 USTRUCT —— 因为 USTRUCT 不能嵌套 `TArray<TArray<...>>` 等递归容器,RC 反射也会丢字段。所有业务 data 字段统一走 JSON Object 序列化,这是本框架"响应 schema 灵活但 USTRUCT 反射严格"两种约束之间的妥协方案。
- **`FScopedTransaction` 不能跨函数**:必须在写工具单次调用内开关;若需要长事务(如 ImportAssets 批量导入多个资产),要自己管理 `GEditor->BeginTransaction/EndTransaction` 配对,代价是 Undo 回滚边界不再与单工具一对一对齐 —— 当前所有 6 个写工具都坚持"一调一事务"原则。
- **L3 UI 同步链 GameThread 死锁**:RC 同步请求本身跑在 GameThread,而 `IAutomationDriver::Wait` 若也在 GameThread 等待会 deadlock;`ClickDetailPanelButtonOffGameThread` / `*AsyncPrototype` 系列就是为此而生 —— 长 UI 操作必须走 `StartUIOperation` + `QueryUIOperation` 轮询,客户端按 `data.operation_state`(pending/running/success/failed)状态机消费。
- **`AutomationDriverAdapter::CachedDriver` 静态缓存**:Driver 实例是进程级静态成员,若 AutomationDriver 模块在运行时被卸载/重载(罕见但理论可能),需要手动清空 `CachedDriver`,否则会持有失效指针;当前实现假设模块生命周期与 Editor 一致,未做主动失效检测。

## 7. UE 5.7 迁移变更点

> 引用 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 / §4(P1 7 条裁决:1 false-positive + 6 confirmed;P2/P3 全部 suspected,留 5.7 实测裁决)。**P1 confirmed 范围严格限于 msc 已裁决 6 条**,其余条目按 P2/P3 标 suspected;本节按 "[BC-NNN] api_or_key → 影响方法签名 → 迁移行动" 三段式列出,与 BC-008/010 P1 confirmed 两条直接影响本 LLD 内类签名编译性的条目优先,P2 suspected 的符号面紧随其后。

- **[BC-008] `EditorScriptingUtilities` 模块依赖 — P1 confirmed**
  影响:`AgentBridge.Build.cs:44` `PrivateDependencyModuleNames.Add("EditorScriptingUtilities")` 与 `AgentBridgeTests.Build.cs:24`。
  迁移行动:删除该依赖,Subsystem 内部所有借道该模块的 `UEditorLevelLibrary::*` / `UEditorAssetLibrary::*` 调用迁移到 `UEditorActorSubsystem` / `ULevelEditorSubsystem` / `UEditorAssetSubsystem` 的 `GetEditorSubsystem<>` 获取方式;`.uplugin:30-32` 同步移除 `EditorScriptingUtilities` Plugin 启用项。

- **[BC-010] `IncludeOrderVersion = Unreal5_5` — P1 confirmed**
  影响:`Source/Mvpv4TestCodex.Target.cs:12` + `Source/Mvpv4TestCodexEditor.Target.cs:11` 硬编码 `EngineIncludeOrderVersion.Unreal5_5`。
  迁移行动:改为 `Unreal5_6` 或 `Unreal5_7`(取决于 5.7 源码枚举),不改会触发 IncludeOrderVersion warning(在 BuildSettingsVersion.V5 下可能被升级为 error)。

- **[BC-001] `UEditorSubsystem` 父类 lifecycle hook — P2 suspected**
  影响:`UAgentBridgeSubsystem::Initialize(FSubsystemCollectionBase&)` / `Deinitialize()` 方法签名。
  迁移行动:5.7 若引入异步 `InitializeAsync` 或 `OnEditorReady` 等新钩子,需评估是否把当前的 `Initialize` 内的延迟初始化逻辑迁过去;当前 PendingUIOperations Map 清理逻辑放 `Deinitialize` 仍是稳的。**严格标 P2 suspected,5.7 实测后再裁决**。

- **[BC-002] `FModuleManager` 模块名 — P2 suspected**
  影响:`AgentBridgeSubsystem.cpp:143,148,1144,1216` + `AutomationDriverAdapter.cpp:67,72,848,854,926,928` 共 ≥10 处 `LoadModuleChecked` / `IsModuleLoaded` 命中 `"LevelEditor"` / `"AssetTools"` / `"AutomationDriver"`。
  迁移行动:5.7 若模块改名(如 `LevelEditor` → `LevelEditorCore`)会编译失败;迁移期跑 `RunUAT BuildEditor` 看是否报 unresolved module。

- **[BC-004] `FSlateApplication::SetCursorPos/Tick` — P2 suspected**
  影响:`AutomationDriverAdapter.cpp:630,647,675,743,775,809+` 22 处 Slate input 注入。
  迁移行动:5.7 若改 Tick 调度(PreTick/PostTick split),L3 UI 套件回归测试可能整体失效;L3 是迁移最高风险面,务必在 5.7 Editor 内重跑 `python Plugins/AgentBridge/Tests/run_system_tests.py` L3 子集。

- **[BC-005] `UCommandlet` 父类 — P2 suspected**
  影响:`UAgentBridgeCommandlet::Main(const FString& Params)` 签名。
  迁移行动:`UCommandlet` 在 5.6+ 仍保留,5.7 不太可能移除;若移除则迁到 `EditorUtilityScript` + Console Command。

- **[BC-006] `FAutomationTestBase` + `IMPLEMENT_SIMPLE_AUTOMATION_TEST` — P2 suspected**
  影响:`AgentBridgeTests/Source/.../*.cpp` 共 20+ 处 simple-test 宏使用。
  迁移行动:5.7 仍保留 simple 宏概率高;若 spec 风格强推,需逐文件改写为 `IMPLEMENT_SPEC` —— 不在本 LLD 触达。

- **[BC-009] `EditorSubsystem` 模块依赖 — P3 suspected**
  影响:`AgentBridge.Build.cs:32` `PublicDependencyModuleNames.Add("EditorSubsystem")`。
  迁移行动:5.6→5.7 无 deprecation 记录,预期稳定;5.7 编译时若失败再回退到 `UnrealEd`。

- **[BC-011] `BuildSettingsVersion.V5` — P2 suspected**
  影响:`Target.cs:11` + `EditorTarget.cs:10`。
  迁移行动:5.7 若引入 V6,V5 仍兼容但有 "newer version available" 提示;非强制升级,与 BC-010 一起改更稳。

- **[BC-014] `AgentBridge.Build.cs` 模块依赖总览 — P2 suspected**
  影响:`AgentBridge.Build.cs:27-93` 含 `EditorStyle` 模块(5.5 已 deprecated 合入 Slate)。
  迁移行动:5.7 若 `EditorStyle` 完全移除,需替换为 `SlateCore` + `Slate` 内的 style 接口。

### 迁移优先级与回归路径

按优先级排序:**P1 confirmed 两条(BC-008 EditorScriptingUtilities + BC-010 IncludeOrderVersion)是 5.7 编译通过的必要条件**,必须先改 —— 改完后跑 `RunUAT BuildEditor`,无 unresolved module 错误即过门;**P2 suspected 7 条(BC-001/002/004/005/006/011/014)是符号面 API 变更风险**,需 5.7 编译时观察 deprecation warning 数量;若某条变成 error,按对应迁移行动落实。**P3 一条(BC-009)** 仅在前两轮全过后再回扫。回归测试统一走 `python Plugins/AgentBridge/Tests/run_system_tests.py` 全套 240 条,L3 UI 子集若失败优先怀疑 BC-002/BC-004,L1 子集若失败优先怀疑 BC-008 衍生 API 缺失。

---

**关联文件**: `Docs/design/HLD.md` §1-§4 / `Docs/requirements/SRS.md` §3.1 / `Docs/FEATURE_INVENTORY.md` F-CPP-01..06 / `Docs/contracts/tool_contract.md` §2-§4(L1/L2/L3 协议) / `Docs/contracts/field_specification.md`(USTRUCT 字段) / `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4
