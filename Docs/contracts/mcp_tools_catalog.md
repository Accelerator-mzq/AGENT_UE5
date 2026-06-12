# MCP Tools Catalog — 57 工具字段级签名表

> 版本: v1.2(2026-06-12,Phase 14 新增 `demo_story_fetch/submit` demo story 工具对,55→57;2026-06-11 Phase 13 新增 `compiler_skill_synthesis_prepare/save` 合成工具对,53→55)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 + Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md §4.2 + Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md
> 关联 FEATURE_INVENTORY: Docs/FEATURE_INVENTORY.md F-MCP-* + F-BRG-* + F-CMP-25 族
> 权威源: Plugins/AgentBridge/MCP/tool_definitions.py(`len(ALL_TOOLS) == 57`,Python 实测)
> 数字注脚: **Python `len()` 实测 57**(Bridge 28 + 前端 18 + 后端 11;demo 工具对注册在 `COMPILER_FRONTEND_TOOLS` 内,16→18),以 `len()` 实测为准;tool_definitions.py:565 分类合计注释已与实测一致

## 主表(57 工具)

| 工具名 | 类别 | 输入 Schema | 输出 Schema | 错误码 | 使用场景 |
|--------|------|-------------|-------------|--------|----------|
| get_current_project_state | Bridge L1 查询 | n/a — 见 tool_definitions.py:23 | Schemas/feedback/project/get_current_project_state.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 查询 UE5 项目运行态 |
| list_level_actors | Bridge L1 查询 | n/a — 见 tool_definitions.py:28 | Schemas/feedback/level/list_level_actors.response.schema.json | INVALID_ARGS, EDITOR_NOT_READY | 列出关卡 Actor |
| get_actor_state | Bridge L1 查询 | n/a — 见 tool_definitions.py:36 | Schemas/feedback/actor/get_actor_state.response.schema.json | ACTOR_NOT_FOUND, INVALID_ARGS | 读取单 Actor 完整状态 |
| get_actor_bounds | Bridge L1 查询 | n/a — 见 tool_definitions.py:43 | Schemas/feedback/actor/get_actor_bounds.response.schema.json | ACTOR_NOT_FOUND, INVALID_ARGS | 读取 Actor 包围盒 |
| get_asset_metadata | Bridge L1 查询 | n/a — 见 tool_definitions.py:50 | Schemas/feedback/asset/get_asset_metadata.response.schema.json | ASSET_NOT_FOUND, INVALID_ARGS | 读取资产元数据 |
| get_dirty_assets | Bridge L1 查询 | n/a — 见 tool_definitions.py:57 | Schemas/feedback/asset/get_dirty_assets.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 列出脏资产 |
| run_map_check | Bridge L1 查询 | n/a — 见 tool_definitions.py:62 | Schemas/feedback/validation/run_map_check.response.schema.json | EDITOR_NOT_READY, INVALID_ARGS | 执行关卡 MapCheck |
| spawn_actor | Bridge L1 写 | n/a — 见 tool_definitions.py:72 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 关卡内生成 Actor |
| set_actor_transform | Bridge L1 写 | n/a — 见 tool_definitions.py:87 | Schemas/write_feedback/write_operation_feedback.response.schema.json | ACTOR_NOT_FOUND, INVALID_ARGS | 修改 Actor Transform |
| import_assets | Bridge L1 写 | n/a — 见 tool_definitions.py:97 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, TOOL_EXECUTION_FAILED | 外部资产导入 |
| create_blueprint_child | Bridge L1 写 | n/a — 见 tool_definitions.py:107 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, TOOL_EXECUTION_FAILED | 创建 Blueprint 子类 |
| set_actor_collision | Bridge L1 写 | n/a — 见 tool_definitions.py:116 | Schemas/write_feedback/write_operation_feedback.response.schema.json | ACTOR_NOT_FOUND, INVALID_ARGS | 设置 Actor 碰撞 |
| assign_material | Bridge L1 写 | n/a — 见 tool_definitions.py:127 | Schemas/write_feedback/write_operation_feedback.response.schema.json | ACTOR_NOT_FOUND, ASSET_NOT_FOUND | 给 Actor 赋材质 |
| capture_screenshot | Bridge L1 服务 | n/a — 见 tool_definitions.py:140 | Schemas/write_feedback/write_operation_feedback.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 视口截图 |
| save_named_assets | Bridge L1 服务 | n/a — 见 tool_definitions.py:147 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, ASSET_NOT_FOUND | 保存指定资产 |
| build_project | Bridge L1 服务 | n/a — 见 tool_definitions.py:154 | Schemas/write_feedback/write_operation_feedback.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | C++ 工程编译 |
| run_automation_tests | Bridge L1 服务 | n/a — 见 tool_definitions.py:162 | Schemas/write_feedback/write_operation_feedback.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 跑 Automation 测试 |
| undo_last_transaction | Bridge L1 服务 | n/a — 见 tool_definitions.py:169 | Schemas/write_feedback/write_operation_feedback.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 撤销上一步事务 |
| create_level | Bridge L2 资产 | n/a — 见 tool_definitions.py:182 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 创建新关卡 |
| create_material | Bridge L2 资产 | n/a — 见 tool_definitions.py:194 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, TOOL_EXECUTION_FAILED | 创建材质母版 |
| create_material_instance | Bridge L2 资产 | n/a — 见 tool_definitions.py:205 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, ASSET_NOT_FOUND | 创建材质实例 |
| create_widget_blueprint | Bridge L2 资产 | n/a — 见 tool_definitions.py:217 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, TOOL_EXECUTION_FAILED | 创建 UMG Widget |
| set_blueprint_defaults | Bridge L2 资产 | n/a — 见 tool_definitions.py:228 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, ASSET_NOT_FOUND | 设置 BP 默认属性 |
| configure_gamemode_bp | Bridge L2 资产 | n/a — 见 tool_definitions.py:238 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, ASSET_NOT_FOUND | 配 GameMode BP |
| configure_world_settings | Bridge L2 资产 | n/a — 见 tool_definitions.py:252 | Schemas/write_feedback/write_operation_feedback.response.schema.json | CHANNEL_UNAVAILABLE, INVALID_ARGS | 配置 World Settings |
| open_level | Bridge L2 资产 | n/a — 见 tool_definitions.py:262 | Schemas/write_feedback/write_operation_feedback.response.schema.json | INVALID_ARGS, ASSET_NOT_FOUND | 打开指定关卡 |
| save_all | Bridge L2 资产 | n/a — 见 tool_definitions.py:270 | Schemas/write_feedback/write_operation_feedback.response.schema.json | EDITOR_NOT_READY, TOOL_EXECUTION_FAILED | 保存全部脏资产 |
| run_editor_python | Bridge L3 兜底 | n/a — 见 tool_definitions.py:284 | Schemas/write_feedback/write_operation_feedback.response.schema.json | TOOL_EXECUTION_FAILED, TIMEOUT, UNKNOWN_ERROR | 执行任意 Editor Python |
| compiler_create_session | 前端 Compiler | Schemas/compiler_session.schema.json | Schemas/compiler_session.schema.json | INVALID_ARGS, TOOL_EXECUTION_FAILED | 创建 Pipeline 会话 |
| compiler_root_skill_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:314 | Schemas/root_skill_contract.schema.json | SESSION_NOT_FOUND, STAGE_LOCKED | Stage1 Root Skill 模板 |
| compiler_root_skill_save | 前端 Compiler | Schemas/root_skill_contract.schema.json | Schemas/root_skill_contract.schema.json | INVALID_ARGS, SESSION_NOT_FOUND, STAGE_LOCKED | Stage1 Root Skill 保存 |
| compiler_intake_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:329 | Schemas/gdd_projection.schema.json | SESSION_NOT_FOUND, STAGE_LOCKED | v1 Intake/alias Stage1 prepare |
| compiler_intake_save | 前端 Compiler | Schemas/gdd_projection.schema.json | Schemas/gdd_projection.schema.json | INVALID_ARGS, SESSION_NOT_FOUND, STAGE_LOCKED | v1 Intake/alias Stage1 save |
| compiler_clarification_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:344 | Schemas/clarification_gate_report.schema.json | SESSION_NOT_FOUND, STAGE_LOCKED | Stage2 Clarification 模板 |
| compiler_clarification_save | 前端 Compiler | Schemas/clarification_gate_report.schema.json | Schemas/clarification_gate_report.schema.json | INVALID_ARGS, SESSION_NOT_FOUND, STAGE_LOCKED | Stage2 Clarification 保存 |
| compiler_skill_graph_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:359 | Schemas/skill_graph.schema.json | SESSION_NOT_FOUND, STAGE_LOCKED | Stage3 Skill Graph 模板 |
| compiler_skill_graph_save | 前端 Compiler | Schemas/skill_graph.schema.json | Schemas/skill_graph.schema.json | INVALID_ARGS, SESSION_NOT_FOUND, STAGE_LOCKED | Stage3 Skill Graph 保存 |
| compiler_plan_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:374 | Schemas/planner_output.schema.json | SESSION_NOT_FOUND, STAGE_LOCKED | v1 Plan/alias Stage3 prepare |
| compiler_plan_save | 前端 Compiler | Schemas/planner_output.schema.json | Schemas/planner_output.schema.json | INVALID_ARGS, SESSION_NOT_FOUND, STAGE_LOCKED | v1 Plan/alias Stage3 save |
| compiler_get_session_status | 前端 Compiler | n/a — 见 tool_definitions.py:389 | Schemas/compiler_session.schema.json | SESSION_NOT_FOUND, INVALID_ARGS | 查询会话状态 |
| compiler_stage4_node_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:396 | Schemas/skill_fragment.schema.json | SESSION_NOT_FOUND, INVALID_ARGS, STAGE_LOCKED | Stage4 节点 prompts |
| compiler_stage4_node_save | 前端 Compiler | Schemas/skill_fragment.schema.json | Schemas/skill_fragment.schema.json | INVALID_ARGS, SESSION_NOT_FOUND, STAGE_LOCKED | Stage4 节点保存+Fragment |
| compiler_skill_synthesis_prepare | 前端 Compiler | n/a — 见 tool_definitions.py:418 | n/a — 合成载荷(gap 上下文+6 文件规范+范例+family 白名单) | SESSION_NOT_FOUND, INVALID_ARGS, TOOL_EXECUTION_FAILED | S3.5 合成准备(per gap) |
| compiler_skill_synthesis_save | 前端 Compiler | n/a — 见 tool_definitions.py:426(six_files 6 文件内容) | n/a — data.synthesis_status 三态(saved/rejected/failed)+ errors[] | SESSION_NOT_FOUND, INVALID_ARGS, TOOL_EXECUTION_FAILED | S3.5 合成提交+机器校验 |
| demo_story_fetch | 前端 Compiler | n/a — 见 tool_definitions.py:435(session_path 必填 run 目录;story_id 选填,缺省取计划顺序下一个可发工单) | n/a — data.story(符合 Schemas/demo_story.schema.json)+ data.construction_manifest 全文;manifest 版本不符告警在 warnings[] | INVALID_ARGS, TOOL_EXECUTION_FAILED | P14 取施工 story 全包 |
| demo_story_submit | 前端 Compiler | n/a — 见 tool_definitions.py:443(session_path / story_id / evidence 对象:files_changed/test_report/smoke_report/screenshots/doc_paths/provisional_decisions/plugin_root) | n/a — data.story_status(verified/in_progress)+ data.errors + data.attempts;校验拒绝是业务信号 status 仍 success(failed 仅环境/数据异常触发 MCP isError) | INVALID_ARGS, TOOL_EXECUTION_FAILED | P14 提交 story 证据+守门 |
| evidence_load_manifest | 后端 Evidence | n/a — 见 tool_definitions.py:425 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, MANIFEST_INVALID | 读 evidence manifest |
| evidence_load_screenshots | 后端 Evidence | n/a — 见 tool_definitions.py:432 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, INVALID_ARGS | 读取截图证据 |
| evidence_load_logs | 后端 Evidence | n/a — 见 tool_definitions.py:439 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, INVALID_ARGS | 读取日志证据 |
| evidence_load_report | 后端 Evidence | n/a — 见 tool_definitions.py:446 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, INVALID_ARGS | 读取报告证据 |
| evidence_judge_acceptance | 后端 Evidence | n/a — 见 tool_definitions.py:453 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, INVALID_ARGS, MANIFEST_INVALID | manifest 覆盖度初判 |
| evidence_decide_escalation | 后端 Evidence | n/a — 见 tool_definitions.py:461 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, INVALID_ARGS | 升级人工确认判定 |
| evidence_export_summary | 后端 Evidence | n/a — 见 tool_definitions.py:468 | Schemas/evidence_manifest.schema.json | RUN_NOT_FOUND, TOOL_EXECUTION_FAILED | 导出验收摘要 |
| evidence_list_runs | 后端 Evidence | n/a — 见 tool_definitions.py:475 | Schemas/evidence_manifest.schema.json | INVALID_ARGS, TOOL_EXECUTION_FAILED | 枚举所有 run_id |
| evidence_compare_runs | 后端 Evidence | n/a — 见 tool_definitions.py:482 | Schemas/run_comparison.schema.json | RUN_NOT_FOUND, INVALID_ARGS | 对比两 run 差异 |
| evidence_create_batch | 后端 Evidence | n/a — 见 tool_definitions.py:491 | Schemas/batch_manifest.schema.json | RUN_NOT_FOUND, PROMOTE_REJECTED | 从 run 创建 batch |
| evidence_promote_run | 后端 Evidence | n/a — 见 tool_definitions.py:501 | Schemas/batch_manifest.schema.json | RUN_NOT_FOUND, PROMOTE_REJECTED | promote run 到 baseline |

## 行数自检

- 主表实测行数: 57
- 类别分布:Bridge L1 查询 7 / L1 写 6 / L1 服务 5 / L2 资产 9 / L3 兜底 1 / 前端 18 / 后端 11 = 57 ✓
- 自检命令:`awk -F'|' 'NF != 8 && /^\|/ && !/^\| 工具名/ && !/^\| ---/' Docs/contracts/mcp_tools_catalog.md`(应空)
- Python 实测命令:`python -c "from tool_definitions import ALL_TOOLS; print(len(ALL_TOOLS))"` → `57`
- 口径历史:Phase 11 收尾实测 53(曾与 line 530 注释"51"冲突,源码注释已修);Phase 13(2026-06-11)新增合成工具对后实测 55;Phase 14(2026-06-12)`COMPILER_FRONTEND_TOOLS` 增 `demo_story_fetch/submit` 工具对后实测 **57**,tool_definitions.py:565 分类合计注释与实测一致;**以 `len(ALL_TOOLS)` 实测为准**

## 字段约定

- 工具名:Python 字典 key,snake_case,直接来自 `tool_definitions.py`
- 类别:7 类之一(Bridge L1 查询 / L1 写 / L1 服务 / L2 资产 / L3 兜底 / 前端 Compiler / 后端 Evidence)
- 输入 Schema:`compiler_*_save` 类工具的 `filled_data` 对应 Stage 主链 Schema;其余多为简单参数,标 `n/a — 见 tool_definitions.py:<line>` 指向源码
- 输出 Schema:L1 query → `Schemas/feedback/<area>/...response.schema.json`;L1 write / L2 / L3 写操作 → `Schemas/write_feedback/write_operation_feedback.response.schema.json`;前端 Compiler 输出主链 Stage Schema;后端 Evidence 输出 `evidence_manifest` / `run_comparison` / `batch_manifest`
- 错误码:来自工具 description / params / 错误码列表推断,通用 5 项 = `INVALID_ARGS` / `TIMEOUT` / `PERMISSION_DENIED` / `TOOL_EXECUTION_FAILED` / `UNKNOWN_ERROR`,Compiler/Evidence 特有 `SESSION_NOT_FOUND` / `STAGE_LOCKED` / `RUN_NOT_FOUND` / `MANIFEST_INVALID` / `PROMOTE_REJECTED`
- 使用场景:中文一句话(≤30 字符)

## 注脚

1. **工具数演进口径**:Phase 11 收尾实测 53(Bridge 28 + 前端 14 + 后端 11;历史上 line 530 注释"51"漏算 stage4 节点对,已修);Phase 13(2026-06-11)`COMPILER_FRONTEND_TOOLS` 增 `compiler_skill_synthesis_prepare/save` 合成工具对 → 前端 16、合计 55;Phase 14(2026-06-12)`COMPILER_FRONTEND_TOOLS` 增 `demo_story_fetch/submit` demo story 工具对 → 前端 **18**、合计 **57**。`python -c "from tool_definitions import ALL_TOOLS; print(len(ALL_TOOLS))"` 实测 **57**。**以 `len(ALL_TOOLS)` 实测为准。**
   - **demo 工具对契约要点**(Phase 14):两工具统一走 `_make_response` 契约,顶层 `status` 仅 success/failed(failed 仅环境/数据异常,触发 MCP isError;submit 的证据校验拒绝是业务信号,story 回 in_progress 并返回具体错误,status 仍 success);submit 的 `evidence.plugin_root` 经锚定校验(resolve 后必须落在项目内白名单),增量批附加 v0 冒烟 hash 守门。
2. **输入 Schema 列 `n/a`**:大多数工具参数为基本类型(string / boolean / array),无独立 JSON Schema 文件;`compiler_*_save` 类的 `filled_data` 才对应主链 Stage Schema。L1/L2/L3 写操作的统一反馈 Schema 已落 `Schemas/write_feedback/write_operation_feedback.response.schema.json`。合成工具对的产物是 6 文件 SkillTemplate 包(落 `SkillTemplates/synthesized/<capability_id>/`,manifest 初始 `review_status: pending_review`),不对应单一 JSON Schema;save 的校验结果经 `data.synthesis_status` 三态表达(saved / rejected=机器校验失败应修正重提 / failed=环境失败应排查环境)。
3. **错误码列**:每行 ≥ 1 错误码字符串,部分工具源码已显式列 `error_codes` 字段(`spawn_actor` / `set_actor_transform` / `build_project` / `create_level`),其余按 `tool_contract_v0_1.md §3` 通用错误码族推断。
   - **错误码权威源**:以 `tool_definitions.py` 模块 docstring (line 13-15) 的 9 项为权威源(`INVALID_ARGS / ACTOR_NOT_FOUND / ASSET_NOT_FOUND / EDITOR_NOT_READY / TOOL_EXECUTION_FAILED / CHANNEL_UNAVAILABLE / PERMISSION_DENIED / TIMEOUT / UNKNOWN_ERROR`),Compiler 前端 / Evidence 后端 特有码(`SESSION_NOT_FOUND` / `STAGE_LOCKED` / `RUN_NOT_FOUND` / `MANIFEST_INVALID` / `PROMOTE_REJECTED`)按类别推断。与 `Docs/contracts/tool_contract.md §6.3` 错误码族存在历史口径差,Phase 2 spec 收口时统一。

## 关联文档

- `Docs/contracts/tool_contract.md` — Tool Contract v0.1(返回结构与通用错误码)
- `Docs/contracts/schemas_catalog.md` — Schemas 目录与主链 Stage 映射
- `Docs/contracts/field_specification.md` — 字段级签名规范
- `Plugins/AgentBridge/MCP/tool_definitions.py` — 权威工具定义源码
- `Plugins/AgentBridge/Schemas/` — 57 工具的输入/输出 Schema 实体
