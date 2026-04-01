# 当前风险

> 文档版本：L1-Phase6-v2

## 仍然存在的风险

### R1：playable runtime 当前是样板化实现

- 当前 `BoardgamePrototypeBoardActor` 面向井字棋样板设计
- 它足以验证 “完整 Spec Tree -> runtime_playable -> runtime config -> runtime actor” 主线
- 但还不代表 boardgame runtime 已完成泛化

### R2：真实 UE5 smoke 已通过，但重复稳定性仍需观察

- `runtime_playable` 的真实 UE5 Editor + RC API + 截图证据已完成一次闭环
- 当前仍需观察多次重复执行时是否出现 RC 时序漂移、截图任务偶发超时或临时关卡差异

### R3：Brownfield 的 runtime/ui patch 仍未自动执行

- 当前已能在 delta 分析与 reviewer 层表达 `TurnFlowPatchContract` / `DecisionUIPatchContract`
- 但真实执行仍然只闭环 `append / no_change`

## 已缓解项

- `_core` 占位问题已缓解：现已落地真实 loader / registry / module loader
- `boardgame pack` 仅 manifest 占位问题已缓解：现已接入 required skills / extensions / delta policy
- C++ runtime actor 的“是否可编译”风险已缓解：UBT 本地编译已通过
- 真实 UE5 playable runtime 真机门禁已缓解：`bridge_rc_api`、自动落子与截图证据均已完成一次成功闭环
