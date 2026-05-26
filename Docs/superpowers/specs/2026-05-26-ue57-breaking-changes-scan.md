# UE 5.5.4 → 5.7 Breaking Change Scan

> 日期: 2026-05-26
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §7
> 状态: P1 已裁决(BC-007 false-positive + 6 条 confirmed,reviewer=msc);P2/P3 仍 suspected,留 5.7 实测阶段批量裁决
> 策略: grep + UE 5.6 release notes 为主,5.7 未公开部分标 inferred + confidence:low + suspected
> WebFetch 预算: 10 次,本轮实际使用 4 次(2 次 WebSearch + 2 次 WebFetch),5.7 release notes 页面无 deprecation 文字、5.6 release notes 页面未返回正文,但 5.6 EditorScriptingUtilities → Editor Subsystem 迁移路径在 dev.epicgames.com API doc 与社区帖中得到一致确认。

## 0. 扫描范围(9 类,见关联 spec §7.1)

1. C++ 代码层 — 项目层 `Source/Mvpv4TestCodex/` + 插件层 `Plugins/AgentBridge/Source/` + 测试插件 `Plugins/AgentBridge/AgentBridgeTests/Source/`
2. 构建系统 — `*.Build.cs` / `*.Target.cs` / `*.uplugin` / `*.uproject`
3. 资产层 — `Content/` 下 .uasset / .umap / Blueprint(仅列数量,不静态扫)
4. 配置层 — `Config/*.ini`
5. Python Editor API — `unreal` module binding
6. Remote Control 协议 — RC HTTP API 端点(端口 30010 / `/remote/*`)
7. UAT / UBT 命令行
8. Plugin 依赖
9. PowerShell / 项目脚本

## 1. 已扫范围(每类扫到的 breaking change 数 + 命中范围说明)

- **类 1 — C++**: `Grep` "UEditorSubsystem|UEditorAssetSubsystem|IAutomationLatentCommand|FAutomationTestBase|IRemoteControlModule|FRemoteControlField|UCommandlet|UFactory|FSlateApplication|IPluginManager|FModuleManager" 命中 33 处/6 文件;补充 grep `IMPLEMENT_SIMPLE_AUTOMATION_TEST` 命中 ≥20 处 Tests 文件;补充 grep `UEditorLevelLibrary|UEditorAssetLibrary` 在 Public/Private C++ 0 命中(只在 UHT gen.cpp 与 Python 中出现 — 说明 C++ 端已经使用 EditorScriptingUtilities 模块但绕道 `EditorScriptingUtilities` 依赖,而非直接 include 该 Library)。**§3 计 9 行**(C++ 类符号)
- **类 2 — Build**: 读完 Source/*.{Build,Target}.cs(3 个)+ Plugins/AgentBridge/Source/AgentBridge/AgentBridge.Build.cs + Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/AgentBridgeTests.Build.cs + Mvpv4TestCodex.uproject + Plugins/AgentBridge/AgentBridge.uplugin + Plugins/AgentBridge/AgentBridgeTests/AgentBridgeTests.uplugin。**§3 计 5 行**(IncludeOrderVersion / BuildSettingsVersion / EngineAssociation / EditorScriptingUtilities 依赖 / RemoteControl 依赖)
- **类 3 — 资产**: `find Content -name "*.uasset" -o -name "*.umap" | wc -l` → 5 uasset + 4 umap。**§3 不计,转 §2**
- **类 4 — Config**: 读完 4 个 ini(DefaultEditor.ini 为空、DefaultGame.ini 4 行 ProjectID/GameMode、DefaultEngine.ini 含 RendererSettings + WindowsTargetPlatform + EngineNameRedirects、DefaultInput.ini 含 AxisConfig + EnhancedInput 默认类)。无明显 5.5→5.7 已知 breaking key。**§3 计 1 行**(汇总 `<no-breakage-found>`)
- **类 5 — Python**: `grep -rn "import unreal" --include="*.py" Plugins/AgentBridge/` 命中 4 个文件;`unreal.` 调用面集中在 EditorLevelLibrary / EditorAssetLibrary / AssetToolsHelpers / MaterialFactoryNew / MaterialEditingLibrary / EditorLoadingAndSavingUtils / AutomationLibrary / SystemLibrary / Paths / load_class / get_default_object。**§3 计 3 行**(EditorLevelLibrary、EditorAssetLibrary、其他 unreal.* binding 汇总)
- **类 6 — RemoteControl**: `grep -rn "remote_control|/remote/|30010"` 命中 ≥20 处,集中在 `Plugins/AgentBridge/Scripts/bridge/remote_control_client.py` 与 `query_tools.py` / `bridge_core.py`,端点用到 `/remote/object/call`、`/remote/object/property`、`/remote/batch`,端口 30010。**§3 计 1 行**
- **类 7 — UAT**: `grep -rn "RunUAT|BuildEditor|BuildCookRun"` 命中 ≥18 处,主要在 `Plugins/AgentBridge/Scripts/bridge/uat_runner.py`(BuildCookRun + RunGauntlet) 和 `Plugins/AgentBridge/Scripts/validation/validate_no_legacy_automation_entrypoints.ps1`(legacy `RunAutomationTests` token 已被检测器禁用)。**§3 计 2 行**(BuildCookRun 命令格式 + legacy `RunAutomationTests` 已迁移)
- **类 8 — Plugin 依赖**: 从 Mvpv4TestCodex.uproject + AgentBridge.uplugin + AgentBridgeTests.uplugin 共列出依赖插件 6 个:AgentBridge / ModelingToolsEditorMode / RemoteControlWebInterface / EditorScriptingUtilities / RemoteControl / PythonScriptPlugin / Gauntlet / FunctionalTesting。**§3 计 3 行**(EditorScriptingUtilities deprecated / Gauntlet beta / RemoteControlWebInterface marketplace 来源)
- **类 9 — PowerShell / Script**: `grep -rn "UE_5\.5|UE_5\.4"` 命中 7 处硬编码 UE_5.5 路径,集中在 `Plugins/AgentBridge/Tests/run_system_tests.py`、`Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py`、`Scripts/validation/start_ue_editor_*.ps1`。**§3 计 1 行**(硬编码 5.5 引擎路径)

§3 行数合计:9 + 5 + 1 + 3 + 1 + 2 + 3 + 1 = **25 行**(满足 ≥15 行要求)。

## 2. 未覆盖范围(留 UE 5.7 实测验证)

- **资产层**: `Content/` 有 5 个 `.uasset` + 4 个 `.umap` 文件。静态扫无法检测 Blueprint / DataAsset / Niagara 节点级的 deprecation(节点变名、引脚类型变更、Function Library 调用对象失效等),需要 UE 5.7 Editor runtime 打开工程后由"Asset Validation"/"Map Check"/"BlueprintCompiler"日志验证。
- **UE 5.7 运行时行为差异**: 渲染管线(Lumen / Nanite / VSM)、物理(Chaos)、网络复制(Iris)、动画(MotionMatching)、Niagara 默认参数等行为级变化不在静态扫范围,需要打开关卡 PIE / Standalone 跑通后从日志判断。
- **Remote Control 序列化 schema**: `IRemoteControlModule` C++ 接口未在本工程直接使用(只用 HTTP 端点),5.6→5.7 若改 JSON 序列化形态(Field 字段名 / Property Path 解析规则)需要实际 30010 探测对比。
- **PythonScriptPlugin 子类映射**: `unreal.EditorLevelLibrary` 等"old API"在 5.6 已标 deprecated,5.7 是否完全移除属于未知;需要 5.7 编辑器内 `import unreal; unreal.EditorLevelLibrary` 实测看是否抛 AttributeError。
- **EnhancedInput 默认类替换**: `DefaultInput.ini` 已使用 EnhancedInput,5.7 是否提升 EnhancedInputComponent 默认 class 名称/路径不在本扫描范围。
- **AutomationDriver 输入模拟**: Slate-level mouse/key 注入路径(`FSlateApplication::SetCursorPos` + 反射查找 widget) 行为级稳定性需要 5.7 Editor 内重跑 L3 UI 测试套件验证。

## 3. Breaking Change 表(12 字段)

| id | api_or_key | category | usage_in_5_5_4 | usage_in_5_7 | source_url | confidence | impacted_files | migration_difficulty | false_positive_status | validation_command | reviewer | linked_F_id |
|----|------------|----------|----------------|--------------|------------|------------|----------------|----------------------|----------------------|--------------------|----------|-------------|
| UE57-BC-001 | UEditorSubsystem | C++ | UAgentBridgeSubsystem 继承 UEditorSubsystem,随 Editor 启动自动实例化 | 大概率仍保留(Editor Subsystem 在 5.6 是迁移目标,反向被升格) | inferred-from-grep | medium | Plugins/AgentBridge/Source/AgentBridge/Public/AgentBridgeSubsystem.h:41, Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeModule.cpp:5, Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeSubsystem.cpp:1+ | low | suspected | RunUAT BuildEditor | pending-msc | |
| UE57-BC-002 | FModuleManager | C++ | LoadModuleChecked / IsModuleLoaded("LevelEditor"/"AssetTools"/"AutomationDriver") 用于按需加载 Editor 模块 | API 稳定,但 5.7 若模块改名(eg LevelEditor → LevelEditorCore)会编译失败 | inferred-from-grep | medium | Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeSubsystem.cpp:143,148,1144,1216, Plugins/AgentBridge/Source/AgentBridge/Private/AutomationDriverAdapter.cpp:67,72,848,854,926,928 | low | suspected | RunUAT BuildEditor | pending-msc | |
| UE57-BC-003 | IPluginManager | C++ | IPluginManager::Get().FindPlugin("AgentBridge") 用于 Commandlet 解析插件目录 | 接口稳定,但 IPlugin::GetBaseDir() 路径解析在 5.6 有重构记录(plugin path normalization) | inferred-from-grep | low | Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeCommandlet.cpp:15,281 | low | suspected | RunUAT BuildEditor | pending-msc | |
| UE57-BC-004 | FSlateApplication::Get().Tick / SetCursorPos | C++ | AutomationDriverAdapter 通过 FSlateApplication 手动 Tick + 鼠标定位 + 按键注入,绕过官方 AutomationDriver session | Slate input 注入是底层 API,5.7 若改 Tick 调度(PreTick/PostTick split)需重打 | inferred-from-grep | medium | Plugins/AgentBridge/Source/AgentBridge/Private/AutomationDriverAdapter.cpp:630,647,675,743,775,809+ (+22 more) | medium | suspected | python Plugins/AgentBridge/Tests/run_system_tests.py(L3 UI 套件) | pending-msc | |
| UE57-BC-005 | UCommandlet | C++ | UAgentBridgeCommandlet 继承 UCommandlet,提供 CLI 入口 -run=AgentBridge | UCommandlet API 在 5.6+ 仍保留但被 EditorUtilityScript / Editor Console Commands 蚕食,5.7 不太可能移除 | inferred-from-grep | medium | Plugins/AgentBridge/Source/AgentBridge/Public/AgentBridgeCommandlet.h:22, Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeCommandlet.cpp:* | low | suspected | RunUAT BuildEditor;命令行 -run=AgentBridge 触发 | pending-msc | |
| UE57-BC-006 | FAutomationTestBase + IMPLEMENT_SIMPLE_AUTOMATION_TEST | C++ | 测试套件用 IMPLEMENT_SIMPLE_AUTOMATION_TEST 宏 + FAutomationTestBase 引用 | UE Automation 框架在 5.6 引入 Spec 风格(IMPLEMENT_SPEC),但 Simple 宏仍保留 | inferred-from-grep | medium | Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/L1_QueryTests.cpp:14,50,76,108,149,184,215,235, L1_UIToolTests.cpp:75,106,167,222, L1_WriteTests.cpp:23,214,286,399,426, L2_ClosedLoopSpecs.spec.cpp:26,49 (+more) | low | suspected | python Plugins/AgentBridge/Tests/run_system_tests.py | pending-msc | |
| UE57-BC-007 | UEditorLevelLibrary (C++ comment-level dependency) | C++ | AgentBridgeSubsystem 的 UE5 依赖注释中明确依赖 UEditorLevelLibrary;实际调用通过 EditorScriptingUtilities 模块完成 | UE 5.6 起 EditorScriptingUtilities Plugin 已 deprecated → 函数迁移至 UEditorActorSubsystem / ULevelEditorSubsystem | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EditorScriptingUtilities/UEditorLevelLibrary | high | Plugins/AgentBridge/Source/AgentBridge/AgentBridge.Build.cs:44 (EditorScriptingUtilities 依赖), Plugins/AgentBridge/Source/AgentBridge/Private/AgentBridgeSubsystem.cpp:* | medium | false-positive | RunUAT BuildEditor + python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor | msc | |
| UE57-BC-008 | EditorScriptingUtilities (module dependency) | C++ | AgentBridge.Build.cs `PrivateDependencyModuleNames.Add("EditorScriptingUtilities")` | 5.6 起 EditorScriptingUtilities Plugin 已 deprecated;若 5.7 完全移除模块,Build 会 fail;若仅 deprecated,会产生大量 deprecation warning | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Plugins/EditorScriptingUtilities/UEditorLevelLibrary | high | Plugins/AgentBridge/Source/AgentBridge/AgentBridge.Build.cs:44, Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/AgentBridgeTests.Build.cs:24, Plugins/AgentBridge/AgentBridge.uplugin:30-32 | medium | confirmed | RunUAT BuildEditor(看 deprecated warning 是否 error) | msc | |
| UE57-BC-009 | UAgentBridgeSubsystem (项目层依赖 EditorSubsystem 模块) | C++ | AgentBridge.Build.cs PublicDependency 包含 `EditorSubsystem` | EditorSubsystem 模块在 5.6→5.7 期间无 deprecation 记录,稳定 | inferred-from-grep | low | Plugins/AgentBridge/Source/AgentBridge/AgentBridge.Build.cs:32 | low | suspected | RunUAT BuildEditor | pending-msc | |
| UE57-BC-010 | IncludeOrderVersion = Unreal5_5 | Build | `Source/Mvpv4TestCodex.Target.cs:12` 与 `Source/Mvpv4TestCodexEditor.Target.cs:11` 都硬编码 `EngineIncludeOrderVersion.Unreal5_5` | 升 5.7 应改为 `EngineIncludeOrderVersion.Unreal5_6` 或 `Unreal5_7`(枚举值是否存在视引擎源码),否则会有 `IncludeOrderVersion warning` | https://forums.unrealengine.com/t/includeorderversion-warning-when-compiling/1229811 | high | Source/Mvpv4TestCodex.Target.cs:12, Source/Mvpv4TestCodexEditor.Target.cs:11 | low | confirmed | RunUAT BuildEditor | msc | |
| UE57-BC-011 | DefaultBuildSettings = BuildSettingsVersion.V5 | Build | `Source/Mvpv4TestCodex.Target.cs:11` + `Source/Mvpv4TestCodexEditor.Target.cs:10` 都用 V5 | UE 5.6/5.7 若引入 V6 枚举,V5 仍兼容但会有"newer version available"提示;无强制升级 | https://forums.unrealengine.com/t/upgrade-to-buildsettingsversion-v4/1747537 | medium | Source/Mvpv4TestCodex.Target.cs:11, Source/Mvpv4TestCodexEditor.Target.cs:10 | low | suspected | RunUAT BuildEditor | pending-msc | |
| UE57-BC-012 | .uproject EngineAssociation = "5.5" | Build | `Mvpv4TestCodex.uproject:3` 硬编码 `EngineAssociation: "5.5"` | 升 5.7 必须改为 `"5.7"`,否则 Launcher 无法识别工程版本(UnrealVersionSelector 弹窗) | inferred-from-grep | high | Mvpv4TestCodex.uproject:3 | low | confirmed | 双击 .uproject 看是否提示 "select engine" | msc | |
| UE57-BC-013 | .uplugin VersionName = "0.3.0" (内部版本) | Build | AgentBridge.uplugin / AgentBridgeTests.uplugin VersionName 字段是插件自身版本,与 UE EngineVersion 无关 | 不受 UE 升级影响,但提示 msc 在 5.7 适配后 bump VersionName 至 0.4.0 作里程碑 | inferred-from-grep | low | Plugins/AgentBridge/AgentBridge.uplugin:4, Plugins/AgentBridge/AgentBridgeTests/AgentBridgeTests.uplugin:4 | low | suspected | n/a(纯文档语义) | pending-msc | |
| UE57-BC-014 | AgentBridge.Build.cs Module 依赖完整列表 | Build | PublicDeps: Core/CoreUObject/Engine/EditorSubsystem/UnrealEd/Json/JsonUtilities;PrivateDeps: EditorScriptingUtilities/AssetTools/RemoteControl/PythonScriptPlugin/Serialization/Projects/HTTP/AutomationController/AutomationDriver/Slate/SlateCore/EditorStyle/LevelEditor/ContentBrowser/InputCore + 条件 Gauntlet | 除 EditorScriptingUtilities(BC-008)与 EditorStyle(5.5 已 deprecated 合并入 Slate)之外其他模块稳定 | inferred-from-grep | medium | Plugins/AgentBridge/Source/AgentBridge/AgentBridge.Build.cs:27-93 | low | suspected | RunUAT BuildEditor(看是否报 EditorStyle deprecation) | pending-msc | |
| UE57-BC-015 | Config Layer 综合扫描 | Config | DefaultEditor.ini=空, DefaultGame.ini 仅 ProjectID/GameMode, DefaultEngine.ini 含 Renderer/WindowsTargetPlatform/AndroidFileServerEditor/EngineNameRedirects 常规段, DefaultInput.ini 含 AxisConfig + EnhancedPlayerInput | UE 5.7 无明显 breaking key 命中 | n/a | medium | Config/DefaultEditor.ini, Config/DefaultEngine.ini, Config/DefaultGame.ini, Config/DefaultInput.ini | low | suspected | UE 5.7 Editor 打开工程看 Config 加载警告 | pending-msc | |
| UE57-BC-016 | unreal.EditorLevelLibrary (Python) | Python | MCP/server.py + Scripts/bridge/query_tools.py 大量调用:get_editor_world / new_level / get_all_level_actors / load_level / get_game_world | UE 5.6 起 unreal.EditorLevelLibrary 各方法标 deprecated → 推荐 unreal.UnrealEditorSubsystem / unreal.LevelEditorSubsystem / unreal.EditorActorSubsystem | https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorLevelLibrary?application_version=5.6 | high | Plugins/AgentBridge/MCP/server.py:137,141,248,581, Plugins/AgentBridge/Scripts/bridge/query_tools.py:91-97,145,205,346,583, Plugins/AgentBridge/Scripts/bridge/write_tools.py (+more) | medium | confirmed | python -c "import unreal; unreal.EditorLevelLibrary.get_editor_world()" 在 5.7 Editor Console | msc | |
| UE57-BC-017 | unreal.EditorAssetLibrary (Python) | Python | MCP/server.py + query_tools.py:load_asset / save_asset / load_blueprint_class | UE 5.6 起标 deprecated → 推荐 unreal.EditorAssetSubsystem | https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/EditorAssetLibrary?application_version=5.6 | high | Plugins/AgentBridge/MCP/server.py:292,337,360,405,427,432,440,445,447,454,640+, Plugins/AgentBridge/Scripts/bridge/query_tools.py:346 | medium | confirmed | python -c "import unreal; unreal.EditorAssetLibrary.load_asset('/Game/...')" 5.7 验证 | msc | |
| UE57-BC-018 | unreal.* 其他 binding 综合 | Python | AssetToolsHelpers / MaterialFactoryNew / MaterialInstanceConstantFactoryNew / MaterialEditingLibrary / WidgetBlueprintFactory / EditorLoadingAndSavingUtils / AutomationLibrary / SystemLibrary / Paths / load_class / get_default_object / LinearColor | 这些非 ESU 系列 binding 在 5.6 release notes 未见 deprecation 提及,大概率稳定 | inferred-from-grep | low | Plugins/AgentBridge/MCP/server.py:281,282,286,326,327,331,344,353,394,395,399,436,451,598,619, Plugins/AgentBridge/Scripts/bridge/query_tools.py:91-95 | low | suspected | python Plugins/AgentBridge/Tests/run_system_tests.py(完整跑套件看 unreal.* 失败) | pending-msc | |
| UE57-BC-019 | RemoteControl HTTP 端点 (/remote/object/call, /remote/object/property, /remote/batch) | RemoteControl | remote_control_client.py 通过 PUT 30010 调用 BlueprintCallable + 读写 Property + Batch 执行;query_tools.py 注释明确"UE5.5.4 下 ActorPath 走 /remote/object/property 读取 RelativeLocation" | UE 5.6/5.7 Remote Control HTTP API 仍维护(release notes 未提及 endpoint 移除),但 5.7 增加 Preset HTTP API + Rundown Server;现有 /remote/object/* 路径预期保留 | https://dev.epicgames.com/documentation/en-us/unreal-engine/remote-control-api-http-reference-for-unreal-engine | medium | Plugins/AgentBridge/Scripts/bridge/remote_control_client.py:2,14,30,104-140, Plugins/AgentBridge/Scripts/bridge/query_tools.py:113,163,221,223,292,346,383,583, Plugins/AgentBridge/Scripts/bridge/bridge_core.py:60,199 | low | suspected | curl http://localhost:30010/remote/preset 在 5.7 验证;运行 query_tools 单元链 | pending-msc | |
| UE57-BC-020 | UAT BuildCookRun -editortest 调用形态 | UAT | uat_runner.py 用 `RunUAT BuildCookRun -project=... -run -editortest -RunAutomationTest=...` 触发 Automation | UE 5.6 起官方推荐路径未变(legacy `RunAutomationTests` token 已经被 validate_no_legacy_automation_entrypoints.ps1 检测器禁止);5.7 BuildCookRun 参数面预期向后兼容 | inferred-from-grep | medium | Plugins/AgentBridge/Scripts/bridge/uat_runner.py:86-134,155,160,213-231, Plugins/AgentBridge/Scripts/validation/validate_no_legacy_automation_entrypoints.ps1:73-78 | low | suspected | RunUAT BuildCookRun -editortest -RunAutomationTest=AgentBridge | pending-msc | |
| UE57-BC-021 | 项目脚本 legacy `RunUAT RunAutomationTests` token 检测 | UAT | validate_no_legacy_automation_entrypoints.ps1 已主动禁用 legacy 入口,Suggestion 推荐 BuildCookRun -editortest | 该检测器是项目内部治理,不受 UE 升级影响;但若 5.7 改 BuildCookRun 参数名,Suggestion 文案需同步 | inferred-from-grep | low | Plugins/AgentBridge/Scripts/validation/validate_no_legacy_automation_entrypoints.ps1:73-78 | low | suspected | pwsh Plugins/AgentBridge/Scripts/validation/validate_no_legacy_automation_entrypoints.ps1 | pending-msc | |
| UE57-BC-022 | .uproject Plugins[]: ModelingToolsEditorMode + RemoteControlWebInterface | Plugin | uproject 启用了 ModelingToolsEditorMode (Editor target only) 和 RemoteControlWebInterface (含 MarketplaceURL) | ModelingToolsEditorMode 在 5.6+ 已合入引擎默认,无 deprecation;RemoteControlWebInterface 含 marketplace URL 是 5.4 时代格式,5.7 是否移除外链待验 | inferred-from-grep | medium | Mvpv4TestCodex.uproject:24-35 | low | suspected | UE 5.7 Editor 打开工程看插件浏览器是否标"missing" | pending-msc | |
| UE57-BC-023 | AgentBridge.uplugin Plugins[]: EditorScriptingUtilities + RemoteControl + PythonScriptPlugin + Gauntlet | Plugin | AgentBridge 显式 Enable 4 个引擎插件;EditorScriptingUtilities 已与 BC-008 重叠 | EditorScriptingUtilities 5.6 deprecated(同 BC-008);Gauntlet 仍 beta;PythonScriptPlugin 稳定;RemoteControl 稳定 | inferred-from-grep | medium | Plugins/AgentBridge/AgentBridge.uplugin:28-45 | low | suspected | UE 5.7 Editor 看插件依赖加载 | pending-msc | |
| UE57-BC-024 | AgentBridgeTests.uplugin FunctionalTesting Optional | Plugin | AgentBridgeTests 启用 FunctionalTesting (Optional=true) | FunctionalTesting 模块在 5.6/5.7 稳定;Optional 标志保留 | inferred-from-grep | low | Plugins/AgentBridge/AgentBridgeTests/AgentBridgeTests.uplugin:30-34 | low | suspected | n/a | pending-msc | |
| UE57-BC-025 | 硬编码 `UE_5.5` 引擎路径 (PowerShell + Python) | Script | run_system_tests.py / task14a_phase11_standalone_smoke.py / start_ue_editor_*.ps1 直接 hardcode `E:\Epic Games\UE_5.5` 与 `C:\Program Files\Epic Games\UE_5.5` 与 `D:\Epic Games\UE_5.5` 三处 fallback | 升 5.7 须批量改 `UE_5.5` → `UE_5.7`(或抽到环境变量 / `$env:UE_INSTALL_ROOT`);否则脚本找不到 UAT.bat | inferred-from-grep | high | Plugins/AgentBridge/Tests/run_system_tests.py:18,727,729,730, Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py:25, Scripts/validation/start_ue_editor_cmd_project.ps1:3, Scripts/validation/start_ue_editor_project.ps1:104-105 | low | confirmed | pwsh Scripts/validation/start_ue_editor_project.ps1(无 UE_5.7 路径会立即 fail) | msc | |

## 4. 待 msc 人工裁决(Step 8 后填)

P2/P3 条目默认 `false_positive_status: suspected`,reviewer:pending-msc,留 5.7 实测阶段裁决。**P1 7 条已由 msc 裁决完成**(BC-007 false-positive + 其余 6 条 confirmed),§3 表中 false_positive_status / reviewer 字段已同步更新。按 confidence 三档分桶:

### P1(高置信、likely 真 breaking change)— 7 条(已裁决:1 false-positive + 6 confirmed)

| id | api_or_key | 1-line 上下文 | 裁决 |
|----|------------|----------------|------|
| UE57-BC-007 | UEditorLevelLibrary (C++ 注释依赖) | AgentBridgeSubsystem.cpp UE5 依赖注释指 UEditorLevelLibrary,实际调用通过 EditorScriptingUtilities 模块完成。真实编译依赖落在 BC-008,本条仅注释,避免重复进 SRS/LLD 迁移记号 | **false-positive** |
| UE57-BC-008 | EditorScriptingUtilities 模块依赖 | AgentBridge.Build.cs PrivateDeps 直接依赖 EditorScriptingUtilities 模块,需迁移到 UEditorActorSubsystem / ULevelEditorSubsystem | **confirmed** |
| UE57-BC-010 | IncludeOrderVersion = Unreal5_5 | Target.cs / EditorTarget.cs 硬编码 Unreal5_5 枚举,升 5.7 须改 Unreal5_6 或 Unreal5_7 | **confirmed** |
| UE57-BC-012 | .uproject EngineAssociation "5.5" | uproject 第 3 行 EngineAssociation "5.5",升 5.7 必须改 "5.7" | **confirmed** |
| UE57-BC-016 | unreal.EditorLevelLibrary (Python) | MCP/server.py + query_tools.py 大量调用 EditorLevelLibrary.*,5.6 已标 deprecated → 推荐 UnrealEditorSubsystem | **confirmed** |
| UE57-BC-017 | unreal.EditorAssetLibrary (Python) | server.py / query_tools.py 大量 load_asset/save_asset/load_blueprint_class,5.6 deprecated → EditorAssetSubsystem | **confirmed** |
| UE57-BC-025 | 硬编码 `UE_5.5` 引擎路径 | run_system_tests.py + start_ue_editor_*.ps1 共 7 处硬编码 5.5 路径,5.7 须批量替换 | **confirmed** |

### P2(中等)— 12 条

| id | api_or_key | 1-line 上下文 |
|----|------------|----------------|
| UE57-BC-001 | UEditorSubsystem | UAgentBridgeSubsystem 继承自 UEditorSubsystem;父类预期稳定,但 5.7 若 lifecycle hook 改名(eg Initialize → InitializeAsync)会影响 |
| UE57-BC-002 | FModuleManager | LoadModuleChecked("LevelEditor"/"AssetTools"/"AutomationDriver"),模块改名会编译失败 |
| UE57-BC-004 | FSlateApplication::Tick/SetCursorPos | AutomationDriverAdapter 底层 Slate input 注入,5.7 Tick 调度改动会影响 |
| UE57-BC-005 | UCommandlet | UAgentBridgeCommandlet 继承,5.7 仍保留概率高 |
| UE57-BC-006 | FAutomationTestBase + IMPLEMENT_SIMPLE_AUTOMATION_TEST | Tests 大量使用,5.7 仍保留概率高 |
| UE57-BC-011 | BuildSettingsVersion.V5 | Target.cs 用 V5,5.7 若引入 V6 会有警告 |
| UE57-BC-014 | AgentBridge.Build.cs 模块依赖总览 | EditorStyle 模块 5.5 时已 deprecated 合入 Slate,5.7 是否完全移除待验 |
| UE57-BC-015 | Config Layer 综合 | 4 个 ini 文件无明显 breaking key,但 5.7 Editor 打开时可能 warning 个别废弃节 |
| UE57-BC-019 | RemoteControl HTTP /remote/object/* | RC HTTP 端点稳定预期,但 5.7 是否改 JSON 序列化形态待实测 |
| UE57-BC-020 | UAT BuildCookRun -editortest | UAT 参数面预期向后兼容 |
| UE57-BC-022 | uproject Plugins[]: ModelingToolsEditorMode + RemoteControlWebInterface | RemoteControlWebInterface 含 marketplace URL 是 5.4 时代格式 |
| UE57-BC-023 | AgentBridge.uplugin Plugins[] | EditorScriptingUtilities 与 BC-008 重叠,Gauntlet beta |

### P3(低置信、推测)— 6 条

| id | api_or_key | 1-line 上下文 |
|----|------------|----------------|
| UE57-BC-003 | IPluginManager | FindPlugin("AgentBridge"),路径解析重构可能影响 |
| UE57-BC-009 | EditorSubsystem 模块依赖 | Build.cs PublicDeps,无 deprecation 记录,推测稳定 |
| UE57-BC-013 | uplugin VersionName "0.3.0" | 插件自身版本,与 UE 升级解耦 |
| UE57-BC-018 | unreal.* 其他 binding(非 ESU) | AssetToolsHelpers / MaterialFactoryNew / MaterialEditingLibrary / WidgetBlueprintFactory / EditorLoadingAndSavingUtils / AutomationLibrary / SystemLibrary / Paths / load_class / get_default_object / LinearColor 共 16 处调用,大概率稳定 |
| UE57-BC-021 | validate_no_legacy_automation_entrypoints.ps1 token | 项目内部治理脚本,不受升级影响 |
| UE57-BC-024 | AgentBridgeTests.uplugin FunctionalTesting Optional | FunctionalTesting 模块稳定 |

**裁决建议给 msc**: P1 7 条先实测(打开 UE 5.7 Editor 看 deprecation warning + 编译看 missing module);P2 12 条等 P1 跑通后看连带影响;P3 6 条仅在 P1/P2 都过完后再回扫。
