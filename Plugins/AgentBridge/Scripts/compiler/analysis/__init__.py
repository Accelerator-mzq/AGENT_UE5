"""
Compiler Analysis Module
提供 Brownfield 基线构建、差量分析与 Contract registry 装载能力。
"""

from .baseline_builder import (
    build_and_save_baseline_snapshot,
    build_baseline_snapshot,
    get_default_snapshot_dir,
    load_baseline_snapshot,
    save_baseline_snapshot,
)
from .contract_registry_loader import (
    get_default_contract_root,
    load_contract_bundle,
    load_contract_registry,
)
from .delta_scope_analyzer import analyze_delta_scope

__all__ = [
    "analyze_delta_scope",
    "build_and_save_baseline_snapshot",
    "build_baseline_snapshot",
    "get_default_contract_root",
    "get_default_snapshot_dir",
    "load_baseline_snapshot",
    "load_contract_bundle",
    "load_contract_registry",
    "save_baseline_snapshot",
]
