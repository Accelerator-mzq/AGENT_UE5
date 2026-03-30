# 当前风险

> 文档版本：L1-Phase3-v1

## 风险清单

1. Bridge 真实调用时参数格式不匹配（Run Plan params → Bridge 接口参数）
2. RC API 端口未开放导致 bridge_rc_api 模式失败
3. 新增的 Scripts/compiler/ 目录可能与现有 Python 路径冲突

## 待验证假设

1. 现有 Bridge 接口（SpawnActor）可以被 handoff_runner.py 正确桥接调用
2. 新增的 Schemas 不会影响现有 validate_examples.py 的校验结果
3. 新增的 orchestrator/handoff_runner.py 不会影响现有 orchestrator.py 的 run(spec_path) 入口
