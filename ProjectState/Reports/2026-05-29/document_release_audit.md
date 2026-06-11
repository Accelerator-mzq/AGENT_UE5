# Document Release Audit — fix/baseline-realization-divergence @ 18223b4

> 运行时间: 2026-05-29
> 比较基准: main (merge-base)
> 触发事件: push / merge 前置门禁(收尾链 document-release)
> 变更性质: Stage 4 内部编译逻辑修复(baseline realization_eligible 发散落地)

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| baseline realization_eligible 节点发散落地(spec_fragments 写入 selected_realization) | NONE(无治理/入口变更) | `Docs/design/LLD/06_skills_and_templates.md`(已同步函数职责描述) | `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`(实现) | `ProjectState/Reports/2026-05-29/baseline_realization_divergence_evidence.md` |
| `_build_discovered_fragment` 去 HUD 硬编码,按 capability_id 经 `_capability_map` 动态查 | NONE | `Docs/design/LLD/06_skills_and_templates.md`(同步说明) | 同上(domain_skill_runtime.py) | 同上 evidence + `Docs/archive/superpowers/specs/2026-05-29-...-design.md` |
| HUD required_elements 保留 GDD 锁定来源(constraint_fields.ui.required_hud_fields) | NONE | `Docs/design/LLD/06_skills_and_templates.md`(注明 HUD 取值来源) | 同上(domain_skill_runtime.py) | 同上 evidence |
| 离线回归测试(9 用例) | NONE | NONE(未登记为正式 System Test Case) | `Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py` | evidence 内贴测试输出 |

零覆盖项:无。仅 A 层无变更属预期(本次为内部编译逻辑修复,不触及项目入口/治理)。

## Documentation health

- README.md: Current — 本次无入口/导航变更,无需改。
- AGENTS.md: Current — 无 Agent 规则变更。
- CLAUDE.md: Current — 「可以修改 / 绝对不要修改」清单未受影响;改动均落在 `Compiler/`(可改区)与 `Tests/scripts/`、`Docs/`、`ProjectState/`(项目层可改区)。
- task.md / Docs/INDEX.md: Current — 阶段入口/索引无需改(Phase 11 已归档,本次为其后置 follow-up 修复)。
- Layer B(阶段事实):Updated — `Docs/design/LLD/06_skills_and_templates.md` 已同步:① `_build_gameplay_spec_fragment` 描述补 selected_realization 来源;② `_build_baseline_spec_fragment` 描述补 converged_pack 参数与 realization_eligible 写入 selected_realization;③ 注明 realization_eligible baseline 经 `_build_discovered_fragment` 动态查 capability、HUD required_elements 仍以 constraint_fields 为准。
- Layer C(框架):
  - `Plugins/AgentBridge/Docs/*`: Current — 经 grep 确认未描述此层级实现细节,无 stale 陈述。
  - `Plugins/AgentBridge/Schemas/*`: Current — 未改 schema;`skill_fragment_v2.schema.json` 的 `spec_fragments` 为 `additionalProperties:{"type":"object"}`,新增 `selected_realization` 字段天然合法。`validate_examples.py --strict` 实测 27/27 通过。
  - `Plugins/AgentBridge/Tests/SystemTestCases.md`: Current — 本次新增的是 `Tests/scripts/` 下脚本级回归测试,非正式登记的 System Test Case,不改登记台账。
- Backlog(`Docs/acceptance/acceptance_report.md#1-附` / `04_Open_Risks.md`): No change — 本次为已完成修复,非新增延期项;未静默删除任何 active 条目。已知遗留 tech-debt(评审提出、本次有意不处理)已记录于下,供后续按需立项,不入正式 backlog 以免噪音。
- ProjectState/Reports: Updated — 新增 `2026-05-29/baseline_realization_divergence_evidence.md`(改动综述 + 两来源不等数据事实 + 9 测试 PASS + 27/27 契约)与本审计文件。
- Archive(`Docs/History/**`、历史日期 Reports): Read-only — 未触碰。

### 验证证据(document-release 收尾自验,均本机实跑)
- `python Plugins/AgentBridge/Tests/scripts/test_baseline_realization_divergence.py` → All 9 passed
- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` → Checked 27 / Passed 27 / Failed 0
- `task14_phase11_baseline_template_validation.py` → exit 0 但零输出,无法确认断言真正执行;记为不确定,不作为通过证据(核心改动已被前两项 + 最终整体审查覆盖)。

### 已知 tech-debt(本次有意不处理,供后续按需立项)
- `_selected_realization_from_converged` 与 `_build_gameplay_spec_fragment` 行内块逻辑重复(保持一致,未合并 gameplay 侧调用)。
- 空 `dimension_id` 在 dict 推导中以空串为 key、后者覆盖前者(与 gameplay 行内既有行为一致)。
- HUD required_elements 来源可考虑改用既有 `_constraint_values` 工具函数(当前内联 `.get()` 链)。
