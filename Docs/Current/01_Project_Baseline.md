# 项目基线

> 文档版本：L1-Phase3-v1
> 基线截止时间：Phase 3（Greenfield + Boardgame + Reviewed Handoff 最小闭环）结束

## 已实装能力

### 插件核心（Phase 1-2 已稳定）

- AgentBridge C++ Editor Plugin（UEditorSubsystem）— 核心实现
- Bridge 三通道架构：通道 A（Python Editor Scripting）/ 通道 B（Remote Control API）/ 通道 C（C++ Plugin，推荐）
- 三层受控工具体系：L1 语义工具 > L2 编辑器服务工具 > L3 UI 工具

### L1 语义接口（Phase 1-2 已稳定）

写接口（4 个，FScopedTransaction）：
- `import_assets` / `create_blueprint_child` / `spawn_actor` / `set_actor_transform`

反馈接口（7 个 + 日志）：
- `get_current_project_state` / `list_level_actors` / `get_actor_state` / `get_actor_bounds` / `get_asset_metadata` / `get_dirty_assets` / `run_map_check` / `get_editor_log_tail`

### L3 UI 工具（Phase 1-2 已稳定）

- `click_detail_panel_button` / `type_in_detail_panel_field` / `drag_asset_to_viewport`
- L3→L1 交叉比对机制已实装

### L2 编辑器服务（Phase 1-2 已稳定）

- Commandlet 无头执行（-Spec / -RunTests / -Tool 三种模式）
- UAT BuildCookRun 构建自动化
- Gauntlet CI/CD 测试会话编排（AllTests / SmokeTests / SpecExecution）

### 验证体系（Phase 1-2 已稳定）

- L1 Simple Automation Test：11 个（Query 7 + Write 4）
- L3 UITool 测试：4 个
- L2 Automation Spec 闭环：5 个（ClosedLoop 3 + UITool 2）
- L3 Functional Testing：AFunctionalTest 子类 + FTEST_WarehouseDemo 地图
- Schema 校验：validate_examples.py --strict → 12/12 通过

### Skill Compiler Plane（Phase 3 新增）

- `Scripts/compiler/intake/design_input_intake.py` — GDD 解析，提取 game_type / board / pieces / rules
- `Scripts/compiler/intake/project_state_intake.py` — 项目状态采集（当前为模拟数据）
- `Scripts/compiler/routing/mode_router.py` — 三级优先级模式路由（显式覆盖 > Preset > 自动检测）
- `Scripts/compiler/handoff/handoff_builder.py` — 从编译结果构建 Reviewed Handoff 结构
- `Scripts/compiler/handoff/handoff_serializer.py` — Handoff 序列化为 YAML 文件
- `Scripts/compiler_main.py` — Compiler 独立运行入口
- 占位模块：`analysis/`（Phase 5）、`generation/`（Phase 4）、`review/`（Phase 4）

### Reviewed Handoff 机制（Phase 3 新增）

- `Schemas/reviewed_handoff.schema.json` — Handoff 数据格式契约
- `Schemas/examples/reviewed_handoff_greenfield.example.json` — Greenfield Handoff 示例
- `ProjectState/Handoffs/draft/` — 草稿 Handoff 存放
- `ProjectState/Handoffs/approved/` — 已审批 Handoff 存放
- 手工审批流程（draft → approved 文件移动）

### Run Plan 机制（Phase 3 新增）

- `Schemas/run_plan.schema.json` — Run Plan 数据格式契约
- `Schemas/examples/run_plan_greenfield.example.json` — Greenfield Run Plan 示例
- `Scripts/orchestrator/run_plan_builder.py` — 从 Reviewed Handoff 生成结构化 Run Plan

### Orchestrator 桥接（Phase 3 新增）

- `Scripts/orchestrator/handoff_runner.py` — Reviewed Handoff 执行入口
  - 支持三种模式：simulated / bridge_python / bridge_rc_api
  - 桥接到现有 Bridge 接口（spawn_actor / set_actor_transform）
- 现有 orchestrator.py 入口保持不变，新增 handoff_runner.py 作为第二入口

### Skills 体系骨架（Phase 3 新增）

- `Skills/base_domains/` — Base Skill Domains 占位（10 个域，Phase 7 完整化）
- `Skills/genre_packs/_core/` — 类型包机制核心占位（Phase 6）
- `Skills/genre_packs/boardgame/` — 首个类型包最小骨架
  - `pack_manifest.yaml` — Boardgame 类型包清单

### Specs 体系骨架（Phase 3 新增）

- `Specs/StaticBase/` — 静态基座占位（Phase 4 实装）
- `Specs/Contracts/` — Patch / Migration Contract 占位（Phase 5 实装）
- `Specs/templates/` — 现有 Spec 模板（3 个，Phase 1-2 已有）

### 项目层结构（Phase 3 新增）

- `ProjectInputs/GDD/` — 游戏设计文档（含 boardgame_tictactoe_v1.md）
- `ProjectInputs/Presets/` — 项目级配置（mode_override.yaml / compiler_profile.yaml）
- `ProjectState/Handoffs/` — Reviewed Handoff 实例（draft / approved）
- `ProjectState/Reports/` — 执行报告
- `ProjectState/Snapshots/` — 项目快照占位

### 端到端管线（Phase 3 新增）

- `run_greenfield_demo.py` — Greenfield 端到端运行入口
- simulated 模式已验证跑通：GDD → Compiler → Handoff → Run Plan → 模拟执行 → Report

### 数据契约

- JSON Schema 体系：6 common + 9 feedback + 1 write_feedback + 2 新增（reviewed_handoff + run_plan） = 18 个 Schema
- 12 个 example JSON
- Spec 模板（YAML）：3 个

### 系统测试（Phase 3 更新）

- 系统测试框架：`Tests/run_system_tests.py`（9 个 Stage，134 条用例）
- Handoff Schema 校验：`Scripts/validation/test_handoff_schema.py`

## 已完成任务

- Phase 1-2：task.md TASK 01–20 全部跑通
- Phase 3：task1.md TASK 01–08 已完成（simulated 模式端到端）
- Phase 3 遗留：TASK 09–11 UE5 真实调用联调待做

## 当前架构状态

- 引擎版本：UE5.5.4
- 插件版本：v0.4.0
- 项目结构：项目壳（Mvpv4TestCodex）+ AgentBridge 插件
- 架构模式：项目层（输入/配置/实例/治理）+ 插件层（编译/执行/验证框架）
- 总链路：Design Inputs → Skill Compiler Plane → Reviewed Handoff → Execution Orchestrator → Bridge → UE5 → Validation → Report

## 已知限制

- 不支持 Blueprint 图深度重写、Niagara 图编辑、材质图深度修改
- 不支持多 Agent 并发、大规模无人监管场景改造
- project_state_intake.py 当前返回模拟数据
- Handoff 审批为手工文件移动
- UE5 真实调用联调未完成（Phase 3 遗留）
- Brownfield 模式未实装（Phase 5）
- Static Spec Base 未实装（Phase 4）
- Phase 2 反馈接口（get_material_assignment 等）待补充
