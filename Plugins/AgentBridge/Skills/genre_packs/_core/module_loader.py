"""
Genre Pack Module Loader
按目录约定解析 required skills / reviewer / validator / delta policy 模块。
"""

from __future__ import annotations

import importlib.util
import os
from types import ModuleType
from typing import Any, Dict, List


def load_pack_modules(pack_manifest: Dict[str, Any]) -> Dict[str, Any]:
    """加载 pack 约定目录下的扩展模块。"""
    pack_dir = pack_manifest.get("pack_dir", "")
    if not pack_dir:
        return {
            "required_skills": [],
            "review_extensions": [],
            "validation_extensions": [],
            "delta_policies": [],
        }

    return {
        "required_skills": _load_module_entries(pack_dir, "required_skills", pack_manifest.get("required_skills", [])),
        "review_extensions": _load_module_entries(
            pack_dir, "review_extensions", pack_manifest.get("review_extensions", [])
        ),
        "validation_extensions": _load_module_entries(
            pack_dir, "validation_extensions", pack_manifest.get("validation_extensions", [])
        ),
        "delta_policies": _load_delta_policy_entries(pack_dir, pack_manifest.get("delta_policy", {})),
    }


def _load_module_entries(pack_dir: str, subdir: str, module_ids: List[str]) -> List[Dict[str, Any]]:
    """按固定子目录加载模块文件。"""
    loaded_entries: List[Dict[str, Any]] = []
    for module_id in module_ids:
        module_path = os.path.join(pack_dir, subdir, f"{module_id}.py")
        if not os.path.exists(module_path):
            loaded_entries.append(
                {
                    "module_id": module_id,
                    "module_path": module_path,
                    "module": None,
                    "exists": False,
                }
            )
            continue

        loaded_entries.append(
            {
                "module_id": module_id,
                "module_path": module_path,
                "module": _load_python_module(module_path, f"{subdir}_{module_id}"),
                "exists": True,
            }
        )
    return loaded_entries


def _load_delta_policy_entries(pack_dir: str, delta_policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """加载 delta policy provider。"""
    provider = delta_policy.get("provider")
    if not provider:
        return []
    return _load_module_entries(pack_dir, "delta_policy", [provider])


def _load_python_module(module_path: str, module_name: str) -> ModuleType:
    """从文件路径加载 Python 模块。"""
    import_name = f"agentbridge_phase6_{module_name}"
    spec = importlib.util.spec_from_file_location(import_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"无法为模块生成导入 spec: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

