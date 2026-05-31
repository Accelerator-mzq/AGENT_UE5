# Baseline realization_eligible 发散落地修复设计

> 创建日期：2026-05-29
> 状态：Design / 待实施
> 关联工作流：Superpowers（brainstorming → writing-plans → executing-plans → verification-before-completion → finishing-a-development-branch）
> 触发来源：评估从 `D:\ClaudeProject\Claude-Code-Game-Studios` 补充 SkillTemplate 模板包时，发现 realization_eligible baseline 节点的发散结果未落入 spec_fragments，属编译器既有缺陷，优先于新增模板修复。
> 影响文件：`Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`（Compiler 可改区）

---

## 1. 背景与问题诊断

### 1.1 缺陷现象

realization_eligible baseline 节点（当前仅 HUD）虽然会执行 Design Space Discovery → Candidates → Convergence 三阶段发散，并产出真实的 `converged_pack`，但**发散收敛结果只进入了 `design_decision_log`（决策理由），没有进入 `spec_fragments`（真正交给下游 Stage 5/6/7 的 spec 主体）**。结果是 baseline 的 spec 主体是固定结构，下游消费方看到的内容不随发散变化——即「跑了发散，但产物固定」。

### 1.2 证据（独立对照代码确认，非推断）

**gameplay 路径会把发散写进 spec：** `domain_skill_runtime.py` `_build_gameplay_spec_fragment`（行 312 起）

- 行 330–337：从 `converged_pack` 提取 `convergence_choices` → 构建 `dimension_choices`
- 行 385：`"selected_realization": dimension_choices` —— 发散结果写入 spec

**baseline 路径不吃发散：** `_build_baseline_spec_fragment`（行 465–501）

- 签名（行 465–469）：`(node, capability, clarification_gate_report)` —— **无 `converged_pack` 参数**
- 行 472–501：spec 字段全部来自硬编码 capability + `instance_id` 特判（HUD/settings/platform），**无 `selected_realization`**

**调用处的硬编码：** `_build_discovered_fragment` baseline 分支（行 618–623）

```python
design_decision_log = _build_converged_decision_log(node, design_space_report, converged_pack)   # 吃发散
spec_fragments = _build_baseline_spec_fragment(
    node,
    {"baseline_item": "HUD", "realization_class": "realization_eligible",
     "required_elements": root_skill_contract["constraint_fields"]["ui.required_hud_fields"]["value"]},  # 硬编码 HUD
    clarification_gate_report,                                                                            # 不传 converged_pack
)
```

此处不仅没传 `converged_pack`，还把 capability 写死为 HUD —— 任何走该路径的 baseline 节点都会被当成 HUD 处理。

### 1.3 下游早已为修复做好准备（佐证这是遗漏而非设计意图）

- Stage 6 Lowering `lowering_v2.py:277`：`"selected_realization": spec.get("selected_realization", {})` —— 已主动读取该字段，baseline 此前一直返回空。
- `Schemas/examples/phase11_build_ir_v2.example.json`：示例 spec 明确含 `selected_realization`。
- Schema `skill_fragment_v2.schema.json`（行 29–32）：`spec_fragments` 定义为 `additionalProperties: {"type": "object"}`，对新增字段无限制。

### 1.4 目标

1. 让 realization_eligible baseline 节点的 `spec_fragments` 携带 `selected_realization`，与 gameplay 节点对称，使发散真正落地。
2. 去掉 baseline 分支的 HUD 硬编码，改为按节点动态取 capability，使该路径对任意 realization_eligible baseline 通用（为后续 audio_foundation 升级铺路）。
3. 在现有 HUD 上验证：发散落地 + 既有语义不变 + 下游不破。

### 1.5 非目标 / YAGNI

- 不在本次新增 audio_foundation 模板（后置）。
- 不在本次做第一档模板提质（economy / baseline UI 的 domain_prompt + optional schema，后置）。
- 不改动 presence_only / clarification_gated baseline 的最小 fragment 路径。
- 不引入新的 schema 字段约束（沿用 `additionalProperties` 自由结构）。

---

## 2. 设计

全部改动落在 `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`（Compiler 可改区）。

### 2.1 `_build_baseline_spec_fragment`（行 465–501）

- 新增参数 `converged_pack: Dict[str, Any] | None = None`，默认 None / `{}`，保持 presence_only 等其他调用处兼容（不传即维持现状）。
- 当 `realization_class == "realization_eligible"` 且 `converged_pack` 非空时：复用 gameplay 行 330–337 的同款逻辑提取 `convergence_choices` → 写入 `spec["selected_realization"]`。
- 保留现有 `instance_id` 特判（settings 的 `persistence`、platform 的 `platform_scope`、HUD 的 `notes`）。

### 2.2 `_build_discovered_fragment` baseline 分支（行 618–623）

- 删除硬编码的 `{"baseline_item": "HUD", ..., constraint_fields["ui.required_hud_fields"]}`。
- 改为按 `node.capability_id` 从 `root_skill_contract.baseline_capabilities` 动态查找对应 capability（复用行 89–91 已有的遍历逻辑；`baseline_capabilities` 每项结构含 `capability_id` / `baseline_item` / `realization_class` / `required_elements` 或 `required_controls` / `activation`，字段充分）。
- 将 `converged_pack` 传入 `_build_baseline_spec_fragment`。

### 2.3 HUD required_elements 等价性处理

HUD 当前的 `required_elements` 来自 `constraint_fields["ui.required_hud_fields"]`，泛化后改从 `baseline_capabilities` 的 HUD 项取。两者需验证等价（见 §3）：

- 若等价：直接采用 `baseline_capabilities`，HUD 产出除新增 `selected_realization` 外不变。
- 若不等价：在 HUD 分支保留从 `constraint_fields` 取 `required_elements` 的特殊处理，仅对其余 baseline 节点走通用路径。

---

## 3. 回归验证

对应「先在 HUD 上验证」的决策：

1. **发散落地验证**：重跑产生 HUD fragment 的链路，确认 HUD 的 `spec_fragments.hud_spec` **新增 `selected_realization`**，且其值来源于 `converged_pack` 的 convergence 选择。
2. **语义等价验证**：对比改动前后 HUD 的 `required_elements` 等既有字段保持一致（不一致则走 §2.3 的保留分支）。
3. **契约验证**：`python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` 通过。
4. **链路验证**：运行相关系统测试 stage（`Plugins/AgentBridge/Tests/run_system_tests.py`，至少覆盖 Stage 4/5/6/7 的 baseline 路径），确认 Cross Review / Lowering / Handoff 不破。

证据落盘：`ProjectState/Reports/2026-05-29/`（改动前后 HUD fragment 对比 + 测试输出）。

---

## 4. 风险

| 风险 | 等级 | 缓解 |
| --- | --- | --- |
| 下游消费方对 baseline spec 字段有强假设 | 低 | 已确认 Stage 5 通用遍历、Stage 6 用 `.get()`、Stage 7 不读 spec_fragments |
| Schema 校验失败 | 低 | `additionalProperties:{"type":"object"}` 允许新增字段；gameplay 早有 `selected_realization` 佐证 |
| HUD required_elements 来源切换导致语义漂移 | 中 | §3 步骤 2 回归对比兜底，不等价则保留特殊取法 |
| 改动核心编译逻辑波及现有 run 等价性 | 中 | 仅对 realization_eligible baseline 增量；presence/gameplay 路径不动；重跑对比 |

---

## 5. 范围边界与后续

本次仅修发散落地缺陷并在 HUD 验证。验证通过后，依次推进（各自独立成轮）：

1. **新增 `baseline/audio_foundation` 模板**：填实既有 `baseline-audio-foundation` 占位节点（`skill_graph_planning.py:174`，`FRAGMENT_FAMILY_MAP` 已含 `audio_foundation_spec`），6 件套；以 CCGS `audio-director.md` / `sound-designer.md`（剥离协作协议，仅取领域人格与方法论）+ `sound-bible.md`（取 audio_events / sfx_categories / music_states / naming_convention 四块）为蓝本；升 realization_eligible 后即可复用本次修好的发散落地路径。
2. **第一档模板提质**：economy（CCGS economy-model 的水龙头/水槽/资金守恒，剔除基尼/高级货币/抽卡保底）+ baseline UI（CCGS team-ui 的不持有状态/本地化/双输入/无障碍）；仅改 domain_prompt + optional schema 字段，向后兼容。
