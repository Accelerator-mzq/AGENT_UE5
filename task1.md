# Phase 3 — Greenfield + Boardgame + Reviewed Handoff 最小闭环

> 目标引擎版本：UE5.5.4 | 文档版本：Phase3-v2
> 架构：Skill Compiler Plane（插件层）→ Reviewed Handoff → Execution Orchestrator → Bridge 受控工具
> 实施方案：Docs/Proposals/Phase3_Implementation_Plan.md
> 实施边界：Docs/Current/05_Implementation_Boundary.md
> 开发路线：参见 AGENT_UE5_Development_Roadmap.md

---

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent
2. 每个 TASK 内附「先读这些文件」列表——编码 Agent 应在动手前先读完
3. 每个 TASK 末尾有【验收标准】——全部通过才可进入下一个 TASK
4. 交付件来源目录：`D:\ClaudeProject\fenxi-claude\input\`（以下简称 INPUT_DIR）
5. 本工程根目录：`D:\UnrealProjects\Mvpv4TestCodex\`（以下简称 PROJECT_ROOT）
6. 插件目录：`Plugins/AgentBridge/`（以下简称 PLUGIN_DIR）
7. PowerShell 读取文本必须使用 `Get-Content -Encoding UTF8`

## 核心约束

- **不修改**任何现有 C++ 文件（Source/AgentBridge/Private/*.cpp / Public/*.h）
- **不修改**任何现有 Bridge 脚本（Scripts/bridge/*.py）
- **不修改**现有 Orchestrator 核心（Scripts/orchestrator/orchestrator.py / plan_generator.py / verifier.py / report_generator.py / spec_reader.py）
- **不修改**任何现有测试文件（AgentBridgeTests/）
- **不修改**任何现有 Schema（Schemas/common/ / feedback/ / write_feedback/）
- **只新增**文件和目录，通过新增并行入口桥接到现有执行链

## 任务总览

阶段 1 项目层基础（01-02）> 阶段 2 插件层 Schema + Compiler（03-05）> 阶段 3 Orchestrator 桥接（06-08）> 阶段 4 端到端联调（09-11）

---
---

# 阶段 1：项目层基础

---

## TASK 01：创建项目层目录结构 + 部署配置文件

```
目标：在项目根目录创建 ProjectInputs/ 和 ProjectState/ 目录结构，
并部署 GDD 示例和 Preset 配置文件。
这是整个 Phase 3 的基础——项目层提供输入，插件层提供机制。

前置依赖：无

先读这些文件：
- AGENTS.md §2.2（分层原则：项目层 = 输入与实例层）
- Docs/Current/05_Implementation_Boundary.md（实施边界）
- Docs/Proposals/Phase3_Implementation_Plan.md §4.1（项目层部署映射）
读完应掌握：项目层只放输入源 / 配置 / 实例 / 治理，不放 Compiler 主体

涉及文件：全部新增，不修改任何现有文件。

═══════════════════════════════════════════════════════
Step 1: 创建 ProjectInputs/ 目录结构
═══════════════════════════════════════════════════════

  mkdir -p ProjectInputs/GDD
  mkdir -p ProjectInputs/Presets
  mkdir -p ProjectInputs/Baselines

═══════════════════════════════════════════════════════
Step 2: 创建 ProjectState/ 目录结构
═══════════════════════════════════════════════════════

  mkdir -p ProjectState/Handoffs/draft
  mkdir -p ProjectState/Handoffs/approved
  mkdir -p ProjectState/Handoffs/archived
  mkdir -p ProjectState/Reports
  mkdir -p ProjectState/Snapshots

═══════════════════════════════════════════════════════
Step 3: 部署 GDD 示例文件
═══════════════════════════════════════════════════════

  从 INPUT_DIR/ProjectInputs/GDD/boardgame_tictactoe_v1.md
  复制到 PROJECT_ROOT/ProjectInputs/GDD/boardgame_tictactoe_v1.md

  文件内容要点：
  - 游戏类型：棋盘游戏（Boardgame）
  - 核心玩法：3x3 棋盘 + 2 种棋子 + 回合制
  - 场景需求：Board（300x300cm 平面）+ PieceX（红色 Cube）+ PieceO（蓝色 Sphere）
  - 初始位置：棋盘中心在世界原点 (0, 0, 0)

═══════════════════════════════════════════════════════
Step 4: 部署 Preset 配置文件
═══════════════════════════════════════════════════════

  从 INPUT_DIR/ProjectInputs/Presets/mode_override.yaml
  复制到 PROJECT_ROOT/ProjectInputs/Presets/mode_override.yaml

  关键字段：
    default_mode: "auto"              # auto / greenfield_bootstrap / brownfield_expansion
    force_mode: null                  # 如果设置，强制使用指定模式
    mode_detection_rules:
      empty_project_threshold: 0      # 多少个 Actor 以下算空项目

  模式解析优先级（基于 Greenfield_Brownfield_模式切换规则_v2）：
    优先级 1: Explicit User Override (force_mode)
    优先级 2: Project / Profile Preset (default_mode)
    优先级 3: Auto Detection Fallback

  从 INPUT_DIR/ProjectInputs/Presets/compiler_profile.yaml
  复制到 PROJECT_ROOT/ProjectInputs/Presets/compiler_profile.yaml

  关键字段：
    compiler:
      enable_intake: true
      enable_routing: true
      enable_handoff_builder: true
      enable_baseline_understanding: false  # Phase 3 不启用
      enable_delta_scope_analysis: false    # Phase 3 不启用
    input_sources:
      gdd_path: "ProjectInputs/GDD/"
      gdd_format: "markdown"
    output:
      handoff_output_path: "ProjectState/Handoffs/draft/"
      handoff_format: "yaml"

═══════════════════════════════════════════════════════
Step 5: 验证
═══════════════════════════════════════════════════════

  ls -R ProjectInputs/
  # 预期：
  #   ProjectInputs/GDD/boardgame_tictactoe_v1.md
  #   ProjectInputs/Presets/mode_override.yaml
  #   ProjectInputs/Presets/compiler_profile.yaml
  #   ProjectInputs/Baselines/（空目录）

  ls -R ProjectState/
  # 预期：
  #   ProjectState/Handoffs/draft/（空）
  #   ProjectState/Handoffs/approved/（空）
  #   ProjectState/Reports/（空）
  #   ProjectState/Snapshots/（空）

  head -5 ProjectInputs/GDD/boardgame_tictactoe_v1.md
  # 预期：看到 "# 井字棋游戏 GDD v1"

  python -c "import yaml; d=yaml.safe_load(open('ProjectInputs/Presets/mode_override.yaml','r',encoding='utf-8')); print(d['default_mode'])"
  # 预期：auto

  python -c "import yaml; d=yaml.safe_load(open('ProjectInputs/Presets/compiler_profile.yaml','r',encoding='utf-8')); print(d['compiler']['enable_intake'])"
  # 预期：True

【验收标准】
- ProjectInputs/ 下有 GDD/ Presets/ Baselines/ 三个子目录
- ProjectState/ 下有 Handoffs/draft/ Handoffs/approved/ Reports/ Snapshots/
- boardgame_tictactoe_v1.md 头部可正常阅读
- mode_override.yaml 可被 Python yaml.safe_load 正确解析
- compiler_profile.yaml 可被 Python yaml.safe_load 正确解析
- 不影响任何现有文件（git diff 为空，除新增文件外）
```

---

## TASK 02：验证现有 MVP 不受影响

```
目标：确认 TASK 01 的新增目录和文件不影响现有 MVP 的任何能力。
这是一个纯验证任务，不新增任何文件。

前置依赖：TASK 01 完成

先读这些文件：
- Docs/Current/05_Implementation_Boundary.md（现有文件保护清单）
读完应掌握：哪些文件属于稳定核心，不应被修改

═══════════════════════════════════════════════════════
Step 1: 验证现有 Schema 校验链
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

  预期输出：
    Checked examples       : 10
    Passed                 : 10
    Failed                 : 0
    [SUCCESS] 全部 example 校验通过

═══════════════════════════════════════════════════════
Step 2: 验证现有文件未被修改
═══════════════════════════════════════════════════════

  git diff Plugins/AgentBridge/Source/
  # 预期：无变更

  git diff Plugins/AgentBridge/Scripts/bridge/
  # 预期：无变更

  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/verifier.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/report_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py
  # 预期：全部无变更

  git diff Plugins/AgentBridge/AgentBridgeTests/
  # 预期：无变更

  git diff Plugins/AgentBridge/Schemas/common/
  git diff Plugins/AgentBridge/Schemas/feedback/
  git diff Plugins/AgentBridge/Schemas/write_feedback/
  # 预期：全部无变更

═══════════════════════════════════════════════════════
Step 3: 验证项目层没有 Compiler 主体代码
═══════════════════════════════════════════════════════

  find ProjectInputs/ -name "*.py" | wc -l
  # 预期：0（项目层不应有 Python 代码）

  find ProjectState/ -name "*.py" | wc -l
  # 预期：0

═══════════════════════════════════════════════════════
Step 4: 验证现有 orchestrator 入口可用
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "from orchestrator.orchestrator import run; print('现有 run() 入口可用')"
  # 预期：输出 "现有 run() 入口可用"（或 import 成功无报错）

【验收标准】
- validate_examples.py --strict 输出 10/10 通过
- 所有 git diff 为空（现有文件无变更）
- 项目层无 .py 文件
- 现有 orchestrator.run() 入口可导入
```

---
---

# 阶段 2：插件层 Schema + Compiler 框架

---

## TASK 03：部署 Reviewed Handoff Schema + Run Plan Schema

```
目标：将 Reviewed Handoff 和 Run Plan 的 JSON Schema 部署到插件层 Schemas/ 目录。
这两个 Schema 定义了 Compiler → Orchestrator 之间的正式交接物格式。
Reviewed Handoff 是整个新架构的核心交接物——Skill Compiler Plane 的输出、Execution Orchestrator Plane 的输入。

前置依赖：TASK 02 完成

先读这些文件：
- Plugins/AgentBridge/Schemas/README.md（现有 Schema 目录结构和版本管理方式）
- Plugins/AgentBridge/Schemas/common/primitives.schema.json（理解现有 status 枚举和基础类型）
读完应掌握：现有 Schema 的组织方式、$ref 引用机制、example 与 Schema 的映射关系

涉及文件：全部新增到 Plugins/AgentBridge/Schemas/，不修改任何现有 Schema 文件。

═══════════════════════════════════════════════════════
Step 1: 部署 Reviewed Handoff Schema
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Schemas/reviewed_handoff.schema.json
  复制到 PLUGIN_DIR/Schemas/reviewed_handoff.schema.json

  关键字段说明（基于 Reviewed_Dynamic_Spec_Tree_交接模型_v2）：

  必填字段：
    handoff_version    string    Schema 版本（"1.0"）
    handoff_id         string    全局唯一 ID（格式：handoff.<project>.<stage>.<sequence>）
    handoff_mode       enum      greenfield_bootstrap | brownfield_expansion
    status             enum      draft | reviewed | approved_for_execution | blocked
    dynamic_spec_tree  object    图纸树（包含 scene_spec.actors[]）

  条件必填字段（Brownfield 必填，Greenfield 可为空）：
    baseline_context   object    基线上下文（baseline_id / snapshot_ref / frozen_baseline_ref）
    delta_context      object    差量上下文（delta_intent / affected_domains / affected_specs / required_regression_checks）

  可选字段：
    project_context    object    项目上下文（project_name / game_type / target_platform）
    routing_context    object    路由信息（mode / genre / target_stage / activated_skill_packs）
    review_summary     object    审查结果（reviewed / reviewer / review_notes）
    capability_gaps    object    缺口信息
    governance_context object    治理输入种子
    metadata           object    审计元信息（generated_at / generator）

  dynamic_spec_tree.scene_spec.actors[] 中每个 Actor 必须包含：
    actor_name         string    Actor 标签名
    actor_class        string    UE 类路径（如 /Script/Engine.StaticMeshActor）
    transform          object    包含 location[3] / rotation[3] / relative_scale3d[3]

═══════════════════════════════════════════════════════
Step 2: 部署 Run Plan Schema
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Schemas/run_plan.schema.json
  复制到 PLUGIN_DIR/Schemas/run_plan.schema.json

  关键字段说明（基于 Run_Plan_输入模型_v2）：

  必填字段：
    run_plan_version     string    Schema 版本（"2.0"）
    run_plan_id          string    全局唯一 ID（格式：runplan.<project>.<stage>.<sequence>）
    source_handoff_id    string    来源 Handoff 的 ID
    mode                 enum      greenfield_bootstrap | brownfield_expansion
    workflow_sequence    array     Workflow 执行序列

  workflow_sequence[] 中每个步骤必须包含：
    step_id              string    步骤唯一标识
    workflow_type        enum      spawn_actor | set_actor_transform | import_assets | create_blueprint_child
    params               object    Workflow 参数

  可选字段：
    status               enum      planned | executing | validating | succeeded | failed | rolled_back
    validation_checkpoints array   验证检查点
    recovery_policies    object    恢复策略
    metadata             object    元信息

═══════════════════════════════════════════════════════
Step 3: 部署 example 文件
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Schemas/examples/reviewed_handoff_greenfield.example.json
  复制到 PLUGIN_DIR/Schemas/examples/reviewed_handoff_greenfield.example.json

  从 INPUT_DIR/Schemas/examples/run_plan_greenfield.example.json
  复制到 PLUGIN_DIR/Schemas/examples/run_plan_greenfield.example.json

  reviewed_handoff_greenfield.example.json 内容要点：
  - handoff_mode: "greenfield_bootstrap"
  - status: "approved_for_execution"
  - 3 个 Actor：Board / PieceX_1 / PieceO_1
  - Board 位于 (0,0,0)，缩放 (3,3,0.1)
  - PieceX_1 位于 (-100,-100,50)
  - PieceO_1 位于 (100,100,50)

═══════════════════════════════════════════════════════
Step 4: 验证新增 Schema 格式正确
═══════════════════════════════════════════════════════

  python -c "import json; s=json.load(open('Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json')); print('required:', s['required'])"
  # 预期：required: ['handoff_version', 'handoff_id', 'handoff_mode', 'status', 'dynamic_spec_tree']

  python -c "import json; s=json.load(open('Plugins/AgentBridge/Schemas/run_plan.schema.json')); print('required:', s['required'])"
  # 预期：required: ['run_plan_version', 'run_plan_id', 'source_handoff_id', 'mode', 'workflow_sequence']

═══════════════════════════════════════════════════════
Step 5: 验证新增 example 通过对应 Schema 校验
═══════════════════════════════════════════════════════

  python -c "
  import json, jsonschema
  schema = json.load(open('Plugins/AgentBridge/Schemas/reviewed_handoff.schema.json'))
  example = json.load(open('Plugins/AgentBridge/Schemas/examples/reviewed_handoff_greenfield.example.json'))
  jsonschema.validate(example, schema)
  print('✅ Handoff example 通过 Schema 校验')
  "

  python -c "
  import json, jsonschema
  schema = json.load(open('Plugins/AgentBridge/Schemas/run_plan.schema.json'))
  example = json.load(open('Plugins/AgentBridge/Schemas/examples/run_plan_greenfield.example.json'))
  jsonschema.validate(example, schema)
  print('✅ Run Plan example 通过 Schema 校验')
  "

═══════════════════════════════════════════════════════
Step 6: 验证现有 Schema 校验链不受影响
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：原有 10 个 example 全部通过（新增 Schema 不影响现有校验）

【验收标准】
- Schemas/ 下新增 reviewed_handoff.schema.json 和 run_plan.schema.json
- Schemas/examples/ 下新增 2 个 example JSON
- 新增 example 通过对应 Schema 校验（jsonschema.validate 无报错）
- 现有 validate_examples.py --strict 仍然 10/10 通过
- 现有 Schema 文件未被修改（git diff Schemas/common/ feedback/ write_feedback/ 为空）
```

---

## TASK 04：部署 Skill Compiler Plane 框架到插件层

```
目标：将 Skill Compiler Plane 最小框架部署到插件层 Scripts/compiler/ 目录。
Compiler 是新架构的编译前端——从 GDD 输入到 Reviewed Handoff 输出的主链路。
本 TASK 部署的是框架骨架，包含 intake / routing / handoff 三个子模块的最小实现，
以及 analysis / generation / review 三个子模块的占位 README。

前置依赖：TASK 03 完成

先读这些文件：
- Plugins/AgentBridge/README.md §5（插件目录结构——确认 Scripts/compiler/ 的位置）
- Plugins/AgentBridge/AGENTS.md §1（插件定位——Compiler 主体在插件层）
- Docs/Current/05_Implementation_Boundary.md（不修改现有 Scripts/bridge/ 和 Scripts/orchestrator/）
读完应掌握：Compiler 是插件层的新增能力，与现有 bridge / orchestrator 并行，不覆盖

涉及文件：全部新增到 Plugins/AgentBridge/Scripts/compiler/，不修改任何现有文件。

═══════════════════════════════════════════════════════
Step 1: 部署 compiler 目录（整个目录树）
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Scripts/compiler/ 整个目录
  复制到 PLUGIN_DIR/Scripts/compiler/

  目标目录结构：
    Scripts/compiler/
    ├── __init__.py                          ← 模块入口
    ├── intake/
    │   ├── __init__.py
    │   ├── design_input_intake.py           ← 读取 GDD，提取 game_type
    │   └── project_state_intake.py          ← 获取项目现状快照
    ├── routing/
    │   ├── __init__.py
    │   └── mode_router.py                   ← 三级优先级模式判定
    ├── handoff/
    │   ├── __init__.py
    │   ├── handoff_builder.py               ← 组装 Reviewed Handoff
    │   └── handoff_serializer.py            ← 序列化为 YAML/JSON
    ├── analysis/
    │   └── README.md                        ← 占位：Brownfield 分析（Phase 5）
    ├── generation/
    │   └── README.md                        ← 占位：Spec 自动生成（Phase 4）
    └── review/
        └── README.md                        ← 占位：Cross-Spec Review（Phase 4）

═══════════════════════════════════════════════════════
Step 2: 部署 compiler_main.py
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Scripts/compiler_main.py
  复制到 PLUGIN_DIR/Scripts/compiler_main.py

  compiler_main.py 是端到端入口脚本，执行流程：
    1. 读取 GDD（调用 compiler.intake.read_gdd_from_directory）
    2. 获取项目现状（调用 compiler.intake.get_project_state_snapshot）
    3. 判断模式（调用 compiler.routing.determine_mode）
    4. 构建 Handoff（调用 compiler.handoff.build_handoff）
    5. 保存 Handoff（调用 compiler.handoff.serialize_handoff）

═══════════════════════════════════════════════════════
Step 3: 验证 Python 模块可导入
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts

  python -c "from compiler.intake import read_gdd, read_gdd_from_directory; print('✅ intake 可导入')"
  python -c "from compiler.intake import get_project_state_snapshot; print('✅ project_state_intake 可导入')"
  python -c "from compiler.routing import determine_mode, load_mode_config; print('✅ routing 可导入')"
  python -c "from compiler.handoff import build_handoff, serialize_handoff; print('✅ handoff 可导入')"

═══════════════════════════════════════════════════════
Step 4: 验证 design_input_intake 功能
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "
  from compiler.intake import read_gdd
  result = read_gdd('../../../ProjectInputs/GDD/boardgame_tictactoe_v1.md')
  print('game_type:', result['game_type'])
  assert result['game_type'] == 'boardgame', f'期望 boardgame，实际 {result[\"game_type\"]}'
  print('✅ design_input_intake 功能正确')
  "
  # 预期：game_type: boardgame

  注意：如果路径不对，需要根据实际工程目录调整相对路径。
  design_input_intake.py 中的 extract_game_type() 通过查找 GDD 中的"游戏类型"关键词提取类型。
  如果提取失败返回 "unknown"，需要检查 GDD 文件格式是否匹配。

═══════════════════════════════════════════════════════
Step 5: 验证 mode_router 功能
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "
  from compiler.routing import determine_mode

  # 测试 1：空项目 + auto 模式 → greenfield
  config = {'default_mode': 'auto', 'force_mode': None, 'mode_detection_rules': {'empty_project_threshold': 0}}
  state = {'actor_count': 0, 'is_empty': True}
  mode = determine_mode(config, state)
  assert mode == 'greenfield_bootstrap', f'期望 greenfield_bootstrap，实际 {mode}'
  print('✅ 测试 1 通过：空项目 → greenfield')

  # 测试 2：非空项目 + auto 模式 → brownfield
  state2 = {'actor_count': 5, 'is_empty': False}
  mode2 = determine_mode(config, state2)
  assert mode2 == 'brownfield_expansion', f'期望 brownfield_expansion，实际 {mode2}'
  print('✅ 测试 2 通过：非空项目 → brownfield')

  # 测试 3：force_mode 覆盖
  config3 = {'default_mode': 'auto', 'force_mode': 'greenfield_bootstrap', 'mode_detection_rules': {}}
  mode3 = determine_mode(config3, state2)
  assert mode3 == 'greenfield_bootstrap', f'期望 greenfield_bootstrap，实际 {mode3}'
  print('✅ 测试 3 通过：force_mode 覆盖自动检测')
  "

═══════════════════════════════════════════════════════
Step 6: 验证 handoff_builder 功能
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "
  from compiler.handoff import build_handoff
  design_input = {'game_type': 'boardgame', 'scene_requirements': [], 'source_file': 'test.md'}
  handoff = build_handoff(design_input, 'greenfield_bootstrap')

  # 验证必填字段
  assert handoff['handoff_version'] == '1.0'
  assert handoff['handoff_mode'] == 'greenfield_bootstrap'
  assert handoff['status'] == 'draft'
  assert 'dynamic_spec_tree' in handoff
  assert 'scene_spec' in handoff['dynamic_spec_tree']

  actors = handoff['dynamic_spec_tree']['scene_spec']['actors']
  assert len(actors) == 3, f'期望 3 个 Actor，实际 {len(actors)}'
  assert actors[0]['actor_name'] == 'Board'
  assert actors[0]['transform']['location'] == [0, 0, 0]
  assert actors[0]['transform']['relative_scale3d'] == [3, 3, 0.1]
  print(f'✅ handoff_builder 功能正确，生成 {len(actors)} 个 Actor')
  "

═══════════════════════════════════════════════════════
Step 7: 验证生成的 Handoff 通过 Schema 校验
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "
  import json, jsonschema
  from compiler.handoff import build_handoff

  design_input = {'game_type': 'boardgame', 'scene_requirements': [], 'source_file': 'test.md'}
  handoff = build_handoff(design_input, 'greenfield_bootstrap')

  schema = json.load(open('../Schemas/reviewed_handoff.schema.json'))
  jsonschema.validate(handoff, schema)
  print('✅ 生成的 Handoff 通过 Schema 校验')
  "

═══════════════════════════════════════════════════════
Step 8: 验证现有文件未被修改
═══════════════════════════════════════════════════════

  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py
  # 预期：全部无变更

【验收标准】
- Scripts/compiler/ 目录完整（intake/ routing/ handoff/ + 占位 README）
- compiler_main.py 存在于 Scripts/ 下
- 4 个 Python 模块全部可正常导入
- design_input_intake 能从 GDD 提取 game_type == "boardgame"
- mode_router 三级优先级判定全部正确（3 个测试用例通过）
- handoff_builder 生成 3 个 Actor 的 Handoff
- 生成的 Handoff 通过 reviewed_handoff.schema.json 校验
- 现有 Scripts/bridge/ 和 Scripts/orchestrator/ 核心文件未被修改
```

---

## TASK 05：部署 Skills 占位 + Specs 占位

```
目标：部署 Skills 体系和 Specs 体系的占位目录到插件层。
Skills/ 是 Base Skill Domains 和 Genre Skill Packs 的未来落点。
Specs/ 扩展 StaticBase/ 和 Contracts/ 子目录作为未来落点。
本 TASK 只创建目录骨架和 README，不实现具体 Skill 逻辑。

前置依赖：TASK 04 完成

先读这些文件：
- Plugins/AgentBridge/README.md §5（插件目录结构——确认 Skills/ 和 Specs/ 的位置）
读完应掌握：Skills/ 和 Specs/ 是插件层的新增目录，与现有 Source/ / Scripts/ / Schemas/ 并列

涉及文件：全部新增，不修改任何现有文件。

═══════════════════════════════════════════════════════
Step 1: 部署 Skills 目录
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Skills/ 整个目录
  复制到 PLUGIN_DIR/Skills/

  目标目录结构：
    Skills/
    ├── base_domains/
    │   └── README.md                        ← 占位：10 个 Base Skill Domains
    └── genre_packs/
        ├── _core/
        │   └── README.md                    ← 占位：类型包机制核心
        └── boardgame/
            ├── pack_manifest.yaml           ← 最小 Manifest（已对齐标准 v1）
            └── README.md                    ← 占位：boardgame 类型包

  boardgame/pack_manifest.yaml 关键字段（基于 Genre_Skill_Pack_Manifest_标准_v1）：
    pack_id: "genre-boardgame"
    version: "0.1.0"
    title: "Boardgame Genre Skill Pack"
    status: "minimal_skeleton"
    activation:
      keywords: ["boardgame", "棋盘游戏", "board game", "棋盘", "回合制"]
    required_skills: []                      # 第一阶段占位
    delta_policy:
      enabled: false                         # Brownfield 待后续补充

═══════════════════════════════════════════════════════
Step 2: 部署 Specs 扩展目录（不覆盖现有 Specs/templates/）
═══════════════════════════════════════════════════════

  mkdir -p PLUGIN_DIR/Specs/StaticBase
  mkdir -p PLUGIN_DIR/Specs/Contracts

  从 INPUT_DIR/Specs/StaticBase/README.md
  复制到 PLUGIN_DIR/Specs/StaticBase/README.md

  从 INPUT_DIR/Specs/Contracts/README.md
  复制到 PLUGIN_DIR/Specs/Contracts/README.md

  注意：不要覆盖现有的 Specs/templates/ 目录！

═══════════════════════════════════════════════════════
Step 3: 验证
═══════════════════════════════════════════════════════

  ls Plugins/AgentBridge/Skills/
  # 预期：base_domains/ genre_packs/

  ls Plugins/AgentBridge/Skills/genre_packs/boardgame/
  # 预期：pack_manifest.yaml README.md

  python -c "
  import yaml
  m = yaml.safe_load(open('Plugins/AgentBridge/Skills/genre_packs/boardgame/pack_manifest.yaml','r',encoding='utf-8'))
  assert m['pack_id'] == 'genre-boardgame', f'期望 genre-boardgame，实际 {m[\"pack_id\"]}'
  assert m['status'] == 'minimal_skeleton'
  print(f'✅ pack_manifest.yaml 格式正确：{m[\"pack_id\"]} v{m[\"version\"]}')
  "

  ls Plugins/AgentBridge/Specs/
  # 预期：StaticBase/ Contracts/ templates/（templates 是现有的）

  ls Plugins/AgentBridge/Specs/templates/
  # 预期：现有模板文件仍然存在

【验收标准】
- Skills/base_domains/README.md 存在
- Skills/genre_packs/_core/README.md 存在
- Skills/genre_packs/boardgame/pack_manifest.yaml 可被 yaml.safe_load 解析
- pack_manifest.yaml 的 pack_id 为 "genre-boardgame"
- Specs/StaticBase/README.md 存在
- Specs/Contracts/README.md 存在
- 现有 Specs/templates/ 未被修改
```

---
---

# 阶段 3：Orchestrator 桥接

---

## TASK 06：部署 Handoff Runner + Run Plan Builder 到 Orchestrator

```
目标：将 handoff_runner.py 和 run_plan_builder.py 部署到插件层 Scripts/orchestrator/。
这两个文件是 Reviewed Handoff → 执行 的桥接层：
  - run_plan_builder.py：从 Handoff 生成 Run Plan
  - handoff_runner.py：读取 Handoff → 生成 Run Plan → 桥接到现有 Bridge 接口执行
它们作为新增的并行入口，不修改现有 orchestrator.py 的 run(spec_path) 入口。

前置依赖：TASK 05 完成

先读这些文件：
- Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py（前 30 行——了解现有入口和导入方式）
  读完应掌握：现有 orchestrator 通过 run(spec_path) 入口执行，依赖 bridge/ 下的模块
- Plugins/AgentBridge/Scripts/bridge/write_tools.py（前 50 行——了解现有写接口的调用方式）
  读完应掌握：写接口通过 _dispatch_write() 分发到三通道，C++ Plugin 函数名映射在 _CPP_WRITE_MAP
- Plugins/AgentBridge/Scripts/bridge/remote_control_client.py（前 40 行——了解 RC API 调用方式）
  读完应掌握：RemoteControlConfig 默认端口 30010，call_function() 是核心调用方法

涉及文件：
  新增 Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py
  新增 Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py
  新增 Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py
  不修改任何现有 orchestrator 文件。

═══════════════════════════════════════════════════════
Step 1: 部署 run_plan_builder.py
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Scripts/orchestrator/run_plan_builder.py
  复制到 PLUGIN_DIR/Scripts/orchestrator/run_plan_builder.py

  核心函数：
    def build_run_plan_from_handoff(handoff: dict) -> dict
      - 从 Handoff 的 dynamic_spec_tree.scene_spec.actors[] 提取 Actor 列表
      - 为每个 Actor 生成一个 workflow_step（workflow_type: "spawn_actor"）
      - 第一个 Actor 无依赖，后续 Actor depends_on 第一个
      - 在最后一个步骤后插入 validation_checkpoint
      - 返回符合 run_plan.schema.json 的 Run Plan

═══════════════════════════════════════════════════════
Step 2: 部署 handoff_runner.py
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Scripts/orchestrator/handoff_runner.py
  复制到 PLUGIN_DIR/Scripts/orchestrator/handoff_runner.py

  核心函数：
    def run_from_handoff(handoff_path, report_output_dir=None, bridge_mode="simulated") -> dict

  bridge_mode 三种模式：
    "simulated"      — 模拟执行，返回模拟结果（第一阶段默认）
    "bridge_python"  — 调用现有 bridge.write_tools.spawn_actor
    "bridge_rc_api"  — 调用现有 bridge.remote_control_client.call_function

  桥接逻辑（execute_spawn_actor 函数）：

    if bridge_mode == "simulated":
        # 返回模拟结果，不调用任何 Bridge 接口
        return {"status": "success", "actor_name": params["actor_name"], ...}

    elif bridge_mode == "bridge_python":
        # 调用现有 Python Bridge（不修改 write_tools.py）
        from bridge.write_tools import spawn_actor
        result = spawn_actor(
            level_path=params.get("level_path", "/Game/Maps/TestMap"),
            actor_class=params.get("actor_class"),
            actor_name=params.get("actor_name"),
            transform=params.get("transform")
        )
        return result

    elif bridge_mode == "bridge_rc_api":
        # 调用现有 Remote Control API 客户端（不修改 remote_control_client.py）
        from bridge.remote_control_client import call_function
        result = call_function("SpawnActor", {
            "LevelPath": params.get("level_path", "/Game/Maps/TestMap"),
            "ActorClass": params.get("actor_class"),
            "ActorName": params.get("actor_name"),
            "Transform": params.get("transform")
        })
        return result

  执行报告生成（build_execution_report 函数）：
    - 记录 source_handoff_id / source_run_plan_id
    - 记录每个步骤的执行结果
    - 统计 succeeded / failed / skipped 数量
    - 保存为 JSON 到 report_output_dir

═══════════════════════════════════════════════════════
Step 3: 部署 test_handoff_schema.py
═══════════════════════════════════════════════════════

  从 INPUT_DIR/Scripts/validation/test_handoff_schema.py
  复制到 PLUGIN_DIR/Scripts/validation/test_handoff_schema.py

  功能：验证 Handoff 和 Run Plan example 是否通过 Schema 校验

═══════════════════════════════════════════════════════
Step 4: 验证新增文件可导入
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "from orchestrator.run_plan_builder import build_run_plan_from_handoff; print('✅ run_plan_builder 可导入')"
  python -c "from orchestrator.handoff_runner import run_from_handoff; print('✅ handoff_runner 可导入')"

═══════════════════════════════════════════════════════
Step 5: 验证 run_plan_builder 功能
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "
  from orchestrator.run_plan_builder import build_run_plan_from_handoff
  test_handoff = {
      'handoff_id': 'handoff.test.prototype.001',
      'handoff_mode': 'greenfield_bootstrap',
      'project_context': {'project_name': 'Test'},
      'dynamic_spec_tree': {
          'scene_spec': {
              'actors': [
                  {'actor_name': 'Board', 'actor_class': '/Script/Engine.StaticMeshActor',
                   'transform': {'location': [0,0,0], 'rotation': [0,0,0], 'relative_scale3d': [1,1,1]}}
              ]
          }
      }
  }
  plan = build_run_plan_from_handoff(test_handoff)
  assert plan['source_handoff_id'] == 'handoff.test.prototype.001'
  assert len(plan['workflow_sequence']) == 1
  assert plan['workflow_sequence'][0]['workflow_type'] == 'spawn_actor'
  print(f'✅ Run Plan 生成正确：{len(plan[\"workflow_sequence\"])} 个步骤')
  "

═══════════════════════════════════════════════════════
Step 6: 验证现有 orchestrator 未被修改
═══════════════════════════════════════════════════════

  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/verifier.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/report_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py
  # 预期：全部无变更

【验收标准】
- orchestrator/ 下新增 handoff_runner.py 和 run_plan_builder.py
- validation/ 下新增 test_handoff_schema.py
- 两个新增模块可正常导入
- run_plan_builder 能从 Handoff 生成正确的 Run Plan
- 现有 orchestrator 5 个核心文件全部无变更
```

---

## TASK 07：部署端到端入口脚本 + 路径适配

```
目标：部署 run_greenfield_demo.py 到项目根目录，并适配本工程的实际目录结构。
这是整个 Phase 3 的端到端验证入口——从 GDD 到执行报告的完整链路。

前置依赖：TASK 06 完成

先读这些文件：
- INPUT_DIR/run_greenfield_demo.py（了解脚本的原始路径配置）
读完应掌握：脚本中的路径需要适配本工程的实际目录结构

涉及文件：
  新增 PROJECT_ROOT/run_greenfield_demo.py
  需要修改脚本中的路径配置以适配本工程。

═══════════════════════════════════════════════════════
Step 1: 复制 run_greenfield_demo.py 到项目根目录
═══════════════════════════════════════════════════════

  从 INPUT_DIR/run_greenfield_demo.py
  复制到 PROJECT_ROOT/run_greenfield_demo.py

═══════════════════════════════════════════════════════
Step 2: 适配路径配置
═══════════════════════════════════════════════════════

  打开 run_greenfield_demo.py，确认以下路径配置正确：

  关键路径（必须适配本工程）：
    gdd_dir          → PROJECT_ROOT/ProjectInputs/GDD/
    mode_config_path → PROJECT_ROOT/ProjectInputs/Presets/mode_override.yaml
    handoff_draft_dir → PROJECT_ROOT/ProjectState/Handoffs/draft/
    handoff_approved_dir → PROJECT_ROOT/ProjectState/Handoffs/approved/
    report_dir       → PROJECT_ROOT/ProjectState/Reports/
    scripts_dir      → PROJECT_ROOT/Plugins/AgentBridge/Scripts/

  sys.path 必须包含：
    Plugins/AgentBridge/Scripts/（让 from compiler.xxx 和 from orchestrator.xxx 可导入）

  如果原始脚本中的路径是相对于 input/ 目录的，需要改为相对于 PROJECT_ROOT 的路径。

═══════════════════════════════════════════════════════
Step 3: 运行 simulated 模式
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python run_greenfield_demo.py

  预期输出（关键行）：
    [阶段 1] Compiler：读取 GDD → 判定模式 → 生成 Handoff
      游戏类型: boardgame
      检测到的模式: greenfield_bootstrap
      Handoff ID: handoff.boardgame.prototype.xxxxxxxx
    [阶段 2] 审批：将 Handoff 从 draft/ 复制到 approved/
    [阶段 3] Orchestrator：读取 approved Handoff → 生成 Run Plan → 执行
      执行步骤: spawn_Board (spawn_actor)
      执行步骤: spawn_PieceX_1 (spawn_actor)
      执行步骤: spawn_PieceO_1 (spawn_actor)
      执行状态: succeeded
    报告已保存: ProjectState/Reports/execution_report_xxx.json

═══════════════════════════════════════════════════════
Step 4: 验证生成的产物
═══════════════════════════════════════════════════════

  ls ProjectState/Handoffs/draft/
  # 预期：有 handoff.boardgame.prototype.xxxxxxxx.yaml

  ls ProjectState/Handoffs/approved/
  # 预期：有 handoff.boardgame.prototype.xxxxxxxx.yaml

  ls ProjectState/Reports/
  # 预期：有 execution_report_xxx.json

  # 验证 Handoff 内容
  python -c "
  import yaml
  import glob
  files = glob.glob('ProjectState/Handoffs/draft/*.yaml')
  h = yaml.safe_load(open(files[0],'r',encoding='utf-8'))
  assert h['handoff_mode'] == 'greenfield_bootstrap'
  assert len(h['dynamic_spec_tree']['scene_spec']['actors']) == 3
  print(f'✅ Handoff 内容正确：{h[\"handoff_id\"]}')
  "

  # 验证 Report 内容
  python -c "
  import json, glob
  files = glob.glob('ProjectState/Reports/*.json')
  r = json.load(open(files[0]))
  assert r['execution_status'] == 'succeeded'
  assert r['summary']['total_steps'] == 3
  assert r['summary']['succeeded'] == 3
  print(f'✅ Report 内容正确：{r[\"summary\"][\"succeeded\"]}/{r[\"summary\"][\"total_steps\"]} 步骤成功')
  "

═══════════════════════════════════════════════════════
Step 5: 验证 Handoff 通过 Schema 校验
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python validation/test_handoff_schema.py
  # 预期：全部通过

═══════════════════════════════════════════════════════
Step 6: 如果路径适配失败的诊断步骤
═══════════════════════════════════════════════════════

  常见问题 1：ModuleNotFoundError: No module named 'compiler'
  → 检查 sys.path 是否包含 Plugins/AgentBridge/Scripts/

  常见问题 2：FileNotFoundError: GDD 文件不存在
  → 检查 gdd_dir 路径是否指向 ProjectInputs/GDD/

  常见问题 3：FileNotFoundError: mode_override.yaml 不存在
  → 检查 mode_config_path 是否指向 ProjectInputs/Presets/mode_override.yaml

  常见问题 4：PermissionError
  → 检查 ProjectState/ 目录是否有写权限

【验收标准】
- python run_greenfield_demo.py 输出 "执行状态: succeeded"
- ProjectState/Handoffs/draft/ 有 Handoff YAML 文件
- ProjectState/Handoffs/approved/ 有 Handoff YAML 文件
- ProjectState/Reports/ 有 execution_report JSON 文件
- Handoff 内容正确（3 个 Actor，greenfield_bootstrap 模式）
- Report 内容正确（3/3 步骤成功）
- Handoff 通过 Schema 校验
```

---

## TASK 08：全面 MVP 不破坏验证

```
目标：在所有新增文件部署完成后，全面验证现有 MVP 不受影响。
这是阶段 3 的最终安全检查。

前置依赖：TASK 07 完成

═══════════════════════════════════════════════════════
Step 1: 验证现有 Schema 校验链
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：原有 10 个 example 全部通过

═══════════════════════════════════════════════════════
Step 2: 验证所有现有文件未被修改
═══════════════════════════════════════════════════════

  # C++ 核心
  git diff Plugins/AgentBridge/Source/
  # 预期：无变更

  # Bridge 客户端
  git diff Plugins/AgentBridge/Scripts/bridge/
  # 预期：无变更

  # Orchestrator 核心（5 个文件）
  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/plan_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/verifier.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/report_generator.py
  git diff Plugins/AgentBridge/Scripts/orchestrator/spec_reader.py
  # 预期：全部无变更

  # 测试体系
  git diff Plugins/AgentBridge/AgentBridgeTests/
  # 预期：无变更

  # 现有 Schema
  git diff Plugins/AgentBridge/Schemas/common/
  git diff Plugins/AgentBridge/Schemas/feedback/
  git diff Plugins/AgentBridge/Schemas/write_feedback/
  # 预期：全部无变更

═══════════════════════════════════════════════════════
Step 3: 验证项目层 / 插件层边界
═══════════════════════════════════════════════════════

  # 项目层没有 Compiler 主体代码
  find ProjectInputs/ -name "*.py" | wc -l
  # 预期：0

  # 插件层没有项目私有 Handoff 实例
  find Plugins/AgentBridge/ -name "*.yaml" -path "*/Handoffs/*" | wc -l
  # 预期：0

  # Compiler 代码在插件层
  find Plugins/AgentBridge/Scripts/compiler/ -name "*.py" | wc -l
  # 预期：≥ 8（__init__.py + 5 个实现文件 + 2 个 __init__.py）

═══════════════════════════════════════════════════════
Step 4: 验证新增文件清单
═══════════════════════════════════════════════════════

  git status --short
  # 预期：只有新增文件（??），没有修改文件（M）
  # 新增文件应包括：
  #   ProjectInputs/（3 个文件）
  #   ProjectState/（目录结构）
  #   Plugins/AgentBridge/Schemas/（4 个新增文件）
  #   Plugins/AgentBridge/Scripts/compiler/（整个目录）
  #   Plugins/AgentBridge/Scripts/compiler_main.py
  #   Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py
  #   Plugins/AgentBridge/Scripts/orchestrator/run_plan_builder.py
  #   Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py
  #   Plugins/AgentBridge/Skills/（整个目录）
  #   Plugins/AgentBridge/Specs/StaticBase/
  #   Plugins/AgentBridge/Specs/Contracts/
  #   run_greenfield_demo.py

【验收标准】
- validate_examples.py --strict 输出 10/10 通过
- 所有现有文件 git diff 为空
- 项目层无 .py 文件
- 插件层无项目私有 Handoff 实例
- git status 只有新增文件，没有修改文件
```

---
---

# 阶段 4：UE5 真实调用联调

---

## TASK 09：Bridge 桥接适配 — 确认现有写接口调用方式 [UE5 环境]

```
目标：在 UE5 Editor 运行状态下，确认现有 Bridge 写接口（spawn_actor）可以被 handoff_runner 正确调用。
这是 simulated 模式到真实执行的关键跨越——需要理解现有 write_tools.py 的调用签名，
并确认 handoff_runner.py 中的桥接参数映射是否正确。

前置依赖：TASK 08 完成 + UE5.5.4 Editor 运行 + AgentBridge 插件已编译

先读这些文件：
- Plugins/AgentBridge/Scripts/bridge/write_tools.py（完整阅读——理解 spawn_actor 的调用签名）
  读完应掌握：
  1. spawn_actor 的参数：level_path / actor_class / actor_name / transform / dry_run
  2. transform 的格式：{"location": [x,y,z], "rotation": [p,y,r], "relative_scale3d": [x,y,z]}
  3. 三通道分发逻辑：_dispatch_write() 根据当前通道选择 Python / RC API / C++ Plugin
  4. 返回值格式：符合 write_operation_feedback.response.schema.json
- Plugins/AgentBridge/Scripts/bridge/remote_control_client.py（前 80 行——理解 RC API 调用方式）
  读完应掌握：
  1. call_function(function_name, parameters) 的调用方式
  2. 默认端口 30010
  3. objectPath 的构造方式
- Plugins/AgentBridge/Scripts/bridge/bridge_core.py（前 50 行——理解通道设置方式）
  读完应掌握：
  1. set_channel(BridgeChannel.XXX) 设置当前通道
  2. BridgeChannel 枚举：PYTHON / RC_API / CPP_PLUGIN / MOCK
- Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py（完整阅读——理解桥接逻辑）
  读完应掌握：
  1. execute_spawn_actor() 的三种 bridge_mode
  2. bridge_python 模式调用 bridge.write_tools.spawn_actor
  3. bridge_rc_api 模式调用 bridge.remote_control_client.call_function

涉及文件：可能需要修改 handoff_runner.py 中的桥接参数映射。

═══════════════════════════════════════════════════════
Step 1: 确认 UE5 Editor 启动 + RC API 可用
═══════════════════════════════════════════════════════

  打开 Mvpv4TestCodex.uproject
  确认 AgentBridge 插件在 Edit → Plugins 中已启用

  curl http://localhost:30010/remote/info
  # 预期：返回 JSON（确认 RC API 可用）
  # 如果返回 connection refused，检查：
  #   1. UE5 Editor 是否已启动
  #   2. Remote Control API 插件是否已启用
  #   3. Web Server 是否已启动（Edit → Project Settings → Remote Control → Enable Web Server）

═══════════════════════════════════════════════════════
Step 2: 用现有 Bridge 直接测试 spawn_actor
═══════════════════════════════════════════════════════

  先用现有 Bridge 直接调用 spawn_actor，确认接口本身可用：

  cd Plugins/AgentBridge/Scripts
  python -c "
  import sys
  sys.path.insert(0, 'bridge')
  from bridge_core import set_channel, BridgeChannel
  from write_tools import spawn_actor

  # 设置通道为 RC API
  set_channel(BridgeChannel.RC_API)

  # 调用 spawn_actor
  result = spawn_actor(
      level_path='/Game/Maps/TestMap',
      actor_class='/Script/Engine.StaticMeshActor',
      actor_name='BridgeTest_Cube',
      transform={
          'location': [0, 0, 200],
          'rotation': [0, 0, 0],
          'relative_scale3d': [1, 1, 1]
      }
  )
  print('status:', result.get('status'))
  print('data:', result.get('data', {}).get('created_objects', []))
  "
  # 预期：status: success + created_objects 包含 BridgeTest_Cube
  # 在 UE5 Editor 的 World Outliner 中确认 BridgeTest_Cube 出现在 (0, 0, 200)

  如果失败：
  - 检查 level_path 是否正确（用 GetCurrentProjectState 查询当前地图）
  - 检查 actor_class 是否正确
  - 检查 RC API 端口是否开放

═══════════════════════════════════════════════════════
Step 3: 检查 handoff_runner 的桥接参数映射
═══════════════════════════════════════════════════════

  对比 handoff_runner.py 中 execute_spawn_actor() 的参数映射
  与 write_tools.py 中 spawn_actor() 的实际签名：

  handoff_runner.py 中的调用：
    from bridge.write_tools import spawn_actor
    result = spawn_actor(
        level_path=params.get("level_path", "/Game/Maps/TestMap"),
        actor_class=params.get("actor_class"),
        actor_name=params.get("actor_name"),
        transform=params.get("transform")
    )

  write_tools.py 中 spawn_actor 的实际签名：
    def spawn_actor(level_path, actor_class, actor_name, transform, dry_run=False)

  需要确认：
  1. 参数名是否匹配（level_path / actor_class / actor_name / transform）
  2. transform 格式是否匹配（location / rotation / relative_scale3d）
  3. level_path 默认值 "/Game/Maps/TestMap" 是否是当前工程的有效地图

  如果参数名不匹配，需要修改 handoff_runner.py 中的映射。
  如果 level_path 不对，需要修改默认值或从 Handoff 中读取。

═══════════════════════════════════════════════════════
Step 4: 确认 bridge_rc_api 模式的参数映射
═══════════════════════════════════════════════════════

  handoff_runner.py 中 bridge_rc_api 模式的调用：
    from bridge.remote_control_client import call_function
    result = call_function("SpawnActor", {
        "LevelPath": ...,
        "ActorClass": ...,
        "ActorName": ...,
        "Transform": ...
    })

  需要确认：
  1. call_function 的第一个参数 "SpawnActor" 是否是 C++ Subsystem 中的函数名
  2. 参数名是否与 C++ 端一致（LevelPath / ActorClass / ActorName / Transform）
  3. Transform 的 JSON 格式是否与 C++ 端的 FBridgeTransform 兼容

  参考 AgentBridgeSubsystem.h 中 SpawnActor 的声明：
    FBridgeResponse SpawnActor(
        const FString& LevelPath,
        const FString& ActorClass,
        const FString& ActorName,
        const FBridgeTransform& Transform,
        bool bDryRun = false
    );

  如果参数名不匹配，需要修改 handoff_runner.py 中的映射。

【验收标准】
- UE5 Editor 启动，RC API 端口 30010 可用
- 现有 Bridge 直接调用 spawn_actor 成功（BridgeTest_Cube 出现在 UE5 中）
- handoff_runner.py 的参数映射与现有 Bridge 接口一致
- 如果有不匹配，已修正 handoff_runner.py 中的映射
```

---

## TASK 10：端到端真实执行 — Greenfield Boardgame [UE5 环境]

```
目标：将 bridge_mode 从 simulated 切换到真实调用，在 UE5 中验证 Actor 生成。
这是 Phase 3 的核心验收——从 GDD 到 UE5 中可见的 Actor 的完整链路。

前置依赖：TASK 09 完成（桥接参数映射已确认/修正）

先读这些文件：
- Plugins/AgentBridge/AGENTS.md §2.4（写后必须读回）
  读完应掌握：写操作后必须读回 actual_transform 并验证
- Plugins/AgentBridge/Docs/tool_contract_v0_1.md §4.1（spawn_actor 的 Response）
  读完应掌握：spawn_actor 返回 created_objects + actual_transform + dirty_assets

═══════════════════════════════════════════════════════
Step 1: 清理 UE5 场景
═══════════════════════════════════════════════════════

  在 UE5 Editor 中：
  - 删除 TASK 09 中创建的 BridgeTest_Cube（如果存在）
  - 确认当前场景中没有 Board / PieceX_1 / PieceO_1

  或者通过 Bridge 查询确认：
  cd Plugins/AgentBridge/Scripts
  python -c "
  import sys; sys.path.insert(0, 'bridge')
  from query_tools import list_level_actors
  actors = list_level_actors()
  for a in actors.get('data', {}).get('actors', []):
      print(a.get('actor_name'))
  "

═══════════════════════════════════════════════════════
Step 2: 清理之前的 simulated 产物
═══════════════════════════════════════════════════════

  # 清理之前 simulated 模式生成的 Handoff 和 Report
  rm -f ProjectState/Handoffs/draft/*.yaml
  rm -f ProjectState/Handoffs/approved/*.yaml
  rm -f ProjectState/Reports/*.json

═══════════════════════════════════════════════════════
Step 3: 运行 bridge_python 模式
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT

  # 方式 A：如果 run_greenfield_demo.py 支持 bridge_mode 参数
  python run_greenfield_demo.py bridge_python

  # 方式 B：如果需要手动修改 bridge_mode
  # 编辑 run_greenfield_demo.py，将 bridge_mode 从 "simulated" 改为 "bridge_python"
  # 然后运行 python run_greenfield_demo.py

  预期输出：
    [阶段 3] Orchestrator 执行
      执行步骤: spawn_Board (spawn_actor)
        status: success
      执行步骤: spawn_PieceX_1 (spawn_actor)
        status: success
      执行步骤: spawn_PieceO_1 (spawn_actor)
        status: success
      执行状态: succeeded

  如果 bridge_python 失败，尝试 bridge_rc_api：
  python run_greenfield_demo.py bridge_rc_api

═══════════════════════════════════════════════════════
Step 4: 在 UE5 Editor 中验证 Actor
═══════════════════════════════════════════════════════

  在 World Outliner 中确认：

  Actor 1: Board
    - 存在于场景中
    - 位置：(0, 0, 0)
    - 缩放：(3, 3, 0.1)

  Actor 2: PieceX_1
    - 存在于场景中
    - 位置：(-100, -100, 50)
    - 缩放：(0.5, 0.5, 0.5)

  Actor 3: PieceO_1
    - 存在于场景中
    - 位置：(100, 100, 50)
    - 缩放：(0.5, 0.5, 0.5)

═══════════════════════════════════════════════════════
Step 5: 通过 Bridge 查询接口验证 Actor 状态
═══════════════════════════════════════════════════════

  cd Plugins/AgentBridge/Scripts
  python -c "
  import sys; sys.path.insert(0, 'bridge')
  from query_tools import list_level_actors, get_actor_state

  # 列出所有 Actor
  actors = list_level_actors()
  actor_names = [a.get('actor_name') for a in actors.get('data', {}).get('actors', [])]
  print('场景中的 Actor:', actor_names)

  # 验证 Board 存在
  assert 'Board' in actor_names, 'Board 不存在！'
  print('✅ Board 存在')

  # 验证 PieceX_1 存在
  assert 'PieceX_1' in actor_names, 'PieceX_1 不存在！'
  print('✅ PieceX_1 存在')

  # 验证 PieceO_1 存在
  assert 'PieceO_1' in actor_names, 'PieceO_1 不存在！'
  print('✅ PieceO_1 存在')
  "

  # 验证 Board 的 Transform
  python -c "
  import sys; sys.path.insert(0, 'bridge')
  from query_tools import get_actor_state

  # 需要用 Board 的 actor_path（从 list_level_actors 获取）
  # 示例：state = get_actor_state('/Game/Maps/TestMap.Board')
  # 验证 location 接近 [0, 0, 0]（容差 0.01）
  # 验证 relative_scale3d 接近 [3, 3, 0.1]（容差 0.001）
  print('请根据实际 actor_path 验证 Transform')
  "

═══════════════════════════════════════════════════════
Step 6: 验证执行报告
═══════════════════════════════════════════════════════

  python -c "
  import json, glob
  files = glob.glob('ProjectState/Reports/*.json')
  assert len(files) > 0, '没有找到执行报告！'
  r = json.load(open(files[-1]))
  assert r['execution_status'] == 'succeeded', f'执行状态不是 succeeded: {r[\"execution_status\"]}'
  assert r['summary']['succeeded'] == 3, f'成功步骤数不是 3: {r[\"summary\"][\"succeeded\"]}'
  print(f'✅ 执行报告正确：{r[\"summary\"][\"succeeded\"]}/{r[\"summary\"][\"total_steps\"]} 步骤成功')
  "

═══════════════════════════════════════════════════════
Step 7: 如果执行失败的诊断步骤
═══════════════════════════════════════════════════════

  常见问题 1：ImportError: No module named 'bridge'
  → 检查 sys.path 是否包含 Scripts/ 目录
  → 检查 handoff_runner.py 中的 import 路径

  常见问题 2：spawn_actor 返回 EDITOR_NOT_READY
  → 确认 UE5 Editor 已启动且不在 PIE 模式

  常见问题 3：spawn_actor 返回 CLASS_NOT_FOUND
  → 确认 actor_class "/Script/Engine.StaticMeshActor" 在 UE5.5.4 中有效

  常见问题 4：spawn_actor 返回 LEVEL_NOT_FOUND
  → 用 get_current_project_state 查询当前地图路径
  → 修改 handoff_runner.py 中的 level_path 默认值

  常见问题 5：RC API connection refused
  → 确认 Remote Control API 插件已启用
  → 确认 Web Server 已启动（端口 30010）

【验收标准】
- UE5 中生成了 Board / PieceX_1 / PieceO_1 三个 Actor
- Board 位于 (0, 0, 0)，缩放 (3, 3, 0.1)
- PieceX_1 位于 (-100, -100, 50)，缩放 (0.5, 0.5, 0.5)
- PieceO_1 位于 (100, 100, 50)，缩放 (0.5, 0.5, 0.5)
- 通过 Bridge 查询接口确认 3 个 Actor 存在
- 执行报告 status 为 "succeeded"，3/3 步骤成功
```

---

## TASK 11：现有 Automation Test 不受影响验证 [UE5 环境]

```
目标：确认所有新增文件不影响现有 Automation Test 的通过率。
这是 Phase 3 的最终安全验证。

前置依赖：TASK 10 完成

═══════════════════════════════════════════════════════
Step 1: 在 Session Frontend 中运行 L1 测试
═══════════════════════════════════════════════════════

  在 UE5 Editor 中打开 Session Frontend（Window → Developer Tools → Session Frontend）
  选择 Automation 标签页
  勾选 Project.AgentBridge.L1.*
  点击 Start Tests

  预期结果：
    L1.Query.GetCurrentProjectState    ✅ Pass
    L1.Query.ListLevelActors           ✅ Pass
    L1.Query.GetActorState             ✅ Pass
    L1.Query.GetActorBounds            ✅ Pass
    L1.Query.GetAssetMetadata          ✅ Pass
    L1.Query.GetDirtyAssets            ✅ Pass
    L1.Query.RunMapCheck               ✅ Pass
    L1.Write.SpawnActor                ✅ Pass
    L1.Write.SetActorTransform         ✅ Pass
    L1.Write.ImportAssets              ✅ Pass
    L1.Write.CreateBlueprintChild      ✅ Pass

═══════════════════════════════════════════════════════
Step 2: 在 Session Frontend 中运行 L2 测试
═══════════════════════════════════════════════════════

  勾选 Project.AgentBridge.L2.*
  点击 Start Tests

  预期结果：
    L2.ClosedLoop.SpawnAndVerify       ✅ Pass
    L2.ClosedLoop.TransformAndVerify   ✅ Pass
    L2.ClosedLoop.ImportAndVerify      ✅ Pass
    L2.UITool.ClickAndVerify           ✅ Pass
    L2.UITool.TypeAndVerify            ✅ Pass

═══════════════════════════════════════════════════════
Step 3: 在 Session Frontend 中运行 L3 UITool 测试
═══════════════════════════════════════════════════════

  勾选 Project.AgentBridge.L3.*
  点击 Start Tests

  预期结果：
    L3.UITool.ClickDetailPanelButton   ✅ Pass
    L3.UITool.TypeInDetailPanelField   ✅ Pass
    L3.UITool.DragAssetToViewport      ✅ Pass
    L3.UITool.CrossVerification        ✅ Pass

═══════════════════════════════════════════════════════
Step 4: 验证测试总数
═══════════════════════════════════════════════════════

  总计应有 20 个测试：
    L1 Query: 7 个
    L1 Write: 4 个
    L3 UITool: 4 个
    L2 ClosedLoop: 3 个
    L2 UITool: 2 个

  全部 20/20 通过才算验收成功。

  如果某个测试失败：
  1. 检查失败原因（Session Frontend 中的错误信息）
  2. 确认失败是否与新增文件有关
  3. 如果与新增文件无关（是现有测试本身的问题），记录但不阻塞
  4. 如果与新增文件有关，回退新增文件并排查

【验收标准】
- 20 个 Automation Test 全部通过（或失败原因与新增文件无关）
- 没有新增的测试失败
- Phase 3 全部 TASK 完成
```
