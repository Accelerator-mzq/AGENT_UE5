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
    # 守门:必须在 UE Editor Python 环境(import unreal 可用),否则早期 raise
    try:
        import unreal  # 失败 → 不在 Editor Python 环境
    except ImportError as exc:
        raise RuntimeError(
            "_import_asset_by_kind 必须在 UE Editor Python 环境运行(import unreal 失败);"
            "外部驱动请用 simulated 模式或 bridge_rc_api 通路"
        ) from exc

    # 拼 source_uri 绝对路径(manifest 中是相对 manifest 目录的相对路径)
    kind = asset["asset_kind"]
    source_uri = (manifest_root / asset["source_uri"]).resolve()
    if not source_uri.exists():
        return _evidence_failure(asset, bridge_mode, f"payload missing: {source_uri}",
                                  source_uri_abs=source_uri)

    target_pkg = asset["target_package_path"]
    import_options = asset.get("import_options", {})

    # 按 asset_kind 6 路 dispatch:texture/sprite_sheet 共享 importer,material/media 走 creator
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

    return _evidence_failure(asset, bridge_mode, f"unsupported asset_kind: {kind}",
                              source_uri_abs=source_uri)


# ============================================================
# helper:evidence 构造
# ============================================================

def _now_iso_utc() -> str:
    """返回当前 UTC 时间 ISO 8601 含毫秒 + Z 后缀(避开 utcnow deprecation)。"""
    # Python 3.13 起 datetime.utcnow() 已 deprecated,改用 timezone-aware now(UTC)
    # 再 replace "+00:00" → "Z" 保持与 schema example 兼容的紧凑表示
    return _dt.datetime.now(_dt.UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _evidence_failure(asset: dict, bridge_mode: str, message: str,
                       *, source_uri_abs: str | Path | None = None,
                       errors: list[str] | None = None) -> dict:
    """构造 failed 状态的 evidence dict(符合 forgeue_import_evidence.schema.json)。"""
    return {
        "asset_entry_id": asset.get("asset_entry_id", ""),
        "op_id": f"op_failed_{asset.get('asset_entry_id', 'unknown')}",
        "asset_kind": asset.get("asset_kind", ""),
        "bridge_mode": bridge_mode,
        "status": "failed",
        "timestamp": _now_iso_utc(),
        # source_uri_abs 优先用 caller 提供的绝对路径;若 None 则 fallback 到 asset 中的相对路径
        # (但应避免 None 场景 — caller 应总是传入)
        "source_uri_abs": str(source_uri_abs) if source_uri_abs is not None
                          else str(asset.get("source_uri", "")),
        "errors": errors or [message],
    }


def _evidence_skipped(asset: dict, bridge_mode: str, reason: str,
                      *, source_uri_abs: str | Path | None = None) -> dict:
    """构造 skipped 状态的 evidence dict。"""
    return {
        "asset_entry_id": asset.get("asset_entry_id", ""),
        "op_id": f"op_skipped_{asset.get('asset_entry_id', 'unknown')}",
        "asset_kind": asset.get("asset_kind", ""),
        "bridge_mode": bridge_mode,
        "status": "skipped",
        "timestamp": _now_iso_utc(),
        # source_uri_abs 优先用 caller 提供的绝对路径;若 None 则 fallback 到 asset 中的相对路径
        # (但应避免 None 场景 — caller 应总是传入)
        "source_uri_abs": str(source_uri_abs) if source_uri_abs is not None
                          else str(asset.get("source_uri", "")),
        "skipped_reason": reason,
    }


def _evidence_success(asset: dict, bridge_mode: str, source_uri_abs: Path,
                      uasset_object_path: str, factory_class: str,
                      duration_ms: int, import_log_excerpt: str = "") -> dict:
    """构造 success 状态的 evidence dict(符合 forgeue_import_evidence.schema.json)。

    Args:
        asset: manifest 中的 asset entry dict
        bridge_mode: 触发的桥接通路(bridge_python / bridge_rc_api)
        source_uri_abs: payload 文件的绝对路径(已 resolve)
        uasset_object_path: UE Content Browser 中 uasset 的对象路径(/Game/...形式)
        factory_class: 实际使用的 unreal Factory 类全名(便于 debug)
        duration_ms: 单条 op 执行耗时(毫秒)
        import_log_excerpt: unreal.log 相关切片(可选)
    """
    return {
        "asset_entry_id": asset.get("asset_entry_id", ""),
        "op_id": f"op_import_{asset.get('asset_entry_id', 'unknown')}",
        "asset_kind": asset.get("asset_kind", ""),
        "bridge_mode": bridge_mode,
        "status": "success",
        "timestamp": _now_iso_utc(),
        "source_uri_abs": str(source_uri_abs),
        "uasset_object_path": uasset_object_path,
        "uasset_package_path": uasset_object_path.split(".")[0] if "." in uasset_object_path else uasset_object_path,
        "factory_class": factory_class,
        "duration_ms": duration_ms,
        "import_log_excerpt": import_log_excerpt,
        "errors": [],
    }


# ============================================================
# 5+1 种 asset_kind 实现(Task 6-10 逐一填充)
# ============================================================

# ============================================================
# texture / sprite_sheet 真机实现(Task 6)
# ============================================================

# ForgeUE compression_settings → unreal.TextureCompressionSettings 枚举值名
# 9 种映射覆盖 ForgeUE 上游可能产出的 compression_settings 字段
_COMPRESSION_MAP: dict[str, str] = {
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


def _apply_texture_properties(texture_asset: Any, import_options: dict[str, Any]) -> None:
    """import 完成后对 Texture2D 实例应用 import_options 属性。

    sRGB / compression_settings / mip_gen_settings 是 UTexture/UTexture2D 属性,
    不是 TextureFactory 属性(UE 5.5 实测验证)。
    必须 import 完成后在资产实例上设置。
    """
    import unreal

    # color_space sRGB → True;Linear → False
    texture_asset.set_editor_property(
        "srgb",
        import_options.get("color_space", "sRGB") == "sRGB",
    )

    # compression_settings:按 _COMPRESSION_MAP 翻译到 unreal 枚举
    cs_name = import_options.get("compression_settings", "default")
    cs_enum_name = _COMPRESSION_MAP.get(cs_name, "TC_DEFAULT")
    texture_asset.set_editor_property(
        "compression_settings",
        getattr(unreal.TextureCompressionSettings, cs_enum_name),
    )

    # tileable=false 时禁 mip(UI/sprite_sheet 等;避免 mip 压平细节)
    if not import_options.get("tileable", False):
        texture_asset.set_editor_property(
            "mip_gen_settings",
            unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS,
        )


def _importer_path_texture(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, import_options: dict[str, Any], bridge_mode: str,
) -> dict[str, Any]:
    """texture / sprite_sheet 真机导入:走 AssetTools.import_asset_tasks + TextureFactory,import 后再对 Texture2D 实例应用属性。"""
    import time
    import unreal
    start = time.monotonic()

    # 目标 package 已存在 + 不允许覆盖 → skipped(不阻塞其他 asset)
    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(
            asset, bridge_mode,
            f"target asset exists and overwrite_existing=false: {target_pkg}",
            source_uri_abs=source_uri,
        )

    # 构造 AssetImportTask(Factory 用默认,不在 Factory 上设属性)
    factory = unreal.TextureFactory()
    task = unreal.AssetImportTask()
    task.filename = str(source_uri)
    task.destination_path = target_pkg.rsplit("/", 1)[0]   # 目录部分:/Game/.../run_p4_full
    task.destination_name = target_pkg.rsplit("/", 1)[-1]  # 资产名:T_run_p4_full_tex_albedo
    task.replace_existing = overwrite
    task.automated = True
    task.save = True
    task.factory = factory

    # 执行导入(同步) — wrap UE API 异常,任何失败都不能让整批中断(spec §3.5)
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        asset_tools.import_asset_tasks([task])
    except Exception as exc:  # noqa: BLE001  # UE API 异常类型不可枚举,catch-all 必须
        return _evidence_failure(
            asset, bridge_mode,
            f"import_asset_tasks raised: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    # 校验:imported_object_paths 应有 1 个新对象
    if not task.imported_object_paths:
        return _evidence_failure(
            asset, bridge_mode,
            f"texture import returned no objects (filename={source_uri})",
            source_uri_abs=source_uri,
        )

    # import 完成后对 Texture2D 实例应用 import_options 属性(sRGB/压缩/mip)
    # 这些属性在 UTexture/UTexture2D 上,不在 TextureFactory 上(UE 5.5 实测)
    imported_object_path = task.imported_object_paths[0]
    try:
        texture_asset = unreal.EditorAssetLibrary.load_asset(imported_object_path)
        _apply_texture_properties(texture_asset, import_options)
        unreal.EditorAssetLibrary.save_asset(target_pkg)
    except Exception as exc:  # noqa: BLE001
        return _evidence_failure(
            asset, bridge_mode,
            f"apply_texture_properties raised: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=imported_object_path,
        factory_class="unreal.TextureFactory",
        duration_ms=duration_ms,
        import_log_excerpt=f"imported {asset['asset_kind']} from {source_uri.name} + applied {len(import_options)} options",
    )


def _importer_path_sound(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, import_options: dict[str, Any], bridge_mode: str,
) -> dict[str, Any]:
    """sound_wave 真机导入:走 AssetTools.import_asset_tasks + SoundFactory(默认设置)。

    UE 5.5 SoundFactory 默认对 WAV/OGG 行为正确,无需在 Factory 上设属性。
    本 milestone fixture 是 mono 16k 短音频,默认导入足够;后续如需 sample_rate /
    compression_quality / streaming 等需在 imported SoundWave 实例上 set_editor_property。
    """
    import time
    import unreal
    start = time.monotonic()

    # 目标 package 已存在 + 不允许覆盖 → skipped(不阻塞其他 asset)
    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(
            asset, bridge_mode,
            f"target asset exists and overwrite_existing=false: {target_pkg}",
            source_uri_abs=source_uri,
        )

    # 构造 AssetImportTask(SoundFactory 用默认,不在 Factory 上设属性)
    factory = unreal.SoundFactory()
    task = unreal.AssetImportTask()
    task.filename = str(source_uri)
    task.destination_path = target_pkg.rsplit("/", 1)[0]   # 目录部分
    task.destination_name = target_pkg.rsplit("/", 1)[-1]  # 资产名:S_*
    task.replace_existing = overwrite
    task.automated = True
    task.save = True
    task.factory = factory

    # 执行导入(同步) — wrap UE API 异常,spec §3.5
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        asset_tools.import_asset_tasks([task])
    except Exception as exc:  # noqa: BLE001  # UE API 异常类型不可枚举,catch-all 必须
        return _evidence_failure(
            asset, bridge_mode,
            f"import_asset_tasks raised: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    if not task.imported_object_paths:
        return _evidence_failure(
            asset, bridge_mode,
            f"sound_wave import returned no objects (filename={source_uri})",
            source_uri_abs=source_uri,
        )

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=task.imported_object_paths[0],
        factory_class="unreal.SoundFactory",
        duration_ms=duration_ms,
        import_log_excerpt=f"imported sound_wave from {source_uri.name}",
    )


def _importer_path_mesh(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, import_options: dict[str, Any], bridge_mode: str,
) -> dict[str, Any]:
    """static_mesh 真机导入:按 import_options.source_format 路由 FBX/GLTF/OBJ Factory。"""
    import time
    import unreal
    start = time.monotonic()

    # 目标 package 已存在 + 不允许覆盖 → skipped(不阻塞其他 asset)
    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(
            asset, bridge_mode,
            f"target asset exists and overwrite_existing=false: {target_pkg}",
            source_uri_abs=source_uri,
        )

    # 按 source_format 选 Factory
    fmt = import_options.get("source_format", "fbx").lower()
    factory, factory_class_name = _build_mesh_factory(fmt, import_options)
    if factory is None:
        return _evidence_failure(
            asset, bridge_mode,
            f"unsupported mesh source_format: {fmt} (expected fbx/gltf/glb/obj)",
            source_uri_abs=source_uri,
        )

    # 构造 AssetImportTask
    task = unreal.AssetImportTask()
    task.filename = str(source_uri)
    task.destination_path = target_pkg.rsplit("/", 1)[0]   # 目录部分
    task.destination_name = target_pkg.rsplit("/", 1)[-1]  # 资产名:SM_*
    task.replace_existing = overwrite
    task.automated = True
    task.save = True
    task.factory = factory

    # 执行导入(同步) — wrap UE API 异常,spec §3.5
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        asset_tools.import_asset_tasks([task])
    except Exception as exc:  # noqa: BLE001  # UE API 异常类型不可枚举,catch-all 必须
        return _evidence_failure(
            asset, bridge_mode,
            f"import_asset_tasks raised: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    # 校验:imported_object_paths 应有 1 个新对象
    if not task.imported_object_paths:
        return _evidence_failure(
            asset, bridge_mode,
            f"static_mesh import returned no objects (filename={source_uri}, fmt={fmt})",
            source_uri_abs=source_uri,
        )

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=task.imported_object_paths[0],
        factory_class=factory_class_name,
        duration_ms=duration_ms,
        import_log_excerpt=f"imported static_mesh ({fmt}) from {source_uri.name}",
    )


def _build_mesh_factory(fmt: str, import_options: dict[str, Any]) -> tuple[Any, str]:
    """按 source_format 选 FBX/GLTF/OBJ Factory。

    Args:
        fmt: source_format 字符串(已 lowercase)
        import_options: manifest entry 的 import_options dict

    Returns:
        (factory_instance, factory_class_name) 元组
        - fmt 不支持时 factory_instance 为 None,caller 应返 evidence_failure
        - GLTF/OBJ 路径在 UE 5.5 可能无显式 Factory 类,本 milestone 留 follow-up

    本 milestone fixture 只测 FBX(mesh_cube.fbx),GLTF/OBJ 路径未覆盖,
    后续 fixture 扩展后再实测验证。
    """
    import unreal

    if fmt == "fbx":
        factory = unreal.FbxFactory()
        # FBX import 选项 — 避免导入材质/合并 mesh 等不需要的副作用
        fbx_import_data = unreal.FbxImportUI()
        fbx_import_data.import_materials = import_options.get("import_materials", False)
        fbx_import_data.import_textures = import_options.get("import_textures", False)
        fbx_import_data.static_mesh_import_data.combine_meshes = import_options.get("combine_meshes", False)
        factory.set_editor_property("import_options", fbx_import_data)
        return factory, "unreal.FbxFactory"

    if fmt in ("gltf", "glb"):
        # UE 5.5 GLTF importer 通常通过 AssetTools.import_assets_automated 自动 dispatch,
        # 无独立 Python Factory 类。本 milestone fixture 不含 GLTF,留 follow-up。
        return None, f"unreal.GLTFImporter (auto-selected by UE; not implemented)"

    if fmt == "obj":
        # UE 5.5 ObjFactory 类名待实测;本 milestone fixture 不含 OBJ,留 follow-up
        factory_class = getattr(unreal, "ObjFactory", None)
        if factory_class is None:
            return None, "unreal.ObjFactory (not found in this UE build; not implemented)"
        return factory_class(), "unreal.ObjFactory"

    return None, f"unknown source_format: {fmt}"


def _creator_path_material(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, bridge_mode: str,
) -> dict[str, Any]:
    """material 真机创建:读 material.json → MaterialFactoryNew → MaterialEditingLibrary 设节点。

    spec §3.4 Option α 最简 PBR 五字段:
        base_color_rgba / metallic / roughness / normal_texture_ref / emissive_color_rgba

    与 texture/sound/mesh 不同,material 不是"导入文件",而是"读 JSON 配置 → 创建 Material asset
    + 加 expression 节点 + 连到 output + 编译 + 保存"。
    """
    import time
    import unreal
    start = time.monotonic()

    # 目标 package 已存在 + 不允许覆盖 → skipped(不阻塞其他 asset)
    if not overwrite and unreal.EditorAssetLibrary.does_asset_exist(target_pkg):
        return _evidence_skipped(
            asset, bridge_mode,
            f"target asset exists and overwrite_existing=false: {target_pkg}",
            source_uri_abs=source_uri,
        )

    # 读 material.definition JSON(Option α 五字段)
    try:
        material_def = json.loads(source_uri.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return _evidence_failure(
            asset, bridge_mode,
            f"cannot read material_simple.json: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    # 1. AssetTools.create_asset(name, package_path, Material, MaterialFactoryNew) — wrap try/except
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_name = target_pkg.rsplit("/", 1)[-1]
    asset_path = target_pkg.rsplit("/", 1)[0]

    try:
        material_asset = asset_tools.create_asset(
            asset_name=asset_name,
            package_path=asset_path,
            asset_class=unreal.Material,
            factory=unreal.MaterialFactoryNew(),
        )
    except Exception as exc:  # noqa: BLE001  # UE API 异常类型不可枚举
        return _evidence_failure(
            asset, bridge_mode,
            f"MaterialFactoryNew.create_asset raised: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    if material_asset is None:
        return _evidence_failure(
            asset, bridge_mode,
            f"MaterialFactoryNew.create_asset returned None for {target_pkg}",
            source_uri_abs=source_uri,
        )

    # 2-4. MaterialEditingLibrary 加 4 个 expression + 连到 Material output + 编译 + 保存(整段 wrap)
    try:
        lib = unreal.MaterialEditingLibrary

        # 2.1 BaseColor:Constant4Vector
        base_color = material_def.get("base_color_rgba", [0.5, 0.5, 0.5, 1.0])
        base_color_expr = lib.create_material_expression(
            material_asset, unreal.MaterialExpressionConstant4Vector,
        )
        base_color_expr.set_editor_property("constant", unreal.LinearColor(*base_color))
        lib.connect_material_property(base_color_expr, "", unreal.MaterialProperty.MP_BASE_COLOR)

        # 2.2 Metallic:Constant
        metallic_expr = lib.create_material_expression(
            material_asset, unreal.MaterialExpressionConstant,
        )
        metallic_expr.set_editor_property("r", float(material_def.get("metallic", 0.0)))
        lib.connect_material_property(metallic_expr, "", unreal.MaterialProperty.MP_METALLIC)

        # 2.3 Roughness:Constant
        roughness_expr = lib.create_material_expression(
            material_asset, unreal.MaterialExpressionConstant,
        )
        roughness_expr.set_editor_property("r", float(material_def.get("roughness", 0.7)))
        lib.connect_material_property(roughness_expr, "", unreal.MaterialProperty.MP_ROUGHNESS)

        # 2.4 Normal:可选,只在 normal_texture_ref 非 None 时连
        # 本 milestone 不解析 normal_texture_ref(需要二次资产 lookup),留 follow-up
        # normal_ref = material_def.get("normal_texture_ref")

        # 2.5 Emissive:Constant4Vector
        emissive = material_def.get("emissive_color_rgba", [0.0, 0.0, 0.0, 1.0])
        emissive_expr = lib.create_material_expression(
            material_asset, unreal.MaterialExpressionConstant4Vector,
        )
        emissive_expr.set_editor_property("constant", unreal.LinearColor(*emissive))
        lib.connect_material_property(emissive_expr, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

        # 3. 编译 material(让 expressions 生效)
        lib.recompile_material(material_asset)

        # 4. 保存 asset 落盘
        unreal.EditorAssetLibrary.save_asset(target_pkg)
    except Exception as exc:  # noqa: BLE001  # UE Material API 异常类型不可枚举
        return _evidence_failure(
            asset, bridge_mode,
            f"MaterialEditingLibrary chain raised: {type(exc).__name__}: {exc}",
            source_uri_abs=source_uri,
        )

    duration_ms = int((time.monotonic() - start) * 1000)
    return _evidence_success(
        asset, bridge_mode,
        source_uri_abs=source_uri,
        uasset_object_path=f"{target_pkg}.{asset_name}",
        factory_class="unreal.MaterialFactoryNew + unreal.MaterialEditingLibrary",
        duration_ms=duration_ms,
        import_log_excerpt=f"created material with 4 expressions (PBR Option α 五字段,normal_texture_ref pending)",
    )


def _creator_path_media(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, bridge_mode: str,
) -> dict[str, Any]:
    """file_media_source 真机创建(待 Task 10 填充);creator path 不走文件 importer,故省略 import_options。"""
    raise NotImplementedError("file_media_source creator pending Task 10")


# ============================================================
# CLI 入口(原有,只在 except 子句多收一个 RuntimeError)
# ============================================================

def main(argv: list[str] | None = None) -> int:
    """命令行入口:`python -m ... --manifest <path> [--plan <path>] [--bridge-mode simulated]`。"""
    import argparse
    import sys as _sys

    parser = argparse.ArgumentParser(
        description="ForgeUE_codex manifest importer (standalone CLI)",
    )
    parser.add_argument("--manifest", required=True, help="ForgeUE_codex manifest.json 路径")
    parser.add_argument("--plan", default=None, help="ForgeUE_codex import_plan.json 路径(可选)")
    parser.add_argument(
        "--bridge-mode",
        default="simulated",
        choices=list(_SUPPORTED_BRIDGE_MODES),
        help="桥接执行模式(默认 simulated)",
    )
    args = parser.parse_args(argv)

    try:
        result = import_from_manifest(
            manifest_path=args.manifest,
            plan_path=args.plan,
            bridge_mode=args.bridge_mode,
        )
    except (ValueError, NotImplementedError, FileNotFoundError, RuntimeError) as exc:
        print(f"[forgeue_manifest_importer] {exc}", file=_sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
