# 当前任务入口 — Phase 13 Skill 合成主链

> 当前状态:Phase 13 Skill 合成主链**实施完成**(2026-06-11)/ UE 5.5.4 稳定 / 验收 runbook 判据 1-4 已闭环,判据 5-12 待人工 / 真机 / Codex 执行
> 入口类型:Phase 13 任务书(实施收尾期)
> 分支:`feat/phase13-skill-synthesis-spec`(实现 commit 范围 7acd860..5911a6b)

## 1. Phase 13 是什么

产品愿景"GDD → agent 发散创造 → N 份 demo → 使用者挑选"的第一步:**让一份超出模板库的 GDD 能编出完整真机单 demo**。三个核心动作:

1. **capability gap 显式化** — 模板库外能力不再被静默丢弃,写入 `skill_graph.metadata.capability_gaps`;
2. **Stage 3 注册表数据化** — `GAMEPLAY_NODE_CONFIGS` / `BASELINE_NODE_CONFIGS` / `FRAGMENT_FAMILY_MAP` 三张硬编码表全删,节点配置由模板 `manifest.yaml` 的 `capability_bindings` + `SkillTemplates/registry_placeholders.yaml` 占位数据自描述,`registry_scan` 扫描建映射;
3. **S3.5 链内合成环节** — capability gap 经 MCP 工具对 `compiler_skill_synthesis_prepare/save` 由 agent 现场合成 6 文件 SkillTemplate 包,机器校验(synthesis_validator)+ 人审 gate(`review_status: approved`)双 gate 后方可被消费。

## 2. 权威文档

- 设计 spec:[2026-06-10-phase13-skill-synthesis-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md)(顶部含实施期修订记录)
- 实施 plan:[2026-06-10-phase13-skill-synthesis.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-06-10-phase13-skill-synthesis.md)(14 任务,TDD,等价回归先行)
- 验收 runbook:[phase13_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md)(判据 1-4 已闭环,5-12 待执行)

## 3. 交付摘要(7acd860..5911a6b,15 个实现 commit)

- **Stage 3 注册表数据化**:三张硬编码表删除,12 存量 manifest 补 `capability_bindings`,占位节点落 `registry_placeholders.yaml`,fragment family 由注册表惰性派生(`_build_fragment_family_map`),等价回归 golden 守门(改造前后 skill_graph 等价)。
- **capability gap 显式化**:required capability 查不到映射 → 记入 `metadata.capability_gaps[]`(capability_id / 来源 anchor / 原因),零静默丢弃。
- **S3.5 合成链**:`synthesis_validator`(capability_id 格式硬校验防路径穿越 / 递归 `additionalProperties: false` 含组合器 / 深度护栏)+ `skill_synthesis`(prepare 载荷含 GDD 上下文 + 6 文件规范 + few-shot 范例 + family 白名单;save 走 `.part` 事务落盘、approved 防覆盖、`data.synthesis_status` 三态、生成审阅清单)+ MCP 工具对三处注册(工具数 53→55)。
- **GDD 覆盖矩阵**:`gdd_coverage` 模块,markdown 结构切分(零语义)+ anchor 认领,`claimed` / `unclaimed` / `container` 三态,防固化四守则落地;矩阵 sidecar 随 Stage 1 保存落盘。
- **anchor 留痕**:`allow_skill_synthesis` 开启时 Stage 1 required capability 强制携带 `source_anchor`(intake alias 转发同样受控,封绕行)。
- **promote 双守卫**:run 含 `template_source=synthesized` 节点或存在未解决 `capability_gaps` → `PROMOTE_REJECTED`;skill_graph 损坏 fail-closed。
- **session**:`compiler_create_session` 增 `allow_skill_synthesis` 开关(默认 false,默认行为与现状一致)。

权威数字(实测):MCP 工具 **55**(Bridge 28 + Compiler 前端 16 + Evidence 后端 11);系统测试 **13 stage / 359 case**(Stage 13 SKS-01~89,9 个 `test_phase13_*.py`);Schema 主 **45**(Phase 13 +`gdd_coverage_matrix`,收尾时补登记 Phase 12 漏录的 `provider_call`/`retry_policy`)/ examples strict **28/28**。

## 4. 验收状态

| 判据 | 状态 |
|---|---|
| 1-4(等价回归不破现状 / 缺件点名+覆盖矩阵 / 造件闭环+重试 / 人审 gate 拦截) | **已闭环**(纯 Python 证据,见 runbook) |
| 5-12(真机 demo 四道关 / 双端等价 Claude Code+Codex / JRPG stretch 等) | **待执行**(需人工 / 真机 Editor / Codex 端 `~/.codex/config.toml` 授权) |

已知预存失败(非 Phase 13 引入,如实记录):MCP-03/04/05(环境缺 mcp 包)、MCP-08/10、P11-09/10/18、CP-44(gitignore 产物 / 历史证据缺失)。

## 5. 下一步

1. 按 runbook 执行判据 5-12(真机 / 双端 / stretch),证据落 `ProjectState/Reports/` + `ProjectState/Evidence/`。
2. 全部判据闭环后走阶段收尾:acceptance 报告定稿 → 本任务书归档 → 分支 merge(主会话处理)。
3. Phase 13 backlog(合成 skill 转正机制等)见 `Docs/acceptance/acceptance_report.md` 附 3。

---

## 历史阶段归档

> 以下为上一版跳转页保留的归档链接,Phase 11 / Phase 12 事实不再改写。

> ⚠️ UE 5.7 重构计划已于 2026-05-27 企汰;BC 知识库 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 保留作未来可能的重启资产,不主动维护。
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
