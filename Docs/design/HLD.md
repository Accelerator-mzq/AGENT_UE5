# High-Level Design (HLD) — Mvpv4TestCodex / AgentBridge 框架

> 版本: v1.0 (2026-05-26)
> 关联 spec: `Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md` v1.1 §4.2
> 关联 FEATURE_INVENTORY: `Docs/FEATURE_INVENTORY.md`
> 关联契约: `Docs/contracts/{tool_contract,schemas_catalog,mcp_tools_catalog,field_specification}.md`
> 关联 LLD 占位: `Docs/design/LLD/0X_<module>.md` (Task 1.7-1.13 后续落地)
> 关联测试: `Docs/testing/test_spec.md` (Task 1.15 后续落地)
> 适用引擎: UE 5.5.4 (5.7 迁移影响详见 §9)

本文是 AgentBridge 框架的高阶设计文档,只回答"系统怎么分层、各层职责边界在哪、跨层数据如何流动",不下沉到方法签名与实现细节(签名留给 LLD 系列)。读者预期是已读过 `Docs/requirements/SRS.md` 与 `Docs/contracts/*` 后再来对照架构。

---

## 1. 架构总览

### 1.1 双层架构图

项目以"项目层 / 插件层"分层,前者承载实例与治理数据,后者承载通用机制。机制不下放到项目层,实例不上溯到插件层。

```
+---------------------------------------------------------+
|             项目层 (D:\UnrealProjects\Mvpv4TestCodex)    |
|                                                          |
|  ProjectInputs/    GDD / Presets / Baselines (设计输入)  |
|  ProjectState/     runs / batches / Handoffs / Reports   |
|                    Snapshots / Evidence  (Run 产物)       |
|  Docs/             治理文档 + 契约 + ADR                  |
+-----------------------+----------------------------------+
                        | 设计输入 ↓     实例产物 ↑
+-----------------------v----------------------------------+
|         插件层 (Plugins/AgentBridge/)                     |
|                                                          |
|  MCP/        前端 Stage 1-3 + 后端 Evidence/Governance    |
|  Compiler/   Stage 4-7 (Skill Runtime / Review / Lower)  |
|  Scripts/    Bridge 客户端 (三通道) + Orchestrator        |
|  Source/     C++ Editor Plugin (Subsystem + Commandlet)  |
|  Schemas/    主链 v1/v2/v3 契约 + common + feedback       |
|  Tests/      Automation Test + 系统测试套件               |
+----------------------------------------------------------+
```

### 1.2 进程拓扑

四个相关进程在不同生命周期与不同信号边界上协作:

- **UE Editor 进程**:加载 `AgentBridge.uplugin`,实例化 `UAgentBridgeSubsystem`(继承 `UEditorSubsystem`,随 Editor 启动自动构造),暴露 Remote Control 端口 30010(通道 B),可通过 `-run=AgentBridge` 进入 `UAgentBridgeCommandlet` 无头模式跑 Spec / Automation Test;由 UAT(`BuildCookRun -editortest`)外层编排时切换为通道 D。
- **Bridge Python 客户端**:`Scripts/bridge/` 下的客户端,可作 in-process `import unreal`(通道 A)或外部 HTTP 客户端(通道 B)调用 Editor;Phase 11 之后 Bridge 不再作为 Compiler 主链入口,只作为 Execution Orchestrator 与 MCP Bridge Passthrough 的工具调用层。
- **MCP Server (stdio)**:`MCP/server.py`,挂在 Agent IDE / CLI 一端,通过 stdio 协议暴露 53 工具(28 Bridge Passthrough + 14 前端 Compiler + 11 后端 Evidence,F-MCP-13)。MCP Server 不是流程总线,而是认知桥接层。
- **Agent 进程**:外部 LLM(Claude / Codex 等)通过 MCP stdio 与 Server 通信,本身即为 Stage 4 Generator 的主路径执行体(`generator_type=mcp_agent`);Agent 不直接持有 UE Editor 进程句柄,所有 UE 操作必经 MCP / Bridge 工具调用。

### 1.3 数据流总图

主数据流是单向的 GDD → Handoff → Evidence,执行层不向前回写 Compiler 产物;治理层(compare / promote)旁路读 run 产物,不破坏主链单向性。

```
GDD (ProjectInputs)
   │
   ▼  MCP 前端 (Stage 1-3)
Root Skill Contract → Clarification Gate → Skill Graph
   │
   ▼  Compiler Core (Stage 4-7)
Domain Skill Runtime (三路) → Cross Review v2 → Build IR v2 → Reviewed Handoff v3
   │
   ▼  Execution Orchestrator
Run Plan → Bridge 工具调用 (L1/L2/L3) → UE Editor
   │
   ▼  Automation Test + Gauntlet
Evidence Manifest (ProjectState/Evidence)
   │
   ▼  MCP 后端 (旁路)
evidence_judge / compare_runs / promote_run → Batch
```

---

## 2. 核心链路 v2 架构

Phase 11 主链由 7 个 Stage 组成,前 3 阶段由 MCP 前端承担(认知分解),后 4 阶段由 Compiler Core 调度(结构化收敛)。Stage 4 是核心创造性发散点,采用三路生成策略。Reviewed Handoff v3 是 Compiler → Execution 的唯一正式边界。

### 2.1 7 阶段主链 v2

| Stage | 名称 | 输入契约 | 输出契约 | FEATURE ID |
|---|---|---|---|---|
| Stage 1 | Root Skill Contract | GDD + Universal Baseline | `root_skill_contract.schema.json` | F-CHN-01 |
| Stage 2 | Clarification Gate | Stage 1 contract | `clarification_gate_report.schema.json` | F-CHN-02 |
| Stage 3 | Skill Graph Planning | Stage 1 + Stage 2 | `skill_graph.schema.json` | F-CHN-03 |
| Stage 4 | Domain Skill Runtime | Stage 3 节点 + Context Bundle | `design_space_report` + `realization_candidates` + `converged_realization_pack` + `skill_fragment_v2` | F-CHN-04 |
| Stage 5 | Cross Domain Review v2 | 全部 Fragment | `cross_review_report_v2.schema.json` | F-CHN-05 |
| Stage 6 | Lowering v2 → Build IR v2 | Reviewed Spec Tree | `build_ir_v2.schema.json` + `naming_resolution_log.schema.json` | F-CHN-06 |
| Stage 7 | Handoff Assembly | Build IR + 全链 metadata | `reviewed_handoff_v3.schema.json` | F-CHN-07 |

边界规则:Stage 1 通过 `compiler_root_skill_prepare/save`(F-MCP-06)、Stage 2 通过 `compiler_clarification_prepare/save`(F-MCP-07)、Stage 3 通过 `compiler_skill_graph_prepare/save`(F-MCP-08)暴露给 Agent,Agent 直接驱动认知分解;Stage 4-7 由 Compiler Core 内部调度,Agent 仅在 Stage 4 通过 `compiler_stage4_node_prepare/save`(F-MCP-09)参与每个 Skill Instance 的 Discovery / Candidates / Convergence 三个 phase,Stage 5-7(Cross Review / Lowering / Handoff)对外不开放交互接口。Stage 之间不允许跳序,前一阶段产物未落盘前后一阶段拒绝执行(由 `compiler_session.schema.json` 的 `current_stage` + `stage_outputs` 字段守护)。详细字段映射见 `Docs/contracts/schemas_catalog.md` 与 `Docs/contracts/mcp_tools_catalog.md`。

Stage 1 输入的 Universal Baseline 来自 `Plugins/AgentBridge/SkillTemplates/baseline/` 下 10 个 Baseline Domain 模板(start_screen / main_menu / hud / settings 等),Stage 3 输出的 Skill Graph 既包含 Gameplay Domain Skill 节点也包含 Baseline Domain Skill 节点,两类在结构上同构(同样的 manifest / system_prompt / domain_prompt / evaluator_prompt / input_selector / output_schema 六文件结构),仅在 Discovery 触发策略上不同:`presence_only` Baseline 跳过 Discovery 直接生成最小 Fragment,`realization_eligible` Baseline 与 Gameplay 走相同的 Stage 4 三 phase。

### 2.2 Stage 4 三路生成策略架构

Stage 4 Domain Skill Runtime 内部以"Discovery → Candidates → Convergence → Fragment"四个 phase 串行执行。每个 phase 都通过 Generator-Evaluator 门控,允许 ≤2 轮质量重试 + ≤2 次 schema 修复。Generator 的 prompt 来源是 SkillTemplate 的 `system_prompt.md` / `domain_prompt.md`,代码不允许硬编码设计知识。

三路 Provider 决定 Generator 的实际执行体:

- **MCP Agent (主路径)**:Agent 通过 `compiler_stage4_node_prepare` 拉取 prompt + Context Bundle,自行做创造性推理,通过 `compiler_stage4_node_save` 回写输出。`generator_type=mcp_agent`,`promotable=true`。
- **LLM Internal**:pipeline 内嵌 `llm_client`,在无人交互场景下自动驱动 Generator/Evaluator。`generator_type=llm`,`promotable=true`。
- **Heuristic Fallback**:`*_fallback.py` 确定性退化,仅在 CI / fast_mode / `allow_heuristic_fallback=true` 时启用。`generator_type=heuristic_fallback`,`promotable=false`(强制不可晋升,见 §3 F-GOV-03)。

Stage 4 产出 4 类 Schema 产物按 phase 依次落盘到 `ProjectState/runs/{run_id}/`,Generator/Evaluator 的 trace 落盘到 `stage4_agent_traces/` sidecar(不进 promoted_artifacts)。详细 Agent 交互协议见 LLD `Docs/design/LLD/04_compiler.md`(占位)。

### 2.3 v1 / v2 session 共存与路由

`compiler_session.schema.json` 的 `session_version` 字段区分两条主链:`1.0` 走 Phase 10 旧链(intake → routing → plan → skill_runtime),`2.0` 走 Phase 11 v2 主链。MCP 前端工具(F-MCP-06/07/08)默认 v2,并保留 4 个兼容 alias(`compiler_intake_prepare/save`、`compiler_plan_prepare/save`,F-MCP-12)将旧名映射到 v2 Stage 1/3 入口。Compiler Core 的 `pipeline_orchestrator` 按 `session_version` 路由到不同 Stage 实现,但同一 session 不能中途切换版本。

→ §2 各 Stage 输入/输出契约的字段级签名见 `Docs/contracts/schemas_catalog.md`;MCP 工具签名见 `Docs/contracts/mcp_tools_catalog.md`;字段共享规范见 `Docs/contracts/field_specification.md`。

---

## 3. Run 治理架构

Run 治理是 Phase 11 在 Compiler / Execution 主链之外旁路加上的"多轮跑可比较 + 可吸收"层,确保每轮管线产物独立存储且可追溯。

**三层目录结构**:
- **Base Project**(`Source/` `Content/` `Plugins/` `ProjectInputs/` `Config/`)只在 promote 时被更新。
- **Run Workspace**(`ProjectState/runs/{run_id}/`)每次管线执行的独立产物空间,`run_id = run-{yyyyMMdd}-{HHmmss}-{short_hash}`,F-GOV-01 负责生命周期管理。
- **Artifact Layer**(`ProjectState/batches/{batch_id}/`)经 promote 的 run 归档为 batch,含 `manifest.json` + `promoted_artifacts/` + `promotion_report.json`。

**治理规则**(F-GOV-02 / F-GOV-03):
- `fast_mode=true` 的 run 强制 `promotable=false`,因 Discovery/Candidates 被跳过,产物不完整。
- Stage 4 任一节点 `generator_type=heuristic_fallback` 时,整个 run 的 `promotable=false`(确定性产物不代表真实设计探索)。
- `constraint_violations > 0` 或 `pipeline_stages_completed` 不全的 run 不可 promote。
- promote 单向操作,不可撤销但可覆盖;同一时间只有一个 active batch。

**Compare/Promote MCP 工具**(F-GOV-04):后端 Evidence 工具族中 `evidence_compare_runs` / `evidence_create_batch` / `evidence_promote_run` 负责跨 run 对比与晋升,产出 `run_comparison.schema.json` 与 `batch_manifest.schema.json`。比较维度覆盖 Constraint 保持性、Realization 差异、Fragment 差异、Decision 差异、Build IR 差异、Naming 差异、Provisional 变化六类。Compare/Promote 是旁路读取 run 产物,不破坏主链单向流。

人类参与点共 3 个 human-in-the-loop:Root Skill Contract 形成后(确认约束理解正确)、Clarification Gate 中 `clarification_required` 项的回答(高风险未决项必须由人回答,fast_mode 不可自动默认)、converged_realization_pack 形成后(确认设计方向可接受)。这三个点是阶段质量的最后一道闸,详见 LLD `Docs/design/LLD/04_compiler.md`(占位)。

**Compare 比较产物**(`run_comparison.schema.json`)落盘到 `ProjectState/runs/comparisons/`,**Batch 元数据**(`batch_manifest.schema.json`)落盘到 `ProjectState/batches/{batch_id}/manifest.json`,促升时不删除原始 run(保留可追溯性),覆盖式 promote 也只更新 active batch 指针。Failed run(`status="failed"`)的执行 trace 保留用于诊断,产物可清理;fast_mode run 可配置自动清理(保留最近 N 个),正式 run 默认永久保留。

---

## 4. 工具体系架构(L1/L2/L3 + 4 通道)

工具体系按"风险等级"与"执行后端"双维度划分。Agent 选工具必须按 **L1 > L2 > L3** 优先级降级。

**三层语义**(详见 `Docs/contracts/tool_contract.md` §1):
- **L1 语义工具**(F-BRG-01 / F-BRG-02 / F-BRG-03 / F-MCP-01 / F-MCP-02 / F-MCP-03):UE5 C++ API 结构化封装,确定性最高;查询子族 7 个 + 写入子族 6 个 + 服务子族 5 个;写工具必须支持 `dry_run` + 写后读回,失败返回 `status=failed` 不抛栈。
- **L2 编辑器服务工具**(F-BRG-06 / F-MCP-04):验证 / 构建 / 测试 / 保存 / Undo 等工程级服务,通过 Commandlet / UAT 子进程或编辑器 Console Command 触发,产出报告路径 + 计数。
- **L3 UI 工具**(F-BRG-04 / F-MCP-05):仅当 L1 无对应 API 时使用,统一走 `start_ui_operation` / `query_ui_operation` 异步壳,执行后必须由 L1 交叉比对返回 `FBridgeUIVerification`(一致 → success,不一致 → mismatch + 字段级 diff)。

**契约层 4 通道枚举**(`Docs/contracts/tool_contract.md` §5.2):
- **通道 A — Python Editor Scripting**:进程内 `import unreal`,适合脚本快速原型。
- **通道 B — Remote Control HTTP**:Editor 进程外,PUT `:30010`,适合 Agent 远程调用与 MCP Bridge Passthrough。
- **通道 C — Commandlet / CLI / C++ Plugin 内部**:无 GUI 批处理,L3 UI 工具专用通道。
- **通道 D — UAT (BuildCookRun / BuildTarget)**:外部进程,长 timeout,L2 构建测试子族唯一通道。

**MCP Server 主入口**(F-MCP-13)通过 stdio 暴露 53 工具:Bridge L1 查询 7 / L1 写 6 / L1 服务 5 / L2 资产 9 / L3 兜底 1(共 28 = F-MCP-01..05 的 Bridge Passthrough)+ 前端 Compiler 14(F-MCP-06..09 + F-MCP-12 alias)+ 后端 Evidence 11(F-MCP-10 / F-MCP-11)。Bridge Passthrough 28 工具在新口径下定位为"可选外部协议适配层",非 MCP 核心价值;MCP 核心价值在前端 Stage 1-3 认知分解与后端证据裁决。

> **通道数实测注脚**:契约层 4 通道是逻辑划分(`tool_contract.md` §5.2),代码层 `BridgeChannel` 枚举实际只实例化 `CPP_PLUGIN` / `REMOTE_CONTROL` / `MOCK` 3 种(`Docs/contracts/field_specification.md` 已纠偏)。HLD 沿用 4 通道契约划分以保持"PYTHON in-process" 与 "MOCK" 的语义可分性,代码层 3 通道实例化属于实现合并而非语义合并。

→ §4 工具签名与错误码族详见 `Docs/contracts/tool_contract.md` §2-§6;53 工具的字段级输入/输出 schema 映射详见 `Docs/contracts/mcp_tools_catalog.md`;字段命名与单位规范详见 `Docs/contracts/field_specification.md`。详细 Bridge / MCP 实现切分见 LLD `Docs/design/LLD/02_bridge.md` 与 `Docs/design/LLD/05_mcp.md`(占位)。

---

## 5. Schema 与契约架构(v1 → v2 → v3 演进策略)

主链 Schema 经历了 3 个主版本演进,演进路径是"破坏性变更升大版本 + 旧版本保留 examples 兼容回归"。

**v1 集合**(Phase 8 之前 + 早期辅助):`reviewed_handoff.schema.json` / `build_ir.schema.json` / `cross_review_report.schema.json` / `skill_fragment.schema.json` / `run_plan.schema.json` / `gdd_projection.schema.json` / `planner_output.schema.json`。F-SCH-02 + F-SCH-06。

**v2 集合**(Phase 8 Skill-First Reset):`reviewed_handoff_v2.schema.json` / `build_ir_v2.schema.json` / `cross_review_report_v2.schema.json` / `skill_fragment_v2.schema.json`。引入 14 类 Build IR target 对象与 Skill Template Pack。F-SCH-02。

**v3 集合**(Phase 11 Skill-First Design Compiler,9 份):`root_skill_contract` / `clarification_gate_report` / `skill_graph` / `design_space_report` / `realization_candidates` / `converged_realization_pack` / `cross_review_report_v2` / `build_ir_v2` / `reviewed_handoff_v3`。F-SCH-01。

**共享层与治理层**:`common/` 6 份(bounds / collision / error / material / primitives / transform,F-SCH-03);`feedback/` 5 子目录(actor / asset / level / project / validation)+ `write_feedback/` 1 份(F-SCH-04);治理 6 份(`compiler_session` / `naming_resolution_log` / `design_decision_log` / `run_comparison` / `batch_manifest` / `evidence_manifest`,F-SCH-05);examples 26 份(F-SCH-06)。主 catalog 41 + examples 26 = 67(实测)。

**演进硬规则**:所有 schema 用 jsonschema draft-07 + `additionalProperties:false`;破坏性变更必须升大版本号(参 `reviewed_handoff_v2` 先例);v1 数据用 v1 schema 校验保留兼容;新字段必须先入 schema 再被工具引用,禁止"先用后补";共享字段(transform / bounds / collision / material)在 C++ Plugin `BridgeTypes.h` 以 USTRUCT 实现且 Schema 字段名 = UE C++ 属性名 snake_case 转换(不另立翻译层)。

→ Schema 字段级清单与引用方追踪见 `Docs/contracts/schemas_catalog.md`;共享字段规范见 `Docs/contracts/field_specification.md`。详细 Schema 演进影响面见 LLD `Docs/design/LLD/07_schemas.md`(占位)。

---

## 6. 测试架构

测试体系按"语义层 + 执行后端"两维划分,共 16 类 266 条用例(`Plugins/AgentBridge/Tests/SystemTestCases.md` §1)。

**三层 UE Automation 测试**(F-TST-01 / F-TST-02 / F-TST-03):
- L1 Simple Automation Test 11 个(Query 7 + Write 4)+ L3.UITool 4 个,`IMPLEMENT_SIMPLE_AUTOMATION_TEST` 宏注册,Session Frontend 可见。
- L2 Automation Spec 5 个(ClosedLoop 3 + UITool 2),BDD 风格 Describe / BeforeEach / It / AfterEach。
- L3 Functional Testing AFunctionalTest 子类放在 FTEST_ 测试地图。

**系统测试套件**(F-TST-04):`run_system_tests.py` 注册 10 个 Stage 共 240+ 条用例(当期总表 266 条),分 16 类 (SV/BL/Q/W/CL/UI/CMD/PY/ORC/CP/SS/GA/E2E/MCP/P11 等)。证据落盘到 `ProjectState/Reports/YYYY-MM-DD/` + `ProjectState/Evidence/`,历史归档复制到 `Docs/History/reports/AgentBridgeEvidence/`(`Docs/Current/07_Evidence_And_Artifacts.md`)。

**CI/CD 编排**:Gauntlet (C#) 在外层启动 / 监控 / 停止 Editor 进程,内部通过 GauntletTestController 调度 Automation RunTests。Gauntlet 负责"在什么环境下运行",Orchestrator 负责"运行什么内容",两者不互替代。

**容差比对**统一走 C++ `FBridgeTransform::NearlyEquals`,Python verifier 端只调不实现(`Docs/contracts/field_specification.md` §3 硬规则);v0.3 之后所有 transform / bounds / collision 字段的"是否相等"判定由 C++ USTRUCT 一处定义,避免 Python / C++ 双实现漂移。

**测试入口**(`SystemTestCases.md` §3.1 通用约束):无头基线统一用 `-run=AgentBridge -RunTests=<Filter>`,显式传 `-PLUGIN=<绝对路径>/AgentBridgeTests.uplugin`(嵌套 Plugin 路径无法稳定隐式定位)与 `-ProjectPath=<uproject>`;legacy `RunUAT RunAutomationTests` 入口已被 `validate_no_legacy_automation_entrypoints.ps1` 检测器禁用,统一改走 `BuildCookRun -editortest -RunAutomationTest=<Filter>`。

→ 测试用例编号、自动化命令、证据路径详见 `Docs/testing/test_spec.md`(Task 1.15 后续落地)。

---

## 7. 跨切面

**命名解析**:Stage 6 Lowering 产出 `naming_resolution_log.schema.json` 作为 Build IR v2 的命名审计 sidecar,记录每个 IR step 中类名 / 路径 / 资产名的解析来源(用户输入 / GDD / Constraint / Variant / 默认规则)。字段命名规则在 `Docs/contracts/field_specification.md` §2 锁定:snake_case + UE5 API 属性名直接映射 + 禁止翻译别名 + 禁止字段名清单(`size` / `position` / `center` / `big` / `small` / `proper` 等)。

**决策日志**:Stage 4 Fragment 内嵌 `design_decision_log` 字段(对应 `design_decision_log.schema.json`),记录已收敛方向内的非平凡选择(trade-off / 多合理实现 / provisional 值使用);impact 三档 high/medium/low。`design_decision_log` 与 `realization_candidates` / `converged_realization_pack` 形成"有哪些路径 / 选了哪条 / 沿途岔口"三层分离。

**错误处理**:`status` 枚举 5 值 `{success, warning, failed, mismatch, validation_error}` 在 `common/error.schema.json` 锁定;`errors[]` 元素必填 `code` + `message`,`details` 选填携带定位字段;错误码族 4 类(输入 / 寻址 / 权限 / 执行)详见 `Docs/contracts/tool_contract.md` §6.3。工具内部异常必须捕获降级为 `status=failed`,不允许向 Bridge 抛栈;`mismatch` 由编排层按 Spec 决定是否标记任务失败,不擅自重试。

**可观测性**:Run 产物以 `run_id` 隔离,每个 Stage 输出落盘到 `ProjectState/runs/{run_id}/<stage>.json`;Stage 4 Generator/Evaluator trace 落盘到 `stage4_agent_traces/{skill_instance}/{phase}_{role}_{attempt}.json` sidecar,包含 prompt hash / context hash / raw response / token usage;Evidence Manifest 由 `evidence_manifest.schema.json` 标准化测试证据(test_type / test_scope / evidence_items / summary / status)。Compare/Promote 比较产物保留运行间差异详情(constraint_consistent / realization_changes / fragment_changes / decision_changes / ir_action_delta / provisional_delta 六维),让"哪轮做了什么决策、为什么"可被回溯。

**Provisional 传播**:Clarification Gate 中 `clarification_required` 项若被以 `provisional_default` 继续,该值在整条管线中保持 `provisional: true` 标记,下游 Fragment 的 `design_decision_log` 标记 `provisional: true`,Build IR 的 `execution_hints` 标 `contains_provisional: true`,Handoff v3 汇总 `provisional_items[]`。Promote 时 `remaining_provisionals` 写入 `promotion_report.json`,允许"先跑完再回填"的工程节奏,但所有基于未确认信息的决策可被定位和回滚。

---

## 8. 关键 ADR

两条已 accepted 的关键 ADR 在 HLD 阶段仍保留架构裁决力,新阶段不应回退:

- **ADR-001 文档治理结构**(`Docs/Decisions/ADR-001-Doc-Governance.md`):采用五层文档治理(L0 入口 / L1 当前生效 / L2 插件 Canonical / L3 历史归档 / L4 决策 + L5 草案),task.md 定位为一次性消耗品,AI 默认只读 L0+L1+L2。本次 docs-restructure-for-ue57 重构在 ADR-001 框架内做实现(将散落规则合并为 `Docs/governance.md` + `Docs/contracts/*` + `Docs/design/*` + `Docs/requirements/*`)。
- **ADR-002 Task 与 Evidence 归档规则**(`Docs/Decisions/ADR-002-Task-And-Evidence-Archiving.md`):根目录 task.md 是当前阶段唯一任务入口,阶段结束后归档到 `Docs/History/Tasks/taskN_phaseX.md`;Snapshots / Evidence / Reports 分目录;系统测试用例阶段结算后再补录到 `SystemTestCases.md`。

两条 ADR 落到本 HLD 的具体后果:§1.1 项目层 / 插件层分层是 ADR-001 在架构上的体现;§3 Run 治理 + §6 Evidence 路径规则是 ADR-002 在治理层的体现。

---

## 9. UE 5.7 架构迁移影响

UE 5.5.4 → 5.7 升级中,以下 BC 条目对架构层有显著影响。**P1 confirmed** 6 条已由 msc 裁决,5.7 升级前必须迁;**P2 suspected** 3 条待 5.7 实测裁决,reviewer=pending-msc。详细 BC 表见 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3。

**P1 confirmed**(必须迁移):

- **[UE57-BC-008] `EditorScriptingUtilities` 模块依赖**(P1 confirmed, msc):影响 §1.1 插件层 C++ 构建 + §4 L1/L3。`AgentBridge.Build.cs` / `AgentBridgeTests.Build.cs` / `AgentBridge.uplugin` 须移除该模块依赖,调用迁到 `UEditorActorSubsystem` / `ULevelEditorSubsystem` / `UEditorAssetSubsystem`。
- **[UE57-BC-010] `IncludeOrderVersion = Unreal5_5`**(P1 confirmed, msc):影响 §1.1 项目层 Build。`Source/Mvpv4TestCodex.Target.cs` + `Mvpv4TestCodexEditor.Target.cs` 须改为 `Unreal5_6` 或 `Unreal5_7`。
- **[UE57-BC-012] `.uproject EngineAssociation "5.5"`**(P1 confirmed, msc):影响 §1.1 项目层 Launcher 加载。`Mvpv4TestCodex.uproject:3` 改 `"5.7"`,否则双击工程无法识别。
- **[UE57-BC-016] `unreal.EditorLevelLibrary` (Python)**(P1 confirmed, msc):影响 §4 L1 通道 A 全部查询与写工具。`MCP/server.py` + `Scripts/bridge/query_tools.py` + `write_tools.py` 中所有 `unreal.EditorLevelLibrary.*` 改为 `unreal.UnrealEditorSubsystem` / `LevelEditorSubsystem` / `EditorActorSubsystem`。
- **[UE57-BC-017] `unreal.EditorAssetLibrary` (Python)**(P1 confirmed, msc):影响 §4 L1 写工具 import / create_blueprint + L2 save 子族。改为 `unreal.EditorAssetSubsystem.*`。
- **[UE57-BC-025] 硬编码 `UE_5.5` 引擎路径**(P1 confirmed, msc):影响 §6 测试入口脚本。`run_system_tests.py` + `task14a_phase11_standalone_smoke.py` + `start_ue_editor_*.ps1` 共 7 处批量改 `UE_5.7` 或抽到 `$env:UE_INSTALL_ROOT`。

**P2 suspected**(待 5.7 实测):

- **[UE57-BC-019] RemoteControl HTTP 端点**(P2 suspected, pending-msc):影响 §4 通道 B 全部。5.7 RC 端点(`/remote/object/call` / `/remote/object/property` / `/remote/batch`)预期保留,但 JSON 序列化形态(Field 字段名 / Property Path 解析)可能变;新增 Preset HTTP API + Rundown Server 是否对现有调用有副作用待实测。注:BC-019 通道 B 全量受影响但 5.7 行为不明,**严格留 P2 suspected,不可上 P1**。
- **[UE57-BC-022] `.uproject` Plugins[]**(P2 suspected, pending-msc):`ModelingToolsEditorMode` + `RemoteControlWebInterface`(含 5.4 时代 `MarketplaceURL` 写法),5.7 是否移除外链待实测。
- **[UE57-BC-015] Config Layer**(P2 suspected, pending-msc):4 个 ini 无明显 breaking key,5.7 Editor 加载时可能 warning 个别废弃节,与字段规范交集小。

**迁移落点建议**(`Docs/contracts/tool_contract.md` §7.1):先解 BC-010 / BC-012 / BC-025 让工程能在 5.7 下加载,再处理 BC-008 编译错误,再实测 BC-019 端点行为,最后回扫 P2/P3。本 HLD 的架构边界(双层 / 三层工具 / 4 通道 / 7 Stage / Run 治理)在 5.7 升级中不变;只有"实现层适配"(unreal binding 改名 / 模块迁移 / 路径替换)需要按上述 BC 条目逐条修。

---

## 10. 与其他文档的关系

| 文档 | 关系 |
|---|---|
| `Docs/requirements/SRS.md` | 需求规格(本 HLD 的上游) |
| `Docs/contracts/tool_contract.md` | §4 工具签名与错误码族 |
| `Docs/contracts/schemas_catalog.md` | §2 / §5 Schema 字段级清单 |
| `Docs/contracts/mcp_tools_catalog.md` | §2 / §4 MCP 53 工具签名 |
| `Docs/contracts/field_specification.md` | §4 / §7 字段命名规范 |
| `Docs/design/LLD/02_bridge.md` | §4 Bridge 详细实现(占位) |
| `Docs/design/LLD/03_orchestrator.md` | §1.3 / §3 Orchestrator + Run 治理详细实现(占位) |
| `Docs/design/LLD/04_compiler.md` | §2 Compiler Core + Stage 4 Agent 协议详细实现(占位) |
| `Docs/design/LLD/05_mcp.md` | §4 MCP Server 详细实现(占位) |
| `Docs/design/LLD/06_skills_and_templates.md` | §2 / §3 SkillTemplates + Baseline Domain 详细实现(占位) |
| `Docs/design/LLD/07_schemas.md` | §5 Schema 演进与版本化详细实现(占位) |
| `Docs/testing/test_spec.md` | §6 测试用例编号与命令(占位) |
| `Docs/governance.md` | §3 / §7 治理规则(已 Phase 1.5 落地) |
| `Docs/Decisions/ADR-001-Doc-Governance.md` | §8 ADR 引用 |
| `Docs/Decisions/ADR-002-Task-And-Evidence-Archiving.md` | §8 ADR 引用 |
| `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` | §9 BC ID 来源 |
