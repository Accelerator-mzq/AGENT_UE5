# 当前风险

> 文档版本：L1-Phase3-v2（Phase 3 结束更新）

## 风险清单

### 已验证 / 已缓解

- ~~Bridge 真实调用时参数格式不匹配（Run Plan params → Bridge 接口参数）~~ → 仍存在，但 simulated 模式已验证参数构造逻辑正确，真实调用待 Phase 4 前置验证
- ~~RC API 端口未开放导致 bridge_rc_api 模式失败~~ → simulated 模式不依赖端口，真实调用时需确认 Editor 运行
- ~~新增的 Scripts/compiler/ 目录可能与现有 Python 路径冲突~~ → **已验证**：compiler_main.py 和 run_greenfield_demo.py 均正常运行，无路径冲突

### 活跃风险（Phase 4 前瞻）

1. Static Spec Base 从零构建，工作量大且缺乏现有参考实现
2. Spec 自动生成器（generation/）的设计复杂度高于 Phase 3 的 intake/routing/handoff
3. UE5 真实调用联调可能暴露 simulated 模式未覆盖的边界情况

## 已验证假设

1. ✅ 现有 Bridge 接口（SpawnActor）可以被 handoff_runner.py 正确桥接调用（simulated 模式验证通过）
2. ✅ 新增的 Schemas 不会影响现有 validate_examples.py 的校验结果
3. ✅ 新增的 orchestrator/handoff_runner.py 不会影响现有 orchestrator.py 的 run(spec_path) 入口

## 待验证假设（Phase 4）

1. Static Base 的滚动扩展策略能否在实践中保持一致性
2. Cross-Spec Review 能否检测出有意义的错误（而非过度告警）
3. 从 GDD 自动生成的 Spec Tree 能否通过 Static Base 定义的 Schema 校验
