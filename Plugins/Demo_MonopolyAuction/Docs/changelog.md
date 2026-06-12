# Demo_MonopolyAuction — 变更日志(changelog.md)

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。
> 逐批追加。

## v0(2026-06-12)— Phase 14 demo-first 首批

首次无人值守从 demo story 工单合成的可玩 demo 骨架与完整回合主链。

新增:
- 自包含 Runtime 插件 `Demo_MonopolyAuction`(模块 `FDemo_MonopolyAuctionModule`),依赖白名单内。
- 数据驱动资产:`UMADemoBoardDataAsset`(28 格 GDD 2.3)、`UMADemoRulesDataAsset`(全部可调参数)。
- 裁决与状态:`AMADemoGameMode`(回合状态机+规则裁决)、`AMADemoGameState`(全量只读态)、
  `UMADemoPlayerData`、`AMADemoPlayerController`、`UMADemoStockMarket`。
- UI:`UMADemoHUDWidget` 及前台外壳 `UMADemoStartScreenWidget` / `UMADemoMainMenuWidget` /
  `UMADemoSettingsWidget` / `UMADemoPauseWidget` / `UMADemoResultsWidget`;
  底座 `UMADemoInputFoundation` / `UMADemoAudioFoundation` / `UMADemoPlatformFoundation`。
- 冒烟:Demo_MonopolyAuction.Smoke 7 用例全过(整局到终局零报错 + widget 创建 + Visual 反射 dump)。

覆盖的 v0 story(17 个,均经机器证据门 verified):
baseline-start-screen / main-menu / input-foundation / settings / audio-foundation / pause /
platform-foundation / board-topology / dice / tile-system / turn-loop / economy /
player-management / hud / results / jail / v0-docs。

已知降级:Visual story 截图证据降级为 widget 反射 dump + 一张真实引擎渲染 PNG(已如实披露,
见 design.md §5)。

待后续批:拍卖完整 UI(increment-1)、股票交易完整 UI(increment-2)、authored 3D 关卡与 WBP 实例。
