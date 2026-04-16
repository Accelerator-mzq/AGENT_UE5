# Domain Prompt — Start Screen 入口壳层

## 领域边界

本 Skill 处理游戏的 **入口壳层**，即玩家启动游戏后、进入主菜单前看到的第一个界面。

## 能力级定义（与实现方式解耦）

必须满足的能力：
- **project_identity_display**：展示项目标识（项目名称或 Logo）
- **user_interaction_trigger**：明确的用户交互触发进入主菜单（按键 / 点击 / 自动倒计时）
- **navigate_to_main_menu**：交互后导航到主菜单

## 实现方式选择

| 实现方式 | 说明 | 适用场景 |
|---------|------|---------|
| independent_level | 独立 Level（L_StartScreen）+ Widget | 默认方式，presence_only 首选 |
| main_menu_pre_state | 主菜单 Level 内的前置 Widget 状态 | 减少 Level 切换开销 |
| frontend_shell_page | Frontend Shell Level 内的第一个页面 | 多页面壳层架构 |

presence_only 使用 `independent_level`；realization_eligible 可通过 Discovery 选择替代方式。

## 范围约束

### 必须处理
- 确认项目标识展示方式
- 确认交互触发方式
- 确认导航目标为主菜单
- 输出 Widget + C++ 基类需求

### 不处理
- 主菜单内容（由 main_menu 处理）
- 加载画面 / Loading Screen
- 多语言 / 本地化
- 动画效果和转场（presence_only 不做）
