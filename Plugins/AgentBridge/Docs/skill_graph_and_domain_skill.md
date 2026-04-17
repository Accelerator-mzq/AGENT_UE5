# Skill Graph 与 Domain Skill

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/08_Skill_Graph_and_Domain_Skill.md

## 1. Skill Graph 定义

Skill Graph 是 Domain Skill 的组织载体。它以图结构描述所有 Skill Instance 的依赖关系、耦合关系和收敛顺序。

Skill Graph 不是执行计划——它不规定具体做什么，而是规定"谁先做、谁后做、谁和谁关联"。

---

## 2. Skill Graph 结构

### 2.1 节点

每个节点是一个 Skill Instance，包含：instance_id、template_id、domain_type、status、allows_design_space_discovery、dependencies、coupling、convergence_priority。

### 2.2 边

| 边类型 | 含义 | 影响 |
|--------|------|------|
| **dependency** | 前者必须完成后者才能开始 | 严格执行顺序 |
| **coupling** | 两者产物有接口耦合，需协调 | Cross-Domain Review 重点检查 |
| **convergence_order** | 建议收敛顺序（不严格） | 影响人类 review 呈现顺序 |

### 2.3 产物

`skill_graph.json`（含 graph_version、source_contract_id、nodes、edges、metadata）。

---

## 3. Domain Skill 四重职责

每个 Domain Skill（无论 Gameplay 还是 Baseline realization_eligible）执行四重职责：

1. **约束识别**：读取 Root Skill Contract 中与本域相关的 Constraint Fields、Variant Fields bounds、Clarification Gate 决策结果
2. **Design Space Discovery**：在 Variant Fields 的 bounds 内发现可设计维度，标注维度间耦合（详见 `design_space_discovery.md`）
3. **Realization Candidate Generation**：对每个可设计维度生成候选方向，评估 trade-off，通过 Convergence 选择最终方向
4. **Fragment Generation**：基于收敛结果生成 Dynamic Spec Fragment，含 design_decision_log

> **Agent 调用细节**（Generator/Evaluator 角色分离、Context Bundle、重试策略）详见 `agent_interaction_protocol.md`。

---

## 4. Baseline Domain Skill 与 Gameplay Domain Skill 的同构性

### 4.1 结构同构

两者拥有完全相同的目录结构（manifest.yaml / system_prompt.md / domain_prompt.md / evaluator_prompt.md / input_selector.yaml / output_schema.json）。

### 4.2 行为差异

| 维度 | Gameplay Domain Skill | Baseline Domain Skill |
|------|----------------------|----------------------|
| 创造性程度 | 高 | 通常较低（保守、标准化） |
| Discovery | 总是执行（除非 fast_mode） | 仅 realization_eligible 执行 |
| presence_only | 不适用 | 适用（最小实现，跳过 Discovery） |
| 评估标准 | gameplay feel + 规则一致性 | UX 完整性 + 产品规范 |

---

## 5. SkillTemplates vs Skills 分层

### 5.1 SkillTemplates（插件层）

位置：`Plugins/AgentBridge/SkillTemplates/`

职责：提供通用模板，不含项目实例数据。
- `genre_packs/` — 按游戏类型组织的 Gameplay 模板
- `baseline/` — Baseline 域模板

### 5.2 Skills（插件层 + 项目层）

- `Plugins/AgentBridge/Skills/` — 通用 Skill 基础设施（registry、base class）
- 项目层通过 Skill Graph 动态创建 Skill Instance

### 5.3 映射关系

```
SkillTemplate（模板）
  -> Skill Graph Node（规划）
    -> Skill Instance（运行时）
      -> Fragment（产出）
```

一个 SkillTemplate 可以被多个 Skill Graph Node 引用。一个 Skill Graph Node 在运行时创建一个 Skill Instance。

---

## 6. Skill Instance 生命周期

```
pending（已规划，未开始）
  -> running（正在执行四重职责）
    -> completed（四重职责完成，Fragment 已生成）
    -> failed（执行中断，记录 failure_reason）
```

failed Skill 不阻塞整个 Graph 执行，但 coupling 边连接的 Skill 会收到 warning，Cross-Domain Review 会标记不完整区域。

---

## 7. Skill Graph Planning 的职责边界

**负责**：从 Root Skill Contract 派生 Gameplay/Baseline Domain Skills、建立依赖/耦合/收敛顺序、选择合适的 SkillTemplate。

**不负责**：替 Domain Skill 提前写死 realization、决定 Discovery 会发现什么维度、执行 Fragment 生成。

Skill Graph 是规划产物，不是执行产物。执行由 Domain Skill Runtime 完成。
