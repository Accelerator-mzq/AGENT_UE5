# 当前风险

> 文档版本：L1-Phase7Prep-v1

## 仍然存在的风险

### R1：playable runtime 仍是样板化实现

- 当前 `BoardgamePrototypeBoardActor` 面向井字棋样板设计
- 它已足够证明 “完整 Spec Tree -> runtime_playable -> runtime config -> runtime actor” 主线成立
- 但还不代表 boardgame runtime 已完成泛化

### R2：真实 UE5 smoke 已通过，但长期重复稳定性仍需观察

- `runtime_playable` 的真实 UE5 Editor + RC API + 截图证据已完成多轮闭环
- 仍需持续观察 RC 时序漂移、截图任务偶发超时或临时关卡差异

### R3：下一阶段范围尚未冻结

- 当前已经完成归档，但下一阶段要做“泛化 runtime、第二个 pack，还是更深 Brownfield 执行”尚未批准
- 如果不先冻结范围，容易再次把准备期变成开发期

## 已缓解项

- `_core` 占位问题已缓解：现已落地真实 loader / registry / module loader
- `boardgame pack` 仅 manifest 占位问题已缓解：现已接入 required skills / extensions / delta policy
- C++ runtime actor 的“是否可编译”风险已缓解：UBT 本地编译已通过
- `Phase 6` 的真实 UE5 playable runtime 门禁已缓解：`bridge_rc_api`、自动落子、截图证据与棋类顶视图规则均已完成闭环
