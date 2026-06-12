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

## v0 试玩反馈修复轮(2026-06-12,msc C4 attempt 2 试玩窗口反馈)

发现:Enter/Esc 为空操作且 HUD/README 宣称与行为不符(掷骰后自动切人,Enter 无事可做;
Esc 仅打日志)。修复(msc 裁决:缺陷修复轮,不算 PIVOT,v0 未冻结):

- **Enter 获得真实语义**:`AMADemoGameMode` 的 RequestRollAndResolve 正常结算后停 TurnEnd
  不再自动切人,Enter(IntentEndTurn)在 TurnEnd 时 AdvanceToNextPlayer;TurnEnd 阶段
  Space 无效。监狱蹲守、三连双入狱同样停 TurnEnd(给玩家看清事件再按 Enter);破产者由
  系统自动跳过(玩家对已退场者无操作空间)——三个特殊路径取舍均记 provisional。
- **自动模式不破坏**:RunFullGameToCompletion / AutoAdvanceOneTurn(冒烟与 -MADemoAutoPlay)
  在 TurnEnd 由驱动逻辑代按 Enter(直调 AdvanceToNextPlayer),冒烟不挂在等键上。
- **Esc 实做暂停**:`AMADemoGameState` 增 bPaused;`AMADemoGameMode` 增 TogglePauseState /
  SetPauseState / IsPaused;Esc 切换暂停态,暂停期间 Space/Enter 被拒(PC 与 GameMode
  双层守卫);Canvas HUD(`AMADemoHUD`)渲染真实暂停面板,再按 Esc 恢复。
- **宣称对齐**:HUD 键位提示按阶段切换(WaitingForRoll→Space / TurnEnd→Enter / 暂停→Esc 继续),
  `FMADemoHUDSnapshot` 增 TurnPhase/bPaused 字段供 UMG widget 同步;README 键位表与
  一局流程同步更新;-MADemoPanel=pause 演示分支删除,pause 截图改由 -MADemoAutoPauseShot
  真实 Escape 按键注入路径(走完整输入管线)截取。
- **冒烟**:Dice 用例适配新流程;新增 Demo_MonopolyAuction.Smoke.InteractionSemantics
  钉死四条交互语义回归(结算停 TurnEnd 未切人/TurnEnd 掷骰被拒/Enter 推进/暂停掷骰被拒);
  8/8 全绿。

## increment-1(2026-06-12,英式拍卖入可玩循环)

msc PROCEED 后首个增量批。v0 冒烟基线已冻结(hash 守门),本批零触碰冻结文件,
拍卖用例放独立新文件 Demo_MonopolyAuction.Inc1 名字空间。

新增(GDD 2.1 地产拍卖;合成包 synthesized.gameplay-property-auction.v1 为设计参考):
- **触发**:玩家落无主地产且拒购(AutoBuyPolicy 拒绝)→ 立即进入英式拍卖;
  途经/已有主/非地产格不触发(`AMADemoGameMode` 的 StartAuction 守卫)。
- **规则**(数据驱动,`UMADemoRulesDataAsset`):起拍价=地价 50%、加价步长 $10(GDD 锁定);
  全体未破产玩家轮流出价或弃权(破产者无资格);弃权粘性(退出本场);
  全弃且无人出价→流拍保持无主(不降价重拍);仅剩最高出价者→立即按出价支付并获地契。
- **热座竞价交互**:拍卖期键位语义切换——轮到的竞价玩家 [Space]=出价(首口=起拍价,
  其后=最高+步长)、[Enter]=弃权;买不起拟出价时 Space 无效(HUD 提示只能弃权)。
- **HUD 拍卖面板**(`AMADemoHUD` 的 DrawAuctionPanel,GDD 3.1):标的名/地价/起拍价/步长、
  当前最高价+出价人(高亮)、各玩家竞价状态(弃权变灰)、轮到谁、出价记录(最近 6 条)、
  拟出价键位提示;拍后主面板保留"上一场拍卖"结果行。
- **暂停冻结**:Esc 暂停期间出价/弃权双层守卫拒绝,恢复后继续。
- **回合流衔接**:拍卖打断双数追加掷时暂存,拍后恢复等待掷骰,否则停 TurnEnd;
  自动模式(冒烟直驱/-MADemoAutoPlay)按自动竞价策略代打
  (出价后剩余≥缓冲且拟出价≤地价则出价,否则弃权,provisional)。
- **冒烟**:新文件 MADemoInc1AuctionTests.cpp 六用例(AuctionTrigger/AuctionBidProgression/
  AuctionSettlement/AuctionNoSale/AuctionPausedFrozen/FullGameWithAuction);
  全量 14/14 通过,v0 回归段 pass(冻结 hash 对账通过)。

**拍卖可见性调参(实测驱动)**:缓冲 100/300 时开局人人买得起,16 块地产售罄前
拒购窗口不存在,120 玩家回合零拍卖(日志实证);购买缓冲(AutoBuyReserveBuffer)
调至 1200 并与竞价缓冲(AuctionBidReserveBuffer=100)拆分后,30 玩家回合内 6 场拍卖
跨玩家竞价成交(便宜地直接买、贵地进拍卖,合真实大富翁手感)。自动演示模式拍卖期
逐口推进(每 tick 一步),旁观者可见面板过程;`-MADemoAuctionShotPath=` 可截首场拍卖面板。

provisional:轮转起点=落格玩家且拒购者可参拍;弃权粘性(全弃即流拍的最小解释);
自动竞价不溢价(拟出价≤地价);购买/竞价缓冲拆分(1200/100,数据驱动可回调)。

## increment-2(待批)

- 股票市场完整交互(交易所买卖面板)。
