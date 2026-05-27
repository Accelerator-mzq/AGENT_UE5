# -*- coding: utf-8 -*-
"""Secret redaction — API key / Bearer token / 各类 credential 字段脱敏。

落盘 evidence 前必经此层,防止 API key / api_base 等敏感字段落到 git-tracked 文件。
"""

from __future__ import annotations

import re
from typing import Any

# 敏感字段名集合 — 大小写敏感(同时列入常见两种写法)
SENSITIVE_KEYS = {
    "api_key", "api-key", "apikey",
    "Authorization", "authorization",
    "x-api-key", "X-Api-Key",
    "token", "access_token", "refresh_token",
    "secret", "password",
}

# 敏感值正则 — OpenAI sk- 风格 / Bearer 头 / JWT 三段式
SENSITIVE_VALUE_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._\-+/=]+"),
    re.compile(r"[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{32,}"),  # JWT
]

REDACTED_MARK = "***"


def redact_mapping(d: dict[str, Any]) -> dict[str, Any]:
    """递归脱敏 dict 中的敏感字段。

    规则:
    - key 命中 SENSITIVE_KEYS → value 替换为 ``***``
    - value 为 dict → 递归
    - value 为 list → 元素若是 dict 则递归
    - value 为 str → 走 redact_text(扫敏感正则)
    """
    out: dict[str, Any] = {}
    for k, v in (d or {}).items():
        if k in SENSITIVE_KEYS:
            out[k] = REDACTED_MARK
        elif isinstance(v, dict):
            out[k] = redact_mapping(v)
        elif isinstance(v, list):
            out[k] = [redact_mapping(it) if isinstance(it, dict) else it for it in v]
        elif isinstance(v, str):
            out[k] = redact_text(v)
        else:
            out[k] = v
    return out


def redact_text(s: str) -> str:
    """脱敏字符串中的 API key / Bearer token / JWT 模式。"""
    if not isinstance(s, str):
        return s
    out = s
    for pat in SENSITIVE_VALUE_PATTERNS:
        out = pat.sub(REDACTED_MARK, out)
    return out
