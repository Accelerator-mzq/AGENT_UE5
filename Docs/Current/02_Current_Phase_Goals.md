# Phase 6 目标

> 文档版本：L1-Phase6-v2

## 本期目标

本期目标是把 Phase 5 已打通的 Greenfield/Brownfield 前端能力，推进到：

1. 从 [boardgame_tictactoe_v1.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/boardgame_tictactoe_v1.md) 自动编译完整 boardgame Spec Tree
2. 完整接入 `Genre Skill Packs _core + boardgame pack`
3. 在 `preview_static` 与 `runtime_playable` 两种投影之间保持清晰分流
4. 在 UE5 中落地最小可玩的井字棋 runtime actor
5. 保持 Phase 4/5 Greenfield / Brownfield 最小闭环不回归
6. 继续遵守 `task.md`、`Snapshots`、`Evidence/Phase6` 的当前期规则

## 成功标准

1. `_core` 已从占位 README 变为真实 loader / registry / router / module loader
2. `boardgame` pack 已具备完整 manifest 和可调用 required skills / extensions / delta policy
3. `dynamic_spec_tree` 默认可生成完整 10 节点 Phase 6 树
4. `projection_profile=preview_static` 不破坏 Phase 4/5 既有 preview 行为
5. `projection_profile=runtime_playable` 能生成 runtime actor + runtime config
6. 项目层 runtime actor 至少支持：
   - `LoadRuntimeConfigFromFile`
   - `ApplyMoveByCell`
   - `GetBoardRuntimeState`
   - `ResetBoard`
7. 至少一轮真实 UE5 `bridge_rc_api` playable runtime smoke + 截图证据闭环成功
8. Phase 6 测试用例先维护在根目录 `task.md`，不提前写入 `SystemTestCases.md`

## 本期不做

- 完整 Base Skill Domains 机制
- 第二个 Genre Pack
- 完整 patch / migration 自动落地
- 自动化 Handoff 审批治理
- 提前把 Phase 6 用例写进 `SystemTestCases.md`
