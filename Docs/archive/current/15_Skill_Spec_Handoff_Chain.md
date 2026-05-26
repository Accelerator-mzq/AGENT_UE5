# AGENT_UE5 Skill → Static Spec / Dynamic Spec → Reviewed Handoff 关系结构说明 v2

## 0. 文档目的

本文用于正式说明 `AGENT_UE5` 中以下四层对象之间的关系与边界：

- **Skill**
- **Static Spec**
- **Dynamic Spec**
- **Reviewed Handoff**

本文的目标不是重新定义整个架构，而是把编译前端到执行交接之间最关键的一条主链讲清楚，避免以下常见误解：

1. 误把 Skill 当作可直接执行的对象
2. 误把 Spec 当作与 Skill 并列、互相替代的对象
3. 误把 Dynamic Spec 理解成"随手生成的临时文本"
4. 误把 Reviewed Handoff 理解成普通导出文件，而非 Compiler → Execution 的唯一正式交接物

---

## 1. 一句话结论

在 `AGENT_UE5` 中，这四者的关系应被定义为：

> **Skill 是上游能力分解树；Static Spec 是结构骨架；Dynamic Spec 是当前项目实例化出来的结构化结果（结构受 Static Spec 约束，内容由 AI Agent 填充）；Reviewed Handoff 是经 review / lowering 后交给执行层的正式交接物。**

更直接地说：

- **Skill 决定"生成什么 spec"**
- **Static Spec 决定"spec 长什么样"**
- **Dynamic Spec 决定"这次项目里实际生成了什么"**
- **Reviewed Handoff 决定"执行层正式吃什么"**

---

## 2. 四层对象的定义

## 2.1 Skill

Skill 是：

- 能力语义单元
- 能力组合单元
- 依赖关系与分解关系的组织单元
- 从 GDD 走向 Spec 的上游认知中间层

Skill 负责回答的问题是：

- 这个游戏需要哪些能力
- 这些能力如何拆成子能力
- 哪些能力之间有依赖关系
- 哪些能力应该落向哪些 spec family

Skill **不是**：

- 直接执行 UE 的动作集合
- A/B/C 通道的调用脚本
- Reviewed Handoff 本体

---

## 2.2 Static Spec

Static Spec 是：

- Spec family 的固定骨架
- schema / contract / template / defaults 的载体
- 框架预先存在的结构性基底

Static Spec 负责回答的问题是：

- 这一类 spec 的字段结构是什么
- 这一类 spec 的边界与约束是什么
- 这一类 spec 的默认形状是什么
- 这一类 spec 可以被哪些 Skill 投影生成

Static Spec **不是**：

- 当前项目的最终结果
- 某次编译的实例化产物
- 运行时状态快照

---

## 2.3 Dynamic Spec

Dynamic Spec 是：

- 当前 GDD / 当前 Project State / 当前编译上下文下的实例化 spec 结果
- 每个 Skill 运行后产出的 spec fragments
- fragments 经过 review / merge 后形成的 dynamic spec tree

**关键特征：Dynamic Spec 的结构受 Static Spec 的 schema / contract 约束，但字段值由 AI Agent 基于 GDD 上下文填充。** 这意味着 Static Spec 决定了"哪些字段必须存在、取值范围是什么"，而 Agent 的认知能力决定了"这些字段在当前项目中应该填什么值"。

Dynamic Spec 负责回答的问题是：

- 这次项目里实际生成了哪些 spec
- 每个 spec 的当前取值是什么
- 多个 Skill 的产物合并后，完整结构长什么样
- 当前项目的结构化编译结果是什么

Dynamic Spec **不是**：

- 静态 schema
- 任意自由格式文本
- 最终执行脚本

---

## 2.4 Reviewed Handoff

Reviewed Handoff 是：

- Compiler Plane 到 Execution Plane 的唯一正式交接物
- Reviewed Dynamic Spec Tree、Build IR 及其相关 metadata 的正式封装
- 执行层消费的结构化真源

Reviewed Handoff 负责回答的问题是：

- 当前编译结果经过 review / lowering 后，执行层正式应接收什么
- 这次执行的模式、范围、输入和约束是什么
- 这次执行对应的 reviewed spec tree / build intent / run plan 基础是什么

Reviewed Handoff **不是**：

- Skill 列表
- 纯 fragment 集合
- 未经 review 的草稿 spec

---

## 3. 四者关系总图

```text
GDD
↓
MCP 前端认知分解（Stage 1-2）
├─ GDD 语义理解
├─ Root Skill 形成
├─ Sub-Skill Graph 分解
└─ Spec Family 映射建议与冲突预警
─────────────────────────────────────
  ▲ MCP 前端止于此（Stage 1-2）
  ▼ 以下由 Compiler Core 调度（Stage 3-5）
    Agent 通过 Core 内部 prepare/save 参与
─────────────────────────────────────
结合 Static Spec Families / Contracts / Templates
↓
Skill Runtime 逐 Skill 生成 Dynamic Spec Fragments（Stage 3）
  （结构受 Static Spec 约束，内容由 AI Agent 填充）
↓
Cross-Spec Review（Stage 4）
↓
Reviewed Dynamic Spec Tree
↓
Lowering（Stage 5）
↓
Build IR
↓
Reviewed Handoff
↓
Execution
```

这张链路图里，边界很清楚：

- **Skill 层**：负责能力分解
- **Static Spec 层**：负责结构骨架
- **Dynamic Spec 层**：负责实例化结构结果（结构受约束，内容由 Agent 填充）
- **Reviewed Handoff 层**：负责执行交接
- **MCP 前端**：负责 Stage 1-2 的认知分解
- **Compiler Core**：负责 Stage 3-5 的结构化调度

---

## 4. 谁依赖谁

## 4.1 Skill 依赖 Static Spec，但不等于 Static Spec

Skill 要想生成 spec，必须知道：

- 可用的 spec family 有哪些
- 每种 spec family 的 schema / contract / template 是什么
- 哪些 Skill 可以合法投影到哪些 spec family

因此：

> Skill 依赖 Static Spec 提供的结构边界与模板。

但 Skill 本身仍然是"能力语义层"，不应被等同于 Static Spec。

---

## 4.2 Dynamic Spec 由 Skill 在 Static Spec 边界内生成

Dynamic Spec 的正确来源不是：

- GDD 直接硬编码生成
- 执行层倒推生成
- 任意自由生成文本

而应是：

> Skill Runtime（Stage 3）在 Static Spec 的约束和模板基础上，结合当前项目上下文，由 AI Agent 填充字段值，产出 per-Skill 的 Dynamic Spec Fragments。

因此：

- 没有 Skill，Dynamic Spec 会失去语义来源
- 没有 Static Spec，Dynamic Spec 会失去结构边界
- 没有 Agent，Dynamic Spec 会失去内容填充能力

---

## 4.3 Reviewed Handoff 不是 Skill 直接产物，而是 Dynamic Spec 经 review / lowering 后的正式输出

Skill 的直接产物应是：

- spec projection
- per-skill fragments
- review inputs
- lowering hints

而不是直接生成最终交接物。

Reviewed Handoff 应由以下路径形成：

1. Skill Runtime（Stage 3）生成 per-Skill Dynamic Spec Fragments
2. Cross-Spec Review（Stage 4）合并、校验、修正
3. 得到 Reviewed Dynamic Spec Tree
4. Lowering（Stage 5）到 Build IR
5. 再组装为 Reviewed Handoff

以上 Stage 3-5 由 Compiler Core 调度，Agent 通过 Core 内部 prepare/save 参与。

所以：

> **Reviewed Handoff 是"编译收敛后的正式输出"，不是"Skill 运行时的直接输出"。**

---

## 5. 从 Monopoly 示例理解这条关系

以 `GDD_MonopolyGame.md` 为例。

## 5.1 GDD 先被识别为一个完整游戏能力组合

MCP 前端不应只输出一句：

- 这是一个 boardgame

而应进一步识别：

- 棋盘回合制能力
- 掷骰 / 移动 / 结算能力
- 地块 / 事件 / 经济系统能力
- HUD / Popup / 菜单能力
- 俯视角摄像机能力
- 音频与设置能力
- 前台壳层与关卡流转能力
- 多人能力（若 GDD 需要）

这些能力组合形成一个：

**Root Skill（总 Skill / Game Composition Skill）**

---

## 5.2 Root Skill 继续分解成 Sub-Skill Graph

例如可分解为：

- `boardgame_core_skill`
- `turn_flow_skill`
- `dice_resolution_skill`
- `tile_event_skill`
- `economy_property_skill`
- `topdown_camera_skill`
- `hud_popup_ui_skill`
- `frontend_menu_skill`
- `settings_menu_skill`
- `level_transition_skill`
- `audio_control_skill`
- `network_session_skill`（若需要）

这一步的意义是：

> Skill 不再只是一个平面标签，而是变成一棵能力分解树。

---

## 5.3 Sub-Skill Graph 再映射到 Static Spec Families

例如：

- `topdown_camera_skill`
  - 对应 `camera_spec` family 的 static schema / template / defaults

- `hud_popup_ui_skill`
  - 对应 `hud_spec`
  - 对应 `widget_layout_spec`
  - 对应 `popup_spec`

- `turn_flow_skill`
  - 对应 `turn_flow_spec`

- `boardgame_core_skill`
  - 对应 `board_layout_spec`
  - 对应 `piece_movement_spec`

- `settings_menu_skill`
  - 对应 `settings_ui_spec`
  - 对应 `audio_settings_spec`
  - 对应 `display_settings_spec`

这一步回答的是：

> 子 Skill 将落向哪些 spec family。

**至此，MCP 前端认知分解完成（Stage 1-2）。以下由 Compiler Core 调度。**

---

## 5.4 Compiler Core 调度 Skill Runtime 生成 per-Skill Dynamic Spec Fragments（Stage 3）

在当前 Monopoly GDD 下，Compiler Core 调度 Skill Runtime 逐 Skill 执行，Agent 通过 prepare/save 填充内容：

- `topdown_camera_skill`
  - 生成具体的俯视角 camera fragment

- `hud_popup_ui_skill`
  - 生成当前玩家 / 资产 / 回合数 / 当前格子等 HUD fragment
  - 生成 popup 行为 fragment

- `turn_flow_skill`
  - 生成 WaitForRoll / ResolveMove / ResolveEvent / EndTurn 等回合状态机 fragment

- `settings_menu_skill`
  - 生成音量调节 / 分辨率调节 / 菜单跳转相关 fragment

这些 fragment 的结构由 Static Spec schema/contract 约束，字段值由 AI Agent 填充。

它们都属于：**Dynamic Spec Fragments**

---

## 5.5 Compiler Core 调度 Cross-Review 合并为 Reviewed Dynamic Spec Tree（Stage 4）

多个子 Skill 的 fragments 在 Cross-Spec Review 后：

- 解决命名、依赖、边界冲突
- 解决重复字段或约束冲突
- 解决互相引用的关系问题

最终得到：

**Reviewed Dynamic Spec Tree**

此时，结构已经从"零散 fragment"上升为"当前项目完整的结构化 spec tree"。

---

## 5.6 Compiler Core 调度 Lowering 为 Build IR 并组装 Reviewed Handoff（Stage 5）

接下来：

- 将 Reviewed Dynamic Spec Tree Lowering 为 Build IR
- 把 Build IR、review metadata、执行模式等封装进 Reviewed Handoff

执行层最终消费的不是：

- Root Skill
- Sub-Skill Graph
- 单独某个 fragment

而是：

**Reviewed Handoff**

---

## 6. Skill、Static Spec、Dynamic Spec、Reviewed Handoff 的层级关系

可以把四层关系理解成下面这样：

```text
[能力语义层]
Root Skill
Sub-Skill Graph

[结构骨架层]
Static Spec Families / Contracts / Templates / Schemas

[项目实例层]
Dynamic Spec Fragments（结构受约束，内容由 Agent 填充）
Reviewed Dynamic Spec Tree

[执行交接层]
Build IR
Reviewed Handoff
```

这四层从上到下的职责越来越确定：

- 上层更偏语义与组合
- 中层更偏结构骨架
- 下层更偏当前项目实例化结果
- 最下层更偏执行交接

---

## 7. 与 Compiler Core 的关系

Compiler Core 的职责，不应被误认为"自己发明所有 spec"。

它更合理的职责是：

- Intake / Normalize / Route（Stage 1）
- Planner 调度（Stage 2）
- Skill Registry / Contracts / Templates 装载
- Skill Runtime 调度（Stage 3）
- Cross-Review 调度（Stage 4）
- Lowering 调度（Stage 5）
- Handoff Builder / Serializer

因此：

- Skill 的语义分解不是 Core 本体
- Static Spec 的骨架不是 Core 本体
- Dynamic Spec 的生成也不是 Core 单独硬编码完成——内容由 Agent 填充
- Core 更像"编译主骨架与调度器"

---

## 8. 与 MCP 前端的关系

MCP 前端参与到 Stage 1-2 的认知分解：

- GDD 语义理解（Stage 1）
- Root Skill 形成（Stage 1-2）
- Sub-Skill Graph 分解（Stage 2）
- per-Skill spec family mapping 建议（Stage 2）
- 风险 / 缺口 / 冲突提示（Stage 2）

但 MCP 前端不应直接取代 Compiler Core 调度的 Stage 3-5：

- Skill Runtime = Stage 3
- Cross-Review = Stage 4
- Lowering = Stage 5
- Handoff Builder = 组装阶段

Agent 在 Stage 3-5 中仍然参与（填充 fragment 内容、做 review 判断、做 lowering 决策），但参与方式是 **Compiler Core 内部的 prepare/save 调度**，不通过 MCP 对外工具。

也就是说：

> MCP 前端负责"认知分解"（Stage 1-2），Compiler Core 负责"结构化生成与收敛"（Stage 3-5），Agent 全程参与但中段通过 Core 调度。

---

## 9. 与 Execution 的关系

Execution 侧不应直接消费 Skill。

Execution 侧应消费的是：

- Reviewed Handoff
- Build IR
- Reviewed Dynamic Spec Tree 的执行化结果

因此：

- Skill 不是执行入口
- Dynamic Spec 也不是最终直接执行入口
- Reviewed Handoff 才是正式交接边界

---

## 10. 常见误解与纠正

## 误解 1：Skill 就是执行脚本
错误。

Skill 是能力分解与语义组织层，不应直接等同于执行脚本。

---

## 误解 2：Spec 和 Skill 是平级替代关系
错误。

Skill 是上游能力语义层，Spec 是下游结构化投影层。二者是上下游关系，不是并列替代关系。

---

## 误解 3：Dynamic Spec 只是临时草稿
错误。

Dynamic Spec 是当前项目真实的结构化编译结果，其结构受 Static Spec 约束，内容由 AI Agent 填充。经过 review 后会成为 Reviewed Dynamic Spec Tree 的核心组成。

---

## 误解 4：Reviewed Handoff 只是导出文件
错误。

Reviewed Handoff 是 Compiler → Execution 的唯一正式交接物，是执行层的结构化真源。

---

## 误解 5：MCP 前端控制整条编译链
错误。

MCP 前端负责 Stage 1-2 的认知分解（GDD → Root Skill → Sub-Skill Graph → Spec Family 映射）。Stage 3-5（Skill Runtime → Cross-Review → Lowering → Handoff 组装）由 Compiler Core 调度，Agent 通过 Core 内部 prepare/save 参与。

---

## 11. 最终定义

如果要用一句更收敛的话定义这条关系，可以写成：

> **Skill 是上游能力分解树；Static Spec 是结构骨架；Dynamic Spec 是当前项目实例化出来的结构结果（结构受 Static Spec 约束，内容由 AI Agent 填充）；Reviewed Handoff 是经 review / lowering 后交给执行层的正式交接物。**

再压缩一点就是：

> **Skill 负责认知分解，Spec 负责结构化落地，Handoff 负责正式交接。**

---

## 12. 可直接用于后续文档的标准表述

建议在后续文档中统一采用如下表述：

### 标准表述 A
Skill 决定生成什么 spec；Static Spec 决定 spec 长什么样；Dynamic Spec 决定当前项目里实际生成了什么（结构受 Static Spec 约束，内容由 AI Agent 填充）；Reviewed Handoff 决定执行层正式消费什么。

### 标准表述 B
Root Skill / Sub-Skill Graph 由 MCP 前端认知分解（Stage 1-2）形成；Skill Runtime（Stage 3）结合 Static Spec Base / Contracts / Templates，由 AI Agent 填充内容，生成 per-Skill Dynamic Spec Fragments（结构受 Static Spec 约束）；这些 fragments 经 Cross-Spec Review（Stage 4）合并为 Reviewed Dynamic Spec Tree，再 Lowering（Stage 5）为 Build IR 与 Reviewed Handoff，最后进入执行。Stage 3-5 由 Compiler Core 调度，Agent 通过 Core 内部 prepare/save 参与。

### 标准表述 C
在 `AGENT_UE5` 中，Skill 不是执行入口，Reviewed Handoff 才是 Compiler → Execution 的正式边界。MCP 前端止于 Stage 2，Compiler Core 调度 Stage 3-5。
