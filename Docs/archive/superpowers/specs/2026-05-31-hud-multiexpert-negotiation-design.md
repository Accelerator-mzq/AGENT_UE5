# HUD 多专家协商试点设计

> 创建日期：2026-05-31
> 状态：Design / 待实施
> 关联工作流：Superpowers（brainstorming → writing-plans → executing-plans → verification-before-completion → finishing-a-development-branch）
> 触发来源：调查 baseline 发散落地修复后，用真实 LLM 跑出 HUD 发散产物，发现当前 LLM 在发散时被单个笼统的「HUD 专家」prompt 实例化，一人包揽 UX/UI程序/美术/无障碍多职责，导致每维度决策深度摊薄、维度清单由单专家一次性发现。借鉴 D:\ClaudeProject\Claude-Code-Game-Studios 的 team-ui 多 persona 分工思路。
> 落地范围：独立试点脚本，不碰编译主链

---

## 1. 背景与目标

### 1.1 问题诊断（已实证）

用真实 LLM（MiniMax M2.7）跑 HUD 单节点发散，产物 `ProjectState/Reports/2026-05-29/hud_llm_divergence_fragment.json` 与过程报告 `hud_llm_design_space_report.json` 暴露两点：

1. **单一笼统专家身份**：`SkillTemplates/baseline/hud/system_prompt.md` 把 LLM 实例化为一个「UE5 HUD 设计专家」，由它一人在 Discovery/Candidates/Convergence 三阶段包揽信息架构（UX）、数据绑定（UI 程序）、视觉主题（美术）、无障碍等本属不同专业的决策。每维度 rationale 因此被摊薄。
2. **维度由单专家一次性发现**：HUD 那 8 个 discovery_dimensions 是该 LLM 调用当场发现的（`generator_type: "llm"`），数量与划分随单次调用波动（heuristic 兜底只发现 4 个）；只有 5 个 locked_dimensions 是 GDD 真正锁定的硬约束。维度发现这一步没有多视角校验。

### 1.2 目标

用一个独立脚本，把 HUD 的发散从「单专家包办」改为「UX/UI程序/美术 三专家各自发现维度 → 协商分歧 → 收敛」，产出 HUD fragment，与已有单专家 LLM 产物对比，**用数据回答「多专家分工是否值得推广到框架」**。

### 1.3 非目标 / YAGNI

- 不修改 `domain_skill_runtime.py` / `agent_protocol.py` 编译主链。
- 不修改 SkillTemplate 结构（3 个专家 prompt 内联在脚本中，推广时再抽出为模板文件）。
- 不推广到 HUD 以外的节点。
- 不接入 Stage 5/6/7；试点只产出可对比的 HUD fragment + 协商过程记录。
- 试点产物标注「不可 promote」，不进真实交付链路。

---

## 2. 三专家职责边界

| 专家 | 主责 HUD 维度领域 | 关注点（system prompt 人设） |
|---|---|---|
| **ux-designer** | 信息密度、玩家信息展示、位置信息、动态显隐 | 信息完整性、可读性、认知负担、无障碍 |
| **ui-programmer** | 数据绑定可行性、刷新频率/触发、资金反馈机制 | 实现可行性、UI 不持有 gameplay 状态、性能 |
| **art-director** | 布局方向、视觉主题整合、监狱指示样式 | 视觉一致性、不遮挡棋盘、Monopoly 识别度 |

- 维度领域是「主责」，非硬隔离：协商阶段任何专家都可对其他专家的维度提异议（「信息全 vs 别遮棋盘」张力的来源即在此）。
- 三专家共享同一份 GDD locked 约束（28 格可见、required_hud_fields=[current_player, player_cash, turn_number]、弹窗非遮挡等），任何专家不可违反。
- 「主责」用于第 3 节降级阶段的加权多数：某维度主责专家的票权重更高。

---

## 3. 协商编排流程

```
阶段 0 · 准备
  载入 root_skill_contract + HUD 节点 + locked 约束（复用现有 run 的 Stage 1-3 产物作输入）

阶段 1 · 各自发现（3 次 LLM 调用）
  每个专家从自身视角发现 HUD 可设计维度 → 三份维度清单
  合并去重（按 dimension_id 语义归并）= 候选维度全集
  目的：治「单专家一次性拍脑袋列维度」，多视角补全覆盖

阶段 2 · 各自立场（3 次调用）
  对合并后的维度全集，每个专家给出自己主张的选择 + 理由

阶段 3 · 协商（多轮，每轮 3 次调用，max_rounds=2）
  把「三方立场 + 当前分歧维度」摆给每个专家 → 各自调整或坚持（带理由）
  收敛判定：逐维度比对三方选择是否一致
    全部维度一致 → 进阶段 4
    仍有分歧维度 → 进入下一轮；达到 max_rounds 仍分歧 → 进阶段 4 降级

阶段 4 · 收敛 / 兜底
  趋同维度 → 直接定稿
  残留分歧维度 → 降级：加权多数（主责专家票权重 2，其余各 1；仍平局取主责专家选择）
    残留分歧写入 fragment.capability_gaps + 协商记录
```

**调用量预估**：发现 3 + 立场 3 + 协商 3×2 + 收敛 0 ≈ **12~15 次 LLM 调用**（单专家版为 3 次）。该成本差正是试点要量化的对象。

**收敛判定的「一致」定义**：同一 dimension_id 下三方 chosen 候选值字符串相等。维度合并后若某专家未对某维度表态，视为弃权，不计入分歧。

---

## 4. 产物与对比

脚本落盘到 `ProjectState/Reports/<date>/`：

1. **`hud_multiexpert_fragment.json`** — 最终 HUD fragment，沿用 skill_fragment_v2 结构（含 selected_realization、design_decision_log、capability_gaps），metadata 标注 `promotable: false` 与 `mode: multiexpert_pilot`。
2. **`hud_multiexpert_negotiation_log.json`** — 协商全过程：阶段 1 各专家维度清单、合并结果、每轮各专家立场、分歧维度、收敛或降级方式。
3. **`hud_multiexpert_vs_single_comparison.md`** — 与单专家版（`hud_llm_divergence_fragment.json`）三栏对比。

**成功判据（试点结论以数据为准，不靠主观）**：

| 维度 | 判据 |
|---|---|
| 维度覆盖 | 多专家合并后发现的维度数 ≥ 单专家版，并能具体指出单专家漏掉的维度 |
| 收敛性 | 能在 max_rounds 内收敛，或干净降级（不死循环、不抛异常） |
| 成本 | 记录实际 LLM 调用次数与总耗时 |
| 论证深度 | 抽样对比同一维度在两版中的 rationale 详尽度与是否体现专业视角差异 |

试点结论：基于以上四项，给出「质量提升是否抵得过成本」的明确判断，作为「是否推广到框架」的决策依据。

---

## 5. 文件结构与风险

### 5.1 新增 / 复用

| 类型 | 路径 | 说明 |
|---|---|---|
| 新增 | `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py` | 试点主脚本，含协商编排 + 3 专家内联 prompt |
| 产出 | `ProjectState/Reports/<date>/hud_multiexpert_*.{json,md}` | 见第 4 节 |
| 复用 | `Plugins/AgentBridge/Compiler/stages/llm_client.py` | 用 `C:\Python312\python.exe`（带 anthropic SDK）运行 |
| 复用 | `ProjectState/runs/run-20260417-051444-a2b8/`（root_skill_contract / skill_graph / clarification_gate_report） | 作为 Stage 1-3 输入 |

- 3 个专家的 system prompt 内联在脚本常量中（试点阶段不新建模板文件，YAGNI；推广时再抽出为 SkillTemplate persona）。
- 不依赖也不修改编译主链；脚本自带 LLM 调用与 JSON 解析（解析逻辑可参考 agent_protocol 的健壮性处理，但不 import 主链执行函数，避免耦合）。

### 5.2 风险

| 风险 | 等级 | 缓解 |
|---|---|---|
| LLM 非确定性导致协商震荡 | 中 | max_rounds=2 兜底；产物标注不可 promote；协商记录完整留痕便于复盘 |
| 真实 API 调用消耗额度 | 中 | 单次试点 12~15 调用，范围可控；只跑 HUD 单节点 |
| 试点结论不等于框架可用性 | 低（已知边界） | 诚实声明：试点验证「思路 + 产物质量 + 成本」层面，推广到框架需另立项（改 SkillTemplate + LLMProvider） |
| 维度合并去重的语义归并不准 | 中 | 阶段 1 合并按 dimension_id 归并；不同 id 但语义重复的情况记入协商记录由人工判断，不强行自动合并 |

---

## 6. 后续（试点通过后，独立立项，非本次范围）

若试点数据支持推广：把 3 专家 prompt 抽为 HUD SkillTemplate 下的 persona 文件，改造 `LLMProvider` 支持「多 persona 发现→协商→收敛」编排，接入 `domain_skill_runtime` 主链，并补端到端回归（Stage 4→5→6→7）。该改造涉及编译核心，须单独走完整 brainstorming → 设计 → 评审。
