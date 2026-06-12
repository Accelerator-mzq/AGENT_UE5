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

`-MADemoAutoPlay=N` 自动推进 N 回合;`-MADemoAutoShot` 演示完截图退出;
`-MADemoShotPath=` 指定截图输出;`-MADemoPanel=<start|menu|settings|pause|input|audio|platform|results>`
切换截取的前台外壳/底座面板(provisional,仅演示截图用,不影响人玩路径)。

## 键位表(默认意图映射,provisional)

| 动作 | 默认键 | 转发 |
|------|--------|------|
| 掷骰推进 | `Space` | `AMADemoPlayerController::IntentRollDice` -> `AMADemoGameMode::RequestRollAndResolve` |
| 结束回合 | `Enter` | `AMADemoPlayerController::IntentEndTurn` -> `AMADemoGameMode::AdvanceToNextPlayer` |
| 暂停 | `Esc` | `AMADemoPlayerController::IntentPause` |

## 一局预期流程

1. `InitializeGame`:N 名玩家(2-6,关卡默认 4),各 $1500,棋子置起点,3 支股票各 $100。
2. 每回合:`StartTurn`(股票按上轮掷骰确定性波动 → 监狱回合判定)→
   `RequestRollAndResolve`(掷骰 2D6 → 移动 → 过起点 +$200 → 落点事件:地产自动购买/付租、
   税务扣款、前往监狱)→ 双数再掷(三连双入狱)→ 切下一玩家。
3. 破产即退场、地产归无主;存活 1 人或达回合上限(默认 200,按净资产)→ `GameOver`,
   `AMADemoGameState::WinnerIndex` 落定,结果面板呈现胜者。

## 冒烟

```
AGENTBRIDGE_UE_CMD="<UE>/UnrealEditor-Cmd.exe" \
python Plugins/AgentBridge/Scripts/demo_smoke/runner.py \
  --filter "Demo_MonopolyAuction.Smoke" --out <绝对路径>/smoke_report.json
```

7 用例:BoardData / Dice / Economy / EntryMapLoad / FullGameLoop / JailBankruptcy / WidgetCreation。

## Provisional 摘要

插件名 `Demo_MonopolyAuction`(契约派生);交易所选 16 号格;僵局上限 200 按净资产收敛;
设置 session_only;确定性骰子与固定先手;自动购买保守策略;Canvas HUD 截图通路(UMG 叠加层
不入标准截图,改 Canvas 直绘);PythonScriptPlugin 临时启用建关卡;自动驾驶启动参数。
完整清单见 `Docs/design.md` §5。

## 边界

拍卖/股票完整交互 UI、authored 3D 棋盘与棋子 Actor 非 v0 范围,见 `Docs/changelog.md`。
