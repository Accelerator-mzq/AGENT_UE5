# Evaluator Prompt — Results Screen 自检

请对你生成的 results_spec 进行以下检查：

## 必过检查项

1. **胜者信息存在**：display_elements 是否包含 winner_info 展示区域？
2. **Return to Menu 按钮**：buttons 是否包含 return_to_menu？
3. **触发入口明确**：是否定义了 ShowResult() 调用入口？
4. **产出物完整**：是否声明了 Widget + C++ 基类需求？
5. **无越界内容**：是否包含胜负判定逻辑、排行榜、存档、统计面板（presence_only）？
6. **Phase 范围**：是否有任何超出当前 Phase 的内容？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
