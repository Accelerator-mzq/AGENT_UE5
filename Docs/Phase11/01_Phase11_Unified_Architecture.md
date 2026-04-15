# AGENT_UE5 Phase 11 最终统一架构

## 1. 一句话结论

Phase 11 的目标是把 AGENT_UE5 从"翻译编译器"升级为"设计编译器"：

> 一个以 Root Skill 为上游约束骨架、以 Domain Skill 为设计与编译单元、以 Skill Graph 为组织载体、以 Agent 发现设计空间并生成 realization 为核心能力、以 review/convergence 为收口机制、以 run isolation 为测试治理基础的 Skill-First Design Compiler Framework。

---

## 2. 正式主链

```
GDD
  -> Root Skill Contract (含 Universal Baseline Merge)
  -> Clarification Gate
  -> Skill Graph Planning
  -> Domain Skill Runtime
       含: Design Space Discovery
       含: Realization Candidate Generation
       含: Fragment Generation (含 design_decision_log)
  -> Cross-Domain Convergence Review
  -> Reviewed Dynamic Spec Tree
  -> Build IR (含 naming_resolution_log + Baseline 构建步骤)
  -> Reviewed Handoff v3
  -> Execution
```

---

## 3. 各阶段职责

### 3.1 Root Skill Contract 形成

**输入**：GDD + Universal Game Baseline Standard
**输出**：`root_skill_contract.json`
**职责**：
- 提取 GDD 硬约束（Constraint Fields）
- 识别可变化空间（Variant Fields）
- 合并 Universal Baseline（标注 presence_only / realization_eligible / clarification_gated）
- 提取软意图（gameplay feel、design tensions）
- 决定当前 Phase 能力启用范围
- 决定哪些域允许 Design Space Discovery

**不负责**：穷举实现选项、直接生成 realization、直接产出 Build IR

### 3.2 Clarification Gate

**输入**：`root_skill_contract.json`
**输出**：`clarification_gate_report.json`
**职责**：
- 对每个缺失/含糊/冲突项做出 4 档决策：
  - `accept_as_explicit`：GDD 已明确，直接接受
  - `accept_with_safe_default`：未明确但可安全默认
  - `send_to_design_space_discovery`：未明确，送入设计空间探索
  - `clarification_required`：必须追问
- 对 `clarification_required` 项：管线暂停或使用 provisional 默认值继续（带 provisional 标记传播）

### 3.3 Skill Graph Planning

**输入**：`root_skill_contract.json` + `clarification_gate_report.json`
**输出**：`skill_graph.json`
**职责**：
- 从 Root Skill 派生 Gameplay Domain Skills
- 从 Baseline Merge 派生 Baseline Domain Skills
- 建立 Skill Instances
- 标记依赖关系和耦合关系
- 标记收敛顺序

**不负责**：替 Domain Skill 提前写死所有 realization

### 3.4 Domain Skill Runtime

**输入**：`skill_graph.json` + `root_skill_contract.json` + `clarification_gate_report.json`
**输出**：
- `design_space_report.json`
- `realization_candidates.json`
- `converged_realization_pack.json`
- `skill_fragments/*.json`（含 design_decision_log）

**每个 Domain Skill 的四重职责**：
1. 约束识别（读取 Constraint Fields）
2. Design Space Discovery（发现可设计维度）
3. Realization Candidate Generation（生成候选方向）
4. Fragment Generation（基于收敛结果生成 Dynamic Spec Fragment）

### 3.5 Cross-Domain Convergence Review

**输入**：全部 skill_fragments + realization_candidates
**输出**：`cross_review_report.json`（增强版）
**职责**：
- Phase 10 原有一致性检查
- 新增：跨域 realization 冲突检测
- 新增：设计连贯性评估
- 新增：Baseline 完整性检查
- 新增：约束保持性检查（Constraint Field 值在下游保持不变）
- 新增：Blueprint 薄层原则检查
- 输出 Reviewed Dynamic Spec Tree

### 3.6 Lowering

**输入**：Reviewed Dynamic Spec Tree
**输出**：`build_ir.json`（增强版）
**增强**：
- 新增 Baseline 构建步骤（约 10 个新 IR Action）
- 每个步骤增加 `naming_resolution_log`
- 每个步骤增加 `provisional_warning`（如包含 provisional 值）

### 3.7 Handoff Assembly

**输入**：全部前序产物
**输出**：`reviewed_handoff_v3.json`
**增强**（相对 v2）：
- `run_id`
- `design_directions_summary`
- `constraint_variant_summary`
- `baseline_coverage_summary`
- `provisional_items`
- `design_decision_log_summary`

---

## 4. MCP 边界

### 4.1 MCP 前端（认知桥接层）

覆盖：Root Skill Contract 形成 + Clarification Gate + Skill Graph Planning

这三个是 GDD 理解和规划阶段，需要 Agent 理解设计意图并做出结构性判断，属于认知桥接。

**MCP 前端工具**：
| 工具 | 状态 |
|------|------|
| `compiler_create_session` | 保留（增加 session_version, run_id） |
| `compiler_root_skill_prepare` / `save` | 新增（替代 intake_prepare/save） |
| `compiler_clarification_prepare` / `save` | 新增 |
| `compiler_skill_graph_prepare` / `save` | 新增（替代 plan_prepare/save） |
| `compiler_get_session_status` | 保留（增加新阶段状态） |

旧工具名 `compiler_intake_prepare/save` 和 `compiler_plan_prepare/save` 在过渡期保留为别名。

### 4.2 MCP 前端不覆盖

Design Space Discovery 开始后进入 Compiler Core。

**判断准则**：MCP 前端只覆盖"需要 Agent 理解设计意图并做出结构性判断"的阶段。一旦进入"按照已形成的 Skill Graph 逐域执行"的阶段，就是 Compiler Core。

### 4.3 MCP 后端（证据判定层）

保持 Phase 10 定位不变。新增 3 个 Run 治理工具：
- `evidence_create_batch`
- `evidence_compare_runs`
- `evidence_promote_run`

### 4.4 工具总数

Phase 10: 42 -> Phase 11: 47（重命名 4 个，新增 5 个）

---

## 5. 与 Phase 10 的兼容策略

### 5.1 Session 版本化

- `session_version: "1.0"` -> Phase 10 五阶段管线
- `session_version: "2.0"` -> Phase 11 新主链
- 缺失 session_version 字段 -> 视为 "1.0"

### 5.2 Compatibility Adapter

放在 `Compiler/pipeline/pipeline_orchestrator.py` 层。根据 session_version 选择不同的 stage map 和 artifact map。不做产物格式转换。

### 5.3 旧 Schema 保留

`gdd_projection.schema.json`、`planner_output.schema.json`、`reviewed_handoff_v2.schema.json` 保留不删。

---

## 6. 核心设计原则

1. **Skill-First**：Skill 是主轴，不是附属层
2. **Constraint 不可违背**：Constraint Field 在整个管线中保持不变
3. **创造性在正确阶段发生**：Design Space Discovery + Realization，不是执行前随机变化
4. **创造性不退化为枚举**：Agent 发现维度、生成方向，不是从预设列表中选
5. **Baseline 是正式公民**：不只是 checklist，进入编译主链
6. **C++ 为主**：核心逻辑 C++，Blueprint 为薄层承载
7. **Run 隔离**：每轮生成独立存储，支持比较和吸收
8. **GDD-First 命名**：GDD 显式命名 > GDD 风格 > 项目规范 > 默认
