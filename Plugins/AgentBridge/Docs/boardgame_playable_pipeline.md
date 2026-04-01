# Boardgame Playable Pipeline

> 文档版本：v0.5.0（Phase 6 口径）

## 1. 文档目的

本文档说明 Phase 6 中，`boardgame_tictactoe_v1.md` 如何从 GDD 被编译为完整 Spec Tree，并投影为最小可玩 runtime。

## 2. 输入与输出

### 输入

- 项目层 GDD：`ProjectInputs/GDD/boardgame_tictactoe_v1.md`
- 可选项目状态：`project_state_intake.py`
- Static Base：`Specs/StaticBase/`
- Contracts：`Specs/Contracts/`
- Genre Pack：`Skills/genre_packs/boardgame/`

### 输出

- `dynamic_spec_tree`
- `Reviewed Handoff`
- `ProjectState/RuntimeConfigs/runtime_<handoff_id>.json`
- `scene_spec.actors[]`

## 3. 标准 Spec Tree 节点

Phase 6 的 boardgame 编译结果至少包含：

- `world_build_spec`
- `boardgame_spec`
- `board_layout_spec`
- `piece_movement_spec`
- `turn_flow_spec`
- `decision_ui_spec`
- `runtime_wiring_spec`
- `validation_spec`
- `scene_spec`
- `generation_trace`

## 4. 两种投影

### 4.1 `preview_static`

用途：

- 延续 Phase 4/5 的 Greenfield / Brownfield 回归
- 在场景中直接投影 `Board + preview pieces`

当前仍是默认投影。

### 4.2 `runtime_playable`

用途：

- 面向 Phase 6 的“完整树 + 可玩 runtime”验收
- 在场景中投影 `BoardRuntimeActor`
- 运行时通过 `runtime_<handoff_id>.json` 初始化

## 5. Compiler 当前链路

```text
boardgame_tictactoe_v1.md
→ design_input_intake
→ genre_pack_core（registry / manifest_loader / module_loader）
→ boardgame required_skills
   ├── board_layout
   ├── piece_movement
   └── turn_system
→ boardgame review_extensions / validation_extensions / delta_policy
→ handoff_builder
→ run_plan_builder
→ handoff_runner
```

## 6. 项目层运行时承载

当前项目层运行时承载体为：

- `Source/Mvpv4TestCodex/BoardgamePrototypeBoardActor.h`
- `Source/Mvpv4TestCodex/BoardgamePrototypeBoardActor.cpp`

该 Actor 当前负责：

- 读取 runtime config
- 处理点击落子
- 交替生成 X/O
- 胜利 / 平局判定
- 返回最小状态读回

## 7. 当前入口

- 预览链路：`Scripts/run_greenfield_demo.py`
- Brownfield 链路：`Scripts/run_brownfield_demo.py`
- Phase 6 playable runtime 主入口：`Scripts/run_boardgame_playable_demo.py`

## 8. 当前边界

- playable runtime 只覆盖当前井字棋样板
- 当前 Orchestrator 只做最小 runtime 兼容，不重构稳定执行主链
- Brownfield 真实执行仍主要是 `append / no_change`
- turn/ui patch 当前仍以 contract + review 阻断为主，不承诺完整自动 patch
