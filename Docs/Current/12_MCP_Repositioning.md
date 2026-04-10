# MCP 重新定位：从执行层包装到框架级 Agent 接口

> 文档类型：架构决策记录（ADR）
> 状态：已确认方向，待实施
> 确认日期：2026-04-07
> 前置文档：Phase9_MCP_Implementation_Plan.md（Phase 9 已实施归档）

---

## 1. 问题陈述

Phase 9 完成的 MCP Server（28 个工具）本质上是 Bridge 三通道的协议再包装。即使没有 MCP，Orchestrator 通过 `query_tools` / `write_tools` / `py_channel` 已经能完整操作 UE5 Editor。MCP 在执行层只增加了一层协议转换，没有提供新能力。

```
当前（执行层包装，与 Bridge 三通道能力重复）：
  Agent → MCP → Bridge 三通道 → UE5 Editor
                ↑ 没有 MCP 也能直接用
```

MCP 的定位需要重新审视。

---

## 2. 结论

MCP 应当从"执行层的 Bridge 包装"上移为"框架级 Agent 接口"，在两个层面发挥作用：

### 2.1 上游：Compiler Plane 的 Agent 接口

MCP 应暴露 Skill-First Compiler 6 阶段主链的能力，让 AI Agent 通过标准协议驱动编译流程：

```
Agent → MCP → Compiler Plane → Reviewed Handoff → Orchestrator → Bridge → UE5
       ↑ AI Agent 通过 MCP 驱动编译主链
```

MCP 在 Compiler Plane 暴露的能力方向：

| 能力域 | 说明 |
|--------|------|
| Design Intake | 接收 GDD（Part A + Part B），解析设计意图 |
| Skill 选择与编排 | 查询 Skill Registry，组合 Skill Instance，生成依赖图 |
| Spec 生成与审查 | 生成 Dynamic Spec Tree，触发 Cross-Spec Review |
| Handoff 组装 | 产出 Reviewed Handoff v2 / Build IR |
| 编译状态查询 | 当前编译阶段、依赖图、阻断项、编译进度 |

这样 MCP 的价值变为：**让 AI Agent 以标准协议驱动 GDD → Skills → Specs → Handoff 这条编译主链**，而不是绕过编译直接操作编辑器。

### 2.2 下游：Runtime Validation 的 Agent 接口

MCP 应提供"感知 + 操作 + 判定"的能力，让 Agent 代替人完成运行时冒烟测试。

**背景**：Phase 8 task8 TASK 06 Step 7（Batch 7）定义了 7 个运行时集成验证点（val-13 ~ val-19），这些验证点要求"真实可见 / 真实可交互 / 真实可玩"，当前必须人工完成。

| 验证点 | 人工判定内容 | Agent 化后的做法 |
|--------|------------|----------------|
| val-15 | 进入 Play 后场景非黑屏 | Agent 截图 → 视觉判定"是否全黑" |
| val-16 | HUD 可见，含 4 个核心元素 | Agent 截图 → 判定"玩家/资金/回合/格子是否存在" |
| val-17 | 按钮可悬停可点击，点击后有变化 | Agent 操作鼠标 → 截图对比前后状态差异 |
| val-18 | Popup 可显示可关闭，焦点恢复 | Agent 触发弹窗 → 截图确认 → 关闭 → 再截图确认 |
| val-19 | 完成一轮完整冒烟 | Agent 按流程操作：掷骰→移动→结算→结束回合，逐步截图留证 |

这些不是简单的"对象是否存在"断言，而是需要**感知 + 判断 + 操作**的闭环。当前框架中：
- Bridge 三通道能操作编辑器，但不能"看"
- Orchestrator 能编排，但不能"判断"

MCP 在测试侧的作用是：**给 Agent 提供"看 + 操作 + 判定"的能力接口**，让 Agent 代替人完成冒烟测试的感知循环：

```
Agent（视觉判定 + 决策）
  ↓ MCP
测试能力接口
  ├── 截图 / 录屏 → 返回给 Agent 做视觉判定
  ├── 模拟输入（鼠标点击、键盘）→ 与游戏交互
  ├── 读取运行时状态（GameState、HUD 控件树）→ 辅助判定
  └── 生成证据（截图 + 日志 + 结论报告）
```

---

## 3. 重新定位总结

| 维度 | Phase 9 现状（旧定位） | 新定位 |
|------|----------------------|--------|
| 架构位置 | Execution Orchestrator 外层 | Compiler Plane + Runtime Validation |
| 暴露能力 | Bridge 三通道的 28 个编辑器操作 | 编译主链驱动 + 运行时感知验证 |
| 核心价值 | 协议转换（MCP ↔ Bridge） | Agent 驱动 pipeline + Agent 代替人工冒烟 |
| 是否可替代 | 是（Bridge 三通道已有同等能力） | 否（编译驱动和视觉判定是新能力） |

```
MCP 新定位：

  ┌─────────────────────────────────────────┐
  │           AI Agent（Claude 等）           │
  └────────────┬───────────────┬────────────┘
               │               │
       ┌───────▼───────┐ ┌────▼──────────────┐
       │ MCP 上游接口   │ │ MCP 下游接口       │
       │ Compiler Plane │ │ Runtime Validation │
       │               │ │                    │
       │ · GDD Intake  │ │ · 截图 / 视觉感知   │
       │ · Skill 编排   │ │ · 模拟输入 / 交互   │
       │ · Spec 生成    │ │ · 状态读取 / 判定   │
       │ · Handoff 组装 │ │ · 证据生成 / 报告   │
       └───────┬───────┘ └────┬──────────────┘
               │               │
       ┌───────▼───────────────▼──────────────┐
       │     Orchestrator + Bridge 三通道       │
       │          （执行层，已有能力）           │
       └──────────────────────────────────────┘
```

---

## 4. Phase 9 已有实现的处置

Phase 9 已实现的 28 个工具（server.py / tool_definitions.py）不需要删除，但需要重新归类：
- 其中大部分编辑器操作工具应下沉回 Bridge 层直接使用，不再作为 MCP 的核心价值
- `capture_screenshot`、`run_editor_python` 等工具可保留为 Runtime Validation 接口的基础组件
- 新增的 Compiler Plane 接口和 Runtime Validation 接口将成为 MCP 的核心工具集

---

## 5. 后续步骤

本文档记录架构方向决策。具体实施方案（工具集设计、接口定义、阶段划分）待后续 Phase 立项时制定。
