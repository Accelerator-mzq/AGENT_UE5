# LLD/04 — Compiler 子系统详细设计

> 版本: v1 (2026-05-26)
> 范围: Legacy v1 Pipeline(`Plugins/AgentBridge/Scripts/compiler/`,6 子目录)+ Phase 11 Compiler Framework(`Plugins/AgentBridge/Compiler/`,pipeline + 12 stages + v1 framework 残留)共 ~30 个 Python 模块
> 上游: `Docs/design/HLD.md` §2 + `Docs/requirements/SRS.md` §3.4 + `Docs/FEATURE_INVENTORY.md` F-CMP-01..24
> 契约: `Docs/contracts/schemas_catalog.md`(主链 v3 9 Schema + v1/v2 兼容)+ `Docs/contracts/tool_contract.md` §2(L1/L2/L3 协议)
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

Compiler 子系统是 AgentBridge "Skill-First Design Compiler" 的编译前端,职责是把游戏设计文档(GDD / 项目状态)逐阶段下降为执行域可消费的 Reviewed Handoff,也是整个 AgentBridge 框架"从自然语言设计意图到可执行编排"这条主路径的左半段。代码层分两代并存:**Legacy v1 Pipeline** 位于 `Scripts/compiler/`,是 Phase 8/9 时代的 5 阶段定制管线(analysis / generation / handoff / intake / review / routing 六子目录,对应 F-CMP-01..06),按 Greenfield/Brownfield/Playable 模式分发场景生成器、走 design_input → planner → skill_runtime → cross_review → lowering 五段定制处理;**Phase 11 Compiler Framework** 位于 `Plugins/AgentBridge/Compiler/`,以 `pipeline_orchestrator` 为顶层入口(F-CMP-07),驱动 12 个 Stage 模块(F-CMP-08..19)实现新主链 7 阶段(Root Skill Contract → Clarification Gate → Skill Graph Planning → Domain Skill Runtime → Cross Review v2 → Lowering v2 → Handoff v3)。同目录下 `cross_review/` `intake/` `lowering/` `planner/` `skill_runtime/` 五个子目录是 v1 五阶段的 framework 残留(F-CMP-20..24),由 `STAGE_NAME_MAP_V1` 调度保持向后兼容,Phase 11 新链路不直接调用,新功能一律往 Phase 11 framework 加。两代版本的路由由 `CompilerSession.session_version`(`"1.0"` / `"2.0"`)在 pipeline_orchestrator 内 `_get_session_version` 决定,**不可中途切换**;`__post_init__` 调 `_normalize_session_version` 在创建期锁定该字段,改 session.json 强切版本会让下游 Stage schema 校验立即崩。当前生产链路全部走 Phase 11 主链,合计 ~30 个 Python 文件;本 LLD 聚焦内部分层、关键函数签名、数据流与状态机、扩展点、已知约束与 UE 5.7 迁移变更点,目标是让接手者无需通读全部源码就能精准定位修改点与评估迁移成本。

## 2. 内部分层

### 2.1 Phase 11 Compiler Framework(主链,F-CMP-07..19)

| Stage / 模块 | 文件 | F-CMP ID | 角色一句话 |
|---|---|---|---|
| Pipeline Orchestrator | `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py` | F-CMP-07 | 顶层入口,v1/v2 双路由 + schema 校验 + Handoff 组装 |
| Session 状态 | `Plugins/AgentBridge/Compiler/pipeline/session.py` | F-CMP-07 | CompilerSession 数据类 + is_promotable 治理判定 |
| Stage 1 Root Skill Contract | `Plugins/AgentBridge/Compiler/stages/root_skill_contract.py` | F-CMP-08 | GDD → Root Skill Contract(约束/变体/能力声明) |
| Stage 2 Clarification Gate | `Plugins/AgentBridge/Compiler/stages/clarification_gate.py` | F-CMP-09 | 用户必填项澄清门 + provisional/blocking 项 |
| Stage 3 Skill Graph Planning | `Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py` | F-CMP-10 | Skill Graph 节点 + 边构造 + gameplay/baseline 分类 |
| Stage 4 路 A Discovery Fallback | `Plugins/AgentBridge/Compiler/stages/discovery_fallback.py` | F-CMP-11 | Discovery 启发式 fallback,产 design_space_report |
| Stage 4 路 B Realization Fallback | `Plugins/AgentBridge/Compiler/stages/realization_fallback.py` | F-CMP-12 | Candidates 启发式 fallback,产 realization_candidates |
| Stage 4 路 C Convergence Fallback | `Plugins/AgentBridge/Compiler/stages/convergence_fallback.py` | F-CMP-13 | Convergence 启发式 fallback,产 converged_realization_pack |
| Stage 通用 Agent Protocol | `Plugins/AgentBridge/Compiler/stages/agent_protocol.py` | F-CMP-14 | Provider 抽象(MCP/LLM/Heuristic 三路)+ phase trace |
| Stage 通用 LLM Provider Framework | `Plugins/AgentBridge/Compiler/providers/{base,_retry,_retry_async,litellm_adapter,capability_router,model_registry,fake_adapter}.py` + `observability/{secrets,compactor}.py` + `runtime/budget_tracker.py` + `stages/candidates_batch_orchestrator.py` | F-CMP-15 | LiteLLM + Instructor 统一接入 + capability 路由 + observe-only budget + Stage 4 Candidates 分批(Phase 12 重开,旧 `llm_client.py` 已 deprecate)|
| Stage 7 Handoff v3 | `Plugins/AgentBridge/Compiler/stages/handoff_v3.py` | F-CMP-16 | Stage 1-6 全产物 → Reviewed Handoff v3 组装 |
| Stage 5 Cross Review v2 | `Plugins/AgentBridge/Compiler/stages/cross_review_v2.py` | F-CMP-17 | 5 维跨域审查(约束/Blueprint/baseline/playability/scope)|
| Stage 6 Lowering v2 | `Plugins/AgentBridge/Compiler/stages/lowering_v2.py` | F-CMP-18 | Spec Tree → Build IR v2 + naming_resolution_log sidecar |
| Stage 4 Domain Skill Runtime | `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py` | F-CMP-19 | Stage 4 主体:Discovery+Candidates+Convergence 三 phase 编排 |

12 Stage 模块按职责分四类:**契约层** Stage 1/2(F-CMP-08/09)生成根契约与澄清门;**规划层** Stage 3(F-CMP-10)生成 Skill Graph;**领域层** Stage 4(F-CMP-19)三 phase 编排 + 三 fallback(F-CMP-11/12/13);**收尾层** Stage 5/6/7(F-CMP-17/18/16)审查 + 下降 + 组装。Stage 通用支撑(F-CMP-14/15)横切所有 Stage。

### 2.1.1 Phase 12 LLM Provider Framework 内部架构

T08-T18 期间 LLM 内部子树重组,见 §2.1 F-CMP-15 行已经更新。子目录职责:

- `Compiler/providers/`:LLM 抽象 + 路由 + adapter
  - `base.py` — `ProviderAdapter` ABC + 4 类异常 + `ProviderCall/Result`
  - `_retry.py` + `_retry_async.py` — transient 错误重试工具
  - `litellm_adapter.py` — LiteLLM + Instructor 默认实现(支持 prompt cache + auto-compact)
  - `capability_router.py` — 按 ProviderPolicy 路由(本期单 model,中期扩多 model fallback)
  - `model_registry.py` — `build_default_router` 工厂(读 `Config/llm_config.yaml`)
  - `fake_adapter.py` — offline 单测桩(L2-A/B/C 测试用)
- `Compiler/observability/`:LLM 横切支撑
  - `secrets.py` — `redact_mapping` / `redact_text`(api_key/Bearer/JWT 脱敏)
  - `compactor.py` — 超长消息历史 `compact_messages`(4 char/token 估算)
- `Compiler/runtime/`:run-level 资源跟踪
  - `budget_tracker.py` — Per-Run cost/usage 累计(本期 observe-only,中期扩软阈值)
- `Compiler/stages/candidates_batch_orchestrator.py`:Stage 4 Candidates 分批执行器
  - `LLMBatchExecutor.run_candidates_batch()` async 入口,7 dim 并发 + retry + 聚合
  - 7 个 batch 完成后聚合为 `AggregatedReport(promotable,partial,per_dimension)`

完整 spec:[Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/specs/2026-05-27-llm-internal-reopen-design.md)。
完整 plan:[Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/superpowers/plans/2026-05-27-llm-internal-reopen.md)。
真 LLM 验收 7/7:[ProjectState/Reports/2026-05-27/llm_internal_reopen_acceptance.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-05-27/llm_internal_reopen_acceptance.md)。

### 2.2 Legacy v1 Pipeline(F-CMP-01..06 + framework 残留 F-CMP-20..24)

| 子目录 | 主要模块 | F-CMP ID |
|---|---|---|
| `Scripts/compiler/analysis/` | `baseline_builder.py` / `contract_registry_loader.py` / `delta_scope_analyzer.py` | F-CMP-01 |
| `Scripts/compiler/generation/` | `boardgame_scene_generator.py` / `brownfield_delta_generator.py` / `jrpg_scene_generator.py` / `spec_generation_dispatcher.py` / `static_base_loader.py` | F-CMP-02 |
| `Scripts/compiler/handoff/` | `handoff_builder.py` / `handoff_serializer.py` | F-CMP-03 |
| `Scripts/compiler/intake/` | `design_input_intake.py` / `project_state_intake.py` | F-CMP-04 |
| `Scripts/compiler/review/` | `cross_spec_reviewer.py` | F-CMP-05 |
| `Scripts/compiler/routing/` | `mode_router.py` | F-CMP-06 |
| `Compiler/intake/`(framework 残留) | `design_intake.py` | F-CMP-21 |
| `Compiler/planner/`(framework 残留) | `planner.py` | F-CMP-23 |
| `Compiler/skill_runtime/`(framework 残留) | `skill_runtime.py` | F-CMP-24 |
| `Compiler/cross_review/`(framework 残留) | `cross_review.py` | F-CMP-20 |
| `Compiler/lowering/`(framework 残留) | `lowering.py` | F-CMP-22 |

> v1 由 `pipeline_orchestrator.STAGE_NAME_MAP_V1` 调度(`design_intake → planner → skill_runtime → cross_review → lowering` 5 阶段),Phase 11 新链路不直接调用。`Scripts/compiler/` 下六子目录是 Phase 8 之前的"定制场景生成"模块,被 Phase 9/10 部分挪到 `Compiler/` 后留作 Greenfield/Brownfield/Playable 三模式分发的实现细节,**新功能不应往 Scripts/compiler/ 加**。

## 3. 关键类/函数签名

> 仅列与外部协议、Stage 路由、Provider 调度、Schema 校验、治理判定强相关的函数,**不 dump 整文件**;完整方法表参见各 `.py` 文件 `^def ` 抓取。签名后 1 行中文用途(<=20 字)。

### 3.1 Pipeline / Session(F-CMP-07)

```python
# pipeline_orchestrator.py
STAGE_NAME_MAP_V1 = {1:"design_intake", 2:"planner", 3:"skill_runtime", 4:"cross_review", 5:"lowering"}  # v1 五阶段表
STAGE_NAME_MAP_V2 = {1:"root_skill_contract", 2:"clarification_gate", 3:"skill_graph_planning", 4:"domain_skill_runtime", 5:"cross_domain_review", 6:"lowering", 7:"handoff_assembly"}  # v2 七阶段表
def prepare_stage(session: CompilerSession, stage_num: int) -> Dict[str, Any]  # 按 version 路由的 prepare 入口
def save_stage(session: CompilerSession, stage_num: int, filled_data: Any) -> Dict[str, Any]  # 校验+保存+session 推进
def run_stage(session: CompilerSession, stage_num: int) -> Dict[str, Any]  # 单 stage prepare 调度
def run_pipeline(session: CompilerSession, stage_range: Iterable[int] | None = None) -> Dict[str, Any]  # 多 stage 串行 prepare
def assemble_handoff(session: CompilerSession) -> Dict[str, Any]  # v1→v2 / v2→v3 双轨组装入口
def _get_session_version(session: CompilerSession) -> str  # v1.0 / v2.0 路由决策点
def get_stage_name_map(session: CompilerSession) -> Dict[int, str]  # 按 version 返回 STAGE_NAME_MAP_V1/V2
def build_run_metadata(session, clarification_gate_report=None, cross_review_report=None, completed_at=None) -> Dict[str, Any]  # 治理元数据组装

# session.py
class CompilerSession:  # @dataclass; session_id/run_id/gdd_path/target_phase/output_dir/current_stage/stage_outputs/status/session_version/fast_mode/generator_provider
    @property
    def is_promotable(self) -> bool  # fast_mode 或 heuristic_fallback 都不可 promote(F-GOV-02/03)
    def get_stage_output_path(self, stage_num: int) -> str | None  # 取已登记产物路径
    def has_stage_output(self, stage_num: int) -> bool  # 路径登记且文件真实存在
    def advance_stage(self) -> bool  # 当前阶段产物存在时推进 current_stage
def create_session(gdd_path, target_phase, output_dir, session_version="2.0", run_id=None, fast_mode=False) -> CompilerSession  # 新建会话
def get_max_stage(session_version: Optional[str] = None) -> int  # session.py:67;v1 → 5,v2 → 7
# 注:pipeline_orchestrator.py:274 有同名 wrapper get_max_stage(session) 接 session 对象,grep 命中 2 处
```

### 3.2 Phase 11 七主链 Stage 主入口(F-CMP-08/09/10/19/17/18/16)

```python
# Stage 1: root_skill_contract.py  (F-CMP-08)
def create_root_skill_contract(gdd_path: str, target_phase: str, run_id: str | None = None) -> Dict[str, Any]  # GDD → 根契约
def save_root_skill_contract(contract: Dict[str, Any], output_path: str | Path) -> str  # 落盘 JSON

# Stage 2: clarification_gate.py  (F-CMP-09)
def create_clarification_gate_report(root_skill_contract: Dict[str, Any], fast_mode: bool = False, run_id: str | None = None) -> Dict[str, Any]  # 澄清门 + provisional/blocking
def save_clarification_gate_report(report: Dict[str, Any], output_path: str | Path) -> str  # 落盘

# Stage 3: skill_graph_planning.py  (F-CMP-10)
def create_skill_graph(root_skill_contract, clarification_gate_report, run_id=None) -> Dict[str, Any]  # 构造 SkillGraph 节点 + 边
def save_skill_graph(skill_graph: Dict[str, Any], output_path: str | Path) -> str  # 落盘

# Stage 4: domain_skill_runtime.py  (F-CMP-19)
def run_domain_skill_runtime(skill_graph, root_skill_contract, clarification_gate_report, phase_scope: str, fast_mode: bool=False, allow_heuristic_fallback: bool=True, llm_client=None) -> Dict[str, Any]  # 三 phase 编排主入口
def prepare_node_phase(...) -> Dict[str, Any]  # 单节点单 phase 的 prepare(MCP 模式)
def save_node_phase(...) -> Dict[str, Any]  # 单节点单 phase 的 save
def _validate_stage4_node_acceptance(...) -> List[str]  # ≤2 轮质量重试 + ≤2 次 schema 修复约束

# Stage 5: cross_review_v2.py  (F-CMP-17)
def create_cross_review_report_v2(root_skill_contract, clarification_gate_report, skill_graph, stage4_output, phase_scope: str) -> Dict[str, Any]  # 5 维审查主入口
def check_constraint_preservation(root_skill_contract, fragments) -> Tuple[List[Dict], Dict]  # 约束保留检查
def check_blueprint_thin_layer(fragments) -> Tuple[List[Dict], Dict]  # BP 薄层检查
def check_baseline_completeness(root_skill_contract, fragments) -> Tuple[List[Dict], Dict]  # baseline 完备性
def check_minimum_playability_completeness(root_skill_contract, fragments) -> Tuple[List[Dict], Dict]  # 可玩性最低门槛
def check_cross_domain_conflicts(fragments) -> Tuple[List[Dict], Dict]  # 跨域冲突
def check_phase_scope(fragments, phase_scope) -> Tuple[List[Dict], Dict]  # phase 范围一致性

# Stage 6: lowering_v2.py  (F-CMP-18)
def create_build_ir_v2(cross_review_report, root_skill_contract, skill_graph, phase_scope: str) -> Dict[str, Any]  # Build IR + naming_resolution_log
def _generate_build_step(...) -> Dict[str, Any]  # 单 build_step 生成(写 naming_resolution_log 段,**不**写 __RUNTIME_CONFIG_REF__ 占位)
def _generate_validation_points(build_steps) -> List[Dict[str, Any]]  # validation_ir 生成

# Stage 7: handoff_v3.py  (F-CMP-16)
def assemble_handoff_v3(root_skill_contract, clarification_gate_report, skill_graph, stage4_output, cross_review_report, build_ir, naming_resolution_log, session_meta) -> Dict[str, Any]  # v3 组装
```

### 3.3 Stage 4 三 Fallback(F-CMP-11/12/13)

```python
# discovery_fallback.py  (F-CMP-11)
def create_design_space_report(skill_graph: Dict[str, Any], root_skill_contract: Dict[str, Any], clarification_gate_report: Dict[str, Any]) -> Dict[str, Any]  # 维度蓝图发现

# realization_fallback.py  (F-CMP-12)
def create_realization_candidates(design_space_report: Dict[str, Any], skill_graph: Dict[str, Any]) -> Dict[str, Any]  # 候选实现化

# convergence_fallback.py  (F-CMP-13)
def create_converged_realization_pack(realization_candidates, design_space_report, skill_graph, root_skill_contract, phase_scope: str) -> Dict[str, Any]  # 候选 → 收敛
```

### 3.4 Provider 体系(F-CMP-14/15)

```python
# agent_protocol.py  (F-CMP-14)
class GeneratorProvider(ABC)  # 抽象基类:generate(phase, context_bundle, traces) → Dict
class LLMProvider(GeneratorProvider)  # 走 LLM(OpenAI/Anthropic),is_promotable 兼容
class HeuristicFallbackProvider(GeneratorProvider)  # 走启发式,产 generator_provider_type="heuristic_fallback" → is_promotable=False
class ProviderNotAvailable(Exception)  # 探测失败异常(MCPAgentProvider 不可用时 fallback)
def build_context_bundle(...)  # 节点上下文打包
def create_trace(...)  # phase trace 创建
def validate_phase_output_for_acceptance(phase: str, output: Dict[str, Any]) -> List[str]  # phase 输出验收
def heuristic_evaluate_discovery / _candidates / _convergence(output, context) -> Dict[str, Any]  # 三 phase 启发式打分

# llm_client.py  (F-CMP-15)
class UnifiedLLMClient  # OpenAI/Anthropic 统一封装
def load_llm_client_from_config(config_path: str | Path | None = None) -> UnifiedLLMClient | None  # 配置驱动初始化
def _extract_openai_text(response: Any) -> str  # OpenAI 响应抽文
def _extract_anthropic_text(response: Any) -> str  # Anthropic 响应抽文
def _is_placeholder_api_key(provider: str, api_key: str) -> bool  # 占位 key 检测
```

### 3.5 Legacy v1 关键(F-CMP-01..06 + F-CMP-20..24)

```python
# Scripts/compiler/routing/mode_router.py  (F-CMP-06)
def determine_mode(config: Dict[str, Any], project_state: Dict[str, Any]) -> str  # Greenfield/Brownfield/Playable 决断
def resolve_mode(config: Dict[str, Any], project_state: Dict[str, Any]) -> Dict[str, Any]  # 模式 + 元数据解析
def auto_detect_mode(config, project_state) -> str  # 自动检测(无显式 config 时)

# Scripts/compiler/intake/design_input_intake.py  (F-CMP-04)
def read_gdd(gdd_path: str) -> Dict[str, Any]  # GDD 文件读取
def build_design_input(content: str, source_file: str) -> Dict[str, Any]  # 七段(party/combat/board/rules/layout/preview/tech)抽取
def extract_game_type / extract_party_setup / extract_combat_spec / extract_board_spec(content) -> ...  # 分段抽取器族

# Scripts/compiler/intake/project_state_intake.py  (F-CMP-04)
def get_project_state_snapshot(...) -> Dict[str, Any]  # 项目状态快照(走 bridge 或 mock fallback)
def check_baseline_exists(baseline_path: str) -> bool  # baseline 存在性

# Scripts/compiler/handoff/handoff_builder.py  (F-CMP-03)
def build_handoff(...) -> Dict[str, Any]  # design_input + dynamic_spec_tree → Reviewed Handoff
def build_minimal_spec_tree(design_input: Dict[str, Any], mode: str) -> Dict[str, Any]  # 最小 spec_tree 兜底

# Scripts/compiler/handoff/handoff_serializer.py  (F-CMP-03)
def serialize_handoff(...) -> str  # YAML/JSON 双格式落盘
def deserialize_handoff(handoff_path: str) -> Dict[str, Any]  # 读回

# Scripts/compiler/review/cross_spec_reviewer.py  (F-CMP-05)
def review_dynamic_spec_tree(...) -> Dict[str, Any]  # spec tree 跨规格审查(actors/transform/preview/brownfield)

# Scripts/compiler/analysis/baseline_builder.py  (F-CMP-01)
def build_baseline_snapshot(...) -> Dict[str, Any]  # baseline 快照构造
def save_baseline_snapshot(...) -> str  # 落盘 + manifest

# Scripts/compiler/generation/spec_generation_dispatcher.py  (F-CMP-02)
def load_skill_pack_manifest(...) -> Dict[str, Any]  # Skill Pack manifest 读取
def generate_dynamic_spec_tree(...) -> Dict[str, Any]  # 分发到 boardgame/jrpg/brownfield 生成器
```

## 4. 数据流与状态机

### 4.1 Phase 11 主链 7 阶段流程(F-CHN-01..07)

```
GDD (.md)
  └─ create_session(session_version="2.0", run_id=<auto>)
  └─ pipeline_orchestrator.run_pipeline(session, range(1,8))
     ├─ Stage 1: root_skill_contract.create_root_skill_contract
     │           → root_skill_contract.json (F-CMP-08)
     ├─ Stage 2: clarification_gate.create_clarification_gate_report
     │           → clarification_gate_report.json
     │           ├─ provisional_items[]   (F-GOV-01 影响 is_promotable)
     │           └─ blocking_items[]      (有 blocker → Stage 3 直接 blocked_by_clarification 返回)
     ├─ Stage 3: skill_graph_planning.create_skill_graph
     │           → skill_graph.json(nodes + edges,gameplay/baseline 二分)
     ├─ Stage 4: domain_skill_runtime.run_domain_skill_runtime
     │           (三 phase 各调一次 Provider,见 §4.2)
     │           → converged_realization_pack.json + design_space_report.json
     │             + realization_candidates.json + skill_fragments/*.json
     ├─ Stage 5: cross_review_v2.create_cross_review_report_v2
     │           (5 维 check_* → reviewed_dynamic_spec_tree)
     │           → cross_review_report.json
     ├─ Stage 6: lowering_v2.create_build_ir_v2
     │           (Build IR + naming_resolution_log sidecar)
     │           → build_ir.json + naming_resolution_log.json
     └─ Stage 7: assemble_handoff (= handoff_v3.assemble_handoff_v3)
                 → reviewed_handoff_v3.json (供 Orchestrator handoff_runner 消费)
```

每阶段保存后 `_update_session_after_save` 调 `session.advance_stage()` 推进 `current_stage`,Stage 7 完成后 `session.status = "completed"`。所有产物落 `ProjectState/runs/<run_id>/`(v2 固定路径,由 `_get_session_output_root` 拼出);v1 则保持原 `session.output_dir` 字段。各阶段产物文件名严格由 `STAGE_ARTIFACT_MAP_V2` 表驱动,**新增 Stage 必须同步该表否则 `_build_stage_output_path` 解析失败**。Stage 4 由于产物多(design_space_report / realization_candidates / converged_realization_pack / skill_fragments[*]),在 `STAGE_ARTIFACT_MAP_V2[4]` 下用 `output_files` 子表细分,Stage 6 用 `sidecar_files` 子表挂 naming_resolution_log;这两个子表是两种不同的"多产物"语义,前者代表"同阶段平级输出",后者代表"主产物 + 旁挂"。

### 4.2 Stage 4 三 Provider 三 Phase 编排(F-CMP-19 + F-CMP-11/12/13)

```
domain_skill_runtime.run_domain_skill_runtime
  └─ 对每个 skill_graph.node (按 _topological_execution_order):
     ├─ Phase: discovery
     │   ├─ 输入源探测(MCP sidecar 第一优先,Provider 二路兜底):
     │   │   ├─ MCP Agent 旁路输入(读 env MCP_NODE_STATE_PATH 文件;非 GeneratorProvider 子类)
     │   │   ├─ LLM Provider (UnifiedLLMClient,agent_protocol.LLMProvider)
     │   │   └─ Heuristic Fallback Provider → discovery_fallback.create_design_space_report
     │   ├─ ≤ 2 轮质量重试(_validate_stage4_node_acceptance)
     │   └─ ≤ 2 次 schema 修复
     ├─ Phase: candidates
     │   └─ 同上三路;heuristic → realization_fallback.create_realization_candidates
     ├─ Phase: convergence
     │   └─ 同上三路;heuristic → convergence_fallback.create_converged_realization_pack
     └─ 任一 phase 走 heuristic_fallback → session.generator_provider = "heuristic_fallback"
                                        → session.is_promotable = False (F-GOV-03)
```

> **三 fallback 文件 ↔ 三 Phase 是一一对应**(discovery↔discovery_fallback、candidates↔realization_fallback、convergence↔convergence_fallback);**MCP/LLM/Heuristic 三路输入** 与 phase 三路是**正交两个维度**(HLD §2.2 已澄清,易混点)。**术语澄清**:`agent_protocol.resolve_provider` 只实例化 2 个 `GeneratorProvider` 子类(`LLMProvider` / `HeuristicFallbackProvider`);MCP 不是 Provider 子类,而是 **sidecar 旁路输入**(读 `env MCP_NODE_STATE_PATH` 文件供 domain_skill_runtime 优先采纳)。`session.generator_provider` 字段枚举 `{"llm","mcp_agent","heuristic_fallback"}` 是**输入来源标签**而非 Provider 类实例化。

### 4.3 Session 生命周期 + is_promotable 治理

```
create_session(fast_mode=?, session_version="2.0")
  → session.status = "pending"
  → 每次 run_stage / save_stage:
       success → session.status = "running" / "pending"(等下一 stage)
       error   → session.status = "failed"
  → Stage 7 完成 → session.status = "completed"

is_promotable 判定(@property):
  if fast_mode == True               → False  (F-GOV-02)
  if generator_provider == "heuristic_fallback" → False  (F-GOV-03)
  其他                                → True
```

`fast_mode` 在 Stage 2 触发跳过部分澄清项;`generator_provider` 在 Stage 4 任一节点走 heuristic 时被 pipeline_orchestrator 自动写入(`if gp_type and not session.generator_provider: session.generator_provider = gp_type`)。**这两个 flag 是一旦置位不可清零的单向降级**。

### 4.4 v1 / v2 路由决策

```
pipeline_orchestrator._get_session_version(session)
  ├─ "1.0" → STAGE_NAME_MAP_V1 (5 阶段)
  │         → _prepare_stage_v1 / _save_stage_v1 / _assemble_handoff_v1
  │         → schema: reviewed_handoff_v2.schema.json
  └─ "2.0" → STAGE_NAME_MAP_V2 (7 阶段)
            → _prepare_stage_v2 / _save_stage_v2 / _assemble_handoff_v2
            → schema: reviewed_handoff_v3.schema.json
```

新建 session 默认 `"2.0"`(`DEFAULT_SESSION_VERSION`);v1 session 仍可从老 JSON 读回(`_apply_legacy_defaults` 补默认字段),但**禁止跨版本运行同一 session**(`session_version` 在 `__post_init__` 被 `_normalize_session_version` 锁定)。

### 4.5 Greenfield / Brownfield / Playable 模式分发(Legacy v1,F-CMP-06)

```
Scripts/compiler/routing/mode_router.resolve_mode(config, project_state)
  ├─ config.mode 明确指定 → 直接采用
  ├─ project_state.baseline 存在 + 有 actors → "brownfield_expansion"
  ├─ project_state 为空 → "greenfield_bootstrap"
  └─ playable_template 路径 → "playable_template"
```

此分发仅 Legacy v1 链路使用,Phase 11 主链通过 `root_skill_contract.create_root_skill_contract` 的 `target_phase` 参数 + `planner_output.execution_strategy.build_mode` 间接表达,**不再走 mode_router**。

## 5. 扩展点

- **新增 Phase 11 Stage**:在 `Compiler/stages/` 加 `.py`(命名 `stageN_<name>.py` 或 `<name>.py`);在 `pipeline_orchestrator.STAGE_NAME_MAP_V2` 与 `STAGE_ARTIFACT_MAP_V2` 加项;在 `Schemas/` 加对应 schema;在 `_prepare_stage_v2` / `_save_stage_v2` 加分支;在 `session.get_max_stage` 同步上限。Stage 7 已是终点,新增需考虑是否插到 7 之后或拆 6.5。
- **新增 Provider 类型**(MCP Agent / LLM / Heuristic 之外):继承 `agent_protocol.GeneratorProvider`,在 `domain_skill_runtime` 的 Provider 三路探测序列里追加;在 `VALID_GENERATOR_PROVIDERS` 加新枚举值;评估是否影响 `is_promotable`(默认新 Provider 应明确声明 promotable 属性)。
- **新增 Domain Skill Template**:见 `LLD/06_skills_and_templates.md` §5,在 `Plugins/AgentBridge/SkillTemplates/` 加 yaml + JSON schema,Stage 3 `skill_graph_planning._build_gameplay_nodes` / `_build_baseline_nodes` 通过 `template_id` 自动拾取,**Compiler 侧通常不需要改代码**。
- **新增 Genre Pack 场景生成器**(Legacy v1,boardgame/jrpg 之外):在 `Scripts/compiler/generation/` 加 `<genre>_scene_generator.py`,在 `spec_generation_dispatcher._determine_required_spec_ids` 与 `_get_default_pack_manifest_path` 加 `game_type` 分支;仅影响 Legacy v1 链路。
- **Session 自定义 metadata**:`CompilerSession` 是 `@dataclass`,直接加 field + 在 `to_dict` / `_apply_legacy_defaults` / `session.schema.json` 同步即可;**禁止改 session_id / run_id / session_version 三个轴向字段**。
- **新增 Cross Review v2 维度**:在 `cross_review_v2.py` 加 `check_<dim>` 函数,在 `create_cross_review_report_v2` 主流程编排,在 `reviewed_dynamic_spec_tree` 注释清楚维度归属。
- **新增 Schema 校验放行规则**:`_validate_stage_payload` 已对 Phase 8 历史 `skill_instance_id` 连字符命名做过 filter(stage_num==2 + pattern + skill_instance_id),新增放行需在同函数加 if 分支,**禁止全局禁用 schema 校验**。

## 6. 已知约束与陷阱

- **v1 / v2 不可中途切换**:`session.session_version` 在 `__post_init__` 被 `_normalize_session_version` 锁定,Stage 4 之后若手改 session.json 改 version 会导致 `STAGE_NAME_MAP` 错位,Stage 5+ schema 校验立即失败。重建 session 是唯一安全做法。
- **Heuristic Fallback `is_promotable=False` 硬约束**:`HeuristicFallbackProvider` 一旦被 Stage 4 任一 phase 选中,`generator_provider="heuristic_fallback"` 被写入 session,`is_promotable` 永久 False(F-GOV-03)。这是 governance 层防止低质量 run 直接 promote 的硬闸,**不可在 session 里手改 generator_provider 字段绕过**(`VALID_GENERATOR_PROVIDERS` 在 `__post_init__` 严格校验)。
- **`fast_mode=True` 不可 promote**(F-GOV-02):`is_promotable` 同上,fast_mode 主要用于开发期快速跑通流程,**生产 run 必须 `fast_mode=False`**。
- **3 个 fallback 文件 ↔ 三 phase 一一对应,Provider 三路与 phase 三路是不同维度**:三 fallback(`discovery_fallback` / `realization_fallback` / `convergence_fallback`)是"在 phase X 下作为 heuristic Provider 的具体实现",Provider 三路(MCP/LLM/Heuristic)是"在同一 phase 下选哪条 Provider 路径"。HLD §2.2 已澄清,这是 Phase 11 最易被误读为"3×3=9 个组合"的地方,**实际只有 3 phase × 3 provider = 9 个调度点,fallback 文件只是其中 3 个 heuristic 单元**。
- **Stage 4 ≤ 2 轮质量重试 + ≤ 2 次 schema 修复**:`_validate_stage4_node_acceptance` 硬上限,超限直接 `status="validation_failed"` → pipeline_orchestrator 返回 `stage_generation_failed`,**不可在节点层自行加重试循环**,这是 cost / latency 控制硬约束。
- **`naming_resolution_log` sidecar(Phase 11 Stage 6 lowering_v2 产出)**:Stage 6 输出 `build_ir.json` + sidecar `naming_resolution_log.json`,后者承载 GDD 名 → UE 路径解析记录,供 handoff_v3 与 Orchestrator 联合溯源使用。**注**:占位 `__RUNTIME_CONFIG_REF__` **不属于** Phase 11 v2 链路 — `lowering_v2._generate_build_step` 不写该字符串。该占位是 **Legacy v1 链路**(`Scripts/compiler/generation/boardgame_scene_generator.py:163,169`)写入,在 `Scripts/compiler/handoff/handoff_builder._materialize_runtime_config`(line 207-243)解析,`Scripts/orchestrator/handoff_runner.py:341-344` 兜底兼容。Phase 11 v3 链路通过 naming_resolution_log + handoff_v3 资产产物间接表达,**不依赖**该占位机制。
- **`clarification_required=true` 阻断 promote**(F-GOV-01):Stage 2 输出若有 `blocking_items`,Stage 3 `_prepare_stage_v2` 直接返回 `blocked_by_clarification`;若有 `provisional_items` 但无 blocker,允许继续但治理元数据中 `provisional_items` 进 `build_run_metadata`,下游 promotion gate 决定是否阻断。
- **Legacy v1 与 Phase 11 共用 `Schemas/`**:v1 用 `reviewed_handoff_v2.schema.json`,v2 用 `reviewed_handoff_v3.schema.json`;同名 `cross_review_report.schema.json` 在 v1/v2 路径下指向不同 schema 文件(`cross_review_report_v2.schema.json`),**写测试 fixture 时必须先确认 schema_version**。
- **`Scripts/compiler/intake/project_state_intake.py` 依赖 bridge**:此模块通过 `bridge.query_tools` 拉真实工程状态,无 Editor 时走 `_build_mock_fallback_snapshot`,**但 Phase 11 主链 root_skill_contract 不依赖这条路径**(Phase 11 GDD 是唯一输入)。

## 7. UE 5.7 迁移变更点

> 引用 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 / §4(P1 7 条裁决:1 false-positive + 6 confirmed;P2/P3 全部 suspected 留 5.7 实测裁决)。Compiler 是 pure Python 编译前端,**无直接 UE5 API 调用**,UE 5.7 影响相对小,主要走"Stage 6 lowering 产物 / Stage 7 handoff 产物"间接命中执行域。每条按 "[BC-NNN] api_or_key (P? 状态) → 影响 → 迁移行动" 三段式列出。**BC-019 严格 P2 suspected,不在编译期升 P1**(Task 1.1/1.2/1.5/1.6/1.7/1.8/1.9 统一教训)。

- **[BC-008] EditorScriptingUtilities 模块依赖 — P1 confirmed (reviewer=msc)**
  影响:Compiler 自身不直接 `import` 该模块,但 `lowering_v2.create_build_ir_v2` 生成的 `build_ir.json` 里 `build_steps[].tool` 字段会引用 `bridge.write_tools.spawn_actor` / `set_actor_transform` 等,这些 L1 工具链下沉到 C++ Subsystem 必经 EditorScriptingUtilities。
  迁移行动:Compiler 自身无改动,但生成的 Handoff v3 若要在 5.7 Editor 跑通必须先解决 BC-008(由 `LLD/01_cpp_subsystem.md` + `LLD/02_bridge.md` 承担)。Compiler 侧需在 Stage 6 输出后跑 `validation/validate_examples.py --strict` 校验 build_ir 字段名仍可被 bridge 消费。

- **[BC-016] Python EditorLevelLibrary 调用 — P1 confirmed (reviewer=msc)**
  影响:`lowering_v2._generate_build_step` 当前不直接 hardcode `unreal.EditorLevelLibrary` 字符串(由 bridge 层 wrap),但若 Phase 11 后续新增 Stage 加"直接产 Python 调用代码"的下降模式,需注意 5.7 后 `EditorLevelLibrary` API 形态变化。
  迁移行动:在 lowering_v2 输出 Python 代码字符串的扩展中(若未来引入),用 `unreal.EditorActorSubsystem` / `unreal.EditorLevelSubsystem` 替换;当前 v3 主链不命中本风险点。

- **[BC-017] Python EditorAssetLibrary 调用 — P1 confirmed (reviewer=msc)**
  影响:同 BC-016,当前 Compiler 不直接 hardcode `unreal.EditorAssetLibrary`,但 Stage 7 handoff_v3 输出的资产相关 step 若被 bridge 翻译为 Python 调用,需关注 5.7 后 `EditorAssetLibrary` 的废弃推进。
  迁移行动:无需在 Compiler 侧改;bridge 层 query_tools / write_tools 替换为 `unreal.EditorAssetSubsystem` 时,Compiler 输出契约不变(F-CMP-18 lowering 仅产抽象 tool 名,不产 unreal binding)。

- **[BC-019] RemoteControl HTTP 端点 `/remote/object/*` — P2 suspected (reviewer=pending-msc)**
  影响:Compiler 自身**完全不调** RC HTTP;但 `lowering_v2.create_build_ir_v2` 生成的 `build_ir.json` 在 Orchestrator `handoff_runner` 的 `bridge_mode="bridge_rc_api"` 通道下被翻译为 RC `call_function`,Compiler 是 RC 链路的上游契约定义方。
  迁移行动:UE 5.6/5.7 release notes 未提及 endpoint 移除,**预期向后兼容**;5.7 Editor 跑通 handoff_v3 → handoff_runner bridge_rc_api 后再决断。**严格 P2 suspected,不在 Compiler LLD 阶段升 P1**(Task 1.1/1.2/1.5/1.6/1.7/1.8/1.9 教训)。

- **[BC-018] unreal.* 其他 binding 综合 — P2 suspected (reviewer=pending-msc)**
  影响:Compiler 产 `build_ir.json` / `reviewed_handoff_v3.json` 中部分 step 引用了"未来可能下沉为 unreal.* Python 调用"的工具(例如 `spawn_actor` / `set_actor_transform`);若 5.7 整体 `unreal` 模块 binding 路径变化,会通过 bridge 层间接影响 Compiler 产物的可执行性。
  迁移行动:5.7 Editor 实测;Compiler 侧无直接改动,仅在 lowering_v2 输出 tool 抽象层稳定的前提下,bridge 层自行兼容。**严格 P2 suspected**。

- **[BC-022] `.uproject` Plugins[] enabled — P2 suspected (reviewer=pending-msc)**
  影响:Stage 7 handoff_v3 输出的 `reviewed_handoff_v3.json` 中 `handoff_meta` / `metadata` 段未直接声明 Plugins 依赖,但若 5.7 后 `AgentBridge.uplugin` Plugins[] 形态变化,handoff_v3 中标的 `target_phase` / `build_goal` 是否仍可被 Orchestrator 拾取需要 5.7 实测。
  迁移行动:**严格 P2 suspected**;5.7 Editor 打开本工程,确认 `AgentBridge` 插件被正确加载,handoff_v3 schema 校验通过即可。

- **[BC-023] `.uplugin` Plugins[] 依赖声明 — P2 suspected (reviewer=pending-msc)**
  影响:Compiler 自身不读 `.uplugin`,但其产物 `handoff_v3` 的执行依赖 `AgentBridge.uplugin` Plugins[] 正确声明 `EditorScriptingUtilities` / `RemoteControl` 等模块;5.7 后若 Plugins[] 字段名变化,会让 handoff_v3 产物在 5.7 Editor 不可执行。
  迁移行动:**严格 P2 suspected**;Compiler 侧无改动,仅依赖 `LLD/01_cpp_subsystem.md` + `LLD/02_bridge.md` 同步迁移。

### 迁移优先级与回归路径

按优先级排序:**P1 confirmed 三条(BC-008 / BC-016 / BC-017)主要影响 Compiler 产物的下游执行**,Compiler 本身无需改动;**P2 suspected 四条(BC-018 / BC-019 / BC-022 / BC-023)严格留 5.7 实测裁决**,不在编译期升 P1。回归路径:Phase 11 主链先跑 `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` 校验全部 schema(v2 / v3 双轨)→ 跑 `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor` 看 Stage 1-7 全链路 → 5.7 Editor 打开 + 跑 handoff_v3 在 `bridge_mode="bridge_rc_api"` 通道下的 e2e。Legacy v1 链路(`Scripts/compiler/`)在 Phase 11 主链稳定后**不进入 5.7 主回归**,仅保留单元测试基线。

---

**关联文件**: `Docs/design/HLD.md` §2 / `Docs/requirements/SRS.md` §3.4 / `Docs/FEATURE_INVENTORY.md` F-CMP-01..24 / `Docs/contracts/schemas_catalog.md`(v3 9 schema + v1/v2 兼容)/ `Docs/contracts/tool_contract.md` §2(L1/L2/L3 协议)/ `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4 / `Plugins/AgentBridge/Schemas/reviewed_handoff_v2.schema.json` + `reviewed_handoff_v3.schema.json` + `build_ir_v2.schema.json` + `cross_review_report_v2.schema.json` + `naming_resolution_log.schema.json` / `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py`(STAGE_NAME_MAP_V1/V2 双路由)
