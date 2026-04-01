"""
Boardgame Delta Policy
输出 boardgame 类型包的 Brownfield 策略偏好。
"""

from __future__ import annotations

from typing import Any, Dict


def build_delta_policy(design_input: Dict[str, Any], routing_context: Dict[str, Any]) -> Dict[str, Any]:
    """生成 boardgame 的 delta policy 描述。"""
    return {
        "preferred_delta_modes": ["append_actor", "no_change", "patch_existing_content"],
        "regression_focus": [
            "existing_actor_presence",
            "boardgame-turn-smoke-check",
            "boardgame-decision-ui-smoke-check",
            "boardgame-core-loop-closure-check",
        ],
        "high_risk_breakpoints": [
            "turn_flow_changed",
            "decision_ui_changed",
            "runtime_wiring_changed",
        ],
        "preferred_recovery_modes": ["manual_review", "block_handoff"],
        "notes": [
            f"game_type={design_input.get('game_type', 'unknown')}",
            f"mode={routing_context.get('mode', 'unknown')}",
        ],
    }

