"""
MCP Server 工具定义 — 所有工具的参数、返回值、错误码规范。

分三层：
  Layer 1: Bridge 已有工具（15 个）— 包装 query_tools + write_tools
  Layer 2: 新增 Channel A 资产创建工具（9 个）
  Layer 3: 通用兜底（1 个）

所有工具统一返回 tool_contract_v0_1.md 格式：
  {status, summary, data, warnings, errors}

错误码复用 tool_contract_v0_1.md §3 定义：
  INVALID_ARGS, ACTOR_NOT_FOUND, ASSET_NOT_FOUND,
  EDITOR_NOT_READY, TOOL_EXECUTION_FAILED, CHANNEL_UNAVAILABLE,
  PERMISSION_DENIED, TIMEOUT, UNKNOWN_ERROR
"""

# ============================================================
# Layer 1: Bridge 已有工具（复用）
# ============================================================

LAYER1_QUERY_TOOLS = {
    "get_current_project_state": {
        "description": "获取当前 UE5 项目状态（项目名、引擎版本、当前关卡等）",
        "params": {},
        "returns": "项目状态对象"
    },
    "list_level_actors": {
        "description": "列出当前关卡中的所有 Actor",
        "params": {
            "level_path": {"type": "string", "required": False, "description": "关卡路径（默认当前）"},
            "class_filter": {"type": "string", "required": False, "description": "可选类名过滤"}
        },
        "returns": "Actor 列表"
    },
    "get_actor_state": {
        "description": "获取指定 Actor 的完整状态（transform、组件、属性等）",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"}
        },
        "returns": "Actor 状态对象"
    },
    "get_actor_bounds": {
        "description": "获取指定 Actor 的包围盒",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"}
        },
        "returns": "包围盒数据"
    },
    "get_asset_metadata": {
        "description": "获取指定资产的元数据",
        "params": {
            "asset_path": {"type": "string", "required": True, "description": "资产路径"}
        },
        "returns": "资产元数据"
    },
    "get_dirty_assets": {
        "description": "获取所有未保存的脏资产列表",
        "params": {},
        "returns": "脏资产列表"
    },
    "run_map_check": {
        "description": "运行当前关卡的 Map Check，检查错误和警告",
        "params": {
            "level_path": {"type": "string", "required": False, "description": "关卡路径（默认当前）"}
        },
        "returns": "Map Check 结果"
    },
}

LAYER1_WRITE_TOOLS = {
    "spawn_actor": {
        "description": "在当前关卡中生成 Actor",
        "params": {
            "level_path": {"type": "string", "required": False, "description": "关卡路径（默认当前）"},
            "actor_class": {"type": "string", "required": True, "description": "Actor 类路径"},
            "actor_name": {"type": "string", "required": True, "description": "Actor 名称"},
            "transform": {
                "type": "object", "required": True,
                "description": "Transform {location: [x,y,z], rotation: [p,y,r], relative_scale3d: [x,y,z]}"
            },
            "dry_run": {"type": "boolean", "required": False, "description": "模拟执行不实际创建"}
        },
        "returns": "含 actual_transform 的反馈",
        "error_codes": ["INVALID_ARGS", "EDITOR_NOT_READY", "TOOL_EXECUTION_FAILED"]
    },
    "set_actor_transform": {
        "description": "修改指定 Actor 的 Transform",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"},
            "transform": {"type": "object", "required": True, "description": "新 Transform"},
            "dry_run": {"type": "boolean", "required": False}
        },
        "returns": "含 actual_transform 的反馈",
        "error_codes": ["ACTOR_NOT_FOUND", "INVALID_ARGS"]
    },
    "import_assets": {
        "description": "导入外部资产到 UE5 项目",
        "params": {
            "source_dir": {"type": "string", "required": True, "description": "源目录路径"},
            "dest_path": {"type": "string", "required": True, "description": "目标内容浏览器路径"},
            "replace_existing": {"type": "boolean", "required": False, "description": "是否覆盖已有资产"},
            "dry_run": {"type": "boolean", "required": False, "description": "模拟执行不实际导入"}
        },
        "returns": "导入结果"
    },
    "create_blueprint_child": {
        "description": "创建指定父类的 Blueprint 子类",
        "params": {
            "parent_class": {"type": "string", "required": True, "description": "父类路径"},
            "package_path": {"type": "string", "required": True, "description": "Blueprint 保存路径"},
            "dry_run": {"type": "boolean", "required": False, "description": "模拟执行不实际创建"}
        },
        "returns": "创建的 Blueprint 路径"
    },
    "set_actor_collision": {
        "description": "设置 Actor 碰撞配置",
        "params": {
            "actor_path": {"type": "string", "required": True, "description": "Actor 路径"},
            "profile_name": {"type": "string", "required": True, "description": "碰撞 Profile 名称"},
            "collision_enabled": {"type": "string", "required": False, "description": "碰撞模式（默认 QueryAndPhysics）"},
            "can_affect_navigation": {"type": "boolean", "required": False, "description": "是否影响导航"},
            "dry_run": {"type": "boolean", "required": False, "description": "模拟执行不实际写入"}
        },
        "returns": "碰撞设置结果"
    },
    "assign_material": {
        "description": "给 Actor 指定材质",
        "params": {
            "actor_path": {"type": "string", "required": True},
            "material_path": {"type": "string", "required": True},
            "slot_index": {"type": "integer", "required": False, "description": "材质槽索引（默认 0）"},
            "dry_run": {"type": "boolean", "required": False, "description": "模拟执行不实际赋材质"}
        },
        "returns": "材质赋值结果"
    },
}

LAYER1_SERVICE_TOOLS = {
    "capture_screenshot": {
        "description": "截取当前视口截图",
        "params": {
            "output_path": {"type": "string", "required": False, "description": "保存路径"}
        },
        "returns": "截图文件路径"
    },
    "save_named_assets": {
        "description": "保存指定资产",
        "params": {
            "asset_paths": {"type": "array", "required": True, "description": "资产路径列表"}
        },
        "returns": "保存结果"
    },
    "build_project": {
        "description": "编译 C++ 项目",
        "params": {
            "target": {"type": "string", "required": False, "description": "编译目标（默认 Editor）"}
        },
        "returns": "编译结果（成功/失败/错误列表）",
        "error_codes": ["EDITOR_NOT_READY", "TOOL_EXECUTION_FAILED"]
    },
    "run_automation_tests": {
        "description": "运行 UE5 Automation Test",
        "params": {
            "test_filter": {"type": "string", "required": False, "description": "测试过滤器"}
        },
        "returns": "测试结果"
    },
    "undo_last_transaction": {
        "description": "撤销上一次 Transaction",
        "params": {},
        "returns": "撤销结果"
    },
}


# ============================================================
# Layer 2: 新增 Channel A 资产创建工具
# ============================================================

LAYER2_ASSET_TOOLS = {
    "create_level": {
        "description": "创建新关卡",
        "params": {
            "level_name": {"type": "string", "required": True, "description": "关卡名称（如 L_BoardLevel）"},
            "level_path": {"type": "string", "required": False, "description": "保存路径（默认 /Game/Maps/）"},
            "template": {"type": "string", "required": False, "description": "模板（默认 Empty Level）"}
        },
        "returns": "创建的关卡路径",
        "error_codes": ["INVALID_ARGS", "EDITOR_NOT_READY", "TOOL_EXECUTION_FAILED"],
        "channel": "A",
        "notes": "通过 Python Editor Scripting 的 unreal.EditorLevelLibrary 实现"
    },
    "create_material": {
        "description": "创建材质母版",
        "params": {
            "material_name": {"type": "string", "required": True, "description": "材质名称（如 M_TileBase）"},
            "material_path": {"type": "string", "required": False, "description": "保存路径（默认 /Game/Materials/）"},
            "base_color": {"type": "array", "required": False, "description": "基础颜色 [R, G, B, A]（0-1 范围）"}
        },
        "returns": "创建的材质路径",
        "channel": "A",
        "notes": "通过 unreal.AssetToolsHelpers + unreal.MaterialFactoryNew 实现"
    },
    "create_material_instance": {
        "description": "创建材质实例",
        "params": {
            "instance_name": {"type": "string", "required": True, "description": "实例名称（如 MI_Brown）"},
            "parent_material": {"type": "string", "required": True, "description": "父材质路径"},
            "instance_path": {"type": "string", "required": False, "description": "保存路径"},
            "scalar_params": {"type": "object", "required": False, "description": "标量参数 {name: value}"},
            "vector_params": {"type": "object", "required": False, "description": "向量参数 {name: [R,G,B,A]}"}
        },
        "returns": "创建的材质实例路径",
        "channel": "A"
    },
    "create_widget_blueprint": {
        "description": "创建 Widget Blueprint（UMG）",
        "params": {
            "widget_name": {"type": "string", "required": True, "description": "Widget 名称（如 WBP_GameHUD）"},
            "widget_path": {"type": "string", "required": False, "description": "保存路径（默认 /Game/UI/）"},
            "parent_class": {"type": "string", "required": False, "description": "父类（默认 UserWidget）"}
        },
        "returns": "创建的 Widget Blueprint 路径",
        "channel": "A",
        "notes": "通过 Python Editor Scripting 创建，具体 UI 布局需在蓝图编辑器中完成"
    },
    "set_blueprint_defaults": {
        "description": "设置 Blueprint 的默认属性值",
        "params": {
            "blueprint_path": {"type": "string", "required": True, "description": "Blueprint 路径"},
            "property_name": {"type": "string", "required": True, "description": "属性名"},
            "property_value": {"type": "any", "required": True, "description": "属性值"}
        },
        "returns": "设置结果",
        "channel": "A"
    },
    "configure_gamemode_bp": {
        "description": "配置 GameMode Blueprint 的核心设置",
        "params": {
            "gamemode_path": {"type": "string", "required": True, "description": "GameMode BP 路径"},
            "default_pawn_class": {"type": "string", "required": False},
            "player_controller_class": {"type": "string", "required": False},
            "game_state_class": {"type": "string", "required": False},
            "player_state_class": {"type": "string", "required": False},
            "hud_class": {"type": "string", "required": False}
        },
        "returns": "配置结果",
        "channel": "A",
        "notes": "通过 set_blueprint_defaults 设置 GameMode 各默认类引用"
    },
    "configure_world_settings": {
        "description": "配置当前关卡的 World Settings",
        "params": {
            "gamemode_override": {"type": "string", "required": False, "description": "GameMode 覆盖类"},
            "default_gamemode": {"type": "string", "required": False}
        },
        "returns": "配置结果",
        "channel": "B",
        "notes": "通过 Remote Control API 设置 WorldSettings 属性"
    },
    "open_level": {
        "description": "打开指定关卡",
        "params": {
            "level_path": {"type": "string", "required": True, "description": "关卡资产路径"}
        },
        "returns": "打开结果",
        "channel": "A"
    },
    "save_all": {
        "description": "保存所有脏资产",
        "params": {},
        "returns": "保存结果",
        "channel": "A"
    },
}


# ============================================================
# Layer 3: 通用兜底
# ============================================================

LAYER3_TOOLS = {
    "run_editor_python": {
        "description": "在 UE5 Editor 中执行任意 Python 脚本",
        "params": {
            "script": {"type": "string", "required": True, "description": "Python 脚本内容"},
            "timeout_ms": {"type": "integer", "required": False, "description": "超时毫秒数（默认 30000）"}
        },
        "returns": "脚本执行结果（stdout + return value）",
        "channel": "A",
        "notes": "兜底工具，仅在 Layer 1/2 工具无法覆盖时使用"
    },
}


# ============================================================
# Compiler Frontend: v1/v2 认知分解工具
# ============================================================

COMPILER_FRONTEND_TOOLS = {
    "compiler_create_session": {
        "description": "创建 Compiler Pipeline 会话，支持 v1.0 与 v2.0。",
        "params": {
            "gdd_path": {"type": "string", "required": True, "description": "输入 GDD 文件路径"},
            "target_phase": {"type": "string", "required": True, "description": "目标阶段标识"},
            "output_dir": {"type": "string", "required": True, "description": "本次 pipeline 输出目录"},
            "session_version": {"type": "string", "required": False, "description": "Pipeline 版本，默认 1.0，可选 2.0"},
            "run_id": {"type": "string", "required": False, "description": "Phase 11 run_id，可留空自动生成"},
            "fast_mode": {"type": "boolean", "required": False, "description": "是否启用 fast_mode，默认 false"},
            "allow_skill_synthesis": {"type": "boolean", "required": False, "description": "Phase 13 Skill 合成开关，默认 false；开启后持久化进 session.json，Stage 1 保存强制 required capability 携带 source_anchor"},
        },
        "returns": "session_id 与 session_path",
    },
    "compiler_root_skill_prepare": {
        "description": "Phase 11 Stage 1 准备：生成 Root Skill Contract 模板供 Agent 填充。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        },
        "returns": "Root Skill Contract 模板、schema 与输入上下文",
    },
    "compiler_root_skill_save": {
        "description": "Phase 11 Stage 1 保存：校验并保存 Root Skill Contract。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "filled_data": {"type": "object", "required": True, "description": "已填充完成的 Root Skill Contract"},
        },
        "returns": "保存结果与输出路径",
    },
    "compiler_intake_prepare": {
        "description": "旧名 alias：v1 生成 GDD Projection，v2 等价于 compiler_root_skill_prepare。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        },
        "returns": "Stage 1 模板、schema 与输入上下文",
    },
    "compiler_intake_save": {
        "description": "旧名 alias：转发到 compiler_root_skill_save，与正名工具同享 Phase 13 anchor 强制与覆盖矩阵落盘（v1 保存 GDD Projection 行为不变）。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "filled_data": {"type": "object", "required": True, "description": "已填充完成的 Stage 1 产物"},
        },
        "returns": "保存结果与输出路径",
    },
    "compiler_clarification_prepare": {
        "description": "Phase 11 Stage 2 准备：生成 Clarification Gate 模板供 Agent 填充。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        },
        "returns": "Clarification Gate 模板、schema 与输入上下文",
    },
    "compiler_clarification_save": {
        "description": "Phase 11 Stage 2 保存：校验并保存 Clarification Gate Report。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "filled_data": {"type": "object", "required": True, "description": "已填充完成的 Clarification Gate Report"},
        },
        "returns": "保存结果与输出路径",
    },
    "compiler_skill_graph_prepare": {
        "description": "Phase 11 Stage 3 准备：生成 Skill Graph 模板供 Agent 填充。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        },
        "returns": "Skill Graph 模板、schema 与输入上下文",
    },
    "compiler_skill_graph_save": {
        "description": "Phase 11 Stage 3 保存：校验并保存 Skill Graph。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "filled_data": {"type": "object", "required": True, "description": "已填充完成的 Skill Graph"},
        },
        "returns": "保存结果与输出路径",
    },
    "compiler_plan_prepare": {
        "description": "旧名 alias：v1 生成 Planner Output，v2 等价于 compiler_skill_graph_prepare。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        },
        "returns": "Stage 2 模板、schema 与输入上下文",
    },
    "compiler_plan_save": {
        "description": "旧名 alias：v1 保存 Planner Output，v2 等价于 compiler_skill_graph_save。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "filled_data": {"type": "object", "required": True, "description": "已填充完成的 Stage 2 或 Skill Graph 产物"},
        },
        "returns": "保存结果与输出路径",
    },
    "compiler_get_session_status": {
        "description": "查询 Compiler Pipeline 会话当前状态。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        },
        "returns": "session 当前状态对象",
    },
    "compiler_stage4_node_prepare": {
        "description": "Stage 4 逐节点交互：为指定节点的 Discovery/Candidates/Convergence 阶段准备 Agent 输入（SkillTemplate prompts + Context Bundle + 生成指引）。Agent 读取后做创造性生成。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "node_id": {"type": "string", "required": True, "description": "skill_graph 中的 instance_id"},
            "phase": {"type": "string", "required": True, "description": "阶段：discovery / candidates / convergence"},
            "node_state": {"type": "object", "required": False, "description": "前序阶段的 node_state（candidates/convergence 时必须传入 discovery/candidates 结果）"},
        },
        "returns": "SkillTemplate prompts、Context Bundle、生成指引、输出结构示例",
    },
    "compiler_stage4_node_save": {
        "description": "Stage 4 逐节点交互：保存 Agent 为指定节点某阶段生成的输出。校验通过后返回 node_state 供下一阶段使用；convergence 完成后自动生成 Fragment。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "node_id": {"type": "string", "required": True, "description": "skill_graph 中的 instance_id"},
            "phase": {"type": "string", "required": True, "description": "阶段：discovery / candidates / convergence"},
            "output": {"type": "object", "required": True, "description": "Agent 生成的该阶段输出"},
            "node_state": {"type": "object", "required": False, "description": "前序阶段的 node_state"},
        },
        "returns": "校验结果、更新后的 node_state、Fragment（convergence 完成时）",
    },
    "compiler_skill_synthesis_prepare": {
        "description": "S3.5 合成准备：为指定 capability gap 返回 GDD 上下文、6 文件规范、范例模板与执行 family 白名单，供 Agent 现场合成 SkillTemplate。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "capability_id": {"type": "string", "required": True, "description": "skill_graph metadata.capability_gaps 中的能力 ID"},
        },
        "returns": "gap 上下文、file_spec、exemplars、family_whitelist、naming_rules、instructions",
    },
    "compiler_skill_synthesis_save": {
        "description": "S3.5 合成提交：接收 6 文件内容，结果三态在 data.synthesis_status——rejected=机器校验失败（返回具体错误，修正内容后重提）；failed=环境失败（不应重试内容，先排查环境）；saved=落盘 SkillTemplates/synthesized/<capability_id>/ 并标 review_status=pending_review。MCP 顶层 status 仅 success/failed。该工具不受 allow_skill_synthesis 开关拦截（开关只门控 Stage 1 anchor 强制）；试制隔离由 pending_review+人审+promote 守卫纵深保证。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
            "capability_id": {"type": "string", "required": True, "description": "目标能力 ID"},
            "six_files": {"type": "object", "required": True, "description": "key=文件名（manifest.yaml 等 6 个），value=完整文件内容字符串"},
        },
        "returns": "data.synthesis_status=saved/rejected/failed、errors[]、package_dir、review 提示（agent 据 data.synthesis_status 决定重提内容还是排查环境）",
    },
    "demo_story_fetch": {
        "description": "Phase 14 demo-first:取下一个(或指定)施工 story 全包——story JSON、施工规范全文、材料路径清单。in_progress 可幂等重入续作。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "run 目录路径(含 demo_plan.json 与 stories/)"},
            "story_id": {"type": "string", "required": False, "description": "缺省取计划顺序下一个可发工单"},
        },
        "returns": "data.story / data.construction_manifest(全文);manifest 版本不符告警在 warnings[];status=ok/failed(failed 仅环境/数据异常,触发 MCP isError)",
    },
    "demo_story_submit": {
        "description": "Phase 14 demo-first:提交 story 完成证据。按 evidence_class 机器校验;失败回 in_progress 并返回具体错误(重试闭环);增量批附加 v0 冒烟 hash 守门。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "run 目录路径"},
            "story_id": {"type": "string", "required": True, "description": "工单 id"},
            "evidence": {"type": "object", "required": True, "description": "files_changed/test_report/smoke_report/screenshots/doc_paths/provisional_decisions/plugin_root"},
        },
        "returns": "data.story_status(verified|in_progress) / data.errors / data.attempts;校验拒绝是业务信号,status 仍为 ok(failed 仅环境/数据异常,触发 MCP isError)",
    },
}


# ============================================================
# Evidence Judge Backend: 后端证据裁决工具
# ============================================================

EVIDENCE_JUDGE_TOOLS = {
    "evidence_load_manifest": {
        "description": "读取指定 run_id 的 evidence manifest。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
        },
        "returns": "manifest 原始内容",
    },
    "evidence_load_screenshots": {
        "description": "读取指定 run_id 的 screenshots 证据列表。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
        },
        "returns": "截图文件路径列表",
    },
    "evidence_load_logs": {
        "description": "读取指定 run_id 的日志证据内容。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
        },
        "returns": "日志文件与文本内容列表",
    },
    "evidence_load_report": {
        "description": "读取指定 run_id 的报告证据内容。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
        },
        "returns": "报告文件与文本内容列表",
    },
    "evidence_judge_acceptance": {
        "description": "基于 manifest 覆盖度与摘要做 pass/fail/escalate 初步判定。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
            "criteria": {"type": "object", "required": True, "description": "判定准则，如 required_types 与 min_checks"},
        },
        "returns": "初步判定结果、置信度与开放问题",
    },
    "evidence_decide_escalation": {
        "description": "判断指定 run_id 是否需要升级人工确认。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
        },
        "returns": "needs_human、reason 与 escalation_note",
    },
    "evidence_export_summary": {
        "description": "导出指定 run_id 的结构化验收摘要。",
        "params": {
            "run_id": {"type": "string", "required": True, "description": "证据运行标识 run_id"},
        },
        "returns": "run_id、test_type、judgment 与 open_questions",
    },
    "evidence_list_runs": {
        "description": "列出证据根目录下的全部 run_id。",
        "params": {
            "date_filter": {"type": "string", "required": False, "description": "按 YYYY-MM-DD 过滤指定日期的 run_id"},
        },
        "returns": "run_id 列表",
    },
    "evidence_compare_runs": {
        "description": "比较两个 Phase 11 run 的核心产物差异，覆盖 Constraint、Realization、Fragment、Build IR、Naming、Provisional。",
        "params": {
            "run_a_id": {"type": "string", "required": True, "description": "基准 run_id"},
            "run_b_id": {"type": "string", "required": True, "description": "对比 run_id"},
            "output_path": {"type": "string", "required": False, "description": "可选：将 run_comparison.json 落盘到指定路径"},
        },
        "returns": "run_comparison 结构化比较结果",
    },
    "evidence_create_batch": {
        "description": "从指定 promotable run 创建 batch，复制 promoted_artifacts 并生成 manifest / promotion_report。",
        "params": {
            "source_run_id": {"type": "string", "required": True, "description": "来源 run_id"},
            "promoted_by": {"type": "string", "required": False, "description": "promote 执行者标识"},
            "notes": {"type": "string", "required": False, "description": "promote 备注"},
            "make_active": {"type": "boolean", "required": False, "description": "是否将该 batch 设为 active，默认 true"},
        },
        "returns": "batch_id、manifest 路径、promotion_report 路径与 promoted_artifacts 目录",
    },
    "evidence_promote_run": {
        "description": "promote run 到 batch，并更新治理层 baseline 指针。",
        "params": {
            "source_run_id": {"type": "string", "required": True, "description": "来源 run_id"},
            "promoted_by": {"type": "string", "required": False, "description": "promote 执行者标识"},
            "notes": {"type": "string", "required": False, "description": "promote 备注"},
            "make_active": {"type": "boolean", "required": False, "description": "是否将该 batch 设为 active，默认 true"},
            "update_base_project": {"type": "boolean", "required": False, "description": "是否更新治理层 baseline 指针，默认 true"},
        },
        "returns": "batch_id、manifest 路径、promotion_report 路径与 baseline 指针更新结果",
    },
}


# ============================================================
# 工具总表
# ============================================================

ALL_TOOLS = {}
ALL_TOOLS.update(LAYER1_QUERY_TOOLS)
ALL_TOOLS.update(LAYER1_WRITE_TOOLS)
ALL_TOOLS.update(LAYER1_SERVICE_TOOLS)
ALL_TOOLS.update(LAYER2_ASSET_TOOLS)
ALL_TOOLS.update(LAYER3_TOOLS)
ALL_TOOLS.update(COMPILER_FRONTEND_TOOLS)
ALL_TOOLS.update(EVIDENCE_JUDGE_TOOLS)

TOOL_COUNT = len(ALL_TOOLS)
# 当前 flat alias layout：
# 7(query) + 6(write) + 5(service) + 9(asset) + 1(fallback) + 18(compiler_frontend) + 11(evidence_backend) = 57


def to_json_schema(tool_def: dict) -> dict:
    """将内部参数定义转换为 MCP Tool.inputSchema 所需的 JSON Schema。"""
    type_map = {
        "string": "string",
        "integer": "integer",
        "boolean": "boolean",
        "array": "array",
        "object": "object",
    }

    properties = {}
    required = []

    for param_name, spec in tool_def.get("params", {}).items():
        prop_schema = {}
        param_type = spec.get("type")
        if param_type in type_map:
            prop_schema["type"] = type_map[param_type]

        description = spec.get("description")
        if description:
            prop_schema["description"] = description

        properties[param_name] = prop_schema

        if spec.get("required", False):
            required.append(param_name)

    schema = {
        "type": "object",
        "properties": properties,
    }
    if required:
        schema["required"] = required
    return schema
