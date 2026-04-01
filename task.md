# Phase 5 — Brownfield Baseline Understanding + Contracts 任务清单

> 目标引擎版本：UE5.5.4  
> 阶段定位：Phase 5  
> 当前阶段入口：[Docs/Current/06_Phase5_Task_List.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/06_Phase5_Task_List.md)  
> 上一阶段归档：[task2_phase4.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task2_phase4.md)

## 使用说明

1. 编码 Agent 必须先阅读每个 TASK 中列出的“先读这些文件”。
2. 所有新增 Python 代码必须带中文注释。
3. 本阶段测试用例先维护在本文件中，不提前写入 `Plugins/AgentBridge/Tests/SystemTestCases.md`。
4. `ProjectState/Snapshots/` 只保存 baseline / state snapshot；截图证据统一写入 `ProjectState/Evidence/Phase5/`。
5. 每个 TASK 的【验收标准】全部满足后，才能进入下一个 TASK。

## 核心约束

- 不修改稳定 C++ 核心：`Plugins/AgentBridge/Source/AgentBridge/`
- 不重构 `Plugins/AgentBridge/Scripts/bridge/*.py`
- 不重构 `Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py`
- 不修改稳定 Schema：`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`
- Greenfield 主链必须保持可用
- Brownfield 当前只真正执行 `append/new-actor`

## 任务总览

阶段 1 文档结算与证据治理（01-02）  
阶段 2 Brownfield 输入与分析（03-04）  
阶段 3 Contract 与 Delta 生成（05-06）  
阶段 4 主链集成、测试与验收（07-08）

---

## TASK 01：完成 Phase 5 当前文档切换与入口结算

目标：把项目层与插件层入口文档全部切到 Phase 5 当前口径，并明确根目录 `task.md` 是当前阶段唯一任务入口。  
前置依赖：无

先读这些文件：
- [AGENTS.md](/D:/UnrealProjects/Mvpv4TestCodex/AGENTS.md)
- [Docs/Current/00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [README.md](/D:/UnrealProjects/Mvpv4TestCodex/README.md)
- [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)

涉及文件：
- 更新：`README.md`
- 更新：`Docs/Current/00_Index.md`
- 更新：`Docs/Current/01_Project_Baseline.md`
- 更新：`Docs/Current/02_Current_Phase_Goals.md`
- 更新：`Docs/Current/03_Active_Backlog.md`
- 更新：`Docs/Current/04_Open_Risks.md`
- 更新：`Docs/Current/05_Implementation_Boundary.md`
- 更新：`Docs/Current/06_Phase5_Task_List.md`
- 新增：`Docs/Current/07_Evidence_And_Artifacts.md`
- 更新：`Plugins/AgentBridge/README.md`
- 更新：`Plugins/AgentBridge/Docs/compiler_design.md`
- 更新：`Plugins/AgentBridge/Docs/greenfield_pipeline.md`
- 按需更新：`Plugins/AgentBridge/Docs/architecture_overview.md`
- 迁移：`Plugins/AgentBridge/Docs/mvp_scope.md` → `Plugins/AgentBridge/Docs/Archive/Phase1-2/`

Step 1：把项目层 README、Current 文档和插件层 README 改到 Phase 5 事实口径。  
Step 2：把 `task.md` 的当前入口地位写入 `README.md`、`Docs/Current/06_Phase5_Task_List.md`。  
Step 3：把 `Snapshots` 与 `Evidence` 的职责边界写入 `Docs/Current/07_Evidence_And_Artifacts.md`。  
Step 4：把过时的 `mvp_scope.md` 移出插件主入口。  
Step 5：更新插件 canonical 文档，去掉“analysis/generation/review 占位”“Greenfield 仅 simulated”“RC 未联调”等过时表述。

【验收标准】
- `Docs/Current/00_Index.md` 已登记 `07_Evidence_And_Artifacts.md`
- `README.md` 不再出现根目录 `task1.md`
- `Plugins/AgentBridge/README.md` 不再要求阅读主路径下的 `Docs/mvp_scope.md`
- `Plugins/AgentBridge/Docs/compiler_design.md` / `greenfield_pipeline.md` 与当前代码事实一致

【证据要求】
- 在 `ProjectState/Reports/` 写一份 Phase 5 文档结算记录
- 记录被更新的入口文档清单

---

## TASK 02：明确 Task 与 Evidence 的阶段归档规则

目标：用 ADR 明确从 Phase 4 起的 `task.md` 归档规则和证据目录规则。  
前置依赖：TASK 01 完成

先读这些文件：
- [Docs/Decisions/ADR-001-Doc-Governance.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Decisions/ADR-001-Doc-Governance.md)
- [Docs/History/Tasks/00_Task_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/00_Task_Index.md)
- [Docs/Current/07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md)

涉及文件：
- 新增：`Docs/Decisions/ADR-002-Task-And-Evidence-Archiving.md`

Step 1：说明为什么不直接改写 ADR-001。  
Step 2：写明“根目录 `task.md` 为当前阶段入口，阶段结束归档到 `Docs/History/Tasks/`”。  
Step 3：写明“Phase 5 测试用例先留在 `task.md`，阶段归档时再补录到 `SystemTestCases.md`”。  
Step 4：写明“`Snapshots` 是基线产物，`Evidence/Phase5` 是阶段证据”。

【验收标准】
- ADR-002 可独立解释当前期任务与证据归档规则
- 不与 `Docs/History/Tasks/00_Task_Index.md` 冲突

【证据要求】
- ADR 文件本身即为证据；另在阶段验收记录中引用

---

## TASK 03：桥接真实 Project State Intake

目标：让 `project_state_intake.py` 从固定 mock 升级为真实 Bridge 查询 + fallback。  
前置依赖：TASK 01 完成

先读这些文件：
- [project_state_intake.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/compiler/intake/project_state_intake.py)
- [compiler_design.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/compiler_design.md)
- [05_Implementation_Boundary.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/05_Implementation_Boundary.md)

涉及文件：
- 更新：`Plugins/AgentBridge/Scripts/compiler/intake/project_state_intake.py`

Step 1：优先复用现有 `query_tools.py` 查询当前项目状态。  
Step 2：保留兼容字段：`project_name / engine_version / current_level / actor_count / is_empty / actors`。  
Step 3：新增 Brownfield 字段：`has_existing_content / has_baseline / baseline_refs / registry_refs / known_issues_summary / metadata / current_project_state_digest`。  
Step 4：在默认 MOCK 通道下回退为空项目快照，避免误把 Greenfield 流程识别成 Brownfield。  
Step 5：新增代码全部带中文注释。

【验收标准】
- 无 Editor 时返回明确 `mock_fallback` 快照
- 有真实 Bridge 时能返回结构化项目状态
- 现有 Greenfield 脚本不会因为 intake 改造而误判模式

【证据要求】
- 纯 Python 测试记录
- 如有真实 Editor，会话日志写入 `ProjectState/Evidence/Phase5/logs/`

---

## TASK 04：落地 Baseline Builder 与 Delta Scope Analyzer

目标：在 `analysis/` 下实装最小 Brownfield 分析链。  
前置依赖：TASK 03 完成

先读这些文件：
- [architecture_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/architecture_overview.md)
- [compiler_design.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/compiler_design.md)
- [01_Project_Baseline.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/01_Project_Baseline.md)

涉及文件：
- 新增：`Plugins/AgentBridge/Scripts/compiler/analysis/baseline_builder.py`
- 新增：`Plugins/AgentBridge/Scripts/compiler/analysis/delta_scope_analyzer.py`
- 新增：`Plugins/AgentBridge/Scripts/compiler/analysis/__init__.py`

Step 1：Baseline Builder 将项目状态固化到 `ProjectState/Snapshots/`。  
Step 2：Baseline Snapshot 至少包含：`baseline_id / snapshot_ref / current_project_model / current_spec_baseline / metadata`。  
Step 3：Delta Analyzer 至少输出：`delta_intent / affected_domains / affected_specs / append_specs / patch_specs / replace_specs / required_regression_checks / unsupported_items`。  
Step 4：当前只真正支持 `no_change / append_actor` 的执行闭环。  
Step 5：`patch / replace / migrate` 先输出表达和阻断信息，不伪装成 create。

【验收标准】
- 能在 `ProjectState/Snapshots/` 生成 baseline snapshot 文件
- 能区分 `no_change / append_actor / patch_existing_content`
- Brownfield append 样板下，delta 结果只追加 `PieceO_1`

【证据要求】
- snapshot 文件路径
- Phase 5 Python 测试结果

---

## TASK 05：创建最小 Contract 体系

目标：把 `Specs/Contracts/` 从占位升级为最小可加载 Contract 体系。  
前置依赖：TASK 04 完成

先读这些文件：
- [Specs/Contracts/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Specs/Contracts/README.md)
- [skills_and_specs_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/skills_and_specs_overview.md)

涉及文件：
- 新增：`Specs/Contracts/Registry/contract_type_registry.yaml`
- 新增：`Specs/Contracts/Common/SpecPatchContractModel/*`
- 新增：`Specs/Contracts/Common/MigrationContractModel/*`
- 新增：`Specs/Contracts/Common/RegressionValidationContractModel/*`
- 更新：`Specs/Contracts/README.md`

Step 1：建立 Contract registry。  
Step 2：落 3 类 Common Contract 的 `manifest / template / schema`。  
Step 3：在 registry 中登记 `contract_id / contract_kind / target_spec_family / required_fields / template_ref / schema_ref`。  
Step 4：保证 Brownfield 生成链能引用这些 Contract。

【验收标准】
- registry 能被 `yaml.safe_load` 解析
- 3 类 Common Contract 都可被 loader 装载
- Brownfield delta tree 中能看到 `contract_refs`

【证据要求】
- Contract loader 测试结果
- registry 路径写入阶段验收记录

---

## TASK 06：接入 Brownfield Delta 生成与 Handoff 主链

目标：让 Brownfield 模式真正输出 `baseline_context / delta_context / tree_type=delta`。  
前置依赖：TASK 05 完成

先读这些文件：
- [handoff_builder.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/compiler/handoff/handoff_builder.py)
- [compiler_main.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/compiler_main.py)
- [reviewed_handoff.schema.json](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json)

涉及文件：
- 更新：`Plugins/AgentBridge/Scripts/compiler/generation/spec_generation_dispatcher.py`
- 新增：`Plugins/AgentBridge/Scripts/compiler/generation/brownfield_delta_generator.py`
- 更新：`Plugins/AgentBridge/Scripts/compiler/review/cross_spec_reviewer.py`
- 更新：`Plugins/AgentBridge/Scripts/compiler/handoff/handoff_builder.py`
- 更新：`Plugins/AgentBridge/Scripts/compiler_main.py`

Step 1：Greenfield 路径保持原样。  
Step 2：Brownfield 路径串联 `project_state_intake → baseline_builder → delta_scope_analyzer → Contracts → brownfield_delta_generator → review`。  
Step 3：delta tree 必须包含 `tree_type / delta_operations / baseline_actor_refs / contract_refs`。  
Step 4：`scene_spec.actors[]` 在 Brownfield 下只保留本次新增 Actor。  
Step 5：review 对 patch/migration 缺少 Contract 或 unsupported_items 时必须阻断 handoff。

【验收标准】
- Brownfield Handoff 通过 Schema 校验
- append-only 样板下 `scene_spec.actors[]` 只包含 `PieceO_1`
- Greenfield Phase 4 旧回归仍通过

【证据要求】
- Brownfield Handoff 文件
- Brownfield baseline snapshot 文件
- Greenfield / Brownfield pytest 结果

---

## TASK 07：提供项目层 Brownfield Demo 与截图证据脚本

目标：在项目层提供最小 Brownfield 端到端入口，并把截图证据写入统一目录。  
前置依赖：TASK 06 完成

先读这些文件：
- [Scripts/run_greenfield_demo.py](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/run_greenfield_demo.py)
- [07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md)
- [tool_contract_v0_1.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/tool_contract_v0_1.md)

涉及文件：
- 新增：`Scripts/run_brownfield_demo.py`
- 新增：`Scripts/validation/capture_phase5_evidence.py`
- 新增：`ProjectState/Evidence/Phase5/screenshots/.gitkeep`
- 新增：`ProjectState/Evidence/Phase5/logs/.gitkeep`
- 新增：`ProjectState/Evidence/Phase5/notes/.gitkeep`

Step 1：提供 Board + PieceX_1 → 追加 PieceO_1 的 Brownfield 样板。  
Step 2：simulated 模式下验证 delta 只追加新增 Actor。  
Step 3：真实 UE5 模式下，调用截图辅助脚本。  
Step 4：截图命名必须符合 `phase5_<taskid>_<scenario>_<view>.png`。  
Step 5：同时生成 `phase5_<taskid>_<scenario>_evidence.md` 记录 handoff、report、相机说明与画面中应见 Actor。

【验收标准】
- `python Scripts/run_brownfield_demo.py` 可跑通 simulated
- 真机模式下能把证据写到 `ProjectState/Evidence/Phase5/`
- 截图不写入 `ProjectState/Snapshots/`

【证据要求】
- Brownfield simulated 报告
- 如有真实 Editor：overview_oblique + topdown_alignment 两张截图
- 对应 evidence note

---

## TASK 08：补齐 Phase 5 测试与阶段验收记录

目标：先在代码和 `task.md` 中完成 Phase 5 测试闭环，暂不写 `SystemTestCases.md`。  
前置依赖：TASK 07 完成

先读这些文件：
- [test_phase4_compiler.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/scripts/test_phase4_compiler.py)
- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)
- [Docs/Current/07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md)

涉及文件：
- 新增：`Plugins/AgentBridge/Tests/scripts/test_phase5_brownfield.py`
- 新增：`ProjectState/Reports/task_phase5_validation_<date>.md`
- 暂不更新：`Plugins/AgentBridge/Tests/SystemTestCases.md`

Step 1：新增 Phase 5 Python 测试。  
Step 2：至少覆盖：
  - `project_state_intake` fallback
  - baseline snapshot 序列化
  - `delta_scope_analyzer` 的 `no_change / append_actor`
  - Contract registry / template / schema 加载
  - Brownfield Handoff Schema 校验
  - Brownfield simulated E2E
Step 3：跑 Greenfield 回归测试。  
Step 4：生成一份 Phase 5 当前阶段验收记录。  
Step 5：在验收记录中明确写出：本阶段测试用例尚未并入 `SystemTestCases.md`，将在 Phase 5 归档时统一补录。

【验收标准】
- `pytest test_phase4_compiler.py` 通过
- `pytest test_phase5_brownfield.py` 通过
- `python Scripts/run_greenfield_demo.py` 通过
- `python Scripts/run_brownfield_demo.py` 通过
- `ProjectState/Reports/` 下存在 Phase 5 验收记录

【证据要求】
- pytest 输出摘要
- Greenfield / Brownfield 运行报告
- 如有真机验证：截图证据路径

---

## 阶段收尾预留（本阶段结束时执行，不在中途提前做）

- 将根目录 `task.md` 归档为 `Docs/History/Tasks/task3_phase5.md`
- 将本文件中已验证完成的测试用例补录到 `Plugins/AgentBridge/Tests/SystemTestCases.md`
- 将 `ProjectState/Evidence/Phase5/` 归档到 `Docs/History/reports/AgentBridgeEvidence/phase5_evidence_<date>/`
