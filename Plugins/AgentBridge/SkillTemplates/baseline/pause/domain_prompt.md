# Domain Prompt — Pause Menu 暂停菜单

## 领域边界

本 Skill 处理游戏的 **暂停菜单**，即玩家在 gameplay 中按 ESC 键弹出的暂停界面。

## 最低标准（presence_only）

### 触发方式
- ESC 键绑定到 PlayerController
- 按下 ESC 时调用 SetGamePaused(true) 并显示暂停 Widget
- 再次按 ESC 或点击 Resume 时恢复

### 三按钮

| 按钮 | 动作 | 说明 |
|------|------|------|
| Resume | SetGamePaused(false) + 关闭 Widget | 恢复游戏 |
| Settings | 打开 Settings 子页面 | 复用设置页 Widget |
| Quit to Menu | SetGamePaused(false) + 导航到主菜单 | 退出到主菜单 |

## 范围约束

### 必须处理
- ESC 输入绑定定义
- 三按钮及其动作
- SetGamePaused 状态管理
- 声明 Widget + C++ 基类 + PlayerController 绑定需求

### 不处理
- Settings 页面具体控件（由 settings 处理）
- 在线模式暂停语义（Phase 1 仅本地多人）
- 暂停视觉效果（模糊、变暗等，presence_only 不做）
- 存档 / Quick Save（Phase 1 不做）
- 多人暂停同步
