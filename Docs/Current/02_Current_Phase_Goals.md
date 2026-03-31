# Phase 5 目标

> 文档版本：L1-Phase5-v1

## 本期目标

本期目标是从 Phase 4 的 Greenfield 自动生成链继续向前推进，把 Brownfield 所需的“基线理解 + 差量分析 + Contract 约束”真正落地：

1. 让 `project_state_intake.py` 从 mock 过渡到真实项目状态采集，能够通过现有 Bridge 查询当前项目内容
2. 在 `Scripts/compiler/analysis/` 中实装最小 Brownfield 分析链：`baseline_builder.py` + `delta_scope_analyzer.py`
3. 在 `Specs/Contracts/` 中落地最小 Contract 体系：`SpecPatchContract`、`MigrationContract`、`RegressionValidationContract`
4. 让 Compiler 能为 Brownfield 模式输出合法的 `baseline_context` / `delta_context` / `tree_type=delta`
5. 在不破坏 Phase 4 Greenfield 主链的前提下，为后续 Brownfield 执行链和回归验证打下可扩展地基

## 核心链路

```
ProjectInputs/GDD/
→ compiler/intake/
→ compiler/analysis/（Baseline Builder + Delta Scope Analyzer）
→ Specs/Contracts/
→ compiler/handoff/
→ ProjectState/Handoffs/draft/ → 审批 → approved/
→ orchestrator/handoff_runner.py
→ Bridge → UE5
→ ProjectState/Reports/
```

## 本期不做

- 完整 Brownfield 自动执行编排
- 完整 Regression 自动修复闭环
- 完整 Genre Skill Pack 机制
- 完整 Base Skill Domains 机制
- 自动化 Handoff 审批治理
- 重写现有 C++ Subsystem
- 重构既有 Bridge 三通道
- 修改现有稳定 Schema（`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`）

## 成功标准

1. `project_state_intake.py` 至少能读取真实 Actor 数量、关卡信息和基线存在性，而不是固定 mock
2. `Scripts/compiler/analysis/` 不再是 README 占位，而是可运行的 baseline / delta 分析模块
3. `Specs/Contracts/` 至少具备 3 类 Contract 的 manifest / template / schema 或等价结构化定义
4. Brownfield 模式下生成的 Handoff 能填充 `baseline_context` 与 `delta_context`
5. Greenfield 现有 `python Scripts/run_greenfield_demo.py` 链路不回归
6. 新增 Phase 5 Python 测试和系统测试条目可运行
7. 至少形成一份 Phase 5 Brownfield 样例报告或 smoke 记录
