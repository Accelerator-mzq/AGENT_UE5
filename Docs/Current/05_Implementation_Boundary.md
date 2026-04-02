# 实施边界

> 阶段：Phase 7 已归档 / 下一阶段待规划

## 允许改动

- 归档后的文档维护与事实回写。
- 下一阶段规划前的边界说明、规则说明和入口文档维护。
- 对既有回归链路的稳定性修复，但不隐式扩阶段范围。

## 暂不允许改动

- 不虚构新的阶段名称或提前创建“Phase 8”任务清单。
- 不在没有新阶段规划的情况下新增测试编号。
- 不在无明确目标的前提下扩展 promotion 流水线、第三个 genre pack 或新的治理协议字段。

## 当前固定口径

- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 与 [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 当前统一为 `230` 条口径。
- 根目录 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 只承担“下一阶段待规划”入口。
- 新阶段启动前，任何新增用例都必须同时考虑总表、系统测试入口和归档策略。
