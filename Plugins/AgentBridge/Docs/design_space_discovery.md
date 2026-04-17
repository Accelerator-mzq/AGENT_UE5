# Design Space Discovery 与 Realization 协议

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/07_Design_Space_Discovery_and_Realization.md

## 1. 定义

Design Space Discovery 是框架的核心能力：Agent 不再从预设列表中选取实现，而是主动发现设计维度、生成候选方向、评估 trade-off、收敛并记录决策。

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

### 2.2 阶段二：Realization Candidate Generation

**输入**：design_space_report.json

**职责**：
- 对每个可设计维度生成 2-4 个候选方向
- 每个候选包含具体设计描述 + trade-off 分析
- 候选必须满足 Variant bounds
- 标注候选之间的互斥/兼容关系

**核心原则**：候选方向是 Agent **生成**的，不是从预设库中取的。

**产物**：`realization_candidates.json`

### 2.3 阶段三：Convergence

**输入**：realization_candidates.json

**职责**：
- 对每个维度选择一个候选方向
- 给出选择 rationale
- 检查跨维度一致性
- 标记需要人类确认的选择

**人类确认点**：converged_realization_pack 形成后是三个正式 human-in-the-loop 交互点之一。

**产物**：`converged_realization_pack.json`

> **Agent 调用协议**（Generator-Evaluator 门控模型、Context Bundle 结构、各阶段 Evaluator 质量维度、重试策略、Trace 审计）详见 `agent_interaction_protocol.md`。

---

## 3. design_decision_log 定义

### 3.1 三层分离

| 层 | 产物 | 回答的问题 |
|----|------|----------|
| **realization_candidates** | `realization_candidates.json` | "有哪些路径可以走？" |
| **converged_pack** | `converged_realization_pack.json` | "选了哪条路径？为什么？" |
| **design_decision_log** | Fragment 内的 `design_decision_log` 字段 | "沿途每个岔口是怎么走的？" |

### 3.2 记录条件

design_decision_log 记录 Fragment 生成过程中的**非平凡决策**。

**记录条件**（任一满足即记录）：
- 收敛方向只定了大方向，具体实现有多种可能
- 需要在两个同样合理的实现方式中选择
- 涉及 trade-off（性能 vs 可读性、简单 vs 灵活等）
- 使用了 provisional 值

**不记录**：
- 显而易见的实现选择
- Constraint Field 的直接应用（无决策空间）
- 纯格式/命名选择（在 naming_resolution_log 中记录）

### 3.3 impact 分级

| 级别 | 含义 | 示例 |
|------|------|------|
| **high** | 影响多个下游 Fragment 或改变用户可感知行为 | 坐标系选择、数据结构主轴 |
| **medium** | 影响当前 Fragment 的实现方式 | 间距计算方式、事件派发模式 |
| **low** | 局部实现选择，不影响接口 | 内部变量初始化顺序 |

---

## 4. fast_mode 下的行为

| 阶段 | 正式模式 | fast_mode |
|------|---------|-----------|
| Discovery | 完整执行 | **跳过** |
| Candidates | 完整生成 | **跳过**，使用默认/最简实现 |
| Convergence | 人类确认 | **跳过** |
| design_decision_log | 完整记录 | 最小记录（标注 `fast_mode: true`） |

fast_mode 产出的 Fragment 中 design_decision_log 标记为 `"fast_mode_default": true`。

---

## 5. 与 Baseline 域的关系

| Baseline 类型 | Discovery 行为 |
|--------------|---------------|
| presence_only | 不进入 Discovery，直接生成最小 Fragment |
| realization_eligible | 完整进入 Discovery -> Candidates -> Convergence |
| clarification_gated | 等待 Clarification 回答后，升级为 presence_only 或 realization_eligible |

---

## 6. 质量检查点

- **Discovery**：维度数量合理（3-8 个/域），每个维度有明确约束来源标注
- **Candidates**：每维度至少 2 个候选，trade-off 涉及真实工程/设计矛盾
- **Convergence**：每个选择有 rationale，跨维度一致性检查通过
