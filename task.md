# Phase 5 — Brownfield Baseline Understanding + Contracts 任务清单

> 目标引擎版本：UE5.5.4 | 文档版本：Phase5-v1
> 架构主轴：Static Spec Base → Skill Compilation → Dynamic / Delta Spec Tree → Reviewed Handoff → Execution Orchestrator
> 当前阶段入口：`Docs/Current/06_Phase5_Task_List.md`
> 上一阶段归档：`Docs/History/Tasks/task2_phase4.md`

---

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent。
2. 每个 TASK 内附“先读这些文件”列表，编码 Agent 必须先读完再动手。
3. 每个 TASK 末尾有【验收标准】。
4. PowerShell 读取文本必须使用 `Get-Content -Encoding UTF8`。
5. 所有新增 Python 代码必须带中文注释。
6. 当前 Phase 5 只做“Brownfield 基线理解 + 差量分析 + Contracts 最小落地”，不完整实现 Phase 6/7 的 Skill 机制。

## 核心约束

- **不修改**任何现有 C++ 核心：`Plugins/AgentBridge/Source/AgentBridge/`
- **不修改**任何现有稳定 Bridge 客户端主链：`Plugins/AgentBridge/Scripts/bridge/*.py`
- **不修改**现有 Orchestrator 核心：`orchestrator.py` / `plan_generator.py` / `verifier.py` / `report_generator.py` / `spec_reader.py`
- **不修改**任何现有稳定 Schema：`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`
- **允许修改** Compiler 相关 Python 入口：`project_state_intake.py`、`handoff_builder.py`、`compiler_main.py`
- Greenfield 现有 `dynamic_spec_tree.scene_spec.actors[]` 兼容链必须保留
- Brownfield 允许新增 `baseline_context` / `delta_context` / Contract 引用，但不能破坏 Phase 4 已闭环能力

## 任务总览

阶段 1 文档切换与归档（01） > 阶段 2 Brownfield 输入与分析（02-04） > 阶段 3 Contract 体系（05-06） > 阶段 4 集成与验收（07-08）

---
---

# 阶段 1：文档切换与归档

---

## TASK 01：归档 Phase 4 并切换到 Phase 5 当前入口

```
目标：把根目录 task.md 从 Phase 4 切换到 Phase 5，并把 Phase 4 任务统一归档到 Docs/History/Tasks/。

前置依赖：无

先读这些文件：
- AGENTS.md
- Docs/Current/00_Index.md
- Docs/History/Tasks/task2_phase4.md
- Docs/History/Tasks/00_Task_Index.md

涉及文件：
- 更新：AGENTS.md
- 更新：Docs/Current/00_Index.md / 01_Project_Baseline.md / 02_Current_Phase_Goals.md / 03_Active_Backlog.md / 04_Open_Risks.md / 05_Implementation_Boundary.md
- 新增：Docs/Current/06_Phase5_Task_List.md
- 更新：根目录 task.md

【验收标准】
- Docs/Current 已切换为 Phase 5 Active
- 根目录 task.md 为 Phase 5 当前任务清单
- Docs/History/Tasks/task2_phase4.md 保留为 Phase 4 归档
```

---
---

# 阶段 2：Brownfield 输入与分析

---

## TASK 02：桥接真实 Project State Intake

```
目标：让 project_state_intake.py 不再返回固定 mock，而是能读取真实项目状态。

前置依赖：TASK 01 完成

先读这些文件：
- Plugins/AgentBridge/Scripts/compiler/intake/project_state_intake.py
- Plugins/AgentBridge/Docs/compiler_design.md
- Plugins/AgentBridge/Docs/greenfield_pipeline.md

涉及文件：
- 更新：Plugins/AgentBridge/Scripts/compiler/intake/project_state_intake.py
- 视需要新增：相关辅助模块或 fixture

关键要求：
- 至少读取 actor_count / level_name / has_existing_content / has_baseline
- 优先复用现有 Bridge 查询接口
- 保留 mock fallback，不让无 Editor 环境完全失效

【验收标准】
- 在无 Editor 环境下仍可返回可识别的 fallback 结构
- 在真实环境下能返回非硬编码的项目状态
- 新增代码带中文注释
```

---

## TASK 03：实装 Baseline Builder

```
目标：在 Scripts/compiler/analysis/ 下创建 baseline_builder.py，生成可持久化的基线快照。

前置依赖：TASK 02 完成

先读这些文件：
- Plugins/AgentBridge/Docs/compiler_design.md
- Plugins/AgentBridge/Docs/architecture_overview.md
- Docs/Current/01_Project_Baseline.md

涉及文件：
- 新增：Plugins/AgentBridge/Scripts/compiler/analysis/baseline_builder.py
- 更新：Plugins/AgentBridge/Scripts/compiler/analysis/__init__.py（如无则新增）
- 输出目录：ProjectState/Snapshots/ 或 ProjectInputs/Baselines/

关键要求：
- 基线至少包含项目名、关卡信息、Actor 清单、采集时间戳
- 输出格式必须稳定可比对
- 允许先以 JSON/YAML 的轻量快照为主

【验收标准】
- baseline_builder 可独立导入和运行
- 至少能生成 1 份基线快照文件
- 快照字段可供 delta 分析复用
```

---

## TASK 04：实装 Delta Scope Analyzer

```
目标：比较 design_input 与 baseline snapshot，输出 Brownfield 的最小差量范围。

前置依赖：TASK 03 完成

先读这些文件：
- Plugins/AgentBridge/Docs/compiler_design.md
- Plugins/AgentBridge/Docs/reviewed_handoff_design.md
- Plugins/AgentBridge/Docs/skills_and_specs_overview.md

涉及文件：
- 新增：Plugins/AgentBridge/Scripts/compiler/analysis/delta_scope_analyzer.py

关键要求：
- 输出至少包含 affected_domains / affected_specs / delta_intent
- 无法判断的项必须写入 capability_gaps，而不是静默忽略
- 当前阶段只要求最小 Brownfield 样例，不追求完整语义 diff

【验收标准】
- 给定 baseline + design_input 时可返回结构化 delta_context
- 至少能区分“无需修改 / 需要新增 / 需要 patch”三类结果
```

---
---

# 阶段 3：Contract 体系

---

## TASK 05：创建 Contracts 顶层结构与 registry

```
目标：把 Specs/Contracts/ 从 README 占位升级为可加载的最小 Contract 体系。

前置依赖：TASK 04 完成

先读这些文件：
- Plugins/AgentBridge/Docs/skills_and_specs_overview.md
- Plugins/AgentBridge/Specs/Contracts/README.md

涉及文件：
- 新增：Plugins/AgentBridge/Specs/Contracts/Registry/contract_type_registry.yaml
- 新增目录：SpecPatchContract/ MigrationContract/ RegressionValidationContract/

关键要求：
- registry 至少登记 contract_id / purpose / required_fields / schema_ref / template_ref
- README 要从占位升级为入口说明

【验收标准】
- registry 可被 yaml.safe_load 正常解析
- 3 类 Contract 均已登记
```

---

## TASK 06：实装 3 类最小 Contract 模板

```
目标：落地 SpecPatchContract、MigrationContract、RegressionValidationContract 的最小 manifest/template/schema。

前置依赖：TASK 05 完成

先读这些文件：
- Plugins/AgentBridge/Docs/skills_and_specs_overview.md
- Plugins/AgentBridge/Docs/reviewed_handoff_design.md

涉及文件：
- Specs/Contracts/*/manifest.yaml
- Specs/Contracts/*/template.yaml
- Specs/Contracts/*/schema.json

关键要求：
- SpecPatchContract：表达局部 patch 目标与允许修改边界
- MigrationContract：表达跨结构迁移
- RegressionValidationContract：表达 Brownfield 回归验证要求

【验收标准】
- 3 类 Contract 模板和 schema 可正常加载
- 至少 1 份 Brownfield 样例能引用这些 Contract
```

---
---

# 阶段 4：集成与验收

---

## TASK 07：将 Brownfield 上下文接入 Handoff / Compiler 主链

```
目标：让 Compiler 在 Brownfield 模式下输出 baseline_context / delta_context / Contract 引用。

前置依赖：TASK 06 完成

先读这些文件：
- Plugins/AgentBridge/Scripts/compiler/handoff/handoff_builder.py
- Plugins/AgentBridge/Scripts/compiler_main.py
- Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json

涉及文件：
- 更新：handoff_builder.py
- 更新：compiler_main.py

关键要求：
- Greenfield 链路不能回归
- Brownfield Handoff 至少能产出 tree_type=delta 的最小表达
- capability_gaps 继续作为缺口兜底

【验收标准】
- Greenfield Handoff 继续可生成
- Brownfield 样例 Handoff 能通过 Schema 校验
```

---

## TASK 08：补齐 Phase 5 测试、系统测试条目与验收记录

```
目标：为 Phase 5 增加 Python 测试、SystemTestCases 条目和验收记录。

前置依赖：TASK 07 完成

先读这些文件：
- Plugins/AgentBridge/Tests/SystemTestCases.md
- Plugins/AgentBridge/Tests/run_system_tests.py
- ProjectState/Reports/task_phase4_validation_2026-03-31.md

涉及文件：
- 新增：Phase 5 Python 测试文件
- 更新：SystemTestCases.md
- 更新：run_system_tests.py（如需）
- 新增：ProjectState/Reports/task_phase5_validation_*.md

关键要求：
- 至少覆盖真实 project_state intake、baseline_builder、delta_scope_analyzer、Contract registry、Brownfield handoff
- 不破坏现有 Phase 4 测试

【验收标准】
- Phase 4 旧测试继续通过
- Phase 5 新增测试通过
- 生成 1 份 Phase 5 验收记录
```

---

## 阶段总验收

- Docs/Current 已切换到 Phase 5，Phase 4 已归档到 `Docs/History/Tasks/task2_phase4.md`
- `project_state_intake.py` 不再仅是固定 mock
- `Scripts/compiler/analysis/` 不再是占位目录
- `Specs/Contracts/` 不再只有 README 占位
- Brownfield 样例 Handoff 可生成并通过 Schema 校验
- Greenfield 现有 `Scripts/run_greenfield_demo.py` 链路继续可用

## 假设与默认

- 当前 Phase 5 仍优先做最小 Brownfield 闭环，而不是完整生产级增量流水线
- 完整 Genre Skill Pack / Base Skill Domains 机制继续延后到 Phase 6 / Phase 7
