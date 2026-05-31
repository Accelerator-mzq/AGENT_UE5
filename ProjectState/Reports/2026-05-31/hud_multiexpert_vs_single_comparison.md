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
