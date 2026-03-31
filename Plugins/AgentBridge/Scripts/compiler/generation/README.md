# Compiler Generation Module

## 当前状态
📦 **占位目录** - 第一阶段暂未实现

## 职责

Generation 模块负责从设计输入生成 Dynamic / Delta Spec Tree。

### 计划能力

1. **Spec Generation Dispatcher**
   - 全量 Spec 生成调度（Greenfield）
   - 根据 design_input 和 routing_context 选择合适的生成器

2. **Delta Generation Dispatcher**
   - 增量 Spec 生成调度（Brownfield）
   - 根据 delta_scope 生成 patch / expansion plan

### 计划文件结构

```
generation/
├── __init__.py
├── spec_generation_dispatcher.py
└── delta_generation_dispatcher.py
```

## 第一阶段

第一阶段的 Spec Tree 生成采用**最小手工构造**方式：
- 在 `handoff/handoff_builder.py` 中直接构造简单的 scene_spec
- 不做复杂的自动生成逻辑

这样可以快速验证整个链路，避免在生成逻辑上花费过多时间。

## 未来扩展方向

后续阶段将实现：
- 从 GDD 自动提取场景需求
- 根据 boardgame 类型包规则生成棋盘布局
- 根据 Static Spec Base 生成符合规范的 Spec
- 支持模板化生成（基于 Specs/Templates/）

## 为什么第一阶段不做深

1. **验证链路优先**：先确保 Handoff → Run Plan → 执行 这条链路通
2. **避免过度设计**：生成逻辑需要大量实例积累才能总结出规律
3. **手工构造足够**：第一阶段只需要生成 3 个 Actor，手工构造更快
