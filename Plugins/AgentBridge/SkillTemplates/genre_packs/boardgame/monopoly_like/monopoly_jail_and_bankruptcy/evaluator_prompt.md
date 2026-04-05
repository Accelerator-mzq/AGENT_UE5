# Evaluator Prompt — Jail & Bankruptcy 自检

## 必过检查项

1. **入狱条件完整**：是否包含 GO_TO_JAIL 格着陆和三连双数两种触发？
2. **监狱索引一致**：jail_tile_index 是否与 board_topology 中的 jail_visit 一致？
3. **出狱方式完整**：是否包含支付保释、掷双数出狱、第三回合强制支付三种方式？
4. **保释金额**：是否为 $50？
5. **最大关押回合**：是否为 3 回合？
6. **破产触发**：是否为"需要支付但资金不足"？
7. **破产后果顺序**：是否先标记破产、再释放地产为无主、再退出轮转？
8. **游戏结束**：是否为"仅剩 1 名未破产玩家"？
9. **与 turn_flow 的接口**：三连双数入狱是否与 turn_flow 的双数计数器一致？
10. **与 property_economy 的接口**：破产触发是否与 payment_flow 的 insufficient_funds_action 一致？
