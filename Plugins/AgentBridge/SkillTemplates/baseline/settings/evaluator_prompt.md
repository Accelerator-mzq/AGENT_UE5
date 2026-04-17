# Evaluator Prompt — Settings 自检

请对你生成的 settings_spec 进行以下检查：

## 必过检查项

1. **六项底线完整**：required_controls 是否包含 master_volume_slider、sfx_volume_slider、window_mode_selector、resolution_selector、apply_button、back_button？
2. **控件类型正确**：滑块有 min/max/default，下拉有 options，按钮有 action？
3. **持久化策略明确**：persistence 是否为 session_only / save_game / ini 之一？
4. **可 defer 项分离**：deferred_controls 是否与 required_controls 不重叠？
5. **产出物完整**：是否声明了 Widget + C++ 基类需求？
6. **无越界内容**：是否包含 gameplay 设置、菜单导航、视觉样式定制？
7. **Phase 范围**：是否有任何超出当前 Phase 的内容？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
