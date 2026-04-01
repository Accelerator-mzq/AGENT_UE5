"""
Project State Intake
调用现有查询接口，获取项目现状，并为 Brownfield 分析提供统一快照。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def get_project_state_snapshot(
    project_root: Optional[str] = None,
    allow_mock_existing_content: bool = False,
) -> Dict[str, Any]:
    """
    获取项目现状快照。

    兼容要求：
    - 保留 Phase 3/4 既有顶层字段
    - 新增 Brownfield 所需的 richer 字段

    Args:
        project_root: 项目根目录；为空时自动推导
        allow_mock_existing_content: 是否允许直接消费 mock 示例中的已有 Actor。
            默认关闭，避免 MOCK 通道把 Greenfield 流程误判成 Brownfield。

    Returns:
        标准化的项目现状快照
    """
    resolved_project_root = project_root or _get_project_root()
    baseline_refs = _collect_baseline_refs(resolved_project_root)
    registry_refs = _collect_registry_refs(resolved_project_root)

    try:
        bridge_snapshot = _query_bridge_snapshot(
            resolved_project_root=resolved_project_root,
            allow_mock_existing_content=allow_mock_existing_content,
            baseline_refs=baseline_refs,
            registry_refs=registry_refs,
        )
        if bridge_snapshot is not None:
            return bridge_snapshot
    except Exception as exc:
        return _build_mock_fallback_snapshot(
            resolved_project_root,
            baseline_refs=baseline_refs,
            registry_refs=registry_refs,
            reason=str(exc),
        )

    return _build_mock_fallback_snapshot(
        resolved_project_root,
        baseline_refs=baseline_refs,
        registry_refs=registry_refs,
        reason="MOCK 通道默认回退为空项目快照",
    )


def check_baseline_exists(baseline_path: str) -> bool:
    """
    检查是否存在 baseline。

    Args:
        baseline_path: Baseline 目录路径

    Returns:
        是否存在 baseline 文件
    """
    if not os.path.exists(baseline_path):
        return False

    if os.path.isfile(baseline_path):
        return True

    return any(
        os.path.isfile(os.path.join(baseline_path, file_name))
        for file_name in os.listdir(baseline_path)
    )


def _get_project_root() -> str:
    """返回项目根目录。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(script_dir, "..", "..", "..", "..", ".."))


def _query_bridge_snapshot(
    resolved_project_root: str,
    allow_mock_existing_content: bool,
    baseline_refs: List[str],
    registry_refs: List[str],
) -> Optional[Dict[str, Any]]:
    """通过现有 Bridge 查询接口读取项目状态。"""
    bridge_dir = os.path.join(
        resolved_project_root,
        "Plugins",
        "AgentBridge",
        "Scripts",
        "bridge",
    )
    if bridge_dir not in sys.path:
        sys.path.insert(0, bridge_dir)

    from bridge_core import BridgeChannel, get_channel
    from query_tools import (
        get_actor_state,
        get_current_project_state,
        get_dirty_assets,
        list_level_actors,
        run_map_check,
    )

    channel = get_channel()
    if channel == BridgeChannel.MOCK and not allow_mock_existing_content:
        # 默认保持 Greenfield 兼容性；Brownfield 测试可显式打开。
        return None

    project_state_resp = get_current_project_state()
    actors_resp = list_level_actors()
    dirty_assets_resp = get_dirty_assets()
    map_check_resp = run_map_check()

    project_state_data = _unwrap_success_data(project_state_resp, "get_current_project_state")
    actors_data = _unwrap_success_data(actors_resp, "list_level_actors")
    dirty_assets_data = _unwrap_optional_data(dirty_assets_resp)
    map_check_data = _unwrap_optional_data(map_check_resp)

    actors = []
    for actor_entry in actors_data.get("actors", []):
        actor_name = actor_entry.get("actor_name", "")
        actor_path = actor_entry.get("actor_path", "")
        actor_class = actor_entry.get("class", "")
        actor_state = {}

        if actor_path:
            actor_state_resp = get_actor_state(actor_path)
            actor_state = _unwrap_optional_data(actor_state_resp)

        actors.append(
            {
                "actor_name": actor_name or actor_state.get("actor_name", ""),
                "actor_path": actor_path or actor_state.get("actor_path", ""),
                "class": actor_class or actor_state.get("class", ""),
                "transform": actor_state.get(
                    "transform",
                    {
                        "location": [0.0, 0.0, 0.0],
                        "rotation": [0.0, 0.0, 0.0],
                        "relative_scale3d": [1.0, 1.0, 1.0],
                    },
                ),
                "target_level": actor_state.get("target_level", project_state_data.get("current_level", "")),
                "tags": actor_state.get("tags", []),
            }
        )

    snapshot = _build_snapshot(
        project_name=project_state_data.get("project_name", "Unknown"),
        engine_version=project_state_data.get("engine_version", "Unknown"),
        current_level=project_state_data.get("current_level", ""),
        actors=actors,
        baseline_refs=baseline_refs,
        registry_refs=registry_refs,
        known_issues_summary=_build_known_issues_summary(
            dirty_assets=dirty_assets_data.get("dirty_assets", []),
            map_errors=map_check_data.get("map_errors", []),
            map_warnings=map_check_data.get("map_warnings", []),
        ),
        metadata={
            "captured_at": datetime.now().isoformat(),
            "source": "bridge_live" if channel != BridgeChannel.MOCK else "bridge_mock",
            "channel": channel.value,
            "uproject_path": project_state_data.get("uproject_path", ""),
            "editor_mode": project_state_data.get("editor_mode", ""),
        },
        extra_fields={
            "dirty_assets": dirty_assets_data.get("dirty_assets", []),
            "map_check_summary": {
                "map_errors": map_check_data.get("map_errors", []),
                "map_warnings": map_check_data.get("map_warnings", []),
            },
        },
    )

    return snapshot


def _build_mock_fallback_snapshot(
    resolved_project_root: str,
    baseline_refs: List[str],
    registry_refs: List[str],
    reason: str,
) -> Dict[str, Any]:
    """在无 Editor / 无 Bridge / 默认 MOCK 通道下返回兼容的空项目快照。"""
    return _build_snapshot(
        project_name=os.path.splitext(os.path.basename(resolved_project_root))[0] or "Mvpv4TestCodex",
        engine_version="Unknown",
        current_level="",
        actors=[],
        baseline_refs=baseline_refs,
        registry_refs=registry_refs,
        known_issues_summary=[reason],
        metadata={
            "captured_at": datetime.now().isoformat(),
            "source": "mock_fallback",
            "channel": "mock",
            "project_root": resolved_project_root,
        },
        extra_fields={
            "error": reason,
            "dirty_assets": [],
            "map_check_summary": {"map_errors": [], "map_warnings": []},
        },
    )


def _build_snapshot(
    project_name: str,
    engine_version: str,
    current_level: str,
    actors: List[Dict[str, Any]],
    baseline_refs: List[str],
    registry_refs: List[str],
    known_issues_summary: List[str],
    metadata: Dict[str, Any],
    extra_fields: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """构造标准化 project_state 快照。"""
    actor_count = len(actors)
    digest_source = {
        "project_name": project_name,
        "engine_version": engine_version,
        "current_level": current_level,
        "actors": actors,
    }
    digest = hashlib.sha1(
        json.dumps(digest_source, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    snapshot = {
        "project_name": project_name,
        "engine_version": engine_version,
        "current_level": current_level,
        "actor_count": actor_count,
        "is_empty": actor_count == 0,
        "actors": actors,
        "has_existing_content": actor_count > 0,
        "has_baseline": bool(baseline_refs),
        "baseline_refs": baseline_refs,
        "registry_refs": registry_refs,
        "known_issues_summary": known_issues_summary,
        "metadata": metadata,
        "current_project_state_digest": digest,
    }

    if extra_fields:
        snapshot.update(extra_fields)

    return snapshot


def _collect_baseline_refs(project_root: str) -> List[str]:
    """收集当前可见的 baseline / snapshot 引用。"""
    refs: List[str] = []
    candidate_dirs = [
        os.path.join(project_root, "ProjectState", "Snapshots"),
        os.path.join(project_root, "ProjectInputs", "Baselines"),
    ]

    for candidate_dir in candidate_dirs:
        if not os.path.isdir(candidate_dir):
            continue
        for file_name in sorted(os.listdir(candidate_dir)):
            file_path = os.path.join(candidate_dir, file_name)
            if os.path.isfile(file_path):
                refs.append(file_path)

    return refs


def _collect_registry_refs(project_root: str) -> List[str]:
    """收集当前可见的 registry / handoff 引用。"""
    refs: List[str] = []
    candidate_dirs = [
        os.path.join(project_root, "ProjectState", "Handoffs", "approved"),
        os.path.join(project_root, "Plugins", "AgentBridge", "Specs", "StaticBase", "Registry"),
        os.path.join(project_root, "Plugins", "AgentBridge", "Specs", "Contracts", "Registry"),
    ]

    for candidate_dir in candidate_dirs:
        if not os.path.isdir(candidate_dir):
            continue
        for file_name in sorted(os.listdir(candidate_dir)):
            file_path = os.path.join(candidate_dir, file_name)
            if os.path.isfile(file_path):
                refs.append(file_path)

    return refs


def _unwrap_success_data(response: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """读取成功响应中的 data。"""
    if response.get("status") != "success":
        raise RuntimeError(f"{tool_name} 调用失败: {response}")
    return response.get("data", {})


def _unwrap_optional_data(response: Dict[str, Any]) -> Dict[str, Any]:
    """读取可选响应中的 data；失败时返回空字典。"""
    if response.get("status") != "success":
        return {}
    return response.get("data", {})


def _build_known_issues_summary(
    dirty_assets: List[str],
    map_errors: List[str],
    map_warnings: List[str],
) -> List[str]:
    """构造简短的问题摘要。"""
    issues = []
    if dirty_assets:
        issues.append(f"存在 {len(dirty_assets)} 个未保存脏资产")
    if map_errors:
        issues.append(f"MapCheck errors={len(map_errors)}")
    if map_warnings:
        issues.append(f"MapCheck warnings={len(map_warnings)}")
    return issues


if __name__ == "__main__":
    snapshot = get_project_state_snapshot()
    print(f"项目名称: {snapshot['project_name']}")
    print(f"Actor 数量: {snapshot['actor_count']}")
    print(f"是否为空项目: {snapshot['is_empty']}")
    print(f"快照来源: {snapshot.get('metadata', {}).get('source')}")
