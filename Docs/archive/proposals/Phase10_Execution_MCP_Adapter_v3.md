# AGENT_UE5 Execution MCP Adapter 边界说明 v3

## 0. 文档定位

本文件定义 MCP 在执行侧的最小存在方式。

在当前最终口径中，Execution 侧 MCP 可以存在，但其地位应被明确降级为：

**可选外部协议适配层**

它不是：

- 框架前端认知分解主干
- Skill / Spec 生成主干
- 执行主工作流承载层
- 测试主工作流承载层

---

## 1. 定义

`Execution MCP Adapter` 的合理职责是：

- 向外部 Agent / MCP Client 暴露一组受控执行入口
- 做工具发现与调用协议适配
- 把执行请求分发到既有 A/B/C 通道
- 保持对外接入的一致性

---

## 2. 为什么它只能是薄层

`AGENT_UE5` 的执行主干已经存在：

- Reviewed Handoff v2 / Build IR
- Orchestrator / Handoff Runner / Run Plan Builder
- Channel A：Python Editor Scripting
- Channel B：Remote Control API
- Channel C：C++ Plugin / Subsystem

因此，Execution 侧 MCP 不能被抬升为主工作流承载层。

它只能消费已经完成前端认知分解与 reviewed handoff 组装后的交接物。

---

## 3. 与前端认知分解的边界

前端 MCP（Stage 1-2）负责：

- GDD 语义分析
- Root Skill 形成
- Sub-Skill Graph 分解
- Spec Family 映射建议

MCP 前端的认知分解止于 Stage 2（Spec Family mapping 建议）。Stage 3-5（Skill Runtime / Cross-Review / Lowering / Handoff 组装）由 Compiler Core 调度。

Execution Adapter 完全不应承担这些职责。

它只应消费：

- Spec
- Reviewed Dynamic Spec Tree
- Build IR
- Reviewed Handoff
- Run Plan

---

## 4. 与 Skill / Spec 的边界

Execution Adapter 不应承担：

- Skill 选择
- Skill 组合
- Dynamic Spec Fragments 生成
- Spec Tree 合并
- Review / Lowering 主逻辑

这些仍应属于：

- 前端认知分解层（Stage 1-2）
- Skill Runtime（Stage 3）
- Compiler Core / Cross-Review（Stage 4）
- Lowering（Stage 5）

---

## 5. 与测试主干的边界

Execution Adapter 也不应承担：

- Functional Testing 本体执行
- Automation Driver 主逻辑
- Automation Spec 主逻辑
- Gauntlet / UAT 会话编排
- 测试证据判定主逻辑

测试证据判定归后端 MCP（Evidence Judge / Human Confirmation Gate），见 Validation Testing Plane 角色定义。

它最多只提供：

- 执行后产物查询
- 结果文件收集接口

---

## 6. 推荐最小职责集合

推荐仅保留以下能力：

- `list_execution_tools()`
- `dispatch_execution_request()`
- `query_execution_status()`
- `collect_execution_artifacts()`

不推荐扩成：

- `decide_skill_set()` — 属于前端 MCP Stage 1-2
- `build_spec_tree()` — 属于 Compiler Core Stage 3-4
- `run_test_semantics()` — 属于官方测试体系
- `judge_acceptance()` — 属于后端 MCP 证据判读

---

## 7. 保留它的意义

保留 Execution Adapter 的理由主要有：

1. 对外部 Agent 提供统一协议入口
2. 屏蔽直接接触多通道细节的复杂度
3. 在不改变执行主干的前提下，提供有限的协议化接入

---

## 8. 成功标准

1. 没有它，A/B/C 仍可构成完整执行主干
2. 有了它，也不会造成执行责任漂移
3. Skill / Spec 语义不会回流到执行层
4. 测试语义不会回流到执行层
5. 它始终是薄层、可选、非核心

---

## 9. 结论

Execution MCP Adapter 可以存在，但它的正确定位只能是：

**执行层外部协议适配器，而不是 AGENT_UE5 的中段主轴。**
