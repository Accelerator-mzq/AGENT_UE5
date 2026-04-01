# 当前风险

> 文档版本：L1-Phase6-v1

## 活跃风险

1. `_core` 类型包机制如果直接绑定 boardgame 特例，后续扩展到第二个 Genre Pack 时可能需要返工。
2. `boardgame` pack 的 `required_skills` 若只是 manifest 层声明而未真正接入编译链，会造成“看起来完整、实际未生效”的假闭环。
3. Genre contract 如果过早绑定当前最小 Brownfield 实现，后续可能与更复杂 patch / migration 语义冲突。
4. Phase 5 真机 smoke 虽已通过，但换机或更换引擎安装仍可能因为 BuildId / Editor 启动层问题重新触发 RC 连接失败。
5. Phase 6 如需真实截图证据，若仍沿用 phase5 命名脚本而不做阶段化封装，可能在命名和目录治理上引入混淆。

## 已缓解风险

- Greenfield 主链已稳定，可作为 Phase 6 回归基线
- Brownfield 空壳模块（analysis / Contracts / delta tree）已替换为最小可运行实现
- `Scripts/run_brownfield_demo.py` 已能验证 append-only 样板
- Phase 5 真机 RC API + 截图证据链已闭环
- `ProjectState/Snapshots/` 与 `ProjectState/Evidence/PhaseX/` 已明确分责

## 已验证假设

1. Brownfield Handoff 可以在不修改稳定 Schema 的前提下扩展 `baseline_context` / `delta_context`
2. `scene_spec.actors[]` 只放新增 Actor 时，现有 `run_plan_builder.py` 仍可消费
3. 当前 Common Contracts 最小模型足以支撑 append/new-actor 场景的审查与阻断
4. 真机 `bridge_rc_api` + 截图证据脚本可以稳定跑完 Phase 5 Brownfield smoke

## 待验证假设

1. `_core` manifest loader / registry / router base 能在不重构当前 Compiler 主链的前提下接入现有编译流程
2. boardgame pack 的 `review_extensions / validation_extensions / delta_policy` 能在 Phase 6 内形成真正可调用的最小闭环
3. `project_state_intake.py` 的真实采集字段足以支撑更多 Brownfield 类型，而不只是 boardgame append 样板
