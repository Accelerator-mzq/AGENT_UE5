# Baseline realization_eligible 发散落地修复 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 realization_eligible baseline 节点（当前仅 HUD）的 `spec_fragments` 携带发散收敛结果 `selected_realization`，并去掉 HUD 硬编码使该路径通用，在 HUD 上验证发散真落地且语义不变。

**Architecture:** 在 `domain_skill_runtime.py` 抽出一个 `_selected_realization_from_converged` 纯函数（复用 gameplay 行 330–337 的收敛提取逻辑），让 `_build_baseline_spec_fragment` 接受 `converged_pack` 并在 realization_eligible 时写入 `selected_realization`；把 `_build_discovered_fragment` 的 baseline 分支从硬编码 HUD 改为经 `_capability_map` 按 `capability_id` 动态查 capability。测试用项目既有的 `Tests/scripts/` 独立脚本风格（非 pytest），纯函数 + 真实 run 录制数据，离线可跑。

**Tech Stack:** Python 3.x、jsonschema；项目自有 Compiler pipeline；测试为 `python <script>.py` 自带 `__main__` 断言运行器。

参照设计：`Docs/archive/superpowers/specs/2026-05-29-baseline-realization-divergence-fix-design.md`

---

## File Structure

- **Modify** `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`
  - 新增纯函数 `_selected_realization_from_converged(converged_pack)`（约行 308 前，紧邻 `_build_gameplay_spec_fragment`）
  - 扩展 `_build_baseline_spec_fragment`（行 465–501）：新增 `converged_pack` 参数 + 写入 `selected_realization`
  - 改 `_build_discovered_fragment` baseline 分支（行 618–623）：动态查 capability + 传 `converged_pack`
- **Create** `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
  - 离线单元/数据回归测试，house style（`sys.path` 注入 + 断言 + `sys.exit`）
- **Create** `ProjectState/Reports/2026-05-29/baseline_realization_divergence_evidence.md`
  - 改动前后 HUD fragment 对比 + 测试与校验输出

> 注：`Plugins/AgentBridge/AgentBridgeTests/` 为禁改区，测试一律落 `Tests/scripts/`。

---

## Task 1: 抽出 `_selected_realization_from_converged` 纯函数

把 gameplay 内联的收敛提取逻辑抽成可复用纯函数，供 baseline 复用（DRY）。gameplay 自身本任务不改（降低风险，见 spec §4）。

**Files:**
- Create: `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
- Modify: `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`（在 `_build_gameplay_spec_fragment`（行 312）之前插入新函数）

- [ ] **Step 1: 写失败测试（新建测试脚本，含第一个用例）**

创建 `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`：

```python
"""Baseline realization_eligible 发散落地修复 —— 离线回归测试。

house style：手写断言 + __main__ 运行器，python 直接跑。
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Compiler.stages import domain_skill_runtime as dsr  # noqa: E402


def test_selected_realization_from_converged_maps_choices():
    """converged_choices / convergence_decisions 都能被提取成 dimension->choice 映射。"""
    converged_pack = {
        "converged_choices": [
            {"dimension_id": "dim-a", "chosen_candidate_name": "方案甲"},
            {"dimension_id": "dim-b", "chosen_candidate": "方案乙"},
        ]
    }
    result = dsr._selected_realization_from_converged(converged_pack)
    assert result == {"dim-a": "方案甲", "dim-b": "方案乙"}, result


def test_selected_realization_from_converged_empty():
    """空 pack 返回空 dict，不抛异常。"""
    assert dsr._selected_realization_from_converged({}) == {}
    assert dsr._selected_realization_from_converged(None) == {}


ALL_TESTS = [
    test_selected_realization_from_converged_maps_choices,
    test_selected_realization_from_converged_empty,
]


def main() -> int:
    failures = []
    for fn in ALL_TESTS:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures.append((fn.__name__, repr(exc)))
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

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: FAIL，`AttributeError: module ... has no attribute '_selected_realization_from_converged'`

- [ ] **Step 3: 实现纯函数**

在 `domain_skill_runtime.py` 的 `_build_gameplay_spec_fragment`（行 312）定义之前插入：

```python
def _selected_realization_from_converged(converged_pack: Dict[str, Any] | None) -> Dict[str, Any]:
    """从 converged_pack 提取 dimension_id -> chosen 候选 的映射。

    兼容 converged_choices / convergence_decisions 两种键，
    以及 chosen_candidate_name / chosen_candidate / selected_candidate_id 三种候选字段。
    与 _build_gameplay_spec_fragment 行内逻辑保持一致，供 baseline 复用。
    """
    if not converged_pack:
        return {}
    convergence_choices = (
        converged_pack.get("converged_choices")
        or converged_pack.get("convergence_decisions", [])
    )
    return {
        choice.get("dimension_id", ""): choice.get(
            "chosen_candidate_name",
            choice.get("chosen_candidate", choice.get("selected_candidate_id", "")),
        )
        for choice in convergence_choices
    }
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: PASS，`All 2 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py
git commit -m "[skip-doc] refactor(stage4): 抽出 _selected_realization_from_converged 纯函数 + 测试"
```

> `[skip-doc]`：本次是新增内部测试 + 纯函数抽取，无对外文档面变更；最终收尾任务会统一过 document-release。

---

## Task 2: `_build_baseline_spec_fragment` 接受 converged_pack 并写入 selected_realization

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py:465-501`
- Test: `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`

- [ ] **Step 1: 追加失败测试**

在测试脚本中，`ALL_TESTS` 列表定义之前追加两个用例：

```python
def test_baseline_eligible_emits_selected_realization():
    """realization_eligible baseline 节点：带 converged_pack 时写入 selected_realization。"""
    node = {"instance_id": "skill-baseline-hud", "capability_id": "baseline-hud"}
    capability = {
        "baseline_item": "HUD",
        "realization_class": "realization_eligible",
        "required_elements": ["current_player", "turn_number"],
    }
    converged_pack = {
        "converged_choices": [
            {"dimension_id": "dim-hud-density", "chosen_candidate_name": "紧凑列表密度"},
        ]
    }
    fragments = dsr._build_baseline_spec_fragment(
        node, capability, {}, converged_pack=converged_pack
    )
    spec = next(iter(fragments.values()))
    assert spec.get("selected_realization") == {"dim-hud-density": "紧凑列表密度"}, spec


def test_baseline_presence_only_no_selected_realization():
    """presence_only baseline：即使误传 converged_pack 也不写 selected_realization。"""
    node = {"instance_id": "skill-baseline-main-menu", "capability_id": "baseline-main-menu"}
    capability = {
        "baseline_item": "Main Menu",
        "realization_class": "presence_only",
        "required_elements": ["New Game", "Quit"],
    }
    fragments = dsr._build_baseline_spec_fragment(
        node, capability, {}, converged_pack={"converged_choices": [
            {"dimension_id": "x", "chosen_candidate_name": "y"}]}
    )
    spec = next(iter(fragments.values()))
    assert "selected_realization" not in spec, spec
```

并把这两个函数名加入 `ALL_TESTS` 列表：

```python
ALL_TESTS = [
    test_selected_realization_from_converged_maps_choices,
    test_selected_realization_from_converged_empty,
    test_baseline_eligible_emits_selected_realization,
    test_baseline_presence_only_no_selected_realization,
]
```

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: FAIL，`TypeError: _build_baseline_spec_fragment() got an unexpected keyword argument 'converged_pack'`

- [ ] **Step 3: 修改函数签名与实现**

把 `_build_baseline_spec_fragment`（行 465）签名改为：

```python
def _build_baseline_spec_fragment(
    node: Dict[str, Any],
    capability: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    converged_pack: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
```

在函数体 `return {family_name: spec}`（行 501）之前、instance_id 特判（行 493–499）之后插入：

```python
    # realization_eligible baseline 与 gameplay 对称：把发散收敛结果写入 spec。
    if capability.get("realization_class") == "realization_eligible":
        selected_realization = _selected_realization_from_converged(converged_pack)
        if selected_realization:
            spec["selected_realization"] = selected_realization
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: PASS，`All 4 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py
git commit -m "[skip-doc] feat(stage4): baseline realization_eligible 写入 selected_realization"
```

---

## Task 3: 泛化 `_build_discovered_fragment` baseline 分支（去 HUD 硬编码 + 传 converged_pack）

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py:608-623`
- Test: `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`

- [ ] **Step 1: 追加失败测试（含 HUD 语义等价 + 非 HUD 通用）**

在 `ALL_TESTS` 之前追加。该测试构造一个 root_skill_contract（含两个 realization_eligible baseline capability：HUD 与一个非 HUD 的 audio），验证：① baseline 分支按 capability_id 取到正确 capability（非 HUD 节点不再被当 HUD）；② 两者都拿到 selected_realization。

```python
def _fake_contract_two_eligible():
    return {
        "baseline_capabilities": [
            {"capability_id": "baseline-hud", "baseline_item": "HUD",
             "realization_class": "realization_eligible",
             "required_elements": ["current_player", "turn_number"]},
            {"capability_id": "baseline-audio-foundation", "baseline_item": "Audio Foundation",
             "realization_class": "realization_eligible",
             "required_elements": ["master_volume", "sfx_bus"]},
        ],
        "gameplay_capabilities": [],
        "constraint_fields": {
            "ui.required_hud_fields": {"value": ["current_player", "turn_number"]}
        },
    }


def _fake_converged(dim_id, choice):
    return {"converged_choices": [{"dimension_id": dim_id, "chosen_candidate_name": choice}]}


def test_discovered_baseline_uses_capability_by_id_not_hardcoded_hud():
    """非 HUD 的 realization_eligible baseline 不再被硬编码成 HUD。"""
    contract = _fake_contract_two_eligible()
    node = {
        "instance_id": "skill-baseline-audio-foundation",
        "capability_id": "baseline-audio-foundation",
        "domain_type": "baseline",
    }
    fragment = dsr._build_discovered_fragment(
        node=node,
        root_skill_contract=contract,
        clarification_gate_report={},
        design_space_report={"discovery_dimensions": []},
        converged_pack=_fake_converged("dim-audio-density", "丰富音效层"),
        phase_scope="test",
    )
    spec = next(iter(fragment["spec_fragments"].values()))
    assert spec.get("capability") == "Audio Foundation", spec
    assert spec.get("required_elements") == ["master_volume", "sfx_bus"], spec
    assert spec.get("selected_realization") == {"dim-audio-density": "丰富音效层"}, spec


def test_discovered_baseline_hud_semantics_preserved():
    """HUD 经泛化路径后 required_elements 不变，且新增 selected_realization。"""
    contract = _fake_contract_two_eligible()
    node = {
        "instance_id": "skill-baseline-hud",
        "capability_id": "baseline-hud",
        "domain_type": "baseline",
    }
    fragment = dsr._build_discovered_fragment(
        node=node,
        root_skill_contract=contract,
        clarification_gate_report={},
        design_space_report={"discovery_dimensions": []},
        converged_pack=_fake_converged("dim-hud-density", "紧凑列表密度"),
        phase_scope="test",
    )
    spec = next(iter(fragment["spec_fragments"].values()))
    assert spec.get("required_elements") == ["current_player", "turn_number"], spec
    assert spec.get("selected_realization") == {"dim-hud-density": "紧凑列表密度"}, spec
```

把 4 个函数加入 `ALL_TESTS`：

```python
    test_discovered_baseline_uses_capability_by_id_not_hardcoded_hud,
    test_discovered_baseline_hud_semantics_preserved,
```

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: FAIL，`test_discovered_baseline_uses_capability_by_id_not_hardcoded_hud` 断言失败（`capability == "HUD"` 而非 `"Audio Foundation"`，因为当前硬编码）

- [ ] **Step 3: 改 baseline 分支**

把 `_build_discovered_fragment`（行 619–623）的 spec_fragments 赋值改为：

```python
    if is_baseline:
        capability = _capability_map(root_skill_contract).get(
            node.get("capability_id", ""), {}
        )
        spec_fragments = _build_baseline_spec_fragment(
            node, capability, clarification_gate_report, converged_pack=converged_pack
        )
    else:
        spec_fragments = _build_gameplay_spec_fragment(
            node, root_skill_contract, converged_pack, clarification_gate_report
        )
```

> 说明：`_capability_map`（行 88–95）已存在，按 `capability_id` 返回 baseline/gameplay capability 对象。HUD 的 `required_elements` 改由 `baseline_capabilities` 提供；§3 回归（Task 4）用真实 run 数据确认与旧 `constraint_fields["ui.required_hud_fields"]` 等价。若 Task 4 发现不等价，则在此 `if is_baseline` 内对 `node.capability_id == "baseline-hud"` 追加 `capability = {**capability, "required_elements": root_skill_contract["constraint_fields"]["ui.required_hud_fields"]["value"]}`。

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: PASS，`All 6 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py
git commit -m "[skip-doc] feat(stage4): baseline discovered 分支去 HUD 硬编码，按 capability_id 动态查"
```

---

## Task 4: 真实数据回归 + 契约校验 + 证据落盘

用既有 run 的真实 `root_skill_contract` 验证 HUD `required_elements` 等价性；跑契约校验；落证据。

**Files:**
- Test: `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
- Create: `ProjectState/Reports/2026-05-29/baseline_realization_divergence_evidence.md`

- [ ] **Step 1: 追加真实数据等价性测试**

追加用例，读取既有 run 的 root_skill_contract，断言 `baseline_capabilities` 里 HUD 的 `required_elements` 与 `constraint_fields["ui.required_hud_fields"].value` 一致（这是 Task 3 泛化语义不漂移的根据）：

```python
import json


def test_real_run_hud_required_elements_equivalent():
    """真实 run：baseline_capabilities 的 HUD required_elements 与旧 constraint_fields 来源等价。"""
    runs_root = PROJECT_ROOT / "ProjectState" / "runs"
    contracts = sorted(runs_root.glob("run-*/root_skill_contract.json"))
    assert contracts, "未找到任何 run 的 root_skill_contract.json"
    contract = json.loads(contracts[-1].read_text(encoding="utf-8"))
    hud = next(
        c for c in contract["baseline_capabilities"]
        if c.get("capability_id") == "baseline-hud"
    )
    legacy = contract["constraint_fields"]["ui.required_hud_fields"]["value"]
    assert hud.get("required_elements") == legacy, (
        f"HUD required_elements 不等价：capability={hud.get('required_elements')} "
        f"vs constraint={legacy}"
    )
```

加入 `ALL_TESTS`：`test_real_run_hud_required_elements_equivalent,`

- [ ] **Step 2: 运行全部测试**

Run: `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py`
Expected: PASS，`All 7 passed`。

> 若该用例 FAIL（来源不等价）：执行 Task 3 Step 3 注释中的 HUD 保留分支补丁，再重跑至全绿。

- [ ] **Step 3: 契约校验**

Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: 退出码 0，无 schema 错误。

- [ ] **Step 4: 既有 baseline 模板验收脚本（确认未回归）**

Run: `python Plugins/AgentBridge/Tests/scripts/task14_phase11_baseline_template_validation.py`
Expected: 脚本自报通过（退出码 0）。若该脚本因需 GDD/网络等前置无法离线跑，记录其前置条件与跳过原因到证据文件，不视为本任务失败项。

- [ ] **Step 5: 落证据并提交**

创建 `ProjectState/Reports/2026-05-29/baseline_realization_divergence_evidence.md`，内容包含：
- 改动前后 HUD `spec_fragments.hud_spec` 对比（改前无 `selected_realization`、改后有；`required_elements` 不变）
- 上述 Step 2–4 命令的实际输出粘贴
- 结论：发散落地达成、HUD 语义不变、下游契约不破

```bash
git add Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py ProjectState/Reports/2026-05-29/baseline_realization_divergence_evidence.md
git commit -m "[skip-doc] test(stage4): baseline 发散落地真实数据回归 + 证据落盘"
```

---

## Task 5: 收尾门禁

- [ ] **Step 1: verification-before-completion**

调用 `superpowers:verification-before-completion`，逐条核对：6+1 测试全绿、`validate_examples --strict` 绿、HUD 对比证据齐、范围未越界（未碰 audio / 第一档提质 / presence / gameplay 路径）。

- [ ] **Step 2: document-release 门禁**

调用本项目 `document-release` skill，同步受影响文档面（本次属内部编译逻辑修复，预计仅需在 acceptance backlog / 相关 Docs 标注「baseline 发散落地已修复」）。这是 commit/push 前的强制门禁；前面各任务用 `[skip-doc]` 暂通过，最终须在此统一过闸。

- [ ] **Step 3: finishing-a-development-branch**

调用 `superpowers:finishing-a-development-branch`，按其指引完成 merge / PR。

---

## Self-Review

**Spec coverage：**
- spec §2.1（baseline 写 selected_realization）→ Task 2 ✅
- spec §2.2（去 HUD 硬编码 + capability_map 动态查 + 传 converged_pack）→ Task 3 ✅
- spec §2.3（HUD required_elements 等价性，含不等价回退）→ Task 4 Step 1–2 + Task 3 Step 3 注释回退 ✅
- spec §3（发散落地/语义等价/契约/链路验证 + 证据落盘）→ Task 4 ✅
- spec §1.5 非目标（不碰 audio / 提质 / presence / gameplay）→ 计划未触及，Task 5 Step 1 复核 ✅

**Placeholder scan：** 无 TBD/TODO；每个代码步给出完整代码；命令均含预期输出。Task 4 Step 4 的「无法离线跑则记录跳过」是显式条件分支而非占位。

**Type consistency：** `_selected_realization_from_converged(converged_pack)` 在 Task 1 定义、Task 2/3 调用签名一致；`_build_baseline_spec_fragment(node, capability, clarification_gate_report, converged_pack=None)` 在 Task 2 定义、Task 3 以 `converged_pack=converged_pack` 调用一致；`_capability_map`、`_build_discovered_fragment` 参数名与现有源码一致。
