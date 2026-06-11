manifest_version: 1.0.0

# Demo Plugin 施工规范(construction manifest)v1

> 消费者:实施 demo story 的 coding agent(经 demo_story_fetch 全文下发)。
> 本文件是项目层实例;版本变更时递增顶部 manifest_version,story 携带切批时版本,fetch 不符告警。

## 1. Plugin 骨架

- 每个 demo = 一个自包含 runtime plugin:`Plugins/<PluginName>/`(名称由 demo_plan 派生,见 story 材料)
- 必含:`<PluginName>.uplugin`(Type=Runtime)、`Source/<PluginName>/`(模块同名)、`Content/`、`Docs/`、`README.md`
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
- **规则参数一律数据驱动**:数值/配置进 DataAsset 或 DataTable(Content/Data/),C++ 不许硬编码可调参数——这是增量与扇出的留缝

## 4. 冒烟用例(随 demo 交付)

- 放 `Source/<PluginName>/Private/Tests/`,UE Automation Test 框架,名字空间 `<PluginName>.Smoke`
- v0 必含:一局从开始驱动到终局(经 GameState API,不走 UI 点击)零报错;widget 创建冒烟
- v0 经 msc PROCEED 后用例冻结(hash 守门),增量批只许新增用例文件,不许改既有
- 基线冻结由验收 runbook 在 msc PROCEED 时调用 evidence_validator.freeze_v0_baseline 落盘 v0_smoke_baseline.json,agent 无需自行触发

## 5. Provisional 决策留痕

- GDD 未规定的设计点:给默认值继续,不许停下提问
- 每条记入 demo_story_submit 的 evidence.provisional_decisions 数组:{"decision": 内容, "rationale": 依据, "scope": 影响面};story verified 后随 evidence 存档于 story JSON

## 6. 文档(批末文档 story 产出)

- 落 `Plugins/<PluginName>/Docs/`:design.md(系统总览+决策含 provisional)、architecture.md(模块/类职责/数据资产/扩展点)、changelog.md(逐批追加)
- README.md(plugin 根):试玩入口地图、操作方式、一局预期流程、provisional 摘要
- 文档头部标注:"生成物,与 ProjectState/runs/<run_id> 数据不一致时以数据为准"
- 文档中类名/资产路径用反引号包裹(机器引用对账依赖此约定)
