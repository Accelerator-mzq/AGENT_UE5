"""
Spec Generation Dispatcher
按 design_input + Static Base + Genre Pack 生成 dynamic spec tree。
"""

import os
import sys
from typing import Any, Dict, Optional

from compiler.analysis import analyze_delta_scope, load_contract_registry

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from Plugins.AgentBridge.Skills.genre_packs._core import (
    load_pack_manifest as load_pack_manifest_via_core,
    load_pack_modules,
    resolve_active_pack,
)

from .boardgame_scene_generator import generate_boardgame_dynamic_spec_tree
from .brownfield_delta_generator import generate_brownfield_delta_tree
from .static_base_loader import get_project_root, load_phase4_static_specs


def load_skill_pack_manifest(
    game_type: str,
    pack_manifest_path: Optional[str] = None,
) -> Dict[str, Any]:
    """兼容旧接口：加载单个类型包 manifest。"""
    resolved_path = pack_manifest_path or _get_default_pack_manifest_path(game_type)
    if not os.path.exists(resolved_path):
        return {
            "pack_id": f"genre-{game_type}",
            "version": "missing",
            "dependencies": {},
            "outputs": {},
            "manifest_path": resolved_path,
        }
    return load_pack_manifest_via_core(resolved_path)


def generate_dynamic_spec_tree(
    design_input: Dict[str, Any],
    routing_context: Dict[str, Any],
    static_base_root: Optional[str] = None,
    pack_manifest_path: Optional[str] = None,
    baseline_snapshot: Optional[Dict[str, Any]] = None,
    contract_root: Optional[str] = None,
    projection_profile: str = "preview_static",
) -> Dict[str, Any]:
    """统一生成 dynamic spec tree。"""
    _ensure_project_root_on_sys_path()
    static_spec_context = load_phase4_static_specs(static_base_root)
    game_type = design_input.get("game_type", "unknown")
    pack_manifest = resolve_active_pack(
        design_input=design_input,
        routing_context=routing_context,
        explicit_manifest_path=pack_manifest_path,
    )
    pack_modules = load_pack_modules(pack_manifest)

    required_spec_ids = _determine_required_spec_ids(game_type)
    static_spec_context["required_spec_ids"] = required_spec_ids

    if game_type == "boardgame":
        full_target_tree = generate_boardgame_dynamic_spec_tree(
            design_input=design_input,
            routing_context=routing_context,
            static_spec_context=static_spec_context,
            pack_manifest=pack_manifest,
            pack_modules=pack_modules,
            projection_profile=projection_profile,
        )
        analysis_context = {}
        delta_policy = full_target_tree.get("generation_trace", {}).get("delta_policy", {})

        if routing_context.get("mode") == "brownfield_expansion":
            contract_registry = load_contract_registry(contract_root)
            delta_context = analyze_delta_scope(
                design_input=design_input,
                baseline_snapshot=baseline_snapshot or {},
                target_scene_actors=full_target_tree.get("scene_spec", {}).get("actors", []),
                target_dynamic_spec_tree=full_target_tree,
                delta_policy=delta_policy,
            )
            dynamic_spec_tree = generate_brownfield_delta_tree(
                full_target_tree=full_target_tree,
                baseline_snapshot=baseline_snapshot or {},
                delta_context=delta_context,
                contract_registry=contract_registry,
            )
            analysis_context = {
                "baseline_snapshot": baseline_snapshot or {},
                "delta_context": delta_context,
                "contract_registry": contract_registry,
                "full_target_tree": full_target_tree,
                "pack_modules": pack_modules,
                "pack_manifest": pack_manifest,
            }
        else:
            dynamic_spec_tree = full_target_tree
            analysis_context = {
                "baseline_snapshot": baseline_snapshot or {},
                "delta_context": {},
                "contract_registry": {},
                "full_target_tree": full_target_tree,
                "pack_modules": pack_modules,
                "pack_manifest": pack_manifest,
            }
    else:
        dynamic_spec_tree = {
            "scene_spec": {"actors": []},
            "generation_trace": {
                "generator": "AgentBridge.Compiler.Phase6.SpecGenerationDispatcher",
                "projection_profile": projection_profile,
                "skill_pack_id": pack_manifest.get("pack_id", "unknown"),
            },
        }
        analysis_context = {
            "baseline_snapshot": baseline_snapshot or {},
            "delta_context": {},
            "contract_registry": {},
            "full_target_tree": dynamic_spec_tree,
            "pack_modules": pack_modules,
            "pack_manifest": pack_manifest,
        }

    return {
        "dynamic_spec_tree": dynamic_spec_tree,
        "static_spec_context": static_spec_context,
        "pack_manifest": pack_manifest,
        "pack_modules": pack_modules,
        "analysis_context": analysis_context,
    }


def _determine_required_spec_ids(game_type: str) -> list:
    """按当前 Phase 4 实际支持范围声明必需静态基座。"""
    if game_type == "boardgame":
        return [
            "WorldBuildStaticSpec",
            "ValidationStaticSpec",
            "BoardgameStaticSpec",
            "BoardgameValidationStaticSpec",
        ]
    return []


def _get_default_pack_manifest_path(game_type: str) -> str:
    """返回默认的类型包 manifest 路径。"""
    return os.path.join(
        get_project_root(),
        "Plugins",
        "AgentBridge",
        "Skills",
        "genre_packs",
        game_type,
        "pack_manifest.yaml",
    )


def _ensure_project_root_on_sys_path() -> None:
    """确保可以通过项目根导入 Plugins.AgentBridge.Skills。"""
    project_root = get_project_root()
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
