# Phase 6 目标

> 文档版本：L1-Phase6-v1

## 本期目标

本期目标是把 Phase 5 已打通的 Greenfield/Brownfield 前端能力，继续推进到 **Genre Skill Packs 完整化**，重点完成 boardgame 类型包和 `_core` 机制：

1. 实装 `Skills/genre_packs/_core/` 的最小可用机制：manifest loader / router base / registry
2. 完整化 `Skills/genre_packs/boardgame/`：`required_skills / review_extensions / validation_extensions / delta_policy`
3. 在 `Specs/Contracts/Genres/Boardgame/` 中落地首批 genre contract
4. 让 Compiler 能开始从“仅识别 pack_manifest”走向“真正消费 Genre Pack 机制”
5. 保持 Phase 5 的 Greenfield / Brownfield 闭环不回归
6. 继续遵守 `task.md`、`Snapshots`、`Evidence/Phase6` 的当前期规则

## 成功标准

1. `_core` 至少提供可加载的 manifest loader / registry / router base
2. `boardgame` pack 至少能登记并暴露核心 `required_skills`
3. `review_extensions / validation_extensions / delta_policy` 至少具备最小可装载骨架
4. `Specs/Contracts/Genres/Boardgame/` 至少具备首批 genre contract 骨架
5. `python Scripts/run_greenfield_demo.py` 与 `python Scripts/run_brownfield_demo.py` 继续可跑
6. Phase 6 测试先维护在根目录 `task.md`，阶段归档时再补录到 `SystemTestCases.md`
7. 当前阶段真实证据统一写入 `ProjectState/Evidence/Phase6/`

## 本期不做

- 完整 Base Skill Domains 机制
- 第二个 Genre Pack
- 动态加载 / 热更新类型包
- 完整 patch / migration 自动落地
- 自动化 Handoff 审批治理
- 提前把 Phase 6 用例写进 `SystemTestCases.md`
