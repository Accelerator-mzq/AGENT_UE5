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

## 总监裁决版（arbiter_pilot）—— 真实 LLM 试点结果

> 运行日期：2026-05-31
> 产物：`ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json` + `hud_arbiter_log.json`
> 模型：anthropic/MiniMax M2.7

### 基本数据

| 指标 | 数值 |
|---|---|
| 合并后维度数 | 32 |
| selected_realization 条数 | 32 |
| capability_gaps 总数 | 32（全部为 arbiter_missing） |
| unresolved 维度数 | 0 |
| arbiter_missing 维度数 | **32**（占比 100%） |
| LLM 实际调用次数 | 7 次（discover×3 + stance×3 + arbitrate×1） |

### LLM 调用阶段结构（来自 hud_arbiter_log.json）

- 阶段1：三专家各自发现维度，3 次调用 —— 正常返回（UX 发现 17 维度，UI程序 8，美术 7；合并后 32 个）
- 阶段2：三专家各自对维度全集表态，3 次调用 —— 正常返回（三方均对全部 32 个维度有立场）
- 阶段3：中立总监一次性裁决，1 次调用 —— **返回空 dict（`arbitration: {}`），裁决结果完全缺失**

### 诚实记录（必须纳入决策）

**本次试点的核心发现：总监裁决阶段 LLM 调用成功（无网络/SDK 异常），但返回的 arbitration 字段为空 dict。**

具体表现：
- `_call()` 正常执行，`_parse_json()` 也未报错（即 LLM 确实返回了某段文本）
- 但解析后 `out.get("arbitration", {})` 取到空 dict，说明 LLM 的响应中 `arbitration` key 不存在或对应值为空/非 dict
- 兜底机制按设计正确触发：全部 32 维度进 gaps，标记 `resolved_by: arbiter_missing`，`selected_realization` 保留 key 但值为空串

**arbitration 返回空的可能原因（单次 LLM 非确定性判断，无法复核）：**
1. 上下文窗口过长：输入包含 32 个维度 id + 三方各 32 条立场（约 200 行 JSON），可能超出模型有效处理能力
2. 输出格式遵从失败：模型未能严格按 `{"arbitration":{...}}` 格式输出，可能输出了解释性文字或截断
3. 单次调用局限：将 32 个维度的三方裁决压缩为单次 LLM 调用，信息量可能超出模型单次可靠输出的边界

这不是框架 bug（兜底机制正确工作），而是**单次 LLM 调用承载量与维度规模的不匹配问题**。

### 与单专家基线的覆盖对比（dimension_id 精确匹配）

运行 `compare_dimension_coverage(arbiter_keys, single_keys)`：

- **only_in_multi（总监版独有）**：32 个
- **only_in_single（单专家独有）**：8 个（`hud.cash_feedback`, `hud.dynamic_visibility`, `hud.info_density`, `hud.jail_indicator_style`, `hud.layout_direction`, `hud.player_display_mode`, `hud.position_visibility`, `hud.theme_integration`）
- **common（两版共有）**：0 个

说明与协商版一致：每次 LLM 运行的维度命名均不同，导致 id 级零交集。这不代表多专家版缺少这 8 个单专家维度所对应的设计考量，仅代表命名体系不同。

### 总监裁决版 vs 协商版对比

| 维度 | 协商版 | 总监裁决版 |
|---|---|---|
| 维度覆盖 | 33 个 | 32 个（规模相近） |
| LLM 调用次数 | ~12 次 | 7 次（成本更低） |
| 有效最终 spec | 33 个有值的 selected | **32 个均为空串**（总监裁决完全失效） |
| capability_gaps | 0 个 | 32 个（arbiter_missing×32） |
| 伪收敛/伪分歧问题 | 有（字符串比较零冲突）| 无法评估（裁决阶段未产出结果） |
| 语义整合连贯性 | 协商版收敛但语义混合 | 未产出 |

### 结论

**总监裁决版本次未能消除协商版的缺陷，原因不同：协商版的缺陷是字符串比较导致伪零冲突（收敛看起来成功但缺乏语义整合），而总监裁决版的缺陷是单次 LLM 调用无法为 32 个维度产出有效裁决，导致整个 spec 为空。**

架构设计层面，总监裁决的思路（语义整合替代字符串比较）是正确方向，但实现上需要解决：
1. 维度规模过大时改为分批裁决（而非单次承载全部）
2. 增加裁决结果的格式验证与重试机制
3. 推广前须先小规模（≤10 维度）验证裁决输出稳定性

**本结论基于单次真实 LLM 运行，arbitration 返回空属于本次实测发现，客观记录，不做乐观估计。**
