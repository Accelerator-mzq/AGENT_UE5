# Phase 8 DD-1：Schema 完整字段定义 + Compiler 五段接口规约

## 文档目的

本文档是 Phase 8 的第一份详细设计文档，为 M1（Compiler Contracts Reset）提供：
1. 6 个新增 Schema 的完整字段定义（字段名、类型、required/optional、枚举值、示例）
2. Compiler 五段主链（Intake → Planner → Skill Runtime → Cross-Review → Lowering）的接口规约

所有 Schema 统一使用 `http://json-schema.org/draft-07/schema#`，与现有 `reviewed_handoff.schema.json` 和 `run_plan.schema.json` 保持一致。

---

## 一、Schema 总览与依赖关系

```
gdd_projection.schema.json          ← Intake 输出
    ↓
planner_output.schema.json           ← Planner 输出
    ↓
skill_fragment.schema.json           ← Skill Runtime 输出（每个 Skill Instance 一份）
    ↓
cross_review_report.schema.json      ← Cross-Spec Review 输出
    ↓
build_ir.schema.json                 ← Lowering 输出
    ↓
reviewed_handoff_v2.schema.json      ← 最终边界交接物（包含以上所有摘要）
```

---

## 二、Schema 1：gdd_projection.schema.json

### 用途
Intake 阶段从原始 GDD markdown 中提取的结构化设计投影。将 GDD 的自然语言转化为下游模块可消费的 JSON。

### 完整字段定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GDD Projection",
  "description": "Design Intake 从 GDD 中提取的结构化设计投影",
  "type": "object",
  "required": [
    "projection_version",
    "projection_id",
    "source_gdd",
    "game_identity",
    "phase_scope",
    "design_domains"
  ],
  "properties": {
    "projection_version": {
      "type": "string",
      "description": "投影 schema 版本",
      "const": "1.0"
    },
    "projection_id": {
      "type": "string",
      "description": "投影唯一标识",
      "pattern": "^proj\\.[a-z0-9_]+\\.[a-z0-9]+$",
      "example": "proj.monopoly_phase1.001"
    },
    "source_gdd": {
      "type": "object",
      "description": "源 GDD 元信息",
      "required": ["file_path", "part_a_scope", "part_b_scope"],
      "properties": {
        "file_path": {
          "type": "string",
          "description": "GDD 文件相对路径",
          "example": "ProjectInputs/GDD/GDD_MonopolyGame.md"
        },
        "part_a_scope": {
          "type": "string",
          "description": "Part A（设计真源）覆盖内容摘要",
          "example": "游戏规则、棋盘结构、格子数据、回合规则、经济规则、监狱规则、UI 需求"
        },
        "part_b_scope": {
          "type": "string",
          "description": "Part B（实现约束）覆盖内容摘要",
          "example": "C++ 类设计、UE5 项目结构、编辑器操作步骤、Phase 2 网络演进"
        }
      }
    },
    "game_identity": {
      "type": "object",
      "description": "游戏身份识别",
      "required": ["game_type", "subgenre", "presentation_model", "player_count_range", "win_condition"],
      "properties": {
        "game_type": {
          "type": "string",
          "description": "一级游戏类型",
          "enum": ["board_strategy", "jrpg", "action", "puzzle", "simulation"],
          "example": "board_strategy"
        },
        "subgenre": {
          "type": "string",
          "description": "二级子类型",
          "example": "monopoly_like"
        },
        "presentation_model": {
          "type": "string",
          "description": "呈现模式",
          "enum": ["top_down_2d", "top_down_3d", "side_scroll", "third_person", "first_person", "isometric"],
          "example": "top_down_3d"
        },
        "player_count_range": {
          "type": "array",
          "description": "玩家人数范围 [min, max]",
          "items": {"type": "integer", "minimum": 1},
          "minItems": 2,
          "maxItems": 2,
          "example": [2, 4]
        },
        "win_condition": {
          "type": "string",
          "description": "主要胜利条件",
          "example": "last_non_bankrupt_player"
        },
        "target_match_length_minutes": {
          "type": "array",
          "description": "目标单局时长 [min, max] 分钟",
          "items": {"type": "integer"},
          "minItems": 2,
          "maxItems": 2,
          "example": [20, 40]
        }
      }
    },
    "phase_scope": {
      "type": "object",
      "description": "阶段范围定义",
      "required": ["current_phase", "in_scope", "out_of_scope"],
      "properties": {
        "current_phase": {
          "type": "string",
          "description": "当前阶段标识",
          "example": "phase1_local_multiplayer"
        },
        "in_scope": {
          "type": "array",
          "description": "本轮范围内的功能列表",
          "items": {"type": "string"},
          "example": ["local_turn_play", "ring_board_28_tiles", "dice_movement", "property_buy_rent", "jail_logic", "minimal_hud_and_popups"]
        },
        "out_of_scope": {
          "type": "array",
          "description": "本轮明确排除的功能列表",
          "items": {"type": "string"},
          "example": ["online_multiplayer", "session_management", "chance_card_events", "community_card_events", "property_auction", "house_hotel_building"]
        },
        "future_phases": {
          "type": "array",
          "description": "后续阶段演进列表",
          "items": {
            "type": "object",
            "properties": {
              "phase_id": {"type": "string"},
              "summary": {"type": "string"}
            }
          },
          "example": [{"phase_id": "phase2_online_multiplayer", "summary": "Server-Authoritative 在线多人"}]
        }
      }
    },
    "design_domains": {
      "type": "object",
      "description": "从 GDD Part A 提取的各设计域结构化数据",
      "properties": {
        "board_layout": {
          "type": "object",
          "description": "棋盘/地图布局",
          "properties": {
            "shape": {"type": "string", "enum": ["square_ring", "linear", "grid", "hex_grid", "custom"], "example": "square_ring"},
            "tile_count": {"type": "integer", "minimum": 1, "example": 28},
            "tiles_per_side": {"type": "integer", "example": 7},
            "movement_direction": {"type": "string", "enum": ["clockwise", "counterclockwise", "bidirectional"], "example": "clockwise"},
            "corner_indices": {
              "type": "object",
              "description": "特殊角格索引",
              "properties": {
                "start": {"type": "integer", "example": 0},
                "jail_visit": {"type": "integer", "example": 7},
                "free_parking": {"type": "integer", "example": 14},
                "go_to_jail": {"type": "integer", "example": 21}
              }
            }
          }
        },
        "tile_catalog": {
          "type": "array",
          "description": "完整格子目录",
          "items": {
            "type": "object",
            "required": ["index", "type", "name"],
            "properties": {
              "index": {"type": "integer", "minimum": 0},
              "type": {
                "type": "string",
                "enum": ["START", "PROPERTY", "TAX", "CHANCE", "COMMUNITY", "JAIL_VISIT", "FREE_PARKING", "GO_TO_JAIL"]
              },
              "name": {"type": "string"},
              "color_group": {"type": ["string", "null"]},
              "price": {"type": ["integer", "null"]},
              "base_rent": {"type": ["integer", "null"]}
            }
          }
        },
        "color_groups": {
          "type": "object",
          "description": "颜色组定义",
          "additionalProperties": {
            "type": "object",
            "properties": {
              "tile_indices": {"type": "array", "items": {"type": "integer"}},
              "full_set_multiplier": {"type": "number", "example": 2}
            }
          }
        },
        "turn_loop": {
          "type": "object",
          "description": "回合循环规则",
          "properties": {
            "dice_count": {"type": "integer", "example": 2},
            "dice_sides": {"type": "integer", "example": 6},
            "start_bonus": {"type": "integer", "description": "过起点奖励金额", "example": 200},
            "doubles_extra_turn": {"type": "boolean", "example": true},
            "triple_doubles_jail": {"type": "boolean", "example": true}
          }
        },
        "property_rules": {
          "type": "object",
          "description": "地产规则",
          "properties": {
            "unowned_landing": {"type": "string", "description": "踩到无主地产的行为", "example": "offer_purchase"},
            "owned_by_self": {"type": "string", "example": "no_action"},
            "owned_by_other": {"type": "string", "example": "pay_rent"},
            "color_group_bonus": {"type": "string", "example": "rent_multiplier_x2"},
            "bankruptcy_release": {"type": "string", "description": "破产后地产处理", "example": "release_to_unowned"}
          }
        },
        "jail_rules": {
          "type": "object",
          "description": "监狱规则",
          "properties": {
            "entry_conditions": {
              "type": "array",
              "items": {"type": "string"},
              "example": ["land_on_go_to_jail", "triple_doubles"]
            },
            "bail_cost": {"type": "integer", "example": 50},
            "doubles_release": {"type": "boolean", "example": true},
            "max_jail_turns": {"type": "integer", "description": "最大关押回合数，超过则强制支付", "example": 3}
          }
        },
        "bankruptcy_rules": {
          "type": "object",
          "description": "破产规则",
          "properties": {
            "trigger": {"type": "string", "example": "cannot_pay_obligation"},
            "consequence": {"type": "string", "example": "eliminate_player"},
            "asset_handling": {"type": "string", "example": "release_all_properties_to_unowned"},
            "game_end_condition": {"type": "string", "example": "one_player_remaining"}
          }
        },
        "ui_requirements": {
          "type": "object",
          "description": "UI 需求",
          "properties": {
            "hud_elements": {
              "type": "array",
              "items": {"type": "string"},
              "example": ["current_player_name", "player_money", "turn_number", "property_count"]
            },
            "popup_types": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "popup_id": {"type": "string"},
                  "trigger": {"type": "string"},
                  "buttons": {"type": "array", "items": {"type": "string"}}
                }
              },
              "example": [
                {"popup_id": "dice_roll", "trigger": "turn_start", "buttons": ["roll_dice"]},
                {"popup_id": "buy_property", "trigger": "land_on_unowned", "buttons": ["buy", "pass"]},
                {"popup_id": "jail_decision", "trigger": "in_jail_turn_start", "buttons": ["pay_bail", "try_doubles"]}
              ]
            }
          }
        }
      }
    },
    "implementation_hints": {
      "type": "object",
      "description": "从 GDD Part B 提取的实现约束（不驱动编译主链，仅作为 Lowering 参考）",
      "properties": {
        "class_naming_convention": {
          "type": "string",
          "description": "C++ 类命名前缀",
          "example": "M"
        },
        "core_classes": {
          "type": "array",
          "description": "GDD 建议的核心 C++ 类列表",
          "items": {"type": "string"},
          "example": ["MGameMode", "MGameState", "MPlayerState", "MPlayerController", "MBoardManager", "MTile", "MPlayerPawn", "MDice"]
        },
        "editor_steps_summary": {
          "type": "string",
          "description": "编辑器操作步骤摘要"
        },
        "phase2_network_notes": {
          "type": "string",
          "description": "Phase 2 网络演进方向摘要（仅记录，不进本轮执行）",
          "example": "Server-Authoritative, GameMode server-only, GameState/PlayerState replicated"
        }
      }
    },
    "ambiguities": {
      "type": "array",
      "description": "GDD 中的歧义或模糊点",
      "items": {
        "type": "object",
        "properties": {
          "topic": {"type": "string"},
          "description": {"type": "string"},
          "default_assumption": {"type": "string"}
        }
      }
    },
    "risk_notes": {
      "type": "array",
      "description": "风险与注意事项",
      "items": {"type": "string"}
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "generator": {"type": "string"}
      }
    }
  }
}
```

---

## 三、Schema 2：planner_output.schema.json

### 用途
Planner 读取 GDD Projection 后输出的任务编排意图：选了哪些 Skill、目标哪些 Dynamic Spec families、能力缺口、审查重点。

### 完整字段定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Planner Output",
  "description": "Planner / Routing Agent 的结构化输出",
  "type": "object",
  "required": [
    "planner_meta",
    "project_intent",
    "routing_decision",
    "selected_skill_instances",
    "dynamic_spec_targets",
    "execution_strategy"
  ],
  "properties": {
    "planner_meta": {
      "type": "object",
      "description": "Planner 元数据",
      "required": ["planner_version", "mode", "target_phase"],
      "properties": {
        "planner_version": {"type": "string", "const": "v1"},
        "timestamp": {"type": "string", "format": "date-time"},
        "source_projection_id": {"type": "string", "description": "输入的 gdd_projection 的 projection_id"},
        "mode": {
          "type": "string",
          "enum": ["greenfield", "brownfield", "playable_runtime"],
          "example": "greenfield"
        },
        "target_phase": {"type": "string", "example": "phase1_local_multiplayer"},
        "target_build_goal": {
          "type": "string",
          "enum": ["playable_template", "vertical_slice", "production"],
          "example": "playable_template"
        }
      }
    },
    "project_intent": {
      "type": "object",
      "description": "Planner 对本轮任务目标的理解",
      "required": ["game_type", "subgenre", "phase_scope"],
      "properties": {
        "game_type": {"type": "string", "example": "board_strategy"},
        "subgenre": {"type": "string", "example": "monopoly_like"},
        "camera_model": {"type": "string", "example": "top_down_3d"},
        "player_count_range": {"type": "string", "example": "2-4"},
        "primary_win_condition": {"type": "string", "example": "last_non_bankrupt_player"},
        "phase_scope": {"type": "string", "example": "phase1_local_multiplayer"},
        "out_of_scope": {
          "type": "array",
          "items": {"type": "string"},
          "example": ["phase2_network_replication", "chance_card_effects"]
        }
      }
    },
    "routing_decision": {
      "type": "object",
      "description": "路由决策说明",
      "required": ["identified_domains", "required_family_targets"],
      "properties": {
        "identified_domains": {
          "type": "array",
          "description": "识别出的能力域",
          "items": {"type": "string"},
          "example": ["board_topology", "tile_system", "turn_flow", "player_economy", "jail_system", "ui_flow", "runtime_validation"]
        },
        "routing_reasoning_summary": {
          "type": "string",
          "description": "路由决策简要说明"
        },
        "required_family_targets": {
          "type": "array",
          "description": "本轮必须生成的 family 列表",
          "items": {"type": "string"}
        },
        "rejected_branches": {
          "type": "array",
          "description": "明确拒绝的分支及理由",
          "items": {
            "type": "object",
            "properties": {
              "branch": {"type": "string"},
              "reason": {"type": "string"}
            }
          }
        }
      }
    },
    "selected_skill_instances": {
      "type": "array",
      "description": "本轮需要实例化的 Skill 列表",
      "items": {
        "type": "object",
        "required": ["skill_instance_id", "template_id", "role", "emits_families"],
        "properties": {
          "skill_instance_id": {
            "type": "string",
            "description": "运行时实例 ID",
            "pattern": "^skill-[a-z0-9_]+$",
            "example": "skill-board"
          },
          "template_id": {
            "type": "string",
            "description": "引用的 Template Pack ID",
            "example": "monopoly.board_topology.phase1"
          },
          "role": {
            "type": "string",
            "description": "本实例在本轮中的角色描述",
            "example": "define_ring_board_layout"
          },
          "priority": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low"],
            "example": "high"
          },
          "depends_on": {
            "type": "array",
            "description": "依赖的 Skill Instance ID",
            "items": {"type": "string"},
            "example": []
          },
          "reads_context": {
            "type": "array",
            "description": "需要从 GDD Projection 中读取的设计域",
            "items": {"type": "string"},
            "example": ["board_layout", "tile_catalog"]
          },
          "emits_families": {
            "type": "array",
            "description": "预期产出的 Dynamic Spec Family 列表",
            "items": {"type": "string"},
            "example": ["board_topology_spec"]
          }
        }
      }
    },
    "dynamic_spec_targets": {
      "type": "array",
      "description": "本轮预期生成的全部 Dynamic Spec Family",
      "items": {"type": "string"},
      "example": ["board_topology_spec", "tile_system_spec", "turn_flow_spec", "jail_system_spec", "player_economy_spec", "property_ownership_spec", "ui_flow_spec", "runtime_entity_spec", "runtime_validation_spec"]
    },
    "execution_strategy": {
      "type": "object",
      "description": "总体执行策略",
      "required": ["build_mode", "target_output_kind"],
      "properties": {
        "build_mode": {
          "type": "string",
          "enum": ["greenfield", "brownfield"],
          "example": "greenfield"
        },
        "target_output_kind": {
          "type": "string",
          "example": "playable_phase1_template"
        },
        "manual_editor_dependency": {
          "type": "string",
          "enum": ["none", "low", "medium", "high"],
          "description": "对人工编辑器操作的依赖程度",
          "example": "medium"
        },
        "expected_review_gate": {
          "type": "string",
          "enum": ["required", "optional", "skip"],
          "example": "required"
        },
        "expected_lowering_depth": {
          "type": "string",
          "example": "static_specs_plus_build_ir"
        }
      }
    },
    "capability_gaps": {
      "type": "array",
      "description": "已知能力缺口",
      "items": {
        "type": "object",
        "required": ["gap_id", "description"],
        "properties": {
          "gap_id": {"type": "string"},
          "description": {"type": "string"},
          "severity": {
            "type": "string",
            "enum": ["blocker", "degraded", "cosmetic"],
            "example": "degraded"
          },
          "workaround": {"type": "string"}
        }
      }
    },
    "review_focuses": {
      "type": "array",
      "description": "告诉 Cross-Spec Review 的审查重点",
      "items": {"type": "string"},
      "example": ["board_index_closure", "go_and_jail_rule_consistency", "rent_and_bankruptcy_consistency", "decision_ui_completeness"]
    },
    "open_questions": {
      "type": "array",
      "description": "开放问题",
      "items": {
        "type": "object",
        "properties": {
          "question": {"type": "string"},
          "default_assumption": {"type": "string"}
        }
      }
    },
    "confidence": {
      "type": "object",
      "description": "Planner 自评",
      "properties": {
        "gdd_coverage": {"type": "number", "minimum": 0, "maximum": 1, "description": "GDD 覆盖率"},
        "phase_alignment": {"type": "number", "minimum": 0, "maximum": 1, "description": "Phase 对齐度"},
        "skill_selection_confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "known_unknowns": {"type": "number", "minimum": 0, "maximum": 1, "description": "已知未知项比例"}
      }
    }
  }
}
```

---

## 四、Schema 3：skill_fragment.schema.json

### 用途
每个 Skill Instance 运行后输出的结构化产物。包含 Dynamic Spec Fragment 和元信息。

### 完整字段定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Skill Fragment",
  "description": "单个 Skill Instance 的运行时输出产物",
  "type": "object",
  "required": [
    "skill_instance_id",
    "template_id",
    "phase_scope",
    "emitted_families",
    "spec_fragments",
    "status"
  ],
  "properties": {
    "skill_instance_id": {
      "type": "string",
      "description": "对应 Planner 选出的 Skill Instance ID",
      "example": "skill-board"
    },
    "template_id": {
      "type": "string",
      "description": "使用的 Template Pack ID",
      "example": "monopoly.board_topology.phase1"
    },
    "phase_scope": {
      "type": "string",
      "description": "执行时的 Phase 范围",
      "example": "phase1_local_multiplayer"
    },
    "status": {
      "type": "string",
      "enum": ["completed", "partial", "failed"],
      "description": "completed=全部 family 生成完成, partial=部分完成, failed=失败"
    },
    "emitted_families": {
      "type": "array",
      "description": "实际产出的 family 名称列表",
      "items": {"type": "string"},
      "example": ["board_topology_spec"]
    },
    "spec_fragments": {
      "type": "object",
      "description": "按 family 名组织的 Dynamic Spec Fragment。每个 key 是 family 名，value 是该 family 的结构化内容",
      "additionalProperties": {
        "type": "object",
        "description": "单个 family 的具体内容，结构由对应 Skill Template 的 output_schema.json 定义"
      },
      "example": {
        "board_topology_spec": {
          "board_shape": "square_ring",
          "tile_count": 28,
          "movement_direction": "clockwise",
          "corner_tiles": {
            "start": 0,
            "jail_visit": 7,
            "free_parking": 14,
            "go_to_jail": 21
          }
        }
      }
    },
    "assumptions": {
      "type": "array",
      "description": "Skill 生成过程中做出的假设",
      "items": {
        "type": "object",
        "properties": {
          "assumption": {"type": "string"},
          "basis": {"type": "string", "description": "假设来源（GDD 节号/默认值/推断）"}
        }
      }
    },
    "open_questions": {
      "type": "array",
      "description": "未解决的开放问题",
      "items": {"type": "string"}
    },
    "review_hints": {
      "type": "array",
      "description": "给 Cross-Spec Review 的审查提示",
      "items": {"type": "string"},
      "example": ["确认 28 格索引 0..27 无缺口", "确认四角格索引与回合流转逻辑一致"]
    },
    "capability_gaps": {
      "type": "array",
      "description": "发现的能力缺口",
      "items": {
        "type": "object",
        "properties": {
          "gap_id": {"type": "string"},
          "description": {"type": "string"},
          "severity": {"type": "string", "enum": ["blocker", "degraded", "cosmetic"]}
        }
      }
    },
    "confidence": {
      "type": "object",
      "description": "Skill 对本次输出的自评",
      "properties": {
        "coverage": {"type": "number", "minimum": 0, "maximum": 1, "description": "对目标 family 的覆盖率"},
        "consistency": {"type": "number", "minimum": 0, "maximum": 1, "description": "内部一致性评估"}
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "generator": {"type": "string"},
        "template_version": {"type": "string"}
      }
    }
  }
}
```

---

## 五、Schema 4：cross_review_report.schema.json

### 用途
Cross-Spec Review 对所有 Skill Fragment 进行统一审查后的报告。输出 reviewed dynamic spec tree 和审查结论。

### 完整字段定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Cross-Spec Review Report",
  "description": "Cross-Spec Review 阶段对所有 Skill Fragment 的统一审查报告",
  "type": "object",
  "required": [
    "review_id",
    "review_version",
    "input_fragment_ids",
    "review_status",
    "reviewed_dynamic_spec_tree",
    "review_checks"
  ],
  "properties": {
    "review_id": {
      "type": "string",
      "pattern": "^review\\.[a-z0-9_]+\\.[a-z0-9]+$",
      "example": "review.monopoly_phase1.001"
    },
    "review_version": {
      "type": "string",
      "const": "v1"
    },
    "input_fragment_ids": {
      "type": "array",
      "description": "输入的 Skill Fragment ID 列表",
      "items": {"type": "string"},
      "example": ["skill-board", "skill-turn", "skill-tile-event", "skill-economy", "skill-jail", "skill-ui"]
    },
    "review_status": {
      "type": "string",
      "enum": ["approved", "approved_with_warnings", "blocked"],
      "description": "approved=全部通过, approved_with_warnings=通过但有警告, blocked=存在阻塞问题"
    },
    "review_checks": {
      "type": "array",
      "description": "逐项审查结果",
      "items": {
        "type": "object",
        "required": ["check_id", "check_name", "result"],
        "properties": {
          "check_id": {"type": "string", "example": "chk-board-closure"},
          "check_name": {
            "type": "string",
            "description": "审查项名称",
            "example": "28 格棋盘索引闭合"
          },
          "result": {
            "type": "string",
            "enum": ["pass", "warning", "fail"],
            "description": "pass=通过, warning=有潜在问题但不阻塞, fail=审查失败"
          },
          "details": {
            "type": "string",
            "description": "审查细节说明"
          },
          "affected_families": {
            "type": "array",
            "items": {"type": "string"},
            "description": "涉及的 family"
          }
        }
      },
      "example": [
        {"check_id": "chk-board-closure", "check_name": "28 格棋盘索引闭合", "result": "pass", "affected_families": ["board_topology_spec", "tile_system_spec"]},
        {"check_id": "chk-jail-doubles", "check_name": "双数规则与监狱规则一致性", "result": "pass", "affected_families": ["turn_flow_spec", "jail_system_spec"]},
        {"check_id": "chk-ui-coverage", "check_name": "UI 决策分支覆盖完整性", "result": "warning", "details": "Chance/Community 格 Phase 1 无弹窗，确认为预期行为", "affected_families": ["ui_flow_spec", "tile_system_spec"]}
      ]
    },
    "issues_found": {
      "type": "array",
      "description": "发现的问题",
      "items": {
        "type": "object",
        "required": ["issue_id", "severity", "description"],
        "properties": {
          "issue_id": {"type": "string"},
          "severity": {"type": "string", "enum": ["blocker", "warning", "info"]},
          "description": {"type": "string"},
          "resolution": {"type": "string", "description": "如何解决"},
          "resolved": {"type": "boolean"}
        }
      }
    },
    "phase_scope_check": {
      "type": "object",
      "description": "Phase 范围检查",
      "properties": {
        "in_scope_confirmed": {"type": "boolean"},
        "out_of_scope_violations": {
          "type": "array",
          "items": {"type": "string"},
          "description": "如果有越界到 Phase 2 的内容，列出"
        }
      }
    },
    "reviewed_dynamic_spec_tree": {
      "type": "object",
      "description": "审查通过后的统一 Dynamic Spec Tree，按 family 名组织",
      "additionalProperties": {
        "type": "object",
        "description": "每个 family 审查后的最终版本"
      }
    },
    "capability_gap_list": {
      "type": "array",
      "description": "汇总所有 Skill 报告的能力缺口",
      "items": {
        "type": "object",
        "properties": {
          "gap_id": {"type": "string"},
          "source_skill": {"type": "string"},
          "description": {"type": "string"},
          "severity": {"type": "string", "enum": ["blocker", "degraded", "cosmetic"]}
        }
      }
    },
    "lowering_ready": {
      "type": "boolean",
      "description": "审查通过且可以进入 Lowering 阶段"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "generator": {"type": "string"}
      }
    }
  }
}
```

---

## 六、Schema 5：build_ir.schema.json

### 用途
Lowering 阶段输出的构建中间表示。表达构建意图（不是引擎调用细节），供执行层消费。

### 完整字段定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Build IR",
  "description": "Lowering Pipeline 输出的构建中间表示",
  "type": "object",
  "required": [
    "ir_version",
    "ir_id",
    "source_review_id",
    "phase_scope",
    "build_steps",
    "lowering_report"
  ],
  "properties": {
    "ir_version": {
      "type": "string",
      "const": "1.0"
    },
    "ir_id": {
      "type": "string",
      "pattern": "^ir\\.[a-z0-9_]+\\.[a-z0-9]+$",
      "example": "ir.monopoly_phase1.001"
    },
    "source_review_id": {
      "type": "string",
      "description": "来源的 Cross-Review Report ID"
    },
    "phase_scope": {
      "type": "string",
      "example": "phase1_local_multiplayer"
    },
    "build_steps": {
      "type": "array",
      "description": "构建步骤序列，每步表达一个构建意图",
      "items": {
        "type": "object",
        "required": ["step_id", "ir_action", "source_families", "params"],
        "properties": {
          "step_id": {
            "type": "string",
            "description": "步骤唯一 ID",
            "example": "ir-001"
          },
          "ir_action": {
            "type": "string",
            "description": "构建意图动作",
            "enum": [
              "create_board_ring_layout",
              "create_tile_actors",
              "assign_tile_metadata",
              "create_player_tokens",
              "create_game_mode_shell",
              "bind_turn_state_machine",
              "bind_dice_roll_logic",
              "bind_tile_event_dispatch",
              "bind_property_economy_logic",
              "bind_jail_logic",
              "bind_bankruptcy_logic",
              "create_phase1_ui_widgets",
              "bind_ui_to_game_state",
              "attach_validation_hooks"
            ]
          },
          "source_families": {
            "type": "array",
            "description": "此步骤依据的 Dynamic Spec Family",
            "items": {"type": "string"},
            "example": ["board_topology_spec"]
          },
          "depends_on": {
            "type": "array",
            "description": "依赖的前置步骤 ID",
            "items": {"type": "string"}
          },
          "params": {
            "type": "object",
            "description": "构建参数（由 Lowering 从 Dynamic Spec 翻译而来）。不同 ir_action 有不同的参数结构",
            "additionalProperties": true
          },
          "static_base_bindings": {
            "type": "array",
            "description": "绑定的 Static Base 能力",
            "items": {"type": "string"},
            "example": ["board_manager_spec", "tile_spawn_layout_spec"]
          },
          "execution_hints": {
            "type": "object",
            "description": "给执行层的提示（非强制）",
            "properties": {
              "tool_preference": {
                "type": "string",
                "enum": ["mcp_bridge", "cpp_code", "python_editor_scripting", "manual"],
                "description": "建议使用的执行通道"
              },
              "estimated_complexity": {
                "type": "string",
                "enum": ["trivial", "simple", "moderate", "complex"]
              }
            }
          }
        }
      }
    },
    "validation_ir": {
      "type": "array",
      "description": "验证中间表示，定义执行后必须检查的验证点",
      "items": {
        "type": "object",
        "required": ["validation_id", "check_type", "description"],
        "properties": {
          "validation_id": {
            "type": "string",
            "example": "val-001"
          },
          "after_step": {
            "type": "string",
            "description": "在哪个 build_step 之后执行验证"
          },
          "check_type": {
            "type": "string",
            "enum": ["actor_exists", "actor_count", "property_value", "state_machine_state", "ui_widget_exists", "gameplay_rule", "data_consistency"],
            "description": "验证类型"
          },
          "description": {
            "type": "string",
            "example": "确认 28 个 Tile Actor 已生成"
          },
          "expected": {
            "type": ["string", "number", "boolean", "object"],
            "description": "期望值"
          },
          "tolerance": {
            "type": "number",
            "description": "数值容差（如适用）"
          }
        }
      }
    },
    "lowering_report": {
      "type": "object",
      "description": "Lowering 过程报告",
      "required": ["families_received", "families_bound"],
      "properties": {
        "families_received": {
          "type": "array",
          "items": {"type": "string"},
          "description": "接收到的 family 列表"
        },
        "families_bound": {
          "type": "array",
          "items": {"type": "string"},
          "description": "成功绑定的 family 列表"
        },
        "families_partially_bound": {
          "type": "array",
          "items": {"type": "string"},
          "description": "部分绑定的 family 列表"
        },
        "unbound_requirements": {
          "type": "array",
          "description": "无法绑定的需求",
          "items": {
            "type": "object",
            "properties": {
              "requirement": {"type": "string"},
              "reason": {"type": "string"},
              "fallback": {"type": "string"}
            }
          }
        },
        "capability_gaps": {
          "type": "array",
          "items": {
            "type": "object",
            "properties": {
              "gap_id": {"type": "string"},
              "description": {"type": "string"}
            }
          }
        }
      }
    },
    "recovery_hints": {
      "type": "array",
      "description": "执行失败时的恢复提示",
      "items": {
        "type": "object",
        "properties": {
          "step_id": {"type": "string"},
          "recovery_strategy": {
            "type": "string",
            "enum": ["retry", "skip", "rollback", "manual"],
            "description": "建议的恢复策略"
          },
          "notes": {"type": "string"}
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "generator": {"type": "string"}
      }
    }
  }
}
```

---

## 七、Schema 6：reviewed_handoff_v2.schema.json

### 用途
编译面→执行面的唯一正式边界。v2 相比 v1 的核心升级：不再以 `scene_spec.actors` 为中心，改为容纳完整的 Skill 编译结果。

### 与 v1 的兼容策略
- v2 新增 `handoff_version: "2.0"` 字段
- v1 的 `dynamic_spec_tree.scene_spec.actors` 仍可保留为兼容字段（optional），但不再是 required
- 执行层检测 `handoff_version` 决定走新链路还是旧链路

### 完整字段定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Reviewed Handoff v2",
  "description": "Skill-First Compiler 编译结果向 Execution Orchestrator 的正式交接物（v2）",
  "type": "object",
  "required": [
    "handoff_meta",
    "project_context",
    "planner_summary",
    "reviewed_dynamic_spec_tree",
    "build_ir",
    "approval"
  ],
  "properties": {
    "handoff_meta": {
      "type": "object",
      "description": "Handoff 元数据",
      "required": ["handoff_version", "handoff_id", "handoff_mode", "target_phase", "build_goal"],
      "properties": {
        "handoff_version": {"type": "string", "const": "2.0"},
        "handoff_id": {
          "type": "string",
          "pattern": "^handoff\\.[a-z0-9_]+\\.[a-z0-9_]+\\.[a-z0-9]+$",
          "example": "handoff.monopoly.phase1.001"
        },
        "handoff_mode": {
          "type": "string",
          "enum": ["greenfield_bootstrap", "brownfield_expansion"],
          "example": "greenfield_bootstrap"
        },
        "schema_version": {"type": "string", "const": "2.0"},
        "created_at": {"type": "string", "format": "date-time"},
        "target_phase": {"type": "string", "example": "phase1_local_multiplayer"},
        "build_goal": {
          "type": "string",
          "enum": ["playable_template", "vertical_slice", "production"],
          "example": "playable_template"
        }
      }
    },
    "project_context": {
      "type": "object",
      "description": "执行层需要的最小项目上下文",
      "required": ["project_name", "game_type"],
      "properties": {
        "project_name": {"type": "string", "example": "MonopolyGame"},
        "game_type": {"type": "string", "example": "board_strategy"},
        "subgenre": {"type": "string", "example": "monopoly_like"},
        "target_phase": {"type": "string", "example": "phase1_local_multiplayer"},
        "current_iteration": {"type": "string", "example": "phase8_reset_slice_01"}
      }
    },
    "planner_summary": {
      "type": "object",
      "description": "Planner 输出的最小摘要（不是全量）",
      "required": ["identified_domains", "phase_scope"],
      "properties": {
        "identified_domains": {"type": "array", "items": {"type": "string"}},
        "selected_families": {"type": "array", "items": {"type": "string"}},
        "phase_scope": {"type": "string"},
        "out_of_scope": {"type": "array", "items": {"type": "string"}},
        "routing_summary": {"type": "string"}
      }
    },
    "selected_skill_instances": {
      "type": "array",
      "description": "本轮参与编译的 Skill Instances（用于审计追溯）",
      "items": {
        "type": "object",
        "required": ["skill_instance_id", "template_id", "status"],
        "properties": {
          "skill_instance_id": {"type": "string"},
          "template_id": {"type": "string"},
          "role": {"type": "string"},
          "status": {
            "type": "string",
            "enum": ["completed", "partial", "failed"]
          },
          "emitted_families": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "reviewed_dynamic_spec_tree": {
      "type": "object",
      "description": "经过 Cross-Spec Review 审查的统一 Dynamic Spec Tree。按 family 名组织，每个 family 为其审查后最终版本",
      "additionalProperties": {
        "type": "object"
      }
    },
    "cross_review_summary": {
      "type": "object",
      "description": "Cross-Spec Review 摘要",
      "required": ["status"],
      "properties": {
        "status": {
          "type": "string",
          "enum": ["approved", "approved_with_warnings", "blocked"]
        },
        "issues_found": {"type": "integer", "description": "发现的问题数"},
        "issues_resolved": {"type": "integer", "description": "已解决的问题数"},
        "remaining_warnings": {"type": "array", "items": {"type": "string"}},
        "review_focus_coverage": {
          "type": "object",
          "description": "审查重点覆盖情况",
          "additionalProperties": {"type": "string"}
        }
      }
    },
    "lowering_summary": {
      "type": "object",
      "description": "Lowering 过程摘要",
      "properties": {
        "families_bound": {"type": "array", "items": {"type": "string"}},
        "families_partially_bound": {"type": "array", "items": {"type": "string"}},
        "unbound_requirements": {"type": "array", "items": {"type": "string"}},
        "build_ir_step_count": {"type": "integer"},
        "validation_point_count": {"type": "integer"}
      }
    },
    "build_ir": {
      "type": "object",
      "description": "完整的 Build IR（来自 build_ir.schema.json），或其引用",
      "properties": {
        "ir_id": {"type": "string"},
        "build_steps": {"type": "array", "description": "构建步骤（完整内嵌或引用外部文件）"},
        "inline": {"type": "boolean", "description": "true=build_steps 内嵌在此, false=通过 ir_id 引用外部文件"}
      }
    },
    "validation_ir": {
      "type": "object",
      "description": "验证 IR（来自 build_ir.schema.json 中的 validation_ir），或其引用",
      "properties": {
        "validations": {"type": "array"},
        "inline": {"type": "boolean"}
      }
    },
    "capability_gaps": {
      "type": "array",
      "description": "汇总的能力缺口",
      "items": {
        "type": "object",
        "properties": {
          "gap_id": {"type": "string"},
          "source": {"type": "string", "description": "来源阶段（planner/skill/review/lowering）"},
          "description": {"type": "string"},
          "severity": {"type": "string", "enum": ["blocker", "degraded", "cosmetic"]}
        }
      }
    },
    "approval": {
      "type": "object",
      "description": "执行批准状态",
      "required": ["approval_status"],
      "properties": {
        "approval_status": {
          "type": "string",
          "enum": ["approved", "approved_with_warnings", "blocked"],
          "description": "approved=可执行, blocked=不允许进入执行"
        },
        "approver": {"type": "string", "description": "批准者（human/auto）"},
        "blocked_reasons": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"}
      }
    },
    "legacy_compatibility": {
      "type": "object",
      "description": "v1 兼容层（可选），仅在旧链路 fallback 时使用",
      "properties": {
        "scene_spec": {
          "type": "object",
          "description": "v1 格式的 scene_spec.actors（由 Lowering 额外生成的降级产物）",
          "properties": {
            "actors": {"type": "array"}
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "generated_at": {"type": "string", "format": "date-time"},
        "generator": {"type": "string"},
        "source_gdd": {"type": "string"},
        "source_projection_id": {"type": "string"},
        "source_planner_id": {"type": "string"},
        "source_review_id": {"type": "string"},
        "source_ir_id": {"type": "string"}
      }
    }
  }
}
```

---

## 八、Compiler 五段接口规约

### 8.1 总体约定

- **调用方式**：Claude Code 作为 AI Agent，按序读取上一阶段输出、加载相关 Knowledge Pack / Skill Template，生成本阶段结构化 JSON 输出
- **错误处理**：每个阶段输出中包含 `status` 字段。如果 status 为 `failed` 或 `blocked`，后续阶段不得继续
- **段间传递格式**：统一 JSON，文件保存到 `ProjectState/phase8/` 目录下
- **幂等性**：同一输入重复执行同一阶段，应产生一致的结构化输出

### 8.2 Stage 1：Design Intake

**职责**：从 GDD markdown 提取结构化设计投影

**输入**：
| 输入 | 来源 | 格式 |
|------|------|------|
| GDD 文件 | `ProjectInputs/GDD/GDD_MonopolyGame.md` | Markdown |
| Phase 配置 | 硬编码/配置文件 | `{ "target_phase": "phase1_local_multiplayer" }` |

**处理逻辑**：
1. 读取 GDD 全文
2. 识别 Part A（设计真源）和 Part B（实现约束）边界
3. 从 Part A 提取：game_identity, board_layout, tile_catalog, color_groups, turn_loop, property_rules, jail_rules, bankruptcy_rules, ui_requirements
4. 从 Part B 提取：class_naming_convention, core_classes, editor_steps_summary, phase2_network_notes
5. 标记 phase_scope：in_scope / out_of_scope
6. 标记 ambiguities 和 risk_notes

**输出**：
| 输出 | 文件 | Schema |
|------|------|--------|
| GDD Projection | `ProjectState/phase8/gdd_projection.json` | `gdd_projection.schema.json` |

**错误条件**：
- GDD 文件不存在 → 失败
- 无法识别 game_type → 失败
- Part A / Part B 无法区分 → 降级为全文投影 + warning

### 8.3 Stage 2：Planner / Routing

**职责**：基于 GDD Projection 选择 Skill Templates、定义 Dynamic Spec 目标、报告能力缺口

**输入**：
| 输入 | 来源 | 格式 |
|------|------|------|
| GDD Projection | Stage 1 输出 | `gdd_projection.json` |
| Skill Template Library | `SkillTemplates/` 目录下所有 `manifest.yaml` | YAML |
| Static Base 词表 | `StaticBase/vocabulary/` | YAML/JSON |
| 项目模式 | 配置 | `greenfield` / `brownfield` |

**处理逻辑**：
1. 读取 GDD Projection 中的 game_identity 和 phase_scope
2. 扫描可用 Skill Template Library，匹配 game_type + subgenre + phase_scope
3. 选择需要实例化的 Skill Templates，建立依赖图
4. 确定本轮目标 Dynamic Spec Families
5. 检查 Static Base 是否足以承接，报告 capability_gaps
6. 输出 review_focuses（告诉 Cross-Review 重点审什么）

**输出**：
| 输出 | 文件 | Schema |
|------|------|--------|
| Planner Output | `ProjectState/phase8/planner_output.json` | `planner_output.schema.json` |

**错误条件**：
- 无匹配的 Skill Template → 报告 capability_gap，status = blocked
- Phase scope 无法确定 → 失败
- GDD Projection 缺少关键域 → 失败

### 8.4 Stage 3：Skill Runtime

**职责**：按 Planner 选出的 Skill Instance 列表，逐个实例化并运行，生成 Dynamic Spec Fragments

**输入**：
| 输入 | 来源 | 格式 |
|------|------|------|
| Planner Output | Stage 2 输出 | `planner_output.json` |
| GDD Projection | Stage 1 输出 | `gdd_projection.json` |
| Skill Template Pack | `SkillTemplates/genre_packs/boardgame/monopoly_like/<template>/` | 目录（manifest + prompt + schema + examples） |

**处理逻辑**：
对 Planner 选出的每个 skill_instance（按依赖顺序）：
1. 加载对应 Template Pack 的 `system_prompt.md` + `domain_prompt.md`
2. 按 `input_selector.yaml` 从 GDD Projection 中选取相关设计域
3. Claude 作为该领域专家，按 `output_schema.json` 约束生成 spec_fragment
4. 执行 `evaluator_prompt.md` 自检
5. 记录 assumptions、open_questions、review_hints、capability_gaps
6. 输出 Skill Fragment

**输出**：
| 输出 | 文件 | Schema |
|------|------|--------|
| Skill Fragment × N | `ProjectState/phase8/skill_fragments/skill-board.json` 等 | `skill_fragment.schema.json` |

**执行顺序**（MonopolyGame）：
```
skill-board       (monopoly.board_topology.phase1)     → depends_on: []
skill-tile-event  (monopoly.tile_event_dispatch.phase1) → depends_on: [skill-board]
skill-turn        (monopoly.turn_and_dice_flow.phase1)  → depends_on: [skill-board]
skill-economy     (monopoly.property_economy.phase1)    → depends_on: [skill-board, skill-tile-event]
skill-jail        (monopoly.jail_and_bankruptcy.phase1)  → depends_on: [skill-turn, skill-economy]
skill-ui          (monopoly.phase1_ui_flow.phase1)      → depends_on: [skill-turn, skill-economy, skill-jail]
```

**错误条件**：
- Template Pack 不存在 → 失败
- output_schema.json 校验不通过 → 标记 status = failed，继续下一个
- 所有 Skill 均失败 → 整体失败

### 8.5 Stage 4：Cross-Spec Review

**职责**：对所有 Skill Fragment 做统一审查，检查一致性、闭合性、Phase 边界

**输入**：
| 输入 | 来源 | 格式 |
|------|------|------|
| Skill Fragments | Stage 3 输出 | `skill_fragments/*.json` |
| Planner Output | Stage 2 输出 | `planner_output.json`（获取 review_focuses） |
| Knowledge Pack Review Rubric | `SkillTemplates/base_domains/review_rubric.md`（如有） | Markdown |

**处理逻辑**：
1. 加载所有 Skill Fragment
2. 按 Planner 的 review_focuses 逐项审查
3. MonopolyGame 必检项：
   - 28 格索引 0..27 闭合，无缺口
   - 四角格索引与 board_topology 一致
   - 双数再掷与三连入狱规则不冲突
   - 起点奖励与前往监狱逻辑不冲突
   - 租金计算依赖 owner + color_group 数据可用
   - 破产释放地产与 ownership 数据闭合
   - UI 弹窗覆盖所有决策分支
   - 未越界到 Phase 2
4. 合并所有 fragments 为统一的 reviewed_dynamic_spec_tree
5. 汇总 capability_gaps

**输出**：
| 输出 | 文件 | Schema |
|------|------|--------|
| Cross-Review Report | `ProjectState/phase8/cross_review_report.json` | `cross_review_report.schema.json` |

报告中包含 `reviewed_dynamic_spec_tree`（审查后的统一树）。

**错误条件**：
- 存在 blocker 级别的审查失败 → review_status = blocked，不允许进入 Lowering
- 存在 warning → review_status = approved_with_warnings，可继续

### 8.6 Stage 5：Lowering

**职责**：将 reviewed dynamic spec tree 下沉为 Build IR + Validation IR

**输入**：
| 输入 | 来源 | 格式 |
|------|------|------|
| Cross-Review Report（含 reviewed_dynamic_spec_tree） | Stage 4 输出 | `cross_review_report.json` |
| Static Base 词表 | `StaticBase/vocabulary/` | YAML/JSON |
| Lowering 映射表 | `StaticBase/lowering_maps/` | YAML/JSON |
| 项目模式 | 配置 | `greenfield` |

**处理逻辑**：
按 Lowering_Pipeline_v1 的四阶段管线：

**Phase A: Normalization**
- 归一化 family 引用
- 确认 tile_count=28、索引 0..27 完整
- 消解别名与重复定义

**Phase B: Dependency Closure**
- 检查 family 间依赖闭合
- 确认租金计算所需的 owner/color_group 数据存在
- 确认 UI 决策节点可追溯到 turn_flow/property/jail

**Phase C: Static Capability Binding**
- board_topology_spec → board_manager_spec + tile_spawn_layout_spec + tile_world_location_spec
- tile_system_spec → tile_data_schema_spec + tile_event_slot_spec
- turn_flow_spec → game_mode_phase_machine_spec + dice_roll_rule_spec
- player_economy_spec → player_state_money_spec + payment_transfer_rule_spec
- ui_flow_spec → hud_widget_spec + popup_widget_spec + controller_ui_binding_spec

**Phase D: Build IR Generation**
- 生成 14 个 build_steps（create_board_ring_layout ... attach_validation_hooks）
- 生成 validation_ir（验证点列表）
- 生成 lowering_report

**输出**：
| 输出 | 文件 | Schema |
|------|------|--------|
| Build IR | `ProjectState/phase8/build_ir.json` | `build_ir.schema.json` |

**错误条件**：
- family 依赖未闭合 → 失败
- 关键规则无法绑定 → 失败
- 误下沉了 Phase 2 功能 → 失败

---

## 九、段间数据流总结

```
GDD_MonopolyGame.md
  │
  ▼ [Stage 1: Intake]
ProjectState/phase8/gdd_projection.json
  │
  ▼ [Stage 2: Planner]
ProjectState/phase8/planner_output.json
  │
  ▼ [Stage 3: Skill Runtime]
ProjectState/phase8/skill_fragments/
  ├── skill-board.json
  ├── skill-tile-event.json
  ├── skill-turn.json
  ├── skill-economy.json
  ├── skill-jail.json
  └── skill-ui.json
  │
  ▼ [Stage 4: Cross-Review]
ProjectState/phase8/cross_review_report.json
  （内含 reviewed_dynamic_spec_tree）
  │
  ▼ [Stage 5: Lowering]
ProjectState/phase8/build_ir.json
  │
  ▼ [Handoff 组装]
ProjectState/phase8/reviewed_handoff_v2.json
  │
  ▼ [Execution]
Run Plan → MCP/Bridge → UE5
```

---

## 十、MonopolyGame 样例数据概要

为便于实施，此处给出每个 Schema 的 MonopolyGame 关键数据点：

| Schema | 关键数据点 |
|--------|-----------|
| gdd_projection | game_type=board_strategy, subgenre=monopoly_like, tile_count=28, player_count=[2,4], start_bonus=200 |
| planner_output | 6 个 skill instances, 9 个 dynamic_spec_targets, mode=greenfield |
| skill_fragment × 6 | board(28格), turn(2d6+doubles), tile_event(8类型), economy(rent+bankruptcy), jail(bail+3turn), ui(6 popups) |
| cross_review_report | 7+ 审查项, reviewed_dynamic_spec_tree 含 9 个 family |
| build_ir | 14 个 build_steps, 10+ 个 validation_ir 点 |
| reviewed_handoff_v2 | 包含以上所有摘要 + approval_status |
