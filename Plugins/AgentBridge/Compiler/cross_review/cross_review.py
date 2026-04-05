"""
Cross-Spec Review — Stage 4 主入口

职责：
  对所有 Skill Fragment 做统一审查：
  - 一致性检查（索引闭合、规则不冲突）
  - 闭合性检查（依赖数据是否都存在）
  - Phase 边界检查（未越界到 Phase 2）
  合并所有 fragments 为统一的 reviewed_dynamic_spec_tree。

输入：
  - skill_fragments/*.json（Stage 3 输出）
  - planner_output.json（Stage 2 输出，获取 review_focuses）
  - Knowledge Pack review_rubric.md（如有）

输出：
  - cross_review_report.json（符合 cross_review_report.schema.json）
  - 报告中包含 reviewed_dynamic_spec_tree

MonopolyGame 必检项：
  - 28 格索引 0..27 闭合，无缺口
  - 四角格索引与 board_topology 一致
  - 双数再掷与三连入狱规则不冲突
  - 起点奖励与前往监狱逻辑不冲突
  - 租金计算依赖 owner + color_group 数据可用
  - 破产释放地产与 ownership 数据闭合
  - UI 弹窗覆盖所有决策分支
  - 未越界到 Phase 2
"""

import json
import os
from datetime import datetime, timezone


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Schemas', 'cross_review_report.schema.json'
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'ProjectState', 'phase8'
)


def get_schema():
    """加载 Cross-Review Report Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_all_fragments(fragments_dir: str) -> list:
    """加载所有 Skill Fragment 文件"""
    fragments = []
    if os.path.isdir(fragments_dir):
        for filename in sorted(os.listdir(fragments_dir)):
            if filename.endswith('.json'):
                filepath = os.path.join(fragments_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    fragments.append(json.load(f))
    return fragments


def create_review_report_template(input_fragment_ids: list) -> dict:
    """
    创建 Cross-Review Report 模板结构。
    实际审查逻辑由 AI Agent 执行。
    """
    return {
        "review_id": "",  # AI 填充
        "review_version": "v1",
        "input_fragment_ids": input_fragment_ids,
        "review_status": "",      # AI 判定
        "review_checks": [],      # AI 填充
        "issues_found": [],
        "phase_scope_check": {
            "in_scope_confirmed": False,
            "out_of_scope_violations": []
        },
        "reviewed_dynamic_spec_tree": {},  # AI 合并
        "capability_gap_list": [],
        "lowering_ready": False,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "AgentBridge.Compiler.CrossReview.v1"
        }
    }


def save_review_report(report: dict, output_path: str = None):
    """保存 Cross-Review Report 到文件"""
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, 'cross_review_report.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    return output_path
