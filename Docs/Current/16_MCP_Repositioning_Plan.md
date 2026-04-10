# AGENT_UE5 MCP 重定位方案 v3

## 0. 文档目的

本文基于当前收敛后的最终结论，重新定义 MCP 在 `AGENT_UE5` 中的位置与职责。

本版明确否定两种错误理解：

1. **MCP = 全流程总线**
2. **MCP = 只做一次 GDD→Skill 判断后立刻退出**

本版的最终结论是：

- **前端（Stage 1-2）**：MCP 负责从 GDD → Root Skill → Sub-Skill Graph → Spec Family 映射建议的认知分解
- **中段（Stage 3-5 + 执行）**：Compiler Core 调度 Skill Runtime / Cross-Review / Lowering / Handoff 组装；Agent 仍通过 Core 内部 prepare/save 参与，但不是 MCP 对外工具；执行层 A/B/C 与 UE 官方测试体系保持主干地位
- **后端**：MCP 负责读取测试结果与证据，做通过/失败/人工确认升级的认知裁决

---

## 1. 总体定位

MCP 在 `AGENT_UE5` 中应被定义为：

**认知桥接层（Cognitive Bridge Layer）**

它不是执行主干，也不是测试执行总线，而是位于两端的高不确定性认知层：

### A. 前端认知分解链（Stage 1-2）
用于回答：

- 这份 GDD 对应什么类型的完整游戏能力组合
- 这个游戏的总 Skill 是什么
- 这个总 Skill 应如何拆成子 Skill 图
- 每个子 Skill 应映射到哪些 spec family
- 组合中有哪些冲突、缺口、风险

### B. 后端证据裁决链
用于回答：

- 当前自动化测试证据是否足以自动验收
- 哪些结果可以自动通过
- 哪些结果可以自动失败
- 哪些结果必须升级人工确认

---

## 2. 关键边界

## 2.1 MCP 不替代 Skill
Skill 仍然是能力语义、能力组合、领域复用的主承载层。

## 2.2 MCP 不替代 Spec / Handoff
Spec / Handoff 仍然是编译与执行之间的结构化真源。

## 2.3 MCP 不替代 A / B / C 执行通道
执行仍由：

- Python Editor Scripting
- Remote Control API
- C++ Plugin / Subsystem

等原生执行主干承担。

## 2.4 MCP 不替代 UE 官方自动化测试体系
测试执行仍由：

- Automation Test Framework
- Automation Spec
- Functional Testing
- Automation Driver
- Gauntlet / UAT

承担主责。

## 2.5 MCP 只承担高不确定性的认知判断
凡是能够由结构化自动化稳定完成的环节，都不应为了"统一"而迁入 MCP。

## 2.6 MCP 前端止于 Stage 2，不控制 Stage 3-5
Stage 3（Skill Runtime）、Stage 4（Cross-Review）、Stage 5（Lowering）及 Handoff 组装由 Compiler Core 调度。Agent 在这些阶段仍然参与（填充 Dynamic Spec Fragment 内容、做 review 判断、做 lowering 决策），但参与方式是 Compiler Core 内部的 prepare/save 调度，不是 MCP 对外工具。

---

## 3. Skill 与 Static/Dynamic Spec 的关系

这一点是本版修订的关键。

### Skill 是什么
Skill 是：

- 能力语义单元
- 能力组合单元
- 依赖关系与分解关系的组织单元

### Static Spec 是什么
Static Spec 是：

- Spec family 的固定骨架
- 字段结构、约束、默认值、模板、合同
- 框架预先存在的结构基底

### Dynamic Spec 是什么
Dynamic Spec 是：

- 当前 GDD / 当前 Project State 下，Skill 运行后的实例化 spec 结果
- per-Skill 的 spec fragments 及其合并后的 spec tree
- **结构受 Static Spec 的 schema / contract 约束，内容由 AI Agent 基于 GDD 上下文填充**

因此三者关系应被定义为：

> **Skill 决定"生成什么 spec"；Static Spec 决定"spec 长什么样"；Dynamic Spec 决定"这次项目里实际生成了什么"（结构受约束，内容由 Agent 填充）。**

---

## 4. 前端主流程：GDD 到 Reviewed Handoff

```text
GDD
↓
MCP 前端语义分析
↓
Root Skill（总 Skill / 游戏能力组合）
↓
Sub-Skill Graph（子 Skill 图 / 依赖图）
↓
按子 Skill 映射到 Static Spec Families / Contracts / Templates
═══════════════════════════════════════════════════
  ▲ MCP 前端认知分解止于此（Stage 1-2）
  ▼ 以下由 Compiler Core 调度（Stage 3-5）
    Agent 通过 Core 内部 prepare/save 参与
═══════════════════════════════════════════════════
Skill Runtime 逐 Skill 产出 Dynamic Spec Fragments（Stage 3）
  （结构受 Static Spec 约束，内容由 AI Agent 填充）
↓
Cross-Spec Review（Stage 4）
↓
Reviewed Dynamic Spec Tree
↓
Lowering（Stage 5）
↓
Build IR + Reviewed Handoff
↓
Execution
```

这条链路里：

- **MCP 前端负责 Stage 1（Intake/Projection）+ Stage 2（Planner/Skill 选择与 Spec Family 映射）的认知判断**
- **Compiler Core 负责 Stage 3-5 的结构化调度，Agent 通过 Core 内部 prepare/save 参与**
- **Execution 只消费 reviewed 之后的交接物**

---

## 5. Monopoly 示例下的理解方式

以 `GDD_MonopolyGame.md` 为例。

### 5.1 MCP 前端：GDD 语义理解（Stage 1）

MCP 第一轮不应只给出一个粗粒度标签，而应先识别这个游戏所需的完整能力面，例如：

- 棋盘回合制规则能力
- 掷骰 / 移动 / 结算能力
- 地块 / 事件 / 资产 / 金钱系统能力
- HUD / Popup / 菜单能力
- 俯视角摄像机能力
- 音频与设置能力
- 前台壳层与关卡流转能力
- 多人能力（如 GDD 需要）

这些能力组合共同组成一个：

**Root Skill（总 Skill / Game Composition Skill）**

### 5.2 MCP 前端：Sub-Skill Graph 分解（Stage 2）

随后 MCP 应将它继续分解为子 Skill 图，例如：

- boardgame_core_skill
- turn_flow_skill
- tile_event_skill
- economy_property_skill
- topdown_camera_skill
- hud_popup_ui_skill
- frontend_menu_skill
- settings_menu_skill
- level_transition_skill
- audio_control_skill
- network_session_skill（如需要）

### 5.3 MCP 前端：Spec Family 映射建议（Stage 2）

再进一步把子 Skill 投影到 spec family：

- board_layout_spec
- turn_flow_spec
- event_rules_spec
- economy_spec
- camera_spec
- hud_spec
- popup_spec
- frontend_flow_spec
- settings_ui_spec
- transition_spec
- audio_settings_spec
- network_spec

**至此，MCP 前端认知分解完成。**

---

### 5.4 Compiler Core 调度：Dynamic Spec Fragment 生成（Stage 3）

以下由 Compiler Core 调度 Skill Runtime 逐 Skill 执行，Agent 通过 prepare/save 填充内容。

每个子 Skill 运行后产出 Dynamic Spec Fragment（结构受 Static Spec 约束，内容由 Agent 填充）：

- `topdown_camera_skill` → 俯视角 camera fragment
- `hud_popup_ui_skill` → HUD fragment + popup 行为 fragment
- `turn_flow_skill` → WaitForRoll / ResolveMove / ResolveEvent / EndTurn 回合状态机 fragment
- `settings_menu_skill` → 音量 / 分辨率 / 菜单跳转 fragment

### 5.5 Compiler Core 调度：Cross-Review + Lowering + Handoff（Stage 4-5）

多 Skill 的 fragments 经 Cross-Spec Review 解决冲突后，合并为 Reviewed Dynamic Spec Tree。

再 Lowering 为 Build IR，封装进 Reviewed Handoff。

最终形成：

**Reviewed Handoff** — 执行层正式消费的交接物

---

## 6. 系统架构图（纯 ASCII，最终收敛版）

```text
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ 项目层（ProjectInputs / ProjectState）                                                      │
│                                                                                              │
│  GDD / Presets / Baselines / Existing Handoffs / Snapshots / Reports / Evidence            │
└──────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ MCP_FRONT：前端认知分解层（Stage 1-2）                                                      │
│                                                                                              │
│  GDD 语义理解                                                                               │
│  Root Skill 形成                                                                            │
│  Sub-Skill Graph 分解                                                                       │
│  Spec Family 映射建议                                                                       │
│  冲突 / 缺口 / 风险提示                                                                     │
│                                                                                              │
│  止于此。不控制 Stage 3-5。                                                                  │
└──────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Skill Compiler Plane（Stage 3-5 由 Compiler Core 调度）                                     │
│                                                                                              │
│  Compiler Core                                                                              │
│  ├─ Intake / Normalize / Route（Stage 1）                                                   │
│  ├─ Planner 调度（Stage 2）                                                                 │
│  ├─ Skill Registry / Contracts / Templates 装载                                             │
│  ├─ Skill Runtime 调度（Stage 3）— Agent 通过 prepare/save 填充内容                         │
│  ├─ Cross-Review 调度（Stage 4）— Agent 通过 prepare/save 做 review 判断                    │
│  ├─ Lowering 调度（Stage 5）— Agent 通过 prepare/save 做 lowering 决策                      │
│  └─ Handoff Builder / Serializer                                                            │
│                                                                                              │
│  Skill System                                                                               │
│  ├─ Root Skill / Sub-Skill Graph                                                            │
│  ├─ Skill Semantics                                                                         │
│  ├─ Review Rules                                                                            │
│  └─ Lowering Rules                                                                          │
│                                                                                              │
│  Static Spec Base                                                                           │
│  ├─ Families / Schemas / Contracts                                                          │
│  └─ Defaults / Templates                                                                    │
│                                                                                              │
│  Dynamic Spec Output（结构受 Static Spec 约束，内容由 Agent 填充）                          │
│  ├─ per-Skill Dynamic Spec Fragments                                                        │
│  └─ Reviewed Dynamic Spec Tree                                                              │
└──────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                       │
                                       ▼
                          Reviewed Handoff v2 / Build IR
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ Execution 主干                                                                              │
│                                                                                              │
│  Orchestrator / Handoff Runner / Run Plan                                                   │
│  Channel A / Channel B / Channel C                                                          │
│                                                                                              │
│  说明：                                                                                     │
│  - 这里不是 MCP 主舞台                                                                      │
│  - 这里消费的是 reviewed 之后的交接物                                                       │
│  - Execution MCP Adapter 可存在但仅为可选外部协议适配层                                     │
└──────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ UE 官方自动化测试主干                                                                       │
│                                                                                              │
│  Automation Test Framework / Automation Spec / Functional Testing /                         │
│  Automation Driver / Gauntlet / UAT                                                         │
│                                                                                              │
│  说明：                                                                                     │
│  - 测试执行、交互驱动、场景闭环、会话编排仍由官方测试体系承载                              │
└──────────────────────────────────────┬───────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│ MCP_BACK：后端证据裁决层                                                                    │
│                                                                                              │
│  Screenshots / Logs / Reports / Runtime State / Validation Results                          │
│    ↓                                                                                         │
│  证据读取 / 证据摘要 / 验收判读 / Pass-Fail-Escalate / Human Confirmation Gate              │
│                                                                                              │
│  说明：                                                                                     │
│  - 只做证据判读，不做测试执行                                                               │
│  - 只输出 pass / fail / escalate                                                            │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Execution 侧 MCP 的角色

执行侧 MCP 可以保留，但只能作为：

**可选外部协议适配层**

它的职责是：

- 对外暴露执行工具入口
- 统一协议接入
- 将请求分发到既有 A/B/C 通道

它不是：

- 执行主干
- 类型语义主干
- spec 生成主干
- 测试执行主干

没有它，A/B/C 仍可构成完整执行主干。

---

## 8. 测试侧 MCP 的角色

测试侧 MCP 应被严格收缩为：

**测试证据判定层**

它负责：

- 读取自动化测试产出的证据（截图、日志、报告、状态摘要）
- 提炼关键信息
- 判断是否足以自动验收
- 决定是否升级人工确认
- 输出 pass / fail / escalate

它不负责：

- 取代 Functional Testing
- 取代 Automation Driver
- 取代 Gauntlet/UAT
- 取代低层断言与会话编排
- 启动 PIE
- 驱动按钮点击或输入事件

---

## 9. 验收标准

当以下条件同时成立时，说明 MCP 定位是健康的：

1. MCP 前端负责 Stage 1-2 的认知分解（GDD → Root Skill → Sub-Skill Graph → Spec Family 映射）
2. Stage 3-5 由 Compiler Core 调度，Agent 通过 Core 内部 prepare/save 参与
3. Skill 仍是语义主干
4. Static/Dynamic Spec 关系清晰（结构受约束，内容由 Agent 填充）
5. Reviewed Handoff 仍是 Compiler → Execution 唯一正式边界
6. A/B/C 仍是执行主干
7. Execution MCP Adapter 仅为可选薄层
8. UE 官方测试体系仍是测试主干
9. MCP 后端只做证据判读 + pass/fail/escalate
10. 不出现"万物接入 MCP"的扩张路径

---

## 10. 最终结论

MCP 在 `AGENT_UE5` 中的最终正确位置不是：

- 全流程统一总线
- 中段主干
- 测试执行总线

而是：

**前端（Stage 1-2）负责 GDD→Root Skill→Sub-Skill Graph→Spec Family 映射的认知分解，后端负责测试证据→验收结论的认知裁决，中段（Stage 3-5）由 Compiler Core 调度（Agent 通过 Core 内部 prepare/save 参与），MCP 不抢 Skill / Spec / Execution / 官方测试主干。**

---

## 11. 已收敛为治理口径，但仍依赖后续实现层补齐的事项

本文档及关联的 14/15 号治理文档已完成架构层面的口径收敛。以下事项在治理层面已定义清楚，但仍需后续实现阶段落地：

### 11.1 Compiler 5-stage 的独立编排入口

当前 Compiler skeleton（`Plugins/AgentBridge/Compiler/`）中 5 个阶段各有 `get_schema()` / `create_*_template()` / `save_*()` 三件套，但缺少：

- **统一的 session / pipeline 编排入口**：目前没有一个顶层调度器能串联 Stage 1-5 + Handoff 组装的完整流程
- **MCP Compiler Plane 工具注册**：Phase 10 计划中的 12 个 Compiler Plane MCP 工具（prepare/save 对）尚未实现
- **Stage 间产物传递规范**：每个 Stage 的输出路径如何成为下一个 Stage 的输入路径，需要实现层定义

### 11.2 测试证据标准化存放格式 / run_id 规范

后端 MCP 证据裁决层依赖能用 `run_id` 定位到一组测试证据，但目前：

- **run_id 格式未定义**：需要明确 run_id 的生成规则（时间戳 / UUID / 组合键）
- **证据存放目录结构未标准化**：截图、日志、报告、状态摘要应按统一目录结构组织，例如 `ProjectState/Reports/<date>/<run_id>/screenshots/`、`logs/`、`reports/`
- **证据文件命名规范未定义**：需要明确各类证据文件的命名模式，以便 MCP 工具通过 run_id 自动定位
- **证据索引 manifest 未定义**：建议每次测试运行产出一个 `evidence_manifest.json`，列出所有可用证据及其路径

### 11.3 Phase 10 计划同步修订

Phase 10 开发计划（plan file）中以下内容与本轮修订后的治理口径存在差异，需在正式进入实现前同步：

- `val_simulate_input` 和 `val_pie_control` 两个工具与 §8 "测试侧 MCP 不负责启动 PIE / 驱动按钮点击"的口径矛盾
- 这两个工具应从 MCP Validation Plane 移出，改为 UE 官方测试体系的自动化脚本或 Compiler Core 执行通道
