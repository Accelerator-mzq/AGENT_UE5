# AGENT_UE5 MCP 测试工具集最小实现说明 v2

## 0. 文档目的

本文件定义 MCP 在测试阶段的最小正确工具集。

本版明确收敛为：

**测试证据判定工具集**

而不是：

**测试执行工具集**

即：

- 官方自动化测试体系负责执行与取证
- MCP 工具集负责读取证据并形成高层判定

---

## 1. 上下游关系

### 上游：自动化执行与取证
由以下能力负责：

- Automation Test Framework
- Automation Spec
- Functional Testing
- Automation Driver
- Gauntlet / UAT

这些能力产出：

- screenshots
- logs
- reports
- runtime state
- assertion results
- smoke results

### 下游：MCP 判定层
MCP 工具集负责：

- 读取这些产物
- 提炼关键信息
- 判断是否足以自动验收
- 判断是否需要人工确认
- 输出结论与升级说明

---

## 2. 设计原则

1. 不替代 UE 官方测试框架
2. 不替代 Functional Testing / Automation Driver
3. 不替代 Gauntlet / UAT
4. 只面向"自动化无法充分自证"的问题
5. 输出必须是结构化验收结论与升级建议

---

## 3. 最小工具族建议

### A. 证据读取
- `load_runtime_screenshots(run_id)`
- `load_runtime_logs(run_id)`
- `load_validation_report(run_id)`
- `load_runtime_state_summary(run_id)`

### B. 证据摘要
- `summarize_runtime_evidence(run_id)`
- `summarize_smoke_findings(run_id)`

### C. 验收判读
- `judge_visibility_acceptance(run_id, criteria)`
- `judge_interaction_acceptance(run_id, criteria)`
- `judge_smoke_acceptance(run_id, scenario)`

### D. 升级判断
- `decide_requires_human_confirmation(run_id)`
- `list_open_acceptance_questions(run_id)`

### E. 结论输出
- `export_acceptance_summary(run_id)`
- `export_escalation_note(run_id)`

---

## 4. 对应问题类型

### 适合本工具集处理的
- HUD 是否"基本达到可见验收意图"
- 场景是否"基本达到非黑屏且可见"
- 交互结果是否"足以证明有效"
- 一轮 smoke 是否"足以认为通过"
- 当前证据是否"足够让系统自动验收"

### 不适合本工具集处理的
- 启动 PIE
- 驱动绝大多数按钮点击
- 操纵底层输入事件
- 执行 Functional Test
- 执行 Automation Driver 行为脚本
- 调度 Gauntlet 会话

这些都应留在自动化执行层。

---

## 5. 与典型运行时集成验证的关系

例如运行时集成验证中的：

- HUD 可见性检查
- Popup 生命周期检查
- 鼠标 / 输入检查
- 一轮 gameplay smoke

这些检查的关系应是：

### 执行层负责
- 真正运行测试
- 真正驱动交互
- 真正产生截图 / 日志 / 报告 / 状态摘要

### MCP 判定层负责
- 读这些结果
- 总结关键证据
- 判断证据是否足够
- 判断是否需要人工确认
- 给出验收结论说明

---

## 6. 输出模型建议

每次判定至少输出：

- `status`: `pass | fail | escalate`
- `confidence`: `low | medium | high`
- `evidence_used`: 证据项列表
- `reasoning_summary`: 判定摘要
- `open_questions`: 未解决问题
- `human_confirmation_needed`: 布尔值

---

## 7. 成功标准

1. 工具集不与自动化执行层职责重叠
2. 工具集以证据判定与升级为中心
3. 工具集可在关键验收点形成统一输出模型
4. 工具集可支撑人工确认流程
5. 工具集不会把 MCP 再次膨胀成测试执行主干

---

## 8. 结论

MCP 测试工具集的最小正确形态不是：

**"帮系统去跑更多测试"**

而是：

**"帮系统判断现有测试证据是否足够，以及何时需要人来确认"**
