# AGENT_UE5 Skill Graph 与 Domain Skill
> 原始来源：Docs/History/Phase11_Design_Pack/08_Skill_Graph_and_Domain_Skill.md

## 1. Skill Graph 定义

Skill Graph 是 Domain Skill 的组织载体。它以图结构描述所有 Skill Instance 的依赖关系、耦合关系和收敛顺序。

Skill Graph 不是执行计划——它不规定具体做什么，而是规定"谁先做、谁后做、谁和谁关联"。

---

## 2. Skill Graph 结构

### 2.1 节点

每个节点是一个 Skill Instance：

```json
{
  "instance_id": "skill-board-topology",
  "template_id": "boardgame.monopoly_like.board_topology",
  "domain_type": "gameplay",
  "status": "pending",
  "allows_design_space_discovery": true,
  "dependencies": ["skill-root-contract"],
  "coupling": ["skill-tile-system", "skill-hud"],
  "convergence_priority": 1
}
```

### 2.2 边

三种边类型：

| 边类型 | 含义 | 影响 |
|--------|------|------|
| **dependency** | 前者必须完成后者才能开始 | 严格执行顺序 |
| **coupling** | 两者产物有接口耦合，需协调 | Cross-Domain Review 重点检查 |
| **convergence_order** | 建议收敛顺序（不严格） | 影响人类 review 呈现顺序 |

### 2.3 skill_graph.json 产物

```json
{
  "graph_version": "1.0",
  "source_contract_id": "rsc.monopoly.phase1.20260415",
  "nodes": [
    {
      "instance_id": "skill-board-topology",
      "template_id": "boardgame.monopoly_like.board_topology",
      "domain_type": "gameplay",
      "allows_design_space_discovery": true,
      "convergence_priority": 1
    },
    {
      "instance_id": "skill-tile-system",
      "template_id": "boardgame.monopoly_like.tile_system",
      "domain_type": "gameplay",
      "allows_design_space_discovery": true,
      "convergence_priority": 2
    },
    {
      "instance_id": "skill-turn-loop",
      "template_id": "boardgame.monopoly_like.turn_loop",
      "domain_type": "gameplay",
      "allows_design_space_discovery": true,
      "convergence_priority": 2
    },
    {
      "instance_id": "skill-baseline-start-screen",
      "template_id": "baseline.start_screen.presence_only",
      "domain_type": "baseline",
      "allows_design_space_discovery": false,
      "convergence_priority": 5
    },
    {
      "instance_id": "skill-baseline-main-menu",
      "template_id": "baseline.main_menu.presence_only",
      "domain_type": "baseline",
      "allows_design_space_discovery": false,
      "convergence_priority": 5
    },
    {
      "instance_id": "skill-baseline-hud",
      "template_id": "baseline.hud.realization_eligible",
      "domain_type": "baseline",
      "allows_design_space_discovery": true,
      "convergence_priority": 3
    }
  ],
  "edges": [
    {
      "from": "skill-board-topology",
      "to": "skill-tile-system",
      "type": "dependency",
      "reason": "tile system 需要知道 board 布局才能定义 tile 位置"
    },
    {
      "from": "skill-tile-system",
      "to": "skill-baseline-hud",
      "type": "coupling",
      "reason": "HUD 需要展示 tile 信息，但不严格依赖 tile 实现完成"
    },
    {
      "from": "skill-board-topology",
      "to": "skill-turn-loop",
      "type": "coupling",
      "reason": "turn loop 中的移动逻辑需要 board topology 信息"
    }
  ],
  "metadata": {
    "total_gameplay_skills": 6,
    "total_baseline_skills": 6,
    "total_edges": 15,
    "generated_at": "2026-04-15T14:30:22Z"
  }
}
```

---

## 3. Domain Skill 四重职责

每个 Domain Skill（无论 Gameplay 还是 Baseline realization_eligible）执行四重职责：

### 3.1 职责一：约束识别

- 读取 Root Skill Contract 中与本域相关的 Constraint Fields
- 读取 Variant Fields 的 bounds
- 读取 Clarification Gate 中与本域相关的决策结果
- 将约束整理为本域的 input constraints

### 3.2 职责二：Design Space Discovery

- 在 Variant Fields 的 bounds 内发现可设计维度
- 标注维度间耦合（含跨域耦合）
- 产出 design_space_report

（详见 `07_Design_Space_Discovery_and_Realization.md`）

### 3.3 职责三：Realization Candidate Generation

- 对每个可设计维度生成候选方向
- 评估 trade-off
- 通过 Convergence 选择最终方向
- 产出 realization_candidates + converged_realization_pack

### 3.4 职责四：Fragment Generation

- 基于收敛结果生成 Dynamic Spec Fragment
- Fragment 中包含 design_decision_log
- Fragment 中引用 Constraint 值必须与 Root Skill Contract 一致
- 产出 skill_fragment（含 spec_fragments + design_decision_log + assumptions + confidence）

> **Agent 调用细节**（Generator/Evaluator 角色分离、Context Bundle 输入、Evaluator 质量维度、重试策略、Trace 落盘）详见 `14_Agent_Interaction_Protocol.md`。

---

## 4. Baseline Domain Skill 与 Gameplay Domain Skill 的同构性

### 4.1 结构同构

Baseline Domain Skill 与 Gameplay Domain Skill 拥有完全相同的目录结构：

```
SkillTemplates/
  baseline/
    {baseline_name}/
      manifest.yaml
      system_prompt.md
      domain_prompt.md
      evaluator_prompt.md
      input_selector.yaml
      output_schema.json

  genre_packs/
    {genre}/{subgenre}/
      {skill_name}/
        manifest.yaml
        system_prompt.md
        domain_prompt.md
        evaluator_prompt.md
        input_selector.yaml
        output_schema.json
```

### 4.2 行为差异

| 维度 | Gameplay Domain Skill | Baseline Domain Skill |
|------|----------------------|----------------------|
| 创造性程度 | 高（gameplay 设计空间大） | 通常较低（保守、标准化） |
| Discovery | 总是执行（除非 fast_mode） | 仅 realization_eligible 执行 |
| presence_only | 不适用 | 适用（最小实现，跳过 Discovery） |
| 评估标准 | gameplay feel + 规则一致性 | UX 完整性 + 产品规范 |

---

## 5. SkillTemplates vs Skills 分层

### 5.1 SkillTemplates（插件层）

位置：`Plugins/AgentBridge/SkillTemplates/`

职责：提供通用模板，不含项目实例数据。

包含：
- `genre_packs/` — 按游戏类型组织的 Gameplay 模板
- `baseline/` — Baseline 域模板（Phase 11 新增）

### 5.2 Skills（插件层 + 项目层）

位置：
- `Plugins/AgentBridge/Skills/` — 通用 Skill 基础设施（registry、base class）
- 项目层通过 Skill Graph 动态创建 Skill Instance

职责：
- `base_domains/registry.py` — 10 个基础域定义（Phase 11 激活为 Baseline Domain Skills）
- Skill Instance 是运行时对象，不持久化为文件

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

状态转换规则：
- `pending -> running`：所有 dependency 边的前置 Skill 状态为 completed
- `running -> completed`：四重职责全部完成 + Fragment 通过自检
- `running -> failed`：任何职责阶段发生不可恢复错误

failed Skill 不阻塞整个 Graph 执行，但：
- coupling 边连接的 Skill 会收到 warning
- Cross-Domain Review 会标记不完整区域
- Handoff 中会汇报 failed skills

---

## 7. Skill Graph Planning 的职责边界

Skill Graph Planning 阶段（MCP 前端覆盖）的职责：

**负责**：
- 从 Root Skill Contract 派生 Gameplay Domain Skills
- 从 Baseline Merge 派生 Baseline Domain Skills
- 建立依赖、耦合、收敛顺序
- 选择合适的 SkillTemplate 作为每个节点的模板

**不负责**：
- 替 Domain Skill 提前写死 realization
- 决定 Design Space Discovery 会发现什么维度
- 决定 Realization Candidates 会生成什么方向
- 执行 Fragment 生成

Skill Graph 是规划产物，不是执行产物。执行由 Domain Skill Runtime 完成。
