# Demo_MonopolyAuction — 架构文档(architecture.md)

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。

## 1. 模块结构

单一 Runtime 模块 `FDemo_MonopolyAuctionModule`(`Demo_MonopolyAuction`),
依赖严格限定在施工规范白名单:Core / CoreUObject / Engine / InputCore(public)与
UMG / Slate / SlateCore(private)。不依赖 Mvpv4TestCodex 主模块任何类(完全自包含)。

目录:
- Source/Demo_MonopolyAuction/Public:对外头文件
- Source/Demo_MonopolyAuction/Private:实现
- Source/Demo_MonopolyAuction/Private/Tests:冒烟用例(名字空间 Demo_MonopolyAuction.Smoke)
- Content/Data:数据资产落点(v0 用代码默认资产兜底,留作扇出 author 入口)
- Docs / README.md:文档

## 2. 类职责与协作

### 2.1 裁决与状态

- `AMADemoGameMode`:回合驱动核心。对外 API:`InitializeGame`(铺局)、`StartTurn`、
  `RequestRollAndResolve`(掷骰+移动+落点结算+双数处理一体)、`AdvanceToNextPlayer`、
  `RunFullGameToCompletion`(冒烟主入口,驱动整局到终局)。内部裁决:`MoveCurrentPlayer`、
  `OnPlayerLanded`、`HandlePropertyTile`、`HandleTaxTile`、`HandleGoToJail`、
  `HandleJailTurnStart`、`ProcessPayment`、`EliminatePlayer`、`CheckGameOver`、`AutoBuyPolicy`。
- `AMADemoGameState`:只读查询 API:`GetTileInfo`、`GetTileOwner`/`SetTileOwner`、`GetPlayer`、
  `GetActivePlayerCount`、`DoesPlayerOwnColorGroup`、`CalculateRent`(含满色组翻倍)、
  `GetPlayerNetWorth`(现金+地产+股票市值)。

### 2.2 玩家与子系统

- `UMADemoPlayerData`:`AddMoney`/`DeductMoney`/`CanAfford`/`AddProperty`,及监狱/破产/股票持仓字段。
- `UMADemoStockMarket`:`InitializeStocks`(3 支 A/B/C)、`ApplyTurnSwing`(按掷骰和确定性 ±波动)、
  `GetPrice`。
- `AMADemoPlayerController`:`IntentRollDice` / `IntentEndTurn` 转发到 GameMode。

### 2.3 数据资产

- `UMADemoBoardDataAsset`:`BuildDefaultBoard` 铺 28 格(GDD 2.3);角格/交易所索引字段。
- `UMADemoRulesDataAsset`:全部可调数值字段(见 design.md §3)。

### 2.4 UI(只读 GameState / 只发意图)

- `UMADemoHUDWidget`:`BuildSnapshot` 产出 `FMADemoHUDSnapshot`(回合/当前玩家/各玩家现金+股值/
  骰子文本/3 股摘要),`RefreshHUD` 广播给蓝图 `OnHUDRefreshed`。
- 前台外壳:`UMADemoStartScreenWidget`、`UMADemoMainMenuWidget`、`UMADemoSettingsWidget`、
  `UMADemoPauseWidget`、`UMADemoResultsWidget` 各暴露必备元素对应的意图方法与
  BlueprintImplementableEvent。
- 底座:`UMADemoInputFoundation`(4 动作默认绑定)、`UMADemoAudioFoundation`(音量+基础 SFX)、
  `UMADemoPlatformFoundation`(窗口/分辨率/退出)。

## 3. 回合状态机

`EMADemoTurnPhase`:NotStarted → WaitingForRoll →(Resolving)→ TurnEnd/WaitingForRoll(双数再掷)
→ AdvanceToNextPlayer → … → GameOver。胜负在 `CheckGameOver` 收敛(存活 1 人或达回合上限按净资产)。

## 4. 数据流(冒烟直驱路径)

```
InitializeGame(N, seed)
  → StartTurn → RequestRollAndResolve(× 双数次)
  → AdvanceToNextPlayer → … → IsGameOver
  → WinnerIndex 落定
```

冒烟经 `AMADemoGameState`/`AMADemoGameMode` 公有 API 驱动,不走 UI 点击、不依赖 PIE 关卡,
保证 `-unattended` commandlet 下可跑。

## 5. 扩展点(Phase 14 留缝)

- 规则数值:改 `UMADemoRulesDataAsset` 实例值。
- 棋盘布局:改 `UMADemoBoardDataAsset` 的 Tiles。
- 拍卖/股票交易 UI:在 increment 批新增 widget 与 GameMode 分支,数据结构
  `FMADemoAuctionState` / `UMADemoStockMarket` 已就位。

## 6. 冒烟用例覆盖(Demo_MonopolyAuction.Smoke)

| 用例 | 覆盖 |
|------|------|
| BoardData | 28 格/角格/交易所/地产计数 |
| Dice | 2D6 范围与双数判定 |
| Economy | 初始资金 + 满色组租金翻倍 |
| FullGameLoop | 5 个种子各驱动整局到终局零报错、胜者合法 |
| JailBankruptcy | 监狱标记与存活计数语义 |
| WidgetCreation | HUD 快照 + 全部前台 widget + 三底座创建 |
| VisualDump | 9 个 Visual story 反射 dump(截图降级证据) |
