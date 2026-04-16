# Evaluator Prompt — Main Menu 自检

请对你生成的 main_menu_spec 进行以下检查：

## 必过检查项

1. **三按钮完整性**：buttons 是否包含 new_game、settings、quit 三项？
2. **导航目标明确**：每个按钮是否有明确的 navigation_target？
3. **产出物完整**：是否声明了 Widget + C++ 基类需求？
4. **无越界内容**：是否包含 Settings 控件定义、gameplay 逻辑、存档功能？
5. **presence_only 约束**：如果 realization_class 为 presence_only，是否排除了布局样式、动画、背景等设计维度？
6. **Phase 范围**：是否有任何超出当前 Phase 的内容（如 Continue、Load Game）？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
