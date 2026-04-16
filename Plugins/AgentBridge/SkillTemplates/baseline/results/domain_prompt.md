# Domain Prompt — Results Screen 结果页

## 领域边界

本 Skill 处理游戏的 **结果页**，即游戏结束后展示胜负结果并提供导航的界面。

## 最低标准（presence_only）

### 必须展示
- **胜者信息**：胜出玩家的标识（名称 / 编号）
- **Return to Menu 按钮**：点击后返回主菜单

### 触发方式
- gameplay 域调用 ShowResult(winner_info) 时显示结果 Widget
- 结果页覆盖 gameplay HUD

## 范围约束

### 必须处理
- 胜者信息展示区域
- Return to Menu 按钮及导航
- ShowResult() 入口定义
- 声明 Widget + C++ 基类需求

### 不处理
- 胜负判定逻辑（由 gameplay 域处理）
- 游戏统计详情（总资产、回合数等，presence_only 不做）
- 结果动画 / 特效（presence_only 不做）
- Rematch / Play Again 按钮（Phase 1 不做）
- 排行榜 / 成就
- 多语言 / 本地化

## realization_eligible 时的设计维度

如果升级为 realization_eligible，以下维度可进入 Discovery：
- 结果展示动画（胜利 / 失败差异化）
- 游戏统计面板（总资产、地产数、回合数）
- Rematch 按钮
- 结果页背景与音效
