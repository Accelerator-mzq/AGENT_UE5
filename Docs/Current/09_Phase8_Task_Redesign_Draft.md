# Phase 8 改进版任务草案

> 目的：给出一版“如果现在重新设计 Phase 8 的 `task.md`，如何覆盖已暴露问题”的可执行草案
> 状态：Draft
> 适用场景：Phase 8 复盘、Phase 9 任务设计、后续类似垂直切片项目复用

## 1. 设计原则

这版任务草案不再只追求“产物存在”和“脚本通过”，而是明确要求“进入编辑器后真实可玩、真实可见、真实可交互”。

核心原则如下：

1. `CreateWidget()` 成功不等于 HUD 可见。
2. `HUDWidget != nullptr` 不等于按钮可点击。
3. `--no-editor` 回归通过不等于编辑器内可玩。
4. 默认地图、默认 GameMode、基础光照、输入焦点都属于“可玩运行时需求”，不是环境细节。
5. 所有成功结论都必须有证据：日志、截图、配置文件或报告。

## 2. 新增总则

## 2.1 Playable Runtime Contract

只要 TASK 06 的目标写着“可运行”或“可玩”，就默认必须同时满足下面 6 条：

1. 打开编辑器后能够进入目标地图或明确可一键打开目标地图。
2. 点击 Play 后场景可见，不允许整屏纯黑。
3. 目标 GameMode、GameState、PlayerController 已按设计实例化。
4. HUD 在视口中真实可见。
5. 鼠标光标可见，且至少一个 UI 按钮可点击。
6. 至少能完成一个完整回合的人工验证。

## 2.2 UMG Runtime Contract

如果 Widget 采用“纯 C++ 运行时构建”方案，任务里必须显式写明：

1. 默认优先使用 `RebuildWidget()`、`NativeOnInitialized()` 或等效安全时机构建控件树。
2. 不将 `NativeConstruct()` 视为唯一安全的首次建树时机。
3. Widget owner 默认优先为 `PlayerController`。
4. 输入模式由单一责任方统一管理，避免 `GameMode` 与 `PlayerController` 相互覆盖。

## 2.3 集成基线 Contract

以下项目一律视为 M3 集成基线，不再作为“可选优化”：

1. `EditorStartupMap`
2. `GameDefaultMap`
3. 默认 `GameMode`
4. 基础光照或等效可见性方案
5. HUD 输入焦点链路
6. Popup 焦点恢复链路

## 3. 里程碑定义

| 里程碑 | 内容 | 对应 TASK | 完成标准 |
|------|------|-----------|----------|
| M1 | Schema + Compiler 骨架 | TASK 02 | 结构化产物合法，旧链路不破 |
| M2 | Main Chain 样本数据 | TASK 04 | 11 JSON 产物齐备且可校验 |
| M3 | MonopolyGame 垂直切片运行时 | TASK 06 | 代码通过、运行时可见、HUD 可交互、人工冒烟通过 |
| M4 | 兼容性清理 + 最终验收 | TASK 07 | 自动化回归通过 + 编辑器冒烟留证 + 测试编号补录 |

## 4. 任务总览

阶段 1 入口统一（TASK 01）  
阶段 2 Schema + Compiler 骨架（TASK 02）  
阶段 3 Skill Template + MCP（TASK 03）  
阶段 4 Main Chain 数据（TASK 04）  
阶段 5 C++ 设计 + 交接（TASK 05）  
阶段 6 垂直切片执行（TASK 06）  
阶段 7 验收（TASK 07）

---

## TASK 01：文档与入口统一

保留原目标，但新增两条硬约束：

1. `Docs/Current/` 必须明确记录“可玩运行时需要编辑器内 Play 冒烟验证”。
2. `Docs/Current/04_Open_Risks.md` 必须显式列出“编辑器级运行时冒烟验证缺口”风险。

【新增验收标准】

- [Docs/Current/04_Open_Risks.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/04_Open_Risks.md) 中存在编辑器冒烟风险项。
- [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md) 中可找到运行时复盘或改进任务草案入口。

---

## TASK 02：Schema + Compiler 骨架

保留原有结构任务，但新增一条约束：

1. 对于 UI / Runtime 类产物，Schema 或生成结果中必须能表达“可见性 / 输入 / 运行时交互”类信息，而不仅是对象名和控件树。

【新增验收标准】

- UI 相关样本数据中能反映 HUD、Popup、交互绑定或可玩运行时要求。

---

## TASK 03：Skill Template + MCP

保留原目标，但新增：

1. Skill UI 模板里应明确区分“布局存在”与“可交互运行时行为”。
2. MCP 或辅助脚本应能够回收运行时证据，如截图、日志或当前地图配置。

【新增验收标准】

- UI 模板不只包含控件树描述，还包含可交互约束。
- 运行时证据可以归档到 `ProjectState/Reports/` 或 `ProjectState/Evidence/`。

---

## TASK 04：Main Chain 数据生成

保留 11 JSON 产物目标，但新增：

1. `ui_flow_spec` 不仅描述 5 个 WBP 和控件树，还应描述 HUD 是否常驻、按钮是否可点击、Popup 是否可关闭与恢复焦点。
2. `build_ir` 或等效 lowering 结果中应出现“默认地图 / 默认 GameMode / 集成基线 / 人工冒烟”要求。

【新增验收标准】

- `skill-ui.json` 能区分 HUD 常驻与 Popup 临时显示语义。
- `build_ir` 或交接材料中存在运行时集成约束。

---

## TASK 05：详细设计 + 交接

这一阶段必须显式补齐两类内容：

### 5.1 技术设计必须写清

1. HUD / Popup 的运行时构建时机。
2. 输入模式由谁负责设置。
3. Widget owner 由谁提供。
4. 默认地图 / 默认 GameMode / 光照由配置还是运行时解决。
5. 编辑器内 Play 的人工冒烟步骤。

### 5.2 交接文档必须避免的危险口径

1. 不允许只写“在 `NativeConstruct()` 里构建 WidgetTree”而不说明生命周期风险。
2. 不允许只写“Widget 可 CreateWidget”而不写“可见 / 可点击”验收。
3. 不允许只交付控件树，不交付输入与焦点策略。

【新增验收标准】

- 交接文档中包含“运行时集成前置条件”章节。
- 交接文档中包含“编辑器内 Play 冒烟步骤”章节。
- 交接文档中包含“HUD / Popup 生命周期与焦点链路说明”章节。

---

## TASK 06：执行 MonopolyGame 垂直切片（M3）

本任务改成“两层交付 + 四层验证”。

### 6.1 交付层 A：代码与对象

保留原本 11 个 C++ 类、地图、WBP、运行逻辑等交付内容。

### 6.2 交付层 B：可玩运行时集成

新增以下必须交付的集成项：

1. `EditorStartupMap` 指向 `L_MonopolyBoard`
2. `GameDefaultMap` 指向 `L_MonopolyBoard`
3. 默认 `GameMode` 指向 `AMMonopolyGameMode`
4. 场景具备基础可见性，不允许黑屏
5. HUD 进入视口后真实可见
6. 鼠标可见，HUD 主按钮可点击
7. Popup 可见、可关闭、关闭后焦点恢复

### 6.3 Batch 设计

#### Batch 0：集成前置条件

在正式写逻辑前，先完成以下集成检查：

1. 地图与默认配置绑定
2. 场景基础可见性方案
3. PlayerController 输入责任归属
4. UI owner 责任归属

【Batch 0 验收标准】

- [Config/DefaultEngine.ini](/D:/UnrealProjects/Mvpv4TestCodex/Config/DefaultEngine.ini) 中能看到目标地图配置。
- [Config/DefaultGame.ini](/D:/UnrealProjects/Mvpv4TestCodex/Config/DefaultGame.ini) 或地图 World Settings 中能确认目标 GameMode。

#### Batch 1：类型与壳类

与原任务一致。

#### Batch 2：BoardManager / Tile / Pawn / 地图

在原任务基础上新增：

1. 地图进入后至少能看到棋盘、Pawn 或占位几何。
2. 如果地图资源本身不带光照，必须在本 Batch 明确由运行时提供基础光照。

#### Batch 3：FSM + 骰子逻辑

与原任务一致，但要求日志或状态切换可观察。

#### Batch 4：经济 / 监狱 / 破产

与原任务一致，但所有 Popup 路径必须真实经过同一套可显示的 UI 通道。

#### Batch 5：UI + 事件绑定

这一步重写为：

1. HUD / Popup 的控件树必须在安全生命周期构建。
2. HUD `AddToViewport()` 后必须显式校验可见性。
3. `PlayerController`、`GameMode`、HUD 三者的输入模式与焦点责任必须一致。
4. 绑定不只验证 Delegate 是否存在，还要验证点击后有可观察状态变化。

【Batch 5 验收标准】

- HUD 在视口中真实可见，不接受仅 `HUDWidget != nullptr`。
- 至少一个 HUD 按钮点击后，能推动状态变化或产生日志。
- Popup 可显示、可关闭、可回到 HUD 焦点。

### 6.4 M3 验收从“12 个验证点”升级为“4 层验证”

#### L0：编译验证

1. UHT 通过
2. Editor 编译通过

#### L1：逻辑验证

保留原 12 个逻辑验证点，但将 UI 验证升级：

- 原 `val-11` 替换为：
  - `val-11a`：HUD 已加入视口并可见
  - `val-11b`：HUD 主内容存在且非空白
  - `val-11c`：至少一个 HUD 按钮可点击
- 原 `val-12` 替换为：
  - `val-12a`：Popup 可显示
  - `val-12b`：Popup 可关闭
  - `val-12c`：Popup 关闭后 HUD 焦点恢复

#### L2：无头日志验证

必须看到以下关键日志：

1. `MonopolyGameMode BeginPlay`
2. `HUD RebuildWidget` 或等效建树日志
3. `HUD widget created`
4. `HUD input mode refreshed`
5. `PlayerController BeginPlay`

#### L3：编辑器内 Play 冒烟

这是 M3 阻塞项，不通过就不能宣告完成。

人工验证步骤：

1. 打开 `L_MonopolyBoard`
2. 点击 Play
3. 确认场景非黑屏
4. 确认 HUD 可见
5. 确认鼠标可点击 HUD 主按钮
6. 完成至少一轮 `掷骰 -> 移动/结算 -> 结束回合`

### 6.5 M3 证据要求

M3 通过必须附带以下证据：

1. 一份编译通过记录
2. 一份无头日志
3. 一张编辑器内 Play 截图
4. 一份人工冒烟结论报告

【M3 总验收标准】

- L0 / L1 / L2 / L3 四层验证全部通过。
- 所有成功结论均有证据文件。
- 如果只通过自动化、不通过编辑器冒烟，则 M3 判定为“未完成”。

---

## TASK 07：兼容性清理与最终验收（M4）

M4 保留原有回归任务，但新增“运行时交互验收闭环”。

### 7.1 保留项

1. `run_system_tests.py --no-editor`
2. `validate_examples.py --strict`
3. `run_greenfield_demo.py simulated`
4. 稳定区 diff 审核

### 7.2 新增项

1. 编辑器内 Play 冒烟必须归档到测试编号体系。
2. 默认地图、默认 GameMode、基础光照、HUD 可见、按钮可点击必须作为 Phase 8 新增测试口径补录。
3. 最终验收报告中必须明确区分：
   - 自动化通过
   - 无头运行通过
   - 编辑器内人工冒烟通过

### 7.3 建议新增的测试编号方向

1. `E2E-xx`：打开目标地图并进入 Play
2. `E2E-xx`：HUD 可见与主按钮可点击
3. `E2E-xx`：Popup 可显示与焦点恢复
4. `E2E-xx`：默认地图 / 默认 GameMode 配置正确
5. `E2E-xx`：场景基础光照可见

【M4 总验收标准】

- 自动化回归通过
- 无头运行时验证通过
- 编辑器内冒烟验证通过
- Phase 8 新增测试编号已补录
- 最终报告明确列出自动化、无头、人工三类结论

## 5. 这版草案如何覆盖本次问题

这版草案专门针对本次暴露的问题补了 5 个口子：

1. 用“HUD 可见 / 按钮可点击”替代“HUDWidget != nullptr”。
2. 用“Batch 0 集成前置条件”提前锁住默认地图、默认 GameMode 和基础光照。
3. 用“UMG Runtime Contract”避免把 `NativeConstruct()` 当成唯一安全建树时机。
4. 用“输入责任归属”避免 `GameMode` 和 `PlayerController` 互相覆盖焦点。
5. 用“L3 编辑器内 Play 冒烟”堵上 `--no-editor` 无法发现的真实交互问题。

## 6. 使用建议

如果后续你想正式采纳这版草案，我建议按下面顺序推进：

1. 先保留现有 [task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md) 作为历史执行记录。
2. 将这份草案评审后升级为下一阶段正式任务文档。
3. 同步把新增验收点补到系统测试编号与人工验收模板里。

## 7. 关联文档

- Phase 8 运行时复盘：[08_Phase8_Retrospective_And_Phase9_Checklist.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Phase8_Retrospective_And_Phase9_Checklist.md)
- HUD / 输入修复证据：[phase8_hud_input_fix_20260405.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase8_hud_input_fix_20260405.md)
- 当前历史任务入口：[task.md](/D:/UnrealProjects/Mvpv4TestCodex/task.md)
