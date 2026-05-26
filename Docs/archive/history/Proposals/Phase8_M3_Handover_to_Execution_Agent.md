# Phase 8 M3 交接文档：MonopolyGame 垂直切片执行

> 本文档由 Compiler Agent 编写，交接给 Execution Agent 执行 M3 任务。
> 日期：2026-04-04

---

## 1. 已完成的工作

### 1.1 总览

Phase 8 的目标是将 AgentBridge 从 Python 脚本驱动重构为 AI Agent 驱动的 Skill-First Compiler 框架，以 MonopolyGame（Phase 1 本地多人）作为唯一垂直切片测试案例。

我已完成 **DD-1 → M1 → DD-2 → M2 → Main Chain → DD-3**，即：
- 详细设计（Schema 定义、Compiler 接口、Skill Template、MCP 工具、C++ 类设计）
- Compiler 主链全 5 阶段 + Handoff 组装的样本数据生成
- **Reviewed Handoff v2 已输出，审查状态 approved_with_warnings，可进入执行阶段**

### 1.2 里程碑完成状态

| 里程碑 | 状态 | 说明 |
|--------|------|------|
| DD-1: Schema + Compiler 接口规约 | ✅ 已完成 | 6 个 Schema 完整字段定义 |
| M1: Compiler Contracts Reset | ✅ 已完成 | 6 个 Schema JSON 文件 + 5 段 Python 骨架 |
| DD-2: Skill Template + MCP 详细设计 | ✅ 已完成 | 6 套 Template Pack (36 文件) + MCP Server (6 文件) |
| M2: Main Chain 数据生成 | ✅ 已完成 | 11 个 JSON 产物（见下文） |
| DD-3: Lowering 映射表 + C++ 类详细设计 | ✅ 已完成 | 14 Build Steps → C++ 类映射、11 对文件清单、6 批次实施计划 |
| **M3: MonopolyGame 垂直切片执行** | ⬜ **待执行** | **你的任务** |
| M4: 兼容性清理 + 最终验收 | ⬜ 待执行 | M3 之后 |

---

## 2. 你的任务：M3 MonopolyGame 垂直切片执行

> **权威任务入口：`task.md` 中的 TASK 06**
> 本章为概要说明，详细的逐步操作、验证命令、验收标准以 `task.md` TASK 06 为准。

### 2.1 目标

根据 Reviewed Handoff v2 中的 Build IR（14 个构建步骤），在 UE5.5.4 项目中实际编写 C++ 代码、生成 Actor、创建 Widget，使 MonopolyGame Phase 1 可运行。

### 2.2 具体交付物

1. **11 对 C++ 文件**（.h + .cpp），位于 `Source/Mvpv4TestCodex/`
2. **场景级别** `L_MonopolyBoard`，包含 28 个 Tile Actor + 4 个 PlayerPawn + BoardManager + Dice
3. **5 个 Widget Blueprint**（WBP_GameHUD, WBP_DicePopup, WBP_BuyPopup, WBP_InfoPopup, WBP_JailPopup）
4. **12 个验证检查点全部通过**

### 2.3 建议实施顺序（6 个 Batch）

| 批次 | Build Steps | 内容 | 前置条件 |
|------|-------------|------|----------|
| Batch 1 | step-05, step-03(types) | GameMode/State/PlayerState 壳 + 枚举/结构体 | 无 |
| Batch 2 | step-01, 02, 04 | 棋盘布局 + 格子 + 棋子 Actor | Batch 1 编译通过 |
| Batch 3 | step-06, 07 | 回合 FSM + 骰子逻辑 | Batch 1 |
| Batch 4 | step-08, 09, 10, 11 | 事件分发 + 经济 + 监狱 + 破产 | Batch 1, 3 |
| Batch 5 | step-12, 13 | UI Widget + 事件绑定 | Batch 1, 3 |
| Batch 6 | step-14 | 自动化验证测试 | 全部 |

---

## 3. 必读文档索引

按**阅读优先级**排列：

### 3.1 最高优先级 — 直接指导执行

| 文档 | 路径 | 内容 | 用途 |
|------|------|------|------|
| **C++ 类详细设计** | `Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md` | 11 个 C++ 类的属性、方法签名、枚举定义、依赖图、Batch 顺序 | **编码的主要依据** |
| **Build IR** | `ProjectState/phase8/build_ir.json` | 14 个 build_steps 的完整参数、execution_hints、12 个 validation_ir | **每个步骤的具体参数** |
| **Reviewed Handoff v2** | `ProjectState/phase8/reviewed_handoff_v2.json` | Compiler→Execution 的正式交接物，包含审查摘要、能力缺口、批准状态 | **整体交接入口** |

### 3.2 高优先级 — 理解游戏规则和数据

| 文档 | 路径 | 内容 | 用途 |
|------|------|------|------|
| **GDD 原文** | `ProjectInputs/GDD/GDD_MonopolyGame.md` | 完整游戏设计文档（Part A 设计 + Part B UE5 实现） | 游戏规则权威来源 |
| **Cross-Review Report** | `ProjectState/phase8/cross_review_report.json` | 13 项审查 + reviewed_dynamic_spec_tree | 理解规则间如何互锁 |
| **6 个 Skill Fragments** | `ProjectState/phase8/skill_fragments/skill-*.json` | 每个游戏子系统的完整规则定义 | 详细规则参考 |

各 Fragment 内容：
- `skill-board.json` — 28 格棋盘拓扑（索引、边、角）
- `skill-tile-event.json` — 格子类型、28 行数据表、7 颜色组、事件分发
- `skill-turn.json` — 10 状态 / 12 转换的回合 FSM、2d6 骰子、移动、过起点
- `skill-economy.json` — 购买、租金（颜色组 2x）、税、5 种资金流
- `skill-jail.json` — 入狱条件、保释 / 掷双数、强制保释、破产触发
- `skill-ui.json` — HUD 4 元素、7 种弹窗、5 个 WBP、事件绑定

### 3.3 中优先级 — 理解整体架构

| 文档 | 路径 | 内容 | 用途 |
|------|------|------|------|
| **Phase 8 统一方案** | `Docs/History/Proposals/Phase8_Plan_Original.md` | 概要设计，19 个章节，M1-M4 里程碑定义 | 理解全局目标和禁止事项 |
| **Schema 接口规约** | `Docs/History/Proposals/Phase8_DD1_Schema_and_Interface_Spec.md` | 6 个 Schema 的字段级定义 + Compiler 5 段接口 | 理解数据流 |
| **GDD Projection** | `ProjectState/phase8/gdd_projection.json` | Intake 阶段对 GDD 的结构化提取 | 理解 Phase 1 范围边界 |
| **Planner Output** | `ProjectState/phase8/planner_output.json` | 6 个 Skill Instance 的选择和依赖图 | 理解编译路由 |

### 3.4 参考级 — 按需查阅

| 文档 | 路径 | 内容 |
|------|------|------|
| 项目总规则 | `CLAUDE.md` | 不可修改的文件清单、代码风格、常用命令 |
| Agent 规则 | `AGENTS.md` | 项目级 Agent 行为约束 |
| 插件说明 | `Plugins/AgentBridge/README.md` | AgentBridge 插件概述 |
| MCP 工具定义 | `Plugins/AgentBridge/MCP/tool_definitions.py` | 28 个 MCP 工具的参数和返回值 |
| MCP Server | `Plugins/AgentBridge/MCP/server.py` | MCP 入口，如需通过 MCP 执行操作 |
| 6 套 Skill Template | `Plugins/AgentBridge/SkillTemplates/genre_packs/boardgame/monopoly_like/*/` | 每套 6 个文件（manifest/prompt/schema/evaluator） |
| 6 个 Schema | `Plugins/AgentBridge/Schemas/{gdd_projection,planner_output,skill_fragment,cross_review_report,build_ir,reviewed_handoff_v2}.schema.json` | JSON Schema 定义 |
| Compiler Python 骨架 | `Plugins/AgentBridge/Compiler/*/` | 5 段 Compiler 的 Python 骨架代码 |

---

## 4. 关键约束和注意事项

### 4.1 绝对不要修改的文件

参见 `CLAUDE.md` 的"绝对不要修改的文件"章节。核心要点：
- **不改 Plugins/AgentBridge/Source/ 下的任何 C++**
- **不改 Plugins/AgentBridge/Scripts/ 下的 bridge/orchestrator Python**
- **不改 Plugins/AgentBridge/AgentBridgeTests/**
- **不改 Plugins/AgentBridge/Schemas/common/ 和 feedback/ 和 write_feedback/**

### 4.2 新代码写在哪里

所有新增 C++ 代码位于**项目层**：
```
Source/Mvpv4TestCodex/Public/   ← 头文件
Source/Mvpv4TestCodex/Private/  ← 实现文件
```

**不要在 Plugins/AgentBridge/ 下创建游戏 C++ 代码。**

### 4.3 命名规范

- C++ 类前缀：`AM`（Actor）、`UM`（UObject/Widget）、`FM`（Struct）、`EM`（Enum）
- Widget Blueprint 前缀：`WBP_`
- 中文注释
- 所有 UPROPERTY/UFUNCTION 需要正确的反射宏

### 4.4 已知能力缺口（不阻塞执行）

| gap_id | 严重度 | 说明 | 处理方式 |
|--------|--------|------|----------|
| ~~gap-umg-auto-layout~~ | ~~degraded~~ | ~~UMG Widget 布局无法自动生成~~ | **已解决**：全部纯 C++ 构建布局，见本文档第 7 章 UMG Widget 布局方案 |
| gap-dice-animation | cosmetic | 骰子/棋子动画需 Timeline | 生成占位函数 `PlayDiceAnimation()` / `PlayPawnMoveAnimation()` |
| gap-animation-asset | cosmetic | 3D 模型/材质资产 | Phase 1 使用基础几何体（Box/Cylinder） |

### 4.5 关键设计决策（已在 DD-3 中确定）

- FSM 实现：手动 switch on EMTurnState（不用 State Tree）
- 数据存储：C++ InitializeTileData() 硬编码 28 格（不用 DataTable Asset）
- UI 架构：UMPopupWidget 基类 + WBP 参数化（不做每种弹窗独立 C++ 类）
- 资金不足：立即破产（Phase 1 无抵押/交易）
- Blue 组（1 个地产）：自动满足颜色组完整条件

### 4.6 验收标准

M3 完成标准（12 个验证点全部通过）：
1. 场景中 28 个 AMTile Actor
2. TileDataArray 28 行，16 个 PROPERTY 有 Price > 0
3. 2-4 个 AMPlayerPawn
4. GameMode + GameState 正确实例化
5. 初始状态 WaitForRoll
6. 骰子结果 [2, 12]，双数检测正确
7. 8 种格子事件正确分发
8. 购买扣款 + 颜色组租金翻倍
9. 监狱全路径（入狱 / 保释 / 掷双数 / 强制保释）
10. 破产释放地产 + 游戏结束
11. 5 个 Widget Blueprint 存在
12. 10 个事件委托已绑定

---

## 5. 数据流全景图

```
GDD_MonopolyGame.md
  │
  ▼ [Stage 1: Intake]
gdd_projection.json
  │
  ▼ [Stage 2: Planner]
planner_output.json
  │
  ▼ [Stage 3: Skill Runtime]
skill_fragments/skill-{board,tile-event,turn,economy,jail,ui}.json  (×6)
  │
  ▼ [Stage 4: Cross-Review]
cross_review_report.json  (reviewed_dynamic_spec_tree 在此合并)
  │
  ▼ [Stage 5: Lowering]
build_ir.json  (14 build_steps + 12 validation_ir)
  │
  ▼ [Handoff Assembly]
reviewed_handoff_v2.json  ← Compiler 产出的终点、Execution 的起点
  │
  ▼ [M3: 你的任务 — 按 build_steps 执行]
Source/Mvpv4TestCodex/ 下的 C++ 代码 + UE5 场景 + Widget
```

---

## 7. UMG Widget 布局方案（Batch 5 执行指南）

> 全部纯 C++ 构建，在 `NativeConstruct()` 中用 `WidgetTree->ConstructWidget<>()` 构建控件树，不依赖蓝图编辑器手动排版。

### 7.1 公共视觉规范

| 参数 | 值 |
|------|-----|
| 弹窗背景色 | `(0, 0, 0, 0.8)` RGBA |
| HUD 背景色 | `(0, 0, 0, 0.6)` RGBA |
| 标题字号 | 24 |
| 正文字号 | 16 |
| 辅助文字字号 | 14 |
| 文字颜色-默认 | 白色 `(1,1,1,1)` |
| 文字颜色-金额 | 绿色 `(0.2,0.9,0.3,1)` |
| 文字颜色-警告 | 黄色 `(1,0.9,0.2,1)` |
| 文字颜色-危险 | 红色 `(1,0.3,0.2,1)` |
| 文字颜色-灰色 | `(0.6,0.6,0.6,1)` |
| Primary 按钮色 | 蓝色 `(0.2,0.4,0.8,1)` |
| Secondary 按钮色 | 灰色 `(0.3,0.3,0.3,1)` |
| 按钮文字 | 白色, 字号 16 |
| 按钮标准尺寸 | 高 44px，宽按内容自适应（最小 160px）|
| 玩家颜色 | 红/蓝/绿/黄 四色 |
| 参考分辨率 | 1920×1080，使用 DPI Scale + Anchor 适配 |

### 7.2 WBP_GameHUD（常驻 HUD）

```
屏幕位置：左上角
Anchor: (0, 0)  Alignment: (0, 0)
Offset: (20, 20)
尺寸: 320 × 自适应高度

┌─────────────────────────┐
│ ● 玩家1 的回合    回合 5 │  ← 顶行：玩家颜色圆点 + 名称 + 回合数
├─────────────────────────┤
│ 当前位置：东方大道 [地产] │  ← 当前格子信息
├─────────────────────────┤
│ 💰 玩家资金               │
│  ● 玩家1    $1,200       │  ← 颜色圆点 + 名字 + 资金
│  ● 玩家2    $980         │
│  ● 玩家3    $1,500       │
│  ● 玩家4    [破产]       │  ← 破产玩家灰色显示
└─────────────────────────┘
```

**控件树**:
```
CanvasPanel (Root)
 └─ VerticalBox [Anchor:TopLeft, Padding:(20,20,0,0)]
     ├─ HorizontalBox                          // 顶行
     │   ├─ Image (12×12, 圆形, PlayerColor)   // 颜色标识
     │   ├─ TextBlock "{PlayerName} 的回合"     // 字号 18, 白色
     │   └─ TextBlock "回合 {N}"               // 字号 14, 右对齐, 灰色
     ├─ TextBlock "当前位置：{TileName} [{Type}]" // 字号 14, 浅灰
     ├─ Spacer (8px)
     ├─ TextBlock "玩家资金"                    // 字号 14, 黄色
     └─ VerticalBox                            // 玩家列表（动态生成 2-4 行）
         └─ [每行] HorizontalBox
              ├─ Image (10×10, 圆形, Color)
              ├─ TextBlock "{Name}"            // 字号 14, 白色
              └─ TextBlock "${Money}"          // 字号 14, 右对齐, 绿色
                                               // 破产时整行灰色 + "[破产]"
```

背景: SlateBrush 黑色半透明 `(0,0,0,0.6)`

### 7.3 WBP_DicePopup（掷骰弹窗）

```
屏幕位置：正中央
Anchor: (0.5, 0.5)  Alignment: (0.5, 0.5)
尺寸: 400 × 280

┌──────────────────────────────┐
│         掷骰子                │  ← 标题，字号 24, 白色, 居中
│                              │
│     玩家1 的回合              │  ← 副标题，字号 16, 浅灰, 居中
│                              │
│        ⚂  +  ⚄  =  9        │  ← 骰子结果区（掷骰后显示）
│       [双数！再来一次]        │  ← 双数提示（条件显示, 黄色）
│                              │
│      ┌──────────────┐        │
│      │   掷骰子      │        │  ← Primary 按钮
│      └──────────────┘        │
└──────────────────────────────┘
```

**控件树**:
```
CanvasPanel (Root)
 └─ SizeBox [400×280]
     └─ Border [背景: (0,0,0,0.8)]
         └─ VerticalBox [HAlign:Center, Padding:24]
             ├─ TextBlock "掷骰子"             // 标题, 24, 白色, Center
             ├─ Spacer (12px)
             ├─ TextBlock "{player_name} 的回合" // 16, 浅灰, Center
             ├─ Spacer (20px)
             ├─ HorizontalBox [HAlign:Center]   // 骰子结果（初始隐藏）
             │   ├─ TextBlock "{die1}"          // 36, 白色
             │   ├─ TextBlock " + "             // 24
             │   ├─ TextBlock "{die2}"          // 36, 白色
             │   ├─ TextBlock " = "             // 24
             │   └─ TextBlock "{total}"         // 36, 黄色
             ├─ TextBlock "双数！再来一次"       // 14, 黄色, 条件可见
             ├─ Spacer (16px)
             └─ Button "掷骰子"                 // 240×48, 蓝色, 白字 18
```

**两阶段交互**：
1. 显示时：只有"掷骰子"按钮，骰子结果区隐藏
2. 点击后：按钮禁用，播放短暂延迟（0.5s），显示骰子结果，按钮文字变为"继续"

### 7.4 WBP_BuyPopup（购买决策弹窗）

```
屏幕位置：正中央
Anchor: (0.5, 0.5)  Alignment: (0.5, 0.5)
尺寸: 420 × 320

┌──────────────────────────────────┐
│          购买地产                  │  ← 标题, 字号 24
│                                  │
│   是否购买 东方大道？              │  ← 地产名, 字号 18
│                                  │
│   价格：      $100               │  ← 信息行, 左标签灰色, 右值白色
│   基础租金：  $12                │
│   颜色组：    LightBlue ■        │  ← 颜色块 Image(16×16, GroupColor)
│                                  │
│   当前资金：  $1,200             │  ← 绿色
│                                  │
│   ┌──────────┐  ┌──────────┐    │
│   │   购买    │  │   放弃    │    │  ← Primary蓝 + Secondary灰
│   └──────────┘  └──────────┘    │
└──────────────────────────────────┘
```

**控件树**:
```
CanvasPanel (Root)
 └─ SizeBox [420×320]
     └─ Border [背景: (0,0,0,0.8)]
         └─ VerticalBox [HAlign:Center, Padding:24]
             ├─ TextBlock "购买地产"               // 24, 白色, Center
             ├─ Spacer (12px)
             ├─ TextBlock "是否购买 {tile_name}？"  // 18, 白色, Center
             ├─ Spacer (16px)
             ├─ VerticalBox                        // 信息区
             │   ├─ HorizontalBox: "价格：" (灰) | "${price}" (白)
             │   ├─ HorizontalBox: "基础租金：" (灰) | "${base_rent}" (白)
             │   └─ HorizontalBox: "颜色组：" (灰) | "{group}" (白) | Image(16×16, Color)
             ├─ Spacer (12px)
             ├─ TextBlock "当前资金：${player_money}" // 16, 绿色
             ├─ Spacer (20px)
             └─ HorizontalBox [HAlign:Center, Spacing:16]
                 ├─ Button "购买"                    // 160×44, 蓝色, 白字 16
                 └─ Button "放弃"                    // 160×44, 灰色, 白字 16
```

### 7.5 WBP_InfoPopup（通用信息弹窗）

复用于：支付租金、缴税、破产通知、游戏结束

```
屏幕位置：正中央
Anchor: (0.5, 0.5)  Alignment: (0.5, 0.5)
尺寸: 400 × 自适应（最小 200，最大 300）

┌──────────────────────────────┐
│          支付租金              │  ← 标题, 字号 24（由调用方传入）
│                              │
│  你落在了 玩家2 的            │  ← 正文, 字号 16, 居中, 自动换行
│  东方大道 上                  │
│  需支付租金：$24              │
│  [颜色组加成！租金翻倍]       │  ← 条件显示，黄色，字号 14
│                              │
│      ┌──────────────┐        │
│      │     确认      │        │  ← Primary 按钮
│      └──────────────┘        │
└──────────────────────────────┘
```

**控件树**:
```
CanvasPanel (Root)
 └─ SizeBox [400, MinHeight:200, MaxHeight:300]
     └─ Border [背景: (0,0,0,0.8)]
         └─ VerticalBox [HAlign:Center, Padding:24]
             ├─ TextBlock Title                 // 24, 白色, Center
             ├─ Spacer (16px)
             ├─ TextBlock Body                  // 16, 浅灰, Center, AutoWrap
             ├─ TextBlock BonusHint             // 14, 黄色, 默认隐藏
             ├─ Spacer (20px)
             └─ Button "确认"                   // 200×44, 蓝色, 白字 16
```

**各场景参数化**:
- 租金: Title="支付租金", Body="{rent_info}", BonusHint=条件显示
- 税务: Title="缴税", Body="{tax_info}", BonusHint=隐藏
- 破产: Title="破产", Body="{bankruptcy_info}", BonusHint=隐藏
- 游戏结束: Title="游戏结束", Body="{winner_info}", Button文字="再来一局"

### 7.6 WBP_JailPopup（监狱决策弹窗）

```
屏幕位置：正中央
Anchor: (0.5, 0.5)  Alignment: (0.5, 0.5)
尺寸: 420 × 300

┌──────────────────────────────────┐
│           监狱决策                 │  ← 标题, 字号 24
│                                  │
│   你在监狱中（剩余 2 回合）       │  ← 状态, 字号 16
│   当前资金：$800                 │  ← 绿色
│                                  │
│  ⚠ 第三回合：必须支付 $50 保释金  │  ← 条件显示（remaining==1时）, 红色
│                                  │
│   ┌────────────────┐             │
│   │  支付 $50 保释  │             │  ← Primary蓝（资金不足时禁用灰色）
│   └────────────────┘             │
│   ┌────────────────┐             │
│   │ 尝试掷双数出狱  │             │  ← Secondary灰
│   └────────────────┘             │
└──────────────────────────────────┘
```

**控件树**:
```
CanvasPanel (Root)
 └─ SizeBox [420×300]
     └─ Border [背景: (0,0,0,0.8)]
         └─ VerticalBox [HAlign:Center, Padding:24]
             ├─ TextBlock "监狱决策"                    // 24, 白色, Center
             ├─ Spacer (12px)
             ├─ TextBlock "你在监狱中（剩余 {N} 回合）"  // 16, 浅灰, Center
             ├─ TextBlock "当前资金：${money}"           // 16, 绿色, Center
             ├─ Spacer (8px)
             ├─ TextBlock "⚠ 第三回合..."               // 14, 红色, 条件可见(remaining==1)
             ├─ Spacer (16px)
             ├─ Button "支付 $50 保释"                   // 280×44, 蓝色
             │   // money < 50 时: bIsEnabled=false, 灰色, 提示"资金不足"
             ├─ Spacer (8px)
             └─ Button "尝试掷双数出狱"                   // 280×44, 灰色
                // forced_bail (remaining==1 失败后): 隐藏两按钮, 自动执行强制保释
```

### 7.7 C++ 生成方式示例

全部在 `NativeConstruct()` 中构建控件树：

```cpp
void UMGameHUDWidget::NativeConstruct()
{
    Super::NativeConstruct();

    // Root
    UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>();
    WidgetTree->RootWidget = Root;

    // 背景
    UBorder* Bg = WidgetTree->ConstructWidget<UBorder>();
    Bg->SetBrushColor(FLinearColor(0, 0, 0, 0.6f));
    UCanvasPanelSlot* BgSlot = Root->AddChildToCanvas(Bg);
    BgSlot->SetAnchors(FAnchors(0, 0));
    BgSlot->SetOffsets(FMargin(20, 20, 320, 0));

    // ... 依次构建 VerticalBox、TextBlock、Button 等
}
```

弹窗基类 `UMPopupWidget` 提供 `ShowPopup(Title, Body, Buttons)` 方法，各弹窗 WBP 通过参数化区分，无需独立 C++ 子类。

---

## 8. 快速启动清单

1. 读 `Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md` — 这是你的执行蓝图
2. 读 `ProjectState/phase8/build_ir.json` — 14 个步骤的具体参数
3. 读 `ProjectState/phase8/reviewed_handoff_v2.json` — 确认审批状态和能力缺口
4. 从 Batch 1 开始：先写 `MMonopolyTypes.h` + GameMode/State/PlayerState 壳
5. 每完成一个 Batch 确保编译通过后再进入下一个
6. Batch 5 时参照本文档第 7 章 UMG 布局方案，纯 C++ 构建全部 Widget
7. 最后执行 Batch 6 的 12 个验证检查点

祝顺利。
