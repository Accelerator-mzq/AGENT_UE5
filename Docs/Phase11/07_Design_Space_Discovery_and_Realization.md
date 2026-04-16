# AGENT_UE5 Design Space Discovery 与 Realization 协议

## 1. 一句话结论

Design Space Discovery 是 Phase 11 的核心能力升级：Agent 不再从预设列表中选取实现，而是主动发现设计维度、生成候选方向、评估 trade-off、收敛并记录决策。

---

## 2. 三阶段协议

```
Design Space Discovery（发现可设计维度）
  -> Realization Candidate Generation（生成候选方向）
  -> Convergence（收敛 + 人类确认）
```

### 2.1 阶段一：Design Space Discovery

**输入**：Root Skill Contract + Clarification Gate Report + 当前 Domain Skill 的职责范围

**职责**：
- 识别当前域中所有可设计维度（dimensions）
- 每个维度标注约束来源（Constraint Field 不可设计，Variant Field 可设计）
- 区分哪些维度有 GDD 线索、哪些完全开放
- 标注维度间的耦合关系

**核心原则**：Agent **发现**维度，不是从预设列表中选。如果发现过程退化为"从模板中挑选"，说明 Discovery 失败。

**产物**：`design_space_report.json`

```json
{
  "skill_instance_id": "skill-board-topology",
  "discovery_dimensions": [
    {
      "dimension_id": "dim-001",
      "name": "棋盘世界布局",
      "constraint_source": "variant",
      "variant_bounds": {
        "must_satisfy": ["格子在俯视相机下清晰可见"],
        "must_not": ["格子重叠"]
      },
      "gdd_hints": ["GDD 提到矩形环形但未给尺寸"],
      "coupled_dimensions": ["dim-002"],
      "design_freedom": "high"
    },
    {
      "dimension_id": "dim-002",
      "name": "格子间距与对齐方式",
      "constraint_source": "variant",
      "variant_bounds": {
        "must_satisfy": ["28 个格子均匀分布"],
        "must_not": ["间距不一致导致视觉破碎"]
      },
      "gdd_hints": [],
      "coupled_dimensions": ["dim-001"],
      "design_freedom": "medium"
    }
  ],
  "locked_dimensions": [
    {
      "dimension_id": "dim-locked-001",
      "name": "格子总数",
      "constraint_source": "constraint",
      "locked_value": 28,
      "reason": "GDD SS2.1 明确指定"
    }
  ]
}
```

### 2.2 阶段二：Realization Candidate Generation

**输入**：design_space_report.json

**职责**：
- 对每个可设计维度生成 2-4 个候选方向
- 每个候选包含具体设计描述 + trade-off 分析
- 候选必须满足 Variant bounds
- 标注候选之间的互斥/兼容关系

**核心原则**：候选方向是 Agent **生成**的，不是从预设库中取的。每个候选应该有独特的设计思路和取舍。

**产物**：`realization_candidates.json`

```json
{
  "skill_instance_id": "skill-board-topology",
  "candidates": [
    {
      "dimension_id": "dim-001",
      "candidates": [
        {
          "candidate_id": "rc-001-a",
          "name": "紧凑居中矩形",
          "description": "28 格紧凑排列，棋盘居中，四周留白",
          "trade_offs": {
            "pros": ["格子清晰可见", "棋盘整体感强"],
            "cons": ["四周空间浪费", "格子较小"]
          },
          "satisfies_bounds": true,
          "estimated_complexity": "low"
        },
        {
          "candidate_id": "rc-001-b",
          "name": "满屏扩展矩形",
          "description": "28 格扩展至接近屏幕边缘，格子更大",
          "trade_offs": {
            "pros": ["格子大，信息展示充分", "空间利用率高"],
            "cons": ["棋盘边缘可能被 HUD 遮挡", "相机需要更高视角"]
          },
          "satisfies_bounds": true,
          "estimated_complexity": "medium"
        }
      ]
    }
  ]
}
```

### 2.3 阶段三：Convergence

**输入**：realization_candidates.json

**职责**：
- 对每个维度选择一个候选方向
- 给出选择 rationale（为什么选这个、不选其他）
- 检查跨维度一致性（选择 A 维度的候选 X 是否与 B 维度的候选 Y 兼容）
- 标记需要人类确认的选择

**人类确认点**：converged_realization_pack 形成后是三个正式 human-in-the-loop 交互点之一。

**产物**：`converged_realization_pack.json`

```json
{
  "skill_instance_id": "skill-board-topology",
  "converged_choices": [
    {
      "dimension_id": "dim-001",
      "chosen_candidate": "rc-001-a",
      "rationale": "紧凑居中更适合 Monopoly 的传统视觉预期，且留白可用于未来 HUD 扩展",
      "rejected_alternatives": [
        {
          "candidate_id": "rc-001-b",
          "rejection_reason": "满屏布局可能与 HUD 冲突，且偏离传统棋盘游戏视觉"
        }
      ],
      "human_confirmation_needed": false,
      "provisional": false
    }
  ],
  "cross_dimension_consistency": {
    "checked": true,
    "conflicts": []
  }
}
```

> **完整 Agent 调用协议**（Generator-Evaluator 门控模型、Context Bundle 结构、各阶段 Evaluator 质量维度、重试策略、Trace 审计）详见 `14_Agent_Interaction_Protocol.md`。

---

## 3. design_decision_log 定义

### 3.1 三层分离

Phase 11 中设计决策记录分三层，各层职责不同：

| 层 | 产物 | 回答的问题 |
|----|------|----------|
| **realization_candidates** | `realization_candidates.json` | "有哪些路径可以走？" |
| **converged_pack** | `converged_realization_pack.json` | "选了哪条路径？为什么？" |
| **design_decision_log** | Fragment 内的 `design_decision_log` 字段 | "沿途每个岔口是怎么走的？" |

### 3.2 design_decision_log 的范围

design_decision_log 记录的是 Fragment 生成过程中的**非平凡决策**——那些在已收敛方向内仍然需要做出选择的点。

**记录条件**（任一满足即记录）：
- 收敛方向只定了大方向，具体实现有多种可能
- 需要在两个同样合理的实现方式中选择
- 涉及 trade-off（性能 vs 可读性、简单 vs 灵活等）
- 使用了 provisional 值

**不记录**：
- 显而易见的实现选择（如用 `TArray` 还是 `TMap` 存储列表数据）
- Constraint Field 的直接应用（无决策空间）
- 纯格式/命名选择（这些在 naming_resolution_log 中记录）

### 3.3 结构

```json
{
  "design_decision_log": [
    {
      "decision_id": "ddl-001",
      "topic": "格子坐标系原点位置",
      "context": "收敛方向选择了紧凑居中矩形，但原点可以在左上角或棋盘中心",
      "chosen": "棋盘中心为原点",
      "rationale": "中心原点更适合旋转/缩放操作，且与 UE5 世界坐标习惯一致",
      "alternatives": ["左上角原点：适合 2D 网格逻辑但不利于 3D 变换"],
      "provisional": false,
      "impact": "medium"
    },
    {
      "decision_id": "ddl-002",
      "topic": "格子间距计算方式",
      "context": "28 格均匀分布在矩形上，但可以等间距或等比例",
      "chosen": "等间距分布",
      "rationale": "Monopoly 传统布局为等间距，且简化坐标计算",
      "alternatives": ["等比例：角格和边格面积不同，更有视觉层次"],
      "provisional": false,
      "impact": "low"
    }
  ]
}
```

### 3.4 impact 分级

| 级别 | 含义 | 示例 |
|------|------|------|
| **high** | 影响多个下游 Fragment 或改变用户可感知行为 | 坐标系选择、数据结构主轴 |
| **medium** | 影响当前 Fragment 的实现方式 | 间距计算方式、事件派发模式 |
| **low** | 局部实现选择，不影响接口 | 内部变量初始化顺序 |

---

## 4. fast_mode 下的行为

fast_mode 下 Design Space Discovery 被跳过：

| 阶段 | 正式模式 | fast_mode |
|------|---------|-----------|
| Discovery | 完整执行 | **跳过** |
| Candidates | 完整生成 | **跳过**，使用默认/最简实现 |
| Convergence | 人类确认 | **跳过** |
| design_decision_log | 完整记录 | 最小记录（标注 `fast_mode: true`） |

fast_mode 产出的 Fragment 中 design_decision_log 标记为 `"fast_mode_default": true`，表示未经过正式 Discovery 过程。

---

## 5. 与 Baseline 域的关系

Baseline 域中的三类处理：

| Baseline 类型 | Discovery 行为 |
|--------------|---------------|
| presence_only | 不进入 Discovery，直接生成最小 Fragment |
| realization_eligible | 完整进入 Discovery -> Candidates -> Convergence |
| clarification_gated | 等待 Clarification 回答后，升级为 presence_only 或 realization_eligible |

realization_eligible 的 Baseline 项（如 HUD 布局、主菜单结构）与 Gameplay 域的 Discovery 过程完全相同。

---

## 6. 质量检查点

### 6.1 Discovery 质量

- 维度数量合理（通常 3-8 个/域，过少说明探索不充分，过多说明粒度过细）
- 每个维度有明确的约束来源标注
- locked_dimensions 与 Root Skill Contract 的 Constraint Fields 一致

### 6.2 Candidates 质量

- 每个维度至少 2 个候选
- 每个候选有具体描述（不是泛泛的"方案 A / 方案 B"）
- trade-off 分析涉及真实权衡（不是一个明显优于其他）
- 所有候选满足 Variant bounds

### 6.3 Convergence 质量

- 每个选择有 rationale
- rejection_reason 具体（不是"不够好"）
- 跨维度一致性检查通过
- provisional 标记正确传播
