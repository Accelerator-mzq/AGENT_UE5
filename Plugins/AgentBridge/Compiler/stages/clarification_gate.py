"""
Phase 11 Clarification Gate stage.

职责：
  - 读取 Root Skill Contract 中的 clarification_markers、variant_fields 与 baseline 信息
  - 对缺失、含糊、冲突或高风险项做四档决策
  - 生成 clarification_gate_report.json，并把 provisional 传播契约显式写给下游
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


DECISION_ACCEPT_AS_EXPLICIT = "accept_as_explicit"
DECISION_ACCEPT_WITH_SAFE_DEFAULT = "accept_with_safe_default"
DECISION_SEND_TO_DISCOVERY = "send_to_design_space_discovery"
DECISION_CLARIFICATION_REQUIRED = "clarification_required"

RISK_LOW = "low"
RISK_MEDIUM = "medium"
RISK_HIGH = "high"
RISK_CRITICAL = "critical"


def _find_marker(root_skill_contract: Dict[str, Any], item_id: str) -> Dict[str, Any]:
    """按 item_id 查找 Root Skill Contract 内的 clarification marker。"""
    for marker in root_skill_contract.get("clarification_markers", []):
        if marker.get("item_id") == item_id:
            return marker
    return {}


def _has_variant(root_skill_contract: Dict[str, Any], field_path: str) -> bool:
    """检查某个 variant field 是否存在。"""
    variant_fields = root_skill_contract.get("variant_fields", {})
    return field_path in variant_fields


def _has_baseline_capability(root_skill_contract: Dict[str, Any], capability_id: str) -> bool:
    """检查某个 baseline capability 是否启用。"""
    for capability in root_skill_contract.get("baseline_capabilities", []):
        if capability.get("capability_id") == capability_id:
            return True
    return False


def _build_item(
    item_id: str,
    topic: str,
    decision: str,
    risk_level: str,
    *,
    impact: str = "",
    default_value: Any | None = None,
    provisional_default: Any | None = None,
    provisional: bool | None = None,
    provisional_warning: bool | None = None,
    inference_basis: str = "",
    reason: str = "",
    confidence: float | None = None,
    blocking: bool | None = None,
) -> Dict[str, Any]:
    """构造单个 Clarification Gate item。"""
    item: Dict[str, Any] = {
        "item_id": item_id,
        "topic": topic,
        "decision": decision,
        "risk_level": risk_level,
    }
    if impact:
        item["impact"] = impact
    if default_value is not None:
        item["default_value"] = default_value
    if provisional_default is not None:
        item["provisional_default"] = provisional_default
    if provisional is not None:
        item["provisional"] = provisional
    if provisional_warning is not None:
        item["provisional_warning"] = provisional_warning
    if inference_basis:
        item["inference_basis"] = inference_basis
    if reason:
        item["reason"] = reason
    if confidence is not None:
        item["confidence"] = confidence
    if blocking is not None:
        item["blocking"] = blocking
    return item


def _build_marker_items(root_skill_contract: Dict[str, Any], fast_mode: bool) -> List[Dict[str, Any]]:
    """把 Root Skill Contract 中的 marker 转成 Clarification Gate item。"""
    items: List[Dict[str, Any]] = []
    handled_item_ids: set[str] = set()

    max_length_marker = _find_marker(root_skill_contract, "cg-max-game-length")
    if max_length_marker:
        handled_item_ids.add("cg-max-game-length")
        items.append(
            _build_item(
                item_id="cg-max-game-length",
                topic="最大游戏时长/僵局处理",
                decision=DECISION_CLARIFICATION_REQUIRED,
                risk_level=max_length_marker.get("risk_level", RISK_HIGH),
                impact="若无人破产，单局可能无限持续，直接影响胜负收敛与可玩闭环验收。",
                provisional_default="200 回合上限；若到达上限，则按资金最高者获胜。",
                provisional=True,
                inference_basis="GDD 只给出 20-40 分钟目标时长，未定义硬性僵局收敛机制。",
                reason=max_length_marker.get("reason", "最大游戏时长未明确。"),
                confidence=0.55,
            )
        )

    platform_marker = _find_marker(root_skill_contract, "cg-platform-persistence")
    if platform_marker:
        handled_item_ids.add("cg-platform-persistence")
        items.append(
            _build_item(
                item_id="cg-platform-persistence",
                topic="设置持久化策略",
                decision=DECISION_ACCEPT_WITH_SAFE_DEFAULT,
                risk_level=platform_marker.get("risk_level", RISK_MEDIUM),
                impact="影响设置页 Apply/Back 的保存语义，以及平台基础能力的最小实现边界。",
                default_value=platform_marker.get("provisional_default", "session_only"),
                provisional=False,
                provisional_warning=fast_mode,
                inference_basis="Phase 1 先保证设置页可用；未锁定持久化时采用 session_only 更保守。",
                reason=platform_marker.get("reason", "持久化策略未明确。"),
                confidence=0.82,
            )
        )

    # 未知 marker 走通用规则，确保后续项目和新增 marker 也能得到正确的风险处理。
    for marker in root_skill_contract.get("clarification_markers", []):
        item_id = marker.get("item_id", "")
        if not item_id or item_id in handled_item_ids:
            continue

        decision = marker.get("suggested_decision", DECISION_CLARIFICATION_REQUIRED)
        risk_level = marker.get("risk_level", RISK_MEDIUM)

        # high / critical 不能被自动默认；critical 同时进入 blocker 列表。
        if risk_level in {RISK_HIGH, RISK_CRITICAL} and decision == DECISION_ACCEPT_WITH_SAFE_DEFAULT:
            decision = DECISION_CLARIFICATION_REQUIRED

        default_value = marker.get("default_value")
        provisional_default = marker.get("provisional_default")
        provisional = decision == DECISION_CLARIFICATION_REQUIRED and risk_level != RISK_CRITICAL and provisional_default is not None
        blocking = risk_level == RISK_CRITICAL
        topic = marker.get("topic") or marker.get("field_path") or item_id

        if decision == DECISION_ACCEPT_WITH_SAFE_DEFAULT and default_value is None:
            default_value = provisional_default

        items.append(
            _build_item(
                item_id=item_id,
                topic=topic,
                decision=decision,
                risk_level=risk_level,
                impact=marker.get("impact", ""),
                default_value=default_value,
                provisional_default=provisional_default if decision == DECISION_CLARIFICATION_REQUIRED else None,
                provisional=provisional,
                provisional_warning=fast_mode and risk_level == RISK_MEDIUM and decision == DECISION_ACCEPT_WITH_SAFE_DEFAULT,
                inference_basis=marker.get("inference_basis", ""),
                reason=marker.get("reason", ""),
                confidence=marker.get("confidence"),
                blocking=blocking if blocking else None,
            )
        )

    return items


def _build_heuristic_items(root_skill_contract: Dict[str, Any]) -> List[Dict[str, Any]]:
    """补充 Monopoly GDD 里典型但未被 marker 单独列出的 Clarification Gate 项。"""
    items: List[Dict[str, Any]] = []

    phase_scope = root_skill_contract.get("phase_scope", {})
    out_of_scope = phase_scope.get("out_of_scope", [])
    if "full card events for Chance and Community" in out_of_scope:
        items.append(
            _build_item(
                item_id="cg-card-events-phase1",
                topic="Chance / Community 在 Phase 1 的行为",
                decision=DECISION_ACCEPT_AS_EXPLICIT,
                risk_level=RISK_LOW,
                impact="决定卡牌格是否进入当前阶段实现范围。",
                default_value="踩上去无事发生，不触发卡牌事件。",
                inference_basis="GDD 2.2、2.3 明确写明 Phase 1 留空，不触发事件。",
                reason="这是 GDD 已明确锁定的显式规则，不需要追问。",
                confidence=0.98,
            )
        )

    if _has_variant(root_skill_contract, "hud.layout_style"):
        items.append(
            _build_item(
                item_id="cg-hud-layout-style",
                topic="HUD 布局方式",
                decision=DECISION_SEND_TO_DISCOVERY,
                risk_level=RISK_LOW,
                impact="影响 HUD 与棋盘的可读性，但不改变规则语义。",
                reason="GDD 只锁定 HUD 必须显示的信息，未锁定布局；属于 realization-level 设计空间。",
                confidence=0.91,
            )
        )

    if _has_variant(root_skill_contract, "player_token.visual_style"):
        items.append(
            _build_item(
                item_id="cg-player-token-visual-style",
                topic="玩家棋子视觉样式",
                decision=DECISION_ACCEPT_WITH_SAFE_DEFAULT,
                risk_level=RISK_LOW,
                impact="影响可辨识度与原型观感，但不改变棋盘规则。",
                default_value="简洁彩色几何棋子（圆柱体或锥体）",
                inference_basis="GDD Part B 已建议 Phase 1 使用简单几何体作为棋子模型。",
                reason="在玩法验证阶段，优先保证可区分与实现成本可控。",
                confidence=0.9,
            )
        )

    if _has_variant(root_skill_contract, "dice.roll_feedback"):
        items.append(
            _build_item(
                item_id="cg-dice-roll-feedback",
                topic="骰子表现与反馈节奏",
                decision=DECISION_SEND_TO_DISCOVERY,
                risk_level=RISK_LOW,
                impact="影响回合节奏与反馈品质，但不改变 2D6 的规则约束。",
                reason="GDD 锁定了 2D6 规则，没有锁定表现方式，适合放入设计空间探索。",
                confidence=0.88,
            )
        )

    if _has_baseline_capability(root_skill_contract, "baseline-platform-foundation"):
        items.append(
            _build_item(
                item_id="cg-platform-foundation-boundary",
                topic="平台基础能力边界",
                decision=DECISION_CLARIFICATION_REQUIRED,
                risk_level=RISK_HIGH,
                impact="影响窗口模式、分辨率、退出处理与设置保存的最终交付边界。",
                provisional_default="桌面端本地运行；支持窗口模式、分辨率切换，但设置仅本次会话生效。",
                provisional=True,
                inference_basis="Universal Baseline 要求平台基础能力存在，但 GDD 未明确最终平台和持久化边界。",
                reason="该项会影响平台配置与设置行为，应保留为 clarifications。",
                confidence=0.6,
            )
        )

    return items


def _build_summary(items: List[Dict[str, Any]]) -> Dict[str, int]:
    """按决策类型汇总 item 数量。"""
    summary = {
        DECISION_ACCEPT_AS_EXPLICIT: 0,
        DECISION_ACCEPT_WITH_SAFE_DEFAULT: 0,
        DECISION_SEND_TO_DISCOVERY: 0,
        DECISION_CLARIFICATION_REQUIRED: 0,
    }
    for item in items:
        decision = item.get("decision")
        if decision in summary:
            summary[decision] += 1
    return summary


def _build_provisional_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取需要在后续阶段持续传播的 provisional 项。"""
    downstream_impacts = [
        "design_decision_log[].provisional = true",
        "build_steps[].execution_hints.contains_provisional = true",
        "reviewed_handoff_v3.provisional_items[] includes item",
    ]
    provisional_items: List[Dict[str, Any]] = []
    for item in items:
        if not item.get("provisional"):
            continue
        provisional_items.append(
            {
                "item_id": item.get("item_id", ""),
                "topic": item.get("topic", ""),
                "provisional_value": item.get("provisional_default", item.get("default_value")),
                "source_decision": item.get("decision", ""),
                "risk_level": item.get("risk_level", ""),
                "downstream_impacts": downstream_impacts,
            }
        )
    return provisional_items


def _build_blocking_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """提取 critical blocker。"""
    blocking_items: List[Dict[str, Any]] = []
    for item in items:
        if item.get("risk_level") != RISK_CRITICAL:
            continue
        blocking_items.append(
            {
                "item_id": item.get("item_id", ""),
                "topic": item.get("topic", ""),
                "blocking_reason": item.get("reason") or item.get("impact") or "critical clarification required",
            }
        )
    return blocking_items


def _downstream_propagation_contract() -> Dict[str, str]:
    """定义 provisional 在后续阶段的标准传播字段。"""
    return {
        "skill_fragment_provisional_flag": "design_decision_log[].provisional = true",
        "build_ir_provisional_flag": "build_steps[].execution_hints.contains_provisional = true",
        "handoff_provisional_summary": "reviewed_handoff_v3.provisional_items[]",
    }


def create_clarification_gate_report(
    root_skill_contract: Dict[str, Any],
    fast_mode: bool = False,
    run_id: str | None = None,
) -> Dict[str, Any]:
    """生成 Clarification Gate Report。"""
    generated_at = datetime.now(timezone.utc).isoformat()
    items = _build_marker_items(root_skill_contract, fast_mode)
    items.extend(_build_heuristic_items(root_skill_contract))

    # 统一去重，避免 marker 与启发式规则重复产出同一 item_id。
    deduplicated_items: List[Dict[str, Any]] = []
    seen_item_ids: set[str] = set()
    for item in items:
        item_id = item.get("item_id", "")
        if item_id in seen_item_ids:
            continue
        seen_item_ids.add(item_id)
        deduplicated_items.append(item)

    provisional_items = _build_provisional_items(deduplicated_items)
    blocking_items = _build_blocking_items(deduplicated_items)
    retained_clarifications = [
        item.get("item_id", "")
        for item in deduplicated_items
        if item.get("decision") == DECISION_CLARIFICATION_REQUIRED
    ]

    return {
        "gate_version": "1.0",
        "source_contract_id": root_skill_contract.get("contract_id", ""),
        "items": deduplicated_items,
        "provisional_items": provisional_items,
        "blocking_items": blocking_items,
        "fast_mode": fast_mode,
        "clarification_gate_policy": (
            "auto_default_low_medium_only" if fast_mode else "formal_mode_keep_high_risk_questions"
        ),
        "retained_clarifications": retained_clarifications,
        "items_by_decision_summary": _build_summary(deduplicated_items),
        "downstream_propagation_contract": _downstream_propagation_contract(),
        "metadata": {
            "generated_at": generated_at,
            "generator": "AgentBridge.Compiler.ClarificationGate.v1",
            "source_run_id": run_id,
            "blocked_by_critical": bool(blocking_items),
        },
    }


def save_clarification_gate_report(report: Dict[str, Any], output_path: str | Path) -> str:
    """保存 Clarification Gate Report JSON。"""
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, ensure_ascii=False, indent=2)
    return str(target_path)
