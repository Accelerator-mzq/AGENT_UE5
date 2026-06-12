manifest_version: 1.1.0

# Demo Plugin 施工规范(construction manifest)v1.1

> 消费者:实施 demo story 的 coding agent(经 demo_story_fetch 全文下发)。
> 本文件是项目层实例;版本变更时递增顶部 manifest_version,story 携带切批时版本,fetch 不符告警。
> 1.1.0 修订(2026-06-12,PIVOT #1):新增 v0 可玩硬判据、authored 启动关卡必含、无人值守资产创建通路——
> 见 `ProjectState/Reports/2026-06-12/phase14_v0_pivot_note_1.md`。

## 0. v0 可玩硬判据(PIVOT #1 新增,不满足即 v0 不算完成)

- **人可交互地玩**:`UnrealEditor-Cmd <uproject> <EntryMap> -game -windowed -ResX=1280 -ResY=720` 可启动进入对局;
  键盘意图(至少:掷骰/确认、结束回合)能推进游戏;HUD 在画面上呈现当前玩家/资金/位置等核心状态
- 试玩入口 = authored 启动关卡(见 §1);README 必须给出上述启动命令与键位表
- 冒烟含关卡加载用例(见 §4);最终人工裁决仍归 msc 试玩窗口

## 1. Plugin 骨架

- 每个 demo = 一个自包含 runtime plugin:`Plugins/<PluginName>/`;名称由实施 agent 从契约 game_identity/contract_id 派生(Demo_ 前缀 + 大驼峰,如 Demo_MonopolyAuction),并记入首个 story 的 provisional_decisions
- 必含:`<PluginName>.uplugin`(Type=Runtime)、`Source/<PluginName>/`(模块同名)、`Content/`、`Docs/`、`README.md`
- **必含 authored 启动关卡**:`Content/Maps/<EntryMap>.umap`,WorldSettings 绑定 demo 的 GameMode(创建通路见 §7)
- Build.cs 依赖白名单:Core、CoreUObject、Engine、InputCore、UMG、Slate、SlateCore;新增依赖须在 provisional_decisions 留痕
- **禁止依赖**:`Source/Mvpv4TestCodex` 主模块的任何类(MMonopoly*、MBoardManager、MDice 等)——include 或模块依赖均算违规

## 2. C++ 编码约束(UE5.5)

- UObject 指针一律 `TObjectPtr<>`;容器用 TArray/TMap/TSet;禁 new/delete 管理 UObject
- 反射宏齐全:UPROPERTY/UFUNCTION/UCLASS,带中文注释说明用途
- 禁热路径(Tick/逐帧)字符串拼接与查找;非必要不开 Tick(默认 PrimaryActorTick.bCanEverTick=false)
- 命名:A 前缀 Actor、U 前缀 UObject/组件、F 前缀结构、E 前缀枚举;文件名与类名一致
- 注释一律中文;只解释"为什么",不复述代码

## 3. 架构分层

- GameMode:规则裁决与流程推进(回合推进、胜负判定入口)
- GameState:全量可复制游戏状态(玩家/资源/棋盘态),冒烟测试经 GameState API 直驱
- 玩家交互走 PlayerController;UI 为 UMG Widget,只读 GameState、只发意图,不持有规则
- HUD 允许 C++ 运行时 CreateWidget 呈现(WBP 蓝图实例非 v0 必需);但呈现必须真实可见于 -game 画面
- **规则参数一律数据驱动**:数值/配置进 DataAsset 或 DataTable(Content/Data/),C++ 不许硬编码可调参数——这是增量与扇出的留缝

## 4. 冒烟用例(随 demo 交付)

- 放 `Source/<PluginName>/Private/Tests/`,UE Automation Test 框架,名字空间 `<PluginName>.Smoke`
- v0 必含:一局从开始驱动到终局(经 GameState API,不走 UI 点击)零报错;widget 创建冒烟;
  **启动关卡加载用例**(加载 `<EntryMap>`,校验 WorldSettings GameMode 为 demo GameMode、GameState 类正确、HUD widget 在关卡上下文创建成功)
- v0 经 msc PROCEED 后用例冻结(hash 守门),增量批只许新增用例文件,不许改既有
- 基线冻结由验收 runbook 在 msc PROCEED 时调用 evidence_validator.freeze_v0_baseline 落盘 v0_smoke_baseline.json,agent 无需自行触发

## 5. Provisional 决策留痕

- GDD 未规定的设计点:给默认值继续,不许停下提问
- 每条记入 demo_story_submit 的 evidence.provisional_decisions 数组:{"decision": 内容, "rationale": 依据, "scope": 影响面};story verified 后随 evidence 存档于 story JSON

## 6. 文档(批末文档 story 产出)

- 落 `Plugins/<PluginName>/Docs/`:design.md(系统总览+决策含 provisional)、architecture.md(模块/类职责/数据资产/扩展点)、changelog.md(逐批追加)
- README.md(plugin 根):试玩入口地图与 -game 启动命令、键位表、一局预期流程、provisional 摘要
- 文档头部标注:"生成物,与 ProjectState/runs/<run_id> 数据不一致时以数据为准"
- 文档中类名/资产路径用反引号包裹(机器引用对账依赖此约定)

## 7. 无人值守资产创建通路(PIVOT #1 新增)

- 编辑器资产(.umap 等)经编辑器 Python 无人值守创建:
  `UnrealEditor-Cmd <uproject> -run=pythonscript -script="<绝对路径>.py" -unattended -nosplash -stdout`
  脚本内用 `unreal` 模块(LevelEditorSubsystem/EditorLevelLibrary 建图、WorldSettings 设 GameModeOverride、
  EditorAssetLibrary 保存到 `/<PluginName>/Maps/`);脚本与日志留 `ProjectState/Evidence/` 备查
- 若需 PythonScriptPlugin 未启用:允许在 .uproject 同级以 -EnablePlugins=PythonScriptPlugin 临时启用或在
  uplugin 声明依赖,记 provisional;不许改 .uproject 之外的工程级配置
- WBP 蓝图实例创建非必需;若尝试失败不阻塞(C++ CreateWidget 兜底),记 provisional
- 截图:有了启动关卡后,Visual 证据用 `-game` 模式 HighResShot 真实截取 HUD 画面;反射 dump 仅作补充
