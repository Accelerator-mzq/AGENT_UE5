# Phase 4 — Static Spec Base + 自动 Dynamic Spec 生成任务清单

> 目标引擎版本：UE5.5.4 | 文档版本：Phase4-v1
> 架构主轴：Static Spec Base → Skill Compilation → Dynamic / Delta Spec Tree → Reviewed Handoff → Execution Orchestrator
> 开发路线：参见 `D:\ClaudeProject\fenxi-claude\AGENT_UE5_Development_Roadmap.md`
> 当前阶段入口：`Docs/Current/06_Phase4_Task_List.md`

---

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent。
2. 每个 TASK 内附“先读这些文件”列表，编码 Agent 必须先读完再动手。
3. 每个 TASK 末尾有【验收标准】——全部通过才可进入下一个 TASK。
4. PowerShell 读取文本必须使用 `Get-Content -Encoding UTF8`。
5. 所有新增 Python 代码必须带中文注释。
6. 当前 Phase 4 只做“Static Base + 自动生成 + 最小编译层”，不完整实现 Genre Skill Pack / Base Skill Domains。

## 核心约束

- **不修改**任何现有 C++ 核心：`Plugins/AgentBridge/Source/AgentBridge/`
- **不修改**任何现有 Bridge 客户端：`Plugins/AgentBridge/Scripts/bridge/*.py`
- **不修改**现有 Orchestrator 核心：`orchestrator.py` / `plan_generator.py` / `verifier.py` / `report_generator.py` / `spec_reader.py`
- **不修改**任何现有稳定 Schema：`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`
- **允许修改** Phase 3 新增 Python 入口：`design_input_intake.py`、`handoff_builder.py`、`compiler_main.py`、`run_greenfield_demo.py`
- `dynamic_spec_tree` **必须继续保留** `scene_spec.actors[]`
- 当前阶段继续以 Greenfield 为主，Brownfield 只预留字段与依赖位

## 任务总览

阶段 1 文档切换与门禁（01-02） > 阶段 2 Static Base 落地（03-05） > 阶段 3 Compiler 自动生成（06-08） > 阶段 4 集成与验收（09-10）

---
---

# 阶段 1：文档切换与门禁

---

## TASK 01：创建 Phase 4 当前任务入口与文档切换

```
目标：把 Docs/Current/ 从 Phase 3 切换到 Phase 4，并在项目根目录创建 task.md 作为当前阶段任务入口。

前置依赖：无

先读这些文件：
- AGENTS.md
- Docs/Current/00_Index.md
- Docs/Current/01_Project_Baseline.md
- Docs/Current/03_Active_Backlog.md
- Docs/Current/04_Open_Risks.md
读完应掌握：当前 Docs/Current/ 仍停在 Phase 3，需要正式切换到 Phase 4。

涉及文件：
- 根目录新增：task.md
- Docs/Current/ 新增：06_Phase4_Task_List.md
- Docs/Current/ 更新：00_Index.md / 02_Current_Phase_Goals.md / 03_Active_Backlog.md / 04_Open_Risks.md / 05_Implementation_Boundary.md

Step 1: 创建根目录 task.md，并写入 Phase 4 的 10 个 TASK。
Step 2: 创建 Docs/Current/06_Phase4_Task_List.md，作为当前阶段任务索引。
Step 3: 更新 00_Index.md，将阶段名切换为 Phase 4 并登记 06 文件。
Step 4: 更新 02_Current_Phase_Goals.md，改写为 Static Base + 自动生成主线。
Step 5: 更新 03_Active_Backlog.md / 04_Open_Risks.md / 05_Implementation_Boundary.md 到 Phase 4 口径。

【验收标准】
- 根目录 task.md 存在且头部可正常阅读
- Docs/Current/06_Phase4_Task_List.md 存在
- Docs/Current/00_Index.md 显示 Phase 4 为 Active
- Docs/Current/02/03/04/05 已切换到 Phase 4 口径
```

---

## TASK 02：完成 Phase 3 遗留的真实 UE5 smoke 门禁

```
目标：在不改稳定核心的前提下，确认当前 scene_spec.actors[] 链路能通过真实 UE5 跑通一次。

前置依赖：TASK 01 完成

先读这些文件：
- Docs/Current/03_Active_Backlog.md
- Docs/Current/04_Open_Risks.md
- run_greenfield_demo.py
- Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py
读完应掌握：本任务只做真实 smoke，不重构稳定核心。

涉及文件：
- 可修改：run_greenfield_demo.py / handoff_runner.py
- 验收产物：ProjectState/Reports/ 下新增真实 smoke 报告

Step 1: 启动 UE5.5.4 Editor，确保项目能打开。
Step 2: 运行 `python run_greenfield_demo.py bridge_rc_api` 或 `python run_greenfield_demo.py bridge_python`。
Step 3: 若参数适配有问题，只允许修正 handoff_runner.py 的桥接层与 Transform 适配。
Step 4: 验证 Board / PieceX_1 / PieceO_1 是否在 UE5 中生成。
Step 5: 若环境不满足，必须记录失败证据，不得宣称成功。

【验收标准】
- 真实模式下至少一次成功生成 Board / PieceX_1 / PieceO_1
- 执行报告输出到 ProjectState/Reports/
- 若失败，失败原因已沉淀到 Docs/Current/04_Open_Risks.md 和 ProjectState/Reports/
```

---
---

# 阶段 2：Static Base 落地

---

## TASK 03：创建 Static Base 顶层结构与 registry

```
目标：把 Specs/StaticBase/ 从 README 占位升级成可加载的最小 Static Base 体系。

前置依赖：TASK 02 完成

先读这些文件：
- Plugins/AgentBridge/Specs/StaticBase/README.md
- D:\ClaudeProject\fenxi-claude\Prototype_阶段最小_Static_Spec_Base_清单_v2.md
- D:\ClaudeProject\fenxi-claude\Static_Spec_Base_与_Skill_编译依赖关系草案_v2.md
读完应掌握：Static Base 是地基，Skill 在其约束下生成 Dynamic Spec Tree。

涉及文件：
- 新增：Plugins/AgentBridge/Specs/StaticBase/Registry/spec_type_registry.yaml
- 新增目录：Core/ / Genres/Boardgame/
- 更新：Plugins/AgentBridge/Specs/StaticBase/README.md

Step 1: 创建 Registry 目录和 `spec_type_registry.yaml`。
Step 2: 在 registry 中登记 10 个静态基座的 spec_id / layer / dependencies / required_input_keys / template_ref / schema_ref / emits_tree_nodes / phase4_enabled。
Step 3: 创建 Core/ 和 Genres/Boardgame/ 目录骨架。
Step 4: 更新 README.md，说明 Static Base 已从占位转为可加载入口。

【验收标准】
- registry 能被 Python `yaml.safe_load` 正常解析
- 10 个静态基座全部在 registry 中可见
- 旧 README 未删除，而是转为真正入口说明
```

---

## TASK 04：实装 Layer A 六个通用静态基座

```
目标：实装 GameplayFrameworkStaticSpec、UIModelStaticSpec、AudioEventStaticSpec、WorldBuildStaticSpec、ConfigStaticSpec、ValidationStaticSpec 的最小模板。

前置依赖：TASK 03 完成

先读这些文件：
- Plugins/AgentBridge/Docs/skills_and_specs_overview.md
- Plugins/AgentBridge/Specs/templates/scene_spec_template.yaml
读完应掌握：Layer A 是跨类型的通用表达地基，其中 WorldBuild / Validation 会直接支撑 Phase 4 主链。

涉及文件：
- 每个 Layer A 基座目录新增：
  manifest.yaml
  template.yaml
  schema.json

Step 1: 为 6 个基座补齐 manifest.yaml。
Step 2: 为 6 个基座补齐 template.yaml。
Step 3: 为 6 个基座补齐 schema.json。
Step 4: 重点保证 WorldBuildStaticSpec 与 ValidationStaticSpec 能直接服务 Phase 4 主链。

【验收标准】
- 6 个基座目录完整
- schema.json 全部是合法 JSON
- template.yaml 全部可被 yaml.safe_load 解析
- registry 中每个 Layer A 基座都能解析出依赖和输出节点
```

---

## TASK 05：实装 Layer B 四个 Boardgame 静态基座

```
目标：实装 BoardgameStaticSpec、BoardgameUIStaticSpec、BoardgameAudioStaticSpec、BoardgameValidationStaticSpec。

前置依赖：TASK 04 完成

先读这些文件：
- D:\ClaudeProject\fenxi-claude\Boardgame_Static_Base_草案_v2.md
- D:\ClaudeProject\fenxi-claude\genre_boardgame_设计草案_v2.md
- Plugins/AgentBridge/Skills/genre_packs/boardgame/pack_manifest.yaml
读完应掌握：Boardgame Layer B 不只是多几个字段，而是对类型化表达、预览策略和验证逻辑的补强。

涉及文件：
- Genres/Boardgame/ 下 4 个基座目录，各自新增：
  manifest.yaml
  template.yaml
  schema.json

Step 1: 实装 BoardgameStaticSpec，至少表达棋盘尺寸、格子尺寸、棋子目录、示例棋子预览策略。
Step 2: 实装 BoardgameUIStaticSpec / BoardgameAudioStaticSpec，提供真实模板和 schema。
Step 3: 实装 BoardgameValidationStaticSpec，至少表达棋盘存在、示例棋子数量、Transform 合法。
Step 4: 将 4 个 Boardgame 基座都补入 registry。

【验收标准】
- 4 个 Boardgame 基座都在 registry 注册
- BoardgameStaticSpec 可覆盖井字棋 GDD 的核心字段
- BoardgameValidationStaticSpec 至少能表达“棋盘存在 / 示例棋子数量 / Transform 合法”三类检查
```

---
---

# 阶段 3：Compiler 自动生成

---

## TASK 06：增强 Design Input Intake，提取结构化 GDD

```
目标：把当前只返回 game_type 的 intake 升级为 Phase 4 可用的结构化设计输入。

前置依赖：TASK 05 完成

先读这些文件：
- Plugins/AgentBridge/Scripts/compiler/intake/design_input_intake.py
- ProjectInputs/GDD/boardgame_tictactoe_v1.md
- D:\ClaudeProject\fenxi-claude\Design_与_Project_State_Intake_设计草案_v1.md
读完应掌握：Phase 4 的 intake 不做复杂 NLP，但要提取到足够支撑 Static Base / generation 的结构化程度。

涉及文件：
- 更新：Plugins/AgentBridge/Scripts/compiler/intake/design_input_intake.py

Step 1: `read_gdd()` / `read_gdd_from_directory()` 新增 `feature_tags`、`board`、`piece_catalog`、`rules`、`initial_layout`、`prototype_preview`、`technical_requirements`。
Step 2: 为井字棋 GDD 增加确定性提取逻辑：棋盘总尺寸、格子尺寸、X/O 类型、初始为空棋盘、StaticMeshActor 等。
Step 3: 实现示例棋子默认策略：未指定 → 1 个 X + 1 个 O；显式 0 → 不生成。
Step 4: 保持代码可读性，关键解析逻辑必须有中文注释。

【验收标准】
- `read_gdd(...).keys()` 可看到新增字段
- 棋盘尺寸、格子尺寸、X/O 类型都非空
- 显式 0 示例棋子时能正确返回不生成
- 新增代码带中文注释
```

---

## TASK 07：实装最小自动生成链

```
目标：让 Compiler 从 “design_input + Static Base” 自动生成 dynamic_spec_tree。

前置依赖：TASK 06 完成

先读这些文件：
- Plugins/AgentBridge/Docs/compiler_design.md
- Plugins/AgentBridge/Scripts/compiler/generation/README.md
- Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json
读完应掌握：generation 的职责是自动生成 Dynamic Spec Tree，但必须保留 scene_spec.actors[] 兼容现有执行链。

涉及文件：
- 新增：Plugins/AgentBridge/Scripts/compiler/generation/__init__.py
- 新增：Plugins/AgentBridge/Scripts/compiler/generation/static_base_loader.py
- 新增：Plugins/AgentBridge/Scripts/compiler/generation/spec_generation_dispatcher.py
- 新增：Plugins/AgentBridge/Scripts/compiler/generation/boardgame_scene_generator.py
- 更新：Plugins/AgentBridge/Scripts/compiler/generation/README.md

Step 1: 实装 static_base_loader.py，能加载 registry 与每个静态基座的 manifest/template/schema。
Step 2: 实装 spec_generation_dispatcher.py，只做调度，不写成一整块硬编码。
Step 3: 实装 boardgame_scene_generator.py，同时产出 `boardgame_spec` / `validation_spec` / `scene_spec.actors[]`。
Step 4: dispatcher 读取现有 `pack_manifest.yaml` 的激活与依赖提示，但不在 Phase 4 完整实现 Skill Pack runtime。
Step 5: 保持与 reviewed_handoff.schema.json 兼容，不修改现有 Schema。

【验收标准】
- 自动生成后的 dynamic_spec_tree 不再来自 handoff_builder.py 手工写死
- scene_spec.actors[] 至少包含 Board 和默认示例棋子
- 生成结果通过 handoff schema 校验
```

---

## TASK 08：实装最小 Cross-Spec Review

```
目标：在执行前做最小但可判定的静态审查。

前置依赖：TASK 07 完成

先读这些文件：
- Plugins/AgentBridge/Scripts/compiler/review/README.md
- Plugins/AgentBridge/Docs/field_specification_v0_1.md
- Plugins/AgentBridge/AGENTS.md
读完应掌握：Review 是编译时检查，不是运行时验证；它的目标是发现明显错误和能力缺口。

涉及文件：
- 新增：Plugins/AgentBridge/Scripts/compiler/review/__init__.py
- 新增：Plugins/AgentBridge/Scripts/compiler/review/cross_spec_reviewer.py
- 更新：Plugins/AgentBridge/Scripts/compiler/review/README.md

Step 1: 定义 review 返回结构：`status` / `reviewed` / `errors` / `warnings` / `capability_gaps`。
Step 2: capability_gaps 固定使用：`required_static_templates` / `unresolved_refs` / `unsupported_gdd_sections` / `missing_patch_contracts` / `unsupported_regression_checks`。
Step 3: 最小检查项至少覆盖模板存在、依赖完整、Actor 名称唯一、actor_class 非空、Transform 为数值三元组、预览棋子与 piece_catalog 一致。
Step 4: 将无法落地的内容写入 capability_gaps，而不是直接吞掉。

【验收标准】
- 构造一份故意错误的 dynamic_spec_tree 时，review 能返回失败并指出缺口
- 合法井字棋 dynamic_spec_tree 能返回 reviewed
- capability_gaps 固定使用 Phase 4 约定的 5 个键
```

---
---

# 阶段 4：集成与验收

---

## TASK 09：集成 Compiler / Handoff / Demo 主链

```
目标：让 Phase 4 的自动生成链接入现有 Compiler 与 demo 入口。

前置依赖：TASK 08 完成

先读这些文件：
- Plugins/AgentBridge/Scripts/compiler/handoff/handoff_builder.py
- Plugins/AgentBridge/Scripts/compiler_main.py
- run_greenfield_demo.py
读完应掌握：Phase 3 的主链已经存在，Phase 4 只替换 handoff_builder 的图纸来源，不破坏入口形式。

涉及文件：
- 更新：Plugins/AgentBridge/Scripts/compiler/handoff/handoff_builder.py
- 更新：Plugins/AgentBridge/Scripts/compiler/handoff/__init__.py
- 更新：Plugins/AgentBridge/Scripts/compiler_main.py
- 更新：run_greenfield_demo.py
- 视情况更新：Plugins/AgentBridge/Scripts/compiler/__init__.py

Step 1: 改造 handoff_builder.py，从“手工构造 3 Actor”切换到“载入 static base → 自动生成 → review → 组装 handoff”。
Step 2: 保持 `routing_context.activated_skill_packs`，即使本阶段不完整实现 Skill runtime。
Step 3: 修正 compiler_main.py 的默认项目根路径，确保从项目根 `ProjectInputs/` 读取。
Step 4: 让 run_greenfield_demo.py 继续支持 simulated / bridge_python / bridge_rc_api，但改走新的 Handoff 生成主链。

【验收标准】
- `python Plugins/AgentBridge/Scripts/compiler_main.py` 能输出新的 Handoff
- `python run_greenfield_demo.py` 仍可跑通 simulated 模式
- 输出 Handoff 中可看到 richer spec 节点和兼容的 scene_spec.actors[]
```

---

## TASK 10：补齐系统测试、验收记录与 Phase 4 收尾

```
目标：让 Phase 4 有成体系的 Python 测试、系统测试条目和验收记录。

前置依赖：TASK 09 完成

先读这些文件：
- Plugins/AgentBridge/Tests/SystemTestCases.md
- Plugins/AgentBridge/Tests/run_system_tests.py
- ProjectState/Reports/task07_validation_2026-03-31.md
读完应掌握：Phase 4 需要新增 CP/SS/E2E 维度的测试与验收记录，但不改现有 C++ Automation Test。

涉及文件：
- 新增：Plugins/AgentBridge/Tests/scripts/test_phase4_compiler.py
- 更新：Plugins/AgentBridge/Tests/scripts/conftest.py（如需新增 fixture）
- 更新：Plugins/AgentBridge/Tests/SystemTestCases.md
- 视需要更新：Plugins/AgentBridge/Tests/README.md / run_system_tests.py
- 新增验收记录：ProjectState/Reports/task_phase4_validation_*.md

Step 1: 新增 test_phase4_compiler.py，至少覆盖 registry 加载、10 个静态基座存在、GDD 解析字段完整、默认示例棋子策略、显式 0 策略、dynamic_spec_tree 自动生成、review 失败样例、handoff schema 校验。
Step 2: 在 SystemTestCases.md 的 CP / SS / E2E 段新增 Phase 4 用例。
Step 3: 运行 `validate_examples.py --strict`、`pytest test_mvp_regression.py`、`pytest test_phase4_compiler.py`、`python run_greenfield_demo.py`。
Step 4: 在 ProjectState/Reports/ 下新增一份 Phase 4 验收记录，记录文档切换、Static Base、generation、review、simulated E2E、真实 smoke、回归情况。

【验收标准】
- 旧回归仍通过
- 新增 Phase 4 Python 测试通过
- SystemTestCases.md 能覆盖默认示例棋子、GDD 覆盖数量、显式 0 示例棋子、缺失模板报 gap、simulated E2E、真实 UE5 smoke 六类用例
- ProjectState/Reports/ 下有一份 Phase 4 验收记录
```

---

## 阶段总验收

- 根目录 `task.md` 与 `Docs/Current/06_Phase4_Task_List.md` 同步存在，且都能定位 Phase 4 任务入口
- `Specs/StaticBase/` 不再是 README 占位，而是可加载的 registry + 10 个静态基座
- `design_input_intake.py` 已能从井字棋 GDD 提取结构化字段，而不只是 `game_type`
- `handoff_builder.py` 不再手工写死 3 Actor；`dynamic_spec_tree` 来自自动生成
- `dynamic_spec_tree` 同时具备 richer spec 节点和当前 Orchestrator 仍能消费的 `scene_spec.actors[]`
- 真实 UE5 smoke 至少尝试一次；若成功则记录成功证据，若失败则记录失败原因与环境约束
- 所有新增 Python 代码带中文注释；稳定 C++ / Bridge / Orchestrator 核心 / 旧 Schema 均未被破坏

## 假设与默认

- 当前 Phase 4 仍以 Greenfield 为主，`project_state_intake.py` 保持 mock
- Brownfield 的 Patch / Regression Contract 延后到 Phase 5
- 完整 Genre Skill Pack / Base Skill Domains 机制延后到 Phase 6 / Phase 7，本阶段只保留最小编译层与 `activated_skill_packs` 主轴
