# Compiler Generation Module

## 当前状态
Phase 4 已实装最小自动生成链。

## 职责

Generation 模块负责在 `Static Spec Base` 约束下，将 `design_input` 转为 `dynamic_spec_tree`。

## 当前文件结构

```text
generation/
├── __init__.py
├── static_base_loader.py
├── spec_generation_dispatcher.py
└── boardgame_scene_generator.py
```

## 当前能力

1. 读取 `Specs/StaticBase/Registry/spec_type_registry.yaml`
2. 加载 Phase 4 启用的静态基座模板 / schema / manifest
3. 读取最小 `boardgame` 类型包 manifest
4. 生成 richer spec 节点：
   - `world_build_spec`
   - `boardgame_spec`
   - `validation_spec`
5. 投影为兼容现有 orchestrator 的 `scene_spec.actors[]`

## 阶段边界

- 当前只支持 `boardgame` 的 Greenfield prototype
- 当前不实现完整 Skill Pack runtime
- 当前不实现 Brownfield delta generation
