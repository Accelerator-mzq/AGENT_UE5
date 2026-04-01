# Phase 6 — 完整 Spec Tree + 可玩 Runtime 任务清单

> 拟归档路径：`/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task4_phase6.md`  
> 目标引擎版本：UE5.5.4 | 阶段定位：Phase 6  
> 编写口径参考：[task2_phase4.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task2_phase4.md)、[task3_phase5.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task3_phase5.md)  
> 当前阶段索引：[00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)

## 本期固定规则

1. 根目录 `task.md` 是当前阶段唯一任务入口。
2. Phase 6 测试用例只维护在本文件，不提前写入 [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md)。
3. `ProjectState/Snapshots/` 只保存 baseline / state snapshot，`ProjectState/Evidence/Phase6/` 只保存 Phase 6 证据。
4. 真实 UE5 截图证据统一调用 [capture_editor_evidence.py](/D:/UnrealProjects/Mvpv4TestCodex/Scripts/validation/capture_editor_evidence.py)，不再沿用 `capture_phase5_*` 命名。

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent。
2. 每个 TASK 内的“先读这些文件”必须先读完，再动手。
3. 每个 TASK 末尾的【验收标准】全部通过，才能进入下一个 TASK。
4. PowerShell 读取文本统一使用 `Get-Content -Encoding UTF8`。
5. 所有新增代码必须带中文注释。
6. Phase 6 结束时，先归档本文件到 `Docs/History/Tasks/task4_phase6.md`，再把已验证通过的测试用例补录进 `SystemTestCases.md`。

## 核心约束

- 不重写现有稳定 C++ Subsystem：`Plugins/AgentBridge/Source/AgentBridge/`
- 不重构现有 Bridge 三通道主链：`Plugins/AgentBridge/Scripts/bridge/*.py`
- 不大改 Orchestrator 核心：`orchestrator.py` / `plan_generator.py` / `verifier.py` / `report_generator.py` / `spec_reader.py`
- 不修改现有稳定 Schema：`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`
- 允许扩展 `run_plan_builder.py` / `handoff_runner.py` 做最小兼容，不做大重构
- Phase 6 只做 `boardgame` 一个类型包，不提前进入第二个 Genre Pack

## 测试编号约定（仅本期使用）

- `SS-08~SS-13`：结构 / 模块 / 契约级测试
- `CP-25~CP-31`：编译期 / 审查期测试
- `E2E-22~E2E-27`：端到端与真机验证

## TASK 01：完成 Phase 6 文档结算与入口统一

目标：把项目层和插件层入口文档统一切到“完整 Spec Tree + 可玩 Runtime”口径。  
前置依赖：无

先读这些文件：
- [README.md](/D:/UnrealProjects/Mvpv4TestCodex/README.md)
- [00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
- [02_Current_Phase_Goals.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/02_Current_Phase_Goals.md)
- [Plugins/AgentBridge/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/README.md)

涉及文件：
- `README.md`
- `Docs/Current/00_Index.md`
- `Docs/Current/01_Project_Baseline.md`
- `Docs/Current/02_Current_Phase_Goals.md`
- `Docs/Current/03_Active_Backlog.md`
- `Docs/Current/04_Open_Risks.md`
- `Docs/Current/05_Implementation_Boundary.md`
- `Docs/Current/06_Phase6_Task_List.md`
- `Docs/Current/07_Evidence_And_Artifacts.md`
- `Docs/Current/08_Playable_Runtime_Acceptance.md`
- `Plugins/AgentBridge/README.md`

Step 1：把当前阶段目标明确为“完整 Spec Tree + 可玩 Runtime”，不再只写“Genre Skill Packs 完整化”。  
Step 2：把 `run_boardgame_playable_demo.py`、`capture_editor_evidence.py`、`RuntimeConfigs/` 写成正式 Phase 6 入口。  
Step 3：明确 `task.md` 为唯一当前任务入口，Phase 6 测试只在本文件维护。  

【验收标准】
- `Docs/Current/00_Index.md` 明确 Phase 6 为“完整 Spec Tree + 可玩 Runtime”
- `Docs/Current/08_Playable_Runtime_Acceptance.md` 存在
- `SystemTestCases.md` 本阶段未追加 Phase 6 用例正文

【证据要求】
- 在 `ProjectState/Reports/` 写一份 Phase 6 当前验证记录

## TASK 02：落地 Genre Pack Core 最小机制

目标：让 `Skills/genre_packs/_core/` 从占位目录变成真实可调用机制。  
前置依赖：TASK 01 完成

先读这些文件：
- [skills_and_specs_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/skills_and_specs_overview.md)
- [compiler_design.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/compiler_design.md)
- [AGENT_UE5_Development_Roadmap.md](/D:/ClaudeProject/fenxi-claude/AGENT_UE5_Development_Roadmap.md)

涉及文件：
- `Plugins/AgentBridge/Skills/genre_packs/_core/manifest_loader.py`
- `Plugins/AgentBridge/Skills/genre_packs/_core/registry.py`
- `Plugins/AgentBridge/Skills/genre_packs/_core/router_base.py`
- `Plugins/AgentBridge/Skills/genre_packs/_core/module_loader.py`
- `Plugins/AgentBridge/Skills/__init__.py`
- `Plugins/AgentBridge/Skills/genre_packs/__init__.py`

Step 1：实现单 pack manifest 装载与标准化。  
Step 2：实现类型包目录扫描与激活选择。  
Step 3：实现 required skills / review / validation / delta policy 的按目录加载。  

【验收标准】
- `SS-08`：_core registry 能发现 `genre-boardgame`
- `SS-09`：完整 boardgame manifest 可解析且字段齐全
- `_core` 不再依赖手工硬编码 pack 路径

【证据要求】
- pytest 输出或验证报告中能看到 `_core` 模块加载通过

## TASK 03：完整化 boardgame pack

目标：让 `boardgame` pack 真正成为编译驱动力，而不是只声明 manifest。  
前置依赖：TASK 02 完成

先读这些文件：
- [boardgame_tictactoe_v1.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/boardgame_tictactoe_v1.md)
- [skills_and_specs_overview.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/skills_and_specs_overview.md)
- [pack_manifest.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Skills/genre_packs/boardgame/pack_manifest.yaml)

涉及文件：
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/pack_manifest.yaml`
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/required_skills/board_layout.py`
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/required_skills/piece_movement.py`
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/required_skills/turn_system.py`
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/review_extensions/boardgame_reviewer.py`
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/validation_extensions/boardgame_validator.py`
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/delta_policy/boardgame_delta_policy.py`

Step 1：把 manifest 扩展到 Phase 6 完整字段。  
Step 2：实现 3 个 required skills，分别负责棋盘布局、落子规则、回合/UI/runtime wiring。  
Step 3：实现 reviewer / validator / delta policy。  

【验收标准】
- `SS-10`：3 个 required skills 模块可加载
- `SS-11`：review_extensions / validation_extensions / delta_policy 模块可加载
- `CP-25`：默认 `preview_static` 已生成完整 10 节点 Spec Tree

【证据要求】
- pytest 或编译报告中能看到 boardgame pack 模块加载通过

## TASK 04：将完整 Pack 机制接入 Compiler 主链

目标：让 Compiler 真正消费 `_core + boardgame pack`，而不是继续手工直读最小 manifest。  
前置依赖：TASK 03 完成

先读这些文件：
- [compiler_design.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/compiler_design.md)
- [spec_generation_dispatcher.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/compiler/generation/spec_generation_dispatcher.py)
- [boardgame_scene_generator.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Scripts/compiler/generation/boardgame_scene_generator.py)

涉及文件：
- `Plugins/AgentBridge/Scripts/compiler/generation/spec_generation_dispatcher.py`
- `Plugins/AgentBridge/Scripts/compiler/generation/boardgame_scene_generator.py`
- `Plugins/AgentBridge/Scripts/compiler/review/cross_spec_reviewer.py`
- `Plugins/AgentBridge/Scripts/compiler/analysis/delta_scope_analyzer.py`

Step 1：把 `generate_dynamic_spec_tree()` 改成 pack-aware。  
Step 2：加入 `projection_profile`，支持 `preview_static / runtime_playable`。  
Step 3：让 reviewer 能感知 `turn_flow_spec / decision_ui_spec / runtime_wiring_spec`。  

【验收标准】
- `CP-26`：`projection_profile=runtime_playable` 生成 runtime actor 投影与 runtime config 引用
- `CP-28`：缺失 `turn_flow_spec / decision_ui_spec / runtime_wiring_spec` 时 reviewer 阻断
- `CP-30`：delta policy 能影响 Brownfield delta trace

【证据要求】
- 生成的 handoff / dynamic_spec_tree 样例保存到 `ProjectState/Handoffs/` / `Reports/`

## TASK 05：补齐 Boardgame Genre Contracts

目标：把 boardgame 的 turn/ui 变更约束进 Contract registry。  
前置依赖：TASK 04 完成

先读这些文件：
- [contract_type_registry.yaml](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Specs/Contracts/Registry/contract_type_registry.yaml)
- [05_Implementation_Boundary.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/05_Implementation_Boundary.md)

涉及文件：
- `Plugins/AgentBridge/Specs/Contracts/Registry/contract_type_registry.yaml`
- `Plugins/AgentBridge/Specs/Contracts/Genres/Boardgame/TurnFlowPatchContract/*`
- `Plugins/AgentBridge/Specs/Contracts/Genres/Boardgame/DecisionUIPatchContract/*`

Step 1：新增 `TurnFlowPatchContract`。  
Step 2：新增 `DecisionUIPatchContract`。  
Step 3：让 Brownfield reviewer 能识别 contract 缺失并阻断。  

【验收标准】
- `SS-12`：Genre contracts 已登记到 contract registry
- `SS-13`：Common + Genre contract bundle 均可加载
- `CP-31`：缺少 turn/ui genre contract 时 Brownfield 对应 patch 被阻断

【证据要求】
- pytest 或编译报告中能看到 genre contract 装载通过

## TASK 06：落地项目层 playable runtime

目标：在项目层 `Source/Mvpv4TestCodex/` 中提供最小可玩井字棋运行时。  
前置依赖：TASK 05 完成

先读这些文件：
- [08_Playable_Runtime_Acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/08_Playable_Runtime_Acceptance.md)
- [boardgame_tictactoe_v1.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectInputs/GDD/boardgame_tictactoe_v1.md)

涉及文件：
- `Source/Mvpv4TestCodex/BoardgamePrototypeBoardActor.h`
- `Source/Mvpv4TestCodex/BoardgamePrototypeBoardActor.cpp`
- `Source/Mvpv4TestCodex/Mvpv4TestCodex.Build.cs`
- `ProjectState/RuntimeConfigs/`

Step 1：实现 runtime actor 的配置加载、落子、胜负判定、状态读回。  
Step 2：让 handoff 在 `runtime_playable` 路径下生成 `runtime_<handoff_id>.json`。  
Step 3：保持 `preview_static` 旧链路不回归。  

【验收标准】
- `CP-27`：runtime actor 至少暴露 `LoadRuntimeConfigFromFile / ApplyMoveByCell / GetBoardRuntimeState / ResetBoard`
- UBT 编译 `Mvpv4TestCodexEditor` 通过
- `runtime_playable` 不破坏 `preview_static` 和 Brownfield append 链路

【证据要求】
- UBT 编译日志
- `ProjectState/RuntimeConfigs/runtime_<handoff_id>.json`

## TASK 07：补齐项目层 demo 与截图证据链

目标：提供 Phase 6 主入口和阶段无关截图脚本。  
前置依赖：TASK 06 完成

先读这些文件：
- [editor_screenshot_evidence_workflow.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md)
- [07_Evidence_And_Artifacts.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/07_Evidence_And_Artifacts.md)

涉及文件：
- `Scripts/run_boardgame_playable_demo.py`
- `Scripts/validation/capture_editor_evidence.py`
- `Plugins/AgentBridge/Docs/editor_screenshot_evidence_workflow.md`

Step 1：新增 `run_boardgame_playable_demo.py` 作为 Phase 6 playable runtime 主入口。  
Step 2：将截图脚本改成阶段无关命名并写入 `ProjectState/Evidence/Phase6/`。  
Step 3：保留 Phase 5 历史脚本，但不再作为 Phase 6 默认入口。  

【验收标准】
- `E2E-24`：`python Scripts/run_boardgame_playable_demo.py` simulated 可跑通
- `E2E-27`：真实 UE5 截图证据链可写入 `ProjectState/Evidence/Phase6/`

【证据要求】
- `ProjectState/Evidence/Phase6/screenshots/`
- `ProjectState/Evidence/Phase6/logs/`
- `ProjectState/Evidence/Phase6/notes/`

## TASK 08：完成 Phase 6 测试与当前验证记录

目标：把本期测试只维护在本文件，并完成本地验证。  
前置依赖：TASK 07 完成

先读这些文件：
- [task2_phase4.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task2_phase4.md)
- [task3_phase5.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task3_phase5.md)

涉及文件：
- `Plugins/AgentBridge/Tests/scripts/test_phase6_playable_runtime.py`
- `ProjectState/Reports/`

Step 1：补齐 Phase 6 pytest。  
Step 2：回归 Phase 4 / Phase 5 pytest。  
Step 3：跑 schema 校验、Greenfield/Brownfield/playable demo 的 simulated 闭环。  
Step 4：把结果写进 `ProjectState/Reports/`。  

【验收标准】
- `SS-08~SS-13` 全部通过
- `CP-25~CP-31` 全部通过
- `E2E-22`：`run_greenfield_demo.py` simulated 成功
- `E2E-23`：`run_brownfield_demo.py` simulated 成功
- `E2E-24`：`run_boardgame_playable_demo.py` simulated 成功

【证据要求】
- `ProjectState/Reports/` 下保存 Phase 6 当前验证记录

## 当前阶段测试清单（仅本期维护）

### SS

- `SS-08`：_core registry 能发现 `genre-boardgame`
- `SS-09`：boardgame manifest 覆盖完整 Phase 6 字段
- `SS-10`：3 个 required skills 可加载
- `SS-11`：review / validation / delta policy 模块可加载
- `SS-12`：Genre contracts 已登记到 contract registry
- `SS-13`：Common + Genre contract bundle 均可加载

### CP

- `CP-25`：默认 `preview_static` 已生成完整 10 节点 Spec Tree
- `CP-26`：`runtime_playable` 生成 runtime actor 投影与 runtime config
- `CP-27`：runtime actor 需要的最小 callable 接口已落地
- `CP-28`：缺失 `turn_flow_spec / decision_ui_spec / runtime_wiring_spec` 时 reviewer 阻断
- `CP-29`：Brownfield turn/ui patch 缺少 genre contract 时 reviewer 阻断
- `CP-30`：delta policy 能影响 Brownfield delta trace 与 regression focus
- `CP-31`：合同 registry 中 Common + Genre 路径均可读取

### E2E

- `E2E-22`：`python Scripts/run_greenfield_demo.py`
- `E2E-23`：`python Scripts/run_brownfield_demo.py`
- `E2E-24`：`python Scripts/run_boardgame_playable_demo.py`
- `E2E-25`：真实 UE5 Editor 中成功生成 `BoardRuntimeActor`
- `E2E-26`：自动落子序列后 `GetBoardRuntimeState()` 返回终局结果
- `E2E-27`：真实截图证据写入 `ProjectState/Evidence/Phase6/`
