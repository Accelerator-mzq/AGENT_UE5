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
