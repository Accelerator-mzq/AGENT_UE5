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
# 5+1 种 asset_kind 实现(Task 6-10 逐一填充;此 task 全 raise NotImplementedError 占位)
# ============================================================

def _importer_path_texture(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, import_options: dict[str, Any], bridge_mode: str,
) -> dict[str, Any]:
    """texture / sprite_sheet 真机导入(待 Task 6 填充)。"""
    raise NotImplementedError("texture/sprite_sheet importer pending Task 6")


def _importer_path_sound(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, import_options: dict[str, Any], bridge_mode: str,
) -> dict[str, Any]:
    """sound_wave 真机导入(待 Task 7 填充)。"""
    raise NotImplementedError("sound_wave importer pending Task 7")


def _importer_path_mesh(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, import_options: dict[str, Any], bridge_mode: str,
) -> dict[str, Any]:
    """static_mesh 真机导入(待 Task 8 填充)。"""
    raise NotImplementedError("static_mesh importer pending Task 8")


def _creator_path_material(
    asset: dict[str, Any], source_uri: Path, target_pkg: str,
    overwrite: bool, bridge_mode: str,
) -> dict[str, Any]:
    """material 真机创建(待 Task 9 填充);creator path 不走文件 importer,故省略 import_options。"""
    raise NotImplementedError("material creator pending Task 9")


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
