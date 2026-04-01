# Skill Compiler Plane 设计

> 文档版本：v0.5.0（Phase 6 口径）

## 1. 定位

Skill Compiler Plane 位于设计输入与执行编排之间，负责把：

- GDD / Requirements
- Project State
- Static Spec Base / Contracts
- Genre Pack Core / Genre Pack Modules

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

并且 Phase 6 起，Compiler 会显式消费：

```text
Skills/genre_packs/_core/
Skills/genre_packs/boardgame/
Specs/Contracts/Genres/Boardgame/
```

## 3. 两条主链

### 3.1 Greenfield

```text
GDD
→ design_input_intake
→ project_state_intake（通常为空项目 fallback）
→ mode_router
→ Genre Pack registry / activation
→ Static Base + required_skills generation
→ review_extensions / validation_extensions
→ review
→ Reviewed Handoff
```

### 3.2 Brownfield

```text
GDD + Project State
→ project_state_intake
→ baseline_builder
→ delta_scope_analyzer
→ Contracts + Genre Contracts
→ Genre Pack registry / activation
→ delta_policy + brownfield_delta_generator
→ review
→ Reviewed Delta Handoff
```

## 4. 当前输出

### Greenfield

- 输出 full dynamic spec tree
- `scene_spec.actors[]` 供当前 Run Plan Builder 消费
- 支持两类投影：
  - `preview_static`
  - `runtime_playable`

### Brownfield

- 输出 `tree_type=delta`
- `scene_spec.actors[]` 只放本次新增 Actor
- `baseline_context` / `delta_context` / `contract_refs` 写入 Handoff
- 当前执行主线仍只闭环 `append / no_change`

## 5. 项目层入口

- `python Plugins/AgentBridge/Scripts/compiler_main.py`
- `python Scripts/run_greenfield_demo.py`
- `python Scripts/run_brownfield_demo.py`
- `python Scripts/run_boardgame_playable_demo.py`

## 6. Phase 6 新增输出

- `dynamic_spec_tree` 增加完整 boardgame runtime 节点：
  - `board_layout_spec`
  - `piece_movement_spec`
  - `turn_flow_spec`
  - `decision_ui_spec`
  - `runtime_wiring_spec`
- `ProjectState/RuntimeConfigs/runtime_<handoff_id>.json`
- `routing_context.projection_profile`

## 7. 当前边界

- Greenfield 主链不允许回归
- Brownfield 当前只执行 append/new-actor 样板
- `SystemTestCases.md` 的 Phase 6 用例在阶段归档时再补录
- playable runtime 当前只要求井字棋样板可玩，不承诺泛化到所有 boardgame
