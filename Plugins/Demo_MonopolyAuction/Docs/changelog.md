# Demo_MonopolyAuction — 变更记录(changelog.md)

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。

## v0(2026-06-12,attempt 2)

首批从 demo story 工单无人值守合成,聚焦「一局可驱动到终局」主链 + v0 可玩硬判据。

新增:
- 裁决/状态/玩家/意图/表现五层:`AMADemoGameMode`、`AMADemoGameState`、`UMADemoPlayerData`、
  `AMADemoPlayerController`、`AMADemoHUD`、`UMADemoHUDWidget`。
- 数据驱动资产:`UMADemoBoardDataAsset`(28 格)、`UMADemoRulesDataAsset`(规则参数)。
- 股票市场 `UMADemoStockMarket`(3 支 A/B/C,确定性回合波动);拍卖数据骨架 `FMADemoAuctionState`。
- 前台外壳 widget:开始/主菜单/设置/暂停/结果;三底座:输入/音频/平台。
- authored 启动关卡 `L_MonopolyDemo`(经 pythonscript 通路创建,WorldSettings 绑定 `AMADemoGameMode`)。
- 冒烟 7 用例(含 `EntryMapLoad` 启动关卡加载用例)。
- 可玩硬判据:`-game` 启动进对局、键盘意图(Space/Enter/Esc)推进、Canvas HUD 真实呈现状态、
  自动驾驶启动参数与分面板截图通路。

边界:拍卖/股票完整交互 UI、authored 3D 棋盘 Actor 留待 increment 批。

## increment-1(待批)

- 地产拍卖完整交互(英式拍卖出价面板)。

## increment-2(待批)

- 股票市场完整交互(交易所买卖面板)。
