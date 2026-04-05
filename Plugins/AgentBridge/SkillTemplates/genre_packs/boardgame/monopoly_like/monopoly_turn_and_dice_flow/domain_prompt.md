# Domain Prompt — Monopoly Turn & Dice Flow

## 领域边界

本 Skill 处理 Monopoly Phase 1 的回合流转核心：

### 必须处理
- 游戏初始化：2-4 玩家、初始位置起点、决定先手顺序
- 回合状态机：等待掷骰 → 掷骰 → 计算步数 → 移动棋子 → 触发格子事件 → 检查双数 → 结束/继续
- 骰子规则：2d6、双数（两颗相同）允许再掷、连续三次双数直接入狱
- 移动规则：顺时针移动 steps 格、经过或停在起点时获得 $200
- 玩家轮转：当前玩家回合结束后切换到下一名未破产玩家

### 不处理
- 格子上的具体事件内容（购买/租金/税务/监狱）
- 经济系统（资金、支付）
- 在狱中的行为选择（保释/掷双数出狱/强制支付）
- UI 弹窗设计
- Phase 2 网络同步

## 状态机参考
```
GAME_INIT → TURN_START → WAIT_ROLL → ROLLING → MOVING → 
TILE_EVENT → CHECK_DOUBLES → TURN_END → (next player) TURN_START
                                    ↘ (doubles) WAIT_ROLL
                                    ↘ (triple doubles) SEND_TO_JAIL
```
