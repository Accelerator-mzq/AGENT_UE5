# Phase 14 验收 runbook

> 对应 spec §7 判据 C1-C6(`Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md`)。
> 每条做完勾选并贴证据路径。失败如实记录(KILL 是合法收尾,spec §7 如实记录条款)。
> 验收 GDD:`ProjectInputs/GDD/monopoly_extended_auction_v1.md`
> 机制实现:`feat/phase14-demo-first-spec` 分支(Task 1-10,2026-06-11~12)
> 已知预存失败清单见附录,验收时如实跳过不算 Phase 14 缺陷。

---

## C1 机器判据

- [x] `python -m pytest Plugins/AgentBridge/Tests/scripts/ -k phase14 -v` 全绿(登记 56 条)
      **已闭环(2026-06-12 执行)**:`56 passed, 369 deselected in 4.89s`
- [x] `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor --stage 14` → PASS (56/56)
      **已闭环**:exit 0,报告 `Plugins/AgentBridge/reports/2026-06-12/system_test_report_2026-06-12_080700.json`
- [x] `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor` 全量等价:除附录预存失败外零新增 FAIL
      **已闭环**:6 passed / 4 failed / 4 skipped(723.5s),失败集 = 附录 A 清单(Stage 7 CP-44 / Stage 10 MCP×5 / Stage 11 P11×3 / Stage 13 SKS 残留 4 条段传播),零新增。报告 `Plugins/AgentBridge/reports/2026-06-12/system_test_report_2026-06-12_081947.json`。
      执行注:本次跑通前清理了 2026-06-11 07:56 遗留的 headless UE Editor(PID 33008,Phase 13 验收残留,挂起 Stage 4 commandlet 通路),见附录 B。
- [x] `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` → 30/30
      **已闭环**:Checked 30 / Passed 30 / Failed 0

## C2 实战:切批标准答案

- [x] 复用 Phase 13 流程产出 gap=0 的 run:`run-20260611-052252-5101`(Phase 13 验收 run,步骤 6 后 gaps=0、两合成包 approved,直接复用)
- [x] `python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir ProjectState/runs/run-20260611-052252-5101`
      **已闭环(2026-06-12 执行)**:`[OK] demo_plan 落盘: 3 批 / 21 story`,exit 0
- [x] 标准答案断言:**恰好 3 批 / 21 story 全中**——
  - v0:17 story(末位 story-v0-docs)✓
  - increment-1:story-skill-property-auction + story-increment-1-docs ✓
  - increment-2:story-skill-stock-market + story-increment-2-docs ✓
  - 批内拓扑序机器断言 PASS(批内依赖全部排序在前;增量批跨批依赖落更早批)✓
  - manifest_version=1.0.1(命名派生澄清修订,commit 65e447a)
  - run_id:`run-20260611-052252-5101` demo_plan 路径:`ProjectState/runs/run-20260611-052252-5101/demo_plan.json`(stories/ 21 文件,全 pending)

## C3 v0 无人值守实证(最大赌注,如实记录)

- [ ] 驱动器就位(headless 会话或 driver 脚本;无人值守窗口从首次 demo_story_fetch 起算)
- [ ] coding agent 按施工规范(`ProjectInputs/ConstructionManifest/demo_plugin_standards.md` v1.0.1)
      在 `Plugins/<派生名>/` 完成 v0 全部 17 story:
  - 编译通过;冒烟:一局从开始驱动到终局零报错(GameState API 直驱)+ widget 创建冒烟
  - 冒烟 runner:`python Plugins/AgentBridge/Scripts/demo_smoke/runner.py --filter "<PluginName>.Smoke" --out ProjectState/Evidence/phase14_v0_smoke_report.json`
    (退出码契约:0=pass / 1=demo 失败计自修轮 / 3=环境故障不计自修轮)
  - README 试玩说明 + Docs/ 维护文档包(批末文档 story,机器引用对账)
  - 全部 story submit verified(经 demo_story_submit,evidence 按 evidence_class 分级)
- [ ] 自修上限:每里程碑(骨架可编译 / 完整 loop 冒烟过)≤5 轮,超限停且落盘失败报告
- [ ] 干预/超限如实降级记录:______________________
- [ ] 证据:`ProjectState/runs/<run_id>/velocity_log.json` + 冒烟报告 + 截图 → `ProjectState/Evidence/phase14_v0_*`

## C4 人审窗口 1:msc 试玩 v0

- [ ] msc 无引导玩一局,裁决 PROCEED / PIVOT / KILL:____________(留痕路径:______________________)
- [ ] PROCEED 时冻结 v0 冒烟基线(`<run_id>` 与插件名按实际填):

  ```bash
  python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ev','Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); import glob; m.freeze_v0_baseline('.', 'ProjectState/runs/<run_id>', [p.replace('\\','/') for p in glob.glob('Plugins/<派生名>/Source/*/Private/Tests/*.cpp')])"
  ```

- [ ] 批拍卖合成包(manifest review_status: pending_review → approved;Phase 13 原 gate 原位)
- [ ] PIVOT 时:写 pivot note → 删除整个 demo plugin → 重跑 v0(连续同因 PIVOT 升级 KILL 评估)
- [ ] KILL 时:失败归档(归因+可复用残值+教训),Phase 14 以"实证失败"收尾(合法产出)

## C5 增量批 1(拍卖)

- [ ] 逐 story fetch/submit;增量批冒烟带 `--v0-filter "<PluginName>.Smoke.V0"`
- [ ] submit 机器守门:v0 冒烟用例 hash 不变(v0_smoke_baseline.json 对账)且 v0 回归全绿
- [ ] 文档包更新过引用对账;msc 试玩 v1 终裁:____________
- [ ] 增量失败不毁 v0:若自修超限,增量批失败落盘,v0 保持有效交付物

## C6 接口中立

- [ ] 工具数 57:
  `python -c "import sys; sys.path.insert(0, 'Plugins/AgentBridge'); from MCP import tool_definitions as td; print(td.TOOL_COUNT)"`
- [ ] demo_story_fetch / demo_story_submit 在 MCP server 工具清单可见(Codex 可接入,本期不实证)

---

## 附录 A:已知预存失败(验收时跳过,非 Phase 14 缺陷)

| 用例 | 根因 | 说明 |
|------|------|------|
| MCP-03/04/05 | 环境缺 `mcp` Python 包 | Phase 13 验收时即存在 |
| MCP-08/10 | 历史证据文件缺失(gitignore 产物) | 同上 |
| P11-09/10/18 | gitignore 产物缺失 | 同上 |
| CP-44 | gitignore 产物缺失 | 同上 |
| SKS:test_sks04_family_map_derived_equals_legacy | Phase 13 验收 run 的 2 个 approved 合成包留树(`SkillTemplates/synthesized/`,main d02e8bf 即存在) | Phase 13 验收发现 2(树内目录默认信任);修复属 Phase 13 backlog(registry_scan 目录白名单),不在 Phase 14 范围 |
| SKS:test_sks04_module_builder_equals_legacy | 同上 | 同上 |
| SKS:test_zz_real_templates_tree_no_synthesized_residue | 同上 | 同上 |
| SKS:test_sks02_real_templates_cover_all_16_capabilities | 同上 | 同上 |

> 后四条系统测试层面表现为 Stage 13 FAIL(段传播);pytest 层面为 `-k phase13` 4 failed 90 passed。
> 全量回归判定口径:与本清单一致即等价,出现清单外失败才算回归。

## 附录 B:环境故障记录(退出码 3,不计入 demo 失败与自修轮)

| 时间 | 故障 | 处置 |
|------|------|------|
