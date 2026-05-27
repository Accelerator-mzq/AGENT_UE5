# -*- coding: utf-8 -*-
"""observability 子树 smoke 测试。"""

from Plugins.AgentBridge.Compiler.observability import (
    redact_mapping,
    redact_text,
    compact_messages,
)


def test_redact_mapping_api_key() -> None:
    """sensitive key 整字段替换 + 非敏感字段保留。"""
    out = redact_mapping({"api_key": "sk-abc123def456ghi789", "model": "gpt-4o"})
    assert out["api_key"] == "***"
    assert out["model"] == "gpt-4o"


def test_redact_mapping_nested() -> None:
    """嵌套 dict 递归脱敏。"""
    out = redact_mapping({"outer": {"api_key": "sk-xxx", "x": 1}})
    assert out["outer"]["api_key"] == "***"
    assert out["outer"]["x"] == 1


def test_redact_text_bearer() -> None:
    """文本中 Bearer + JWT-like token 被正则替换。"""
    out = redact_text("Header: Bearer abc.def.ghi")
    assert "Bearer" not in out  # 整个 Bearer xxx 模式被替换为 ***
    assert "abc.def.ghi" not in out
    assert "***" in out


def test_compact_messages_short_noop() -> None:
    """短消息不触发裁剪。"""
    msgs = [{"role": "user", "content": "hi"}]
    out, stats = compact_messages(msgs, max_tokens=1000)
    assert out == msgs
    assert stats["dropped_count"] == 0


def test_compact_messages_long_drops_middle() -> None:
    """超长消息触发裁剪 — 保留 first system + last N turns。"""
    msgs = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1" * 5000},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "tail"},
    ]
    out, stats = compact_messages(msgs, max_tokens=50, keep_tail_turns=2)
    # 保留 first system + last 2 turn
    assert any(m["role"] == "system" for m in out)
    assert out[-1]["content"] == "tail"
    assert stats["dropped_count"] > 0


def test_redact_mapping_list_of_str_redacts() -> None:
    """list-of-str 容器中的 Bearer/sk- token 也必须脱敏(Important fix)。"""
    out = redact_mapping({
        "logs": [
            "Header: Bearer abc.def.ghi",
            "Plain log entry",
            "sk-1234567890abcdefghij",
        ],
    })
    assert "Bearer" not in out["logs"][0]
    assert "abc.def.ghi" not in out["logs"][0]
    assert out["logs"][1] == "Plain log entry"  # 非敏感字符串原样保留
    assert "sk-1234567890" not in out["logs"][2]
    assert "***" in out["logs"][2]


def test_compact_messages_over_budget_flag() -> None:
    """system 本身超 max_tokens 时 stats['over_budget'] 必须为 True。"""
    huge_system = "x" * 10000  # 估算 ~2500 token,远超 max_tokens=10
    msgs = [
        {"role": "system", "content": huge_system},
        {"role": "user", "content": "u"},
    ]
    out, stats = compact_messages(msgs, max_tokens=10, keep_tail_turns=1)
    assert stats["over_budget"] is True
    assert stats["kept_tokens_estimate"] > 10
