# AGENT_UE5 MCP 认知桥接层定位修正版 v2

## 0. 文档目的

本文不是新的并列方案文档，而是一份**总口径声明**。

它的作用是：

- 在阅读 MCP 相关细化文档前，先明确最终收敛后的核心定位
- 防止把 MCP 继续理解成"全流程总线"或"万物接入层"
- 作为后续交叉评审、文档修订、实现边界讨论时的优先裁决依据

---

## 1. 一句话结论

**MCP 在 AGENT_UE5 中的正确定位是：认知桥接层，而不是流程主干层。**

更具体地说：

- **前期（Stage 1-2）**：MCP 负责 GDD 语义理解、Root Skill / Sub-Skill Graph 形成、Spec Family 映射建议与冲突预警
- **中期（Stage 3-5 + 执行）**：Compiler Core 调度 Skill Runtime / Cross-Review / Lowering / Handoff 组装；Agent 仍参与（填充内容、做 review 判断），但方式是 Compiler Core 内部的 prepare/save 调度，而不是 MCP 对外工具
- **后期**：MCP 负责读取测试证据并判断是否可以自动验收，或是否需要人工确认

---

## 2. 核心原则

### 原则 1：MCP 不替代 Skill
Skill 仍然是类型语义、领域能力、同类 GDD 复用的主承载层。

### 原则 2：MCP 不替代 Spec / Handoff
Spec / Handoff 仍然是编译与执行之间的结构化真源。

### 原则 3：MCP 不替代 A / B / C 执行通道
执行阶段仍由：

- Python Editor Scripting
- Remote Control API
- C++ Plugin / Subsystem

等既有执行主干承担。

### 原则 4：MCP 不替代 UE 官方自动化测试体系
测试阶段仍由：

- Automation Test Framework
- Automation Spec
- Functional Testing
- Automation Driver
- Gauntlet / UAT

承担执行、驱动、编排与取证主责。

### 原则 5：MCP 只负责高不确定性的认知判断
也就是：

- 前期的语义裁决（Stage 1-2）
- 后期的证据裁决

凡是能够由结构化自动化稳定完成的环节，都不应为了"统一"而迁入 MCP。

---

## 3. 四层标准表述

在 AGENT_UE5 中，编译前端到执行交接的主链由四层构成：

> **Skill 决定生成什么 spec；Static Spec 决定 spec 长什么样；Dynamic Spec 决定这次项目实际生成了什么（结构受 Static Spec 约束，内容由 AI Agent 填充）；Reviewed Handoff 决定执行层正式消费什么。**

---

## 4. MCP 在整体工作流中的准确位置

## 4.1 前期：语义裁决节点（Stage 1-2）
工作流：

`GDD -> MCP 前端 -> Root Skill / Sub-Skill Graph / Spec Family 映射建议 -> Compiler Core（Stage 3-5 调度）-> Reviewed Handoff`

在这一段，MCP 前端适合做：

- GDD 设计意图分析
- Root Skill 形成
- Sub-Skill Graph 分解
- Skill 到 Spec Family 的映射建议
- Spec family 冲突预警与缺口提示
- 高层风险摘要

它不应直接取代：

- Compiler Core
- Planner
- Skill Runtime
- Cross-Review
- Lowering
- Handoff Builder

---

## 4.2 中期：原生主干执行节点（Stage 3-5 + Execution）
工作流：

`Compiler Core 调度: Skill Runtime(Stage 3) -> Cross-Review(Stage 4) -> Lowering(Stage 5) -> Handoff 组装 -> Orchestrator -> A / B / C -> UE 执行 -> UE 官方自动化测试`

在这一段，MCP 不应成为主工作流承载层。

必须保留原生主干：

- Skill 仍是语义主干
- Spec / Handoff 仍是交接真源
- A / B / C 仍是执行主干
- UE 官方测试能力仍是测试主干

**Agent 在 Stage 3-5 中仍然参与**——填充 Dynamic Spec Fragment 内容、做 Cross-Review 判断、做 Lowering 决策——但参与方式是 **Compiler Core 内部的 prepare/save 调度**，而不是 MCP 对外逐阶段控制工具。

如果这段也 MCP 化，系统会退化成：

> Agent 直接调工具，而不是 Skill-First 框架

---

## 4.3 后期：证据裁决节点
工作流：

`测试结果 / 截图 / 日志 / 报告 -> MCP -> 自动通过 / 自动失败 / 人工确认升级`

在这一段，MCP 适合做：

- 读取测试证据
- 总结关键信息
- 判断证据是否足够
- 判断结果是否可信
- 输出：
  - pass
  - fail
  - escalate to human

MCP 不应直接承担：

- 测试主执行
- 大部分交互驱动
- 会话编排
- 低层断言

---

## 5. 为什么这份定位很重要

如果没有这份收敛，MCP 很容易被越画越大，最终出现两个问题：

### 5.1 Skill 会被冲淡
系统会逐渐从：

`GDD -> Skill -> Spec -> Execute -> Test`

滑向：

`GDD -> MCP -> 一堆工具 -> UE`

这样就失去了 Skill-First 的意义。

### 5.2 自动化体系会被重复包装
UE 已经有一整套官方测试体系与执行体系。
如果 MCP 再去吞这些能力，只会造成：

- 责任重复
- 边界变模糊
- 框架复杂度上升
- 真正的主干被稀释

---

## 6. 与已有 MCP 文档的关系

本文应被视为**优先级更高的总口径说明**。

如果后续细化文档中出现如下倾向，应以本文为准进行修正：

- 把 MCP 写成编译主干
- 把 MCP 写成执行主干
- 把 MCP 写成测试执行总线
- 把大量原生自动化能力迁成 MCP 主通路
- 让 Skill / Spec / Handoff 的中心性下降
- 让 MCP 对外工具覆盖 Stage 3-5 的 Compiler Core 调度职责

---

## 7. 对 Claude 的使用建议

如果把这份文档交给 Claude，建议这样使用：

### 方式 A：作为"先读总口径"
先读本文，再读其余 MCP 相关细化文档。

### 方式 B：作为"裁决优先依据"
如果后续文档和本文存在边界冲突，以本文为优先裁决依据。

### 方式 C：作为"评审锚点"
要求 Claude 在输出结论时，明确回答：

- 是否仍然保住了 Skill-First 主干
- 是否仍然保住了 Spec / Handoff 主干
- 是否仍然保住了 UE 官方自动化测试主干
- MCP 前端是否只停留在 Stage 1-2 的认知分解
- MCP 后端是否只停留在证据判读 + pass/fail/escalate
- Agent 在 Stage 3-5 是否通过 Compiler Core 内部调度参与，而不是 MCP 对外工具

---

## 8. 最终结论

AGENT_UE5 中，MCP 的最合理定义不是：

- 全流程总线
- 万物接入层
- 编译/执行/测试统一承载层

而是：

**前期（Stage 1-2）做语义裁决，后期做证据裁决，中段由 Compiler Core 调度（Agent 通过 Core 内部 prepare/save 参与），MCP 不抢主干的认知桥接层。**

这份定义，应作为后续所有 MCP 相关文档修订、Claude 交叉评审、以及实现边界控制的总口径。
