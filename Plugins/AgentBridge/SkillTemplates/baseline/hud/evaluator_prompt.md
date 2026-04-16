# Evaluator Prompt — HUD 自检

请对你生成的 hud_spec 进行以下检查：

## 必过检查项

1. **最低元素存在**：hud_elements 是否至少包含 current_turn 和 current_player 的展示？
2. **数据绑定明确**：每个 hud_element 是否声明了 data_binding 来源？
3. **布局区域定义**：是否定义了 HUD 布局区域（位置、大小策略）？
4. **Gameplay 耦合**：是否声明了需要从哪些 gameplay skill 获取数据？
5. **产出物完整**：是否声明了 Widget + C++ 基类需求？
6. **无越界内容**：是否包含 gameplay 行为逻辑、弹窗触发、结果展示？
7. **Phase 范围**：是否有任何超出当前 Phase 的内容？

## Discovery 质量检查（仅 realization_eligible）

8. **维度完整性**：是否至少探索了信息密度和布局方向两个维度？
9. **候选方向合理**：每个维度的候选方向是否有 trade-off 分析？
10. **收敛有理由**：最终选择是否有 rationale？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
