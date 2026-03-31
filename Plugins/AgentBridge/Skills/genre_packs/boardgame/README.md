# Boardgame Genre Pack

## 当前状态
📦 **最小骨架** - 第一阶段只包含 manifest，无实际 Skill 实现

## 职责

Boardgame Genre Pack 提供棋盘游戏类型的专用编译能力。

### 计划包含的 Skill

#### Required Skills（必需）
1. **board_layout**
   - 生成棋盘布局
   - 支持网格类型：正方形 / 六边形
   - 支持尺寸配置

2. **piece_movement**
   - 定义棋子移动规则
   - 生成移动逻辑

3. **turn_system**
   - 生成回合制逻辑
   - 玩家轮流机制

#### Optional Skills（可选）
1. **auction_system**
   - 拍卖系统（如大富翁）

2. **trading_system**
   - 交易系统

### 计划目录结构

```
boardgame/
├── pack_manifest.yaml          # 类型包清单（已有）
├── README.md                   # 本文件
├── routers/
│   └── boardgame_router.py
├── required_skills/
│   ├── board_layout.py
│   ├── piece_movement.py
│   └── turn_system.py
├── optional_skills/
│   ├── auction_system.py
│   └── trading_system.py
├── review_extensions/
│   └── boardgame_reviewer.py
├── validation_extensions/
│   └── boardgame_validator.py
├── delta_policy/
│   └── boardgame_delta_policy.py
└── templates/
    ├── board_spec_template.yaml
    └── piece_spec_template.yaml
```

## 第一阶段

第一阶段只有：
- ✅ `pack_manifest.yaml`（最小清单）
- ✅ `README.md`（本文件）

其他能力将在后续阶段补充。

## 与 Static Spec Base 的关系

- **Static Spec Base**：定义通用的 Spec 格式（如 scene_spec）
- **Boardgame Pack**：提供 boardgame 特定的生成逻辑

Static Base 是"语法"，Genre Pack 是"语义"。
