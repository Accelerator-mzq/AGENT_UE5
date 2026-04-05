"""
Planner / Routing — Stage 2 主入口

职责：
  基于 GDD Projection 选择 Skill Templates、建立依赖图、
  定义 Dynamic Spec 目标、报告能力缺口和审查重点。

输入：
  - gdd_projection.json（Stage 1 输出）
  - Skill Template Library（SkillTemplates/ 目录下所有 manifest.yaml）
  - Static Base 词表（StaticBase/vocabulary/）
  - 项目模式（greenfield / brownfield）

输出：
  - planner_output.json（符合 planner_output.schema.json）

注意：
  本阶段由 Claude Code 作为 AI Agent 执行。
  Planner 不直接生成 UE5 代码，不替代 Dynamic Spec families，
  不把 Build IR 混进 Planner 层。
"""

import json
import os
from datetime import datetime, timezone


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Schemas', 'planner_output.schema.json'
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'ProjectState', 'phase8'
)


def get_schema():
    """加载 Planner Output Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_skill_templates(templates_dir: str) -> list:
    """
    扫描可用的 Skill Template manifest.yaml 列表。
    返回 template_id 和元信息列表。
    """
    templates = []
    for root, dirs, files in os.walk(templates_dir):
        if 'manifest.yaml' in files:
            manifest_path = os.path.join(root, 'manifest.yaml')
            templates.append({
                "path": manifest_path,
                "dir": root
            })
    return templates


def create_planner_output_template(
    source_projection_id: str,
    mode: str = "greenfield",
    target_phase: str = "phase1_local_multiplayer"
) -> dict:
    """
    创建 Planner Output 模板结构。
    实际选择和路由决策由 AI Agent 填充。
    """
    return {
        "planner_meta": {
            "planner_version": "v1",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_projection_id": source_projection_id,
            "mode": mode,
            "target_phase": target_phase,
            "target_build_goal": "playable_template"
        },
        "project_intent": {},      # AI 填充
        "routing_decision": {},     # AI 填充
        "selected_skill_instances": [],  # AI 填充
        "dynamic_spec_targets": [],     # AI 填充
        "execution_strategy": {},       # AI 填充
        "capability_gaps": [],
        "review_focuses": [],
        "open_questions": [],
        "confidence": {}
    }


def save_planner_output(output: dict, output_path: str = None):
    """保存 Planner Output 到文件"""
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, 'planner_output.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    return output_path
