"""
Static Base Loader
负责装载 Phase 4 的 Static Spec Base registry 与模板资源。
"""

import json
import os
from typing import Any, Dict, Optional

import yaml


def get_project_root() -> str:
    """返回项目根目录。"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))


def get_default_static_base_root() -> str:
    """返回默认的 StaticBase 根目录。"""
    return os.path.join(get_project_root(), "Plugins", "AgentBridge", "Specs", "StaticBase")


def load_static_base_registry(static_base_root: Optional[str] = None) -> Dict[str, Any]:
    """加载 static spec registry。"""
    resolved_root = static_base_root or get_default_static_base_root()
    registry_path = os.path.join(resolved_root, "Registry", "spec_type_registry.yaml")

    if not os.path.exists(registry_path):
        raise FileNotFoundError(f"Static Base registry 不存在: {registry_path}")

    with open(registry_path, "r", encoding="utf-8") as file:
        registry = yaml.safe_load(file) or {}

    registry["registry_path"] = registry_path
    registry["static_base_root"] = resolved_root
    return registry


def load_static_spec_bundle(
    spec_id: str,
    registry: Optional[Dict[str, Any]] = None,
    static_base_root: Optional[str] = None,
) -> Dict[str, Any]:
    """按 spec_id 装载单个 Static Base。"""
    registry_data = registry or load_static_base_registry(static_base_root)
    resolved_root = static_base_root or registry_data.get("static_base_root") or get_default_static_base_root()

    entry = _find_registry_entry(registry_data, spec_id)
    if entry is None:
        raise KeyError(f"registry 中不存在 spec_id: {spec_id}")

    template_path = os.path.join(resolved_root, entry["template_ref"])
    schema_path = os.path.join(resolved_root, entry["schema_ref"])
    manifest_path = os.path.join(os.path.dirname(template_path), "manifest.yaml")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Static Base template 不存在: {template_path}")
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Static Base schema 不存在: {schema_path}")
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Static Base manifest 不存在: {manifest_path}")

    with open(manifest_path, "r", encoding="utf-8") as file:
        manifest = yaml.safe_load(file) or {}
    with open(template_path, "r", encoding="utf-8") as file:
        template = yaml.safe_load(file) or {}
    with open(schema_path, "r", encoding="utf-8") as file:
        schema = json.load(file)

    return {
        "spec_id": spec_id,
        "entry": entry,
        "manifest": manifest,
        "template": template,
        "schema": schema,
        "manifest_path": manifest_path,
        "template_path": template_path,
        "schema_path": schema_path,
    }


def load_phase4_static_specs(static_base_root: Optional[str] = None) -> Dict[str, Any]:
    """装载所有 phase4_enabled 的静态基座。"""
    registry = load_static_base_registry(static_base_root)
    loaded_specs: Dict[str, Any] = {}
    missing_specs = []

    for entry in registry.get("static_specs", []):
        if not entry.get("phase4_enabled", False):
            continue

        spec_id = entry.get("spec_id", "")
        try:
            loaded_specs[spec_id] = load_static_spec_bundle(
                spec_id=spec_id,
                registry=registry,
                static_base_root=registry["static_base_root"],
            )
        except FileNotFoundError:
            missing_specs.append(spec_id)

    return {
        "registry": registry,
        "loaded_specs": loaded_specs,
        "missing_specs": missing_specs,
        "static_base_root": registry["static_base_root"],
    }


def _find_registry_entry(registry: Dict[str, Any], spec_id: str) -> Optional[Dict[str, Any]]:
    """在 registry 中查找目标条目。"""
    for entry in registry.get("static_specs", []):
        if entry.get("spec_id") == spec_id:
            return entry
    return None
