# Document Release Audit — feat/hud-multiexpert-pilot @ 18334c2

> 运行时间: 2026-05-31
> 比较基准: merge-base 3a7fedf(vs origin/main)
> 触发事件: merge 前置门禁(Superpowers 收尾链 document-release)
> 本次增量: HUD **总监裁决版**试点(commits 7fd2b13..18334c2,8 个 commit)
> 说明: 本分支早期的 baseline 发散修复(commit 6842c28)与 HUD 多专家协商试点(commit 48f8d27)已在各自 document-release 运行中发布,其审计留痕见 git 历史与本目录上一版本。本次审计聚焦总监裁决增量。
> 变更性质: 试点编排替换(协商→中立总监裁决)+ 新证据,不碰编译主链/契约/框架行为

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| core 新增 `assemble_arbitration_result` 纯函数(装配正常/unresolved/missing)+ 3 测试 | NONE | NONE(纯逻辑,未改需求/系统测试登记) | NONE | `Plugins/AgentBridge/Tests/scripts/hud_multiexpert_core.py` + `test_hud_multiexpert_core.py` |
| 编排替换:去多轮协商/字符串收敛,改中立总监一次性语义裁决(`ARBITER_PROMPT`/`arbitrate`)+ 原始响应诊断留痕 | NONE | `Docs/archive/superpowers/specs|plans/2026-05-31-hud-arbiter*`(设计+计划) | NONE(故意不碰 SkillTemplate/Provider/主链,spec §1.4 非目标) | `Plugins/AgentBridge/Tests/scripts/demo_hud_multiexpert.py` |
| 真实 LLM 试点产物(两次运行:一次空、一次成功)+ 三方对比更新 | NONE | NONE | NONE | `ProjectState/Reports/2026-05-31/hud_arbiter_fragment.json` + `hud_arbiter_log.json` + `hud_multiexpert_vs_single_comparison.md`(总监裁决版一节) |
| 试点 follow-up backlog 登记 | NONE | `Docs/acceptance/acceptance_report.md` 附 3.1(FU-HUDME-04) | NONE | 同上对比报告 |

零覆盖项:无。A 层无变更属预期(独立试点,不触项目入口/治理)。C 层无变更属**有意**(spec §1.4 明确不碰主链/模板/client,故意保持隔离;fragment 标 `promotable:false`,不进契约校验对象)。

## Documentation health

- README.md: Current — 无入口/导航变更。
- AGENTS.md: Current — 无 Agent 规则变更。
- CLAUDE.md: Current — 改动全在 `Tests/scripts/`(试点脚本区,非禁改的 `AgentBridgeTests/`)+ `Docs/archive/` + `ProjectState/Reports/` + `Docs/acceptance/`,均项目可改区;grep 确认未碰 domain_skill_runtime / agent_protocol / SkillTemplate / llm_client / bridge / orchestrator / Source 核心。
- task.md / Docs/INDEX.md: Current — Phase 11 已归档,本次为其后置探索性试点,不改阶段入口/索引。
- Layer B(阶段事实): Updated — `Docs/acceptance/acceptance_report.md` 附 3.1 新增 FU-HUDME-04(总监裁决版试点结论 + 推广待定)。未改 SRS / SystemTestCases(独立试点脚本,非正式登记的 System Test Case,也未改需求基线)。
- Layer C(框架): Current — `Plugins/AgentBridge/Docs/*` / `Schemas/*` / `README.md` 均未改;总监裁决 fragment 复用 skill_fragment v2.0 结构但标 `promotable:false`,不进契约校验对象,不影响框架契约。
- Backlog: Updated — `acceptance_report.md` 附 3.1 新增 FU-HUDME-04;未删除任何 active 条目,未改 FU-HUDME-01/02/03。
- ProjectState/Reports: Updated — `2026-05-31/` 新增/更新总监裁决产物(`hud_arbiter_fragment.json` / `hud_arbiter_log.json`)+ 对比报告追加总监裁决版一节 + 本审计刷新。历史日期目录未重写。
- Archive(`Docs/History/**`): Read-only — 未触碰。

### 验证证据(document-release 收尾自验,均本机实跑,见对话内输出)
- `python Plugins/AgentBridge/Tests/scripts/test_hud_multiexpert_core.py` → **All 9 passed**(原 6 + 新增 assemble_arbitration 的 normal/unresolved/missing 3 例)
- 总监裁决产物校验:`selected_realization` 35 维**全部非空**、`capability_gaps` 1 个(`hud.collapsibility`,`arbiter_unresolved`)、`mode=arbiter_pilot`、`promotable=False`
- 诊断留痕校验:`arbitration_diag.raw` 14310 字符、完整闭合 `{"arbitration":{...}}`、`out_keys=["arbitration"]`、35 维齐全 → 本次裁决调用成功、格式遵从、无截断
- demo 残留协商引用:`grep -nE "renegotiate|detect_convergence|weighted_majority|MAX_ROUNDS|round_0_stances|owner_map"` → 无
- 范围合规:`git diff 3a7fedf...HEAD --name-only` 比对受保护路径(Source/AgentBridge/{Private,Public} / Scripts/bridge / Scripts/orchestrator / AgentBridgeTests / 稳定 Schema / llm_client / SkillTemplates / MCP / domain_skill_runtime / agent_protocol)→ **无一被改动**
- 注:本次为脚本 + 证据 + backlog,未触及 schema/example,故未跑 validate_examples(doc/pilot-only,无契约变更)。

### 试点诚实结论(摘自对比报告,纳入审计留痕)
总监裁决方向正确——让三专家面向同一维度全集表态、由中立总监语义整合,**消除了协商版字符串比较的伪零冲突**,并在成功那次真实暴露了 1 个跨专业硬分歧(`hud.collapsibility`)。但**非确定性**是实测硬缺陷:同脚本连跑两次,第一次裁决返回空 `{}`(全 `arbiter_missing`、spec 全空),第二次才成功;第一次真因因当时无 raw 留痕**不可追溯**(已补 `arbitration_diag`)。推广前必须解决单次裁决稳定性(格式校验 + 重试 / 分批裁决)并跨多次运行验证,详见 FU-HUDME-04。
