# Demo_MonopolyAuction — 架构文档(architecture.md)

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。

## 1. 模块结构

单一 Runtime 模块 `Demo_MonopolyAuction`,依赖严格限定在施工规范白名单:
Core / CoreUObject / Engine / InputCore(public)与 UMG / Slate / SlateCore(private)。
不依赖 Mvpv4TestCodex 主模块任何类(完全自包含)。

目录:
- `Source/Demo_MonopolyAuction/Public`:对外头文件
- `Source/Demo_MonopolyAuction/Private`:实现
- `Source/Demo_MonopolyAuction/Private/Tests`:冒烟用例(名字空间 `Demo_MonopolyAuction.Smoke`)
- `Content/Maps`:authored 启动关卡 `L_MonopolyDemo`
- `Content/Data`:数据资产落点(v0 用代码默认资产兜底,留作扇出 author 入口)
- `Docs` / `README.md`:文档

## 2. 类职责与协作

### 2.1 裁决与状态

- `AMADemoGameMode`:回合驱动核心。对外 API:`InitializeGame`、`StartTurn`、
  `RequestRollAndResolve`(掷骰+移动+落点结算+双数处理;**正常结算后停 TurnEnd 等 Enter**,
  暂停/TurnEnd 阶段调用被拒——试玩反馈修复轮)、`AdvanceToNextPlayer`(Enter 意图落点)、
  `RunFullGameToCompletion`(冒烟主入口,TurnEnd 时代按 Enter)、`AutoAdvanceOneTurn`
  (自动驾驶推进一回合,同样代按 Enter)、`TogglePauseState`/`SetPauseState`/`IsPaused`(暂停)。
  内部裁决:`MoveCurrentPlayer`、`OnPlayerLanded`、`HandlePropertyTile`、`HandleTaxTile`、
  `HandleGoToJail`、`HandleJailTurnStart`、`ProcessPayment`、`EliminatePlayer`、
  `CheckGameOver`、`AutoBuyPolicy`。
- `AMADemoGameState`:只读查询 API:`GetTileInfo`、`GetTileOwner`/`SetTileOwner`、`GetPlayer`、
  `GetActivePlayerCount`、`DoesPlayerOwnColorGroup`、`CalculateRent`(含满色组翻倍)、
  `GetPlayerNetWorth`、`GetPlayerStockValue`。

### 2.2 玩家与子系统

- `UMADemoPlayerData`:`AddMoney`/`DeductMoney`/`CanAfford`/`AddProperty`/`ClearProperties`,
  及监狱/破产/股票持仓字段。
- `UMADemoStockMarket`:`InitializeStocks`(3 支 A/B/C)、`ApplyTurnSwing`(按掷骰确定性 ±波动)、
  `GetPrice`。
- `AMADemoPlayerController`:`IntentRollDice` / `IntentEndTurn` / `IntentPause` 转发到 GameMode。

### 2.3 数据资产

- `UMADemoBoardDataAsset`:`BuildDefaultBoard` 铺 28 格(GDD 2.3);角格/交易所索引字段。
- `UMADemoRulesDataAsset`:全部可调数值字段(见 design.md §3)。

### 2.4 UI

- `AMADemoHUD`:`DrawHUD` 用 Canvas 直绘对局 HUD 与各前台外壳/底座面板
  (`-MADemoPanel=` 选择),保证 `-game` 截图真实可见。
- `UMADemoHUDWidget`:`BuildSnapshot` 产出 `FMADemoHUDSnapshot`,`RefreshHUD` 广播
  `OnHUDRefreshed`,供契约/冒烟/扇出蓝图绑定。
- 前台外壳:`UMADemoStartScreenWidget`、`UMADemoMainMenuWidget`、`UMADemoSettingsWidget`、
  `UMADemoPauseWidget`、`UMADemoResultsWidget`。
- 底座:`UMADemoInputFoundation`(4 动作默认绑定)、`UMADemoAudioFoundation`、
  `UMADemoPlatformFoundation`。

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

冒烟经 `AMADemoGameState`/`AMADemoGameMode` 公有 API 驱动,不走 UI 点击;
`Demo_MonopolyAuction.Smoke.EntryMapLoad` 用例额外校验 authored 关卡加载与 GameMode 绑定。

## 5. 扩展点(Phase 14 留缝)

- 规则数值:改 `UMADemoRulesDataAsset` 实例值。
- 棋盘布局:改 `UMADemoBoardDataAsset` 的 Tiles。
- 拍卖/股票交易 UI:在 increment 批新增 widget 与 GameMode 分支,数据结构
  `FMADemoAuctionState` / `UMADemoStockMarket` 已就位。

## 6. 冒烟用例覆盖(`Demo_MonopolyAuction.Smoke`)

| 用例 | 覆盖 |
|------|------|
| BoardData | 28 格/角格/交易所/16 地产 |
| Dice | 2D6 范围与双数判定 |
| Economy | 初始资金 + 满色组租金翻倍 |
| EntryMapLoad | 启动关卡加载 + WorldSettings GameMode 绑定 + HUD 关卡上下文创建 |
| FullGameLoop | 5 个种子各驱动整局到终局零报错、胜者合法非破产 |
| JailBankruptcy | 监狱标记与存活计数语义 |
| WidgetCreation | HUD 快照 + 全部前台 widget + 三底座创建 |
| InteractionSemantics | 试玩反馈修复轮回归:结算停 TurnEnd 未切人 / TurnEnd 掷骰被拒 / Enter 推进玩家 / 暂停态掷骰被拒 |
