"""HUD 多专家协商试点 —— 纯逻辑层。

不依赖 LLM / 网络，可离线单元测试。
LLM 调用与编排在 demo_hud_multiexpert.py。
"""
from __future__ import annotations

from typing import Any


def merge_discovered_dimensions(
    expert_dim_lists: list[tuple[str, list[dict[str, Any]]]],
) -> list[dict[str, Any]]:
    """合并多专家维度清单。

    expert_dim_lists: [(专家名, [维度dict,...]), ...]，维度 dict 至少含 dimension_id。
    返回: 去重后的维度列表（按首次出现顺序），每项是首现维度的副本 +
          "proposed_by": [按出现顺序提出该维度的专家名]。
    """
    merged: dict[str, dict[str, Any]] = {}
    order: list[str] = []
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


def resolve_owner(proposed_by: list[str], expert_priority: list[str]) -> str:
    """维度归属：按 expert_priority 顺序取 proposed_by 中第一个出现的专家。

    proposed_by 为空时返回 expert_priority[0] 作为兜底 owner。
    """
    for expert in expert_priority:
        if expert in proposed_by:
            return expert
    return expert_priority[0]


def detect_convergence(stances: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    """逐维度判断三方选择是否趋同。

    stances: {专家名: {dimension_id: chosen_value}}
    返回: {dimension_id: {"converged": bool, "choices": {专家: value}}}
      - 弃权（某专家未对该维度表态）不计入 choices，也不计入分歧；
      - 至少一方表态且所有表态者取值相等 → converged=True。
    """
    all_dims = sorted(
        {dim_id for per_expert in stances.values() for dim_id in per_expert}
    )
    result: dict[str, dict[str, Any]] = {}
    for did in all_dims:
        choices = {
            expert: per_expert[did]
            for expert, per_expert in stances.items()
            if did in per_expert
        }
        result[did] = {"converged": len(set(choices.values())) == 1, "choices": choices}
    return result


def weighted_majority_fallback(choices: dict[str, str], owner: str) -> str | None:
    """对未趋同维度做加权多数裁决。

    choices: {专家名: chosen_value}
    owner: 主责专家，票权重 2，其余各 1。
    返回: 胜出的 chosen_value；平票取 owner 的选择（owner 未表态则取字典序最小，确定性）。
          choices 为空时返回 None。
    """
    if not choices:
        return None
    tally: dict[str, int] = {}
    for expert, value in choices.items():
        tally[value] = tally.get(value, 0) + (2 if expert == owner else 1)
    max_weight = max(tally.values())
    winners = [v for v, w in tally.items() if w == max_weight]
    if len(winners) == 1:
        return winners[0]
    if owner in choices and choices[owner] in winners:
        return choices[owner]
    return min(winners)   # 平票且 owner 未表态 → 字典序最小，与输入顺序无关


def compare_dimension_coverage(
    multi_dim_ids: list[str], single_dim_ids: list[str]
) -> dict[str, list[str]]:
    """对比多专家与单专家发现的维度 id 集合。

    返回 {only_in_multi, only_in_single, common}，三者均为排序后的 list。
    """
    multi, single = set(multi_dim_ids), set(single_dim_ids)
    return {
        "only_in_multi": sorted(multi - single),
        "only_in_single": sorted(single - multi),
        "common": sorted(multi & single),
    }


def assemble_arbitration_result(
    merged_dims: list[dict[str, Any]],
    arbitration: dict[str, dict[str, Any]],
    stances: dict[str, dict[str, str]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """根据中立总监的裁决结果装配最终 spec。

    merged_dims: merge_discovered_dimensions 的输出（每项含 dimension_id）。
    arbitration: 总监输出 {dimension_id: {final_choice, integration_note, unresolved}}。
    stances: {专家名: {dimension_id: choice}} 三方原始立场（用于 gap 留痕）。
    返回: (selected_realization, capability_gaps)。
      - 正常 resolved：selected 取 final_choice，不进 gaps；
      - unresolved=True：selected 仍取 final_choice，该维度进 gaps（附 integration_note + 三方立场）；
      - 合并维度在 arbitration 中缺失：selected 兜底空串，进 gaps 标 arbiter_missing。
    """
    def _stances_for(did: str) -> dict[str, str]:
        # 收集所有对该维度有表态的专家立场
        return {expert: per[did] for expert, per in stances.items() if did in per}

    selected: dict[str, str] = {}
    gaps: list[dict[str, Any]] = []
    for dim in merged_dims:
        did = dim.get("dimension_id")
        if not did:
            continue
        verdict = arbitration.get(did)
        if verdict is None:
            # 该维度在裁决结果中缺失，兜底空串并记录 gap
            selected[did] = ""
            gaps.append({
                "dimension_id": did,
                "resolved_by": "arbiter_missing",
                "stances": _stances_for(did),
            })
            continue
        # 正常写入 final_choice，None 或缺失均兜底空串
        selected[did] = verdict.get("final_choice", "") or ""
        if verdict.get("unresolved"):
            # 虽有裁决但标记为未解决，进 gaps 留痕
            gaps.append({
                "dimension_id": did,
                "integration_note": verdict.get("integration_note", ""),
                "resolved_by": "arbiter_unresolved",
                "stances": _stances_for(did),
            })
    return selected, gaps
