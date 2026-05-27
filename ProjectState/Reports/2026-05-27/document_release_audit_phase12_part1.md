# Document Release Audit — feat/llm-internal-reopen @ 88a77a7

> 运行时间: 2026-05-27T18:00:00+08:00
> 比较基准: ccd9308a (origin/main)
> 触发事件: push(Phase 12 Part 1 PR 推送)
> 关联 spec: `Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md`
> 关联 plan: `Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md`(20 task)
> 本批次完成: Phase 0(T01-T07,7/20 task)+ 1 个基础设施修复(pytest.ini)
> 范围: 14 commits / 24 files / +5665 / -0

## 背景

本次 audit 是 Phase 12 LLM Internal Reopen 的 Part 1(基础设施移植)收尾文档同步门禁。Phase 11 已归档(commit `6498df2` PR #36),Phase 12 由本会话 brainstorming → spec(`768b50b` + `26b7009` self-review)→ plan(`d6a79e1`)→ Phase 0 实施(T01-T07 共 11 commits)产出。

最终交付物:
- ForgeUE_codex `src/framework/providers/` 整套移植到本项目 `Plugins/AgentBridge/Compiler/providers/`(8 文件,~1000 行)
- observability/{secrets, compactor} + runtime/budget_tracker(observe-only)子树就绪
- 45 case smoke 测试全 PASS,覆盖率 ≥ 85%(单元层)
- pytest.ini 加 `pythonpath = .` 解决 pytest 直接调用 ModuleNotFoundError
- 0 触 CLAUDE.md "绝对不修改" 红线

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| Phase 12 spec + plan(brainstorming 产物) | NONE(INDEX 同步推迟 T19) | NONE(acceptance §残留 待 T19 翻面) | NONE(spec 自带架构图) | `Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md` + `plans/2026-05-27-llm-internal-reopen.md` |
| Provider 框架移植(LLM 抽象层 + 4 类 typed exception) | NONE | NONE(spec §2-3 已述) | 新建 `Plugins/AgentBridge/Compiler/providers/`(8 文件:`__init__` / `base` / `_retry` / `_retry_async` / `litellm_adapter` / `capability_router` / `model_registry` / `fake_adapter`) | `Tests/scripts/test_{providers,litellm_adapter,router_registry,fake_adapter}_smoke.py`(29 case PASS) |
| Observability 横切支撑(secrets 脱敏 + compactor 超长上下文裁剪) | NONE | NONE | 新建 `Plugins/AgentBridge/Compiler/observability/`(3 文件:`__init__` / `secrets` / `compactor`) | `Tests/scripts/test_observability_smoke.py`(7 case PASS) |
| Runtime budget tracker(observe-only,去硬阻断) | NONE | NONE(spec §1.8 决断 i) | 新建 `Plugins/AgentBridge/Compiler/runtime/`(2 文件:`__init__` / `budget_tracker`) | `Tests/scripts/test_budget_tracker_smoke.py`(5 case PASS) |
| pytest.ini 加 pythonpath=. | NONE | NONE | `pytest.ini`(+4 行)修复 `pytest` 直接调用 ModuleNotFoundError | 45 测试回归 PASS in 6.70s |
| 依赖装(litellm + instructor + pydantic + httpx) | NONE | NONE | 新建 `Plugins/AgentBridge/Scripts/setup/check_llm_deps.py`(版本探测) | `Tests/scripts/test_llm_deps_smoke.py`(4 case PASS,实际装版本:litellm 1.83.10 / instructor 1.15.1 / pydantic 2.12.5 / httpx 0.28.1) |

**零覆盖说明**:Layer A/B 全部 NONE 是**预期行为**,不是 doc gap。原因:Phase 0 是 plan §10 T01-T07 范围,纯基础设施移植 — 不动调用链、不接入 Stage 4、不改 generator_provider 路由。Plan §T19 显式要求"实施完后同步 HLD §2.2 + LLD 04 §2.1 + acceptance_report §残留翻面 + task.md 跳转",即文档同步统一在 Phase 4 完成。本次 push 是"Phase 12 Part 1: provider framework migration",Layer A/B 同步留给 T19 批量做。

## Documentation health

- **README.md**: Current — Phase 0 是 LLM 路径内部基础设施,用户层不可见,不需要改 README。
- **AGENTS.md**: Current — Phase 0 不变 Agent 规则。
- **CLAUDE.md**: Current — 所有改动都在"可以修改"清单内(`Plugins/AgentBridge/Compiler/{providers,observability,runtime}/` + `Scripts/setup/` + `Tests/scripts/` + `pytest.ini`);"绝对不修改"红线 0 违反(C++ 核心 / Bridge 客户端 / Orchestrator 核心 / AgentBridgeTests / 已稳定 Schema 全部不动)。
- **task.md**: Current — Phase 11 已收尾跳转页,Phase 12 仍在进行中(20 task 完成 7),按 plan T19 在 Phase 12 完整收尾时统一更新。
- **Docs/INDEX.md**: Needs user decision (deferred to T19) — INDEX §1 "项目状态" 现写"Phase 11 已完成,UE 5.5.4 → 5.7 重构准备中"。Phase 12(LLM Internal Reopen)是 UE 5.7 前置门禁(spec §1.2 决断),理论上现应在 INDEX 提示"Phase 12 进行中"。但本批次只完成 35% 工作(7/20 task),且 plan §T19 明确"实施完后同步 task.md / INDEX 跳转"。**决定:暂不动,留 T19 批量更新**;避免在 Phase 12 半成品阶段污染 INDEX 主页面。
- **Layer B(SRS / HLD / LLD / acceptance_report)**: Deferred to T19 — Plan §T19 显式同步面:`Docs/design/HLD.md §2.2`(加图 B + 改"LLM 暂缓"措辞为"Phase 12 重开 promotable")、`Docs/design/LLD/04_compiler.md §2.1`(F-CMP-15 行补"litellm 升级")、`Docs/acceptance/acceptance_report.md §残留`(删 "LLM Internal 暂缓" + 改 "LLM Internal 是 UE 5.7 重构前置门禁")。本批次不动这些 current docs,完全合规 plan 设计意图。
- **Layer C(Plugins/AgentBridge/{README,Docs,Schemas,Tests/SystemTestCases})**: Current — Phase 0 不动 README;插件框架文档由 T19 同步;Schemas 升级在 Phase 1(T08-T09);SystemTestCases 由 T16 新增 Stage 11。
- **Backlog**: No changes —
  - Active backlog(`Docs/acceptance/acceptance_report.md §1-附`)无新加 / 无完成。Phase 0 是 Phase 12 plan 内部进度,不算"完成"任何 acceptance_report backlog item。
  - Spec §9.2 follow-up 候选(FU-LLM-01..06)已写入 spec 文档,不进 acceptance_report(spec §10 实施序列预告本身覆盖)。
- **ProjectState/Reports**: Updated —
  - 本次新写 `ProjectState/Reports/2026-05-27/document_release_audit_phase12_part1.md`(本文件)
  - 同目录已有 `document_release_audit.md`(forgeue 那一波)+ `forgeue_*` 系列(只读不动)
- **Archive(`Docs/History/**`)**: Read-only — 本次不写 archive,Phase 11 历史归档不动。

## Phase 12 progress snapshot(给 reviewer / 后续接手者)

```
Phase 0 ✅ COMPLETE  T01-T07 7/7 task + pytest.ini fix(本 push)
Phase 1 ⏳ pending   T08-T09 Schema 升级(provider_call + retry_policy + design_space_report 扩字段)
Phase 2 ⏳ pending   T10-T12 核心调度(candidates_batch_orchestrator + LLMProvider 委托 + pipeline_orchestrator 装 router)
Phase 3 ⏳ pending   T13-T16 配置 + L2 单元/集成/系统测试
Phase 4 ⏳ pending   T17-T20 真 LLM 7/7 验收 + 文档同步 + 收尾
```

## 后续 PR 计划

- 本 PR(`feat/llm-internal-reopen`)→ "Phase 12 Part 1: Provider framework migration"
- T08-T20 在 main 上新切分支推进,避免主线漂移
- T19 文档同步(HLD/LLD/acceptance_report/INDEX/task.md)在最后一个 PR 统一做

## Verify 命令(本批次回归)

```powershell
# Phase 0 全部 smoke 测试回归
pytest Plugins/AgentBridge/Tests/scripts/test_llm_deps_smoke.py `
       Plugins/AgentBridge/Tests/scripts/test_providers_smoke.py `
       Plugins/AgentBridge/Tests/scripts/test_observability_smoke.py `
       Plugins/AgentBridge/Tests/scripts/test_litellm_adapter_smoke.py `
       Plugins/AgentBridge/Tests/scripts/test_router_registry_smoke.py `
       Plugins/AgentBridge/Tests/scripts/test_fake_adapter_smoke.py `
       Plugins/AgentBridge/Tests/scripts/test_budget_tracker_smoke.py -v
# 实测: 45 passed in 6.70s
```

## 同步路径决策汇总

| 维度 | 本批次决策 | 理由 |
|---|---|---|
| README/AGENTS/CLAUDE/task.md | 不动 | Phase 0 内部基础设施,用户层不可见 |
| Docs/INDEX.md | 推迟 T19 | 避免半成品阶段污染主页 |
| HLD/LLD/acceptance_report | 推迟 T19 | Plan §10 设计意图,统一收尾 |
| Backlog | 无变化 | Spec follow-up §9.2 已自含 |
| ProjectState/Reports | 本次写 audit.md | 强制门禁要求 |
| Archive | 只读 | 历史归档不动 |

## CLAUDE.md "绝对不修改" 红线交叉检查

逐项验证(本批次 24 文件,全部在"可以修改"清单内):

| 红线类别 | 本批次是否触碰 |
|---|---|
| C++ 核心(`Source/*`) | ❌ 0 触碰 |
| Bridge 客户端(`Scripts/bridge/*`) | ❌ 0 触碰 |
| Orchestrator 核心(`Scripts/orchestrator/*`) | ❌ 0 触碰 |
| 测试体系(`AgentBridgeTests/*`) | ❌ 0 触碰 |
| 已稳定 Schema(`Schemas/common/` `Schemas/feedback/` `Schemas/write_feedback/`) | ❌ 0 触碰 |

✅ 红线 0 违反。
