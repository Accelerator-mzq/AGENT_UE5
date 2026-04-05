"""
Lowering / Translation — Stage 5 主入口

职责：
  将 reviewed dynamic spec tree 下沉为 Build IR + Validation IR。
  四阶段管线：
    Phase A: Normalization — 归一化 family、消解别名
    Phase B: Dependency Closure — 检查依赖闭合
    Phase C: Static Capability Binding — 绑定 Static Base
    Phase D: Build IR Generation — 生成构建意图 + 验证点

输入：
  - cross_review_report.json（Stage 4 输出，含 reviewed_dynamic_spec_tree）
  - StaticBase/vocabulary/ — 静态词表
  - StaticBase/lowering_maps/ — 语义→引擎映射表
  - 项目模式 + build_goal

输出：
  - build_ir.json（符合 build_ir.schema.json）

明确禁止：
  - 不允许把 GDD 拍平为单一 scene_spec / actor 列表
  - 不允许误下沉 Phase 2 功能
  - Lowering 不再重新理解 GDD，只翻译已审查的 spec tree
"""

import json
import os
from datetime import datetime, timezone


SCHEMA_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'Schemas', 'build_ir.schema.json'
)

OUTPUT_DIR = os.path.join(
    os.path.dirname(__file__), '..', '..', '..', '..', 'ProjectState', 'phase8'
)


def get_schema():
    """加载 Build IR Schema"""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_build_ir_template(
    source_review_id: str,
    phase_scope: str = "phase1_local_multiplayer"
) -> dict:
    """
    创建 Build IR 模板结构。
    实际的 build_steps 和 validation_ir 由 AI Agent 填充。
    """
    return {
        "ir_version": "1.0",
        "ir_id": "",  # AI 填充
        "source_review_id": source_review_id,
        "phase_scope": phase_scope,
        "build_steps": [],        # AI 填充 14 个步骤
        "validation_ir": [],      # AI 填充验证点
        "lowering_report": {
            "families_received": [],
            "families_bound": [],
            "families_partially_bound": [],
            "unbound_requirements": [],
            "capability_gaps": []
        },
        "recovery_hints": [],
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "AgentBridge.Compiler.Lowering.v1"
        }
    }


def save_build_ir(ir: dict, output_path: str = None):
    """保存 Build IR 到文件"""
    if output_path is None:
        output_path = os.path.join(OUTPUT_DIR, 'build_ir.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ir, f, ensure_ascii=False, indent=2)
    return output_path
