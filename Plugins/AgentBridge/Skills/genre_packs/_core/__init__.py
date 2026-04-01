"""
Genre Pack Core 机制入口。
"""

from .manifest_loader import load_pack_manifest, normalize_pack_manifest
from .registry import load_pack_registry, resolve_active_pack
from .module_loader import load_pack_modules
from .router_base import build_router_result, match_activation

__all__ = [
    "build_router_result",
    "load_pack_manifest",
    "load_pack_modules",
    "load_pack_registry",
    "match_activation",
    "normalize_pack_manifest",
    "resolve_active_pack",
]

