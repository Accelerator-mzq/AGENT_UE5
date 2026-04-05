"""
Skill Runtime — Stage 3 主入口

职责：
  按 Planner 选出的 Skill Instance 列表（按依赖顺序），
  逐个加载 Template Pack、实例化运行，生成 Dynamic Spec Fragment。

输入：
  - planner_output.json（Stage 2 输出）
  - gdd_projection.json（Stage 1 输出）
  - Skill Template Pack 目录（每个 Template 的 manifest + prompt + schema + examples）

输出：
  - skill_fragments/skill-<id>.json × N（符合 skill_fragment.schema.json）

工作方式（AI Agent 驱动）：
  对 Planner 选出的每个 skill_instance（按依赖顺序）：
  1. 加载对应 Template Pack 的 system_prompt.md + domain_prompt.md
  2. 按 input_selector.yaml 从 GDD Projection 中选取相关设计域
  3. Claude 作为该领域专家，按 output_schema.json 约束生成 spec_fragment
  4. 执行 evaluator_prompt.md 自检
  5. 记录 assumptions, open_questions, review_hints, capability_gaps
  6. 输出 Skill Fragment
"""

import json
import os
from datetime import datetime, timezone


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Schemas', 'skill_fragment.schema.json'
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'ProjectState', 'phase8', 'skill_fragments'
)


def get_schema():
    """加载 Skill Fragment Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_template_pack(template_dir: str) -> dict:
    """
    加载 Skill Template Pack 的组件。
    返回包含 manifest, system_prompt, domain_prompt, input_selector, output_schema 的字典。
    """
    pack = {"dir": template_dir}
    for filename in ['manifest.yaml', 'system_prompt.md', 'domain_prompt.md',
                     'input_selector.yaml', 'output_schema.json', 'evaluator_prompt.md']:
        filepath = os.path.join(template_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                pack[filename] = f.read()
    return pack


def create_fragment_template(
    skill_instance_id: str,
    template_id: str,
    phase_scope: str = "phase1_local_multiplayer"
) -> dict:
    """
    创建 Skill Fragment 模板结构。
    实际的 spec_fragments 由 AI Agent 填充。
    """
    return {
        "skill_instance_id": skill_instance_id,
        "template_id": template_id,
        "phase_scope": phase_scope,
        "status": "completed",
        "emitted_families": [],     # AI 填充
        "spec_fragments": {},       # AI 填充
        "assumptions": [],
        "open_questions": [],
        "review_hints": [],
        "capability_gaps": [],
        "confidence": {
            "coverage": 0.0,
            "consistency": 0.0
        },
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "AgentBridge.Compiler.SkillRuntime.v1"
        }
    }


def save_fragment(fragment: dict, skill_instance_id: str, output_dir: str = None):
    """保存 Skill Fragment 到文件"""
    if output_dir is None:
        output_dir = OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f'{skill_instance_id}.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(fragment, f, ensure_ascii=False, indent=2)
    return output_path
