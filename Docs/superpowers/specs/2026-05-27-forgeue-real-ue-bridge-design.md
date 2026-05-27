# ForgeUE Manifest Import Bridge — Real-UE Path Design Spec

> 文档版本: v1.0
> 日期: 2026-05-27
> 作者: Claude Code (msc 主导决断)
> 类型: superpowers spec (brainstorming 阶段产物)
> 后续: 通过 `superpowers:writing-plans` 生成 implementation plan
>
> **修订记录**
> - v1.0 (2026-05-27): 初版,基于 5 节 brainstorming 决断整合;关键决策由 msc 通过 AskUserQuestion 逐项确认

---

## 0. 目的与场景

`ForgeUE_codex` P4 流水线产出的 `UEAssetManifest` 已经通过 `forgeue_manifest_importer.py` 的 **simulated** 通路完成契约级集成(11 个单测 PASS,CLI 端到端通)。但要让 UE 真把这批资产**真机导入并产出 uasset**,需要把当前两条 `NotImplementedError` stub 通路实出来:

- `bridge_python` — 在 UE Editor Python 进程内直接调 `unreal.AssetTools.import_assets_automated(...)` / `create_asset(...)`
- `bridge_rc_api` — 外部 Python 通过 Remote Control HTTP(端口 30010)触发 Editor 内同一套导入逻辑

本 spec 是这两条通路的实施前设计,产出 design,等 `superpowers:writing-plans` 翻成可执行 implementation plan。

**目标读者**:
- 主读者:实施本 milestone 的开发者(可能是 Claude Code / Codex / msc 本人)
- 次读者:UE 5.7 升级时需要回看新增 surface 的 reviewer

**不在 spec 范围**:见 §5.E yagni 划界。

---

## 1. 已确认前提(brainstorming 阶段决断)

### 1.1 PNG payload 落地策略

- 拷贝 6 个最小 sample(< 1 MB)到 `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/`
- `manifest.json` 的 `project_target.project_root` 改为 fixture 目录;`source_uri` 保持相对路径
- 决断理由:本仓库自洽 + CI/任意机器可跑 + 真机测试可重现;放弃"严格 byte-for-byte 复制 ForgeUE_codex 上游输出"

### 1.2 C++ 红线策略

**两条通路全部纯 Python 实现,不动 CLAUDE.md 禁止修改清单内的任何文件**(详细交叉检查见 §5.A)。

**放弃的方案**(archive 文档 `Docs/archive/plugins/forgeue_manifest_integration.md:79` 的原始设计):在 `AgentBridge/Source/AgentBridge/Private/` 加 `ImportFromForgeUEManifest` 蓝图节点 ← **直接撞红线,不采用**。

### 1.3 asset_kind 覆盖范围

本 milestone 覆盖 **5+1 种**(对应 ForgeUE_codex `manifest_builder._KIND_MAP` 全量):

| asset_kind | UE prefix | source modality.shape |
|------------|-----------|----------------------|
| texture | T_ | image.raster |
| sprite_sheet(复用 texture) | T_ | image.sprite_sheet |
| sound_wave | S_ | audio.waveform |
| static_mesh | SM_ | mesh.gltf / fbx / obj |
| material | M_ | material.definition |
| file_media_source | MS_ | video.mp4 |

### 1.4 evidence 契约策略

- **新建**`Plugins/AgentBridge/Schemas/forgeue_import_evidence.schema.json`(逐条 op 证据,详见 §4.A)
- **外层 wrapper 复用**现有 `Plugins/AgentBridge/Schemas/evidence_manifest.schema.json`(Phase 10 MCP 用,test_type=smoke_test)
- 放弃方案:复用 evidence_manifest 逐 op(字段不够结构化)/ 镜像 ForgeUE_codex 上游 evidence.json(跨项目依赖)

### 1.5 整体实施路径:Path C 共享内核 + 两条 track 同时接入

- `_import_asset_by_kind(asset)` 共享内核函数(只在 UE Editor Python 环境可跑,因依赖 `unreal` 模块)
- bridge_python 直接调内核;bridge_rc_api 通过 RC HTTP 触发 Editor 内已 startup-loaded 的 wrapper,wrapper 内调同一内核
- 放弃方案:Path A(Track A 先 Track B 后串行)/ Path B(Track B 先,RC 路径风险高时阻塞 milestone)

### 1.6 material 实现深度:Option α 最简 PBR 五字段

- 本侧定义最简 `material.definition` schema:`base_color_rgba` / `metallic` / `roughness` / `normal_texture_ref` / `emissive_color_rgba`
- 实施 `_creator_path_material` 时按这个最小 schema 走 `MaterialFactoryNew` + `MaterialEditingLibrary`
- 放弃方案:Option β(跨项目读 ForgeUE_codex `_KIND_MAP` 源码搞清楚完整 schema)— 引入跨项目依赖,工作量超出 milestone

---

## 2. 架构总览

### 2.1 模块边界(新增 / 修改)

```
Plugins/AgentBridge/
├── Scripts/orchestrator/
│   └── forgeue_manifest_importer.py        ◀ 修改:加 _import_asset_by_kind 内核 + bridge_python 分支
├── Content/Python/                          ◀ 新增目录
│   ├── forgeue_rc_endpoint.py               ◀ 新增:Editor startup 加载,注册 RC-可见 wrapper
│   └── init_unreal.py                       ◀ 新增:UE Editor Python 自动加载 hook
├── Schemas/
│   ├── forgeue_import_evidence.schema.json  ◀ 新增:逐条 op 证据契约
│   └── examples/
│       └── forgeue_import_evidence_example.json  ◀ 新增:passing example,过 validate_examples.py --strict
└── Tests/
    ├── fixtures/forgeue_manifest/
    │   ├── manifest.json                    ◀ 修改:project_root 改 fixture 目录,扩 5+1 种 asset
    │   ├── import_plan.json                 ◀ 修改:扩 7 个 op
    │   └── payload/                         ◀ 新增:6 个 sample 文件 < 1 MB
    └── scripts/
        ├── test_forgeue_manifest_importer.py ◀ 修改:扩 simulated 含 6 种 asset_kind
        └── test_forgeue_real_ue_smoke.py     ◀ 新增:L2 marker 真机测试

Scripts/
└── run_forgeue_real_smoke.py                ◀ 新增:外部驱动验收 smoke

ProjectState/Reports/<date>/forgeue_real_smoke/
├── evidence_manifest.json                   ◀ L4 wrapper(复用现有 schema)
├── op_evidence/<asset_entry_id>.json        ◀ L1 逐条
├── screenshots/                             ◀ Content Browser 截图
├── unreal.log                               ◀ 切片
└── assertions.json                          ◀ EditorAssetLibrary.does_asset_exist 校验
```

### 2.2 三种 bridge_mode 分发关系

```
forgeue_manifest_importer.import_from_manifest(bridge_mode=...)
        │
        ├─ "simulated"      → _simulate_asset(asset)         ─────► 离线 mock(现状,不动)
        │
        ├─ "bridge_python"  → _import_asset_by_kind(asset)   ─────► 直接调 unreal.AssetTools
        │                       (只能在 UE Editor Python 环境)
        │
        └─ "bridge_rc_api"  → remote_control_client.call_function(
                                  object_path="/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint",
                                  function_name="ImportAssetsFromManifest",
                                  parameters={ManifestPath, PlanPath, OverwriteExisting})
                                       │
                                       ▼  (HTTP 30010 → Editor 内)
                              forgeue_rc_endpoint.AgentBridgeForgeUEEndpoint.import_assets_from_manifest(...)
                                       │
                                       └─► _import_asset_by_kind(asset)   ◀ 共享同一内核
```

### 2.3 核心设计要点

1. **共享内核 `_import_asset_by_kind(asset, manifest_root)`** 只在 UE Editor 内可调(顶部 `import unreal` 失败则该函数不可用,但 simulated 模式不受影响)
2. **bridge_python 入口**:用户在 UE Editor → Tools → Python Console 直接 `import forgeue_manifest_importer; importer.import_from_manifest(..., bridge_mode="bridge_python")`,或 `Scripts/run_forgeue_real_smoke.py` 通过 `UnrealEditor.exe -ExecutePythonScript=...` 间接触发
3. **bridge_rc_api 入口**:外部 Python 跑 `remote_control_client.call_function(...)` → HTTP 30010 → Editor 内已 startup-loaded 的 `forgeue_rc_endpoint.py` 提供的 BlueprintCallable wrapper → 同一内核
4. **RC 可见函数注册机制**:UE Python `@unreal.uclass()` decorator 定义 PythonScripted UCLASS,`@unreal.ufunction(meta=dict(BlueprintCallable=""))` 标记的方法变成 BlueprintCallable UFunction;`forgeue_rc_endpoint.py` 在 Editor 启动时通过 `init_unreal.py` hook 加载即注册
5. **simulated 路径完全不动**,作为契约不漂移的看护(11 个现行单测全部保留)

---

## 3. `_import_asset_by_kind` 内核 + 5+1 种 asset_kind 实现

### 3.1 内核分两类:importer kinds vs creator kinds

| asset_kind | 类别 | UE Python API | Factory / Creator |
|------------|------|---------------|-------------------|
| texture | importer | `AssetTools.import_assets_automated()` | `TextureFactory` |
| sprite_sheet | importer(复用 texture) | 同上 | `TextureFactory` + `import_options.tileable` |
| sound_wave | importer | `AssetTools.import_assets_automated()` | `SoundFactory` |
| static_mesh | importer | `AssetTools.import_assets_automated()` | `FbxFactory`(.fbx) / `GLTFImporter`(.gltf/.glb) / `ObjFactory`(.obj),按 `import_options.source_format` 路由 |
| material | **creator** | `AssetTools.create_asset()` | `MaterialFactoryNew` + `MaterialEditingLibrary` 按最简 PBR 五字段配 |
| file_media_source | **creator** | `AssetTools.create_asset()` | `FileMediaSourceFactoryNew` + 设 `FilePath` 指向 source_uri |

### 3.2 内核函数骨架

```python
def _import_asset_by_kind(asset: dict, manifest_root: Path, overwrite_existing: bool) -> dict:
    """单 asset 真机执行;只能在 UE Editor Python 环境跑。

    返回 forgeue_import_evidence.schema.json 兼容的 dict:
        {asset_entry_id, op_id, asset_kind, bridge_mode, status, timestamp,
         source_uri_abs, uasset_object_path, uasset_package_path,
         factory_class, duration_ms, import_log_excerpt, errors, skipped_reason}
    """
    import unreal  # 失败 → 不在 Editor Python 环境,早期 raise

    kind = asset["asset_kind"]
    source_uri = (manifest_root / asset["source_uri"]).resolve()
    if not source_uri.exists():
        return _evidence_failure(asset, f"payload missing: {source_uri}")

    target_pkg = asset["target_package_path"]

    if kind in ("texture", "sprite_sheet"):
        return _importer_path(asset, source_uri, target_pkg, overwrite_existing,
                              _build_texture_factory(asset["import_options"]))
    if kind == "sound_wave":
        return _importer_path(asset, source_uri, target_pkg, overwrite_existing,
                              _build_sound_factory(asset["import_options"]))
    if kind == "static_mesh":
        return _importer_path(asset, source_uri, target_pkg, overwrite_existing,
                              _build_mesh_factory(asset["import_options"]))
    if kind == "material":
        return _creator_path_material(asset, source_uri, target_pkg, overwrite_existing)
    if kind == "file_media_source":
        return _creator_path_media(asset, source_uri, target_pkg, overwrite_existing)

    return _evidence_failure(asset, f"unsupported asset_kind: {kind}")
```

### 3.3 import_options → Factory 属性映射(以 texture 为例)

```python
def _build_texture_factory(import_options: dict) -> "unreal.TextureFactory":
    import unreal
    factory = unreal.TextureFactory()
    factory.set_editor_property("srgb",
                                import_options.get("color_space", "sRGB") == "sRGB")
    cs = import_options.get("compression_settings", "default")
    factory.set_editor_property("compression_settings",
                                _COMPRESSION_MAP.get(cs, unreal.TextureCompressionSettings.TC_DEFAULT))
    if not import_options.get("tileable", False):
        factory.set_editor_property("mip_gen_settings",
                                    unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
    return factory
```

类似 `_build_sound_factory` / `_build_mesh_factory` / `_creator_path_material` / `_creator_path_media` 各自一段 helper,挂在同一 module 内保持 cohesive。

### 3.4 material Option α 最简 PBR 五字段 schema

`material.definition`(本仓库定义,与 ForgeUE_codex 上游 schema 当前 milestone **不强制同步**):

```json
{
  "base_color_rgba": [0.5, 0.5, 0.5, 1.0],
  "metallic": 0.0,
  "roughness": 0.7,
  "normal_texture_ref": null,
  "emissive_color_rgba": [0.0, 0.0, 0.0, 1.0]
}
```

`_creator_path_material` 实施步骤:
1. `AssetTools.create_asset(asset_name, package_path, unreal.Material, MaterialFactoryNew())`
2. 用 `unreal.MaterialEditingLibrary.create_material_expression(...)` 加 5 个 expression(BaseColor / Metallic / Roughness / Normal / Emissive)
3. `connect_material_property(...)` 把 expression 连到 Material output
4. `recompile_material(...)` 触发编译
5. `EditorAssetLibrary.save_asset(...)` 落盘

### 3.5 错误处理

| 错误场景 | 处理 |
|----------|------|
| `import unreal` 失败 | bridge_python/rc 模式早期 raise `RuntimeError("not running inside UE Editor Python env")`;simulated 不受影响 |
| payload 文件不存在 | 该 op evidence 标 `status=failed`,继续下一 asset(不中止全批) |
| Factory.import 抛异常 | 同上,evidence 记 `errors[]` |
| target_package_path 已存在 + overwrite_existing=false | 标 `status=skipped`,evidence 记 `skipped_reason` |
| 整批失败率 > 阈值(可配,默认 50%) | 主入口 return 整体 status=failed,触发上层告警 |

---

## 4. bridge_rc_api 通路 + RC endpoint 注册

### 4.1 Editor 内 RC endpoint 文件结构

```python
# Plugins/AgentBridge/Content/Python/forgeue_rc_endpoint.py
"""ForgeUE manifest 导入的 RC HTTP endpoint(Editor 内 startup 加载)。

注册一个 PythonScripted UCLASS:AgentBridgeForgeUEEndpoint,
含一个 BlueprintCallable UFUNCTION:import_assets_from_manifest。

外部通过 remote_control_client.call_function(
    object_path="/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint",
    function_name="ImportAssetsFromManifest",
    parameters={"ManifestPath": "...", "PlanPath": "...", "OverwriteExisting": false}
) 触发。
"""
from __future__ import annotations
import json
import sys
import unreal

# 让 endpoint 能找到 forgeue_manifest_importer 共享内核
_ORCH_DIR = unreal.Paths.project_plugins_dir() + "AgentBridge/Scripts/orchestrator"
if _ORCH_DIR not in sys.path:
    sys.path.insert(0, _ORCH_DIR)

import forgeue_manifest_importer as importer


@unreal.uclass()
class AgentBridgeForgeUEEndpoint(unreal.Object):
    """RC HTTP 入口对象;作为 PythonScripted UCLASS 注册到 UE 反射系统。"""

    @unreal.ufunction(
        ret=str,
        params=[str, str, bool],
        meta=dict(Category="AgentBridge|ForgeUE", BlueprintCallable=""),
    )
    def import_assets_from_manifest(
        self, manifest_path: str, plan_path: str, overwrite_existing: bool
    ) -> str:
        """RC 入口:同步执行整批导入,返回结构化 JSON 字符串。"""
        try:
            result = importer.import_from_manifest(
                manifest_path=manifest_path,
                plan_path=plan_path or None,
                bridge_mode="bridge_python",  # endpoint 在 Editor 内,等价于 bridge_python
            )
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"status": "error", "error_class": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
            )
```

### 4.2 Editor 启动自动加载机制

```python
# Plugins/AgentBridge/Content/Python/init_unreal.py(新增)
"""UE Editor Python 插件启动时自动执行,完成 AgentBridge 端 Python endpoint 注册。

UE 5.4+ PythonScriptPlugin 标准 hook:任何 plugin 的 Content/Python/init_unreal.py
在 Editor 启动时被自动执行。
"""
import unreal
unreal.log("[AgentBridge] Loading ForgeUE RC endpoint...")
try:
    import forgeue_rc_endpoint  # noqa: F401  # 导入即触发 @unreal.uclass() 注册
    unreal.log("[AgentBridge] ForgeUE RC endpoint registered.")
except Exception as exc:
    # 关键:即使注册失败,也不能阻塞 Editor 启动
    unreal.log_error(f"[AgentBridge] ForgeUE RC endpoint registration failed: {exc}")
```

### 4.3 外部 client → RC 调用拼法

```python
# Scripts/run_forgeue_real_smoke.py(新增)
from Plugins.AgentBridge.Scripts.bridge import remote_control_client as rc

result = rc.call_function(
    object_path="/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint",
    function_name="ImportAssetsFromManifest",
    parameters={
        "ManifestPath": "<abs path>",
        "PlanPath": "<abs path>",
        "OverwriteExisting": False,
    },
)
# result.ReturnValue 是 endpoint 序列化后的 JSON 字符串,本侧 json.loads 还原
```

### 4.4 实施第一步:验证清单(降低 Path C 风险)

> 这是 Path C 的"未知技术风险",必须在写完 endpoint 后的**第一动作**就验证,**不要先写 5+1 种 asset_kind**。

1. 启 UE 5.5.4 Editor + AgentBridge plugin 启用
2. 看 `unreal.log` 含 `[AgentBridge] ForgeUE RC endpoint registered`
3. 跑 `curl http://localhost:30010/remote/object/describe?objectPath=/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint`,看返回是否含 `import_assets_from_manifest`
4. 跑一次最简调用(只 simulated 模式),看 `ReturnValue` 是不是 JSON 字符串

### 4.5 Fallback 方案 — Editor Utility Blueprint(EUB)wrapper

如果验证清单**任意一步失败**(尤其 PythonScripted UCLASS 在 RC 可见性这一点):

- 改在 Editor 内手建一个 EUB:`/Game/Editor/ForgeUEBridge.ForgeUEBridge`
- 蓝图内一个 BlueprintCallable function `ImportAssetsFromManifest(manifest_path, plan_path, overwrite)`,内部调 `ExecutePythonCommand` 节点 invoke `forgeue_manifest_importer.import_from_manifest(...)`
- RC 端 object_path 拼 `/Game/Editor/ForgeUEBridge.Default__ForgeUEBridge_C`
- EUB 是 UE 内置工作流,可见性更稳;代价是需要在 Editor 里手建一次,提交进 git

**优先 PythonScripted UCLASS**(更纯 Python,不增加 Content asset),验证失败再回退 EUB。

---

## 5. 风险 / 约束 / UE 5.7 影响 / yagni 划界

### 5.A 与 CLAUDE.md 红线交叉检查(必须 0 触碰)

| CLAUDE.md 禁止修改文件 | 本 design 是否触碰 |
|------------------------|---------------------|
| `AgentBridge/Source/AgentBridge/Private/*.cpp` | ❌ 不动 |
| `AgentBridge/Source/AgentBridge/Public/*.h` | ❌ 不动 |
| `Scripts/bridge/bridge_core.py` / `query_tools.py` / `write_tools.py` | ❌ 不动 |
| `Scripts/bridge/remote_control_client.py` | ❌ 不动(只调用 API,不改本体) |
| `Scripts/orchestrator/orchestrator.py` / `plan_generator.py` / `verifier.py` / `report_generator.py` / `spec_reader.py` | ❌ 不动 |
| `AgentBridgeTests/` | ❌ 不动 |
| `Schemas/common/`、`Schemas/feedback/`、`Schemas/write_feedback/` | ❌ 不动 |

**新增/修改文件全部落在"可以修改"区**:`Scripts/orchestrator/forgeue_manifest_importer.py`(明确在可修改清单)/ `Schemas/forgeue_import_evidence.schema.json`(不在三个稳定区)/ `Content/Python/*`(新增目录)/ `Tests/fixtures/*`(项目层 fixture)/ `Tests/scripts/*`(项目层测试)/ `Scripts/run_forgeue_real_smoke.py`(项目根 Scripts/)/ `ProjectState/Reports/*`(证据落盘)。

**结论:0 触红线**。

### 5.B UE 5.7 迁移影响

| 新 surface | UE 5.7 风险 | 关联 BC ID | 缓解 |
|------------|-------------|------------|------|
| `unreal.AssetTools.import_assets_automated()` | 低 — UE 长期稳定 | 不在已识别 25 BC 内 | 升 5.7 跑 L2/L3 验证 |
| `@unreal.uclass()` + `@unreal.ufunction()` PythonScripted UCLASS | 中 — PythonScriptPlugin 5.7 行为未公开 | **BC-NEW-A**(P2 suspected,本 design 新增) | Fallback EUB 已设计,5.7 升级时如失败可切 EUB |
| `init_unreal.py` 自动加载 | 低 — UE 5.4+ 标准 hook | 不在已识别 25 BC 内 | 同上 |
| RC HTTP `/remote/object/call` PUT 调 PythonScripted UClass | 中 — BC-020 P2 suspected | BC-020 | 验证清单步骤 3 提前测出 |
| `TextureFactory` / `SoundFactory` / `FbxFactory` / `MaterialFactoryNew` / `FileMediaSourceFactoryNew` | 低 — Factory 类 5.6/5.7 release notes 未提移除 | 不在已识别 25 BC 内 | 跑 L3 验证 |
| `MaterialEditingLibrary`(EditorScriptingUtilities 系列) | **中** — BC-008/016 confirmed P1(UE 5.6+ deprecated) | **BC-NEW-B**(P1 candidate,本 design 新增,与 BC-008 联动) | 5.7 升级时必须迁移到新 API |

**新增 BC 候选**(待 spec 收纳到 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 主表):
- BC-NEW-A(P2 suspected,reviewer pending-msc):PythonScripted UCLASS 在 RC HTTP 调用下的 5.7 兼容性
- BC-NEW-B(P1 candidate,与 BC-008/016 联动):`unreal.MaterialEditingLibrary` 在 5.7 是否仍可用

### 5.C 已知风险 + 缓解

| # | 风险 | 概率 | 影响 | 缓解 |
|---|------|------|------|------|
| 1 | PythonScripted UCLASS 不可被 RC 调用 | 中 | 卡住 bridge_rc_api | Fallback EUB(§4.5)+ 实施第一步验证清单(§4.4) |
| 2 | `MaterialFactoryNew` + `MaterialEditingLibrary` 设节点失败 | 中 | material asset_kind 失败 | Option α 已收窄到五字段;失败时该 op evidence=failed,不阻塞其他 5 种 |
| 3 | FBX import 在 UE 版本间默认设置漂移(LOD/碰撞) | 低 | static_mesh 出"不符合预期"资产但 status=success | L3 验收 smoke 手动截图人工核对一次 |
| 4 | RC HTTP 长时间阻塞(整批 6 个 asset 串行)超 30s 默认 timeout | 低 | 大 fixture 失败 | endpoint 内分批 commit,或加 timeout 参数;本 milestone 6 个小 asset 不会触发 |
| 5 | `init_unreal.py` 加载失败导致 Editor 起不来 | 低 | 严重 | 注册逻辑 try/except 包,失败仅 unreal.log 报错不抛 |
| 6 | 6 个 payload 入 git 触 git LFS 阈值 | 低 | 提交被拦 | 实施时确认 `.gitattributes` 不强制 LFS;< 1 MB 通常 OK |

### 5.D 与现有契约/主链兼容性

- `handoff_runner.execute_run_plan` 的 `import_assets` dispatch(`handoff_runner.py`,Phase 8 后骨架)已支持 `bridge_mode` 透传 → 本 design 不改 handoff_runner,只让 importer 在收到 `bridge_python`/`bridge_rc_api` 时不再 raise NotImplementedError ✅
- 现有 11 个 simulated 单测全部保留不动 ✅
- `SystemTestCases.md` / `run_system_tests.py` 主回归(`Docs/INDEX.md` 权威定义 266 case / 15 测试类)**不动**;真机 smoke 走 L3 独立脚本,**不**进主回归(保持 CI 离线性)✅
- **pytest L1 单测**新增 6 个 simulated case(每种 asset_kind 一个),`test_forgeue_manifest_importer.py` 从 11 → 17;是否同步登记到 `SystemTestCases.md` 由实施时按 docs governance 决定,本 spec 不强制
- MCP 工具数不变(53 工具不增)
- ForgeUE_codex 上游契约不变(继续硬断 `schema_version == "1.0.0"`)

### 5.E yagni 划界(spec 不覆盖)

1. ❌ ForgeUE_codex 上游 evidence.json cross-check
2. ❌ material 复杂节点图 / material function(只 Option α 五字段)
3. ❌ 跨机部署(只支持 ForgeUE_codex 与本项目同机 + manifest 相对路径)
4. ❌ UE 5.7 兼容性主动适配(只在 spec 登记 BC-NEW-A/B,实测留 5.7 实测阶段)
5. ❌ EUB Fallback 实际实现(只设计,等 PythonScripted UCLASS 验证失败时再补)
6. ❌ schema_version 2.0.0 支持(保留 1.0.0 单值硬断)
7. ❌ 真机 smoke 进 `run_system_tests.py` 主回归(保持 CI 离线性)
8. ❌ headless commandlet 模式跑 import(只支持 Editor 启动后跑)

---

## 6. 测试策略 — 三层(L1 / L2 / L3)

| 层 | 触发 | 覆盖 | 跑哪 |
|------|------|------|------|
| **L1: simulated pytest** | `pytest test_forgeue_manifest_importer.py` | 契约 / dispatch / CLI(现有 11 + 扩到 6 种 asset_kind 的 simulated 路径,约 17 个测试) | 离线、CI、本地任意机器 |
| **L2: real-UE pytest with marker** | `pytest test_forgeue_real_ue_smoke.py -m real_ue` | bridge_python / bridge_rc_api 真机调用、6 种 asset_kind 全打通、evidence 写盘格式合规 | 必须 UE Editor 启动 + 本机跑,marker 跳过条件 `pytest.mark.skipif(not _ue_editor_alive())` |
| **L3: 验收 smoke 脚本** | `python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_python` 或 `--bridge-mode bridge_rc_api` | 端到端跑一遍,产出 `ProjectState/Reports/<date>/forgeue_real_smoke/` 完整证据包(含手动截一张 Content Browser 图) | 手动触发 |

`pytest.ini` 需加 marker 登记:

```ini
markers =
    real_ue: requires running UE 5.5.4 Editor with RC API enabled
```

---

## 7. evidence 契约(新增)

### 7.1 逐条 op schema(新增 `Schemas/forgeue_import_evidence.schema.json`)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ForgeUE Import Evidence (per-op)",
  "description": "ForgeUE manifest 真机导入每条 asset 的逐条证据,由 bridge_python/bridge_rc_api 写盘。",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "asset_entry_id", "op_id", "asset_kind", "bridge_mode",
    "status", "timestamp", "source_uri_abs"
  ],
  "properties": {
    "asset_entry_id":      {"type": "string", "minLength": 1},
    "op_id":               {"type": "string", "minLength": 1},
    "asset_kind":          {"enum": ["texture","sprite_sheet","sound_wave","static_mesh","material","file_media_source"]},
    "bridge_mode":         {"enum": ["bridge_python","bridge_rc_api","simulated"]},
    "status":              {"enum": ["success","failed","skipped"]},
    "timestamp":           {"type": "string", "format": "date-time"},
    "source_uri_abs":      {"type": "string"},
    "uasset_object_path":  {"type": "string"},
    "uasset_package_path": {"type": "string"},
    "factory_class":       {"type": "string"},
    "duration_ms":         {"type": "integer", "minimum": 0},
    "import_log_excerpt":  {"type": "string"},
    "errors":              {"type": "array", "items": {"type": "string"}},
    "skipped_reason":      {"type": "string"}
  }
}
```

每条 op 写一份独立 JSON 到 `ProjectState/Reports/<date>/forgeue_real_smoke/op_evidence/<asset_entry_id>.json`。

### 7.2 外层 wrapper(复用现有 `evidence_manifest.schema.json`,不动)

外层一份 `ProjectState/Reports/<date>/forgeue_real_smoke/evidence_manifest.json`:

```jsonc
{
  "run_id": "2026-05-27_<hash8>",
  "created_at": "2026-05-27T10:23:45Z",
  "test_type": "smoke_test",
  "test_scope": "ForgeUE Manifest Real-UE Import Bridge (bridge_python + bridge_rc_api)",
  "evidence_items": [
    {"type": "report",          "path": "op_evidence/ae_..._texture.json",  "description": "texture import op evidence",       "timestamp": "..."},
    {"type": "report",          "path": "op_evidence/ae_..._sound.json",    "description": "sound_wave import op evidence",   "timestamp": "..."},
    /* 6 条 op_evidence */
    {"type": "screenshot",      "path": "screenshots/content_browser.png",  "description": "Content Browser 显示 6 个新增 uasset", "timestamp": "..."},
    {"type": "log",             "path": "unreal.log",                       "description": "unreal.log 切片(导入开始-结束)", "timestamp": "..."},
    {"type": "assertion_result","path": "assertions.json",                  "description": "EditorAssetLibrary.does_asset_exist 6/6 PASS", "timestamp": "..."}
  ],
  "summary": {"total_checks": 6, "passed": 6, "failed": 0, "warnings": 0},
  "status": "pass"
}
```

---

## 8. fixture 扩展

```
Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/
├── manifest.json         ◀ 扩 6 条 asset entry(texture/sprite_sheet/sound_wave/static_mesh/material/file_media_source)
├── import_plan.json      ◀ 扩 7 个 op(create_folder + 6 import/create)
└── payload/              ◀ 新增
    ├── tex_albedo.png             64×64 sRGB
    ├── tex_sprite_sheet.png       128×128 灰阶
    ├── sfx_click.wav              <1 秒 mono 16k WAV
    ├── mesh_cube.fbx              UE 5.5 ImportToUE 兼容的最简 FBX(单立方体)
    ├── material_simple.json       本仓库定义的最简 PBR 五字段
    └── video_clip.mp4             <2 秒 H.264 mp4
```

`manifest.json` 中 `project_target.project_root` 改为 fixture 目录路径(相对仓库根:`Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/`),`source_uri` 保持类似 `payload/tex_albedo.png` 的相对路径。

`material_simple.json` 例子:见 §3.4。

**payload 体积控制**:全部 6 个文件 < 1 MB,可安全入 git;实施时确认 `.gitattributes` 不强制 LFS。

---

## 9. ProjectState 落盘约定

```
ProjectState/Reports/2026-05-27/forgeue_real_smoke/
├── evidence_manifest.json         L4 wrapper(test_type=smoke_test)
├── op_evidence/
│   ├── ae_..._texture.json        L1 逐条
│   ├── ae_..._sprite_sheet.json
│   ├── ae_..._sound_wave.json
│   ├── ae_..._static_mesh.json
│   ├── ae_..._material.json
│   └── ae_..._file_media_source.json
├── screenshots/
│   ├── content_browser_after.png  6 个 uasset 全显示
│   └── content_browser_before.png 导入前空目录
├── unreal.log                     unreal.log 切片(前后约 100 行)
└── assertions.json                EditorAssetLibrary.does_asset_exist + Get*Asset 校验结果
```

---

## 10. 实施完整性 checklist(给 writing-plans skill 用)

- [ ] payload 6 个文件(< 1 MB)落到 `Tests/fixtures/forgeue_manifest/payload/`
- [ ] manifest.json / import_plan.json 扩到 6 个 asset entry / 7 个 op
- [ ] `Schemas/forgeue_import_evidence.schema.json` 新增 + 1 个 passing example 进 `Schemas/examples/`
- [ ] `Scripts/orchestrator/forgeue_manifest_importer.py` 加 `_import_asset_by_kind()` 内核 + 6 个 _build_*/_creator_path_* helper + bridge_python dispatch 分支
- [ ] `Content/Python/forgeue_rc_endpoint.py` + `init_unreal.py` 新增
- [ ] `Scripts/run_forgeue_real_smoke.py` 新增(选 bridge_mode 触发)
- [ ] `Tests/scripts/test_forgeue_real_ue_smoke.py` 新增(L2 marker)
- [ ] `pytest.ini` 加 `real_ue` marker 登记
- [ ] simulated 单测扩到含 6 种 asset_kind(L1)
- [ ] 实施第一步跑 §4.4 验证清单(curl /remote/object/describe)
- [ ] 跑 L3 一次,产出 `ProjectState/Reports/2026-05-27/forgeue_real_smoke/` 完整证据包
- [ ] 跑 `Scripts/validation/validate_examples.py --strict` 确认新 schema example pass(26 → 27 examples)
- [ ] `Docs/INDEX.md` / `Docs/FEATURE_INVENTORY.md` 同步登记新增 schema 数(41 主 → 42)+ 6 个新测试 + BC-NEW-A/B
- [ ] `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 主表登记 BC-NEW-A/B(P2/P1 候选)
- [ ] `AGENTS.md` / `CLAUDE.md` / `task.md` 同步 milestone 状态(由 document-release skill 强制)

---

## 11. 关联文档

- 上游契约:`Docs/archive/plugins/forgeue_manifest_integration.md`(archive 版,canonical 已搬到 `Docs/design/LLD/02_bridge.md` + `03_orchestrator.md`)
- 现行 importer:`Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`(168 行,simulated 已实现)
- 现行测试:`Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`(11 个测试 PASS)
- 现行 fixture:`Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/{manifest,import_plan}.json`(1 个 texture)
- LLD:`Docs/design/LLD/03_orchestrator.md` §3.8 `forgeue_manifest_importer`(F-ORC-08)
- 现行 evidence schema:`Plugins/AgentBridge/Schemas/evidence_manifest.schema.json`(Phase 10 MCP 用,外层 wrapper 复用)
- RC client:`Plugins/AgentBridge/Scripts/bridge/remote_control_client.py`(只调 API 不改本体)
- UE 5.7 BC 扫描:`Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`(本 spec 新增 BC-NEW-A/B 候选待登记)
- 总口径:`Docs/INDEX.md`
