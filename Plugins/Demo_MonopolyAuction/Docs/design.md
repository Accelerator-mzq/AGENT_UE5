# Demo_MonopolyAuction — 设计文档(design.md)

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。

## 1. 系统总览

`Demo_MonopolyAuction` 是 Phase 14 v0 的自包含可玩 demo:一个 Monopoly-like 本地热座多人原型,
在经典大富翁核心规则(28 格环形棋盘、2D6 掷骰移动、购地收租、税务、监狱、破产、胜负)之上
预留拍卖与股票市场扩展。来源 GDD `ProjectInputs/GDD/monopoly_extended_auction_v1.md`
(核心规则按引用沿用 `GDD_MonopolyGame.md`)与根契约
`rsc.monopoly.phase1_local_multiplayer.20260611`。

v0 批交付完整的「一局可驱动到终局」主链,并满足 **v0 可玩硬判据**:
authored 启动关卡 `L_MonopolyDemo` 经 `-game` 启动进入对局,键盘意图(掷骰/结束回合/暂停)
推进游戏,Canvas HUD 在画面真实呈现当前玩家/资金/位置/股市等核心状态。

## 2. 架构分层(施工规范 §3)

- **裁决层**:`AMADemoGameMode` 持有全部规则裁决与回合状态机,是唯一改写游戏状态的入口。
- **状态层**:`AMADemoGameState` 承载全量可读状态(棋盘所有权、玩家集合、回合数、骰子结果、
  股票市场、拍卖态、胜者),对外只读 API 供 UI 与冒烟断言。
- **玩家数据**:`UMADemoPlayerData` 以 UObject 建模单玩家(资金/位置/地产/监狱/破产/股票持仓),
  热座多人下避免引入网络栈,使冒烟可纯逻辑直驱。
- **意图层**:`AMADemoPlayerController` 把键盘意图转发给 GameMode,不持有规则。
- **表现层**:`AMADemoHUD`(Canvas 直绘,保证截图可见)+ `UMADemoHUDWidget`(UMG 只读快照,
  契约/冒烟用);前台外壳 widget 只读 GameState、只发意图,不含规则。

## 3. 数据驱动(施工规范 §3 留缝)

可调规则参数与棋盘数据下沉到 DataAsset,C++ 不硬编码可调值:

- `UMADemoBoardDataAsset`:28 格静态数据(类型/名称/颜色组/价格/租金,GDD 2.3 数据表),
  角格索引(起点 0/监狱探访 7/免费停车 14/前往监狱 21)与交易所选址(16)。构造时铺默认棋盘。
- `UMADemoRulesDataAsset`:初始资金 1500、起点奖励 200、骰子 2D6、保释 50、监狱上限 3、
  满色组倍率 2、拍卖起拍价比例/步长、股票初始价/波动幅度、僵局回合上限——对应契约硬约束或
  provisional 默认值。

增量批与多 demo 扇出只需改资产值,不动 C++,这是 Phase 14 设计的核心留缝。

## 4. 关键类清单

| 类 | 角色 |
|----|------|
| `AMADemoGameMode` | 回合状态机 + 规则裁决 |
| `AMADemoGameState` | 全量可读状态 |
| `UMADemoPlayerData` | 单玩家运行期数据 |
| `AMADemoPlayerController` | 键盘意图转发 |
| `UMADemoBoardDataAsset` | 棋盘数据(数据驱动) |
| `UMADemoRulesDataAsset` | 规则参数(数据驱动) |
| `UMADemoStockMarket` | 股票市场态与回合波动 |
| `AMADemoHUD` | Canvas 画面 HUD(截图可见) |
| `UMADemoHUDWidget` | UMG HUD 只读快照 |
| `UMADemoStartScreenWidget` | 开始画面 |
| `UMADemoMainMenuWidget` | 主菜单 |
| `UMADemoSettingsWidget` | 设置 |
| `UMADemoPauseWidget` | 暂停 |
| `UMADemoResultsWidget` | 结果 |
| `UMADemoInputFoundation` | 输入底座 |
| `UMADemoAudioFoundation` | 音频底座 |
| `UMADemoPlatformFoundation` | 平台底座 |

## 5. Provisional 决策汇总

- **插件命名** `Demo_MonopolyAuction`:契约 game_identity(monopoly_like)+ 扩展玩法(auction)派生。
- **交易所角格选址 16 号**(原机会格):扩展 GDD 2.2 要求替换一个普通空白格但未指定位置。
- **僵局回合上限 200,达上限按净资产判最高者胜**:契约 cg-max-game-length 高风险未决,给可收敛默认值。
- **设置持久化 session_only**:契约 cg-platform-persistence 的 provisional_default。
- **固定先手 + 确定性骰子(FRandomStream)**:GDD 提随机先手,为冒烟可复现改固定。
- **AutoBuyPolicy(买得起且留够保释金缓冲才买)**:无人值守需自动购买裁决。
- **破产清算(现金尽数转债主后退场,地产归无主)**:GDD 规定破产地产无主,清算细节给简化全转。
- **默认键位**(确认=Enter/取消=Esc/暂停=Esc/掷骰=Space)与默认分辨率 1280x720。
- **Canvas HUD 截图通路**:UMG/Slate 叠加层不入标准 `-game` 截图,改 `AMADemoHUD` Canvas 直绘
  保证 Visual 证据真实可见;UMG `UMADemoHUDWidget` 仍保留供契约/冒烟/交互。
- **PythonScriptPlugin 临时启用**:authored 关卡经 `-EnablePlugins=PythonScriptPlugin` 通路创建。
- **自动驾驶启动参数**(`-MADemoAutoPlay`/`-MADemoAutoShot`/`-MADemoShotPath`/`-MADemoPanel`):
  无人值守演示与分面板截图用;人玩键盘路径同样真实存在(见 README)。

### 增量批 1 追加(英式拍卖)

- **拍卖触发沿用 AutoBuyPolicy 作"是否购买"裁决**:拒绝(买不起或留缓冲不足)即视为
  GDD 2.1 的"选择不购买",立即开拍——人玩与无人值守同语义。
- **轮转起点 = 落格玩家,拒购者可参拍**:GDD 未定顺序起点;现实 Monopoly 惯例拒购者可竞拍。
- **弃权粘性**(弃权即退出本场):GDD "连续全体弃权则流拍"取一轮全弃即流拍的最小解释
  (合成包设计空间收敛项 pass_reentry_allowed=false)。
- **自动竞价策略**:出价后剩余 ≥ 竞价缓冲(AuctionBidReserveBuffer=100,与购买缓冲拆分)
  且拟出价 ≤ 地价(不溢价抢拍)则出价,否则弃权——无人值守/自动演示代打用。
- **拍卖可见性调参(实测驱动)**:购买缓冲 AutoBuyReserveBuffer 100→1200——实测低缓冲下
  16 块地产开局售罄、拒购窗口不存在(120 玩家回合零拍卖);调参后便宜地直接买、贵地进
  拍卖通道,30 玩家回合 6 场拍卖跨玩家成交。数据驱动可回调。
- **拍卖期键位语义切换**:[Space]=出价 / [Enter]=弃权(热座);买不起拟出价时 Space 无效。

## 6. 拍卖系统(增量批 1,GDD 2.1)

- **触发**:落无主地产且拒购立即进入英式拍卖;途经/已有主/非地产不触发。
- **规则**(数据驱动 `UMADemoRulesDataAsset`):起拍价=地价 50%、步长 $10(GDD 锁定);
  全体未破产玩家轮流出价或弃权;全弃且无人出价→流拍保持无主;
  仅剩最高出价者→立即按出价支付并获得地契(出价守卫保证可兑现,无负余额)。
- **状态**:`FMADemoAuctionState`(标的/起拍价/最高价+出价人/轮到谁/弃权表/出价记录),
  承载于 `AMADemoGameState`,只读供 HUD 与冒烟。
- **呈现**:`AMADemoHUD` 拍卖面板(GDD 3.1 五要素:面板/地产名/最高价/出价/弃权),
  拍后主面板保留"上一场拍卖"结果行;暂停面板压拍卖面板之上(暂停冻结拍卖)。
- **回合衔接**:拍卖打断双数追加掷暂存恢复;拍后停 TurnEnd 等 Enter。

## 7. 已知边界(当前批次外)

- 股票交易完整交互 UI 在 increment-2;数据骨架 `UMADemoStockMarket` 已就位。
- authored 3D 棋盘 Actor/棋子 Actor 非当前范围(图形归 Phase 15);启动关卡为最小可玩外壳 + Canvas HUD。
- 网络多人、AI 对手为契约 deferred 能力,不在范围。
