# TASK 04 Evidence — Phase 11 第一批 Schema 与 Example 校验

日期：2026-04-15

## 任务范围

- 新增 Phase 11 第一批 7 个 draft-07 Schema：
  - [root_skill_contract.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/root_skill_contract.schema.json)
  - [clarification_gate_report.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/clarification_gate_report.schema.json)
  - [skill_graph.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/skill_graph.schema.json)
  - [design_space_report.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/design_space_report.schema.json)
  - [realization_candidates.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/realization_candidates.schema.json)
  - [converged_realization_pack.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/converged_realization_pack.schema.json)
  - [skill_fragment_v2.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/skill_fragment_v2.schema.json)
- 新增 7 个 Monopoly 上下文 example：
  - [phase11_root_skill_contract.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_root_skill_contract.example.json)
  - [phase11_clarification_gate_report.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_clarification_gate_report.example.json)
  - [phase11_skill_graph.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_skill_graph.example.json)
  - [phase11_design_space_report.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_design_space_report.example.json)
  - [phase11_realization_candidates.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_realization_candidates.example.json)
  - [phase11_converged_realization_pack.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_converged_realization_pack.example.json)
  - [phase11_skill_fragment_v2.example.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/examples/phase11_skill_fragment_v2.example.json)
- 更新 [validate_examples.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/validation/validate_examples.py)，将 7 个 Phase 11 example 接入显式 schema 映射。
- 更新 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 的 TASK 04 与 M3 状态。

## 实现摘要

- 7 个 Schema 均使用 draft-07，且不使用 `$id`，避免远程解析。
- Schema 只约束核心结构：产物版本、来源、关键数组/对象、必要枚举和 metadata。
- Root Skill Contract 覆盖 constraint_fields、variant_fields、baseline_capabilities、gameplay_capabilities。
- Clarification Gate 覆盖 4 档 decision、risk_level、provisional 与 fast_mode 相关字段。
- Skill Graph 覆盖 nodes、edges、dependency/coupling/convergence_order。
- Discovery / Candidates / Convergence 三个 Schema 分别覆盖设计维度、候选方向、收敛选择。
- Skill Fragment v2 在 v1 fragment 主体基础上增加 `design_decision_log`。

## 验证结果

文件存在性验证：

```text
TASK04_SCHEMA_FILE_CHECK=passed
NEW_SCHEMA_COUNT=7
NEW_EXAMPLE_COUNT=7
OLD_SCHEMA_RETAINED_COUNT=6
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

v2 Stage 1 prepare 烟测：

```text
TASK04_V2_STAGE1_PREPARE=passed
```

语法验证：

```text
python -m py_compile Plugins/AgentBridge/Scripts/validation/validate_examples.py
```

执行命令：

```powershell
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

## 结论

TASK 04 验收标准已满足。M3 已完成：Phase 11 第一批 7 个 Schema 与 7 个 example 已创建并通过 strict 校验，旧 v1 Schema 全部保留。
