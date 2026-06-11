# -*- coding: utf-8 -*-
"""施工规范读取:全文 + 版本号(首部 manifest_version 行),fetch 载荷注入用。零领域语义。"""
import re
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_MANIFEST_REL = Path("ProjectInputs") / "ConstructionManifest" / "demo_plugin_standards.md"
_VERSION_LINE = re.compile(r"^manifest_version:\s*([0-9][0-9.]*)\s*$", re.MULTILINE)


def load_construction_manifest(project_root, path: Optional[Path] = None) -> Tuple[str, str]:
    """返回 (全文, 版本)。无版本行 fail-closed(规范文件必须可对账)。"""
    target = Path(path) if path else Path(project_root) / DEFAULT_MANIFEST_REL
    text = target.read_text(encoding="utf-8")
    match = _VERSION_LINE.search(text)
    if not match:
        raise ValueError(f"施工规范缺 manifest_version 行: {target}")
    return text, match.group(1)
