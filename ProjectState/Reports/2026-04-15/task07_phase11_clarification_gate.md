# TASK 07 Evidence — Clarification Gate 执行逻辑与 provisional 传播

日期：2026-04-15

## 任务范围

- 新增 [clarification_gate.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/stages/clarification_gate.py)，实现 Phase 11 Stage 2 Clarification Gate 真实生成逻辑。
- 更新 [pipeline_orchestrator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py)，使 v2 Stage 2 `prepare_stage` 返回真实生成的 `clarification_gate_report`，并把 provisional 传播字段写入 `input_context`。
- 扩展 [clarification_gate_report.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/clarification_gate_report.schema.json)，补齐 `provisional_items`、`blocking_items`、`items_by_decision_summary`、`downstream_propagation_contract`。
- 更新 [phase11_clarification_gate_report.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_clarification_gate_report.example.json)。
- 生成真实产物：[clarification_gate_report.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260415-191500-a707/clarification_gate_report.json)。
- 更新 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 的 TASK 07 状态与 M5 进度。

## 实现摘要

- Clarification Gate 现在会真实消费 Root Skill Contract 的 `clarification_markers`、`variant_fields`、`baseline_capabilities`。
- Monopoly GDD 场景下输出 7 条 item，覆盖 4 档决策：
  - `accept_as_explicit`
  - `accept_with_safe_default`
  - `send_to_design_space_discovery`
  - `clarification_required`
- 已实现 low / medium / high / critical 风险分级。
- 已实现 high / critical 保护规则：
  - high 保持 `clarification_required`
  - critical 进入 `blocking_items`，不会被 `fast_mode` 自动默认
- 已输出 `provisional_items`，并在 `downstream_propagation_contract` 中显式规定后续阶段的消费字段：
  - `design_decision_log[].provisional = true`
  - `build_steps[].execution_hints.contains_provisional = true`
  - `reviewed_handoff_v3.provisional_items[]`
- `pipeline_orchestrator.py` 的 Stage 2 `input_context` 已注入：
  - `clarification_items`
  - `clarification_items_by_decision`
  - `provisional_items`
  - `blocking_items`
  - `downstream_propagation_contract`

## 验证结果

语法验证：

```text
PY_COMPILE_OK
```

Stage 专项验证：

```text
STAGE1_STATUS=ready_for_agent
STAGE1_SAVE=saved
STAGE2_STATUS=ready_for_agent
STAGE2_NAME=clarification_gate
STAGE2_ITEMS=7
STAGE2_DECISIONS={"accept_as_explicit": 1, "accept_with_safe_default": 2, "clarification_required": 2, "send_to_design_space_discovery": 2}
STAGE2_PROVISIONAL=2
CTX_HAS_PROVISIONAL=True
CTX_HAS_DOWNSTREAM=True
```

critical 风险保护验证：

```text
CRITICAL_ITEMS=1
CRITICAL_DECISION=clarification_required
CRITICAL_BLOCKING=True
BLOCKING_ITEMS=1
PROVISIONAL_ITEMS=0
```

MCP 工具链验证：

```text
MCP_CREATE=success
MCP_ROOT_PREPARE=success
MCP_ROOT_SAVE=success
MCP_CLAR_PREPARE=success
MCP_CLAR_SAVE=success
REPORT_PATH=D:\UnrealProjects\Mvpv4TestCodex\ProjectState\runs\run-20260415-191500-a707\clarification_gate_report.json
RETained=2
PROVISIONAL=2
DECISION_TYPES=4
```

严格示例验证：

```text
Checked examples       : 19
Passed                 : 19
Failed                 : 0
Reference-only skipped : 0
Unmapped examples      : 0
Missing schema targets : 0

[SUCCESS] 全部 example 校验通过，本地校验链正常。
```

## 关键验收项

- `clarification_gate_report.json` 非空：通过。
- items 覆盖 Monopoly GDD 中的缺失或含糊项：通过。
- 4 档决策至少覆盖 2 种实际结果：通过，当前覆盖 4 种。
- high / critical 不被 `fast_mode` 自动默认：通过。
- `provisional_items` 可被下游读取：通过，Stage 2 `input_context` 已注入。
- Fragment / Build IR / Handoff 的 provisional 传播字段：本任务已通过 `downstream_propagation_contract` 与 `input_context` 完成接口约定，实际消费行为将在 TASK 09、TASK 10、TASK 11 继续验收。
- `validate_examples.py --strict` 通过：通过。

## 结论

TASK 07 当前范围已完成。M5 仍未完成，因为 Skill Graph Planning（TASK 08）尚未执行。
