"""
Design Intake — Stage 1 主入口

职责：
  从 GDD markdown 提取结构化设计投影。
  将 GDD 的自然语言转化为下游模块可消费的 JSON。

输入：
  - GDD 文件路径（如 ProjectInputs/GDD/GDD_MonopolyGame.md）
  - Phase 配置（如 { "target_phase": "phase1_local_multiplayer" }）

输出：
  - gdd_projection.json（符合 gdd_projection.schema.json）

处理逻辑：
  1. 读取 GDD 全文
  2. 识别 Part A（设计真源）和 Part B（实现约束）边界
  3. 从 Part A 提取：game_identity, board_layout, tile_catalog, color_groups,
     turn_loop, property_rules, jail_rules, bankruptcy_rules, ui_requirements
  4. 从 Part B 提取：class_naming_convention, core_classes, phase2_network_notes
  5. 标记 phase_scope: in_scope / out_of_scope
  6. 标记 ambiguities 和 risk_notes

注意：
  本阶段由 Claude Code 作为 AI Agent 执行。
  此文件是接口定义和文档，不是硬编码解析逻辑。
  实际的 GDD 理解由 LLM 完成，不再使用 regex 解析。
"""

import json
import os
from datetime import datetime, timezone


# Schema 路径
SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Schemas', 'gdd_projection.schema.json'
)

# 输出目录
OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'ProjectState', 'phase8'
)


def get_schema():
    """加载 GDD Projection Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_projection_template(gdd_path: str, target_phase: str) -> dict:
    """
    创建 GDD Projection 模板结构。
    实际字段值由 AI Agent 填充。
    """
    return {
        "projection_version": "1.0",
        "projection_id": "",  # AI 填充
        "source_gdd": {
            "file_path": gdd_path,
            "part_a_scope": "",  # AI 填充
            "part_b_scope": ""   # AI 填充
        },
        "game_identity": {
            "game_type": "",      # AI 识别
            "subgenre": "",       # AI 识别
            "presentation_model": "",
            "player_count_range": [0, 0],
            "win_condition": ""
        },
        "phase_scope": {
            "current_phase": target_phase,
            "in_scope": [],       # AI 提取
            "out_of_scope": []    # AI 提取
        },
        "design_domains": {},     # AI 填充各设计域
        "implementation_hints": {},
        "ambiguities": [],
        "risk_notes": [],
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "AgentBridge.Compiler.Intake.v1"
        }
    }


def save_projection(projection: dict, output_path: str = None):
    """保存 GDD Projection 到文件"""
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, 'gdd_projection.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(projection, f, ensure_ascii=False, indent=2)
    return output_path
