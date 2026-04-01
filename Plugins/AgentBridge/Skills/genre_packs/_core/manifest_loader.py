"""
Genre Pack Manifest Loader
负责读取并标准化类型包 manifest。
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import yaml


def load_pack_manifest(manifest_path: str) -> Dict[str, Any]:
    """加载单个类型包 manifest。"""
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Pack manifest 不存在: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}

    return normalize_pack_manifest(manifest, manifest_path)


def normalize_pack_manifest(
    manifest: Dict[str, Any],
    manifest_path: Optional[str] = None,
) -> Dict[str, Any]:
    """将 manifest 标准化为 Phase 6 统一结构。"""
    resolved_path = os.path.abspath(manifest_path) if manifest_path else ""
    pack_dir = os.path.dirname(resolved_path) if resolved_path else ""
    normalized = dict(manifest)

    normalized.setdefault("pack_id", os.path.basename(pack_dir) if pack_dir else "unknown-pack")
    normalized.setdefault("version", "0.1.0")
    normalized.setdefault("title", normalized["pack_id"])
    normalized.setdefault("status", "draft")
    normalized.setdefault("description", "")
    normalized.setdefault("router", {})
    normalized.setdefault("activation", {})
    normalized.setdefault("required_skills", [])
    normalized.setdefault("optional_skills", [])
    normalized.setdefault("review_extensions", [])
    normalized.setdefault("validation_extensions", [])
    normalized.setdefault("delta_policy", {})
    normalized.setdefault("policy", {})
    normalized.setdefault("dependencies", {})
    normalized.setdefault("outputs", {})
    normalized.setdefault("metadata", {})

    for key in ["required_skills", "optional_skills", "review_extensions", "validation_extensions"]:
        if not isinstance(normalized.get(key), list):
            normalized[key] = list(normalized.get(key) or [])

    normalized["manifest_path"] = resolved_path
    normalized["pack_dir"] = pack_dir
    normalized["pack_name"] = os.path.basename(pack_dir) if pack_dir else normalized["pack_id"]
    return normalized

