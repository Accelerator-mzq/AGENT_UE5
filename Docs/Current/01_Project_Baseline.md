# 项目基线

> 文档版本：L1-Phase8-v1

## 1. 当前事实

- `Phase 6` 已完成并归档，历史任务见 [task4_phase6.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md)。
- `Phase 7` 已完成并归档，历史任务见 [task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)。
- `Phase 8` 正式开发期，当前处于 M3（垂直切片执行）。
- 插件层系统总表与系统测试入口当前统一为 `230` 条口径。

## 2. Phase 8 已产出事实

### 设计文档
- DD-1：`PhaseDoc/Phase8_DD1_Schema_and_Interface_Spec.md`（Schema + Compiler 接口规约）
- DD-3：`PhaseDoc/Phase8_DD3_Lowering_Map_and_CPP_Design.md`（C++ 类设计 + Build Step 映射）
- 交接文档：`PhaseDoc/Phase8_M3_Handover_to_Execution_Agent.md`（含 UMG 布局方案）
- 统一方案：`PhaseDoc/typed-petting-porcupine.md`

### 新增 Schema（6 个）
- `Plugins/AgentBridge/Schemas/{gdd_projection,planner_output,skill_fragment,cross_review_report,build_ir,reviewed_handoff_v2}.schema.json`

### 新增 Compiler 骨架（5 段）
- `Plugins/AgentBridge/Compiler/{intake,planner,skill_runtime,cross_review,lowering}/`

### 新增 Skill Template Pack（6 套 × 6 文件 = 36 文件）
- `Plugins/AgentBridge/SkillTemplates/genre_packs/boardgame/monopoly_like/`

### 新增 MCP Server（6 文件）
- `Plugins/AgentBridge/MCP/{server,tool_definitions,naming,py_channel,rc_channel}.py` + `README.md`

### Main Chain 产物（11 个 JSON）
- `ProjectState/phase8/{gdd_projection,planner_output,cross_review_report,build_ir,reviewed_handoff_v2}.json`
- `ProjectState/phase8/skill_fragments/skill-{board,tile-event,turn,economy,jail,ui}.json`

## 3. 已确认的项目真相

- Phase 6/7 的 `preview_static` 与 `runtime_playable` 仍是回归基线。
- Phase 8 引入 Skill-First 6 阶段主链，替代旧的 intake/routing/generation 链路。
- Reviewed Handoff v2 以 `reviewed_dynamic_spec_tree` 替代 v1 的 `scene_spec.actors` 中心。
- MonopolyGame 是 Phase 8 唯一垂直切片测试案例。
