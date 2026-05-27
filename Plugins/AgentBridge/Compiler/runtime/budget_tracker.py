"""Per-Run cost / usage 累计 — 本期 observe-only,只落盘不阻断 run。

中期开"软阈值"模式时,可在 record() / would_exceed_after() 上加阻断逻辑,
内核数据结构保持兼容。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any


@dataclass
class BudgetSpend:
    # Per-Run 累计花费与 token 用量快照
    total_usd: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    by_dimension: dict[str, float] = field(default_factory=dict)
    by_model: dict[str, float] = field(default_factory=dict)
    by_dimension_tokens: dict[str, dict[str, int]] = field(default_factory=dict)
    call_count: int = 0


class BudgetTracker:
    """observe-only 模式:不抛 BudgetExceeded,只累计 + 落盘。"""

    def __init__(self, *, observe_only: bool = True, cost_cap_usd: float | None = None) -> None:
        # observe_only=True 时不阻断,仅记录;cost_cap_usd 留给中期 hard-limit 模式使用
        self._observe_only = observe_only
        self._cost_cap_usd = cost_cap_usd
        self._spend = BudgetSpend()

    @property
    def spend(self) -> BudgetSpend:
        return self._spend

    @property
    def cap_usd(self) -> float | None:
        return self._cost_cap_usd

    @property
    def observe_only(self) -> bool:
        return self._observe_only

    def record(
        self,
        *,
        dimension_id: str,
        model: str,
        cost_usd: float = 0.0,
        usage: dict[str, int] | None = None,
    ) -> None:
        """累计一次调用的 cost + usage(token 数)。"""
        # 1) 累计总花费 + per-dimension / per-model 花费
        self._spend.total_usd += cost_usd
        self._spend.by_dimension[dimension_id] = (
            self._spend.by_dimension.get(dimension_id, 0.0) + cost_usd
        )
        self._spend.by_model[model] = self._spend.by_model.get(model, 0.0) + cost_usd

        # 2) 如带 usage,累计 token 用量(prompt / completion / total)
        if usage:
            prompt = int(usage.get("prompt", 0))
            completion = int(usage.get("completion", 0))
            total = int(usage.get("total", prompt + completion))

            self._spend.total_prompt_tokens += prompt
            self._spend.total_completion_tokens += completion
            self._spend.total_tokens += total

            dim_buckets = self._spend.by_dimension_tokens.setdefault(
                dimension_id, {"prompt": 0, "completion": 0, "total": 0},
            )
            dim_buckets["prompt"] += prompt
            dim_buckets["completion"] += completion
            dim_buckets["total"] += total

        # 3) 调用次数 +1
        self._spend.call_count += 1

    def would_exceed_after(self, extra_usd: float) -> bool:
        """observe-only 模式恒返 False;非 observe-only 才真比较 cap。"""
        if self._observe_only:
            return False
        if self._cost_cap_usd is None:
            return False
        return self._spend.total_usd + extra_usd > self._cost_cap_usd

    def dump_evidence(self, path: str | Path) -> None:
        """落盘到 ProjectState/runs/{run_id}/llm_usage.json。"""
        # 父目录不存在则递归创建
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "observe_only": self._observe_only,
            "cost_cap_usd": self._cost_cap_usd,
            "over_budget": (
                False if self._observe_only or self._cost_cap_usd is None
                else self._spend.total_usd > self._cost_cap_usd
            ),
            "spend": asdict(self._spend),
        }
        p.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
