# -*- coding: utf-8 -*-
"""Phase 12 L2-A:observability 子树单元测试(spec §6.2 覆盖度目标 ≥ 85%)。

由 Phase 0 的 test_observability_smoke.py 重命名而来,Phase 12 T14 在末尾
Section B 增补 secrets / compactor 边界 case。
"""

from Plugins.AgentBridge.Compiler.observability import (
    redact_mapping,
    redact_text,
    compact_messages,
)

# ============================================================================
# Section A: Phase 0 原 smoke case
# ============================================================================


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


# ============================================================================
# Section B: Phase 12 T14 新增 case
# ============================================================================

def test_compact_messages_keeps_first_system_under_budget() -> None:
    """超 budget 时 first system 必保留(单 first system + tail)。"""
    msgs = [
        {"role": "system", "content": "sysA"},
        {"role": "system", "content": "sysB"},  # 第二 system 应被裁
        {"role": "user", "content": "u" * 5000},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
        {"role": "assistant", "content": "tail"},
    ]
    out, stats = compact_messages(msgs, max_tokens=20, keep_tail_turns=2)
    # 保留的 system 只有 first 一条
    system_kept = [m for m in out if m.get("role") == "system"]
    assert len(system_kept) == 1
    assert system_kept[0]["content"] == "sysA"
    # 尾部最后一条必保留
    assert out[-1]["content"] == "tail"
    assert stats["dropped_count"] > 0


def test_compact_messages_empty_input_noop() -> None:
    """空 messages 时 compactor 不抛,直接返空 list + 默认 stats。"""
    out, stats = compact_messages([], max_tokens=100)
    assert out == []
    assert stats["dropped_count"] == 0
    assert stats["over_budget"] is False


def test_compact_messages_max_tokens_zero_returns_original() -> None:
    """max_tokens ≤ 0 时是 invalid 输入,compactor 应 short-circuit 返回原 messages。"""
    msgs = [{"role": "user", "content": "x"}]
    out, stats = compact_messages(msgs, max_tokens=0)
    assert out == msgs
    assert stats["dropped_count"] == 0


def test_redact_text_multiple_sk_keys_in_one_string() -> None:
    """同一字符串内多个 sk-... token 都应被脱敏。"""
    raw = "log A: sk-aaaaaaaaaaaaaaaaaaaa key1; log B: sk-bbbbbbbbbbbbbbbbbbbb key2"
    out = redact_text(raw)
    assert "sk-aaaa" not in out
    assert "sk-bbbb" not in out
    assert out.count("***") >= 2


def test_redact_mapping_authorization_header_redacted() -> None:
    """Authorization 字段名整字段替换(典型 HTTP header 上下文)。"""
    out = redact_mapping({"Authorization": "Bearer abc.def.ghi", "x-trace-id": "t-001"})
    assert out["Authorization"] == "***"
    assert out["x-trace-id"] == "t-001"


def test_redact_mapping_non_string_values_passthrough() -> None:
    """int / bool / None 等非 str/dict/list 值不被改写,但 sensitive key 仍替换。"""
    out = redact_mapping({"retries": 3, "enabled": True, "extra": None, "secret": 42})
    assert out["retries"] == 3
    assert out["enabled"] is True
    assert out["extra"] is None
    # secret 是 SENSITIVE_KEYS,即使 value 是 int 也整字段替换为 ***
    assert out["secret"] == "***"


def test_redact_text_non_str_passthrough() -> None:
    """redact_text 接到非 str 直接 passthrough(防御性,实际只该收到 str)。"""
    assert redact_text(123) == 123  # type: ignore[arg-type]
    assert redact_text(None) is None  # type: ignore[arg-type]
