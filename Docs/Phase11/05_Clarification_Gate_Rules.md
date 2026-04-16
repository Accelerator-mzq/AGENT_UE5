# AGENT_UE5 Clarification Gate 规则

## 1. 定义

Clarification Gate 用于处理 GDD 缺失、含糊、冲突或高风险未决项。它的目标不是"遇到不确定就打断流程"，而是把不确定性进行分类处理。

---

## 2. 四类决策结果

### 2.1 accept_as_explicit
GDD 已明确，直接接受，不追问。

### 2.2 accept_with_safe_default
GDD 未明确，但可安全采用保守默认值。
- 需记录默认值和推理依据
- 置信度需标注

### 2.3 send_to_design_space_discovery
GDD 未明确，但这是 realization-level 设计空间，允许 Agent 继续发现与生成。

该决策的正式含义是：**把问题送入 Compiler Core 内部的真 Agent Stage 4**。后续由 Domain Skill Runtime 触发 Discovery / Candidates / Convergence，而不是在 Clarification Gate 中用启发式默认值提前写死。

### 2.4 clarification_required
GDD 未明确，且该问题会显著影响玩法、架构、网络、成本或平台边界，必须追问。

---

## 3. 产物结构 (`clarification_gate_report.json`)

```json
{
  "gate_version": "1.0",
  "source_contract_id": "rsc.monopoly.phase1.20260415",
  "items": [
    {
      "item_id": "cg-001",
      "topic": "最大游戏时长/僵局处理",
      "decision": "clarification_required",
      "risk_level": "high",
      "impact": "游戏可能因无人破产而无限持续",
      "provisional_default": "200 回合限制，最富有玩家获胜",
      "provisional": true
    },
    {
      "item_id": "cg-002",
      "topic": "玩家棋子视觉样式",
      "decision": "accept_with_safe_default",
      "risk_level": "low",
      "default_value": "简单彩色圆柱体",
      "inference_basis": "棋盘游戏原型标准惯例",
      "confidence": 0.9
    },
    {
      "item_id": "cg-003",
      "topic": "HUD 布局方式",
      "decision": "send_to_design_space_discovery",
      "risk_level": "low",
      "reason": "GDD 列了必须显示的元素但未规定布局，属于 realization-level 设计空间"
    }
  ]
}
```

---

## 4. Provisional 值传播机制

当 `clarification_required` 项未得到人类回答但管线选择继续时：

1. 使用 `provisional_default` 值继续
2. 该值在整个管线中保持 `provisional: true` 标记
3. 下游 Skill Fragment 中使用 provisional 值的决策在 design_decision_log 中标记 `provisional: true`
4. Build IR 中使用 provisional 值的步骤在 execution_hints 中标注 `contains_provisional: true`
5. Handoff v3 中汇总所有 `provisional_items`

provisional 标记的目的是：让管线可以先跑完，但所有基于未确认信息的决策都可以被追溯和重做。

---

## 5. fast_mode 下的 Clarification Gate 规则

### 5.1 硬规则

fast_mode 下 Clarification Gate 的自动默认**只适用于低风险缺失项**。

### 5.2 风险分级与 fast_mode 行为

| 风险级别 | fast_mode 行为 | 示例 |
|---------|--------------|------|
| **low** | 自动 `accept_with_safe_default` | 玩家棋子视觉样式、背景音乐风格 |
| **medium** | 自动 `accept_with_safe_default` 但标记 `provisional_warning: true` | Blue 颜色组单地产租金翻倍、TAX base_rent 语义 |
| **high** | **保持 `clarification_required`，不自动默认** | 最大游戏时长/僵局处理、胜负条件变体 |
| **critical** | **阻塞管线，不允许继续** | 网络模式、目标平台、核心玩法循环定义 |

### 5.3 高风险判断标准

以下任一条件满足即为 high 或 critical：
- 改变玩法骨架（核心循环、胜负条件、玩家人数上限）
- 改变平台边界（目标平台、输入设备类型）
- 改变网络模式（本地/在线/混合）
- 改变关键规则语义（规则的存在/不存在会导致完全不同的游戏体验）

### 5.4 fast_mode session 标记

```json
{
  "fast_mode": true,
  "clarification_gate_policy": "auto_default_low_medium_only",
  "retained_clarifications": ["cg-001", "cg-005"]
}
```

## 6. 人类参与点

Clarification Gate 是三个正式 human-in-the-loop 交互点之一：

1. Root Skill Contract 形成后（确认约束理解正确）
2. **Clarification Gate 中 clarification_required 项的回答**
3. converged_realization_pack 形成后（确认设计方向可接受）
