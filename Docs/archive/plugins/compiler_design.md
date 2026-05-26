# Skill Compiler Plane 设计

> 文档版本：v1.0.0（Phase 11 已完成）

## 1. 定位

Skill Compiler Plane 位于设计输入与执行编排之间，负责把 GDD 编译为 **Reviewed Handoff v3**。

Phase 11 中，Compiler 已从早期“翻译式 Spec 生成器”升级为 **Skill-First Design Compiler**。当前主链由 7 个阶段组成：

1. Root Skill Contract
2. Clarification Gate
3. Skill Graph Planning
4. Domain Skill Runtime
5. Cross Review v2
6. Lowering / Build IR v2
7. Handoff Assembly / Reviewed Handoff v3

对应的框架级规范见：

- `root_skill_contract_standard.md`
- `clarification_gate_rules.md`
- `skill_graph_and_domain_skill.md`
- `design_space_discovery.md`
- `agent_interaction_protocol.md`
- `constraint_variant_policy.md`
- `run_isolation_compare_promote.md`

## 2. 当前主链结构

### 2.1 Phase 11 当前主链（7 阶段）

```text
GDD
→ Stage 1: Root Skill Contract
→ Stage 2: Clarification Gate
→ Stage 3: Skill Graph Planning
→ Stage 4: Domain Skill Runtime
  → Design Space Discovery
  → Realization Candidates
  → Convergence
  → Skill Fragment Generation
→ Stage 5: Cross Review v2
→ Stage 6: Lowering → Build IR v2
  → naming_resolution_log
→ Stage 7: Handoff Assembly → Reviewed Handoff v3
```

Stage 1-3 由 MCP 前端认知桥接层承接交互，Stage 4-7 由 Compiler Core 调度。

### 2.2 当前模块落位

```text
Compiler/
├── pipeline/
│   ├── session.py                 ← Session v2 / run_id / fast_mode / generator_provider
│   └── pipeline_orchestrator.py   ← Stage 路由、产物落盘、schema 校验
├── stages/
│   ├── root_skill_contract.py     ← Stage 1
│   ├── clarification_gate.py      ← Stage 2
│   ├── skill_graph_planning.py    ← Stage 3
│   ├── domain_skill_runtime.py    ← Stage 4 主运行时
│   ├── agent_protocol.py          ← Stage 4 MCP Agent 交互协议实现
│   ├── llm_client.py              ← Stage 4 LLM Internal provider 封装
│   ├── discovery_fallback.py      ← Stage 4 fallback：Discovery
│   ├── realization_fallback.py    ← Stage 4 fallback：Candidates
│   ├── convergence_fallback.py    ← Stage 4 fallback：Convergence
│   ├── cross_review_v2.py         ← Stage 5
│   ├── lowering_v2.py             ← Stage 6
│   └── handoff_v3.py              ← Stage 7
├── intake/
├── planner/
├── skill_runtime/
├── cross_review/
└── lowering/
```

`intake/`、`planner/`、`skill_runtime/`、`cross_review/`、`lowering/` 这些目录仍保留，用于旧链路兼容和历史回归；当前 Phase 11 正式主链以 `pipeline/ + stages/` 为准。

### 2.3 MCP 认知桥接层边界

当前 MCP 的职责边界如下：

- 前端（Stage 1-3）
  - `compiler_create_session`
  - `compiler_root_skill_prepare/save`
  - `compiler_clarification_prepare/save`
  - `compiler_skill_graph_prepare/save`
- Stage 4-7
  - 由 `pipeline_orchestrator.py` 调度
  - Stage 4 支持 MCP Agent / LLM Internal / Heuristic Fallback 三路生成
  - 不通过 MCP 暴露“直接执行 Stage 5-7”的外部写工具
- 中段 Bridge Passthrough
  - 保留为可选外部协议适配层
  - 当前 MCP 工具总数为 `53 = 49 正式 + 4 alias`
- 后端
  - 负责证据判读与 Run 治理（compare / promote / batch）

## 3. 当前输入模式

### 3.1 Greenfield

当前 Greenfield 主线通过 Session v2 + Pipeline Orchestrator 进入 Stage 1-7 统一链路：

```text
GDD
→ CompilerSession(session_version=2.0)
→ pipeline_orchestrator.py
→ Stage 1-7
→ ProjectState/runs/{run_id}/reviewed_handoff_v3.json
```

### 3.2 Brownfield

Brownfield 在 Phase 11 中不再拥有独立的“另一条主链”，而是共享同一套 Stage 1-7 框架；差异主要体现在：

- 输入中是否带入现有项目基线和上下文
- Root Skill Contract / Clarification Gate 如何界定本轮增量范围
- Lowering 和 Execution 阶段如何消费已有工程状态

也就是说，**Greenfield / Brownfield 的差异体现在输入约束与实施边界，不体现在另起一套 Compiler Core**。

## 4. 当前主产物

Phase 11 当前主产物固定写入 `ProjectState/runs/{run_id}/`：

- `metadata.json`
- `root_skill_contract.json`
- `clarification_gate_report.json`
- `skill_graph.json`
- `design_space_report.json`
- `realization_candidates.json`
- `converged_realization_pack.json`
- `skill_fragments/*.json`
- `cross_review_report.json`（schema 为 `cross_review_report_v2.schema.json`）
- `build_ir.json`（schema 为 `build_ir_v2.schema.json`）
- `naming_resolution_log.json`
- `reviewed_handoff_v3.json`

这些产物与以下 schema 对齐：

- `root_skill_contract.schema.json`
- `clarification_gate_report.schema.json`
- `skill_graph.schema.json`
- `design_space_report.schema.json`
- `realization_candidates.schema.json`
- `converged_realization_pack.schema.json`
- `skill_fragment_v2.schema.json`
- `cross_review_report_v2.schema.json`
- `build_ir_v2.schema.json`
- `naming_resolution_log.schema.json`
- `reviewed_handoff_v3.schema.json`

## 5. 当前入口

当前项目的正式入口不再是 Phase 8 的 demo 脚本，而是以下几类入口：

- MCP 入口
  - `Plugins/AgentBridge/MCP/compiler_tools.py`
  - `Plugins/AgentBridge/MCP/server.py`
  - `Plugins/AgentBridge/MCP/tool_definitions.py`
- 本地编排入口
  - `Plugins/AgentBridge/Scripts/compiler_main.py`
- 系统与任务验证入口
  - `Plugins/AgentBridge/Tests/run_system_tests.py`
  - `Plugins/AgentBridge/Tests/scripts/task11_phase11_mcp_e2e.py`
  - `Plugins/AgentBridge/Tests/scripts/task12_phase11_run_governance_validation.py`
  - `Plugins/AgentBridge/Tests/scripts/task13_phase11_fast_mode_validation.py`
  - `Plugins/AgentBridge/Tests/scripts/task14_phase11_baseline_template_validation.py`

根目录 `Scripts/run_greenfield_demo.py`、`Scripts/run_brownfield_demo.py` 等脚本仍可用于历史回归或旧链路说明，但不再代表 Phase 11 主开发入口。

## 6. 历史链路保留

### 6.1 Phase 8 历史主链快照

Phase 8 引入过 Skill-First 6 阶段链路：

```text
design_intake
→ planner
→ skill_runtime
→ cross_review
→ lowering
→ reviewed_handoff_v2
```

这条链路对理解演进历史仍有价值，但**不再是当前推荐主链**。

### 6.2 v0.5.0-v0.7.0 旧链路

更早阶段的旧链路仍保留用于 boardgame / JRPG 历史回归：

```text
Scripts/compiler/
  intake → routing → analysis → generation → review → handoff
```

该链路属于历史兼容资产，不承担 Phase 11 当前事实说明职责。

## 7. 当前边界

当前文档需要明确以下边界：

- Compiler 的正式边界是 `reviewed_handoff_v3.json`，不负责后续 UE 真机执行结果本身
- MCP 前端止于 Stage 1-3；Stage 4-7 由 Compiler Core 调度
- `fast_mode` 是显式降级策略，不是主路径失败后的静默替代
- Stage 4 三路生成中，Heuristic Fallback 属于退化路径，不代表默认创造性实现
- Greenfield 是当前验证主线；旧 demo 脚本与旧 Handoff / Run Plan 链路仅保留为历史回归与兼容说明
