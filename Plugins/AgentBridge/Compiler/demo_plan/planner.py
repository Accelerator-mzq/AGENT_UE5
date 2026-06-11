# -*- coding: utf-8 -*-
"""demo_plan 切批核心:从 skill graph + 契约确定性产出批次计划与 stories。

防固化硬约束(Phase 13 spec §5.3 / Phase 14 spec §8):
本模块零游戏领域语义——切批只依赖通用结构字段
(template_source / domain_type / dependencies / instance_id),
capability_id 等业务字符串仅透传,不参与任何分支判断。
"""
from typing import Any, Dict, List

PLAN_SCHEMA_VERSION = "1.0.0"
STORY_SCHEMA_VERSION = "1.0.0"

# evidence_class 由 domain_type 机械映射(通用字段);未知 domain 保守取 Integration
_EVIDENCE_BY_DOMAIN = {"gameplay": "Logic", "baseline": "Visual"}
_SYNTHESIZED_DIR = "Plugins/AgentBridge/SkillTemplates/synthesized"


def _topo_order(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Kahn 拓扑排序;只计批内依赖入度;同层按 instance_id 字典序保证确定性;成环 fail-closed。"""
    ids = {n["instance_id"] for n in nodes}
    by_id = {n["instance_id"]: n for n in nodes}
    indeg = {i: 0 for i in ids}
    consumers: Dict[str, List[str]] = {i: [] for i in ids}
    for n in nodes:
        for dep in n.get("dependencies", []):
            if dep in ids:
                indeg[n["instance_id"]] += 1
                consumers[dep].append(n["instance_id"])
    ready = sorted(i for i in ids if indeg[i] == 0)
    ordered: List[Dict[str, Any]] = []
    while ready:
        cur = ready.pop(0)
        ordered.append(by_id[cur])
        for c in consumers[cur]:
            indeg[c] -= 1
            if indeg[c] == 0:
                ready.append(c)
        ready.sort()
    if len(ordered) != len(ids):
        raise ValueError("demo_plan: 批内依赖成环,fail-closed")
    return ordered


def _anchor_map(contract: Dict[str, Any]) -> Dict[str, List[str]]:
    """capability_id → GDD 锚点列表(契约两个容器统一收集)。"""
    out: Dict[str, List[str]] = {}
    for key in ("baseline_capabilities", "gameplay_capabilities"):
        for cap in contract.get(key) or []:
            anchor = cap.get("source_anchor")
            out[cap["capability_id"]] = [anchor] if anchor else []
    return out


def _capability_story(node: Dict[str, Any], batch_id: str, anchors: List[str],
                      manifest_version: str, paths: Dict[str, Any]) -> Dict[str, Any]:
    evidence_class = _EVIDENCE_BY_DOMAIN.get(node.get("domain_type"), "Integration")
    synthesized = node.get("template_source") == "synthesized"
    template_dir = f"{_SYNTHESIZED_DIR}/{node['capability_id']}" if synthesized else None
    anchor_text = "; ".join(anchors) if anchors else "(无锚点,按模板材料自证)"
    return {
        "story_schema_version": STORY_SCHEMA_VERSION,
        "story_id": f"story-{node['instance_id']}",
        "batch_id": batch_id,
        "story_kind": "capability",
        "capability_id": node["capability_id"],
        "instance_id": node["instance_id"],
        "evidence_class": evidence_class,
        "depends_on": [f"story-{d}" for d in node.get("dependencies", [])],
        "materials": {
            "gdd_path": paths["gdd_path"],
            "gdd_anchors": anchors,
            "contract_path": paths["contract_path"],
            "skill_graph_path": paths["skill_graph_path"],
            "template_id": node.get("template_id"),
            "template_source": node.get("template_source"),
            "template_dir": template_dir,
            "construction_manifest_path": paths["construction_manifest_path"],
            "extra_paths": [],
        },
        "acceptance_criteria": [
            "demo plugin 编译通过且既有冒烟用例不破(证据: smoke_report)",
            f"按 evidence_class={evidence_class} 提交全部必交证据并通过机器校验",
            f"实现范围对 GDD 锚点自证: {anchor_text}",
            "设计取舍零提问: 未定点给默认值并记入 provisional_decisions",
        ],
        "status": "pending",
        "attempts": 0,
        "manifest_version": manifest_version,
    }


def _doc_story(batch_id: str, member_ids: List[str], manifest_version: str,
               paths: Dict[str, Any]) -> Dict[str, Any]:
    """批末文档 story:功能 story 全 verified 后执行(spec §4.7,后置投影)。"""
    return {
        "story_schema_version": STORY_SCHEMA_VERSION,
        "story_id": f"story-{batch_id}-docs",
        "batch_id": batch_id,
        "story_kind": "documentation",
        "evidence_class": "Config",
        "depends_on": list(member_ids),
        "materials": {
            "gdd_path": paths["gdd_path"],
            "gdd_anchors": [],
            "contract_path": paths["contract_path"],
            "skill_graph_path": paths["skill_graph_path"],
            "template_id": None,
            "template_source": None,
            "template_dir": None,
            "construction_manifest_path": paths["construction_manifest_path"],
            "extra_paths": paths.get("doc_extra_paths", []),
        },
        "acceptance_criteria": [
            "维护文档包按施工规范 §文档 节写入 demo plugin 的 Docs/ 目录(设计/架构/changelog)",
            "文档只描述已 verified 的实现;结构性内容自 run 产物投影,头部标注生成物口径",
            "文档中引用的类/资产经机器引用对账存在",
        ],
        "status": "pending",
        "attempts": 0,
        "manifest_version": manifest_version,
    }


def build_demo_plan(skill_graph: Dict[str, Any], contract: Dict[str, Any],
                    manifest_version: str, paths: Dict[str, Any]) -> Dict[str, Any]:
    """纯函数:同输入同输出。返回 {"plan": demo_plan, "stories": [demo_story...]}。

    切批规则(通用,零领域语义):
    - v0 批 = template_source != "synthesized" 的全部节点
    - 每个 synthesized 节点(全图拓扑序)各自一个增量批
    - 批内 story 拓扑序;每批末尾追加文档 story
    """
    anchors = _anchor_map(contract)
    ordered_all = _topo_order(skill_graph["nodes"])
    library = [n for n in ordered_all if n.get("template_source") != "synthesized"]
    synthesized = [n for n in ordered_all if n.get("template_source") == "synthesized"]

    stories: List[Dict[str, Any]] = []
    batches: List[Dict[str, Any]] = []

    v0_members = []
    for node in _topo_order(library):
        story = _capability_story(node, "v0", anchors.get(node["capability_id"], []),
                                  manifest_version, paths)
        stories.append(story)
        v0_members.append(story["story_id"])
    doc = _doc_story("v0", v0_members, manifest_version, paths)
    stories.append(doc)
    batches.append({"batch_id": "v0", "story_ids": v0_members + [doc["story_id"]]})

    for idx, node in enumerate(synthesized, start=1):
        batch_id = f"increment-{idx}"
        story = _capability_story(node, batch_id, anchors.get(node["capability_id"], []),
                                  manifest_version, paths)
        doc = _doc_story(batch_id, [story["story_id"]], manifest_version, paths)
        stories.extend([story, doc])
        batches.append({"batch_id": batch_id, "story_ids": [story["story_id"], doc["story_id"]]})

    plan = {
        "plan_schema_version": PLAN_SCHEMA_VERSION,
        "run_id": skill_graph.get("metadata", {}).get("source_run_id", ""),
        "source_graph_id": skill_graph.get("graph_id", ""),
        "manifest_version": manifest_version,
        "batches": batches,
    }
    return {"plan": plan, "stories": stories}
