# AGENT_UE5 命名与路径规范

## 1. GDD-First 四层命名优先级

所有命名（类名、文件名、资产名、路径名）遵循以下优先级：

| 优先级 | 层级 | 说明 | 示例 |
|--------|------|------|------|
| **Tier 1** | GDD 显式命名 | GDD 中明确给出的名称，原样采用 | GDD 写 `MonopolyBoard` -> 类名 `AMonopolyBoard` |
| **Tier 2** | GDD 风格推导 | GDD 未给出名称，但根据 GDD 用语风格推导 | GDD 用 "property tile" -> `APropertyTile` |
| **Tier 3** | 项目规范 | GDD 无相关线索，使用项目既定命名规范 | 项目规范要求 `A` 前缀 Actor, `U` 前缀 Object |
| **Tier 4** | 默认回退 | 以上都无法确定，使用 UE5 社区惯例 | `ABP_GameMode` -> `AMonopolyGameMode` |

### 1.1 优先级规则

- 高层级覆盖低层级：GDD 显式命名 > GDD 风格 > 项目规范 > 默认
- 同层级冲突时，优先选择更具体的命名
- Tier 1 命名不可被任何下游阶段修改（视为 Constraint）
- Tier 2-4 命名可在 Design Space Discovery 中讨论替代方案

### 1.2 GDD 显式命名的判定

以下情况视为 GDD 显式命名：
- GDD 中使用代码格式（反引号或代码块）给出名称
- GDD 中在"类名"、"文件名"等标题下列出名称
- GDD 中反复使用同一术语指代同一概念

以下情况**不视为** GDD 显式命名：
- GDD 中随意提及的自然语言描述
- GDD 中的示意性伪代码
- GDD 中的概念名（如"回合系统"不等于类名 `TurnSystem`）

---

## 2. UE5 资产路径规范

### 2.1 Content 目录结构

```
Content/
  {ProjectName}/
    Blueprints/
      GameModes/
      Characters/
      UI/
    Maps/
      L_StartScreen.umap
      L_MainMenu.umap
      L_Gameplay.umap
    UI/
      Widgets/
        WBP_MainMenu.uasset
        WBP_HUD.uasset
        WBP_Settings.uasset
        WBP_PauseMenu.uasset
        WBP_Results.uasset
      Textures/
    Materials/
    Audio/
      BGM/
      SFX/
    DataAssets/
```

### 2.2 命名前缀规范

| 资产类型 | 前缀 | 示例 |
|---------|------|------|
| Blueprint Actor | `BP_` | `BP_MonopolyBoard` |
| Widget Blueprint | `WBP_` | `WBP_MainMenu` |
| Material | `M_` | `M_TileBase` |
| Material Instance | `MI_` | `MI_TileProperty` |
| Texture | `T_` | `T_BoardBackground` |
| Level | `L_` | `L_Gameplay` |
| Data Asset | `DA_` | `DA_TileConfig` |
| Sound Cue | `SC_` | `SC_DiceRoll` |
| Sound Wave | `SW_` | `SW_BGM_Main` |

### 2.3 C++ 类命名规范

| 类型 | 前缀 | 示例 |
|------|------|------|
| Actor | `A` | `AMonopolyBoard` |
| UObject | `U` | `UTurnManager` |
| Component | `U` + `Component` 后缀 | `UTileComponent` |
| Interface | `I` | `ITileInteractable` |
| Widget (C++) | `U` | `UMainMenuWidget` |
| GameMode | `A` + `GameMode` 后缀 | `AMonopolyGameMode` |
| GameState | `A` + `GameState` 后缀 | `AMonopolyGameState` |
| PlayerState | `A` + `PlayerState` 后缀 | `AMonopolyPlayerState` |
| PlayerController | `A` + `PlayerController` 后缀 | `AMonopolyPlayerController` |

---

## 3. naming_resolution_log

### 3.1 定义

naming_resolution_log 是 Build IR 中每个步骤的命名审计记录。它追踪每个命名决策是如何做出的，确保可追溯性。

### 3.2 结构

每个 Build IR Action 必须包含 naming_resolution_log：

```json
{
  "ir_action_id": "ir-create-board-actor",
  "action": "create_cpp_class",
  "naming_resolution_log": {
    "class_name": {
      "resolved": "AMonopolyBoard",
      "tier": 1,
      "evidence": "GDD SS2.1 明确写出 'MonopolyBoard' 类名",
      "alternatives_considered": []
    },
    "file_path": {
      "resolved": "Source/Mvpv4TestCodex/Board/MonopolyBoard.h",
      "tier": 3,
      "evidence": "项目规范：按功能域分子目录",
      "alternatives_considered": ["Source/Mvpv4TestCodex/Gameplay/MonopolyBoard.h"]
    },
    "asset_path": {
      "resolved": "/Game/Mvpv4TestCodex/Blueprints/BP_MonopolyBoard",
      "tier": 3,
      "evidence": "项目规范：Blueprint 放在 Blueprints/ 下",
      "alternatives_considered": []
    }
  }
}
```

### 3.3 必填字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `resolved` | string | 最终确定的名称 |
| `tier` | int (1-4) | 决定该名称的优先级层级 |
| `evidence` | string | 做出该命名决策的依据（GDD 引用、规范引用等） |

### 3.4 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `alternatives_considered` | string[] | 考虑过但未采用的替代名称 |
| `gdd_ref` | string | GDD 中的具体位置引用 |
| `provisional` | bool | 是否基于 provisional 值命名 |

### 3.5 mandatory vs inheritable

| 类型 | 说明 | 示例 |
|------|------|------|
| **mandatory** | 每个 IR Action 必须独立记录 | class_name, file_path |
| **inheritable** | 可从父级/模板继承，只需记录覆盖项 | asset_path 前缀从项目规范继承 |

如果一个命名从父级继承且未修改，可以标记 `"inherited_from": "project_convention"` 而不重复记录完整推理。

---

## 4. C++ 为主 + Blueprint 薄层原则

### 4.1 核心规则

- **核心逻辑必须在 C++ 中实现**：游戏规则、状态管理、回合逻辑、经济系统
- **Blueprint 仅作为薄层承载**：资产绑定、视觉布局、简单事件响应
- **Widget Blueprint 允许布局**：UI 布局在 Widget Blueprint 中完成，但交互逻辑回调到 C++

### 4.2 Blueprint 薄层判定标准

| 允许在 Blueprint 中 | 不允许在 Blueprint 中 |
|-------------------|---------------------|
| Widget 布局（按钮位置、文本框位置） | 游戏规则判断逻辑 |
| 资产引用绑定（Mesh、Material、Sound） | 状态机转换逻辑 |
| 简单动画播放触发 | 数据计算和处理 |
| C++ 事件的 UI 响应绑定 | 网络同步逻辑 |
| 关卡中 Actor 的初始摆放 | 存档/读档逻辑 |

### 4.3 检查点

Cross-Domain Convergence Review 中必须检查 Blueprint 薄层原则：
- 每个 Blueprint 的逻辑节点数不应超过 20 个（超过说明需要下沉到 C++）
- Blueprint 中不应包含循环逻辑
- Blueprint 中不应包含条件分支超过 3 层的逻辑
- 如发现违反，在 cross_review_report 中标记 `bp_thickness_warning`

---

## 5. 命名冲突解决

当不同来源的命名产生冲突时：

1. **GDD 内部冲突**：送入 Clarification Gate 的 `clarification_required`
2. **GDD 与项目规范冲突**：GDD 优先（Tier 1 > Tier 3）
3. **跨域命名冲突**（两个 Domain Skill 生成同名类）：Cross-Domain Review 检测并要求冲突方之一改名
4. **UE5 保留字冲突**：添加项目前缀绕过，在 naming_resolution_log 中记录
