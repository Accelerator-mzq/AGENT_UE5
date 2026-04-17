# AGENT_UE5 Claude/Codex 交接文档

## 1. 目的

本文档是给 Claude Code / Codex / 其他 AI Agent 在实施 Phase 11 时的强制阅读指南。它规定了文档阅读顺序、执行约束和常见陷阱。

---

## 2. 强制阅读顺序

进入 Phase 11 实施前，**必须按以下顺序阅读**，不可跳过：

| 顺序 | 文档 | 读后必须理解 |
|------|------|------------|
| 1 | `01_Phase11_Unified_Architecture.md` | 主链 7 个阶段、MCP 前后端边界、与 Phase 10 兼容策略 |
| 2 | `02_Root_Skill_Contract_Standard.md` | Root Skill Contract 的 10 个问题、产物结构 |
| 3 | `06_Constraint_vs_Variant_Policy.md` | Constraint/Variant 标注判据、下游保持性检查 |
| 4 | `03_Universal_Baseline_Standard.md` | Baseline 完整清单、presence_only 最低标准、不能再降的底线 |
| 5 | `04_Baseline_Realization_Policy.md` | 三类分法、升级条件 |
| 6 | `05_Clarification_Gate_Rules.md` | 4 档决策、fast_mode 高风险保护、provisional 传播 |
| 7 | `07_Design_Space_Discovery_and_Realization.md` | Discovery -> Candidates -> Convergence 协议、design_decision_log 三层分离 |
| 8 | `08_Skill_Graph_and_Domain_Skill.md` | Skill Graph 结构、Domain Skill 四重职责 |
| 9 | `14_Agent_Interaction_Protocol.md` | Generator-Evaluator 门控模型、Context Bundle、Evaluator 质量维度、重试策略 |
| 10 | `10_Naming_and_Path_Convention.md` | GDD-First 四层命名、naming_resolution_log、BP 薄层原则 |
| 11 | `09_Run_Isolation_Compare_Promote.md` | 三层结构、promotable 判定、fast_mode run 不可 promote |
| 12 | `11_Schema_and_Artifact_Reference.md` | Schema 变更清单、MCP 工具变更 |
| 13 | `12_Implementation_Taskbook.md` | 分批计划、优先级、依赖关系 |

`00_Phase11_Document_Index.md` 可随时查阅作为索引和术语速查。

---

## 3. 文档间依赖关系

```
01 (统一架构)
  ├── 02 (Root Skill Contract) ── 06 (Constraint/Variant)
  ├── 03 (Baseline Standard) ── 04 (Baseline Realization)
  ├── 05 (Clarification Gate)
  ├── 07 (Design Space Discovery) ── 08 (Skill Graph)
  ├── 09 (Run Isolation)
  ├── 10 (Naming Convention)
  └── 11 (Schema Reference) ── 12 (Implementation Taskbook)
```

- 01 是所有文档的上游
- 02 和 06 强耦合（Constraint/Variant 标注在 Root Skill Contract 中发生）
- 03 和 04 强耦合（Baseline Standard 定义项，Realization Policy 定义实现分类）
- 07 和 08 强耦合（Discovery/Realization 在 Domain Skill 中执行）
- 11 和 12 强耦合（Schema 变更驱动实施计划）

---

## 4. 执行约束

### 4.1 不可跳过的前置条件

| 实施动作 | 必须先完成 |
|---------|----------|
| 修改 `session.py` | 读完 01（理解 session_version 路由） |
| 创建 Root Skill Contract Schema | 读完 02 + 06 |
| 创建 Clarification Gate Schema | 读完 05 |
| 创建 Skill Graph Schema | 读完 08 |
| 修改 `pipeline_orchestrator.py` | 读完 01 + 11（理解 stage map 变更） |
| 创建 Design Space Discovery 逻辑 | 读完 07 + 08 + **14**（Agent 调用协议） |
| 实现 Generator-Evaluator 循环 | 读完 **14**（Context Bundle、Evaluator 质量维度、重试策略） |
| 创建 naming_resolution_log | 读完 10 |
| 创建 Run 治理工具 | 读完 09 |
| 修改 MCP 前端工具 | 读完 01（MCP 边界）+ 11（工具变更表） |

### 4.2 绝对不可做的事

- 不可删除 Phase 10 的旧 Schema（保留兼容）
- 不可修改 `CLAUDE.md` 中列出的"绝对不要修改的文件"
- 不可在 Blueprint 中实现核心逻辑（薄层原则）
- 不可在 fast_mode 中跳过高风险 Clarification 项
- 不可在 Domain Skill 中修改 Constraint Field 值
- 不可将 Design Space Discovery 放入 MCP 前端（它属于 Compiler Core）

---

## 5. 术语速查

| 术语 | 含义 | 首次定义 |
|------|------|---------|
| Root Skill Contract | 项目能力骨架 + 约束容器 + 启用边界 | 02 |
| Constraint Field | GDD 锁定，管线不可变更的字段 | 06 |
| Variant Field | GDD 允许变化，受 bounds 约束的字段 | 06 |
| Clarification Gate | 对缺失/含糊/冲突项的 4 档决策机制 | 05 |
| provisional | 未经人类确认但暂时采用的值，全管线带标记传播 | 05 |
| Design Space Discovery | Agent 识别可设计维度的过程 | 07 |
| Realization Candidates | 每个维度的候选方向 + trade-off | 07 |
| Convergence | 从候选中选择最终方向 + rationale | 07 |
| design_decision_log | per-fragment 非平凡决策记录 | 07 |
| Skill Graph | Domain Skill 的依赖/耦合/收敛图 | 08 |
| Domain Skill | 执行约束识别 + Discovery + Realization + Fragment 的编译单元 | 08 |
| presence_only | Baseline 项只要求存在，不进入发散设计 | 04 |
| realization_eligible | Baseline 项允许进入 Design Space Discovery | 04 |
| clarification_gated | Baseline 项需确认后才能实现 | 04 |
| naming_resolution_log | Build IR 步骤的命名审计记录 | 10 |
| Run Workspace | 单次管线执行的独立产物空间 | 09 |
| Promote | 将 run 正式吸收为项目基线 | 09 |
| fast_mode | 跳过 Discovery 的快速模式，不可 promote | 09 |
| MCP 前端 | 认知桥接层：Root Skill + Clarification + Skill Graph | 01 |
| MCP 后端 | 证据判定层：Evidence 系列工具 | 01 |
| Blueprint 薄层 | BP 仅承载资产绑定/布局，核心逻辑在 C++ | 10 |

---

## 6. 常见陷阱

### 6.1 架构陷阱

- **不要把 Design Space Discovery 当成枚举**：Agent 发现维度、生成方向，不是从预设列表中选。如果发现自己在写 `options: ["A", "B", "C"]`，说明走偏了。
- **不要混淆 Constraint 和 Clarification**：Constraint/Variant 是字段性质（可不可变），Clarification 是值状态（已知还是未知）。两个正交维度。
- **不要扩展 MCP 前端到 Design Space Discovery**：Discovery 在 Domain Skill 内执行，属于 Compiler Core，不是认知桥接。

### 6.2 实施陷阱

- **session_version 路由**：新旧管线通过 `session_version` 字段选择不同 stage map，不做产物格式转换。缺失 session_version 视为 "1.0"。
- **旧 Schema 不删**：`gdd_projection.schema.json`、`planner_output.schema.json`、`reviewed_handoff_v2.schema.json` 保留。
- **MCP 工具重命名保留别名**：`compiler_intake_prepare/save` 和 `compiler_plan_prepare/save` 在过渡期保留为别名。
- **naming_resolution_log 是 mandatory**：每个 Build IR Action 都必须有，不是可选项。

### 6.3 质量陷阱

- **Constraint 保持性检查不能跳过**：Cross-Domain Review 必须验证所有 Constraint 值未被修改。
- **provisional 标记必须传播到 Handoff**：如果 Clarification Gate 中有 provisional 值，整个管线下游都必须带 `provisional: true` 标记。
- **fast_mode 高风险保护**：fast_mode 不能自动默认 high/critical 风险项。如果发现 fast_mode run 中所有 Clarification 项都被 auto_default 了，说明高风险保护没生效。
