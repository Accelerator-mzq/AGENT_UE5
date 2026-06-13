# 当前任务入口 — Phase 15 呈现增量轴 + 反馈回流通道

> 当前状态:Phase 15 **机制层完成**(2026-06-13,最终整体复审 Ready to merge)/ **验收期进行中**(demo 三 rung 无人值守 + 试玩两窗口未启动)/ UE 5.5.4 稳定
> 入口类型:Phase 15 任务书(机制层已落地,验收待执行)
> 分支:`feat/phase15-presentation-axis`(机制层 commit 范围 acab5c5..b7c9d42,领先 main 17 commit,未合)

## 1. Phase 15 是什么

把"呈现 / 图形"建成与玩法批同等地位的**增量维度**(机制能力),无人值守把 Demo_MonopolyAuction 的呈现从文字 HUD 逐级升到 3D 场景(面板 → 2D 棋盘 → 3D);并把试玩反馈回流建成**机制内闭环**(反馈批),人只在两个试玩窗口出现。两条主轴:

1. **呈现增量轴** — planner 新增 `amend` 批次追加模式,读项目层呈现阶梯(`monopoly_demo_ladder.json`)数据驱动切出 presentation-1/2/3 三批(UMG 面板 → 2D 棋盘 → 3D);每批结束 demo 仍可玩、冒烟全绿;冻结分层(逻辑 / 呈现契约 / 呈现实现三层 + supersedes 退役声明)保证"可玩且不降呈现"。
2. **反馈回流通道**(根治 P14-BL-06) — `demo_feedback_log` 登记试玩反馈 → amend 确定性切 feedback 批 → 走同一 fetch/submit 门禁 + 不退化守门 → 修复 story verified 后条目流转 resolved。配套行为校验门禁(BL-05:claims/README『## 键位』/InteractionSemantics 三方对账,根治 C4 教训)。

机制层全部落 AgentBridge 框架;阶梯实例 / 施工规范 / 可玩 demo 是**项目层产物,不属框架**。

## 2. 权威文档

- 设计 spec:[2026-06-12-phase15-presentation-axis-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-12-phase15-presentation-axis-design.md)(顶部含实施期修订记录 R1-R5)
- 实施 plan:[2026-06-12-phase15-presentation-axis.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-06-12-phase15-presentation-axis.md)(13 任务,TDD,机制层全代码就绪 + 验收交接段)
- 机制层验证报告:[phase15_mechanism_verification.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-13/phase15_mechanism_verification.md)(全量机器证据)
- 呈现阶梯实例:[monopoly_demo_ladder.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/PresentationLadder/monopoly_demo_ladder.json)(3 rung / 7 story,游戏语义只在此)
- 施工规范:[demo_plugin_standards.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/ConstructionManifest/demo_plugin_standards.md)(项目层实例,当前版本 **1.2.0**)

## 3. 交付摘要(机制层,acab5c5..b7c9d42)

- **planner amend 模式**:`Compiler/demo_plan/amend.py`(新)——build_presentation_amend(阶梯数据驱动切呈现批)+ build_feedback_amend(open 反馈条目机械切批);锚点 = 最后一个全 verified 批末位,幂等,零 LLM 确定性,零游戏语义。
- **evidence_validator 三道新门禁**:BL-01 路径越界(resolve + is_relative_to)/ BL-05 行为校验(interaction_claims 三方对账)/ 冻结分层(`freeze_layer` → `frozen_baselines.json`,supersedes_paths 放行退役),v0_smoke_baseline 双轨兼容。
- **MCP**:`demo_feedback_log`(工具数 **57→58**,实测 `len(ALL_TOOLS) = 58`)+ demo_story_submit 接 frozen_layers + feedback→resolved 流转。
- **smoke runner**:BL-04 errorMessage 透传(含 null 防御)+ 多段冻结层回归聚合。
- **Schema +2**:`presentation_ladder` + `feedback_entry`(strict **30→32**);`demo_story`/`demo_plan` 升 1.1.0(batch_id +presentation-N/feedback-N,story_kind +presentation/feedback,interaction_claims)。
- **系统测试**:Stage 15 PRX-01~46 登记(5 个 `test_phase15_*.py` 纯 Python),系统测试总数 **420→466**(实测 `run_system_tests.py` TOTAL_CASES = 466,15 stage)。
- **项目层产物**:阶梯实例 `monopoly_demo_ladder.json` + 施工规范 1.2.0(§4 呈现用例文件约定 / §7 程序化 3D 通路 / §8 呈现层架构约束含键位对账锚)。

权威数字(实测,2026-06-13):phase15 pytest **46** / phase14 回归 **56** / 系统测试 **466**(15 stage,Stage 15 PRX 46)/ Schema examples strict **32/32** / MCP 工具 **58** / 红线 diff 空(零触碰)。

## 4. 验收状态(C 系,沿用 Phase 14 形状)

| 判据 | 状态 |
|---|---|
| C1 机器全绿(pytest 46+56 / strict 32 / Stage 15+14 / 工具 58) | ✅ 全过(主会话亲跑,机制层) |
| C2 切批标准答案(amend 后呈现 3 批 golden) | ⏳ 验收期(机制 golden 已绿,真机切批待跑) |
| C3 无人值守 rung1+rung2 | ⏳ 验收期(coding agent fetch/submit 待执行) |
| C4 窗口 1 + 回流闭环(msc 试玩 2D + 反馈批) | ⏳ 验收期(msc 试玩) |
| C5 无人值守 rung3(3D) | ⏳ 验收期 |
| C6 窗口 2 终裁 | ⏳ 验收期(msc) |

- 机制层完成 ≠ 验收完成:真正赌注(3D 批无人值守、msc 试玩终裁)在验收期。最终整体复审(opus)判定机制层 **Ready to merge**。

## 5. 下一步(验收期,plan 末尾交接段)

1. amend 追加呈现 3 批(C2 切批 golden 真机断言)。
2. coding agent 无人值守跑 presentation-1/2,每 rung verified 后 runbook 调 `freeze_layer` 冻 `rung<N>-contract`/`rung<N>-impl` 层(C3)。
3. 窗口 1:msc 试玩 2D 版 → `demo_feedback_log` 登记 → `--amend-feedback` 切批 → 修复复验(C4 回流实证;诚实条款:零真实反馈时用显式"演练"合成条目)。
4. presentation-3 无人值守(C5)→ 窗口 2 终裁(C6)。
5. 收尾:document-release(本期机制层已跑一次)→ finishing-a-development-branch(**merge 方式 msc 定**)。

> 范围裁决(msc,延续 2026-06-12):"扇出 N demo + 挑选会话层"维持去除,恢复需 msc 主动提出;backlog **BL-02/BL-03/词表扩展/模板固化不纳入 Phase 15**(spec §5);已纳入 **BL-01/04/05/06**(机制层闭环,见 `Docs/acceptance/acceptance_report.md` 附 5)。

---

## 历史阶段归档

> 以下为上一版任务书与跳转页保留的归档链接,Phase 11 / 12 / 13 / 14 事实不再改写。

> **Phase 14 — Demo-First 增量主链**(已完成 2026-06-12,验收 C1-C6 全闭环 msc v1 终裁通过,**PR #46 已合 main**):agent 无人值守把 GDD 写出可玩 v0 demo + 机器守门保证增量不破可玩;可玩 demo `Plugins/Demo_MonopolyAuction/`(authored 关卡 + 键盘可玩 + 拍卖增量)。
> Phase 14 spec:[2026-06-11-phase14-demo-first-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md)
> Phase 14 plan:[2026-06-11-phase14-demo-first.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-06-11-phase14-demo-first.md)
> Phase 14 验收 runbook:[phase14_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md)
> Phase 14 backlog(P14-BL-01~06):[acceptance_report.md 附 4](/D:/UnrealProjects/Mvpv4TestCodex/Docs/acceptance/acceptance_report.md)(BL-01/04/05/06 经 Phase 15 闭环,见附 5)

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
