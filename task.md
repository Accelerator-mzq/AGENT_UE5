# 当前任务入口 — Phase 14 Demo-First 增量主链

> 当前状态:Phase 14 Demo-First 增量主链**实施 + 验收全部完成**(2026-06-12)/ UE 5.5.4 稳定 / 验收 C1-C6 全闭环,msc v1 终裁**通过**
> 入口类型:Phase 14 任务书(已完成)
> 分支:`feat/phase14-demo-first-spec`(实现 commit 范围 cd84dfe..739ecc1)

## 1. Phase 14 是什么

产品愿景"GDD → agent 发散创造 → N 份 demo → 使用者挑选"的增量交付实证:**让 agent 无人值守把一份 GDD 写出一个可玩 v0 demo,并以机器守门保证后续增量不破坏可玩**。两条核心主张:

1. **agent 无人值守写出可玩 v0** — 切批机制(planner)按拓扑序把 skill_graph 切成 v0 全量批 + 每合成节点一增量批,coding agent 凭施工规范在 `Plugins/Demo_MonopolyAuction/` 落地 authored 启动关卡 + 键盘可玩 + 真实 HUD,经证据门(evidence_validator 分级必交 + hash 守门 + 文档引用对账)验收;
2. **增量不破可玩** — v0 冒烟基线冻结后,每个增量批 submit 走 hash 守门(冻结文件改动即拒)+ v0 回归冒烟门,实证"拍卖增量入可玩循环且 v0 不退化"。

机制层全部落 AgentBridge 框架(planner / story_store 状态机 / evidence_validator / velocity / manifest_loader 五模块 + MCP 工具对 + 冒烟 runner);可玩 demo `Plugins/Demo_MonopolyAuction/` 是**项目层产物,不属 AgentBridge 框架**。

## 2. 权威文档

- 设计 spec:[2026-06-11-phase14-demo-first-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md)(顶部含实施期修订记录)
- 实施 plan:[2026-06-11-phase14-demo-first.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-06-11-phase14-demo-first.md)(11 任务,TDD,机制层全代码就绪)
- 验收 runbook:[phase14_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md)(C1-C6 全闭环 + 最终判定表 + PIVOT/修复轮全记录)
- PIVOT note:[phase14_v0_pivot_note_1.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-12/phase14_v0_pivot_note_1.md)(C4 attempt 1 可玩定义缝根因)
- 施工规范:[demo_plugin_standards.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/ConstructionManifest/demo_plugin_standards.md)(项目层实例,当前版本 **1.1.0**)

## 3. 交付摘要(cd84dfe..739ecc1)

- **机制层(插件层)**:`Plugins/AgentBridge/Compiler/demo_plan/` 五模块——planner(拓扑序切批 + v0 全量批 + 每合成节点增量批 + 文档 story 末位)/ story_store(状态机:依赖门 / 幂等重入 / `.part` 事务)/ evidence_validator(分级必交 + hash 守门 + 文档引用对账)/ velocity / manifest_loader(版本对账 fail-closed)。
- **Schema +2**:`demo_plan.schema.json` + `demo_story.schema.json` + 2 examples,入 strict 校验(**30/30**,实测 `validate_examples.py --strict`)。
- **MCP 工具对**:`demo_story_fetch` / `demo_story_submit`(`_make_response` 契约统一,`plugin_root` 锚定校验),工具数 **55→57**(实测 `tool_definitions.ALL_TOOLS` = 57)。
- **CLI + 冒烟 runner**:`Scripts/demo_plan_main.py`(gap/run_id fail-closed + schema 自校验落盘 + 友好报错)+ `Scripts/demo_smoke/runner.py`(环境自检 / 报告契约 / 归因分离退出码 0/1/3)。
- **系统测试**:Stage 14 DMP-01~56 登记(6 个 `test_phase14_*.py` 纯 Python),系统测试总数 **364→420**(实测 `run_system_tests.py` TOTAL_CASES = 420,14 stage;`SystemTestCases.md` 已同步,`CLAUDE.md` 常用命令行已同步)。
- **项目层产物**:施工规范 `demo_plugin_standards.md`(经 C4 PIVOT #1 从 1.0.1 升 1.1.0,增 §0 可玩硬判据 / §1 authored 关卡必含 / §4 关卡加载冒烟 / §7 无人值守资产创建通路)+ 可玩 demo `Plugins/Demo_MonopolyAuction/`(authored 关卡 + 键盘可玩 + 拍卖增量,不属 AgentBridge 框架)。

权威数字(实测,2026-06-12):phase14 pytest **56**(`pytest -k phase14 --collect-only`);系统测试 **420**(14 stage,Stage 14 DMP 56);Schema examples strict **30/30**;MCP 工具 **57**。

## 4. 验收状态

| 判据 | 状态 |
|---|---|
| C1 机器(pytest 56 / Stage 14 / 全量等价 / strict 30) | ✅ 全过(主会话亲跑) |
| C2 切批标准答案(3 批 / 21 story / 拓扑序) | ✅ 全中(含机器断言) |
| C3 v0 无人值守 | ✅ 经 1 次 PIVOT + 1 次试玩反馈修复轮后达成(attempt 2:17/17 verified,authored 关卡 + 键盘可玩 + 真实截图;主会话亲驱一局复证) |
| C4 人审窗口 1 | ✅ attempt 1 PIVOT(可玩定义缝,规范升 1.1.0)→ attempt 2 修复轮(Enter/Esc)→ **PROCEED**(图形归 Phase 15) |
| C5 增量批 1(拍卖) | ✅ 2/2 verified;hash 守门 + v0 回归实证;拍卖入可玩循环;**msc 试玩 v1 终裁通过** |
| C6 接口中立 | ✅ 真实 MCP stdio 实测 57 工具,fetch/submit 可见 |

- 范围说明:increment-2(股票市场)按 spec §2 留批不执行(计划在册,Phase 14 范围 = v0 + 一次增量)。
- 关键事件:C3 经 1 次 PIVOT(可玩定义缝,spec 根因)+ 1 次试玩反馈修复轮(Enter/Esc 空操作);C4 PROCEED(图形归 Phase 15)。

## 5. 下一步(Phase 15 输入)

1. **呈现 / 图形增量轴**(msc 试玩诉求):demo 当前只有文字 HUD,capability 切批机制缺呈现升级轴;Phase 15 需把"呈现/图形"作为增量分化维度。
2. **词表扩展 / Stage 1 模板固化**(Phase 13 遗留)。
3. Phase 14 实施期 backlog(P14-BL-01~06,含安全/机制/性能/可观测/门禁/机制缺口)见 `Docs/acceptance/acceptance_report.md` 附 4。

> 范围裁决(msc,2026-06-12):原列项"扇出 N demo + 挑选会话层"自 Phase 15 范围去除,恢复需 msc 主动提出;"N 份 demo + 使用者挑选"保持为产品长期方向,不进近期阶段规划。

---

## 历史阶段归档

> 以下为上一版任务书与跳转页保留的归档链接,Phase 11 / 12 / 13 事实不再改写。

> **Phase 13 — Skill 合成主链**(已完成 2026-06-11,验收 1-12 全执行,commit d02e8bf):capability gap 显式化 + Stage 3 注册表数据化 + S3.5 链内合成环节(MCP `compiler_skill_synthesis_prepare/save` 双 gate)+ GDD 覆盖矩阵。
> Phase 13 spec:[2026-06-10-phase13-skill-synthesis-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md)
> Phase 13 plan:[2026-06-10-phase13-skill-synthesis.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-06-10-phase13-skill-synthesis.md)
> Phase 13 验收 runbook:[phase13_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md)
> Phase 13 backlog(P13-BL-01~07):[acceptance_report.md 附 3](/D:/UnrealProjects/Mvpv4TestCodex/Docs/acceptance/acceptance_report.md)

> ⚠️ UE 5.7 重构计划已于 2026-05-27 弃置;BC 知识库 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 保留作未来可能的重启资产,不主动维护。
>
> Phase 12 验收报告:[llm_internal_reopen_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-05-27/llm_internal_reopen_acceptance.md)
> Phase 12 实施 plan:[2026-05-27-llm-internal-reopen.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md)
> Phase 12 实施 spec:[2026-05-27-llm-internal-reopen-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md)
>
> Phase 11 历史任务正文:[task11_phase11.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task11_phase11.md)
> Phase 11 收尾总览:[18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/acceptance/acceptance_report.md#1)
> Phase 11 最终验收:[task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
> Phase 11 功能覆盖报告:[phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md)
> Phase 11 系统测试对齐:[task_phase11_system_test_alignment.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task_phase11_system_test_alignment.md)
>
> Phase 10 历史任务见 [task10_phase10.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/history/Tasks/task10_phase10.md)。
