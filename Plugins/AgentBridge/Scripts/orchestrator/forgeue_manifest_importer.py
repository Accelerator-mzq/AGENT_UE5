"""ForgeUE_codex UEAssetManifest 导入桥接。

读取 ForgeUE_codex P4 流水线产出的 `manifest.json` + `import_plan.json`，
按 bridge_mode 分发到 simulated / bridge_python / bridge_rc_api 三种执行通路。

输入契约固定为 ForgeUE_codex `framework.core.ue.UEAssetManifest`
（schema_version 1.0.0），asset_kind 枚举：
    texture / sound_wave / static_mesh / material / file_media_source

设计原则:
- 只负责"读 manifest → 翻译成 AgentBridge 可执行单元"
- 不做任何 UE Editor 内部副作用（那是 bridge_mode 各自下游的事）
- simulated 模式必须能完全离线跑通，作为契约不漂移的看护
"""

# ------------------------------------------------------------
# 未实现部分(后续 milestone 接入)
# ------------------------------------------------------------
# bridge_python:
#   在 UE Editor 进程内通过 unreal Python API 调 AssetTools.ImportAssets,
#   对每条 op 写 evidence(沿用 ForgeUE_codex 的 evidence.json 契约)。
#   只能在 UE Editor 内执行,不能离线跑;触发条件:UE Editor 启动 +
#   AgentBridge subsystem 已 ready。
#
# bridge_rc_api:
#   通过 Remote Control API(端口 30010)远程触发同样的导入。
#   依赖 bridge.remote_control_client; 触发条件: UE Editor + Remote Control
#   plugin enabled。
# ------------------------------------------------------------

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_manifest(manifest_path: str) -> dict[str, Any]:
    """读 ForgeUE_codex manifest.json 并做基本校验。

    返回的 dict 至少包含 ``schema_version`` / ``run_id`` / ``assets``。
    上游 schema 若往 2.x 演进且不向后兼容，本函数会通过断言早期失败。
    """
    raw = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    # 只允许已对齐的契约版本；上游升级时这里会显式断版本号。
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


def import_from_manifest(
    *,
    manifest_path: str,
    plan_path: str | None = None,
    bridge_mode: str = "simulated",
) -> dict[str, Any]:
    """主入口:按 bridge_mode dispatch,返回结构化执行结果。

    - simulated: 离线模拟,不副作用,用于契约校验 + handoff_runner 单元测试
    - bridge_python: 调 UE Python Editor API(本计划留 NotImplementedError stub)
    - bridge_rc_api: 调 Remote Control API(本计划留 NotImplementedError stub)
    """
    if bridge_mode not in _SUPPORTED_BRIDGE_MODES:
        raise ValueError(
            f"unsupported bridge_mode: {bridge_mode!r} "
            f"(expected one of {_SUPPORTED_BRIDGE_MODES})"
        )

    manifest = parse_manifest(manifest_path)
    plan = parse_import_plan(plan_path) if plan_path else None

    if bridge_mode == "simulated":
        asset_results = [_simulate_asset(asset) for asset in manifest["assets"]]
        return {
            "status": "success",
            "bridge_mode": bridge_mode,
            "run_id": manifest["run_id"],
            "manifest_id": manifest.get("manifest_id"),
            "plan_id": plan.get("plan_id") if plan else None,
            "asset_results": asset_results,
        }

    # bridge_python / bridge_rc_api 由 Task 4 填充 NotImplementedError stub
    raise NotImplementedError(
        f"bridge_mode={bridge_mode!r} not implemented in this milestone"
    )


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
