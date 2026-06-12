# Document Release Audit — feat/phase14-demo-first-spec @ 739ecc1

> 运行时间: 2026-06-12T00:00:00Z
> 比较基准: b7f9d380d059aed88749bcc484d7fc747191fb68 (merge-base with origin/main)
> 触发事件: manual (Phase 14 收尾文档同步,收尾链 document-release 门禁)
> 实际 base 解析: origin/main 可用,merge-base = b7f9d38

## 概览

- diff 规模:83 文件,+9636 / -6(`git diff b7f9d38...HEAD --stat`)。
- 实现已由 41 个 `[skip-doc]` commit 落地(cd84dfe..739ecc1),本次 document-release 补 Layer A/B 当前文档面同步。
- 权威数字全部实时取数(非硬编码):
  - pytest `-k phase14 --collect-only` → **56**
  - `run_system_tests.py` TOTAL_CASES(动态求和)→ **420**,STAGES = **14**
  - `validate_examples.py --strict` → Checked **30** / Passed **30** / Failed 0
  - `tool_definitions.ALL_TOOLS` → **57**(含 demo_story_fetch/submit)
  - `demo_plugin_standards.md` manifest_version → **1.1.0**
  - phase14 测试文件数 → **6**(`test_phase14_*.py`)

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| demo_plan 切批机制(planner/story_store/evidence_validator/velocity/manifest_loader) | task.md / CLAUDE.md / Docs/INDEX.md | acceptance_report.md 附 4.1 | Plugins/AgentBridge/Compiler/demo_plan/(代码已落,[skip-doc] commit) | ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md C1 |
| Schema +2(demo_plan/demo_story)+ strict 30/30 | Docs/INDEX.md §4 | acceptance_report.md 附 4.1 | Plugins/AgentBridge/Schemas/demo_plan.schema.json / demo_story.schema.json + examples | validate_examples.py --strict 实时 30/30 |
| MCP 工具对 demo_story_fetch/submit(55→57) | Docs/INDEX.md §4 | acceptance_report.md 附 4.1 | Plugins/AgentBridge/MCP/tool_definitions.py ALL_TOOLS=57(代码已落) | runbook C6(真实 MCP stdio 57 工具) |
| 系统测试 Stage 14 DMP-01~56(364→420) | CLAUDE.md 常用命令 / task.md / Docs/INDEX.md §4 | Plugins/AgentBridge/Tests/SystemTestCases.md §19(已同步) | run_system_tests.py TOTAL_CASES=420(代码已落) | runbook C1 / reports/2026-06-12/system_test_report_*.json |
| CLI + 冒烟 runner(demo_plan_main / demo_smoke) | task.md | acceptance_report.md 附 4.1 | Plugins/AgentBridge/Scripts/demo_plan_main.py / demo_smoke/runner.py(代码已落) | runbook C1 / C3 |
| 施工规范 demo_plugin_standards 1.1.0(PIVOT #1) | task.md §2 | acceptance_report.md 附 4 | ProjectInputs/ConstructionManifest/demo_plugin_standards.md(项目层实例) | runbook C4 / phase14_v0_pivot_note_1.md |
| 可玩 demo Plugins/Demo_MonopolyAuction/(项目层产物,非框架) | task.md §1/§3(标注不属 AgentBridge) | acceptance_report.md 附 4.1(标注项目层) | NONE(明确不入框架文档) | runbook C3/C4/C5 + ProjectState/Evidence/phase14_v0_attempt2/* |
| Phase 14 验收 C1-C6 闭环 + msc v1 终裁 | task.md §4 | acceptance_report.md 附 4.2 | NONE | ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md(最终判定表) |
| Phase 14 backlog P14-BL-01~06 | NONE | acceptance_report.md 附 4.3 | NONE | runbook(实施期审查累积) |
| Phase 15 输入(呈现轴/扇出会话层/词表) | task.md §5 | acceptance_report.md 附 4.4 | NONE | runbook 最终判定 + MEMORY |
| Phase 14 spec/plan | task.md §2 / CLAUDE.md 当前阶段 / Docs/INDEX.md §1 | acceptance_report.md 附 4.1 | NONE | Docs/superpowers/specs|plans/2026-06-11-phase14-demo-first*.md |
| task.md 换页(Phase 13 任务书 → Phase 14 任务书已完成) | task.md(全文重写,Phase 13 移历史归档区) | NONE | NONE | NONE |

零覆盖项检查:无 critical gap(每个机制变更点均有 A 入口 + B 阶段事实落点)。Demo_MonopolyAuction 与可玩 demo 的 C 框架列标 NONE 为**有意**——按事实清单与 spec,该插件是项目层产物,不属 AgentBridge 框架文档面。

## Documentation health

- README.md: Current — 无当前阶段声明(phase-agnostic),无需改动;扫描确认无 stale "364"/"55 工具"/"Phase 13 当前"。
- AGENTS.md: Current — 项目级 Agent 规则,无当前阶段数字,无需改动;`Plugins/AgentBridge/AGENTS.md`(框架通用规则)按 Hard Boundary 只读未触碰。
- CLAUDE.md: Updated — 「最后更新」2026-06-11→2026-06-12;「当前阶段」改写为 Phase 14 已完成(spec/plan/runbook 路径),Phase 13 下移一行;「常用命令」14 Stage / 420 已在实现期同步(本次复核保留)。
- task.md: Updated — 从 Phase 13 任务书全文重写为 Phase 14 任务书(已完成)入口页,形制沿 Phase 13 版(状态行/是什么/权威文档/交付摘要/验收状态/下一步);Phase 13 区块移至「历史阶段归档」区段(与 Phase 12/11/10 并列),Phase 13 事实不改写。
- Docs/INDEX.md: Updated — 版本 v1.1→v1.2;§1 项目状态一句话改 Phase 14;§2 阅读顺序「364」→「420」、附录引用补 Phase 14;§4 权威定义点三行(MCP 55→57 / 系统测试 364→420 / strict 28→30)按实时数同步,均标注实测来源。
- Layer B(阶段事实): Updated — `Docs/acceptance/acceptance_report.md` 新增「附 4:Phase 14」(4.1 交付摘要 / 4.2 验收状态 / 4.3 backlog P14-BL-01~06 / 4.4 Phase 15 输入),沿 附 3(Phase 13)既有格式;`Plugins/AgentBridge/Tests/SystemTestCases.md` Stage 14 / DMP / 420 已在实现期同步(本次复核确认一致,「6 个 test_phase14_*.py」与实测文件数相符)。
- Layer C(插件层框架): Current(代码侧已落) — demo_plan 五模块 / Schema +2 / MCP 工具对 / 冒烟 runner 由实现期 [skip-doc] commit 落地;框架文档面数字事实经 Docs/INDEX.md §4 汇总同步;`Plugins/AgentBridge/Docs/*.md` 深层框架文档本次未逐篇改(无新增框架概念需补,仅数字汇总在 INDEX/acceptance)。Needs user decision — 见下「未覆盖面」第 1 条(是否需把 demo_plan 机制写入某篇 Plugins/AgentBridge/Docs 框架文档,而非仅 INDEX/acceptance 汇总)。
- Backlog: Updated — P14-BL-01~06 写入 acceptance_report.md 附 4.3(active,未删任何既有 active 条目;附 3 Phase 13 backlog 原位保留)。Phase 15 输入入 附 4.4。
- ProjectState/Reports: Updated — 本审计写入 `ProjectState/Reports/2026-06-12/document_release_audit.md`;runbook / pivot note 为实现期产物(只读引用,未改写)。两份 `doc_release_skipped.log`(2026-06-11/2026-06-12)为 harness 自动产物,未纳入本次 doc 提交。
- Archive: Read-only — `Docs/History/**` 与历史日期 Reports(含 2026-06-11)按 Hard Boundary 未改写;task.md 历史归档区仅做链接引用,不重写历史事实。

## 未覆盖面 / Needs user decision(诚实披露)

1. **(Needs user decision)** demo_plan 机制(五模块 + MCP 工具对)目前仅在 `Docs/INDEX.md §4` 与 `acceptance_report.md 附 4` 做数字 + 摘要汇总,未在 `Plugins/AgentBridge/Docs/*.md`(如 mcp_tools_catalog / schemas_catalog / LLD)逐篇补章节。事实清单未要求改这些深层契约目录,且改动属"是否新增框架文档章节"的架构判断 → 按 skill「Ask first」列此,不擅自展开。若需把 demo_plan/demo_story Schema 与 demo_story_fetch/submit 工具登记进 `Docs/contracts/{mcp_tools_catalog,schemas_catalog}.md` 主表(当前主表停在 Phase 13 的 55 工具 / 45 主 Schema),请明示。
2. `Plugins/AgentBridge/Tests/SystemTestCases.md` 头部「全部 420 条」与 Stage 14 DMP 表已在实现期 commit 同步,本次为复核确认(未改);若需我对其逐行 DMP 编号再核一遍可另行指出。
3. 两份 `doc_release_skipped.log` 工作树改动为 harness 自动写入,未纳入本次 doc 提交范围(非文档事实)。
