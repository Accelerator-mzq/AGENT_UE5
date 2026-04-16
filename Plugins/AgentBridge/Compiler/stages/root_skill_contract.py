"""
Phase 11 Root Skill Contract stage.

职责：
  - 从 GDD 中提取当前 Phase 的硬约束与可变空间
  - 合并 Universal Game Baseline 的最低能力要求
  - 输出可直接保存并校验的 root_skill_contract.json
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _read_gdd(gdd_path: str) -> str:
    """读取 GDD 文本；路径按当前项目工作目录解析。"""
    return Path(gdd_path).read_text(encoding="utf-8")


def _safe_token(raw_value: str, fallback: str) -> str:
    """生成 contract_id 使用的安全小写 token。"""
    token = re.sub(r"[^a-z0-9_]+", "_", raw_value.lower()).strip("_")
    return token or fallback


def _extract_player_count(gdd_text: str) -> List[int]:
    """从 GDD 中提取玩家人数范围。"""
    match = re.search(r"玩家人数\*\*?[:：]\s*(\d+)\s*-\s*(\d+)", gdd_text)
    if match:
        return [int(match.group(1)), int(match.group(2))]
    return [2, 4]


def _extract_int(pattern: str, gdd_text: str, fallback: int) -> int:
    """用正则提取单个整数，失败时使用保守默认值。"""
    match = re.search(pattern, gdd_text)
    return int(match.group(1)) if match else fallback


def _make_constraint(value: Any, gdd_ref: str) -> Dict[str, Any]:
    """构造 Root Skill Contract 的 constraint field。"""
    return {
        "type": "constraint",
        "value": value,
        "gdd_ref": gdd_ref,
    }


def _make_variant(must_satisfy: List[str], must_not: List[str], gdd_ref: str) -> Dict[str, Any]:
    """构造 Root Skill Contract 的 variant field。"""
    return {
        "type": "variant",
        "bounds": {
            "must_satisfy": must_satisfy,
            "must_not": must_not,
        },
        "gdd_ref": gdd_ref,
    }


def _build_constraint_fields(gdd_text: str) -> Dict[str, Any]:
    """提取 GDD 明确锁定的硬约束。"""
    tile_count = _extract_int(r"共\s*\*\*(\d+)\s*格\*\*", gdd_text, 28)
    start_bonus = _extract_int(r"获得\s*\$(\d+)", gdd_text, 200)
    starting_cash = _extract_int(r"初始资金\s*\$(\d+)", gdd_text, 1500)
    jail_bail = _extract_int(r"支付\s*\$(\d+)\s*保释", gdd_text, 50)
    match_length = re.search(r"单局时长目标\*\*?[:：]\s*(\d+)\s*-\s*(\d+)", gdd_text)
    match_length_range = [int(match_length.group(1)), int(match_length.group(2))] if match_length else [20, 40]

    return {
        "game.game_type": _make_constraint("board_strategy", "GDD 1 游戏类型"),
        "game.subgenre": _make_constraint("monopoly_like", "GDD 1 游戏类型"),
        "game.player_count_range": _make_constraint(_extract_player_count(gdd_text), "GDD 1 玩家人数"),
        "game.presentation_model": _make_constraint("top_down_3d", "GDD 1 视角"),
        "game.win_condition": _make_constraint("last_non_bankrupt_player", "GDD 1 胜利条件"),
        "game.match_length_minutes": _make_constraint(match_length_range, "GDD 1 单局时长目标"),
        "phase.current_scope": _make_constraint("phase1_local_multiplayer", "GDD 开发分期"),
        "board.tile_count": _make_constraint(tile_count, "GDD 2.1 棋盘布局"),
        "board.layout_shape": _make_constraint("square_ring", "GDD 2.1 棋盘布局"),
        "board.movement_direction": _make_constraint("clockwise", "GDD 2.1 棋盘布局"),
        "board.corner_indices": _make_constraint(
            {
                "start": 0,
                "jail_visit": 7,
                "free_parking": 14,
                "go_to_jail": 21,
            },
            "GDD 2.1 角格",
        ),
        "economy.starting_cash": _make_constraint(starting_cash, "GDD 3.1 游戏流程"),
        "economy.start_bonus": _make_constraint(start_bonus, "GDD 3.2 START"),
        "dice.count": _make_constraint(2, "GDD 3.4 骰子规则"),
        "dice.sides": _make_constraint(6, "GDD 3.4 骰子规则"),
        "dice.doubles_extra_turn": _make_constraint(True, "GDD 3.4 骰子规则"),
        "dice.triple_doubles_jail": _make_constraint(True, "GDD 3.4 骰子规则"),
        "jail.visit_tile_index": _make_constraint(7, "GDD 2.1 角格"),
        "jail.bail_cost": _make_constraint(jail_bail, "GDD 3.2 监狱规则"),
        "jail.max_turns": _make_constraint(3, "GDD 3.2 监狱规则"),
        "property.full_color_group_rent_multiplier": _make_constraint(2, "GDD 2.4 颜色组"),
        "ui.required_hud_fields": _make_constraint(
            ["current_player", "player_cash", "turn_number"],
            "GDD 4.1 HUD 信息",
        ),
    }


def _build_variant_fields() -> Dict[str, Any]:
    """定义 GDD 未锁死但必须受 bounds 管控的设计空间。"""
    return {
        "board.world_layout_dimensions": _make_variant(
            [
                "28 个格子在主相机下完整可见",
                "四个角格可读且玩家移动路径清晰",
            ],
            [
                "格子重叠",
                "HUD 遮挡核心棋盘区域",
            ],
            "GDD 2.1 仅锁定环形路线，未锁定世界坐标尺寸",
        ),
        "board.tile_visual_style": _make_variant(
            ["地产、税务、机会、公共基金等类型可区分"],
            ["视觉样式改变格子类型语义"],
            "GDD 2.2 格子类型定义",
        ),
        "player_token.visual_style": _make_variant(
            ["2-4 名玩家在棋盘上可区分"],
            ["棋子遮挡格子标签"],
            "GDD 未锁定棋子模型",
        ),
        "hud.layout_style": _make_variant(
            ["显示当前玩家、全部资金、当前回合数"],
            ["遮挡购买/租金/监狱弹窗"],
            "GDD 4.1 只定义 HUD 信息，不锁定布局",
        ),
        "popup.presentation_style": _make_variant(
            ["覆盖购买、租金、监狱、破产、游戏结束交互"],
            ["省略 GDD 指定按钮"],
            "GDD 4.2 弹出式 UI",
        ),
        "dice.roll_feedback": _make_variant(
            ["显示两颗骰子结果与是否双数"],
            ["动画延迟阻塞回合节奏"],
            "GDD 3.4 未锁定骰子表现",
        ),
        "audio.feedback_style": _make_variant(
            ["基础 BGM/SFX 可被设置页音量控制"],
            ["音效反馈影响规则判断"],
            "Universal Baseline 音频基础",
        ),
        "frontend.visual_theme": _make_variant(
            ["保留 Monopoly-like 棋盘策略识别度"],
            ["主题风格降低按钮和文字可读性"],
            "Universal Baseline 前台壳层",
        ),
    }


def _baseline_capabilities() -> List[Dict[str, Any]]:
    """合并 Universal Baseline 七类基础能力。"""
    return [
        {
            "capability_id": "baseline-start-screen",
            "category": "startup_entry",
            "baseline_item": "Start Screen",
            "activation": "required",
            "realization_class": "presence_only",
            "required_elements": [
                "project_identity_display",
                "user_interaction_trigger",
                "navigate_to_main_menu",
            ],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-main-menu",
            "category": "frontend_shell",
            "baseline_item": "Main Menu",
            "activation": "required",
            "realization_class": "presence_only",
            "required_elements": ["New Game", "Settings", "Quit"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-settings",
            "category": "settings_configuration",
            "baseline_item": "Settings",
            "activation": "required",
            "realization_class": "presence_only",
            "required_controls": [
                "Master Volume",
                "SFX Volume",
                "Window Mode",
                "Resolution",
                "Apply",
                "Back",
            ],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-pause",
            "category": "frontend_shell",
            "baseline_item": "Pause",
            "activation": "required",
            "realization_class": "presence_only",
            "required_elements": ["ESC entry", "Resume", "Settings", "Quit to Menu"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-results",
            "category": "hud_popup_results",
            "baseline_item": "Results",
            "activation": "required",
            "realization_class": "presence_only",
            "required_elements": ["winner_info", "Return to Menu"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-hud",
            "category": "hud_popup_results",
            "baseline_item": "HUD",
            "activation": "required",
            "realization_class": "realization_eligible",
            "required_elements": ["current_turn", "current_player", "player_cash", "dice_result"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
            "realization_basis": "HUD 与回合、资金、骰子结果强耦合，进入 Design Space Discovery。",
        },
        {
            "capability_id": "baseline-input-foundation",
            "category": "input_foundation",
            "baseline_item": "Input Foundation",
            "activation": "required",
            "realization_class": "presence_only",
            "required_elements": ["menu_confirm", "menu_cancel", "pause_input", "roll_dice_action"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-audio-foundation",
            "category": "audio_foundation",
            "baseline_item": "Audio Foundation",
            "activation": "required",
            "realization_class": "presence_only",
            "required_elements": ["bgm_volume_control", "sfx_volume_control", "basic_sfx_playback"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
        },
        {
            "capability_id": "baseline-platform-foundation",
            "category": "platform_foundation",
            "baseline_item": "Platform Foundation",
            "activation": "required",
            "realization_class": "clarification_gated",
            "required_elements": ["window_mode", "resolution", "quit_handling"],
            "upgrade_policy": "presence_only_to_realization_eligible_only",
            "clarification_reason": "目标平台与持久化策略会影响输入、分辨率和设置保存边界。",
        },
    ]


def _gameplay_capabilities() -> List[Dict[str, Any]]:
    """从 Monopoly GDD 派生当前 Phase 需要的 Gameplay Domain Skills。"""
    return [
        {"capability_id": "gameplay-board-topology", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-tile-system", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-turn-loop", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-dice", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-economy", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-player-management", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-jail", "activation": "required", "allows_design_space_discovery": True},
        {"capability_id": "gameplay-networking", "activation": "deferred", "allows_design_space_discovery": False},
        {"capability_id": "gameplay-ai-opponents", "activation": "deferred", "allows_design_space_discovery": False},
    ]


def _baseline_coverage(capabilities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """建立 Universal Baseline 七类能力覆盖记录。"""
    categories = {
        "startup_entry": "启动与入口",
        "frontend_shell": "前台壳层与页面流转",
        "settings_configuration": "设置与配置",
        "input_foundation": "输入基础",
        "hud_popup_results": "HUD / Popup / 结果表达",
        "audio_foundation": "音频基础",
        "platform_foundation": "平台基础",
    }
    return {
        category_id: {
            "label": label,
            "covered": any(item.get("category") == category_id for item in capabilities),
            "capability_ids": [
                item["capability_id"]
                for item in capabilities
                if item.get("category") == category_id
            ],
        }
        for category_id, label in categories.items()
    }


def _root_questions(
    constraints: Dict[str, Any],
    variants: Dict[str, Any],
    baseline: List[Dict[str, Any]],
    gameplay: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """回答 Root Skill Contract 标准中的 10 个问题。"""
    enabled = [item["capability_id"] for item in baseline + gameplay if item.get("activation") == "required"]
    deferred = [item["capability_id"] for item in baseline + gameplay if item.get("activation") == "deferred"]
    presence_only = [item["capability_id"] for item in baseline if item.get("realization_class") == "presence_only"]
    realization_eligible = [
        item["capability_id"]
        for item in baseline
        if item.get("realization_class") == "realization_eligible"
    ]
    discovery_domains = [
        item["capability_id"]
        for item in gameplay
        if item.get("allows_design_space_discovery")
    ]
    clarification_domains = [
        item["capability_id"]
        for item in baseline
        if item.get("realization_class") == "clarification_gated"
    ]
    return [
        {
            "question_id": "q1_constraint_fields",
            "status": "answered",
            "answer": f"已锁定 {len(constraints)} 个硬约束，包括棋盘 28 格、2-4 玩家、初始资金 1500、2D6、顺时针移动和破产胜利条件。",
        },
        {
            "question_id": "q2_soft_intents",
            "status": "answered",
            "answer": "目标是本地多人、节奏清晰、规则简化但仍保持 Monopoly-like 策略感。",
        },
        {
            "question_id": "q3_required_capabilities",
            "status": "answered",
            "answer": ", ".join(enabled),
        },
        {
            "question_id": "q4_phase_enabled_capabilities",
            "status": "answered",
            "answer": "Phase 1 启用本地多人、棋盘、回合、骰子、经济、监狱、HUD 与 Universal Baseline 壳层。",
        },
        {
            "question_id": "q5_deferred_capabilities",
            "status": "answered",
            "answer": ", ".join(deferred) if deferred else "无 deferred capability。",
        },
        {
            "question_id": "q6_presence_contract_baseline",
            "status": "answered",
            "answer": ", ".join(presence_only),
        },
        {
            "question_id": "q7_realization_eligible_baseline",
            "status": "answered",
            "answer": ", ".join(realization_eligible),
        },
        {
            "question_id": "q8_gameplay_discovery_domains",
            "status": "answered",
            "answer": ", ".join(discovery_domains),
        },
        {
            "question_id": "q9_clarification_required_domains",
            "status": "clarification_required",
            "answer": ", ".join(clarification_domains) + "；另需 Clarification Gate 确认最大游戏时长/僵局处理。",
        },
        {
            "question_id": "q10_skill_graph_boundary",
            "status": "answered",
            "answer": "Skill Graph 只规划 Domain Skill、Baseline Skill、依赖、耦合和收敛顺序；不提前写死 realization 或 Build IR。",
        },
    ]


def _design_element_classification(constraints: Dict[str, Any], variants: Dict[str, Any]) -> List[Dict[str, Any]]:
    """汇总设计元素的 Constraint / Variant 标注，方便验收和下游保持性检查。"""
    classified = [
        {
            "field_path": field_path,
            "classification": "constraint",
            "basis": value.get("gdd_ref", ""),
        }
        for field_path, value in constraints.items()
    ]
    classified.extend(
        {
            "field_path": field_path,
            "classification": "variant",
            "basis": value.get("gdd_ref", ""),
        }
        for field_path, value in variants.items()
    )
    return classified


def create_root_skill_contract(
    gdd_path: str,
    target_phase: str,
    run_id: str | None = None,
) -> Dict[str, Any]:
    """生成可保存的 Root Skill Contract。"""
    gdd_text = _read_gdd(gdd_path)
    generated_at = datetime.now(timezone.utc).isoformat()
    date_token = datetime.now(timezone.utc).strftime("%Y%m%d")
    phase_token = _safe_token(target_phase, "phase")
    project_token = "monopoly"

    constraints = _build_constraint_fields(gdd_text)
    variants = _build_variant_fields()
    baseline = _baseline_capabilities()
    gameplay = _gameplay_capabilities()

    contract = {
        "contract_version": "1.0",
        "contract_id": f"rsc.{project_token}.{phase_token}.{date_token}",
        "source_gdd": {
            "file_path": gdd_path,
            "scope_summary": "Part A defines Monopoly-like local multiplayer rules; Part B defines UE5 C++ implementation constraints.",
        },
        "game_identity": {
            "game_type": "board_strategy",
            "subgenre": "monopoly_like",
            "presentation_model": "top_down_3d",
            "player_count_range": constraints["game.player_count_range"]["value"],
            "win_condition": "last_non_bankrupt_player",
        },
        "phase_scope": {
            "current_phase": target_phase,
            "in_scope": [
                "local hot-seat multiplayer",
                "28 tile square-ring board",
                "2d6 turn loop",
                "property purchase and rent",
                "tax, jail, bankruptcy and win condition",
                "Universal Baseline shell",
            ],
            "out_of_scope": [
                "online multiplayer",
                "AI opponents",
                "auction rules",
                "full card events for Chance and Community",
            ],
        },
        "constraint_fields": constraints,
        "variant_fields": variants,
        "soft_intents": {
            "gameplay_feel": [
                "fast simplified Monopoly-like local prototype",
                "clear feedback for turn, dice, cash and ownership changes",
            ],
            "design_tensions": [
                "traditional board readability vs compact HUD",
                "simple Phase 1 rules vs enough strategic clarity",
                "elimination win condition vs avoiding unresolved stalemates",
            ],
        },
        "baseline_capabilities": baseline,
        "gameplay_capabilities": gameplay,
        "root_questions": _root_questions(constraints, variants, baseline, gameplay),
        "baseline_coverage": _baseline_coverage(baseline),
        "design_element_classification": _design_element_classification(constraints, variants),
        "clarification_markers": [
            {
                "item_id": "cg-max-game-length",
                "field_path": "game.stalemate_or_round_limit",
                "risk_level": "high",
                "reason": "GDD gives target match length but does not define a hard stalemate or round limit.",
                "suggested_decision": "clarification_required",
            },
            {
                "item_id": "cg-platform-persistence",
                "field_path": "baseline-platform-foundation.persistence_policy",
                "risk_level": "medium",
                "reason": "Settings persistence is not locked by GDD and affects platform behavior.",
                "suggested_decision": "accept_with_safe_default",
                "provisional_default": "session_only",
            },
        ],
        "metadata": {
            "generated_at": generated_at,
            "generator": "AgentBridge.Compiler.RootSkill.v1",
            "source_run_id": run_id,
        },
    }
    return contract


def save_root_skill_contract(contract: Dict[str, Any], output_path: str | Path) -> str:
    """保存 Root Skill Contract JSON。"""
    target_path = Path(output_path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as file:
        json.dump(contract, file, ensure_ascii=False, indent=2)
    return str(target_path)
