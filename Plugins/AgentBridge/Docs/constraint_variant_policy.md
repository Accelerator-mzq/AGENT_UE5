# Constraint vs Variant 标注策略

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/06_Constraint_vs_Variant_Policy.md

## 1. 定义

### 1.1 Constraint Field

GDD 明确锁定的值，整个管线中不可变更。

特征：
- GDD 给出精确数值、枚举或明确断言
- 修改该值会改变游戏身份或违背设计者意图
- 管线中任何阶段都不允许偏离

### 1.2 Variant Field

GDD 允许变化的空间，受 bounds 约束但不锁定具体值。

特征：
- GDD 只给出范围、意图、或完全沉默
- 具体值由 Design Space Discovery 和 Realization 过程决定
- 有 `must_satisfy`（必须满足的约束）和 `must_not`（必须避免的条件）

---

## 2. 标注时机

标注发生在 **Root Skill Contract 形成阶段**，是 Root Skill Contract 的核心职责之一。

标注一旦完成，在整个管线中保持不变：
- Domain Skill 读取 Constraint Fields 作为输入约束
- Domain Skill 在 Variant Fields 的 bounds 内进行 Design Space Discovery
- Cross-Domain Review 验证 Constraint 保持性
- Build IR 中 Constraint 值原样传递
- Handoff 中 Constraint 值原样传递

---

## 3. 标注判据

### 3.1 判为 Constraint 的条件

| 条件 | 示例 |
|------|------|
| GDD 给出精确数值 | "棋盘有 28 个格子" |
| GDD 给出精确枚举 | "支持 2-4 名玩家" |
| GDD 给出明确断言 | "最后一个未破产的玩家获胜" |
| 修改会改变游戏类型 | 棋盘格子数从 28 改为 100 |
| 修改会改变核心循环 | 将回合制改为实时制 |

### 3.2 判为 Variant 的条件

| 条件 | 示例 |
|------|------|
| GDD 只给出意图而非精确值 | "棋盘应该看起来清晰" |
| GDD 给出范围而非定值 | "租金在合理范围内递增" |
| GDD 完全沉默 | 未提及 HUD 布局方式 |
| 该维度属于 realization-level | 3D 棋盘的世界坐标尺寸 |
| 该维度对游戏身份无决定性影响 | 棋子的具体视觉样式 |

### 3.3 边界判定

1. **有疑义时倾向 Constraint**：宁可限制 Agent 创造空间也不冒违背设计者意图的风险
2. **Clarification Gate 兜底**：如果判断困难且影响显著，送入 `clarification_required`
3. **不可拆分原则**：一个 GDD 语句中的约束部分和可变部分必须拆分标注

---

## 4. 下游保持性检查

### 4.1 检查点

| 检查环节 | 检查方式 |
|---------|---------|
| Domain Skill Fragment 生成 | Fragment 中引用的 Constraint 值必须与 Root Skill Contract 一致 |
| Cross-Domain Convergence Review | 遍历所有 Fragment，验证 Constraint 值未被篡改 |
| Build IR 生成 | IR Action 中使用的 Constraint 值必须与 Root Skill Contract 一致 |
| Handoff Assembly | 汇总 Constraint 值，与 Root Skill Contract 做最终一致性校验 |

### 4.2 违反处理

如果在任何环节发现 Constraint 值被修改：
- 标记为 `constraint_violation`
- 阻塞该 Fragment 或 IR Action 的后续处理
- 在 Cross-Domain Review Report 中报告
- 不允许 provisional 绕过（Constraint 违反不是"待确认"，是"错误"）

---

## 5. Variant Field 的 bounds 传播

```
Root Skill Contract (bounds 定义)
  -> Domain Skill (bounds 作为 Discovery 约束输入)
  -> Realization Candidates (每个候选必须满足 bounds)
  -> Converged Pack (选中候选必须满足 bounds)
  -> Fragment (具体值必须在 bounds 内)
  -> Build IR (具体值传递)
```

bounds 本身不可在下游修改。如果 Design Space Discovery 发现 bounds 不合理，应回溯到 Clarification Gate 而非自行放宽 bounds。

---

## 6. 与 Clarification Gate 的关系

| | 已确认值 | 未确认值 |
|---|---------|---------|
| **Constraint** | 直接锁定 | 送 Clarification Gate，回答后锁定 |
| **Variant** | bounds 已知，进入 Discovery | bounds 不明，送 Clarification Gate 确认 bounds 后进入 Discovery |

两者是正交维度：Constraint/Variant 回答"字段性质是什么"，Clarification Gate 回答"字段值/bounds 是否已知"。
