# Domain Prompt — Monopoly Tile Event Dispatch

## 领域边界

### 必须处理
- 完整 28 格数据表：index, type, name, color_group, price, base_rent
- 8 种格子类型枚举：START, PROPERTY, TAX, CHANCE, COMMUNITY, JAIL_VISIT, FREE_PARKING, GO_TO_JAIL
- 颜色组定义：Brown, LightBlue, Pink, Orange, Red, Yellow, Green, DarkBlue
- 事件分发矩阵：每种格子类型着陆时触发什么事件
- 税务格的固定扣款金额

### Phase 1 事件分发规则
| 格子类型 | 着陆事件 |
|---------|---------|
| START | 无事件（过起点奖励由 turn_flow 处理） |
| PROPERTY | 检查所有权 → 无主则提供购买 / 他人则收租 / 自有则无事件 |
| TAX | 扣除固定金额 |
| CHANCE | Phase 1 无事件（留空槽位） |
| COMMUNITY | Phase 1 无事件（留空槽位） |
| JAIL_VISIT | 无事件（只是探视） |
| FREE_PARKING | 无事件 |
| GO_TO_JAIL | 直接送入监狱 |

### 不处理
- 购买/租金的具体金额计算逻辑（由 property_economy 处理）
- 监狱内的行为逻辑（由 jail_and_bankruptcy 处理）
- 回合流转
