# JRPG Genre Pack Design

> 状态：Phase 7 历史快照，不再代表 Phase 11 当前主链
> 类型包：`genre-jrpg`  
> 目标：验证第二个真实类型包与治理闭环的最小组合

## 当前定位

本文保留为 **Phase 7 历史方案快照**，用于说明早期 `genre-jrpg` 类型包如何作为“第二个真实类型包”参与 Greenfield / Brownfield / 治理闭环验证。

它不再描述 Phase 11 当前的正式事实。当前 Phase 11 请优先参考：

- [skill_graph_and_domain_skill.md](skill_graph_and_domain_skill.md)
- [compiler_design.md](compiler_design.md)
- [reviewed_handoff_design.md](reviewed_handoff_design.md)
- [run_isolation_compare_promote.md](run_isolation_compare_promote.md)
- [architecture_overview.md](architecture_overview.md)

## 目标

Phase 7 需要一个与 `boardgame` 差异足够大的第二类型包，用来验证：

1. 类型包机制不是只适配棋类
2. 基础域与治理闭环可复用于其他玩法类型
3. Greenfield / Brownfield 在第二类型包下仍有最小工作流

本期固定选择：

- `JRPG Turn-Based`

## 最小玩法闭环（Phase 7 历史口径）

本期 JRPG 只覆盖：

- 回合制战斗场景
- 主角 / 敌人的最小站位
- 最小命令菜单锚点
- 回合队列表达
- 从 GDD 编译出可执行的最小 demo

本期明确不做：

- 大地图
- 背包
- 任务系统
- 复杂 UI
- 完整战斗数值系统

## Pack Manifest（Phase 7 历史口径）

文件：

- `Skills/genre_packs/jrpg/pack_manifest.yaml`

关键字段：

- `pack_id = genre-jrpg`
- `required_skills = battle_layout / turn_queue / command_menu`
- `review_extensions = jrpg_reviewer`
- `validation_extensions = jrpg_validator`
- `delta_policy.provider = jrpg_delta_policy`
- `dependencies.base_domains`
  - `product_scope`
  - `runtime_gameplay`
  - `presentation_asset`
  - `qa_validation`
  - `planning_governance`

## Required Skills（Phase 7 历史口径）

### battle_layout

负责生成：

- `world_build_spec`
- `jrpg_spec`
- `battle_layout_spec`

### turn_queue

负责生成：

- `turn_queue_spec`

### command_menu

负责生成：

- `command_menu_spec`
- `runtime_wiring_spec`

## Review / Validation / Delta（Phase 7 历史口径）

### jrpg_reviewer

最小检查：

- 必需 spec 节点是否存在
- `BattleArena` / `CommandMenuAnchor` 是否存在
- Brownfield 下是否补入最小 battle loop regression 提示

### jrpg_validator

最小验证标记：

- `battle_actor_presence`
- `command_menu_ready`
- `turn_queue_ready`

### jrpg_delta_policy

最小 Brownfield 策略：

- `regression_focus`
  - `existing_actor_presence`
  - `jrpg-battle-loop-smoke-check`
  - `jrpg-command-menu-smoke-check`
- `high_risk_breakpoints`
  - `turn_queue_changed`
  - `command_menu_changed`
  - `runtime_wiring_changed`

## 编译目标（Phase 7 历史口径）

### Greenfield

应能生成最小 spec tree，至少包含：

- `world_build_spec`
- `jrpg_spec`
- `battle_layout_spec`
- `turn_queue_spec`
- `command_menu_spec`
- `runtime_wiring_spec`
- `validation_spec`
- `scene_spec`
- `generation_trace`

### Brownfield

应能在已有 `BattleArena / HeroUnit_1` 的 baseline 上表达最小增量：

- `EnemyUnit_1`
- `CommandMenuAnchor`

## Demo 入口（Phase 7 历史口径）

以下入口描述的是 Phase 7 时期的 JRPG demo 运行方式，不是 Phase 11 当前默认开发入口。

文件：

- `ProjectInputs/GDD/jrpg_turn_based_v1.md`
- `Scripts/run_jrpg_turn_based_demo.py`

本期目标：

- `simulated + greenfield_bootstrap` 可跑
- `simulated + brownfield_expansion` 可跑
- 保留 `bridge_rc_api` 真机 smoke 入口，但 Phase 7 当前不把它作为默认开发阻塞

## 验收口径（Phase 7 历史口径）

满足以下条件即可判定 JRPG 第二类型包最小闭环成立：

1. router 能命中 `genre-jrpg`
2. required skills / reviewer / validator / delta policy 能加载
3. Greenfield compile 能生成最小 JRPG spec tree
4. Brownfield delta 能表达最小增量
5. `run_jrpg_turn_based_demo.py simulated` 可成功执行
