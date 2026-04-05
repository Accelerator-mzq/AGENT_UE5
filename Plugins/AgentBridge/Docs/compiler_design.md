# Skill Compiler Plane 设计

> 文档版本：v0.8.0（Phase 8 口径）

## 1. 定位

Skill Compiler Plane 位于设计输入与执行编排之间，负责把 GDD 编译为 Reviewed Handoff。

Phase 8 引入 **Skill-First 6 阶段主链**，替代旧的 intake/routing/generation 链路。

## 2. 当前模块结构

### 2.1 Phase 8 新链路（Skill-First 6 阶段，推荐）

```text
Compiler/                          ← 新骨架目录
├── __init__.py
├── intake/
│   └── design_intake.py           ← Stage 1: GDD → GDD Projection
├── planner/
│   └── planner.py                 ← Stage 2: Projection → Planner Output
├── skill_runtime/
│   └── skill_runtime.py           ← Stage 3: Template Pack → Skill Fragments
├── cross_review/
│   └── cross_review.py            ← Stage 4: Fragments → Cross-Review Report
└── lowering/
    └── lowering.py                ← Stage 5: Reviewed Spec Tree → Build IR

对应 Schema（6 个新增）：
- Schemas/gdd_projection.schema.json
- Schemas/planner_output.schema.json
- Schemas/skill_fragment.schema.json
- Schemas/cross_review_report.schema.json
- Schemas/build_ir.schema.json
- Schemas/reviewed_handoff_v2.schema.json

Skill Template Pack：
- SkillTemplates/genre_packs/boardgame/monopoly_like/ （6 套 × 6 文件）

MCP Server（执行通道）：
- MCP/server.py + tool_definitions.py + naming.py + py_channel.py + rc_channel.py
```

### 2.2 旧链路（v0.5.0–v0.7.0，仍保留用于 boardgame/JRPG 回归）

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

并且 Phase 7 起，Compiler 会显式消费：

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

## 6. Phase 7 当前输出

- `dynamic_spec_tree` 同时支持 `boardgame` 与 `jrpg` 两条最小类型包路径：
  - `board_layout_spec`
  - `piece_movement_spec`
  - `turn_flow_spec`
  - `decision_ui_spec`
  - `runtime_wiring_spec`
- `ProjectState/RuntimeConfigs/runtime_<handoff_id>.json`
- `routing_context.projection_profile`

## 7. 当前边界

- Greenfield 主链不允许回归
- Brownfield 当前仍以 append/new-actor 为最小主链
- Phase 7 新测试只维护在根目录 `task.md`，阶段归档时再补录总表
- 第二个类型包固定为 `JRPG Turn-Based`，用于验证多类型扩展而不是替代现有 boardgame 主链
