# Domain Prompt — Main Menu 主菜单

## 领域边界

本 Skill 处理游戏的 **主菜单**，即玩家从 Start Screen 进入后看到的功能导航页面。

## 最低标准（presence_only）

主菜单必须包含以下三个按钮及其回调：

| 按钮 | 导航目标 | 说明 |
|------|---------|------|
| New Game | Gameplay Level / 玩家设置 | 开始新游戏 |
| Settings | Settings 子页面 | 打开设置页 |
| Quit | 退出游戏 | 关闭应用 |

## 范围约束

### 必须处理
- 确认三按钮存在
- 定义每个按钮的导航目标
- 声明 Widget + C++ 基类需求
- 定义按钮交互方式（键鼠 Click）

### 不处理
- Settings 页面具体控件（由 settings 处理）
- 游戏启动参数配置（如玩家人数选择，由 gameplay 域处理）
- 按钮视觉样式、动画效果（presence_only 不做）
- 背景画面、音乐（presence_only 不做）
- 多语言 / 本地化
- Continue / Load Game（Phase 1 不做存档）

## realization_eligible 时的设计维度

如果升级为 realization_eligible，以下维度可进入 Discovery：
- 菜单布局方向（水平 / 垂直 / 放射状）
- 背景展示（静态图 / 3D 场景 / 动态效果）
- 按钮进入动画
- 背景音乐与音效
- 附加信息展示（版本号、制作组、法律声明）
