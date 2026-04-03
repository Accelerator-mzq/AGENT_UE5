# 大富翁游戏 - 游戏设计文档 (GDD) & UE5 实施指南

> **文档用途**：本文档分两部分。Part A 是游戏设计文档，定义所有规则和数据；Part B 是 UE5 实施指南，包含类设计、代码架构和编辑器操作步骤。将 Part A 交给 Claude Code 生成代码，Part B 作为你在 UE5 编辑器中的操作手册。

> **开发分期**：Phase 1 = 本地多人（同屏轮流），Phase 2 = 在线多人。两个阶段共享相同的游戏逻辑，Phase 2 仅增加网络同步层。

---

# PART A: 游戏设计文档

---

## 1. 游戏概述

- **游戏类型**：回合制棋盘策略游戏（大富翁 / Monopoly-like）
- **玩家人数**：2-4 人
- **视角**：3D 俯视角（45° 斜视，类似 Rento）
- **胜利条件**：其他所有玩家破产，最后存活的玩家获胜
- **单局时长目标**：20-40 分钟

---

## 2. 棋盘设计

### 2.1 棋盘布局

棋盘为正方形环形路线，共 **28 格**（每边 7 格 + 4 个角格）。玩家沿顺时针方向移动。

```
格子编号布局（俯视）：

        [21][20][19][18][17][16][15]
        [22]                   [14]
        [23]                   [13]
        [24]                   [12]
        [25]                   [11]
        [26]                   [10]
        [27][ 0][ 1][ 2][ 3][ 4][ 7][ 8][ 9]

注：[ 0] = 起点（右下角），顺时针排列
角格：[0] 起点, [7] 监狱/探访, [14] 免费停车, [21] 前往监狱
```

### 2.2 格子类型定义

| 类型 ID | 类型名称 | 数量 | 说明 |
|---------|---------|------|------|
| `PROPERTY` | 地产 | 16 | 可购买，收租 |
| `START` | 起点 | 1 | 经过或停留获得奖金 |
| `TAX` | 税务 | 2 | 强制缴纳固定金额 |
| `JAIL_VISIT` | 监狱探访 | 1 | 无事发生 |
| `FREE_PARKING` | 免费停车 | 1 | 无事发生 |
| `GO_TO_JAIL` | 前往监狱 | 1 | 立即移至监狱 |
| `CHANCE` | 机会 | 3 | （Phase 1 留空，不触发事件） |
| `COMMUNITY` | 公共基金 | 3 | （Phase 1 留空，不触发事件） |

### 2.3 棋盘数据表

以下是 28 格的完整数据。Phase 1 中机会/公共基金格子踩上去无事发生。

```
Index | Type         | Name       | Color   | Price | Rent_Base
------|------------- |------------|---------|-------|----------
0     | START        | 起点       | -       | -     | -
1     | PROPERTY     | 地中海街   | Brown   | 60    | 4
2     | COMMUNITY    | 公共基金   | -       | -     | -
3     | PROPERTY     | 波罗的海街 | Brown   | 80    | 8
4     | TAX          | 所得税     | -       | -     | 200 (缴纳)
5     | PROPERTY     | 东方大道   | LightBlue | 100 | 12
6     | CHANCE       | 机会       | -       | -     | -
7     | JAIL_VISIT   | 监狱探访   | -       | -     | -
8     | PROPERTY     | 佛蒙特大道 | LightBlue | 120 | 14
9     | PROPERTY     | 康涅狄格街 | LightBlue | 140 | 16
10    | PROPERTY     | 圣查尔斯   | Pink    | 160   | 20
11    | PROPERTY     | 弗吉尼亚街 | Pink    | 180   | 22
12    | COMMUNITY    | 公共基金   | -       | -     | -
13    | PROPERTY     | 田纳西街   | Pink    | 200   | 24
14    | FREE_PARKING | 免费停车   | -       | -     | -
15    | PROPERTY     | 纽约大道   | Orange  | 220   | 28
16    | CHANCE       | 机会       | -       | -     | -
17    | PROPERTY     | 肯塔基大道 | Orange  | 240   | 30
18    | PROPERTY     | 印第安纳街 | Red     | 260   | 32
19    | PROPERTY     | 伊利诺伊街 | Red     | 280   | 34
20    | TAX          | 奢侈税     | -       | -     | 150 (缴纳)
21    | GO_TO_JAIL   | 前往监狱   | -       | -     | -
22    | PROPERTY     | 太平洋大道 | Green   | 300   | 36
23    | COMMUNITY    | 公共基金   | -       | -     | -
24    | PROPERTY     | 北卡罗来纳 | Green   | 320   | 38
25    | PROPERTY     | 宾夕法尼亚 | Green   | 340   | 40
26    | CHANCE       | 机会       | -       | -     | -
27    | PROPERTY     | 百老汇     | Blue    | 400   | 50
```

### 2.4 颜色组

同一颜色组的所有地产被同一玩家持有时，租金翻倍。

| 颜色组 | 包含格子 Index | 数量 |
|--------|---------------|------|
| Brown | 1, 3 | 2 |
| LightBlue | 5, 8, 9 | 3 |
| Pink | 10, 11, 13 | 3 |
| Orange | 15, 17 | 2 |
| Red | 18, 19 | 2 |
| Green | 22, 24, 25 | 3 |
| Blue | 27 | 1 |

---

## 3. 游戏规则（Phase 1 核心规则）

### 3.1 游戏流程

```
游戏开始
  → 所有玩家放置在起点（Index 0）
  → 每人初始资金 $1500
  → 随机决定先手顺序
  → 进入回合循环

回合循环：
  当前玩家的回合 →
    1. 掷骰子（2颗六面骰）
    2. 移动棋子（前进骰子点数之和的格数）
    3. 判断是否经过/到达起点 → 是则获得 $200
    4. 触发当前格子事件
    5. 判断是否掷出双数（两颗骰子相同）
       → 是：再掷一次（最多连续3次，第3次直接入狱）
       → 否：回合结束，轮到下一个玩家
```

### 3.2 格子事件详细逻辑

#### PROPERTY（地产格）

```
玩家踩到地产格 →
  如果 无人拥有：
    → 弹出购买选项：[购买 $Price] / [放弃]
    → 购买：扣除金额，地产归玩家所有
    → 放弃：无事发生（Phase 1 不做拍卖）
  如果 自己拥有：
    → 无事发生
  如果 其他玩家拥有：
    → 计算租金 → 支付给地主
    → 如果持有该颜色组全部地产：租金 = Rent_Base × 2
    → 如果钱不够支付：玩家破产
```

#### TAX（税务格）

```
玩家踩到税务格 →
  强制扣除固定金额（所得税 $200 / 奢侈税 $150）
  如果钱不够：玩家破产
```

#### GO_TO_JAIL（前往监狱）

```
玩家踩到此格 →
  立即移动到 JAIL_VISIT（Index 7）位置
  标记为"在狱中"状态
  不经过起点，不领 $200
```

#### 监狱规则

```
玩家处于"在狱中"状态时：
  每回合开始可选择：
    1. 支付 $50 保释 → 正常掷骰子移动
    2. 尝试掷双数 → 掷出则免费出狱并移动
    → 连续 3 回合未掷出双数 → 强制支付 $50 出狱
```

#### START（起点）

```
经过或停留在起点 → 获得 $200
```

#### 其他格子（CHANCE / COMMUNITY / FREE_PARKING / JAIL_VISIT）

```
Phase 1：无事发生
```

### 3.3 破产规则

```
当玩家需要支付但资金不足时：
  → 玩家破产
  → 其拥有的所有地产变为无主
  → 该玩家退出游戏
  → 如果剩余玩家 = 1 → 游戏结束，该玩家胜利
```

### 3.4 骰子规则

- 使用 2 颗六面骰子（1-6）
- 点数之和为移动步数（2-12）
- 双数（两颗相同）：当前玩家再掷一次
- 连续掷出 3 次双数：直接入狱

---

## 4. UI 需求（Phase 1 最小 UI）

### 4.1 HUD 信息

常驻显示：
- 当前玩家标识（颜色/名称）
- 所有玩家的资金数额
- 当前回合数

### 4.2 弹出式 UI

| 触发条件 | UI 内容 | 按钮 |
|----------|---------|------|
| 轮到该玩家 | "你的回合" | [掷骰子] |
| 踩到无主地产 | "购买 {地名}？价格 ${Price}" | [购买] / [放弃] |
| 踩到他人地产 | "支付租金 ${Rent} 给 {玩家}" | [确认] |
| 在监狱中 | "你在监狱中" | [支付$50] / [掷骰子] |
| 玩家破产 | "{玩家} 破产了！" | [确认] |
| 游戏结束 | "{玩家} 获胜！" | [返回主菜单] |

---

# PART B: UE5 实施指南

---

## 5. UE5 项目设置

### 5.1 创建项目

1. 打开 UE5 → 选择 **Games** → **Blank** 模板
2. 选择 **C++** （不是 Blueprint）
3. 项目名称：`MonopolyGame`
4. 创建后，UE5 会自动打开 Visual Studio / Rider

### 5.2 项目结构规划

```
MonopolyGame/
├── Source/MonopolyGame/
│   ├── MonopolyGame.Build.cs
│   ├── Core/                      ← 游戏核心逻辑
│   │   ├── MGameMode.h/.cpp       ← 游戏模式（回合管理）
│   │   ├── MGameState.h/.cpp      ← 游戏全局状态
│   │   ├── MPlayerState.h/.cpp    ← 玩家数据
│   │   └── MPlayerController.h/.cpp ← 玩家输入处理
│   ├── Board/                     ← 棋盘相关
│   │   ├── MBoardManager.h/.cpp   ← 棋盘管理器
│   │   ├── MTile.h/.cpp           ← 格子基类 Actor
│   │   └── MTileData.h/.cpp       ← 格子数据（DataAsset）
│   ├── Gameplay/                  ← 游戏玩法
│   │   ├── MDice.h/.cpp           ← 骰子 Actor
│   │   └── MPlayerPawn.h/.cpp     ← 棋子 Actor
│   └── UI/                        ← UI 相关
│       ├── MGameHUD.h/.cpp        ← HUD 管理
│       └── Widgets/               ← UMG Widget C++ 基类
```

---

## 6. 核心类设计（给 Claude Code 的规格说明）

> **命名约定**：所有类以 `M` 前缀开头（代表 Monopoly），避免与引擎类冲突。

### 6.1 MGameMode（回合管理核心）

```
类名：AMGameMode
父类：AGameModeBase
职责：控制回合流转、游戏阶段状态机

关键属性：
- CurrentPlayerIndex : int32          // 当前玩家索引
- PlayerOrder : TArray<APlayerState*>  // 玩家顺序
- ConsecutiveDoubles : int32           // 连续双数计数
- CurrentPhase : EGamePhase            // 当前游戏阶段

枚举 EGamePhase：
  - WaitingForRoll    // 等待掷骰子
  - Moving            // 棋子移动中
  - TileEvent         // 处理格子事件
  - WaitingForDecision // 等待玩家决策（买/不买）
  - TurnEnd           // 回合结束处理
  - GameOver          // 游戏结束

关键方法：
- StartGame()                    // 初始化游戏
- StartTurn()                    // 开始当前玩家回合
- RequestRollDice()              // 玩家请求掷骰子
- OnDiceRolled(int Die1, int Die2) // 骰子结果回调
- MoveCurrentPlayer(int Steps)   // 移动当前玩家
- OnPlayerLanded(int TileIndex)  // 玩家到达格子
- HandlePropertyTile(int TileIndex) // 处理地产格逻辑
- HandleTaxTile(int TileIndex)   // 处理税务格逻辑
- HandleGoToJail()               // 处理入狱
- ProcessBuyDecision(bool Buy)   // 处理购买决策
- ProcessRentPayment(APlayerState* Payer, APlayerState* Owner, int Amount)
- CheckBankruptcy(APlayerState* Player, int AmountOwed)
- EliminatePlayer(APlayerState* Player) // 淘汰玩家
- EndTurn()                      // 结束回合
- NextPlayer()                   // 切换到下一玩家
- CheckGameOver()                // 检查游戏是否结束
```

### 6.2 MGameState（全局数据）

```
类名：AMGameState
父类：AGameState
职责：存储所有需要同步的游戏数据

关键属性：
- TileOwnership : TArray<int32>       // 每格的所有者 PlayerIndex（-1=无主）
- TileData : TArray<FMTileInfo>       // 格子静态数据
- ActivePlayerCount : int32            // 存活玩家数
- TurnNumber : int32                   // 当前回合数

结构体 FMTileInfo：
  - TileType : EMTileType              // 格子类型枚举
  - Name : FString                     // 格子名称
  - ColorGroup : EMColorGroup          // 颜色组
  - Price : int32                      // 购买价格
  - BaseRent : int32                   // 基础租金

方法：
- InitializeBoard()                    // 用上面的28格数据初始化
- GetTileInfo(int Index) : FMTileInfo
- GetTileOwner(int Index) : int32
- SetTileOwner(int Index, int PlayerIndex)
- DoesPlayerOwnColorGroup(int PlayerIndex, EMColorGroup Group) : bool
- CalculateRent(int TileIndex) : int32
```

### 6.3 MPlayerState（玩家数据）

```
类名：AMPlayerState
父类：APlayerState
职责：单个玩家的所有数据

关键属性：
- Money : int32                        // 当前资金（初始 1500）
- CurrentTileIndex : int32             // 当前所在格子
- OwnedProperties : TArray<int32>     // 拥有的地产索引列表
- bIsInJail : bool                     // 是否在监狱中
- JailTurnsRemaining : int32           // 监狱剩余回合（最多3）
- bIsBankrupt : bool                   // 是否已破产
- PlayerColor : FLinearColor           // 玩家颜色标识

方法：
- AddMoney(int32 Amount)
- DeductMoney(int32 Amount) : bool     // 返回是否够钱
- AddProperty(int32 TileIndex)
- RemoveAllProperties()                // 破产时调用
- CanAfford(int32 Amount) : bool
```

### 6.4 MBoardManager（棋盘管理）

```
类名：AMBoardManager
父类：AActor
职责：管理棋盘的3D表现，提供格子世界坐标

关键属性：
- TileActors : TArray<AMTile*>         // 所有格子Actor的引用
- BoardSize : float                     // 棋盘尺寸参数

方法：
- SpawnBoard()                          // 生成所有格子Actor
- GetTileWorldLocation(int Index) : FVector  // 获取格子的3D坐标
- GetTileActor(int Index) : AMTile*
- HighlightTile(int Index, FLinearColor Color) // 高亮某格
```

### 6.5 MTile（格子 Actor）

```
类名：AMTile
父类：AActor
职责：单个格子的3D表现

组件：
- MeshComponent : UStaticMeshComponent  // 格子模型（Phase 1 用方块）
- TextComponent : UTextRenderComponent  // 显示格子名称（可选）

属性：
- TileIndex : int32                     // 自己的索引
- TileInfo : FMTileInfo                 // 格子数据引用

方法：
- SetOwnerColor(FLinearColor Color)     // 设置拥有者颜色（改变材质）
- SetHighlight(bool bHighlight)
```

### 6.6 MPlayerPawn（棋子）

```
类名：AMPlayerPawn
父类：APawn
职责：棋盘上代表玩家的棋子

组件：
- MeshComponent : UStaticMeshComponent  // 棋子模型（Phase 1 用圆柱/锥体）

属性：
- OwnerPlayerIndex : int32

方法：
- MoveToTile(FVector TargetLocation, int Steps)  // 动画移动到目标格
  → 逐格移动，每格之间有短暂停顿，产生"走棋"的视觉效果
- OnMoveComplete()                                // 移动完成回调
```

### 6.7 MDice（骰子）

```
类名：AMDice
父类：AActor
职责：骰子的3D表现和结果生成

组件：
- MeshComponent : UStaticMeshComponent  // 骰子模型

方法：
- RollDice() : FDiceResult              // 随机生成结果 + 播放动画
  → FDiceResult { int Die1, int Die2, bool bIsDouble }
- PlayRollAnimation()                   // 掷骰子动画
- OnRollComplete()                      // 动画完成回调
```

---

## 7. 游戏状态机流程（Claude Code 实现参考）

```
                    ┌──────────────┐
                    │  StartGame   │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
              ┌────►│  StartTurn   │
              │     └──────┬───────┘
              │            ▼
              │     ┌──────────────────┐
              │     │ WaitingForRoll   │ ← 显示"掷骰子"按钮
              │     └──────┬───────────┘
              │            ▼
              │     ┌──────────────┐
              │     │  DiceRolled  │ ← 播放骰子动画
              │     └──────┬───────┘
              │            ▼
              │     ┌──────────────┐
              │     │   Moving     │ ← 棋子逐格移动动画
              │     └──────┬───────┘
              │            ▼
              │     ┌──────────────┐
              │     │  TileEvent   │ ← 根据格子类型分发
              │     └──────┬───────┘
              │            ▼
              │     ┌──────────────────────┐
              │     │ WaitingForDecision?  │ ← 如果需要玩家选择
              │     └──────┬───────────────┘
              │            ▼
              │     ┌──────────────┐
              │     │  TurnEnd     │
              │     └──────┬───────┘
              │            ▼
              │       是否双数？──是──►（回到 WaitingForRoll）
              │            │否
              │            ▼
              │     ┌──────────────┐
              │     │ NextPlayer   │
              │     └──────┬───────┘
              │            │
              └────────────┘
```

---

## 8. Phase 2：在线多人扩展说明

### 8.1 UE5 网络架构要点

- UE5 使用 **Server-Authoritative** 模型：服务器是权威，客户端发送请求
- `GameMode` 只存在于服务器端
- `GameState` 和 `PlayerState` 会自动同步到所有客户端
- 需要标记属性为 `UPROPERTY(Replicated)` 才能同步

### 8.2 Phase 1 → Phase 2 改造清单

| Phase 1 现状 | Phase 2 改造 |
|-------------|-------------|
| 本地直接调用 GameMode 方法 | 改为 Server RPC（`UFUNCTION(Server, Reliable)`）|
| 玩家状态本地修改 | 属性标记 `Replicated` + `OnRep` 回调 |
| UI 直接读取 GameState | 通过 `OnRep` 回调更新 UI |
| 无需 Session | 添加 Session 管理（创建/加入房间）|

### 8.3 关键网络函数模式

```cpp
// 客户端 → 服务器：玩家请求掷骰子
UFUNCTION(Server, Reliable)
void ServerRequestRollDice();

// 服务器 → 所有客户端：广播骰子结果
UFUNCTION(NetMulticast, Reliable)
void MulticastOnDiceRolled(int32 Die1, int32 Die2);

// 属性同步
UPROPERTY(ReplicatedUsing = OnRep_Money)
int32 Money;

UFUNCTION()
void OnRep_Money(); // 客户端收到同步后更新UI
```

---

## 9. UE5 编辑器操作步骤（Phase 1）

> 以下是你需要在 UE5 编辑器中手动完成的操作，按顺序执行。

### 步骤 1：创建 C++ 类

在 UE5 编辑器中：
1. 顶部菜单 → **Tools** → **New C++ Class**
2. 按以下顺序创建（每次选择正确的父类）：

| 类名 | 父类 | 说明 |
|------|------|------|
| MGameMode | GameModeBase | 第一个创建 |
| MGameState | GameState | |
| MPlayerState | PlayerState | |
| MPlayerController | PlayerController | |
| MBoardManager | Actor | |
| MTile | Actor | |
| MPlayerPawn | Pawn | |
| MDice | Actor | |

每次创建后 UE5 会自动编译。如果提示 Hot Reload 失败，关闭编辑器重新用 IDE 编译。

### 步骤 2：配置 GameMode

1. 在 Content Browser 中右键 → **Blueprint Class** → 选择 **MGameMode** 作为父类
2. 命名为 `BP_MGameMode`
3. 双击打开 → 在 **Details** 面板中设置：
   - Default Pawn Class = `MPlayerPawn`（或之后创建的 BP）
   - Player Controller Class = `MPlayerController`
   - Game State Class = `MGameState`
   - Player State Class = `MPlayerState`

### 步骤 3：配置关卡

1. 创建新关卡：**File** → **New Level** → **Empty Level**
2. 保存为 `BoardLevel`
3. 在 **World Settings**（右侧面板）中：
   - GameMode Override = `BP_MGameMode`
4. 添加光源：在关卡中放置一个 **Directional Light** + **Sky Light**
5. 添加摄像机：放置一个 **Camera Actor**，设置为俯视角
   - 位置大约：X=0, Y=0, Z=2000
   - 旋转：Pitch=-90（正下方看）或 Pitch=-60（略带角度）

### 步骤 4：棋盘搭建

**方案 A（推荐，代码生成）**：
- `MBoardManager::SpawnBoard()` 在 BeginPlay 时自动生成 28 个 `MTile` Actor
- 你只需在关卡中放置一个 `MBoardManager` Actor
- 格子位置由代码计算

**方案 B（手动摆放）**：
- 手动在关卡中拖入 28 个 `MTile` Actor 并排列成方形
- 不推荐，太繁琐

### 步骤 5：创建基础材质

1. Content Browser → 右键 → **Material** → 创建 `M_TileBase`
2. 双击打开材质编辑器 → 添加一个 **Vector Parameter** 命名为 `TileColor`
3. 连接到 Base Color
4. 保存 → 右键该材质 → **Create Material Instance** → 命名为 `MI_TileDefault`
5. 为每个颜色组各创建一个 Material Instance（可选，Phase 1 先用同一个也行）

### 步骤 6：创建 UI Widget

1. Content Browser → 右键 → **User Interface** → **Widget Blueprint**
2. 创建以下 Widget：
   - `WBP_GameHUD`：常驻 HUD（玩家资金、回合信息）
   - `WBP_DicePopup`：掷骰子按钮
   - `WBP_BuyPopup`：购买决策弹窗
   - `WBP_InfoPopup`：通用信息弹窗（租金、税务、破产等）
3. 在 Widget Blueprint 编辑器中用拖拽方式搭建 UI 布局
4. 绑定到 C++ 的 UFUNCTION 进行交互

---

## 10. Claude Code 任务分解

> 将以下任务按顺序交给 Claude Code 执行。每个任务是一个独立的工作单元。

### Task 1：项目基础 + 数据定义
```
请在 UE5 项目 MonopolyGame 中创建以下内容：
1. 枚举 EMTileType（包含：Start, Property, Tax, JailVisit, FreeParking, GoToJail, Chance, Community）
2. 枚举 EMColorGroup（包含：None, Brown, LightBlue, Pink, Orange, Red, Green, Blue）
3. 结构体 FMTileInfo（TileType, Name, ColorGroup, Price, BaseRent）
4. 在 MGameState 中用 TArray<FMTileInfo> 初始化 28 格棋盘数据（参照 GDD 2.3 节数据表）
```

### Task 2：GameMode 回合系统
```
在 AMGameMode 中实现：
1. 游戏状态机（EGamePhase 枚举和状态转换）
2. StartGame()：初始化玩家顺序，设置初始资金 1500
3. StartTurn() / EndTurn() / NextPlayer()：回合流转
4. RequestRollDice()：掷骰子逻辑（随机 1-6 两颗）
5. 双数判定：连续双数计数，第 3 次入狱
```

### Task 3：移动和过起点
```
在 AMGameMode 中实现：
1. MoveCurrentPlayer(Steps)：计算新位置（环形 % 28）
2. 经过起点判定：如果新位置 < 旧位置，说明绕了一圈，加 $200
3. 通知 MPlayerPawn 执行移动动画（逐格移动）
4. 移动完成后调用 OnPlayerLanded(TileIndex)
```

### Task 4：格子事件系统
```
实现 OnPlayerLanded 的分发逻辑：
1. Property 格：无主→弹出购买UI / 他人拥有→计算租金并扣款
2. Tax 格：强制扣款
3. GoToJail 格：移动到监狱位置，设置 bIsInJail
4. 监狱逻辑：每回合选择付 $50 或掷双数
5. 租金计算：基础租金，持有全色组则翻倍
6. 破产判定：钱不够时淘汰玩家
```

### Task 5：棋盘 3D 生成
```
实现 AMBoardManager：
1. SpawnBoard()：在 BeginPlay 时生成 28 个 AMTile Actor
2. 计算每个格子的世界坐标（正方形排列，每边 7 格）
3. 每个 AMTile 使用基础方块 Mesh + 动态材质实例显示颜色
4. GetTileWorldLocation(Index)：返回指定格子坐标
```

### Task 6：棋子和骰子
```
实现：
1. AMPlayerPawn：棋子 Actor，带移动动画（Timeline 或 Lerp）
   - MoveToTile()：逐格移动，每格停顿 0.2s
2. AMDice：骰子 Actor
   - RollDice()：随机生成结果 + 简单旋转动画
```

### Task 7：基础 UI
```
创建 UMG Widget 的 C++ 基类：
1. UMGameHUDWidget：显示所有玩家资金、当前回合
2. UMPopupWidget：通用弹窗基类
3. 在 MPlayerController 中管理 Widget 的显示/隐藏
4. 绑定按钮事件到 GameMode 的对应方法
```

---

## 11. 关键 UE5 概念速查

| 概念 | 作用 | 大富翁中的对应 |
|------|------|-------------|
| GameMode | 游戏规则，只在服务器 | 回合管理、规则判定 |
| GameState | 所有人可见的全局数据 | 棋盘所有权、回合数 |
| PlayerState | 单个玩家的同步数据 | 资金、拥有地产、位置 |
| PlayerController | 处理玩家输入 | 点击"掷骰子"、"购买" |
| Pawn | 世界中代表玩家的实体 | 棋子 |
| Actor | 世界中的任何物体 | 格子、骰子、棋盘 |
| UMG Widget | UI 元素 | HUD、弹窗 |
| BeginPlay() | Actor 生成后自动调用 | 初始化棋盘、开始游戏 |
| Tick() | 每帧调用 | 一般不用，用 Timer 代替 |

---

## 12. 已知风险和注意事项

1. **Hot Reload 不可靠**：修改 C++ 后建议关闭编辑器重新编译，不要依赖 Live Coding
2. **UE5 编译慢**：首次编译可能需要 5-10 分钟，后续增量编译较快
3. **蓝图 vs C++**：UI 交互部分（按钮点击事件）可能用蓝图更方便，C++ 提供基类，蓝图做绑定
4. **Phase 2 网络**：GameMode 里的逻辑不需要大改，但所有客户端交互都需要走 RPC
5. **资源管理**：Phase 1 用 UE5 自带的基础形状（Cube, Cylinder），不需要外部美术资源
