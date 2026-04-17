# Evaluator Prompt — Pause Menu 自检

请对你生成的 pause_spec 进行以下检查：

## 必过检查项

1. **触发方式明确**：trigger_input 是否指定了 ESC 键？
2. **三按钮完整性**：buttons 是否包含 resume、settings、quit_to_menu 三项？
3. **暂停状态管理**：是否声明了 SetGamePaused(true/false) 调用？
4. **产出物完整**：是否声明了 Widget + C++ 基类 + PlayerController 绑定需求？
5. **无越界内容**：是否包含 Settings 控件定义、在线暂停语义、视觉效果？
6. **Phase 范围**：是否有任何超出当前 Phase 的内容（如 Quick Save、多人暂停同步）？

## 如果检查失败
- 标记 confidence.coverage 为较低值
- 在 review_hints 中说明具体问题
- 在 open_questions 中列出不确定点
