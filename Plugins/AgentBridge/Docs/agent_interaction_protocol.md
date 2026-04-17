# Stage 4 Agent 交互协议

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/14_Agent_Interaction_Protocol.md

## 1. 定位

本文档定义 Stage 4（Domain Skill Runtime）中 Agent 的调用模型：
- Discovery / Candidates / Convergence 三阶段由谁执行、怎么执行
- Generator 和 Evaluator 的职责划分
- 每阶段的输入、输出、质量门控和重试策略
- 与 SkillTemplates 中 prompt 文件的映射关系

---

## 2. 交互模型：结构化多阶段 + Evaluator 门控

对每个 `allows_design_space_discovery = true` 且非 `fast_mode` 的 Skill Instance，Stage 4 Runtime 按 Discovery → Candidates → Convergence 三阶段执行，每阶段均有 Generator 生成 + Evaluator 门控。

### 2.1 核心设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| Generator 和 Evaluator 使用同一个 LLM | 是 | 通过 prompt 差异化实现角色分离 |
| 每阶段最大重试次数 | 2 轮（含首次共 3 次调用） | 超过 3 次通常是 prompt 问题 |
| 重试耗尽后行为 | 节点 failed，保留最后一次产物 + 全部 trace | 不 silent fallback 到启发式 |

---

## 3. Context Bundle（结构化输入包）

Generator 的输入分为两层：

| 层 | 性质 | Generator 的使用方式 |
|----|------|-------------------|
| `structural` | 硬约束，程序可校验 | 必须遵守，不可违反 |
| `semantic` | 软信号，创造性推理素材 | 用于启发设计思维 |

SkillTemplate 中的 `input_selector.yaml` 定义从全局产物中提取哪些字段构成 Context Bundle。

---

## 4. Generator — 三条 Provider 路径

### 4.0 Prompt-First 原则

Generator 的设计知识唯一来源是 SkillTemplate 的 prompt 文件。代码只负责：加载 prompt、注入 Context Bundle、调用 LLM、解析输出。代码中不允许硬编码"发现什么维度""生成什么候选""如何收敛"。

### 4.1 Provider 路径

| 路径 | 条件 | 行为 | 产物标记 |
|------|------|------|---------|
| **MCP Agent**（主路径） | Agent 通过 `compiler_stage4_node_prepare` / `save` 交互 | Agent 本身即 LLM，prepare 返回 prompt + Context Bundle | `generator_type: "mcp_agent"`, `promotable: true` |
| **LLM Internal** | `llm_client` 已配置 | pipeline 内嵌 LLM API 调用 | `generator_type: "llm"`, `promotable: true` |
| **Heuristic Fallback** | 无 LLM 且 `allow_heuristic_fallback: true` | `*_fallback.py` 确定性退化运行 | `generator_type: "heuristic_fallback"`, `promotable: false` |

无 LLM 且 `allow_heuristic_fallback: false` 时 → Stage 4 拒绝执行，返回 `status: "refused"`。

### 4.2 MCP Agent 交互流程

```
1. Agent 调用 compiler_stage4_node_prepare(session_path, node_id, phase)
   ← 返回 prompts + context_bundle + instructions + output_hint

2. Agent 阅读 prompt + context_bundle，做创造性推理和生成

3. Agent 调用 compiler_stage4_node_save(session_path, node_id, phase, output)
   ← 返回 status: "saved" / "validation_failed"
```

### 4.3 Schema 修复 vs 质量重试

| 失败类型 | 处理方式 | 消耗重试次数 |
|---------|---------|------------|
| JSON / schema 校验失败 | 错误信息回灌 LLM 做格式修复 | **否**（独立计数，最多 2 次） |
| Evaluator 判定质量不合格 | specific_feedback 注入 prior_feedback 重试 | **是** |

---

## 5. Evaluator 调用协议

Evaluator 不是格式检查器，而是**设计质量评审员**。

### 5.1 各阶段质量维度

- **Discovery**：维度覆盖、非显然性、Constraint 正确性、耦合识别、粒度合理性
- **Candidates**：真实差异、Trade-off 真实性、Bounds 合规、数量充分、复杂度评估
- **Convergence**：Rationale 深度、Rejection 质量、跨维度一致性、Provisional 正确性

### 5.2 三级判定

| verdict | 含义 | 后续动作 |
|---------|------|---------|
| **pass** | 所有维度合格 | 进入下一阶段 |
| **revise** | 部分不合格但可修复 | 注入 feedback 重试 |
| **fail** | 不可修复的结构性问题 | 如已耗尽重试次数，节点 failed |

合格阈值：所有维度 score >= 0.6 且无任何 verdict = "fail" 的维度。

---

## 6. 与 SkillTemplates 的映射

```
SkillTemplates/{domain}/{skill_name}/
  manifest.yaml           → 元数据 + 重试策略覆盖 + 阈值覆盖
  system_prompt.md        → Generator 系统 prompt
  domain_prompt.md        → Generator 领域 prompt
  evaluator_prompt.md     → Evaluator 系统 prompt（设计质量评审）
  input_selector.yaml     → Context Bundle 字段选择规则
  output_schema.json      → Generator 输出 schema
```

---

## 7. Trace 与审计

每次 LLM 调用保留 Trace，落盘位置：`ProjectState/runs/{run_id}/stage4_agent_traces/{skill_instance_id}/`。

Trace 属于审计 sidecar，不进入 promoted_artifacts。

---

## 8. fast_mode 下的行为

| 组件 | MCP Agent 模式 | LLM Internal 模式 | fast_mode |
|------|---------------|-------------------|-----------|
| Generator 调用 | Agent 通过 prepare/save 交互 | pipeline 内部 LLM 调用 | **跳过** |
| Evaluator 调用 | Agent 自行评审 | pipeline 内部 LLM 调用 | **跳过** |
| Fragment 来源 | Agent 收敛结果 | Agent 收敛结果 | heuristic fallback |
| `generator_type` | `"mcp_agent"` | `"llm"` | `"heuristic_fallback"` |
| `promotable` | `true` | `true` | `false` |
