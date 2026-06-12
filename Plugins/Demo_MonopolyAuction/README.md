# Demo_MonopolyAuction

> 生成物,与 `ProjectState/runs/run-20260611-052252-5101` 数据不一致时以数据为准。

Phase 14 v0 自包含可玩 demo(Monopoly 扩展版:拍卖 + 股票)的 Runtime 插件。
本首批从 demo story 工单**无人值守**合成,完整设计见 `Docs/design.md`、架构见 `Docs/architecture.md`、
变更见 `Docs/changelog.md`。

## 试玩入口地图

v0 聚焦逻辑主链与 widget 接口能力,**无 authored 关卡/WBP 蓝图实例**,因此试玩以两种方式呈现:

1. **逻辑试玩(冒烟直驱一局)**:经 `AMADemoGameMode` 公有 API 驱动整局。
   - 入口:`AMADemoGameMode::InitializeGame(NumPlayers, Seed)` → `RunFullGameToCompletion()`。
   - 自动跑 7 个冒烟用例验证:
     ```
     AGENTBRIDGE_UE_CMD="<UE>/UnrealEditor-Cmd.exe" \
     python Plugins/AgentBridge/Scripts/demo_smoke/runner.py \
       --filter "Demo_MonopolyAuction.Smoke" \
       --out <绝对路径>/ProjectState/Evidence/phase14_v0_smoke_report.json
     ```
2. **接口试玩(widget 能力)**:`UMADemoHUDWidget::BuildSnapshot` 产出 HUD 快照;前台外壳
   widget 暴露各自意图方法。可在蓝图子类绑定控件搭建可视页面(后续扇出)。

## 操作方式(默认意图映射)

| 动作 | 默认键(`UMADemoInputFoundation`) |
|------|----------------------------------|
| 菜单确认 | Enter |
| 菜单取消 | Esc |
| 暂停 | Esc |
| 掷骰 | Space |

意图经 `AMADemoPlayerController::IntentRollDice` / `IntentEndTurn` 转发到 `AMADemoGameMode`。

## 一局预期流程

1. `InitializeGame`:N 名玩家(2-6),各 1500 金,棋子置起点,3 支股票各 100 金。
2. 每回合:`StartTurn` → `RequestRollAndResolve`(掷骰 2D6 → 股票按掷骰和波动 → 移动 →
   过起点 +200 → 落点事件:地产自动购买/付租、税务扣款、前往监狱、监狱出狱判定)→
   双数再掷(三连双入狱)→ 切下一玩家。
3. 破产即退场、地产归无主;存活 1 人或达回合上限(默认 200,按净资产判)→ `GameOver`,
   `AMADemoGameState::WinnerIndex` 落定。

## Provisional 摘要

插件名 `Demo_MonopolyAuction`(契约派生);交易所选 16 号格;僵局上限 200 按净资产收敛;
设置 session_only;确定性骰子与固定先手(可复现);自动购买保守策略;截图证据降级为反射 dump +
真实渲染 PNG。完整清单见 `Docs/design.md` §5。

## 边界

拍卖/股票完整交互 UI、authored 3D 关卡与棋子 Actor 非 v0 范围,见 `Docs/changelog.md`。
