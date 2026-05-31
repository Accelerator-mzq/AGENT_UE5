"""HUD 多专家协商试点 —— 纯逻辑层。

不依赖 LLM / 网络，可离线单元测试。
LLM 调用与编排在 demo_hud_multiexpert.py。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def merge_discovered_dimensions(
    expert_dim_lists: List[Tuple[str, List[Dict[str, Any]]]],
) -> List[Dict[str, Any]]:
    """合并多专家维度清单。

    expert_dim_lists: [(专家名, [维度dict,...]), ...]，维度 dict 至少含 dimension_id。
    返回: 去重后的维度列表（按首次出现顺序），每项是首现维度的副本 +
          "proposed_by": [按出现顺序提出该维度的专家名]。
    """
    merged: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for expert_name, dims in expert_dim_lists:
        for dim in dims:
            did = dim.get("dimension_id")
            if not did:
                continue
            if did not in merged:
                merged[did] = {**dim, "proposed_by": [expert_name]}
                order.append(did)
            elif expert_name not in merged[did]["proposed_by"]:
                merged[did]["proposed_by"].append(expert_name)
    return [merged[d] for d in order]


def resolve_owner(proposed_by: List[str], expert_priority: List[str]) -> str:
    """维度归属：按 expert_priority 顺序取 proposed_by 中第一个出现的专家。

    proposed_by 为空时返回 expert_priority[0] 作为兜底 owner。
    """
    for expert in expert_priority:
        if expert in proposed_by:
            return expert
    return expert_priority[0]


def detect_convergence(stances: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """逐维度判断三方选择是否趋同。

    stances: {专家名: {dimension_id: chosen_value}}
    返回: {dimension_id: {"converged": bool, "choices": {专家: value}}}
      - 弃权（某专家未对该维度表态）不计入 choices，也不计入分歧；
      - 至少一方表态且所有表态者取值相等 → converged=True。
    """
    all_dims: set[str] = set()
    for per_expert in stances.values():
        all_dims.update(per_expert.keys())

    result: Dict[str, Dict[str, Any]] = {}
    for did in all_dims:
        choices = {
            expert: per_expert[did]
            for expert, per_expert in stances.items()
            if did in per_expert
        }
        result[did] = {"converged": len(set(choices.values())) == 1, "choices": choices}
    return result


def weighted_majority_fallback(choices: Dict[str, str], owner: str) -> str | None:
    """对未趋同维度做加权多数裁决。

    choices: {专家名: chosen_value}
    owner: 主责专家，票权重 2，其余各 1。
    返回: 胜出的 chosen_value；平票取 owner 的选择（owner 未表态则取并列首个，确定性）。
          choices 为空时返回 None。
    """
    if not choices:
        return None
    tally: Dict[str, int] = {}
    for expert, value in choices.items():
        tally[value] = tally.get(value, 0) + (2 if expert == owner else 1)
    max_weight = max(tally.values())
    winners = [v for v, w in tally.items() if w == max_weight]
    if len(winners) == 1:
        return winners[0]
    if owner in choices and choices[owner] in winners:
        return choices[owner]
    return winners[0]


def compare_dimension_coverage(
    multi_dim_ids: List[str], single_dim_ids: List[str]
) -> Dict[str, List[str]]:
    """对比多专家与单专家发现的维度 id 集合。

    返回 {only_in_multi, only_in_single, common}，三者均为排序后的 list。
    """
    multi, single = set(multi_dim_ids), set(single_dim_ids)
    return {
        "only_in_multi": sorted(multi - single),
        "only_in_single": sorted(single - multi),
        "common": sorted(multi & single),
    }
