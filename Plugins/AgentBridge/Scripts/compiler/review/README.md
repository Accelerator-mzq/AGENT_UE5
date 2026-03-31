# Compiler Review Module

## 当前状态
📦 **占位目录** - 第一阶段暂未实现

## 职责

Review 模块负责 Cross-Spec Review（跨 Spec 审查）。

### 计划能力

1. **引用完整性检查**
   - 检查引用的 Actor 是否存在
   - 检查引用的 Asset 是否存在

2. **字段类型正确性检查**
   - 检查 location 是否是 [x, y, z]
   - 检查 rotation 是否是 [pitch, yaw, roll]

3. **基础约束检查**
   - Actor 名称不重复
   - Transform 值在合理范围内

4. **深度语义分析（未来）**
   - 物理合理性检查
   - 美学合理性检查
   - 性能影响评估

### 计划文件结构

```
review/
├── __init__.py
└── cross_spec_reviewer.py
```

## 第一阶段

第一阶段**不做 Cross-Spec Review**，原因：
1. 需要先积累 Spec 实例，才能总结出常见的审查规则
2. 第一阶段的 Spec 非常简单（只有 3 个 Actor），手工检查即可
3. 避免误报率高的过度设计

## 未来扩展方向

后续阶段将实现：
- 基础一致性检查（引用完整性 / 字段类型）
- 约束冲突检测（如：must_not_overlap + forced_same_location）
- 依赖关系验证（如：Actor A 依赖 Actor B，但 B 不存在）

## 与 Validation 的区别

- **Review**：编译时检查（Spec Tree 生成后，执行前）
- **Validation**：运行时检查（执行后，读回验证）

Review 是静态分析，Validation 是动态验证。
