"""
Baseline Builder
将 project_state 快照固化为可复用的 Brownfield baseline snapshot。
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import yaml


def get_default_snapshot_dir(project_root: Optional[str] = None) -> str:
    """返回默认的 baseline snapshot 输出目录。"""
    resolved_project_root = project_root or _get_project_root()
    return os.path.join(resolved_project_root, "ProjectState", "Snapshots")


def build_baseline_snapshot(
    project_state: Dict[str, Any],
    design_input: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """根据 project_state 构造 baseline snapshot 数据。"""
    source_project_state = copy.deepcopy(project_state)
    project_name = project_state.get("project_name", "Unknown")
    current_level = project_state.get("current_level", "")
    game_type = (design_input or {}).get("game_type", "unknown")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    digest = project_state.get("current_project_state_digest") or _build_digest(source_project_state)
    baseline_id = f"baseline.{game_type}.{timestamp}.{digest[:8]}"

    current_project_model = {
        "current_level": current_level,
        "actor_count": project_state.get("actor_count", len(project_state.get("actors", []))),
        "actors": [
            {
                "actor_name": actor.get("actor_name", ""),
                "actor_path": actor.get("actor_path", ""),
                "actor_class": actor.get("class") or actor.get("actor_class", ""),
                "transform": copy.deepcopy(actor.get("transform", {})),
                "tags": list(actor.get("tags", [])),
            }
            for actor in project_state.get("actors", [])
        ],
        "dirty_assets": list(project_state.get("dirty_assets", [])),
        "map_check_summary": copy.deepcopy(
            project_state.get(
                "map_check_summary",
                {"map_errors": [], "map_warnings": []},
            )
        ),
    }

    current_spec_baseline = {
        "scene_spec": {
            "actors": [
                {
                    "actor_name": actor.get("actor_name", ""),
                    "actor_class": actor.get("class") or actor.get("actor_class", ""),
                    "transform": copy.deepcopy(actor.get("transform", {})),
                    "actor_path": actor.get("actor_path", ""),
                }
                for actor in project_state.get("actors", [])
            ]
        }
    }

    return {
        "baseline_id": baseline_id,
        "snapshot_ref": "",
        "project_context": {
            "project_name": project_name,
            "game_type": game_type,
            "current_level": current_level,
            "engine_version": project_state.get("engine_version", "Unknown"),
        },
        "current_project_model": current_project_model,
        "current_spec_baseline": current_spec_baseline,
        "current_capability_map": {
            "supported_delta_operations": ["no_change", "append_actor"],
            "blocked_delta_operations": ["patch", "replace", "migrate"],
        },
        "source_project_state": source_project_state,
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "generator": "AgentBridge.Compiler.Phase5.BaselineBuilder",
            "source_digest": digest,
        },
    }


def save_baseline_snapshot(
    baseline_snapshot: Dict[str, Any],
    output_dir: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """保存 baseline snapshot 到 ProjectState/Snapshots/。"""
    resolved_output_dir = output_dir or get_default_snapshot_dir()
    os.makedirs(resolved_output_dir, exist_ok=True)

    filename = f"{baseline_snapshot['baseline_id']}.yaml"
    output_path = os.path.join(resolved_output_dir, filename)

    snapshot_to_save = copy.deepcopy(baseline_snapshot)
    snapshot_to_save["snapshot_ref"] = output_path

    with open(output_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(snapshot_to_save, file, allow_unicode=True, sort_keys=False)

    return snapshot_to_save, output_path


def build_and_save_baseline_snapshot(
    project_state: Dict[str, Any],
    design_input: Optional[Dict[str, Any]] = None,
    output_dir: Optional[str] = None,
) -> Tuple[Dict[str, Any], str]:
    """构建并保存 baseline snapshot。"""
    snapshot = build_baseline_snapshot(project_state, design_input=design_input)
    return save_baseline_snapshot(snapshot, output_dir=output_dir)


def load_baseline_snapshot(snapshot_path: str) -> Dict[str, Any]:
    """加载 baseline snapshot 文件。"""
    with open(snapshot_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def _build_digest(source_project_state: Dict[str, Any]) -> str:
    """为 source_project_state 生成稳定摘要。"""
    return hashlib.sha1(
        json.dumps(source_project_state, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _get_project_root() -> str:
    """返回项目根目录。"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
