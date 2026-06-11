# Phase 13 验收判据 6:双端驱动等价性对比报告

> 日期:2026-06-11
> 对应 runbook 步骤 8-9(`ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md`)
> 同一 GDD:`ProjectInputs/GDD/monopoly_extended_auction_v1.md`

## 两端运行档案

| 项 | Claude Code 端 | Codex 端 |
|---|---|---|
| run_id | run-20260611-052252-5101 | run-20260611-073328-cec6 |
| 驱动方式 | MCP stdio 协议(`mcp_driver.py`,py312 mcp 客户端直连 server.py) | codex CLI 0.130.0 经 `~/.codex/config.toml` 注册的同一 server.py |
| agent 模型 | Claude(Fable 5,本会话) | GPT-5.5(CodexPlusPlus 本地代理) |
| 范围 | 步骤 1-7 全链(含审批后 Stage 4-7 + promote 拒绝) | 步骤 1-4(按 runbook 止于 pending_review,不审批) |

## 等价断言结果(全部通过)

| # | 断言 | 结果 | 证据 |
|---|---|---|---|
| 1 | capability_gaps 集合一致 | ✅ `['gameplay-property-auction', 'gameplay-stock-market']`,且 **source_anchor 值逐项一致**(2.1 地产拍卖 / 2.2 股票市场) | Claude 审批前存档 `TestArtifacts/phase13_acceptance/stage3_prepare_out.json` vs Codex `ProjectState/runs/run-20260611-073328-cec6/skill_graph.json` |
| 2 | Codex 全部 stage 产物 schema 校验通过 | ✅ root_skill_contract / clarification_gate_report / skill_graph / gdd_coverage_matrix 四产物 Draft7 零错误 | 本报告生成时实跑校验 |
| 3 | 两个合成包通过机器校验(save 成功) | ✅ 双包 `synthesis_validator` 复核 PASS,`review_status: pending_review`,provenance 戳 Codex 自己的 run_id + `synthesized_by: mcp_agent` | 包目录见下;`codex_drive_log5.txt` |
| 4 | 双端 required capability 全带 source_anchor | ✅ 双端缺 anchor 清单均为空 | 双端 root_skill_contract.json |
| 5 | 重试闭环在独立 agent 上实证 | ✅ Codex 拍卖包**首提被机器校验拒**(缺 `realization_class`),按 errors 自行修正重提成功(retry_rounds: auction=1, stock=0)——非脚本预演,是真实独立 agent 的重试 | `codex_drive_log5.txt`:"第一次提交被机器校验拒绝,原因明确:manifest.yaml 缺少必填 realization_class。我只补这个字段后重提" |

按 runbook 约定:**不要求内容字节一致**(LLM 非确定性),仅结构等价——双端各自创作的 domain_prompt/output_schema 内容不同,均忠实 GDD。

## 过程偏差与发现(如实记录)

1. **codex exec 非交互 MCP 审批闸门**:`approval_policy=never` 只放行 shell 不放行 MCP 工具调用(1.6ms 即被自动取消),最终用 `--dangerously-bypass-approvals-and-sandbox` 放行(受控验收场景:本机 + msc 授权 + 提示词限定只用 agentbridge 工具)。前三次驱动失败均系此因(另有一次因 stdin 非 TTY 挂起,属 codex exec 用法问题)。
2. **治理发现(记 backlog)**:第四次驱动 gap=0 的根因——Claude 端已审批包的备份目录 `synthesized.cc-approved.bak` 放在 `SkillTemplates/` 树内,registry rglob 把它当**正式库**默认信任(绕过 synthesized/ 审批门)。实证了"`SkillTemplates/` 树内任何含 capability_bindings 的目录都被默认信任"的风险,建议 registry_scan 增加正式库目录白名单或对非常规目录告警。
3. Codex 在 gap=0 时**自行停止并如实报告**(`not_started_gap_count_mismatch`),未硬编下去——独立 agent 对 runbook 断言的遵从性良好。

## 产物落点

- Codex 合成包(pending_review,未审批):验收后归档至 `TestArtifacts/phase13_acceptance/synthesized.codex/`
- Claude 合成包(approved,驱动了 Stage 4-7 与真机执行):恢复至 `Plugins/AgentBridge/SkillTemplates/synthesized/`
- Codex 驱动全过程日志:`TestArtifacts/phase13_acceptance/codex_drive_log4.txt`(MCP 放行后首跑,止于 gap 断言)、`codex_drive_log5.txt`(成功跑)
