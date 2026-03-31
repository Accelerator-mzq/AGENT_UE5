"""
Handoff Serializer
序列化 Handoff 为 YAML/JSON
"""

import os
import yaml
import json
from typing import Dict, Any


def serialize_handoff(
    handoff: Dict[str, Any],
    output_path: str,
    format: str = "yaml"
) -> str:
    """
    序列化 Handoff

    Args:
        handoff: Handoff 字典
        output_path: 输出路径（文件路径或目录路径）
        format: 格式（yaml / json）

    Returns:
        实际保存的文件路径
    """
    # 如果 output_path 是目录，生成文件名
    if os.path.isdir(output_path):
        handoff_id = handoff.get("handoff_id", "unknown")
        filename = f"{handoff_id}.{format}"
        output_file = os.path.join(output_path, filename)
    else:
        output_file = output_path

    # 确保目录存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 序列化
    if format == "yaml":
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(handoff, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    elif format == "json":
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(handoff, f, indent=2, ensure_ascii=False)
    else:
        raise ValueError(f"不支持的格式: {format}")

    return output_file


def deserialize_handoff(handoff_path: str) -> Dict[str, Any]:
    """
    反序列化 Handoff

    Args:
        handoff_path: Handoff 文件路径

    Returns:
        Handoff 字典
    """
    if not os.path.exists(handoff_path):
        raise FileNotFoundError(f"Handoff 文件不存在: {handoff_path}")

    # 根据扩展名判断格式
    ext = os.path.splitext(handoff_path)[1].lower()

    if ext in ['.yaml', '.yml']:
        with open(handoff_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    elif ext == '.json':
        with open(handoff_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


if __name__ == "__main__":
    # 测试代码
    test_handoff = {
        "handoff_version": "1.0",
        "handoff_id": "handoff.test.prototype.001",
        "handoff_mode": "greenfield_bootstrap",
        "status": "draft",
        "dynamic_spec_tree": {
            "scene_spec": {
                "actors": []
            }
        }
    }

    # 测试序列化
    output_file = serialize_handoff(test_handoff, "test_output/", format="yaml")
    print(f"保存到: {output_file}")

    # 测试反序列化
    if os.path.exists(output_file):
        loaded = deserialize_handoff(output_file)
        print(f"加载成功: {loaded['handoff_id']}")
