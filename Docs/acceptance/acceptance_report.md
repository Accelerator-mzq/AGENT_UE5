# 验收报告 — Mvpv4TestCodex

> 版本: v1(2026-05-26,Phase 1.16 初稿)
> 上游: Docs/Current/18_Phase11_Closeout.md + ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md + phase11_feature_coverage_report.md
> 关联: Docs/FEATURE_INVENTORY.md(105 F-* IDs)+ Docs/testing/test_spec.md(266 case)+ Docs/contracts/{schemas_catalog,mcp_tools_catalog}.md
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §4.5
> 状态: §1 / §2 / §4 已基于 Phase 11 as-is 实地化;§3 UE 5.7 验收为空模板,待重构完成后逐项勾选

## 1. Phase 11 as-is 验收基线

### 1.1 总体结论

Phase 11(Skill-First Design Compiler Framework)已于 2026-04-17 完成收尾,最终结论 `pass`,详见
[task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
与 [18_Phase11_Closeout.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/18_Phase11_Closeout.md)。
本次重构(UE 5.5.4 → 5.7)的 as-is 验收基线锁定在该收尾事实,不再回退。已交付的正式主链为:
`GDD → Root Skill Contract + Universal Baseline Merge → Clarification Gate → Skill Graph Planning →
Domain Skill Runtime → Design Space Discovery / Realization / Convergence → Cross Review v2 →
Build IR v2 + naming_resolution_log → Reviewed Handoff v3 → Execution`。
Run 治理(`run_id` / `fast_mode` / `generator_provider` / `promotable`)、Baseline Domain 模板体系
(Start Screen / Main Menu / Settings / Pause / Results / HUD 六项)、以及 UE 运行时最小可玩性
(Editor + Standalone 双路径)均已留证。残留项仅有 `LLM Internal` 高负载验收暂缓
(等 `llm_client` 框架升级)与 `raw DebugGame + .uproject` 非标准路径不再作为官方验收链。

Phase 11 收尾 2026-04-17 实测三项硬证据可作为 UE 5.7 重构后的对照基线:
`validate_examples.py --strict` 实测 `26/26 通过`、TASK 11 复跑 `run-20260417-051425-aad0`
`generator_provider=mcp_agent / promotable=True`、TASK 14A standalone smoke 退出码 `0`
且 `playability_passed=True / baseline_passed=True`。
本验收报告锁定的事实层是这些数字与产物路径,不是文档内的描述性结论。
任何 UE 5.7 后的回归必须先在 ProjectState/Reports 留证,再决定基线是否调整。

### 1.2 功能覆盖逐项核对

源自 [phase11_feature_coverage_report.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/phase11_feature_coverage_report.md)
对 `Docs/Phase11/00-13 + 14_Agent_Interaction_Protocol.md` 共 15 份设计包的逐项绑定结果:

| Phase 11 文档 | 关键能力 | 绑定 TASK | 状态 |
|---------------|----------|-----------|------|
| 00 Document_Index | 主链索引 / 10 类问题 / 发散位置总览 | T01/09A/09B/10/15 | 已覆盖 |
| 01 Unified_Architecture | 7 阶段主链 / MCP 前后端边界 / v1↔v2 兼容 | T02/03/05/10/12/15 | 已覆盖(工具数已纠偏 53) |
| 02 Root_Skill_Contract | 10 问题结构 / Constraint/Variant / Baseline merge | T04/06/10/11 | 已覆盖 |
| 03 Universal_Baseline | 六项底线 / presence_only / realization_eligible / clarification_gated | T06/09B/10/11/14/14A/15 | 已覆盖 |
| 04 Baseline_Realization | 三类域 / Baseline Fragment / Start Screen 能力级 | T06/08/09B/14/14A | 已覆盖 |
| 05 Clarification_Gate | 4 档决策 / provisional 传播 / fast_mode 保护 | T07/10/13 | 已覆盖 |
| 06 Constraint_vs_Variant | 不可拆分项 / variant bounds 传播 | T06/09B/10/11 | 已覆盖 |
| 07 Design_Space_Discovery | Discovery / Candidates / Convergence / design_decision_log | T09B/11/13 | 已覆盖 |
| 08 Skill_Graph & Domain_Skill | SkillGraph 节点/边 / Domain Skill 四重职责 | T08/09B/14/14A | 已覆盖 |
| 09 Run_Isolation | Run Workspace / promotable / compare/promote | T02/11/12/13 | 已覆盖 |
| 10 Naming_and_Path | GDD-First 命名 / UE5 路径 / naming_resolution_log | T10/11/15 | 已覆盖 |
| 11 Schema_and_Artifact | Phase 11 Schema 集 / Stage/Artifact Map | T04/05/10/11/12/15 | 已覆盖(工具数已纠偏) |
| 12 Implementation_Taskbook | 分批策略 / 测试策略 | T01-15 | 已覆盖 |
| 13 Claude_Handoff | 强制阅读顺序 / 不可做项 | 全 TASK + T15 | 已覆盖 |
| 14 Agent_Interaction_Protocol(附录) | Prompt-First / GeneratorProvider / Context Bundle | T09A/09B/10/11/13/14 | 已覆盖 |

15 份文档中的 Phase 11 新增功能全部已绑定具体 TASK 与证据报告,无"新增功能未绑定 TASK"
的缺口;Stage 1 / 4 / 5 / 6 / 7 已串行通过,`--no-editor` 等价覆盖补录已完成;
Defer 治理项与 UE 运行时专项全部落盘,残留风险仅有 `LLM Internal` 高负载验收暂缓与
`raw DebugGame + .uproject` 非标准路径,均不阻塞 UE 5.7 重构。

### 1.3 关键数字基线

以下数字为 Phase 11 as-is 实测事实,作为 UE 5.7 重构后验收的对照线(任何回退视为 regression):

| 维度 | 数量 | F-* 区段 / 锚点 |
|------|------|-----------------|
| C++ 核心类 | 6 | F-CPP-01..06(Subsystem / Commandlet / UATRunner / AutomationDriverAdapter / BridgeTypes / Module) |
| Bridge Python 模块 | 9 | F-BRG-01..09 |
| Orchestrator 模块 | 8 | F-ORC-01..08(主体编排 / Plan / Spec / Verify / Report / Recovery / Handoff / ForgeUE) |
| Compiler 框架 | ~30 文件 | F-CMP-01..24(Legacy v1 子模块 6 + Phase 11 主链 stages 13 + 框架 Stage 1..7 5) |
| MCP 工具(可见) | 53 | F-MCP-01..13(Bridge 28 + 前端 14 + 后端 11;含 4 alias / 49 正式主工具) |
| Schemas | 41 主 + 26 examples = 67 | F-SCH-01..06(v3 集 9 + v1/v2 兼容 / common 6 / feedback / 治理 / examples) |
| SystemTest(Python) | 266 case(15 测试类,Phase 8/9/10 Stage 240 + Phase 11 增量) | F-TST-04 |
| C++ Automation | ~26 | F-TST-01..03(L1 Query/Write/UITool + L2 闭环 Spec + L3 FunctionalTest/Gauntlet) |
| Skill 模板 | 12 skill × 6 文件 = 72 | F-SKL-03 / F-SKL-04(Baseline 6 + Genre Pack Boardgame) |
| 旧文档 inventory | 108 行(38 already-consumed + 70 archive-only) | Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv |

## 2. 验收门禁清单

UE 5.7 重构验收必须逐项通过下列 5 个门禁,任何一项不通过视为整体未达验收:

### 2.1 Schema --strict 26/26

```bash
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

期望:`checked=26, passed=26, failed=0`(对应 Phase 11 收尾 2026-04-17 实测事实)。
该数字基线意味着 Schema 集合中每个主 schema 至少有一个落地的 example,且每个 example
能在 `--strict` 严格模式下通过 JSON Schema Draft 校验。
详细 schema 与 example 的逐项映射见 [schemas_catalog.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/contracts/schemas_catalog.md) 附录。
对应 F-SCH-01..06 / F-VAL-02。任何 schema 升级或 example 改动,都必须在本门禁下复测才能合入。

### 2.2 SystemTest 266 case

```bash
python Plugins/AgentBridge/Tests/run_system_tests.py
```

期望:`STAGES TOTAL_CASES = 266`,15 测试类全 pass(允许显式 skip,不允许 fail)。
15 测试类逐类详情见 [test_spec.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/testing/test_spec.md) §3。
对应 F-TST-04;`--no-editor` 等价分段验证见 task08_orchestrate 内置链路。

### 2.3 UE 运行时双路径

UE Editor 在线引导关卡(F-RT-01)与 Standalone Staged 运行(F-RT-02)均须完成最小可玩性 smoke。
Editor 路径要求关卡可加载、初始 Actor 列表与 Spec 一致、基础交互(Start Screen / Main Menu /
Pause / Results)能响应输入;Standalone 路径要求 UAT BuildCookRun 产出的可执行体能独立运行,
脱离 Editor 进程也能跑通同一份 baseline smoke 用例。
Phase 11 收尾基线证据:[task14a_ue_runtime_playability_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_ue_runtime_playability_validation.md)
与 [task14a_standalone_runtime_smoke_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task14a_standalone_runtime_smoke_validation.md)。
Standalone smoke 入口脚本:`Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py`。
注意:`raw DebugGame + .uproject` 不在官方验收链(Phase 11 收尾时已明确)。
UE 5.7 升级后,BC-008 EditorScriptingUtilities 与 BC-025 硬编码 `UE_5.5` 路径
若未处理,该门禁会立即失败。

### 2.4 MCP 工具注册数 53

```bash
python -c "from Plugins.AgentBridge.MCP.tool_definitions import ALL_TOOLS; print(len(ALL_TOOLS))"
```

期望输出 `53`(Bridge 28 + Compiler 前端 14 + 后端治理/Evidence 11;含 4 兼容 alias)。
此为 Phase 11 收尾纠偏后的实现事实,Phase 11 实施前文档中的 `50` 是 planning 口径,不再使用。
详细工具表(主工具 49 + alias 4)见 [mcp_tools_catalog.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/contracts/mcp_tools_catalog.md)。
对应 F-MCP-01..13。

### 2.5 文档体系自检

- [FEATURE_INVENTORY.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/FEATURE_INVENTORY.md) 105 行 F-* IDs 全部有主文档锚点(无 `TBD`,无空白)。
- [redirects.json](/D:/UnrealProjects/Mvpv4TestCodex/Docs/redirects.json) 108 条 old→new 映射齐(Phase 0.4 已实测 108 条)。
- [Docs/archive/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/README.md) 反向映射表与
  [old-docs-inventory.csv](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv) 完全一致(108 行)。
- 4 份契约文件(tool_contract / field_specification / schemas_catalog / mcp_tools_catalog)与
  7 份 LLD(01..07)全部实地化,无 placeholder。
- 对应 F-HOOK-01 document-release gate 通过、F-VAL-01..03 治理脚本全绿。

## 3. UE 5.7 重构验收模板(空模板,待重构完成后填)

> 说明:本节是 UE 5.5.4 → 5.7 重构完成后的验收 checkbox 模板。
> 每项需附执行命令与证据文件链接,证据落 `ProjectState/Reports/<YYYY-MM-DD>/`。
> Breaking Change ID 来源:[2026-05-26-ue57-breaking-changes-scan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md) §3 共 25 条。

### 3.1 P1 已裁决 confirmed 6 条迁移

- [ ] **BC-008** EditorScriptingUtilities 模块依赖迁移完成(AgentBridge.Build.cs / AgentBridgeTests.Build.cs / AgentBridge.uplugin 同步切到 UEditorActorSubsystem / ULevelEditorSubsystem)
- [ ] **BC-010** `IncludeOrderVersion = Unreal5_7`(Source/Mvpv4TestCodex.Target.cs + Source/Mvpv4TestCodexEditor.Target.cs)
- [ ] **BC-012** `.uproject EngineAssociation = "5.7"`(Mvpv4TestCodex.uproject:3)
- [ ] **BC-016** `unreal.EditorLevelLibrary` 全部替换为 `unreal.UnrealEditorSubsystem` / `unreal.LevelEditorSubsystem` / `unreal.EditorActorSubsystem`(MCP/server.py + Scripts/bridge/{query_tools,write_tools}.py)
- [ ] **BC-017** `unreal.EditorAssetLibrary` 全部替换为 `unreal.EditorAssetSubsystem`(MCP/server.py + Scripts/bridge/query_tools.py)
- [ ] **BC-025** 硬编码 `UE_5.5` 引擎路径批量更新为 `UE_5.7`(run_system_tests.py + task14a_phase11_standalone_smoke.py + start_ue_editor_*.ps1 共 7 处)

### 3.2 P1 已裁决 false-positive 留档

- [ ] **BC-007** UEditorLevelLibrary C++ 注释级依赖确认 false-positive(真实编译依赖落在 BC-008,不重复登记迁移)

### 3.3 P2/P3 suspected 18 条实测裁决

- [ ] P2 12 条(BC-001/002/004/005/006/011/014/015/019/020/022/023)逐条 实测 → confirmed / false-positive 裁决
- [ ] P3 6 条(BC-003/009/013/018/021/024)逐条 实测 → confirmed / false-positive 裁决

### 3.4 五个门禁在 UE 5.7 下复测

- [ ] 系统测试 266 case 在 UE 5.7 下全 pass(对照 §2.2 基线)
- [ ] Schema --strict 26/26 在 UE 5.7 下保持通过(对照 §2.1 基线)
- [ ] UE Editor + Standalone 双路径在 5.7 下最小可玩性 smoke 通过(对照 §2.3 基线)
- [ ] MCP 工具注册数仍为 53(若新增需同步更新 §2.4 基线;不允许回退)
- [ ] FEATURE_INVENTORY 105 行 UE 5.7 状态列全部填实(`unchanged` / `migration` / `deprecated` / `new` 四态之一,无 `TBD`)
- [ ] SRS / HLD / LLD 7 份的 "UE 5.7 迁移变更点" 小节实地化(从 placeholder 切换为实测内容)

## 4. 防遗漏 checklist

为保证 105 F-* IDs 验收门禁底座完整、四份契约 + 七份 LLD + 108 条 redirects 齐全、
25 条 BC 全部裁决到位,提供如下逐项对账模板:

### 4.1 FEATURE_INVENTORY 105 F-* IDs 全量勾选模板

每行需逐一确认在 UE 5.7 下的状态:

- [ ] F-CPP-01..06 共 6 行(C++ 核心类)
- [ ] F-BRG-01..09 共 9 行(Bridge Python 模块)
- [ ] F-ORC-01..08 共 8 行(Orchestrator 模块)
- [ ] F-CMP-01..24 共 24 行(Legacy v1 6 + Phase 11 主链 / 框架 18)
- [ ] F-MCP-01..13 共 13 行(MCP 工具族)
- [ ] F-SKL-01..04 共 4 行(SkillGraph / Domain Skill / 模板)
- [ ] F-RT-01..05 共 5 行(Runtime / Evidence / Reports / Run Workspace)
- [ ] F-CHN-01..07 + F-CHN-S4-01..03 + F-CHN-MODE-01..03 共 13 行(主链 / Stage 4 三路 / 模式路由)
- [ ] F-GOV-01..04 共 4 行(run_id / fast_mode / generator_provider / compare/promote)
- [ ] F-SCH-01..06 共 6 行(Schema 集)
- [ ] F-VAL-01..03 共 3 行(治理 / Schema / Evidence 校验)
- [ ] F-TST-01..04 共 4 行(L1/L2/L3 + 系统测试套件)
- [ ] F-HOOK-01..02 共 2 行(document-release gate + Git hooks)
- [ ] F-INP-01..02 共 2 行(GDD 实例 + Compiler Preset)
- [ ] F-DEMO-02..03 共 2 行(可运行 demo + 资产生成辅助)

合计 6+9+8+24+13+4+5+13+4+6+3+4+2+2+2 = **105 行**(对应 FEATURE_INVENTORY 主表 105 行,验收门禁底座)。

勾选规则:每行需在 UE 5.7 重构完成后,由 msc 实测对照 SRS / LLD 锚点 + 证据源代码路径
后单独裁决。UE 5.7 状态列取值受限于 `unchanged` / `migration` / `deprecated` / `new` 四态,
不允许保留 `TBD`;若实测发现旧功能在 5.7 下变为新形态,需要在 inventory 表新增一行 new
状态行,旧行标 `deprecated`,以保证血缘可追溯。

### 4.2 contracts 4 份契约完整

- [ ] `Docs/contracts/tool_contract.md` 实地化(MCP 工具调用契约)
- [ ] `Docs/contracts/field_specification.md` 实地化(字段规范)
- [ ] `Docs/contracts/schemas_catalog.md` 实地化(Schema 目录,41 主 + 26 examples)
- [ ] `Docs/contracts/mcp_tools_catalog.md` 实地化(53 工具目录)

### 4.3 LLD 7 份完整

- [ ] `Docs/design/LLD/01_cpp_subsystem.md`(对应 F-CPP-01..06)
- [ ] `Docs/design/LLD/02_bridge.md`(对应 F-BRG-01..09)
- [ ] `Docs/design/LLD/03_orchestrator.md`(对应 F-ORC-01..08)
- [ ] `Docs/design/LLD/04_compiler.md`(对应 F-CMP-01..24)
- [ ] `Docs/design/LLD/05_mcp_server.md`(对应 F-MCP-01..13)
- [ ] `Docs/design/LLD/06_skills_and_templates.md`(对应 F-SKL-01..04)
- [ ] `Docs/design/LLD/07_runtime_and_evidence.md`(对应 F-RT-01..05)
- [ ] `Docs/design/LLD/README.md` 索引齐(7 份 LLD 入口表 + 模块归属对照)

### 4.4 redirects.json 108 条映射完整

- [ ] `Docs/redirects.json` 实测 108 条 old→new 映射(对应 inventory CSV 108 行)
- [ ] Phase 4 grep 校验脚本能在新文档树中命中每条 new_anchor
- [ ] `Docs/archive/README.md` 反向映射表与 inventory CSV 108 行内容完全一致

### 4.5 BC 25 条裁决状态对账

- [ ] **P1 共 7 条已裁决**:6 confirmed(BC-008/010/012/016/017/025)+ 1 false-positive(BC-007)
- [ ] **P2 共 12 条 suspected**:实测裁决记录 confirmed / false-positive 个数
- [ ] **P3 共 6 条 suspected**:实测裁决记录 confirmed / false-positive 个数
- [ ] 合计 7 + 12 + 6 = **25 条**(对应 scan spec §3 表与 §4 三档分桶,reviewer 字段全部从 `pending-msc` 切到 `msc`)

> 注:scan spec §4 P1 行写作 "7 条已裁决",其中 1 条 false-positive + 6 条 confirmed,
> 与 §3 表内 false_positive_status 字段完全一致。本节按 scan spec 实际值 25 条对账。

## 附:Phase 11 残留与重构注意事项

- `LLM Internal` 高负载验收暂缓,等 `llm_client` 框架升级后重开,不阻塞 UE 5.7 重构。
  Phase 11 正式主路径仍是 `MCP Agent` 驱动的 Stage 4 创造性生成,`heuristic_fallback` 是显式后备。
- `raw DebugGame + .uproject` 非标准路径不作为官方验收链;若要恢复,作为独立构建链问题治理。
- Phase 11 v2 完整 run 产物落盘于 [run-20260417-051425-aad0](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260417-051425-aad0),
  作为 UE 5.7 下 E2E 验证对照基线。后续 UE 5.7 下做对比验证时,新 run 的 `promotable`
  字段、Stage 4 generator 一致性、naming_resolution_log 命中率都须与该基线 run 对照。
- 任何 UE 5.7 下的 regression 必须先在 ProjectState/Reports/ 留证,再决定是否调整本验收报告基线。
- Phase 11 实施前文档中 MCP 工具数 `50` 是 planning 口径,本报告统一以收尾事实 `53` 为准
 (49 主工具 + 4 兼容 alias),Phase 11 收尾已同步纠偏到 Current 文档与 Schema 参考文档。
- UE 5.7 重构未达成前,本报告 §3 模板项保留 `[ ]` 未勾选状态;勾选动作只在 UE 5.7
  实测产出对应证据后由 msc 手动完成,Claude/Codex 不得自动批量勾选以避免假阳性。
