# Compiler Review Module

## 当前状态
Phase 4 已实装最小 Cross-Spec Review。

## 职责

Review 模块负责在执行前做编译期静态审查，避免非法 `dynamic_spec_tree` 进入 Orchestrator。

## 当前文件结构

```text
review/
├── __init__.py
└── cross_spec_reviewer.py
```

## 当前检查项

1. 必需静态基座是否存在
2. Actor 名称是否重复
3. `actor_class` 是否为空
4. `transform` 是否为合法三元组
5. 预览棋子是否与 `piece_catalog` / `prototype_preview` 一致
6. `capability_gaps` 是否按 Phase 4 约定输出

## 输出语义

- 审查通过：`status=reviewed`
- 审查失败：`status=blocked`

## 阶段边界

- 当前不做深层语义分析
- 当前不实现 Brownfield patch / regression contract 检查
