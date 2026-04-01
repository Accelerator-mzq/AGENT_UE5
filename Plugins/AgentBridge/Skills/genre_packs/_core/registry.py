"""
Genre Pack Registry
负责扫描并选择当前设计输入对应的类型包。
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from .manifest_loader import load_pack_manifest
from .router_base import match_activation


def get_default_pack_root(project_root: Optional[str] = None) -> str:
    """返回类型包目录。"""
    if project_root:
        return os.path.join(project_root, "Plugins", "AgentBridge", "Skills", "genre_packs")

    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_pack_registry(pack_root: Optional[str] = None) -> Dict[str, Any]:
    """扫描 genre_packs 目录，构建 registry。"""
    resolved_root = pack_root or get_default_pack_root()
    packs: List[Dict[str, Any]] = []

    if not os.path.isdir(resolved_root):
        return {
            "pack_root": resolved_root,
            "packs": [],
            "pack_map": {},
        }

    for entry_name in sorted(os.listdir(resolved_root)):
        if entry_name.startswith("_"):
            continue
        manifest_path = os.path.join(resolved_root, entry_name, "pack_manifest.yaml")
        if not os.path.exists(manifest_path):
            continue
        manifest = load_pack_manifest(manifest_path)
        packs.append(manifest)

    return {
        "pack_root": resolved_root,
        "packs": packs,
        "pack_map": {pack["pack_id"]: pack for pack in packs},
    }


def resolve_active_pack(
    design_input: Dict[str, Any],
    routing_context: Dict[str, Any],
    pack_root: Optional[str] = None,
    explicit_manifest_path: Optional[str] = None,
) -> Dict[str, Any]:
    """根据设计输入与路由上下文选择一个激活的类型包。"""
    if explicit_manifest_path:
        manifest = load_pack_manifest(explicit_manifest_path)
        manifest["router_result"] = {
            "matched": True,
            "confidence": 1.0,
            "matched_feature_tags": list(design_input.get("feature_tags", [])),
            "reasons": ["显式传入 pack_manifest_path"],
            "activated_pack_ids": [manifest.get("pack_id", "")],
        }
        return manifest

    registry = load_pack_registry(pack_root)
    candidates: List[Dict[str, Any]] = []
    expected_game_type = str(design_input.get("game_type", "")).lower()

    for pack in registry.get("packs", []):
        router_result = match_activation(
            design_input=design_input,
            activation=pack.get("activation", {}),
            pack_id=pack.get("pack_id", ""),
        )
        pack_with_result = dict(pack)
        pack_with_result["router_result"] = router_result
        candidates.append(pack_with_result)

    if not candidates:
        return {
            "pack_id": f"genre-{expected_game_type or 'unknown'}",
            "version": "missing",
            "status": "missing",
            "manifest_path": "",
            "pack_dir": "",
            "router_result": {
                "matched": False,
                "confidence": 0.0,
                "matched_feature_tags": [],
                "reasons": ["未扫描到任何类型包 manifest"],
                "activated_pack_ids": [],
            },
        }

    candidates.sort(
        key=lambda item: (
            1 if expected_game_type and expected_game_type in item.get("pack_id", "").lower() else 0,
            float(item.get("router_result", {}).get("confidence", 0.0)),
        ),
        reverse=True,
    )
    selected = candidates[0]
    selected["registry"] = registry
    return selected

