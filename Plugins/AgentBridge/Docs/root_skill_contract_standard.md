# Root Skill Contract 标准

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/02_Root_Skill_Contract_Standard.md

## 1. 定义

Root Skill Contract 是：
- 当前项目的**能力骨架**
- 当前项目的**约束容器**
- 当前 Phase 的**启用边界**
- Gameplay Domain 与 Baseline Domain 的**共同上游约束对象**

它不是：realization 候选列表、Dynamic Spec 本体、Build IR、Handoff。

---

## 2. 输入来源

### 2.1 GDD 显式输入
- 游戏类型、胜利条件、玩家人数、视角
- 核心玩法循环、已确认系统
- 已确认类名/文件名/路径风格
- 当前 Phase 限制

### 2.2 Universal Game Baseline Standard
- 启动与入口、前台壳层、设置与配置
- 输入基础、HUD/Popup/结果表达
- 音频基础、平台基础

详见 `universal_baseline_standard.md`。

### 2.3 Clarification Gate 结果
- 已确认项、延后项、默认项、阻塞项

详见 `clarification_gate_rules.md`。

### 2.4 项目策略
- run policy、naming policy、placement policy、phase policy

---

## 3. Root Skill Contract 必须回答的 10 个问题

1. 当前项目的硬约束有哪些（Constraint Fields）
2. 当前项目的软意图有哪些（gameplay feel、design tensions）
3. 当前项目有哪些 required capabilities
4. 哪些 capabilities 当前 Phase 启用
5. 哪些 capabilities 为 deferred
6. 哪些 Baseline 项只做 presence contract
7. 哪些 Baseline 项允许 realization-level 发散
8. 哪些 Gameplay 域允许 Design Space Discovery
9. 哪些域需要 Clarification 才能继续
10. Skill Graph 规划的边界是什么

---

## 4. 产物结构 (`root_skill_contract.json`)

```json
{
  "contract_version": "1.0",
  "contract_id": "rsc.{project}.{phase}.{date}",
  "source_gdd": {
    "file_path": "ProjectInputs/GDD/GDD_MonopolyGame.md",
    "scope_summary": "..."
  },
  "game_identity": {
    "game_type": "board_strategy",
    "subgenre": "monopoly_like",
    "presentation_model": "top_down_3d",
    "player_count_range": [2, 4],
    "win_condition": "last_non_bankrupt_player"
  },
  "phase_scope": {
    "current_phase": "phase1_local_multiplayer",
    "in_scope": ["..."],
    "out_of_scope": ["..."]
  },
  "constraint_fields": {
    "board.tile_count": {
      "type": "constraint",
      "value": 28,
      "gdd_ref": "GDD SS2.1"
    }
  },
  "variant_fields": {
    "board.world_layout_dimensions": {
      "type": "variant",
      "bounds": {
        "must_satisfy": ["格子在俯视相机下清晰可见"],
        "must_not": ["格子重叠"]
      }
    }
  },
  "soft_intents": {
    "gameplay_feel": ["fast-paced simplified monopoly", "casual party game"],
    "design_tensions": ["simplified board vs strategic depth", "elimination vs engagement"]
  },
  "baseline_capabilities": [
    {
      "capability_id": "baseline-start-screen",
      "activation": "required",
      "realization_class": "presence_only"
    }
  ],
  "gameplay_capabilities": [
    {
      "capability_id": "gameplay-board-topology",
      "activation": "required",
      "allows_design_space_discovery": true
    }
  ],
  "metadata": {
    "generated_at": "...",
    "generator": "AgentBridge.Compiler.RootSkill.v1"
  }
}
```

---

## 5. Constraint Field vs Variant Field 标注规则

详见 `constraint_variant_policy.md`。

Root Skill Contract 中每个设计元素必须被标注为 Constraint 或 Variant。标注发生在 Root Skill Contract 形成阶段，贯穿整个管线。
