"""
Handoff Schema 验证脚本
验证 Handoff 和 Run Plan 是否符合 Schema
"""

import os
import sys
import json
import yaml
import jsonschema
from typing import Dict, Any


def validate_handoff(handoff_path: str, schema_path: str) -> bool:
    """
    验证 Handoff 是否符合 Schema

    Args:
        handoff_path: Handoff 文件路径
        schema_path: Schema 文件路径

    Returns:
        是否通过验证
    """
    try:
        # 加载 Handoff
        handoff = load_file(handoff_path)

        # 加载 Schema
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        # 验证
        jsonschema.validate(handoff, schema)

        print(f"[OK] {os.path.basename(handoff_path)} 通过 Schema 校验")
        return True

    except jsonschema.ValidationError as e:
        print(f"[ERROR] {os.path.basename(handoff_path)} Schema 校验失败:")
        print(f"   错误位置: {' -> '.join(str(p) for p in e.path)}")
        print(f"   错误信息: {e.message}")
        return False

    except Exception as e:
        print(f"[ERROR] {os.path.basename(handoff_path)} 验证过程出错: {str(e)}")
        return False


def load_file(file_path: str) -> Dict[str, Any]:
    """加载 YAML 或 JSON 文件"""
    ext = os.path.splitext(file_path)[1].lower()

    with open(file_path, 'r', encoding='utf-8') as f:
        if ext in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif ext == '.json':
            return json.load(f)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")


def validate_all_examples():
    """验证所有示例文件"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    schemas_dir = os.path.join(script_dir, "..", "..", "Schemas")
    examples_dir = os.path.join(schemas_dir, "examples")

    # 验证 Handoff 示例
    handoff_schema = os.path.join(schemas_dir, "reviewed_handoff.schema.json")
    handoff_examples = [
        os.path.join(examples_dir, "reviewed_handoff_greenfield.example.json")
    ]

    # 验证 Run Plan 示例
    run_plan_schema = os.path.join(schemas_dir, "run_plan.schema.json")
    run_plan_examples = [
        os.path.join(examples_dir, "run_plan_greenfield.example.json")
    ]

    print("=" * 60)
    print("验证 Reviewed Handoff 示例")
    print("=" * 60)

    handoff_passed = 0
    for example in handoff_examples:
        if os.path.exists(example):
            if validate_handoff(example, handoff_schema):
                handoff_passed += 1
        else:
            print(f"[WARN] 文件不存在: {example}")

    print()
    print("=" * 60)
    print("验证 Run Plan 示例")
    print("=" * 60)

    run_plan_passed = 0
    for example in run_plan_examples:
        if os.path.exists(example):
            if validate_handoff(example, run_plan_schema):
                run_plan_passed += 1
        else:
            print(f"[WARN] 文件不存在: {example}")

    print()
    print("=" * 60)
    print("验证结果汇总")
    print("=" * 60)
    print(f"Handoff 示例: {handoff_passed}/{len(handoff_examples)} 通过")
    print(f"Run Plan 示例: {run_plan_passed}/{len(run_plan_examples)} 通过")

    total_passed = handoff_passed + run_plan_passed
    total_count = len(handoff_examples) + len(run_plan_examples)

    if total_passed == total_count:
        print("\n[SUCCESS] 全部通过！")
        return 0
    else:
        print(f"\n[FAILED] {total_count - total_passed} 个文件未通过验证")
        return 1


if __name__ == "__main__":
    sys.exit(validate_all_examples())
