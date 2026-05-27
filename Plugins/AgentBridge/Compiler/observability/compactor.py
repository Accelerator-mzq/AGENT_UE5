# -*- coding: utf-8 -*-
"""消息历史 auto-compact — 4 char/token 估算,保留 first system + last N turns。"""

from __future__ import annotations

from typing import Any

DEFAULT_KEEP_TAIL = 4
CHARS_PER_TOKEN = 4


def _estimate_tokens(msg: dict[str, Any]) -> int:
    """粗估单条 message 的 token 数(4 char ≈ 1 token)。"""
    content = msg.get("content", "")
    if isinstance(content, str):
        return max(1, len(content) // CHARS_PER_TOKEN)
    if isinstance(content, list):
        total = 0
        for block in content:
            if isinstance(block, dict):
                t = block.get("text", "")
                total += max(1, len(t) // CHARS_PER_TOKEN)
        return total
    return 1


def compact_messages(
    messages: list[dict[str, Any]],
    *,
    max_tokens: int,
    keep_tail_turns: int = DEFAULT_KEEP_TAIL,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """裁剪消息历史到 ≤ max_tokens(粗估),保留 first system + last keep_tail turns。

    返回 (compacted_messages, stats),stats 含 dropped_count / kept_tokens_estimate。
    """
    if not messages or max_tokens <= 0:
        return list(messages), {"dropped_count": 0, "kept_tokens_estimate": 0}

    total = sum(_estimate_tokens(m) for m in messages)
    if total <= max_tokens:
        return list(messages), {"dropped_count": 0, "kept_tokens_estimate": total}

    # 保留 first system + last keep_tail turns
    system_msgs = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]

    keep_head = system_msgs[:1] if system_msgs else []
    keep_tail = non_system[-keep_tail_turns:] if keep_tail_turns > 0 else []

    compacted = keep_head + keep_tail
    kept = sum(_estimate_tokens(m) for m in compacted)
    dropped = len(messages) - len(compacted)
    return compacted, {"dropped_count": dropped, "kept_tokens_estimate": kept}
