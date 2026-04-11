# Phase 10 — MCP 认知桥接层实现 + Compiler Pipeline 编排

> 目标引擎版本：UE5.5.4
> 阶段定位：Phase 10 正式开发期
> 架构：MCP 前端（Stage 1-2 认知分解）+ Compiler Core（Stage 3-5 调度）+ MCP 后端（证据裁决）
> 上一阶段任务：[task9_phase9.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/History/Tasks/task9_phase9.md)
> 当前阶段索引：[00_Index.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/00_Index.md)
> 交接文档：[Handoff_Phase10_Execution.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Handoff_Phase10_Execution.md)
> MCP 总口径：[14_MCP_Cognitive_Bridge_Anchor.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md)
> 四层主链定义：[15_Skill_Spec_Handoff_Chain.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/15_Skill_Spec_Handoff_Chain.md)
> MCP 重定位方案：[16_MCP_Repositioning_Plan.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/16_MCP_Repositioning_Plan.md)

---

## 使用说明

1. 将每个 TASK 逐个发送给编码 Agent。
2. 每个 TASK 内附「先读这些文件」列表——编码 Agent 应在动手前先读完。
3. 每个 TASK 末尾有【验收标准】——全部通过才可进入下一个 TASK。
4. 本工程根目录：`D:\UnrealProjects\Mvpv4TestCodex\`（以下简称 PROJECT_ROOT）
5. 插件目录：`Plugins/AgentBridge/`（以下简称 PLUGIN_DIR）
6. MCP 目录：`Plugins/AgentBridge/MCP/`（以下简称 MCP_DIR）
7. Compiler 目录：`Plugins/AgentBridge/Compiler/`（以下简称 COMPILER_DIR）

## 核心约束

- **不修改**任何现有 C++ 文件（Plugins/AgentBridge/Source/AgentBridge/Private/*.cpp / Public/*.h）
- **不修改**任何现有 Bridge 脚本（Plugins/AgentBridge/Scripts/bridge/*.py）
- **不修改**现有 Orchestrator 核心（orchestrator.py / plan_generator.py / verifier.py / report_generator.py / spec_reader.py）
- **不修改**任何现有测试文件（Plugins/AgentBridge/AgentBridgeTests/）
- **不修改**任何现有稳定 Schema（Schemas/common/ / feedback/ / write_feedback/）
- **不修改**现有 28 个 Bridge Passthrough 工具的行为（server.py 中已有的 TOOL_DISPATCH / dispatch_tool / 28 工具注册）
- 所有新代码带中文注释
- MCP SDK 固定为 `mcp==1.26.0`

## 本期固定规则

1. 根目录 `task.md` 是 Phase 10 当前阶段唯一任务入口。
2. 14 号文档（MCP 总口径）是最高优先级裁决依据——如与其他文档冲突，以 14 号为准。
3. MCP 前端边界 = Stage 1-2；Stage 3-5 = Compiler Core 调度（R1 规则）。
4. 测试 MCP = 证据读取 + 判读 + pass/fail/escalate；不控制 PIE、不模拟输入（R3 规则）。
5. Phase 8/9 基线回归不可被破坏——任何 TASK 完成后都必须通过 `validate_examples.py --strict`。
6. 现有 28 个 Bridge Passthrough 工具不删除、不改行为，新工具在其旁边追加注册。

## 里程碑定义

| 里程碑 | 内容 | 对应 TASK | 状态 |
|--------|------|-----------|------|
| M1 | Compiler Pipeline 编排入口 + Stage 间产物传递规范 | TASK 01-02 | ✅ 已完成 |
| M2 | MCP 前端工具注册（Stage 1-2 认知分解接口） | TASK 03 | ✅ 已完成 |
| M3 | 测试证据标准化 + run_id 规范 | TASK 04 | ✅ 已完成 |
| M4 | MCP 后端工具注册（证据裁决接口） | TASK 05 | ✅ 已完成 |
| M5 | GDD→Skill→Spec 全链路：MCP 前端认知分解 + Compiler Core 生成 | TASK 06 | ✅ 已完成 |
| M6 | Spec→关卡落地：通过 Build IR 在 UE5 Editor 中创建 MonopolyGame 关卡 | TASK 07 | ✅ 已完成 |
| M7 | 运行时验证 + MCP 后端证据裁决 | TASK 08 | ✅ 已完成 |
| M8 | 最终验收 + 文档收尾 | TASK 09 | ✅ 已完成 |

## 任务总览

阶段 1 Pipeline 编排入口（01）> 阶段 2 Stage 间产物传递（02）> 阶段 3 MCP 前端工具（03）> 阶段 4 证据标准化（04）> 阶段 5 MCP 后端工具（05）> **阶段 6 GDD→Skill→Spec 全链路（06）> 阶段 7 Spec→关卡落地（07）> 阶段 8 运行时验证+证据裁决（08）** > 阶段 9 最终验收（09）

---
---

# 阶段 1：Compiler Pipeline 编排入口

---

## TASK 01：创建 Compiler Pipeline Orchestrator ✅

```
目标：为 Compiler 5-stage pipeline 创建统一的 session / pipeline 编排入口。
当前 COMPILER_DIR 下有 5 个阶段骨架（intake/planner/skill_runtime/cross_review/lowering），
各自有 get_schema() / create_*_template() / save_*() 三件套，
但缺少串联 Stage 1-5 + Handoff 组装的顶层调度器。

前置依赖：无

先读这些文件：
- Docs/Handoff_Phase10_Execution.md（交接文档——Phase 10 全貌）
- Docs/Current/16_MCP_Repositioning_Plan.md §5（Monopoly 示例中 Stage 1-5 流程）
- Docs/Current/15_Skill_Spec_Handoff_Chain.md §3（流程图，含 MCP/Compiler Core 边界）
- COMPILER_DIR/intake/design_intake.py（Stage 1 骨架——理解三件套接口模式）
- COMPILER_DIR/planner/planner.py（Stage 2 骨架）
- COMPILER_DIR/skill_runtime/skill_runtime.py（Stage 3 骨架）
- COMPILER_DIR/cross_review/cross_review.py（Stage 4 骨架）
- COMPILER_DIR/lowering/lowering.py（Stage 5 骨架）
读完应掌握：5 个阶段的现有接口签名，每阶段的输入/输出关系

涉及文件：全部新增，不修改任何现有 Compiler 骨架文件。

═══════════════════════════════════════════════════════
Step 1: 创建 Pipeline Session 定义
═══════════════════════════════════════════════════════

  新增文件：COMPILER_DIR/pipeline/
  ├── __init__.py
  ├── session.py
  └── pipeline_orchestrator.py

  session.py:
    - CompilerSession 类
    - 属性：session_id（UUID）、created_at、current_stage（枚举 1-5）、
      stage_outputs（dict: stage_name → output_path）、status（pending/running/completed/failed）
    - 方法：
      - create_session(gdd_path, target_phase, output_dir) → CompilerSession
      - advance_stage() — 检查当前 stage 产物存在后，推进到下一 stage
      - get_stage_input_path(stage_num) — 返回上一 stage 的输出路径
      - to_dict() / save() / load(session_path) — 序列化/反序列化
    - session 文件格式：JSON，保存在 output_dir/session.json

  pipeline_orchestrator.py:
    - run_pipeline(session, stage_range=None) — 按顺序调度指定范围的 stage
    - run_stage(session, stage_num) — 调度单个 stage：
      Stage 1: 调用 intake.create_projection_template() → 返回模板供 Agent 填充
      Stage 2: 调用 planner.create_planner_output_template() → 返回模板供 Agent 填充
      Stage 3: 调用 skill_runtime.create_fragment_template() → 返回模板供 Agent 填充
      Stage 4: 调用 cross_review.create_review_report_template() → 返回模板供 Agent 填充
      Stage 5: 调用 lowering.create_build_ir_template() → 返回模板供 Agent 填充
    - prepare_stage(session, stage_num) — 生成模板，返回 {template, schema, input_context}
    - save_stage(session, stage_num, filled_data) — 校验 + 保存，更新 session
    - assemble_handoff(session) — Stage 5 完成后，组装 Reviewed Handoff v2
    - 错误处理：schema 校验失败时返回结构化错误，不抛异常

═══════════════════════════════════════════════════════
Step 2: 创建 Pipeline Schema
═══════════════════════════════════════════════════════

  新增文件：PLUGIN_DIR/Schemas/compiler_session.schema.json

  required 字段：
    - session_id（string, UUID 格式）
    - created_at（string, ISO 8601）
    - gdd_path（string）
    - target_phase（string）
    - output_dir（string）
    - current_stage（integer, 1-5）
    - stage_outputs（object: {"stage_1": path, ...}）
    - status（enum: pending/running/completed/failed）

═══════════════════════════════════════════════════════
Step 3: 验证 Pipeline 可导入
═══════════════════════════════════════════════════════

  cd PLUGIN_DIR
  python -c "
  from Compiler.pipeline.session import CompilerSession, create_session
  from Compiler.pipeline.pipeline_orchestrator import run_pipeline, run_stage, prepare_stage, save_stage, assemble_handoff
  print('✅ Pipeline 模块可导入')
  "

═══════════════════════════════════════════════════════
Step 4: 验证 Session 创建与序列化
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys, os, json, tempfile
  sys.path.insert(0, 'Plugins/AgentBridge')
  from Compiler.pipeline.session import create_session

  with tempfile.TemporaryDirectory() as tmp:
      s = create_session('ProjectInputs/GDD/GDD_MonopolyGame.md', 'phase1_local_multiplayer', tmp)
      assert s.session_id, 'session_id 不应为空'
      assert s.current_stage == 1, f'初始 stage 应为 1，实际 {s.current_stage}'
      assert s.status == 'pending', f'初始 status 应为 pending，实际 {s.status}'
      s.save()
      loaded = type(s).load(os.path.join(tmp, 'session.json'))
      assert loaded.session_id == s.session_id, 'session_id 序列化/反序列化不一致'
      print(f'✅ Session 创建成功: id={s.session_id[:8]}..., stage={s.current_stage}, status={s.status}')
  "

═══════════════════════════════════════════════════════
Step 5: 验证 prepare_stage 返回模板
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys, tempfile
  sys.path.insert(0, 'Plugins/AgentBridge')
  from Compiler.pipeline.session import create_session
  from Compiler.pipeline.pipeline_orchestrator import prepare_stage

  with tempfile.TemporaryDirectory() as tmp:
      s = create_session('ProjectInputs/GDD/GDD_MonopolyGame.md', 'phase1_local_multiplayer', tmp)
      result = prepare_stage(s, 1)
      assert 'template' in result, '返回值缺少 template'
      assert 'schema' in result, '返回值缺少 schema'
      assert result['template']['projection_version'], '模板缺少 projection_version'
      print(f'✅ Stage 1 prepare 成功: template keys={list(result[\"template\"].keys())[:5]}...')
  "

═══════════════════════════════════════════════════════
Step 6: 验证现有文件未被修改
═══════════════════════════════════════════════════════

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/AgentBridgeTests/
  git diff Plugins/AgentBridge/Schemas/common/
  git diff Plugins/AgentBridge/MCP/server.py
  # 预期：全部无变更

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：原有 example 全部通过

【验收标准】
- Compiler/pipeline/ 下新增 3 个 .py 文件（__init__.py / session.py / pipeline_orchestrator.py）
- Schemas/ 下新增 compiler_session.schema.json
- CompilerSession 可创建、序列化、反序列化
- prepare_stage(session, 1) 返回含 template + schema 的 dict
- 现有 Compiler 骨架文件无变更
- validate_examples.py --strict 通过
- 现有稳定文件无变更
```

---
---

# 阶段 2：Stage 间产物传递规范

---

## TASK 02：实现 Stage 间产物传递 + save_stage 校验 ✅

```
目标：实现每个 Stage 的输出路径如何成为下一个 Stage 的输入路径，
以及 save_stage 时的 Schema 校验逻辑。
完成后，prepare → (Agent 填充) → save 的完整循环可以在每个 Stage 上跑通。

前置依赖：TASK 01 完成

先读这些文件：
- COMPILER_DIR/pipeline/session.py（TASK 01 新增的 Session 定义）
- COMPILER_DIR/pipeline/pipeline_orchestrator.py（TASK 01 新增的编排入口）
- PLUGIN_DIR/Schemas/gdd_projection.schema.json（Stage 1 输出 Schema）
- PLUGIN_DIR/Schemas/planner_output.schema.json（Stage 2 输出 Schema）
- PLUGIN_DIR/Schemas/skill_fragment.schema.json（Stage 3 输出 Schema）
- PLUGIN_DIR/Schemas/cross_review_report.schema.json（Stage 4 输出 Schema）
- PLUGIN_DIR/Schemas/build_ir.schema.json（Stage 5 输出 Schema）
- PLUGIN_DIR/Schemas/reviewed_handoff_v2.schema.json（Handoff 输出 Schema）
- ProjectState/phase8/（Phase 8 的 11 个 JSON 样本数据——理解实际产物结构）
读完应掌握：每个 Stage 的输入/输出 Schema，Stage 间如何传递产物

涉及文件：修改 TASK 01 新增的 pipeline_orchestrator.py 和 session.py

═══════════════════════════════════════════════════════
Step 1: 定义产物传递映射表
═══════════════════════════════════════════════════════

  在 pipeline_orchestrator.py 中新增常量 STAGE_ARTIFACT_MAP:

    STAGE_ARTIFACT_MAP = {
        1: {
            "output_file": "gdd_projection.json",
            "schema_file": "gdd_projection.schema.json",
            "next_stage_input_key": "gdd_projection"
        },
        2: {
            "output_file": "planner_output.json",
            "schema_file": "planner_output.schema.json",
            "next_stage_input_key": "planner_output"
        },
        3: {
            "output_dir": "skill_fragments/",
            "schema_file": "skill_fragment.schema.json",
            "next_stage_input_key": "skill_fragments",
            "multi_file": True  # Stage 3 产出多个 fragment 文件
        },
        4: {
            "output_file": "cross_review_report.json",
            "schema_file": "cross_review_report.schema.json",
            "next_stage_input_key": "cross_review_report"
        },
        5: {
            "output_file": "build_ir.json",
            "schema_file": "build_ir.schema.json",
            "next_stage_input_key": "build_ir"
        }
    }

═══════════════════════════════════════════════════════
Step 2: 实现 save_stage 的 Schema 校验
═══════════════════════════════════════════════════════

  save_stage(session, stage_num, filled_data):
    1. 从 STAGE_ARTIFACT_MAP 获取 schema_file
    2. 加载 Schema JSON
    3. 使用 jsonschema.validate() 校验 filled_data
    4. 校验通过：写入 output_dir/{output_file}，更新 session.stage_outputs
    5. 校验失败：返回结构化错误 {"status": "validation_error", "errors": [...]}，不写入文件
    6. 更新 session.current_stage，调用 session.save()

  Stage 3 特殊处理（multi_file）：
    - filled_data 可以是单个 fragment dict 或 fragment dict 列表
    - 每个 fragment 独立校验，独立保存到 skill_fragments/{skill_instance_id}.json
    - session.stage_outputs["stage_3"] 记录目录路径而非单文件路径

═══════════════════════════════════════════════════════
Step 3: 实现 prepare_stage 的上游产物加载
═══════════════════════════════════════════════════════

  prepare_stage(session, stage_num):
    1. 如果 stage_num > 1，检查 session.stage_outputs 中上游产物路径存在
    2. 加载上游产物 JSON 作为 input_context
    3. 调用对应骨架的 create_*_template()
    4. 返回 {"template": ..., "schema": ..., "input_context": ..., "stage": stage_num}

  Stage 3 特殊处理：
    - input_context 包含 planner_output（Stage 2 输出）中的 selected_skill_instances 列表
    - 为每个 skill_instance 生成一个 fragment template

═══════════════════════════════════════════════════════
Step 4: 实现 assemble_handoff
═══════════════════════════════════════════════════════

  assemble_handoff(session):
    1. 检查 Stage 1-5 全部完成（session.stage_outputs 包含 stage_1 到 stage_5）
    2. 加载所有 stage 产物
    3. 组装 Reviewed Handoff v2 结构（参考 reviewed_handoff_v2.schema.json）
    4. 校验 + 保存到 output_dir/reviewed_handoff_v2.json
    5. 更新 session.status = "completed"

═══════════════════════════════════════════════════════
Step 5: 用 Phase 8 样本数据做端到端验证
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys, json, os, tempfile, shutil
  sys.path.insert(0, 'Plugins/AgentBridge')
  from Compiler.pipeline.session import create_session
  from Compiler.pipeline.pipeline_orchestrator import prepare_stage, save_stage, assemble_handoff

  # 用 Phase 8 已有样本数据模拟完整 pipeline
  with tempfile.TemporaryDirectory() as tmp:
      s = create_session('ProjectInputs/GDD/GDD_MonopolyGame.md', 'phase1_local_multiplayer', tmp)

      # Stage 1: 用 Phase 8 现有 projection
      data1 = json.load(open('ProjectState/phase8/gdd_projection.json'))
      result1 = save_stage(s, 1, data1)
      assert result1.get('status') != 'validation_error', f'Stage 1 校验失败: {result1}'
      print(f'✅ Stage 1 save 成功')

      # Stage 2: 用 Phase 8 现有 planner_output
      data2 = json.load(open('ProjectState/phase8/planner_output.json'))
      result2 = save_stage(s, 2, data2)
      assert result2.get('status') != 'validation_error', f'Stage 2 校验失败: {result2}'
      print(f'✅ Stage 2 save 成功')

      # Stage 3: 用 Phase 8 现有 fragments
      frag_dir = 'ProjectState/phase8/skill_fragments'
      frags = []
      for f in sorted(os.listdir(frag_dir)):
          frags.append(json.load(open(os.path.join(frag_dir, f))))
      result3 = save_stage(s, 3, frags)
      assert result3.get('status') != 'validation_error', f'Stage 3 校验失败: {result3}'
      print(f'✅ Stage 3 save 成功: {len(frags)} fragments')

      # Stage 4: 用 Phase 8 现有 cross_review
      data4 = json.load(open('ProjectState/phase8/cross_review_report.json'))
      result4 = save_stage(s, 4, data4)
      assert result4.get('status') != 'validation_error', f'Stage 4 校验失败: {result4}'
      print(f'✅ Stage 4 save 成功')

      # Stage 5: 用 Phase 8 现有 build_ir
      data5 = json.load(open('ProjectState/phase8/build_ir.json'))
      result5 = save_stage(s, 5, data5)
      assert result5.get('status') != 'validation_error', f'Stage 5 校验失败: {result5}'
      print(f'✅ Stage 5 save 成功')

      # Handoff 组装
      handoff_result = assemble_handoff(s)
      assert os.path.exists(os.path.join(tmp, 'reviewed_handoff_v2.json')), 'Handoff 文件未生成'
      assert s.status == 'completed', f'Session 状态应为 completed，实际 {s.status}'
      print(f'✅ Handoff 组装成功，session status={s.status}')

      print(f'✅ 端到端 Pipeline 验证通过')
  "

═══════════════════════════════════════════════════════
Step 6: 验证基线回归
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：通过

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/MCP/server.py
  # 预期：全部无变更

【验收标准】
- STAGE_ARTIFACT_MAP 定义 5 个 Stage 的产物映射
- save_stage 对每个 Stage 执行 jsonschema 校验，校验失败返回结构化错误不写入文件
- prepare_stage 加载上游产物作为 input_context
- assemble_handoff 在 Stage 1-5 全部完成后组装 Reviewed Handoff v2
- Phase 8 样本数据可作为输入完成端到端 pipeline（5 个 Stage + Handoff 组装全部通过）
- validate_examples.py --strict 通过
- 现有稳定文件无变更
```

---
---

# 阶段 3：MCP 前端工具注册

---

## TASK 03：注册 MCP 前端认知分解工具（Stage 1-2） ✅

```
目标：在现有 MCP Server 中注册 Stage 1-2 的 prepare/save 工具对。
这些工具是 MCP 认知桥接层前端的核心——AI Agent 通过它们驱动 GDD 到 Planner Output 的认知分解。
Stage 3-5 的 prepare/save 由 Compiler Core 内部调度，不注册为 MCP 对外工具。

前置依赖：TASK 02 完成

先读这些文件：
- Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md §4（MCP 工具在流程中的位置）
- Docs/Current/16_MCP_Repositioning_Plan.md §2.6（MCP 前端止于 Stage 2）
- Docs/Proposals/Phase10_Compiler_Capability_Bus_v3.md §7（推荐最小接口族）
- MCP_DIR/server.py（现有 MCP Server 实现——理解工具注册模式）
- MCP_DIR/tool_definitions.py（现有 28 工具定义——理解定义格式）
- COMPILER_DIR/pipeline/pipeline_orchestrator.py（TASK 01-02 新增的编排入口）
读完应掌握：现有 MCP 工具注册方式，前端接口族定义，prepare/save 工具对的调用模式

涉及文件：
- MCP_DIR/tool_definitions.py（修改——追加前端工具定义）
- MCP_DIR/server.py（修改——追加前端工具注册和 dispatch）
- MCP_DIR/compiler_tools.py（新增——前端工具实现）

═══════════════════════════════════════════════════════
Step 1: 新增 compiler_tools.py
═══════════════════════════════════════════════════════

  新增文件：MCP_DIR/compiler_tools.py

  实现以下 6 个函数（3 对 prepare/save + 辅助）：

  compiler_create_session(gdd_path, target_phase, output_dir):
    - 调用 pipeline.session.create_session()
    - 返回 {status, summary, data: {session_id, session_path}}

  compiler_intake_prepare(session_path):
    - 加载 session → 调用 prepare_stage(session, 1)
    - 返回 {status, summary, data: {template, schema, stage: 1}}

  compiler_intake_save(session_path, filled_data):
    - 加载 session → 调用 save_stage(session, 1, filled_data)
    - 返回 {status, summary, data: {output_path}} 或 {status: "failed", errors: [...]}

  compiler_plan_prepare(session_path):
    - 加载 session → 调用 prepare_stage(session, 2)
    - 返回 {status, summary, data: {template, schema, input_context, stage: 2}}

  compiler_plan_save(session_path, filled_data):
    - 加载 session → 调用 save_stage(session, 2, filled_data)
    - 返回 {status, summary, data: {output_path}} 或 {status: "failed", errors: [...]}

  compiler_get_session_status(session_path):
    - 加载 session → 返回 {status, summary, data: session.to_dict()}

  所有函数统一返回 {status, summary, data, warnings, errors} 格式（与 Bridge 工具一致）。

═══════════════════════════════════════════════════════
Step 2: 在 tool_definitions.py 追加前端工具定义
═══════════════════════════════════════════════════════

  新增 COMPILER_FRONTEND_TOOLS dict（6 个工具）：

  compiler_create_session:
    description: "创建 Compiler Pipeline 会话。Stage 1-2 由 MCP 前端驱动认知分解。"
    params: {gdd_path: string, target_phase: string, output_dir: string}

  compiler_intake_prepare:
    description: "Stage 1 准备：生成 GDD Projection 模板供 Agent 填充。"
    params: {session_path: string}

  compiler_intake_save:
    description: "Stage 1 保存：校验并保存 Agent 填充后的 GDD Projection。"
    params: {session_path: string, filled_data: object}

  compiler_plan_prepare:
    description: "Stage 2 准备：生成 Planner Output 模板供 Agent 填充。"
    params: {session_path: string}

  compiler_plan_save:
    description: "Stage 2 保存：校验并保存 Agent 填充后的 Planner Output。"
    params: {session_path: string, filled_data: object}

  compiler_get_session_status:
    description: "查询 Compiler Pipeline 会话当前状态。"
    params: {session_path: string}

  将 COMPILER_FRONTEND_TOOLS 加入 ALL_TOOLS。

═══════════════════════════════════════════════════════
Step 3: 在 server.py 追加前端工具注册
═══════════════════════════════════════════════════════

  在 create_mcp_server() 中：
  - 导入 compiler_tools 模块
  - 为 6 个前端工具注册到 TOOL_DISPATCH
  - 在 @server.list_tools() 中追加 6 个工具的 JSON Schema
  - 在 dispatch_tool() 中追加分发逻辑

  注意：现有 28 个 Bridge 工具的注册逻辑不改动，前端工具在其后追加。

═══════════════════════════════════════════════════════
Step 4: 验证工具注册
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys
  sys.path.insert(0, 'Plugins/AgentBridge/MCP')
  from tool_definitions import ALL_TOOLS, COMPILER_FRONTEND_TOOLS
  print(f'前端工具数量: {len(COMPILER_FRONTEND_TOOLS)}')
  assert len(COMPILER_FRONTEND_TOOLS) == 6, f'期望 6 个，实际 {len(COMPILER_FRONTEND_TOOLS)}'
  total = len(ALL_TOOLS)
  print(f'工具总数: {total}')
  assert total == 34, f'期望 34（28 + 6），实际 {total}'
  for name in COMPILER_FRONTEND_TOOLS:
      assert name in ALL_TOOLS, f'{name} 未加入 ALL_TOOLS'
  print('✅ 6 个前端工具定义全部注册')
  "

═══════════════════════════════════════════════════════
Step 5: MCP 协议级验证
═══════════════════════════════════════════════════════

  用 MCP Client 验证 tools/list 返回 34 个工具（含 6 个新前端工具）：

  cd PROJECT_ROOT
  python -c "
  import asyncio, os
  from mcp import ClientSession
  from mcp.client.stdio import StdioServerParameters, stdio_client

  async def main():
      server_params = StdioServerParameters(
          command='python',
          args=['Plugins/AgentBridge/MCP/server.py'],
          cwd=r'd:\UnrealProjects\Mvpv4TestCodex',
          env={**os.environ, 'PYTHONPATH': 'Plugins/AgentBridge/Scripts/bridge'},
      )
      async with stdio_client(server_params) as (r, w):
          async with ClientSession(r, w) as session:
              await session.initialize()
              tools = await session.list_tools()
              names = [t.name for t in tools.tools]
              print(f'工具总数: {len(names)}')
              assert len(names) == 34, f'期望 34，实际 {len(names)}'
              frontend = [n for n in names if n.startswith('compiler_')]
              print(f'前端工具: {frontend}')
              assert len(frontend) == 6, f'前端工具期望 6，实际 {len(frontend)}'
              print('✅ MCP 协议级验证通过: 34 工具，含 6 个前端工具')

  asyncio.run(main())
  "

═══════════════════════════════════════════════════════
Step 6: 验证现有 28 工具不受影响
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import asyncio, os
  from mcp import ClientSession
  from mcp.client.stdio import StdioServerParameters, stdio_client

  async def main():
      server_params = StdioServerParameters(
          command='python',
          args=['Plugins/AgentBridge/MCP/server.py'],
          cwd=r'd:\UnrealProjects\Mvpv4TestCodex',
          env={**os.environ, 'PYTHONPATH': 'Plugins/AgentBridge/Scripts/bridge'},
      )
      async with stdio_client(server_params) as (r, w):
          async with ClientSession(r, w) as session:
              await session.initialize()
              result = await session.call_tool('get_current_project_state', {})
              print(f'project_state isError={result.isError}')
              print('✅ 现有 Bridge 工具仍正常工作')

  asyncio.run(main())
  "

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：通过

【验收标准】
- MCP_DIR/compiler_tools.py 实现 6 个函数，统一返回 {status, summary, data, warnings, errors}
- tool_definitions.py 新增 COMPILER_FRONTEND_TOOLS（6 个工具）
- ALL_TOOLS 总数从 28 增加到 34
- MCP tools/list 返回 34 个工具
- 现有 28 个 Bridge 工具调用不受影响
- validate_examples.py --strict 通过
```

---
---

# 阶段 4：测试证据标准化

---

## TASK 04：实现测试证据标准化存放 + run_id 规范 ✅

```
目标：定义 run_id 生成规则、测试证据目录结构、证据文件命名规范、
以及 evidence_manifest.json 格式。这是 MCP 后端证据裁决层的前置依赖。

前置依赖：TASK 03 完成

先读这些文件：
- Docs/Current/16_MCP_Repositioning_Plan.md §11.2（run_id 规范待定义事项）
- Docs/Proposals/Phase10_Validation_Testing_Plane_v3.md §2（MCP 在测试中的正确位置）
- Docs/Proposals/Phase10_MCP_Testing_Toolset_v2.md §1（上下游关系）
- ProjectState/Reports/（现有报告目录结构——理解当前证据存放方式）
- Docs/Current/07_Evidence_And_Artifacts.md（现有落盘规则）
读完应掌握：后端证据裁决的上游产物类型，现有证据存放惯例

涉及文件：全部新增，不修改现有文件。

═══════════════════════════════════════════════════════
Step 1: 定义 run_id 生成规则
═══════════════════════════════════════════════════════

  新增文件：PLUGIN_DIR/Schemas/evidence_manifest.schema.json

  run_id 格式：{date}_{short_uuid}
    例：2026-04-11_a3f7b2c1
    date: YYYY-MM-DD
    short_uuid: UUID 前 8 位

  evidence_manifest.schema.json required 字段：
    - run_id（string, pattern: ^\d{4}-\d{2}-\d{2}_[a-f0-9]{8}$）
    - created_at（string, ISO 8601）
    - test_type（enum: automation_test / functional_test / smoke_test / gauntlet_session / manual_check）
    - test_scope（string, 描述测试范围）
    - evidence_items（array of objects）
      每个 item:
        - type（enum: screenshot / log / report / state_summary / assertion_result）
        - path（string, 相对于 run_id 目录的路径）
        - description（string）
        - timestamp（string, ISO 8601）
    - summary（object）
      - total_checks（integer）
      - passed（integer）
      - failed（integer）
      - warnings（integer）
    - status（enum: pass / fail / escalate / pending）

═══════════════════════════════════════════════════════
Step 2: 创建证据管理模块
═══════════════════════════════════════════════════════

  新增文件：PLUGIN_DIR/Scripts/evidence/
  ├── __init__.py
  ├── evidence_manager.py
  └── run_id.py

  run_id.py:
    - generate_run_id() → string（格式：2026-04-11_a3f7b2c1）
    - parse_run_id(run_id) → {date, uuid_short}
    - validate_run_id(run_id) → bool

  evidence_manager.py:
    - EVIDENCE_ROOT = ProjectState/Evidence/（默认根目录）
    - create_evidence_dir(run_id) → 创建 {EVIDENCE_ROOT}/{run_id}/ 并返回路径
      子目录：screenshots/ / logs/ / reports/ / state/
    - register_evidence(run_id, evidence_type, source_path, description) → 复制文件到对应子目录，返回相对路径
    - create_manifest(run_id, test_type, test_scope) → 创建空 manifest
    - add_evidence_item(manifest, type, path, description) → 追加 item
    - save_manifest(manifest, run_id) → 校验 Schema + 保存到 {EVIDENCE_ROOT}/{run_id}/evidence_manifest.json
    - load_manifest(run_id) → 加载 manifest
    - list_runs(date_filter=None) → 列出所有 run_id

═══════════════════════════════════════════════════════
Step 3: 验证 run_id 生成与解析
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys, re
  sys.path.insert(0, 'Plugins/AgentBridge/Scripts')
  from evidence.run_id import generate_run_id, parse_run_id, validate_run_id

  rid = generate_run_id()
  print(f'生成的 run_id: {rid}')
  assert validate_run_id(rid), f'run_id 格式不合法: {rid}'
  parsed = parse_run_id(rid)
  assert 'date' in parsed and 'uuid_short' in parsed
  assert re.match(r'^\d{4}-\d{2}-\d{2}_[a-f0-9]{8}$', rid)
  print(f'✅ run_id 生成/解析/校验通过: date={parsed[\"date\"]}, uuid={parsed[\"uuid_short\"]}')
  "

═══════════════════════════════════════════════════════
Step 4: 验证证据目录创建与 manifest 生成
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys, os, json, tempfile
  sys.path.insert(0, 'Plugins/AgentBridge/Scripts')
  from evidence.run_id import generate_run_id
  from evidence.evidence_manager import create_evidence_dir, create_manifest, add_evidence_item, save_manifest, load_manifest

  # 使用临时目录避免污染项目
  import evidence.evidence_manager as em
  original_root = em.EVIDENCE_ROOT

  with tempfile.TemporaryDirectory() as tmp:
      em.EVIDENCE_ROOT = tmp
      rid = generate_run_id()

      # 创建证据目录
      edir = create_evidence_dir(rid)
      assert os.path.isdir(os.path.join(edir, 'screenshots'))
      assert os.path.isdir(os.path.join(edir, 'logs'))
      assert os.path.isdir(os.path.join(edir, 'reports'))
      assert os.path.isdir(os.path.join(edir, 'state'))
      print(f'✅ 证据目录创建成功: {edir}')

      # 创建 manifest
      m = create_manifest(rid, 'smoke_test', 'Phase 10 冒烟验证')
      add_evidence_item(m, 'log', 'logs/test.log', '冒烟测试日志')
      add_evidence_item(m, 'screenshot', 'screenshots/hud.png', 'HUD 截图')
      save_manifest(m, rid)

      # 加载 manifest
      loaded = load_manifest(rid)
      assert loaded['run_id'] == rid
      assert len(loaded['evidence_items']) == 2
      assert loaded['status'] == 'pending'
      print(f'✅ Manifest 创建/保存/加载通过: {len(loaded[\"evidence_items\"])} items')

      em.EVIDENCE_ROOT = original_root
  "

═══════════════════════════════════════════════════════
Step 5: 验证基线回归
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：通过

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/MCP/server.py
  # 预期：无变更（本 TASK 不改 MCP Server）

【验收标准】
- Schemas/evidence_manifest.schema.json 定义完整字段
- run_id 格式为 {YYYY-MM-DD}_{8位hex}，可生成/解析/校验
- evidence_manager 可创建目录结构（screenshots/logs/reports/state 4 个子目录）
- manifest 可创建/追加/保存/加载，保存时通过 Schema 校验
- validate_examples.py --strict 通过
- 现有稳定文件无变更
```

---
---

# 阶段 5：MCP 后端工具注册

---

## TASK 05：注册 MCP 后端证据裁决工具 ✅

```
目标：在现有 MCP Server 中注册后端证据裁决工具。
这些工具是 MCP 认知桥接层后端的核心——AI Agent 通过它们读取测试证据，
形成 pass/fail/escalate 裁决，不直接控制 PIE 或模拟输入。

前置依赖：TASK 04 完成

先读这些文件：
- Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md §1（后端定位）
- Docs/Proposals/Phase10_MCP_Testing_Toolset_v2.md §3（最小工具族建议）
- Docs/Proposals/Phase10_Validation_Testing_Plane_v3.md §2（正确位置）、§4（不应包含的工具）
- PLUGIN_DIR/Scripts/evidence/evidence_manager.py（TASK 04 新增的证据管理模块）
- MCP_DIR/server.py（当前 MCP Server——理解注册模式）
- MCP_DIR/compiler_tools.py（TASK 03 新增——参考实现模式）
读完应掌握：后端工具族定义，证据管理接口，工具注册模式

涉及文件：
- MCP_DIR/tool_definitions.py（修改——追加后端工具定义）
- MCP_DIR/server.py（修改——追加后端工具注册和 dispatch）
- MCP_DIR/evidence_tools.py（新增——后端工具实现）

═══════════════════════════════════════════════════════
Step 1: 新增 evidence_tools.py
═══════════════════════════════════════════════════════

  新增文件：MCP_DIR/evidence_tools.py

  实现以下 8 个函数：

  A. 证据读取（4 个）：
  evidence_load_manifest(run_id):
    - 调用 evidence_manager.load_manifest(run_id)
    - 返回 {status, summary, data: manifest}

  evidence_load_screenshots(run_id):
    - 列出 {EVIDENCE_ROOT}/{run_id}/screenshots/ 下所有文件
    - 返回 {status, summary, data: {files: [path, ...]}}

  evidence_load_logs(run_id):
    - 读取 {EVIDENCE_ROOT}/{run_id}/logs/ 下所有日志文件内容
    - 返回 {status, summary, data: {logs: [{file, content}, ...]}}

  evidence_load_report(run_id):
    - 读取 {EVIDENCE_ROOT}/{run_id}/reports/ 下所有报告
    - 返回 {status, summary, data: {reports: [{file, content}, ...]}}

  B. 裁决输出（3 个）：
  evidence_judge_acceptance(run_id, criteria):
    - 加载 manifest → 检查 evidence_items 覆盖度 → 返回初步判定
    - criteria: {required_types: [...], min_checks: N}
    - 返回 {status, summary, data: {judgment: pass/fail/escalate, confidence, reasoning, open_questions}}

  evidence_decide_escalation(run_id):
    - 加载 manifest → 检查是否需要人工确认
    - 返回 {status, summary, data: {needs_human: bool, reason, escalation_note}}

  evidence_export_summary(run_id):
    - 加载 manifest → 汇总所有证据 → 输出结构化验收摘要
    - 返回 {status, summary, data: {run_id, test_type, status, evidence_count, judgment, open_questions}}

  C. 运行管理（1 个）：
  evidence_list_runs(date_filter=None):
    - 调用 evidence_manager.list_runs(date_filter)
    - 返回 {status, summary, data: {runs: [...]}}

  所有函数统一返回 {status, summary, data, warnings, errors} 格式。

═══════════════════════════════════════════════════════
Step 2: 在 tool_definitions.py 追加后端工具定义
═══════════════════════════════════════════════════════

  新增 EVIDENCE_JUDGE_TOOLS dict（8 个工具）：

  evidence_load_manifest:
    params: {run_id: string}
  evidence_load_screenshots:
    params: {run_id: string}
  evidence_load_logs:
    params: {run_id: string}
  evidence_load_report:
    params: {run_id: string}
  evidence_judge_acceptance:
    params: {run_id: string, criteria: object}
  evidence_decide_escalation:
    params: {run_id: string}
  evidence_export_summary:
    params: {run_id: string}
  evidence_list_runs:
    params: {date_filter: string (optional)}

  将 EVIDENCE_JUDGE_TOOLS 加入 ALL_TOOLS。
  ALL_TOOLS 总数应为 42（28 Bridge + 6 前端 + 8 后端）。

═══════════════════════════════════════════════════════
Step 3: 在 server.py 追加后端工具注册
═══════════════════════════════════════════════════════

  在 create_mcp_server() 中：
  - 导入 evidence_tools 模块
  - 为 8 个后端工具注册到 TOOL_DISPATCH
  - 在 @server.list_tools() 中追加 8 个工具的 JSON Schema
  - 在 dispatch_tool() 中追加分发逻辑

═══════════════════════════════════════════════════════
Step 4: 验证工具注册
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import sys
  sys.path.insert(0, 'Plugins/AgentBridge/MCP')
  from tool_definitions import ALL_TOOLS, COMPILER_FRONTEND_TOOLS, EVIDENCE_JUDGE_TOOLS
  print(f'前端工具: {len(COMPILER_FRONTEND_TOOLS)}')
  print(f'后端工具: {len(EVIDENCE_JUDGE_TOOLS)}')
  total = len(ALL_TOOLS)
  print(f'工具总数: {total}')
  assert total == 42, f'期望 42（28+6+8），实际 {total}'
  print('✅ 42 个工具定义全部注册')
  "

═══════════════════════════════════════════════════════
Step 5: MCP 协议级验证
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import asyncio, os
  from mcp import ClientSession
  from mcp.client.stdio import StdioServerParameters, stdio_client

  async def main():
      server_params = StdioServerParameters(
          command='python',
          args=['Plugins/AgentBridge/MCP/server.py'],
          cwd=r'd:\UnrealProjects\Mvpv4TestCodex',
          env={**os.environ, 'PYTHONPATH': 'Plugins/AgentBridge/Scripts/bridge'},
      )
      async with stdio_client(server_params) as (r, w):
          async with ClientSession(r, w) as session:
              await session.initialize()
              tools = await session.list_tools()
              names = [t.name for t in tools.tools]
              print(f'工具总数: {len(names)}')
              assert len(names) == 42, f'期望 42，实际 {len(names)}'
              frontend = [n for n in names if n.startswith('compiler_')]
              backend = [n for n in names if n.startswith('evidence_')]
              print(f'前端工具: {frontend}')
              print(f'后端工具: {backend}')
              assert len(frontend) == 6
              assert len(backend) == 8

              # 验证现有工具不受影响
              result = await session.call_tool('get_current_project_state', {})
              print(f'Bridge 工具: isError={result.isError}')

              print('✅ MCP 协议级验证通过: 42 工具（28 Bridge + 6 前端 + 8 后端）')

  asyncio.run(main())
  "

═══════════════════════════════════════════════════════
Step 6: 验证基线回归
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：通过

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  # 预期：无变更

【验收标准】
- MCP_DIR/evidence_tools.py 实现 8 个函数，统一返回 {status, summary, data, warnings, errors}
- tool_definitions.py 新增 EVIDENCE_JUDGE_TOOLS（8 个工具）
- ALL_TOOLS 总数从 34 增加到 42
- MCP tools/list 返回 42 个工具
- 现有 28 个 Bridge 工具调用不受影响
- validate_examples.py --strict 通过
```

---
---

# 阶段 6：GDD → Skill → Spec 全链路

---

## TASK 06：通过 Pipeline 运行 MonopolyGame GDD 全链路（Stage 1-5 + Handoff） ✅

```
目标：用 MonopolyGame GDD 作为真实输入，通过 MCP 前端 + Compiler Core 跑完
Stage 1-5 全链路，产出完整的 Pipeline 产物（Projection → Planner → 6 Fragments →
Cross-Review → Build IR → Reviewed Handoff v2）。
这不是用 Phase 8 样本数据做冒烟，而是 AI Agent 真正参与的端到端认知分解与编译。

前置依赖：TASK 05 完成
执行者：AI Agent 通过 MCP 工具 + Compiler Core 协作完成
产物输出目录：ProjectState/phase10/

先读这些文件：
- ProjectInputs/GDD/GDD_MonopolyGame.md（完整 GDD，698 行——Stage 1 的真实输入）
  Part A（§1-§4）：游戏概述、棋盘设计（28格/7颜色组）、游戏规则、UI需求
  Part B（§5-§10）：UE5 设置、C++ 类定义、状态机、网络扩展
- Docs/Current/16_MCP_Repositioning_Plan.md §5（Monopoly 示例的前端/Compiler Core 分工）
- Docs/Current/15_Skill_Spec_Handoff_Chain.md §3（流程图）
- COMPILER_DIR/pipeline/pipeline_orchestrator.py（Pipeline 编排入口）
- MCP_DIR/compiler_tools.py（前端工具实现）
- ProjectState/phase8/（Phase 8 样本数据——可对照验证，但不直接复用）
读完应掌握：GDD 完整内容、Pipeline 调度接口、Stage 1-5 各阶段的输入/输出格式

涉及文件：
- ProjectState/phase10/（全部新增——Pipeline 产物）

═══════════════════════════════════════════════════════
Step 1: 创建 Pipeline Session
═══════════════════════════════════════════════════════

  通过 MCP 工具 compiler_create_session 创建 Pipeline 会话：
  - gdd_path: ProjectInputs/GDD/GDD_MonopolyGame.md
  - target_phase: phase1_local_multiplayer
  - output_dir: ProjectState/phase10/

  验证：
  python -c "
  import json, os
  s = json.load(open('ProjectState/phase10/session.json', encoding='utf-8'))
  assert s['current_stage'] == 1
  assert s['status'] == 'pending'
  print(f'✅ Session 创建: id={s[\"session_id\"][:8]}..., stage={s[\"current_stage\"]}')
  "

═══════════════════════════════════════════════════════
Step 2: Stage 1 — MCP 前端认知分解 → GDD Projection
═══════════════════════════════════════════════════════

  通过 MCP 工具 compiler_intake_prepare 获取模板。
  AI Agent 阅读 GDD 全文，填充 GDD Projection：
    - game_identity: game_type=board_strategy, subgenre=monopoly_like, presentation_model=top_down_3d
    - phase_scope: current_phase=phase1_local_multiplayer, in_scope/out_of_scope 完整列表
    - design_domains: 28 格 tile_catalog + 7 color_groups + turn_loop + property_rules + jail_rules + bankruptcy_rules + ui_requirements
    - ambiguities: 至少标记 Blue 单地产组 / TAX base_rent 语义 / 过起点与入狱互斥 3 项
  通过 MCP 工具 compiler_intake_save 校验并保存。

  输出：ProjectState/phase10/gdd_projection.json

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase10/gdd_projection.json', encoding='utf-8'))
  assert d['game_identity']['game_type'] == 'board_strategy'
  assert len(d['design_domains']['tile_catalog']) == 28
  assert len(d['design_domains']['color_groups']) == 7
  assert len(d['ambiguities']) >= 3
  print(f'✅ Stage 1: {len(d[\"design_domains\"][\"tile_catalog\"])} tiles, {len(d[\"design_domains\"][\"color_groups\"])} groups, {len(d[\"ambiguities\"])} ambiguities')
  "

═══════════════════════════════════════════════════════
Step 3: Stage 2 — MCP 前端认知分解 → Planner Output
═══════════════════════════════════════════════════════

  通过 MCP 工具 compiler_plan_prepare 获取模板（含 Stage 1 的 Projection 作为 input_context）。
  AI Agent 基于 Projection 做 Skill 选择和依赖图规划：
    - 6 个 selected_skill_instances:
      skill-board（无依赖）→ skill-tile-event（依赖 board）+ skill-turn（依赖 board）
      → skill-economy（依赖 board, tile-event）→ skill-jail（依赖 turn, economy）
      → skill-ui（依赖 turn, economy, jail）
    - 每个 skill_instance 包含 skill_instance_id / template_id / priority / depends_on
    - dynamic_spec_targets: 至少 9 个
    - capability_gaps: 至少标记 umg-auto-layout / animation 2 项
  通过 MCP 工具 compiler_plan_save 校验并保存。

  输出：ProjectState/phase10/planner_output.json

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase10/planner_output.json', encoding='utf-8'))
  assert len(d['selected_skill_instances']) == 6
  ids = [s['skill_instance_id'] for s in d['selected_skill_instances']]
  assert 'skill-board' in ids and 'skill-ui' in ids
  # 验证依赖图完整性：skill-ui 依赖 skill-turn, skill-economy, skill-jail
  ui = [s for s in d['selected_skill_instances'] if s['skill_instance_id'] == 'skill-ui'][0]
  assert len(ui['depends_on']) >= 3
  print(f'✅ Stage 2: {len(ids)} skills: {ids}')
  "

  ──── MCP 前端边界 ────
  Stage 1-2 完成后，MCP 前端认知分解结束。
  以下 Stage 3-5 由 Compiler Core 调度，Agent 通过 Core 内部 prepare/save 参与。
  ────────────────────────

═══════════════════════════════════════════════════════
Step 4: Stage 3 — Compiler Core 调度 Skill Runtime → 6 个 Skill Fragments
═══════════════════════════════════════════════════════

  通过 pipeline_orchestrator.prepare_stage(session, 3) 获取每个 Skill 的 fragment 模板。
  AI Agent 为每个 skill_instance 填充 fragment：
    - skill-board → board_topology_spec（28 tile_index_list，4 corner_tiles）
    - skill-tile-event → tile_system_spec（28 行 tile_data_table，8 种 tile_types，7 color_groups）
    - skill-turn → turn_flow_spec（10 状态 / 12 转换 FSM，2d6 dice_rules）
    - skill-economy → property_economy_spec（initial $1500，purchase/rent/tax 规则）
    - skill-jail → jail_rule_spec + bankruptcy_rule_spec
    - skill-ui → ui_flow_spec（HUD 4 元素，7 popup_specs，5 widget_blueprints）
  通过 pipeline_orchestrator.save_stage(session, 3, fragments) 校验并保存。

  输出：ProjectState/phase10/skill_fragments/skill-{board,tile-event,turn,economy,jail,ui}.json

  验证：
  python -c "
  import json, os
  frag_dir = 'ProjectState/phase10/skill_fragments'
  frags = sorted(os.listdir(frag_dir))
  print(f'Fragment 数量: {len(frags)}')
  assert len(frags) == 6
  for f in frags:
      d = json.load(open(os.path.join(frag_dir, f), encoding='utf-8'))
      assert d['status'] == 'completed', f'{f} status 不是 completed'
      print(f'  {f}: status={d[\"status\"]}, families={d[\"emitted_families\"]}')
  print('✅ Stage 3: 6 个 Skill Fragment 全部 completed')
  "

═══════════════════════════════════════════════════════
Step 5: Stage 4 — Compiler Core 调度 Cross-Review → Review Report
═══════════════════════════════════════════════════════

  通过 pipeline_orchestrator.prepare_stage(session, 4) 获取模板（含所有 fragments 作为 input_context）。
  AI Agent 执行交叉审查：
    - 至少 13 个 review_checks，结果：≥11 pass，0 fail
    - issues_found 中的问题必须全部 resolved
    - reviewed_dynamic_spec_tree: 7 个 family 合并为统一树
    - lowering_ready: true
  通过 pipeline_orchestrator.save_stage(session, 4, report) 校验并保存。

  输出：ProjectState/phase10/cross_review_report.json

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase10/cross_review_report.json', encoding='utf-8'))
  assert d['review_status'] in ['approved', 'approved_with_warnings']
  assert d['lowering_ready'] == True
  checks = d['review_checks']
  fails = sum(1 for c in checks if c['result'] == 'fail')
  assert fails == 0, f'不应有 fail，实际 {fails} 个'
  print(f'✅ Stage 4: {len(checks)} checks, {fails} fail, status={d[\"review_status\"]}')
  "

═══════════════════════════════════════════════════════
Step 6: Stage 5 — Compiler Core 调度 Lowering → Build IR
═══════════════════════════════════════════════════════

  通过 pipeline_orchestrator.prepare_stage(session, 5) 获取模板。
  AI Agent 将 Reviewed Spec Tree 降级为 Build IR：
    - 14 个 build_steps（create_board_ring_layout → ... → attach_validation_hooks）
    - 12 个 validation_ir（actor_count / property_value / gameplay_rule / ui_widget_exists）
    - lowering_report: 7/7 families_bound, 0 partially_bound
  通过 pipeline_orchestrator.save_stage(session, 5, build_ir) 校验并保存。

  输出：ProjectState/phase10/build_ir.json

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase10/build_ir.json', encoding='utf-8'))
  assert len(d['build_steps']) == 14
  assert len(d['validation_ir']) == 12
  bound = d['lowering_report']['families_bound']
  assert len(bound) == 7
  print(f'✅ Stage 5: {len(d[\"build_steps\"])} steps, {len(d[\"validation_ir\"])} validations, {len(bound)}/7 families')
  "

═══════════════════════════════════════════════════════
Step 7: Handoff Assembly → Reviewed Handoff v2
═══════════════════════════════════════════════════════

  通过 pipeline_orchestrator.assemble_handoff(session) 组装最终交接物：
    - handoff_meta.handoff_version: "2.0"
    - approval.approval_status: approved 或 approved_with_warnings
    - 6 个 skill_instances 全部 status=completed
    - reviewed_dynamic_spec_tree: 7 个 family
    - build_ir: 引用 Stage 5 产物
    - metadata: 完整 source 链路（gdd → projection → planner → review → ir）

  输出：ProjectState/phase10/reviewed_handoff_v2.json

  验证：
  python -c "
  import json
  d = json.load(open('ProjectState/phase10/reviewed_handoff_v2.json', encoding='utf-8'))
  assert d['handoff_meta']['handoff_version'] == '2.0'
  assert d['approval']['approval_status'] in ['approved', 'approved_with_warnings']
  skills = d['selected_skill_instances']
  all_done = all(s['status'] == 'completed' for s in skills)
  assert all_done, '存在未完成的 skill'
  print(f'✅ Handoff v2: version={d[\"handoff_meta\"][\"handoff_version\"]}, approval={d[\"approval\"][\"approval_status\"]}, {len(skills)} skills all_completed={all_done}')
  "

═══════════════════════════════════════════════════════
Step 8: 全量产物完整性验证
═══════════════════════════════════════════════════════

  python -c "
  import json, os
  files = [
      'ProjectState/phase10/session.json',
      'ProjectState/phase10/gdd_projection.json',
      'ProjectState/phase10/planner_output.json',
      'ProjectState/phase10/cross_review_report.json',
      'ProjectState/phase10/build_ir.json',
      'ProjectState/phase10/reviewed_handoff_v2.json',
  ]
  frags = [f'ProjectState/phase10/skill_fragments/{f}' for f in os.listdir('ProjectState/phase10/skill_fragments/')]
  files.extend(sorted(frags))
  print(f'总文件数: {len(files)}')
  for f in files:
      d = json.load(open(f, encoding='utf-8'))
      print(f'  ✅ {f}')
  assert len(files) == 12, f'期望 12（6 主文件 + 6 fragments），实际 {len(files)}'
  print('✅ Phase 10 Pipeline 全部 12 个 JSON 文件合法')
  "

═══════════════════════════════════════════════════════
Step 9: 验证基线回归
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  # 预期：通过

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  # 预期：全部无变更

【验收标准】
- ProjectState/phase10/ 下共 12 个 JSON 文件（6 主文件 + 6 fragments）
- Stage 1-2 通过 MCP 前端工具完成（compiler_intake_*/compiler_plan_*）
- Stage 3-5 通过 Compiler Core 内部 prepare/save 完成（不通过 MCP 对外工具）
- gdd_projection: 28 tiles, 7 color_groups, ≥3 ambiguities
- planner_output: 6 skill instances，依赖图完整
- 6 个 skill_fragments: 全部 status=completed
- cross_review_report: 0 fail, lowering_ready=true
- build_ir: 14 build_steps, 12 validation_ir, 7/7 families_bound
- reviewed_handoff_v2: version=2.0, 全链路 metadata
- session.json status=completed
- validate_examples.py --strict 通过
- 现有稳定文件无变更
```

---
---

# 阶段 7：Spec → 关卡落地

---

## TASK 07：通过 Build IR 在 UE5 Editor 中创建 MonopolyGame 关卡 ✅

```
目标：读取 TASK 06 产出的 Build IR（14 个 build_steps），通过 MCP Bridge Passthrough 工具
在 UE5 Editor 中创建 MonopolyGame 关卡。
Phase 8 已经有 C++ 代码（Source/Mvpv4TestCodex/），本 TASK 利用这些已编译的类，
通过 MCP 工具在场景中实际 spawn Actor、配置属性、搭建关卡。

前置依赖：TASK 06 完成 + UE5 Editor 在线
执行者：AI Agent 通过 MCP Bridge Passthrough 工具操作 UE5 Editor

先读这些文件：
- ProjectState/phase10/build_ir.json（14 个 build_steps——执行蓝图）
- ProjectState/phase10/reviewed_handoff_v2.json（审批状态）
- Docs/History/Proposals/Phase8_DD3_Lowering_Map_and_CPP_Design.md §3（枚举和结构体定义）、§4（9 个核心类）
- Docs/History/Proposals/Phase8_M3_Handover_to_Execution_Agent.md §7（UMG 布局方案——5 个 Widget）
- Source/Mvpv4TestCodex/Public/MMonopolyTypes.h（枚举/结构体定义——确认 C++ 类已存在）
- MCP_DIR/server.py（MCP Bridge 工具——理解 spawn_actor / set_actor_transform 等工具参数）
读完应掌握：14 步如何映射到 MCP 工具调用，已有 C++ 类清单

涉及文件：
- Content/Maps/L_MonopolyBoard_Pipeline.umap（新建关卡——不覆盖 Phase 8 手动成果）
- ProjectState/phase10/execution_log.json（新增——记录每步执行结果）

═══════════════════════════════════════════════════════
Step 1: 确认 Editor 在线 + 已有 C++ 类可用
═══════════════════════════════════════════════════════

  通过 MCP 工具 get_current_project_state 确认 Editor 连接：
  - 预期返回 project_name: Mvpv4TestCodex
  - 预期 Editor 已编译且 MonopolyGame C++ 类可用

  通过 MCP 工具 list_level_actors 确认 Editor 在线。

  注意：Phase 8 手动创建的 L_MonopolyBoard 不动。
  本 TASK 新建 L_MonopolyBoard_Pipeline 作为 Pipeline 驱动的独立关卡，
  完成后可与 Phase 8 关卡对比验证。

═══════════════════════════════════════════════════════
Step 2: 创建 Pipeline 专用关卡
═══════════════════════════════════════════════════════

  通过 MCP 工具 create_level 创建 /Game/Maps/L_MonopolyBoard_Pipeline。
  通过 MCP 工具 open_level 打开该关卡。

  验证：
  通过 MCP 工具 list_level_actors 确认关卡为空（仅默认 Actor）。

═══════════════════════════════════════════════════════
Step 3 (Build Steps 1-4): 棋盘 + 格子 + 玩家
═══════════════════════════════════════════════════════

  对应 build_ir.json 中 step 1-4:

  3a. create_board_ring_layout:
    通过 spawn_actor 生成 1 个 AMBoardManager
    通过 set_actor_transform 设置位置到世界原点

  3b. create_tile_actors:
    通过 spawn_actor 生成 28 个 AMTile Actor
    通过 set_actor_transform 按环形排列设置每个 Tile 的世界坐标
    参数：SideLength=700cm, TileSpacing=100cm, 4 corner_tiles at index 0/7/14/21

  3c. assign_tile_metadata:
    通过 run_editor_python 批量设置 28 个 Tile 的 TileData（FMTileData）
    数据来源：build_ir.json step-03 的 execution_hints

  3d. create_player_tokens:
    通过 spawn_actor 生成 2-4 个 AMPlayerPawn
    通过 set_actor_transform 放置在起点格（index=0）

  验证：
  通过 MCP 工具 list_level_actors 确认：
    - AMBoardManager: 1 个
    - AMTile: 28 个
    - AMPlayerPawn: ≥2 个

═══════════════════════════════════════════════════════
Step 4 (Build Step 5): GameMode 配置
═══════════════════════════════════════════════════════

  通过 MCP 工具 configure_gamemode_bp 或 configure_world_settings：
  - 设置 World Settings 的 DefaultGameMode 为 AMMonopolyGameMode
  - 设置 PlayerControllerClass 为 AMMonopolyPlayerController

  验证：
  通过 MCP 工具 run_editor_python 检查 World Settings:
    python -c "确认 GameMode == MMonopolyGameMode"

═══════════════════════════════════════════════════════
Step 5 (Build Steps 6-11): 逻辑绑定验证
═══════════════════════════════════════════════════════

  Build Steps 6-11（FSM / 骰子 / 事件分发 / 经济 / 监狱 / 破产）是 C++ 代码逻辑，
  Phase 8 已经实现在 Source/Mvpv4TestCodex/ 中。
  本步骤通过 MCP 工具 run_editor_python 执行验证脚本确认逻辑正确：

  6a. val-05: 确认初始状态 == WaitForRoll
  6b. val-06: RollDice() 多次，结果全在 [2,12]
  6c. val-07: 8 种格子事件正确分发
  6d. val-08: 购买扣款正确 + 颜色组租金翻倍
  6e. val-09: 监狱全路径
  6f. val-10: 破产释放地产 + 游戏结束

═══════════════════════════════════════════════════════
Step 6 (Build Steps 12-13): UI Widget 创建与绑定
═══════════════════════════════════════════════════════

  通过 MCP 工具 create_widget_blueprint 创建：
  - WBP_GameHUD（基于 MGameHUDWidget C++ 类）
  - WBP_DicePopup / WBP_BuyPopup / WBP_InfoPopup / WBP_JailPopup（基于 MPopupWidget）

  通过 MCP 工具 run_editor_python 验证：
  - val-11: 5 个 Widget Blueprint 存在
  - val-12: 10 个事件委托已绑定

═══════════════════════════════════════════════════════
Step 7 (Build Step 14): 验证钩子
═══════════════════════════════════════════════════════

  通过 MCP 工具 run_editor_python 运行 12 个基础验证检查点：
    val-01: AMTile 数量 == 28
    val-02: TileDataArray 28 条，PROPERTY 类型 16 个且 Price > 0
    val-03: AMPlayerPawn 数量 ≥ 2
    val-04: GameMode 正确
    val-05 ~ val-12: 同上

═══════════════════════════════════════════════════════
Step 8: 记录执行日志
═══════════════════════════════════════════════════════

  将每步执行结果写入 ProjectState/phase10/execution_log.json:
    - 每条记录：{step, ir_action, mcp_tool_used, status, summary, timestamp}
    - 14 个 build_steps 全部记录

  验证：
  python -c "
  import json
  log = json.load(open('ProjectState/phase10/execution_log.json', encoding='utf-8'))
  print(f'执行记录数: {len(log)}')
  assert len(log) >= 14
  failed = [l for l in log if l['status'] == 'failed']
  print(f'失败: {len(failed)}')
  for f in failed: print(f'  ❌ {f[\"step\"]}: {f[\"ir_action\"]}')
  if not failed: print('✅ 14 步全部成功')
  "

═══════════════════════════════════════════════════════
Step 9: 保存关卡
═══════════════════════════════════════════════════════

  通过 MCP 工具 save_all 保存所有修改。

  通过 MCP 工具 capture_screenshot 截取关卡编辑器视图，
  保存到 ProjectState/Evidence/ 用于后续证据裁决。

【验收标准】
- Editor 在线，关卡 L_MonopolyBoard_Pipeline 已创建并打开
- Phase 8 关卡 L_MonopolyBoard 未被修改
- 28 个 AMTile + ≥2 个 AMPlayerPawn + 1 个 AMBoardManager 存在于场景中
- World Settings DefaultGameMode = AMMonopolyGameMode
- 12 个基础验证检查点通过（val-01 ~ val-12）
- 5 个 Widget Blueprint 存在
- execution_log.json 记录 14 步，0 failed
- 关卡已保存
- 至少 1 张编辑器截图已保存到 Evidence
```

---
---

# 阶段 8：运行时验证 + MCP 后端证据裁决

---

## TASK 08：运行时集成验证 + MCP 后端证据裁决 ✅

```
目标：
A. 在 UE5 Editor 中执行运行时集成验证（Play → 冒烟 → 截图 → 日志）
B. 收集测试证据到标准化目录（run_id + manifest）
C. 通过 MCP 后端工具执行证据裁决（pass/fail/escalate）
D. 修订 Phase 10 计划中与治理口径矛盾的内容

这是完整 Pipeline 的最后一环：
GDD → Skill → Spec → Build IR → 关卡创建 → 运行时验证 → **证据裁决**

前置依赖：TASK 07 完成 + UE5 Editor 在线

先读这些文件：
- Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md §7（评估检查表）
- Docs/Current/16_MCP_Repositioning_Plan.md §11.3（val_simulate_input 矛盾）
- Docs/Proposals/Phase10_MCP_Testing_Toolset_v2.md §3（后端工具族）
- MCP_DIR/evidence_tools.py（后端工具实现）
- PLUGIN_DIR/Scripts/evidence/evidence_manager.py（证据管理模块）
读完应掌握：证据裁决流程，后端工具使用方式

涉及文件：
- ProjectState/Evidence/{run_id}/（新增——标准化证据目录）
- Docs/Current/16_MCP_Repositioning_Plan.md（修改 §11.3 标记已处理）

═══════════════════════════════════════════════════════
Step 1: 运行时集成验证（7 个验证点）
═══════════════════════════════════════════════════════

  在 Editor 中 Play，执行以下 7 个运行时验证点：

  val-13: L_MonopolyBoard_Pipeline 关卡中 World Settings DefaultGameMode 正确绑定
  val-14: World Settings 默认 GameMode = AMMonopolyGameMode
  val-15: Play 后场景非黑屏（有基础光照）
  val-16: HUD 在视口中可见（当前玩家/资金/回合/格子 4 个元素）
  val-17: 鼠标光标可见，按钮可悬停可点击
  val-18: Popup 可显示、可关闭，关闭后焦点恢复
  val-19: 完成至少一轮冒烟：掷骰 → 移动/结算 → 结束回合

  通过 MCP 工具 capture_screenshot 截取：
  - 编辑器关卡概览截图
  - Play 状态 HUD 截图
  - Popup 弹出截图

  通过 MCP 工具 run_automation_tests 执行自动化测试（如已注册）。

═══════════════════════════════════════════════════════
Step 2: 收集证据到标准化目录
═══════════════════════════════════════════════════════

  通过 evidence_manager 创建 run_id 和证据目录：

  python -c "
  import sys
  sys.path.insert(0, 'Plugins/AgentBridge/Scripts')
  from evidence.run_id import generate_run_id
  from evidence.evidence_manager import create_evidence_dir, create_manifest, add_evidence_item, save_manifest

  rid = generate_run_id()
  edir = create_evidence_dir(rid)
  m = create_manifest(rid, 'smoke_test', 'Phase 10 MonopolyGame 运行时集成验证')
  # 后续步骤中将截图/日志/报告注册到 manifest
  print(f'run_id: {rid}')
  print(f'evidence_dir: {edir}')
  "

  将以下证据注册到 manifest：
  - screenshots/: 编辑器截图、HUD 截图、Popup 截图
  - logs/: Editor 日志、Play 日志
  - reports/: 12 个基础验证结果、7 个运行时验证结果
  - state/: runtime_state_summary（GameMode 状态、玩家状态）

═══════════════════════════════════════════════════════
Step 3: MCP 后端证据裁决
═══════════════════════════════════════════════════════

  通过 MCP 工具执行证据裁决链：

  1. evidence_load_manifest(run_id) — 加载证据清单
  2. evidence_load_screenshots(run_id) — 加载截图
  3. evidence_load_logs(run_id) — 加载日志
  4. evidence_load_report(run_id) — 加载报告
  5. evidence_judge_acceptance(run_id, criteria) — 裁决验收
     criteria: {required_types: ['screenshot', 'log', 'report', 'state_summary'], min_checks: 19}
  6. evidence_decide_escalation(run_id) — 判断是否需人工确认
  7. evidence_export_summary(run_id) — 输出最终验收摘要

  预期裁决结果：
  - 19 个验证点（12 基础 + 7 运行时）全部通过 → judgment: pass
  - 或部分运行时验证需人工确认 → judgment: escalate + escalation_note

═══════════════════════════════════════════════════════
Step 4: 修订 Phase 10 计划中的矛盾项
═══════════════════════════════════════════════════════

  在 Docs/Current/16_MCP_Repositioning_Plan.md §11.3 中：
  - 确认 val_simulate_input 和 val_pie_control 已从 MCP Validation Plane 移出
  - 更新状态为"已处理"

═══════════════════════════════════════════════════════
Step 5: 14 号文档评估检查表
═══════════════════════════════════════════════════════

  逐项验证：
  1. MCP 前端只覆盖 Stage 1-2？→ TASK 06 Step 2-3 通过 MCP 工具，Step 4-6 通过 Core
  2. Stage 3-5 由 Compiler Core 调度？→ TASK 06 Step 4-6 使用 pipeline_orchestrator
  3. MCP 后端只做证据判读？→ 本 TASK Step 3 仅读取证据做裁决，不控制 PIE
  4. Bridge Passthrough 保留但不膨胀？→ Bridge 仍为 28 个
  5. val_simulate_input / val_pie_control 已移出？→ Step 4 已处理

═══════════════════════════════════════════════════════
Step 6: 验证基线回归
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  python -c "
  import importlib.util, json, pathlib
  script = pathlib.Path('ProjectState/phase10/task08_orchestrate.py').resolve()
  spec = importlib.util.spec_from_file_location('task08_orchestrate', script)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  result = module.run_no_editor_equivalent_regression()
  print(json.dumps(result, ensure_ascii=False, indent=2))
  assert result['status'] == 'passed'
  "
  # 预期：通过（无编辑器 Stage 分段等价验证）

【验收标准】
- 7 个运行时集成验证点通过（val-13 ~ val-19）
- 证据目录 ProjectState/Evidence/{run_id}/ 包含 screenshots/logs/reports/state 4 个子目录
- evidence_manifest.json 已创建且包含 ≥4 个 evidence_items
- MCP 后端裁决完成：evidence_judge_acceptance 返回 pass 或 escalate（不应为 fail）
- evidence_export_summary 输出完整验收摘要
- 至少 1 张 HUD 截图 + 1 份 Play 日志 + 1 份验证报告 + 1 份冒烟结论
- 16 号文档 §11.3 矛盾项已标记为已处理
- 14 号文档 §7 评估检查表全部通过
- validate_examples.py --strict 通过
- 无编辑器 Stage 分段等价验证通过（6/6）
```

---
---

# 阶段 9：最终验收 + 文档收尾

---

## TASK 09：Phase 10 最终验收 + 文档切换 ✅

```
目标：完成 Phase 10 最终验收，更新文档到 Phase 10 完成口径，归档过程文档。

前置依赖：TASK 08 完成

先读这些文件：
- Docs/Current/00_Index.md（当前索引——需更新到 Phase 10 完成口径）
- Docs/Current/01_Project_Baseline.md（基线——需补入 Phase 10 产出事实）
- Docs/Current/02_Current_Phase_Goals.md（需切换到 Phase 10 已完成状态）
- CLAUDE.md（需更新当前阶段描述）
- AGENTS.md（需更新版本号和文档路径）
- Plugins/AgentBridge/Docs/architecture_overview.md（检查架构图是否仍与实现一致）
读完应掌握：哪些文档需要更新为 Phase 10 完成口径

涉及文件：
- Docs/Current/（修改多个文件）
- CLAUDE.md（修改）
- AGENTS.md（修改）
- task.md（更新状态）

═══════════════════════════════════════════════════════
Step 1: 工具清单最终确认
═══════════════════════════════════════════════════════

  cd PROJECT_ROOT
  python -c "
  import asyncio, os
  from mcp import ClientSession
  from mcp.client.stdio import StdioServerParameters, stdio_client

  async def main():
      server_params = StdioServerParameters(
          command='python',
          args=['Plugins/AgentBridge/MCP/server.py'],
          cwd=r'd:\UnrealProjects\Mvpv4TestCodex',
          env={**os.environ, 'PYTHONPATH': 'Plugins/AgentBridge/Scripts/bridge'},
      )
      async with stdio_client(server_params) as (r, w):
          async with ClientSession(r, w) as session:
              await session.initialize()
              tools = await session.list_tools()
              names = sorted([t.name for t in tools.tools])
              print(f'MCP 工具总数: {len(names)}')
              print('─── Bridge Passthrough（28）───')
              bridge = [n for n in names if not n.startswith('compiler_') and not n.startswith('evidence_')]
              for n in bridge: print(f'  {n}')
              print('─── Compiler 前端（6）───')
              frontend = [n for n in names if n.startswith('compiler_')]
              for n in frontend: print(f'  {n}')
              print('─── Evidence 后端（8）───')
              backend = [n for n in names if n.startswith('evidence_')]
              for n in backend: print(f'  {n}')
              assert len(names) == 42
              print('✅ 最终工具清单确认: 42 工具（28 + 6 + 8）')

  asyncio.run(main())
  "

═══════════════════════════════════════════════════════
Step 2: 全量回归验证
═══════════════════════════════════════════════════════

  python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
  python -c "
  import importlib.util, json, pathlib
  script = pathlib.Path('ProjectState/phase10/task08_orchestrate.py').resolve()
  spec = importlib.util.spec_from_file_location('task08_orchestrate', script)
  module = importlib.util.module_from_spec(spec)
  spec.loader.exec_module(module)
  result = module.run_no_editor_equivalent_regression()
  print(json.dumps(result, ensure_ascii=False, indent=2))
  assert result['status'] == 'passed'
  "

  git diff Plugins/AgentBridge/Source/
  git diff Plugins/AgentBridge/Scripts/bridge/
  git diff Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py
  git diff Plugins/AgentBridge/AgentBridgeTests/
  git diff Plugins/AgentBridge/Schemas/common/
  git diff Plugins/AgentBridge/Schemas/feedback/
  # 预期：全部无变更

═══════════════════════════════════════════════════════
Step 3: 更新文档到 Phase 10 完成口径
═══════════════════════════════════════════════════════

  00_Index.md:
    - 状态 → Completed
    - 补入 Phase 10 完成事实

  01_Project_Baseline.md:
    - 补入 Phase 10 产出：
      - Compiler Pipeline Orchestrator（session / 5-stage 编排 / Handoff 组装）
      - MCP 前端 6 工具（Stage 1-2 认知分解）
      - MCP 后端 8 工具（证据裁决）
      - 测试证据标准化（run_id / manifest / 目录结构）
      - MCP 工具总数：42（28 Bridge + 6 前端 + 8 后端）
      - GDD→Skill→Spec→Build IR→关卡落地 端到端 Pipeline 验证通过
      - MCP 后端证据裁决闭环验证通过

  02_Current_Phase_Goals.md:
    - 当前阶段 → Phase 10 已完成
    - 补入完成结果与当前约束

  CLAUDE.md:
    - 当前阶段 → Phase 10 已完成
    - 最后更新日期 → 当天

  AGENTS.md:
    - 版本 → v1.3（Phase 10 完成口径）

  architecture_overview.md:
    - 将 “Phase 10 准备阶段将...” 更新为完成口径

═══════════════════════════════════════════════════════
Step 4: 创建 Phase 10 收尾文档
═══════════════════════════════════════════════════════

  新增：Docs/Current/17_Phase10_Closeout.md

  内容：
  - Phase 10 目标回顾
  - 交付物清单（新增文件 + 修改文件）
  - 工具清单（42 = 28 + 6 + 8）
  - 端到端验证证据引用（Pipeline 产物 + 关卡截图 + 证据裁决结果）
  - Pipeline 流程总结：GDD → Stage 1-2（MCP 前端）→ Stage 3-5（Compiler Core）→ Build IR → 关卡 → 运行时验证 → 证据裁决（MCP 后端）
  - 遗留事项（如有，需明确说明无编辑器验收采用分段等价验证）

═══════════════════════════════════════════════════════
Step 5: 更新 task.md 状态
═══════════════════════════════════════════════════════

  将本文件中所有 TASK 状态更新为 ✅，里程碑状态更新为 ✅ 已完成。

═══════════════════════════════════════════════════════
Step 6: 验证文档口径一致性
═══════════════════════════════════════════════════════

  grep "Phase 10" CLAUDE.md
  # 预期：匹配到完成口径

  grep "v1.3" AGENTS.md
  # 预期：匹配到版本号

  test -f Docs/Current/17_Phase10_Closeout.md
  # 预期：文件存在

  test -d ProjectState/phase10/
  # 预期：Pipeline 产物目录存在

  test -f ProjectState/phase10/reviewed_handoff_v2.json
  # 预期：最终 Handoff 产物存在

  ls ProjectState/Evidence/
  # 预期：至少 1 个 run_id 目录存在

【验收标准】
- MCP 工具总数 42（28 Bridge + 6 前端 + 8 后端），协议级验证通过
- validate_examples.py --strict 通过
- 无编辑器 Stage 分段等价验证通过
- 所有稳定文件无变更（C++ / Bridge / Orchestrator / AgentBridgeTests / 稳定 Schema）
- ProjectState/phase10/ 包含完整 Pipeline 产物（12 JSON）
- ProjectState/Evidence/ 包含至少 1 组标准化证据（含 manifest）
- 00_Index.md / 01_Project_Baseline.md / 02_Current_Phase_Goals.md / CLAUDE.md / AGENTS.md 已更新到 Phase 10 完成口径
- 17_Phase10_Closeout.md 存在且包含端到端流程总结
- task.md 所有 TASK 状态为 ✅
```
