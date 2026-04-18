# MCP 工具数量一致性报告

## 1. 结论

- 当前口径声明：`53 = 49 正式 + 4 alias`
- 实际计数：`53 = 49 正式 + 4 alias`

结论：✅ 当前 MCP 工具总数与 Phase 11 收尾口径一致。

## 2. alias 清单

- `compiler_intake_prepare`
- `compiler_intake_save`
- `compiler_plan_prepare`
- `compiler_plan_save`

## 3. 正式工具清单

- `assign_material`
- `build_project`
- `capture_screenshot`
- `compiler_clarification_prepare`
- `compiler_clarification_save`
- `compiler_create_session`
- `compiler_get_session_status`
- `compiler_root_skill_prepare`
- `compiler_root_skill_save`
- `compiler_skill_graph_prepare`
- `compiler_skill_graph_save`
- `compiler_stage4_node_prepare`
- `compiler_stage4_node_save`
- `configure_gamemode_bp`
- `configure_world_settings`
- `create_blueprint_child`
- `create_level`
- `create_material`
- `create_material_instance`
- `create_widget_blueprint`
- `evidence_compare_runs`
- `evidence_create_batch`
- `evidence_decide_escalation`
- `evidence_export_summary`
- `evidence_judge_acceptance`
- `evidence_list_runs`
- `evidence_load_logs`
- `evidence_load_manifest`
- `evidence_load_report`
- `evidence_load_screenshots`
- `evidence_promote_run`
- `get_actor_bounds`
- `get_actor_state`
- `get_asset_metadata`
- `get_current_project_state`
- `get_dirty_assets`
- `import_assets`
- `list_level_actors`
- `open_level`
- `run_automation_tests`
- `run_editor_python`
- `run_map_check`
- `save_all`
- `save_named_assets`
- `set_actor_collision`
- `set_actor_transform`
- `set_blueprint_defaults`
- `spawn_actor`
- `undo_last_transaction`

## 4. 额外观察

- `tool_definitions.py` 内仍有旧注释口径残留，提示数值与实际实现不一致，需要后续人工决定是否修正。
