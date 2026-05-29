# LLD/06 — Skills 与 Templates 子系统详细设计

> 版本: v1 (2026-05-26)
> 范围: Skill Runtime(`Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py` 705 行 + `domain_skill_runtime.py` 1753 行 + v1 残留 `Compiler/skill_runtime/skill_runtime.py` 100 行 / `Compiler/planner/planner.py` 96 行)+ SkillTemplate 静态模板(`Plugins/AgentBridge/SkillTemplates/` 下 12 skill × 6 文件 = 72 文件)
> 上游: `Docs/design/HLD.md` §2.2 + `Docs/requirements/SRS.md` §3.6 + `Docs/FEATURE_INVENTORY.md` F-SKL-01..04
> 契约: `Docs/contracts/schemas_catalog.md`(skill_graph + skill_fragment_v2)+ `Docs/contracts/field_specification.md`
> UE 版本: 当前 5.5.4 → 目标 5.7

## 1. 模块概述

Skill 与 Template 子系统是 AgentBridge "Skill-First Design Compiler" 主链的中段语义层,职责是把上游 Clarification Gate 收敛后的 Root Skill Contract 拆解为一组按依赖排序、按域分工的 Skill Node,再由每个 Node 在对应 SkillTemplate 静态模板的 prompt + schema 约束下生成 Spec Fragment 给下游 Lowering 阶段消费。架构上分为**两个互补层**:**Skill Runtime 实现层**(代码,F-SKL-01 / F-SKL-02)由 Phase 11 Stage 3 `skill_graph_planning.py`(705 行,生成 Skill Graph)+ Stage 4 `domain_skill_runtime.py`(1753 行,Discovery / Candidates / Convergence 三阶段执行)承担,v1 时代的 `skill_runtime.py` / `planner.py` 共 196 行作为 framework 残留保留向后兼容;**SkillTemplate 静态模板层**(F-SKL-03 / F-SKL-04)位于 `Plugins/AgentBridge/SkillTemplates/`,以"12 Skill × 6 文件 = 72 文件"的网格组织,12 Skill 拆分为 Baseline 6 个(HUD / Main Menu / Pause / Results / Settings / Start Screen,通用 UI 壳层)与 Genre Pack Monopoly-Like 6 个(Board Topology / Jail and Bankruptcy / Phase1 UI Flow / Property Economy / Tile Event Dispatch / Turn and Dice Flow,棋盘体类型专有 gameplay 域),每个 Skill 固定 6 文件:`manifest.yaml` / `system_prompt.md` / `domain_prompt.md` / `evaluator_prompt.md` / `input_selector.yaml` / `output_schema.json`。两层关系是**实现读模板**:Skill Runtime 不内嵌任何业务知识,所有"棋盘是什么 / HUD 要显示什么"的领域语义都从 SkillTemplate 加载;反过来 SkillTemplate 也不携带执行能力,只提供 prompt 文本与 JSON Schema。这一分离让"新增 Skill 域"在多数情况下退化为"加 6 文件 + 在 GAMEPLAY_NODE_CONFIGS 注册一行 template_id",不需要触碰执行流程主体。

## 2. 内部分层

### 2.1 Skill Runtime 实现层

| 模块 | 角色一句话 | F-SKL ID | 文件:行数 |
|---|---|---|---|
| Stage 3 Skill Graph Planning(v2 主链) | 读 Root Skill Contract + Clarification Gate Report,生成 Gameplay/Baseline 节点 + 依赖边 + 收敛序号 → skill_graph.json | F-SKL-01 | `Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py`:705 |
| Stage 4 Domain Skill Runtime(v2 主链) | 按拓扑顺序运行每个 Node 的 Discovery / Candidates / Convergence 三 phase,聚合 Stage 4 三份总览 + skill_fragments/* | F-SKL-02 | `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`:1753 |
| v1 Skill Runtime(framework 残留) | Phase 8/9 时代的 Skill Fragment 模板填充逻辑,由 Stage 4 经 `from ..skill_runtime import skill_runtime` 复用 helper | F-SKL-02(legacy 兼容) | `Plugins/AgentBridge/Compiler/skill_runtime/skill_runtime.py`:100 |
| v1 Planner(framework 残留) | Phase 8/9 时代的 Skill Template 扫描 + Planner Output 模板,Phase 11 主链不直接调用 | F-SKL-01(legacy 兼容) | `Plugins/AgentBridge/Compiler/planner/planner.py`:96 |

### 2.2 SkillTemplate 静态模板层(12 Skill × 6 文件 = 72 文件)

| 子层 | F-SKL ID | 目录根 | Skill 列表 |
|---|---|---|---|
| Baseline 6 域(universal,通用 UI 壳层) | F-SKL-03 | `Plugins/AgentBridge/SkillTemplates/baseline/` | `hud` / `main_menu` / `pause` / `results` / `settings` / `start_screen` |
| Genre Pack Monopoly-Like 6 skill(棋盘体类型) | F-SKL-04 | `Plugins/AgentBridge/SkillTemplates/genre_packs/boardgame/monopoly_like/` | `monopoly_board_topology` / `monopoly_jail_and_bankruptcy` / `monopoly_phase1_ui_flow` / `monopoly_property_economy` / `monopoly_tile_event_dispatch` / `monopoly_turn_and_dice_flow` |

**每个 Skill 固定 6 文件结构**(由 `skill_graph_planning.STANDARD_TEMPLATE_FILES` 集合约束):

| 文件 | 角色 |
|---|---|
| `manifest.yaml` | 元数据:`template_id` / `template_kind`(baseline_skill / genre_skill)/ `genre`(universal / monopoly_like 等)/ `template_version` / `realization_class`(presence_only / realization_eligible)/ `phase_scope` / `input_contract_ref` / `output_schema_ref` / `requires_static_vocab` / `can_emit_families` / `depends_on_templates` / `gameplay_coupling` / `priority` |
| `system_prompt.md` | Provider 通用系统人格(本 Skill 是哪类领域专家、遵守哪些硬规则) |
| `domain_prompt.md` | Provider 领域专用知识与生成指令(棋盘形状有哪些 / HUD 信息密度如何取舍) |
| `evaluator_prompt.md` | Evaluator 自检 prompt(生成结果是否满足收敛标准、是否遗漏 capability) |
| `input_selector.yaml` | 从 GDD Projection / Root Skill Contract 中选取 / 排除哪些字段作为 Provider 输入 |
| `output_schema.json` | JSON Schema(draft-07,`additionalProperties: false` 硬性要求),Generator 输出格式契约 |

## 3. 关键类/函数签名

> 仅列与 Skill Graph 生成、Stage 4 三阶段执行、Template 加载、Fragment 装配强相关的函数,签名后 1 行中文用途(<=24 字)。

**Stage 3 — `Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py`:**

```python
# 顶层 API
def create_skill_graph(root_skill_contract: Dict[str, Any], clarification_gate_report: Dict[str, Any], run_id: str | None = None) -> Dict[str, Any]:
    # 生成 skill_graph.json 主结构(nodes + edges + metadata)
def save_skill_graph(skill_graph: Dict[str, Any], output_path: str | Path) -> str:
    # 落盘 skill_graph JSON

# 节点构造
def _build_gameplay_nodes(root_skill_contract, clarification_gate_report) -> List[Dict[str, Any]]:
    # 按 GAMEPLAY_NODE_CONFIGS 表(Monopoly 7 candidate)按 capability.activation == "required" 过滤生成 ≤7 节点
def _build_baseline_nodes(root_skill_contract, clarification_gate_report) -> List[Dict[str, Any]]:
    # 按 Root Skill Contract baseline_capabilities 生成 Baseline 节点,allows_design_space_discovery 此处置 false
def _annotate_node(node, dependency_map, coupling_map, order_map) -> Dict[str, Any]:
    # 注入 dependencies + coupling(按 order_map 排序);allows_design_space_discovery 与 convergence_priority 由各自 _build_*_nodes 设置(_annotate_node 不写)

# Template 解析
def _baseline_template_dir(template_id: str) -> Path:
    # 解析 baseline.<domain>.<realization_class> → SkillTemplates 子目录
def _resolve_baseline_template_source(template_id: str) -> str:
    # 判定 plugin_skill_template / missing,缺一个 6 文件即 missing

# 全局常量
GAMEPLAY_NODE_CONFIGS  # gameplay-board-topology / -tile-system / -turn-loop / -dice / -economy / -player-management / -jail 7 节点 template 映射
STANDARD_TEMPLATE_FILES  # {manifest.yaml, system_prompt.md, domain_prompt.md, evaluator_prompt.md, input_selector.yaml, output_schema.json}
BASELINE_TEMPLATES_ROOT  # PLUGIN_DIR / "SkillTemplates" / "baseline"
```

**Stage 4 — `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py`:**

```python
# 顶层 API
def run_domain_skill_runtime(skill_graph, root_skill_contract, clarification_gate_report, phase_scope, fast_mode=False, allow_heuristic_fallback=True, llm_client=None) -> Dict[str, Any]:
    # Stage 4 主入口:三 Provider(LLM/MCP sidecar/Heuristic Fallback)解析 + 拓扑遍历

# Provider / 执行
def prepare_node_phase(node, phase, ...) -> Dict[str, Any]:
    # 为 MCP sidecar 准备 phase 输入(Discovery/Candidates/Convergence)
def save_node_phase(node, phase, output) -> Dict[str, Any]:
    # 接收 sidecar 输出,落盘 trace + node_state
def load_mcp_node_state(output_dir, node_id) -> Dict[str, Any]:
    # 读取 sidecar 持久化的单节点 state

# Fragment 构造
def _build_gameplay_spec_fragment(node, ...) -> Dict[str, Any]:
    # gameplay 节点完整 fragment(locked_constraints + 来自 converged_pack 的 selected_realization)
def _build_baseline_spec_fragment(node, ..., converged_pack=None) -> Dict[str, Any]:
    # baseline 节点 fragment;realization_eligible 时写入 selected_realization(与 gameplay 对称),presence_only 走 _build_presence_fragment 短路径
    # 注:realization_eligible baseline(如 HUD)经 _build_discovered_fragment 调用本函数,capability 按 capability_id 动态查;HUD 的 required_elements 仍以 constraint_fields.ui.required_hud_fields 为准
def _build_presence_fragment(node, ...) -> Dict[str, Any]:
    # presence_only / fast_mode 短路径,跳过 Discovery 直接生成最小 Fragment
def _build_discovered_fragment(node, design_space, candidates, convergence) -> Dict[str, Any]:
    # 三阶段聚合后的最终 fragment

# 总览聚合
def _aggregate_design_space(...) -> Dict[str, Any]   # Stage 4-A 总览
def _aggregate_candidates(...) -> Dict[str, Any]      # Stage 4-B 总览
def _aggregate_converged_pack(...) -> Dict[str, Any]  # Stage 4-C 总览
def _topological_execution_order(nodes) -> List[Dict[str, Any]]:
    # 按 dependencies 拓扑排序节点

# Provider 输出规范化(来自 Doc 14 Agent Interaction Protocol)
def _normalize_mcp_discovery_output(node, output) -> Dict[str, Any]
def _normalize_mcp_candidates_output(node, output) -> Dict[str, Any]
def _normalize_mcp_convergence_output(node, output) -> Dict[str, Any]

# 全局常量
FRAGMENT_FAMILY_MAP   # skill-* → *_spec family(16 项映射)
MCP_AGENT_SIDECAR_DIR # "stage4_mcp_agent_sidecar"
```

**v1 残留(framework 兼容):**

```python
# Plugins/AgentBridge/Compiler/skill_runtime/skill_runtime.py
def load_template_pack(template_dir: str) -> dict:           # 读 6 文件成 dict
def create_fragment_template(skill_instance_id, template_id, phase_scope) -> dict:  # v1 fragment 骨架

# Plugins/AgentBridge/Compiler/planner/planner.py
def scan_skill_templates(templates_dir: str) -> list:         # 扫描 manifest.yaml 列表
```

**SkillTemplate `manifest.yaml` 字段集**(实例:`baseline/hud/manifest.yaml`):

```yaml
template_id: baseline.hud.realization_eligible       # 全局唯一,Skill Graph edge 引用
display_name: HUD（常驻界面）
template_kind: baseline_skill | genre_skill          # 区分两大类
genre: universal | monopoly_like | ...               # Genre Pack 归属
template_version / schema_version / evaluator_version
phase_scope: [phase1_local_multiplayer, ...]         # 适用阶段
realization_class: presence_only | realization_eligible   # 决定 Stage 4 是否走 Discovery
input_contract_ref / output_schema_ref               # 跨文件引用
requires_static_vocab / can_emit_families            # Static Base 词表与输出族名
depends_on_templates / gameplay_coupling / priority  # Skill Graph 依赖与耦合
```

## 4. 数据流与状态机

**场景 A — Skill Graph 生成(Stage 3,F-SKL-01):** Pipeline Orchestrator 把上游 `root_skill_contract.json` + `clarification_gate_report.json` 喂入 `create_skill_graph()`;`_build_gameplay_nodes` 按 GAMEPLAY_NODE_CONFIGS 静态表(Monopoly 7 candidate:`skill-board-topology` / `-tile-system` / `-turn-loop` / `-dice` / `-economy` / `-player-management` / `-jail`)按 `capability.activation == "required"` 过滤生成 ≤7 个 gameplay 节点,每个节点的 `template_id` 指向 Monopoly Genre Pack 下某个 SkillTemplate;`_build_baseline_nodes` 读 Root Skill Contract 的 `baseline_capabilities` 对每个 baseline 域生成节点,`_resolve_baseline_template_source` 检查 `SkillTemplates/baseline/<domain>/` 6 文件是否齐全,缺即标 `missing`(进入 `metadata.missing_baseline_templates` 警告列表)。`_filter_edges` 从静态 edge 表过滤出当前节点集合内部的边,`_build_relationship_maps` 派生 `dependency_map` / `coupling_map`,最终 `_annotate_node` 在每个节点上追加 `dependencies` + `coupling`(按 order_map 排序);`allows_design_space_discovery` 和 `convergence_priority` 由各自 `_build_gameplay_nodes` / `_build_baseline_nodes` 单独设置;落 `skill_graph.json`。

**场景 B — Domain Skill Runtime 执行(Stage 4,F-SKL-02):** `run_domain_skill_runtime` 先用 `agent_protocol.resolve_provider` 选定 Generator Provider(优先级 LLMProvider > HeuristicFallbackProvider,二者皆不可得且 `allow_heuristic_fallback=False` 则 `status="refused"`,详见 LLD 04 §4 修订);`_topological_execution_order` 按依赖拓扑排序节点。**每个节点的执行循环**:(1) 检查所有 dependencies 状态为 `completed`,否则 lifecycle 标 `blocked` 并跳过;(2) `realization_class=presence_only` 且当前在 Baseline 走 `_build_presence_fragment` **短路径**(跳过 Discovery,直接生成 minimal fragment + assumption "采用 presence_only 最低实现标准");(3) 其他节点走完整三 phase:**Discovery phase** 探索 Design Space 维度(棋盘形状 8 选 / HUD 信息密度高中低),**Candidates phase** 在 Design Space 内生成 2-N 个 realization 候选,**Convergence phase** 评估并收敛到 selected_realization;(4) 每 phase 输出经 `_normalize_mcp_*_output` 规范化、写入 `stage4_mcp_agent_sidecar/node_traces/<node_id>/<phase>.json`;(5) `_build_gameplay_spec_fragment` / `_build_baseline_spec_fragment` 装配 Skill Fragment 并落 `skill_fragments/skill-<id>.json`。最终 `_aggregate_design_space` / `_aggregate_candidates` / `_aggregate_converged_pack` 三份总览汇总输出。

**场景 C — SkillTemplate 6 文件读取拼装:** 任一 phase 进入 Provider 前,Stage 4 通过 `_resolve_template_prompts(template_id)` 把对应 SkillTemplate 目录的 `system_prompt.md` + `domain_prompt.md` 拼接为 Provider 的 system message;`evaluator_prompt.md` 单独读出供 Evaluator 自检;`output_schema.json` 在 Generator 调用处作为输出 JSON Schema 约束;`input_selector.yaml` 的 `include_sections` / `exclude_sections` 用于从 GDD Projection 中投影出 Provider 真正需要的字段。

**场景 D — Baseline vs Gameplay 同构差异:** 两类 Skill 完全共享 6 文件结构与同一套 Stage 4 执行管线,区别只在 `manifest.realization_class`:`presence_only`(典型如 `baseline/start_screen` 这类壳层 UI)在 Stage 4 走 `_build_presence_fragment` 短路径,**跳过 Discovery / Candidates / Convergence 三 phase**(F-CHN-S4-01);`realization_eligible`(典型如 `baseline/hud` 因 HUD 信息密度本身需要设计探索)则与 gameplay 节点一样走完整三 phase。这是 Baseline 域允许"绝大多数 UI 用最小标准,但某些核心 UI(HUD)允许设计探索"的关键开关。

## 5. 扩展点

1. **新增 Baseline Domain:** 在 `Plugins/AgentBridge/SkillTemplates/baseline/<new_domain>/` 建目录,落齐 6 文件(`manifest.yaml` 中 `template_id` 形如 `baseline.<new_domain>.<realization_class>`、`template_kind: baseline_skill`、`genre: universal`)。然后在 `universal_baseline_standard` 配套文档加 metadata、在 Root Skill Contract 的 `baseline_capabilities` 加同名键。Stage 3 `_build_baseline_nodes` 会自动发现并加入 Graph,**Skill Runtime 代码无需改动**。

2. **新增 Genre Pack(全新游戏类型):** 在 `Plugins/AgentBridge/SkillTemplates/genre_packs/<genre>/<variant>/` 建目录树(如 `genre_packs/rpg/jrpg/`),为该 Genre 下每个 skill 建 6 文件子目录。需要同步更新 Stage 3 `GAMEPLAY_NODE_CONFIGS`(增加 gameplay-* 节点 → template_id 映射)与 `FRAGMENT_FAMILY_MAP`(node id → spec family name)。当前 inventory 中 `jrpg_genre_pack_design.md` / `genre_pack_core_design.md` 即为新 Genre 设计的输入参考。

3. **扩展 6 文件结构到 7+ 文件:** 例如增加 `input_validator.yaml` 在 Provider 调用前做硬性输入校验。需同步修改 `STANDARD_TEMPLATE_FILES` 集合 + `_resolve_baseline_template_source` 完整性检查 + Stage 4 `_resolve_template_prompts` 加载逻辑 + 在所有 12 个已有 Skill 补齐新文件(否则会被标 `missing`)。

4. **新增 Discovery 触发策略:** 当前只有 `presence_only`(跳过)与 `realization_eligible`(走全 Stage 4)二选一。若引入第三类(如 `clarification_gated`:仅当 Clarification Gate 留存某项 retained_clarification 时才走 Discovery),需在 `_build_baseline_spec_fragment` / `_build_presence_fragment` 之外加新分支并在 `manifest.realization_class` 字段枚举值扩展、配套更新 evaluator_prompt 与 Stage 4 拓扑判定。

5. **新增 Provider 类型:** 当前 Stage 4 支持 LLM / MCP sidecar / Heuristic Fallback 三 Provider(见 LLD 04 §4 与 Doc 14)。若要新增(如 RAG-augmented Provider),在 `agent_protocol.resolve_provider` 注册解析顺序、实现对应 `*_normalize_output` 规范化函数即可,SkillTemplate 层完全不需要改动。

## 6. 已知约束与陷阱

1. **72 文件一致性硬约束:** 12 Skill × 6 文件 = 72 文件,缺任一文件(如某个 Skill 漏写 `evaluator_prompt.md`)会被 `_resolve_baseline_template_source` 判定为 `missing`,Stage 3 把它放进 `metadata.missing_baseline_template_warnings`、Stage 4 跳过该节点,且不会自动报错——只在最终 Skill Graph 元数据里留警告。批量改 SkillTemplate 时务必 `STANDARD_TEMPLATE_FILES` 全配齐。

2. **presence_only 跳过 Discovery 是单向的:** `realization_class=presence_only` 的 Baseline 节点走 `_build_presence_fragment` 短路径(F-CHN-S4-01),不生成 design_space / candidates 输出,Stage 4 三份总览中对应位置只有 `presence_only_default` 占位。如果业务需要让某个原本 presence_only 的 Baseline 进入完整 Discovery,**必须改 manifest.yaml 而不是改 Stage 4 代码**;反向同理。

3. **`output_schema.json` 必须 `additionalProperties: false`:** 由 `Docs/contracts/field_specification.md` §3 硬规则约束。若不显式声明,Generator 输出会绕过 Schema 校验、把 Provider 编出来的额外字段污染下游 Lowering——Stage 4 不强制再次校验。手工新增 SkillTemplate 时一律在 root + 每个 nested object 显式写 `"additionalProperties": false`。

4. **`skill_id` 与目录名强一致:** `manifest.template_id` 形如 `baseline.hud.realization_eligible` 或 `monopoly.board_topology.phase1`,前缀必须与目录路径吻合(`baseline/hud/`、`genre_packs/boardgame/monopoly_like/monopoly_board_topology/`)。`Plugins/AgentBridge/MCP/naming.py` 有相关校验,但 Stage 3 `_baseline_template_dir` 只反向解析,**目录名错放不会立即报错**——会在 Stage 4 加载 prompt 时悄无声息地走 `missing` 分支。

5. **`template_version` 升级不向下兼容:** `manifest.template_version` 升级(如 `1.0.0` → `2.0.0`)意味着 `output_schema.json` 字段集可能变化,旧 Skill Fragment 在 Lowering 阶段会因为 Schema 不匹配崩溃。当前 codebase 没有 `lowering` 层的 schema_version compatibility shim,**升级 SkillTemplate version 前必须同步检查下游消费者**(Lowering / Handoff 阶段)。

6. **v1 残留与 v2 主链共存:** `Compiler/skill_runtime/skill_runtime.py` 与 `Compiler/planner/planner.py` 是 Phase 8/9 时代的 framework 残留,Stage 4 通过 `from ..skill_runtime import skill_runtime` 复用部分 helper(如 `load_template_pack`)。改 v1 文件需评估是否会反向污染 v2 主链;新功能一律加在 `Compiler/stages/` 下,不要往 v1 framework 残留里塞。

## 7. UE 5.7 迁移变更点

> Skill / Template 层本身是 **prompt 文本 + JSON Schema**,**不含直接 UE5 API 调用**,UE 5.7 升级对本子系统的代码层影响最小。但下游 Lowering / 执行域消费 Skill Fragment 时会经过 LLD 02 Bridge 与 LLD 05 MCP Server 暴露的工具,因此存在**间接影响**:

- **BC-008(P1 confirmed,由 msc 在 Phase 0.2 §4 裁决,源:`AgentBridge.Build.cs` + `AgentBridgeTests.Build.cs` + `AgentBridge.uplugin` 的 EditorScriptingUtilities C++ 模块依赖):** Skill/Template 层是 prompt + schema,完全不直接消费 C++ Build.cs 依赖,本 BC 对本子系统**无直接影响**;迁移由 LLD/01 cpp + LLD/02 bridge 承担。

- **BC-016 / BC-017(P1 confirmed,由 msc 在 Phase 0.2 §4 裁决,源:`MCP/server.py` + `Scripts/bridge/query_tools.py` 中的 `unreal.EditorLevelLibrary` / `unreal.EditorAssetLibrary` 调用):** 这两条 BC 影响 Python Editor Scripting binding。若任何 `evaluator_prompt.md` 中嵌入"通过 UE Python API 验证 X"类指令(如调用 `EditorLevelLibrary` / `EditorAssetLibrary`),则 evaluator 在 UE 5.7 下执行时会因为 API 重命名而失败。**对当前 12 个 SkillTemplate 的实测命中数:0**(2026-05-26 `grep -rn "EditorLevelLibrary\|EditorAssetLibrary" Plugins/AgentBridge/SkillTemplates/` 无任何匹配),即当前所有 evaluator_prompt 都是纯文本评估指令,不嵌入 UE API 字符串,**本子系统目前不受 BC-016/017 直接影响**。新增 SkillTemplate 时如果在 evaluator_prompt 引入 UE API,必须按 BC-016/017 的 5.7 替换矩阵改写(`UnrealEditorSubsystem` / `LevelEditorSubsystem` / `EditorActorSubsystem` / `EditorAssetSubsystem`)。

- **BC-019(P2 suspected,pending-msc,源:工具体系 L2/L3 在 UE 5.7 下的具体接口变更):** 若 evaluator_prompt 通过 Channel B 调用 L2 资产管理或 L3 编排工具来验证 Skill Fragment 落地后的 UE 副作用(当前 12 SkillTemplate 未发现此模式),则受 BC-019 影响。此 BC 当前 **P2 suspected,等待 msc 在后续阶段裁决,严禁标 P1 confirmed**;在 P2 状态下,本子系统不主动适配,只在 evaluator_prompt 引入 L2/L3 调用时再评估。

- **整体结论:** 在不修改 SkillTemplate prompt 内容、不引入新 UE API 调用的前提下,Skill / Template 子系统对 UE 5.7 迁移**零成本**;迁移成本完全落在下游 Bridge(LLD 02)与 MCP Server(LLD 05)。Stage 3 / Stage 4 Python 代码本身只调用 stdlib + `json` + `pathlib`,无 UE 依赖。
