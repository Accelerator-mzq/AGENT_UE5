# Domain Prompt — HUD 常驻界面

## 领域边界

本 Skill 处理游戏的 **常驻 HUD**，即 gameplay 期间始终可见（或按需显示）的信息面板。

HUD 是 **realization_eligible** 的 Baseline 项，因为其内容直接取决于 gameplay 域的数据输出。

## 最低标准

无论 realization 结果如何，HUD 至少必须展示：
- **当前回合数**：绑定到 gameplay 回合计数器
- **当前玩家标识**：绑定到当前活跃玩家的名称/编号

## Gameplay 耦合输入

HUD 内容由 gameplay 域决定。典型的数据绑定源：

| 数据源 | 说明 | 来自哪个 gameplay skill |
|--------|------|----------------------|
| current_turn | 当前回合数 | turn_and_dice_flow |
| current_player | 当前活跃玩家 | turn_and_dice_flow |
| player_money | 各玩家资金 | property_economy |
| player_position | 各玩家位置 | board_topology + turn_and_dice_flow |
| jail_status | 玩家入狱状态 | jail_and_bankruptcy |
| property_ownership | 地产持有状态 | property_economy |

## Design Space Discovery 维度

作为 realization_eligible，以下维度应进入 Discovery：

1. **信息密度**：最小（仅回合+玩家） vs 丰富（资金+地产+位置）
2. **布局方向**：顶部横条 / 侧边栏 / 底部面板 / 角落指示器
3. **玩家信息展示**：列表式 / 轮播式 / 面板式
4. **动态显隐**：始终可见 / 按需展开 / 回合切换时高亮
5. **资金变化反馈**：无反馈 / 数字跳动 / 颜色闪烁

## 范围约束

### 必须处理
- 最小 HUD 元素定义（回合数 + 当前玩家）
- 数据绑定接口声明
- HUD 布局区域定义
- 声明 Widget + C++ 基类需求

### 不处理
- gameplay 逻辑（只消费数据，不产生行为）
- 确认性弹窗（由 gameplay 域触发）
- 结果展示（由 results 处理）
- 暂停菜单覆盖（由 pause 处理）
- 多语言 / 本地化
