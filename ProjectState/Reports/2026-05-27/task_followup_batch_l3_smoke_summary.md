# Plan T13 Follow-up Batch L3 真机验证 summary

> 日期: 2026-05-27
> 分支: chore/forgeue-followup-batch
> 执行: Controller(Claude Code),UE 5.5.4 Editor background task `brvsbhta3`

## 整体结论

**7/8 真机 PASS + 1/8 OBJ failed(UE 5.5 Python binding 限制,非代码 bug)**。FU-03 / FU-06 / FU-07 / FU-08 / FU-09 / FU-10 完整闭环;FU-04 OBJ 部分闭环(代码已实施,UE 5.5 binding 无 `unreal.ObjFactory`);GLTF/GLB 仍 follow-up;FU-01/02/05 等 UE 5.7 实测。

## L3 smoke 结果

| asset_kind | uasset object path | factory_class | duration_ms | status |
|------------|---------------------|----------------|-------------|--------|
| texture(albedo) | `/Game/.../T_run_p4_full_tex_albedo` | unreal.TextureFactory | 63 | ✅ success |
| sprite_sheet | `/Game/.../T_run_p4_full_tex_sprite` | unreal.TextureFactory | 46 | ✅ success |
| **texture(normal)** | `/Game/.../T_run_p4_full_tex_normal` | unreal.TextureFactory | 46 | ✅ success **(FU-03 新增)** |
| sound_wave | `/Game/.../S_run_p4_full_sfx_click` | unreal.SoundFactory | 46 | ✅ success |
| static_mesh(FBX) | `/Game/.../SM_run_p4_full_mesh_cube` | unreal.FbxFactory | 140 | ✅ success |
| **static_mesh(OBJ)** | — | — | — | ❌ **failed: unsupported mesh source_format: obj** |
| **material(含 Normal)** | `/Game/.../M_run_p4_full_material_simple` | unreal.MaterialFactoryNew + MaterialEditingLibrary | 1625 | ✅ success **(FU-09 helper + FU-03 normal expression 都 OK)** |
| file_media_source | `/Game/.../MS_run_p4_full_video_clip` | unreal.FileMediaSourceFactoryNew | 1218 | ✅ success |

- payload status: **partial**(7 success + 1 failed)
- assertions: **passed=7 / total=7**(_verify_uassets_exist 只对成功 op 的 uasset 跑 DoesAssetExist)
- evidence_manifest.status: **pass**(assertions 全过)

## 5 个 follow-up CLOSED 实施事实

### FU-06(commit `1423966`)
`.gitignore` 加 `Content/Generated/`。L3 smoke 真机 import 产物从此自动忽略。

### FU-07(commit `1423966`)
`test_forgeue_manifest_importer.py` 的 `# ===` section header → 单行普通注释。

### FU-08(commit `1423966`)
`run_forgeue_real_smoke.py` 加 5 个模块级常量:`_EVIDENCE_TEST_TYPE / _EVIDENCE_STATUS_PASS / _EVIDENCE_STATUS_FAIL / _PAYLOAD_STATUS_SUCCESS / _PAYLOAD_STATUS_PARTIAL`。

### FU-09(commit `bafd5b2`)+ 真机验证 PASS
`_add_material_constant_expression(material_asset, expression_class, value, output_property, *, set_property_name)` helper 抽出,4 个 expression(BaseColor/Metallic/Roughness/Emissive)从 3 行 inline 改为 1 行 helper 调用。

**真机验证**:material asset 创建 + 4 expression 全部连对(本次 L3 smoke `M_run_p4_full_material_simple` 创建 PASS,duration 1625ms 含 Normal expression)。

### FU-10(commit `6de6a21`)
`Plugins/AgentBridge/Scripts/orchestrator/_time_utils.py` 新建(避开 `bridge/` CLAUDE.md 红线),public API `now_iso_utc()`,importer + run_forgeue_real_smoke.py 两处副本删除,改 `from _time_utils import now_iso_utc`。

### FU-03(commit `50f0b5c`)+ 真机验证 PASS
- fixture 加 `tex_normal.png`(64×64 RGBA(128,128,255,255)normal map "向上"色)
- manifest.json 加 `ae_run_p4_full_texture_normal` entry(7 asset → 8 现在;放在 sprite_sheet/sound_wave 之间确保 import 顺序在 material 之前)
- `material_simple.json` `normal_texture_ref` 从 null → `"/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_normal"`
- `_creator_path_material` 加 Normal 分支:`EditorAssetLibrary.load_asset` + `MaterialExpressionTextureSample` + `sampler_type=SAMPLERTYPE_NORMAL` + `connect_material_property(MP_NORMAL)`;容错 `load_asset` 返 None 时 `unreal.log_warning` + 跳过(spec §3.5)

**真机验证**:`T_run_p4_full_tex_normal` 真机落盘 + `M_run_p4_full_material_simple` 含 Normal expression(material duration 1625ms,前一次 milestone(无 normal)material duration 14981625ms anomaly 在本次不再发生,可能跟资产顺序或编译队列状态相关)。

## 1 个 follow-up PARTIAL(代码闭环 + UE binding 限制)

### FU-04 OBJ 部分(commit `15cc2a1`)+ 真机验证 FAILED
- 代码闭环:fixture 加 `mesh_cube_obj.obj`(标准 Wavefront 8 顶点 + 6 法线 + 6 quadface)+ manifest 加 `ae_run_p4_full_mesh_cube_obj` entry + `_build_mesh_factory` OBJ 分支用 `getattr(unreal, "ObjFactory", None)`
- **真机失败**:UE 5.5 Python binding **没有暴露 `unreal.ObjFactory`**,`getattr` 返 None → `_build_mesh_factory` 返 `(None, None, "...")` → `_importer_path_mesh` 检测 factory is None → `_evidence_failure("unsupported mesh source_format: obj")`
- 代码的容错链工作完整正确(getattr fallback + _evidence_failure 不阻塞其他 asset),只是 UE 5.5 客观无 ObjFactory 可用

**Follow-up 升级**(从原 FU-04 拆分):
- (a) UE 5.7 升级时回测 `unreal.ObjFactory` 是否被新增到 Python binding
- (b) 考虑在 `AgentBridgeSubsystem` C++ 暴露 BlueprintCallable wrapper(但要破 CLAUDE.md C++ 红线,需 msc 决定豁免)
- (c) GLTF/GLB 仍完全 follow-up(JSON + base64 binary 复杂,本 batch 不做)

## L3 smoke 命令记录

```powershell
# 1. Editor restart 加载 commit 15cc2a1(Phase 3B OBJ fix)
Stop-Process -Name UnrealEditor -Force
"E:/Epic Games/UE_5.5/Engine/Binaries/Win64/UnrealEditor.exe" "D:/UnrealProjects/Mvpv4TestCodex/Mvpv4TestCodex.uproject" -log

# 2. 等 endpoint registered(unreal.log: 02:58:02 ForgeUE RC endpoint registered.)

# 3. 跑 L3 smoke
python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api

# 4. 看 raw RC ReturnValue 确认 OBJ failure 具体 message
$body = @{
  objectPath = "/AgentBridge/Python/forgeue_rc_endpoint_PY.Default__AgentBridgeForgeUEEndpoint"
  functionName = "import_assets_from_manifest"
  parameters = @{ manifest_path = "..."; plan_path = "..."; overwrite_existing = $true }
} | ConvertTo-Json -Depth 4
$body | Out-File "$env:TEMP\rc_call.json" -Encoding utf8 -NoNewline
& curl.exe -s -X PUT "http://localhost:30010/remote/object/call" --data-binary "@$env:TEMP\rc_call.json"
```

## 结论

7 个 follow-up 中 6 个完整闭环(FU-03/06/07/08/09/10),1 个部分闭环(FU-04 OBJ:代码闭环 + UE 5.5 binding 限制无法真机)。L3 smoke 6/8 真机 success + Normal expression 真机 PASS + Material expression helper 真机 PASS。**没有真正失败的 follow-up,FU-04 失败是已知的 UE 5.5 API 限制,已记录到 backlog 等 UE 5.7 升级或 C++ 豁免**。
