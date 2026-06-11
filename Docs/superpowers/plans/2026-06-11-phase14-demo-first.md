# Phase 14 Demo-First 增量主链 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 落地 demo_plan 切批环节 + story 状态机 + 证据校验 + 2 个 MCP 工具(55→57)+ 施工规范层 + 冒烟 runner + Stage 14 测试登记,使"GDD→可玩 v0→增量"主链具备无人值守执行的全部机制。

**Architecture:** 纯新增:`Plugins/AgentBridge/Compiler/demo_plan/` 四个自包含模块(planner/story_store/evidence_validator/velocity + manifest_loader),MCP 层组合它们暴露 `demo_story_fetch/submit` 两工具;Stage 1-7 既有代码零改动。切批确定性零 LLM,机制代码零游戏领域语义(测试守门)。

**Tech Stack:** Python 3.x + jsonschema + pytest;MCP server(既有);UE5.5 Automation commandlet(冒烟 runner)。

**Spec:** `Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md`
**分支:** 沿用 `feat/phase14-demo-first-spec`(Phase 13 先例:spec 分支即实现分支)。
**Commit 约定:** 实现期一律 `[skip-doc] feat(phase14): ...`,document-release 在阶段收尾统一跑(项目任务收尾流程)。
**测试运行目录:** 一律项目根 `D:\UnrealProjects\Mvpv4TestCodex`。

---

## 文件结构总览

| 动作 | 路径 | 职责 |
|---|---|---|
| Create | `Plugins/AgentBridge/Compiler/demo_plan/__init__.py` | 空包标记 |
| Create | `Plugins/AgentBridge/Compiler/demo_plan/planner.py` | 切批纯函数(skill_graph+契约→plan+stories) |
| Create | `Plugins/AgentBridge/Compiler/demo_plan/story_store.py` | story 状态机 + `.part` 事务落盘 + 重入 |
| Create | `Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py` | 证据分级校验 + hash 守门 + 文档引用对账 |
| Create | `Plugins/AgentBridge/Compiler/demo_plan/velocity.py` | velocity_log 追加器 |
| Create | `Plugins/AgentBridge/Compiler/demo_plan/manifest_loader.py` | 施工规范读取 + 版本解析 |
| Create | `Plugins/AgentBridge/Schemas/demo_plan.schema.json` + `demo_story.schema.json` | 契约 |
| Create | `Plugins/AgentBridge/Schemas/examples/phase14_demo_plan.example.json` + `phase14_demo_story.example.json` | strict 校验样例 |
| Create | `ProjectInputs/ConstructionManifest/demo_plugin_standards.md` | 施工规范 v1(项目层实例) |
| Create | `Plugins/AgentBridge/Scripts/demo_plan_main.py` | demo_plan 生成 CLI(runbook 驱动用) |
| Create | `Plugins/AgentBridge/Scripts/demo_smoke/runner.py` | 冒烟 runner(环境自检+commandlet+报告) |
| Create | `Plugins/AgentBridge/Tests/scripts/test_phase14_*.py`(6 个文件) | DMP-xx 用例 |
| Modify | `Plugins/AgentBridge/MCP/tool_definitions.py` | 两工具 schema + TOOL_COUNT 注释 55→57 |
| Modify | `Plugins/AgentBridge/MCP/server.py` | TOOL_DISPATCH 两行 |
| Modify | `Plugins/AgentBridge/MCP/compiler_tools.py` | 两工具实现 |
| Modify | `Plugins/AgentBridge/Scripts/validation/validate_examples.py` | EXAMPLE_TO_SCHEMA 两行 |
| Modify | `Plugins/AgentBridge/Tests/run_system_tests.py` | Stage 14 登记 |
| Create | `ProjectState/Reports/2026-06-11/phase14_acceptance_runbook.md` | 验收 runbook |

**红线提醒:** `AgentBridgeTests/`、`Scripts/bridge/*`、`Scripts/orchestrator/orchestrator.py` 等 CLAUDE.md"绝对不要修改"清单零触碰。本计划只 Modify 上表五个文件,全部在可改区。

---

### Task 1: demo_plan / demo_story schema + examples + strict 注册

**Files:**
- Create: `Plugins/AgentBridge/Schemas/demo_plan.schema.json`
- Create: `Plugins/AgentBridge/Schemas/demo_story.schema.json`
- Create: `Plugins/AgentBridge/Schemas/examples/phase14_demo_plan.example.json`
- Create: `Plugins/AgentBridge/Schemas/examples/phase14_demo_story.example.json`
- Modify: `Plugins/AgentBridge/Scripts/validation/validate_examples.py`(EXAMPLE_TO_SCHEMA 字典,约 59-127 行区间末尾)

- [ ] **Step 1: 写 demo_story.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "demo_story",
  "description": "Phase 14 demo-first:单条施工工单。materials 全部为路径指针(agent 读全文,零语义压缩)。",
  "type": "object",
  "additionalProperties": false,
  "required": ["story_schema_version", "story_id", "batch_id", "story_kind", "evidence_class",
               "depends_on", "materials", "acceptance_criteria", "status", "attempts", "manifest_version"],
  "properties": {
    "story_schema_version": {"type": "string", "description": "schema 版本"},
    "story_id": {"type": "string", "pattern": "^story-[a-z0-9-]+$", "description": "工单 id"},
    "batch_id": {"type": "string", "pattern": "^(v0|increment-[0-9]+)$", "description": "所属批次"},
    "story_kind": {"enum": ["capability", "documentation"], "description": "功能工单 / 批末文档工单"},
    "capability_id": {"type": "string", "description": "功能工单对应 capability(文档工单缺省)"},
    "instance_id": {"type": "string", "description": "skill graph 节点 id(功能工单)"},
    "evidence_class": {"enum": ["Logic", "Integration", "Visual", "Config"],
                       "description": "证据分级:决定 submit 必交证据"},
    "depends_on": {"type": "array", "items": {"type": "string"}, "description": "前置 story id(verified 后方可 fetch)"},
    "materials": {
      "type": "object", "additionalProperties": false,
      "required": ["gdd_path", "gdd_anchors", "contract_path", "skill_graph_path", "construction_manifest_path"],
      "properties": {
        "gdd_path": {"type": "string", "description": "GDD 原文路径"},
        "gdd_anchors": {"type": "array", "items": {"type": "string"}, "description": "本工单相关 GDD 锚点标题"},
        "contract_path": {"type": "string", "description": "root_skill_contract.json 路径"},
        "skill_graph_path": {"type": "string", "description": "skill_graph.json 路径"},
        "template_id": {"type": ["string", "null"], "description": "绑定模板 id(文档工单为 null)"},
        "template_source": {"type": ["string", "null"], "description": "plugin_skill_template / synthesized"},
        "template_dir": {"type": ["string", "null"], "description": "合成包目录(仅 synthesized 预解析,其余 null)"},
        "construction_manifest_path": {"type": "string", "description": "施工规范路径"},
        "extra_paths": {"type": "array", "items": {"type": "string"}, "description": "附加材料(文档工单:plan/velocity 等)"}
      }
    },
    "acceptance_criteria": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    "status": {"enum": ["pending", "in_progress", "submitted", "verified"]},
    "attempts": {"type": "integer", "minimum": 0, "description": "自修轮次(submit 被拒 +1)"},
    "manifest_version": {"type": "string", "description": "切批时施工规范版本(fetch 时对账)"},
    "submit_errors": {"type": "array", "items": {"type": "string"}, "description": "最近一次被拒的错误清单"},
    "evidence": {"type": "object", "description": "verified 时的最终证据载荷(透传存档)"}
  }
}
```

- [ ] **Step 2: 写 demo_plan.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "demo_plan",
  "description": "Phase 14 demo-first:批次计划。v0 批 = 全部库内绑定节点;每个合成节点一个增量批;批内拓扑序;每批末尾文档 story。",
  "type": "object",
  "additionalProperties": false,
  "required": ["plan_schema_version", "run_id", "source_graph_id", "manifest_version", "batches"],
  "properties": {
    "plan_schema_version": {"type": "string"},
    "run_id": {"type": "string"},
    "source_graph_id": {"type": "string", "description": "来源 skill_graph 的 graph_id"},
    "manifest_version": {"type": "string", "description": "切批时施工规范版本"},
    "batches": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["batch_id", "story_ids"],
        "properties": {
          "batch_id": {"type": "string", "pattern": "^(v0|increment-[0-9]+)$"},
          "story_ids": {"type": "array", "items": {"type": "string"}, "minItems": 1,
                        "description": "批内拓扑序,末位恒为文档 story"}
        }
      }
    }
  }
}
```

- [ ] **Step 3: 写两个 example**

`phase14_demo_story.example.json`(注意:示例值是数据不是机制,允许出现领域词):

```json
{
  "story_schema_version": "1.0.0",
  "story_id": "story-skill-board-topology",
  "batch_id": "v0",
  "story_kind": "capability",
  "capability_id": "gameplay-board-topology",
  "instance_id": "skill-board-topology",
  "evidence_class": "Logic",
  "depends_on": [],
  "materials": {
    "gdd_path": "ProjectInputs/GDD/monopoly_extended_auction_v1.md",
    "gdd_anchors": ["1. 游戏概述"],
    "contract_path": "ProjectState/runs/run-20260611-052252-5101/root_skill_contract.json",
    "skill_graph_path": "ProjectState/runs/run-20260611-052252-5101/skill_graph.json",
    "template_id": "monopoly.board_topology.phase1",
    "template_source": "plugin_skill_template",
    "template_dir": null,
    "construction_manifest_path": "ProjectInputs/ConstructionManifest/demo_plugin_standards.md",
    "extra_paths": []
  },
  "acceptance_criteria": [
    "demo plugin 编译通过且既有冒烟用例不破(证据: smoke_report)",
    "按 evidence_class=Logic 提交全部必交证据并通过机器校验",
    "实现范围对 GDD 锚点自证: 1. 游戏概述",
    "设计取舍零提问: 未定点给默认值并记入 provisional_decisions"
  ],
  "status": "pending",
  "attempts": 0,
  "manifest_version": "1.0.0"
}
```

`phase14_demo_plan.example.json`:

```json
{
  "plan_schema_version": "1.0.0",
  "run_id": "run-20260611-052252-5101",
  "source_graph_id": "graph-20260611-0001",
  "manifest_version": "1.0.0",
  "batches": [
    {"batch_id": "v0", "story_ids": ["story-skill-board-topology", "story-v0-docs"]},
    {"batch_id": "increment-1", "story_ids": ["story-skill-property-auction", "story-increment-1-docs"]}
  ]
}
```

- [ ] **Step 4: 注册进 strict 校验并验证失败→成功**

在 `validate_examples.py` 的 `EXAMPLE_TO_SCHEMA` 字典末尾添加:

```python
    # === Phase 14 demo-first 增量主链 ===
    "phase14_demo_plan.example.json": "demo_plan.schema.json",
    "phase14_demo_story.example.json": "demo_story.schema.json",
```

Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: `Checked examples : 30` / `Passed : 30`(28+2;若示例与 schema 不符会精确报错,修到全过)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Schemas/demo_plan.schema.json Plugins/AgentBridge/Schemas/demo_story.schema.json Plugins/AgentBridge/Schemas/examples/phase14_demo_plan.example.json Plugins/AgentBridge/Schemas/examples/phase14_demo_story.example.json Plugins/AgentBridge/Scripts/validation/validate_examples.py
git commit -m "[skip-doc] feat(phase14): demo_plan/demo_story schema + examples + strict 注册"
```

---

### Task 2: planner 切批核心(确定性,零领域语义)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/demo_plan/__init__.py`(空文件)
- Create: `Plugins/AgentBridge/Compiler/demo_plan/planner.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py`

- [ ] **Step 1: 写失败测试(DMP-01~10)**

```python
# -*- coding: utf-8 -*-
"""DMP-01~10: demo_plan 切批核心——拓扑序/批切分/文档 story/确定性/fail-closed。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    """动态加载 Compiler/demo_plan 下的自包含模块(与 test_phase13_* 同款模式)。"""
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _graph(nodes):
    return {"graph_version": "1.0", "graph_id": "graph-test-0001",
            "nodes": nodes, "edges": [], "metadata": {}}


def _node(iid, cap, domain="gameplay", deps=None, source="plugin_skill_template", template="tpl.x.v1"):
    return {"instance_id": iid, "capability_id": cap, "template_id": template,
            "domain_type": domain, "template_source": source,
            "dependencies": deps or [], "coupling": []}


def _contract(caps):
    """caps: [(capability_id, source_anchor)]。gameplay/baseline 容器各放一半足够测试。"""
    entries = [{"capability_id": c, "activation": "required", "source_anchor": a} for c, a in caps]
    return {"contract_id": "contract-test", "gameplay_capabilities": entries, "baseline_capabilities": []}


_PATHS = {
    "gdd_path": "ProjectInputs/GDD/x.md",
    "contract_path": "ProjectState/runs/r/root_skill_contract.json",
    "skill_graph_path": "ProjectState/runs/r/skill_graph.json",
    "construction_manifest_path": "ProjectInputs/ConstructionManifest/demo_plugin_standards.md",
}


class TestDemoPlanner:
    def test_dmp01_v0_batch_contains_all_library_nodes(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a"), _node("skill-b", "cap-b", deps=["skill-a"]),
                 _node("skill-s", "cap-s", source="synthesized")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-b", "S2"), ("cap-s", "S3")]),
                                "1.0.0", _PATHS)
        v0 = out["plan"]["batches"][0]
        assert v0["batch_id"] == "v0"
        assert "story-skill-a" in v0["story_ids"] and "story-skill-b" in v0["story_ids"]
        assert "story-skill-s" not in v0["story_ids"]

    def test_dmp02_each_synthesized_node_gets_own_increment_batch(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a"),
                 _node("skill-s1", "cap-s1", source="synthesized", deps=["skill-a"]),
                 _node("skill-s2", "cap-s2", source="synthesized", deps=["skill-a"])]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-s1", "S2"), ("cap-s2", "S3")]),
                                "1.0.0", _PATHS)
        ids = [b["batch_id"] for b in out["plan"]["batches"]]
        assert ids == ["v0", "increment-1", "increment-2"]

    def test_dmp03_batch_inner_topological_order(self):
        p = _load("planner")
        nodes = [_node("skill-b", "cap-b", deps=["skill-a"]), _node("skill-a", "cap-a")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-b", "S2")]), "1.0.0", _PATHS)
        sids = out["plan"]["batches"][0]["story_ids"]
        assert sids.index("story-skill-a") < sids.index("story-skill-b")

    def test_dmp04_doc_story_appended_last_per_batch(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a"), _node("skill-s", "cap-s", source="synthesized")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-s", "S2")]), "1.0.0", _PATHS)
        for batch in out["plan"]["batches"]:
            assert batch["story_ids"][-1] == f"story-{batch['batch_id']}-docs"
        doc = [s for s in out["stories"] if s["story_id"] == "story-v0-docs"][0]
        assert doc["story_kind"] == "documentation" and doc["evidence_class"] == "Config"
        assert set(doc["depends_on"]) == {"story-skill-a"}

    def test_dmp05_evidence_class_mapped_from_domain_type_only(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a", domain="gameplay"), _node("skill-h", "cap-h", domain="baseline")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "S1"), ("cap-h", "S2")]), "1.0.0", _PATHS)
        by_id = {s["story_id"]: s for s in out["stories"]}
        assert by_id["story-skill-a"]["evidence_class"] == "Logic"
        assert by_id["story-skill-h"]["evidence_class"] == "Visual"

    def test_dmp06_anchor_from_contract_into_materials(self):
        p = _load("planner")
        nodes = [_node("skill-a", "cap-a")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "2.1 某锚点")]), "1.0.0", _PATHS)
        story = out["stories"][0]
        assert story["materials"]["gdd_anchors"] == ["2.1 某锚点"]

    def test_dmp07_synthesized_template_dir_preresolved(self):
        p = _load("planner")
        nodes = [_node("skill-s", "cap-s", source="synthesized", template="synthesized.cap-s.v1")]
        out = p.build_demo_plan(_graph(nodes), _contract([("cap-s", "S")]), "1.0.0", _PATHS)
        story = [s for s in out["stories"] if s.get("instance_id") == "skill-s"][0]
        assert story["materials"]["template_dir"] == "Plugins/AgentBridge/SkillTemplates/synthesized/cap-s"

    def test_dmp08_deterministic_same_input_same_output(self):
        p = _load("planner")
        nodes = [_node("skill-b", "cap-b"), _node("skill-a", "cap-a"), _node("skill-c", "cap-c")]
        a = p.build_demo_plan(_graph(nodes), _contract([("cap-a", "1"), ("cap-b", "2"), ("cap-c", "3")]), "1.0.0", _PATHS)
        b = p.build_demo_plan(_graph(list(reversed(nodes))), _contract([("cap-c", "3"), ("cap-a", "1"), ("cap-b", "2")]), "1.0.0", _PATHS)
        assert a == b

    def test_dmp09_cycle_fails_closed(self):
        p = _load("planner")
        import pytest
        nodes = [_node("skill-a", "cap-a", deps=["skill-b"]), _node("skill-b", "cap-b", deps=["skill-a"])]
        with pytest.raises(ValueError):
            p.build_demo_plan(_graph(nodes), _contract([("cap-a", "1"), ("cap-b", "2")]), "1.0.0", _PATHS)

    def test_dmp10_manifest_version_stamped_on_plan_and_stories(self):
        p = _load("planner")
        out = p.build_demo_plan(_graph([_node("skill-a", "cap-a")]), _contract([("cap-a", "1")]), "9.9.9", _PATHS)
        assert out["plan"]["manifest_version"] == "9.9.9"
        assert all(s["manifest_version"] == "9.9.9" for s in out["stories"])
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -v`
Expected: 10 failed(`FileNotFoundError`/`ModuleNotFoundError`,planner.py 不存在)

- [ ] **Step 3: 实现 planner.py**

```python
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
```

同时创建空的 `Plugins/AgentBridge/Compiler/demo_plan/__init__.py`(单行中文注释:`# demo_plan:Phase 14 demo-first 切批与 story 机制(自包含模块,模块间不互相 import)`)。

- [ ] **Step 4: 确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -v`
Expected: 10 passed

注意 `test_dmp01` 里 `plan["run_id"]` 为空串(测试 graph 无 metadata.source_run_id)是预期行为;CLI(Task 8)会从真实 graph 取到。

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/__init__.py Plugins/AgentBridge/Compiler/demo_plan/planner.py Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py
git commit -m "[skip-doc] feat(phase14): demo_plan 切批核心——拓扑序/批切分/文档story/确定性"
```

---

### Task 3: 防固化机器检查(机制零游戏语义)

**Files:**
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase14_no_domain_semantics.py`

- [ ] **Step 1: 写测试(DMP-11~12)**

```python
# -*- coding: utf-8 -*-
"""DMP-11~12: 防固化守则机器化——demo_plan 机制代码与 MCP 工具实现零游戏领域语义。

检查对象是机制源码;schema example、测试夹具、施工规范实例(项目层)不在范围内。
"""
import re
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

# 领域词黑名单:来自既有 GDD/模板的游戏语义词根(小写比对)
_DOMAIN_WORDS = re.compile(
    r"monopoly|auction|stock|jrpg|dice|board|tile|jail|property|economy|turn[_ ]?loop",
    re.IGNORECASE,
)

_MECHANISM_FILES = [
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "planner.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "story_store.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "evidence_validator.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "velocity.py",
    PLUGIN_ROOT / "Compiler" / "demo_plan" / "manifest_loader.py",
]


class TestNoDomainSemantics:
    def test_dmp11_demo_plan_modules_free_of_domain_words(self):
        for path in _MECHANISM_FILES:
            if not path.exists():
                continue  # 后续 task 才创建的模块,创建后自动纳入扫描
            hits = _DOMAIN_WORDS.findall(path.read_text(encoding="utf-8"))
            assert not hits, f"{path.name} 含游戏领域词(防固化违规): {sorted(set(hits))}"

    def test_dmp12_mcp_demo_tool_impl_free_of_domain_words(self):
        src = (PLUGIN_ROOT / "MCP" / "compiler_tools.py").read_text(encoding="utf-8")
        # 只扫描 Phase 14 两个工具函数体(文件其余部分属 Phase 13 既有范围)
        match = re.search(r"def demo_story_fetch.*?(?=\ndef [a-z]|\Z)", src, re.DOTALL)
        if match is None:
            return  # 工具尚未实现(Task 7),实现后自动生效
        segment = src[match.start():]
        hits = _DOMAIN_WORDS.findall(segment)
        assert not hits, f"MCP demo 工具实现含游戏领域词: {sorted(set(hits))}"
```

- [ ] **Step 2: 运行确认通过(planner 已满足)**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_no_domain_semantics.py -v`
Expected: 2 passed(若 planner.py 哪个注释里写了领域词,此处会抓出来,改注释)

- [ ] **Step 3: Commit**

```bash
git add Plugins/AgentBridge/Tests/scripts/test_phase14_no_domain_semantics.py
git commit -m "[skip-doc] test(phase14): 防固化守则机器化——机制代码零游戏语义扫描"
```

---

### Task 4: story_store 状态机 + velocity log

**Files:**
- Create: `Plugins/AgentBridge/Compiler/demo_plan/story_store.py`
- Create: `Plugins/AgentBridge/Compiler/demo_plan/velocity.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase14_story_store.py`

- [ ] **Step 1: 写失败测试(DMP-13~20)**

```python
# -*- coding: utf-8 -*-
"""DMP-13~20: story 状态机——fetch/submit 流转、依赖门、幂等重入、.part 事务、velocity。"""
import importlib.util
import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _story(sid, deps=None, status="pending"):
    return {"story_schema_version": "1.0.0", "story_id": sid, "batch_id": "v0",
            "story_kind": "capability", "capability_id": f"cap-{sid}", "instance_id": sid,
            "evidence_class": "Logic", "depends_on": deps or [],
            "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                          "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                          "template_dir": None, "construction_manifest_path": "m.md", "extra_paths": []},
            "acceptance_criteria": ["x"], "status": status, "attempts": 0, "manifest_version": "1.0.0"}


@pytest.fixture
def run_dir(workspace_tmp_path):
    """构造假 run 目录:demo_plan.json + stories/。"""
    stories = [_story("story-a"), _story("story-b", deps=["story-a"])]
    plan = {"plan_schema_version": "1.0.0", "run_id": "run-test", "source_graph_id": "g",
            "manifest_version": "1.0.0",
            "batches": [{"batch_id": "v0", "story_ids": ["story-a", "story-b"]}]}
    (workspace_tmp_path / "stories").mkdir()
    (workspace_tmp_path / "demo_plan.json").write_text(
        json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    for s in stories:
        (workspace_tmp_path / "stories" / f"{s['story_id']}.json").write_text(
            json.dumps(s, ensure_ascii=False), encoding="utf-8")
    return workspace_tmp_path


class TestStoryStore:
    def test_dmp13_fetch_next_respects_plan_order_and_deps(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        story = store.fetch(None)
        assert story["story_id"] == "story-a" and story["status"] == "in_progress"

    def test_dmp14_dependent_story_blocked_until_dep_verified(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        with pytest.raises(ValueError, match="前置"):
            store.fetch("story-b")

    def test_dmp15_fetch_in_progress_is_idempotent_reentry(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        first = store.fetch(None)
        again = store.fetch(first["story_id"])
        assert again["status"] == "in_progress" and again["attempts"] == first["attempts"]

    def test_dmp16_submit_pass_marks_verified_and_archives_evidence(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        out = store.submit("story-a", {"files_changed": ["x.cpp"]},
                           {"status": "verified", "errors": []})
        assert out["status"] == "verified"
        on_disk = json.loads((run_dir / "stories" / "story-a.json").read_text(encoding="utf-8"))
        assert on_disk["status"] == "verified" and on_disk["evidence"] == {"files_changed": ["x.cpp"]}

    def test_dmp17_submit_reject_returns_in_progress_and_bumps_attempts(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        out = store.submit("story-a", {}, {"status": "rejected", "errors": ["缺 smoke_report"]})
        assert out["status"] == "in_progress" and out["attempts"] == 1
        assert out["submit_errors"] == ["缺 smoke_report"]

    def test_dmp18_verified_unlocks_dependent(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        store.submit("story-a", {"files_changed": []}, {"status": "verified", "errors": []})
        nxt = store.fetch(None)
        assert nxt["story_id"] == "story-b"

    def test_dmp19_atomic_write_no_part_residue(self, run_dir):
        ss = _load("story_store")
        store = ss.StoryStore(run_dir)
        store.fetch(None)
        assert not list((run_dir / "stories").glob("*.part"))

    def test_dmp20_velocity_appends_fetch_and_submit_events(self, run_dir):
        ss = _load("story_store")
        vel = _load("velocity")
        store = ss.StoryStore(run_dir)
        story = store.fetch(None)
        vel.append_event(run_dir, {"kind": "fetch", "story_id": story["story_id"]})
        vel.append_event(run_dir, {"kind": "submit", "story_id": story["story_id"], "result": "verified"})
        log = json.loads((run_dir / "velocity_log.json").read_text(encoding="utf-8"))
        assert [e["kind"] for e in log["events"]] == ["fetch", "submit"]
        assert all("ts" in e for e in log["events"])
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_story_store.py -v`
Expected: 8 failed(story_store.py 不存在)

- [ ] **Step 3: 实现 story_store.py 与 velocity.py**

`story_store.py`:

```python
# -*- coding: utf-8 -*-
"""story 状态机:pending → in_progress → submitted → verified;被拒回 in_progress。

落盘约定:每个 story 一个 JSON(ProjectState/runs/<run_id>/stories/<story_id>.json),
写入一律 .part 临时文件 + os.replace 原子替换(Phase 13 合成链同款事务形状)。
本模块零游戏领域语义;不 import 包内其他模块(自包含,经 importlib 单文件加载友好)。
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


class StoryStore:
    def __init__(self, run_dir) -> None:
        self.run_dir = Path(run_dir)
        self.stories_dir = self.run_dir / "stories"
        self.plan_path = self.run_dir / "demo_plan.json"

    # ---- 基础 IO ----
    def _plan(self) -> Dict[str, Any]:
        return json.loads(self.plan_path.read_text(encoding="utf-8"))

    def _ordered_ids(self) -> List[str]:
        """全局顺序 = 批次序 × 批内序(plan 文件是唯一顺序权威)。"""
        return [sid for b in self._plan()["batches"] for sid in b["story_ids"]]

    def load(self, story_id: str) -> Dict[str, Any]:
        path = self.stories_dir / f"{story_id}.json"
        if not path.exists():
            raise ValueError(f"story 不存在: {story_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _write(self, story: Dict[str, Any]) -> None:
        path = self.stories_dir / f"{story['story_id']}.json"
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(story, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    # ---- 状态查询 ----
    def _deps_verified(self, story: Dict[str, Any]) -> bool:
        return all(self.load(d)["status"] == "verified" for d in story.get("depends_on", []))

    def next_available(self) -> Optional[Dict[str, Any]]:
        """plan 顺序上第一个 pending 且前置全 verified 的 story。"""
        for sid in self._ordered_ids():
            story = self.load(sid)
            if story["status"] == "pending" and self._deps_verified(story):
                return story
        return None

    # ---- 状态流转 ----
    def fetch(self, story_id: Optional[str]) -> Dict[str, Any]:
        """story_id 为空取下一个可发工单;in_progress 可幂等重入(断点续作);verified 拒发。"""
        if story_id is None:
            story = self.next_available()
            if story is None:
                raise ValueError("没有可发的 story(全部完成或被前置阻塞)")
        else:
            story = self.load(story_id)
        if story["status"] == "verified":
            raise ValueError(f"story 已 verified,不可重发: {story['story_id']}")
        if story["status"] == "pending":
            if not self._deps_verified(story):
                raise ValueError(f"前置 story 未全部 verified: {story['story_id']}")
            story["status"] = "in_progress"
            self._write(story)
        return story

    def submit(self, story_id: str, evidence: Dict[str, Any],
               validation: Dict[str, Any]) -> Dict[str, Any]:
        """validation 是 evidence_validator.validate_evidence 的结果(机制分离:store 只管状态)。"""
        story = self.load(story_id)
        if story["status"] not in ("in_progress", "submitted"):
            raise ValueError(f"story 状态不允许 submit: {story['status']}")
        if validation["status"] == "verified":
            story["status"] = "verified"
            story["evidence"] = evidence
            story["submit_errors"] = []
        else:
            story["status"] = "in_progress"
            story["attempts"] = int(story.get("attempts", 0)) + 1
            story["submit_errors"] = list(validation.get("errors", []))
        self._write(story)
        return story
```

`velocity.py`:

```python
# -*- coding: utf-8 -*-
"""velocity log:逐 story、逐自修轮的时间戳事件流(Phase 15 扇出成本估算的实测依据)。"""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


def append_event(run_dir, event: Dict[str, Any]) -> None:
    """追加一条事件(自动盖 UTC 时间戳),.part 原子写。"""
    path = Path(run_dir) / "velocity_log.json"
    log = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"events": []}
    stamped = dict(event)
    stamped["ts"] = datetime.now(timezone.utc).isoformat()
    log["events"].append(stamped)
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
```

- [ ] **Step 4: 确认通过(含防固化扫描自动纳入新模块)**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_story_store.py Plugins/AgentBridge/Tests/scripts/test_phase14_no_domain_semantics.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/story_store.py Plugins/AgentBridge/Compiler/demo_plan/velocity.py Plugins/AgentBridge/Tests/scripts/test_phase14_story_store.py
git commit -m "[skip-doc] feat(phase14): story 状态机+velocity log——依赖门/幂等重入/.part 事务"
```

---

### Task 5: evidence_validator(分级校验/hash 守门/文档引用对账)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py`

- [ ] **Step 1: 写失败测试(DMP-21~30)**

```python
# -*- coding: utf-8 -*-
"""DMP-21~30: 证据校验——分级必交/路径存在/冒烟 pass/增量 hash 守门/文档引用对账。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _story(ec="Logic", batch="v0", kind="capability"):
    return {"story_id": "story-x", "batch_id": batch, "story_kind": kind, "evidence_class": ec}


def _touch(root, rel, content="x"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return rel


def _smoke(root, status="pass", v0reg="n/a"):
    return _touch(root, "smoke_report.json",
                  json.dumps({"status": status, "v0_regression": v0reg, "suites": []}))


class TestEvidenceValidator:
    def test_dmp21_logic_requires_test_and_smoke(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        out = ev.validate_evidence(_story("Logic"), {"files_changed": []}, workspace_tmp_path)
        assert out["status"] == "rejected"
        assert any("test_report" in e for e in out["errors"]) and any("smoke_report" in e for e in out["errors"])

    def test_dmp22_visual_requires_screenshots(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        out = ev.validate_evidence(_story("Visual"), {"files_changed": []}, workspace_tmp_path)
        assert out["status"] == "rejected" and any("screenshots" in e for e in out["errors"])

    def test_dmp23_referenced_paths_must_exist(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": ["ghost.cpp"], "test_report": "no.json", "smoke_report": "no2.json"}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out["status"] == "rejected" and any("ghost.cpp" in e for e in out["errors"])

    def test_dmp24_smoke_report_must_be_pass(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, status="fail")}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out["status"] == "rejected" and any("smoke" in e for e in out["errors"])

    def test_dmp25_logic_happy_path_verified(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path)}
        out = ev.validate_evidence(_story("Logic"), evidence, workspace_tmp_path)
        assert out == {"status": "verified", "errors": []}

    def test_dmp26_increment_requires_baseline(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, v0reg="pass")}
        out = ev.validate_evidence(_story("Logic", batch="increment-1"), evidence,
                                   workspace_tmp_path, baseline=None)
        assert out["status"] == "rejected" and any("baseline" in e.lower() for e in out["errors"])

    def test_dmp27_increment_hash_guard_detects_tampering(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        rel = _touch(workspace_tmp_path, "Plugins/DemoX/SmokeTest.cpp", "original")
        baseline = ev.freeze_v0_baseline(workspace_tmp_path, workspace_tmp_path, [rel])
        (workspace_tmp_path / rel).write_text("tampered", encoding="utf-8")
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, v0reg="pass")}
        out = ev.validate_evidence(_story("Logic", batch="increment-1"), evidence,
                                   workspace_tmp_path, baseline=baseline)
        assert out["status"] == "rejected" and any("hash" in e.lower() for e in out["errors"])

    def test_dmp28_increment_requires_v0_regression_pass(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        rel = _touch(workspace_tmp_path, "Plugins/DemoX/SmokeTest.cpp")
        baseline = ev.freeze_v0_baseline(workspace_tmp_path, workspace_tmp_path, [rel])
        evidence = {"files_changed": [_touch(workspace_tmp_path, "a.cpp")],
                    "test_report": _touch(workspace_tmp_path, "t.json", "{}"),
                    "smoke_report": _smoke(workspace_tmp_path, v0reg="fail")}
        out = ev.validate_evidence(_story("Logic", batch="increment-1"), evidence,
                                   workspace_tmp_path, baseline=baseline)
        assert out["status"] == "rejected" and any("v0" in e for e in out["errors"])

    def test_dmp29_doc_story_reference_check(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        plugin = workspace_tmp_path / "Plugins" / "DemoX"
        _touch(workspace_tmp_path, "Plugins/DemoX/Source/DemoX/Core.h", "class ADemoActor {};")
        doc = _touch(workspace_tmp_path, "Plugins/DemoX/Docs/arch.md",
                     "架构含 `ADemoActor` 与 `AGhostActor`。")
        evidence = {"files_changed": [doc], "doc_paths": [doc]}
        out = ev.validate_evidence(_story("Config", kind="documentation"), evidence,
                                   workspace_tmp_path, plugin_root=plugin)
        assert out["status"] == "rejected"
        assert any("AGhostActor" in e for e in out["errors"])
        assert not any("ADemoActor" in e for e in out["errors"])

    def test_dmp30_freeze_baseline_writes_sha256_file(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        rel = _touch(workspace_tmp_path, "s.cpp", "abc")
        baseline = ev.freeze_v0_baseline(workspace_tmp_path, workspace_tmp_path, [rel])
        on_disk = json.loads((workspace_tmp_path / "v0_smoke_baseline.json").read_text(encoding="utf-8"))
        assert on_disk == baseline and rel.replace("\\", "/") in on_disk["files"]
        assert len(list(on_disk["files"].values())[0]) == 64
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py -v`
Expected: 10 failed

- [ ] **Step 3: 实现 evidence_validator.py**

```python
# -*- coding: utf-8 -*-
"""证据校验器:evidence_class 分级必交、路径存在、冒烟 pass、增量 hash 守门、文档引用对账。

机制分离:本模块只产出 {"status","errors"},状态流转归 story_store。
零游戏领域语义;自包含(不 import 包内其他模块)。
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# evidence_class → 必交证据字段(spec §4.2/§4.3)
REQUIRED_EVIDENCE = {
    "Logic": ("files_changed", "test_report", "smoke_report"),
    "Integration": ("files_changed", "smoke_report"),
    "Visual": ("files_changed", "screenshots"),
    "Config": ("files_changed", "doc_paths"),
}

# 路径型证据字段(逐一检查相对 project_root 存在)
_PATH_FIELDS = ("files_changed", "test_report", "smoke_report", "screenshots", "doc_paths")

# 文档引用对账:反引号包裹的 UE 类名(A/U/F/E 前缀大驼峰)与资产路径
_CLASS_TOKEN = re.compile(r"`([AUFE][A-Z][A-Za-z0-9_]{2,})`")
_ASSET_TOKEN = re.compile(r"`(/[A-Za-z0-9_]+(?:/[A-Za-z0-9_.]+)+)`")


def _iter_paths(evidence: Dict[str, Any]):
    for field in _PATH_FIELDS:
        value = evidence.get(field)
        if value is None:
            continue
        for item in (value if isinstance(value, list) else [value]):
            yield field, str(item)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_v0_baseline(project_root, run_dir, smoke_file_rel_paths: List[str]) -> Dict[str, Any]:
    """v0 PROCEED 后冻结冒烟用例 hash 基线,落盘 run 目录(人审窗口 1 的 runbook 步骤调用)。"""
    root = Path(project_root)
    files = {str(rel).replace("\\", "/"): _sha256(root / rel) for rel in smoke_file_rel_paths}
    baseline = {"files": files, "frozen_at": datetime.now(timezone.utc).isoformat()}
    path = Path(run_dir) / "v0_smoke_baseline.json"
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return baseline


def _check_baseline(project_root: Path, baseline: Dict[str, Any]) -> List[str]:
    errors = []
    for rel, expected in baseline.get("files", {}).items():
        target = project_root / rel
        if not target.exists():
            errors.append(f"hash 守门: 基线文件缺失 {rel}")
        elif _sha256(target) != expected:
            errors.append(f"hash 守门: 基线文件被修改 {rel}(v0 冒烟用例 PROCEED 后冻结,不许动)")
    return errors


def _check_doc_references(doc_text: str, plugin_root: Path) -> List[str]:
    """文档提到的类/资产必须真实存在(spec §4.7 引用对账)。"""
    errors: List[str] = []
    source_dir = plugin_root / "Source"
    corpus = ""
    if source_dir.exists():
        for ext in ("*.h", "*.cpp"):
            for f in sorted(source_dir.rglob(ext)):
                corpus += f.read_text(encoding="utf-8", errors="ignore")
    for cls in sorted(set(_CLASS_TOKEN.findall(doc_text))):
        if not any(marker + cls in corpus for marker in ("class ", "struct ", "enum class ")):
            errors.append(f"文档引用对账: 类 {cls} 在 plugin Source 中不存在")
    for asset in sorted(set(_ASSET_TOKEN.findall(doc_text))):
        parts = asset.strip("/").split("/")
        rel = Path(*parts[1:]) if len(parts) > 1 else Path(parts[0])
        candidates = [(plugin_root / "Content" / rel).with_suffix(suffix) for suffix in (".uasset", ".umap")]
        if not any(c.exists() for c in candidates):
            errors.append(f"文档引用对账: 资产 {asset} 在 plugin Content 中不存在")
    return errors


def validate_evidence(story: Dict[str, Any], evidence: Dict[str, Any], project_root,
                      baseline: Optional[Dict[str, Any]] = None,
                      plugin_root=None) -> Dict[str, Any]:
    """返回 {"status": "verified"|"rejected", "errors": [...]};错误信息具体可执行(重试闭环)。"""
    root = Path(project_root)
    errors: List[str] = []

    for field in REQUIRED_EVIDENCE[story["evidence_class"]]:
        if evidence.get(field) is None:
            errors.append(f"缺少必交证据字段: {field}(evidence_class={story['evidence_class']})")

    for field, rel in _iter_paths(evidence):
        if not (root / rel).exists():
            errors.append(f"证据路径不存在: {field} -> {rel}")

    smoke_rel = evidence.get("smoke_report")
    if smoke_rel and (root / str(smoke_rel)).exists():
        try:
            report = json.loads((root / str(smoke_rel)).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            report = None
            errors.append(f"smoke_report 不可解析: {exc}")
        if report is not None:
            if report.get("status") != "pass":
                errors.append(f"smoke_report 状态非 pass: {report.get('status')}")
            if str(story.get("batch_id", "")).startswith("increment") and report.get("v0_regression") != "pass":
                errors.append(f"增量批要求 v0 回归 pass,实际: {report.get('v0_regression')}")

    if str(story.get("batch_id", "")).startswith("increment"):
        if baseline is None:
            errors.append("增量批必须提供 v0 baseline(先在人审窗口 1 冻结)")
        else:
            errors.extend(_check_baseline(root, baseline))

    if story.get("story_kind") == "documentation":
        if plugin_root is None:
            errors.append("文档 story 校验需要 plugin_root")
        else:
            for rel in evidence.get("doc_paths") or []:
                doc_path = root / str(rel)
                if doc_path.exists():
                    errors.extend(_check_doc_references(
                        doc_path.read_text(encoding="utf-8", errors="ignore"), Path(plugin_root)))

    return {"status": "verified" if not errors else "rejected", "errors": errors}
```

- [ ] **Step 4: 确认通过(连防固化扫描)**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py Plugins/AgentBridge/Tests/scripts/test_phase14_no_domain_semantics.py -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py
git commit -m "[skip-doc] feat(phase14): 证据校验器——分级必交/hash 守门/文档引用对账"
```

---

### Task 6: 施工规范 v1 + manifest_loader

**Files:**
- Create: `ProjectInputs/ConstructionManifest/demo_plugin_standards.md`
- Create: `Plugins/AgentBridge/Compiler/demo_plan/manifest_loader.py`
- Test: 并入 `test_phase14_demo_plan.py`(追加 DMP-31~32)

- [ ] **Step 1: 写施工规范 v1(项目层实例,允许领域词)**

```markdown
manifest_version: 1.0.0

# Demo Plugin 施工规范(construction manifest)v1

> 消费者:实施 demo story 的 coding agent(经 demo_story_fetch 全文下发)。
> 本文件是项目层实例;版本变更时递增顶部 manifest_version,story 携带切批时版本,fetch 不符告警。

## 1. Plugin 骨架

- 每个 demo = 一个自包含 runtime plugin:`Plugins/<PluginName>/`(名称由 demo_plan 派生,见 story 材料)
- 必含:`<PluginName>.uplugin`(Type=Runtime)、`Source/<PluginName>/`(模块同名)、`Content/`、`Docs/`、`README.md`
- Build.cs 依赖白名单:Core、CoreUObject、Engine、InputCore、UMG、Slate、SlateCore;新增依赖须在 provisional_decisions 留痕
- **禁止依赖**:`Source/Mvpv4TestCodex` 主模块的任何类(MMonopoly*、MBoardManager、MDice 等)——include 或模块依赖均算违规

## 2. C++ 编码约束(UE5.5)

- UObject 指针一律 `TObjectPtr<>`;容器用 TArray/TMap/TSet;禁 new/delete 管理 UObject
- 反射宏齐全:UPROPERTY/UFUNCTION/UCLASS,带中文注释说明用途
- 禁热路径(Tick/逐帧)字符串拼接与查找;非必要不开 Tick(默认 PrimaryActorTick.bCanEverTick=false)
- 命名:A 前缀 Actor、U 前缀 UObject/组件、F 前缀结构、E 前缀枚举;文件名与类名一致
- 注释一律中文;只解释"为什么",不复述代码

## 3. 架构分层

- GameMode:规则裁决与流程推进(回合推进、胜负判定入口)
- GameState:全量可复制游戏状态(玩家/资源/棋盘态),冒烟测试经 GameState API 直驱
- 玩家交互走 PlayerController;UI 为 UMG Widget,只读 GameState、只发意图,不持有规则
- **规则参数一律数据驱动**:数值/配置进 DataAsset 或 DataTable(Content/Data/),C++ 不许硬编码可调参数——这是增量与扇出的留缝

## 4. 冒烟用例(随 demo 交付)

- 放 `Source/<PluginName>/Private/Tests/`,UE Automation Test 框架,名字空间 `<PluginName>.Smoke`
- v0 必含:一局从开始驱动到终局(经 GameState API,不走 UI 点击)零报错;widget 创建冒烟
- v0 经 msc PROCEED 后用例冻结(hash 守门),增量批只许新增用例文件,不许改既有

## 5. Provisional 决策留痕

- GDD 未规定的设计点:给默认值继续,不许停下提问
- 每条记入 submit 载荷 provisional_decisions:{"decision": 内容, "rationale": 依据, "scope": 影响面}

## 6. 文档(批末文档 story 产出)

- 落 `Plugins/<PluginName>/Docs/`:design.md(系统总览+决策含 provisional)、architecture.md(模块/类职责/数据资产/扩展点)、changelog.md(逐批追加)
- README.md(plugin 根):试玩入口地图、操作方式、一局预期流程、provisional 摘要
- 文档头部标注:"生成物,与 ProjectState/runs/<run_id> 数据不一致时以数据为准"
- 文档中类名/资产路径用反引号包裹(机器引用对账依赖此约定)
```

- [ ] **Step 2: 在 test_phase14_demo_plan.py 追加 DMP-31~32 并确认失败**

```python
class TestManifestLoader:
    def test_dmp31_load_manifest_text_and_version(self, project_root):
        ml = _load("manifest_loader")
        text, version = ml.load_construction_manifest(project_root)
        assert version == "1.0.0" and "Plugin 骨架" in text

    def test_dmp32_missing_version_line_fails_closed(self, workspace_tmp_path):
        ml = _load("manifest_loader")
        bad = workspace_tmp_path / "m.md"
        bad.write_text("# 无版本行", encoding="utf-8")
        import pytest
        with pytest.raises(ValueError, match="manifest_version"):
            ml.load_construction_manifest(workspace_tmp_path, path=bad)
```

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -k dmp31 or dmp32 -v` → 2 failed

- [ ] **Step 3: 实现 manifest_loader.py**

```python
# -*- coding: utf-8 -*-
"""施工规范读取:全文 + 版本号(首部 manifest_version 行),fetch 载荷注入用。零领域语义。"""
import re
from pathlib import Path
from typing import Optional, Tuple

DEFAULT_MANIFEST_REL = Path("ProjectInputs") / "ConstructionManifest" / "demo_plugin_standards.md"
_VERSION_LINE = re.compile(r"^manifest_version:\s*([0-9][0-9.]*)\s*$", re.MULTILINE)


def load_construction_manifest(project_root, path: Optional[Path] = None) -> Tuple[str, str]:
    """返回 (全文, 版本)。无版本行 fail-closed(规范文件必须可对账)。"""
    target = Path(path) if path else Path(project_root) / DEFAULT_MANIFEST_REL
    text = target.read_text(encoding="utf-8")
    match = _VERSION_LINE.search(text)
    if not match:
        raise ValueError(f"施工规范缺 manifest_version 行: {target}")
    return text, match.group(1)
```

- [ ] **Step 4: 确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py Plugins/AgentBridge/Tests/scripts/test_phase14_no_domain_semantics.py -v`
Expected: 14 passed(12+2;注意 conftest 已有 `project_root` fixture)

- [ ] **Step 5: Commit**

```bash
git add ProjectInputs/ConstructionManifest/demo_plugin_standards.md Plugins/AgentBridge/Compiler/demo_plan/manifest_loader.py Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py
git commit -m "[skip-doc] feat(phase14): 施工规范 v1 + manifest_loader——版本对账 fail-closed"
```

---

### Task 7: MCP 工具对(demo_story_fetch / demo_story_submit,55→57)

**Files:**
- Modify: `Plugins/AgentBridge/MCP/tool_definitions.py`(COMPILER_FRONTEND_TOOLS 字典末尾 + 第 546-548 行 TOOL_COUNT 注释)
- Modify: `Plugins/AgentBridge/MCP/server.py`(TOOL_DISPATCH,约 805 行区域)
- Modify: `Plugins/AgentBridge/MCP/compiler_tools.py`(文件末尾追加两函数)
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py`

- [ ] **Step 1: 写失败测试(DMP-33~38)**

```python
# -*- coding: utf-8 -*-
"""DMP-33~38: MCP 工具对——注册三处齐全、fetch 载荷、submit 校验闭环、工具数 57。"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _import_mcp(name):
    """以包内文件方式加载 MCP 模块(镜像既有 test_phase13 MCP 测试的加载方式;
    若 conftest 已提供加载 helper,改用之)。"""
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "MCP" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _seed_run(tmp, manifest_root):
    """假 run 目录 + 假施工规范。"""
    story = {"story_schema_version": "1.0.0", "story_id": "story-a", "batch_id": "v0",
             "story_kind": "capability", "capability_id": "cap-a", "instance_id": "skill-a",
             "evidence_class": "Config", "depends_on": [],
             "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                           "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                           "template_dir": None, "construction_manifest_path": "m.md", "extra_paths": []},
             "acceptance_criteria": ["x"], "status": "pending", "attempts": 0,
             "manifest_version": "1.0.0"}
    plan = {"plan_schema_version": "1.0.0", "run_id": "run-test", "source_graph_id": "g",
            "manifest_version": "1.0.0",
            "batches": [{"batch_id": "v0", "story_ids": ["story-a"]}]}
    (tmp / "stories").mkdir(parents=True)
    (tmp / "demo_plan.json").write_text(json.dumps(plan), encoding="utf-8")
    (tmp / "stories" / "story-a.json").write_text(json.dumps(story), encoding="utf-8")
    mdir = manifest_root / "ProjectInputs" / "ConstructionManifest"
    mdir.mkdir(parents=True, exist_ok=True)
    (mdir / "demo_plugin_standards.md").write_text(
        "manifest_version: 1.0.0\n# 规范\n", encoding="utf-8")


class TestMcpDemoTools:
    def test_dmp33_tool_definitions_registered(self):
        td = _import_mcp("tool_definitions")
        assert "demo_story_fetch" in td.COMPILER_FRONTEND_TOOLS
        assert "demo_story_submit" in td.COMPILER_FRONTEND_TOOLS

    def test_dmp34_tool_count_is_57(self):
        td = _import_mcp("tool_definitions")
        assert td.TOOL_COUNT == 57

    def test_dmp35_server_dispatch_has_both(self):
        src = (PLUGIN_ROOT / "MCP" / "server.py").read_text(encoding="utf-8")
        assert '"demo_story_fetch"' in src and '"demo_story_submit"' in src

    def test_dmp36_fetch_returns_story_and_manifest(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        out = ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                                  project_root=str(workspace_tmp_path))
        assert out["success"] is True
        assert out["data"]["story"]["story_id"] == "story-a"
        assert "manifest_version: 1.0.0" in out["data"]["construction_manifest"]
        assert out["data"]["manifest_warning"] is None

    def test_dmp37_submit_reject_then_pass_loop(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                            project_root=str(workspace_tmp_path))
        bad = ct.demo_story_submit(session_path=str(workspace_tmp_path), story_id="story-a",
                                   evidence={}, project_root=str(workspace_tmp_path))
        assert bad["success"] is True and bad["data"]["story_status"] == "in_progress"
        assert bad["data"]["errors"]
        doc = workspace_tmp_path / "Plugins" / "DemoX" / "Docs" / "d.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("无引用", encoding="utf-8")
        rel = str(doc.relative_to(workspace_tmp_path)).replace("\\", "/")
        good = ct.demo_story_submit(session_path=str(workspace_tmp_path), story_id="story-a",
                                    evidence={"files_changed": [rel], "doc_paths": [rel],
                                              "plugin_root": "Plugins/DemoX"},
                                    project_root=str(workspace_tmp_path))
        assert good["data"]["story_status"] == "verified"

    def test_dmp38_fetch_manifest_version_mismatch_warns(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        _seed_run(workspace_tmp_path, workspace_tmp_path)
        mpath = workspace_tmp_path / "ProjectInputs" / "ConstructionManifest" / "demo_plugin_standards.md"
        mpath.write_text("manifest_version: 2.0.0\n# 规范\n", encoding="utf-8")
        out = ct.demo_story_fetch(session_path=str(workspace_tmp_path), story_id=None,
                                  project_root=str(workspace_tmp_path))
        assert out["data"]["manifest_warning"] is not None
```

- [ ] **Step 2: 确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py -v`
Expected: 6 failed

- [ ] **Step 3: 三处注册 + 实现**

3a. `tool_definitions.py` 的 `COMPILER_FRONTEND_TOOLS` 字典末尾追加(镜像 compiler_skill_synthesis_* 条目形状):

```python
    "demo_story_fetch": {
        "description": "Phase 14 demo-first:取下一个(或指定)施工 story 全包——story JSON、施工规范全文、材料路径清单。in_progress 可幂等重入续作。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "run 目录路径(含 demo_plan.json 与 stories/)"},
            "story_id": {"type": "string", "required": False, "description": "缺省取计划顺序下一个可发工单"},
        },
        "returns": "data.story / data.construction_manifest(全文) / data.manifest_warning(版本不符告警,可为 null)",
    },
    "demo_story_submit": {
        "description": "Phase 14 demo-first:提交 story 完成证据。按 evidence_class 机器校验;失败回 in_progress 并返回具体错误(重试闭环);增量批附加 v0 冒烟 hash 守门。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "run 目录路径"},
            "story_id": {"type": "string", "required": True},
            "evidence": {"type": "object", "required": True, "description": "files_changed/test_report/smoke_report/screenshots/doc_paths/provisional_decisions/plugin_root"},
        },
        "returns": "data.story_status(verified|in_progress) / data.errors / data.attempts",
    },
```

3b. 同文件第 546-548 行计数注释更新:`16(compiler_frontend)` → `18(compiler_frontend)`,总和注释 `= 55` → `= 57`(`TOOL_COUNT = len(ALL_TOOLS)` 是计算值,只改注释)。

3c. `server.py` TOOL_DISPATCH(compiler_skill_synthesis 两行之后):

```python
        "demo_story_fetch": ("compiler", compiler_tools.demo_story_fetch),
        "demo_story_submit": ("compiler", compiler_tools.demo_story_submit),
```

3d. `compiler_tools.py` 文件末尾追加(import 区按该文件既有方式补 demo_plan 模块引入——先 grep `gdd_coverage` 的 import 行,完全镜像其风格;若该文件用包导入则写 `from Compiler.demo_plan import story_store, evidence_validator, velocity, manifest_loader`):

```python
# ---------------- Phase 14 demo-first:story 工具对 ----------------

def _demo_project_root(project_root: str | None) -> Path:
    """project_root 仅测试注入用;生产路径 = 插件向上三级(MCP/ → AgentBridge → Plugins → 项目根)。"""
    return Path(project_root) if project_root else Path(__file__).resolve().parents[3]


def demo_story_fetch(session_path: str, story_id: str = None, project_root: str = None) -> dict:
    """取施工 story 全包:story + 施工规范全文 + 版本对账告警。"""
    try:
        root = _demo_project_root(project_root)
        store = story_store.StoryStore(session_path)
        story = store.fetch(story_id)
        manifest_text, manifest_version = manifest_loader.load_construction_manifest(root)
        warning = None
        if story.get("manifest_version") != manifest_version:
            warning = (f"施工规范版本不符: story 切批于 {story.get('manifest_version')},"
                       f"当前 {manifest_version},请人工确认差异后再施工")
        velocity.append_event(session_path, {"kind": "fetch", "story_id": story["story_id"],
                                             "attempts": story.get("attempts", 0)})
        return {"success": True, "data": {"story": story, "construction_manifest": manifest_text,
                                          "manifest_warning": warning}}
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return {"success": False, "error": f"demo_story_fetch 失败: {exc}"}


def demo_story_submit(session_path: str, story_id: str, evidence: dict,
                      project_root: str = None) -> dict:
    """提交证据:机器校验 → verified 或回 in_progress + 具体错误清单。"""
    try:
        root = _demo_project_root(project_root)
        store = story_store.StoryStore(session_path)
        story = store.load(story_id)
        baseline = None
        baseline_path = Path(session_path) / "v0_smoke_baseline.json"
        if baseline_path.exists():
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
        plugin_root = None
        if evidence.get("plugin_root"):
            plugin_root = root / str(evidence["plugin_root"])
        result = evidence_validator.validate_evidence(
            story, evidence, root, baseline=baseline, plugin_root=plugin_root)
        updated = store.submit(story_id, evidence, result)
        velocity.append_event(session_path, {"kind": "submit", "story_id": story_id,
                                             "result": updated["status"],
                                             "attempts": updated.get("attempts", 0)})
        return {"success": True, "data": {"story_status": updated["status"],
                                          "errors": updated.get("submit_errors", []),
                                          "attempts": updated.get("attempts", 0)}}
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return {"success": False, "error": f"demo_story_submit 失败: {exc}"}
```

注意:若 compiler_tools.py 的 import 方式与上面假设不符(用 importlib 而非包导入),以文件内 gdd_coverage 的既有引入方式为准镜像,函数体不变。

- [ ] **Step 4: 确认通过 + 既有 MCP 测试不破**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py -v`
Expected: 6 passed

Run: `grep -rn "TOOL_COUNT\|== 55\|55 个" Plugins/AgentBridge/Tests/scripts/ | grep -v phase14`
找出既有断言工具数=55 的用例(Phase 13 有 MCP 工具数断言),把它们更新为 57,并在 commit message 里点名。

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/ -k "phase13 or phase14" -v`
Expected: 全绿(89 + 新增全过,被更新的工具数断言过)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py Plugins/AgentBridge/MCP/compiler_tools.py Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py
# 如有更新工具数断言的既有测试文件一并 add,并在 message 注明
git commit -m "[skip-doc] feat(phase14): MCP 工具对 demo_story_fetch/submit——工具数 55→57"
```

---

### Task 8: demo_plan 生成 CLI

**Files:**
- Create: `Plugins/AgentBridge/Scripts/demo_plan_main.py`
- Test: 并入 `test_phase14_demo_plan.py`(追加 DMP-39~40)

- [ ] **Step 1: 追加失败测试**

```python
class TestDemoPlanCli:
    def _seed(self, tmp):
        import json as _json
        graph = {"graph_version": "1.0", "graph_id": "g-1",
                 "nodes": [{"instance_id": "skill-a", "capability_id": "cap-a",
                            "template_id": "t.v1", "domain_type": "gameplay",
                            "template_source": "plugin_skill_template",
                            "dependencies": [], "coupling": []}],
                 "edges": [], "metadata": {"source_run_id": "run-cli-test", "capability_gaps": []}}
        contract = {"contract_id": "c-1", "source_gdd": "ProjectInputs/GDD/x.md",
                    "gameplay_capabilities": [{"capability_id": "cap-a", "activation": "required",
                                               "source_anchor": "1. 概述"}],
                    "baseline_capabilities": []}
        (tmp / "skill_graph.json").write_text(_json.dumps(graph), encoding="utf-8")
        (tmp / "root_skill_contract.json").write_text(_json.dumps(contract), encoding="utf-8")

    def test_dmp39_cli_writes_plan_and_stories(self, workspace_tmp_path, project_root):
        import subprocess, sys, json as _json
        self._seed(workspace_tmp_path)
        cli = Path(project_root) / "Plugins" / "AgentBridge" / "Scripts" / "demo_plan_main.py"
        result = subprocess.run([sys.executable, str(cli), "--run-dir", str(workspace_tmp_path)],
                                capture_output=True, text=True, cwd=project_root)
        assert result.returncode == 0, result.stderr
        plan = _json.loads((workspace_tmp_path / "demo_plan.json").read_text(encoding="utf-8"))
        assert plan["run_id"] == "run-cli-test"
        assert (workspace_tmp_path / "stories" / "story-skill-a.json").exists()

    def test_dmp40_cli_fails_closed_on_unresolved_gaps(self, workspace_tmp_path, project_root):
        import subprocess, sys, json as _json
        self._seed(workspace_tmp_path)
        graph = _json.loads((workspace_tmp_path / "skill_graph.json").read_text(encoding="utf-8"))
        graph["metadata"]["capability_gaps"] = [{"capability_id": "cap-gap", "reason": "x"}]
        (workspace_tmp_path / "skill_graph.json").write_text(_json.dumps(graph), encoding="utf-8")
        cli = Path(project_root) / "Plugins" / "AgentBridge" / "Scripts" / "demo_plan_main.py"
        result = subprocess.run([sys.executable, str(cli), "--run-dir", str(workspace_tmp_path)],
                                capture_output=True, text=True, cwd=project_root)
        assert result.returncode != 0 and "capability_gaps" in (result.stderr + result.stdout)
```

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -k "dmp39 or dmp40" -v` → 2 failed

- [ ] **Step 2: 实现 demo_plan_main.py**

```python
# -*- coding: utf-8 -*-
"""demo_plan 生成 CLI(runbook 驱动用,无人值守窗口之前的准备步骤)。

用法:
  python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir ProjectState/runs/<run_id>

行为:
  读 run 目录的 skill_graph.json + root_skill_contract.json,
  未解决 capability_gaps 时 fail-closed(增量批的合成包必须先走 Phase 13 合成+人审),
  经 jsonschema 校验后写 demo_plan.json + stories/*.json(.part 原子写)。
"""
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPTS_DIR.parent
PROJECT_ROOT = PLUGIN_ROOT.parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 14 demo_plan 生成")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--manifest", default=None, help="施工规范路径(缺省项目层默认位置)")
    args = parser.parse_args()
    run_dir = Path(args.run_dir)

    graph = json.loads((run_dir / "skill_graph.json").read_text(encoding="utf-8"))
    contract = json.loads((run_dir / "root_skill_contract.json").read_text(encoding="utf-8"))

    gaps = (graph.get("metadata") or {}).get("capability_gaps") or []
    if gaps:
        print(f"[FAIL] 存在未解决 capability_gaps({len(gaps)} 条),先走合成+人审再切批", file=sys.stderr)
        return 2

    ml = _load("manifest_loader")
    planner = _load("planner")
    _, manifest_version = ml.load_construction_manifest(
        PROJECT_ROOT, path=Path(args.manifest) if args.manifest else None)

    def rel(p):
        return str(Path(p)).replace("\\", "/")

    paths = {
        "gdd_path": contract.get("source_gdd", ""),
        "contract_path": rel(run_dir / "root_skill_contract.json"),
        "skill_graph_path": rel(run_dir / "skill_graph.json"),
        "construction_manifest_path": rel(ml.DEFAULT_MANIFEST_REL),
        "doc_extra_paths": [rel(run_dir / "demo_plan.json"), rel(run_dir / "velocity_log.json")],
    }
    out = planner.build_demo_plan(graph, contract, manifest_version, paths)

    # schema 自校验(机器守门,与 validate_examples 同源 schema)
    import jsonschema
    schemas_dir = PLUGIN_ROOT / "Schemas"
    plan_schema = json.loads((schemas_dir / "demo_plan.schema.json").read_text(encoding="utf-8"))
    story_schema = json.loads((schemas_dir / "demo_story.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(out["plan"], plan_schema)
    for story in out["stories"]:
        jsonschema.validate(story, story_schema)

    stories_dir = run_dir / "stories"
    stories_dir.mkdir(exist_ok=True)

    def atomic_write(path: Path, data):
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, path)

    atomic_write(run_dir / "demo_plan.json", out["plan"])
    for story in out["stories"]:
        atomic_write(stories_dir / f"{story['story_id']}.json", story)

    total = len(out["stories"])
    print(f"[OK] demo_plan 落盘: {len(out['plan']['batches'])} 批 / {total} story → {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -v`
Expected: 14 passed(10+2+2)

- [ ] **Step 4: Commit**

```bash
git add Plugins/AgentBridge/Scripts/demo_plan_main.py Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py
git commit -m "[skip-doc] feat(phase14): demo_plan CLI——gap fail-closed + schema 自校验落盘"
```

---

### Task 9: 冒烟 runner(环境自检 + commandlet + 报告)

**Files:**
- Create: `Plugins/AgentBridge/Scripts/demo_smoke/__init__.py`(空)
- Create: `Plugins/AgentBridge/Scripts/demo_smoke/runner.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase14_smoke_runner.py`

- [ ] **Step 1: 写失败测试(DMP-41~44,subprocess 全 mock,不要求真机)**

```python
# -*- coding: utf-8 -*-
"""DMP-41~44: 冒烟 runner——环境自检/报告解析/v0 回归段/环境故障归因分离。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "runner", PLUGIN_ROOT / "Scripts" / "demo_smoke" / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ue_report(tmp, failed=0):
    d = tmp / "ue_report"
    d.mkdir(parents=True, exist_ok=True)
    (d / "index.json").write_text(json.dumps(
        {"succeeded": 3, "succeededWithWarnings": 0, "failed": failed, "notRun": 0,
         "tests": [{"fullTestPath": "X.Smoke.FullLoop", "state": "Success" if not failed else "Fail"}]}),
        encoding="utf-8")
    return d


class TestSmokeRunner:
    def test_dmp41_precheck_missing_editor_is_env_error(self, workspace_tmp_path):
        r = _load()
        out = r.precheck(editor_cmd=workspace_tmp_path / "no_editor.exe",
                         uproject=workspace_tmp_path / "no.uproject")
        assert out["ok"] is False and out["kind"] == "environment"

    def test_dmp42_parse_ue_report_pass(self, workspace_tmp_path):
        r = _load()
        report = r.build_smoke_report(_ue_report(workspace_tmp_path), v0_regression="n/a",
                                      screenshots=[])
        assert report["status"] == "pass" and report["counts"]["failed"] == 0

    def test_dmp43_parse_ue_report_fail(self, workspace_tmp_path):
        r = _load()
        report = r.build_smoke_report(_ue_report(workspace_tmp_path, failed=1),
                                      v0_regression="n/a", screenshots=[])
        assert report["status"] == "fail"

    def test_dmp44_missing_index_json_is_env_error_not_fail(self, workspace_tmp_path):
        r = _load()
        import pytest
        with pytest.raises(r.EnvironmentFault):
            r.build_smoke_report(workspace_tmp_path / "empty", v0_regression="n/a", screenshots=[])
```

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_smoke_runner.py -v` → 4 failed

- [ ] **Step 2: 实现 runner.py**

```python
# -*- coding: utf-8 -*-
"""demo 冒烟 runner:UE Automation commandlet 驱动 + 环境故障与 demo 失败分离归因。

用法(runbook):
  python Plugins/AgentBridge/Scripts/demo_smoke/runner.py \
      --filter "<PluginName>.Smoke" --out ProjectState/Evidence/<name>_smoke_report.json \
      [--v0-filter "<PluginName>.Smoke.V0"] [--editor-cmd <UnrealEditor-Cmd.exe>]

环境约定:editor-cmd 缺省读环境变量 AGENTBRIDGE_UE_CMD;uproject 取项目根唯一 .uproject。
报告契约(evidence_validator 消费):{"status": "pass|fail", "v0_regression": "pass|fail|n/a",
"counts": {...}, "suites": [...], "screenshots": [...], "log_path": ...}
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]


class EnvironmentFault(RuntimeError):
    """环境故障(编辑器缺失/报告未产出):不计入 demo 失败与自修轮次(spec §5.1 归因分离)。"""


def precheck(editor_cmd: Path, uproject: Path) -> dict:
    """前置自检:不过即环境故障,直接拒绝开跑。"""
    missing = [str(p) for p in (editor_cmd, uproject) if not Path(p).exists()]
    if missing:
        return {"ok": False, "kind": "environment", "missing": missing}
    return {"ok": True, "kind": "ready", "missing": []}


def run_automation(editor_cmd: Path, uproject: Path, test_filter: str, report_dir: Path,
                   log_path: Path) -> None:
    """UE Automation commandlet(同步阻塞);真机参数微调记 runbook,不改报告契约。"""
    cmd = [str(editor_cmd), str(uproject),
           f"-ExecCmds=Automation RunTests {test_filter}; Quit",
           "-unattended", "-nopause", "-nosplash",
           f"-ReportExportPath={report_dir}", f"-abslog={log_path}"]
    subprocess.run(cmd, check=False, timeout=1800)


def build_smoke_report(report_dir: Path, v0_regression: str, screenshots: list,
                       log_path: str = "") -> dict:
    index = Path(report_dir) / "index.json"
    if not index.exists():
        raise EnvironmentFault(f"UE 报告未产出(index.json 缺失): {report_dir}")
    data = json.loads(index.read_text(encoding="utf-8-sig"))
    failed = int(data.get("failed", 0)) + int(data.get("notRun", 0))
    return {
        "status": "pass" if failed == 0 else "fail",
        "v0_regression": v0_regression,
        "counts": {k: data.get(k, 0) for k in ("succeeded", "succeededWithWarnings", "failed", "notRun")},
        "suites": [{"name": t.get("fullTestPath", ""), "state": t.get("state", "")}
                   for t in data.get("tests", [])],
        "screenshots": list(screenshots),
        "log_path": log_path,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 14 demo 冒烟 runner")
    parser.add_argument("--filter", required=True)
    parser.add_argument("--v0-filter", default=None, help="增量批传入:先跑 v0 回归段")
    parser.add_argument("--out", required=True)
    parser.add_argument("--editor-cmd", default=os.environ.get("AGENTBRIDGE_UE_CMD", ""))
    parser.add_argument("--screenshots", nargs="*", default=[])
    args = parser.parse_args()

    uprojects = sorted(PROJECT_ROOT.glob("*.uproject"))
    if not uprojects or not args.editor_cmd:
        print("[ENV] 环境自检失败: 缺 uproject 或 editor-cmd(AGENTBRIDGE_UE_CMD)", file=sys.stderr)
        return 3
    check = precheck(Path(args.editor_cmd), uprojects[0])
    if not check["ok"]:
        print(f"[ENV] 环境自检失败: {check['missing']}", file=sys.stderr)
        return 3

    out_path = Path(args.out)
    work = out_path.parent / (out_path.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)

    try:
        v0_state = "n/a"
        if args.v0_filter:
            v0_dir = work / "v0"
            run_automation(Path(args.editor_cmd), uprojects[0], args.v0_filter, v0_dir,
                           work / "v0.log")
            v0_state = "pass" if build_smoke_report(v0_dir, "n/a", [])["status"] == "pass" else "fail"
        main_dir = work / "main"
        run_automation(Path(args.editor_cmd), uprojects[0], args.filter, main_dir,
                       work / "main.log")
        report = build_smoke_report(main_dir, v0_state, args.screenshots,
                                    log_path=str(work / "main.log"))
    except EnvironmentFault as exc:
        print(f"[ENV] {exc}", file=sys.stderr)
        return 3

    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'OK' if report['status'] == 'pass' else 'FAIL'}] 冒烟报告 → {out_path}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
```

退出码契约:0=pass / 1=demo 失败(计自修轮)/ 3=环境故障(不计自修轮)。

- [ ] **Step 3: 确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_smoke_runner.py -v`
Expected: 4 passed

- [ ] **Step 4: Commit**

```bash
git add Plugins/AgentBridge/Scripts/demo_smoke/__init__.py Plugins/AgentBridge/Scripts/demo_smoke/runner.py Plugins/AgentBridge/Tests/scripts/test_phase14_smoke_runner.py
git commit -m "[skip-doc] feat(phase14): 冒烟 runner——环境自检/报告契约/归因分离(退出码 0/1/3)"
```

---

### Task 10: Stage 14 登记 + 全量回归

**Files:**
- Modify: `Plugins/AgentBridge/Tests/run_system_tests.py`(STAGES 字典第 207 行后 + 必要的执行分支)

- [ ] **Step 1: 统计实际用例数**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/ -k phase14 --collect-only -q`
Expected: 末行 `44 tests collected`(10+2+2 demo_plan + 2 语义 + 8 store + 10 validator + 6 mcp + 4 runner = 44;以实际收集数为准,下面 N=实际值)

- [ ] **Step 2: 登记 Stage 14**

先看 Stage 13 怎么被执行:`grep -n "phase13\|stage == 13\|case_ids" Plugins/AgentBridge/Tests/run_system_tests.py`,镜像其执行分支(Stage 13 是 pytest -k 过滤模式)。在 STAGES 字典 13 号条目后追加(N 用 Step 1 实际值):

```python
    14: {
        'name': 'Phase 14 Demo Plan（DMP）',
        'cases': 'DMP-01 ~ DMP-N（6 个 test_phase14_* 文件）',
        'case_ids': make_case_ids('DMP', 1, N),
        'count': N,
        'requires_editor': False,
        'requires_build': False,
    },
```

并镜像 Stage 13 的执行函数/分支为 phase14(pytest `-k phase14`)。`TOTAL_CASES` 是 sum 自动更新;同步更新第 209 行注释(364 → 364+N)。

- [ ] **Step 3: 跑 Stage 14 与全量**

Run: `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor --stage 14`
Expected: `[PASS] Phase 14 Demo Plan 全部通过 (N/N)`

Run: `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`
Expected: 等价回归——既有 stage 结果与 Phase 13 收尾一致(预存失败清单照旧 skip),新增 Stage 14 PASS

Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: 30/30 passed

- [ ] **Step 4: 更新 CLAUDE.md 测试登记数**

CLAUDE.md 常用命令注释里"当前登记 364 条"同步为新总数(这是登记数说明,属 trivial 同步;权威源仍是 run_system_tests.py)。

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Tests/run_system_tests.py CLAUDE.md
git commit -m "[skip-doc] test(phase14): Stage 14 登记(DMP N 条)——总数 364→364+N"
```

---

### Task 11: 验收 runbook

**Files:**
- Create: `ProjectState/Reports/2026-06-11/phase14_acceptance_runbook.md`

- [ ] **Step 1: 写 runbook(对应 spec §7 判据 C1-C6)**

```markdown
# Phase 14 验收 runbook

> 对应 spec §7 判据 C1-C6(`Docs/superpowers/specs/2026-06-11-phase14-demo-first-design.md`)。
> 每条做完勾选并贴证据路径。失败如实记录(KILL 是合法收尾,spec §7 如实记录条款)。
> 验收 GDD:`ProjectInputs/GDD/monopoly_extended_auction_v1.md`

## C1 机器判据

- [ ] `python -m pytest Plugins/AgentBridge/Tests/scripts/ -k phase14 -v` 全绿
- [ ] `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor` 全量等价(预存失败照旧 skip)
- [ ] `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` 30/30

## C2 实战:切批标准答案

- [ ] 复用 Phase 13 流程产出 gap=0 的 run(Stage 1-3 + 合成包均 approved 后重跑 Stage 3)
- [ ] `python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir ProjectState/runs/<run_id>`
- [ ] 标准答案断言:批次 = v0(16 库内 capability story + story-v0-docs)+ increment-1(拍卖)+ increment-2(股票);批内拓扑序正确
  - run_id:______ demo_plan 路径:______

## C3 v0 无人值守实证(最大赌注,如实记录)

- [ ] 驱动器就位(headless 会话或 driver 脚本,零人工干预窗口从首次 demo_story_fetch 起算)
- [ ] coding agent 按施工规范在 `Plugins/<派生名>/` 完成 v0 全部 story:编译过 + 冒烟(完整一局到终局零报错)+ README 试玩说明 + Docs/ 文档包,submit 全部 verified
- [ ] 干预/自修超限(里程碑内 >5 轮)如实降级记录:______
- [ ] 证据:velocity_log + 冒烟报告 + 截图 → `ProjectState/Evidence/phase14_v0_*`

## C4 人审窗口 1:msc 试玩 v0

- [ ] msc 无引导玩一局,裁决 PROCEED / PIVOT / KILL:______(留痕路径:______)
- [ ] PROCEED 时:冻结 v0 冒烟基线(`<run_id>` 与用例路径按当日实际值填):

      ```bash
      python -c "import importlib.util; spec=importlib.util.spec_from_file_location('ev','Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); import glob; m.freeze_v0_baseline('.', 'ProjectState/runs/<run_id>', [p.replace('\\\\','/') for p in glob.glob('Plugins/<派生名>/Source/*/Private/Tests/*.cpp')])"
      ```

      再批拍卖合成包(manifest review_status: pending_review → approved)

## C5 增量批 1(拍卖)

- [ ] 逐 story fetch/submit;v0 hash 不变且回归全绿(submit 机器守门)
- [ ] 文档包更新过引用对账;msc 试玩 v1 终裁:______

## C6 接口中立

- [ ] `python -c "import sys; sys.path.insert(0, 'Plugins/AgentBridge'); from MCP import tool_definitions as td; print(td.TOOL_COUNT)"` 输出 57
- [ ] 两工具在 MCP server 启动日志可见(Codex 可接入,本期不实证)

## 附:环境故障记录(不计入 demo 失败)

| 时间 | 故障 | 处置 |
|---|---|---|
```

- [ ] **Step 2: Commit**

```bash
git add ProjectState/Reports/2026-06-11/phase14_acceptance_runbook.md
git commit -m "[skip-doc] docs(phase14): 验收 runbook C1-C6"
```

---

## 收尾(plan 执行完后,不属于本 plan 的 task)

1. `superpowers:verification-before-completion` → 全量证据复核
2. runbook C2-C5 实战执行(真机 + msc 两个试玩窗口)
3. `document-release`(任务收尾流程:task.md 换页 Phase 14、INDEX、acceptance 报告、工具数 57 全文档同步)
4. `superpowers:finishing-a-development-branch`(merge / PR)
```
