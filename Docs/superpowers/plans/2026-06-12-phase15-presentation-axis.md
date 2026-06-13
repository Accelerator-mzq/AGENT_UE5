# Phase 15 呈现增量轴 + 反馈回流通道 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把"呈现/图形"建成数据驱动的增量批维度(presentation ladder + planner amend),把试玩反馈建成机制内闭环(feedback 批),并落地行为校验门禁(BL-05)、路径越界守门(BL-01)、smoke errorMessage 透传(BL-04)。

**Architecture:** 全部新机制走既有 demo_plan 形状——amend 模块纯函数确定性追加批次(呈现批来源=项目层阶梯 JSON;反馈批来源=run 目录 feedback 条目),story_store/MCP fetch-submit 主干不变;evidence_validator 增三道行为对账 + 分层冻结(frozen_baselines.json)+ supersedes 放行;新 MCP 工具 demo_feedback_log(57→58)。

**Tech Stack:** Python 3.x + jsonschema + pytest(机制层);JSON Schema draft-07;MCP stdio(既有 server.py);UE Automation(demo 侧,验收期由 coding agent 实施,不在本 plan 内)。

**Spec:** `Docs/superpowers/specs/2026-06-12-phase15-presentation-axis-design.md`(已 msc 批准)

**范围切割(重要):** 本 plan 只覆盖机制层 + 项目层输入(阶梯实例/施工规范 1.2.0)+ 测试登记。demo 侧三个 rung 的 UMG/2D/3D 实施由验收期 coding agent 经 fetch/submit 无人值守完成(Phase 14 C3 同款),不在本 plan 任务里。

**Spec 细化备案(写入 spec 顶部修订记录,见 Task 13):** spec §4.2 只点名 `story_kind` 增加 `feedback`;实施定案呈现 story 用独立 `story_kind: "presentation"`(复用 `capability` 需伪造 capability_id/instance_id,违背 schema 条件约束本意)。

---

## 文件结构总览

**新建(插件层机制):**

| 文件 | 职责 |
|---|---|
| `Plugins/AgentBridge/Schemas/presentation_ladder.schema.json` | 呈现阶梯 schema(rung/story 切分/claims/supersedes) |
| `Plugins/AgentBridge/Schemas/feedback_entry.schema.json` | 反馈条目 schema(现象/期望/严重度/状态机) |
| `Plugins/AgentBridge/Schemas/examples/phase15_presentation_ladder.example.json` | 阶梯最小示例(strict 校验) |
| `Plugins/AgentBridge/Schemas/examples/phase15_feedback_entry.example.json` | 反馈条目示例(strict 校验) |
| `Plugins/AgentBridge/Compiler/demo_plan/amend.py` | 批次追加纯函数(呈现批 + 反馈批共用入口) |
| `Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py` | PRX-01~15 |
| `Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py` | PRX-16~25 |
| `Plugins/AgentBridge/Tests/scripts/test_phase15_feedback_tool.py` | PRX-26~32 |
| `Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py` | PRX-33~39 |
| `Plugins/AgentBridge/Tests/scripts/test_phase15_smoke_runner.py` | PRX-40~44 |

**新建(项目层输入):**

| 文件 | 职责 |
|---|---|
| `ProjectInputs/PresentationLadder/monopoly_demo_ladder.json` | 本 demo 的阶梯实例(游戏语义只在这里) |

**修改:**

| 文件 | 改动 |
|---|---|
| `Plugins/AgentBridge/Schemas/demo_story.schema.json` | 1.1.0:batch_id 模式扩展、story_kind +presentation/+feedback、interaction_claims、materials +3 可选字段 |
| `Plugins/AgentBridge/Schemas/demo_plan.schema.json` | 1.1.0:batch_id 模式扩展 |
| `Plugins/AgentBridge/Schemas/examples/phase14_demo_plan.example.json` | 版本字符串 1.0.0→1.1.0 |
| `Plugins/AgentBridge/Schemas/examples/phase14_demo_story.example.json` | 版本字符串 1.0.0→1.1.0 |
| `Plugins/AgentBridge/Compiler/demo_plan/planner.py` | 仅版本常量 1.0.0→1.1.0(产物须过新 schema const) |
| `Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py` | BL-01 越界、呈现批截图必交、行为校验三道对账、frozen_baselines 分层冻结 + supersedes |
| `Plugins/AgentBridge/Scripts/demo_plan_main.py` | --amend-presentation/--amend-feedback/--ladder |
| `Plugins/AgentBridge/Scripts/demo_smoke/runner.py` | BL-04 suites.errors 透传、--regression-filter 多段聚合 |
| `Plugins/AgentBridge/MCP/compiler_tools.py` | demo_feedback_log + submit 接 frozen_layers + feedback resolved 流转 |
| `Plugins/AgentBridge/MCP/tool_definitions.py` | 注册 demo_feedback_log(TOOL_COUNT 57→58) |
| `Plugins/AgentBridge/MCP/server.py` | dispatch 表 +1 行 |
| `Plugins/AgentBridge/Scripts/validation/validate_examples.py` | +2 example 映射 |
| `Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py` | 工具数断言 57→58 |
| `Plugins/AgentBridge/Tests/run_system_tests.py` | STAGES[15] + run_stage_15 + dispatch + CASE_ID_PATTERN |
| `Plugins/AgentBridge/Tests/SystemTestCases.md` | PRX-01~44 登记 |
| `ProjectInputs/ConstructionManifest/demo_plugin_standards.md` | 1.2.0:§4 用例命名补充、§7 程序化 3D 通路、新 §8 呈现层架构约束 |
| `Docs/superpowers/specs/2026-06-12-phase15-presentation-axis-design.md` | 顶部追加实施期修订记录 |

**红线确认:** 以上无一触碰 CLAUDE.md"绝对不要修改"清单(C++ 核心 / bridge 客户端 / orchestrator 核心 / AgentBridgeTests/ / 稳定 Schema 目录)。`Plugins/AgentBridge/Tests/`(系统测试)与 `Compiler/demo_plan/` 均在可改清单先例内(Phase 14 已动过)。

**环境与命令约定:** 所有 pytest 命令在项目根 `D:\UnrealProjects\Mvpv4TestCodex` 下执行;`python -m pytest` 用既有 conftest(`Plugins/AgentBridge/Tests/scripts/conftest.py` 提供 `project_root` / `workspace_tmp_path` fixture)。commit 一律带 `[skip-doc]` 前缀(document-release 在验收收尾统一跑,Phase 14 同款)。

---

### Task 1: demo_story / demo_plan schema 升 1.1.0 + planner 版本常量

**Files:**
- Modify: `Plugins/AgentBridge/Schemas/demo_story.schema.json`
- Modify: `Plugins/AgentBridge/Schemas/demo_plan.schema.json`
- Modify: `Plugins/AgentBridge/Schemas/examples/phase14_demo_plan.example.json`
- Modify: `Plugins/AgentBridge/Schemas/examples/phase14_demo_story.example.json`
- Modify: `Plugins/AgentBridge/Compiler/demo_plan/planner.py:11-12`
- Create: `Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py`

- [ ] **Step 1: 写失败测试(新建 test_phase15_schemas.py)**

```python
# -*- coding: utf-8 -*-
"""PRX schema 组:demo_story/demo_plan 1.1.0 升版 + 新 schema(阶梯/反馈)+ 实例校验。

注:本文件 Task 1 先落 4 条(p15s01~04),Task 2 追加 p15s05~06,Task 11 追加 p15s07。
"""
import json
from pathlib import Path

import jsonschema
import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = PLUGIN_ROOT / "Schemas"


def _schema(name):
    """读插件层 schema 文件。"""
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def _story(**over):
    """最小合法 demo_story(1.1.0),over 覆盖字段。"""
    base = {
        "story_schema_version": "1.1.0", "story_id": "story-x", "batch_id": "v0",
        "story_kind": "presentation", "evidence_class": "Integration", "depends_on": [],
        "materials": {"gdd_path": "g.md", "gdd_anchors": [], "contract_path": "c.json",
                      "skill_graph_path": "s.json", "template_id": None, "template_source": None,
                      "template_dir": None, "construction_manifest_path": "m.md", "extra_paths": []},
        "acceptance_criteria": ["x"], "status": "pending", "attempts": 0,
        "manifest_version": "1.2.0",
    }
    base.update(over)
    return base


class TestStorySchema110:
    def test_p15s01_story_accepts_feedback_kind(self):
        schema = _schema("demo_story.schema.json")
        jsonschema.validate(_story(story_kind="feedback", batch_id="feedback-1"), schema)

    def test_p15s02_story_accepts_presentation_batch_id(self):
        schema = _schema("demo_story.schema.json")
        jsonschema.validate(_story(batch_id="presentation-3"), schema)

    def test_p15s03_story_rejects_unknown_batch_id(self):
        schema = _schema("demo_story.schema.json")
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(_story(batch_id="rung-1"), schema)

    def test_p15s04_interaction_claims_shape_enforced(self):
        schema = _schema("demo_story.schema.json")
        jsonschema.validate(
            _story(interaction_claims=[{"input": "Space", "behavior": "推进回合"}]), schema)
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(_story(interaction_claims=[{"input": "Space"}]), schema)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py -v`
Expected: 4 failed(story_schema_version const 1.0.0 拒绝 1.1.0 / story_kind 枚举无 presentation)

- [ ] **Step 3: 改 demo_story.schema.json(整文件替换)**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "demo_story",
  "description": "Phase 14 demo-first:单条施工工单;Phase 15 增 presentation/feedback 工单与 interaction_claims。materials 全部为路径指针(agent 读全文,零语义压缩)。",
  "type": "object",
  "additionalProperties": false,
  "required": ["story_schema_version", "story_id", "batch_id", "story_kind", "evidence_class",
               "depends_on", "materials", "acceptance_criteria", "status", "attempts", "manifest_version"],
  "properties": {
    "story_schema_version": {"const": "1.1.0", "description": "schema 版本(Phase 15 升 1.1.0)"},
    "story_id": {"type": "string", "pattern": "^story-[a-z0-9-]+$", "description": "工单 id"},
    "batch_id": {"type": "string",
                 "pattern": "^(v0|increment-[1-9][0-9]*|presentation-[1-9][0-9]*|feedback-[1-9][0-9]*)$",
                 "description": "所属批次(Phase 15 增 presentation-N / feedback-N)"},
    "story_kind": {"enum": ["capability", "documentation", "presentation", "feedback"],
                   "description": "功能 / 批末文档 / 呈现 / 反馈修复工单"},
    "capability_id": {"type": "string", "description": "功能工单对应 capability(其余工单缺省)"},
    "instance_id": {"type": "string", "description": "skill graph 节点 id(功能工单)"},
    "evidence_class": {"enum": ["Logic", "Integration", "Visual", "Config"],
                       "description": "证据分级:决定 submit 必交证据"},
    "depends_on": {"type": "array", "items": {"type": "string", "pattern": "^story-[a-z0-9-]+$"}, "description": "前置 story id(verified 后方可 fetch)"},
    "interaction_claims": {
      "type": "array",
      "description": "交互宣称清单(行为校验门禁 P14-BL-05 的对账输入;呈现批自阶梯数据带入)",
      "items": {"type": "object", "additionalProperties": false,
                "required": ["input", "behavior"],
                "properties": {"input": {"type": "string", "minLength": 1, "description": "按键/输入名(README 键位 token 同名)"},
                               "behavior": {"type": "string", "minLength": 1, "description": "宣称行为(人读)"}}}
    },
    "materials": {
      "type": "object", "additionalProperties": false,
      "required": ["gdd_path", "gdd_anchors", "contract_path", "skill_graph_path", "construction_manifest_path"],
      "properties": {
        "gdd_path": {"type": "string", "description": "GDD 原文路径"},
        "gdd_anchors": {"type": "array", "items": {"type": "string"}, "description": "本工单相关 GDD 锚点标题"},
        "contract_path": {"type": "string", "description": "root_skill_contract.json 路径"},
        "skill_graph_path": {"type": "string", "description": "skill_graph.json 路径"},
        "template_id": {"type": ["string", "null"], "description": "绑定模板 id(非功能工单为 null)"},
        "template_source": {"enum": ["plugin_skill_template", "future_baseline_template", "synthesized", null], "description": "节点模板来源(null 为非功能工单)"},
        "template_dir": {"type": ["string", "null"], "description": "合成包目录(仅 synthesized 预解析,其余 null)"},
        "construction_manifest_path": {"type": "string", "description": "施工规范路径"},
        "ladder_rung_path": {"type": ["string", "null"], "description": "呈现阶梯实例路径(呈现工单;其余 null/缺省)"},
        "feedback_path": {"type": ["string", "null"], "description": "反馈条目 JSON 路径(反馈工单;其余 null/缺省)"},
        "supersedes_paths": {"type": "array", "items": {"type": "string"}, "description": "阶梯 rung 显式退役的文件(hash 守门放行清单;authored 数据,非 agent 自报)"},
        "extra_paths": {"type": "array", "items": {"type": "string"}, "description": "附加材料(文档工单:plan/velocity 等)"}
      }
    },
    "acceptance_criteria": {"type": "array", "items": {"type": "string"}, "minItems": 1},
    "status": {"enum": ["pending", "in_progress", "submitted", "verified"]},
    "attempts": {"type": "integer", "minimum": 0, "description": "自修轮次(submit 被拒 +1)"},
    "manifest_version": {"type": "string", "description": "切批时施工规范版本(fetch 时对账)"},
    "submit_errors": {"type": "array", "items": {"type": "string"}, "description": "最近一次被拒的错误清单"},
    "evidence": {"type": "object", "description": "verified 时的最终证据载荷(透传存档)"}
  },
  "if": {"properties": {"story_kind": {"const": "capability"}}, "required": ["story_kind"]},
  "then": {"required": ["capability_id", "instance_id"]}
}
```

- [ ] **Step 4: 改 demo_plan.schema.json(两处)**

第 9 行 `"plan_schema_version": {"const": "1.0.0", ...}` 改为:

```json
    "plan_schema_version": {"const": "1.1.0", "description": "schema 版本(Phase 15 升 1.1.0)"},
```

第 19 行 batch_id pattern 改为:

```json
          "batch_id": {"type": "string", "pattern": "^(v0|increment-[1-9][0-9]*|presentation-[1-9][0-9]*|feedback-[1-9][0-9]*)$"},
```

- [ ] **Step 5: planner.py 版本常量升级(11-12 行)**

```python
PLAN_SCHEMA_VERSION = "1.1.0"
STORY_SCHEMA_VERSION = "1.1.0"
```

- [ ] **Step 6: 两个 phase14 example 的版本字符串 1.0.0→1.1.0**

`phase14_demo_plan.example.json` 中 `"plan_schema_version": "1.0.0"` → `"1.1.0"`;
`phase14_demo_story.example.json` 中 `"story_schema_version": "1.0.0"` → `"1.1.0"`。
(注:磁盘上 Phase 14 既有 run 的 1.0.0 story 不回写不重校验——store 不做 schema 校验,amend 只新增 1.1.0 产物;此口径记入 Task 13 spec 修订备案。)

- [ ] **Step 7: 跑测试确认通过 + strict 不破**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py -v`
Expected: 4 passed
Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: 30/30 通过(两个 phase14 example 已同步升版)
Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -v`
Expected: 17 passed(planner 版本常量升级不破既有断言;CLI 自校验对新 const 成立)

- [ ] **Step 8: Commit**

```bash
git add Plugins/AgentBridge/Schemas/demo_story.schema.json Plugins/AgentBridge/Schemas/demo_plan.schema.json Plugins/AgentBridge/Schemas/examples/phase14_demo_plan.example.json Plugins/AgentBridge/Schemas/examples/phase14_demo_story.example.json Plugins/AgentBridge/Compiler/demo_plan/planner.py Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py
git commit -m "[skip-doc] feat(phase15): demo_story/demo_plan schema 1.1.0——presentation/feedback 批次与 interaction_claims"
```

### Task 2: presentation_ladder / feedback_entry 新 schema + examples + strict 映射

**Files:**
- Create: `Plugins/AgentBridge/Schemas/presentation_ladder.schema.json`
- Create: `Plugins/AgentBridge/Schemas/feedback_entry.schema.json`
- Create: `Plugins/AgentBridge/Schemas/examples/phase15_presentation_ladder.example.json`
- Create: `Plugins/AgentBridge/Schemas/examples/phase15_feedback_entry.example.json`
- Modify: `Plugins/AgentBridge/Scripts/validation/validate_examples.py:129-133`(映射表)
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py`(追加 2 条)

- [ ] **Step 1: 追加失败测试(test_phase15_schemas.py 末尾新增类)**

```python
class TestNewSchemas:
    def test_p15s05_ladder_example_validates(self):
        schema = _schema("presentation_ladder.schema.json")
        example = json.loads((SCHEMAS / "examples" / "phase15_presentation_ladder.example.json")
                             .read_text(encoding="utf-8"))
        jsonschema.validate(example, schema)

    def test_p15s06_feedback_example_validates(self):
        schema = _schema("feedback_entry.schema.json")
        example = json.loads((SCHEMAS / "examples" / "phase15_feedback_entry.example.json")
                             .read_text(encoding="utf-8"))
        jsonschema.validate(example, schema)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py -v -k "p15s05 or p15s06"`
Expected: 2 failed(schema 文件不存在)

- [ ] **Step 3: 写 presentation_ladder.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "presentation_ladder",
  "description": "Phase 15 呈现阶梯:数据驱动的呈现增量批定义。游戏语义只存在于项目层实例,机制只消费结构字段(防固化)。",
  "type": "object",
  "additionalProperties": false,
  "required": ["ladder_schema_version", "ladder_id", "target_plugin_root", "rungs"],
  "properties": {
    "ladder_schema_version": {"const": "1.0.0", "description": "schema 版本(当前钉死 1.0.0)"},
    "ladder_id": {"type": "string", "pattern": "^ladder-[a-z0-9-]+$", "description": "阶梯实例 id"},
    "target_plugin_root": {"type": "string", "minLength": 1, "description": "demo plugin 根(相对项目根)"},
    "rungs": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["rung_id", "title", "stories"],
        "properties": {
          "rung_id": {"type": "integer", "minimum": 1, "description": "阶梯层级(批次 id = presentation-<rung_id>)"},
          "title": {"type": "string", "minLength": 1, "description": "层级标题(人读)"},
          "gdd_anchors": {"type": "array", "items": {"type": "string"}, "description": "相关 GDD 锚点(可选)"},
          "supersedes": {"type": "array", "items": {"type": "string"},
                         "description": "本 rung 显式退役的下层实现用例文件(相对项目根);hash 守门据此放行"},
          "stories": {
            "type": "array", "minItems": 1,
            "items": {
              "type": "object", "additionalProperties": false,
              "required": ["story_slug", "summary", "evidence_class", "requirements"],
              "properties": {
                "story_slug": {"type": "string", "pattern": "^[a-z0-9-]+$", "description": "story id 派生用 slug"},
                "summary": {"type": "string", "minLength": 1, "description": "工单概要(人读)"},
                "evidence_class": {"enum": ["Logic", "Integration", "Visual", "Config"],
                                   "description": "显式证据分级(呈现批不走 domain_type 映射)"},
                "requirements": {"type": "array", "items": {"type": "string"}, "minItems": 1,
                                 "description": "呈现要求清单(进 acceptance_criteria 前段)"},
                "interaction_claims": {
                  "type": "array",
                  "items": {"type": "object", "additionalProperties": false,
                            "required": ["input", "behavior"],
                            "properties": {"input": {"type": "string", "minLength": 1},
                                           "behavior": {"type": "string", "minLength": 1}}},
                  "description": "交互宣称(喂行为校验门禁)"
                }
              }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: 写 feedback_entry.schema.json**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "feedback_entry",
  "description": "Phase 15 试玩反馈条目:demo_feedback_log 登记 → amend 切 feedback 批 → 状态机 open/in_batch/resolved。",
  "type": "object",
  "additionalProperties": false,
  "required": ["feedback_schema_version", "feedback_id", "window_id", "phenomenon", "expectation", "severity", "status"],
  "properties": {
    "feedback_schema_version": {"const": "1.0.0", "description": "schema 版本(当前钉死 1.0.0)"},
    "feedback_id": {"type": "string", "pattern": "^fb-w[0-9]+-[0-9]{2}$", "description": "条目 id(工具按窗口内序号生成)"},
    "window_id": {"type": "string", "pattern": "^w[0-9]+$", "description": "人审窗口 id(w1/w2/...)"},
    "phenomenon": {"type": "string", "minLength": 1, "description": "现象(msc 原话或忠实转述)"},
    "expectation": {"type": "string", "minLength": 1, "description": "期望行为"},
    "severity": {"enum": ["blocker", "major", "minor"], "description": "严重度"},
    "related_rung": {"type": ["integer", "null"], "description": "关联呈现 rung(可选)"},
    "related_capability": {"type": ["string", "null"], "description": "关联 capability(可选)"},
    "status": {"enum": ["open", "in_batch", "resolved"], "description": "open=已登记 / in_batch=已切批 / resolved=修复 story verified"}
  }
}
```

- [ ] **Step 5: 写两个 example**

`phase15_presentation_ladder.example.json`:

```json
{
  "ladder_schema_version": "1.0.0",
  "ladder_id": "ladder-example-demo",
  "target_plugin_root": "Plugins/Demo_Example",
  "rungs": [
    {
      "rung_id": 1,
      "title": "信息面板化",
      "gdd_anchors": ["4.1 HUD 常驻扩展"],
      "supersedes": [],
      "stories": [
        {
          "story_slug": "hud-panels",
          "summary": "文字 HUD 升级为结构化面板",
          "evidence_class": "Integration",
          "requirements": ["HUD 呈现回合与玩家状态面板,数据仅来自 GameState 快照"],
          "interaction_claims": [{"input": "Space", "behavior": "推进回合,面板同步刷新"}]
        }
      ]
    },
    {
      "rung_id": 2,
      "title": "2D 棋盘",
      "gdd_anchors": [],
      "supersedes": ["Plugins/Demo_Example/Source/Demo_Example/Private/Tests/Rung1ImplTests.cpp"],
      "stories": [
        {
          "story_slug": "board-2d",
          "summary": "2D 棋盘可视化",
          "evidence_class": "Integration",
          "requirements": ["棋盘环形布局呈现全部地块"]
        }
      ]
    }
  ]
}
```

`phase15_feedback_entry.example.json`:

```json
{
  "feedback_schema_version": "1.0.0",
  "feedback_id": "fb-w1-01",
  "window_id": "w1",
  "phenomenon": "拍卖面板出价后当前价未刷新",
  "expectation": "出价后面板当前最高价立即更新并高亮",
  "severity": "major",
  "related_rung": 1,
  "related_capability": "gameplay-property-auction",
  "status": "open"
}
```

- [ ] **Step 6: validate_examples.py 映射表追加(Phase 14 段之后)**

```python
    # === Phase 15 呈现增量轴 + 反馈回流 ===
    "phase15_presentation_ladder.example.json":
        "presentation_ladder.schema.json",
    "phase15_feedback_entry.example.json":
        "feedback_entry.schema.json",
```

- [ ] **Step 7: 跑测试确认通过 + strict 32/32**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py -v`
Expected: 6 passed
Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: 32/32 通过(30+2)

- [ ] **Step 8: Commit**

```bash
git add Plugins/AgentBridge/Schemas/presentation_ladder.schema.json Plugins/AgentBridge/Schemas/feedback_entry.schema.json Plugins/AgentBridge/Schemas/examples/phase15_presentation_ladder.example.json Plugins/AgentBridge/Schemas/examples/phase15_feedback_entry.example.json Plugins/AgentBridge/Scripts/validation/validate_examples.py Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py
git commit -m "[skip-doc] feat(phase15): presentation_ladder/feedback_entry schema + examples 入 strict(30→32)"
```

---

### Task 3: amend.py — 呈现批追加(纯函数)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/demo_plan/amend.py`
- Create: `Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py`

- [ ] **Step 1: 写失败测试(test_phase15_amend.py,本 Task 落 p15a01~10)**

```python
# -*- coding: utf-8 -*-
"""PRX amend 组:呈现批/反馈批追加——锚点/幂等/链式依赖/确定性/CLI。"""
import importlib.util
import json
from pathlib import Path

import pytest

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    """动态加载 Compiler/demo_plan 自包含模块(与 test_phase14_* 同款模式)。"""
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "demo_plan" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_PATHS = {
    "gdd_path": "ProjectInputs/GDD/x.md",
    "contract_path": "ProjectState/runs/r/root_skill_contract.json",
    "skill_graph_path": "ProjectState/runs/r/skill_graph.json",
    "construction_manifest_path": "ProjectInputs/ConstructionManifest/demo_plugin_standards.md",
    "ladder_path": "ProjectInputs/PresentationLadder/test_ladder.json",
    "feedback_dir": "ProjectState/runs/r/feedback",
    "doc_extra_paths": [],
}


def _plan_and_stories(verified_batches, pending_batches=()):
    """构造现状 plan + stories_by_id:verified_batches 全 verified,pending_batches 留批。"""
    batches, stories = [], {}
    for bid in list(verified_batches) + list(pending_batches):
        sid, did = f"story-{bid}-a", f"story-{bid}-docs"
        status = "verified" if bid in verified_batches else "pending"
        stories[sid] = {"story_id": sid, "status": status}
        stories[did] = {"story_id": did, "status": status}
        batches.append({"batch_id": bid, "story_ids": [sid, did]})
    plan = {"plan_schema_version": "1.0.0", "run_id": "r", "source_graph_id": "g",
            "manifest_version": "1.1.0", "batches": batches}
    return plan, stories


def _ladder_story(slug, claims=None):
    return {"story_slug": slug, "summary": "x", "evidence_class": "Integration",
            "requirements": ["req-1"], "interaction_claims": claims or []}


def _ladder(rung_stories=None):
    """rung_stories: {rung_id: [story...]};缺省三 rung 各一 story,rung3 带 supersedes。"""
    rung_stories = rung_stories or {1: [_ladder_story("s1a")], 2: [_ladder_story("s2a")],
                                    3: [_ladder_story("s3a")]}
    return {"ladder_schema_version": "1.0.0", "ladder_id": "ladder-test",
            "target_plugin_root": "Plugins/DemoX",
            "rungs": [{"rung_id": rid, "title": f"R{rid}", "gdd_anchors": [f"3.{rid}"],
                       "supersedes": (["Plugins/DemoX/Tests/R2Impl.cpp"] if rid == 3 else []),
                       "stories": stories}
                      for rid, stories in sorted(rung_stories.items())]}


class TestPresentationAmend:
    def test_p15a01_appends_three_presentation_batches(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "increment-1"], ["increment-2"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        ids = [b["batch_id"] for b in out["plan"]["batches"]]
        assert ids == ["v0", "increment-1", "increment-2",
                       "presentation-1", "presentation-2", "presentation-3"]

    def test_p15a02_story_ids_derived_from_slug(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        sids = {s["story_id"] for s in out["new_stories"]}
        assert "story-presentation-1-s1a" in sids and "story-presentation-1-docs" in sids

    def test_p15a03_first_story_anchored_on_last_verified_doc(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "increment-1"], ["increment-2"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        first = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-1-s1a"][0]
        assert first["depends_on"] == ["story-increment-1-docs"]

    def test_p15a04_pending_increment_does_not_block_or_anchor(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "increment-1"], ["increment-2"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        all_deps = {d for s in out["new_stories"] for d in s["depends_on"]}
        assert "story-increment-2-docs" not in all_deps and "story-increment-2-a" not in all_deps

    def test_p15a05_sequential_chain_within_batch(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        ladder = _ladder({1: [_ladder_story("first"), _ladder_story("second")]})
        out = a.build_presentation_amend(plan, st, ladder, "1.2.0", _PATHS)
        second = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-1-second"][0]
        assert second["depends_on"] == ["story-presentation-1-first"]

    def test_p15a06_doc_story_last_depends_members(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        ladder = _ladder({1: [_ladder_story("first"), _ladder_story("second")]})
        out = a.build_presentation_amend(plan, st, ladder, "1.2.0", _PATHS)
        batch = [b for b in out["plan"]["batches"] if b["batch_id"] == "presentation-1"][0]
        assert batch["story_ids"][-1] == "story-presentation-1-docs"
        doc = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-1-docs"][0]
        assert set(doc["depends_on"]) == {"story-presentation-1-first", "story-presentation-1-second"}

    def test_p15a07_idempotent_existing_batches_skipped(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "presentation-1"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        new_ids = [b["batch_id"] for b in out["plan"]["batches"]]
        assert new_ids.count("presentation-1") == 1
        first2 = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-2-s2a"][0]
        assert first2["depends_on"] == ["story-presentation-1-docs"]

    def test_p15a08_materials_carry_ladder_supersedes_manifest(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        out = a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
        s3 = [s for s in out["new_stories"] if s["story_id"] == "story-presentation-3-s3a"][0]
        assert s3["materials"]["ladder_rung_path"] == _PATHS["ladder_path"]
        assert s3["materials"]["supersedes_paths"] == ["Plugins/DemoX/Tests/R2Impl.cpp"]
        assert s3["manifest_version"] == "1.2.0"
        assert s3["story_kind"] == "presentation"
        assert s3["story_schema_version"] == "1.1.0"

    def test_p15a09_deterministic_rung_order_input_invariant(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        ladder = _ladder()
        shuffled = dict(ladder)
        shuffled["rungs"] = list(reversed(ladder["rungs"]))
        assert a.build_presentation_amend(plan, st, ladder, "1.2.0", _PATHS) == \
               a.build_presentation_amend(plan, st, shuffled, "1.2.0", _PATHS)

    def test_p15a10_no_verified_base_fails_closed(self):
        a = _load("amend")
        plan, st = _plan_and_stories([], ["v0"])
        with pytest.raises(ValueError, match="基底"):
            a.build_presentation_amend(plan, st, _ladder(), "1.2.0", _PATHS)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py -v`
Expected: 10 failed/error(amend.py 不存在)

- [ ] **Step 3: 写 amend.py(本 Task 只含呈现批;反馈批函数 Task 4 追加)**

```python
# -*- coding: utf-8 -*-
"""demo_plan 批次追加(amend):呈现批(阶梯数据驱动)与反馈批共用一个机制入口。

防固化硬约束(Phase 15 spec §9):
本模块零游戏领域语义——只消费 rung_id/story_slug/supersedes/severity 等结构字段,
"棋盘""token"等语义只存在于项目层阶梯实例/反馈条目里。
纯函数、确定性:同(现 plan + 阶梯/反馈)输入同输出;
自包含,不 import 包内其他模块(story_store 同款先例,importlib 单文件加载友好)。
"""
from typing import Any, Dict, List

PLAN_SCHEMA_VERSION = "1.1.0"
STORY_SCHEMA_VERSION = "1.1.0"


def _last_verified_tail(plan: Dict[str, Any], stories_by_id: Dict[str, Any]) -> str:
    """plan 顺序上最后一个全 verified 批的末位 story_id;无 → None(调用处 fail-closed)。"""
    tail = None
    for batch in plan["batches"]:
        ids = batch["story_ids"]
        if ids and all(stories_by_id[s]["status"] == "verified" for s in ids):
            tail = ids[-1]
    return tail


def _base_materials(paths: Dict[str, Any]) -> Dict[str, Any]:
    """materials 公共骨架(模板字段一律 null:呈现/反馈/文档工单不绑模板)。"""
    return {
        "gdd_path": paths["gdd_path"],
        "gdd_anchors": [],
        "contract_path": paths["contract_path"],
        "skill_graph_path": paths["skill_graph_path"],
        "template_id": None,
        "template_source": None,
        "template_dir": None,
        "construction_manifest_path": paths["construction_manifest_path"],
        "extra_paths": [],
    }


def _doc_story(batch_id: str, member_ids: List[str], manifest_version: str,
               paths: Dict[str, Any]) -> Dict[str, Any]:
    """批末文档 story(与 planner._doc_story 同形;自包含模块故意复写,不抽公共)。"""
    materials = _base_materials(paths)
    materials["extra_paths"] = list(paths.get("doc_extra_paths", []))
    return {
        "story_schema_version": STORY_SCHEMA_VERSION,
        "story_id": f"story-{batch_id}-docs",
        "batch_id": batch_id,
        "story_kind": "documentation",
        "evidence_class": "Config",
        "depends_on": list(member_ids),
        "materials": materials,
        "acceptance_criteria": [
            "维护文档包按施工规范 §6 写入 demo plugin 的 Docs/ 目录(设计/架构/changelog)",
            "文档只描述已 verified 的实现;结构性内容自 run 产物投影,头部标注生成物口径",
            "文档中引用的类/资产经机器引用对账存在",
        ],
        "status": "pending",
        "attempts": 0,
        "manifest_version": manifest_version,
    }


def build_presentation_amend(plan: Dict[str, Any], stories_by_id: Dict[str, Any],
                             ladder: Dict[str, Any], manifest_version: str,
                             paths: Dict[str, Any]) -> Dict[str, Any]:
    """追加呈现批:每 rung 一批(presentation-<rung_id>),批内 story 按阶梯顺序链式依赖。

    返回 {"plan": 新 plan, "new_stories": [...]}(stories_by_id 不修改);
    已存在的 presentation 批跳过(幂等),其末位作为下一批锚点。
    """
    existing = {b["batch_id"]: b for b in plan["batches"]}
    anchor = _last_verified_tail(plan, stories_by_id)
    if anchor is None:
        raise ValueError("amend: 没有全 verified 的基底批,呈现批必须建立在可玩基底上(fail-closed)")
    new_batches: List[Dict[str, Any]] = []
    new_stories: List[Dict[str, Any]] = []
    prev_tail = anchor
    for rung in sorted(ladder["rungs"], key=lambda r: int(r["rung_id"])):
        batch_id = f"presentation-{rung['rung_id']}"
        if batch_id in existing:
            prev_tail = existing[batch_id]["story_ids"][-1]
            continue
        member_ids: List[str] = []
        for entry in rung["stories"]:
            story_id = f"story-{batch_id}-{entry['story_slug']}"
            materials = _base_materials(paths)
            materials["gdd_anchors"] = list(rung.get("gdd_anchors", []))
            materials["ladder_rung_path"] = paths["ladder_path"]
            materials["supersedes_paths"] = list(rung.get("supersedes", []))
            story = {
                "story_schema_version": STORY_SCHEMA_VERSION,
                "story_id": story_id,
                "batch_id": batch_id,
                "story_kind": "presentation",
                "evidence_class": entry["evidence_class"],
                "depends_on": [member_ids[-1] if member_ids else prev_tail],
                "interaction_claims": list(entry.get("interaction_claims", [])),
                "materials": materials,
                "acceptance_criteria": list(entry["requirements"]) + [
                    "demo plugin 编译通过且全部已冻结层冒烟不退化(证据: smoke_report)",
                    f"按 evidence_class={entry['evidence_class']} 提交全部必交证据并通过机器校验",
                    "宣称交互逐条有 InteractionSemantics 用例对应且通过(行为校验门禁)",
                    "设计取舍零提问: 未定点给默认值并记入 provisional_decisions",
                ],
                "status": "pending",
                "attempts": 0,
                "manifest_version": manifest_version,
            }
            new_stories.append(story)
            member_ids.append(story_id)
        doc = _doc_story(batch_id, member_ids, manifest_version, paths)
        new_stories.append(doc)
        new_batches.append({"batch_id": batch_id, "story_ids": member_ids + [doc["story_id"]]})
        prev_tail = doc["story_id"]
    new_plan = dict(plan)
    new_plan["plan_schema_version"] = PLAN_SCHEMA_VERSION
    new_plan["batches"] = list(plan["batches"]) + new_batches
    return {"plan": new_plan, "new_stories": new_stories}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py -v`
Expected: 10 passed

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/amend.py Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py
git commit -m "[skip-doc] feat(phase15): amend 呈现批追加——阶梯数据驱动/锚点机械规则/幂等/确定性"
```

### Task 4: amend.py — 反馈批追加

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/demo_plan/amend.py`(末尾追加函数)
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py`(追加 p15a11~13)

- [ ] **Step 1: 追加失败测试**

```python
def _entry(fid, status="open", phenomenon="现象X", expectation="期望Y"):
    return {"feedback_schema_version": "1.0.0", "feedback_id": fid, "window_id": "w1",
            "phenomenon": phenomenon, "expectation": expectation, "severity": "major",
            "related_rung": None, "related_capability": None, "status": status}


class TestFeedbackAmend:
    def test_p15a11_feedback_one_story_per_entry_plus_doc(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "presentation-1"])
        out = a.build_feedback_amend(plan, st, [_entry("fb-w1-01"), _entry("fb-w1-02")],
                                     "1.2.0", _PATHS)
        batch = out["plan"]["batches"][-1]
        assert batch["batch_id"] == "feedback-1"
        assert batch["story_ids"] == ["story-feedback-1-fb-w1-01", "story-feedback-1-fb-w1-02",
                                      "story-feedback-1-docs"]
        s1 = [s for s in out["new_stories"] if s["story_id"] == "story-feedback-1-fb-w1-01"][0]
        assert s1["story_kind"] == "feedback"
        assert s1["depends_on"] == ["story-presentation-1-docs"]
        assert s1["materials"]["feedback_path"] == f"{_PATHS['feedback_dir']}/fb-w1-01.json"
        assert any("现象X" in c for c in s1["acceptance_criteria"])

    def test_p15a12_feedback_batch_numbering_increments(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0", "feedback-1"])
        out = a.build_feedback_amend(plan, st, [_entry("fb-w2-01")], "1.2.0", _PATHS)
        assert out["plan"]["batches"][-1]["batch_id"] == "feedback-2"

    def test_p15a13_feedback_sorted_and_no_open_fails_closed(self):
        a = _load("amend")
        plan, st = _plan_and_stories(["v0"])
        out = a.build_feedback_amend(
            plan, st, [_entry("fb-w1-02"), _entry("fb-w1-01")], "1.2.0", _PATHS)
        assert out["plan"]["batches"][-1]["story_ids"][0] == "story-feedback-1-fb-w1-01"
        with pytest.raises(ValueError, match="open"):
            a.build_feedback_amend(plan, st, [_entry("fb-w1-01", status="resolved")],
                                   "1.2.0", _PATHS)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py -v -k Feedback`
Expected: 3 failed(build_feedback_amend 不存在)

- [ ] **Step 3: amend.py 末尾追加函数**

```python
def build_feedback_amend(plan: Dict[str, Any], stories_by_id: Dict[str, Any],
                         entries: List[Dict[str, Any]], manifest_version: str,
                         paths: Dict[str, Any]) -> Dict[str, Any]:
    """追加一个反馈批:open 条目按 feedback_id 字典序,每条一个 story(机械规则零 LLM)。

    批号 = 已有 feedback 批数 + 1(每个人审窗口切一批);无 open 条目 → fail-closed。
    """
    open_entries = sorted((e for e in entries if e.get("status") == "open"),
                          key=lambda e: e["feedback_id"])
    if not open_entries:
        raise ValueError("amend: 没有 open 状态的反馈条目,反馈批无可切(fail-closed)")
    anchor = _last_verified_tail(plan, stories_by_id)
    if anchor is None:
        raise ValueError("amend: 没有全 verified 的基底批(fail-closed)")
    seq = 1 + sum(1 for b in plan["batches"] if str(b["batch_id"]).startswith("feedback-"))
    batch_id = f"feedback-{seq}"
    member_ids: List[str] = []
    new_stories: List[Dict[str, Any]] = []
    prev_tail = anchor
    for entry in open_entries:
        story_id = f"story-{batch_id}-{entry['feedback_id']}"
        materials = _base_materials(paths)
        materials["feedback_path"] = f"{paths['feedback_dir']}/{entry['feedback_id']}.json"
        story = {
            "story_schema_version": STORY_SCHEMA_VERSION,
            "story_id": story_id,
            "batch_id": batch_id,
            "story_kind": "feedback",
            "evidence_class": "Integration",
            "depends_on": [prev_tail],
            "materials": materials,
            "acceptance_criteria": [
                f"复现并修复反馈现象: {entry['phenomenon']}",
                f"达成期望行为: {entry['expectation']}",
                "demo plugin 编译通过且全部已冻结层冒烟不退化(证据: smoke_report)",
                "按 evidence_class=Integration 提交全部必交证据并通过机器校验",
            ],
            "status": "pending",
            "attempts": 0,
            "manifest_version": manifest_version,
        }
        new_stories.append(story)
        member_ids.append(story_id)
        prev_tail = story_id
    doc = _doc_story(batch_id, member_ids, manifest_version, paths)
    new_stories.append(doc)
    new_plan = dict(plan)
    new_plan["plan_schema_version"] = PLAN_SCHEMA_VERSION
    new_plan["batches"] = list(plan["batches"]) + [
        {"batch_id": batch_id, "story_ids": member_ids + [doc["story_id"]]}]
    return {"plan": new_plan, "new_stories": new_stories}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py -v`
Expected: 13 passed

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/amend.py Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py
git commit -m "[skip-doc] feat(phase15): amend 反馈批追加——open 条目机械切批/窗口批号递增"
```

---

### Task 5: CLI --amend-presentation / --amend-feedback

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/demo_plan_main.py`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py`(追加 p15a14~15)

- [ ] **Step 1: 追加失败测试**

```python
class TestAmendCli:
    def _seed_run(self, tmp):
        """最小已完成 run:v0 批全 verified + 必需产物。"""
        plan = {"plan_schema_version": "1.1.0", "run_id": "r-cli", "source_graph_id": "g",
                "manifest_version": "1.0.0",
                "batches": [{"batch_id": "v0", "story_ids": ["story-v0-a", "story-v0-docs"]}]}
        base_mat = {"gdd_path": "ProjectInputs/GDD/x.md",
                    "gdd_anchors": [], "contract_path": "c.json", "skill_graph_path": "s.json",
                    "template_id": None, "template_source": None, "template_dir": None,
                    "construction_manifest_path": "m.md", "extra_paths": []}
        (tmp / "stories").mkdir(parents=True)
        for sid, kind, ec in (("story-v0-a", "presentation", "Integration"),
                              ("story-v0-docs", "documentation", "Config")):
            story = {"story_schema_version": "1.1.0", "story_id": sid, "batch_id": "v0",
                     "story_kind": kind, "evidence_class": ec, "depends_on": [],
                     "materials": dict(base_mat), "acceptance_criteria": ["x"],
                     "status": "verified", "attempts": 0, "manifest_version": "1.0.0"}
            (tmp / "stories" / f"{sid}.json").write_text(json.dumps(story), encoding="utf-8")
        (tmp / "demo_plan.json").write_text(json.dumps(plan), encoding="utf-8")
        ladder = {"ladder_schema_version": "1.0.0", "ladder_id": "ladder-cli",
                  "target_plugin_root": "Plugins/DemoX",
                  "rungs": [{"rung_id": 1, "title": "R1", "gdd_anchors": [], "supersedes": [],
                             "stories": [{"story_slug": "s1", "summary": "x",
                                          "evidence_class": "Integration",
                                          "requirements": ["r"]}]}]}
        ladder_path = tmp / "ladder.json"
        ladder_path.write_text(json.dumps(ladder), encoding="utf-8")
        return ladder_path

    def _run_cli(self, project_root, *argv):
        import subprocess, sys
        cli = Path(project_root) / "Plugins" / "AgentBridge" / "Scripts" / "demo_plan_main.py"
        return subprocess.run([sys.executable, str(cli), *argv],
                              capture_output=True, text=True, cwd=project_root)

    def test_p15a14_cli_amend_presentation_writes_plan_and_stories(self, workspace_tmp_path, project_root):
        ladder_path = self._seed_run(workspace_tmp_path)
        result = self._run_cli(project_root, "--run-dir", str(workspace_tmp_path),
                               "--amend-presentation", "--ladder", str(ladder_path))
        assert result.returncode == 0, result.stderr
        plan = json.loads((workspace_tmp_path / "demo_plan.json").read_text(encoding="utf-8"))
        assert [b["batch_id"] for b in plan["batches"]] == ["v0", "presentation-1"]
        assert plan["plan_schema_version"] == "1.1.0"
        assert (workspace_tmp_path / "stories" / "story-presentation-1-s1.json").exists()

    def test_p15a15_cli_amend_fails_closed_on_missing_ladder(self, workspace_tmp_path, project_root):
        self._seed_run(workspace_tmp_path)
        result = self._run_cli(project_root, "--run-dir", str(workspace_tmp_path),
                               "--amend-presentation")
        assert result.returncode == 2
        assert "--ladder" in (result.stderr + result.stdout) and "Traceback" not in result.stderr
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py -v -k Cli`
Expected: 2 failed(CLI 不识别 --amend-presentation)

- [ ] **Step 3: 改 demo_plan_main.py**

3a. 把 main() 内嵌套的 `atomic_write` 提升为模块级函数(原嵌套定义删除,main 内改调用 `_atomic_write`):

```python
def _atomic_write(path: Path, data) -> None:
    """与 story_store 同款事务形状(.part 暂存 + os.replace 原子换名)。"""
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
```

3b. main() 的 argparse 段追加三个参数(--manifest 之后):

```python
    parser.add_argument("--amend-presentation", action="store_true",
                        help="追加呈现批(读 --ladder 阶梯实例,幂等)")
    parser.add_argument("--amend-feedback", action="store_true",
                        help="把 run 目录 feedback/ 下 open 条目切为一个反馈批")
    parser.add_argument("--ladder", default=None,
                        help="呈现阶梯实例 JSON 路径(--amend-presentation 必填)")
```

3c. parse_args 之后、读 skill_graph 之前插入分流(amend 模式不需要 skill_graph/contract):

```python
    if args.amend_presentation and args.amend_feedback:
        print("[FAIL] --amend-presentation 与 --amend-feedback 互斥,一次只追加一类批", file=sys.stderr)
        return 2
    if args.amend_presentation or args.amend_feedback:
        return _run_amend(args, run_dir)
```

3d. 新增模块级函数 `_run_amend`(放 main 之前):

```python
def _run_amend(args, run_dir: Path) -> int:
    """amend 模式:读现 plan + stories 状态,追加呈现/反馈批,schema 校验后原子落盘。

    与首切同口径:输入缺件/损坏不许裸 traceback,统一 [FAIL] + 退出码 2。
    """
    import jsonschema
    if args.amend_presentation and not args.ladder:
        print("[FAIL] --amend-presentation 需要 --ladder <阶梯实例路径>", file=sys.stderr)
        return 2
    try:
        plan = json.loads((run_dir / "demo_plan.json").read_text(encoding="utf-8"))
        stories_by_id = {}
        for sp in sorted((run_dir / "stories").glob("story-*.json")):
            story = json.loads(sp.read_text(encoding="utf-8"))
            stories_by_id[story["story_id"]] = story
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] run 目录产物不可读: {exc}", file=sys.stderr)
        return 2
    if not stories_by_id:
        print("[FAIL] stories/ 为空,amend 需要已有切批产物", file=sys.stderr)
        return 2

    ml = _load("manifest_loader")
    amend = _load("amend")
    _, manifest_version = ml.load_construction_manifest(
        PROJECT_ROOT, path=Path(args.manifest) if args.manifest else None)

    def rel(p):
        return str(p).replace("\\", "/")

    # 公共路径自既有 story 的 materials 继承(amend 不重新推导 GDD/契约路径,保持同 run 一致)
    sample = next(iter(stories_by_id.values()))
    paths = {
        "gdd_path": sample["materials"]["gdd_path"],
        "contract_path": sample["materials"]["contract_path"],
        "skill_graph_path": sample["materials"]["skill_graph_path"],
        "construction_manifest_path": sample["materials"]["construction_manifest_path"],
        "doc_extra_paths": [rel(run_dir / "demo_plan.json"), rel(run_dir / "velocity_log.json")],
        "ladder_path": rel(args.ladder) if args.ladder else None,
        "feedback_dir": rel(run_dir / "feedback"),
    }

    entries = []
    try:
        if args.amend_presentation:
            ladder_schema = json.loads(
                (PLUGIN_ROOT / "Schemas" / "presentation_ladder.schema.json").read_text(encoding="utf-8"))
            ladder = json.loads(Path(args.ladder).read_text(encoding="utf-8"))
            jsonschema.validate(ladder, ladder_schema)
            out = amend.build_presentation_amend(plan, stories_by_id, ladder, manifest_version, paths)
        else:
            for ep in sorted((run_dir / "feedback").glob("fb-*.json")):
                entries.append(json.loads(ep.read_text(encoding="utf-8")))
            out = amend.build_feedback_amend(plan, stories_by_id, entries, manifest_version, paths)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] amend 输入不可读: {exc}", file=sys.stderr)
        return 2
    except (ValueError, jsonschema.ValidationError) as exc:
        print(f"[FAIL] amend 失败: {exc}", file=sys.stderr)
        return 2

    # 新产物 schema 自校验(与首切同口径,机器守门)
    schemas_dir = PLUGIN_ROOT / "Schemas"
    plan_schema = json.loads((schemas_dir / "demo_plan.schema.json").read_text(encoding="utf-8"))
    story_schema = json.loads((schemas_dir / "demo_story.schema.json").read_text(encoding="utf-8"))
    try:
        jsonschema.validate(out["plan"], plan_schema)
        for story in out["new_stories"]:
            jsonschema.validate(story, story_schema)
    except jsonschema.ValidationError as exc:
        print(f"[FAIL] amend 产物 schema 校验失败: {exc.message}(路径: {list(exc.path)})", file=sys.stderr)
        return 2

    # 落盘:先 stories 后 plan(plan 是顺序权威,最后原子换名);反馈条目置 in_batch
    stories_dir = run_dir / "stories"
    stories_dir.mkdir(exist_ok=True)
    for story in out["new_stories"]:
        _atomic_write(stories_dir / f"{story['story_id']}.json", story)
    _atomic_write(run_dir / "demo_plan.json", out["plan"])
    if args.amend_feedback:
        for entry in entries:
            if entry.get("status") == "open":
                entry["status"] = "in_batch"
                _atomic_write(run_dir / "feedback" / f"{entry['feedback_id']}.json", entry)

    added = len(out["plan"]["batches"]) - len(plan["batches"])
    print(f"[OK] amend 落盘: +{added} 批 / +{len(out['new_stories'])} story → {run_dir}")
    return 0
```

- [ ] **Step 4: 跑测试确认通过 + phase14 CLI 回归**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py -v`
Expected: 15 passed
Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -v`
Expected: 17 passed(普通切批路径不受 amend 分流影响)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Scripts/demo_plan_main.py Plugins/AgentBridge/Tests/scripts/test_phase15_amend.py
git commit -m "[skip-doc] feat(phase15): demo_plan CLI amend 模式——呈现/反馈批追加落盘 + 条目 in_batch 流转"
```

### Task 6: evidence_validator — BL-01 路径越界 + 呈现批截图必交

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py`
- Create: `Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py`

- [ ] **Step 1: 写失败测试(新建文件,本 Task 落 p15b01~02)**

```python
# -*- coding: utf-8 -*-
"""PRX 行为门禁组:BL-01 越界 / 呈现截图必交 / interaction_claims 对账 / 冻结分层 + supersedes。"""
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


def _story(batch_id="presentation-1", kind="presentation", ec="Integration",
           claims=None, supersedes=None):
    """最小 story(validator 只读这些字段,无需全 schema 字段)。"""
    return {"story_id": "story-x", "batch_id": batch_id, "story_kind": kind,
            "evidence_class": ec, "interaction_claims": claims or [],
            "materials": {"supersedes_paths": supersedes or []}}


def _touch(root: Path, rel: str, text="x") -> str:
    """在 root 下落一个文件,返回相对路径(正斜杠)。"""
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return rel.replace("\\", "/")


def _smoke(root: Path, rel="smoke.json", status="pass", regression="pass") -> str:
    return _touch(root, rel, json.dumps({"status": status, "v0_regression": regression}))


class TestPathAndScreenshotGate:
    def test_p15b01_path_traversal_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        smoke = _smoke(workspace_tmp_path)
        out = ev.validate_evidence(
            _story(), {"files_changed": ["../outside.txt"], "smoke_report": smoke,
                       "screenshots": [_touch(workspace_tmp_path, "shot.png")]},
            workspace_tmp_path, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("越界" in e for e in out["errors"])

    def test_p15b02_presentation_requires_screenshots(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        smoke = _smoke(workspace_tmp_path)
        out = ev.validate_evidence(
            _story(), {"files_changed": [smoke], "smoke_report": smoke},
            workspace_tmp_path, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("screenshots" in e for e in out["errors"])
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py -v`
Expected: 2 failed(validate_evidence 不接受 frozen_layers 参数 / 无越界与截图检查)

- [ ] **Step 3: 改 evidence_validator.py(三处)**

3a. `validate_evidence` 签名加参(向后兼容,缺省 None):

```python
def validate_evidence(story: Dict[str, Any], evidence: Dict[str, Any], project_root,
                      baseline: Optional[Dict[str, Any]] = None,
                      plugin_root=None,
                      frozen_layers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
```

3b. 第 1 段(分级必交)之后追加呈现批截图必交(按 batch 前缀的结构判断,零领域语义):

```python
    # ── 1b. 呈现批附加必交:真实截图(Phase 15 spec §4.3 第 3 道) ──────────────
    if str(story.get("batch_id", "")).startswith("presentation") and evidence.get("screenshots") is None:
        errors.append("缺少必交证据字段: screenshots(呈现批必交真实截图)")
```

3c. 第 2 段(路径存在检查)整段替换为越界 + 存在双检(P14-BL-01,同 MCP plugin_root 口径):

```python
    # ── 2. 路径越界 + 存在检查(P14-BL-01:resolve 后必须仍在项目根内) ────────
    root_resolved = root.resolve()
    for field, rel in _iter_paths(evidence):
        target = root / rel
        try:
            resolved = target.resolve()
        except OSError as exc:
            errors.append(f"证据路径不可解析: {field} -> {rel}({exc})")
            continue
        if not resolved.is_relative_to(root_resolved):
            errors.append(f"证据路径越界: {field} -> {rel} 不在项目根内(P14-BL-01 守门)")
            continue
        if not target.exists():
            errors.append(f"证据路径不存在: {field} -> {rel}")
```

- [ ] **Step 4: 跑测试确认通过 + phase14 validator 回归**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py -v`
Expected: 2 passed
Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py -v`
Expected: 15 passed(新参数缺省 None、新检查不触及既有用例路径——若有用例用了越界路径会暴露真问题,如实修 fixture)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py
git commit -m "[skip-doc] feat(phase15): evidence_validator BL-01 路径越界守门 + 呈现批截图必交"
```

---

### Task 7: evidence_validator — interaction_claims 行为校验三道对账(BL-05)

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py`(追加 p15b03~07)

**对账语义(钉死,防实施期漂移):**
- token 全集 = story.interaction_claims 的 input 集 ∪ README『## 键位』节的 `[Key]` token 集;
- 全集中每个 key 必须在 test_report.suites 里有名字含 `InteractionSemantics.<Key>` 且 state 为通过态的用例(C4 教训:README 写了键位、代码没行为 → 这里拒);
- claims ⊆ README token(代码有行为、文档必须宣称);
- claims 为空时本门禁整体放行(玩法/文档/反馈工单不强制)。

- [ ] **Step 1: 追加失败测试**

```python
def _report(root: Path, suites, rel="test_report.json") -> str:
    """test_report 与冒烟报告同形({suites:[{name,state}]})。"""
    return _touch(root, rel, json.dumps({"suites": suites}))


def _readme(root: Path, plugin_rel: str, keys) -> Path:
    """写 plugin README,含『## 键位』节。返回 plugin 绝对根。"""
    lines = ["# Demo", "", "## 键位", ""] + [f"- [{k}] 某操作" for k in keys] + ["", "## 其他", "x"]
    p = root / plugin_rel / "README.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("\n".join(lines), encoding="utf-8")
    return root / plugin_rel


_CLAIM = [{"input": "Space", "behavior": "推进回合"}]


class TestInteractionClaims:
    # 行为校验与批前缀无关;用 batch_id="v0"(非守门批)隔离被测变量,
    # 避免空 frozen_layers 触发守门批"冻结基线缺失"拒绝干扰断言
    def _story_claims(self):
        return _story(batch_id="v0", claims=_CLAIM)

    def _evidence(self, root, suites, keys=("Space",)):
        smoke = _smoke(root)
        return {"files_changed": [smoke], "smoke_report": smoke,
                "screenshots": [_touch(root, "shot.png")],
                "test_report": _report(root, suites),
                "plugin_root": "Plugins/DemoX"}, _readme(root, "Plugins/DemoX", keys)

    def test_p15b03_claim_without_passing_case_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(workspace_tmp_path, suites=[])
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("InteractionSemantics.Space" in e for e in out["errors"])

    def test_p15b04_claim_with_failing_case_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "fail"}])
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"

    def test_p15b05_claim_with_passing_case_and_readme_passes(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "Success"}])
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "verified", out["errors"]

    def test_p15b06_readme_key_without_behavior_case_rejected(self, workspace_tmp_path):
        # C4 教训本尊:README 宣称 [Enter] 但没有对应 InteractionSemantics 用例
        ev = _load("evidence_validator")
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "Success"}],
            keys=("Space", "Enter"))
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("InteractionSemantics.Enter" in e for e in out["errors"])

    def test_p15b07_claim_missing_from_readme_or_no_section_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        # 7a: README 键位节没宣称 claim 的键
        evidence, plugin = self._evidence(
            workspace_tmp_path,
            suites=[{"name": "DemoX.InteractionSemantics.Space", "state": "Success"}],
            keys=())
        out = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                   plugin_root=plugin, frozen_layers={})
        assert out["status"] == "rejected"
        assert any("未宣称" in e for e in out["errors"])
        # 7b: README 缺『## 键位』节
        (workspace_tmp_path / "Plugins" / "DemoX" / "README.md").write_text("# 无键位节", encoding="utf-8")
        out2 = ev.validate_evidence(self._story_claims(), evidence, workspace_tmp_path,
                                    plugin_root=plugin, frozen_layers={})
        assert out2["status"] == "rejected"
        assert any("键位" in e for e in out2["errors"])
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py -v -k Interaction`
Expected: 5 failed

- [ ] **Step 3: evidence_validator.py 追加行为校验**

3a. 模块顶部常量区追加:

```python
# 行为校验(P14-BL-05):InteractionSemantics 用例通过态 + README 键位 token
_PASS_STATES = {"success", "passed", "pass"}
_KEY_TOKEN = re.compile(r"\[([A-Za-z0-9]+)\]")
```

3b. 模块级新函数(放 `_check_doc_references` 之后):

```python
def _readme_key_tokens(readme_text: str) -> Optional[set]:
    """提取 README『## 键位』节中的 [Key] token;无该节返回 None(调用处报错)。"""
    lines = readme_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("## ") and "键位" in line:
            start = i + 1
            break
    if start is None:
        return None
    section = []
    for line in lines[start:]:
        if line.strip().startswith("## "):
            break
        section.append(line)
    return set(_KEY_TOKEN.findall("\n".join(section)))


def _check_interaction_claims(story: Dict[str, Any], evidence: Dict[str, Any],
                              root: Path, plugin_root) -> List[str]:
    """行为校验门禁(P14-BL-05):claims∪README 全集逐 key 对 InteractionSemantics 用例,
    claims ⊆ README。claims 为空整体放行(玩法/文档/反馈工单不强制)。"""
    claims = story.get("interaction_claims") or []
    if not claims:
        return []
    report_rel = evidence.get("test_report")
    if not report_rel or not (root / str(report_rel)).exists():
        return ["行为校验: interaction_claims 非空时必须提交 test_report(InteractionSemantics 用例报告)"]
    try:
        report = json.loads((root / str(report_rel)).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"行为校验: test_report 不可解析: {exc}"]
    suites = report.get("suites") if isinstance(report, dict) else None
    if not isinstance(suites, list):
        return ["行为校验: test_report 缺 suites 数组(报告契约与冒烟报告同形)"]
    passing = {str(s.get("name", "")) for s in suites
               if str(s.get("state", "")).lower() in _PASS_STATES}

    errors: List[str] = []
    claimed = {c["input"] for c in claims}
    readme_tokens: set = set()
    if plugin_root is None:
        errors.append("行为校验: interaction_claims 非空时 evidence 必须带 plugin_root(README 对账需要)")
    else:
        readme = Path(plugin_root) / "README.md"
        if not readme.exists():
            errors.append("行为校验: plugin README.md 不存在,无法做键位对账")
        else:
            tokens = _readme_key_tokens(readme.read_text(encoding="utf-8", errors="ignore"))
            if tokens is None:
                errors.append("行为校验: README 缺『## 键位』节(施工规范 §8 要求,机器对账锚)")
            else:
                readme_tokens = tokens
                for missing in sorted(claimed - tokens):
                    errors.append(f"行为校验: README 键位节未宣称 [{missing}](代码有行为文档没写)")
    # 全集逐 key 必须有通过的 InteractionSemantics 用例(C4 教训:文档写了键位代码没行为)
    for key in sorted(claimed | readme_tokens):
        token = f"InteractionSemantics.{key}"
        if not any(token in name for name in passing):
            errors.append(f"行为校验: 键位 [{key}] 无通过的 {token} 用例(命名约定见施工规范 §8)")
    return errors
```

3c. `validate_evidence` 第 5 段(文档对账)之前插入调用:

```python
    # ── 4b. 行为校验门禁(P14-BL-05) ────────────────────────────────────────
    errors.extend(_check_interaction_claims(story, evidence, root, plugin_root))
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py -v`
Expected: 7 passed
Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py -v`
Expected: 15 passed(phase14 story 无 interaction_claims 字段 → 门禁整体放行)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py
git commit -m "[skip-doc] feat(phase15): 行为校验门禁(BL-05)——claims/README/InteractionSemantics 三方对账"
```

### Task 8: evidence_validator — 分层冻结 frozen_baselines + supersedes 放行 + submit 接线

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py`
- Modify: `Plugins/AgentBridge/MCP/compiler_tools.py:804-853`(demo_story_submit)
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py`(追加 p15b08~10)

**冻结分层语义(spec §4.6):** `frozen_baselines.json` = `{"layers": {"<层名>": {"files": {...}, "frozen_at": ...}}}`;守门批(increment/presentation/feedback 前缀)逐层 hash 对账;story.materials.supersedes_paths(阶梯 authored 数据,非 agent 自报)中的文件放行改动/删除。既有 `v0_smoke_baseline.json` 原样兼容(继续作为 v0 层检查)。

- [ ] **Step 1: 追加失败测试**

```python
class TestFrozenLayers:
    def test_p15b08_frozen_layer_modified_rejected(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        guarded = _touch(workspace_tmp_path, "Plugins/DemoX/Tests/ContractTests.cpp", "v1")
        layer = ev.freeze_layer(workspace_tmp_path, workspace_tmp_path,
                                "presentation-contract-rung1", [guarded])
        assert layer["files"][guarded]
        (workspace_tmp_path / guarded).write_text("v2-tampered", encoding="utf-8")
        smoke = _smoke(workspace_tmp_path)
        frozen = json.loads((workspace_tmp_path / "frozen_baselines.json").read_text(encoding="utf-8"))
        out = ev.validate_evidence(
            _story(batch_id="presentation-2"),
            {"files_changed": [smoke], "smoke_report": smoke,
             "screenshots": [_touch(workspace_tmp_path, "s.png")]},
            workspace_tmp_path, frozen_layers=frozen["layers"])
        assert out["status"] == "rejected"
        assert any("presentation-contract-rung1" in e and "被修改" in e for e in out["errors"])

    def test_p15b09_supersedes_exempts_declared_file(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        guarded = _touch(workspace_tmp_path, "Plugins/DemoX/Tests/R2Impl.cpp", "v1")
        ev.freeze_layer(workspace_tmp_path, workspace_tmp_path, "rung2-impl", [guarded])
        (workspace_tmp_path / guarded).unlink()  # rung3 退役该实现用例文件
        smoke = _smoke(workspace_tmp_path)
        frozen = json.loads((workspace_tmp_path / "frozen_baselines.json").read_text(encoding="utf-8"))
        out = ev.validate_evidence(
            _story(batch_id="presentation-3", supersedes=[guarded]),
            {"files_changed": [smoke], "smoke_report": smoke,
             "screenshots": [_touch(workspace_tmp_path, "s.png")]},
            workspace_tmp_path, frozen_layers=frozen["layers"])
        assert out["status"] == "verified", out["errors"]

    def test_p15b10_gated_batch_requires_regression_pass_and_some_baseline(self, workspace_tmp_path):
        ev = _load("evidence_validator")
        # 10a: 守门批但回归段 fail → 拒
        smoke_bad = _smoke(workspace_tmp_path, rel="bad.json", regression="fail")
        out = ev.validate_evidence(
            _story(batch_id="feedback-1", kind="feedback"),
            {"files_changed": [smoke_bad], "smoke_report": smoke_bad},
            workspace_tmp_path, frozen_layers={"l": {"files": {}}})
        assert out["status"] == "rejected"
        assert any("回归" in e for e in out["errors"])
        # 10b: 守门批但既无 baseline 也无 frozen_layers → 拒
        smoke_ok = _smoke(workspace_tmp_path, rel="ok.json")
        out2 = ev.validate_evidence(
            _story(batch_id="feedback-1", kind="feedback"),
            {"files_changed": [smoke_ok], "smoke_report": smoke_ok},
            workspace_tmp_path, baseline=None, frozen_layers=None)
        assert out2["status"] == "rejected"
        assert any("冻结基线" in e for e in out2["errors"])
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py -v -k Frozen`
Expected: 3 failed(freeze_layer 不存在等)

- [ ] **Step 3: 改 evidence_validator.py(四处)**

3a. 常量区追加:

```python
# 守门批前缀:增量 / 呈现 / 反馈批都受冻结层 hash 守门与回归门约束
_GATED_PREFIXES = ("increment", "presentation", "feedback")
```

3b. `freeze_v0_baseline` 之后追加分层冻结函数:

```python
def freeze_layer(project_root, run_dir, layer_name: str,
                 file_rel_paths: List[str]) -> Dict[str, Any]:
    """冻结一层判据文件 hash(逻辑层/各 rung 呈现契约层/实现层),
    追加进 run 目录 frozen_baselines.json(.part 原子写)。
    验收 runbook 在 rung verified / msc PROCEED 时调用(v0 沿用 freeze_v0_baseline 不迁移)。"""
    root = Path(project_root)
    files = {str(rel).replace("\\", "/"): _sha256(root / rel) for rel in file_rel_paths}
    path = Path(run_dir) / "frozen_baselines.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"layers": {}}
    data["layers"][layer_name] = {"files": files,
                                  "frozen_at": datetime.now(timezone.utc).isoformat()}
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return data["layers"][layer_name]
```

3c. `_check_baseline` 加 exempt/layer 参数(签名与正文替换):

```python
def _check_baseline(project_root: Path, baseline: Dict[str, Any],
                    exempt=frozenset(), layer: str = "v0") -> List[str]:
    """对比现有文件 hash 与冻结基线;exempt 为阶梯 supersedes 显式退役清单(authored 数据)。"""
    errors = []
    for rel, expected in baseline.get("files", {}).items():
        if rel in exempt:
            continue  # supersedes 显式声明放行(退役非作弊)
        target = project_root / rel
        if not target.exists():
            errors.append(f"hash 守门[{layer}]: 基线文件缺失 {rel}(退役须经阶梯 supersedes 声明)")
        elif _sha256(target) != expected:
            errors.append(f"hash 守门[{layer}]: 基线文件被修改 {rel}(冻结层不许动;退役须经阶梯 supersedes 声明)")
    return errors
```

3d. `validate_evidence` 内:第 3 段 smoke 检查中 `startswith("increment")` 行改为守门批口径,第 4 段整段替换:

```python
                # 守门批(增量/呈现/反馈)还须冻结层回归通过
                if str(story.get("batch_id", "")).startswith(_GATED_PREFIXES) \
                        and report.get("v0_regression") != "pass":
                    errors.append(f"守门批要求冻结层回归 pass,实际: {report.get('v0_regression')}")
```

```python
    # ── 4. 守门批冻结基线检查(v0 基线 + frozen_baselines 分层;supersedes 放行) ──
    if str(story.get("batch_id", "")).startswith(_GATED_PREFIXES):
        exempt = frozenset(str(p).replace("\\", "/")
                           for p in (story.get("materials") or {}).get("supersedes_paths") or [])
        if baseline is None and not frozen_layers:
            errors.append("守门批必须提供冻结基线(v0_smoke_baseline 或 frozen_baselines,先在人审/rung 验收时冻结)")
        if baseline is not None:
            errors.extend(_check_baseline(root, baseline, exempt=exempt, layer="v0"))
        for layer_name in sorted(frozen_layers or {}):
            errors.extend(_check_baseline(root, (frozen_layers or {})[layer_name],
                                          exempt=exempt, layer=layer_name))
```

- [ ] **Step 4: compiler_tools.demo_story_submit 接线(两处)**

4a. baseline 读取段之后追加 frozen_layers 读取,validator 调用加参:

```python
        if result is None:
            baseline = None
            baseline_path = Path(session_path) / "v0_smoke_baseline.json"
            if baseline_path.exists():
                baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            frozen_layers = None
            frozen_path = Path(session_path) / "frozen_baselines.json"
            if frozen_path.exists():
                frozen_layers = json.loads(frozen_path.read_text(encoding="utf-8")).get("layers", {})
            result = evidence_validator.validate_evidence(
                story, evidence, root, baseline=baseline, plugin_root=plugin_root,
                frozen_layers=frozen_layers)
```

4b. `updated = store.submit(...)` 之后、velocity 之前追加反馈条目 resolved 流转(失败降级 warnings,镜像 synthesis_save 的 review_path 先例):

```python
        warnings: list[str] = []
        if updated["status"] == "verified" and updated.get("story_kind") == "feedback":
            fb_rel = (updated.get("materials") or {}).get("feedback_path")
            if fb_rel:
                try:
                    fb_path = root / str(fb_rel)
                    entry = json.loads(fb_path.read_text(encoding="utf-8"))
                    entry["status"] = "resolved"
                    tmp = fb_path.with_suffix(".json.part")
                    tmp.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
                    tmp.replace(fb_path)
                except (OSError, json.JSONDecodeError) as exc:
                    warnings.append(f"反馈条目 resolved 流转失败(story 已 verified): {exc}")
```

并把该函数末尾 `_make_response` 加 `warnings=warnings`。

- [ ] **Step 5: 跑测试确认通过 + 回归**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py -v`
Expected: 10 passed
Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase14_evidence_validator.py Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py -v`
Expected: 全 passed(increment 批走 baseline 路径不变;submit 新逻辑只对 feedback story 生效)

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Compiler/demo_plan/evidence_validator.py Plugins/AgentBridge/MCP/compiler_tools.py Plugins/AgentBridge/Tests/scripts/test_phase15_behavior_gate.py
git commit -m "[skip-doc] feat(phase15): 分层冻结 frozen_baselines + supersedes 放行 + feedback resolved 流转"
```

---

### Task 9: smoke runner — BL-04 errorMessage 透传 + 多段回归过滤器

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/demo_smoke/runner.py`
- Create: `Plugins/AgentBridge/Tests/scripts/test_phase15_smoke_runner.py`

- [ ] **Step 1: 写失败测试**

```python
# -*- coding: utf-8 -*-
"""PRX smoke runner 组:BL-04 errorMessage 透传 + 冻结层多段回归聚合。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "runner", PLUGIN_ROOT / "Scripts" / "demo_smoke" / "runner.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestSmokeRunnerP15:
    def test_p15r01_suites_carry_error_messages(self, workspace_tmp_path):
        r = _load_runner()
        index = {"succeeded": 0, "failed": 1, "notRun": 0,
                 "tests": [{"fullTestPath": "DemoX.Smoke.A", "state": "Fail",
                            "entries": [
                                {"event": {"type": "Error", "message": "Assertion failed: X"}},
                                {"event": {"type": "Info", "message": "noise"}}]}]}
        (workspace_tmp_path / "index.json").write_text(json.dumps(index), encoding="utf-8")
        report = r.build_smoke_report(workspace_tmp_path, "n/a", [])
        assert report["suites"][0]["errors"] == ["Assertion failed: X"]

    def test_p15r02_aggregate_all_pass(self):
        r = _load_runner()
        assert r.aggregate_regression(["pass", "pass"]) == "pass"

    def test_p15r03_aggregate_any_fail(self):
        r = _load_runner()
        assert r.aggregate_regression(["pass", "fail"]) == "fail"

    def test_p15r04_aggregate_empty_is_na(self):
        r = _load_runner()
        assert r.aggregate_regression([]) == "n/a"

    def test_p15r05_collect_filters_merges_v0_and_regression(self):
        r = _load_runner()
        parser = r.build_parser()
        args = parser.parse_args(["--filter", "X", "--out", "o.json",
                                  "--v0-filter", "A", "--regression-filter", "B",
                                  "--regression-filter", "C"])
        assert r.collect_regression_filters(args) == ["A", "B", "C"]
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_smoke_runner.py -v`
Expected: 5 failed

- [ ] **Step 3: 改 runner.py(四处)**

3a. `build_smoke_report` 的 suites 行替换(BL-04:Error 事件 message 透传):

```python
        "suites": [{"name": t.get("fullTestPath", ""), "state": t.get("state", ""),
                    "errors": [str(e.get("event", {}).get("message", ""))
                               for e in t.get("entries", [])
                               if str(e.get("event", {}).get("type", "")).lower() == "error"]}
                   for t in data.get("tests", [])],
```

3b. argparse 段抽成模块级 `build_parser()`(main 内改调 `build_parser().parse_args()`),并追加参数:

```python
def build_parser() -> argparse.ArgumentParser:
    """CLI 参数定义(抽出便于纯函数测试)。"""
    parser = argparse.ArgumentParser(description="Phase 14/15 demo 冒烟 runner")
    parser.add_argument("--filter", required=True, help="Automation 测试过滤器")
    parser.add_argument("--v0-filter", default=None, help="v0 回归段过滤器(兼容保留,与 --regression-filter 合并)")
    parser.add_argument("--regression-filter", action="append", default=[],
                        help="冻结层回归过滤器(可重复:逐 rung 契约段等)")
    parser.add_argument("--out", required=True, help="输出报告 JSON 路径")
    parser.add_argument("--editor-cmd", default=os.environ.get("AGENTBRIDGE_UE_CMD", ""),
                        help="UnrealEditor-Cmd.exe 路径,缺省读 AGENTBRIDGE_UE_CMD")
    parser.add_argument("--screenshots", nargs="*", default=[], help="附加截图路径列表")
    return parser


def collect_regression_filters(args) -> list:
    """合并 v0 兼容口径与多段回归过滤器(顺序稳定:v0 在前)。"""
    return ([args.v0_filter] if args.v0_filter else []) + list(args.regression_filter)


def aggregate_regression(states: list) -> str:
    """聚合冻结层回归段:全 pass → pass;任一非 pass → fail;空 → n/a。"""
    if not states:
        return "n/a"
    return "pass" if all(s == "pass" for s in states) else "fail"
```

3c. main() 内 v0 回归段替换为多段循环(报告契约键 `v0_regression` 保留——validator 消费它,语义升级为"全部冻结层回归"):

```python
        # 冻结层回归段(可多段):逐段单跑,聚合进 v0_regression(键名兼容 validator 契约)
        segments = []
        for i, reg_filter in enumerate(collect_regression_filters(args), start=1):
            seg_dir = work / f"regression_{i}"
            run_automation(Path(args.editor_cmd), uprojects[0], reg_filter, seg_dir,
                           work / f"regression_{i}.log")
            seg_state = "pass" if build_smoke_report(seg_dir, "n/a", [])["status"] == "pass" else "fail"
            segments.append({"filter": reg_filter, "status": seg_state})
        v0_state = aggregate_regression([s["status"] for s in segments])
```

3d. 主冒烟段之后、写报告之前,把分段明细附进报告:

```python
        report["regression_segments"] = segments
```

- [ ] **Step 4: 跑测试确认通过 + phase14 runner 回归**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_smoke_runner.py Plugins/AgentBridge/Tests/scripts/test_phase14_smoke_runner.py -v`
Expected: 5 + 7 passed(若 phase14 用例断言 suites 形状,新增 errors 键是增量字段——有断言钉死全键集就如实更新该用例并在 commit message 记录)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Scripts/demo_smoke/runner.py Plugins/AgentBridge/Tests/scripts/test_phase15_smoke_runner.py
git commit -m "[skip-doc] feat(phase15): smoke runner BL-04 errorMessage 透传 + 冻结层多段回归聚合"
```

### Task 10: MCP 工具 demo_feedback_log(57→58)

**Files:**
- Modify: `Plugins/AgentBridge/MCP/compiler_tools.py`(demo_story_submit 之后追加)
- Modify: `Plugins/AgentBridge/MCP/tool_definitions.py:443-452`(COMPILER_FRONTEND_TOOLS 段尾)
- Modify: `Plugins/AgentBridge/MCP/server.py:808`(dispatch 表 demo_story_submit 行后)
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py:60-62`(工具数 57→58)
- Create: `Plugins/AgentBridge/Tests/scripts/test_phase15_feedback_tool.py`

- [ ] **Step 1: 写失败测试(新文件)+ 改 phase14 工具数断言**

新文件:

```python
# -*- coding: utf-8 -*-
"""PRX 反馈工具组:demo_feedback_log 三处注册 + 落盘 + 序号 + 校验拒绝 + velocity。"""
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _import_mcp(name):
    """以包内文件方式加载 MCP 模块(test_phase14_mcp_tools 同款)。"""
    if str(PLUGIN_ROOT) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT))
    spec = importlib.util.spec_from_file_location(name, PLUGIN_ROOT / "MCP" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _entry(**over):
    base = {"window_id": "w1", "phenomenon": "拍卖面板当前价不刷新",
            "expectation": "出价后当前价即时刷新", "severity": "major",
            "related_rung": 1, "related_capability": None}
    base.update(over)
    return base


class TestFeedbackTool:
    def test_p15f01_tool_definitions_registered(self):
        td = _import_mcp("tool_definitions")
        assert "demo_feedback_log" in td.COMPILER_FRONTEND_TOOLS

    def test_p15f02_tool_count_is_58(self):
        td = _import_mcp("tool_definitions")
        assert td.TOOL_COUNT == 58

    def test_p15f03_server_dispatch_registered(self):
        src = (PLUGIN_ROOT / "MCP" / "server.py").read_text(encoding="utf-8")
        assert '"demo_feedback_log"' in src

    def test_p15f04_log_writes_entry_open_with_sequential_id(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        out = ct.demo_feedback_log(session_path=str(workspace_tmp_path), entry=_entry())
        assert out["status"] == "success"
        assert out["data"]["feedback_id"] == "fb-w1-01"
        saved = json.loads((workspace_tmp_path / "feedback" / "fb-w1-01.json")
                           .read_text(encoding="utf-8"))
        assert saved["status"] == "open" and saved["feedback_schema_version"] == "1.0.0"

    def test_p15f05_second_entry_increments_seq(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        ct.demo_feedback_log(session_path=str(workspace_tmp_path), entry=_entry())
        out = ct.demo_feedback_log(session_path=str(workspace_tmp_path),
                                   entry=_entry(phenomenon="第二条"))
        assert out["data"]["feedback_id"] == "fb-w1-02"

    def test_p15f06_invalid_entry_failed(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        out = ct.demo_feedback_log(session_path=str(workspace_tmp_path),
                                   entry=_entry(severity="urgent"))
        assert out["status"] == "failed"
        assert out["errors"]
        assert not list((workspace_tmp_path / "feedback").glob("*.json"))

    def test_p15f07_velocity_event_appended(self, workspace_tmp_path):
        ct = _import_mcp("compiler_tools")
        ct.demo_feedback_log(session_path=str(workspace_tmp_path), entry=_entry())
        log = json.loads((workspace_tmp_path / "velocity_log.json").read_text(encoding="utf-8"))
        assert any(e.get("kind") == "feedback_log" and e.get("feedback_id") == "fb-w1-01"
                   for e in log["events"])
```

phase14 文件:`test_dmp34_tool_count_is_57` 改名 `test_dmp34_tool_count_is_58`,断言改 `assert td.TOOL_COUNT == 58`(文件头注释"工具数 57"同步改 58)。

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_feedback_tool.py Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py -v`
Expected: phase15 7 条 failed;dmp34 failed(TOOL_COUNT 仍 57)

- [ ] **Step 3: compiler_tools.py 追加工具函数(demo_story_submit 之后)**

```python
def demo_feedback_log(session_path: str, entry: dict,
                      project_root: Optional[str] = None) -> dict:
    """登记一条试玩窗口反馈条目(Phase 15 反馈回流入口)。

    设计要点:
      - feedback_id 由工具按窗口内序号生成(fb-<window_id>-NN),调用方不可指定(防撞号);
      - 条目经 feedback_entry.schema 校验后才落盘;不合法 → status="failed"
        (登记是人审窗口操作,改对参数直接重调,无 in_progress 重试态);
      - .part 原子写 + velocity 留痕(与 story 流转同口径);project_root 仅测试注入。
    """
    try:
        import jsonschema  # 延迟导入,镜像 demo_plan_main 的用法
        schema_path = Path(__file__).resolve().parents[1] / "Schemas" / "feedback_entry.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        feedback_dir = Path(session_path) / "feedback"
        feedback_dir.mkdir(parents=True, exist_ok=True)
        window_id = str(entry.get("window_id", ""))
        seq = 1 + sum(1 for _ in feedback_dir.glob(f"fb-{window_id}-*.json"))
        record = dict(entry)
        record["feedback_schema_version"] = "1.0.0"
        record["feedback_id"] = f"fb-{window_id}-{seq:02d}"
        record["status"] = "open"
        jsonschema.validate(record, schema)
        path = feedback_dir / f"{record['feedback_id']}.json"
        tmp = path.with_suffix(".json.part")
        tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
        velocity.append_event(session_path, {"kind": "feedback_log",
                                             "feedback_id": record["feedback_id"],
                                             "severity": record.get("severity")})
        return _make_response(
            "success",
            f"反馈已登记: {record['feedback_id']}(severity={record.get('severity')})",
            data={"feedback_id": record["feedback_id"],
                  "path": str(path).replace("\\", "/")},
        )
    except Exception as exc:  # ValidationError/OSError/JSONDecodeError 统一 failed(镜像 synthesis_save 末段)
        return _make_response(
            "failed",
            f"demo_feedback_log 失败: {exc}",
            errors=[f"TOOL_EXECUTION_FAILED: {exc}"],
        )
```

- [ ] **Step 4: tool_definitions.py 注册(demo_story_submit 条目之后)**

```python
    "demo_feedback_log": {
        "description": "Phase 15 反馈回流:登记一条试玩窗口反馈条目(结构化:现象/期望/严重度),落 run 目录 feedback/,状态 open;之后由 demo_plan CLI --amend-feedback 确定性切 feedback 批。",
        "params": {
            "session_path": {"type": "string", "required": True, "description": "run 目录路径"},
            "entry": {"type": "object", "required": True, "description": "window_id/phenomenon/expectation/severity(/related_rung/related_capability);feedback_id 与 status 由工具生成"},
        },
        "returns": "data.feedback_id / data.path;status=success/failed(failed 含条目 schema 不合法——登记是人审窗口操作,改对参数重调即可)",
    },
```

- [ ] **Step 5: server.py dispatch 表追加(demo_story_submit 行之后)**

```python
        "demo_feedback_log": ("compiler", compiler_tools.demo_feedback_log),
```

- [ ] **Step 6: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_feedback_tool.py Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py -v`
Expected: 7 + 7 passed(TOOL_COUNT==58)

- [ ] **Step 7: Commit**

```bash
git add Plugins/AgentBridge/MCP/compiler_tools.py Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py Plugins/AgentBridge/Tests/scripts/test_phase14_mcp_tools.py Plugins/AgentBridge/Tests/scripts/test_phase15_feedback_tool.py
git commit -m "[skip-doc] feat(phase15): MCP demo_feedback_log 工具(57→58)——窗口反馈结构化登记"
```

---

### Task 11: 项目层输入 — 阶梯实例 + 施工规范 1.2.0

**Files:**
- Create: `ProjectInputs/PresentationLadder/monopoly_demo_ladder.json`
- Modify: `ProjectInputs/ConstructionManifest/demo_plugin_standards.md`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py`(追加 p15s07)

- [ ] **Step 1: 追加失败测试(实例文件对 schema 校验,防 authored 数据漂移)**

```python
class TestProjectLadderInstance:
    def test_p15s07_real_monopoly_ladder_validates(self, project_root):
        schema = _schema("presentation_ladder.schema.json")
        ladder_path = (Path(project_root) / "ProjectInputs" / "PresentationLadder"
                       / "monopoly_demo_ladder.json")
        ladder = json.loads(ladder_path.read_text(encoding="utf-8"))
        jsonschema.validate(ladder, schema)
        assert [r["rung_id"] for r in ladder["rungs"]] == [1, 2, 3]
```

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py -v -k p15s07`
Expected: 1 failed(实例文件不存在)

- [ ] **Step 2: 写阶梯实例(完整内容;游戏语义只在此文件,机制零感知)**

`ProjectInputs/PresentationLadder/monopoly_demo_ladder.json`:

```json
{
  "ladder_schema_version": "1.0.0",
  "ladder_id": "ladder-monopoly-demo-v1",
  "target_plugin_root": "Plugins/Demo_MonopolyAuction",
  "rungs": [
    {
      "rung_id": 1,
      "title": "UMG 信息面板化(文字 HUD → 结构化面板)",
      "gdd_anchors": ["4.1 HUD 常驻扩展", "4.2 弹出式 UI 扩展"],
      "supersedes": [],
      "stories": [
        {
          "story_slug": "hud-panels",
          "summary": "HUD 从 5 行文本块升级为结构化面板:回合/阶段指示器、玩家卡片(色块+资金条)、拍卖弹窗面板、事件提示区;FMADemoHUDSnapshot 快照接口保持不变",
          "evidence_class": "Integration",
          "requirements": [
            "HUD 呈现回合数/阶段/当前玩家高亮的指示区,数据仅来自 GameState 快照",
            "每位玩家一张卡片:名称色块、资金数值与资金条,当前回合玩家有可见高亮",
            "拍卖进行时屏幕中央弹出拍卖面板:地产名称、当前最高价高亮、出价/弃权提示(GDD 3.1)",
            "呈现参数(配色/布局尺寸)进 DataAsset,C++ 不硬编码可调参数",
            "保持 FMADemoHUDSnapshot 接口与既有冒烟用例不变;新增呈现契约用例(信息可见性,施工规范 §8)"
          ],
          "interaction_claims": [
            {"input": "Space", "behavior": "推进回合,HUD 回合指示区同步刷新"},
            {"input": "Enter", "behavior": "拍卖中出价,拍卖面板当前价刷新"},
            {"input": "Esc", "behavior": "暂停并弹出暂停面板"}
          ]
        },
        {
          "story_slug": "frontend-panels",
          "summary": "前台外壳(开始/主菜单/设置/暂停/结果)从 presence_only 文本条目升级为真按钮+布局",
          "evidence_class": "Integration",
          "requirements": [
            "五个前台面板均有标题区与按钮区布局,按钮可聚焦可触发既有意图函数",
            "结果面板呈现胜者信息(来自 GameState),按钮可返回主菜单",
            "面板间导航走既有意图函数(NavigateToMainMenu/IntentNewGame 等),不新增规则逻辑"
          ],
          "interaction_claims": []
        }
      ]
    },
    {
      "rung_id": 2,
      "title": "2D 棋盘可视化",
      "gdd_anchors": ["1. 游戏概述", "3.1 拍卖界面"],
      "supersedes": [],
      "stories": [
        {
          "story_slug": "board-2d",
          "summary": "UMG 2D 棋盘:环形地块布局、地产组配色、归属标记、当前拍卖地块高亮,数据从 GameState 快照拉取",
          "evidence_class": "Integration",
          "requirements": [
            "棋盘以环形布局呈现全部地块,地块按地产组配色(配色进 DataAsset)",
            "地块呈现归属状态(无主/各玩家色),拍卖中地块有可见高亮",
            "棋盘 widget 只读 GameState 快照,不持有规则逻辑(施工规范 §8 呈现分层)"
          ],
          "interaction_claims": []
        },
        {
          "story_slug": "board-tokens",
          "summary": "玩家 token 在 2D 棋盘上随位置移动,当前回合玩家 token 高亮",
          "evidence_class": "Integration",
          "requirements": [
            "每位玩家一个 token,位置与 GameState 玩家位置一致,回合推进后移动",
            "当前回合玩家 token 有可见高亮",
            "token 移动允许简单插值动画;无动画立即落位亦可,记 provisional"
          ],
          "interaction_claims": [
            {"input": "Space", "behavior": "推进回合,token 移动到新位置"}
          ]
        }
      ]
    },
    {
      "rung_id": 3,
      "title": "3D 场景化(棋盘 mesh + 棋子 actor + 相机)",
      "gdd_anchors": ["1. 游戏概述", "3.1 拍卖界面"],
      "supersedes": [
        "Plugins/Demo_MonopolyAuction/Source/Demo_MonopolyAuction/Private/Tests/MADemoPresentationRung2Tests.cpp"
      ],
      "stories": [
        {
          "story_slug": "board-3d",
          "summary": "程序化 3D 棋盘落入 L_MonopolyDemo:引擎基础几何拼地块环 + 动态材质实例着色 + 地块标签;演进现关卡非重建",
          "evidence_class": "Integration",
          "requirements": [
            "3D 棋盘由引擎自带基础几何程序化生成(施工规范 §7,禁外部资产导入)",
            "地块按地产组着色(动态材质实例),归属/拍卖中状态在 3D 棋盘上可见",
            "棋盘生成落 authored 关卡 L_MonopolyDemo,关卡加载冒烟保持通过"
          ],
          "interaction_claims": []
        },
        {
          "story_slug": "pawn-actors",
          "summary": "玩家棋子 actor(基础几何),GameState 位置驱动插值移动",
          "evidence_class": "Integration",
          "requirements": [
            "每位玩家一个棋子 actor,位置由 GameState 驱动,回合推进后插值移动到目标地块",
            "当前回合玩家棋子有可见标识(高亮/浮标)",
            "棋子 actor 只读 GameState,不持有规则逻辑"
          ],
          "interaction_claims": [
            {"input": "Space", "behavior": "推进回合,3D 棋子移动到新地块"}
          ]
        },
        {
          "story_slug": "camera-integration",
          "summary": "固定机位 CameraActor + HUD 面板叠加保留;2D 棋盘 widget 退役(supersedes 已声明)",
          "evidence_class": "Integration",
          "requirements": [
            "固定机位 CameraActor 俯视/斜视棋盘,允许简单插值运镜,禁复杂 cinematic(施工规范 §7)",
            "rung1 的 HUD 面板与拍卖面板继续叠加呈现,全部呈现契约用例保持通过",
            "2D 棋盘 widget 自画面退役,其实现用例按 supersedes 声明退役;信息可见性由呈现契约用例守住"
          ],
          "interaction_claims": [
            {"input": "Space", "behavior": "推进回合,3D 视角下回合信息与棋子状态同步刷新"},
            {"input": "Enter", "behavior": "拍卖中出价,拍卖面板在 3D 场景上叠加刷新"},
            {"input": "Esc", "behavior": "暂停并弹出暂停面板(3D 场景上叠加)"}
          ]
        }
      ]
    }
  ]
}
```

- [ ] **Step 3: 施工规范升 1.2.0(四处改动)**

3a. 首行 `manifest_version: 1.1.0` → `manifest_version: 1.2.0`;标题行 `v1.1` → `v1.2`;头部修订注记追加一行:

```markdown
> 1.2.0 修订(Phase 15):§4 补呈现用例文件约定;§7 补程序化 3D 通路;新增 §8 呈现层架构约束——
> 见 `Docs/superpowers/specs/2026-06-12-phase15-presentation-axis-design.md`。
```

3b. §4 末尾追加:

```markdown
- **呈现用例文件约定(Phase 15)**:呈现契约用例集中 `Private/Tests/<模块前缀>PresentationContractTests.cpp`
  (逐 rung 验收后冻结,断言信息可见性,禁绑具体 widget 类名);呈现实现用例按 rung 分文件
  `Private/Tests/<模块前缀>PresentationRung<N>Tests.cpp`(可被后续 rung 经阶梯 supersedes 声明退役);
  交互行为用例命名 `<PluginName>.InteractionSemantics.<Input>`(行为校验门禁按此对账)
```

3c. §7 末尾追加:

```markdown
- **程序化 3D 通路(Phase 15)**:3D 棋盘/棋子一律用引擎自带基础几何(`/Engine/BasicShapes/` 的
  Cube/Plane/Cylinder/Sphere)+ 动态材质实例(MID)程序化配色 + TextRender 或 widget component 做标签;
  **禁外部资产导入**(无美术管线);相机限定固定机位 CameraActor + 简单插值运镜,禁复杂 cinematic;
  3D 摆放可运行时程序化生成(GameMode/专责 actor 在 BeginPlay 构建),不强制落 .umap 编辑器资产
```

3d. 文件末尾新增 §8:

```markdown
## 8. 呈现层架构约束(Phase 15 新增)

- 呈现只读 GameState 快照(`FMADemoHUDSnapshot` 形状先例):呈现组件不查询规则、不改状态、只发意图
- 呈现组件三层独立可替换:HUD 面板 / 棋盘渲染 / 世界 actor,层间不互相持有,各自可单独退役
- 配色/布局/尺寸等呈现参数一律进 DataAsset(`Content/Data/`),C++ 不硬编码
- **呈现批不得改玩法逻辑文件**(GameMode/GameState/PlayerData 等;冻结层 hash 守门技术钉死)
- **README 必须含『## 键位』节**,键位用 `[Key]` 方括号 token 标注(行为校验门禁的机器对账锚);
  每个键位必须有通过的 `<PluginName>.InteractionSemantics.<Key>` 用例
- **呈现契约用例形状**(逐 rung 冻结):GameState API 直驱到目标局面 → 经呈现快照接口取值 →
  断言信息可见(如"拍卖进行时快照含拍卖地块标识与当前价")+ 呈现入口存在(viewport 有注册的呈现根);
  禁止断言具体 widget 类名/控件树结构(那属实现用例,可随 rung 替换退役)
```

- [ ] **Step 4: 跑测试确认通过(manifest 版本回归一并验)**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py Plugins/AgentBridge/Tests/scripts/test_phase14_demo_plan.py -v`
Expected: 7 + 17 passed(dmp31 只锚定语义化三段格式,不钉具体版本值,1.2.0 不破)

- [ ] **Step 5: Commit**

```bash
git add ProjectInputs/PresentationLadder/monopoly_demo_ladder.json ProjectInputs/ConstructionManifest/demo_plugin_standards.md Plugins/AgentBridge/Tests/scripts/test_phase15_schemas.py
git commit -m "[skip-doc] feat(phase15): 阶梯实例 monopoly_demo_ladder + 施工规范 1.2.0(3D 通路/呈现层约束/键位对账锚)"
```

### Task 12: 系统测试 Stage 15 注册(PRX-01~44)

**Files:**
- Modify: `Plugins/AgentBridge/Tests/run_system_tests.py`(STAGES 表 / CASE_ID_PATTERN / run_stage_15 / dispatch 表)
- Modify: `Plugins/AgentBridge/Tests/SystemTestCases.md`(PRX 登记段)

- [ ] **Step 1: STAGES 表追加 15 号 stage(14 号条目之后)**

```python
    15: {
        'name': 'Phase 15 Presentation Axis（PRX）',
        'cases': 'PRX-01 ~ PRX-44（5 个 test_phase15_* 文件）',
        'case_ids': make_case_ids('PRX', 1, 44),
        'count': 44,
        'requires_editor': False,
        'requires_build': False,
    },
```

同文件 `TOTAL_CASES` 行注释更新为 `# 464 (420 + P15 PRX-01~44 加 44)`;`CASE_ID_PATTERN` 的前缀组 `|SKS|DMP)` 改为 `|SKS|DMP|PRX)`。

- [ ] **Step 2: run_stage_15 函数(放 run_stage_14 之后,镜像其结构)**

```python
def run_stage_15(result, engine_root, completed_results=None):
    """Stage 15：Phase 15 Presentation Axis — PRX-01~44 用例。

    5 个 test_phase15_*.py 文件按 pytest 收集顺序（文件名字母序）连续编号：
      PRX-01~15: test_phase15_amend.py          （amend 呈现批/反馈批/CLI）
      PRX-16~25: test_phase15_behavior_gate.py  （BL-01/截图/行为校验/冻结分层）
      PRX-26~32: test_phase15_feedback_tool.py  （MCP demo_feedback_log）
      PRX-33~39: test_phase15_schemas.py        （schema 1.1.0 + 新 schema + 阶梯实例）
      PRX-40~44: test_phase15_smoke_runner.py   （BL-04 + 多段回归聚合）

    注：登记编号为文件段顺序编号；判据与 Stage 14 同款——pytest 全绿 + 实收数 == 登记数。
    """
    check_map = {}
    runtime_dir = os.path.join(PROJECT_ROOT, 'ProjectState', 'Temp', 'run_system_tests_stage15')
    os.makedirs(runtime_dir, exist_ok=True)
    result.log_path = runtime_dir

    # 文件名 -> (PRX 起始编号, 期望用例数)；登记数与 pytest --co 实收数挂钩，漂移即 FAIL
    phase15_test_files = [
        ('test_phase15_amend.py', 1, 15),
        ('test_phase15_behavior_gate.py', 16, 10),
        ('test_phase15_feedback_tool.py', 26, 7),
        ('test_phase15_schemas.py', 33, 7),
        ('test_phase15_smoke_runner.py', 40, 5),
    ]

    file_notes = []
    for file_name, start_id, expected_count in phase15_test_files:
        exit_code, stdout, stderr = run_pytest_selection(
            [os.path.join(TESTS_SCRIPTS_DIR, file_name)], timeout=900
        )
        passed_match = re.search(r'(\d+)\s+passed', stdout)
        failed_match = re.search(r'(\d+)\s+failed', stdout)
        skipped_match = re.search(r'(\d+)\s+skipped', stdout)
        n_pass = int(passed_match.group(1)) if passed_match else 0
        n_fail = int(failed_match.group(1)) if failed_match else 0
        n_skip = int(skipped_match.group(1)) if skipped_match else 0

        log_path = os.path.join(runtime_dir, f'{file_name}_pytest.log')
        try:
            with open(log_path, 'w', encoding='utf-8') as fp:
                fp.write(f'cmd_exit={exit_code}\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n')
        except Exception:
            pass

        ok = (
            exit_code == 0
            and n_fail == 0
            and (n_pass + n_skip) == expected_count
        )
        range_label = f'PRX-{start_id:02d}~PRX-{start_id + expected_count - 1:02d}'
        note = (
            f'{file_name}: pytest passed={n_pass} failed={n_fail} skipped={n_skip} '
            f'exit={exit_code} 登记={expected_count}'
        )
        file_notes.append((range_label, ok, note))
        for case_index in range(start_id, start_id + expected_count):
            check_map[f'PRX-{case_index:02d}'] = (ok, note)

    summary_path = os.path.join(runtime_dir, 'phase15_case_checks.json')
    with open(summary_path, 'w', encoding='utf-8') as file:
        json.dump(
            {
                'generated_at': datetime.datetime.now().isoformat(),
                'cases': {
                    case_id: {'ok': ok, 'note': note}
                    for case_id, (ok, note) in check_map.items()
                },
            },
            file,
            ensure_ascii=False,
            indent=2,
        )

    missing_case_ids = [case_id for case_id in STAGES[15]['case_ids'] if case_id not in check_map]
    if missing_case_ids:
        result.status = 'failed'
        result.exit_code = 1
        result.message = f'Stage 15 用例注册不完整，缺失: {", ".join(missing_case_ids)}'
        return

    checks = [
        (case_id, check_map[case_id][0], check_map[case_id][1])
        for case_id in STAGES[15]['case_ids']
    ]
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    failed_cases = [case_id for case_id, ok, _ in checks if not ok]
```

(本函数余下的"按文件分段打印 + result 状态落定"段:逐行镜像 `run_stage_14` 同位置代码,只把字符串里的 `Stage 14`/`phase14` 换成 `Stage 15`/`phase15`——run_stage_14 紧邻其上,照抄即可。)

- [ ] **Step 3: dispatch 表挂接(`14: run_stage_14,` 行之后)**

```python
    15: run_stage_15,
```

- [ ] **Step 4: SystemTestCases.md 登记**

先看既有 DMP 段格式:`grep -n "DMP-01" Plugins/AgentBridge/Tests/SystemTestCases.md`,镜像其表格列结构,在 DMP 段之后新增"Stage 15(PRX)"段——44 行,逐行格式与 DMP 行一致,内容按 run_stage_15 docstring 的文件段映射展开,例如(列结构以实际文件为准):

```markdown
| PRX-01 | Stage 15 | test_phase15_amend.py:test_p15a01 呈现批追加三批次序 | 纯 Python |
```

44 行覆盖:p15a01~15(PRX-01~15)、p15b01~10(PRX-16~25)、p15f01~07(PRX-26~32)、p15s01~07(PRX-33~39)、p15r01~05(PRX-40~44)。漏登会被 run_system_tests 的 CASE_ID_PATTERN 对账抓住(机器守门,登记不完整 Stage 15 直接 FAIL)。

- [ ] **Step 5: 跑 Stage 15 验证挂接**

Run: `python Plugins/AgentBridge/Tests/run_system_tests.py --stage 15`(若 CLI 用其他 stage 选择参数,以 `python Plugins/AgentBridge/Tests/run_system_tests.py --help` 实际输出为准)
Expected: Stage 15 PASS,44/44;`ProjectState/Temp/run_system_tests_stage15/phase15_case_checks.json` 落盘
Run: `python -c "import sys; sys.path.insert(0, 'Plugins/AgentBridge/Tests'); import run_system_tests as r; print(r.TOTAL_CASES)"`
Expected: `464`

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Tests/run_system_tests.py Plugins/AgentBridge/Tests/SystemTestCases.md
git commit -m "[skip-doc] feat(phase15): 系统测试 Stage 15 登记 PRX-01~44(总数 420→464)"
```

---

### Task 13: spec 修订记录 + 全量回归收口

**Files:**
- Modify: `Docs/superpowers/specs/2026-06-12-phase15-presentation-axis-design.md`(顶部追加修订记录)
- 无新代码;本 Task 是机器证据收口

- [ ] **Step 1: spec 顶部状态行之后追加实施期修订记录(Phase 14 spec 同款形状)**

```markdown
> **实施期修订记录:**
> - R1(plan Task 1/3):呈现 story 用独立 `story_kind: "presentation"`(spec §4.2 原文只点名 +feedback;
>   复用 capability 需伪造 capability_id/instance_id,违背 schema 条件约束本意)。
> - R2(plan Task 1):磁盘上 Phase 14 既有 run 的 1.0.0 story 不回写不重校验;amend 只新增 1.1.0 产物,
>   plan 文件在 amend 时升 1.1.0(store 不做 schema 校验,验收 runbook 用新 CLI 自校验口径)。
> - R3(plan Task 8):呈现契约/实现用例的冻结落地为 `frozen_baselines.json` 分层(layer 命名由 runbook 定,
>   建议 `rung<N>-contract` / `rung<N>-impl`),v0 沿用 `v0_smoke_baseline.json` 不迁移;
>   supersedes 放行经 story.materials.supersedes_paths(authored 阶梯数据,非 agent 自报)。
> - R4(plan Task 9):runner 报告契约键 `v0_regression` 保留(validator 兼容),语义升级为"全部冻结层回归聚合";
>   分段明细新增 `regression_segments`。
```

- [ ] **Step 2: 全量机器证据(逐条跑,输出留存)**

```bash
python -m pytest Plugins/AgentBridge/Tests/scripts -k phase15 -v
```
Expected: **44 passed**

```bash
python -m pytest Plugins/AgentBridge/Tests/scripts -k phase14 -v
```
Expected: **56 passed**(dmp34 已升 58 断言)

```bash
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```
Expected: **32/32**

```bash
python Plugins/AgentBridge/Tests/run_system_tests.py --stage 14 && python Plugins/AgentBridge/Tests/run_system_tests.py --stage 15
```
Expected: 两个 stage 均 PASS(stage 选择参数以 --help 为准)

```bash
git diff main --stat -- Plugins/AgentBridge/Source Plugins/AgentBridge/Scripts/bridge Plugins/AgentBridge/Scripts/orchestrator/orchestrator.py Plugins/AgentBridge/AgentBridgeTests
```
Expected: 空输出(红线零触碰;orchestrator 下只允许 handoff_runner/run_plan_builder 有 diff,本期应为零)

- [ ] **Step 3: Commit + 收口**

```bash
git add Docs/superpowers/specs/2026-06-12-phase15-presentation-axis-design.md
git commit -m "[skip-doc] docs(phase15): spec 实施期修订记录 R1-R4"
```

随后走 `superpowers:verification-before-completion`,把上述命令的真实输出落盘 `ProjectState/Reports/<当日>/phase15_mechanism_verification.md` 后,才许宣称机制层完成。

---

## 验收期交接(不属本 plan,防误执行)

机制层 13 个 Task 完成后,Phase 15 进入验收(主会话驱动,Phase 14 runbook 同款形状):

1. 验收 runbook 落 `ProjectState/Reports/<当日>/phase15_acceptance_runbook.md`(C1-C6 对照 spec §7)。
2. `demo_plan_main.py --run-dir <Phase14 run 目录> --amend-presentation --ladder ProjectInputs/PresentationLadder/monopoly_demo_ladder.json` 追加呈现三批(C2 切批断言在此做)。
3. coding agent 经 fetch/submit 无人值守跑 presentation-1/2(C3);每 rung verified 后 runbook 调 `evidence_validator.freeze_layer` 冻结 `rung<N>-contract` / `rung<N>-impl` 层。
4. 窗口 1:msc 试玩 2D 版 → `demo_feedback_log` 登记 → `--amend-feedback` 切批 → 修复 → 复验(C4)。
5. presentation-3 无人值守(C5)→ 窗口 2 终裁(C6)。
6. document-release(task.md 换页 / contracts 登记 58 工具 49 schema / acceptance 附录 / CLAUDE.md 常用命令数字同步)→ finishing-a-development-branch(merge 方式 msc 定)。

## Self-Review 备注(plan 作者自查结论)

- **Spec 覆盖**:§4.1 阶梯(Task 2/11)/ §4.2 amend(Task 3/4/5)/ §4.3 行为校验+BL-01/04(Task 6/7/9)/ §4.4 反馈批(Task 4/5/8/10)/ §4.5 rung 交付物(Task 11 阶梯实例;实施在验收期)/ §4.6 冻结分层(Task 8)/ §4.7 施工规范(Task 11)/ §6 测试(各 Task + Task 12)/ §9 防固化(amend 零领域语义 + 阶梯实例承载语义)。spec §7 验收判据属验收期,见交接段。
- **占位扫描**:仅两处刻意留给实际环境的引用——Stage 15 打印尾段"照抄 run_stage_14 同位置"(其代码紧邻,逐行可对照)与 SystemTestCases.md 行格式"以实际文件为准"(CASE_ID_PATTERN 机器对账兜底);其余步骤均含完整代码/命令/预期输出。
- **类型一致性**:amend 的 paths 键(ladder_path/feedback_dir)与 CLI `_run_amend` 构造一致;validator 新签名 frozen_layers 与 compiler_tools 调用一致;runner 新函数名(build_parser/collect_regression_filters/aggregate_regression)与测试引用一致;TOOL_COUNT 58 在 phase14/phase15 两处测试一致。

