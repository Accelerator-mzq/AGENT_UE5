"""
Genre Pack Router Base
提供最小路由结果结构与激活匹配逻辑。
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_router_result(
    matched: bool,
    confidence: float,
    matched_feature_tags: List[str],
    reasons: List[str],
    activated_pack_ids: List[str],
) -> Dict[str, Any]:
    """构造统一 router 输出结构。"""
    return {
        "matched": bool(matched),
        "confidence": float(confidence),
        "matched_feature_tags": list(matched_feature_tags),
        "reasons": list(reasons),
        "activated_pack_ids": list(activated_pack_ids),
    }


def match_activation(design_input: Dict[str, Any], activation: Dict[str, Any], pack_id: str) -> Dict[str, Any]:
    """根据关键词和 feature_tags 计算 pack 是否匹配。"""
    raw_content = str(design_input.get("raw_content", "")).lower()
    feature_tags = [str(tag).lower() for tag in design_input.get("feature_tags", [])]
    game_type = str(design_input.get("game_type", "")).lower()
    keywords = [str(keyword).lower() for keyword in activation.get("keywords", [])]
    min_confidence = float(activation.get("min_confidence", 0.5))

    matched_feature_tags: List[str] = []
    reasons: List[str] = []
    score = 0.0

    if game_type and game_type in pack_id.lower():
        score += 0.5
        reasons.append(f"game_type={game_type} 与 pack_id 匹配")

    for keyword in keywords:
        if keyword in raw_content or keyword in feature_tags:
            matched_feature_tags.append(keyword)

    if keywords:
        score += min(0.5, len(set(matched_feature_tags)) / max(len(keywords), 1))
    elif game_type:
        score += 0.25

    matched = score >= min_confidence or (game_type and game_type in pack_id.lower())
    if matched_feature_tags:
        reasons.append(f"命中激活关键词: {sorted(set(matched_feature_tags))}")
    if not reasons:
        reasons.append("未命中特定关键词，使用默认路由判断")

    return build_router_result(
        matched=matched,
        confidence=min(1.0, score),
        matched_feature_tags=sorted(set(matched_feature_tags)),
        reasons=reasons,
        activated_pack_ids=[pack_id] if matched else [],
    )

