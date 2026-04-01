# 项目基线

> 文档版本：L1-Phase6-v2
> 基线状态：Phase 5 已归档，Phase 6 已进入“完整 Spec Tree + 可玩 Runtime”阶段

## 已实装能力

### 插件核心（Phase 1-2 稳定）

- AgentBridge C++ Editor Plugin（UEditorSubsystem）
- Bridge 三通道：Python / Remote Control API / C++ Plugin
- L1/L2/L3 受控工具体系
- Automation Test / Automation Spec / Functional Testing / Gauntlet

### Greenfield / Brownfield 已闭环基线（Phase 3-5）

- `design_input_intake.py` 已能解析 boardgame GDD
- `StaticBase` registry + 10 个静态基座已落地
- `project_state_intake.py` / `baseline_builder.py` / `delta_scope_analyzer.py` 已支撑 Brownfield 最小闭环
- `Specs/Contracts/` 已具备 Common Contract registry 与 3 类 Common Contract Model
- `Scripts/run_greenfield_demo.py` 与 `Scripts/run_brownfield_demo.py` 已支持 simulated 最小闭环

### Phase 6 当前起点已经落地的能力

- `Skills/genre_packs/_core/` 已有：
  - `manifest_loader.py`
  - `registry.py`
  - `router_base.py`
  - `module_loader.py`
- `Skills/genre_packs/boardgame/` 已有：
  - 完整 `pack_manifest.yaml`
  - `required_skills/board_layout.py`
  - `required_skills/piece_movement.py`
  - `required_skills/turn_system.py`
  - `review_extensions/boardgame_reviewer.py`
  - `validation_extensions/boardgame_validator.py`
  - `delta_policy/boardgame_delta_policy.py`
- `dynamic_spec_tree` 当前可生成 10 个关键节点：
  - `world_build_spec`
  - `boardgame_spec`
  - `board_layout_spec`
  - `piece_movement_spec`
  - `turn_flow_spec`
  - `decision_ui_spec`
  - `runtime_wiring_spec`
  - `validation_spec`
  - `scene_spec`
  - `generation_trace`
- 项目层 `Source/Mvpv4TestCodex/BoardgamePrototypeBoardActor.*` 已提供最小 runtime actor
- `ProjectState/RuntimeConfigs/` 已作为 runtime config 输出目录接入 handoff
- `Scripts/run_boardgame_playable_demo.py` 已作为 Phase 6 playable runtime 主入口
- `Scripts/validation/capture_editor_evidence.py` 已作为阶段无关截图脚本接入

## 当前架构状态

```text
Design Inputs + Existing Project State
→ Static Spec Base / Contracts / Genre Pack Core
→ Required Skills / Review Extensions / Validation Extensions / Delta Policy
→ Dynamic / Delta Spec Tree
→ Reviewed Handoff
→ Run Plan
→ Handoff Runner
→ Bridge
→ UE5
→ Report / Runtime Config / Evidence
```

## 当前已验证的本地链路

- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
- `pytest Plugins/AgentBridge/Tests/scripts/test_phase4_compiler.py`
- `pytest Plugins/AgentBridge/Tests/scripts/test_phase5_brownfield.py`
- `pytest Plugins/AgentBridge/Tests/scripts/test_phase6_playable_runtime.py`
- `python Scripts/run_greenfield_demo.py`
- `python Scripts/run_brownfield_demo.py`
- `python Scripts/run_boardgame_playable_demo.py`
- UBT 编译 `Mvpv4TestCodexEditor` 通过

## 当前限制

- `runtime_playable` 目前只针对井字棋样板，不泛化到所有 boardgame
- `patch / replace / migrate` 仍然只做到表达、校验与阻断
- Phase 6 当前尚未完成真实 UE5 playable smoke 与 Phase 6 截图证据
