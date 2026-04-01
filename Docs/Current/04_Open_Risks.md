# 当前风险

> 文档版本：L1-Phase5-v2

## 活跃风险

1. `project_state_intake.py` 虽已接入真实结构，但 Editor 会话、当前关卡和 Bridge 通道状态仍可能影响采集完整性。
2. Phase 5 当前只安全支持 append/new-actor，如果 patch / replace 判定不准，仍有把存量内容误当成新建内容的风险。
3. Contract 体系当前是最小模型，如果后续场景变复杂，可能需要更细的 Contract 实例化规则。
4. 截图证据依赖视口相机和真实 Editor 运行态；若 Editor 未就绪或相机设置失败，证据采集会退化为日志而不是 PNG。
5. 真机 RC API 虽已在本机通过，但换机或更换引擎安装仍可能因为 BuildId / Editor 启动层问题重新触发连接失败。

## 已缓解风险

- Greenfield 主链已稳定，可作为 Phase 5 回归基线
- Brownfield 空壳模块（analysis / Contracts / delta tree）已替换为最小可运行实现
- `Scripts/run_brownfield_demo.py` 已能验证 append-only 样板
- `ProjectState/Snapshots/` 与 `ProjectState/Evidence/Phase5/` 已明确分责

## 已验证假设

1. Brownfield Handoff 可以在不修改稳定 Schema 的前提下扩展 `baseline_context` / `delta_context`
2. `scene_spec.actors[]` 只放新增 Actor 时，现有 `run_plan_builder.py` 仍可消费
3. 当前 Contracts 最小模型足以支撑 append/new-actor 场景的审查与阻断

## 待验证假设

1. 真机 `bridge_rc_api` + 截图证据脚本能稳定跑完 Brownfield smoke
2. `project_state_intake.py` 的真实采集字段足以支撑更多 Brownfield 类型，而不只是 boardgame append 样板
3. 当前回归检查集合足够防止 append 场景误伤已有 Actor
