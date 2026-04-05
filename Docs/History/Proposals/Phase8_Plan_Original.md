# Phase 8 统一方案：Skill-First Compiler Reset + MonopolyGame 垂直切片

## Context

AgentBridge 经过 7 个 Phase 建立了完整的执行基础设施（C++ Plugin、Bridge 三通道、Orchestrator、验证体系、230 条测试），但 Skill Compiler Plane 被实现为硬编码 Python（regex 解析 GDD、if/else 路由、Python builder 生成），导致系统主轴偏离了 AI-First 的目标。

**本轮核心任务**：将 AGENT_UE5 的主链从 `Spec-first / Python-first 自动化编排` 纠正为 `GDD-first / Skill-first 的 AI Agent Compiler 主链`，以 `GDD_MonopolyGame.md` 为唯一正式样例输入，打通 Phase 1 本地多人垂直切片。

**三方案融合策略**：
- **GPT**（主框架）：Skill 三层定义、6 段主链、4 里程碑、DoD/失败判定、目录重构、GDD Part A/B 分层
- **Gemini**（LLM 集成）：Skill 实体化为 prompt+schema 文件、Self-Healing Loop、结构化输出约束
- **Claude**（工具+执行）：MCP Server 暴露 Bridge 工具、Claude Code 直接写 C++ 游戏代码、Channel A 资产创建

---

## 一、唯一正式样例输入

`ProjectInputs/GDD/GDD_MonopolyGame.md`

### 处理原则（来自 MonopolyGame_GDD_Projection_v1）
- **Part A = 设计真源**：玩法语义、规则拆解、Dynamic Spec Tree 生成输入
- **Part B = 实现约束**：UE5 类设计参考、Lowering 约束、编辑器操作提示
- **Phase 8 只取 Phase 1**：本地多人（同屏轮流），不做在线多人/Session/RPC

### Phase 1 允许范围
2-4 人本地、28 格棋盘、起点奖励 $200、地产购买/租金/颜色组翻倍、所得税/奢侈税、Go To Jail / Jail Visit、保释/掷双数出狱/三回合强制支付、破产退出、游戏结束、HUD + Popup UI、CHANCE/COMMUNITY 留空

### 明确排除
在线多人、Session、RPC/Replication、Chance/Community 事件卡牌、地产拍卖、抵押/建房/旅馆

---

## 二、新主链架构

```
GDD_MonopolyGame.md
  │
  ├─ Step A: Design Intake ─────────── 结构化设计理解 + GDD Projection
  ├─ Step B: Planner / Routing ─────── Skill 选择 + 依赖图 + 能力缺口
  ├─ Step C: Skill Runtime ─────────── 6 个 Skill Instance → Dynamic Spec Fragments
  ├─ Step D: Cross-Spec Review ─────── 一致性审查 → Reviewed Dynamic Spec Tree
  ├─ Step E: Lowering / Translation ── Dynamic Spec → Static Specs + Build IR + Validation IR
  ├─ Step F: Reviewed Handoff v2 ───── 编译面→执行面的唯一正式边界
  └─ Step G: Deterministic Execution ─ Schema 校验 → MCP/Bridge 执行 → 验证 → 证据
                                        └─ Self-Healing Loop（≤3 次重试）
```

### 关键边界

| 边界 | 上游输出 | 下游输入 | 格式 |
|------|---------|---------|------|
| GDD → Intake | 原始 Markdown（Part A/B 分层） | Claude 阅读理解 | 自然语言 |
| Intake → Planner | `gdd_projection.json` | Planner 消费 | JSON（`gdd_projection.schema.json`） |
| Planner → Skill Runtime | `planner_output.json` | Skill 实例化 | JSON（`planner_output.schema.json`） |
| Skill Runtime → Review | `skill_fragments/*.json` | Cross-Spec Review | JSON（`skill_fragment.schema.json`） |
| Review → Lowering | `reviewed_dynamic_spec_tree.json` | Lowering 消费 | JSON |
| Lowering → Handoff | `build_ir.json` + Static Specs | Handoff v2 组装 | JSON（`build_ir.schema.json`） |
| Handoff → Execution | `reviewed_handoff_v2.json` | Orchestrator 消费 | JSON（`reviewed_handoff_v2.schema.json`） |
| Execution → UE5 | Run Plan 步骤 | MCP/Bridge 调用 | Tool Contract 格式 |

---

## 三、Skill 三层定义（来自 Skill_Template_Pack_v1）

### 3.1 Skill Template Pack（静态层）
版本化、可落盘、可复用的能力模板包。每个 Template Pack 包含：

```
SkillTemplates/<domain>/<template_name>/
├── manifest.yaml          # 模板 ID、适用条件、输入输出契约、可发射 family
├── system_prompt.md       # 专家身份与思考角度
├── domain_prompt.md       # 领域边界、范围与禁止事项
├── input_selector.yaml    # 从总上下文中选择哪些片段（防止 LLM 漂移）
├── output_schema.json     # 输出结构强约束
├── evaluator_prompt.md    # 自检逻辑（遗漏/冲突/越界检查）
├── examples/              # few-shot 示例
└── policies/
    ├── tool_allowlist.yaml
    └── gap_reporting.md
```

### 3.2 Skill Instance（运行时层）
Planner 在当前任务上下文中实例化的能力调用。由 GDD + 阶段目标 + 项目模式 + Static Base 能力边界共同决定。

### 3.3 Skill Artifact（产物层）
统一输出包络（来自 Skill_Template_Pack_v1 §8）：
```json
{
  "skill_instance_id": "runtime-generated-id",
  "template_id": "monopoly.board_topology.phase1",
  "phase_scope": "phase1_local_multiplayer",
  "emitted_family": "board_topology_spec",
  "spec_fragment": {},
  "assumptions": [],
  "open_questions": [],
  "review_hints": [],
  "capability_gaps": [],
  "confidence": { "coverage": 0.0, "consistency": 0.0 }
}
```

---

## 四、MonopolyGame 第一批 6 个 Skill Templates

| # | Template ID | 输入 | 输出 families | 来源 GDD 节 |
|---|------------|------|--------------|------------|
| 1 | `monopoly.board_topology.phase1` | board layout, tile count, corner defs | `board_topology_spec`, `tile_positioning_intent` | §2.1 |
| 2 | `monopoly.turn_and_dice_flow.phase1` | turn loop, dice rules, start bonus | `turn_flow_spec`, `dice_rule_spec`, `movement_rule_spec` | §3.1, §3.4 |
| 3 | `monopoly.tile_event_dispatch.phase1` | tile type table, event rules | `tile_event_spec`, `event_dispatch_matrix` | §2.2-2.4 |
| 4 | `monopoly.property_economy.phase1` | property tiles, color groups, rent/bankruptcy | `property_economy_spec`, `ownership_transition_spec` | §3.2-3.3 |
| 5 | `monopoly.jail_and_bankruptcy.phase1` | jail rule, go-to-jail, bankruptcy | `jail_rule_spec`, `bankruptcy_rule_spec`, `special_state_transition_spec` | §3.2 |
| 6 | `monopoly.phase1_ui_flow.phase1` | HUD, popup, decision points | `ui_prompt_flow_spec`, `decision_ui_binding_spec` | §4 |

补充 Intake/Routing 模板：`intake.monopoly_classifier` + `routing.monopoly_phase_scope_router`
补充验证模板：`validation.monopoly_phase1_runtime_checks`

---

## 五、Dynamic Spec Families（来自 Dynamic_Spec_Families_v1）

12 个 family，先表达 **Monopoly 游戏语义**，不提前压成 `scene/layout/anchors/actors`：

| Family | 核心内容 |
|--------|---------|
| `game_identity_spec` | 类型 board_strategy / monopoly_like / 2-4 人 / 胜利条件 |
| `phase_scope_spec` | phase1_local_multiplayer / in_scope / out_of_scope |
| `board_topology_spec` | 28 格正方形环 / 顺时针 / 四角索引 0/7/14/21 |
| `tile_system_spec` | 28 格完整表 / 类型 / 名称 / 颜色组 / 价格 / 基础租金 |
| `turn_flow_spec` | 初始化 → 掷骰 → 移动 → 过起点 → 格子事件 → 双数再掷 → 三连入狱 |
| `jail_system_spec` | 入狱触发 / 保释 / 掷双数出狱 / 三回合强制付费 |
| `player_economy_spec` | 1500 初始 / 起点 200 / 税务 / 租金 / 破产释放 |
| `property_ownership_spec` | 无主可买 / 有主收租 / 同色组翻倍 |
| `ui_flow_spec` | HUD / 掷骰 / 购买 / 租金 / 监狱决策 / 破产胜利弹窗 |
| `runtime_entity_spec` | GameMode/State/PlayerState/Controller/BoardManager/Tile/Pawn/Dice |
| `runtime_validation_spec` | 核心规则闭环检查点 / 断言 |
| `network_evolution_spec` | Phase 2 演进占位（不进本轮执行） |

**依赖方向**：game_identity → phase_scope → board_topology → tile_system → turn_flow → jail_system → player_economy → property_ownership → ui_flow → runtime_validation

---

## 六、Lowering Pipeline（来自 Lowering_Pipeline_v1）

### 四阶段管线

| 阶段 | 目标 | MonopolyGame 关键动作 |
|------|------|---------------------|
| **A: Normalization** | 归一化多 family、消解别名 | 确认 28 格索引覆盖 0..27、特殊索引与 topology 一致 |
| **B: Dependency Closure** | 检查依赖闭合 | 租金需 owner+color_group、双数三连需 dice+jail、UI 需追溯 turn/property/jail |
| **C: Static Capability Binding** | 绑定到 Static Base 能力 | board→board_manager_spec+tile_spawn、turn→game_mode_phase_machine、economy→player_state_money |
| **D: Build IR Generation** | 生成构建意图中间表示 | 见下方 Build IR 列表 |

### Build IR 目标对象（14 个）

```
create_board_ring_layout          # 28 格环形布局
create_tile_actors                # 格子 Actor
assign_tile_metadata              # 格子数据绑定
create_player_tokens              # 玩家棋子
create_game_mode_shell            # GameMode 骨架
bind_turn_state_machine           # 回合状态机
bind_dice_roll_logic              # 骰子逻辑
bind_tile_event_dispatch          # 格子事件分发
bind_property_economy_logic       # 地产经济
bind_jail_logic                   # 监狱逻辑
bind_bankruptcy_logic             # 破产逻辑
create_phase1_ui_widgets          # UI 组件
bind_ui_to_game_state             # UI-状态绑定
attach_validation_hooks           # 验证钩子
```

**明确禁止**：不允许把 GDD 拍平为单一 `scene_spec` / actor 列表 / 纯 `spawn_actor` workflow。

---

## 七、Reviewed Handoff v2（来自 Reviewed_Handoff_v2_Design）

编译面→执行面的唯一正式边界。v2 升级点：

```json
{
  "handoff_meta": { "handoff_version": "v2", "target_phase": "phase1_local_multiplayer" },
  "project_context": { "project_name": "MonopolyGame", "game_type": "board_strategy" },
  "planner_summary": { "identified_domains": [...], "phase_scope": "...", "out_of_scope": [...] },
  "selected_skill_instances": [...],
  "reviewed_dynamic_spec_tree": { "board_topology_spec": {}, "tile_system_spec": {}, ... },
  "cross_review_summary": { "status": "approved_with_warnings", "issues_resolved": [...] },
  "lowering_summary": { "families_bound": [...], "unbound_requirements": [...] },
  "build_ir": {},
  "validation_ir": {},
  "capability_gaps": [],
  "approval": { "approval_status": "approved_with_warnings" }
}
```

执行层只消费 Handoff v2，不回读原始 GDD。

---

## 八、Planner Output Model（来自 Planner_Output_Model_v1）

```json
{
  "planner_meta": { "planner_version": "v1", "mode": "greenfield", "target_phase": "phase1_local_multiplayer" },
  "project_intent": { "game_type": "board_strategy", "subgenre": "monopoly_like", "player_count_range": "2-4" },
  "routing_decision": { "identified_domains": [...], "required_family_targets": [...] },
  "selected_skill_instances": [
    { "skill_instance_id": "skill-board", "template_id": "monopoly.board_topology.phase1", "depends_on": [], "emits_families": ["board_topology_spec"] }
  ],
  "dynamic_spec_targets": ["board_topology_spec", "tile_system_spec", "turn_flow_spec", ...],
  "execution_strategy": { "build_mode": "greenfield", "target_output_kind": "playable_phase1_template" },
  "capability_gaps": [],
  "review_focuses": ["board_index_closure", "go_and_jail_rule_consistency", "rent_and_bankruptcy_consistency"],
  "confidence": { "gdd_coverage": 0.91, "phase_alignment": 0.95 }
}
```

---

## 九、MCP Server（工具层，来自 Claude 方案）

### 作用
让 Claude Code 能通过 MCP 协议调用 UE5 Editor，用于 Self-Healing Loop 中的执行和验证。

### 工具清单

**Layer 1：已有 Bridge 工具（15 个，复用 tool_contract_v0_1.md）**
- L1 查询（7 个）：`get_current_project_state`, `list_level_actors`, `get_actor_state`, `get_actor_bounds`, `get_asset_metadata`, `get_dirty_assets`, `run_map_check`
- L1 写入（6 个）：`spawn_actor`, `set_actor_transform`, `import_assets`, `create_blueprint_child`, `set_actor_collision`, `assign_material`
- L2 服务（5 个）：`capture_screenshot`, `save_named_assets`, `build_project`, `run_automation_tests`, `undo_last_transaction`

**Layer 2：新增 Channel A 资产创建工具**
`create_level`, `create_material`, `create_material_instance`, `create_widget_blueprint`, `set_blueprint_defaults`, `configure_gamemode_bp`, `configure_world_settings`, `open_level`, `save_all`

**Layer 3：通用兜底**
`run_editor_python` — 执行任意 Python Editor Scripting

### 文件结构
```
Plugins/AgentBridge/MCP/
├── server.py              ← MCP 入口（stdio，~200 行）
├── naming.py              ← 命名/路径规范
├── rc_channel.py          ← import remote_control_client
├── py_channel.py          ← Python Editor Scripting 执行
├── bridge_tools.py        ← 已有 15 个工具的 MCP 包装
├── asset_tools.py         ← 新增资产创建工具
└── README.md

.mcp.json                 ← 项目根目录 Claude Code 配置
```

---

## 十、Self-Healing Loop（来自 Gemini 方案）

```
Claude 生成 Dynamic Spec → Lowering → Build IR → Reviewed Handoff v2
  → Orchestrator 执行 Run Plan → Bridge/MCP 调用 UE5
  → Verifier 验证结果（容差 location ≤ 0.01cm, rotation ≤ 0.01°）
  │
  ├── 成功 → 继续下一步
  └── 失败 → error.schema.json 结构化错误 + 上下文反馈给 Claude
        → Claude 分析原因，修正 IR 或 C++ 代码
        → 重新降级 + 执行
        → 最多重试 3 次，超过则人工介入
```

---

## 十一、目录重构

### 插件层新目录（`Plugins/AgentBridge/`）

```
Compiler/
  intake/                   # Design Intake 主入口
  planner/                  # Planner / Routing 主入口
  skill_runtime/            # Skill Runtime 主入口
  cross_review/             # Cross-Spec Review 主入口
  lowering/                 # Lowering Pipeline 主入口

SkillTemplates/
  base_domains/             # 通用 Skill（intake/routing/review/validation）
  genre_packs/boardgame/monopoly_like/  # Monopoly 6 个 Skill Templates
  project_local/            # 项目特有约束模板
  external_cache/           # 外部缓存模板（Phase 8 不做）

StaticBase/
  schemas/                  # Static Spec Schema
  vocabulary/               # 静态词表
  lowering_maps/            # 语义→引擎映射表

IR/
  build_ir.schema.json
  validation_ir.schema.json

Execution/
  run_plan/
  executor/
  recovery/

Validation/
  readback/
  evidence/
  regression/

MCP/                        # MCP Server（新增）

Schemas/                    # 新增 6 个 Schema（见下）
```

### 必须新增的 6 个 Schema

| Schema | 用途 |
|--------|------|
| `planner_output.schema.json` | Planner 输出结构约束 |
| `skill_fragment.schema.json` | Skill Artifact 统一输出约束 |
| `cross_review_report.schema.json` | Cross-Spec Review 报告约束 |
| `build_ir.schema.json` | Build IR 结构约束 |
| `reviewed_handoff_v2.schema.json` | Handoff v2 边界约束 |
| `gdd_projection.schema.json` | GDD Projection 结构约束 |

---

## 十二、C++ 游戏代码（Claude Code 直接写文件）

Claude 读取 GDD Part B，直接写入 `Source/Mvpv4TestCodex/` 下的 .h/.cpp 文件：

| 类别 | 文件 |
|------|------|
| 枚举/结构体 | `EMTileType`, `EMColorGroup`, `EGamePhase`, `FMTileInfo` |
| 核心类 | `MGameMode`, `MGameState`, `MPlayerState`, `MPlayerController` |
| 棋盘类 | `MBoardManager`, `MTile` |
| 玩法类 | `MPlayerPawn`, `MDice` |
| UI 基类 | `MGameHUDWidget`, `MPopupWidget` |

### 命名规范
| 资产类型 | 路径 | 前缀 | 示例 |
|---------|------|------|------|
| 关卡 | `/Game/Maps/` | `L_` | `L_BoardLevel` |
| Blueprint | `/Game/Blueprints/Core/` | `BP_` | `BP_MGameMode` |
| 材质母版 | `/Game/Materials/` | `M_` | `M_TileBase` |
| 材质实例 | `/Game/Materials/Instances/` | `MI_` | `MI_Brown` |
| Widget | `/Game/UI/` | `WBP_` | `WBP_GameHUD` |

### 玩家输入设计
Phase 1 热座模式，PIE 启动即开始。全部交互通过 UMG 按钮：
- 掷骰 → `WBP_DicePopup [掷骰子]`
- 无主地产 → `WBP_BuyPopup [购买] / [放弃]`
- 他人地产 → `WBP_InfoPopup "支付租金 $X" [确认]`
- 监狱 → `WBP_JailPopup [支付$50] / [掷骰子]`
- 游戏结束 → `WBP_InfoPopup "玩家X获胜！" [再来一局]`

---

## 十三、4 个里程碑（来自 Phase 8 Milestones and Acceptance）

### M1：Compiler Contracts Reset

**目标**：建立新主链契约层，固定 GDD 投影方式。

**必交付件**：
- 文档：`Skill_Template_Pack_v1.md`, `Planner_Output_Model_v1.md`, `Dynamic_Spec_Families_v1.md`, `Lowering_Pipeline_v1.md`, `Reviewed_Handoff_v2_Design.md`, `MonopolyGame_GDD_Projection_v1.md`
- Schema：6 个新 Schema（planner_output / skill_fragment / cross_review_report / build_ir / reviewed_handoff_v2 / gdd_projection）

**验收标准**：
1. 文档与 Schema 字段定义一致
2. 新链路对象均有正式命名与边界
3. Reviewed Handoff 已升级到 v2 设计
4. Dynamic Spec Family 已脱离默认 scene_spec 中心
5. GDD Part A/B 投影方式已正式化
6. 明确 Phase 1 / Phase 2 边界

**失败判定**：Skill 仍被描述为 Python 函数 / Dynamic Spec 仍默认为 scene actors / 无 Handoff v2 设计 / 无 GDD projection / 无 Phase 边界

### M2：Planner + Skill Runtime Skeleton

**目标**：让新主链上游代码骨架真正存在。

**必交付件**：
- 代码骨架：`Compiler/intake/`, `Compiler/planner/`, `Compiler/skill_runtime/`, `Compiler/cross_review/`, `Compiler/lowering/`
- 适配代码：Reviewed Handoff v2 builder, Build IR builder, 旧链路兼容 adapter
- 绑定 GDD 的输出样例：`gdd_projection.json`, `planner_output.sample.json`
- MCP Server 骨架：`Plugins/AgentBridge/MCP/`

**验收标准**：
1. 可以从 GDD 输入开始，跑到 planner 输出
2. Planner 输出符合 `planner_output.schema.json`
3. GDD projection 可分出 board_layout / tile_catalog / turn_loop / property_rules / jail_rules / ui_requirements / phase2_notes
4. Skill Runtime 至少可调起一个模板，产出合法 fragment
5. Cross-Review 主入口存在
6. Lowering 主入口存在

**失败判定**：Planner 只是旧 Mode Router 改名 / Skill Runtime 仍调用旧 Python builder / GDD projection 不存在 / 无法产出合法 fragment

### M3：MonopolyGame Vertical Slice

**目标**：用 GDD 把新主链真正打穿一次。

**必交付件**：
- 6 个 Skill Templates（完整 manifest + prompt + schema + examples）
- 样例输入：`GDD_MonopolyGame.md`
- 样例输出链：`gdd_projection.json` → `planner_output.json` → `skill_fragments/*.json` → `cross_review_report.json` → `reviewed_dynamic_spec_tree.json` → `build_ir.json` → `reviewed_handoff_v2.json`
- C++ 游戏代码（8 个核心类）
- 执行证据：运行日志、readback 结果、截图/快照

**验收标准**：
1. 系统能自动识别 GDD 为 `boardgame / monopoly-like`
2. 系统能自动锁定 Phase 1
3. 系统能选择 6 个 Skill Templates
4. 每个 Template 通过 Skill Runtime 产生合法 fragment
5. Cross-Spec Review 产出统一 reviewed dynamic spec tree
6. Lowering 产出合法 Build IR
7. Execution 消费 Build IR，不直接依赖旧 `scene_spec.actors`
8. UE5 工程内生成最小可运行模板
9. 最小流程能实际执行至少一局
10. 输出有验证记录与证据留存

**失败判定**：切片靠手写 Python 打通 / Dynamic Spec Tree 是旧 scene_spec 换皮 / Build IR 是旧 Run Plan 改名 / Execution 仍从 scene_spec.actors 读取 / 做进了 Phase 2 / 无可运行证据

### M4：Compatibility Cleanup + Final Acceptance

**目标**：清理旧链路角色，完成最终验收。

**必交付件**：
- 旧链路兼容说明
- 新旧入口关系说明
- Phase 8 验收报告
- MonopolyGame 切片证据归档
- 回归检查结果（230 条现有测试不破坏）

**验收标准**：
1. 旧链路已降级为 compatibility adapter / fallback
2. 新主链已成为默认正式入口
3. 全流程证据完整
4. 关键文档/Schema/样例/证据均可追溯
5. "为什么不做 Phase 2"有明确书面边界

---

## 十四、3 轮实施顺序

### 第 1 轮：Contracts + Skeleton（对应 M1 + M2）

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 创建新目录骨架（Compiler/5 个子目录 + SkillTemplates + StaticBase + IR） | 目录结构 |
| 2 | 编写 6 个新 Schema | `Schemas/` 下 6 个 .schema.json |
| 3 | 创建 Knowledge Pack（改造现有 boardgame genre pack） | `SkillTemplates/base_domains/` |
| 4 | 创建 6 个 Monopoly Skill Template Pack 骨架 | `SkillTemplates/genre_packs/boardgame/monopoly_like/` |
| 5 | 实现 Compiler 五段主入口空壳 | `Compiler/intake/` ~ `Compiler/lowering/` |
| 6 | 设计 Reviewed Handoff v2 | Schema + builder |
| 7 | MonopolyGame GDD Projection 设计 | `gdd_projection.schema.json` + 样例 |
| 8 | 搭建 MCP Server 骨架 | `Plugins/AgentBridge/MCP/` + `.mcp.json` |

### 第 2 轮：MonopolyGame 切片打通（对应 M3）

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | 完善 6 个 Skill Templates（prompt + schema + examples） | 完整 Skill Template Pack |
| 2 | 写 C++ 游戏代码（8 个核心类） | `Source/Mvpv4TestCodex/` |
| 3 | 生成 GDD Projection | `gdd_projection.json` |
| 4 | 生成 Planner Output | `planner_output.json` |
| 5 | 生成 Skill Fragments | `skill_fragments/*.json` |
| 6 | 执行 Cross-Spec Review | `cross_review_report.json` + `reviewed_dynamic_spec_tree.json` |
| 7 | 执行 Lowering | `build_ir.json` |
| 8 | 组装 Reviewed Handoff v2 | `reviewed_handoff_v2.json` |

### 第 3 轮：Execution 接入与验收（对应 M3 后半 + M4）

| 序号 | 任务 | 产出 |
|------|------|------|
| 1 | Build IR → Executor 接入（通过 MCP） | 可执行 Run Plan |
| 2 | 编译 C++ → MCP: build_project | 编译成功 |
| 3 | MCP 创建关卡 + 资产 + Widget | UE5 工程内可见 |
| 4 | 验证 + Self-Healing Loop | readback 结果 + 截图 |
| 5 | 回归测试 230 条用例 | 不破坏现有 |
| 6 | 证据归档 | evidence/ 目录 |
| 7 | 旧链路兼容处理 | compatibility adapter |
| 8 | Phase 8 最终验收报告 | `Phase_8_Acceptance_Report.md` |

---

## 十五、5 条明确禁止

1. **禁止**继续优先扩写 Monopoly 业务生成型 Python 脚本
2. **禁止**继续把 `scene_spec` 当作未来主链的默认中心
3. **禁止**把注意力放到第三个 genre pack
4. **禁止**现在就做"自动生成并永久入库的新 Skill"
5. **禁止**只改文档，不改主入口与数据流

---

## 十六、Definition of Done（6 条同时成立）

1. **DoD-1**：系统主入口已转向新链路（GDD → Intake → Planner → Skill Runtime → ... → Execution）
2. **DoD-2**：Skill 成为不可绕过的一等对象（MonopolyGame 切片中不再主要依靠手写 Python 业务生成逻辑）
3. **DoD-3**：Dynamic Spec Tree 不再默认等价于 scene_spec
4. **DoD-4**：MonopolyGame Phase 1 切片打通（路由 → Skill → Dynamic Spec → Review → Lowering → Execution → 最小可玩模板）
5. **DoD-5**：Phase 1 范围严格收敛（不允许用"顺手做了在线多人"冲淡主线）
6. **DoD-6**：有完整证据链（文档 + Schema + GDD projection + planner output + skill fragments + reviewed spec tree + build ir + 执行证据）

---

## 十七、关键文件清单

### 必读设计文档
- `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` — 工具契约
- `Plugins/AgentBridge/Docs/ue5_capability_map.md` — 能力映射
- `Plugins/AgentBridge/Docs/architecture_overview.md` — 系统架构
- `PhaseDoc/AGENT_UE5_Skill_First_Compiler_Reset_Plan.md` — 重构方案
- `PhaseDoc/AGENT_UE5_Claude_Codex_Execution_Taskbook.md` — 执行任务书
- `PhaseDoc/AGENT_UE5_Phase_8_Milestones_and_Acceptance.md` — 里程碑与验收

### 6 份参考设计文档
- `PhaseDoc/Skill_Template_Pack_v1.md` — Skill Template 标准
- `PhaseDoc/Planner_Output_Model_v1.md` — Planner 输出模型
- `PhaseDoc/Dynamic_Spec_Families_v1.md` — 动态规格家族
- `PhaseDoc/Lowering_Pipeline_v1.md` — Lowering 管线
- `PhaseDoc/Reviewed_Handoff_v2_Design.md` — Handoff v2 设计
- `PhaseDoc/MonopolyGame_GDD_Projection_v1.md` — GDD 投影设计

### 复用代码（不修改）
- `Scripts/bridge/` — Bridge 三通道
- `Scripts/orchestrator/` — Orchestrator + Verifier + Report
- `Scripts/compiler/handoff/` — Handoff Builder + Serializer
- `Scripts/validation/` — Schema 校验
- `Source/AgentBridge/` — C++ Plugin
- `Schemas/common/`, `Schemas/feedback/`, `Schemas/write_feedback/` — 已稳定 Schema

### 改造代码
- `Skills/genre_packs/boardgame/` → 降格为 Knowledge Pack
- `Skills/genre_packs/boardgame/required_skills/*.py` → 降格为 Lowerer

### 新建文件
- `Plugins/AgentBridge/Compiler/` — 5 个子目录（主链骨架）
- `Plugins/AgentBridge/SkillTemplates/` — 模板库
- `Plugins/AgentBridge/MCP/` — MCP Server
- `Plugins/AgentBridge/Schemas/capability_ir/` — IR Schema
- `Source/Mvpv4TestCodex/` — 大富翁 C++ 代码
- `.mcp.json` — Claude Code 配置

---

## 十八、验证方案

### 框架验证
- `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` — Schema 校验
- `python Plugins/AgentBridge/Tests/run_system_tests.py` — 230 条回归测试不破坏

### 主链验证
- GDD → gdd_projection.json：字段完整性、Phase 1/2 分离
- planner_output.json：符合 schema、选中 6 个 Skill
- skill_fragments/*.json：每个 fragment 符合 skill_fragment.schema.json
- cross_review_report.json：28 格闭合、规则一致性
- build_ir.json：14 个 IR 对象完整
- reviewed_handoff_v2.json：符合 v2 schema

### 端到端验证
- MCP: build_project → 编译成功
- MCP: create_level + spawn + configure → UE5 工程可见
- MCP: list_actors + get_actor_state → readback 验证
- MCP: capture_screenshot → 视觉确认
- PIE 启动 → 至少完成一局游戏流程
