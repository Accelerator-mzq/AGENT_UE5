# AGENT_UE5 MCP Validation / Testing Plane 角色定义 v3

## 0. 文档定位

本文件重新定义 MCP 在 Validation / Testing 侧的角色。

本版结论明确为：

**MCP 不执行测试主干。**
**MCP 负责测试证据的认知判读、验收结论生成与人工确认升级。**

因此，本文件不再把 MCP 描述成"测试总线本体"，而将其收敛为：

**Evidence Judge / Human Confirmation Gate**

---

## 1. 测试阶段的主干不变

测试主干仍然由 UE 官方能力承载：

- Automation Test Framework
- Automation Spec
- Functional Testing
- Automation Driver
- Gauntlet / UAT

这些能力负责：

- 断言执行
- 输入驱动
- 场景测试
- 闭环冒烟
- 会话编排
- 报告生成
- 自动化回归

MCP 不应抢占这些职责。

---

## 2. MCP 在测试中的正确位置

MCP 处于：

**官方测试执行之后**

也就是说，顺序应为：

`官方测试执行 -> 结果与证据产出 -> MCP 判读 -> pass/fail/escalate`

因此，MCP 在测试阶段的职责主要是：

### A. 读取证据
- 截图
- 日志
- 报告
- runtime state summary
- validation result summary

### B. 形成高层判读
- 当前证据是否足以支持验收
- 可见性是否满足预期
- 交互性是否满足预期
- 场景级 smoke 是否真正达标

### C. 做升级判断
- 自动通过（pass）
- 自动失败（fail）
- 升级人工确认（escalate）

### D. 输出验收说明
- 失败归因摘要
- 开放问题清单
- 人工确认理由

---

## 3. 适用场景

MCP 适合介入的场景包括：

- HUD 存在，但是否"足够符合验收意图"带有高层判读成分
- 画面非黑屏，但是否"基本可见、基本可玩"仍需认知判断
- 闭环流程走完，但是否能算真正达标需要综合证据解释
- Popup 行为虽然存在，但是否达到 UX 层面的验收要求需要额外说明
- 自动化结果不一致，需要升级人审

---

## 4. 不适用场景

以下仍不应由 MCP 负责：

- 低层断言执行
- 大部分输入驱动动作
- Functional Test 本体执行
- Automation Driver 行为脚本
- Automation Spec 本体执行
- Gauntlet / UAT 会话编排
- 启动 / 停止 PIE
- 模拟鼠标点击或键盘输入

---

## 5. 与前端认知分解的关系

前端 MCP 负责 Stage 1-2 的认知分解：

- GDD → Root Skill → Sub-Skill Graph → Spec Family 映射建议

测试侧 MCP 负责：

- 测试结果 → 证据解释 → 验收结论 的认知裁决

两者都属于 MCP 的认知桥接层，但作用点完全不同：

- 前端（Stage 1-2）解决"怎么设计与分解"
- 后端解决"怎么解释与判定"

中段（Stage 3-5 + Execution + 测试执行）不属于 MCP 主舞台。

---

## 6. 推荐接口族

概要级接口（详细见测试工具集最小实现说明）：

- `load_runtime_screenshots(run_id)` — 读取截图证据
- `load_runtime_logs(run_id)` — 读取日志证据
- `load_validation_report(run_id)` — 读取验证报告
- `load_runtime_state_summary(run_id)` — 读取状态摘要
- `summarize_runtime_evidence(run_id)` — 证据摘要
- `judge_visibility_acceptance(run_id, criteria)` — 可见性判读
- `judge_interaction_acceptance(run_id, criteria)` — 交互性判读
- `judge_smoke_acceptance(run_id, scenario)` — 冒烟判读
- `decide_requires_human_confirmation(run_id)` — 升级判断
- `export_acceptance_summary(run_id)` — 验收结论输出

---

## 7. 设计原则

1. 自动化负责执行，MCP 负责判读
2. 自动化负责取证，MCP 负责证据解释
3. 自动化能稳定处理的，不迁入 MCP
4. 只在自动化无法充分自证时才让 MCP 介入
5. 人工确认应是明确升级出口，而不是默认失败兜底

---

## 8. 成功标准

1. 不把 MCP 写成测试执行总线
2. 不弱化 UE 官方测试体系
3. 能在关键验收点输出高层判定
4. 能明确区分 pass / fail / escalate
5. 能为人工确认提供足够上下文
6. 不包含 PIE 控制、输入模拟等执行类工具

---

## 9. 结论

测试阶段，MCP 的正确角色不是：

**"去跑测试"**

而是：

**"去读证据、做判读、给出验收结论并决定是否需要人来确认"**
