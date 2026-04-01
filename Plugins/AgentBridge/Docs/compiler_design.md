# Skill Compiler Plane 设计

> 文档版本：v0.4.0（Phase 6 口径）

## 1. 定位

Skill Compiler Plane 位于设计输入与执行编排之间，负责把：

- GDD / Requirements
- Project State
- Static Spec Base / Contracts

编译为 Reviewed Handoff。

## 2. 当前模块结构

```text
Scripts/compiler/
├── intake/
│   ├── design_input_intake.py
│   └── project_state_intake.py
├── routing/
│   └── mode_router.py
├── analysis/
│   ├── baseline_builder.py
│   ├── delta_scope_analyzer.py
│   └── contract_registry_loader.py
├── generation/
│   ├── static_base_loader.py
│   ├── spec_generation_dispatcher.py
│   ├── boardgame_scene_generator.py
│   └── brownfield_delta_generator.py
├── review/
│   └── cross_spec_reviewer.py
└── handoff/
    ├── handoff_builder.py
    └── handoff_serializer.py
```

## 3. 两条主链

### 3.1 Greenfield

```text
GDD
→ design_input_intake
→ project_state_intake（通常为空项目 fallback）
→ mode_router
→ Static Base generation
→ review
→ Reviewed Handoff
```

### 3.2 Brownfield

```text
GDD + Project State
→ project_state_intake
→ baseline_builder
→ delta_scope_analyzer
→ Contracts
→ brownfield_delta_generator
→ review
→ Reviewed Delta Handoff
```

## 4. 当前输出

### Greenfield

- 输出 full dynamic spec tree
- `scene_spec.actors[]` 供当前 Run Plan Builder 消费

### Brownfield

- 输出 `tree_type=delta`
- `scene_spec.actors[]` 只放本次新增 Actor
- `baseline_context` / `delta_context` / `contract_refs` 写入 Handoff

## 5. 项目层入口

- `python Plugins/AgentBridge/Scripts/compiler_main.py`
- `python Scripts/run_greenfield_demo.py`
- `python Scripts/run_brownfield_demo.py`

## 6. 当前边界

- Greenfield 主链不允许回归
- Brownfield 当前只执行 append/new-actor 样板
- `SystemTestCases.md` 的 Phase 6 用例在阶段归档时再补录
