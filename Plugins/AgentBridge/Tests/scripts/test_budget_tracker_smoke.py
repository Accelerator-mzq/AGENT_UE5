"""BudgetTracker observe-only smoke 测试。"""

import json
import math
from pathlib import Path

from Plugins.AgentBridge.Compiler.runtime import BudgetTracker


def test_budget_tracker_observe_only_no_block() -> None:
    """observe_only=True 时 would_exceed_after 永远 False,即便已超 cap。"""
    bt = BudgetTracker(observe_only=True, cost_cap_usd=0.01)
    bt.record(dimension_id="d1", model="m", cost_usd=100.0)
    assert bt.would_exceed_after(0.0) is False


def test_budget_tracker_record_per_dim() -> None:
    """record 累计 per-dimension / per-model usage + cost。"""
    bt = BudgetTracker()
    bt.record(dimension_id="d1", model="m", cost_usd=0.5, usage={"prompt": 100, "completion": 50, "total": 150})
    bt.record(dimension_id="d1", model="m", cost_usd=0.3, usage={"prompt": 50, "completion": 30, "total": 80})
    bt.record(dimension_id="d2", model="m", cost_usd=0.2, usage={"prompt": 80, "completion": 20, "total": 100})

    s = bt.spend
    assert s.call_count == 3
    assert math.isclose(s.by_dimension["d1"], 0.8, rel_tol=1e-9)
    assert math.isclose(s.by_dimension["d2"], 0.2, rel_tol=1e-9)
    assert s.total_prompt_tokens == 230
    assert s.total_tokens == 330


def test_budget_tracker_dump_evidence(tmp_path: Path) -> None:
    """dump_evidence 落盘 JSON 内容正确。"""
    bt = BudgetTracker()
    bt.record(dimension_id="d1", model="m", cost_usd=0.5, usage={"prompt": 100, "completion": 50, "total": 150})
    target = tmp_path / "runs" / "run-XYZ" / "llm_usage.json"
    bt.dump_evidence(target)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload["observe_only"] is True
    assert math.isclose(payload["spend"]["total_usd"], 0.5, rel_tol=1e-9)
    assert math.isclose(payload["spend"]["by_dimension"]["d1"], 0.5, rel_tol=1e-9)


def test_budget_tracker_no_usage_recorded() -> None:
    """record 不带 usage 时,token 字段不更新,但 cost + call_count 仍累计。"""
    bt = BudgetTracker()
    bt.record(dimension_id="d1", model="m", cost_usd=0.5)
    assert bt.spend.total_prompt_tokens == 0
    assert bt.spend.total_tokens == 0
    assert math.isclose(bt.spend.total_usd, 0.5)
    assert bt.spend.call_count == 1


def test_budget_tracker_hard_limit_mode_blocks() -> None:
    """非 observe_only 模式 + cap 设置 + 超 cap 时 would_exceed_after 返 True。"""
    bt = BudgetTracker(observe_only=False, cost_cap_usd=1.0)
    bt.record(dimension_id="d1", model="m", cost_usd=0.5)
    assert bt.would_exceed_after(0.4) is False    # 0.5 + 0.4 = 0.9 < 1.0
    assert bt.would_exceed_after(0.6) is True     # 0.5 + 0.6 = 1.1 > 1.0
