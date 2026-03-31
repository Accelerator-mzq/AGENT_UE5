# 项目基线

> 文档版本：L1-Phase4-v1
> 基线截止时间：Phase 4（Static Spec Base + 自动 Dynamic Spec 生成）结束

## 已实装能力

### 插件核心（Phase 1-2 已稳定）

- AgentBridge C++ Editor Plugin（UEditorSubsystem）— 核心实现
- Bridge 三通道架构：通道 A（Python Editor Scripting）/ 通道 B（Remote Control API）/ 通道 C（C++ Plugin，推荐）
- 三层受控工具体系：L1 语义工具 > L2 编辑器服务工具 > L3 UI 工具

### L1 / L2 / L3 工具体系（Phase 1-2 已稳定）

- L1 写接口：`import_assets` / `create_blueprint_child` / `spawn_actor` / `set_actor_transform`
- L1 反馈接口：`get_current_project_state` / `list_level_actors` / `get_actor_state` / `get_actor_bounds` / `get_asset_metadata` / `get_dirty_assets` / `run_map_check`
- L3 UI 工具：`click_detail_panel_button` / `type_in_detail_panel_field` / `drag_asset_to_viewport`
- L2 编辑器服务：Commandlet / UAT BuildCookRun / Gauntlet / Automation Test / Automation Spec / Functional Testing

### Skill Compiler Plane（Phase 4 当前状态）

- `Scripts/compiler/intake/design_input_intake.py` — 已能提取 `game_type / feature_tags / board / piece_catalog / rules / initial_layout / prototype_preview / technical_requirements`
- `Scripts/compiler/intake/project_state_intake.py` — 当前仍为 mock 项目状态输入
- `Scripts/compiler/routing/mode_router.py` — Greenfield / Brownfield 模式路由
- `Scripts/compiler/generation/` — Phase 4 已实装
  - `static_base_loader.py`
  - `spec_generation_dispatcher.py`
  - `boardgame_scene_generator.py`
- `Scripts/compiler/review/` — Phase 4 已实装
  - `cross_spec_reviewer.py`
- `Scripts/compiler/analysis/` — 仍为占位（Phase 5 实装）
- `Scripts/compiler/handoff/handoff_builder.py` — 已从手工 3 Actor 切换为自动生成 + review
- `Scripts/compiler_main.py` — Compiler 独立入口已稳定

### Reviewed Handoff / Run Plan / Runner（Phase 3-4 已稳定）

- `Schemas/reviewed_handoff.schema.json` — Handoff 数据契约
- `Schemas/run_plan.schema.json` — Run Plan 数据契约
- `ProjectState/Handoffs/draft/` / `approved/` — Handoff 实例目录
- `Scripts/orchestrator/run_plan_builder.py` — 从 Reviewed Handoff 构建 Run Plan
- `Scripts/orchestrator/handoff_runner.py` — 支持 `simulated / bridge_python / bridge_rc_api`
- `Scripts/run_greenfield_demo.py` — 项目层 Greenfield 端到端运行入口

### Specs / Skills（Phase 4 当前状态）

- `Specs/StaticBase/` — 已从占位升级为 registry + 10 个静态基座
- `Specs/Contracts/` — Patch / Migration / Regression Contract 仍为占位（Phase 5 实装）
- `Skills/genre_packs/boardgame/pack_manifest.yaml` — Boardgame 类型包最小骨架
- `Skills/base_domains/` — Base Skill Domains 仍为占位（Phase 7 完整化）

### 项目层结构

- `ProjectInputs/GDD/` — 设计输入
- `ProjectInputs/Presets/` — 模式路由和编译配置
- `ProjectState/Handoffs/` — Reviewed Handoff 实例
- `ProjectState/Reports/` — 编译、执行、验证报告
- `ProjectState/Snapshots/` — Brownfield 阶段将使用的快照目录

### 已验证闭环

- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` 通过
- `pytest Plugins/AgentBridge/Tests/scripts/test_phase4_compiler.py` 通过
- `python Scripts/run_greenfield_demo.py` simulated 端到端通过
- `python Scripts/run_greenfield_demo.py bridge_rc_api` 已在 2026-03-31 本机完成真实 RC API smoke 闭环

## 当前架构状态

- 引擎版本：UE5.5.4
- 插件版本：v0.4.0
- 项目结构：项目层（输入/配置/实例/治理）+ 插件层（编译/执行/验证框架）
- 当前已完成链路：

```
Design Inputs
→ Static Spec Base
→ 最小 Skill Compilation 主轴
→ Dynamic Spec Tree
→ Reviewed Handoff
→ Run Plan
→ Handoff Runner
→ Bridge
→ UE5
→ Report
```

## 已知限制

- Brownfield 模式仍未实装，是 Phase 5 主目标
- `project_state_intake.py` 当前仍返回 mock 数据
- `Specs/Contracts/` 尚未落地真实 Contract 模型
- Handoff 审批仍为手工文件移动
- 完整 Genre Skill Pack 机制延后到 Phase 6
- 完整 Base Skill Domains 机制延后到 Phase 7
- 不支持 Blueprint 图深度重写、Niagara 图编辑、材质图深度修改等超出既有能力边界的操作
