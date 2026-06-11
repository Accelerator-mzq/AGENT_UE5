# 验收报告 — Mvpv4TestCodex

> 版本: v1(2026-05-26,Phase 1.16 初稿)
> 上游: <code>Docs/Current/18&#95;Phase11&#95;Closeout.md</code>(Phase 4 已搬到 `Docs/archive/current/18_Phase11_Closeout.md`,本文件 §1 是其消化后归宿)+ ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md + phase11_feature_coverage_report.md
> 关联: Docs/FEATURE_INVENTORY.md(108 F-* IDs)+ Docs/testing/test_spec.md(359 case)+ Docs/contracts/{schemas_catalog,mcp_tools_catalog}.md
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §4.5
> 状态: §1 / §2 / §4 已基于 Phase 11 as-is 实地化;§3 UE 5.7 验收为空模板,待重构完成后逐项勾选

## 1. Phase 11 as-is 验收基线

### 1.1 总体结论

Phase 11(Skill-First Design Compiler Framework)已于 2026-04-17 完成收尾,最终结论 `pass`,详见
[task15_phase11_final_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md)
与本节(原 <code>Docs/Current/18&#95;Phase11&#95;Closeout.md</code>,Phase 4 已归 `Docs/archive/current/18_Phase11_Closeout.md`)。
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

> ⚠️ **UE 5.7 重构计划已于 2026-05-27 企汰**;本节门禁原为 UE 5.7 重构验收设计,**Phase 12 收尾后改作 UE 5.5.4 主线的回归门禁基线**,任何回归视为 main 退化。

下列 5 个门禁是 main 主线的回归门禁(原 UE 5.7 重构验收口径),任何一项不通过视为 main 退化:

### 2.1 Schema --strict 28/28

```bash
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```

期望:`checked=28, passed=28, failed=0`(基线演进:Phase 11 收尾 26 → 2026-05-27 ForgeUE +1 → 2026-06-11 Phase 13 +`phase13_gdd_coverage_matrix.example.json` = 28)。
该数字基线意味着登记进 strict 映射的每个 example 能在 `--strict` 严格模式下通过 JSON Schema Draft 校验。
详细 schema 与 example 的逐项映射见 [schemas_catalog.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/contracts/schemas_catalog.md) 附录。
对应 F-SCH-01..06 / F-VAL-02。任何 schema 升级或 example 改动,都必须在本门禁下复测才能合入。

### 2.2 SystemTest 359 case

```bash
python Plugins/AgentBridge/Tests/run_system_tests.py
```

期望:`STAGES TOTAL_CASES = 359`(基线演进:266 → Phase 12 +LIR 4 = 270 → Phase 13 +SKS 89 = 359),17 测试类全 pass(允许显式 skip,不允许 fail)。
17 测试类逐类详情见 [test_spec.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/testing/test_spec.md) §3。
对应 F-TST-04;`--no-editor` 等价分段验证见 task08_orchestrate 内置链路。
已知预存失败(非 Phase 13 引入,2026-06-11 如实记录):MCP-03/04/05(环境缺 `mcp` 包)、MCP-08/10、P11-09/10/18、CP-44(gitignore 产物 / 历史证据缺失)。

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

### 2.4 MCP 工具注册数 55

```bash
python -c "from Plugins.AgentBridge.MCP.tool_definitions import ALL_TOOLS; print(len(ALL_TOOLS))"
```

期望输出 `55`(Bridge 28 + Compiler 前端 16 + 后端治理/Evidence 11;含 4 兼容 alias。基线演进:Phase 11 收尾 53 → 2026-06-11 Phase 13 +`compiler_skill_synthesis_prepare/save` = 55)。
Phase 11 实施前文档中的 `50` 是 planning 口径,不再使用。
详细工具表(主工具 51 + alias 4)见 [mcp_tools_catalog.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/contracts/mcp_tools_catalog.md)。
对应 F-MCP-01..13 + F-CMP-25。

### 2.5 文档体系自检

- [FEATURE_INVENTORY.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/FEATURE_INVENTORY.md) 108 行 F-* IDs 全部有主文档锚点(无 `TBD`,无空白;2026-06-11 Phase 13 +3 行)。
- [redirects.json](/D:/UnrealProjects/Mvpv4TestCodex/Docs/redirects.json) 108 条 old→new 映射齐(Phase 0.4 已实测 108 条)。
- [Docs/archive/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/README.md) 反向映射表与
  [old-docs-inventory.csv](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv) 完全一致(108 行)。
- 4 份契约文件(tool_contract / field_specification / schemas_catalog / mcp_tools_catalog)与
  7 份 LLD(01..07)全部实地化,无 placeholder。
- 对应 F-HOOK-01 document-release gate 通过、F-VAL-01..03 治理脚本全绿。

## 3. UE 5.7 重构验收模板(**计划已企汰 2026-05-27**,模板保留作未来可能重启的资产)

> ⚠️ **UE 5.7 重构计划已于 2026-05-27 企汰**。本节模板保留(BC 知识库尚有 P1 6 条 msc 已裁决 + P2/P3 留实测)作为未来重启资产,但本阶段不再主动维护、不阻塞主线。
>
> 说明:本节原为 UE 5.5.4 → 5.7 重构完成后的验收 checkbox 模板。
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

### 4.1 FEATURE_INVENTORY 105 F-* IDs 全量勾选

每行 F-* ID 在 UE 5.7 重构完成后,由 msc 实测对照 SRS / LLD 锚点逐项勾选。完整 105 行(自 Phase 2.3 由 `ProjectState/Reports/2026-05-26/_acceptance_checklist_gen.md` 生成):

- [ ] F-CPP-01 UAgentBridgeSubsystem
- [ ] F-CPP-02 UAgentBridgeCommandlet
- [ ] F-CPP-03 FUATRunner
- [ ] F-CPP-04 FAutomationDriverAdapter
- [ ] F-CPP-05 BridgeTypes 共享类型
- [ ] F-CPP-06 FAgentBridgeModule
- [ ] F-BRG-01 L1 查询接口族
- [ ] F-BRG-02 L1 写接口族
- [ ] F-BRG-03 L1 反馈接口族
- [ ] F-BRG-04 L3 UI 自动化族
- [ ] F-BRG-05 Remote Control HTTP 客户端
- [ ] F-BRG-06 UAT 包装器 Python 侧
- [ ] F-BRG-07 UE 资产/关卡 helpers
- [ ] F-BRG-08 项目配置解析
- [ ] F-BRG-09 bridge_core 通信主体
- [ ] F-ORC-01 主体编排 + 通道选择
- [ ] F-ORC-02 Plan 生成
- [ ] F-ORC-03 Spec 读取
- [ ] F-ORC-04 验证与对标
- [ ] F-ORC-05 报告生成
- [ ] F-ORC-06 故障恢复规划
- [ ] F-ORC-07 Handoff 执行
- [ ] F-ORC-08 ForgeUE manifest 导入
- [ ] F-CMP-01 Legacy Compiler — analysis
- [ ] F-CMP-02 Legacy Compiler — generation
- [ ] F-CMP-03 Legacy Compiler — handoff
- [ ] F-CMP-04 Legacy Compiler — intake
- [ ] F-CMP-05 Legacy Compiler — review
- [ ] F-CMP-06 Legacy Compiler — routing
- [ ] F-CMP-07 Phase 11 Pipeline 主入口
- [ ] F-CMP-08 Stage — root_skill_contract
- [ ] F-CMP-09 Stage 2 — 澄清门/Clarification Gate
- [ ] F-CMP-10 Stage 3 — 技能图规划/Skill Graph Planning
- [ ] F-CMP-11 Stage 4 路 A — 设计空间发现/Discovery Fallback
- [ ] F-CMP-12 Stage 4 路 B — 实现化/Realization Fallback
- [ ] F-CMP-13 Stage 4 路 C — 收敛/Convergence Fallback
- [ ] F-CMP-14 Stage 通用 — Agent 协议/Agent Protocol
- [ ] F-CMP-15 Stage 通用 — LLM 客户端/LLM Client
- [ ] F-CMP-16 Stage 7 — Handoff v3 输出/Handoff v3
- [ ] F-CMP-17 Stage 5 — 跨审 v2/Cross Review v2
- [ ] F-CMP-18 Stage 6 — 下降 v2/Lowering v2
- [ ] F-CMP-19 Stage 4 — 领域技能运行时/Domain Skill Runtime
- [ ] F-CMP-20 Framework — cross_review (Legacy v1 Pipeline)
- [ ] F-CMP-21 Framework — intake (Legacy v1 Pipeline)
- [ ] F-CMP-22 Framework — lowering (Legacy v1 Pipeline)
- [ ] F-CMP-23 Framework — planner (Legacy v1 Pipeline)
- [ ] F-CMP-24 Framework — skill_runtime (Legacy v1 Pipeline)
- [ ] F-MCP-01 Bridge L1 查询族(MCP 暴露)
- [ ] F-MCP-02 Bridge L1 写族(MCP 暴露)
- [ ] F-MCP-03 Bridge L1 反馈族(MCP 暴露)
- [ ] F-MCP-04 Bridge L2 编辑器服务族
- [ ] F-MCP-05 Bridge L3 UI 族(MCP 暴露)
- [ ] F-MCP-06 前端 Stage 1 Root Skill Contract 族
- [ ] F-MCP-07 前端 Stage 2 Clarification Gate 族
- [ ] F-MCP-08 前端 Stage 3 Skill Graph Planning 族
- [ ] F-MCP-09 前端 Stage 4 节点交互族
- [ ] F-MCP-10 后端 Evidence 读写族
- [ ] F-MCP-11 后端 Run 治理族
- [ ] F-MCP-12 兼容 alias 族
- [ ] F-MCP-13 MCP Server 主入口
- [ ] F-SKL-01 SkillGraph 数据结构
- [ ] F-SKL-02 Domain Skill Runtime
- [ ] F-SKL-03 Baseline 6 Skill 模板
- [ ] F-SKL-04 Genre Pack — Boardgame
- [ ] F-RT-01 UE Editor 在线引导关卡
- [ ] F-RT-02 Standalone Staged 运行时
- [ ] F-RT-03 Evidence 落盘
- [ ] F-RT-04 Reports 生成
- [ ] F-RT-05 Run Workspace 隔离
- [ ] F-CHN-01 主链 Stage 1 — Root Skill Contract
- [ ] F-CHN-02 主链 Stage 2 — Clarification Gate
- [ ] F-CHN-03 主链 Stage 3 — Skill Graph Planning
- [ ] F-CHN-04 主链 Stage 4 — Design / Realization / Convergence
- [ ] F-CHN-05 主链 Stage 5 — Cross Review v2
- [ ] F-CHN-06 主链 Stage 6 — Lowering v2
- [ ] F-CHN-07 主链 Stage 7 — Handoff v3
- [ ] F-CHN-S4-01 Stage 4 路 A — Design Space Discovery
- [ ] F-CHN-S4-02 Stage 4 路 B — Realization
- [ ] F-CHN-S4-03 Stage 4 路 C — Convergence
- [ ] F-CHN-MODE-01 模式路由 — Greenfield
- [ ] F-CHN-MODE-02 模式路由 — Brownfield
- [ ] F-CHN-MODE-03 模式路由 — Playable Runtime
- [ ] F-GOV-01 run_id 生命周期
- [ ] F-GOV-02 fast_mode 不可 promote
- [ ] F-GOV-03 generator_provider 影响 is_promotable
- [ ] F-GOV-04 compare/promote 工具
- [ ] F-SCH-01 主链 v3 Schema 集
- [ ] F-SCH-02 v1/v2 兼容 Schema
- [ ] F-SCH-03 共享基础 Schema
- [ ] F-SCH-04 反馈契约 Schema
- [ ] F-SCH-05 治理 Schema
- [ ] F-SCH-06 Examples 与版本清单
- [ ] F-VAL-01 Plugin/Project 治理校验脚本族
- [ ] F-VAL-02 Schema 校验脚本族
- [ ] F-VAL-03 Evidence / Functional Map 生成
- [ ] F-TST-01 L1 测试族(Query/Write/UITool)
- [ ] F-TST-02 L2 闭环测试族
- [ ] F-TST-03 L3 FunctionalTest + Gauntlet 控制器
- [ ] F-TST-04 系统测试套件(266 case)
- [ ] F-HOOK-01 document-release gate
- [ ] F-HOOK-02 Git hooks 安装与 CC 通知
- [ ] F-INP-01 GDD 实例输入族
- [ ] F-INP-02 Compiler Profile / Mode Override 预设
- [ ] F-DEMO-02 可运行游戏 demo 族
- [ ] F-DEMO-03 资产生成 / Skills 同步辅助族

合计 **105 行**(对应 FEATURE_INVENTORY 主表 105 行,验收门禁底座)。

勾选规则:每行需在 UE 5.7 重构完成后,由 msc 实测对照 SRS / LLD 锚点 + 证据源代码路径
后单独裁决。UE 5.7 状态列取值受限于 `unchanged` / `migration` / `deprecated` / `new` 四态
(或 `unchanged-pending-test`),不允许保留 `TBD`;若实测发现旧功能在 5.7 下变为新形态,
需要在 inventory 表新增一行 new 状态行,旧行标 `deprecated`,以保证血缘可追溯。

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

### 4.6 mcp_tools_catalog 53 工具全量勾选

每工具按 6 字段(工具名/类别/输入 Schema/输出 Schema/错误码/使用场景)完整核对,在 UE 5.7 重构完成后由 msc 实测对照 mcp_tools_catalog.md 主表逐项勾选:

- [ ] mcp_tool: `get_current_project_state` — Bridge L1 查询
- [ ] mcp_tool: `list_level_actors` — Bridge L1 查询
- [ ] mcp_tool: `get_actor_state` — Bridge L1 查询
- [ ] mcp_tool: `get_actor_bounds` — Bridge L1 查询
- [ ] mcp_tool: `get_asset_metadata` — Bridge L1 查询
- [ ] mcp_tool: `get_dirty_assets` — Bridge L1 查询
- [ ] mcp_tool: `run_map_check` — Bridge L1 查询
- [ ] mcp_tool: `spawn_actor` — Bridge L1 写
- [ ] mcp_tool: `set_actor_transform` — Bridge L1 写
- [ ] mcp_tool: `import_assets` — Bridge L1 写
- [ ] mcp_tool: `create_blueprint_child` — Bridge L1 写
- [ ] mcp_tool: `set_actor_collision` — Bridge L1 写
- [ ] mcp_tool: `assign_material` — Bridge L1 写
- [ ] mcp_tool: `capture_screenshot` — Bridge L1 服务
- [ ] mcp_tool: `save_named_assets` — Bridge L1 服务
- [ ] mcp_tool: `build_project` — Bridge L1 服务
- [ ] mcp_tool: `run_automation_tests` — Bridge L1 服务
- [ ] mcp_tool: `undo_last_transaction` — Bridge L1 服务
- [ ] mcp_tool: `create_level` — Bridge L2 资产
- [ ] mcp_tool: `create_material` — Bridge L2 资产
- [ ] mcp_tool: `create_material_instance` — Bridge L2 资产
- [ ] mcp_tool: `create_widget_blueprint` — Bridge L2 资产
- [ ] mcp_tool: `set_blueprint_defaults` — Bridge L2 资产
- [ ] mcp_tool: `configure_gamemode_bp` — Bridge L2 资产
- [ ] mcp_tool: `configure_world_settings` — Bridge L2 资产
- [ ] mcp_tool: `open_level` — Bridge L2 资产
- [ ] mcp_tool: `save_all` — Bridge L2 资产
- [ ] mcp_tool: `run_editor_python` — Bridge L3 兜底
- [ ] mcp_tool: `compiler_create_session` — 前端 Compiler
- [ ] mcp_tool: `compiler_root_skill_prepare` — 前端 Compiler
- [ ] mcp_tool: `compiler_root_skill_save` — 前端 Compiler
- [ ] mcp_tool: `compiler_intake_prepare` — 前端 Compiler
- [ ] mcp_tool: `compiler_intake_save` — 前端 Compiler
- [ ] mcp_tool: `compiler_clarification_prepare` — 前端 Compiler
- [ ] mcp_tool: `compiler_clarification_save` — 前端 Compiler
- [ ] mcp_tool: `compiler_skill_graph_prepare` — 前端 Compiler
- [ ] mcp_tool: `compiler_skill_graph_save` — 前端 Compiler
- [ ] mcp_tool: `compiler_plan_prepare` — 前端 Compiler
- [ ] mcp_tool: `compiler_plan_save` — 前端 Compiler
- [ ] mcp_tool: `compiler_get_session_status` — 前端 Compiler
- [ ] mcp_tool: `compiler_stage4_node_prepare` — 前端 Compiler
- [ ] mcp_tool: `compiler_stage4_node_save` — 前端 Compiler
- [ ] mcp_tool: `evidence_load_manifest` — 后端 Evidence
- [ ] mcp_tool: `evidence_load_screenshots` — 后端 Evidence
- [ ] mcp_tool: `evidence_load_logs` — 后端 Evidence
- [ ] mcp_tool: `evidence_load_report` — 后端 Evidence
- [ ] mcp_tool: `evidence_judge_acceptance` — 后端 Evidence
- [ ] mcp_tool: `evidence_decide_escalation` — 后端 Evidence
- [ ] mcp_tool: `evidence_export_summary` — 后端 Evidence
- [ ] mcp_tool: `evidence_list_runs` — 后端 Evidence
- [ ] mcp_tool: `evidence_compare_runs` — 后端 Evidence
- [ ] mcp_tool: `evidence_create_batch` — 后端 Evidence
- [ ] mcp_tool: `evidence_promote_run` — 后端 Evidence

合计 **53 工具**(实测 `python -c "from MCP.tool_definitions import TOOL_COUNT; print(TOOL_COUNT)"` 应输出 53)。

### 4.7 schemas_catalog 41 主 Schema 全量勾选

每 Schema 按 5 字段(文件/用途/版本/引用方/关键字段清单)完整核对(examples 26 份附录见 catalog §附录 A):

- [ ] Schema: `batch_manifest.schema.json` — Phase 11 batch promote 治理元数据
- [ ] Schema: `build_ir.schema.json` — Lowering 输出构建中间表示
- [ ] Schema: `build_ir_v2.schema.json` — Stage 6 Build IR v2
- [ ] Schema: `clarification_gate_report.schema.json` — Clarification Gate 决策记录
- [ ] Schema: `common/bounds.schema.json` — UE5 包围盒
- [ ] Schema: `common/collision.schema.json` — UE5 碰撞结构
- [ ] Schema: `common/error.schema.json` — 统一 warnings/errors 数组
- [ ] Schema: `common/material.schema.json` — UE5 材质槽位
- [ ] Schema: `common/primitives.schema.json` — 基础类型(所有 Schema 底层依赖)
- [ ] Schema: `common/transform.schema.json` — UE5 Actor Transform
- [ ] Schema: `compiler_session.schema.json` — Pipeline Orchestrator 会话状态
- [ ] Schema: `converged_realization_pack.schema.json` — Convergence 最终选择产物
- [ ] Schema: `cross_review_report.schema.json` — Cross-Spec Review 统一审查报告(v1)
- [ ] Schema: `cross_review_report_v2.schema.json` — Stage 5 跨域冲突审查(v2)
- [ ] Schema: `design_decision_log.schema.json` — Stage 4 非平凡设计选择日志
- [ ] Schema: `design_space_report.schema.json` — Design Space Discovery 产物
- [ ] Schema: `evidence_manifest.schema.json` — Phase 10 证据裁决标准化清单
- [ ] Schema: `feedback/actor/get_actor_bounds.response.schema.json` — Actor 包围盒查询反馈
- [ ] Schema: `feedback/actor/get_actor_state.response.schema.json` — Actor 核心状态查询反馈
- [ ] Schema: `feedback/actor/get_component_state.response.schema.json` — Actor 组件相对变换查询反馈
- [ ] Schema: `feedback/actor/get_material_assignment.response.schema.json` — Actor 材质槽位查询反馈
- [ ] Schema: `feedback/asset/get_asset_metadata.response.schema.json` — 单资产元数据查询反馈
- [ ] Schema: `feedback/asset/get_dirty_assets.response.schema.json` — 脏资产列表查询反馈
- [ ] Schema: `feedback/level/list_level_actors.response.schema.json` — 关卡 Actor 列表查询反馈
- [ ] Schema: `feedback/project/get_current_project_state.response.schema.json` — 项目状态查询反馈
- [ ] Schema: `feedback/validation/run_map_check.response.schema.json` — Map Check 反馈
- [ ] Schema: `gdd_projection.schema.json` — Design Intake GDD 结构化投影
- [ ] Schema: `naming_resolution_log.schema.json` — Build IR v2 命名审计 sidecar
- [ ] Schema: `planner_output.schema.json` — Planner / Routing Agent 输出
- [ ] Schema: `realization_candidates.schema.json` — Realization Candidate Generation 产物
- [ ] Schema: `reviewed_handoff.schema.json` — Compiler→Orchestrator 交接物 v1
- [ ] Schema: `reviewed_handoff_v2.schema.json` — Skill-First 交接物 v2
- [ ] Schema: `reviewed_handoff_v3.schema.json` — Stage 7 最终 handoff v3
- [ ] Schema: `root_skill_contract.schema.json` — Phase 11 能力骨架/约束容器
- [ ] Schema: `run_comparison.schema.json` — 跨 run 治理比较产物
- [ ] Schema: `run_plan.schema.json` — Orchestrator 执行计划
- [ ] Schema: `skill_fragment.schema.json` — Skill Instance 运行时输出 v1
- [ ] Schema: `skill_fragment_v2.schema.json` — Phase 11 Domain Skill 输出 v2
- [ ] Schema: `skill_graph.schema.json` — Phase 11 Domain Skill 依赖图
- [ ] Schema: `versions/v0.1_manifest.json` — v0.1 Schema 清单 manifest
- [ ] Schema: `write_feedback/write_operation_feedback.response.schema.json` — 通用写操作反馈

合计 **41 主 Schema**(实测 `find Plugins/AgentBridge/Schemas -name "*.json" -not -path "*/examples/*" | wc -l` 应输出 41;examples 26 份附录见 schemas_catalog.md §附录 A)。

### 4.8 总勾选规模

本 §4 全量勾选清单合计:

- §4.1 F-* IDs:**105 行**
- §4.2 contracts 4 份契约
- §4.3 LLD 7 份
- §4.4 redirects.json 108 条
- §4.5 BC 25 条
- §4.6 MCP 工具:**53 行**
- §4.7 主 Schema:**41 行**

**合计 343 个勾选位**(三类对账主体 105+53+41=199 + 4 类辅助 4+7+108+25=144 = 343)。

本清单完整覆盖 spec v1.1 §8 验收门禁"符号/工具/字段/用例级双向 traceability"要求。

## 附:Phase 11 残留与重构注意事项

- `LLM Internal` 已于 Phase 12 重开(2026-05-27)。Phase 12 落地了 `Compiler/providers/` `Compiler/observability/` `Compiler/runtime/` 三子目录 + `Compiler/stages/candidates_batch_orchestrator.py`,通过 7/7 真 LLM 验收(见 [llm_internal_reopen_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-05-27/llm_internal_reopen_acceptance.md))。Spec / Plan / Acceptance:[Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md) / [Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md)。**LLM Internal 是 UE 5.7 重构前置门禁,promotable 候选。**Phase 11 正式主路径仍是 `MCP Agent`,`heuristic_fallback` 仍是显式后备(固化 promotable=False)。
- `raw DebugGame + .uproject` 非标准路径不作为官方验收链;若要恢复,作为独立构建链问题治理。
- Phase 11 v2 完整 run 产物落盘于 [run-20260417-051425-aad0](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/runs/run-20260417-051425-aad0),
  作为 UE 5.7 下 E2E 验证对照基线。后续 UE 5.7 下做对比验证时,新 run 的 `promotable`
  字段、Stage 4 generator 一致性、naming_resolution_log 命中率都须与该基线 run 对照。
- 任何 UE 5.7 下的 regression 必须先在 ProjectState/Reports/ 留证,再决定是否调整本验收报告基线。
- Phase 11 实施前文档中 MCP 工具数 `50` 是 planning 口径,本报告统一以收尾事实 `53` 为准
 (49 主工具 + 4 兼容 alias),Phase 11 收尾已同步纠偏到 Current 文档与 Schema 参考文档。
- UE 5.7 重构未达成前,本报告 §3 模板项保留 `[ ]` 未勾选状态;勾选动作只在 UE 5.7
  实测产出对应证据后由 msc 手动完成,Claude/Codex 不得自动批量勾选以避免假阳性。

## 附 2:ForgeUE Manifest Import Bridge 真机 milestone follow-up(2026-05-27 新增)

由 `Docs/superpowers/specs/2026-05-27-forgeue-real-ue-bridge-design.md` v1.0 + L3 真机 smoke 实测(`ProjectState/Reports/2026-05-27/task12_l3_smoke_summary.md`)产出,作为本次 ForgeUE 真机 milestone 完成后的 backlog 增量:

- **FU-FORGEUE-01(P3)**:material entry `duration_ms` ~4h10min 数据 anomaly + timestamp 与其他 asset 差 4 小时。L3 真机实际 < 1 分钟,猜测 `recompile_material()` GIL release 期间 `time.monotonic()` clock skew 或 UE 异步编译队列影响。仅影响 evidence timing 字段,不影响功能。**Follow-up**:UE 5.7 升级时观察 `MaterialEditingLibrary.recompile_material` 是否改异步模式;若仍有可考虑改用 `time.perf_counter()` 或加 `unreal.SystemLibrary` 时间锁。
- **FU-FORGEUE-02(P3)**:L2 pytest `-m real_ue` 后续 call 触发 30s timeout(L3 跑过后 Editor compile 队列阻塞)。`remote_control_client.py` 在 CLAUDE.md 禁止修改清单内,无法调 timeout。**Follow-up**:L2 测试不可强依赖 RC 30s timeout,真机回归用 L3 smoke 作为 milestone gate;或考虑 L2 case 在调用前先 sleep N 秒等编译队列空。
- **FU-FORGEUE-03(P2)**:~~`_creator_path_material` 的 `normal_texture_ref` 字段当前留 follow-up~~ **[CLOSED 2026-05-27,commit `50f0b5c`]** fixture 加 tex_normal.png(64×64 RGBA(128,128,255,255) normal map "向上"色)+ manifest 加 ae_run_p4_full_texture_normal entry(放在 material 之前确保 import 顺序)+ material_simple.json normal_texture_ref 改 UE asset path + `_creator_path_material` 加 Normal 分支(`load_asset` + `MaterialExpressionTextureSample` + `sampler_type=SAMPLERTYPE_NORMAL` + connect `MP_NORMAL`,容错 None warning)。**真机 L3 smoke PASS**:M_run_p4_full_material_simple 含 Normal expression(duration 1625ms 含 normal texture lookup)。
- **FU-FORGEUE-04(P3)**:~~`_build_mesh_factory` GLTF / GLB / OBJ 路径返 (None, None, "...not implemented")~~ **[PARTIAL 2026-05-27,commit `15cc2a1`]** OBJ 已实施(fixture 加 mesh_cube_obj.obj 标准 Wavefront 格式 + manifest 加 ae_run_p4_full_mesh_cube_obj entry + `_build_mesh_factory` OBJ 分支用 `getattr(unreal, "ObjFactory", None)`)。**真机 L3 smoke FAILED — UE 5.5 Python binding 没暴露 `unreal.ObjFactory`**(getattr 返 None → _evidence_failure "unsupported mesh source_format: obj")。代码层闭环 + UE binding 限制无法真机。**Follow-up**:(1) 等 UE 5.7 升级时再实测 ObjFactory binding;(2) 考虑在 AgentBridgeSubsystem C++ 加 BlueprintCallable 暴露 ObjFactory(但要破 CLAUDE.md C++ 红线);(3) GLTF/GLB 仍完全 follow-up(JSON + base64 binary buffer 复杂,未实施)。
- **FU-FORGEUE-05(P2)**:UE 5.7 升级时实测 BC-NEW-A(PythonScripted UCLASS RC 可见性)+ BC-NEW-B(MaterialEditingLibrary 与 BC-008 联动)— 见 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §4 "NEW" 区段。
- **FU-FORGEUE-06(P3 项目治理)**:~~本次 milestone 真机 import 在 `Content/Generated/Tavern/run_p4_full/` 产生 6 个 .uasset 文件,未进 git~~ **[CLOSED 2026-05-27,commit `1423966`]** `.gitignore` 加 `Content/Generated/`(L3 smoke 真机 import 产物自动忽略,多次跑不污染 git status)。

### code quality reviewer minor nits 补充(2026-05-27 新增,实施期 reviewer 标"接受保留")

下列 4 条来自 Plan T3/T6/T9/T12 code quality review 标记的 minor nits,reviewer 判定"不阻塞合并、可保留",但作为 backlog 显式记录避免未来遗忘:

- **FU-FORGEUE-07(P3 风格)**:~~`test_forgeue_manifest_importer.py` 新增 `# ===` section header 风格孤立~~ **[CLOSED 2026-05-27,commit `1423966`]** 三行 banner 改为单行普通行注释,空行分组自然保留。
- **FU-FORGEUE-08(P3 演进)**:~~`run_forgeue_real_smoke.py` magic string 与 schema 强绑定散落~~ **[CLOSED 2026-05-27,commit `1423966`]** 5 个模块级常量(_EVIDENCE_TEST_TYPE / _EVIDENCE_STATUS_PASS / _EVIDENCE_STATUS_FAIL / _PAYLOAD_STATUS_SUCCESS / _PAYLOAD_STATUS_PARTIAL),4 处引用替换,与 evidence_manifest.schema.json 字段值同步演进更易。
- **FU-FORGEUE-09(P3 DRY)**:~~`_creator_path_material` 4 expression 创建模式重复~~ **[CLOSED 2026-05-27,commit `bafd5b2`]** 抽 `_add_material_constant_expression(material, expression_class, value, output_property, *, set_property_name)` helper,4 个 expression(BaseColor Constant4Vector / Metallic Constant / Roughness Constant / Emissive Constant4Vector)各 1 行 helper 调用;原 try/except 整段 wrap + lib.recompile_material 不变。**真机验证 PASS**(material asset 创建 + 4 expression 连接正确)。
- **FU-FORGEUE-10(P3 DRY)**:~~`_now_iso_utc()` 两处副本~~ **[CLOSED 2026-05-27,commit `6de6a21`]** 抽 `Plugins/AgentBridge/Scripts/orchestrator/_time_utils.py`(避开 `bridge/` 红线),public API `now_iso_utc()`,importer + run_forgeue_real_smoke.py 删本地副本 + `from _time_utils import now_iso_utc`。

## 附 3:Phase 13 Skill 合成主链(2026-06-11 新增)

### 附 3.1 交付摘要

Phase 13 实施完成(分支 `feat/phase13-skill-synthesis-spec`,实现 commit 范围 7acd860..5911a6b 共 15 个实现 commit),交付:

- **Stage 3 注册表数据化**:`GAMEPLAY_NODE_CONFIGS` / `BASELINE_NODE_CONFIGS` / `FRAGMENT_FAMILY_MAP` 三张硬编码表全删;12 存量模板 manifest 补 `capability_bindings` 块(内容逐字照抄下沉),占位节点落 `SkillTemplates/registry_placeholders.yaml`,`registry_scan` 三遍扫描建映射,fragment family 惰性派生。
- **capability gap 显式化**:库外 required capability 写入 `skill_graph.metadata.capability_gaps[]`,零静默丢弃;基线 Monopoly GDD 改造前后 skill_graph 等价(golden 守门)。
- **S3.5 合成链**:`synthesis_validator`(capability_id 格式硬校验 / 递归 `additionalProperties: false` 含组合器 / 深度护栏)+ `skill_synthesis`(prepare 载荷 / save `.part` 事务落盘 / approved 防覆盖 / 审阅清单)+ MCP 工具对 `compiler_skill_synthesis_prepare/save`(工具数 53→55)。
- **GDD 覆盖矩阵**:`gdd_coverage` 模块(claimed / unclaimed / container 三态,防固化四守则),`gdd_coverage_matrix` schema + example 入 strict(27→28)。
- **anchor 留痕 + promote 双守卫**:`allow_skill_synthesis` 开启时 Stage 1 强制 `source_anchor`(intake alias 封绕行);synthesized 消费 / 未解决 gap → `PROMOTE_REJECTED`,损坏 graph fail-closed(F-GOV-05)。
- **测试**:Stage 13 SKS-01~89 登记(系统测试 270→359),9 个 `test_phase13_*.py` 纯 Python。

权威文档:spec [2026-06-10-phase13-skill-synthesis-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md)(顶部含实施期修订记录)/ plan [2026-06-10-phase13-skill-synthesis.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-06-10-phase13-skill-synthesis.md)/ 任务书根 `task.md`。

### 附 3.2 验收状态(runbook 判据)

验收 runbook:[phase13_acceptance_runbook.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md)。

- **判据 1-4 已闭环**(纯 Python 证据):① 等价回归不破现状(golden 等价 + strict 全过);② 缺件被点名 + 覆盖完整(验收 GDD `ProjectInputs/GDD/monopoly_extended_auction_v1.md` 植入拍卖 + 股票市场已知 gap,100% 被识别记 gap);③ 造件闭环(非法包 → save 返回具体校验错误 → 修正重提通过,确定性测试用例验证);④ 人审 gate 生效(未审批包编译器不消费,SKS 系列断言)。
- **判据 5-12 待执行**(需人工 / 真机 Editor / Codex 端授权):真机 demo 四道关、双端等价(Codex 侧需 `~/.codex/config.toml` 注册 MCP server,项目外改动须用户单独授权)、JRPG stretch(非阻塞)等,执行后证据落 `ProjectState/Reports/` + `ProjectState/Evidence/` 并回填 runbook。

### 附 3.3 Phase 13 backlog(实施期审查累积)

- **P13-BL-01(机制)**:合成 skill 转正机制(synthesized → 正式库,解除 promotable 限制;待跨 run 稳定性数据,spec §1.3 既定 backlog)。
- **P13-BL-02(质量)**:合成链错误文案统一模板(当前各校验点文案风格不一)。
- **P13-BL-03(重构)**:`validate_synthesized_package` 函数拆分(单函数承载多类校验,可读性债)。
- **P13-BL-04(健壮)**:覆盖矩阵 sidecar 原子写(当前直接写盘,极端中断可能留半成品文件)。
- **P13-BL-05(对账)**:phase13 测试文件名单与 `test_phase13_*.py` glob 对账自动化(防新增文件漏登记)。
- **P13-BL-06(性能)**:Stage 4 单 run 内 fragment family map 快照优化(当前惰性重建,长 run 可缓存)。
- **P13-BL-07(验收)**:JRPG stretch(spec 判据 7)未执行,留待判据 5-12 批次。
