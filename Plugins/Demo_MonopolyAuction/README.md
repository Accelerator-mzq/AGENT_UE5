# Demo_MonopolyAuction

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。

Phase 14 v0 自包含可玩 demo(Monopoly 扩展版:拍卖 + 股票)的 Runtime 插件。
完整设计见 `Docs/design.md`、架构见 `Docs/architecture.md`、变更见 `Docs/changelog.md`。

## 试玩入口地图与启动命令

authored 启动关卡:`/Demo_MonopolyAuction/Maps/L_MonopolyDemo`
(WorldSettings GameModeOverride 绑定 `AMADemoGameMode`)。

### 模式一:人玩(键盘交互)

```
UnrealEditor-Cmd.exe <uproject> /Demo_MonopolyAuction/Maps/L_MonopolyDemo -game -windowed -ResX=1280 -ResY=720
```

启动后进入对局,左上角 Canvas HUD 实时显示回合/当前玩家/各玩家现金与股值/位置/股市行情;
用键盘推进游戏。

### 模式二:无人值守自动演示(截图/回归用)

```
UnrealEditor-Cmd.exe <uproject> /Demo_MonopolyAuction/Maps/L_MonopolyDemo -game -windowed -ResX=1280 -ResY=720 \
  -MADemoAutoPlay=5 -MADemoAutoShot -MADemoShotPath=<绝对路径>.png
```

`-MADemoAutoPlay=N` 自动推进 N 回合(自动模式由驱动逻辑代按 Enter 切人);`-MADemoAutoShot` 演示完截图退出;
`-MADemoShotPath=` 指定截图输出;`-MADemoPanel=<start|menu|settings|input|audio|platform|results>`
切换截取的前台外壳/底座面板(provisional,仅演示截图用,不影响人玩路径);
`-MADemoAutoPauseShot` 注入真实 Escape 按键事件后截取暂停画面(走完整输入管线)。

## 键位表(默认意图映射,provisional;试玩反馈修复轮对齐真实行为)

| 动作 | 默认键 | 生效阶段 | 转发 |
|------|--------|---------|------|
| 掷骰 | `Space` | 等待掷骰(WaitingForRoll);TurnEnd/暂停时无效 | `AMADemoPlayerController::IntentRollDice` -> `AMADemoGameMode::RequestRollAndResolve` |
| 结束回合 | `Enter` | 回合结束(TurnEnd);其余阶段/暂停时无效 | `AMADemoPlayerController::IntentEndTurn` -> `AMADemoGameMode::AdvanceToNextPlayer` |
| **拍卖出价** | `Space` | 拍卖中(Auction,语义切换);买不起拟出价时无效 | `AMADemoPlayerController::IntentRollDice` -> `AMADemoGameMode::AuctionBidCurrent` |
| **拍卖弃权** | `Enter` | 拍卖中(Auction,语义切换) | `AMADemoPlayerController::IntentEndTurn` -> `AMADemoGameMode::AuctionPassCurrent` |
| 暂停/恢复 | `Esc` | 任意阶段切换;暂停期间 Space/Enter 不响应(拍卖同样冻结) | `AMADemoPlayerController::IntentPause` -> `AMADemoGameMode::TogglePauseState` |

HUD 键位提示随阶段切换:等待掷骰提示 Space,回合结束提示 Enter,拍卖中提示出价/弃权(含拟出价金额);
暂停时中央渲染暂停面板([Esc] 继续)。

## 一局预期流程

1. `InitializeGame`:N 名玩家(2-6,关卡默认 4),各 $1500,棋子置起点,3 支股票各 $100。
2. 每回合:`StartTurn`(股票按上轮掷骰确定性波动 → 监狱回合判定)→ 按 `Space` 掷骰
   (`RequestRollAndResolve`:掷骰 2D6 → 移动 → 过起点 +$200 → 落点事件:地产自动购买/付租、
   税务扣款、前往监狱)→ 双数再掷(三连双入狱则本回合停 TurnEnd)→ **结算完停在
   TurnEnd,HUD 提示按 `Enter` 结束回合** → `Enter` 切下一玩家(回合节奏归玩家;
   监狱蹲守同样停 TurnEnd 后由 `Enter` 结束;破产者由系统自动跳过,provisional)。
3. 破产即退场、地产归无主;存活 1 人或达回合上限(默认 200,按净资产)→ `GameOver`,
   `AMADemoGameState::WinnerIndex` 落定,结果面板呈现胜者。

## 拍卖在对局中怎么发生 / 怎么看(增量批 1,GDD 2.1)

- **怎么发生**:当前玩家落在**无主地产**且拒购(自动购买策略拒绝:现金不足地价+缓冲)时,
  立即进入英式拍卖,回合阶段切到"拍卖中"。
- **怎么看**:屏幕中央弹出**拍卖面板**——标的名/地价/起拍价(=地价 50%)/步长($10)、
  当前最高价与出价人(高亮)、各玩家竞价状态(弃权变灰)、"<- 轮到"指示、出价记录
  (最近 6 条)、底部拟出价键位提示;左上主 HUD 阶段显示"拍卖中"。
- **怎么玩**(热座):轮到的竞价玩家按 `Space` 出价(首口=起拍价,其后=当前最高+$10)
  或按 `Enter` 弃权(弃权即退出本场);买不起拟出价时面板提示"只能弃权"。
  全员弃权且无人出价 → 流拍保持无主;其余全弃 → 最高出价者立即支付并获得地契。
- **拍后**:回合停 TurnEnd 等 `Enter`(若拍卖打断了双数追加掷,拍后回到等待掷骰);
  主 HUD 保留"上一场拍卖"结果行。

## 冒烟

```
AGENTBRIDGE_UE_CMD="<UE>/UnrealEditor-Cmd.exe" \
python Plugins/AgentBridge/Scripts/demo_smoke/runner.py \
  --filter "Demo_MonopolyAuction." --v0-filter "Demo_MonopolyAuction.Smoke" \
  --out <绝对路径>/smoke_report.json
```

v0 基线 8 用例(已冻结):BoardData / Dice / Economy / EntryMapLoad / FullGameLoop /
InteractionSemantics / JailBankruptcy / WidgetCreation。
增量批 1 新增 6 用例(Demo_MonopolyAuction.Inc1,独立文件):AuctionTrigger /
AuctionBidProgression / AuctionSettlement / AuctionNoSale / AuctionPausedFrozen /
FullGameWithAuction。全量 14 用例,增量批提交要求 v0 回归段 pass。

## Provisional 摘要

插件名 `Demo_MonopolyAuction`(契约派生);交易所选 16 号格;僵局上限 200 按净资产收敛;
设置 session_only;确定性骰子与固定先手;自动购买保守策略;Canvas HUD 截图通路(UMG 叠加层
不入标准截图,改 Canvas 直绘);PythonScriptPlugin 临时启用建关卡;自动驾驶启动参数。
增量批 1:拍卖轮转起点=落格玩家且拒购者可参拍;弃权粘性;自动竞价不溢价(拟出价≤地价);
购买/竞价缓冲拆分(1200/100,实测调参保证拍卖在对局中频率可见,数据驱动可回调)。
完整清单见 `Docs/design.md` §5。

## 边界

股票完整交互 UI(increment-2)、authored 3D 棋盘与棋子 Actor(图形归 Phase 15)非当前范围,
见 `Docs/changelog.md`。
