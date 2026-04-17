# Universal Game Baseline Standard

> 文档版本：v1.0.0（Phase 11 吸收）
> 原始来源：Docs/Phase11/03_Universal_Baseline_Standard.md

## 1. 定义

Universal Game Baseline Standard 定义所有游戏都应被检查的一组通用基础能力标准。它用于防止 GDD 只写玩法、不写产品壳层和基础体验，导致 Agent 在实现时漏项。

**核心原则**：Universal Baseline 不只是 capability checklist，还是 Baseline Design Space 的正式上游标准。

---

## 2. 两层结构

### 2.1 Baseline Presence Contract
- 这一项能力要不要有
- 当前 Phase 要做到什么程度
- 是 required / optional / deferred / blocked

### 2.2 Baseline Realization Design Space
- 这一项能力如何承载
- 哪些实现维度允许发散
- 哪些维度需要 Clarification
- 哪些维度只能保守默认

详见 `baseline_realization_policy.md`。

---

## 3. Baseline Categories

### 3.1 启动与入口
- **Start Screen（入口壳层）**
  - 能力要求：必须存在进入主菜单前的可达入口壳层
  - 必须展示项目标识（项目名称或 Logo）
  - 必须有明确的用户交互触发进入主菜单
  - 默认实现：独立 Level + Widget
  - 可选���现：主菜单前态 / Frontend Shell 前置状态
- 初始加载 / Logo / Splash（如项目需要）

### 3.2 前台壳层与页面流转
- **主菜单**：New Game / Settings / Quit（最少三项）
- **暂停菜单**：Resume / Settings / Quit to Menu
- **结果页**：胜者信息 + Return to Menu
- 返回主菜单
- 重新开始
- 关卡 / 页面切换壳层

### 3.3 设置与配置
- **Master Volume** 滑块 — 必须
- **SFX Volume** 滑块 — 必须
- **Window Mode** 切换（Fullscreen / Windowed / Borderless） — 必须
- **Resolution** 下拉选择 — 必须
- **Apply** 按钮 — 必须
- **Back** 按钮 — 必须
- Music Volume 滑块 — 可 defer
- Graphics Quality 预设 — 可 defer
- Key Rebinding — 可 defer
- 持久化到 SaveGame / INI — 可 defer（session 内生效即可）
- Restore Defaults — 可 defer

### 3.4 输入基础
- 键鼠 / 手柄 / 触屏支持策略
- 菜单导航
- 确认 / 取消 / 返回
- 暂停输入
- 输入禁用 / 恢复

### 3.5 HUD / Popup / 结果表达
- 常驻 HUD
- 关键信息提示
- 确认性弹窗
- 局内结果 / 局后结果表达

### 3.6 音频基础
- BGM 播放 / 停止 / 音量控制
- SFX 播放基础
- 音频 profile（如项目需要）

### 3.7 平台基础
- 目标平台适配策略
- 最低帧率 / 分辨率要求
- 退出 / 最小化 / 焦点切换处理

---

## 4. presence_only 最低实现标准

| Baseline 项 | 最低实现 | 产出物 |
|------------|---------|--------|
| **Start Screen** | 入口壳层：展示项目标识 + 用户交互触发 + 导航到主菜单 | Widget + C++ 基类含交互回调 |
| **Main Menu** | New Game / Settings / Quit 三按钮，点击后触发对应导航 | Widget + C++ 基类含三个按钮回调 |
| **Settings** | Master Volume + SFX Volume + Window Mode + Resolution + Apply + Back | Widget + C++ 基类含控件绑定 |
| **Pause** | ESC 弹出暂停 Widget，Resume / Settings / Quit to Menu，SetGamePaused(true) | Widget + C++ 基类 + PlayerController ESC 绑定 |
| **Results** | 胜者信息 + Return to Menu 按钮 | Widget + C++ 基类含 ShowResult() |
| **HUD** | 当前回合数 + 当前玩家标识（具体内容由 gameplay 域决定） | Widget + C++ 基类含最小 data binding |

### 4.1 presence_only 不做的内容
- 不做布局美化（默认居中/堆叠布局即可）
- 不做动画/转场效果
- 不做主题/风格定制
- 不做多语言支持
- 不做自适应布局
- 不做手柄/触屏适配（只做键鼠）

### 4.2 不能再降的底线

Settings 的 Master Volume + SFX Volume + Window Mode + Resolution + Apply + Back 六项是不可删减的底线。低于此标准则不算一个"可用的设置页"。

---

## 5. 升级为 realization_eligible 的触发条件

以下任一条件满足时，该 Baseline 项必须从 presence_only 升级为 realization_eligible：

1. GDD 对该项有明确的设计描述（不只是"需要"，而是描述了"怎样"）
2. 该项直接影响 gameplay feel target
3. 该项与 Gameplay Domain 有强耦合
4. 用户明确要求该项有创造性设计
5. 该项对目标平台有特殊要求

升级是单向的：只能 presence_only -> realization_eligible，不能反向。
