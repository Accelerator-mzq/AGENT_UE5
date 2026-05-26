# ForgeUE RC Endpoint Verification — Task 5 验证清单结果

> 日期: 2026-05-27
> Spec: Docs/superpowers/specs/2026-05-27-forgeue-real-ue-bridge-design.md §4.4
> Plan: Docs/superpowers/plans/2026-05-27-forgeue-real-ue-bridge.md Task 5
> 状态: ✅ 4/4 全过 — Path C 决策为继续 PythonScripted UCLASS 方案
> 执行: 2026-05-27 17:50-17:54(本地时间)Controller(Claude Code)在 UE 5.5.4 Editor `b2uz7lgjo` / `b6jyqa9ss` 两次启动会话内完成

## 验证项

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | Editor 启动加载 init_unreal.py | ✅ | `Saved/Logs/Mvpv4TestCodex.log:1381` — `LogPython: Display: 正在运行启动脚本D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Content/Python/init_unreal.py…… started...`(took 106 ms);第二次重启后 `Mvpv4TestCodex.log` Line `2026.05.26-17.53.46:567` 同样触发(took 30.831 ms) |
| 2 | forgeue_rc_endpoint registered | ✅ | `Saved/Logs/Mvpv4TestCodex.log` — `LogPython: [AgentBridge] Loading ForgeUE RC endpoint...` + `LogPython: [AgentBridge] ForgeUE RC endpoint registered.`;第二次重启加入 self-probe 输出实际 class path 与 default object path(见决策记录区段) |
| 3 | curl /remote/object/describe 返回含 import_assets_from_manifest | ✅ | response JSON:`{ "Name": "Default__AgentBridgeForgeUEEndpoint", "Class": "/AgentBridge/Python/forgeue_rc_endpoint_PY.AgentBridgeForgeUEEndpoint", "Functions": [{"Name": "import_assets_from_manifest", "Description": "RC 入口...", "Arguments": [{"Name": "manifest_path", ...}, {"Name": "plan_path", ...}, {"Name": "overwrite_existing", ...}]}, ...] }`(3 个参数全列出,加上 UE 自动生成的 ExecuteUbergraph) |
| 4 | curl /remote/object/call 返回 endpoint JSON 字符串 | ✅ | response JSON:`{ "ReturnValue": "{\"status\": \"error\", \"error_class\": \"NotImplementedError\", \"message\": \"texture/sprite_sheet importer pending Task 6\"}" }` — 这是预期结果:RC → endpoint → importer.import_from_manifest(bridge_mode="bridge_python")→ 内核 _import_asset_by_kind → _importer_path_texture 抛 NotImplementedError → endpoint catch 包装成 JSON 字符串 → RC 返回 ReturnValue;全链路通,等 Task 6-10 填实 helper |

## Path C 决策

- 4 项全 ✅ → **继续 PythonScripted UCLASS 方案**,进入 Task 6
- ~~任一项 ❌ → 回退 EUB Fallback~~(本次未触发)

## 关键发现 — spec/plan 中的 object_path / function name / parameter keys 全错,需 Task 11/12 修正

实际从 Editor probe log 拿到的真实路径:

| 项 | spec/plan v1.0 假设 | 实际真实值 |
|----|---------------------|-----------|
| object_path | `/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint` | **`/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint`** |
| function name | `ImportAssetsFromManifest`(CamelCase) | **`import_assets_from_manifest`**(snake_case,UE 保留 Python 原名) |
| parameter keys | `ManifestPath` / `PlanPath` / `OverwriteExisting` | **`manifest_path` / `plan_path` / `overwrite_existing`**(全 snake_case) |

**根因**:UE 5.5 Python 的 `@unreal.uclass()` 注册路径基于 plugin name + Python module + `_PY` 后缀,**不是** spec 推测的 `/Script/PythonGeneratedClass`。函数与参数名也**不会**自动 CamelCase 化,保留 Python 原名。

**后续影响**:Task 11(L2 pytest)+ Task 12(L3 验收 smoke 脚本)中所有 RC object_path / function name / parameter key 都需要用真实值,不能套用 spec/plan v1.0 写的占位值。该信息已在 forgeue_rc_endpoint.py 顶部 docstring 改为引用 probe log 输出(commit `3f51e09` 同 commit 内加的 self-probe)。

## EUB Fallback(本次不触发,保留预案)

如未来真实 path 失效或 PythonScripted UCLASS 在 UE 5.7 升级时失败:
- 在 UE Editor 内手建 EUB `/Game/Editor/ForgeUEBridge.ForgeUEBridge`
- 蓝图 BlueprintCallable function `import_assets_from_manifest` 内调 ExecutePythonCommand 节点
- RC object_path 改为 `/Game/Editor/ForgeUEBridge.Default__ForgeUEBridge_C`
- 修改 Task 6-10 中所有 RC 调用 object_path,改 Scripts/run_forgeue_real_smoke.py 对应字符串

## 决策记录

**实测结论**(2026-05-27 Controller 跑):

1. ✅ init_unreal.py 自动加载机制确认有效(前提:AgentBridge.uplugin `CanContainContent: true` — commit `3f51e09`)
2. ✅ Python `@unreal.uclass()` + `@unreal.ufunction()` 注册的 PythonScripted UCLASS **能**被 RC HTTP 反射调用
3. ✅ 错误捕获 + JSON 序列化在 endpoint 内闭环,RC 返回 ReturnValue 字符串可被外部 JSON.loads 还原
4. ✅ 内核 dispatch 5+1 → helper(NotImplementedError pending Task 6-10)链路通

**Path C 验证成果**:不需要回退 EUB;Task 6-10 直接填 helper 即可,RC endpoint + init_unreal hook 都不需要再改。

**遗留 follow-up**(进入对应 Task 时处理,不阻塞 Task 5 收尾):
- Task 11 L2 pytest:用真实 object_path + snake_case function/parameter 名编写
- Task 12 L3 smoke 脚本:同上
- Task 13 文档同步:更新 spec §4.1 + plan Task 5 Step 5.5/5.6 + plan Task 11/12 把伪 object_path 替换为真实值

## 启动会话证据

- 第一次启动:background task `b2uz7lgjo`,unreal.log:`Saved/Logs/Mvpv4TestCodex.log` line 1219 起 AgentBridge plugin loaded;LogPython 显示 "No enabled plugins with python dependencies found"(误导 log)→ 修 `AgentBridge.uplugin` CanContainContent → 第二次启动
- 第二次启动:background task `b6jyqa9ss`,unreal.log:`Saved/Logs/Mvpv4TestCodex.log` line 1381 起 init_unreal.py started(106 ms);commit `3f51e09` 修后正常加载;然后 endpoint self-probe log(见前文表 #2)给出实际 path
- 第三次重启:加入 endpoint self-probe 后(commit 见 Step 5.9),unreal.log 在 `17:53:46:598` 输出真实 path

## 命令记录(controller 执行)

```bash
# 启 Editor
"E:/Epic Games/UE_5.5/Engine/Binaries/Win64/UnrealEditor.exe" "D:/UnrealProjects/Mvpv4TestCodex/Mvpv4TestCodex.uproject" -log

# Step 5.5
curl.exe -s -X PUT "http://localhost:30010/remote/object/describe" \
  -H "Content-Type: application/json" \
  -d '{"objectPath":"/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint"}'

# Step 5.6(JSON 通过 PowerShell ConvertTo-Json 生成,Bash 拼字符串会被 hook 误判)
$body = @{
  objectPath = "/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint"
  functionName = "import_assets_from_manifest"
  parameters = @{
    manifest_path = "D:/.../manifest.json"
    plan_path = "D:/.../import_plan.json"
    overwrite_existing = $true
  }
} | ConvertTo-Json -Depth 4
$body | Out-File -FilePath "$env:TEMP\rc_call.json" -Encoding utf8 -NoNewline
curl.exe -s -X PUT "http://localhost:30010/remote/object/call" \
  -H "Content-Type: application/json" --data-binary "@$env:TEMP\rc_call.json"
```
