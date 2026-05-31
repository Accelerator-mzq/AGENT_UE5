# HUD 多专家协商试点 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用独立脚本把 HUD 发散从「单专家包办」改为「UX/UI程序/美术 三专家各自发现维度 → 协商 → 收敛」，产出 HUD fragment 与单专家版对比，数据化回答「多专家是否值得推广」。

**Architecture:** 把编排逻辑拆成两层——纯逻辑层（维度合并、归属、收敛判定、加权多数兜底、覆盖对比）可离线 TDD；LLM 调用层（3 专家 prompt + 真实 API）是薄封装，作为集成步骤跑真实试点。纯逻辑不依赖 llm_client（延迟 import），单元测试在默认 Python 3.13 跑；真实试点用带 anthropic SDK 的 `C:\Python312\python.exe`。

**Tech Stack:** Python 3.x；项目自有 `llm_client.py`（minimaxi/anthropic 兼容）；house-style 测试脚本（sys.path 注入 + 手写断言 + `__main__` 运行器，非 pytest）。

参照设计：`Docs/archive/superpowers/specs/2026-05-31-hud-multiexpert-negotiation-design.md`

---

## File Structure

- **Create** `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
  - 纯逻辑模块：`merge_discovered_dimensions` / `resolve_owner` / `detect_convergence` / `weighted_majority_fallback` / `compare_dimension_coverage`。无 LLM 依赖，可离线 import。
- **Create** `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
  - 纯逻辑单元测试，house style，默认 python 可跑。
- **Create** `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py`
  - 试点主脚本：3 专家内联 prompt + LLM 调用/解析 + 协商编排（import 上面的 core）+ 落盘产物。用 Python 3.12 跑。
- **Output** `ProjectState/Reports/<date>/hud_multiexpert_fragment.json` / `hud_multiexpert_negotiation_log.json` / `hud_multiexpert_vs_single_comparison.md`

> 纯逻辑与 LLM 编排分文件：前者聚焦、可测；后者承担副作用。`AgentBridgeTests/` 为禁改区，测试落 `Tests/scripts/`。

---

## Task 1: 纯逻辑模块脚手架 + `merge_discovered_dimensions`

合并多专家维度清单，按 dimension_id 去重并记录提出者（治「单专家拍脑袋」，多视角补全）。

**Files:**
- Create: `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
- Create: `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`

- [ ] **Step 1: 写失败测试（建测试文件 + 第一个用例）**

创建 `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`：

```python
"""HUD 多专家协商 —— 纯逻辑单元测试（house style，离线可跑）。"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Tests.scripts import hud_multiexpert_core as core  # noqa: E402


def test_merge_dedup_and_records_proposers():
    """三专家维度合并：按 dimension_id 去重，proposed_by 记录提出者，保持首次出现顺序。"""
    lists = [
        ("ux-designer", [{"dimension_id": "hud.info_density", "name": "信息密度"},
                          {"dimension_id": "hud.player_display", "name": "玩家展示"}]),
        ("ui-programmer", [{"dimension_id": "hud.info_density", "name": "信息密度"},
                           {"dimension_id": "hud.refresh_rate", "name": "刷新频率"}]),
        ("art-director", [{"dimension_id": "hud.layout", "name": "布局"}]),
    ]
    merged = core.merge_discovered_dimensions(lists)
    ids = [d["dimension_id"] for d in merged]
    assert ids == ["hud.info_density", "hud.player_display", "hud.refresh_rate", "hud.layout"], ids
    by_id = {d["dimension_id"]: d for d in merged}
    assert by_id["hud.info_density"]["proposed_by"] == ["ux-designer", "ui-programmer"], by_id["hud.info_density"]
    assert by_id["hud.layout"]["proposed_by"] == ["art-director"]


ALL_TESTS = [
    test_merge_dedup_and_records_proposers,
]


def main() -> int:
    failures = []
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures.append(fn.__name__)
            print(f"FAIL {fn.__name__}: {exc!r}")
    if failures:
        print(f"\n{len(failures)} failed / {len(ALL_TESTS)} total")
        return 1
    print(f"\nAll {len(ALL_TESTS)} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: FAIL，`ModuleNotFoundError` 或 `AttributeError`（core 模块/函数不存在）

- [ ] **Step 3: 建模块并实现函数**

创建 `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`：

```python
"""HUD 多专家协商试点 —— 纯逻辑层。

不依赖 LLM / 网络，可离线单元测试。
LLM 调用与编排在 demo_hud_multiexpert.py。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple


def merge_discovered_dimensions(
    expert_dim_lists: List[Tuple[str, List[Dict[str, Any]]]],
) -> List[Dict[str, Any]]:
    """合并多专家维度清单。

    expert_dim_lists: [(专家名, [维度dict,...]), ...]，维度 dict 至少含 dimension_id。
    返回: 去重后的维度列表（按首次出现顺序），每项是首现维度的副本 +
          "proposed_by": [按出现顺序提出该维度的专家名]。
    """
    merged: Dict[str, Dict[str, Any]] = {}
    order: List[str] = []
    for expert_name, dims in expert_dim_lists:
        for dim in dims:
            did = dim.get("dimension_id")
            if not did:
                continue
            if did not in merged:
                merged[did] = {**dim, "proposed_by": [expert_name]}
                order.append(did)
            elif expert_name not in merged[did]["proposed_by"]:
                merged[did]["proposed_by"].append(expert_name)
    return [merged[d] for d in order]
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS，`All 1 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py
git commit -m "[skip-doc] feat(pilot): HUD 多专家 core - merge_discovered_dimensions + 测试"
```

---

## Task 2: `resolve_owner`

维度归属：按固定专家优先级，从 proposed_by 中取第一个作为该维度 owner（供加权多数用）。

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`

- [ ] **Step 1: 追加失败测试**

在 `ALL_TESTS` 之前追加：

```python
def test_resolve_owner_priority_and_fallback():
    """owner = proposed_by 中按 priority 顺序的第一个；空 proposed_by 取 priority[0]。"""
    priority = ["ux-designer", "ui-programmer", "art-director"]
    assert core.resolve_owner(["ui-programmer", "ux-designer"], priority) == "ux-designer"
    assert core.resolve_owner(["art-director"], priority) == "art-director"
    assert core.resolve_owner([], priority) == "ux-designer"
```

加入 `ALL_TESTS`：`test_resolve_owner_priority_and_fallback,`

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: FAIL，`AttributeError: ... has no attribute 'resolve_owner'`

- [ ] **Step 3: 实现**

在 `hud_multiexpert_core.py` 末尾追加：

```python
def resolve_owner(proposed_by: List[str], expert_priority: List[str]) -> str:
    """维度归属：按 expert_priority 顺序取 proposed_by 中第一个出现的专家。

    proposed_by 为空时返回 expert_priority[0] 作为兜底 owner。
    """
    for expert in expert_priority:
        if expert in proposed_by:
            return expert
    return expert_priority[0]
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS，`All 2 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py
git commit -m "[skip-doc] feat(pilot): HUD 多专家 core - resolve_owner + 测试"
```

---

## Task 3: `detect_convergence`

逐维度判断三方选择是否趋同（弃权不计入分歧）。

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`

- [ ] **Step 1: 追加失败测试**

在 `ALL_TESTS` 之前追加：

```python
def test_detect_convergence_agreement_and_abstain():
    """全表态者取值一致 → converged；不一致 → 否；弃权者不计入。"""
    stances = {
        "ux-designer":   {"d1": "A", "d2": "X"},
        "ui-programmer": {"d1": "A", "d2": "Y"},
        "art-director":  {"d1": "A"},  # 对 d2 弃权
    }
    res = core.detect_convergence(stances)
    assert res["d1"]["converged"] is True, res["d1"]
    assert res["d1"]["choices"] == {"ux-designer": "A", "ui-programmer": "A", "art-director": "A"}
    assert res["d2"]["converged"] is False, res["d2"]
    assert res["d2"]["choices"] == {"ux-designer": "X", "ui-programmer": "Y"}  # 弃权者不在内


def test_detect_convergence_single_voice_is_converged():
    """仅一方表态（其余弃权）视为趋同。"""
    stances = {"ux-designer": {"d3": "Z"}, "ui-programmer": {}, "art-director": {}}
    res = core.detect_convergence(stances)
    assert res["d3"]["converged"] is True, res["d3"]
```

加入 `ALL_TESTS`：`test_detect_convergence_agreement_and_abstain, test_detect_convergence_single_voice_is_converged,`

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: FAIL，`AttributeError: ... 'detect_convergence'`

- [ ] **Step 3: 实现**

在 `hud_multiexpert_core.py` 末尾追加：

```python
def detect_convergence(stances: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
    """逐维度判断三方选择是否趋同。

    stances: {专家名: {dimension_id: chosen_value}}
    返回: {dimension_id: {"converged": bool, "choices": {专家: value}}}
      - 弃权（某专家未对该维度表态）不计入 choices，也不计入分歧；
      - 至少一方表态且所有表态者取值相等 → converged=True。
    """
    all_dims: set[str] = set()
    for per_expert in stances.values():
        all_dims.update(per_expert.keys())

    result: Dict[str, Dict[str, Any]] = {}
    for did in all_dims:
        choices = {
            expert: per_expert[did]
            for expert, per_expert in stances.items()
            if did in per_expert
        }
        result[did] = {"converged": len(set(choices.values())) == 1, "choices": choices}
    return result
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS，`All 4 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py
git commit -m "[skip-doc] feat(pilot): HUD 多专家 core - detect_convergence + 测试"
```

---

## Task 4: `weighted_majority_fallback`

未趋同维度的降级裁决：主责专家票权重 2，其余各 1，平票取 owner 选择。

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`

- [ ] **Step 1: 追加失败测试**

在 `ALL_TESTS` 之前追加：

```python
def test_weighted_majority_owner_weight_and_tie():
    """owner 票权重 2 可压倒单票；普通多数胜出；空 choices 返回 None。"""
    # owner=ux 投 A(权2)，ui 投 B(权1)，art 投 B(权1) → A:2 B:2 平票 → 取 owner 的 A
    assert core.weighted_majority_fallback(
        {"ux-designer": "A", "ui-programmer": "B", "art-director": "B"}, "ux-designer") == "A"
    # 普通多数：A:1+1=2(ui,art) vs owner(ux) 投 B 权2 → A:2 B:2 平 → owner 的 B
    assert core.weighted_majority_fallback(
        {"ux-designer": "B", "ui-programmer": "A", "art-director": "A"}, "ux-designer") == "B"
    # 清晰多数：三人都投 A → A
    assert core.weighted_majority_fallback(
        {"ux-designer": "A", "ui-programmer": "A", "art-director": "A"}, "art-director") == "A"
    # 空
    assert core.weighted_majority_fallback({}, "ux-designer") is None
```

加入 `ALL_TESTS`：`test_weighted_majority_owner_weight_and_tie,`

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: FAIL，`AttributeError: ... 'weighted_majority_fallback'`

- [ ] **Step 3: 实现**

在 `hud_multiexpert_core.py` 末尾追加：

```python
def weighted_majority_fallback(choices: Dict[str, str], owner: str) -> str | None:
    """对未趋同维度做加权多数裁决。

    choices: {专家名: chosen_value}
    owner: 主责专家，票权重 2，其余各 1。
    返回: 胜出的 chosen_value；平票取 owner 的选择（owner 未表态则取并列首个，确定性）。
          choices 为空时返回 None。
    """
    if not choices:
        return None
    tally: Dict[str, int] = {}
    for expert, value in choices.items():
        tally[value] = tally.get(value, 0) + (2 if expert == owner else 1)
    max_weight = max(tally.values())
    winners = [v for v, w in tally.items() if w == max_weight]
    if len(winners) == 1:
        return winners[0]
    if owner in choices and choices[owner] in winners:
        return choices[owner]
    return winners[0]
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS，`All 5 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py
git commit -m "[skip-doc] feat(pilot): HUD 多专家 core - weighted_majority_fallback + 测试"
```

---

## Task 5: `compare_dimension_coverage`

对比多专家 vs 单专家发现的维度集合（量化「维度覆盖」判据）。

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`

- [ ] **Step 1: 追加失败测试**

在 `ALL_TESTS` 之前追加：

```python
def test_compare_dimension_coverage():
    """对比两组维度 id：分出 only_in_multi / only_in_single / common，均排序。"""
    res = core.compare_dimension_coverage(
        multi_dim_ids=["hud.layout", "hud.info_density", "hud.refresh_rate"],
        single_dim_ids=["hud.info_density", "hud.layout"],
    )
    assert res["only_in_multi"] == ["hud.refresh_rate"], res
    assert res["only_in_single"] == [], res
    assert res["common"] == ["hud.info_density", "hud.layout"], res
```

加入 `ALL_TESTS`：`test_compare_dimension_coverage,`

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: FAIL，`AttributeError: ... 'compare_dimension_coverage'`

- [ ] **Step 3: 实现**

在 `hud_multiexpert_core.py` 末尾追加：

```python
def compare_dimension_coverage(
    multi_dim_ids: List[str], single_dim_ids: List[str]
) -> Dict[str, List[str]]:
    """对比多专家与单专家发现的维度 id 集合。

    返回 {only_in_multi, only_in_single, common}，三者均为排序后的 list。
    """
    multi, single = set(multi_dim_ids), set(single_dim_ids)
    return {
        "only_in_multi": sorted(multi - single),
        "only_in_single": sorted(single - multi),
        "common": sorted(multi & single),
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS，`All 6 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py
git commit -m "[skip-doc] feat(pilot): HUD 多专家 core - compare_dimension_coverage + 测试"
```

---

## Task 6: LLM 调用层 + 3 专家 prompt + 协商编排

把纯逻辑串成真实试点脚本。本任务**不写单元测试**（含真实 LLM 副作用），但结构清晰、可被 Task 7 直接运行。

**Files:**
- Create: `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py`

- [ ] **Step 1: 写脚本主体**

创建 `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py`：

```python
"""HUD 多专家协商试点主脚本。

3 专家（UX/UI程序/美术）各自发现维度 → 立场 → 多轮协商 → 收敛/降级，
产出 HUD fragment + 协商记录 + 与单专家版对比。

须用带 anthropic SDK 的解释器运行：
  C:\\Python312\\python.exe Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Tests.scripts import hud_multiexpert_core as core  # noqa: E402

SRC_RUN = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260417-051444-a2b8"
OUT_DIR = PROJECT_ROOT / "ProjectState" / "Reports" / "2026-05-31"
MAX_ROUNDS = 2
EXPERT_PRIORITY = ["ux-designer", "ui-programmer", "art-director"]

# 3 专家 system prompt（试点内联；推广时抽出为 SkillTemplate persona）
EXPERT_PROMPTS = {
    "ux-designer": (
        "你是游戏 UX 设计师。你只从用户体验角度参与 HUD 设计："
        "信息完整性、可读性、玩家认知负担、无障碍（色盲/文字缩放）、多玩家信息对称。"
        "你不决定视觉风格细节，也不评估底层实现可行性。"
        "必须遵守给定的 GDD locked 约束，不得违反。只输出 JSON，不要解释文字。"
    ),
    "ui-programmer": (
        "你是 UI 程序员。你只从实现角度参与 HUD 设计："
        "数据绑定可行性、刷新频率/触发时机、性能、UI 绝不持有或修改 gameplay 状态（只展示）。"
        "你不决定视觉美感，也不替 UX 定义信息取舍。"
        "必须遵守给定的 GDD locked 约束。只输出 JSON，不要解释文字。"
    ),
    "art-director": (
        "你是美术总监。你只从视觉角度参与 HUD 设计："
        "布局方向、视觉主题一致性、不遮挡棋盘、Monopoly 识别度、视觉层级。"
        "你不评估实现可行性，也不替 UX 定义信息密度的功能取舍。"
        "必须遵守给定的 GDD locked 约束。只输出 JSON，不要解释文字。"
    ),
}


def _load(name: str) -> dict:
    return json.loads((SRC_RUN / name).read_text(encoding="utf-8"))


def _parse_json(raw: str) -> dict:
    """从 LLM 文本中提取 JSON object（去除可能的 ``` 代码围栏）。"""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1] if "```" in text[3:] else text
        text = text.lstrip("json").strip().strip("`").strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return {}
    return json.loads(text[start:end + 1])


def _call(client, system_prompt: str, user_prompt: str) -> dict:
    raw = client.call([
        {"role": "system", "content": system_prompt + "\n只返回一个合法 JSON object。"},
        {"role": "user", "content": user_prompt},
    ])
    try:
        return _parse_json(raw)
    except Exception:  # noqa: BLE001
        return {"parse_error": True, "raw": raw}


def _context_block(contract: dict) -> str:
    """给所有专家的共享上下文：GDD locked 约束 + HUD 必需字段。"""
    locked = contract.get("constraint_fields", {}).get("ui.required_hud_fields", {}).get("value", [])
    return (
        "## GDD 锁定约束（不可违反）\n"
        f"- HUD 必须显示字段: {locked}\n"
        "- 28 个格子在主相机下完整可见\n"
        "- HUD 不得遮挡购买/租金/监狱弹窗\n"
        "- 2-4 名玩家本地多人\n"
    )


def discover(client, expert: str, ctx: str) -> list:
    out = _call(client, EXPERT_PROMPTS[expert],
                ctx + "\n## 任务\n从你的专业视角，列出 HUD 的可设计维度。"
                "输出 JSON: {\"dimensions\":[{\"dimension_id\":\"hud.xxx\",\"name\":\"..\",\"description\":\"..\"}]}")
    return out.get("dimensions", [])


def stance(client, expert: str, ctx: str, dims: list) -> dict:
    dim_ids = [d["dimension_id"] for d in dims]
    out = _call(client, EXPERT_PROMPTS[expert],
                ctx + f"\n## 维度全集\n{dim_ids}\n## 任务\n对每个维度给出你主张的选择与理由。"
                "输出 JSON: {\"stance\":{\"hud.xxx\":{\"choice\":\"..\",\"reason\":\"..\"}}}")
    return {k: v.get("choice", "") for k, v in out.get("stance", {}).items() if isinstance(v, dict)}


def renegotiate(client, expert: str, ctx: str, all_stances: dict, conflicts: list) -> dict:
    out = _call(client, EXPERT_PROMPTS[expert],
                ctx + f"\n## 三方当前立场\n{json.dumps(all_stances, ensure_ascii=False)}\n"
                f"## 仍有分歧的维度\n{conflicts}\n## 任务\n查看其他专家立场，对分歧维度调整或坚持你的选择并说明理由。"
                "输出 JSON: {\"stance\":{\"hud.xxx\":{\"choice\":\"..\",\"reason\":\"..\"}}}")
    return {k: v.get("choice", "") for k, v in out.get("stance", {}).items() if isinstance(v, dict)}


def run_pilot() -> int:
    from Plugins.AgentBridge.Compiler.stages.llm_client import load_llm_client_from_config
    client = load_llm_client_from_config()
    if client is None:
        print("ERROR: llm_client 加载失败（需带 anthropic SDK 的解释器）")
        return 1
    print("LLM:", client.model)

    contract = _load("root_skill_contract.json")
    ctx = _context_block(contract)
    log: dict = {"max_rounds": MAX_ROUNDS, "experts": EXPERT_PRIORITY}

    # 阶段1 各自发现 → 合并
    discovered = [(e, discover(client, e, ctx)) for e in EXPERT_PRIORITY]
    merged = core.merge_discovered_dimensions(discovered)
    log["discovered_per_expert"] = {e: [d.get("dimension_id") for d in dl] for e, dl in discovered}
    log["merged_dimensions"] = merged
    owner_map = {d["dimension_id"]: core.resolve_owner(d["proposed_by"], EXPERT_PRIORITY) for d in merged}

    # 阶段2 各自立场
    stances = {e: stance(client, e, ctx, merged) for e in EXPERT_PRIORITY}
    log["round_0_stances"] = stances

    # 阶段3 多轮协商
    final = {}
    for rnd in range(1, MAX_ROUNDS + 1):
        conv = core.detect_convergence(stances)
        conflicts = [d for d, info in conv.items() if not info["converged"]]
        log[f"round_{rnd}_conflicts"] = conflicts
        if not conflicts:
            break
        stances = {e: {**stances[e], **renegotiate(client, e, ctx, stances, conflicts)} for e in EXPERT_PRIORITY}
        log[f"round_{rnd}_stances"] = stances

    # 阶段4 收敛/降级
    conv = core.detect_convergence(stances)
    gaps = []
    for did, info in conv.items():
        if info["converged"]:
            final[did] = next(iter(info["choices"].values())) if info["choices"] else ""
        else:
            final[did] = core.weighted_majority_fallback(info["choices"], owner_map.get(did, EXPERT_PRIORITY[0]))
            gaps.append({"dimension_id": did, "choices": info["choices"],
                         "resolved_by": "weighted_majority", "owner": owner_map.get(did)})
    log["final_convergence"] = conv
    log["downgraded_gaps"] = gaps

    fragment = {
        "fragment_version": "2.0",
        "skill_instance_id": "skill-baseline-hud",
        "template_id": "baseline.hud.realization_eligible",
        "domain_type": "baseline",
        "phase_scope": "phase11_hud_multiexpert_pilot",
        "status": "completed",
        "emitted_families": ["hud_spec"],
        "spec_fragments": {"hud_spec": {
            "capability": "HUD",
            "realization_class": "realization_eligible",
            "required_elements": contract.get("constraint_fields", {}).get("ui.required_hud_fields", {}).get("value", []),
            "selected_realization": final,
        }},
        "capability_gaps": gaps,
        "metadata": {"generator": "HUD-MultiExpert-Pilot", "promotable": False, "mode": "multiexpert_pilot"},
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "hud_multiexpert_fragment.json").write_text(
        json.dumps(fragment, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "hud_multiexpert_negotiation_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已落盘 fragment + negotiation_log；维度数:", len(merged), "| 降级数:", len(gaps))
    return 0


if __name__ == "__main__":
    sys.exit(run_pilot())
```

- [ ] **Step 2: 离线冒烟（确认 import 链无误、纯逻辑可被脚本调用）**

Run: `python -c "import sys; sys.path.insert(0,'.'); from Plugins.AgentBridge.Tests.scripts import demo_hud_multiexpert as d; print('import OK', d.MAX_ROUNDS, d.EXPERT_PRIORITY)"`
Expected: 打印 `import OK 2 ['ux-designer', 'ui-programmer', 'art-director']`（默认 python 即可，因为 llm_client 是 run_pilot 内延迟 import，模块导入不触发）

- [ ] **Step 3: 复跑纯逻辑测试，确认未被 Task 6 破坏**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS，`All 6 passed`

- [ ] **Step 4: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py
git commit -m "[skip-doc] feat(pilot): HUD 多专家协商编排脚本（发现→立场→协商→收敛/降级）"
```

---

## Task 7: 跑真实试点 + 产出对比

**Files:**
- Output: `ProjectState/Reports/2026-05-31/hud_multiexpert_fragment.json` / `hud_multiexpert_negotiation_log.json` / `hud_multiexpert_vs_single_comparison.md`

- [ ] **Step 1: 真实 LLM 跑试点**

Run: `C:\Python312\python.exe Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py`
Expected: 打印 `LLM: anthropic/MiniMax M2.7` 与 `已落盘 fragment + negotiation_log；维度数: N | 降级数: M`，退出码 0。
若 `client 加载失败`：确认用的是 `C:\Python312\python.exe`（带 anthropic SDK），不是默认 3.13。

- [ ] **Step 2: 校验产物结构**

Run: `python -c "import json; d=json.load(open(r'ProjectState/Reports/2026-05-31/hud_multiexpert_fragment.json',encoding='utf-8')); sr=d['spec_fragments']['hud_spec']['selected_realization']; print('selected_realization 维度数:', len(sr)); assert sr, 'selected_realization 不能为空'; print('OK')"`
Expected: 打印维度数 + `OK`

- [ ] **Step 3: 生成对比报告**

读取两份 fragment 的 selected_realization 维度 id，用 `compare_dimension_coverage` 算覆盖差，连同协商轮次/降级数/调用成本，手写成 `ProjectState/Reports/2026-05-31/hud_multiexpert_vs_single_comparison.md`，必须包含四栏对比表（维度覆盖 / 收敛性 / 成本 / 论证深度抽样）与一句明确结论（多专家是否值得推广）。生成覆盖差数据：

Run: `python -c "import sys; sys.path.insert(0,'.'); import json; from Plugins.AgentBridge.Tests.scripts import hud_multiexpert_core as c; m=json.load(open(r'ProjectState/Reports/2026-05-31/hud_multiexpert_fragment.json',encoding='utf-8'))['spec_fragments']['hud_spec']['selected_realization']; s=json.load(open(r'ProjectState/Reports/2026-05-29/hud_llm_divergence_fragment.json',encoding='utf-8'))['spec_fragments']['hud_spec']['selected_realization']; print(json.dumps(c.compare_dimension_coverage(list(m), list(s)), ensure_ascii=False, indent=2))"`
Expected: 打印 only_in_multi / only_in_single / common 三组维度 id —— 把这些写进对比报告。

- [ ] **Step 4: 提交**

```bash
git add ProjectState/Reports/2026-05-31/hud_multiexpert_fragment.json ProjectState/Reports/2026-05-31/hud_multiexpert_negotiation_log.json ProjectState/Reports/2026-05-31/hud_multiexpert_vs_single_comparison.md
git commit -m "[skip-doc] test(pilot): HUD 多专家真实试点产物 + 与单专家对比"
```

---

## Task 8: 收尾门禁

- [ ] **Step 1: verification-before-completion**

调用 `superpowers:verification-before-completion`，逐条核对：纯逻辑测试 6/6 绿、真实试点退出码 0 且 selected_realization 非空、对比报告含四栏 + 结论、范围未越界（未碰 domain_skill_runtime/agent_protocol/SkillTemplate）。

- [ ] **Step 2: document-release 门禁**

调用本项目 `document-release` skill。本次为新增独立试点脚本 + 证据，预计 Coverage Map 中 A 层无变更、记录到 ProjectState/Reports；如对比结论建议推广，在 backlog 留一条「多专家协商推广到框架」的 follow-up。这是 commit/push 前的强制门禁。

- [ ] **Step 3: finishing-a-development-branch**

调用 `superpowers:finishing-a-development-branch`，按其指引完成 merge / PR。

---

## Self-Review

**Spec coverage：**
- spec §2（三专家职责边界）→ Task 6 `EXPERT_PROMPTS` ✅
- spec §3 阶段1 各自发现+合并 → Task 1 merge + Task 6 discover ✅；归属 → Task 2 resolve_owner ✅
- spec §3 阶段3 协商+收敛判定 → Task 3 detect_convergence + Task 6 renegotiate 循环 ✅
- spec §3 阶段4 加权多数降级 → Task 4 weighted_majority_fallback + Task 6 收敛/降级段 ✅
- spec §4 三份产物 → Task 6 落盘 fragment+log + Task 7 对比报告 ✅；维度覆盖判据 → Task 5 compare_dimension_coverage ✅
- spec §4 成功判据（覆盖/收敛/成本/深度）→ Task 7 Step 3 对比报告四栏 ✅
- spec §5 文件结构（core/test/demo 分文件、复用 llm_client、产物落 Reports）→ File Structure + Tasks ✅
- spec §1.5 非目标（不碰主链/模板、标注不可 promote）→ fragment metadata `promotable: False`、Task 8 Step 1 复核 ✅

**Placeholder scan：** 无 TBD/TODO；每个代码步给完整代码；命令均带预期输出。Task 7 Step 3 的「手写对比报告」给了具体四栏要求 + 数据生成命令，非空泛占位。

**Type consistency：** `merge_discovered_dimensions` 产出的 `proposed_by` 被 `resolve_owner` 消费一致；`detect_convergence` 产出的 `{"converged","choices"}` 被 Task 6 收敛段与 `weighted_majority_fallback(choices, owner)` 消费一致；`compare_dimension_coverage` 返回键 `only_in_multi/only_in_single/common` 在 Task 7 引用一致；`EXPERT_PRIORITY` 在 core 调用与 demo 编排中同名同序。
