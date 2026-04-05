# Playable Runtime 验收口径

> 文档版本：L1-Phase7Prep-v1  
> 说明：本文件保留为已归档 `Phase 6` 的 playable runtime 验收参考基线

## 1. 本期“完整 Spec Tree”的最低定义

Phase 6 验收时，boardgame 编译结果至少要同时具备以下节点：

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

## 2. 本期“可玩 runtime”的最低定义

最小可玩 runtime 至少满足：

1. `projection_profile=runtime_playable`
2. `scene_spec.actors[]` 投影到 runtime actor，而不是 preview pieces
3. `ProjectState/RuntimeConfigs/runtime_<handoff_id>.json` 已生成
4. runtime actor 至少支持：
   - `LoadRuntimeConfigFromFile`
   - `ApplyMoveByCell`
   - `GetBoardRuntimeState`
   - `ResetBoard`
5. 至少一轮自动落子序列后，状态可读回
6. 至少一轮真实 UE5 `bridge_rc_api` 执行后，能回读到终局状态

## 3. 最小交互形态

当前 Phase 6 允许的最小交互形态是：

- 点击棋盘格子落子
- 或通过自动化函数调用 `ApplyMoveByCell(Row, Col)` 落子

两者都属于本期可接受的“最小可玩”范围。

## 4. 截图证据要求

真实 UE5 验收时，至少需要两张图：

- `overview_oblique`
- `topdown_alignment`

如果目标是棋类 / boardgame 场景，则 `topdown_alignment` 不是辅助图，而是必需图。  
该截图必须同时满足以下条件：

1. 能看见完整棋盘边界
2. 能看见当前局面中的全部棋子
3. 能直接判断棋子与格子 / 棋盘坐标的对应关系

`overview_oblique` 继续作为辅助证据，用于证明 3D 场景已正确生成；  
但它不能替代 `topdown_alignment` 对“棋局是否可判读”的验证职责。

截图与说明写入：

- `ProjectState/Evidence/Phase6/screenshots/`
- `ProjectState/Evidence/Phase6/notes/`
- `ProjectState/Evidence/Phase6/logs/`

统一调用：

- [capture_editor_evidence.py](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py)

## 5. 当前阶段真机通过口径

本期真机通过至少要同时满足：

1. `BoardRuntimeActor` 成功生成
2. `LoadRuntimeConfigFromFile` 自动执行成功
3. 自动落子序列后 `GetBoardRuntimeState()` 返回可解析终局
4. `overview_oblique` 与 `topdown_alignment` 两张图落盘

对于棋类 / boardgame，还必须额外满足：

5. `topdown_alignment` 能完整覆盖棋盘与全部棋子，且肉眼可判断当前棋局布局是否正确
