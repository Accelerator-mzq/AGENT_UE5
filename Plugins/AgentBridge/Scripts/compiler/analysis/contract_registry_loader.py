"""
Contract Registry Loader
负责加载 Brownfield Contract registry 与模板资源。
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import yaml


def get_default_contract_root() -> str:
    """返回默认的 Contracts 根目录。"""
    return os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "Specs",
            "Contracts",
        )
    )


def load_contract_registry(contract_root: Optional[str] = None) -> Dict[str, Any]:
    """加载 Contract registry。"""
    resolved_root = contract_root or get_default_contract_root()
    registry_path = os.path.join(resolved_root, "Registry", "contract_type_registry.yaml")

    if not os.path.exists(registry_path):
        raise FileNotFoundError(f"Contract registry 不存在: {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as file:
        registry = yaml.safe_load(file) or {}

    registry["registry_path"] = registry_path
    registry["contract_root"] = resolved_root
    return registry


def load_contract_bundle(
    contract_id: str,
    registry: Optional[Dict[str, Any]] = None,
    contract_root: Optional[str] = None,
) -> Dict[str, Any]:
    """按 contract_id 加载单个 Contract bundle。"""
    registry_data = registry or load_contract_registry(contract_root)
    resolved_root = contract_root or registry_data.get("contract_root") or get_default_contract_root()

    entry = _find_registry_entry(registry_data, contract_id)
    if entry is None:
        raise KeyError(f"registry 中不存在 contract_id: {contract_id}")

    template_path = os.path.join(resolved_root, entry["template_ref"])
    schema_path = os.path.join(resolved_root, entry["schema_ref"])
    manifest_path = os.path.join(os.path.dirname(template_path), "manifest.yaml")

    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}
    with open(template_path, "r", encoding="utf-8") as file:
        template = yaml.safe_load(file) or {}
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    return {
        "contract_id": contract_id,
        "entry": entry,
        "manifest": manifest,
        "template": template,
        "schema": schema,
        "manifest_path": manifest_path,
        "template_path": template_path,
        "schema_path": schema_path,
    }


def _find_registry_entry(registry: Dict[str, Any], contract_id: str) -> Optional[Dict[str, Any]]:
    """在 registry 中查找目标条目。"""
    for entry in registry.get("contracts", []):
        if entry.get("contract_id") == contract_id:
            return entry
    return None
