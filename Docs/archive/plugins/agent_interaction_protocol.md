# AGENT_UE5 Agent 交互协议
> 原始来源：Docs/History/Phase11_Design_Pack/14_Agent_Interaction_Protocol.md

## 1. 定位

本文档定义 Stage 4（Domain Skill Runtime）中 Agent 的调用模型。它回答：

- Discovery / Candidates / Convergence 三阶段**由谁执行、怎么执行**
- Generator 和 Evaluator 的职责划分
- 每阶段的输入、输出、质量门控和重试策略
- 与 SkillTemplates 中 prompt 文件的映射关系

本文档是 `07_Design_Space_Discovery_and_Realization.md`（定义三阶段产物结构）和 `08_Skill_Graph_and_Domain_Skill.md`（定义 Domain Skill 四重职责）的执行层补充。

---

## 2. 交互模型：结构化多阶段 + Evaluator 门控（模型 D）

### 2.1 总体结构

对每个 `allows_design_space_discovery = true` 且非 `fast_mode` 的 Skill Instance，Stage 4 Runtime 按以下结构执行：

```
Phase 1: Discovery
  Context Bundle ──→ Generator(Discovery) ──→ draft
                                                ↓
                                         Evaluator(Discovery)
                                           ↓         ↓
                                         pass      fail + feedback
                                          ↓            ↓
                                     进入 Phase 2   Generator(重试, 注入 feedback)
                                                    最多 2 轮重试

Phase 2: Candidates
  design_space_report + Context ──→ Generator(Candidates) ──→ draft
                                                               ↓
                                                        Evaluator(Candidates)
                                                          ↓         ↓
                                                        pass      fail + feedback
                                                         ↓            ↓
                                                    进入 Phase 3   Generator(重试)

Phase 3: Convergence
  realization_candidates + Context ──→ Generator(Convergence) ──→ draft
                                                                    ↓
                                                             Evaluator(Convergence)
                                                               ↓         ↓
                                                             pass      fail + feedback
                                                              ↓            ↓
                                                         输出 + 人类确认点  Generator(重试)
```

### 2.2 核心设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Generator 和 Evaluator 使用同一个 LLM | 是 | 当前阶段可行，通过 prompt 差异化实现角色分离 |
| 每阶段最大重试次数 | 2 轮（含首次共 3 次调用） | 超过 3 次通常是 prompt 问题不是 Agent 能力问题 |
| 重试耗尽后行为 | 节点 failed，保留最后一次产物 + 全部 trace | 不 silent fallback 到启发式 |
| Generator 允许自由文本思考 | 是（extended thinking / scratchpad） | 纯 JSON 压力会让 Agent 跳过深度思考 |

---

## 3. Context Bundle（结构化输入包）

Generator 的输入不是单一 JSON，而是分层的 Context Bundle：

```json
{
  "context_bundle": {
    "structural": {
      "root_skill_contract": "...(与本域相关的子集)",
      "clarification_gate_results": "...(本域相关项)",
      "skill_graph_node": {
        "current_node": "...(当前节点定义)",
        "dependency_nodes": "...(已完成的依赖节点及其产物摘要)",
        "coupling_nodes": "...(耦合节点及其状态/已收敛方向)"
      },
      "constraint_fields": "...(本域锁定字段及值)",
      "variant_fields": "...(本域可变字段 + bounds)"
    },
    "semantic": {
      "gdd_raw_excerpt": "...(GDD 中与本域相关的原文段落，保留原始措辞)",
      "gameplay_feel_targets": ["fast-paced simplified monopoly", "casual party game"],
      "design_tensions": ["simplified board vs strategic depth", "elimination vs engagement"],
      "coupled_domain_summaries": "...(耦合域已收敛方向摘要，若已完成)"
    },
    "prior_feedback": null
  }
}
```

### 3.1 两层分离的原因

| 层 | 性质 | Generator 的使用方式 |
|----|------|-------------------|
| `structural` | 硬约束，程序可校验 | 必须遵守，不可违反 |
| `semantic` | 软信号，创造性推理素材 | 用于启发设计思维，不是硬约束 |

### 3.2 `prior_feedback` 字段

- 首次调用时为 `null`
- 重试时填入 Evaluator 的 `specific_feedback`（见 §5）
- Generator 重试时必须**针对 feedback 做出响应**，不能忽略

### 3.3 input_selector 的角色

SkillTemplate 中的 `input_selector.yaml` 定义从全局产物中提取哪些字段构成 Context Bundle。不同 domain 的 input_selector 不同——board_topology 需要 GDD 中棋盘相关段落，turn_loop 需要回合规则相关段落。

---

## 4. Generator 调用协议

### 4.0 硬约束：Generator 必须由 LLM 驱动（Prompt-First 原则）

**Generator 的设计知识唯一来源是 SkillTemplate 的 prompt 文件**（`system_prompt.md`、`domain_prompt.md`），不是代码中的硬编码算法。代码只负责：加载 prompt、注入 Context Bundle、调用 LLM、解析输出。

这意味着：

1. **代码中不允许硬编码"发现什么维度""生成什么候选""如何收敛"**——这些全由 LLM 根据 prompt + Context Bundle 产出。
2. **确定性启发式引擎（`*_fallback.py`）仅作为显式退化路径**，适用于 CI、测试、fast_mode 等无 LLM 的场景。
3. **使用 heuristic fallback 的 run 自动标记 `promotable: false`**——确定性产物不代表真正的设计探索，不可被 promote 为项目基线。
4. **Stage 4 默认拒绝在无 LLM 的情况下执行**，除非 session 显式设置 `allow_heuristic_fallback: true`。

Provider 三条路径：

| 路径 | 条件 | 行为 | 产物标记 |
|------|------|------|---------|
| **MCP Agent**（主路径） | Agent 通过 `compiler_stage4_node_prepare` / `save` 交互 | Agent 本身即 LLM，prepare 返回 prompt + Context Bundle，Agent 做创造性生成，save 校验存储 | `generator_type: "mcp_agent"`, `promotable: true` |
| **LLM Internal** | `llm_client` 已配置，pipeline 内嵌调用 | LLMProvider 驱动 Generator（代码已实现，见 `agent_protocol.py` LLMProvider） | `generator_type: "llm"`, `promotable: true` |
| **Heuristic Fallback** | 无 LLM 且 `allow_heuristic_fallback: true` | `*_fallback.py` 确定性退化运行 | `generator_type: "heuristic_fallback"`, `promotable: false` |

**MCP Agent 是当前推荐的主路径**：调用 MCP 工具的 Agent（Claude）本身就是 LLM，不需要在 pipeline 内部再嵌一层 LLM API。prepare 返回 SkillTemplate prompt 和 Context Bundle，Agent 据此完成创造性生成，save 接收输出并校验。这使得 Stage 4 的发散创造能力完全由 Agent 驱动。

LLM Internal 路径的 `LLMProvider` 代码已完整实现（prompt 组装、LLM 调用、JSON 解析、格式修复），位于 `agent_protocol.py:399-520`。需要提供一个实现 `call(messages) -> str` 接口的 `llm_client` 实例即可启用。适用于 pipeline 自动化运行（无人交互）场景，如 batch processing 或框架内嵌其他 Agent。

无 LLM 且 `allow_heuristic_fallback: false` 时 → **Stage 4 拒绝执行**，返回 `status: "refused"`。

### 4.1 调用流程

```
1. Runtime 从 input_selector 构建 context_bundle
2. Runtime 加载 system_prompt.md + domain_prompt.md
3. Runtime 将 context_bundle 注入 prompt
4. 调用 LLM（允许 extended thinking）
5. 解析 LLM 输出为 JSON
6. 对 JSON 做 schema 校验（output_schema.json）
7. schema 校验失败 → 将错误回灌给 LLM 做格式修复（不算重试轮次）
8. schema 校验通过 → 交给 Evaluator
```

### 4.2 Generator Prompt 结构

```
[system_prompt.md]                  — 角色定义 + 通用约束
[domain_prompt.md]                  — 领域专属指导
[context_bundle.structural]         — 硬约束注入
[context_bundle.semantic]           — 软信号注入
[context_bundle.prior_feedback]     — Evaluator 反馈（重试时）
[output_schema 要求]                — 输出格式要求
```

Generator 被允许在结构化输出前进行自由文本推理（scratchpad / extended thinking）。这段推理过程记入 trace 但不计入正式产物。

### 4.3 Schema 修复 vs 质量重试

两种失败是不同的：

| 失败类型 | 处理方式 | 是否消耗重试次数 |
|---------|---------|--------------|
| JSON 解析失败 / schema 校验失败 | 将错误信息回灌 LLM 做格式修复 | **否**（格式修复最多 2 次，独立计数） |
| Evaluator 判定质量不合格 | 将 specific_feedback 注入 prior_feedback 重试 | **是** |

### 4.4 MCP Agent 交互流程

MCP Agent 路径通过两个 MCP 工具实现 prepare/save 交互循环：

```
对每个 Skill Instance 的每个 phase (discovery → candidates → convergence):

1. Agent 调用 compiler_stage4_node_prepare(session_path, node_id, phase)
   ← 返回:
     - status: "ready"
     - prompts: { system_prompt, domain_prompt, evaluator_prompt }
     - context_bundle: { structural, semantic }
     - instructions: "阅读 prompt，结合 context_bundle 生成..."
     - output_hint: { expected_fields, output_schema_summary }

2. Agent 阅读 prompt + context_bundle，做创造性推理和生成

3. Agent 调用 compiler_stage4_node_save(session_path, node_id, phase, output)
   → output = Agent 生成的 JSON（符合 output_schema）
   ← 返回:
     - status: "saved" / "validation_failed"
     - metadata: { generator_type: "mcp_agent", promotable: true }
     - 若 convergence 完成: 自动触发 Fragment 生成

4. 若 save 返回 validation_failed，Agent 根据 errors 修正后重新 save
```

**关键区别**：MCP Agent 路径中 Evaluator 由 Agent 自行执行（Agent 已持有 evaluator_prompt），而非 pipeline 内部调用。Agent 可以在 save 前自行做质量评审，也可以直接提交由 schema 校验兜底。

**MCP 工具定义**（见 `MCP/tool_definitions.py`）：
- `compiler_stage4_node_prepare`：参数 `session_path`, `node_id`, `phase`, `node_state`（可选）
- `compiler_stage4_node_save`：参数 `session_path`, `node_id`, `phase`, `output`, `node_state`（可选）

---

## 5. Evaluator 调用协议

### 5.1 Evaluator 的角色

Evaluator 不是格式检查器（那是 schema 校验的职责），而是**设计质量评审员**。它检查 Generator 的产出是否体现了真正的设计思考。

### 5.2 各阶段 Evaluator 质量维度

#### Phase 1: Discovery Evaluator

| 维度 | 检查内容 | 不合格信号 |
|------|---------|----------|
| **维度覆盖** | 是否覆盖了当前域的主要设计维度 | 遗漏了 GDD 提及的维度 |
| **非显然性** | 是否发现了 GDD 未直接提及但逻辑上存在的维度 | 所有维度都是 GDD 原文直接翻译 |
| **Constraint 正确性** | locked_dimensions 是否与 Root Skill Contract 一致 | 把 Constraint 标为 Variant 或反之 |
| **耦合识别** | 是否识别了跨域耦合 | 忽略了 Skill Graph 中标注的 coupling 边 |
| **粒度合理性** | 维度粒度是否适当（通常 3-8 个/域） | 维度过粗（< 2）或过细（> 10） |

#### Phase 2: Candidates Evaluator

| 维度 | 检查内容 | 不合格信号 |
|------|---------|----------|
| **真实差异** | 候选之间是否有本质区别 | 候选只是措辞不同的同一方案 |
| **Trade-off 真实性** | pros/cons 是否触及真实工程/设计矛盾 | 泛泛的"更好/更差"，不涉及具体取舍 |
| **Bounds 合规** | 所有候选是否满足 Variant bounds | 候选违反 must_satisfy 或触犯 must_not |
| **数量充分** | 每个维度是否有 >= 2 个候选 | 某维度只有 1 个候选 |
| **复杂度评估** | estimated_complexity 是否合理 | 明显低估或高估实现难度 |

#### Phase 3: Convergence Evaluator

| 维度 | 检查内容 | 不合格信号 |
|------|---------|----------|
| **Rationale 深度** | 选择理由是否具体、可操作 | "这个更好"而非"因为 X 与 gameplay feel target Y 更匹配" |
| **Rejection 质量** | 拒绝理由是否具体 | "不够好"而非指出具体缺陷 |
| **跨维度一致性** | 选中候选之间是否兼容 | 维度 A 选了紧凑布局，维度 B 选了需要大空间的方案 |
| **Provisional 正确性** | provisional 标记是否正确传播 | 使用了 provisional 值但未标记 |

### 5.3 Evaluator 输出结构

```json
{
  "evaluation_result": {
    "phase": "discovery",
    "overall_verdict": "pass | revise | fail",
    "scores": {
      "dimension_coverage": { "score": 0.8, "verdict": "pass" },
      "non_obviousness": { "score": 0.4, "verdict": "fail" },
      "constraint_correctness": { "score": 1.0, "verdict": "pass" },
      "coupling_awareness": { "score": 0.8, "verdict": "pass" },
      "granularity": { "score": 0.9, "verdict": "pass" }
    },
    "specific_feedback": [
      "GDD SS3.2 描述了租金递增机制，但维度列表中没有涉及经济曲线相关的设计维度",
      "所有维度都直接来自 GDD 条目，缺少'GDD 未提及但逻辑上必须决策'的维度，例如：玩家破产后的观战/退出体验"
    ],
    "retry_hint": "focus_on_implicit_dimensions"
  }
}
```

### 5.4 三级判定

| verdict | 含义 | 后续动作 |
|---------|------|---------|
| **pass** | 所有维度合格 | 进入下一阶段 |
| **revise** | 部分维度不合格但可修复 | 注入 feedback 重试 |
| **fail** | 存在不可修复的结构性问题 | 如果已耗尽重试次数，节点 failed |

合格阈值：所有维度 score >= 0.6 且无任何 verdict = "fail" 的维度。

### 5.5 Evaluator Prompt 结构

```
[evaluator_prompt.md]               — 评审员角色定义 + 质量维度定义
[context_bundle.structural]          — 同 Generator 收到的硬约束（用于验证）
[generator_output]                   — Generator 本次产出
[phase_specific_criteria]            — 当前阶段的评审标准
```

Evaluator 收到与 Generator 相同的 structural context，这样它可以验证 Generator 是否正确遵守了约束。

---

## 6. 与 SkillTemplates 的映射

### 6.1 文件职责映射

```
SkillTemplates/{domain}/{skill_name}/
  manifest.yaml           → 元数据 + 重试策略覆盖 + 阈值覆盖
  system_prompt.md        → Generator 系统 prompt（角色 + 通用约束）
  domain_prompt.md        → Generator 领域 prompt（领域专属指导 + 设计启发）
  evaluator_prompt.md     → Evaluator 系统 prompt（质量维度 + 评审标准）
  input_selector.yaml     → Context Bundle 字段选择规则
  output_schema.json      → Generator 输出的 schema（用于格式校验，非质量评审）
```

### 6.2 evaluator_prompt.md 的新职责

Phase 10 中 evaluator_prompt.md 主要做格式/一致性检查。Phase 11 中它升级为**设计质量评审员**：

| Phase 10 职责 | Phase 11 新增职责 |
|--------------|-----------------|
| 检查 Fragment 格式是否合规 | 检查 Discovery 维度覆盖度和非显然性 |
| 检查 Constraint 值是否一致 | 检查 Candidates 之间的真实差异 |
| — | 检查 Trade-off 是否触及真实矛盾 |
| — | 检查 Convergence rationale 深度 |
| — | 输出结构化 feedback 用于 Generator 重试 |

### 6.3 manifest.yaml 中的可覆盖参数

不同 domain 可以在 manifest.yaml 中覆盖默认协议参数：

```yaml
agent_protocol:
  max_retries: 2                    # 默认 2，可覆盖
  pass_threshold: 0.6               # 默认 0.6，可覆盖
  format_repair_max: 2              # schema 修复最大次数
  allow_scratchpad: true            # 是否允许自由文本思考
  evaluator_dimensions:             # 可添加域专属评审维度
    - name: "physics_plausibility"
      description: "候选的物理表现是否在 UE5 中可实现"
      weight: 0.8
```

---

## 7. Trace 与审计

### 7.1 每次 LLM 调用必须保留的 Trace

```json
{
  "trace_id": "trace-skill-board-discovery-gen-1",
  "skill_instance_id": "skill-board-topology",
  "phase": "discovery",
  "role": "generator",
  "attempt": 1,
  "timestamp": "2026-04-15T14:31:05Z",
  "input": {
    "system_prompt_hash": "sha256:...",
    "context_bundle_hash": "sha256:...",
    "prior_feedback": null
  },
  "output": {
    "raw_response": "...(LLM 原始输出，含 scratchpad)",
    "parsed_json": "...(解析后的 JSON)",
    "schema_valid": true,
    "schema_errors": []
  },
  "token_usage": {
    "input_tokens": 2100,
    "output_tokens": 950
  }
}
```

### 7.2 Trace 落盘位置

```
ProjectState/runs/{run_id}/stage4_agent_traces/
  {skill_instance_id}/
    discovery_gen_1.json
    discovery_eval_1.json
    discovery_gen_2.json      # 重试
    discovery_eval_2.json     # 重试
    candidates_gen_1.json
    candidates_eval_1.json
    convergence_gen_1.json
    convergence_eval_1.json
```

Trace 属于审计 sidecar，不属于 schema 主产物，不进入 promoted_artifacts。

### 7.3 失败时的 Trace 保留

节点 failed 时，保留：
- 最后一次 Generator 的产出（即使未通过 Evaluator）
- 所有 Evaluator 的 feedback
- 完整的重试历史
- failure_reason（`stage4_retry_exhausted` / `stage4_provider_missing` / `stage4_schema_validation_failed`）

---

## 8. 调用量估算

### 8.1 单个 discovery-capable Skill Instance

| 阶段 | 最少调用 | 最多调用（含重试） |
|------|---------|-----------------|
| Discovery | 2（1 Gen + 1 Eval） | 6（3 Gen + 3 Eval） |
| Candidates | 2 | 6 |
| Convergence | 2 | 6 |
| **小计** | **6** | **18** |

格式修复调用另计（每阶段最多 2 次，不占重试额度）。

### 8.2 整个 Skill Graph

假设 12 个 Skill Instance，其中 6 个 discovery-capable：

| 场景 | 调用总数 |
|------|---------|
| 最优（全部首次通过） | 36 |
| 典型（30% 需要 1 次重试） | ~47 |
| 最差（全部耗尽重试） | 108 |

presence_only 节点不触发 Agent 调用，直接生成最小 Fragment。

---

## 9. fast_mode 下的行为

fast_mode 下整个 Agent 交互协议被跳过：

| 组件 | MCP Agent 模式 | LLM Internal 模式 | fast_mode |
|------|---------------|-------------------|-----------|
| Generator 调用 | Agent 通过 prepare/save 交互 | pipeline 内部 LLM 调用 | **跳过** |
| Evaluator 调用 | Agent 自行评审（持有 evaluator_prompt） | pipeline 内部 LLM 调用 | **跳过** |
| Trace 记录 | save 时记录 | 完整记录 | 不产生 |
| Fragment 来源 | Agent 收敛结果 | Agent 收敛结果 | 默认/最简实现（heuristic fallback） |
| `generator_type` 标记 | `"mcp_agent"` | `"llm"` | `"heuristic_fallback"` |
| `promotable` | `true` | `true` | `false` |

这是 fast_mode 的**显式策略跳过**，不是 provider 缺失时的自动降级。三种路径在 metadata 中通过 `generator_type` 和 `promotable` 字段明确区分。

---

## 10. 与其他文档的关系

| 文档 | 关系 |
|------|------|
| `07_Design_Space_Discovery_and_Realization.md` | 定义三阶段的**产物结构**（schema），本文档定义**执行协议** |
| `08_Skill_Graph_and_Domain_Skill.md` | 定义 Domain Skill 的**四重职责**和 Runtime 口径，本文档定义 Stage 4 内部的 **Agent 调用细节** |
| `09_Run_Isolation_Compare_Promote.md` | 定义 `stage4_agent_traces/` 的存储位置和审计定位 |
| `12_Implementation_Taskbook.md` | 任务 2.4-2.7 的实施需遵循本协议 |
