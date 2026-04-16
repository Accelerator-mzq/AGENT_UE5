# Domain Prompt — Settings 设置页

## 领域边界

本 Skill 处理游戏的 **设置页**，提供音频和显示设置控件。

## 不可删减底线（六项）

| 控件 | 类型 | 范围 / 选项 | 说明 |
|------|------|------------|------|
| Master Volume | 滑块 | 0.0 ~ 1.0 | 主音量 |
| SFX Volume | 滑块 | 0.0 ~ 1.0 | 音效音量 |
| Window Mode | 切换 | Fullscreen / Windowed / Borderless | 窗口模式 |
| Resolution | 下拉 | 系统支持的分辨率列表 | 显示分辨率 |
| Apply | 按钮 | — | 应用设置 |
| Back | 按钮 | — | 返回上级菜单 |

低于此标准则不算一个"可用的设置页"。

## 可 defer 项（Phase 2+）

- Music Volume 滑块
- Graphics Quality 预设（Low / Medium / High / Ultra）
- Key Rebinding
- 持久化到 SaveGame / INI（Phase 1 session 内生效即可）
- Restore Defaults 按钮

## 持久化策略

- presence_only 默认 `session_only`：设置在当前游戏 session 内生效，重启后恢复默认
- realization_eligible 可通过 Discovery 选择 SaveGame 或 INI 持久化

## 范围约束

### 必须处理
- 六项底线控件定义
- 每个控件的类型、范围、默认值
- 声明 Widget + C++ 基类需求

### 不处理
- gameplay 设置（难度、AI 行为等）
- 主菜单 / 暂停菜单的导航入口（由对应域处理）
- 控件视觉样式（presence_only 使用默认）
- 多语言 / 本地化
- 手柄 / 触屏适配（Phase 1 只做键鼠）
