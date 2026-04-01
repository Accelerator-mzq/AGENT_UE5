# Phase 5 目标

> 文档版本：L1-Phase5-v2

## 本期目标

本期目标是把 Phase 4 的 Greenfield 自动生成链扩展到 Brownfield 最小闭环，并同步完成文档治理、测试治理和证据治理：

1. 让 `project_state_intake.py` 从 mock 升级为真实 Bridge 查询 + fallback
2. 落地 `baseline_builder.py` 与 `delta_scope_analyzer.py`
3. 在 `Specs/Contracts/` 中落地最小 Contract 体系
4. 让 Compiler 在 Brownfield 模式下输出合法的 `baseline_context` / `delta_context` / `tree_type=delta`
5. 保持 Greenfield 主链不回归
6. 明确 `task.md`、`Snapshots`、`Evidence` 的当前期规则

## 成功标准

1. `project_state_intake.py` 至少能返回真实结构化项目状态或明确 fallback，不再是固定硬编码
2. `Scripts/compiler/analysis/` 不再是 README 占位
3. `Specs/Contracts/` 至少具备 registry + 3 类 Common Contract Model
4. Brownfield 样例 Handoff 能通过 Schema 校验，并只追加新 Actor
5. `python Scripts/run_greenfield_demo.py` 继续可跑
6. Phase 5 Python 测试通过，测试细节先维护在根目录 `task.md`
7. 真实 UE5 验证时可将截图证据写入 `ProjectState/Evidence/Phase5/`

## 本期不做

- 完整 Brownfield 自动执行编排
- 完整 patch / migration 自动落地
- 完整 Genre Skill Pack 机制
- 完整 Base Skill Domains 机制
- 自动化 Handoff 审批治理
- 提前把 Phase 5 用例写进 `SystemTestCases.md`
