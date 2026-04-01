# Phase 6 / E2E-28 修复与复测记录（2026-04-02）

## 修复目标

修复 `runtime_playable` 的截图取证逻辑，使 `topdown_alignment` 真正输出：

- 完整棋盘边界
- 全部棋子
- 可直接判读棋子与格子 / 棋盘坐标关系

## 根因判断

旧链路虽然给 `TakeHighResScreenshot` 传入了临时 `CameraActor`，但实际落盘图片并没有稳定使用该相机取景。

因此会出现：

- 证据元数据记录为顶视角
- 实际图片却仍像当前编辑器视口的斜视角

## 代码修复

本次只修改项目内脚本：

- [capture_editor_evidence.py:29](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py:29)
- [capture_editor_evidence.py:34](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py:34)
- [capture_editor_evidence.py:242](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py:242)
- [capture_editor_evidence.py:285](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py:285)
- [capture_editor_evidence.py:391](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py:391)

修复策略：

1. 先调用 UE5 原生 `UnrealEditorSubsystem.SetLevelViewportCameraInfo`
2. 再调用 `GetLevelViewportCameraInfo` 做读回校验
3. 视口机位对齐后，才触发 `TakeHighResScreenshot`

新的截图后端记录为：

- `UnrealEditorSubsystem.SetLevelViewportCameraInfo + AutomationBlueprintFunctionLibrary.TakeHighResScreenshot`

## 复测证据

### 1. Editor 启动与 RC 就绪

- [phase6_editor_start_2026-04-02_rerun.log](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_editor_start_2026-04-02_rerun.log)
- [phase6_rc_info_2026-04-02_rerun.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_rc_info_2026-04-02_rerun.json)

### 2. runtime_playable 真机复跑

- [phase6_bridge_rc_api_rerun_2026-04-02.log](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_bridge_rc_api_rerun_2026-04-02.log)
- [execution_report_handoff.boardgame.prototype.0d7638bd_20260402_014259.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/execution_report_handoff.boardgame.prototype.0d7638bd_20260402_014259.json)
- [phase6_runtime_smoke_20260402_014312.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_runtime_smoke_20260402_014312.json)

### 3. 新截图证据

- [phase6_task_phase6_boardgame_playable_demo_runtime_playable_evidence.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/notes/phase6_task_phase6_boardgame_playable_demo_runtime_playable_evidence.md)
- [phase6_task_phase6_boardgame_playable_demo_runtime_playable_capture.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/logs/phase6_task_phase6_boardgame_playable_demo_runtime_playable_capture.json)
- [phase6_task_phase6_boardgame_playable_demo_runtime_playable_overview_oblique.png](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/screenshots/phase6_task_phase6_boardgame_playable_demo_runtime_playable_overview_oblique.png)
- [phase6_task_phase6_boardgame_playable_demo_runtime_playable_topdown_alignment.png](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Evidence/Phase6/screenshots/phase6_task_phase6_boardgame_playable_demo_runtime_playable_topdown_alignment.png)

## 复测结果

### 功能链路

- `runtime_playable / bridge_rc_api`：通过
- smoke 结果：`X_wins`

### E2E-28 顶视图证据

人工核验结论：

- 新的 `topdown_alignment` 已经是顶视图
- 棋盘边界完整入镜
- 当前局面中的全部棋子已入镜
- 可以直接判断棋子与格子关系

## 最终判定

- `Phase 6` 功能链路：通过
- `E2E-27` 截图证据链：通过
- `E2E-28` 棋类顶视图证据完整性：通过

结论：

> 本次修复已使 `runtime_playable` 的 `topdown_alignment` 取证链路恢复到“真实顶视图 + 可判读棋局”的状态，`E2E-28` 复测通过。
