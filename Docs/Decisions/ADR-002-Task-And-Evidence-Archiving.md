# ADR-002：Task 与 Evidence 归档规则

> 状态：Accepted
> 日期：2026-04-01

## 背景

从 Phase 4 起，项目已经形成“根目录 `task.md` 作为当前阶段任务入口”的工作方式。与此同时，阶段执行证据也开始区分：

- `Snapshots/`：可复用的 baseline / state snapshot
- `Evidence/PhaseX/`：当前阶段验收截图、日志与说明

`ADR-001-Doc-Governance.md` 记录的是更早阶段的规则，不应被直接改写，但需要一份新的决策来承接当前做法。

## 决策

1. 根目录 `task.md` 是**当前阶段唯一任务入口**
2. 阶段结束后，`task.md` 归档到 `Docs/History/Tasks/`
3. 从 Phase 4 起，阶段任务归档命名统一采用 `taskN_phaseX.md`
4. `ProjectState/Snapshots/` 只存 baseline / state snapshot
5. 当前阶段运行证据统一放在 `ProjectState/Evidence/PhaseX/`
6. 阶段结束时，再将已验证完成的测试用例从归档 `task.md` 补录到 `Plugins/AgentBridge/Tests/SystemTestCases.md`

## 影响

- 当前期任务不会再散落在多个文档中
- `SystemTestCases.md` 保持“阶段结算后再收录”的节奏
- baseline 产物与截图证据不再混放
