# 项目基线

> 文档版本：L1-Phase6-v1
> 基线状态：Phase 5 已归档，Phase 6 已进入 Genre Skill Packs 完整化阶段

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

### Greenfield / Brownfield 当前基线（Phase 5 已闭环）

- `project_state_intake.py` 已支持真实 Bridge 查询结构，并保留 mock fallback
- `Scripts/compiler/analysis/`
  - `baseline_builder.py`
  - `delta_scope_analyzer.py`
  - `contract_registry_loader.py`
- `Specs/Contracts/` 已具备 registry + 3 类 Common Contract Model
- `spec_generation_dispatcher.py` 已支持 Brownfield delta tree 生成
- `handoff_builder.py` 已能输出 `baseline_context` / `delta_context` / `tree_type=delta`
- `Scripts/run_brownfield_demo.py` 已提供 append/new-actor 的最小 Brownfield 样板入口
- 真机 `bridge_rc_api` + 场景截图证据链已验证通过

### Phase 6 当前起点（Genre Skill Packs 完整化前夜）

- `Plugins/AgentBridge/Skills/genre_packs/_core/README.md` 仍是占位，尚未落地 manifest loader / router base / registry
- `Plugins/AgentBridge/Skills/genre_packs/boardgame/pack_manifest.yaml` 已存在，但 `required_skills / review_extensions / validation_extensions / delta_policy` 仍是最小声明
- `Plugins/AgentBridge/Specs/Contracts/Genres/` 还没有真正的 boardgame genre contract
- `StaticBase + Brownfield delta` 已具备下阶段接入 Genre Pack 的基础编译面

### 项目层结构事实

- `ProjectInputs/GDD/`：设计输入
- `ProjectInputs/Baselines/`：人工或冻结 baseline 输入（可选）
- `ProjectState/Handoffs/`：Reviewed Handoff 实例
- `ProjectState/Reports/`：编译、执行、验收报告
- `ProjectState/Snapshots/`：baseline / state snapshot
- `ProjectState/Evidence/Phase6/`：当前阶段截图、日志、说明
- `Docs/History/reports/AgentBridgeEvidence/phase5_evidence_2026-04-01/`：Phase 5 已归档证据

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
- `python Scripts/run_greenfield_demo.py bridge_rc_api`

## 当前限制

- Phase 5 已验证的 Brownfield 当前只真正支持 `append/new-actor` 执行闭环
- `patch / replace / migrate` 目前只做到识别、Contract 约束和阻断
- Phase 6 当前尚未落地 `_core` 类型包机制，也未完整化 boardgame required_skills
- 后续若 Phase 6 需要真实截图证据，应写入 `ProjectState/Evidence/Phase6/`
