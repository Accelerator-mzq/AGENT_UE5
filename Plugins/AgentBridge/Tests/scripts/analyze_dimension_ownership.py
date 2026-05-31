"""只读分析：排查 discovery_fallback 的维度归属全貌。

不做判断、不改任何代码，只把
  节点 × relevant_variant_field × lens维度 × 域前缀 × 被引用次数 × 该节点 coupling/deps
摊成结构化矩阵，落盘供人工解读「跨域归属 / 重复发散 / 对端关系是否闭合」。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.Compiler.stages import discovery_fallback as dfb  # noqa: E402

SKILL_GRAPH = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260417-051444-a2b8" / "skill_graph.json"
OUT = PROJECT_ROOT / "ProjectState" / "Reports" / "2026-05-29" / "dimension_ownership_analysis.json"

# variant field 前缀 → 该域的"自然 owner 节点"。
# 横切类(无单一玩法 owner)标记为 CROSS_CUTTING。
FIELD_PREFIX_OWNERS = {
    "board": ["skill-board-topology", "skill-tile-system"],
    "dice": ["skill-dice", "skill-turn-loop"],
    "hud": ["skill-baseline-hud"],
    "player_token": ["skill-player-management"],
    "popup": "CROSS_CUTTING",      # 弹窗/事件反馈，无单一玩法 owner
    "frontend": "CROSS_CUTTING",   # 全局视觉主题
    "audio": "CROSS_CUTTING",      # 音频（当前无发散节点）
}


def field_prefix(field: str) -> str:
    return field.split(".")[0]


def main() -> int:
    graph = json.loads(SKILL_GRAPH.read_text(encoding="utf-8"))
    node_rel = {}
    for n in graph.get("nodes", []):
        node_rel[n.get("instance_id")] = {
            "coupling": n.get("coupling", []),
            "dependencies": n.get("dependencies", []),
            "domain_type": n.get("domain_type"),
        }

    profiles = dfb.NODE_ROLE_PROFILES
    lenses = dfb.FIELD_DISCOVERY_LENSES

    # ① variant field → 引用它的节点列表（重复发散统计）
    field_to_nodes = {}
    for node_id, prof in profiles.items():
        for f in prof.get("relevant_variant_fields", []):
            field_to_nodes.setdefault(f, []).append(node_id)

    # ② 每个节点的维度归属明细
    per_node = {}
    for node_id, prof in profiles.items():
        rel = node_rel.get(node_id, {})
        edges = set(rel.get("coupling", [])) | set(rel.get("dependencies", []))
        rows = []
        for f in prof.get("relevant_variant_fields", []):
            prefix = field_prefix(f)
            owner = FIELD_PREFIX_OWNERS.get(prefix, "UNKNOWN")
            if owner == "CROSS_CUTTING":
                ownership = "cross_cutting"
                endpoint_closed = None
            elif isinstance(owner, list):
                if node_id in owner:
                    ownership = "native"          # 该字段本就属于此节点域
                    endpoint_closed = None
                else:
                    ownership = "borrowed"         # 跨域借用
                    # 对端 owner 节点是否在本节点的关系边里
                    endpoint_closed = any(o in edges for o in owner)
            else:
                ownership = "unknown"
                endpoint_closed = None
            dims = [l.get("lens_key") for l in lenses.get(f, [])]
            rows.append({
                "variant_field": f,
                "prefix": prefix,
                "ownership": ownership,
                "endpoint_in_edges": endpoint_closed,
                "lens_dims": dims,
                "shared_with_n_nodes": len(field_to_nodes.get(f, [])),
            })
        per_node[node_id] = {
            "domain_type": rel.get("domain_type"),
            "coupling": rel.get("coupling", []),
            "dependencies": rel.get("dependencies", []),
            "fields": rows,
        }

    report = {
        "field_to_nodes": field_to_nodes,
        "per_node": per_node,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # 摘要（英文，避免终端 gbk 乱码）
    print("=== variant_field reuse (repeated divergence) ===")
    for f, nodes in sorted(field_to_nodes.items(), key=lambda kv: -len(kv[1])):
        print(f"  {f}: {len(nodes)} nodes -> {nodes}")
    print()
    print("=== borrowed (cross-domain) dimensions with endpoint closure ===")
    for node_id, info in per_node.items():
        for r in info["fields"]:
            if r["ownership"] == "borrowed":
                closed = "edge-OK" if r["endpoint_in_edges"] else "EDGE-MISSING"
                print(f"  {node_id} borrows {r['variant_field']} (dims={r['lens_dims']}) [{closed}]")
    print()
    print("report written:", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
