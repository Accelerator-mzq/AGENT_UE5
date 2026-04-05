# Phase 8 — Skill-First Compiler Reset + MonopolyGame 垂直切片

> 目标引擎版本：UE5.5.4
> 阶段定位：Phase 8 正式开发期
> 架构：Skill-First 6 阶段 Compiler → Reviewed Handoff v2 → Build IR → Execution
> 上一阶段归档：[task6_phase7.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task6_phase7.md)
> 当前阶段索引：[00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
> 统一方案：[Phase8_Plan_Original.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_Plan_Original.md)
> DD-1 详细设计：[Phase8_DD1_Schema_and_Interface_Spec.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_DD1_Schema_and_Interface_Spec.md)
> DD-3 详细设计：[Phase8_DD3_Lowering_Map_and_CPP_Design.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md)
> 交接文档：[Phase8_M3_Handover_to_Execution_Agent.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md)

---

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent。
2. 每个 TASK 内附「先读这些文件」列表——编码 Agent 应在动手前先读完。
3. 每个 TASK 末尾有【验收标准】——全部通过才可进入下一个 TASK。
4. 本工程根目录：`D:\UnrealProjects\Mvpv4TestCodex\`（以下简称 PROJECT_ROOT）
5. 插件目录：`Plugins/AgentBridge/`（以下简称 PLUGIN_DIR）
6. Compiler 产物目录：`ProjectState/phase8/`
7. Phase 8 设计文档目录：`Docs/History/Proposals/`（Phase8_DD1/DD3/Plan_Original/M3_Handover）

## 核心约束

- **不修改**任何现有 C++ 文件（Plugins/AgentBridge/Source/AgentBridge/Private/*.cpp / Public/*.h）
- **不修改**任何现有 Bridge 脚本（Plugins/AgentBridge/Scripts/bridge/*.py）
- **不修改**现有 Orchestrator 核心（orchestrator.py / plan_generator.py / verifier.py / report_generator.py / spec_reader.py）
- **不修改**任何现有测试文件（Plugins/AgentBridge/AgentBridgeTests/）
- **不修改**任何现有稳定 Schema（Schemas/common/ / feedback/ / write_feedback/）
- MonopolyGame 是 Phase 8 唯一垂直切片，不同时做其他游戏
- Phase 8 新增 C++ 代码全部位于项目层 `Source/Mvpv4TestCodex/`，不写入插件层
- 所有新代码带中文注释

## 本期固定规则

1. 根目录 `task.md` 是 Phase 8 当前阶段唯一任务入口。
2. `SystemTestCases.md` 与 `run_system_tests.py` 保持 `230` 条口径不动，Phase 8 新增编号在 M4 统一补录。
3. Build IR 的 14 个 build_steps 按 6 个 Batch 顺序执行，每 Batch 编译通过后再进入下一个。
4. Compiler 主链产物全部输出到 `ProjectState/phase8/`。

## 里程碑定义

| 里程碑 | 内容 | 对应 TASK | 状态 |
|--------|------|-----------|------|
| DD-1 | Schema 完整字段定义 + Compiler 五段接口规约 | TASK 02 的前置设计 | ✅ 已完成 |
| M1 | Compiler Contracts Reset（6 Schema + 5 段 Python 骨架） | TASK 02 | ✅ 已完成 |
| DD-2 | Skill Template Pack + MCP Server 详细设计与实现 | TASK 03 | ✅ 已完成 |
| M2 | Main Chain 数据生成（5 阶段 + Handoff 组装） | TASK 04 | ✅ 已完成 |
| DD-3 | Lowering 映射表 + C++ 类详细设计 + UMG 布局方案 | TASK 05 | ✅ 已完成 |
| **M3** | **MonopolyGame 垂直切片执行（14 Build Steps）** | **TASK 06** | ⬜ 进行中 |
| M4 | 兼容性清理 + 最终验收 | TASK 07 | ⬜ 待执行 |

## 任务总览

阶段 1 入口统一（01）> 阶段 2 Schema + Compiler 骨架（02）> 阶段 3 Skill Template + MCP（03）> 阶段 4 Main Chain 数据（04）> 阶段 5 C++ 设计 + 交接（05）> 阶段 6 垂直切片执行（06）> 阶段 7 验收（07）

---
---

# 阶段 1：入口统一

---

## TASK 01：完成 Phase 8 文档切换与入口统一 ✅

```
目标：把项目层和插件层入口统一切到 Phase 8 正式开发期口径。
归档 Phase 6 验收基线，更新所有 "Phase 7 已归档/下一阶段待规划" 描述为 Phase 8 Active。

前置依赖：无

先读这些文件：
- Docs/Current/00_Index.md（当前写的是 "Phase 7 已归档"）
- Docs/Current/01_Project_Baseline.md（基线停留在 Phase 7）
- AGENTS.md §3.2（阅读顺序——需要增加 Phase 8 文档路径）
- CLAUDE.md（阶段描述、阅读顺序、可修改文件清单需更新）
- Plugins/AgentBridge/Docs/architecture_overview.md（总链路图需增加 Skill-First 6 阶段）
读完应掌握：哪些文件包含旧阶段口径需要更新，Phase 8 新增了哪些文档路径需要加入导航

涉及文件（全部修改，不新增）：
- Docs/Current/00_Index.md ~ 07_Evidence_And_Artifacts.md
- Docs/Current/08_Playable_Runtime_Acceptance.md（归档到 Docs/History/）
- CLAUDE.md
- AGENTS.md
- task.md
- Plugins/AgentBridge/Docs/architecture_overview.md
- Plugins/AgentBridge/Docs/compiler_design.md
- Plugins/AgentBridge/Docs/reviewed_handoff_design.md
- Plugins/AgentBridge/Docs/skills_and_specs_overview.md
- Plugins/AgentBridge/Docs/greenfield_pipeline.md

═══════════════════════════════════════════════════════
Step 1: 更新 Docs/Current/* 切换到 Phase 8 口径
═══════════════════════════════════════════════════════

  需要更新的文件和关键变更：

  00_Index.md:
    - 阶段名称 → "Phase 8 — Skill-First Compiler Reset + MonopolyGame 垂直切片"
    - 状态 → Active
    - 增加 Phase 8 事实来源（task.md / Docs/History/Proposals/ / ProjectState/phase8/）

  01_Project_Baseline.md:
    - 增加 Phase 8 已产出事实（6 Schema / Compiler 骨架 / Skill Template / MCP / Main Chain 11 JSON）

  02_Current_Phase_Goals.md:
    - 替换为 Phase 8 目标（Skill-First Reset + MonopolyGame 垂直切片）
    - 成功标准：11 JSON 产出 + 12 验证点 + 230 回归

  03_Active_Backlog.md:
    - DD-1~DD-3 / M1~M2 已完成
    - M3 进行中（交接给 Execution Agent）
    - M4 待执行
    - Phase 7 carry-over 处置

  04_Open_Risks.md:
    - 替换为 Phase 8 风险（C++ 编译兼容 / 动画占位 / Build IR 偏差）

  05_Implementation_Boundary.md:
    - 允许：Source/Mvpv4TestCodex/ C++ 新增、Schemas/ 新增、Compiler/ 新增
    - 不允许：已稳定 C++ / Bridge / Orchestrator / Tests / 稳定 Schema

  06_Current_Task_List.md:
    - 指向根目录 task.md

═══════════════════════════════════════════════════════
Step 2: 归档 Phase 6 验收基线
═══════════════════════════════════════════════════════

  cp Docs/Current/08_Playable_Runtime_Acceptance.md Docs/History/08_Playable_Runtime_Acceptance_Phase6.md
  rm Docs/Current/08_Playable_Runtime_Acceptance.md

═══════════════════════════════════════════════════════
Step 3: 更新 CLAUDE.md
═══════════════════════════════════════════════════════

  需要变更的部分：
  - "最后更新" → 2026-04-04
  - "进入项目后的阅读顺序" → 增加 task.md 和交接文档
  - "可以修改的文件" → 增加 Phase 8 新增 Schema / Compiler / SkillTemplates / MCP
  - "当前阶段" → "Phase 8 正式开发期"

═══════════════════════════════════════════════════════
Step 4: 更新 AGENTS.md
═══════════════════════════════════════════════════════

  需要变更的部分：
  - 文档版本 → v0.9（Phase 8 正式开发期）
  - §2.6 附加文档路径 → 增加 Phase 8 设计文档和交接文档
  - §3.2 阅读顺序 → 步骤 6 改为 task.md，增加步骤 9 交接文档

═══════════════════════════════════════════════════════
Step 5: 更新插件层文档
═══════════════════════════════════════════════════════

  architecture_overview.md:
    - 版本 → v0.8.0
    - §1.1 总链路 → 增加 Skill-First 6 阶段主链图
    - §1.4 版本变更 → 增加 v0.8.0 条目

  compiler_design.md:
    - 版本 → v0.8.0
    - §2 → 增加 Phase 8 新链路（Compiler/ 目录结构），旧链路标注保留

  reviewed_handoff_design.md:
    - 版本 → v0.8.0
    - §1 → 增加 v1/v2 版本演进表

  skills_and_specs_overview.md:
    - 版本 → v0.8.0
    - §2.3 → 增加 Skill Template Pack 三层结构说明

  greenfield_pipeline.md:
    - 版本 → v0.8.0
    - §2 → 增加 Phase 8 Skill-First 新链路

═══════════════════════════════════════════════════════
Step 6: 验证
═══════════════════════════════════════════════════════

  grep -r "Phase 7 已归档" Docs/Current/
  # 预期：无匹配（已全部替换为 Phase 8 口径）

  grep -r "下一阶段待规划" Docs/Current/
  # 预期：无匹配

  grep "Phase 8" CLAUDE.md
  # 预期：至少 1 行匹配

  grep "v0.9" AGENTS.md
  # 预期：匹配到文档版本行

  test ! -f Docs/Current/08_Playable_Runtime_Acceptance.md
  # 预期：文件不存在（已归档）

  test -f Docs/History/08_Playable_Runtime_Acceptance_Phase6.md
  # 预期：文件存在

【验收标准】
- Docs/Current/* 不再出现 "Phase 7 已归档" 或 "下一阶段待规划"
- CLAUDE.md 当前阶段描述包含 "Phase 8"
- AGENTS.md 版本为 v0.9
- 08_Playable_Runtime_Acceptance.md 已从 Current/ 移至 History/
- 插件层 5 个文档版本号均为 v0.8.0
- 不影响任何 C++ / Bridge / Orchestrator / Tests 文件
```

---
---

# 阶段 2：Schema + Compiler 骨架

---

## TASK 02：部署 6 个 Compiler Schema + 5 段 Python 骨架 ✅

```
目标：将 Phase 8 Skill-First Compiler 的 6 个 JSON Schema 和 5 段 Python 骨架部署到插件层。
这 6 个 Schema 定义了 Compiler 主链 5 阶段 + Handoff v2 的数据契约。
Python 骨架提供 get_schema() / create_template() / save() 的最小可调用接口。

前置依赖：TASK 01 完成

先读这些文件：
- Docs/History/Proposals/Phase8_DD1_Schema_and_Interface_Spec.md（完整字段定义——6 个 Schema 的每个字段、类型、required/optional）
- Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json（v1 Schema——理解现有格式约定）
- Plugins/AgentBridge/Schemas/common/primitives.schema.json（$defs 引用机制）
读完应掌握：6 个 Schema 的完整字段定义，现有 Schema 的组织方式

涉及文件：全部新增，不修改任何现有 Schema 文件。

═══════════════════════════════════════════════════════
Step 1: 创建 6 个 Schema JSON 文件
═══════════════════════════════════════════════════════

  目标路径和关键字段：

  PLUGIN_DIR/Schemas/gdd_projection.schema.json
    required: [projection_version, projection_id, source_gdd, game_identity, phase_scope, design_domains]
    game_identity.game_type enum: [board_strategy, rpg, action, puzzle, simulation]
    game_identity.presentation_model enum: [top_down_2d, top_down_3d, side_scroll, first_person, third_person, isometric]

  PLUGIN_DIR/Schemas/planner_output.schema.json
    required: [planner_meta, project_intent, routing_decision, selected_skill_instances]
    selected_skill_instances[].skill_instance_id pattern: ^skill-[a-z0-9_]+$
    selected_skill_instances[].priority enum: [critical, high, medium, low]

  PLUGIN_DIR/Schemas/skill_fragment.schema.json
    required: [skill_instance_id, template_id, phase_scope, emitted_families, spec_fragments, status]
    status enum: [completed, partial, failed]

  PLUGIN_DIR/Schemas/cross_review_report.schema.json
    required: [review_id, review_version, input_fragment_ids, review_status, reviewed_dynamic_spec_tree, review_checks]
    review_status enum: [approved, approved_with_warnings, blocked]
    review_checks[].result enum: [pass, warning, fail]

  PLUGIN_DIR/Schemas/build_ir.schema.json
    required: [ir_version, ir_id, source_review_id, phase_scope, build_steps, lowering_report]
    build_steps[].ir_action enum: 14 个值（create_board_ring_layout / create_tile_actors / ... / attach_validation_hooks）
    validation_ir[].check_type enum: [actor_exists, actor_count, property_value, state_machine_state, ui_widget_exists, gameplay_rule, data_consistency]

  PLUGIN_DIR/Schemas/reviewed_handoff_v2.schema.json
    required: [handoff_meta, project_context, planner_summary, reviewed_dynamic_spec_tree, build_ir, approval]
    handoff_meta.handoff_version const: "2.0"
    handoff_meta.handoff_mode enum: [greenfield_bootstrap, brownfield_expansion]
    approval.approval_status enum: [approved, approved_with_warnings, blocked]

═══════════════════════════════════════════════════════
Step 2: 创建 5 段 Compiler Python 骨架
═══════════════════════════════════════════════════════

  目标目录结构：
    PLUGIN_DIR/Compiler/
    ├── __init__.py
    ├── intake/
    │   ├── __init__.py
    │   └── design_intake.py       ← get_schema(), create_projection_template(), save_projection()
    ├── planner/
    │   ├── __init__.py
    │   └── planner.py             ← get_schema(), scan_skill_templates(), create_planner_output_template(), save_planner_output()
    ├── skill_runtime/
    │   ├── __init__.py
    │   └── skill_runtime.py       ← get_schema(), load_template_pack(), create_fragment_template(), save_fragment()
    ├── cross_review/
    │   ├── __init__.py
    │   └── cross_review.py        ← get_schema(), load_all_fragments(), create_review_report_template(), save_review_report()
    └── lowering/
        ├── __init__.py
        └── lowering.py            ← get_schema(), create_build_ir_template(), save_build_ir()

  每段骨架的 get_schema() 返回对应 Schema 的 dict。
  每段骨架的 create_*_template() 返回一个符合 Schema required 字段的空模板 dict。
  每段骨架的 save_*() 将 dict 写入 JSON 文件。

═══════════════════════════════════════════════════════
Step 3: 验证 Schema 格式正确
═══════════════════════════════════════════════════════

  python -c "import json; s=json.load(open('Plugins/AgentBridge/Schemas/gdd_projection.schema.json')); print('required:', s['required'])"
  # 预期：required: ['projection_version', 'projection_id', 'source_gdd', 'game_identity', 'phase_scope', 'design_domains']

  python -c "import json; s=json.load(open('Plugins/AgentBridge/Schemas/build_ir.schema.json')); print('ir_action enum count:', len(s['properties']['build_steps']['items']['properties']['ir_action']['enum']))"
  # 预期：ir_action enum count: 14

  python -c "import json; s=json.load(open('Plugins/AgentBridge/Schemas/reviewed_handoff_v2.schema.json')); print('handoff_version const:', s['properties']['handoff_meta']['properties']['handoff_version']['const'])"
  # 预期：handoff_version const: 2.0

═══════════════════════════════════════════════════════
Step 4: 验证 Python 骨架可导入
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge
  python -c "from Compiler.intake.design_intake import get_schema, create_projection_template, save_projection; print('✅ intake 可导入')"
  python -c "from Compiler.planner.planner import get_schema, scan_skill_templates; print('✅ planner 可导入')"
  python -c "from Compiler.skill_runtime.skill_runtime import get_schema, load_template_pack; print('✅ skill_runtime 可导入')"
  python -c "from Compiler.cross_review.cross_review import get_schema, load_all_fragments; print('✅ cross_review 可导入')"
  python -c "from Compiler.lowering.lowering import get_schema, create_build_ir_template; print('✅ lowering 可导入')"

═══════════════════════════════════════════════════════
Step 5: 验证现有 Schema 校验链不受影响
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：原有 12 个 example 全部通过（新增 Schema 不影响现有校验）

═══════════════════════════════════════════════════════
Step 6: 验证现有文件未被修改
═══════════════════════════════════════════════════════

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/AgentBridgeTests/
  git diff Plugins/AgentBridge/Schemas/common/
  git diff Plugins/AgentBridge/Schemas/feedback/
  # 预期：全部无变更

【验收标准】
- Schemas/ 下新增 6 个 .schema.json 文件，全部可被 json.load 解析
- Compiler/ 下新增 5 段 Python 骨架（11 个 .py 文件），全部可 import
- 现有 12 个 Schema example 校验仍通过（validate_examples.py --strict）
- 现有稳定文件无变更
```

---
---

# 阶段 3：Skill Template + MCP

---

## TASK 03：部署 6 套 Skill Template Pack + MCP Server ✅

```
目标：将 6 套 Monopoly Skill Template Pack 和 MCP Server 部署到插件层。
Skill Template Pack 是 Compiler Stage 3（Skill Runtime）的输入模板，定义了每种游戏子系统的编译策略。
MCP Server 是 Execution 阶段的工具入口，提供 28 个工具覆盖 L1/L2/L3 三层。

前置依赖：TASK 02 完成

先读这些文件：
- Docs/History/Proposals/Phase8_Plan_Original.md §7（Skill Template Pack 三层结构：Template / Instance / Artifact）
- Docs/History/Proposals/Phase8_Plan_Original.md §9（MCP Server 28 工具设计）
- Plugins/AgentBridge/Docs/tool_contract_v0_1.md（工具契约：统一响应格式 {status, summary, data, warnings, errors}）
- Plugins/AgentBridge/Scripts/bridge/remote_control_client.py（RC API HTTP:30010——MCP rc_channel 需要封装此客户端）
读完应掌握：Template Pack 的 6 文件结构（manifest/prompt/schema/evaluator），MCP 的三层 28 工具定义

涉及文件：全部新增，不修改任何现有文件。

═══════════════════════════════════════════════════════
Step 1: 创建 6 套 Skill Template Pack
═══════════════════════════════════════════════════════

  目标路径：PLUGIN_DIR/SkillTemplates/genre_packs/boardgame/monopoly_like/

  6 套 Template（每套 6 个文件）：

  monopoly_board_topology/
    manifest.yaml — template_id: monopoly.board_topology.phase1, emits: [board_topology_spec], depends_on: []
    system_prompt.md — 通用 boardgame 棋盘拓扑 Agent 角色提示
    domain_prompt.md — Monopoly 28 格环形布局特定指令
    input_selector.yaml — 从 GDD Projection 中读取 design_domains.board_layout / tile_catalog
    output_schema.json — board_shape / tile_count / tiles_per_side / corner_tiles / tile_index_list
    evaluator_prompt.md — 审查 28 格完整性、四角位置、side 分配

  monopoly_turn_and_dice_flow/
    manifest.yaml — emits: [turn_flow_spec], depends_on: [board_topology]
    output_schema.json — game_init / turn_state_machine(states+transitions) / dice_rules / movement_rules / player_rotation

  monopoly_tile_event_dispatch/
    manifest.yaml — emits: [tile_system_spec], depends_on: [board_topology]
    output_schema.json — tile_types[] / tile_data_table[28] / color_groups{7} / event_dispatch_matrix[8]

  monopoly_property_economy/
    manifest.yaml — emits: [property_economy_spec], depends_on: [board_topology, tile_event_dispatch]
    output_schema.json — initial_funds / ownership_model / purchase_rules / rent_rules / tax_rules / payment_flows

  monopoly_jail_and_bankruptcy/
    manifest.yaml — emits: [jail_rule_spec, bankruptcy_rule_spec], depends_on: [turn_and_dice, property_economy]
    output_schema.json — jail_system / bankruptcy_system / game_end_condition

  monopoly_phase1_ui_flow/
    manifest.yaml — emits: [ui_flow_spec], depends_on: [turn_and_dice, property_economy, jail_and_bankruptcy]
    output_schema.json — hud_spec / popup_specs[7] / state_bindings / widget_lifecycle

═══════════════════════════════════════════════════════
Step 2: 创建 MCP Server
═══════════════════════════════════════════════════════

  目标路径：PLUGIN_DIR/MCP/

  server.py — MCP 主入口
    - wrap_bridge_query(): 封装 L1 查询工具
    - wrap_bridge_write(): 封装 L1 写工具
    - create_level() / create_material() / create_widget_blueprint() / run_editor_python(): L2 工具实现
    - MCP registration skeleton（TODO: M3 时完善）

  tool_definitions.py — 28 个工具定义
    - LAYER1_QUERY_TOOLS (7): get_actors_in_level / get_actor_properties / get_level_info / ...
    - LAYER1_WRITE_TOOLS (6): spawn_actor / set_actor_property / delete_actor / ...
    - LAYER1_SERVICE_TOOLS (5): build_project / run_automation_test / ...
    - LAYER2_ASSET_TOOLS (9): create_level / create_material / create_widget_blueprint / run_editor_python / ...
    - LAYER3_TOOLS (1): execute_raw_command

  naming.py — 资产命名规范
    - ASSET_PATHS dict: Level / Blueprint / Material / Widget 默认路径
    - ASSET_PREFIXES dict: L_ / BP_ / M_ / MI_ / WBP_ / DA_ / T_
    - validate_asset_name() / get_default_path() / make_full_asset_path()

  py_channel.py — Channel A (Python Editor Scripting via RC API /remote/script/run)
  rc_channel.py — Channel B (直接调用现有 remote_control_client.py)
  README.md — 架构和工具层文档

  项目根目录 .mcp.json — Claude Code MCP 配置指向 server.py

═══════════════════════════════════════════════════════
Step 3: 验证 Skill Template Pack
═══════════════════════════════════════════════════════

  python -c "
  import yaml, os
  base = 'Plugins/AgentBridge/SkillTemplates/genre_packs/boardgame/monopoly_like'
  packs = os.listdir(base)
  print(f'Template Pack 数量: {len(packs)}')
  assert len(packs) == 6, f'期望 6 个，实际 {len(packs)}'
  for p in packs:
      m = yaml.safe_load(open(os.path.join(base, p, 'manifest.yaml'), encoding='utf-8'))
      print(f'  {p}: template_id={m[\"template_id\"]}, emits={m[\"emits\"]}')
  print('✅ 6 套 Template Pack 全部可解析')
  "
  # 预期：6 套 Pack，每套 manifest 包含 template_id 和 emits

═══════════════════════════════════════════════════════
Step 4: 验证 MCP Server
═══════════════════════════════════════════════════════

  python -c "
  import sys; sys.path.insert(0, 'Plugins/AgentBridge/MCP')
  from tool_definitions import LAYER1_QUERY_TOOLS, LAYER1_WRITE_TOOLS, LAYER1_SERVICE_TOOLS, LAYER2_ASSET_TOOLS, LAYER3_TOOLS
  total = len(LAYER1_QUERY_TOOLS) + len(LAYER1_WRITE_TOOLS) + len(LAYER1_SERVICE_TOOLS) + len(LAYER2_ASSET_TOOLS) + len(LAYER3_TOOLS)
  print(f'工具总数: {total}')
  assert total == 28, f'期望 28，实际 {total}'
  print('✅ 28 个工具定义全部可加载')
  "

  python -c "import json; c=json.load(open('.mcp.json')); print('MCP server:', c); print('✅ .mcp.json 可解析')"

【验收标准】
- SkillTemplates/ 下 6 个子目录，每个含 6 个文件（共 36 文件）
- 每套 manifest.yaml 可被 yaml.safe_load 正确解析，包含 template_id / emits / depends_on
- MCP/ 下 6 个文件（server.py / tool_definitions.py / naming.py / py_channel.py / rc_channel.py / README.md）
- tool_definitions.py 可加载 28 个工具定义
- .mcp.json 指向正确入口
- 现有文件无变更
```

---
---

# 阶段 4：Main Chain 数据生成

---

## TASK 04：运行 Compiler 主链生成 MonopolyGame 样本数据 ✅

```
目标：按 Compiler 主链 5 阶段 + Handoff 组装的顺序，为 MonopolyGame Phase 1
生成全套样本数据（11 个 JSON 文件）。数据来源是 GDD_MonopolyGame.md。

前置依赖：TASK 03 完成

先读这些文件：
- ProjectInputs/GDD/GDD_MonopolyGame.md（完整 GDD，698 行）
  Part A（§1-§4）：游戏概述、棋盘设计（28格/7颜色组）、游戏规则（骰子/事件/破产）、UI需求（HUD/弹窗）
  Part B（§5-§10）：UE5 设置、C++ 类定义（8类）、状态机、网络扩展、编辑器操作
- Docs/History/Proposals/Phase8_DD1_Schema_and_Interface_Spec.md §3（Compiler 五段接口规约——每阶段的输入/输出/错误条件）
- Plugins/AgentBridge/Schemas/gdd_projection.schema.json（Stage 1 输出格式）
- Plugins/AgentBridge/Schemas/skill_fragment.schema.json（Stage 3 输出格式）
读完应掌握：GDD 中 28 格数据表的完整内容，每阶段的输入输出关系

涉及文件：全部新增到 ProjectState/phase8/

═══════════════════════════════════════════════════════
Step 1: Stage 1 — Design Intake → GDD Projection
═══════════════════════════════════════════════════════

  输出：ProjectState/phase8/gdd_projection.json

  关键内容：
  - game_identity: {game_type: "board_strategy", subgenre: "monopoly_like", presentation_model: "top_down_3d", player_count_range: [2,4]}
  - phase_scope: {current_phase: "phase1_local_multiplayer", in_scope: 15项, out_of_scope: 10项}
  - design_domains: 28格 tile_catalog + 7 color_groups + turn_loop + property_rules + jail_rules + bankruptcy_rules + ui_requirements
  - ambiguities: 3项（Blue单地产组 / TAX的base_rent语义 / 过起点奖励与入狱互斥）

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase8/gdd_projection.json'))
  assert d['game_identity']['game_type'] == 'board_strategy'
  assert len(d['design_domains']['tile_catalog']) == 28
  assert len(d['design_domains']['color_groups']) == 7
  print(f'✅ GDD Projection: {len(d[\"design_domains\"][\"tile_catalog\"])} tiles, {len(d[\"design_domains\"][\"color_groups\"])} groups')
  "

═══════════════════════════════════════════════════════
Step 2: Stage 2 — Planner → Planner Output
═══════════════════════════════════════════════════════

  输出：ProjectState/phase8/planner_output.json

  关键内容：
  - 6 个 selected_skill_instances，依赖图：
    skill-board(无依赖) → skill-tile-event(依赖board) + skill-turn(依赖board) → skill-economy(依赖board,tile-event) → skill-jail(依赖turn,economy) → skill-ui(依赖turn,economy,jail)
  - 9 个 dynamic_spec_targets
  - 2 个 capability_gaps（umg-auto-layout degraded, animation cosmetic）

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase8/planner_output.json'))
  assert len(d['selected_skill_instances']) == 6
  ids = [s['skill_instance_id'] for s in d['selected_skill_instances']]
  assert 'skill-board' in ids and 'skill-ui' in ids
  print(f'✅ Planner: {len(ids)} skill instances: {ids}')
  "

═══════════════════════════════════════════════════════
Step 3: Stage 3 — Skill Runtime → 6 个 Skill Fragments
═══════════════════════════════════════════════════════

  输出：ProjectState/phase8/skill_fragments/skill-{board,tile-event,turn,economy,jail,ui}.json

  每个 Fragment 的关键 emitted_families：
  - skill-board.json → board_topology_spec（28 tile_index_list，4 corner_tiles）
  - skill-tile-event.json → tile_system_spec（28行 tile_data_table，8种 tile_types，7 color_groups，8条 event_dispatch）
  - skill-turn.json → turn_flow_spec（10 状态 / 12 转换 FSM，2d6 dice_rules，movement_rules，player_rotation）
  - skill-economy.json → property_economy_spec（initial $1500，ownership_model，purchase/rent/tax 规则，5种 payment_flows）
  - skill-jail.json → jail_rule_spec + bankruptcy_rule_spec（入狱条件，保释/$50/掷双数/强制第三回合，破产释放地产，game_end）
  - skill-ui.json → ui_flow_spec（HUD 4元素，7 popup_specs，5 widget_blueprints，10 state_bindings）

  验证：
  python -c "
  import json, os
  frags = os.listdir('ProjectState/phase8/skill_fragments/')
  print(f'Fragment 数量: {len(frags)}')
  assert len(frags) == 6
  for f in sorted(frags):
      d = json.load(open(f'ProjectState/phase8/skill_fragments/{f}'))
      print(f'  {f}: status={d[\"status\"]}, families={d[\"emitted_families\"]}')
      assert d['status'] == 'completed'
  print('✅ 6 个 Skill Fragment 全部 completed')
  "

═══════════════════════════════════════════════════════
Step 4: Stage 4 — Cross-Spec Review → Cross-Review Report
═══════════════════════════════════════════════════════

  输出：ProjectState/phase8/cross_review_report.json

  关键内容：
  - 13 个 review_checks，结果：11 pass + 2 warning
  - 2 个 issues_found（Blue单地产组 + forced_bail时机），全部 resolved
  - reviewed_dynamic_spec_tree：7 个 family 合并为统一树
  - lowering_ready: true

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase8/cross_review_report.json'))
  assert d['review_status'] in ['approved', 'approved_with_warnings']
  assert d['lowering_ready'] == True
  checks = d['review_checks']
  passes = sum(1 for c in checks if c['result'] == 'pass')
  warns = sum(1 for c in checks if c['result'] == 'warning')
  fails = sum(1 for c in checks if c['result'] == 'fail')
  print(f'✅ Cross-Review: {passes} pass, {warns} warning, {fails} fail → {d[\"review_status\"]}')
  assert fails == 0, '不应有 fail'
  "

═══════════════════════════════════════════════════════
Step 5: Stage 5 — Lowering → Build IR
═══════════════════════════════════════════════════════

  输出：ProjectState/phase8/build_ir.json

  关键内容：
  - 14 个 build_steps（create_board_ring_layout → ... → attach_validation_hooks）
  - 12 个 validation_ir（actor_count / data_consistency / gameplay_rule / ui_widget_exists）
  - lowering_report: 7/7 families_bound, 0 partially_bound

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase8/build_ir.json'))
  assert len(d['build_steps']) == 14
  assert len(d['validation_ir']) == 12
  bound = d['lowering_report']['families_bound']
  print(f'✅ Build IR: {len(d[\"build_steps\"])} steps, {len(d[\"validation_ir\"])} validations, {len(bound)}/7 families bound')
  assert len(bound) == 7
  "

═══════════════════════════════════════════════════════
Step 6: Handoff Assembly → Reviewed Handoff v2
═══════════════════════════════════════════════════════

  输出：ProjectState/phase8/reviewed_handoff_v2.json

  关键内容：
  - handoff_meta.handoff_version: "2.0"
  - approval.approval_status: "approved_with_warnings"
  - 6 个 selected_skill_instances 全部 status=completed
  - reviewed_dynamic_spec_tree: 7 个 family
  - build_ir: 引用 ir.monopoly_phase1.v1
  - metadata: source_gdd → source_projection_id → source_planner_id → source_review_id → source_ir_id 完整链路

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase8/reviewed_handoff_v2.json'))
  assert d['handoff_meta']['handoff_version'] == '2.0'
  assert d['approval']['approval_status'] in ['approved', 'approved_with_warnings']
  skills = d['selected_skill_instances']
  all_completed = all(s['status'] == 'completed' for s in skills)
  print(f'✅ Handoff v2: version={d[\"handoff_meta\"][\"handoff_version\"]}, approval={d[\"approval\"][\"approval_status\"]}, {len(skills)} skills all_completed={all_completed}')
  assert all_completed
  "

═══════════════════════════════════════════════════════
Step 7: 全量完整性验证
═══════════════════════════════════════════════════════

  python -c "
  import json, os
  files = [
      'ProjectState/phase8/gdd_projection.json',
      'ProjectState/phase8/planner_output.json',
      'ProjectState/phase8/cross_review_report.json',
      'ProjectState/phase8/build_ir.json',
      'ProjectState/phase8/reviewed_handoff_v2.json',
  ]
  frags = [f'ProjectState/phase8/skill_fragments/{f}' for f in os.listdir('ProjectState/phase8/skill_fragments/')]
  files.extend(sorted(frags))
  print(f'总文件数: {len(files)}')
  for f in files:
      d = json.load(open(f))
      print(f'  ✅ {f} — JSON 合法')
  assert len(files) == 11
  print('✅ 全部 11 个 JSON 文件合法')
  "

【验收标准】
- ProjectState/phase8/ 下共 11 个 JSON 文件（5 + 6 fragments）
- gdd_projection: 28 tiles, 7 color_groups
- planner_output: 6 skill instances
- 6 个 skill_fragments: 全部 status=completed
- cross_review_report: 0 fail, lowering_ready=true
- build_ir: 14 build_steps, 12 validation_ir, 7/7 families_bound
- reviewed_handoff_v2: version=2.0, approval=approved 或 approved_with_warnings, 全链路 metadata
- 现有文件无变更
```

---
---

# 阶段 5：C++ 设计 + 交接

---

## TASK 05：完成 C++ 类详细设计 + UMG 布局方案 + 交接文档 ✅

```
目标：基于 Build IR 的 14 个构建步骤和 GDD §6 的 C++ 类定义，
产出完整的 C++ 类详细设计文档、UMG Widget 布局方案和 M3 交接文档。
这是 Compiler Agent 的最后一个 TASK，之后交接给 Execution Agent。

前置依赖：TASK 04 完成

先读这些文件：
- ProjectState/phase8/build_ir.json（14 个 build_steps 的完整参数——映射到 C++ 类）
- ProjectInputs/GDD/GDD_MonopolyGame.md §6（C++ 类定义：GameMode/GameState/PlayerState/BoardManager/Tile/PlayerPawn/Dice）
- ProjectInputs/GDD/GDD_MonopolyGame.md §4（UI 需求：HUD + 6 种弹窗）
- ProjectState/phase8/skill_fragments/skill-ui.json（ui_flow_spec：HUD 4元素、7 popup、5 WBP）
读完应掌握：14 步如何映射到 11 个 C++ 类，每个类需要哪些属性/方法，5 个 Widget 需要什么控件

涉及文件：全部新增。
- Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md
- Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md

═══════════════════════════════════════════════════════
Step 1: 创建 DD-3 详细设计文档
═══════════════════════════════════════════════════════

  输出：Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md

  必须包含的 9 个章节：
  1. Build Step → C++ 类映射总表（14 行）
  2. C++ 文件清单（11 对 .h/.cpp，全部在 Source/Mvpv4TestCodex/）
  3. 枚举和结构体定义（EMTileType 8值 / EMColorGroup 8值 / EMTurnState 10值 / EMGamePhase 3值 / FMTileData / FMDiceResult，含 UE5 反射宏）
  4. 9 个核心类详细设计（属性 + 方法签名 + 职责）
  5. 执行顺序与依赖图
  6. 6 Batch 实施顺序表
  7. MCP 工具使用映射
  8. 与 GDD §6 的差异说明
  9. 12 个验证检查点的自动化方式

═══════════════════════════════════════════════════════
Step 2: 创建交接文档（含 UMG 布局方案）
═══════════════════════════════════════════════════════

  输出：Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md

  必须包含的 8 个章节：
  1. 已完成的工作总览
  2. M3 任务定义（交付物 + 6 Batch）
  3. 必读文档索引（按优先级 4 层）
  4. 关键约束（不可修改文件 / 代码位置 / 命名规范 / 能力缺口 / 设计决策）
  5. 数据流全景图
  6. 快速启动清单
  7. UMG Widget 布局方案（5 个 Widget 的控件树 + 视觉参数 + ASCII 线框图）
     - WBP_GameHUD: 左上角，320宽，4 元素（当前玩家/资金列表/回合数/当前格子）
     - WBP_DicePopup: 居中 400×280，两阶段交互（掷骰→显示结果+继续）
     - WBP_BuyPopup: 居中 420×320，地产信息 + 购买/放弃 双按钮
     - WBP_InfoPopup: 居中 400×自适应，通用信息弹窗（租金/税/破产/结束 参数化）
     - WBP_JailPopup: 居中 420×300，保释/掷双数 + 强制保释提示
  8. 公共视觉规范表 + C++ 生成方式示例（NativeConstruct + WidgetTree->ConstructWidget）

═══════════════════════════════════════════════════════
Step 3: 验证
═══════════════════════════════════════════════════════

  test -f Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md && echo "✅ DD-3 存在"
  test -f Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md && echo "✅ 交接文档存在"

  grep "MMonopolyTypes.h" Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md
  # 预期：匹配到文件清单中的 MMonopolyTypes.h

  grep "WBP_GameHUD" Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md
  # 预期：匹配到 UMG 布局方案

  grep "NativeConstruct" Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md
  # 预期：匹配到 C++ 生成方式示例

【验收标准】
- DD-3 文档含 14 行映射表、11 对文件清单、4 enum + 2 struct 完整定义、6 Batch 顺序
- 交接文档含 4 层文档索引、5 个 Widget 控件树 + ASCII 线框图、视觉参数表
- UMG 布局方案经用户评审通过
```

---
---

# 阶段 6：垂直切片执行

---

## TASK 06：执行 MonopolyGame 垂直切片（M3） ⬜

```
目标：根据 Build IR 的 14 个步骤，在 UE5.5.4 项目中实际编写 C++ 代码，
创建场景 Actor，创建 UI Widget，使 MonopolyGame Phase 1 可运行。
按 6 个 Batch 顺序执行，每 Batch 编译通过后再进入下一个。

前置依赖：TASK 05 完成
执行者：Execution Agent（非 Compiler Agent）

先读这些文件：
- Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md（完整交接文档——这是执行蓝图）
  §3 必读文档索引（按优先级阅读）
  §4 关键约束（不可修改文件 / 代码位置 / 命名规范）
  §7 UMG Widget 布局方案（5 个 Widget 的控件树和视觉参数）
- Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md（C++ 类详细设计）
  §3 枚举和结构体定义（含完整 UE5 反射宏代码）
  §4 9 个核心类的属性 + 方法签名
  §5 执行顺序与依赖图
- ProjectState/phase8/build_ir.json（14 个 build_steps 的具体参数和 execution_hints）
- ProjectState/phase8/reviewed_handoff_v2.json（审批状态和能力缺口）
读完应掌握：11 个 C++ 类的完整设计，14 步的具体参数，5 个 Widget 的控件树

涉及文件：全部新增到 Source/Mvpv4TestCodex/

═══════════════════════════════════════════════════════
Step 1 (Batch 1): 创建枚举/结构体 + GameMode/State/PlayerState 壳
═══════════════════════════════════════════════════════

  对应 Build Steps: step-05-game-mode + step-03-tile-metadata(types only)

  新增文件：
    Source/Mvpv4TestCodex/Public/MMonopolyTypes.h
      - EMTileType (8 values)
      - EMColorGroup (8 values: None + 7 groups)
      - EMTurnState (10 values)
      - EMGamePhase (3 values)
      - FMTileData {TileIndex, TileName, TileType, ColorGroup, Price, BaseRent, TaxAmount, OwnerPlayerIndex}
      - FMDiceResult {Die1, Die2, Total, bIsDoubles}

    Source/Mvpv4TestCodex/Public/MMonopolyGameMode.h
    Source/Mvpv4TestCodex/Private/MMonopolyGameMode.cpp
      - 父类: AGameModeBase
      - 属性壳: CurrentTurnState, ConsecutiveDoublesCount, CurrentPlayerIndex
      - BeginPlay() 空实现

    Source/Mvpv4TestCodex/Public/MMonopolyGameState.h
    Source/Mvpv4TestCodex/Private/MMonopolyGameState.cpp
      - 父类: AGameStateBase
      - 属性壳: TileDataArray(TArray<FMTileData>), TurnNumber, GamePhase
      - 10 个 DECLARE_DYNAMIC_MULTICAST_DELEGATE 声明

    Source/Mvpv4TestCodex/Public/MMonopolyPlayerState.h
    Source/Mvpv4TestCodex/Private/MMonopolyPlayerState.cpp
      - 父类: APlayerState
      - 属性: Money=1500, CurrentTileIndex=0, OwnedTileIndices, bIsInJail, JailTurnsRemaining, bIsBankrupt
      - 方法: AddMoney / DeductMoney / CanAfford / AddProperty / RemoveAllProperties

    Source/Mvpv4TestCodex/Public/MMonopolyPlayerController.h
    Source/Mvpv4TestCodex/Private/MMonopolyPlayerController.cpp
      - 父类: APlayerController
      - 空壳，后续用于 UI 输入路由

  验证（Batch 1 编译）：
    # 在 UE5 Editor 中编译，或：
    # 检查 .h 文件中的 UCLASS / USTRUCT / UENUM 宏正确
    python -c "
    import os
    files = ['MMonopolyTypes.h', 'MMonopolyGameMode.h', 'MMonopolyGameState.h', 'MMonopolyPlayerState.h', 'MMonopolyPlayerController.h']
    for f in files:
        path = f'Source/Mvpv4TestCodex/Public/{f}'
        assert os.path.exists(path), f'{path} 不存在'
        content = open(path, encoding='utf-8').read()
        assert 'GENERATED_BODY()' in content or 'GENERATED_USTRUCT_BODY()' in content, f'{f} 缺少 GENERATED_BODY()'
    print('✅ Batch 1: 5 个头文件存在且含 GENERATED_BODY()')
    "

═══════════════════════════════════════════════════════
Step 2 (Batch 2): 创建 BoardManager + Tile + PlayerPawn Actor
═══════════════════════════════════════════════════════

  对应 Build Steps: step-01-board-layout, step-02-tile-actors, step-04-player-tokens

  新增文件：
    Source/Mvpv4TestCodex/Public/MBoardManager.h
    Source/Mvpv4TestCodex/Private/MBoardManager.cpp
      - SpawnBoard(): 生成 28 个 AMTile 环形排列
      - CalculateTileWorldLocation(int32 Index): 计算格子世界坐标
      - 参数: SideLength=700cm, TileSpacing=100cm

    Source/Mvpv4TestCodex/Public/MTile.h
    Source/Mvpv4TestCodex/Private/MTile.cpp
      - 组件: UStaticMeshComponent + UTextRenderComponent
      - 属性: TileIndex, TileData(FMTileData)
      - InitTile(FMTileData) / SetOwnerColor(FLinearColor)

    Source/Mvpv4TestCodex/Public/MPlayerPawn.h
    Source/Mvpv4TestCodex/Private/MPlayerPawn.cpp
      - 组件: UStaticMeshComponent（圆柱体）
      - MoveToTile(FVector, Steps)（占位动画）/ SetPawnColor(FLinearColor)

  验证：编译通过 + 场景中可手动放置 Actor

═══════════════════════════════════════════════════════
Step 3 (Batch 3): 实现回合 FSM + 骰子逻辑
═══════════════════════════════════════════════════════

  对应 Build Steps: step-06-turn-fsm, step-07-dice-logic

  修改文件：
    MMonopolyGameMode.h/.cpp — 增加 FSM 方法实现：
      - SetTurnState(EMTurnState) / OnEnterState(EMTurnState)
      - StartTurn() / OnPlayerRequestRoll() / OnDiceResultReady(FMDiceResult) / OnPawnArrived(int32)
      - EndTurn() / FindNextNonBankruptPlayer()
      - RollDice() → FMDiceResult {FMath::RandRange(1,6) × 2}
      - ResetConsecutiveDoubles()

    新增文件：
    Source/Mvpv4TestCodex/Public/MDice.h
    Source/Mvpv4TestCodex/Private/MDice.cpp
      - RollDice(): FMDiceResult / PlayRollAnimation()（占位）

  验证：
    - val-05: 初始状态 == WaitForRoll
    - val-06: RollDice() 100次，结果全在 [2,12]，doubles检测正确

═══════════════════════════════════════════════════════
Step 4 (Batch 4): 实现事件分发 + 经济 + 监狱 + 破产
═══════════════════════════════════════════════════════

  对应 Build Steps: step-08 ~ step-11

  修改文件：
    MMonopolyGameMode.h/.cpp — 增加：
      - HandleTileEvent(int32 TileIndex): switch on TileType → PROPERTY/TAX/GO_TO_JAIL/others
      - HandlePropertyTile(): 无主→ShowBuyPopup, 他人→CollectRent, 自有→无
      - HandleTaxTile(): DeductMoney(TaxAmount) or TriggerBankruptcy
      - HandleGoToJailTile(): SendToJail()
      - TryPurchaseProperty() / CollectRent() / CalculateEffectiveRent()（base × color_group 2x）
      - TransferMoney() / DeductMoney()
      - SendToJail() / HandleJailTurn() / PayBail() / TryRollDoublesForJail() / ForcePayBail()
      - TriggerBankruptcy() / ReleaseAllProperties() / CheckGameEndCondition() / DeclareWinner()

    MMonopolyGameState.h/.cpp — 增加：
      - InitializeTileData()（硬编码 28 格数据）
      - DoesPlayerOwnFullColorGroup(int32, EMColorGroup)

  验证：
    - val-07: 8 种格子事件正确分发
    - val-08: 购买扣款 + 颜色组租金翻倍
    - val-09: 监狱全路径（入狱 / 保释$50 / 掷双数 / 第三回合强制保释）
    - val-10: 破产释放地产 + 游戏结束

═══════════════════════════════════════════════════════
Step 5 (Batch 5): 创建 UI Widget + 事件绑定
═══════════════════════════════════════════════════════

  对应 Build Steps: step-12-ui-widgets, step-13-ui-binding

  参照：交接文档 §7 UMG Widget 布局方案（控件树 + 视觉参数 + C++ 生成方式）

  新增文件：
    Source/Mvpv4TestCodex/Public/MGameHUDWidget.h
    Source/Mvpv4TestCodex/Private/MGameHUDWidget.cpp
      - NativeConstruct() 中用 WidgetTree->ConstructWidget<> 构建控件树
      - 左上角 320×自适应，黑色半透明(0,0,0,0.6) 背景
      - 4 元素：CurrentPlayerIndicator / AllPlayersMoney / TurnNumber / CurrentTileInfo
      - UpdateCurrentPlayer() / UpdateAllPlayersMoney() / UpdateTurnNumber() / UpdateCurrentTileInfo()

    Source/Mvpv4TestCodex/Public/MPopupWidget.h
    Source/Mvpv4TestCodex/Private/MPopupWidget.cpp
      - 基类，居中 SizeBox + Border(0,0,0,0.8) + VerticalBox
      - ShowPopup(Title, Body, Buttons) / OnButtonClicked(int32) / ClosePopup()
      - 5 个 WBP 通过参数化区分，无需独立 C++ 子类

  绑定（在 GameMode::BeginPlay 中）：
    - CreateWidget<UMGameHUDWidget>() → AddToViewport()
    - 10 个 Delegate 绑定：OnTurnChanged / OnMoneyChanged / OnPawnMoved / OnDiceRollRequested / ...

  视觉参数（摘自交接文档 §7.1）：
    标题字号 24，正文 16，辅助 14
    Primary 按钮 蓝色(0.2,0.4,0.8)，Secondary 灰色(0.3,0.3,0.3)
    金额绿色(0.2,0.9,0.3)，警告黄色(1,0.9,0.2)，危险红色(1,0.3,0.2)

  验证：
    - val-11: 5 个 Widget（HUD + 4 弹窗基类实例）存在
    - val-12: 10 个事件委托已绑定（OnTurnChanged.IsBound() etc.）

═══════════════════════════════════════════════════════
Step 6 (Batch 6): 运行 12 个验证检查点
═══════════════════════════════════════════════════════

  对应 Build Step: step-14-validation

  12 个验证点（对应 build_ir.json 的 validation_ir）：

  val-01: GetAllActorsOfClass(AMTile).Num() == 28
  val-02: GameState->TileDataArray.Num() == 28, 其中 PROPERTY 类型 16 个且 Price > 0
  val-03: GetAllActorsOfClass(AMPlayerPawn).Num() >= 2 && <= 4
  val-04: GetWorld()->GetAuthGameMode<AMMonopolyGameMode>() != nullptr
  val-05: GameMode->CurrentTurnState == EMTurnState::WaitForRoll
  val-06: 循环 100 次 RollDice()，全部 Total in [2,12]，Die1==Die2 时 bIsDoubles==true
  val-07: 模拟落地 8 种 tile_type，确认 HandleTileEvent 分发正确
  val-08: 模拟购买→OwnerIndex 设置正确；模拟颜色组完整→租金=base×2
  val-09: 模拟 GO_TO_JAIL→bIsInJail=true；PayBail→bIsInJail=false；TryDoubles 成功/失败；ForcePayBail
  val-10: 模拟 Money=0→TriggerBankruptcy→bIsBankrupt=true + properties released；剩 1 人→GameOver
  val-11: HUDWidget != nullptr, PopupWidget 可 CreateWidget
  val-12: GameState->OnTurnChanged.IsBound() == true（10 个委托全部检查）

【验收标准】
- 11 对 C++ 文件（.h + .cpp）全部存在于 Source/Mvpv4TestCodex/
- UE5 编译通过（0 error）
- 场景中 28 个 AMTile + 2-4 个 AMPlayerPawn + 1 个 AMBoardManager + 1 个 AMDice
- 12 个验证检查点全部通过
- 游戏可从 WaitForRoll 状态开始，完成至少一个完整回合（掷骰→移动→事件→回合结束）
- 不修改 Plugins/AgentBridge/ 下任何已稳定文件
```

---
---

# 阶段 7：验收

---

## TASK 07：兼容性清理与最终验收（M4） ⬜

```
目标：确保 Phase 8 全部新增产物不破坏现有系统。
回归 230 条系统测试，确认 v1→v2 Handoff 兼容性，规划并补录 Phase 8 测试编号。

前置依赖：TASK 06 完成

先读这些文件：
- Plugins/AgentBridge/Tests/SystemTestCases.md（当前 230 条测试总表）
- Plugins/AgentBridge/Tests/run_system_tests.py（系统测试入口）
- Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json（v1 Schema）
- ProjectState/phase8/reviewed_handoff_v2.json（v2 产物——确认 legacy_compatibility 字段）
读完应掌握：现有 230 条测试的 Stage 分布，v1 Handoff 的字段结构

涉及文件：
- Plugins/AgentBridge/Tests/SystemTestCases.md（追加 Phase 8 测试编号）
- Plugins/AgentBridge/Tests/run_system_tests.py（追加 Phase 8 Stage）
- Docs/Current/*（更新为归档口径）

═══════════════════════════════════════════════════════
Step 1: 回归现有 230 条系统测试
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor
  # 预期：纯 Python Stage 全部通过

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：12 个现有 example 全部通过

═══════════════════════════════════════════════════════
Step 2: 验证 v1 Handoff 旧链路仍可跑
═══════════════════════════════════════════════════════

  python Scripts/run_greenfield_demo.py simulated
  # 预期：boardgame TicTacToe Greenfield simulated 成功，使用 v1 Handoff

  python -c "
  import json, jsonschema
  schema = json.load(open('Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json'))
  example = json.load(open('Plugins/AgentBridge/Schemas/examples/reviewed_handoff_greenfield.example.json'))
  jsonschema.validate(example, schema)
  print('✅ v1 Handoff example 仍通过 v1 Schema 校验')
  "

═══════════════════════════════════════════════════════
Step 3: 验证现有稳定文件未被修改
═══════════════════════════════════════════════════════

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/verifier.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/report_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py
  git diff Plugins/AgentBridge/AgentBridgeTests/
  git diff Plugins/AgentBridge/Schemas/common/
  git diff Plugins/AgentBridge/Schemas/feedback/
  git diff Plugins/AgentBridge/Schemas/write_feedback/
  # 预期：全部无变更

═══════════════════════════════════════════════════════
Step 4: 规划 Phase 8 测试编号并补录总表
═══════════════════════════════════════════════════════

  待 TASK 06 完成后，根据实际验证结果规划测试编号：
  - SS-21~SS-xx：Schema / 结构级测试（6 个新 Schema 可解析等）
  - CP-41~CP-xx：编译期测试（Main Chain 5 阶段产出正确等）
  - E2E-37~E2E-xx：端到端测试（MonopolyGame 垂直切片可运行等）

  补录到 SystemTestCases.md 和 run_system_tests.py。

═══════════════════════════════════════════════════════
Step 5: 更新 Docs/Current/ 为归档准备口径
═══════════════════════════════════════════════════════

  02_Current_Phase_Goals.md → 成功标准全部标记结果
  03_Active_Backlog.md → M3/M4 标记完成
  06_Current_Task_List.md → 全部 TASK 标记完成

【验收标准】
- 现有 230 条系统测试（--no-editor）全部通过
- 现有 12 个 Schema example 校验全部通过
- v1 Handoff 旧链路（boardgame TicTacToe simulated）仍可跑
- 所有稳定文件 git diff 为空
- Phase 8 测试编号已补录进 SystemTestCases.md（新增条数待定）
- Docs/Current/ 已更新为归档准备口径
```
