# Phase 8 DD-3: Lowering 映射表 + C++ 类详细设计

> 本文件为 Phase 8 M3（MonopolyGame 垂直切片执行）的详细设计。
> 基于 `build_ir.json` 14 个 Build Steps 和 GDD §6 的 C++ 类定义。
> 日期：2026-04-04

---

## 1. Build Step → C++ 类 映射总表

| Step | ir_action | 主要 C++ 类 / 产物 | 执行通道 | 依赖 |
|------|-----------|---------------------|----------|------|
| 01 | create_board_ring_layout | AMBoardManager, L_MonopolyBoard | Channel A (Python) | — |
| 02 | create_tile_actors | AMTile (×28) | Channel A (Python) | 01 |
| 03 | assign_tile_metadata | FMTileData, DT_TileData, EMTileType, EMColorGroup | C++ Code | 02 |
| 04 | create_player_tokens | AMPlayerPawn (×4) | Channel A (Python) | 01 |
| 05 | create_game_mode_shell | AMMonopolyGameMode, AMMonopolyGameState, AMMonopolyPlayerState, AMMonopolyPlayerController | C++ Code | — |
| 06 | bind_turn_state_machine | EMTurnState (enum), FSM logic in GameMode | C++ Code | 05 |
| 07 | bind_dice_roll_logic | FMDiceResult, AMDice | C++ Code | 06 |
| 08 | bind_tile_event_dispatch | HandleTileEvent() in GameMode | C++ Code | 03,06 |
| 09 | bind_property_economy_logic | Economy 方法 in GameMode+GameState | C++ Code | 03,05 |
| 10 | bind_jail_logic | Jail 方法 in GameMode | C++ Code | 06,07 |
| 11 | bind_bankruptcy_logic | Bankruptcy 方法 in GameMode | C++ Code | 09 |
| 12 | create_phase1_ui_widgets | UMGameHUDWidget, UMPopupWidget, 5× WBP | C++ Code + Editor | 05 |
| 13 | bind_ui_to_game_state | Delegates in GameState, Bindings in Widgets | C++ Code | 12,06 |
| 14 | attach_validation_hooks | FMMonopolyTest_* | C++ Code | 13 |

---

## 2. C++ 文件清单

所有新增文件位于 `Source/Mvpv4TestCodex/`（项目层 Gameplay Module），不修改 AgentBridge 插件层。

### 2.1 头文件（Public/）

| 文件名 | 类/结构体 | 对应 Step |
|--------|-----------|-----------|
| `MMonopolyTypes.h` | EMTileType, EMColorGroup, EMTurnState, EMGamePhase, FMTileData, FMDiceResult | 03,06,07 |
| `MMonopolyGameMode.h` | AMMonopolyGameMode | 05,06,07,08,09,10,11 |
| `MMonopolyGameState.h` | AMMonopolyGameState | 05,09,13 |
| `MMonopolyPlayerState.h` | AMMonopolyPlayerState | 05 |
| `MMonopolyPlayerController.h` | AMMonopolyPlayerController | 05 |
| `MTile.h` | AMTile | 02 |
| `MBoardManager.h` | AMBoardManager | 01 |
| `MPlayerPawn.h` | AMPlayerPawn | 04 |
| `MDice.h` | AMDice | 07 |
| `MGameHUDWidget.h` | UMGameHUDWidget | 12 |
| `MPopupWidget.h` | UMPopupWidget | 12 |

### 2.2 实现文件（Private/）

每个 `.h` 对应一个 `.cpp`，共 11 对。

---

## 3. 枚举和结构体详细定义

### 3.1 MMonopolyTypes.h

```cpp
#pragma once
#include "CoreMinimal.h"
#include "MMonopolyTypes.generated.h"

// 格子类型枚举 — 对应 tile_system_spec.tile_types
UENUM(BlueprintType)
enum class EMTileType : uint8
{
    START        UMETA(DisplayName = "起点"),
    PROPERTY     UMETA(DisplayName = "地产"),
    TAX          UMETA(DisplayName = "税务"),
    CHANCE       UMETA(DisplayName = "机会"),
    COMMUNITY    UMETA(DisplayName = "公共基金"),
    JAIL_VISIT   UMETA(DisplayName = "监狱探访"),
    FREE_PARKING UMETA(DisplayName = "免费停车"),
    GO_TO_JAIL   UMETA(DisplayName = "前往监狱")
};

// 颜色组枚举 — 对应 tile_system_spec.color_groups
UENUM(BlueprintType)
enum class EMColorGroup : uint8
{
    None      UMETA(DisplayName = "无"),
    Brown     UMETA(DisplayName = "Brown"),
    LightBlue UMETA(DisplayName = "LightBlue"),
    Pink      UMETA(DisplayName = "Pink"),
    Orange    UMETA(DisplayName = "Orange"),
    Red       UMETA(DisplayName = "Red"),
    Green     UMETA(DisplayName = "Green"),
    Blue      UMETA(DisplayName = "Blue")
};

// 回合状态枚举 — 对应 turn_flow_spec.turn_state_machine.states
UENUM(BlueprintType)
enum class EMTurnState : uint8
{
    WaitForRoll       UMETA(DisplayName = "等待掷骰"),
    RollingDice       UMETA(DisplayName = "掷骰中"),
    MovingPawn        UMETA(DisplayName = "棋子移动中"),
    PassStartCheck    UMETA(DisplayName = "过起点检查"),
    TileEvent         UMETA(DisplayName = "格子事件"),
    PostEvent         UMETA(DisplayName = "事件后处理"),
    DoublesExtraTurn  UMETA(DisplayName = "双数额外回合"),
    TripleDoublesJail UMETA(DisplayName = "三连双入狱"),
    TurnEnd           UMETA(DisplayName = "回合结束"),
    GameOver          UMETA(DisplayName = "游戏结束")
};

// 游戏阶段枚举
UENUM(BlueprintType)
enum class EMGamePhase : uint8
{
    WaitingForPlayers UMETA(DisplayName = "等待玩家"),
    InProgress        UMETA(DisplayName = "游戏进行中"),
    Finished          UMETA(DisplayName = "游戏结束")
};

// 格子数据结构 — 对应 tile_data_table 的一行
USTRUCT(BlueprintType)
struct FMTileData
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 TileIndex = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FString TileName;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    EMTileType TileType = EMTileType::START;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    EMColorGroup ColorGroup = EMColorGroup::None;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 Price = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 BaseRent = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 TaxAmount = 0;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    int32 OwnerPlayerIndex = -1;  // -1 = 无主
};

// 骰子结果结构 — 对应 turn_flow_spec.dice_rules
USTRUCT(BlueprintType)
struct FMDiceResult
{
    GENERATED_BODY()

    UPROPERTY(BlueprintReadOnly)
    int32 Die1 = 0;

    UPROPERTY(BlueprintReadOnly)
    int32 Die2 = 0;

    UPROPERTY(BlueprintReadOnly)
    int32 Total = 0;

    UPROPERTY(BlueprintReadOnly)
    bool bIsDoubles = false;
};
```

---

## 4. 核心类详细设计

### 4.1 AMMonopolyGameMode — 游戏逻辑核心

**对应 Build Steps**: 05, 06, 07, 08, 09, 10, 11

```
父类: AGameModeBase
职责: 回合状态机、骰子、事件分发、经济、监狱、破产全部逻辑

=== 属性 ===
// 回合 FSM (Step 06)
- CurrentTurnState : EMTurnState                    // 当前状态
- ConsecutiveDoublesCount : int32                   // 连续双数计数
- CurrentPlayerIndex : int32                        // 当前玩家索引

// 引用 (Step 01/02/04)
- BoardManager : AMBoardManager*                    // 棋盘管理器
- Dice : AMDice*                                    // 骰子 Actor
- PlayerPawns : TArray<AMPlayerPawn*>               // 棋子数组

=== 初始化方法 ===
- BeginPlay()                                       // 初始化棋盘、玩家、UI
- InitGame(int32 NumPlayers)                        // 创建玩家、发放初始资金

=== 回合 FSM 方法 (Step 06) ===
- SetTurnState(EMTurnState NewState)                // 统一状态转换入口
- OnEnterState(EMTurnState State)                   // 进入状态时的处理
- StartTurn()                                       // → WaitForRoll
- OnPlayerRequestRoll()                             // WaitForRoll → RollingDice
- OnDiceResultReady(FMDiceResult Result)             // RollingDice → MovingPawn
- OnPawnArrived(int32 TargetTileIndex)              // MovingPawn → PassStartCheck
- OnPassStartCheckDone()                            // PassStartCheck → TileEvent
- OnTileEventResolved()                             // TileEvent → PostEvent
- ProcessPostEvent()                                // PostEvent → 分支判断
- EndTurn()                                         // TurnEnd → 下一玩家
- FindNextNonBankruptPlayer() : int32               // 跳过破产玩家

=== 骰子方法 (Step 07) ===
- RollDice() : FMDiceResult                         // 生成 2d6 结果
- ResetConsecutiveDoubles()                         // 回合结束/入狱时重置

=== 事件分发 (Step 08) ===
- HandleTileEvent(int32 TileIndex)                  // switch on TileType
- HandlePropertyTile(int32 TileIndex)               // 无主→购买，他人→租金，自有→无
- HandleTaxTile(int32 TileIndex)                    // 扣税或破产
- HandleGoToJailTile()                              // 传送到监狱

=== 经济方法 (Step 09) ===
- TryPurchaseProperty(int32 PlayerIndex, int32 TileIndex) : bool
- CollectRent(int32 OwnerIndex, int32 TenantIndex, int32 TileIndex)
- CalculateEffectiveRent(int32 TileIndex) : int32   // 基础 × 颜色组倍率
- TransferMoney(int32 FromPlayer, int32 ToPlayer, int32 Amount) : bool
- DeductMoney(int32 PlayerIndex, int32 Amount) : bool  // 扣银行

=== 监狱方法 (Step 10) ===
- SendToJail(int32 PlayerIndex)                     // 传送 + 设状态
- HandleJailTurn(int32 PlayerIndex)                 // 监狱回合入口
- PayBail(int32 PlayerIndex) : bool                 // 交保释金
- TryRollDoublesForJail(int32 PlayerIndex)          // 掷双数尝试
- ForcePayBail(int32 PlayerIndex)                   // 第三回合强制保释

=== 破产方法 (Step 11) ===
- TriggerBankruptcy(int32 PlayerIndex)              // 标记 + 释放地产
- ReleaseAllProperties(int32 PlayerIndex)           // 所有地产设为无主
- CheckGameEndCondition() : bool                    // 剩余1人 → GameOver
- DeclareWinner(int32 PlayerIndex)                  // 宣布获胜
```

### 4.2 AMMonopolyGameState — 全局同步数据

**对应 Build Steps**: 05, 09, 13

```
父类: AGameStateBase
职责: 所有需要同步/UI 访问的游戏数据、事件委托

=== 属性 ===
- TileDataArray : TArray<FMTileData>                // 28 格数据（含动态 OwnerPlayerIndex）
- TurnNumber : int32                                // 回合数
- CurrentPlayerIndex : int32                        // 当前玩家（冗余同步用）
- GamePhase : EMGamePhase                           // 游戏阶段
- ActivePlayerCount : int32                         // 存活玩家数

=== 委托 (Step 13) ===
- DECLARE_DYNAMIC_MULTICAST_DELEGATE(FOnTurnChanged)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnMoneyChanged, int32, PlayerIndex)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnPawnMoved, int32, PlayerIndex)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnDiceRollRequested, int32, PlayerIndex)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnUnownedPropertyLand, int32, PlayerIndex, int32, TileIndex)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FOnRentDue, int32, TenantIndex, int32, OwnerIndex, int32, Amount)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FOnTaxDue, int32, PlayerIndex, int32, Amount)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnJailTurnStart, int32, PlayerIndex)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnBankruptcy, int32, PlayerIndex)
- DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FOnGameOver, int32, WinnerIndex)

=== 方法 ===
- InitializeTileData()                              // 用 28 格数据表填充
- GetTileData(int32 Index) : FMTileData&
- SetTileOwner(int32 TileIndex, int32 OwnerIndex)
- DoesPlayerOwnFullColorGroup(int32 PlayerIndex, EMColorGroup Group) : bool
```

### 4.3 AMMonopolyPlayerState — 玩家数据

**对应 Build Step**: 05

```
父类: APlayerState
职责: 单个玩家的经济和状态数据

=== 属性 ===
- Money : int32 = 1500                              // 当前资金
- CurrentTileIndex : int32 = 0                      // 当前格子
- OwnedTileIndices : TArray<int32>                  // 拥有的地产
- bIsInJail : bool = false                          // 是否在监狱
- JailTurnsRemaining : int32 = 0                    // 监狱剩余回合
- bIsBankrupt : bool = false                        // 是否破产
- PlayerColor : FLinearColor                        // 颜色标识
- PlayerDisplayName : FString                       // 显示名

=== 方法 ===
- AddMoney(int32 Amount)
- DeductMoney(int32 Amount) : bool                  // 返回是否够钱，够则扣
- CanAfford(int32 Amount) : bool
- AddProperty(int32 TileIndex)
- RemoveProperty(int32 TileIndex)
- RemoveAllProperties()                             // 破产时调用
```

### 4.4 AMBoardManager — 棋盘管理

**对应 Build Steps**: 01, 02

```
父类: AActor
职责: 棋盘3D布局生成、格子坐标计算

=== 属性 ===
- TileActors : TArray<AMTile*>                      // 28 个格子 Actor
- SideLength : float = 700.f                        // 边长 cm
- TileSpacing : float = 100.f                       // 格子间距 cm

=== 方法 ===
- SpawnBoard()                                      // 生成环形棋盘
- CalculateTileWorldLocation(int32 Index) : FVector  // 计算格子世界坐标
- GetTileActor(int32 Index) : AMTile*
- HighlightTile(int32 Index, FLinearColor Color)
```

### 4.5 AMTile — 格子 Actor

**对应 Build Step**: 02

```
父类: AActor
组件: UStaticMeshComponent(格子模型), UTextRenderComponent(名称)

=== 属性 ===
- TileIndex : int32
- TileData : FMTileData                             // 格子数据副本

=== 方法 ===
- InitTile(const FMTileData& Data)
- SetOwnerColor(FLinearColor Color)                 // 改变材质显示拥有者
- SetHighlight(bool bHighlight)
```

### 4.6 AMPlayerPawn — 棋子

**对应 Build Step**: 04

```
父类: APawn
组件: UStaticMeshComponent(棋子模型)

=== 属性 ===
- OwnerPlayerIndex : int32

=== 方法 ===
- MoveToTile(FVector Target, int32 Steps)           // 逐格移动动画（占位）
- OnMoveComplete()                                  // 移动完成委托
- SetPawnColor(FLinearColor Color)
```

### 4.7 AMDice — 骰子

**对应 Build Step**: 07

```
父类: AActor
组件: UStaticMeshComponent(骰子模型)

=== 方法 ===
- RollDice() : FMDiceResult                         // FMath::RandRange(1,6) × 2
- PlayRollAnimation()                               // 占位动画函数
- OnRollComplete()                                  // 动画完成委托
```

### 4.8 UMGameHUDWidget — 常驻 HUD

**对应 Build Step**: 12

```
父类: UUserWidget

=== 绑定组件 (BindWidget) ===
- CurrentPlayerText : UTextBlock*
- MoneyListBox : UVerticalBox*                      // 所有玩家资金列表
- TurnNumberText : UTextBlock*
- CurrentTileText : UTextBlock*

=== 方法 ===
- UpdateCurrentPlayer(int32 PlayerIndex)
- UpdateAllPlayersMoney(const TArray<AMMonopolyPlayerState*>& Players)
- UpdateTurnNumber(int32 TurnNum)
- UpdateCurrentTileInfo(const FString& TileName, EMTileType Type)
```

### 4.9 UMPopupWidget — 弹窗基类

**对应 Build Step**: 12

```
父类: UUserWidget
职责: 所有弹窗的公共基类

=== 属性 ===
- TitleText : UTextBlock*
- BodyText : UTextBlock*
- ButtonContainer : UHorizontalBox*

=== 方法 ===
- ShowPopup(const FString& Title, const FString& Body, const TArray<FString>& ButtonLabels)
- OnButtonClicked(int32 ButtonIndex)                // 委托通知 GameMode
- ClosePopup()

=== 子类（无独立 C++ 类，由 WBP 的参数化区分）===
- WBP_DicePopup: ShowPopup + 骰子结果显示区域
- WBP_BuyPopup: ShowPopup + 地产信息区域 + Buy/Pass 两按钮
- WBP_InfoPopup: ShowPopup + 单确认按钮（租金/税/破产/结束复用）
- WBP_JailPopup: ShowPopup + 保释/掷双数 两按钮 + 强制保释提示
```

---

## 5. 执行顺序与依赖图

```
独立起点:
  step-05-game-mode ─────────────────────────────────────┐
  step-01-board-layout ──┐                                │
                         ├→ step-02-tile-actors           │
                         │    └→ step-03-tile-metadata    │
                         └→ step-04-player-tokens         │
                                                          │
  step-05 完成后:                                         │
  ├→ step-06-turn-fsm ◄──────────────────────────────────┘
  │    ├→ step-07-dice-logic
  │    ├→ step-08-tile-events ◄── step-03
  │    └→ step-10-jail-logic ◄── step-07
  │
  ├→ step-09-property-economy ◄── step-03
  │    └→ step-11-bankruptcy-logic
  │
  └→ step-12-ui-widgets
       └→ step-13-ui-binding ◄── step-06
            └→ step-14-validation
```

**建议实施分批**:

| 批次 | Steps | 内容 | 前置条件 |
|------|-------|------|----------|
| Batch 1 | 05, 03(types only) | GameMode/State/PlayerState 壳 + 枚举/结构体 | 无 |
| Batch 2 | 01, 02, 04 | 棋盘布局 + 格子 + 棋子 Actor（Channel A 脚本） | Batch 1 编译通过 |
| Batch 3 | 06, 07 | 回合 FSM + 骰子逻辑 | Batch 1 |
| Batch 4 | 08, 09, 10, 11 | 事件分发 + 经济 + 监狱 + 破产 | Batch 1,3 |
| Batch 5 | 12, 13 | UI Widget + 事件绑定 | Batch 1,3 |
| Batch 6 | 14 | 验证测试 | 全部 |

---

## 6. MCP 工具使用映射

| Step | 使用的 MCP 工具 | Layer |
|------|----------------|-------|
| 01 | `create_level`, `run_editor_python` | L1 + L2 |
| 02 | `spawn_actor`, `run_editor_python` | L1 |
| 03 | `run_editor_python` (创建 DataTable) | L2 |
| 04 | `spawn_actor` | L1 |
| 05-11 | `run_editor_python` (编译验证) | L2 |
| 12 | `create_widget_blueprint`, `run_editor_python` | L2 |
| 13 | C++ 代码 (编译时静态绑定) | — |
| 14 | `run_editor_python` (触发自动化测试) | L2 |

---

## 7. 关键设计决策

| 决策 | 选项 | 选定 | 理由 |
|------|------|------|------|
| FSM 实现方式 | UE5 State Tree / 手动 switch | 手动 switch on EMTurnState | Phase 1 状态数少(10)，State Tree 引入不必要的复杂度 |
| 数据存储 | DataTable Asset / C++ 硬编码 | C++ 初始化 + Runtime TArray | 28 格数据通过 InitializeTileData() 硬编码填充，避免 Asset 依赖 |
| UI 弹窗架构 | 每种弹窗独立 C++ 类 / 基类+参数化 | 基类 UMPopupWidget + WBP 参数化 | 减少类爆炸，4 个 WBP 共享一个基类 |
| 颜色组检查 | 遍历 TileDataArray / 预缓存 Map | 遍历 TileDataArray | 28 格遍历开销可忽略，Phase 1 不需要优化 |
| 资金不足处理 | 立即破产 / 允许出售 | 立即破产 | Phase 1 无抵押/交易，资金不足直接触发破产 |
| Blue 单地产组 | 忽略颜色组加成 / 自动满足 | 自动满足颜色组条件 | 拥有组内全部地产(1/1)即视为完整，与其他组逻辑一致 |

---

## 8. 与 GDD §6 的差异说明

| GDD §6 类名 | DD-3 类名 | 差异说明 |
|-------------|-----------|----------|
| AMGameMode | AMMonopolyGameMode | 添加 Monopoly 前缀避免与引擎类冲突 |
| AMGameState | AMMonopolyGameState | 同上 |
| AMPlayerState | AMMonopolyPlayerState | 同上 |
| AMBoardManager | AMBoardManager | 保持一致 |
| AMTile | AMTile | 保持一致 |
| AMPlayerPawn | AMPlayerPawn | 保持一致 |
| AMDice | AMDice | 保持一致 |
| EGamePhase | EMGamePhase + EMTurnState | GDD 用单一枚举，DD-3 拆分为游戏阶段和回合状态两个枚举 |
| FMTileInfo | FMTileData | 添加 TaxAmount 和 OwnerPlayerIndex 字段 |
| — | AMMonopolyPlayerController | GDD 未定义，DD-3 新增用于 UI 输入路由 |
| — | UMGameHUDWidget / UMPopupWidget | GDD §4 仅文字描述，DD-3 给出 C++ 基类 |

---

## 9. 验证检查点总结

| val-id | 检查内容 | 自动化方式 |
|--------|---------|-----------|
| val-01 | 场景中 28 个 Tile Actor | `GetAllActorsOfClass(AMTile)` count == 28 |
| val-02 | TileDataArray 28 行，16 个 PROPERTY 有 Price>0 | 遍历检查 |
| val-03 | 2-4 个 PlayerPawn | `GetAllActorsOfClass(AMPlayerPawn)` |
| val-04 | GameMode + GameState 存在 | `GetWorld()->GetAuthGameMode()` |
| val-05 | 初始状态 WaitForRoll | `GameMode->CurrentTurnState == EMTurnState::WaitForRoll` |
| val-06 | 骰子结果 [2,12] | 循环 100 次 `RollDice()` 验证范围 |
| val-07 | 8 种格子事件正确分发 | Mock 落地每种类型，检查调用的函数 |
| val-08 | 购买扣款 + 颜色组租金翻倍 | 模拟购买和收租场景 |
| val-09 | 入狱/保释/掷双数/强制保释 | 模拟全部监狱路径 |
| val-10 | 破产释放地产 + 游戏结束 | 模拟资金不足触发 |
| val-11 | 5 个 Widget 存在 | `IsValid(HUDWidget)` etc. |
| val-12 | 10 个委托已绑定 | `OnTurnChanged.IsBound()` etc. |
