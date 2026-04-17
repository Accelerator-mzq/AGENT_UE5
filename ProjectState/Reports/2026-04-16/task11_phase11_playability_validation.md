# TASK 11：Monopoly 最小可玩闭环验收

## 结论

本次验收为 **compiler-level playability validation**。以下矩阵验证 GDD 的核心玩法需求已经映射到 skill_graph、skill_fragment、build_ir 或 reviewed_handoff_v3。

## 覆盖矩阵

| 需求 | skill_graph / 节点 | skill_fragment / 结构证据 | build_ir / handoff 证据 | 判定 |
| --- | --- | --- | --- | --- |
| 28 格棋盘 | skill-board-topology | 28 | bir_002_board_topology_spec | 通过 |
| 2-4 玩家 | skill-player-management | [2, 4] | bir_010_player_management_spec | 通过 |
| 初始资金 1500 | skill-economy | 1500 | bir_011_property_economy_spec | 通过 |
| 2D6 掷骰 | skill-dice | 2D6 | bir_003_dice_rule_spec | 通过 |
| 顺时针移动 | skill-board-topology | clockwise | bir_002_board_topology_spec、bir_016_turn_flow_spec | 通过 |
| 经过起点 +200 | skill-turn-loop / skill-economy | 200 | bir_011_property_economy_spec、bir_016_turn_flow_spec | 通过 |
| 地产购买/放弃 | skill-tile-system / skill-economy | tile_system_spec + property_economy_spec | bir_011_property_economy_spec、bir_015_tile_system_spec | 通过 |
| 租金支付 | skill-tile-system / skill-economy | tile_system_spec + property_economy_spec | bir_011_property_economy_spec、bir_015_tile_system_spec | 通过 |
| 税务扣款 | skill-tile-system | tile_system_spec 覆盖格子事件结算 | bir_015_tile_system_spec | 通过 |
| 入狱 | skill-jail | 7 | bir_006_jail_rule_spec | 通过 |
| 破产 | skill-player-management / skill-economy | last_non_bankrupt_player | bir_010_player_management_spec、bir_011_property_economy_spec | 通过 |
| 胜利 | skill-player-management | last_non_bankrupt_player | bir_010_player_management_spec | 通过 |
| HUD 资金/回合显示 | skill-baseline-hud | ["current_player", "player_cash", "turn_number"] | bir_004_hud_spec | 通过 |
| 基础弹窗交互 | skill-baseline-main-menu / pause / results | main_menu_spec + pause_spec + results_spec | bir_007_main_menu_spec、bir_008_pause_spec、bir_012_results_spec | 通过 |

## 摘要

- gameplay fragment 数量：`7`
- build_ir 覆盖 families：`audio_foundation_spec, board_topology_spec, dice_rule_spec, hud_spec, input_foundation_spec, jail_rule_spec, main_menu_spec, pause_spec, platform_foundation_spec, player_management_spec, property_economy_spec, results_spec, settings_spec, start_screen_spec, tile_system_spec, turn_flow_spec`
- handoff design_directions skills：`skill-baseline-hud, skill-board-topology, skill-dice, skill-economy, skill-jail, skill-player-management, skill-tile-system, skill-turn-loop`

## 说明

- run 目录：[run](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260417-051425-aad0)
- 本报告不等同于 UE 运行时 smoke test。
- 若后续接入 UE 侧可执行入口，应再补一轮真实 gameplay smoke。