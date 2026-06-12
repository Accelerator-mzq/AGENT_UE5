# Demo_MonopolyAuction — 设计文档(design.md)

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。
> 本文档只描述已 verified 的 v0 实现;结构性内容自 run 产物投影。

## 1. 系统总览

Demo_MonopolyAuction 是 Phase 14 v0 的自包含可玩 demo:一个 Monopoly-like 本地热座多人原型,
在经典大富翁核心规则之上预留拍卖与股票市场扩展接口。来源为 GDD
`ProjectInputs/GDD/monopoly_extended_auction_v1.md`(核心规则按引用沿用 `GDD_MonopolyGame.md`)
与根契约 `rsc.monopoly.phase1_local_multiplayer.20260611`。

v0 批交付完整的"一局可驱动到终局"主链:棋盘拓扑、骰子、格子事件分发、回合流转、
经济结算、玩家管理与破产、监狱,以及 Universal Baseline 前台外壳(开始画面/主菜单/设置/
暂停/结果/HUD)与三大底座(输入/音频/平台)。拍卖与股票的完整交互 UI 属增量批(increment-1/2),
v0 仅落地其数据结构与定价骨架(`FMADemoAuctionState`、`UMADemoStockMarket`)。

## 2. 架构分层(施工规范 §3)

- **裁决层**:`AMADemoGameMode` 持有全部规则裁决与回合状态机,是唯一改写游戏状态的入口。
- **状态层**:`AMADemoGameState` 承载全量可读状态(棋盘所有权、玩家集合、回合数、骰子结果、
  股票市场、拍卖态、胜者),对外只读 API 供 UI 与冒烟断言。
- **玩家数据**:`UMADemoPlayerData` 以 UObject 建模单玩家(资金/位置/地产/监狱/破产/股票持仓),
  热座多人下避免引入 PlayerController/Pawn 网络栈,使冒烟可纯逻辑直驱。
- **意图层**:`AMADemoPlayerController` 仅把玩家意图转发给 GameMode,不持有规则。
- **表现层**:UMG widget 基类只读 GameState、只发意图,不含规则。

## 3. 数据驱动(施工规范 §3 留缝)

所有可调规则参数与棋盘数据下沉到 DataAsset,C++ 不硬编码可调值:

- `UMADemoBoardDataAsset`:28 格静态数据(类型/名称/颜色组/价格/租金,GDD 2.3 数据表),
  角格索引与交易所选址。默认棋盘在对象构造时铺好,编辑器可覆盖。
- `UMADemoRulesDataAsset`:初始资金、起点奖励、骰子规格、监狱参数、满色组倍率、拍卖步长、
  股票初始价与波动幅度、僵局回合上限——全部对应契约硬约束或 provisional 默认值。

增量批与多 demo 扇出只需改资产值,不动 C++,这是 Phase 14 设计的核心留缝。

## 4. 关键类清单

| 类 | 角色 |
|----|------|
| `AMADemoGameMode` | 回合状态机 + 规则裁决 |
| `AMADemoGameState` | 全量可读状态 |
| `UMADemoPlayerData` | 单玩家运行期数据 |
| `AMADemoPlayerController` | 意图转发 |
| `UMADemoBoardDataAsset` | 棋盘数据(数据驱动) |
| `UMADemoRulesDataAsset` | 规则参数(数据驱动) |
| `UMADemoStockMarket` | 股票市场态与回合波动 |
| `UMADemoHUDWidget` | HUD 常驻只读快照 |
| `UMADemoStartScreenWidget` | 开始画面 |
| `UMADemoMainMenuWidget` | 主菜单 |
| `UMADemoSettingsWidget` | 设置 |
| `UMADemoPauseWidget` | 暂停 |
| `UMADemoResultsWidget` | 结果 |
| `UMADemoInputFoundation` | 输入底座 |
| `UMADemoAudioFoundation` | 音频底座 |
| `UMADemoPlatformFoundation` | 平台底座 |

枚举与结构:`EMADemoTileType`、`EMADemoColorGroup`、`EMADemoTurnPhase`、`EMADemoInputAction`、
`FMADemoTileInfo`、`FMADemoDiceResult`、`FMADemoStock`、`FMADemoAuctionState`、`FMADemoHUDSnapshot`。

## 5. Provisional 决策汇总

v0 实施中对 GDD/契约未规定点给定的默认值(每条已随对应 story 的 evidence.provisional_decisions 存档):

- **插件命名** `Demo_MonopolyAuction`:Demo_ 前缀大驼峰,从契约 game_identity(monopoly_like)+
  扩展玩法(auction)派生。
- **交易所角格选址 16 号**(原机会格):扩展 GDD 2.2 要求替换一个普通空白格但未指定位置。
- **僵局回合上限 200,达上限按净资产判最高者胜**:契约 cg-max-game-length 高风险未决点,
  GDD 仅给目标时长未给硬上限,给可收敛默认值。
- **设置持久化 session_only**:契约 cg-platform-persistence 的 provisional_default。
- **先手顺序按索引固定 + 确定性骰子(FRandomStream)**:GDD 提随机先手,为冒烟可复现改固定。
- **AutoBuyPolicy(买得起且留够保释金缓冲才买)**:无人值守需自动购买裁决。
- **破产清算(现金尽数转债主后退场,地产归无主)**:GDD 规定破产地产无主,清算细节给简化全转。
- **默认键位**(确认=Enter/取消=Esc/暂停=Esc/掷骰=Space)与默认分辨率 1280x720。
- **截图证据降级**:Visual story 用 widget 反射 dump + 一张真实引擎渲染 PNG 替代逐页截图
  (无 authored WBP 资产与绑定关卡,无人值守不可渲染具体页面),已如实披露。

## 6. 已知边界(非 v0 范围)

- 拍卖、股票交易的完整弹出式 UI 与交互流在 increment-1/increment-2。
- 无 authored 3D 关卡/棋盘 Actor/棋子 Actor 与 WBP 蓝图实例;v0 聚焦逻辑主链与 widget 接口能力。
- 网络多人、AI 对手为契约 deferred 能力,不在范围。
