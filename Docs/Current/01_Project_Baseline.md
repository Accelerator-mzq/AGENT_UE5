# 项目基线

> 文档版本：L1-Phase7Prep-v1  
> 基线状态：Phase 6 已归档，当前处于 Phase 7 准备期

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

### Phase 6 已归档基线

- `_core + boardgame pack` 已接入 Compiler 主链
- `dynamic_spec_tree` 已稳定生成 10 个关键节点
- 项目层 `BoardgamePrototypeBoardActor.*` 已提供最小 runtime actor
- `runtime_playable` handoff 已接入 `ProjectState/RuntimeConfigs/`
- `Scripts/run_boardgame_playable_demo.py` 已作为 playable runtime 主入口
- `Scripts/validation/capture_editor_evidence.py` 已作为阶段无关截图脚本接入
- `Phase 6` 真实 `bridge_rc_api` playable smoke、自动落子读回、截图证据与顶视图规则已完成闭环

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
- `Phase 6` 真机验收与截图证据已归档，见
  [phase6_runtime_acceptance_20260402_025815.json](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/phase6_runtime_acceptance_20260402_025815.json)

## 当前限制

- `runtime_playable` 仍然是井字棋样板实现，不等于通用 boardgame runtime
- `patch / replace / migrate` 仍然只做到表达、校验与阻断
- Brownfield 的 runtime / turn/ui patch 仍未自动执行
- 下一阶段功能范围尚未冻结，当前只允许继续做基线整理、稳定性观察与任务立项
