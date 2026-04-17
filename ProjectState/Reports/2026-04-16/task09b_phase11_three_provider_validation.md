# TASK 09B 三路 Generator 验证报告

状态：✅ 当前阶段已完成

对应任务：
- [task.md:593](/D:/UnrealProjects/Mvpv4TestCodex/task.md:593)

## 本轮结论

`TASK 09B` 现已按**当前阶段正式口径**收口完成。

本轮最终采用的结论是：

1. `MCP Agent` 路径：通过，并且已补齐 Stage 4 sidecar 持久化与同输入双跑差异验证
2. `Heuristic Fallback` 路径：通过
3. `LLM Internal` 路径：已完成接入与严格诊断，但根据当前治理决定，**暂缓继续测试**，待后续 `llm_client` 框架升级后重开

也就是说，`TASK 09B` 当前不是“三路都完全验收完成”这个口径，而是：

- `MCP Agent` 与 `Heuristic Fallback` 两条当前主线已完成正式验收
- `LLM Internal` 已形成有效阻塞诊断，并被明确移出本轮继续试跑范围
- 因此本任务可以结束，后续主线可进入 `TASK 10`

---

## 本轮修复内容

### 1. LLMProvider 输出约束强化

涉及文件：
- [llm_client.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/llm_client.py)
- [agent_protocol.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/agent_protocol.py)

本轮已实现：
- 更强的 JSON-only prompt
- 空响应不再被视为可接受结果
- parse 失败后增加 schema-aware repair
- OpenAI-Compatible 根路径自动归一化到 `/v1`
- OpenAI-Compatible 的字符串响应不再被吞成空串
- HTML 页面响应会作为错误线索暴露给上层

关键位置：
- [agent_protocol.py:404](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/agent_protocol.py:404)
- [agent_protocol.py:469](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/agent_protocol.py:469)
- [agent_protocol.py:513](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/agent_protocol.py:513)
- [llm_client.py:65](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/llm_client.py:65)
- [llm_client.py:123](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/llm_client.py:123)

### 2. Stage 4 验收口径强化

涉及文件：
- [agent_protocol.py:231](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/agent_protocol.py:231)
- [domain_skill_runtime.py:715](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py:715)
- [pipeline_orchestrator.py:672](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py:672)

本轮已实现：
- 任意 `parse_error` 不再算验收通过
- `discovery_dimensions` 不能为空
- `candidates` 不能为空
- `converged_choices` 不能为空
- discovery-capable fragment 的 `selected_realization` 不能为空
- Stage 4 至少要有部分 discovery-capable fragment 的 `design_decision_log` 非空
- Stage 4 prepare 现在会在验收失败时直接返回 `stage_generation_failed`

---

## 旧 LLM Internal 结果已失效

原先用于宣称 `LLM Internal` 通过的 run：
- [session.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-085301-c9aa/session.json)
- [design_space_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-085301-c9aa/design_space_report.json)
- [realization_candidates.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-085301-c9aa/realization_candidates.json)
- [converged_realization_pack.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-085301-c9aa/converged_realization_pack.json)

重新核对结论：
- `design_space_report.entries`：8/8 为 `parse_error`
- `realization_candidates.entries`：8/8 为 `parse_error`
- `converged_realization_pack.entries`：8/8 为 `parse_error`
- 对应 fragment 中 `selected_realization` 为空，`design_decision_log` 为空

因此，这个 run 只能证明“provider 路由走到了 llm”，不能证明“LLM Internal 生成物通过验收”。

---

## 新的严格重跑结果

严格重跑 run：
- [session.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-090933-95c2/session.json)
- [root_skill_contract.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-090933-95c2/root_skill_contract.json)
- [clarification_gate_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-090933-95c2/clarification_gate_report.json)
- [skill_graph.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-090933-95c2/skill_graph.json)

结果：
- Stage 1-3：通过
- Stage 4：**失败**
- `prepare_stage(session, 4)` 返回 `stage_generation_failed`

失败原因：
- `LLM/MCP Discovery 验收失败：design_space entries 为空`
- `LLM/MCP Candidates 验收失败：candidates entries 为空`
- `LLM/MCP Convergence 验收失败：converged entries 为空`
- `Stage 4 验收失败：所有 discovery-capable fragment 的 selected_realization 均为空`
- `Stage 4 验收失败：所有 discovery-capable fragment 的 design_decision_log 均为空`

这说明新的严格口径已经生效，而且不会再把“空内容 / parse_error / 空 fragment”误判成通过。

---

## 当前 provider 侧真实问题

本轮修复后，OpenAI 风格 relay 路径不再返回首页 HTML，而是暴露出了真实 provider 错误：

- `base_url` 已从根路径归一化到 `https://www.packyapi.com/v1`
- 当前 probe 返回：
  - `503 model_not_found`
  - `分组 cc-sale 下模型 claude-sonnet-4-6 无可用渠道`

也就是说，当前 `LLM Internal` 的剩余阻塞已经从“客户端吞掉错误”变成了**真实的 provider / model 可用性问题**。

---

## 最新严格版 save 尝试

用户要求将严格版 `LLM Internal` 直接跑到 `save` 完成，因此本轮继续复用以下 run：

- [session.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-092018-f6b8/session.json)
- [llm_config.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Config/llm_config.yaml)

当前有效配置（隐去密钥）：
- `provider = "openai"`
- `model = "claude-sonnet-4-6"`
- `base_url = "https://www.packyapi.com/v1"`

结果：
- `prepare_stage(session, 4)` 再次返回 `stage_generation_failed`
- 因为 `prepare` 没有通过，本轮 **没有进入 save 落盘**
- `session.json` 仍停留在 `current_stage = 4`、`status = "pending"`

这次失败与上一轮“严格验收已收紧”的结论一致，但更具体地说明了一点：
- 问题不在 `save` 路径
- 问题出在当前 relay 配置下，真实 LLM Discovery 调用直接失败，导致 Stage 4 聚合产物为空

从本轮返回的 trace 可归纳出两条关键事实：
- `generator_provider_type` 仍然是 `llm`
- 首批 discovery 节点直接收到 provider 侧 `503 model_not_found`

因此，当前不能把这条 run 宣称为“严格版 LLM Internal save 完成”。

### 用户修改配置后的再次重试

用户随后将 [llm_config.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Config/llm_config.yaml) 改为：

- `provider = "anthropic"`
- `model = "MiniMax M2.7"`
- `base_url = "https://www.packyapi.com"`

在这组新配置下，再次对同一条 run 执行严格版 `prepare_stage(session, 4)`，结果仍然是：

- 一次长时间重试最终在外层命令超时
- 超时前没有写出任何新的 Stage 4 主产物，也没有生成 `stage4_agent_traces/`
- `session.json` 仍停留在 Stage 4 pending

最新一次重试说明了一个更具体的事实：
- 当前问题不只是 `openai` / `anthropic` 客户端分支差异
- 当前 relay + model 组合表现出**明显不稳定性**：有时能回结构化内容但无法稳定通过严格 Stage 4，有时直接回 `model_not_found`，有时则长时间无返回直到超时
- 因此截至本报告更新时，仍不能把这条 run 宣称为“严格版 LLM Internal save 完成”

---

## 仍然有效的两条路径

### MCP Agent

证据：
- [session.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-083638-92d3/session.json)
- [mcp_agent_dual_run_variation_test.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/mcp_agent_dual_run_variation_test.md)
- [mcp_agent_dual_run_variation_test.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/mcp_agent_dual_run_variation_test.json)

状态：
- 有效
- `generator_provider = "mcp_agent"`
- `is_promotable = true`

补充说明：
- 已补齐 `stage4_mcp_agent_sidecar/` 持久化
- 已完成同输入双跑，确认 `Discovery` / `Candidates` / `Convergence` / `Fragment` 的中间产物现在可审计、可对比
- 双跑已观察到明确差异：
  - run A：`棋盘视觉尺度 / 角格地标强调 / 路径阅读性`
  - run B：`棋盘俯视高度 / 角格身份风格 / 移动引导语言`

### Heuristic Fallback

证据：
- [session.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260416-083716-1968/session.json)

状态：
- 有效
- `generator_provider = "heuristic_fallback"`
- `is_promotable = false`

---

## 统一校验

本轮已执行：
- `py_compile` 通过
- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` 通过

说明：
- 本轮补充了 `MCP Agent` sidecar 持久化与双跑差异测试，schema example 仍保持通过。

---

## LLM Internal 当前处理口径

`LLM Internal` 没有在技术上“通过”，这一点仍然成立。

但当前正式治理口径已经调整为：

- 不再继续追加 `LLM Internal` 试跑
- 保留现有严格诊断证据
- 等 `llm_client` 框架升级完成后，再单独重开严格回归验收

对应证据：
- [stage4_candidates_prompt_vs_provider_diagnostic.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic.md)
- [task09b_llm_internal_pause_sync.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/task09b_llm_internal_pause_sync.md)

---

## 最终判断

当前 `TASK 09B` 的正式结论应为：

- `MCP Agent`：通过
- `Heuristic Fallback`：通过
- `LLM Internal`：暂停继续测试，后续在 `llm_client` 框架升级后重开

因此：
- [task.md:595](/D:/UnrealProjects/Mvpv4TestCodex/task.md:595) 应更新为“✅ 当前阶段已完成”
- 里程碑 `M6` 也应同步更新为“✅ 当前阶段已完成”

下一步：
- 进入 `TASK 10`
- 后续如进入 `llm_client` 框架升级任务，再单独恢复 `LLM Internal` 严格回归
