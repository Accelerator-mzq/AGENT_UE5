# HUD 总监裁决版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 HUD 多专家试点的收敛机制从"协商辩论 + 字符串判定"替换为"中立总监 LLM 语义整合裁决",根除字符串比较缺陷,产出 HUD fragment 与单专家版对比。

**Architecture:** 抽一个纯函数 `assemble_arbitration_result`(从总监裁决结果 + 合并维度装配 selected_realization 与 capability_gaps,处理正常/unresolved/missing 三情况)做 TDD;总监 prompt、裁决 LLM 调用、编排替换作为集成层改 `demo_hud_multiexpert.py`。core 协商函数按设计保留不删。纯逻辑默认 Python 可测,真实试点用 `C:\Python312\python.exe`。

**Tech Stack:** Python 3.x;项目自有 `llm_client.py`;house-style 测试脚本。

参照设计:`Docs/archive/superpowers/specs/2026-05-31-hud-arbiter-design.md`

---

## File Structure

- **Modify** `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py` — 新增 `assemble_arbitration_result`(纯函数),不动既有 5 函数
- **Modify** `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py` — 追加 3 用例(正常/unresolved/missing)
- **Modify** `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py` — 编排替换为总监裁决
- **Output** `ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json` + `hud_arbiter_log.json` + 更新 `hud_multiexpert_vs_single_comparison.md`

---

## Task 1: core 新增 `assemble_arbitration_result` 纯函数

从总监裁决结果装配最终 spec,处理三情况:正常 resolved、unresolved(真分歧)、missing(裁决遗漏)。

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`

- [ ] **Step 1: 追加失败测试**

在 `test_hud_multiexpert_core.py` 的 `ALL_TESTS` 列表定义之前追加:

```python
def test_assemble_arbitration_normal():
    """全部 resolved：selected 取 final_choice，gaps 空。"""
    merged = [{"dimension_id": "hud.a", "proposed_by": ["ux-designer"]},
              {"dimension_id": "hud.b", "proposed_by": ["art-director"]}]
    arbitration = {
        "hud.a": {"final_choice": "方案A", "integration_note": "三方一致", "unresolved": False},
        "hud.b": {"final_choice": "方案B", "integration_note": "采纳美术", "unresolved": False},
    }
    stances = {"ux-designer": {"hud.a": "x", "hud.b": "y"}}
    selected, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    assert selected == {"hud.a": "方案A", "hud.b": "方案B"}, selected
    assert gaps == [], gaps


def test_assemble_arbitration_unresolved():
    """unresolved=true：selected 仍取 final_choice，但该维度进 gaps 附三方立场。"""
    merged = [{"dimension_id": "hud.a", "proposed_by": ["ux-designer"]}]
    arbitration = {"hud.a": {"final_choice": "总监择优X", "integration_note": "UX与美术对立", "unresolved": True}}
    stances = {"ux-designer": {"hud.a": "全显示"}, "art-director": {"hud.a": "极简"}}
    selected, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    assert selected == {"hud.a": "总监择优X"}, selected
    assert len(gaps) == 1, gaps
    assert gaps[0]["dimension_id"] == "hud.a"
    assert gaps[0]["resolved_by"] == "arbiter_unresolved"
    assert gaps[0]["integration_note"] == "UX与美术对立"
    assert gaps[0]["stances"] == {"ux-designer": "全显示", "art-director": "极简"}


def test_assemble_arbitration_missing():
    """合并维度在 arbitration 中缺失：selected 兜底空串 + gap 标 arbiter_missing。"""
    merged = [{"dimension_id": "hud.a", "proposed_by": ["ux-designer"]},
              {"dimension_id": "hud.missing", "proposed_by": ["ui-programmer"]}]
    arbitration = {"hud.a": {"final_choice": "方案A", "integration_note": "", "unresolved": False}}
    stances = {"ui-programmer": {"hud.missing": "我的主张"}}
    selected, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    assert selected == {"hud.a": "方案A", "hud.missing": ""}, selected
    assert len(gaps) == 1, gaps
    assert gaps[0]["dimension_id"] == "hud.missing"
    assert gaps[0]["resolved_by"] == "arbiter_missing"
    assert gaps[0]["stances"] == {"ui-programmer": "我的主张"}
```

把三个函数名加入 `ALL_TESTS`:

```python
    test_assemble_arbitration_normal,
    test_assemble_arbitration_unresolved,
    test_assemble_arbitration_missing,
```

- [ ] **Step 2: 运行确认失败**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: FAIL,`AttributeError: ... 'assemble_arbitration_result'`

- [ ] **Step 3: 实现**

在 `hud_multiexpert_core.py` 末尾追加:

```python
def assemble_arbitration_result(
    merged_dims: list[dict[str, Any]],
    arbitration: dict[str, dict[str, Any]],
    stances: dict[str, dict[str, str]],
) -> tuple[dict[str, str], list[dict[str, Any]]]:
    """根据中立总监的裁决结果装配最终 spec。

    merged_dims: merge_discovered_dimensions 的输出（每项含 dimension_id）。
    arbitration: 总监输出 {dimension_id: {final_choice, integration_note, unresolved}}。
    stances: {专家名: {dimension_id: choice}} 三方原始立场（用于 gap 留痕）。
    返回: (selected_realization, capability_gaps)。
      - 正常 resolved：selected 取 final_choice，不进 gaps；
      - unresolved=True：selected 仍取 final_choice，该维度进 gaps（附 integration_note + 三方立场）；
      - 合并维度在 arbitration 中缺失：selected 兜底空串，进 gaps 标 arbiter_missing。
    """
    def _stances_for(did: str) -> dict[str, str]:
        return {expert: per[did] for expert, per in stances.items() if did in per}

    selected: dict[str, str] = {}
    gaps: list[dict[str, Any]] = []
    for dim in merged_dims:
        did = dim.get("dimension_id")
        if not did:
            continue
        verdict = arbitration.get(did)
        if verdict is None:
            selected[did] = ""
            gaps.append({
                "dimension_id": did,
                "resolved_by": "arbiter_missing",
                "stances": _stances_for(did),
            })
            continue
        selected[did] = verdict.get("final_choice", "") or ""
        if verdict.get("unresolved"):
            gaps.append({
                "dimension_id": did,
                "integration_note": verdict.get("integration_note", ""),
                "resolved_by": "arbiter_unresolved",
                "stances": _stances_for(did),
            })
    return selected, gaps
```

- [ ] **Step 4: 运行确认通过**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS,`All 9 passed`

- [ ] **Step 5: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py
git commit -m "[skip-doc] feat(pilot): core 新增 assemble_arbitration_result 纯函数 + 测试"
```

---

## Task 2: 改造 demo 编排为总监裁决

**Files:**
- Modify: `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py`

- [ ] **Step 1: 改 docstring + 删 MAX_ROUNDS**

把文件顶部 docstring（第 1-8 行）替换为:

```python
"""HUD 总监裁决试点主脚本。

3 专家（UX/UI程序/美术）各自发现维度 → 立场 → 中立总监语义整合裁决，
产出 HUD fragment + 裁决记录（与单专家版的对比在后续步骤生成）。

须用带 anthropic SDK 的解释器运行：
  C:\\Python312\\python.exe Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py
"""
```

删除第 23 行 `MAX_ROUNDS = 2  # ...`（总监版无多轮协商，不需要）。

- [ ] **Step 2: 加总监 prompt 常量**

在 `EXPERT_PROMPTS = {...}` 字典闭合之后（第 46 行后）追加:

```python

# 中立总监 system prompt（试点内联；CCGS 无对应 persona，本项目编译链特有）
ARBITER_PROMPT = (
    "你是中立的设计整合者，不偏向 UX / UI 程序 / 美术任何一方。"
    "给你三位专家对一组 HUD 设计维度的各自主张。"
    "对每个维度，识别三方是“说法不同但意思相同”（合并成一个连贯统一的表述），"
    "还是“存在真实设计分歧”（择优选择并说明理由；若三方诉求真实对立、"
    "无法在不牺牲某方硬需求下调和，则标记 unresolved=true）。"
    "必须遵守给定的 GDD locked 约束，不得违反。只输出 JSON，不要解释文字。"
)
```

- [ ] **Step 3: 删 renegotiate 函数,加 arbitrate 函数**

删除 `renegotiate` 函数整体（第 107-112 行）。在其位置加 `arbitrate`:

```python
def arbitrate(client, ctx: str, dims: list, stances: dict) -> dict:
    """中立总监一次性裁决：读三方立场，逐维度语义整合。

    返回 {dimension_id: {final_choice, integration_note, unresolved}}。
    """
    dim_ids = [d.get("dimension_id", "") for d in dims if d.get("dimension_id")]
    out = _call(client, ARBITER_PROMPT,
                ctx + f"\n## 待裁决维度全集\n{dim_ids}\n"
                f"## 三方立场\n{json.dumps(stances, ensure_ascii=False)}\n"
                "## 任务\n对每个维度做语义整合裁决。"
                "输出 JSON: {\"arbitration\":{\"hud.xxx\":"
                "{\"final_choice\":\"..\",\"integration_note\":\"..\",\"unresolved\":false}}}")
    result = out.get("arbitration", {})
    return result if isinstance(result, dict) else {}
```

- [ ] **Step 4: 改 run_pilot 阶段3-4 与产物**

把 `run_pilot` 中「阶段2 各自立场」到「阶段4 收敛/降级」整段（第 134-160 行,即 `# 阶段2 各自立场` 到 `log["downgraded_gaps"] = gaps`）替换为:

```python
    # 阶段2 各自立场
    stances = {e: stance(client, e, ctx, merged) for e in EXPERT_PRIORITY}
    log["stances"] = stances

    # 阶段3 中立总监裁决（一次性，语义整合，无字符串比较）
    arbitration = arbitrate(client, ctx, merged, stances)
    log["arbitration"] = arbitration

    # 阶段4 装配（正常/unresolved/missing 三情况由 core 处理）
    final, gaps = core.assemble_arbitration_result(merged, arbitration, stances)
    log["capability_gaps"] = gaps
```

同时删除阶段1 中不再需要的 owner_map 行（第 132 行 `owner_map = {...}`，总监版无加权多数，不需要）。

把 `log: dict = {"max_rounds": MAX_ROUNDS, "experts": EXPERT_PRIORITY}`（第 125 行）改为:

```python
    log: dict = {"experts": EXPERT_PRIORITY}
```

把 fragment 字典的 `phase_scope`（第 167 行）改为:

```python
        "phase_scope": "phase11_hud_arbiter_pilot",
```

把 fragment 的 `metadata`（第 177 行）改为:

```python
        "metadata": {"generator": "HUD-Arbiter-Pilot", "promotable": False, "mode": "arbiter_pilot"},
```

把落盘文件名与末尾 print（第 180-185 行）改为:

```python
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "hud_arbiter_fragment.json").write_text(
        json.dumps(fragment, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT_DIR / "hud_arbiter_log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print("已落盘 arbiter fragment + log；维度数:", len(merged), "| 未解分歧/遗漏数:", len(gaps))
```

- [ ] **Step 5: 离线冒烟（确认 import 链 + 改造到位）**

Run: `python -c "import sys; sys.path.insert(0,'.'); from Plugins.AgentBridge.Tests.scripts import demo_hud_multiexpert as d; print('import OK', d.EXPERT_PRIORITY); assert not hasattr(d, 'MAX_ROUNDS'), 'MAX_ROUNDS 应已删'; assert hasattr(d, 'arbitrate'), 'arbitrate 应存在'; assert hasattr(d, 'ARBITER_PROMPT'); print('arbiter 改造 OK')"`
Expected: 打印 `import OK ['ux-designer', 'ui-programmer', 'art-director']` 与 `arbiter 改造 OK`

- [ ] **Step 6: 确认无残留协商调用**

Run: `grep -nE "renegotiate|detect_convergence|weighted_majority|MAX_ROUNDS|round_0_stances|owner_map" Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py || echo "(无残留协商引用)"`
Expected: 打印 `(无残留协商引用)`

- [ ] **Step 7: 复跑纯逻辑测试确认未破坏**

Run: `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py`
Expected: PASS,`All 9 passed`

- [ ] **Step 8: 提交**

```bash
git add Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py
git commit -m "[skip-doc] feat(pilot): HUD 编排替换为中立总监裁决（去协商循环/字符串判定）"
```

---

## Task 3: 跑真实试点 + 更新对比报告

**Files:**
- Output: `ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json` / `hud_arbiter_log.json` / 更新 `hud_multiexpert_vs_single_comparison.md`

- [ ] **Step 1: 真实 LLM 跑总监裁决试点**

Run: `C:\Python312\python.exe Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py`
Expected: 打印 `LLM: anthropic/MiniMax M2.7` 与 `已落盘 arbiter fragment + log；维度数: N | 未解分歧/遗漏数: M`,退出码 0。
若 `client 加载失败`:确认用的是 `C:\Python312\python.exe`。

- [ ] **Step 2: 校验产物结构**

Run: `python -c "import json; d=json.load(open(r'ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json',encoding='utf-8')); sr=d['spec_fragments']['hud_spec']['selected_realization']; print('维度数:', len(sr), '| gap数:', len(d['capability_gaps']), '| mode:', d['metadata']['mode']); assert sr, 'selected_realization 不能为空'; assert d['metadata']['promotable'] is False; print('OK')"`
Expected: 打印维度数/gap数/mode=arbiter_pilot + `OK`

- [ ] **Step 3: 算覆盖对比数据**

Run: `python -c "import sys; sys.path.insert(0,'.'); import json; from Plugins.AgentBridge.Tests.scripts import hud_multiexpert_core as c; a=json.load(open(r'ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json',encoding='utf-8'))['spec_fragments']['hud_spec']['selected_realization']; s=json.load(open(r'ProjectState/Reports/2026-05-29/hud_llm_divergence_fragment.json',encoding='utf-8'))['spec_fragments']['hud_spec']['selected_realization']; print(json.dumps(c.compare_dimension_coverage(list(a), list(s)), ensure_ascii=False, indent=2))"`
Expected: 打印 only_in_multi / only_in_single / common 三组维度 id。

- [ ] **Step 4: 更新对比报告**

更新 `ProjectState/Reports/2026-05-31/hud_multiexpert_vs_single_comparison.md`,在原协商版双运行发现的基础上追加「总监裁决版」一节,含:总监版维度数 / gap 数（unresolved + missing）/ 调用次数（实测,预期 7）/ 与单专家覆盖对比（Step 3 数据）/ 一句结论:总监裁决是否消除了协商版的伪收敛/伪分歧问题、语义整合是否产出更连贯的统一 spec。**诚实记录**:总监"语义判同"本身是 LLM 单次判断,非跨运行确定;若出现 unresolved/missing 如实列出。

- [ ] **Step 5: 提交**

```bash
git add ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json ProjectState/Reports/2026-05-31/hud_arbiter_log.json ProjectState/Reports/2026-05-31/hud_multiexpert_vs_single_comparison.md
git commit -m "[skip-doc] test(pilot): HUD 总监裁决真实试点产物 + 三方对比更新"
```

---

## Task 4: 收尾门禁

- [ ] **Step 1: verification-before-completion**

调用 `superpowers:verification-before-completion`,逐条核对:纯逻辑测试 9/9 绿、总监版真跑退出码 0 且 selected_realization 非空、demo 无残留协商引用(grep)、范围未越界(未碰 domain_skill_runtime/agent_protocol/SkillTemplate/llm_client)、对比报告含总监版一节 + 诚实记录。

- [ ] **Step 2: document-release 门禁**

调用本项目 `document-release` skill。本次为试点编排替换 + 新证据,Coverage Map 记 Tests/scripts 改动 + Reports 证据;acceptance_report 附 3 追加一条 follow-up:总监裁决版试点结果（消除字符串比较缺陷的验证 + 是否值得作为推广首选方案）。这是 commit/push 前强制门禁。

- [ ] **Step 3: finishing-a-development-branch**

调用 `superpowers:finishing-a-development-branch`,完成 merge / PR。

---

## Self-Review

**Spec coverage:**
- spec §2.1 中立总监 → Task 2 Step 2 `ARBITER_PROMPT` ✅
- spec §2.2 编排（发现→立场→总监裁决→装配）→ Task 2 Step 3/4 ✅
- spec §2.3 一次性裁决 → Task 2 Step 3 `arbitrate` 单次调用 ✅
- spec §3.2 裁决输出契约 → Task 2 Step 3 prompt JSON 格式 ✅
- spec §3.3 装配规则（正常/unresolved/missing）→ Task 1 `assemble_arbitration_result` + 3 测试 ✅
- spec §4 core 保留 → Task 1 仅新增不删；Task 2 Step 6 grep 确认 demo 不再调用协商函数（core 函数仍在）✅
- spec §5.1 产物（hud_arbiter_fragment/log + 对比更新）→ Task 2 Step 4 + Task 3 ✅
- spec §5.2 成功判据 → Task 3 Step 2/3/4 + Task 4 Step 1 ✅
- spec §1.4 非目标（不碰主链、promotable=false）→ Task 2 metadata + Task 4 Step 1 复核 ✅

**Placeholder scan:** 无 TBD/TODO;每个代码步给完整代码;命令均带预期输出。Task 3 Step 4「更新对比报告」给了具体内容要求 + 数据来源命令,非空泛占位。

**Type consistency:** `assemble_arbitration_result(merged_dims, arbitration, stances) -> (selected, gaps)` 在 Task 1 定义、Task 2 Step 4 以 `final, gaps = core.assemble_arbitration_result(merged, arbitration, stances)` 调用一致;`arbitrate(...)` 返回 `{dimension_id: {final_choice, integration_note, unresolved}}` 与 `assemble_arbitration_result` 消费的 arbitration 结构一致;gap 的 `resolved_by` 值（arbiter_unresolved / arbiter_missing）在 core 实现与测试断言中一致。
