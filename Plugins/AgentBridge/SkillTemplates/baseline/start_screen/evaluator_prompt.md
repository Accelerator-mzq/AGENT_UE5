# Evaluator Prompt — Start Screen 自检

请对你生成的 start_screen_spec 进行以下检查：

## 必过检查项

1. **能力完整性**：required_elements 是否包含 project_identity_display、user_interaction_trigger、navigate_to_main_menu？
2. **实现方式合法**：implementation 是否为 independent_level / main_menu_pre_state / frontend_shell_page 之一？
3. **presence_only 约束**：如果 realization_class 为 presence_only，implementation 是否为 independent_level（默认方式）？
4. **产出物完整**：是否声明了 Widget + C++ 基类需求？
5. **无越界内容**：是否包含主菜单逻辑、gameplay 逻辑、动画效果？
6. **Phase 范围**：是否有任何超出当前 Phase 的内容？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
