# testing/test_spec — 测试体系总览 + 系统测试用例汇总索引

> 版本: v1 (2026-05-26)
> 范围: 项目级测试体系总览(C++ Automation / Python pytest / Gauntlet / SystemTest 索引层四栈)+ 系统测试 15 测试类 / 266 case 汇总索引(不复述用例详情)。
> 上游: `Docs/design/HLD.md` §6 + `Docs/requirements/SRS.md` §3.7 / §6.1 + `Docs/FEATURE_INVENTORY.md` F-TST-01..04
> 权威源: `Plugins/AgentBridge/Tests/run_system_tests.py`(11 stage / STAGES dict line 95-189 / TOTAL_CASES=266)+ `Plugins/AgentBridge/Tests/SystemTestCases.md`(266 case 详情,本文不复述)
> 契约: `Docs/contracts/schemas_catalog.md`(Schema 26/26 严格校验映射)+ `Docs/contracts/tool_contract.md`(L1/L2/L3 工具接口)
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 测试体系架构

本项目测试栈分四层,各层独立计数、独立编排,不互替代:

- **C++ Automation 层(Editor 内)** — 位于 `Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/` 共 8 个 cpp:`L1_QueryTests.cpp` / `L1_WriteTests.cpp` / `L1_UIToolTests.cpp`(L1 接口测试 3 份)+ `L2_ClosedLoopSpecs.spec.cpp` / `L2_UIToolClosedLoopSpec.spec.cpp`(L2 闭环 Spec 2 份)+ `L3_FunctionalTestActor.cpp`(L3 关卡级 FunctionalTest)+ `AgentBridgeGauntletController.cpp`(Gauntlet 引擎内"触角")+ `AgentBridgeTestsModule.cpp`(测试模块入口)。基于 `IMPLEMENT_SIMPLE_AUTOMATION_TEST` + `DEFINE_LATENT_AUTOMATION_COMMAND` + Automation Spec 三套宏组合,独立计 ~26 条 C++ Automation test,**不计入 266 系统测试**。
- **Python pytest 层** — 位于 `Plugins/AgentBridge/Tests/scripts/` 下 `task1X_phase11_*.py` 系列 + `conftest.py`,主要承载 Phase 11 设计编译器框架的脚本侧验证(P11-* 18 case 与 Standalone Smoke 入口)。
- **Gauntlet CI/CD 层** — `AgentBridgeGauntletController` 在引擎内继承 `UGauntletTestController`,负责 OnTick 轮询 + EndTest 退出码;Gauntlet C# 端在引擎外驱动 Editor 进程启动 / 监控 / 停止。Gauntlet 负责"在什么环境下运行",Orchestrator 负责"运行什么内容",二者职责正交。
- **SystemTest 索引层(本 LLD 主体)** — `Plugins/AgentBridge/Tests/run_system_tests.py` 编排 11 stage / 15 测试类 / 266 case,STAGES dict 在 line 95-189,`TOTAL_CASES = sum(s['count'] for s in STAGES.values())` 在 line 191 实时计算并 assert 266。

四栈关系:SystemTest 索引层在 Stage 2/3/8/9 主动调起 C++ Automation(通过 Commandlet `-RunTests=` 或 Gauntlet RunUnreal),在 Stage 11 调起 Python pytest,在 Stage 8 调起 Gauntlet;C++ Automation 和 Python pytest 也可单独跑(不经索引层),用于开发期单点调试。系统测试 266 是"对外承诺的最小回归集",C++ Automation ~26 条是"引擎内 L1/L2/L3 接口级单元测试",二者计数维度不同、不可加总。

记账规则:`run_system_tests.py:191-195` 在导入期 `assert TOTAL_CASES == 266`,并由 `CASE_ID_PATTERN` 正则扫 `SystemTestCases.md` 主表行,二者一致性是导入期硬约束;任何新增 case 必须同步改 STAGES dict 的 `count` 与 `case_ids`,以及 `SystemTestCases.md` 主表行,否则 `run_system_tests.py` 在启动时直接 RuntimeError,这是 266 维持单一来源的关键护栏。

## 2. 测试分层

按测试目标划分四类,与第 1 节四栈正交:

| 分层 | 目标 | 对应测试类 | 主要执行栈 |
|---|---|---|---|
| 单元 | Schema / 字段对齐 / 加载链路 | SV / BL | Python(SV)+ C++(BL Compile/Load) |
| 集成 | L1/L2/L3 工具闭环、客户端、Commandlet | Q / W / CL / UI / CMD / PY | C++ Automation + Python |
| E2E | 跨子系统全链路 | ORC / E2E / MCP | Python + Editor + RC HTTP |
| 回归 | Phase 11 设计编译器框架专项 | CP / SS / GA / P11 | Python pytest + Gauntlet |

四类分层不是物理隔离,而是按"测试对象的复杂度边界"切分:**单元层** SV / BL 只验证静态结构(JSON Schema 字段、Compile 后 cpp Symbol 是否可加载),不依赖外部进程;**集成层** Q / W / CL / UI / CMD / PY 把 L1 工具的"调用 → 写副作用 → 读回执"三段闭环或 Python 客户端连 Editor 的链路独立测出,每个 case 限定在单一子系统内;**E2E 层** ORC / E2E / MCP 跨 Orchestrator + Bridge + Editor + Schema 验证四件套,覆盖 Plan → Run → Verify → Report 全链路;**回归层** CP / SS / GA / P11 专门跟踪 Phase 11 引入的设计编译器框架,GA 类负责 Gauntlet 环境,CP / SS 负责编译产物与 Skill / Spec 一致性,P11 负责 Phase 11 章节专项验收。

## 3. 系统测试用例总表

按 15 测试类汇总,每类 1 行 5 字段;**用例描述详情见 `Plugins/AgentBridge/Tests/SystemTestCases.md`,本表不复述**。

| 测试类 | ID 范围 | 入口脚本 | 期望大类 | 当前状态汇总 |
|---|---|---|---|---|
| SV(Schema 验证) | SV-01..10(10) | `run_system_tests.py --stage=1` 或 `validate_examples.py --strict` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| BL(编译与加载) | BL-01..06(6) | `run_system_tests.py --stage=2`(需 Editor + Build) | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| Q(L1 查询) | Q-01..12(12) | `--stage=3` + C++ `L1_QueryTests` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| W(L1 写) | W-01..20(20) | `--stage=3` + C++ `L1_WriteTests` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| CL(L2 闭环) | CL-01..12(12) | `--stage=3` + C++ `L2_ClosedLoopSpecs` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| UI(L3 UI 工具) | UI-01..13(13) | `--stage=3` + C++ `L1_UIToolTests` + `L2_UIToolClosedLoopSpec` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| CMD(Commandlet 无头) | CMD-01..08(8) | `run_system_tests.py --stage=4` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| PY(Python 客户端) | PY-01..10(10) | `run_system_tests.py --stage=5` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| ORC(Orchestrator) | ORC-01..37(37) | `run_system_tests.py --stage=6` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| CP(Compiler Plane) | CP-01..44(44) | `run_system_tests.py --stage=7` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| SS(Skills & Specs) | SS-01..20(20) | `run_system_tests.py --stage=7` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| GA(Gauntlet CI/CD) | GA-01..06(6) | `--stage=8` + `AgentBridgeGauntletController` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| E2E(端到端集成) | E2E-01..40(40) | `run_system_tests.py --stage=9` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| MCP(MCP Server 集成) | MCP-01..10(10) | `run_system_tests.py --stage=10` | Pass | 见 `ProjectState/Reports/` 最近一轮 |
| P11(Phase 11 设计编译器框架) | P11-01..18(18) | `--stage=11` 或 `Tests/scripts/task1X_phase11_*.py` | Pass | 见 `ProjectState/Reports/` 最近一轮 |

合计:**15 测试类 / 266 case**,与 `run_system_tests.py:191` `TOTAL_CASES` 实时计算结果一致(10+6+57+8+10+37+64+6+40+10+18 = 266 ✓;Stage 3 合并 Q+W+CL+UI 共 57,Stage 7 合并 CP+SS 共 64)。

附:266 case 的逐条字段(目标 / 前置 / 步骤 / 期望 / 验证点 / 状态)留在权威源 `Plugins/AgentBridge/Tests/SystemTestCases.md`,本文档**不在此处复述**,以避免双源漂移。

## 4. 关键测试入口

按调用形态枚举常用入口:

- **全量回归:** `python Plugins/AgentBridge/Tests/run_system_tests.py`(11 stage 顺序跑,Stage 2/3/4/8/9 需要 Editor + Build,Stage 1/5/6/7/10/11 纯 Python)。
- **交互模式:** `python Plugins/AgentBridge/Tests/run_system_tests.py --interactive`(逐 stage 选择,适合分段调试)。
- **无编辑器模式:** `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`(Phase 10 后默认 `task08_orchestrate.py` 分段等价验证,跳过所有 `requires_editor=True` 的 stage)。
- **Standalone Smoke:** `python Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py`(Phase 11 引入,UAT BuildCookRun + Standalone 启动一次性烟测)。
- **Schema 严格校验:** `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`(SV-01..10 + Schema/Example 26/26 对齐)。
- **Handoff Schema 校验:** `python Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py`(`reviewed_handoff` / `reviewed_handoff_v2` 双 schema)。
- **Compiler 单独跑:** `python Plugins/AgentBridge/Scripts/compiler_main.py`(走 Compiler Plane 单元链路,不依赖 Editor)。

入口选择策略:本地开发期优先用 `--interactive` 逐 stage 跑,失败立即定位;CI 与回归用全量;远程无 Editor 节点用 `--no-editor`;Phase 11 单点验收用 `task14a_phase11_standalone_smoke.py` 跑一次冷启动 Standalone。Schema 改动后必须先单独跑 `validate_examples.py --strict`,通过后再跑 `--stage=1`,避免 Stage 2/3 在 Schema 不一致时大量伪 fail。所有入口最终都把日志与产物落到 `ProjectState/Reports/<date>/` 与 `ProjectState/Evidence/<run_id>/`,可通过 Run ID 在两套索引维度回溯。

## 5. Schema 严格校验(`--strict` 26/26 覆盖映射)

`validate_examples.py --strict` 严格模式下,**26 个 Example 与 26 个 Schema 一一对应**,且 `additionalProperties: false` 强制启用,任何 example 多余字段直接 fail。覆盖范围按域分组:

- **核心交接物域(8):** `reviewed_handoff` / `reviewed_handoff_v2` / `run_plan` / `gdd_projection` / `planner_output` / `skill_fragment` / `cross_review_report` / `build_ir`。
- **通用反馈域(common/feedback/write_feedback 子目录,~10):** L1/L2 工具调用统一回执 + 写操作差异回执 + 公共错误码字段。
- **Compiler / Skills 域(~5):** Compiler 各阶段 IR + Skill Template 元数据 schema。
- **MCP / Evidence 域(~3):** `evidence_manifest` / `run_comparison` / `batch_manifest`(运行时落盘三件套)。

严格模式三条强约束:(1) `additionalProperties: false` 全开 — example 一旦多出 schema 未定义的字段(如调试期临时塞入的 `_note` / `_debug` 字段)立即 fail;(2) `required` 字段必须出现 — example 不允许"省略默认值"以减少行数,所有 required key 必须显式;(3) `enum` / `pattern` 严格匹配 — 大小写敏感,枚举值不允许新增同义词。SV-01..10 case 在 Stage 1 中分别覆盖:Schema 自身合法性、26 example 顺次校验、跨域引用闭包(`$ref` 不悬空)、字段命名约定、必填字段覆盖、枚举值穷举、reviewed_handoff v1↔v2 字段映射、Compiler IR 链 schema 一致性、Evidence Manifest 与 Run ID 关联、MCP 工具目录字段对齐。

完整 26 项对照表(`Schemas/<...>.schema.json` ↔ `Schemas/examples/*.example.json` 一一行)留在权威源 `Docs/contracts/schemas_catalog.md` 附录 A,本表不复述。每次 Schema 改动后必须重跑 `--strict` 直至 26/26 通过,SV-01..10 case 在 `run_system_tests.py --stage=1` 中已包装此调用。

## 6. CI / Gauntlet 接入

- **`AgentBridgeGauntletController.cpp`**(`Plugins/AgentBridge/AgentBridgeTests/Source/AgentBridgeTests/Private/`)继承 `UGauntletTestController`,引擎内"触角"职责:`OnTick` 周期检测 Automation RunTests 完成状态,`EndTest` 设置退出码并触发 Gauntlet C# 端收尾。
- **职责分离:** Gauntlet 负责"在什么环境下运行"(进程拉起 / 退出码收集 / 日志切片);Orchestrator(`Plugins/AgentBridge/Scripts/orchestrator/`)负责"运行什么内容"(Plan 生成 / 验证 / 报告);二者通过 Run ID + ProjectState 落盘目录解耦,不互替代。
- **GA 类 6 case**(GA-01..06)覆盖 Gauntlet Controller 启动、Editor 状态轮询、Automation RunTests 调度、EndTest 退出码、日志切片落盘、跨阶段串联;详情见 `SystemTestCases.md §GA`。
- 当前 CI 入口:`run_system_tests.py --stage=8` 在本地复现 Gauntlet 流;远程 CI 直接调 Gauntlet C# 驱动 + 同一 Controller。
- 退出码语义:Gauntlet Controller 在 `EndTest` 中将 Automation 结果聚合为 `0=All Pass / 1=Has Failure / 2=Crash / 3=Timeout`,Gauntlet C# 端据此决定 CI 任务的最终成败,索引层 `--stage=8` 把该退出码透传到 `run_system_tests.py` 的 stage result 汇总中,落到最终 Reports JSON 的 `stages[7].exit_code` 字段。

## 7. UE 5.7 测试迁移变更点

本子系统受 UE 5.7 迁移直接影响主要在 **C++ Automation 宏接口 + UAT BuildCookRun 调用 + RC HTTP 通信 + 引擎根路径硬编码** 四处,BC 列表与 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 对齐:

- **BC-025(P1 confirmed,由 msc 在 Phase 0.2 §4 裁决,源:`run_system_tests.py:727-730` `find_engine_root()` 候选列表 + `task14a_phase11_standalone_smoke.py:25` `UAT_PATH` + `Scripts/validation/start_ue_editor_{cmd_project,project}.ps1` 中 `UE_5.5` 字符串共 7 处硬编码):** 必须批量替换为 5.7 路径或抽到 `$env:UE_INSTALL_ROOT`。迁移策略:(a) 优先环境变量化,避免 8.0/8.1 再次硬改;(b) 保留 5.5 / 5.7 双候选,运行时探测;(c) `task14a_phase11_standalone_smoke.py` 的 `UAT_PATH` 改为 `Path(os.environ.get("UE_INSTALL_ROOT", r"E:\Epic Games\UE_5.5")) / "Engine/Build/BatchFiles/RunUAT.bat"`。**修完 BC-025 才能让 `run_system_tests.py` 跑通 5.7**,是本子系统迁移的 P0 卡点。

- **BC-006(P2 suspected,pending-msc,源:`L1_QueryTests.cpp:14,50,76,108,149,184,215,235` / `L1_UIToolTests.cpp:75,106,167,222` / `L1_WriteTests.cpp:23,214,286,399,426` / `L2_ClosedLoopSpecs.spec.cpp:26,49` 等共数十处 `IMPLEMENT_SIMPLE_AUTOMATION_TEST` 宏 + `FAutomationTestBase` 派生):** UE 5.6 引入 `IMPLEMENT_SPEC` 风格但 Simple 宏仍保留,5.7 是否保留 `IMPLEMENT_SIMPLE_AUTOMATION_TEST` / `DEFINE_LATENT_AUTOMATION_COMMAND` / `IAutomationLatentCommand` 接口需 5.7 SDK 实测。**严禁标 P1 confirmed**;迁移阶段一次 `run_system_tests.py --stage=2,3,8,9` 全跑即可确诊,失败再批量改宏。

- **BC-020(P2 suspected,pending-msc,源:`UAT BuildCookRun -editortest -RunAutomationTest=<Filter>` 调用形态):** 影响 `run_system_tests.py` Stage 4(Commandlet -RunTests)/ Stage 8(Gauntlet RunUnreal)/ Stage 9(E2E 三通道)+ `task14a_phase11_standalone_smoke.py` BuildCookRun 命令拼装。5.7 UAT 参数面预期向后兼容,但是否保留 `-editortest` 短开关 / `-RunAutomationTest=` 拼接形态需实测。**严禁标 P1 confirmed**;迁移阶段一次 `run_system_tests.py --stage=4,8,9` 全跑即可确诊。

- **BC-019(P2 suspected,pending-msc,源:`Plugins/AgentBridge/MCP/server.py` + `Plugins/AgentBridge/Scripts/bridge/remote_control_client.py` 中 RC HTTP `/remote/object/*` 端点形态):** 间接影响测试 — ORC / E2E / CL 类在 `bridge_mode=bridge_rc_api` 时走 RC HTTP,5.7 是否改 JSON 序列化形态(尤其字段命名 / null 处理)需在 5.7 启动后跑一次 RC 端点 smoke 验证。**严禁标 P1 confirmed**。

- **整体结论:** 本测试子系统对 UE 5.7 迁移**必须先修 BC-025 才能让 `run_system_tests.py` 跑通 5.7**,其余 BC-006 / 019 / 020 都是 P2 suspected,在 P1 修完后通过一次 `run_system_tests.py --stage=1..11` 全套回归 + `validate_examples.py --strict` 26/26 即可确诊。如 BC-006 在 5.7 上 fail,需批量替换 C++ Automation 宏,影响 ~20 条 C++ test 但不影响 266 系统测试 ID 编排。
