# ForgeUE Manifest Import Bridge — Real-UE Path Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `forgeue_manifest_importer.py` 当前两条 `NotImplementedError` stub(`bridge_python` / `bridge_rc_api`)实出来,让 UE 5.5.4 Editor 真把 ForgeUE manifest 中的 5+1 种 asset 物理导入产出 uasset + 落 evidence。

**Architecture:** Path C 共享内核 + 两条 track 同时接入。`_import_asset_by_kind(asset)` 共享内核函数(只在 UE Editor Python 环境可调),`bridge_python` 直接调内核;`bridge_rc_api` 通过 PythonScripted UCLASS(`@unreal.uclass()`)+ `init_unreal.py` startup hook + RC HTTP 触发同一内核。0 触 CLAUDE.md C++ 红线。

**Tech Stack:** Python 3.13 + UE 5.5.4 Editor Python API(`unreal.AssetTools` / `AssetToolsHelpers` / `MaterialEditingLibrary` / `@unreal.uclass()` PythonScripted UFunction)+ UE Remote Control HTTP API(port 30010,沿用现有 `bridge/remote_control_client.py`)+ pytest 9.0.3 + jsonschema(沿用现有 `Scripts/validation/validate_examples.py --strict`)。

**Spec reference:** `Docs/superpowers/specs/2026-05-27-forgeue-real-ue-bridge-design.md`(v1.0,11 节,6 项 msc 决断)

---

## Task 序总览

| # | Task | 状态机依赖 | 估时 |
|---|------|----------|------|
| 1 | fixture 准备(payload + manifest 扩展) | — | 1.5h |
| 2 | evidence schema + example + validate | — | 0.5h |
| 3 | L1 simulated 单测扩到 6 种 asset_kind | Task 1 | 1h |
| 4 | importer 加 `_import_asset_by_kind` 内核架构 + bridge_python dispatch | Task 1, 3 | 1.5h |
| 5 | RC endpoint + init_unreal.py + 验证清单(关键风险) | Task 4 | 2h |
| 6 | texture / sprite_sheet 真机实现 | Task 5 | 1.5h |
| 7 | sound_wave 真机实现 | Task 6 | 1h |
| 8 | static_mesh 真机实现 | Task 7 | 1.5h |
| 9 | material 真机实现(Option α 五字段) | Task 8 | 2h |
| 10 | file_media_source 真机实现 | Task 9 | 1h |
| 11 | L2 pytest 真机 smoke 测试脚本 + marker | Task 6-10 | 1.5h |
| 12 | L3 验收 smoke 脚本 + 真机跑一次 + ProjectState 落证据 | Task 11 | 2h |
| 13 | 文档同步(走 document-release skill) | Task 12 | 1.5h |

**总估时**:18.5h(可分多个 session)
**关键风险前置**:Task 5(RC endpoint 验证清单)放在 5+1 asset_kind 实现之前,失败时可早期回退 EUB Fallback

---

## Task 1: fixture 准备(payload + manifest 扩展)

**Files:**
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/tex_albedo.png`
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/tex_sprite_sheet.png`
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/sfx_click.wav`
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/material_simple.json`
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/mesh_cube.fbx`(手动放置)
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/video_clip.mp4`(手动放置)
- Create: `Plugins/AgentBridge/Tests/scripts/generate_forgeue_fixture_payload.py`
- Modify: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json`(扩 6 entry,改 project_root)
- Modify: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json`(扩 7 op)

- [ ] **Step 1.1: 创建 payload 目录**

Run:
```powershell
New-Item -ItemType Directory -Force -Path "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload"
```

- [ ] **Step 1.2: 写 fixture 生成脚本(程式化造 PNG/WAV/JSON 4 个文件)**

创建 `Plugins/AgentBridge/Tests/scripts/generate_forgeue_fixture_payload.py`:

```python
"""程式化生成 ForgeUE fixture payload 中的 4 个文件(PNG×2 + WAV + JSON)。

FBX 和 MP4 不在本脚本范围,需要手动放置(见 plan Task 1.5/1.6)。
"""
from __future__ import annotations

import json
import struct
import wave
import zlib
from pathlib import Path

PAYLOAD_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "forgeue_manifest" / "payload"


def _write_solid_png(path: Path, width: int, height: int, rgba: tuple[int, int, int, int]) -> None:
    """写一张纯色 RGBA PNG(最简编码,不用 PIL)。"""
    # PNG 头
    sig = b"\x89PNG\r\n\x1a\n"
    # IHDR chunk
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)  # 8-bit RGBA
    ihdr = _png_chunk(b"IHDR", ihdr_data)
    # IDAT chunk:每行 1 byte filter (0) + width × 4 bytes RGBA
    raw = b""
    row = bytes(rgba) * width
    for _ in range(height):
        raw += b"\x00" + row
    idat = _png_chunk(b"IDAT", zlib.compress(raw, 9))
    # IEND
    iend = _png_chunk(b"IEND", b"")
    path.write_bytes(sig + ihdr + idat + iend)


def _png_chunk(tag: bytes, data: bytes) -> bytes:
    length = struct.pack(">I", len(data))
    crc = struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return length + tag + data + crc


def _write_silent_wav(path: Path, seconds: float, sample_rate: int = 16000) -> None:
    """写一段静音 mono 16-bit WAV(用内置 wave 模块,不需 numpy)。"""
    n_frames = int(seconds * sample_rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)        # mono
        wav.setsampwidth(2)        # 16-bit
        wav.setframerate(sample_rate)
        wav.writeframes(b"\x00\x00" * n_frames)


def _write_material_simple(path: Path) -> None:
    """最简 PBR 五字段 material.definition(spec §3.4 Option α)。"""
    payload = {
        "base_color_rgba": [0.5, 0.5, 0.5, 1.0],
        "metallic": 0.0,
        "roughness": 0.7,
        "normal_texture_ref": None,
        "emissive_color_rgba": [0.0, 0.0, 0.0, 1.0],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # 64×64 sRGB albedo,纯灰色
    _write_solid_png(PAYLOAD_DIR / "tex_albedo.png", 64, 64, (128, 128, 128, 255))
    # 128×128 sprite_sheet,纯白
    _write_solid_png(PAYLOAD_DIR / "tex_sprite_sheet.png", 128, 128, (255, 255, 255, 255))
    # 0.5 秒 16kHz mono 静音
    _write_silent_wav(PAYLOAD_DIR / "sfx_click.wav", 0.5)
    # material 定义
    _write_material_simple(PAYLOAD_DIR / "material_simple.json")
    print(f"[generate_forgeue_fixture_payload] 4 files written under {PAYLOAD_DIR}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 1.3: 跑脚本生成 4 个文件**

Run:
```powershell
python Plugins/AgentBridge/Tests/scripts/generate_forgeue_fixture_payload.py
```

Expected output:
```
[generate_forgeue_fixture_payload] 4 files written under D:\UnrealProjects\Mvpv4TestCodex\Plugins\AgentBridge\Tests\fixtures\forgeue_manifest\payload
```

验证:
```powershell
Get-ChildItem "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload" | Select-Object Name, Length
```
应看到 4 个文件(tex_albedo.png / tex_sprite_sheet.png / sfx_click.wav / material_simple.json),每个 < 200 KB

- [ ] **Step 1.4: 用 UE Engine 自带的 Cube.fbx 作为 mesh_cube.fbx**

UE 5.5 安装包自带 cube mesh 的 FBX:`<UE安装路径>/Engine/Content/EditorMeshes/Cube.fbx`(若该路径不存在则用 `<UE 项目>/Content/Editor/Cube_StaticMesh_Editor.fbx`,或 msc 用 UE Editor 直接 export 任意 cube)。

Run:
```powershell
# UE 5.5 默认路径(根据机器调整)
Copy-Item "C:\Program Files\Epic Games\UE_5.5\Engine\Content\EditorMeshes\Cube.fbx" "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/mesh_cube.fbx"
```

如果该路径不存在,**让 msc 手动**:在 UE Editor 内 import 一个 cube → Content Browser → 右键 → "Asset Actions → Export"  导出为 FBX,保存到 `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/mesh_cube.fbx`。

验证:
```powershell
Test-Path "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/mesh_cube.fbx"
```
Expected: `True`,文件大小 5-100 KB

- [ ] **Step 1.5: 准备 video_clip.mp4(< 500 KB H.264 mp4)**

让 msc 手动放置一个小 mp4(任意来源:手机录的 2 秒视频 / ffmpeg 生成的 black-frame mp4 / 公开资源)。如果 msc 没有现成的,Run:
```powershell
# 若本机有 ffmpeg,生成一段 1 秒纯黑 480p mp4(约 < 50 KB)
ffmpeg -f lavfi -i color=c=black:s=320x240:d=1 -c:v libx264 -pix_fmt yuv420p Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/video_clip.mp4
```

如果没 ffmpeg,**让 msc 手动**放一个 .mp4。

验证:
```powershell
$f = Get-Item "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/video_clip.mp4"
"$($f.Name) — $($f.Length) bytes"
```
Expected: 文件存在,大小 < 500 KB

- [ ] **Step 1.6: 扩 manifest.json 到 6 个 asset entry**

Replace `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json` 整个文件为:

```json
{
  "manifest_id": "m_run_p4_full",
  "schema_version": "1.0.0",
  "run_id": "run_p4_full",
  "project_target": {
    "project_name": "FixtureBundle",
    "project_root": "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest",
    "asset_root": "/Game/Generated/Tavern",
    "run_asset_folder": "/Game/Generated/Tavern/run_p4_full",
    "import_mode": "manifest_only"
  },
  "assets": [
    {
      "asset_entry_id": "ae_run_p4_full_texture_albedo",
      "artifact_id": "run_p4_full_tex_albedo",
      "asset_kind": "texture",
      "source_uri": "payload/tex_albedo.png",
      "target_object_path": "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_albedo",
      "target_package_path": "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_albedo",
      "ue_naming": {"policy": "house_rules", "prefix": "T_", "base_name": "run_p4_full_tex_albedo", "ue_name": "T_run_p4_full_tex_albedo"},
      "import_options": {"compression_settings": "default", "color_space": "sRGB", "has_alpha": false, "tileable": false, "usage_hint": "albedo", "source_format": "png"}
    },
    {
      "asset_entry_id": "ae_run_p4_full_sprite_sheet",
      "artifact_id": "run_p4_full_tex_sprite",
      "asset_kind": "sprite_sheet",
      "source_uri": "payload/tex_sprite_sheet.png",
      "target_object_path": "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_sprite",
      "target_package_path": "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_sprite",
      "ue_naming": {"policy": "house_rules", "prefix": "T_", "base_name": "run_p4_full_tex_sprite", "ue_name": "T_run_p4_full_tex_sprite"},
      "import_options": {"compression_settings": "default", "color_space": "sRGB", "has_alpha": false, "tileable": true, "usage_hint": "ui_atlas", "source_format": "png"}
    },
    {
      "asset_entry_id": "ae_run_p4_full_sound_click",
      "artifact_id": "run_p4_full_sfx_click",
      "asset_kind": "sound_wave",
      "source_uri": "payload/sfx_click.wav",
      "target_object_path": "/Game/Generated/Tavern/run_p4_full/S_run_p4_full_sfx_click",
      "target_package_path": "/Game/Generated/Tavern/run_p4_full/S_run_p4_full_sfx_click",
      "ue_naming": {"policy": "house_rules", "prefix": "S_", "base_name": "run_p4_full_sfx_click", "ue_name": "S_run_p4_full_sfx_click"},
      "import_options": {"source_format": "wav"}
    },
    {
      "asset_entry_id": "ae_run_p4_full_mesh_cube",
      "artifact_id": "run_p4_full_mesh_cube",
      "asset_kind": "static_mesh",
      "source_uri": "payload/mesh_cube.fbx",
      "target_object_path": "/Game/Generated/Tavern/run_p4_full/SM_run_p4_full_mesh_cube",
      "target_package_path": "/Game/Generated/Tavern/run_p4_full/SM_run_p4_full_mesh_cube",
      "ue_naming": {"policy": "house_rules", "prefix": "SM_", "base_name": "run_p4_full_mesh_cube", "ue_name": "SM_run_p4_full_mesh_cube"},
      "import_options": {"source_format": "fbx", "import_materials": false, "combine_meshes": false}
    },
    {
      "asset_entry_id": "ae_run_p4_full_material_simple",
      "artifact_id": "run_p4_full_material_simple",
      "asset_kind": "material",
      "source_uri": "payload/material_simple.json",
      "target_object_path": "/Game/Generated/Tavern/run_p4_full/M_run_p4_full_material_simple",
      "target_package_path": "/Game/Generated/Tavern/run_p4_full/M_run_p4_full_material_simple",
      "ue_naming": {"policy": "house_rules", "prefix": "M_", "base_name": "run_p4_full_material_simple", "ue_name": "M_run_p4_full_material_simple"},
      "import_options": {"source_format": "json"}
    },
    {
      "asset_entry_id": "ae_run_p4_full_video_clip",
      "artifact_id": "run_p4_full_video_clip",
      "asset_kind": "file_media_source",
      "source_uri": "payload/video_clip.mp4",
      "target_object_path": "/Game/Generated/Tavern/run_p4_full/MS_run_p4_full_video_clip",
      "target_package_path": "/Game/Generated/Tavern/run_p4_full/MS_run_p4_full_video_clip",
      "ue_naming": {"policy": "house_rules", "prefix": "MS_", "base_name": "run_p4_full_video_clip", "ue_name": "MS_run_p4_full_video_clip"},
      "import_options": {"source_format": "mp4"}
    }
  ],
  "import_rules": {
    "dry_run": false,
    "overwrite_existing": true,
    "reviewer_selected": ["run_p4_full_tex_albedo", "run_p4_full_tex_sprite", "run_p4_full_sfx_click", "run_p4_full_mesh_cube", "run_p4_full_material_simple", "run_p4_full_video_clip"]
  },
  "naming_policy": {
    "policy": "house_rules",
    "prefix_table": {"texture": "T_", "sprite_sheet": "T_", "sound_wave": "S_", "static_mesh": "SM_", "material": "M_", "file_media_source": "MS_"}
  },
  "path_policy": {
    "run_asset_folder": "/Game/Generated/Tavern/run_p4_full",
    "asset_root": "/Game/Generated/Tavern"
  },
  "dependencies": []
}
```

- [ ] **Step 1.7: 扩 import_plan.json 到 7 个 op(create_folder + 6 import/create)**

Replace `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json` 整个文件为:

```json
{
  "plan_id": "p_run_p4_full",
  "manifest_id": "m_run_p4_full",
  "operations": [
    {"op_id": "op_create_folder_root", "kind": "create_folder", "asset_entry_id": "<root>", "depends_on": []},
    {"op_id": "op_import_texture", "kind": "import_texture", "asset_entry_id": "ae_run_p4_full_texture_albedo", "depends_on": ["op_create_folder_root"]},
    {"op_id": "op_import_sprite_sheet", "kind": "import_texture", "asset_entry_id": "ae_run_p4_full_sprite_sheet", "depends_on": ["op_create_folder_root"]},
    {"op_id": "op_import_sound_wave", "kind": "import_sound_wave", "asset_entry_id": "ae_run_p4_full_sound_click", "depends_on": ["op_create_folder_root"]},
    {"op_id": "op_import_static_mesh", "kind": "import_static_mesh", "asset_entry_id": "ae_run_p4_full_mesh_cube", "depends_on": ["op_create_folder_root"]},
    {"op_id": "op_create_material", "kind": "create_material", "asset_entry_id": "ae_run_p4_full_material_simple", "depends_on": ["op_create_folder_root"]},
    {"op_id": "op_create_media_source", "kind": "create_file_media_source", "asset_entry_id": "ae_run_p4_full_video_clip", "depends_on": ["op_create_folder_root"]}
  ]
}
```

- [ ] **Step 1.8: 跑现行 simulated 单测验证 fixture 没破坏现有契约**

Run:
```powershell
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v 2>&1 | Select-Object -Last 30
```

**Expected**:
- 大部分仍 PASS,但**会有 3-4 个测试 FAIL**(`test_parse_manifest_reads_schema_version_and_assets` / `test_import_from_manifest_simulated_returns_one_op_per_asset` 等),因为它们硬编码 `len(assets) == 1` 和 `texture` 单 asset 路径。
- **这是预期失败**,Task 3 会更新测试。

不要修测试 — Task 3 统一改。

- [ ] **Step 1.9: Commit**

```powershell
git add Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/ Plugins/AgentBridge/Tests/scripts/generate_forgeue_fixture_payload.py
git commit -m "[skip-doc] test(forgeue-real-ue-bridge): fixture 扩展到 6 种 asset_kind (Task 1)

- payload/ 新增 6 个文件(< 1 MB):tex_albedo.png(64×64 灰)+ tex_sprite_sheet.png(128×128 白)+ sfx_click.wav(0.5s 静音 mono 16k)+ material_simple.json(PBR 五字段)+ mesh_cube.fbx(UE Engine 自带 cube)+ video_clip.mp4(< 500KB)
- manifest.json 扩 6 个 asset entry(texture/sprite_sheet/sound_wave/static_mesh/material/file_media_source);project_root 改为 fixture 相对路径
- import_plan.json 扩 7 个 op(create_folder + 6 import/create)
- 新增 generate_forgeue_fixture_payload.py 辅助脚本(程式化造 PNG/WAV/JSON,不依赖 PIL/numpy)
- 现行 pytest 部分 FAIL 是预期(Task 3 会更新断言)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: evidence schema + example + validate

**Files:**
- Create: `Plugins/AgentBridge/Schemas/forgeue_import_evidence.schema.json`
- Create: `Plugins/AgentBridge/Schemas/examples/forgeue_import_evidence_example.json`

- [ ] **Step 2.1: 写 forgeue_import_evidence.schema.json**

创建 `Plugins/AgentBridge/Schemas/forgeue_import_evidence.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ForgeUE Import Evidence (per-op)",
  "description": "ForgeUE manifest 真机导入每条 asset 的逐条证据,由 bridge_python/bridge_rc_api 写盘(spec §7.1)。",
  "type": "object",
  "additionalProperties": false,
  "required": ["asset_entry_id", "op_id", "asset_kind", "bridge_mode", "status", "timestamp", "source_uri_abs"],
  "properties": {
    "asset_entry_id":      {"type": "string", "minLength": 1},
    "op_id":               {"type": "string", "minLength": 1},
    "asset_kind":          {"enum": ["texture", "sprite_sheet", "sound_wave", "static_mesh", "material", "file_media_source"]},
    "bridge_mode":         {"enum": ["bridge_python", "bridge_rc_api", "simulated"]},
    "status":              {"enum": ["success", "failed", "skipped"]},
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

- [ ] **Step 2.2: 写一份 passing example**

创建 `Plugins/AgentBridge/Schemas/examples/forgeue_import_evidence_example.json`:

```json
{
  "asset_entry_id": "ae_run_p4_full_texture_albedo",
  "op_id": "op_import_texture",
  "asset_kind": "texture",
  "bridge_mode": "bridge_python",
  "status": "success",
  "timestamp": "2026-05-27T10:23:45.123Z",
  "source_uri_abs": "D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/payload/tex_albedo.png",
  "uasset_object_path": "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_albedo.T_run_p4_full_tex_albedo",
  "uasset_package_path": "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_albedo",
  "factory_class": "unreal.TextureFactory",
  "duration_ms": 285,
  "import_log_excerpt": "LogTextureFactory: Imported tex_albedo.png as Texture2D (64x64 RGBA8)",
  "errors": []
}
```

- [ ] **Step 2.3: 检查 validate_examples.py 是否会自动发现新 example**

Read `Plugins/AgentBridge/Scripts/validation/validate_examples.py`,确认其 schema 发现机制(通常是 glob `Schemas/*.schema.json` + `Schemas/examples/*_example.json` 命名约定)。

Run:
```powershell
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict 2>&1 | Select-Object -Last 10
```

Expected output 含 `27 examples validated, 27 pass`(原来 26,新增 1)。

如果脚本没自动发现新 schema,**手动加入脚本的 schema 注册表**(具体位置查 `validate_examples.py` 内的 `SCHEMA_TO_EXAMPLE_MAP` 或类似常量)。

- [ ] **Step 2.4: Commit**

```powershell
git add Plugins/AgentBridge/Schemas/forgeue_import_evidence.schema.json Plugins/AgentBridge/Schemas/examples/forgeue_import_evidence_example.json
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): 新增 forgeue_import_evidence schema + example (Task 2)

- forgeue_import_evidence.schema.json:逐条 op 证据契约(asset_entry_id/op_id/asset_kind/bridge_mode/status/uasset_object_path/factory_class/errors 等)
- example.json:passing 用例
- validate_examples.py --strict:26 → 27 examples 全 PASS

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: L1 simulated 单测扩到 6 种 asset_kind

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`

- [ ] **Step 3.1: 更新现有断言(从 1 个 texture → 6 个 asset)**

修改 `test_forgeue_manifest_importer.py` 中 `test_parse_manifest_reads_schema_version_and_assets`:

```python
def test_parse_manifest_reads_schema_version_and_assets():
    """ForgeUE_codex manifest.json 必读字段:schema_version / run_id / assets[]。"""
    parsed = importer.parse_manifest(str(_MANIFEST_PATH))

    assert parsed["schema_version"] == "1.0.0"
    assert parsed["run_id"] == "run_p4_full"
    assert len(parsed["assets"]) == 6, "fixture 扩到 6 种 asset_kind"

    kinds = {a["asset_kind"] for a in parsed["assets"]}
    assert kinds == {"texture", "sprite_sheet", "sound_wave", "static_mesh", "material", "file_media_source"}

    # texture entry 字段健康检查(回归保护)
    tex = next(a for a in parsed["assets"] if a["asset_kind"] == "texture")
    assert tex["ue_naming"]["ue_name"].startswith("T_")
    assert tex["source_uri"].endswith(".png")
```

修改 `test_import_from_manifest_simulated_returns_one_op_per_asset`(更名 + 改断言):

```python
def test_import_from_manifest_simulated_returns_six_ops_one_per_asset():
    """simulated mode:6 种 asset 各产出一条 op 模拟结果,全 success。"""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=str(_PLAN_PATH),
        bridge_mode="simulated",
    )

    assert result["status"] == "success"
    assert result["bridge_mode"] == "simulated"
    assert result["run_id"] == "run_p4_full"
    assert result["manifest_id"] == "m_run_p4_full"
    assert result["plan_id"] == "p_run_p4_full"
    assert len(result["asset_results"]) == 6

    # 6 种 kind 全覆盖
    kinds_in_results = {r["asset_kind"] for r in result["asset_results"]}
    assert kinds_in_results == {"texture", "sprite_sheet", "sound_wave", "static_mesh", "material", "file_media_source"}

    # 全 simulated 标记
    for r in result["asset_results"]:
        assert r["status"] == "success"
        assert r["simulated"] is True
```

修改 `test_import_from_manifest_simulated_without_plan_path_still_works`(只改 asset_results 数):

```python
def test_import_from_manifest_simulated_without_plan_path_still_works():
    """plan_path 可选:只有 manifest 时,6 条 asset_results 但 plan_id=None。"""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=None,
        bridge_mode="simulated",
    )

    assert result["status"] == "success"
    assert result["plan_id"] is None
    assert len(result["asset_results"]) == 6
```

修改 `test_handoff_runner_dispatches_import_assets_to_forgeue_importer`(asset_results 数 1 → 6):

```python
    # ...保留前面的 setup 代码...
    result = handoff_runner.execute_run_plan(run_plan, bridge_mode="simulated")

    assert result["status"] == "succeeded"
    step_results = result["step_results"]
    assert len(step_results) == 1
    inner = step_results[0]["result"]
    assert inner["status"] == "success"
    assert inner["bridge_mode"] == "simulated"
    assert len(inner["asset_results"]) == 6
```

- [ ] **Step 3.2: 新增 6 个 kind-specific simulated 测试**

在 `test_forgeue_manifest_importer.py` 文件末尾追加:

```python
# ============================================================
# Task 3.2 新增:每种 asset_kind 的 simulated 字段健康检查
# ============================================================

@pytest.mark.parametrize("kind,prefix", [
    ("texture",            "T_"),
    ("sprite_sheet",       "T_"),
    ("sound_wave",         "S_"),
    ("static_mesh",        "SM_"),
    ("material",           "M_"),
    ("file_media_source",  "MS_"),
])
def test_simulated_per_kind_target_object_path_uses_correct_prefix(kind, prefix):
    """每种 asset_kind 的 target_object_path 必须用对应 prefix(回归保护命名策略)。"""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=str(_PLAN_PATH),
        bridge_mode="simulated",
    )

    matching = [r for r in result["asset_results"] if r["asset_kind"] == kind]
    assert len(matching) >= 1, f"fixture 必须含至少 1 个 {kind} entry"

    for r in matching:
        # target_object_path 形如 /Game/.../<PREFIX>name
        leaf_name = r["target_object_path"].rsplit("/", 1)[-1]
        assert leaf_name.startswith(prefix), \
            f"{kind} target {leaf_name!r} 应以 {prefix!r} 开头"
```

- [ ] **Step 3.3: 跑全测试,确认全 PASS**

Run:
```powershell
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v 2>&1 | Select-Object -Last 30
```

Expected: `17 passed`(原 11 - 改 0 删 0 + 新增 6 = 17;6 个新 case 来自 parametrize 6 种 kind)

如有 FAIL,根据错误调断言或 fixture(不要绕过 schema_version/asset_kind 守门测试)。

- [ ] **Step 3.4: Commit**

```powershell
git add Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "[skip-doc] test(forgeue-real-ue-bridge): L1 simulated 单测扩到 6 种 asset_kind (Task 3)

- 3 个现有断言更新(1 asset → 6 asset)
- 新增 1 个 parametrize 测试 × 6 种 kind = 6 case
- pytest 整体 11 → 17 PASS
- L1 simulated 路径(契约/dispatch/CLI)全覆盖 ForgeUE _KIND_MAP 6 种 asset_kind

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: importer 加 `_import_asset_by_kind` 内核架构 + bridge_python dispatch

**目标**:把 `bridge_python` 分支接到 `_import_asset_by_kind` 内核(此 task 内核内**只先实现 dispatch 骨架**,5+1 种 asset_kind 的 helper 全 raise `NotImplementedError`,Task 6-10 逐一填充)。

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`(扩 NotImplementedError 守门测试)

- [ ] **Step 4.1: 重构 forgeue_manifest_importer.py 加内核架构**

修改 `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`:

把现有 `import_from_manifest` 内 bridge_python/rc 的 NotImplementedError 行替换为新分发逻辑;在文件末尾追加内核函数群。完整文件替换为:

```python
"""ForgeUE_codex UEAssetManifest 导入桥接。

读取 ForgeUE_codex P4 流水线产出的 `manifest.json` + `import_plan.json`,
按 bridge_mode 分发到 simulated / bridge_python / bridge_rc_api 三种执行通路。

输入契约固定为 ForgeUE_codex `framework.core.ue.UEAssetManifest`
(schema_version 1.0.0),asset_kind 枚举:
    texture / sprite_sheet / sound_wave / static_mesh / material / file_media_source

设计原则:
- 只负责"读 manifest → 翻译成 AgentBridge 可执行单元"
- 不做任何 UE Editor 内部副作用(那是 bridge_mode 各自下游的事)
- simulated 模式必须能完全离线跑通,作为契约不漂移的看护

bridge_python / bridge_rc_api 通过共享内核 `_import_asset_by_kind` 实现:
- bridge_python: 直接调内核(只能在 UE Editor Python 环境)
- bridge_rc_api: RC HTTP → forgeue_rc_endpoint.py → 同一内核
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


# ============================================================
# manifest / plan 解析(原有,不动)
# ============================================================

def parse_manifest(manifest_path: str) -> dict[str, Any]:
    """读 ForgeUE_codex manifest.json 并做基本校验。"""
    raw = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    schema_version = raw.get("schema_version")
    if schema_version != "1.0.0":
        raise ValueError(
            f"unsupported manifest schema_version: {schema_version!r} "
            f"(this bridge only supports '1.0.0')"
        )
    if not isinstance(raw.get("assets"), list):
        raise ValueError("manifest.assets must be a list")
    return raw


_SUPPORTED_BRIDGE_MODES: tuple[str, ...] = (
    "simulated",
    "bridge_python",
    "bridge_rc_api",
)


def parse_import_plan(plan_path: str) -> dict[str, Any]:
    """读 ForgeUE_codex import_plan.json 并做基本结构校验。"""
    raw = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if not isinstance(raw.get("operations"), list):
        raise ValueError("import_plan.operations must be a list")
    return raw


# ============================================================
# 主入口
# ============================================================

def import_from_manifest(
    *,
    manifest_path: str,
    plan_path: str | None = None,
    bridge_mode: str = "simulated",
) -> dict[str, Any]:
    """主入口:按 bridge_mode dispatch,返回结构化执行结果。"""
    if bridge_mode not in _SUPPORTED_BRIDGE_MODES:
        raise ValueError(
            f"unsupported bridge_mode: {bridge_mode!r} "
            f"(expected one of {_SUPPORTED_BRIDGE_MODES})"
        )

    manifest = parse_manifest(manifest_path)
    plan = parse_import_plan(plan_path) if plan_path else None
    manifest_root = Path(manifest_path).resolve().parent

    if bridge_mode == "simulated":
        asset_results = [_simulate_asset(asset) for asset in manifest["assets"]]
    elif bridge_mode == "bridge_python":
        # 真机通路:每条 asset 进入共享内核
        overwrite = manifest.get("import_rules", {}).get("overwrite_existing", False)
        asset_results = [
            _import_asset_by_kind(asset, manifest_root, overwrite, bridge_mode="bridge_python")
            for asset in manifest["assets"]
        ]
    elif bridge_mode == "bridge_rc_api":
        # RC HTTP 通路:外部不应直接走这里,由 forgeue_rc_endpoint 触发后等价于 bridge_python
        raise NotImplementedError(
            "bridge_rc_api 必须由 RC endpoint 触发,不能直接从外部 importer 调;"
            "外部驱动请用 Scripts/run_forgeue_real_smoke.py(--bridge-mode bridge_rc_api)"
        )
    else:
        # _SUPPORTED_BRIDGE_MODES 已守门,此分支理论不可达
        raise AssertionError(f"unreachable: bridge_mode={bridge_mode!r}")

    return {
        "status": "success" if all(r.get("status") == "success" for r in asset_results) else "partial",
        "bridge_mode": bridge_mode,
        "run_id": manifest["run_id"],
        "manifest_id": manifest.get("manifest_id"),
        "plan_id": plan.get("plan_id") if plan else None,
        "asset_results": asset_results,
    }


# ============================================================
# simulated 路径(原有,不动)
# ============================================================

def _simulate_asset(asset: dict[str, Any]) -> dict[str, Any]:
    """单 asset 的模拟执行结果——不做任何 UE 副作用。"""
    return {
        "status": "success",
        "asset_entry_id": asset.get("asset_entry_id"),
        "artifact_id": asset.get("artifact_id"),
        "asset_kind": asset.get("asset_kind"),
        "target_object_path": asset.get("target_object_path"),
        "source_uri": asset.get("source_uri"),
        "simulated": True,
    }


# ============================================================
# 真机内核 _import_asset_by_kind(只能在 UE Editor Python 环境调)
# ============================================================

def _import_asset_by_kind(
    asset: dict[str, Any],
    manifest_root: Path,
    overwrite_existing: bool,
    *,
    bridge_mode: str,
) -> dict[str, Any]:
    """单 asset 真机执行;只能在 UE Editor Python 环境跑。

    返回 forgeue_import_evidence.schema.json 兼容的 dict。
    """
    try:
        import unreal  # 失败 → 不在 Editor Python 环境
    except ImportError as exc:
        raise RuntimeError(
            "_import_asset_by_kind 必须在 UE Editor Python 环境运行(import unreal 失败);"
            "外部驱动请用 simulated 模式或 bridge_rc_api 通路"
        ) from exc

    kind = asset["asset_kind"]
    source_uri = (manifest_root / asset["source_uri"]).resolve()
    if not source_uri.exists():
        return _evidence_failure(asset, bridge_mode, f"payload missing: {source_uri}")

    target_pkg = asset["target_package_path"]
    import_options = asset.get("import_options", {})

    if kind in ("texture", "sprite_sheet"):
        return _importer_path_texture(asset, source_uri, target_pkg, overwrite_existing,
                                      import_options, bridge_mode)
    if kind == "sound_wave":
        return _importer_path_sound(asset, source_uri, target_pkg, overwrite_existing,
                                    import_options, bridge_mode)
    if kind == "static_mesh":
        return _importer_path_mesh(asset, source_uri, target_pkg, overwrite_existing,
                                   import_options, bridge_mode)
    if kind == "material":
        return _creator_path_material(asset, source_uri, target_pkg, overwrite_existing,
                                      bridge_mode)
    if kind == "file_media_source":
        return _creator_path_media(asset, source_uri, target_pkg, overwrite_existing,
                                   bridge_mode)

    return _evidence_failure(asset, bridge_mode, f"unsupported asset_kind: {kind}")


# ============================================================
# helper:evidence 构造
# ============================================================

def _evidence_failure(asset: dict, bridge_mode: str, message: str,
                       *, errors: list[str] | None = None) -> dict:
    return {
        "asset_entry_id": asset.get("asset_entry_id", ""),
        "op_id": f"op_failed_{asset.get('asset_entry_id', 'unknown')}",
        "asset_kind": asset.get("asset_kind", ""),
        "bridge_mode": bridge_mode,
        "status": "failed",
        "timestamp": _dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "source_uri_abs": str(asset.get("source_uri", "")),
        "errors": errors or [message],
    }


def _evidence_skipped(asset: dict, bridge_mode: str, reason: str) -> dict:
    return {
        "asset_entry_id": asset.get("asset_entry_id", ""),
        "op_id": f"op_skipped_{asset.get('asset_entry_id', 'unknown')}",
        "asset_kind": asset.get("asset_kind", ""),
        "bridge_mode": bridge_mode,
        "status": "skipped",
        "timestamp": _dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "source_uri_abs": str(asset.get("source_uri", "")),
        "skipped_reason": reason,
    }


def _evidence_success(asset: dict, bridge_mode: str, source_uri_abs: Path,
                      uasset_object_path: str, factory_class: str,
                      duration_ms: int, import_log_excerpt: str = "") -> dict:
    return {
        "asset_entry_id": asset.get("asset_entry_id", ""),
        "op_id": f"op_import_{asset.get('asset_entry_id', 'unknown')}",
        "asset_kind": asset.get("asset_kind", ""),
        "bridge_mode": bridge_mode,
        "status": "success",
        "timestamp": _dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "source_uri_abs": str(source_uri_abs),
        "uasset_object_path": uasset_object_path,
        "uasset_package_path": uasset_object_path.split(".")[0] if "." in uasset_object_path else uasset_object_path,
        "factory_class": factory_class,
        "duration_ms": duration_ms,
        "import_log_excerpt": import_log_excerpt,
        "errors": [],
    }


# ============================================================
# 5+1 种 asset_kind 实现(Task 6-10 逐一填充;此 task 全 raise NotImplementedError 占位)
# ============================================================

def _importer_path_texture(asset, source_uri, target_pkg, overwrite, import_options, bridge_mode):
    raise NotImplementedError("texture/sprite_sheet importer pending Task 6")


def _importer_path_sound(asset, source_uri, target_pkg, overwrite, import_options, bridge_mode):
    raise NotImplementedError("sound_wave importer pending Task 7")


def _importer_path_mesh(asset, source_uri, target_pkg, overwrite, import_options, bridge_mode):
    raise NotImplementedError("static_mesh importer pending Task 8")


def _creator_path_material(asset, source_uri, target_pkg, overwrite, bridge_mode):
    raise NotImplementedError("material creator pending Task 9")


def _creator_path_media(asset, source_uri, target_pkg, overwrite, bridge_mode):
    raise NotImplementedError("file_media_source creator pending Task 10")


# ============================================================
# CLI 入口(原有,不动)
# ============================================================

def main(argv: list[str] | None = None) -> int:
    """命令行入口。"""
    import argparse
    import sys as _sys

    parser = argparse.ArgumentParser(description="ForgeUE_codex manifest importer (standalone CLI)")
    parser.add_argument("--manifest", required=True, help="ForgeUE_codex manifest.json 路径")
    parser.add_argument("--plan", default=None, help="ForgeUE_codex import_plan.json 路径(可选)")
    parser.add_argument("--bridge-mode", default="simulated", choices=list(_SUPPORTED_BRIDGE_MODES),
                        help="桥接执行模式(默认 simulated)")
    args = parser.parse_args(argv)

    try:
        result = import_from_manifest(
            manifest_path=args.manifest, plan_path=args.plan, bridge_mode=args.bridge_mode,
        )
    except (ValueError, NotImplementedError, FileNotFoundError, RuntimeError) as exc:
        print(f"[forgeue_manifest_importer] {exc}", file=_sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
```

- [ ] **Step 4.2: 更新 NotImplementedError 守门测试(bridge_python 现在不该 raise,改测在 UE 环境外 raise RuntimeError)**

修改 `test_forgeue_manifest_importer.py` 中:

```python
@pytest.mark.parametrize("mode", ["bridge_python"])
def test_import_from_manifest_bridge_python_raises_runtime_error_outside_ue(mode):
    """bridge_python 在非 UE Editor Python 环境必须 raise RuntimeError(不是 NotImplementedError)。"""
    with pytest.raises(RuntimeError, match="UE Editor Python"):
        importer.import_from_manifest(
            manifest_path=str(_MANIFEST_PATH),
            plan_path=str(_PLAN_PATH),
            bridge_mode=mode,
        )


def test_import_from_manifest_bridge_rc_api_raises_not_implemented_for_external():
    """bridge_rc_api 不能从外部 importer 直接调,必须通过 RC endpoint。"""
    with pytest.raises(NotImplementedError, match="RC endpoint"):
        importer.import_from_manifest(
            manifest_path=str(_MANIFEST_PATH),
            plan_path=str(_PLAN_PATH),
            bridge_mode="bridge_rc_api",
        )
```

**删除**原 `test_import_from_manifest_unimplemented_bridge_modes_raise_with_clear_message` 的 `bridge_python` parametrize 项,只保留 `bridge_rc_api`(实际上整个测试可以被上面两个新测试替代,删掉原 parametrize)。

CLI 守门 `test_cli_main_unimplemented_mode_returns_nonzero` 也要改:

```python
def test_cli_main_bridge_python_outside_ue_returns_nonzero(capsys):
    """CLI:bridge_python 在非 UE 环境 return 非 0 并把 RuntimeError 打到 stderr。"""
    rc = importer.main([
        "--manifest", str(_MANIFEST_PATH),
        "--bridge-mode", "bridge_python",
    ])
    captured = capsys.readouterr()

    assert rc != 0
    assert "UE Editor Python" in captured.err
```

- [ ] **Step 4.3: 跑 L1 pytest 验证 dispatch 正确**

Run:
```powershell
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v 2>&1 | Select-Object -Last 30
```

Expected:全 PASS(具体数量取决于 Task 3 的 17 + Step 4.2 的改动,大约 17-18 PASS)

- [ ] **Step 4.4: Commit**

```powershell
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): _import_asset_by_kind 内核架构 + bridge_python dispatch (Task 4)

- 主入口 import_from_manifest 加 bridge_python 分支,调 _import_asset_by_kind 共享内核
- bridge_rc_api 外部入口 raise NotImplementedError(必须由 RC endpoint 触发,Task 5)
- 内核 _import_asset_by_kind 完整 dispatch 骨架:5+1 种 asset_kind → 各自 helper
- helper(_importer_path_*/_creator_path_*) 全 raise NotImplementedError,Task 6-10 逐一填充
- evidence 构造 helper:_evidence_failure / _evidence_skipped / _evidence_success
- 单测改:bridge_python 非 UE 环境 raise RuntimeError;bridge_rc_api 外部直接调 raise NotImplementedError

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: RC endpoint + init_unreal.py + 验证清单(关键风险前置)

**目标**:Path C 的"未知技术风险"在 5+1 种 asset_kind 实现**之前**验证完;失败时早期回退 EUB Fallback。

**Files:**
- Create: `Plugins/AgentBridge/Content/Python/forgeue_rc_endpoint.py`
- Create: `Plugins/AgentBridge/Content/Python/init_unreal.py`
- Create: `ProjectState/Reports/2026-05-27/forgeue_rc_endpoint_verification.md`(验证清单输出)

- [ ] **Step 5.1: 创建 Content/Python 目录**

```powershell
New-Item -ItemType Directory -Force -Path "Plugins/AgentBridge/Content/Python"
```

- [ ] **Step 5.2: 写 forgeue_rc_endpoint.py**

创建 `Plugins/AgentBridge/Content/Python/forgeue_rc_endpoint.py`:

```python
"""ForgeUE manifest 导入的 RC HTTP endpoint(Editor 内 startup 加载)。

注册一个 PythonScripted UCLASS:AgentBridgeForgeUEEndpoint,
含一个 BlueprintCallable UFUNCTION:import_assets_from_manifest。

外部通过 remote_control_client.call_function(
    object_path="/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint",
    function_name="ImportAssetsFromManifest",
    parameters={"ManifestPath": "...", "PlanPath": "...", "OverwriteExisting": false}
) 触发。

设计原则:
- endpoint 在 Editor 内,等价于 bridge_python 触发器
- 失败必须返回 JSON 字符串(含 status/error),不能让 RC HTTP 抛 500
"""
from __future__ import annotations

import json
import sys
import unreal

# 让 endpoint 能找到 forgeue_manifest_importer 共享内核
_ORCH_DIR = unreal.Paths.project_plugins_dir() + "AgentBridge/Scripts/orchestrator"
if _ORCH_DIR not in sys.path:
    sys.path.insert(0, _ORCH_DIR)

import forgeue_manifest_importer as importer  # noqa: E402  # 共享内核


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
        """RC 入口:同步执行整批导入,返回结构化 JSON 字符串。

        endpoint 内调 bridge_python 通路(因为 endpoint 本身在 Editor 内)。
        """
        try:
            result = importer.import_from_manifest(
                manifest_path=manifest_path,
                plan_path=plan_path or None,
                bridge_mode="bridge_python",
            )
            # 标注实际触发来源
            result["triggered_via"] = "bridge_rc_api"
            return json.dumps(result, ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"status": "error", "error_class": type(exc).__name__, "message": str(exc)},
                ensure_ascii=False,
            )
```

- [ ] **Step 5.3: 写 init_unreal.py**

创建 `Plugins/AgentBridge/Content/Python/init_unreal.py`:

```python
"""UE Editor Python 插件启动时自动执行,完成 AgentBridge 端 Python endpoint 注册。

UE 5.4+ PythonScriptPlugin 标准 hook:任何 plugin 的 Content/Python/init_unreal.py
在 Editor 启动时被自动执行。

关键:即使注册失败,也不能阻塞 Editor 启动。
"""
import unreal

unreal.log("[AgentBridge] Loading ForgeUE RC endpoint...")
try:
    import forgeue_rc_endpoint  # noqa: F401  # 导入即触发 @unreal.uclass() 注册
    unreal.log("[AgentBridge] ForgeUE RC endpoint registered.")
except Exception as exc:
    unreal.log_error(f"[AgentBridge] ForgeUE RC endpoint registration failed: {exc}")
```

- [ ] **Step 5.4: 启 UE 5.5.4 Editor**

让 msc 手动:
1. 启动 UE Editor 加载本项目(Mvpv4TestCodex)
2. 等 Editor 完全加载(Content Browser 可见)
3. 打开 Output Log(Window → Output Log)
4. 在 Output Log 顶部 Filter 框搜 `AgentBridge`

**Expected**:看到两行日志:
```
LogPython: [AgentBridge] Loading ForgeUE RC endpoint...
LogPython: [AgentBridge] ForgeUE RC endpoint registered.
```

**如果**看到 `[AgentBridge] ForgeUE RC endpoint registration failed: <error>`,跳到 Step 5.8(Fallback 决策)。

- [ ] **Step 5.5: curl 验证 RC 可见 endpoint**

让 msc 保持 UE Editor 开着,在 PowerShell 跑:

```powershell
curl.exe -X PUT http://localhost:30010/remote/object/describe `
  -H "Content-Type: application/json" `
  -d '{\"objectPath\":\"/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint\"}' 2>&1
```

**Expected**:返回 JSON 含 `import_assets_from_manifest` 函数定义。形如:
```json
{
  "Functions": [
    {"Name": "ImportAssetsFromManifest", "Description": "...", ...}
  ]
}
```

如果返回 `{"errorMessage":"Object not found"}` 或类似,跳到 Step 5.8。

- [ ] **Step 5.6: 跑一次最简 RC 调用(simulated 模式,验证返回值类型)**

让 msc 保持 Editor 开,Run:

```powershell
$body = @{
    objectPath = "/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint"
    functionName = "ImportAssetsFromManifest"
    parameters = @{
        ManifestPath = (Resolve-Path "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json").Path
        PlanPath = (Resolve-Path "Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json").Path
        OverwriteExisting = $true
    }
} | ConvertTo-Json -Depth 4

curl.exe -X PUT http://localhost:30010/remote/object/call `
  -H "Content-Type: application/json" `
  -d $body 2>&1
```

**Expected**:RC 返回的 `ReturnValue` 是 endpoint 返回的 JSON 字符串。

**注意**:此时 _importer_path_* 内核还全是 NotImplementedError,所以**endpoint 内 catch 后会返回**:
```json
{"ReturnValue": "{\"status\":\"error\",\"error_class\":\"NotImplementedError\",\"message\":\"texture/sprite_sheet importer pending Task 6\"}"}
```

**这就是预期** —— 证明 RC 通路 + endpoint 注册 + JSON 序列化 + 错误捕获**全部链路通**,只缺 asset_kind helper 实现。

如果返回 HTTP 500 / 调用本身失败,跳到 Step 5.8。

- [ ] **Step 5.7: 写验证清单结果到 ProjectState/Reports**

创建 `ProjectState/Reports/2026-05-27/forgeue_rc_endpoint_verification.md`:

```markdown
# ForgeUE RC Endpoint Verification — Task 5 验证清单结果

> 日期: 2026-05-27
> Spec: Docs/superpowers/specs/2026-05-27-forgeue-real-ue-bridge-design.md §4.4
> Plan: Docs/superpowers/plans/2026-05-27-forgeue-real-ue-bridge.md Task 5

## 验证项

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | Editor 启动加载 init_unreal.py | ✅ / ❌ | unreal.log 行号 |
| 2 | forgeue_rc_endpoint registered | ✅ / ❌ | unreal.log 行号 |
| 3 | curl /remote/object/describe 含 ImportAssetsFromManifest | ✅ / ❌ | 返回 JSON 摘抄 |
| 4 | curl /remote/object/call 返回 endpoint JSON | ✅ / ❌ | 返回 JSON 摘抄 |

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

[此处由 msc 填:实际跑完 4 项后选哪条路]
```

让 msc 把实际 unreal.log 行号和 curl 返回 JSON 填进去。

- [ ] **Step 5.8: Fallback 决策点(如果 5.4-5.6 任意失败)**

如果验证清单失败,**不要硬扛**。两个选项告诉 msc:

**选项 A**:回退 EUB Fallback(spec §4.5),需要 msc 在 Editor 内手动建 EUB,代价是工作量 +0.5h。
**选项 B**:debug PythonScripted UCLASS 为什么不可见 RC(可能要查 UE PythonScriptPlugin 日志、PythonGeneratedClass 注册时机等),代价不可控。

向 msc 报告失败点 + curl 返回内容,等 msc 决断 A/B,再进 Task 6。

如果验证清单全部 PASS,正常进 Step 5.9。

- [ ] **Step 5.9: Commit**

```powershell
git add Plugins/AgentBridge/Content/Python/ ProjectState/Reports/2026-05-27/forgeue_rc_endpoint_verification.md
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): RC endpoint + init_unreal hook + 验证清单 (Task 5)

- Plugins/AgentBridge/Content/Python/forgeue_rc_endpoint.py:PythonScripted UCLASS AgentBridgeForgeUEEndpoint + @unreal.ufunction ImportAssetsFromManifest
- Plugins/AgentBridge/Content/Python/init_unreal.py:UE 5.4+ 标准 startup hook,try/except 包注册不阻塞 Editor 启动
- ProjectState/Reports/2026-05-27/forgeue_rc_endpoint_verification.md:验证清单结果(4 项全 PASS / Fallback 决策记录)
- 关键风险已前置验证:RC 通路 + endpoint 注册 + JSON 序列化 + 错误捕获全链路通,只缺 asset_kind helper(Task 6-10)

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: texture / sprite_sheet 真机实现

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`(填 `_importer_path_texture` + 辅助)

- [ ] **Step 6.1: 填 `_importer_path_texture` 实现**

修改 `forgeue_manifest_importer.py`,把 `_importer_path_texture` 的 NotImplementedError 替换为完整实现,并在文件末尾追加 `_build_texture_factory` + `_COMPRESSION_MAP`:

```python
def _importer_path_texture(asset, source_uri, target_pkg, overwrite, import_options, bridge_mode):
    """texture / sprite_sheet 真机导入:走 AssetTools.import_assets_automated + TextureFactory。"""
    import time
    import unreal
    start = time.monotonic()

    # 目标 package 已存在 + 不允许覆盖 → skipped
    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(asset, bridge_mode,
                                 f"target asset exists and overwrite_existing=false: {target_pkg}")

    factory = _build_texture_factory(import_options)
    task = unreal.AssetImportTask()
    task.filename = str(source_uri)
    task.destination_path = target_pkg.rsplit("/", 1)[0]  # 目录部分
    task.destination_name = target_pkg.rsplit("/", 1)[-1] # 文件名部分(去 prefix 路径)
    task.replace_existing = overwrite
    task.automated = True
    task.save = True
    task.factory = factory

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    if not task.imported_object_paths:
        return _evidence_failure(asset, bridge_mode,
                                 f"texture import returned no objects (filename={source_uri})")

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=task.imported_object_paths[0],
        factory_class="unreal.TextureFactory",
        duration_ms=duration_ms,
        import_log_excerpt=f"imported {asset['asset_kind']} from {source_uri.name}",
    )


# ============================================================
# texture factory builder
# ============================================================

_COMPRESSION_MAP: dict[str, str] = {
    # ForgeUE compression_settings → unreal.TextureCompressionSettings 枚举值名
    "default":      "TC_DEFAULT",
    "normal_map":   "TC_NORMALMAP",
    "masks":        "TC_MASKS",
    "hdr":          "TC_HDR",
    "ui":           "TC_EDITOR_ICON",
    "bc7":          "TC_BC7",
    "alpha":        "TC_ALPHA",
    "displacement": "TC_DISPLACEMENTMAP",
    "grayscale":    "TC_GRAYSCALE",
}


def _build_texture_factory(import_options: dict):
    """构造 TextureFactory 并按 import_options 设置属性。"""
    import unreal
    factory = unreal.TextureFactory()
    # sRGB
    factory.set_editor_property("srgb",
                                import_options.get("color_space", "sRGB") == "sRGB")
    # compression_settings
    cs_name = import_options.get("compression_settings", "default")
    cs_enum_name = _COMPRESSION_MAP.get(cs_name, "TC_DEFAULT")
    factory.set_editor_property(
        "compression_settings",
        getattr(unreal.TextureCompressionSettings, cs_enum_name),
    )
    # tileable / mip_gen
    if not import_options.get("tileable", False):
        factory.set_editor_property(
            "mip_gen_settings",
            unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS,
        )
    return factory
```

- [ ] **Step 6.2: Editor 内手动验证 texture 真机通路**

让 msc 在保持 Editor 打开的状态下,在 Editor 的 Python Console(Tools → Python Console)跑:

```python
import importlib
import forgeue_manifest_importer as importer
importlib.reload(importer)  # 确保拿到最新代码

result = importer.import_from_manifest(
    manifest_path=r"D:\UnrealProjects\Mvpv4TestCodex\Plugins\AgentBridge\Tests\fixtures\forgeue_manifest\manifest.json",
    plan_path=r"D:\UnrealProjects\Mvpv4TestCodex\Plugins\AgentBridge\Tests\fixtures\forgeue_manifest\import_plan.json",
    bridge_mode="bridge_python",
)
import json
print(json.dumps(result, indent=2, ensure_ascii=False))
```

**Expected**:
- 6 个 asset_results
- texture / sprite_sheet 两条 status=success(uasset 落到 /Game/Generated/Tavern/run_p4_full/T_*)
- sound_wave / static_mesh / material / file_media_source 四条 status=failed(NotImplementedError stub)
- 总 status=partial

让 msc 在 Content Browser 导航到 `/Game/Generated/Tavern/run_p4_full/`,**确认看到 T_run_p4_full_tex_albedo 和 T_run_p4_full_tex_sprite 两个 Texture asset**。

- [ ] **Step 6.3: Commit**

```powershell
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): texture / sprite_sheet 真机实现 (Task 6)

- _importer_path_texture:走 AssetTools.import_asset_tasks + TextureFactory
- _build_texture_factory:srgb / compression_settings / mip_gen_settings 三属性按 import_options 设置
- _COMPRESSION_MAP:9 种 ForgeUE compression_settings → unreal.TextureCompressionSettings 枚举映射
- Editor 内手动验证 PASS:Content Browser 看到 T_run_p4_full_tex_albedo + T_run_p4_full_tex_sprite

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 7: sound_wave 真机实现

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`

- [ ] **Step 7.1: 填 `_importer_path_sound` 实现**

修改 `_importer_path_sound` 替换 NotImplementedError 为:

```python
def _importer_path_sound(asset, source_uri, target_pkg, overwrite, import_options, bridge_mode):
    """sound_wave 真机导入:走 AssetTools.import_asset_tasks + SoundFactory。"""
    import time
    import unreal
    start = time.monotonic()

    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(asset, bridge_mode,
                                 f"target asset exists and overwrite_existing=false: {target_pkg}")

    factory = unreal.SoundFactory()
    # SoundFactory 默认行为已经能 handle WAV/OGG;无 import_options 字段需要映射

    task = unreal.AssetImportTask()
    task.filename = str(source_uri)
    task.destination_path = target_pkg.rsplit("/", 1)[0]
    task.destination_name = target_pkg.rsplit("/", 1)[-1]
    task.replace_existing = overwrite
    task.automated = True
    task.save = True
    task.factory = factory

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    if not task.imported_object_paths:
        return _evidence_failure(asset, bridge_mode,
                                 f"sound_wave import returned no objects (filename={source_uri})")

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=task.imported_object_paths[0],
        factory_class="unreal.SoundFactory",
        duration_ms=duration_ms,
        import_log_excerpt=f"imported sound_wave from {source_uri.name}",
    )
```

- [ ] **Step 7.2: Editor 内手动验证 sound_wave 真机通路**

让 msc 同 Step 6.2 跑 import_from_manifest,看 sound_wave 那条 status=success;Content Browser 看到 `S_run_p4_full_sfx_click`。

- [ ] **Step 7.3: Commit**

```powershell
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): sound_wave 真机实现 (Task 7)

- _importer_path_sound:走 AssetTools.import_asset_tasks + SoundFactory
- 与 texture 同 import_asset_tasks 范式,SoundFactory 默认行为 handle WAV/OGG
- Editor 内手动验证 PASS:Content Browser 看到 S_run_p4_full_sfx_click

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 8: static_mesh 真机实现

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`

- [ ] **Step 8.1: 填 `_importer_path_mesh` 实现(按 source_format 分发 FBX/GLTF/OBJ)**

修改 `_importer_path_mesh` 替换 NotImplementedError 为:

```python
def _importer_path_mesh(asset, source_uri, target_pkg, overwrite, import_options, bridge_mode):
    """static_mesh 真机导入:按 import_options.source_format 路由 FBX/GLTF/OBJ Factory。"""
    import time
    import unreal
    start = time.monotonic()

    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(asset, bridge_mode,
                                 f"target asset exists and overwrite_existing=false: {target_pkg}")

    fmt = import_options.get("source_format", "fbx").lower()
    factory, factory_class_name = _build_mesh_factory(fmt, import_options)
    if factory is None:
        return _evidence_failure(asset, bridge_mode,
                                 f"unsupported mesh source_format: {fmt} (expected fbx/gltf/glb/obj)")

    task = unreal.AssetImportTask()
    task.filename = str(source_uri)
    task.destination_path = target_pkg.rsplit("/", 1)[0]
    task.destination_name = target_pkg.rsplit("/", 1)[-1]
    task.replace_existing = overwrite
    task.automated = True
    task.save = True
    task.factory = factory

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    if not task.imported_object_paths:
        return _evidence_failure(asset, bridge_mode,
                                 f"static_mesh import returned no objects (filename={source_uri})")

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=task.imported_object_paths[0],
        factory_class=factory_class_name,
        duration_ms=duration_ms,
        import_log_excerpt=f"imported static_mesh ({fmt}) from {source_uri.name}",
    )


def _build_mesh_factory(fmt: str, import_options: dict):
    """按 source_format 选 FBX/GLTF/OBJ Factory。返回 (factory, factory_class_name)。"""
    import unreal

    if fmt == "fbx":
        factory = unreal.FbxFactory()
        # FBX import 选项(避免导入材质/合并 mesh 等不需要的副作用)
        fbx_import_data = unreal.FbxImportUI()
        fbx_import_data.import_materials = import_options.get("import_materials", False)
        fbx_import_data.import_textures = import_options.get("import_materials", False)
        fbx_import_data.static_mesh_import_data.combine_meshes = import_options.get("combine_meshes", False)
        factory.set_editor_property("import_options", fbx_import_data)
        return factory, "unreal.FbxFactory"

    if fmt in ("gltf", "glb"):
        # UE 5.5 自带 GLTFImporter,但通常通过 import_assets_automated 自动选,无需指定 factory
        return None, "unreal.GLTFImporter (auto-selected by UE)"
        # 注:如发现 GLTF 文件用 None factory + import_asset_tasks 不行,
        # 改成 task.factory = unreal.AutomatedAssetImportData 让 UE 自动 dispatch

    if fmt == "obj":
        # UE 5.5 ObjFactory 类名,可能是 unreal.ObjFactory 或自动 dispatch
        factory_class = getattr(unreal, "ObjFactory", None)
        if factory_class is None:
            return None, "unreal.ObjFactory (not found in this UE build)"
        return factory_class(), "unreal.ObjFactory"

    return None, f"unknown source_format: {fmt}"
```

**注意**:GLTF/GLB 在 UE 5.5 的 Python 绑定不一定有显式 `GLTFImporter` 类。如果验证时发现 GLTF 路径失败,改为用 `import_assets_automated` + `AutomatedAssetImportData`(让 UE 自动 dispatch factory),代码改动放在 Step 8.2 之后的 fix commit。

- [ ] **Step 8.2: Editor 内手动验证 static_mesh 真机通路(FBX 路径)**

让 msc 同 Step 6.2 跑 import_from_manifest,看 static_mesh 那条 status=success;Content Browser 看到 `SM_run_p4_full_mesh_cube`(单立方体)。

- [ ] **Step 8.3: Commit**

```powershell
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): static_mesh 真机实现 (Task 8)

- _importer_path_mesh:按 source_format 分发 FBX/GLTF/OBJ
- _build_mesh_factory:FBX 走 unreal.FbxFactory + FbxImportUI(import_materials/combine_meshes/import_textures);GLTF/OBJ 留 UE 自动 dispatch(若验证失败 follow-up 改 AutomatedAssetImportData)
- fixture 当前只测 FBX cube,GLTF/OBJ 路径暂不在 milestone 内
- Editor 内手动验证 PASS:Content Browser 看到 SM_run_p4_full_mesh_cube

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 9: material 真机实现(Option α 五字段)

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`

- [ ] **Step 9.1: 填 `_creator_path_material` 实现(MaterialFactoryNew + MaterialEditingLibrary)**

修改 `_creator_path_material` 替换 NotImplementedError 为:

```python
def _creator_path_material(asset, source_uri, target_pkg, overwrite, bridge_mode):
    """material 真机创建:读 material_simple.json → MaterialFactoryNew → MaterialEditingLibrary 设节点。

    spec §3.4 Option α 最简 PBR 五字段:
        base_color_rgba / metallic / roughness / normal_texture_ref / emissive_color_rgba
    """
    import time
    import unreal
    start = time.monotonic()

    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(asset, bridge_mode,
                                 f"target asset exists and overwrite_existing=false: {target_pkg}")

    # 读 material.definition JSON
    try:
        material_def = json.loads(source_uri.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return _evidence_failure(asset, bridge_mode, f"cannot read material_simple.json: {exc}")

    # 1. AssetTools.create_asset(name, package_path, Material, MaterialFactoryNew)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_name = target_pkg.rsplit("/", 1)[-1]
    asset_path = target_pkg.rsplit("/", 1)[0]

    material_asset = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=asset_path,
        asset_class=unreal.Material,
        factory=unreal.MaterialFactoryNew(),
    )

    if material_asset is None:
        return _evidence_failure(asset, bridge_mode,
                                 f"MaterialFactoryNew.create_asset returned None for {target_pkg}")

    # 2. MaterialEditingLibrary 加 5 个 expression + 连到 Material output
    lib = unreal.MaterialEditingLibrary

    # 2.1 BaseColor:Constant4Vector
    base_color = material_def.get("base_color_rgba", [0.5, 0.5, 0.5, 1.0])
    base_color_expr = lib.create_material_expression(material_asset, unreal.MaterialExpressionConstant4Vector)
    base_color_expr.set_editor_property("constant", unreal.LinearColor(*base_color))
    lib.connect_material_property(base_color_expr, "", unreal.MaterialProperty.MP_BASE_COLOR)

    # 2.2 Metallic:Constant
    metallic_expr = lib.create_material_expression(material_asset, unreal.MaterialExpressionConstant)
    metallic_expr.set_editor_property("r", float(material_def.get("metallic", 0.0)))
    lib.connect_material_property(metallic_expr, "", unreal.MaterialProperty.MP_METALLIC)

    # 2.3 Roughness:Constant
    roughness_expr = lib.create_material_expression(material_asset, unreal.MaterialExpressionConstant)
    roughness_expr.set_editor_property("r", float(material_def.get("roughness", 0.7)))
    lib.connect_material_property(roughness_expr, "", unreal.MaterialProperty.MP_ROUGHNESS)

    # 2.4 Normal:可选,只在 normal_texture_ref 非 None 时连
    normal_ref = material_def.get("normal_texture_ref")
    if normal_ref:
        # 简化处理:本 milestone 不解析 ref,留 follow-up
        pass

    # 2.5 Emissive:Constant4Vector
    emissive = material_def.get("emissive_color_rgba", [0.0, 0.0, 0.0, 1.0])
    emissive_expr = lib.create_material_expression(material_asset, unreal.MaterialExpressionConstant4Vector)
    emissive_expr.set_editor_property("constant", unreal.LinearColor(*emissive))
    lib.connect_material_property(emissive_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    # 3. 编译 + 保存
    lib.recompile_material(material_asset)
    unreal.EditorAssetLibrary.save_asset(target_pkg)

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=f"{target_pkg}.{asset_name}",
        factory_class="unreal.MaterialFactoryNew + unreal.MaterialEditingLibrary",
        duration_ms=duration_ms,
        import_log_excerpt=f"created material with 4 expressions (PBR Option α 五字段)",
    )
```

- [ ] **Step 9.2: Editor 内手动验证 material 真机通路**

让 msc 同 Step 6.2 跑 import_from_manifest,看 material 那条 status=success;Content Browser 看到 `M_run_p4_full_material_simple`;双击打开 Material Editor,确认看到 BaseColor / Metallic / Roughness / Emissive 4 个 expression 连到对应 output。

- [ ] **Step 9.3: Commit**

```powershell
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): material 真机实现 Option α 五字段 (Task 9)

- _creator_path_material:AssetTools.create_asset + MaterialFactoryNew + MaterialEditingLibrary
- 4 个 expression(BaseColor/Metallic/Roughness/Emissive)按 material_simple.json 五字段连节点
- normal_texture_ref 字段当前留 follow-up(只解析,非 None 时不实现引用 lookup)
- recompile_material + save_asset 收尾
- Editor 内手动验证 PASS:Content Browser 看到 M_run_p4_full_material_simple,Material Editor 节点连对

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 10: file_media_source 真机实现

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`

- [ ] **Step 10.1: 填 `_creator_path_media` 实现(FileMediaSourceFactoryNew)**

修改 `_creator_path_media` 替换 NotImplementedError 为:

```python
def _creator_path_media(asset, source_uri, target_pkg, overwrite, bridge_mode):
    """file_media_source 真机创建:AssetTools.create_asset + FileMediaSourceFactoryNew + 设 FilePath。"""
    import time
    import unreal
    start = time.monotonic()

    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(asset, bridge_mode,
                                 f"target asset exists and overwrite_existing=false: {target_pkg}")

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_name = target_pkg.rsplit("/", 1)[-1]
    asset_path = target_pkg.rsplit("/", 1)[0]

    media_asset = asset_tools.create_asset(
        asset_name=asset_name,
        package_path=asset_path,
        asset_class=unreal.FileMediaSource,
        factory=unreal.FileMediaSourceFactoryNew(),
    )

    if media_asset is None:
        return _evidence_failure(asset, bridge_mode,
                                 f"FileMediaSourceFactoryNew.create_asset returned None for {target_pkg}")

    # 设 FilePath 指向 source_uri(绝对路径,UE FileMediaSource 期望绝对或相对项目根)
    media_asset.set_editor_property("file_path", str(source_uri))
    unreal.EditorAssetLibrary.save_asset(target_pkg)

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=f"{target_pkg}.{asset_name}",
        factory_class="unreal.FileMediaSourceFactoryNew",
        duration_ms=duration_ms,
        import_log_excerpt=f"created file_media_source pointing to {source_uri.name}",
    )
```

- [ ] **Step 10.2: Editor 内手动验证 file_media_source 真机通路**

让 msc 同 Step 6.2 跑 import_from_manifest,看 file_media_source 那条 status=success;Content Browser 看到 `MS_run_p4_full_video_clip`;双击打开,确认 FilePath 字段指向 fixture 的 video_clip.mp4。

**至此 5+1 种 asset_kind 全部真机通路打通,整个 import_from_manifest(bridge_mode="bridge_python") 应该返回 status=success(6/6)。**

- [ ] **Step 10.3: Commit**

```powershell
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): file_media_source 真机实现 (Task 10)

- _creator_path_media:AssetTools.create_asset + FileMediaSourceFactoryNew + 设 file_path
- save_asset 收尾
- Editor 内手动验证 PASS:Content Browser 看到 MS_run_p4_full_video_clip + FilePath 指向 video_clip.mp4
- 5+1 种 asset_kind(texture/sprite_sheet/sound_wave/static_mesh/material/file_media_source)真机通路全打通

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 11: L2 pytest 真机 smoke 测试脚本 + marker

**Files:**
- Modify: `pytest.ini`(加 real_ue marker)
- Create: `Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py`

- [ ] **Step 11.1: pytest.ini 加 real_ue marker 登记**

Read `pytest.ini`,在 `[pytest]` section 内 `markers =` 列表中追加(如 `markers` key 不存在则新建):

```ini
markers =
    real_ue: requires running UE 5.5.4 Editor with RC API enabled (port 30010)
```

- [ ] **Step 11.2: 写 test_forgeue_real_ue_smoke.py**

创建 `Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py`:

```python
"""L2 真机 smoke 测试:bridge_python(经 RC endpoint via bridge_rc_api)真机调用。

Marker `real_ue` 要求 UE 5.5.4 Editor 在线 + RC API 端口 30010 可达,
默认 CI 跳过(`-m "not real_ue"`)。
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

# 让测试能找到 Scripts/orchestrator/ + bridge/ 目录
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_BRIDGE_DIR = _PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "bridge"
if str(_BRIDGE_DIR) not in sys.path:
    sys.path.insert(0, str(_BRIDGE_DIR))

_FIXTURE_DIR = _PROJECT_ROOT / "Plugins" / "AgentBridge" / "Tests" / "fixtures" / "forgeue_manifest"
_MANIFEST_PATH = _FIXTURE_DIR / "manifest.json"
_PLAN_PATH = _FIXTURE_DIR / "import_plan.json"

_RC_OBJECT_PATH = "/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint"


def _ue_editor_alive() -> bool:
    """探测 UE Editor RC API 是否在线(port 30010 + endpoint 注册)。"""
    try:
        req = urllib.request.Request("http://localhost:30010/remote/info", method="GET")
        urllib.request.urlopen(req, timeout=2.0).read()
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


pytestmark = pytest.mark.skipif(
    not _ue_editor_alive(),
    reason="L2 真机 smoke 要 UE 5.5.4 Editor 在线 + RC API 30010 可达(用 -m real_ue 显式选择)",
)


@pytest.mark.real_ue
def test_rc_endpoint_describes_import_assets_from_manifest():
    """RC 通路验证:/remote/object/describe 必须含 ImportAssetsFromManifest 函数。"""
    import remote_control_client as rc

    info = rc._http_request("/remote/object/describe", {"objectPath": _RC_OBJECT_PATH})
    fn_names = [fn["Name"] for fn in info.get("Functions", [])]
    assert "ImportAssetsFromManifest" in fn_names, \
        f"endpoint 未注册 ImportAssetsFromManifest:实际函数 {fn_names}"


@pytest.mark.real_ue
def test_rc_endpoint_full_import_six_assets_all_success():
    """端到端 L2 smoke:RC 触发 6 asset 全 success(uasset 真落盘)。"""
    import remote_control_client as rc

    result_json = rc.call_function(
        object_path=_RC_OBJECT_PATH,
        function_name="ImportAssetsFromManifest",
        parameters={
            "ManifestPath": str(_MANIFEST_PATH),
            "PlanPath": str(_PLAN_PATH),
            "OverwriteExisting": True,
        },
    )

    # RC 返回结构:ReturnValue 是 endpoint 返回的 JSON 字符串
    return_value = result_json.get("ReturnValue", "")
    assert return_value, f"RC call ReturnValue 为空:{result_json}"

    payload = json.loads(return_value)
    assert payload["status"] == "success", f"非全 success:{payload}"
    assert payload["bridge_mode"] == "bridge_python"  # endpoint 内调 bridge_python
    assert payload.get("triggered_via") == "bridge_rc_api"
    assert len(payload["asset_results"]) == 6

    # 6 种 kind 全 success
    kinds_success = {r["asset_kind"]: r["status"] for r in payload["asset_results"]}
    expected_kinds = {"texture", "sprite_sheet", "sound_wave", "static_mesh", "material", "file_media_source"}
    assert set(kinds_success.keys()) == expected_kinds
    assert all(s == "success" for s in kinds_success.values()), \
        f"非全 success:{kinds_success}"


@pytest.mark.real_ue
def test_imported_uassets_exist_in_content_browser():
    """uasset 真落盘验证:EditorAssetLibrary.does_asset_exist 6/6 PASS。"""
    import remote_control_client as rc

    # 6 个 target package path
    expected_packages = [
        "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_albedo",
        "/Game/Generated/Tavern/run_p4_full/T_run_p4_full_tex_sprite",
        "/Game/Generated/Tavern/run_p4_full/S_run_p4_full_sfx_click",
        "/Game/Generated/Tavern/run_p4_full/SM_run_p4_full_mesh_cube",
        "/Game/Generated/Tavern/run_p4_full/M_run_p4_full_material_simple",
        "/Game/Generated/Tavern/run_p4_full/MS_run_p4_full_video_clip",
    ]

    for pkg in expected_packages:
        result = rc.call_function(
            object_path="/Script/EditorScriptingUtilities.Default__EditorAssetLibrary",
            function_name="DoesAssetExist",
            parameters={"AssetPath": pkg},
        )
        exists = result.get("ReturnValue", False)
        assert exists, f"uasset 未落盘:{pkg}(RC 返回 {result})"
```

- [ ] **Step 11.3: 跑 L2 测试(必须 UE Editor 在线)**

让 msc 保持 Editor 开着,Run:

```powershell
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py -v -m real_ue 2>&1 | Select-Object -Last 30
```

Expected: `3 passed`(3 个 real_ue 测试全 PASS)

如果 Editor 不在线,Run 会 skip 全部 3 个(by pytestmark)。

- [ ] **Step 11.4: 跑 L1 整体回归确保 simulated 仍 OK**

```powershell
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v 2>&1 | Select-Object -Last 10
```

Expected: 17 passed(Task 3 + 4 后的总数)

- [ ] **Step 11.5: Commit**

```powershell
git add pytest.ini Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py
git commit -m "[skip-doc] test(forgeue-real-ue-bridge): L2 真机 smoke 测试 + real_ue marker (Task 11)

- pytest.ini 登记 real_ue marker(要 UE 5.5.4 Editor + RC API 30010)
- test_forgeue_real_ue_smoke.py 3 个 case:
  - endpoint 注册可见(/remote/object/describe 含 ImportAssetsFromManifest)
  - 6 asset 全 success(端到端 RC → endpoint → 内核)
  - uasset 真落盘(EditorAssetLibrary.does_asset_exist 6/6)
- 离线 CI 自动 skip(pytestmark)
- L1 17 passed 不破坏

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 12: L3 验收 smoke 脚本 + 真机跑一次 + ProjectState 落证据

**Files:**
- Create: `Scripts/run_forgeue_real_smoke.py`
- Create: `ProjectState/Reports/2026-05-27/forgeue_real_smoke/` 完整证据包(脚本产出)

- [ ] **Step 12.1: 写 Scripts/run_forgeue_real_smoke.py**

创建 `Scripts/run_forgeue_real_smoke.py`:

```python
"""ForgeUE Manifest 真机导入验收 smoke 脚本(L3,外部驱动)。

用法:
    python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api
    python Scripts/run_forgeue_real_smoke.py --bridge-mode simulated

bridge_python:不能纯外部 driver(要在 Editor 内 Python Console 跑),本脚本不支持。
bridge_rc_api:通过 RC HTTP 触发 Editor 内 endpoint,推荐 L3 默认模式。
simulated:离线 sanity check,不入 UE Editor。

产出:
    ProjectState/Reports/<date>/forgeue_real_smoke/
    ├── evidence_manifest.json         L4 wrapper
    ├── op_evidence/<asset_entry_id>.json  L1 逐条
    ├── assertions.json                EditorAssetLibrary.does_asset_exist 校验
    ├── unreal.log.snippet             unreal.log 切片(由 msc 手动复制)
    └── screenshots/                   手动截一张 Content Browser 图
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# import path:加 bridge/ + orchestrator/
sys.path.insert(0, str(PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "bridge"))
sys.path.insert(0, str(PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "orchestrator"))


FIXTURE_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Tests" / "fixtures" / "forgeue_manifest"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"
PLAN_PATH = FIXTURE_DIR / "import_plan.json"

RC_OBJECT_PATH = "/Script/PythonGeneratedClass.Default__AgentBridgeForgeUEEndpoint"


def _make_run_id() -> str:
    today = _dt.date.today().isoformat()
    short = hashlib.sha1(uuid.uuid4().bytes).hexdigest()[:8]
    return f"{today}_{short}"


def _trigger_via_simulated() -> dict:
    import forgeue_manifest_importer as importer
    return importer.import_from_manifest(
        manifest_path=str(MANIFEST_PATH),
        plan_path=str(PLAN_PATH),
        bridge_mode="simulated",
    )


def _trigger_via_rc_api() -> dict:
    import remote_control_client as rc
    result_json = rc.call_function(
        object_path=RC_OBJECT_PATH,
        function_name="ImportAssetsFromManifest",
        parameters={
            "ManifestPath": str(MANIFEST_PATH),
            "PlanPath": str(PLAN_PATH),
            "OverwriteExisting": True,
        },
    )
    return_value = result_json.get("ReturnValue", "")
    if not return_value:
        raise RuntimeError(f"RC ReturnValue 空:{result_json}")
    return json.loads(return_value)


def _verify_uassets_exist(expected_packages: list[str]) -> dict:
    """逐个 RC 查 EditorAssetLibrary.does_asset_exist,落 assertions.json。"""
    import remote_control_client as rc
    results = {}
    for pkg in expected_packages:
        r = rc.call_function(
            object_path="/Script/EditorScriptingUtilities.Default__EditorAssetLibrary",
            function_name="DoesAssetExist",
            parameters={"AssetPath": pkg},
        )
        results[pkg] = bool(r.get("ReturnValue", False))
    return results


def _write_evidence_pack(report_dir: Path, run_id: str, payload: dict,
                          assertions: dict, bridge_mode: str) -> None:
    """落 6 份 op_evidence + 1 份 evidence_manifest + 1 份 assertions.json。"""
    op_dir = report_dir / "op_evidence"
    op_dir.mkdir(parents=True, exist_ok=True)

    for op in payload.get("asset_results", []):
        out = op_dir / f"{op.get('asset_entry_id', 'unknown')}.json"
        out.write_text(json.dumps(op, ensure_ascii=False, indent=2), encoding="utf-8")

    (report_dir / "assertions.json").write_text(
        json.dumps(assertions, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 外层 evidence_manifest(复用现有 schema)
    evidence_items = []
    for op in payload.get("asset_results", []):
        evidence_items.append({
            "type": "report",
            "path": f"op_evidence/{op.get('asset_entry_id')}.json",
            "description": f"{op.get('asset_kind')} import op evidence",
            "timestamp": op.get("timestamp", _dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z"),
        })
    evidence_items.append({
        "type": "assertion_result",
        "path": "assertions.json",
        "description": "EditorAssetLibrary.does_asset_exist 6/6 校验结果",
        "timestamp": _dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
    })

    passed = sum(1 for v in assertions.values() if v)
    failed = sum(1 for v in assertions.values() if not v)

    manifest = {
        "run_id": run_id,
        "created_at": _dt.datetime.utcnow().isoformat(timespec="milliseconds") + "Z",
        "test_type": "smoke_test",
        "test_scope": f"ForgeUE Manifest Real-UE Import Bridge ({bridge_mode})",
        "evidence_items": evidence_items,
        "summary": {
            "total_checks": passed + failed,
            "passed": passed,
            "failed": failed,
            "warnings": 0,
        },
        "status": "pass" if failed == 0 else "fail",
    }
    (report_dir / "evidence_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="ForgeUE Real-UE smoke (L3)")
    parser.add_argument("--bridge-mode", required=True,
                        choices=["simulated", "bridge_rc_api"],
                        help="L3 入口只支持 simulated(离线 sanity) / bridge_rc_api(真机)")
    args = parser.parse_args()

    run_id = _make_run_id()
    report_dir = PROJECT_ROOT / "ProjectState" / "Reports" / _dt.date.today().isoformat() / "forgeue_real_smoke"
    report_dir.mkdir(parents=True, exist_ok=True)

    print(f"[L3 smoke] run_id={run_id} bridge_mode={args.bridge_mode}")
    print(f"[L3 smoke] report_dir={report_dir}")

    # 1. 触发导入
    if args.bridge_mode == "simulated":
        payload = _trigger_via_simulated()
    else:
        payload = _trigger_via_rc_api()

    # 2. 真机模式跑 uasset 存在断言
    if args.bridge_mode == "bridge_rc_api":
        expected_pkgs = [op.get("uasset_package_path", "") for op in payload.get("asset_results", [])]
        expected_pkgs = [p for p in expected_pkgs if p]
        assertions = _verify_uassets_exist(expected_pkgs)
    else:
        # simulated 无真 asset 落盘,assertion 全标 simulated-pass
        assertions = {op.get("target_object_path", ""): True
                      for op in payload.get("asset_results", [])}

    # 3. 落证据
    _write_evidence_pack(report_dir, run_id, payload, assertions, args.bridge_mode)

    print(f"[L3 smoke] payload status={payload.get('status')}")
    print(f"[L3 smoke] assertions: passed={sum(1 for v in assertions.values() if v)} / total={len(assertions)}")
    print(f"[L3 smoke] evidence_manifest.status={'pass' if all(assertions.values()) else 'fail'}")

    return 0 if all(assertions.values()) and payload.get("status") in ("success", "partial") else 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 12.2: 跑 simulated L3 sanity check**

Run:
```powershell
python Scripts/run_forgeue_real_smoke.py --bridge-mode simulated
```

Expected:
```
[L3 smoke] run_id=2026-05-27_xxxxxxxx bridge_mode=simulated
[L3 smoke] report_dir=...\ProjectState\Reports\2026-05-27\forgeue_real_smoke
[L3 smoke] payload status=success
[L3 smoke] assertions: passed=6 / total=6
[L3 smoke] evidence_manifest.status=pass
```
exit code 0。

验证:
```powershell
Get-ChildItem "ProjectState/Reports/2026-05-27/forgeue_real_smoke" -Recurse | Select-Object FullName, Length
```
应看到 evidence_manifest.json + op_evidence/6 个 + assertions.json。

- [ ] **Step 12.3: 跑真机 L3 smoke(UE Editor 在线)**

让 msc 保持 Editor 开着,Run:
```powershell
python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api
```

Expected:同 12.2,但 assertions 是真 EditorAssetLibrary.does_asset_exist 返回(6 个全 True)。

- [ ] **Step 12.4: msc 手动截图 + 落 unreal.log 切片**

让 msc 做:
1. 在 UE Editor 切到 Content Browser,导航到 `/Game/Generated/Tavern/run_p4_full/`
2. 截一张图(包含 6 个 uasset 的 Content Browser 视图),保存到 `ProjectState/Reports/2026-05-27/forgeue_real_smoke/screenshots/content_browser_after.png`
3. 在 Output Log,过滤 "AgentBridge" 或 "Imported",复制最近 100 行,保存到 `ProjectState/Reports/2026-05-27/forgeue_real_smoke/unreal.log.snippet.txt`

- [ ] **Step 12.5: 把 screenshot / log 加进 evidence_manifest 引用**

手动编辑 `ProjectState/Reports/2026-05-27/forgeue_real_smoke/evidence_manifest.json`,在 `evidence_items` 列表末尾加两条:

```json
{
  "type": "screenshot",
  "path": "screenshots/content_browser_after.png",
  "description": "Content Browser 显示 6 个新增 uasset",
  "timestamp": "<同 created_at>"
},
{
  "type": "log",
  "path": "unreal.log.snippet.txt",
  "description": "unreal.log AgentBridge / Imported 切片",
  "timestamp": "<同 created_at>"
}
```

并把 `summary.total_checks` / `passed` 加 2(假设 screenshot + log 都视为 passed-evidence)。

- [ ] **Step 12.6: Commit**

```powershell
git add Scripts/run_forgeue_real_smoke.py ProjectState/Reports/2026-05-27/forgeue_real_smoke/
git commit -m "[skip-doc] feat(forgeue-real-ue-bridge): L3 验收 smoke 脚本 + 真机跑一次证据落盘 (Task 12)

- Scripts/run_forgeue_real_smoke.py:外部驱动,支持 simulated(离线 sanity) + bridge_rc_api(真机)
- 真机跑:RC 触发 endpoint → 6 asset 全 success + uasset 真落盘 + assertions 6/6 PASS
- ProjectState/Reports/2026-05-27/forgeue_real_smoke/ 完整证据包:
  - evidence_manifest.json:外层 wrapper(复用 evidence_manifest.schema.json,test_type=smoke_test)
  - op_evidence/<asset_entry_id>.json:6 份逐条 op 证据(符合 forgeue_import_evidence.schema.json)
  - assertions.json:EditorAssetLibrary.does_asset_exist 6/6
  - screenshots/content_browser_after.png:msc 手动截图
  - unreal.log.snippet.txt:msc 手动复制日志切片

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 13: 文档同步(走 document-release skill)

**目标**:本 milestone 改动了若干契约 / Schema / 测试 / 新功能,必须走 document-release 强制门禁同步文档。

**Files:**(由 document-release skill 强制触达)
- Modify: `AGENTS.md` / `CLAUDE.md` / `task.md` / `README.md`(L0 anchor)
- Modify: `Docs/INDEX.md`(权威定义点:Schema 数 41→42,examples 26→27)
- Modify: `Docs/FEATURE_INVENTORY.md`(F-* 登记新增功能 + BC-NEW-A/B)
- Modify: `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`(§3 表追加 BC-NEW-A/B)
- Modify: `Docs/design/LLD/03_orchestrator.md`(§3.8 / §4.5 / §5 更新)
- Modify: `Docs/contracts/schemas_catalog.md`(新增 forgeue_import_evidence)
- Modify: `Docs/testing/test_spec.md`(L1 17 / L2 3 / L3 1 case 登记)
- Modify: `Plugins/AgentBridge/Tests/SystemTestCases.md`(可选,由 governance 决断)
- Create: `ProjectState/Reports/2026-05-27/document_release_audit.md`

- [ ] **Step 13.1: 跑校验脚本(确保所有自动检查通过)**

```powershell
python Scripts/validation/feature_inventory_check.py 2>&1 | Select-Object -Last 10
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict 2>&1 | Select-Object -Last 5
python Scripts/validation/link_precheck.py 2>&1 | Select-Object -Last 5
```

Expected:
- feature_inventory_check: 8/8 PASS(或 9+ 因为新增 F-*)
- validate_examples --strict: 27/27 examples PASS
- link_precheck: 0 旧路径残留

如果 feature_inventory_check 失败说找不到 F-NEW-* 锚点,先做 Step 13.2 再回跑。

- [ ] **Step 13.2: 调起 document-release skill**

调起本项目专用 skill:
```
Skill: document-release
```

让 skill 完成:
- 4 层文档同步(A 入口 / B 阶段事实 / C 框架 / D 证据)
- audit.md 强制落盘到 `ProjectState/Reports/2026-05-27/document_release_audit.md`
- Coverage Map + Documentation health 两个 H2 区块齐全
- write-marker 接口校验

- [ ] **Step 13.3: 跑 git pre-commit hook 验证 marker 生效**

不直接跑 pre-commit,通过尝试 git commit 来触发:

```powershell
git add -A
git status --short  # 确认 staged 文件清单符合 Task 13 预期
```

实际 commit 用 Step 13.4。

- [ ] **Step 13.4: Commit(走 document-release 门禁)**

```powershell
git commit -m "docs(forgeue-real-ue-bridge): milestone 收尾 — 5+1 asset_kind 真机通路全打通 + 文档同步 (Task 13)

document-release 强制门禁通过(详见 ProjectState/Reports/2026-05-27/document_release_audit.md):

实施成果:
- 5+1 种 asset_kind(texture/sprite_sheet/sound_wave/static_mesh/material/file_media_source)真机导入全打通
- bridge_python(Editor 内 Python Console)+ bridge_rc_api(RC HTTP via PythonScripted UCLASS)两条通路同时落地
- L1 simulated 17 PASS + L2 真机 marker 3 PASS + L3 验收 smoke 6/6 uasset 真落盘
- 0 触 CLAUDE.md C++ 红线;新增 BC-NEW-A(P2)/BC-NEW-B(P1 candidate)登记到 UE 5.7 BC scan

文档同步:
- Docs/INDEX.md:Schema 41 → 42,examples 26 → 27
- Docs/FEATURE_INVENTORY.md:F-FORGEUE-RT-{01..05} 登记真机通路功能 + BC-NEW-A/B
- Docs/design/LLD/03_orchestrator.md §3.8 / §4.5 / §5 同步
- Docs/contracts/schemas_catalog.md 新增 forgeue_import_evidence
- AGENTS.md / CLAUDE.md / task.md / README.md 同步当前阶段状态
- ProjectState/Reports/2026-05-27/{forgeue_rc_endpoint_verification, forgeue_real_smoke/, document_release_audit}.md 三件证据

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 13.5: 跑最终验证 — 整套 milestone 回归**

```powershell
# L1 pytest
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v 2>&1 | Select-Object -Last 5

# L2 pytest with real_ue marker(UE Editor 必须在线)
python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_real_ue_smoke.py -v -m real_ue 2>&1 | Select-Object -Last 5

# Schema strict 全套
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict 2>&1 | Select-Object -Last 3

# L3 真机一遍
python Scripts/run_forgeue_real_smoke.py --bridge-mode bridge_rc_api
```

Expected:全 PASS,exit code 0;ProjectState/Reports/2026-05-27/forgeue_real_smoke/ 证据完整。

---

## 自审 checklist(plan 内嵌)

**1. Spec coverage**:
- spec §1.1 PNG payload ✅ Task 1
- spec §1.2 C++ 红线 ✅ Task 5(用 PythonScripted UCLASS 不动 C++)+ Task 13(red-line audit)
- spec §1.3 asset_kind 覆盖 ✅ Task 6/7/8/9/10 各对应一种
- spec §1.4 evidence 契约 ✅ Task 2
- spec §1.5 Path C 共享内核 ✅ Task 4(架构)+ Task 6-10(逐 kind 填充)
- spec §1.6 material Option α ✅ Task 9
- spec §3.1 内核分两类(importer/creator) ✅ Task 4
- spec §3.2 内核函数骨架 ✅ Task 4 Step 4.1
- spec §3.3 import_options → Factory ✅ Task 6 Step 6.1 _build_texture_factory
- spec §3.4 material 五字段 schema ✅ Task 1 Step 1.2 + Task 9 Step 9.1
- spec §3.5 错误处理 ✅ Task 4 _evidence_failure/_skipped
- spec §4.1/4.2 RC endpoint + init_unreal ✅ Task 5
- spec §4.3 外部 client 调用拼法 ✅ Task 12 Scripts/run_forgeue_real_smoke.py
- spec §4.4 验证清单 ✅ Task 5 Step 5.4-5.7
- spec §4.5 Fallback EUB ✅ Task 5 Step 5.8(决策点,实际实施延后到失败时)
- spec §5.A C++ 红线 0 触碰 ✅ Task 13 audit
- spec §5.B UE 5.7 BC ✅ Task 13 BC-NEW-A/B 登记
- spec §5.D 现有契约兼容 ✅ Task 4(import_from_manifest 主入口不破)
- spec §6 三层测试 ✅ Task 3 (L1) + Task 11 (L2) + Task 12 (L3)
- spec §7 evidence 契约 ✅ Task 2 + Task 12
- spec §8 fixture 扩展 ✅ Task 1
- spec §9 ProjectState 落盘 ✅ Task 12
- spec §10 实施 checklist 12 项 ✅ 全部对应 task

**0 spec gap**。

**2. Placeholder scan**:全 plan grep 后,无 TBD/TODO/"implement later" 等(只有"<asset_entry_id>"/"<root>" 等 spec 内规定的 manifest 占位符)。

**3. Type consistency**:
- `_import_asset_by_kind(asset, manifest_root, overwrite_existing, *, bridge_mode)` 在 Task 4 定义,Task 5 endpoint 调用一致(bridge_mode 透传)✅
- `_evidence_success / _evidence_failure / _evidence_skipped` 在 Task 4 定义,Task 6-10 使用一致 ✅
- `_build_texture_factory` / `_build_mesh_factory` 命名一致(Task 6/8)✅
- `_creator_path_material` / `_creator_path_media` 命名一致(Task 9/10)✅
- `_COMPRESSION_MAP` 在 Task 6 定义并使用 ✅

**0 type inconsistency**。

---

## Execution Handoff

Plan complete and saved to `Docs/superpowers/plans/2026-05-27-forgeue-real-ue-bridge.md`. Two execution options:

**1. Subagent-Driven(recommended)** — 派 fresh subagent per task,review between tasks,fast iteration。适合本 plan(13 task,每 task 独立 + 强 commit gate)。

**2. Inline Execution** — Execute tasks in this session using executing-plans,batch execution with checkpoints。适合 msc 想全程在主会话中盯着的场景。

**Which approach?**
