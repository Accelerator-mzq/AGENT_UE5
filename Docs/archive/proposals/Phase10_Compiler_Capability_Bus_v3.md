# AGENT_UE5 Compiler Capability Bus 结构定义 v3

## 0. 文档定位

本文件保留 `Compiler Capability Bus` 这一命名，但按当前最终收敛结论，它的实质应理解为：

**前端认知分解接口（Stage 1-2）**

也就是说，它的主职责是：

**GDD → Root Skill → Sub-Skill Graph → Spec Family 映射建议**

它对应 Compiler 5-stage pipeline 中 **Stage 1（Intake/Projection）与 Stage 2（Planner/Skill 选择）的认知判断部分**。

Stage 3（Skill Runtime）、Stage 4（Cross-Review）、Stage 5（Lowering）及 Handoff 组装由 Compiler Core 调度。Agent 在 Stage 3-5 中仍参与，但方式是 Compiler Core 内部的 prepare/save 调度，不属于本接口。

---

## 1. 修正后的定义

`Compiler Capability Bus` 应承担以下职责：

### A. GDD 语义理解（Stage 1）
- 识别游戏类型
- 识别核心玩法形态
- 识别外壳能力需求
- 识别系统性能力需求

### B. Root Skill 形成（Stage 1-2）
- 将 GDD 所需能力组合组织成一个总 Skill
- 输出游戏的能力组合总貌

### C. Sub-Skill Graph 分解（Stage 2）
- 将总 Skill 拆解为子 Skill 图
- 建立依赖关系
- 区分核心、辅助、条件性子 Skill

### D. Spec Family 映射建议（Stage 2）
- 将子 Skill 映射到对应 spec family
- 结合 Static Spec Bases / Contracts / Templates 给出 spec 投影建议
- 输出 Dynamic Spec Fragments 的生成方向

本接口输出 spec family 映射建议，但实际 Dynamic Spec Fragments 的生成由 Compiler Core 调度的 Skill Runtime（Stage 3）完成。

### E. 冲突 / 缺口 / 风险提示
- 提示 skill 组合冲突
- 提示 spec family 缺口
- 提示需要 review 的开放问题

---

## 2. 与 Compiler Core 的边界

### Compiler Core 仍然负责
- 输入读取
- schema 校验
- normalize
- mode routing
- planner 调度
- skill registry / contract 装载
- Skill Runtime 调度（Stage 3）
- Cross-Review 调度（Stage 4）
- Lowering 调度（Stage 5）
- Handoff 组装与序列化

### 本接口负责
- Stage 1-2 的高不确定性前端认知分解
- Root Skill 形成
- Sub-Skill Graph 形成
- Spec Family 映射建议
- review 问题发现

因此：

> Core 负责 canonical compiler flow（特别是 Stage 3-5 的结构化调度）
> 本接口负责 Stage 1-2 的前端认知分解与裁决

---

## 3. 与 Skill System 的边界

### Skill System 负责
- 类型语义
- 领域能力
- Skill 内部规则
- spec fragments 生成逻辑
- review rules
- lowering rules
- 同类 GDD 的复用

### 本接口负责
- 识别该调用哪些 Skill
- 决定 Skill 的组合图
- 帮助判断这些 Skill 将落向哪些 spec family
- 发现高层冲突与缺口

换句话说：

> Skill System 负责"Skill 是什么"
> 本接口负责"这次项目需要哪些 Skill、如何组合、将投影到哪些 spec"

四层标准表述：

> Skill 决定生成什么 spec；Static Spec 决定 spec 长什么样；Dynamic Spec 决定当前项目里实际生成了什么（结构受 Static Spec 约束，内容由 AI Agent 填充）；Reviewed Handoff 决定执行层正式消费什么。

---

## 4. 与 Static / Dynamic Spec 的边界

### Static Spec 负责
- family schema
- contracts
- defaults
- templates
- 结构骨架

### Dynamic Spec 负责
- 当前项目实际生成出的 per-Skill spec fragments（结构受 Static Spec 约束，内容由 Agent 填充）
- reviewed spec tree

### 本接口负责
- 指导"子 Skill 应投影到哪些 spec family"
- 指导"哪些 dynamic fragments 应被生成"
- 但不直接成为 Dynamic Spec 本体
- 实际 fragment 生成由 Compiler Core 调度的 Skill Runtime（Stage 3）完成

---

## 5. 推荐输入

- GDD 文本或 GDD Projection
- Project State 摘要
- 可用 Skill Registry 元数据
- Static Spec Families / Contracts / Templates
- 当前设计目标与约束
- 既有 spec / handoff 摘要（如 Brownfield）

---

## 6. 推荐输出

- GDD intent summary
- Root Skill definition
- Sub-Skill Graph
- per-skill spec family mapping suggestions
- risk / conflict / gap summary
- review questions list

---

## 7. 推荐最小接口族

- `analyze_gdd_intent()`
- `build_root_skill()`
- `decompose_subskill_graph()`
- `map_subskills_to_spec_families()`
- `review_skill_and_spec_conflicts()`
- `summarize_missing_capabilities()`

---

## 8. 不推荐接口

以下职责不应直接落入本接口：

- `run_skill_runtime()` — 属于 Compiler Core Stage 3 调度
- `merge_dynamic_spec_tree()` — 属于 Compiler Core Stage 4 调度
- `build_handoff()` — 属于 Compiler Core Handoff Builder
- `execute_editor_changes()` — 属于 Execution
- `run_official_tests()` — 属于官方测试体系

---

## 9. 成功标准

1. 本接口覆盖 Stage 1-2 的认知分解，不越界到 Stage 3-5
2. 本接口能支撑 Root Skill → Sub-Skill Graph → Spec Family 映射建议的前端链路
3. Skill System 仍是语义主承载层
4. Compiler Core 仍持有 canonical flow（Stage 3-5 调度）
5. Dynamic Spec 仍是 Skill 运行后的结构化产物（结构受约束，内容由 Agent 填充）
6. 不出现"本接口吞掉 Skill / Core / Spec"的倾向

---

## 10. 结论

`Compiler Capability Bus` 的更准确实质应被理解为：

**Stage 1-2 的前端认知分解接口：GDD 到 Root Skill / Sub-Skill Graph / Spec Family 映射建议。**

Stage 3-5 的结构化调度归 Compiler Core，Agent 通过 Core 内部 prepare/save 参与。
