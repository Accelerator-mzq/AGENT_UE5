# Stage 4 Candidates Prompt vs Provider 诊断报告

## 1. 目标

验证 `Candidates` 阶段失败更接近哪一种原因：

1. `prompt` / 上下文过重，超过当前 provider + relay 可稳定承载的阈值
2. provider / relay 本身在轻载下也不稳定

## 2. 测试环境

- 配置文件：`Plugins/AgentBridge/Config/llm_config.yaml`
- 当前配置快照：
  - `provider = anthropic`
  - `model = MiniMax M2.7`
  - `base_url = https://api.minimaxi.com/anthropic`
  - `timeout_sec = 60`
- 目标节点：`skill-board-topology`
- Discovery 输入来源：
  - [stage4_segmented_single_node_discovery.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/stage4_segmented_single_node_discovery.json)

## 3. 对照组设计

### A. Provider 小请求基线

- 只发送一个极小 JSON-only 请求
- 目的：验证 provider / relay 在轻载下是否稳定

### B. Candidates 单维度分批

- 仅保留 1 个 `discovery_dimension`
- 保留最小必要结构
- 目的：验证“按维度分批生成”是否可行

### C. Candidates 压缩版全维度

- 保留 7 个 `discovery_dimensions`
- 去掉较重但弱相关的上下文块
- 目的：验证“只靠压缩上下文”是否足够

### D. Candidates 全量版

- 保留当前主链完整上下文
- 目的：作为现有实现的对照基线

## 4. 实验产物

- 首轮实验原始结果：
  - [stage4_candidates_prompt_vs_provider_diagnostic.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic.json)
- 双样本复测结果：
  - [stage4_candidates_prompt_vs_provider_diagnostic_repeat2.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic_repeat2.json)
- 实验脚本：
  - [stage4_candidates_diagnostic.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/scripts/stage4_candidates_diagnostic.py)

## 5. 关键结果

### 5.1 Provider 小请求基线

- 3/3 成功
- 用时约 `3.88s ~ 7.81s`
- 返回均为合法 JSON

结论：当前 provider / relay **不是轻载即不稳定**。

### 5.2 Candidates 单维度分批

- 原始调用 3/3 成功（首轮 1 次 + 复测 2 次）
- 用时约 `26.71s ~ 32.91s`
- `phase_generate` 成功
- `validation_errors = []`
- `candidate_group_count = 1`

结论：当 `Candidates` 被拆成“单维度分批”后，当前链路可以稳定工作。

### 5.3 Candidates 压缩版全维度

- 首轮 1/1 失败
- 复测 2/2 失败
- 失败用时稳定在 `181.80s ~ 181.84s`
- 统一错误：
  - `Request timed out or interrupted`

结论：即使去掉较重上下文，只要一次吃下 7 个维度，当前链路仍然会稳定超时。

### 5.4 Candidates 全量版

- 首轮 1/1 失败，出现过一次 `529 overloaded_error`
- 复测 2/2 失败
- 复测失败用时稳定在 `181.89s ~ 182.15s`
- 统一错误：
  - `Request timed out or interrupted`

结论：全量版比压缩版更重，但两者都跨过了当前 provider + relay 的稳定阈值。

## 6. 最终判断

本次实验更支持下面这个结论：

> **主因是 `Candidates` 请求负载过重。**
> 不是 provider 在轻载下随机失稳，而是当前 provider + relay 组合在“7 维度一次性生成 Candidates”这类负载下，稳定进入超时区间。

更准确地说：

- `provider 本身就不稳`：**不成立**
  - 轻载小请求稳定
  - 单维度分批也稳定
- `prompt 太重 / 任务太重`：**成立**
  - 压缩版全维度与全量版都稳定失败
  - 失败模式高度一致，说明不是偶发抖动，而是负载阈值问题

## 7. 对实现方向的直接启示

当前最合理的工程方向不是继续放大单次 `Candidates` 请求，而是：

1. 将 `Candidates` 改为按 `discovery_dimension` 分批生成
2. 逐批保存中间结果，再做聚合
3. 不再依赖“一次请求吞下完整 `design_space_report`”

换句话说，`batch by dimension` 不是临时 workaround，而是当前 provider 约束下更符合第一性原理的实现路径。
