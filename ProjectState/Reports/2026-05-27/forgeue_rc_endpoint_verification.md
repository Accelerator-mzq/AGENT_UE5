# ForgeUE RC Endpoint Verification — Task 5 验证清单结果

> 日期: 2026-05-27
> Spec: Docs/superpowers/specs/2026-05-27-forgeue-real-ue-bridge-design.md §4.4
> Plan: Docs/superpowers/plans/2026-05-27-forgeue-real-ue-bridge.md Task 5
> 状态: 骨架 - 等 msc 在 UE 5.5.4 Editor 内配合跑 Step 5.4-5.7 后回填

## 验证项

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | Editor 启动加载 init_unreal.py | ⏳ pending | <unreal.log 行号/snippet> |
| 2 | forgeue_rc_endpoint registered(log 含 "RC endpoint registered") | ⏳ pending | <unreal.log 行号/snippet> |
| 3 | curl /remote/object/describe 含 ImportAssetsFromManifest | ⏳ pending | <返回 JSON 摘抄> |
| 4 | curl /remote/object/call 返回 endpoint JSON(预期是 NotImplementedError 包装,因为 Task 6-10 未完成) | ⏳ pending | <返回 JSON 摘抄> |

## Path C 决策

- 4 项全 ✅ → **继续 PythonScripted UCLASS 方案**,进入 Task 6
- 任一项 ❌ → **回退 EUB Fallback**,本文档底部追加回退实施

## EUB Fallback(如果回退)

按 spec §4.5 实施:
- 在 UE Editor 内手建 EUB `/Game/Editor/ForgeUEBridge.ForgeUEBridge`
- 蓝图 BlueprintCallable function `ImportAssetsFromManifest` 内调 ExecutePythonCommand 节点
- RC object_path 改为 `/Game/Editor/ForgeUEBridge.Default__ForgeUEBridge_C`
- 修改 Task 6-10 中所有 RC 调用 object_path,改 Scripts/run_forgeue_real_smoke.py 对应字符串

## 决策记录

[等 msc 实测后填:实际跑完 4 项后选哪条路]
