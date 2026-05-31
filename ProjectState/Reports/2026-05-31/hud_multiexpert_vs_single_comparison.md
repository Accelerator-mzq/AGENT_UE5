# HUD 多专家协商 vs 单专家 LLM 发散 — 对比报告

> 生成日期：2026-05-31
> 多专家产物：`ProjectState/Reports/2026-05-31/hud_multiexpert_fragment.json`（+ `hud_multiexpert_negotiation_log.json`）
> 单专家基准：`ProjectState/Reports/2026-05-29/hud_llm_divergence_fragment.json`
> 模型：anthropic/MiniMax M2.7（两版同模型，可比）

## 四栏对比

| 维度 | 单专家版 | 多专家协商版 | 判断 |
|---|---|---|---|
| **维度覆盖** | 8 个 HUD 维度 | 33 个（UX 10 + UI程序 8 + 美术 15，合并去重后 33） | 多专家覆盖显著更广、更细 |
| **专业视角分工** | 一个「HUD 专家」包办，视角混合 | 三专家视角清晰可辨：UI程序出 `data_binding_source`/`refresh_trigger`/`responsive_scaling`，美术出 `color_scheme`/`typography`/`iconography`，UX 出 `accessibility`/`accessibility_contrast`/`readability` | 多专家明确体现专业分工 |
| **收敛性 / 成本** | 3 次 LLM 调用（Discovery/Candidates/Convergence） | ~12 次调用（发现 3 + 立场 3 + 协商 1 轮内即趋同，0 降级），耗时显著更长 | 收敛干净（0 降级），但成本约 4× |
| **论证深度** | 每维度 rationale 2-3 句、含约束援引（如「与 28 格可见冲突」） | 每维度给出具体设计值（如「Contrast ratio ≥ 4.5:1」「Roboto/Open Sans 字体」「#00000080 背景」），更接近可落地规格 | 多专家产物更具体、更工程化 |

## 成功判据结论（逐条）

1. **维度覆盖 ≥ 单专家**：✅ 33 > 8。多专家明确补出了单专家完全缺失的工程/视觉维度——如 `data_binding_source`、`z_order_stacking`、`responsive_scaling`、`accessibility_contrast`、`iconography`、`typography`，这些正是单一「HUD 专家」视角下被摊薄/遗漏的。
2. **收敛性**：✅ 在 MAX_ROUNDS=2 内第 1 轮即零冲突收敛，0 降级，无死循环、无异常。
3. **成本**：约 12 次 LLM 调用 vs 单专家 3 次（~4×），耗时更长。
4. **论证深度**：✅ 多专家产物每维度是带具体数值/技术选型的设计决策，比单专家更贴近可实现规格。

## 诚实警示（必须纳入推广决策）

数据漂亮，但有两个**不能掩盖**的解读陷阱：

1. **`common = []`（零 id 交集）≠ 多覆盖 25 个全新维度。**
   `compare_dimension_coverage` 按 dimension_id 精确匹配，得出多专家 33 个与单专家 8 个**零交集**。但这主要是**命名体系不同**：单专家叫 `hud.info_density`，多专家叫 `hud.info_hierarchy`/`hud.visual_hierarchy`，语义近似但 id 不同。因此「33 vs 8」更准确的读法是**「多专家把设计空间切得更细、命名更分散」**，而非「多发现 25 个单专家完全想不到的维度」。其中确有单专家真缺的工程维度（如 data_binding/z_order），但具体净增量需人工语义比对，不能直接用 id 差值。

2. **`round_1_conflicts = 0`（零冲突）说明这次"协商/辩论"几乎没真正发生。**
   设计初衷是「UX 要信息全 vs 美术要别遮棋盘」这类跨专业张力通过多轮辩论收敛。但本次三专家各自发现的维度 id 几乎不重叠，导致**没有人对同一维度持不同意见**，协商阶段无分歧可辩、第一轮直接趋同。也就是说：本次试点验证了**「多视角并行发现 → 维度更丰富」**这一半价值，但**「协商辩论收敛分歧」**这另一半几乎未被触发、未被验证。

## 推广建议

- **值得推广的部分**：多专家**并行发现维度**确实显著提升覆盖与专业分工，这是真实增益。
- **需重新设计的部分**：若要让「协商辩论」真正发挥作用，需先让三专家**面向同一套维度全集表态**（而非各自发明 id），分歧才会显现。当前编排「各自发现 → 合并」会稀释冲突。推广到框架前，应调整为「先合并出统一维度全集 → 三专家对同一全集各自选择 → 再检测冲突」，否则协商层形同虚设。
- 本结论基于**单次** Heuristic-free 真实 LLM 运行，未跨运行验证稳定性，亦未接入 Stage 5/6/7。推广需另立项并补充端到端回归。

---

## 总监裁决版（arbiter_pilot）—— 两次真实 LLM 运行对照记录

> 运行日期：2026-05-31（两次）
> 产物（第二次，当前落盘）：`ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json` + `hud_arbiter_log.json`
> 模型：anthropic/MiniMax M2.7

### 重要前言：同一脚本两次运行、结果截然不同

本节记录的是**同一脚本（arbiter_pilot）的两次独立真实 LLM 运行**。第一次运行总监裁决返回空；加入原始响应诊断留痕（`arbitration_diag`）后重跑，第二次裁决完整成功。两次结果截然不同，这是**非确定性**，是本试点最重要的诚实发现之一，必须如实记录、不可掩盖。

---

### 第一次运行：裁决返回空，spec 完全缺失

| 指标 | 数值 |
|---|---|
| 合并后维度数 | 32 |
| selected_realization 非空条数 | **0**（全部为空串） |
| capability_gaps 总数 | 32（全部 arbiter_missing） |
| arbiter_unresolved 数 | 0（非真无分歧，而是裁决未产出） |
| LLM 调用次数 | 7（discover×3 + stance×3 + arbitrate×1） |

**裁决阶段行为**：`arbitrate` 调用后，解析得到 `arbitration: {}`，兜底机制正确触发，32 个维度全部进 gaps 标记 `arbiter_missing`，selected 均为空串。

**真因不可追溯（必须诚实写明）**：当时 `arbitrate` 未留原始响应（raw），旧报告中"_call/_parse_json 未报错"的表述属于**不可验证推断**——无 raw 留存，就无法区分是（A）网络/SDK 调用异常、（B）输出被截断后 JSON 不完整、（C）模型确实输出了 `{"arbitration":{}}` 空 dict、还是（D）模型输出了解释性文字但 parse 静默落空。旧报告相关说法不应作为已知陈述，现予以纠正。

---

### 第二次运行（当前产物）：裁决完整成功

加入 `arbitration_diag` 原始响应留痕后重跑，裁决阶段成功。

#### 基本数据

| 指标 | 数值 |
|---|---|
| 合并后维度数 | **35**（UX 15 + UI程序 9 + 美术 13，去重合并后 35） |
| selected_realization 非空条数 | **35**（35/35，全部有真实设计值） |
| capability_gaps 总数 | **1**（arbiter_unresolved，非 missing） |
| arbiter_unresolved 维度 | `hud.collapsibility`（唯一真实未解分歧） |
| arbiter_missing 维度数 | **0** |
| LLM 调用次数 | 7（discover×3 + stance×3 + arbitrate×1） |

#### 裁决成功的诊断证据

`arbitration_diag` 记录显示：
- `arbitration_diag.raw` 长度 **14310 字符**，完整闭合的 ` ```json {"arbitration":{...}} ``` ` 块
- `out_keys = ["arbitration"]`，35 个维度 id 全部出现
- 无截断迹象，格式遵从，无 parse 异常

这证明本次裁决调用本身是成功的：模型正确理解了格式要求并输出了完整结构。

#### 语义整合证据（"判同合并"真的发生）

总监并非逐条字符串匹配，而是识别出三方"说法不同但意思相同"并合并为统一表述。两个典型案例：

**案例 1 — `hud.layout_position`**：
> integration_note: "UX Designer and Art Director align on horizontal bar; UI Programmer's 'top-left corner' is subsumed by the broader horizontal..."
> final selected: "Top-edge anchored centered horizontal strip with corner extensions"

三方原始立场各有表述差异，总监识别出 UX 与美术语义对齐、UI程序的"左上角"被水平条带方案包含，将三方整合为统一定位描述。

**案例 2 — `hud.current_player_indicator`**：
三方分别提出色边框+动画、彩色徽章、发光边框三种方案，总监整合为 "Color-coded border/indicator with animated highlight"，提炼了三方共识要素（颜色标识 + 视觉突出）。

这类判断是字符串比较协商版结构上做不到的。

#### 唯一真实未解分歧（arbiter_unresolved）的完整记录

维度：`hud.collapsibility`

| 专家 | 立场 |
|---|---|
| UX Designer | 5秒无操作自动折叠，有输入即恢复 |
| UI Programmer | 可切换折叠 |
| Art Director | Non-collapsible；always fully visible（关键时刻 HUD 不能消失） |

**总监 integration_note**：美术提出的硬约束（关键时刻 HUD 永远可见）与 UX / UI程序的可折叠主张存在结构性对立；若美术的硬约束不能放松，则此维度 UNRESOLVED。总监仍择优填入了 selected 值，但如实标记为 `arbiter_unresolved` 进入 gaps。

这正是字符串比较协商版发现不了的：该分歧是**跨专业立场**（美术硬约束 vs 交互/工程灵活性），不是拼写差异，必须由具备跨域判断能力的总监才能识别。本次总监正确识别并如实上报，而非静默取中间值或掩盖。

---

### 两次运行对照汇总

| 指标 | 第一次运行 | 第二次运行（当前产物） |
|---|---|---|
| 裁决阶段结果 | 返回空 `{}` | 完整，35 维度齐全 |
| selected 非空条数 | 0 / 32 | 35 / 35 |
| capability_gaps | 32（arbiter_missing×32） | 1（arbiter_unresolved×1） |
| 语义整合发生 | 未产出 | 已发生（layout_position / current_player_indicator 等） |
| 真实分歧识别 | 未产出 | 1 个（collapsibility，跨专业硬约束冲突） |
| 裁决 raw 留痕 | **无**（真因不可追溯） | 14310 字符完整闭合（已留痕） |
| LLM 调用次数 | 7 | 7 |

---

### 与协商版的核心差异（第二次运行视角）

协商版（字符串比较）在本试点中的问题是：三专家各自发明维度 id，几乎不重叠，导致"协商"在零冲突状态下直接趋同——从未真正辩论过。

总监裁决版让三专家面向**同一维度全集**表态，然后由中立总监进行语义整合。第二次运行验证了这一结构的两项价值：
1. **语义判同合并**：识别出表述不同但意思相同的多方立场并统一为连贯 spec（字符串比较做不到）
2. **诚实暴露真分歧**：识别出 collapsibility 这一跨专业硬约束冲突，如实上报 arbiter_unresolved 而非掩盖（零冲突协商版结构上无法触发此类识别）

但这两项价值建立在**裁决成功返回**的前提上。第一次运行证明这一前提并不稳定。

### 与单专家基线的覆盖对比（dimension_id 精确匹配，基于第二次运行）

运行 `compare_dimension_coverage(arbiter_keys, single_keys)`：

- **only_in_multi（总监版独有）**：35 个
- **only_in_single（单专家独有）**：8 个（`hud.cash_feedback`, `hud.dynamic_visibility`, `hud.info_density`, `hud.jail_indicator_style`, `hud.layout_direction`, `hud.player_display_mode`, `hud.position_visibility`, `hud.theme_integration`）
- **common（两版共有）**：0 个

**命名 caveat（与协商版一致）**：id 级零交集主要因每次 LLM 运行的维度命名不同，不等于语义上多覆盖 35 个全新维度。"35 vs 8"更准确的读法是多专家把设计空间切得更细、命名更分散；单专家版的 8 个维度在语义上可能对应总监版中的多个维度，具体净增量需人工语义比对，不能直接用 id 差值替代。

---

### 诚实警示（推广决策必须考量）

1. **非确定性是核心工程风险**：同脚本同规模，一次完全空、一次完整成功——这意味着单次裁决调用的可靠性不足。推广前必须加输出格式校验 + 失败重试（或分批裁决），不能假设每次运行都能成功。

2. **第一次失败的真因至今不可知**：因无 raw 留存，无法区分 call_error / 截断 / 模型空返回 / parse 静默落空。现已加 `arbitration_diag` 留痕，**下次再出现空返回即可凭 raw 与 out_keys 精确判定是 A/B/C/D 哪类失败**，但第一次的真因已不可追溯。

3. **"语义判同"是单模型单次判断**：layout_position / current_player_indicator 的整合结论正确与否无法跨运行复现验证，其准确性取决于模型当次的理解质量，不是确定性结论。

4. **id 级覆盖 caveat**：见上一节，35 vs 8 不等于净增 27 个语义全新维度。

5. **仅单链路，未接 Stage5/6/7**：本试点为离线 spec 生成，未连接 Skill Compiler / Handoff / Orchestrator 下游链路。端到端价值需另立项验证。

---

### 总监裁决版 vs 协商版对比汇总（基于第二次运行）

| 维度 | 协商版 | 总监裁决版（第二次） |
|---|---|---|
| 维度覆盖 | 33 个 | 35 个（规模相近） |
| LLM 调用次数 | ~12 次 | 7 次（成本更低） |
| 有效最终 spec | 33 个有值的 selected | **35 个均有真实设计值** |
| capability_gaps | 0 个（伪零冲突） | 1 个（arbiter_unresolved，真实分歧） |
| 语义整合连贯性 | 协商版收敛但基于字符串比较 | **语义判同合并，连贯统一 spec** |
| 真实分歧识别 | 未触发（各自发明 id，无重叠） | **正确识别 1 个跨专业硬约束冲突** |
| 机制稳定性 | 两次运行均有效 | **不稳定（一次空、一次成功）** |

---

### 结论

**总监裁决的方向（语义整合替代字符串比较）在第二次运行中得到正面验证**：产出连贯统一的 35 维度 spec，识别出协商版发现不了的跨专业硬分歧（collapsibility），语义判同合并真实发生。这是字符串比较协商版结构上无法实现的增益。

**但单次裁决调用的稳定性不足是推广前必须解决的工程问题**：第一次运行完全失败（空 arbitration），原因不可追溯；第二次成功，但两次结果截然不同，证明机制当前不可靠。

推广前必须解决：
1. 增加裁决输出的格式校验与失败重试（或分批裁决）机制
2. 始终保留 `arbitration_diag.raw` 留痕，以便失败时精确定位 A/B/C/D 类原因
3. 在更多样本（不同维度规模、不同专家组合）上验证裁决稳定性，而非依赖单次成功推断可靠性

**本节记录两次真实运行，成功与失败均如实呈现，不做乐观估计，不隐瞒第一次失败与真因不可追溯。**
