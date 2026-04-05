# Phase 8 复盘与 Phase 9 防回归清单

> 状态：新增于 Phase 8 运行时验收后
> 目的：记录本轮真实暴露的问题、修复归属、根因判断，以及后续阶段必须固化的防回归清单

## 1. 问题与修复归属

### 1.1 Claude 修复的问题

| 问题 | 现象 | 修复结果 | 证据 |
|------|------|----------|------|
| 默认地图未指向 Monopoly 地图 | 打开编辑器时默认进入空白或非目标地图 | 已将启动地图与游戏默认地图指向 `L_MonopolyBoard` | [DefaultEngine.ini:4](/D:/UnrealProjects/Mvpv4TestCodex/Config/DefaultEngine.ini:4) [DefaultEngine.ini:5](/D:/UnrealProjects/Mvpv4TestCodex/Config/DefaultEngine.ini:5) |
| 项目级默认 GameMode 未锁到 Monopoly | 打开地图或进入 Play 时可能未实例化目标 GameMode | 已补全全局 `GlobalDefaultGameMode` | [DefaultGame.ini:4](/D:/UnrealProjects/Mvpv4TestCodex/Config/DefaultGame.ini:4) |
| 场景缺少基础光照 | `L_MonopolyBoard` 进入后整体发黑，难以验证运行时 | 已在运行时自动补 DirectionalLight / SkyLight / SkyAtmosphere | [MMonopolyGameMode.cpp:172](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp:172) [MMonopolyGameMode.cpp:179](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp:179) [MMonopolyGameMode.cpp:191](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp:191) |
| HUD owner / 输入排查起点建立 | HUD 已创建但不可见、鼠标不可交互时缺少排查入口 | 已把 HUD 创建放到 PlayerController owner 链路，并建立输入模式排查基础 | [MMonopolyGameMode.cpp:373](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp:373) |

### 1.2 Codex 修复的问题

| 问题 | 现象 | 修复结果 | 证据 |
|------|------|----------|------|
| HUD 构建时机错误 | 日志显示 HUD 创建成功，但视口中不可见 | 将 WidgetTree 构建从 `NativeConstruct()` 前移到 `RebuildWidget()` | [MGameHUDWidget.cpp:48](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/Widgets/MGameHUDWidget.cpp:48) [MGameHUDWidget.cpp:208](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/Widgets/MGameHUDWidget.cpp:208) |
| Popup 存在同类空白风险 | HUD 修好后，后续弹窗仍可能“创建成功但不可见” | Popup 采用同样的 `RebuildWidget()` 前置构建方案 | [MPopupWidget.cpp:35](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/Widgets/MPopupWidget.cpp:35) [MPopupWidget.cpp:130](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/Widgets/MPopupWidget.cpp:130) |
| HUD 焦点与鼠标交互未完整恢复 | 鼠标可见但按钮不一定可点击 | `CreateHUDWidget()` 后强制刷新 `GameAndUI`、焦点、点击与悬停事件 | [MMonopolyGameMode.cpp:360](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp:360) [MMonopolyGameMode.cpp:391](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp:391) |
| PlayerController 覆盖 HUD 焦点 | HUD 刚设好焦点，`BeginPlay()` 又可能改掉输入模式 | `BeginPlay()` 仅保留鼠标事件开关，不再覆盖 HUD 焦点 | [MMonopolyPlayerController.cpp:11](/D:/UnrealProjects/Mvpv4TestCodex/Source/Mvpv4TestCodex/Private/MMonopolyPlayerController.cpp:11) |
| 缺少修复后运行时证据 | 仅靠肉眼判断不利于追溯 | 已补充修复报告与无头日志证据 | [phase8_hud_input_fix_20260405.md:5](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase8_hud_input_fix_20260405.md:5) [Mvpv4TestCodex.log:1087](/D:/UnrealProjects/Mvpv4TestCodex/Saved/Logs/Mvpv4TestCodex.log:1087) [Mvpv4TestCodex.log:1095](/D:/UnrealProjects/Mvpv4TestCodex/Saved/Logs/Mvpv4TestCodex.log:1095) |

## 2. 根因判断

## 2.1 不是“功能需求完全缺失”

Phase 8 对 HUD / Popup / WBP 的业务目标其实写得比较明确，说明“要做什么”并没有缺失。

- `task.md` 已明确写出 HUD、Popup、5 个 WBP 和绑定要求，见 [task.md:741](/D:/UnrealProjects/Mvpv4TestCodex/task.md:741) 到 [task.md:756](/D:/UnrealProjects/Mvpv4TestCodex/task.md:756)。
- 交接文档也明确给出 HUD / Popup 的结构草案，见 [Phase8_M3_Handover_to_Execution_Agent.md:229](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md:229) 到 [Phase8_M3_Handover_to_Execution_Agent.md:474](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md:474)。

结论：功能目标没有漏，但“集成后必须真的可见、可点击、开箱即用”的验收语义没有被充分固化。

## 2.2 设计方案里存在一个不稳的技术假设

交接文档明确建议“全部在 `NativeConstruct()` 中构建控件树”，见 [Phase8_M3_Handover_to_Execution_Agent.md:452](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md:452) 到 [Phase8_M3_Handover_to_Execution_Agent.md:471](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md:471)。`task.md` 也沿用了同样口径，见 [task.md:943](/D:/UnrealProjects/Mvpv4TestCodex/task.md:943)。

这个方案在“对象能创建出来”层面是成立的，但在 UMG / Slate 生命周期里不够稳，会导致：

- 日志里 `CreateWidget()` 成功
- `WidgetTree->RootWidget` 在 `NativeConstruct()` 里也被设置
- 但 Slate 可见树已经错过正确构建时机，最终视口仍可能空白

结论：这里属于设计实现建议存在技术风险，不是功能需求本身缺失。

## 2.3 测试与验收漏测是主因

M3 的验证点把“存在”当成了“可用”。

- `val-11` 只要求 `HUDWidget != nullptr, PopupWidget 可 CreateWidget`，见 [task.md:973](/D:/UnrealProjects/Mvpv4TestCodex/task.md:973) 到 [task.md:985](/D:/UnrealProjects/Mvpv4TestCodex/task.md:985)。
- 这里没有检查 HUD 是否真实显示在视口里，也没有检查按钮是否真的能点。

M4 的主回归又主要依赖 `--no-editor` 与 simulated 流程。

- 系统测试主入口是 `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`，见 [task.md:1025](/D:/UnrealProjects/Mvpv4TestCodex/task.md:1025) 到 [task.md:1033](/D:/UnrealProjects/Mvpv4TestCodex/task.md:1033)。
- 兼容性验证依赖 simulated demo，而不是编辑器内真实 Play，见 [task.md:1036](/D:/UnrealProjects/Mvpv4TestCodex/task.md:1036) 到 [task.md:1048](/D:/UnrealProjects/Mvpv4TestCodex/task.md:1048)。

这意味着以下问题都容易漏过去：

- 编辑器默认进错图
- 全局 GameMode 未生效
- 场景没有基础光照导致一片黑
- HUD 有对象但不可见
- 鼠标可见但按钮不可点击

结论：这次问题的主因是测试/验收漏测，设计技术假设不稳是次因。

## 2.4 最终判定

用一句话概括这次 Phase 8 的问题来源：

- 业务功能需求没有漏。
- 集成级、交互级验收要求不够具体。
- 测试覆盖明显偏向“对象存在 / 脚本通过 / no-editor 回归”，缺少“编辑器真实 Play”的最后一层冒烟。

因此最终判定是：

**这不是单点实现失误，而是“技术方案里有一个不稳假设 + 验收与测试漏测”，其中以测试漏测为主。**

## 3. Phase 9 防回归清单

## 3.1 必补验收项

后续阶段或下一个垂直切片，至少补齐以下验收项：

1. 编辑器启动默认进入目标地图，或明确要求验证目标地图已在 World Settings / Project Settings 中绑定正确。
2. `GlobalDefaultGameMode` 或目标地图 World Settings 已绑定到目标 GameMode。
3. 场景在 Play 后不是纯黑，至少具备基础可见性。
4. HUD 在进入 Play 后可见，不只是 `CreateWidget()` 成功。
5. HUD 中至少一个主按钮可被鼠标悬停并点击。
6. Popup 不仅能创建，而且能真实显示、关闭，并恢复 HUD 焦点。
7. 至少完成一个完整手动回合：掷骰子、移动、结算、结束回合。
8. 人工验收结论必须有截图或日志留档。

## 3.2 必补测试项

建议新增一类“编辑器级运行时冒烟”测试，不替代现有 `--no-editor`，而是作为补充：

1. 启动编辑器并打开目标地图。
2. 执行一次 Play。
3. 检查 Outliner / 日志 / 截图，确认 GameMode、HUD、Pawn、Tile 都存在。
4. 检查 HUD 可见与鼠标可点击。
5. 将结果补录到 Phase 9 的 E2E 或冒烟测试编号中。

## 3.3 必补文档约束

后续文档中应明确写入以下约束：

1. 如果采用“纯 C++ 运行时构建 UMG”，默认优先评估 `RebuildWidget()` 或等效安全时机，不直接把 `NativeConstruct()` 当成唯一构建入口。
2. 如果交付的是“可玩运行时”，则默认需要一条“编辑器内 Play 冒烟”验收，而不只看对象存在和脚本回归。
3. 默认地图、默认 GameMode、基础光照和输入焦点链路，都属于“可玩运行时”的集成需求，不应只视为环境细节。

## 4. 关联证据

- HUD / 输入修复报告：[phase8_hud_input_fix_20260405.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase8_hud_input_fix_20260405.md)
- HUD 修复后日志证据：[Mvpv4TestCodex.log:1087](/D:/UnrealProjects/Mvpv4TestCodex/Saved/Logs/Mvpv4TestCodex.log:1087) [Mvpv4TestCodex.log:1090](/D:/UnrealProjects/Mvpv4TestCodex/Saved/Logs/Mvpv4TestCodex.log:1090) [Mvpv4TestCodex.log:1095](/D:/UnrealProjects/Mvpv4TestCodex/Saved/Logs/Mvpv4TestCodex.log:1095) [Mvpv4TestCodex.log:1098](/D:/UnrealProjects/Mvpv4TestCodex/Saved/Logs/Mvpv4TestCodex.log:1098)
- Phase 8 交接与任务依据：[Phase8_M3_Handover_to_Execution_Agent.md:452](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md:452) [task.md:943](/D:/UnrealProjects/Mvpv4TestCodex/task.md:943) [task.md:973](/D:/UnrealProjects/Mvpv4TestCodex/task.md:973) [task.md:1025](/D:/UnrealProjects/Mvpv4TestCodex/task.md:1025)
