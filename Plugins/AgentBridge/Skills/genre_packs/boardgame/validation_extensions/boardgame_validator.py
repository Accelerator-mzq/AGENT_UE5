"""
Boardgame Validator
输出 boardgame playable runtime 的最小验证描述。
"""

from __future__ import annotations

from typing import Any, Dict, List


def build_validation_markers(compilation_state: Dict[str, Any]) -> Dict[str, Any]:
    """生成可写入 validation_spec 的最小检查描述。"""
    return {
        "required_checks": [
            "place_piece_on_empty_cell",
            "reject_move_on_occupied_cell",
            "alternate_turn_after_valid_move",
            "detect_win_row_or_column_or_diagonal",
            "detect_draw_when_board_full",
        ],
        "runtime_smoke_checks": [
            "boardgame-turn-smoke-check",
            "boardgame-decision-ui-smoke-check",
            "boardgame-core-loop-closure-check",
        ],
        "validation_markers": [
            {
                "check_id": "place_piece_on_empty_cell",
                "expected": "success",
            },
            {
                "check_id": "reject_move_on_occupied_cell",
                "expected": "blocked",
            },
            {
                "check_id": "detect_win_row_or_column_or_diagonal",
                "expected": "terminal_result",
            },
        ],
    }

