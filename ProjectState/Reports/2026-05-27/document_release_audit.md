# Document Release Audit — feat/llm-internal-reopen @ 4829293

> 运行时间: 2026-05-27T20:18:19+08:00
> 比较基准: merge-base 0e1fe36(PR #40 Phase 0 merge 到 main)
> 触发事件: T20 收尾流程 — document-release skill 调用,准备 finishing-a-development-branch
> 主题: Phase 12 LLM Internal Reopen 完整实现(T08-T19 + T18 follow-up,共 15 commits)
> 范围: 15 commits / 35 files / +3075 / -448(commit chain `e059296` → `4829293`)

## 背景

Phase 12 LLM Internal Reopen 是 Phase 11 收尾时暂缓的「LLM Internal 高负载验收」重开门禁。Phase 11 (PR #36 2026-05-26) 已归档,Phase 11 主路径仍是 MCP Agent + heuristic_fallback。本次 Phase 12 把 generator_provider="llm" 路径重开为 promotable 候选,作为 UE 5.7 重构的前置门禁。

最终交付物:
- 新 `Compiler/providers/`(8 模块)+ `Compiler/observability/`(2 模块)+ `Compiler/runtime/`(1 模块)+ `Compiler/stages/candidates_batch_orchestrator.py` 整套 LLM 框架移植到位
- LLMProvider 委托 LLMBatchExecutor,Stage 4 Candidates 按 dimension 分批(7 dim × concurrency=3)
- 2 新 Schema(provider_call / retry_policy)+ design_space_report 扩 per_dimension_batch_metadata 字段
- 105 passed + 4 skipped 测试套件 + Stage 12 LIR-01~04 接入系统测试
- 真 LLM 7/7 验收 PASS(promotable=True / 6008 tokens / 50-60s wallclock)
- 0 触 CLAUDE.md 禁止修改文件红线(C++ / Bridge / Orchestrator / AgentBridgeTests 全 0 改动)

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| Phase 12 LLM Internal Reopen 完整实现(provider framework + Stage 4 分批 + 真 LLM 7/7 验收) | README.md(本次同步 line 4-5)+ task.md(T19 已同步)+ Docs/INDEX.md(本次同步 §1)+ AGENTS.md(无需改,通用规则不涉及)+ CLAUDE.md(无需改,通用规则不涉及) | Docs/design/HLD.md §2.2(T19 已更)+ Docs/design/LLD/04_compiler.md §2.1 + §2.1.1(T19 已更)+ Docs/acceptance/acceptance_report.md §残留(T19 已更,§1 F-CMP-15 主表勾选留 msc 手动)+ Docs/requirements/SRS.md §1 F-CMP-15(本次同步)+ Docs/FEATURE_INVENTORY.md F-CMP-15 行(本次同步,Last_changed 翻面 Phase 12) | Plugins/AgentBridge/Docs/(框架级文档无 F-ID 索引,Phase 12 改 Compiler 子树不需要触动框架级 README/architecture_overview;后续 UE 5.7 阶段引入新框架级范式再补)+ Plugins/AgentBridge/Tests/SystemTestCases.md(T16 已更 Stage 12 LIR-01~04)+ Schema 契约 Plugins/AgentBridge/Schemas/{provider_call,retry_policy}.schema.json(T08 新增)+ design_space_report.schema.json(T09 扩字段)+ Plugins/AgentBridge/Config/llm_config.example.yaml(T13 扩 5 字段 + T18 follow-up 加 litellm 前缀) | ProjectState/Reports/2026-05-27/llm_internal_reopen_acceptance.{md,json}(T18 落)+ ProjectState/Reports/2026-05-27/llm_internal_reopen_acceptance.smoke.{md,json}(T17 落)+ ProjectState/runs/run-20260527-200354-328da1/(T18 真跑 evidence 完整 8 文件:design_space_report.json + llm_usage.json + stage4_agent_traces/llm_internal/{dim_1..7.json,aggregation.json}) |

零覆盖:无。三层全覆盖,Layer A 在本次 audit 期间补齐 README + INDEX(原 T19 仅同步 task.md)。

## Documentation health

- **README.md**: Updated — 顶部"当前状态"从"Phase 11 已完成并归档"翻面为"Phase 12 LLM Internal Reopen 已完成(2026-05-27),Phase 11 已归档";"当前正式口径"链接补 Phase 12 acceptance evidence 锚点。
- **AGENTS.md**: Current — Phase 12 仅扩 Compiler 子树,未触 Agent 通用规则,无需更新。
- **CLAUDE.md**: Current — Phase 12 改动均落在 CLAUDE.md "可以修改" 范围内(Compiler/providers/observability/runtime + stages/agent_protocol.py + pipeline_orchestrator.py + Schemas + Tests + Docs),"绝对不要修改" 清单未触,无需更新。
- **task.md**: Updated(T19) — 顶部跳转块加 Phase 12 三链接(acceptance / plan / spec),Phase 11 五链接保留作归档。
- **Docs/INDEX.md**: Updated — §1 项目状态从单一 Phase 11 翻面为"Phase 12 已完成 + Phase 11 已归档",补 Phase 12 完成事实 + 真 LLM 验收 evidence 链接。
- **Layer B (阶段事实)**:
  - **Docs/design/HLD.md §2.2**: Updated(T19)— LLM Internal bullet 末尾追加 Phase 12 LLM 调用栈架构 + LLMBatchExecutor 分批策略 + 7/7 真 LLM 验收 evidence 链接;旧 llm_client.py 标 deprecate。
  - **Docs/design/LLD/04_compiler.md §2.1**: Updated(T19)— F-CMP-15 行从"Stage 通用 LLM Client"改名为"Stage 通用 LLM Provider Framework",文件路径扩为 8 个 Compiler 模块完整清单;表格后新增 §2.1.1 子目录职责详解 + 4 子目录映射 + spec/plan/acceptance 三链接。
  - **Docs/acceptance/acceptance_report.md §残留**: Updated(T19)— 第一条 bullet"LLM Internal 高负载验收暂缓"翻面为"已于 Phase 12 重开(2026-05-27)"+ UE 5.7 前置门禁定位标注 + 3 文档链接(spec/plan/acceptance)。§1 主表 F-CMP-15 勾选状态故意保留未勾,留 msc 手动确认(避免 Claude 自动批量勾选造成假阳性,符合 acceptance_report 现有约定)。
  - **Docs/requirements/SRS.md §1 F-CMP-15**: Updated — line 129 从"Stage 通用 LLM Client — provider 抽象(OpenAI / Claude / 等)"翻面为"Stage 通用 LLM Provider Framework — LiteLLM + Instructor 统一接入(Compiler/providers/)+ capability 路由 + observe-only budget + Stage 4 Candidates 分批,Phase 12 重开(2026-05-27),旧 llm_client.py 已 deprecate"。
  - **Docs/FEATURE_INVENTORY.md F-CMP-15 行**: Updated — 名称、用途、文件路径、测试覆盖、Last_changed 5 列全部同步;Last_changed 从"unchanged"翻面为"Phase 12(2026-05-27)",文件路径扩展为 11 个 Compiler 模块清单。
  - **Docs/governance.md** / **Docs/redirects.json** / **Docs/contracts/** / **Docs/testing/test_spec.md**: Current — Phase 12 不引入新 F-ID、不改命名规则、不重定向旧路径、不新增 schema 范畴(新 schema 已被 schemas_catalog.md 通用规则覆盖),无需个别更新。后续 docs-restructure 阶段可统一刷新。
- **Layer C (框架)**:
  - **Plugins/AgentBridge/README.md**: Current — 插件入口介绍 AgentBridge 整体,Phase 12 是子树扩展,未改插件对外 surface,无需更新。
  - **Plugins/AgentBridge/AGENTS.md**: Read-only(框架通用规则,本 skill 边界不动)。
  - **Plugins/AgentBridge/Docs/\*.md**: Current — 框架级架构文档(compiler_design / architecture_overview 等)不绑 F-ID,Phase 12 改动属于 F-CMP-15 具体实现,Layer B(LLD/04 §2.1.1)已经覆盖。后续 UE 5.7 阶段若引入新框架级范式再补。
  - **Plugins/AgentBridge/Schemas/\*.json**: Updated(T08 + T09)— 新增 provider_call.schema.json / retry_policy.schema.json;design_space_report.schema.json 扩 per_dimension_batch_metadata 字段;26 → 27 example 校验全 PASS。
  - **Plugins/AgentBridge/Tests/SystemTestCases.md**: Updated(T16)— 加第 17 节 LIR 表格(4 条)+ 附录 B LIR 行 + 合计 266 → 270 + 附录 C `--stage=12` 入口命令。
- **Backlog**:
  - **新延期工作**:暂无新加 backlog 条目(Phase 12 完整完成 7/7 真 LLM 验收 PASS,无 partial 项遗留)。
  - **完成或被取代条目**:`acceptance_report.md §残留` 首条"LLM Internal 高负载验收暂缓"已在 T19 翻面为"已于 Phase 12 重开"(本质等同 retire 旧 backlog 条目)。
  - **已知 follow-up**(Plan 实施期评审产出,非阻塞 Phase 12 收口,可挂 Phase 13 evaluate):
    - LLMProvider 未暴露 retry_policy 注入口 → 中期可在 LLMProvider 构造器加 `retry_policy: RetryPolicySpec | None = None` 形参,Phase 12 默认值已满足真 LLM 7/7 验收
    - model_registry.py 不自动拼接 provider+model 前缀 → T18 follow-up commit 在 example.yaml 加前缀解燃眉,production 代码透传 model 字符串符合 LiteLLM 官方约定,不属于 bug
    - candidates_batch_orchestrator.py 中 `_classify unknown` 分支 + `exhausted` safety net 是 dead code → 保留作防御性编程,Phase 13 评估可清理
- **ProjectState/Reports**:
  - **2026-05-27/llm_internal_reopen_acceptance.{md,json}**: Updated(T18 真跑)— promotable=True / 7/7 success / 6008 tokens / 50-60s wallclock。
  - **2026-05-27/llm_internal_reopen_acceptance.smoke.{md,json}**: Updated(T17 干跑)— acceptance machinery smoke 通过证据,留作回归基线。
  - **2026-05-27/document_release_audit.md**: 本次写入(覆盖了同日 ForgeUE milestone 的 audit,该 audit 通过 git 历史仍可追溯到 commit ccd9308 之前)。
  - **runs/run-20260527-200354-328da1/**: T18 落 8 文件完整 evidence(design_space_report.json / llm_usage.json / stage4_agent_traces/llm_internal/dim_{1..7}.json + aggregation.json),不进 git(evidence-only,完整保留供 audit)。
- **Archive**: Read-only — Phase 12 不触 Docs/History/** 或 Docs/archive/**;Phase 12 自身 spec / plan 静态 anchored 在 `Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md` 和 `Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md`,符合"实施期产物"约定。

## Hard Boundaries 自检

- 0 改动 `Source/*` C++ 核心 ✓
- 0 改动 `Scripts/bridge/*` ✓
- 0 改动 `Scripts/orchestrator/*` ✓
- 0 改动 `AgentBridgeTests/` ✓
- 0 改动 `Plugins/AgentBridge/Schemas/{common,feedback,write_feedback}/`(稳定 Schema)✓
- 0 改动 `Plugins/AgentBridge/AGENTS.md` ✓
- 0 改动 `Docs/History/**` 或历史日期 `ProjectState/Reports/<past_date>/` ✓
- 跑测试: `pytest 10 文件` → **105 passed, 4 skipped / 32.01s** ✓
- 跑 Schema: `validate_examples.py --strict` → **27/27 PASS** ✓
- 跑 Stage 12: `run_system_tests.py --stage 12` → **4/4 PASS** (T16/T20 实测)✓
- T18 真 LLM 验收: **promotable=True / 7/7 success** ✓

## 本次 audit 期间补齐的 doc gap

T19 仅同步了 HLD/LLD/acceptance/task.md 4 个文档,本次 audit 扫描 Layer A/B 全表后补齐 4 处遗漏:
1. `README.md` 顶部"当前状态" → 翻面为 Phase 12
2. `Docs/INDEX.md §1 项目状态(一句话)` → 翻面为 Phase 12
3. `Docs/requirements/SRS.md §1 F-CMP-15` 描述 → 翻面为 LLM Provider Framework
4. `Docs/FEATURE_INVENTORY.md F-CMP-15` 行 5 列(名称/用途/路径/测试/Last_changed) → 全部同步 Phase 12

这 4 处补齐 + T19 既有 4 处 = 共 8 处 Layer A/B 文档完整覆盖 Phase 12 变更,无遗漏。
