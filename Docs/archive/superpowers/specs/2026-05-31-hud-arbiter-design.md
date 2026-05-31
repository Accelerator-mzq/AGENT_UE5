# HUD 总监裁决版设计

> 创建日期：2026-05-31
> 状态：Design / 待实施
> 关联工作流：Superpowers（brainstorming → writing-plans → executing-plans → verification-before-completion → finishing-a-development-branch）
> 前序：`Docs/archive/superpowers/specs/2026-05-31-hud-multiexpert-negotiation-design.md`（协商辩论版）+ 其双运行实测（`ProjectState/Reports/2026-05-31/hud_multiexpert_vs_single_comparison.md`）
> 落地范围：替换协商版编排，独立脚本，不碰编译主链

---

## 1. 背景与目标

### 1.1 协商辩论版的根因缺陷（已实测）

协商辩论版（收敛靠多轮辩论 + `detect_convergence` 字符串精确比较）两次真实 LLM 运行从相反方向暴露同一缺陷：

- 第 1 次（0 降级）：三专家各自发明不重叠的 dimension_id，无人对同一维度有异议 → 字符串比较认为"无冲突" → **伪收敛**。
- 第 2 次（32 降级）：三专家对同一维度高度共识但措辞不同 → 字符串比较认为"全冲突" → **伪分歧**（逐条核对 capability_gaps 三方 choices 实为同义）。

根因一致：**收敛判定停留在字符串精确匹配，无法识别语义同/异**。无论协商怎么辩，这个判定器都顶不住。

### 1.2 目标

把收敛机制从"协商辩论 + 字符串判定"替换为"中立总监 LLM 语义整合裁决"，从根上消除字符串比较缺陷——语义判同/判异交给 LLM 本就擅长的能力。

### 1.3 中立总监在 CCGS 中无直接对应（设计依据）

核实 CCGS 的总监层（creative-director 带创意愿景立场、technical-director 带技术立场、producer 偏流程协调）后确认：CCGS 无"中立、不带专业立场、只做设计内容语义整合"的角色——因为 CCGS 是人在环，真正的中立裁决由"坐在中间的人"完成，AI 只提供带立场的专业意见。本项目是无人编译链，需要一个 AI 角色顶替那个中立的人。故"中立整合者"prompt 自定义、不照搬 CCGS persona。

### 1.4 非目标 / YAGNI

- 不碰 `domain_skill_runtime` / `agent_protocol` / `SkillTemplate` / `llm_client` 编译主链。
- 不推广到 HUD 以外节点。
- 不接入 Stage 5/6/7。
- 试点产物标注 `promotable: false`。
- 不并排保留协商版脚本（直接替换；协商版诊断价值已记入 backlog FU-HUDME-01，历史保留在 git）。

---

## 2. 总监身份与编排

### 2.1 总监身份：中立整合者

不偏向 UX / UI程序 / 美术任何一方。职责：读三方对每个 HUD 维度的主张，识别"说法不同但意思相同"（合并）与"真实分歧"（择优 + 说明理由，或标记无法调和）；必须满足 GDD locked 约束。

### 2.2 编排流程

```
阶段1 各自发现（3 调用）   复用 discover() + core.merge_discovered_dimensions 合并去重
阶段2 各自立场（3 调用）   复用 stance()，三专家对合并后的维度全集各自表态
阶段3 总监裁决（1 调用）   中立总监读三方立场，一次性逐维度语义整合：
    每维度产出 final_choice + integration_note + unresolved(bool)
阶段4 装配                final_choice → selected_realization；
    unresolved=true 的维度额外写入 capability_gaps（附 integration_note + 三方原始立场）
```

成本：3 + 3 + 1 = 7 次 LLM 调用（协商版 ~12 次）。

### 2.3 实现粒度：一次性裁决

总监一次性裁决全部合并维度（单次长 prompt），不逐维度调用。理由：省成本 + MiniMax 长上下文足够。装配阶段校验"裁决是否覆盖全部合并维度"，漏掉的维度标记为 gap（见 §3.3）。若实测维度过多导致裁决粗糙，回退分批——本试点先用一次性。

---

## 3. 总监 prompt 与裁决产出契约

### 3.1 总监 system prompt（内联）

> 你是中立的设计整合者，不偏向 UX / UI 程序 / 美术任何一方。给你三位专家对一组 HUD 设计维度的各自主张。你的职责：对每个维度，识别三方是"说法不同但意思相同"（则合并成一个连贯统一的表述）还是"存在真实设计分歧"（则择优选择并说明理由；若三方诉求真实对立、无法在不牺牲某方硬需求下调和，则标记 unresolved=true）。必须遵守给定的 GDD locked 约束，不得违反。只输出 JSON，不要解释文字。

### 3.2 裁决输出契约

```json
{
  "arbitration": {
    "hud.xxx": {
      "final_choice": "统一后的最终设计选择",
      "integration_note": "三方一致，统一表述 / 采纳 UX 的 X，因为 ...",
      "unresolved": false
    }
  }
}
```

### 3.3 装配规则

- 每个合并维度 → 从 arbitration 取 `final_choice` 写入 `selected_realization[维度]`。
- `unresolved == true` → 该维度额外进 `capability_gaps`，记 `{dimension_id, integration_note, stances(三方原始立场), resolved_by: "arbiter_unresolved"}`。
- 裁决遗漏的合并维度（arbitration 中无此 key）→ 视为 gap，记 `resolved_by: "arbiter_missing"`，final_choice 兜底为空串。

---

## 4. core 函数处置

直接替换后，`detect_convergence` / `weighted_majority_fallback` / `resolve_owner` 在总监版中无人调用。**处置：保留（方案 A）**。

- 它们是纯函数、有通过的单元测试、无运行期开销，保留协商版的可复现资产（便于将来对照两种收敛机制）。
- 总监版仍调用 `merge_discovered_dimensions`（阶段1合并）与 `compare_dimension_coverage`（对比报告）。
- 不删除任何 core 函数或其测试；`test_hud_multiexpert_core.py` 6 用例保持全绿。

---

## 5. 产物、文件与风险

### 5.1 改动

| 类型 | 路径 | 说明 |
|---|---|---|
| 改造 | `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py` | 编排从协商辩论替换为总监裁决（去协商循环/detect_convergence调用/weighted_majority，加总监 prompt + 裁决调用 + 装配） |
| 保留 | `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py` | 按 §4 不删函数 |
| 产出 | `ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json` + `hud_arbiter_log.json` | fragment（promotable=false, mode=arbiter_pilot）+ 裁决全过程（三方立场 + 总监 arbitration） |
| 更新 | `ProjectState/Reports/2026-05-31/hud_multiexpert_vs_single_comparison.md` | 改为含总监裁决版的对比 + 协商版双运行非确定性发现的留痕 |
| 复用 | `llm_client.py`（用 `C:\Python312\python.exe` 运行） | 不修改 |

### 5.2 成功判据

| 维度 | 判据 |
|---|---|
| 根因消除 | 编排中不再有字符串相等的收敛判定；语义整合由总监 LLM 承担 |
| 覆盖 | 总监产出的 selected_realization 覆盖全部合并维度（漏的标 gap，不静默丢） |
| 诚实性 | 真实分歧由总监标 unresolved 并入 capability_gaps，不假装无分歧 |
| 成本 | 记录实际调用数（预期 7）与耗时，对比协商版 ~12 |
| 收敛稳定性 | 单次真跑能产出完整 fragment（无字符串比较导致的伪收敛/伪分歧） |

### 5.3 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| 总监一次性长 prompt 漏维度或裁决粗糙 | 中 | §3.3 装配校验覆盖率，漏的标 gap；过粗则回退分批 |
| 总监"语义判同"本身是 LLM 判断、非确定 | 中（方案固有） | 如实记录于裁决 log，标注不可 promote，单次真跑不跨运行声明稳定 |
| LLM 非确定性 / API 失败 | 中 | 复用协商版已加固的 `_call` 容错（call_error/parse_error 不崩） |
| 替换后 core 出现无引用函数 | 低 | §4 有意保留，有测试守护，非死代码风险 |

---

## 6. 后续（试点对比后，独立立项）

若总监裁决版数据支持推广：把总监 + 3 专家 prompt 抽为 SkillTemplate persona，改造 `LLMProvider` 支持"多专家发现→立场→总监裁决"编排，接入 `domain_skill_runtime` 主链，补 Stage 4→5→6→7 端到端回归。本试点结论基于单次真实 LLM 运行，未跨运行验证稳定性。
