# 项目基线

> 文档版本：L1-Phase5-v2
> 基线状态：Phase 4 已闭环，Phase 5 已进入 Brownfield 主线实现

## 已实装能力

### 插件核心（Phase 1-2 稳定）

- AgentBridge C++ Editor Plugin（UEditorSubsystem）
- Bridge 三通道：Python / Remote Control API / C++ Plugin
- L1/L2/L3 受控工具体系
- Automation Test / Automation Spec / Functional Testing / Gauntlet

### Greenfield 主线（Phase 3-4 已闭环）

- `design_input_intake.py` 已能解析 boardgame GDD
- `StaticBase` registry + 10 个静态基座已落地
- `spec_generation_dispatcher.py` / `boardgame_scene_generator.py` 已能生成 richer `dynamic_spec_tree`
- `cross_spec_reviewer.py` 已做静态审查
- `Scripts/run_greenfield_demo.py` 已支持 `simulated / bridge_python / bridge_rc_api`

### Brownfield 当前起点（Phase 5 已落地的第一批能力）

- `project_state_intake.py` 已支持真实 Bridge 查询结构，并保留 mock fallback
- `Scripts/compiler/analysis/`
  - `baseline_builder.py`
  - `delta_scope_analyzer.py`
  - `contract_registry_loader.py`
- `Specs/Contracts/` 已具备 registry + 3 类 Common Contract Model
- `spec_generation_dispatcher.py` 已支持 Brownfield delta tree 生成
- `handoff_builder.py` 已能输出 `baseline_context` / `delta_context` / `tree_type=delta`
- `Scripts/run_brownfield_demo.py` 已提供 append/new-actor 的最小 Brownfield 样板入口

### 项目层结构事实

- `ProjectInputs/GDD/`：设计输入
- `ProjectInputs/Baselines/`：人工或冻结 baseline 输入（可选）
- `ProjectState/Handoffs/`：Reviewed Handoff 实例
- `ProjectState/Reports/`：编译、执行、验收报告
- `ProjectState/Snapshots/`：baseline / state snapshot
- `ProjectState/Evidence/Phase5/`：当前阶段截图、日志、说明

## 当前架构状态

```text
Design Inputs + Existing Project State
→ Static Spec Base / Contracts
→ Skill Compiler Plane
→ Dynamic / Delta Spec Tree
→ Reviewed Handoff
→ Run Plan
→ Handoff Runner
→ Bridge
→ UE5
→ Report / Evidence
```

## 已验证闭环

- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
- `pytest Plugins/AgentBridge/Tests/scripts/test_phase4_compiler.py`
- `python Scripts/run_greenfield_demo.py`
- `python Scripts/run_greenfield_demo.py bridge_rc_api`
- `pytest Plugins/AgentBridge/Tests/scripts/test_phase5_brownfield.py`
- `python Scripts/run_brownfield_demo.py`

## 当前限制

- Phase 5 当前只真正支持 `append/new-actor` 的 Brownfield 执行闭环
- `patch / replace / migrate` 目前只做到识别、Contract 约束和阻断
- Phase 5 测试用例尚未并入 `SystemTestCases.md`，将等阶段归档时统一补录
- 截图证据需要真实 UE5 Editor 运行态；simulated 模式不会产出真实场景截图
