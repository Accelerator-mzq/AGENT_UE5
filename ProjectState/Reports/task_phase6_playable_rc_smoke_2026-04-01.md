# Phase 6 Playable Runtime 真机 Smoke 记录

- 生成时间：2026-04-01
- 目标：验证 `runtime_playable` 在真实 UE5 Editor + `bridge_rc_api` 下的最小闭环

## 执行步骤

1. 使用 `Scripts/validation/start_ue_editor_project.ps1` 拉起 UE5 Editor，并确认 RC API 就绪
2. 执行 `python Scripts/run_boardgame_playable_demo.py bridge_rc_api`
3. 让 `BoardRuntimeActor` 自动加载 runtime config
4. 通过 `ApplyMoveByCell` 执行 5 步落子序列
5. 调用 `GetBoardRuntimeState()` 读回终局状态
6. 调用 `capture_editor_evidence.py` 自动写出两张截图与说明

## 关键结果

- RC 启动信息：
  [phase6_rc_info_2026-04-01.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_rc_info_2026-04-01.json)
- Approved Handoff：
  [handoff.boardgame.prototype.9546f07f.yaml](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Handoffs/approved/handoff.boardgame.prototype.9546f07f.yaml)
- Runtime Config：
  [runtime_handoff.boardgame.prototype.9546f07f.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/RuntimeConfigs/runtime_handoff.boardgame.prototype.9546f07f.json)
- 执行报告：
  [execution_report_handoff.boardgame.prototype.9546f07f_20260401_123358.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/execution_report_handoff.boardgame.prototype.9546f07f_20260401_123358.json)
- Runtime Smoke：
  [phase6_runtime_smoke_20260401_123410.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_runtime_smoke_20260401_123410.json)

## 真机状态摘要

- runtime actor 路径：
  `/Temp/Untitled_1.Untitled_1:PersistentLevel.BoardgamePrototypeBoardActor_UAID_78465C3B14CE72CD02_1244370039`
- 自动落子序列：
  - `(0,0)`
  - `(1,1)`
  - `(0,1)`
  - `(2,2)`
  - `(0,2)`
- 终局结果：
  - `result_state = X_wins`
  - `move_count = 5`

## 截图证据

- 说明文件：
  [phase6_task_phase6_boardgame_playable_demo_runtime_playable_evidence.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/notes/phase6_task_phase6_boardgame_playable_demo_runtime_playable_evidence.md)
- 总览图：
  [phase6_task_phase6_boardgame_playable_demo_runtime_playable_overview_oblique.png](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/screenshots/phase6_task_phase6_boardgame_playable_demo_runtime_playable_overview_oblique.png)
- 顶视图：
  [phase6_task_phase6_boardgame_playable_demo_runtime_playable_topdown_alignment.png](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/screenshots/phase6_task_phase6_boardgame_playable_demo_runtime_playable_topdown_alignment.png)
- 证据日志：
  [phase6_task_phase6_boardgame_playable_demo_runtime_playable_capture.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/logs/phase6_task_phase6_boardgame_playable_demo_runtime_playable_capture.json)

## 结论

- Phase 6 的 `runtime_playable` 真机 smoke 已完成一次成功闭环
- 真机链路已同时覆盖：`BoardRuntimeActor` 生成、runtime config 装载、自动落子、终局读回、截图证据落盘
