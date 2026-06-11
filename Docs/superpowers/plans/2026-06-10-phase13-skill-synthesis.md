# Phase 13 Skill 合成主链 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让超出模板库的 GDD 能编出完整真机单 demo——Stage 3 注册表数据化、capability gap 显式化、链内合成 stage(MCP 双端中立)、双 gate 信任链、GDD 覆盖矩阵。

**Architecture:** 把 `skill_graph_planning.py` 的两张硬编码注册表下沉为 manifest `capability_bindings` 自描述 + 占位数据文件,Stage 3 改为扫描建映射,查不到的能力显式记 gap;新增 `skill_synthesis` 模块经 MCP prepare/save 工具对驱动 agent 现场合成 6 文件包,机器校验 + 人审 `review_status` 双 gate 后重入 Stage 3;`gdd_coverage` 模块提供 Stage 1 anchor 留痕与反向覆盖审计。所有新模块设计为**无相对导入、依赖注入**(templates_root / registry 作参数),便于 importlib 独立加载测试。

**Tech Stack:** Python 3.x + pyyaml + jsonschema(Draft7Validator)+ pytest;MCP stdio server(`Plugins/AgentBridge/MCP/`);不动 C++/Bridge/Orchestrator 稳定核心。

**Spec:** `Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md`(已批准)

**关键事实(写代码前必读):**
- `GAMEPLAY_NODE_CONFIGS`(7 条)在 `Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py:30-101`,`BASELINE_NODE_CONFIGS`(9 条)在 `:103-194`,`EDGE_BLUEPRINTS` 在 `:196-443`(**边表本期不动**,留在代码,见 Task 4 说明)。
- baseline 模板目录只有 6 个(hud/main_menu/pause/results/settings/start_screen),但 BASELINE_NODE_CONFIGS 有 9 条——input/audio/platform foundation 三条是无模板占位(`template_source: future_baseline_template`),数据化时落入占位数据文件,否则等价回归必破。
- gameplay 存在**多 capability 共用一个模板**:turn-loop 与 dice 同指 `monopoly.turn_and_dice_flow.phase1`;player-management 与 jail 同指 `monopoly.jail_and_bankruptcy.phase1`。所以 manifest 的绑定字段必须是**列表** `capability_bindings`。
- `FRAGMENT_FAMILY_MAP`(16 条)在 `Compiler/stages/domain_skill_runtime.py:23-40`;模板加载 `_resolve_template_prompts` 在 `:267-302`(运行时 rglob 扫 manifest,Phase 13 不改它)。
- MCP 加新工具改三处:`MCP/tool_definitions.py`(COMPILER_FRONTEND_TOOLS 字典)、`MCP/compiler_tools.py`(handler)、`MCP/server.py` TOOL_DISPATCH(约 :789-821)。`TOOL_COUNT = len(ALL_TOOLS)` 自动更新。
- 系统测试登记:`Tests/run_system_tests.py` STAGES 字典(:95-197,现 12 个 stage),`TOTAL_CASES` 是 sum 自动算;测试脚本放 `Tests/scripts/test_*.py`,pytest 类 + 用例函数对应 case id。
- Schema example 登记:`Scripts/validation/validate_examples.py` 的 `EXAMPLE_TO_SCHEMA` 显式映射表(:57-123),**不是自动发现**。
- Stage 1 capability 结构见 `Compiler/stages/root_skill_contract.py:163-260`;capability dict 目前**没有** source anchor 字段。
- 仓库提交惯例:开发过程提交用 `[skip-doc]` 前缀过 document-release 门禁,阶段收尾跑正式 document-release。
- 测试导入约定:新模块不用相对导入,测试用 `importlib.util.spec_from_file_location` 独立加载;`skill_graph_planning.create_skill_graph` 改造后接受 `registry` 注入参数,测试不经包导入。

---

### Task 1: 改造前 Golden 快照(等价回归的对照组)

**必须在动任何 Stage 3 代码之前完成。**

**Files:**
- Create: `Plugins/AgentBridge/Tests/golden/skill_graph_baseline_golden.json`(生成物)
- Create: `Plugins/AgentBridge/Tests/scripts/test_phase13_registry_equivalence.py`
- Create: `Plugins/AgentBridge/Tests/golden/make_golden_skill_graph.py`(生成脚本,保留可重跑)

- [ ] **Step 1: 确认基线输入 example 文件存在**

Run: `ls Plugins/AgentBridge/Schemas/examples/ | grep -i -E "root_skill_contract|clarification"`
Expected: 列出 `phase11_root_skill_contract.example.json` 与 clarification gate 的 example(名字含 `clarification`)。把实际文件名记下来,后续脚本用实际名字。

- [ ] **Step 2: 写 golden 生成脚本**

`Plugins/AgentBridge/Tests/golden/make_golden_skill_graph.py`:

```python
# -*- coding: utf-8 -*-
"""生成 Stage 3 等价回归的 golden 快照。

用 Schemas/examples 的 Phase 11 contract + gate example 作确定性输入,
跑 create_skill_graph 并剥离易变字段后落盘。改造前跑一次生成对照组;
改造后测试断言输出不变。
"""
import importlib.util
import json
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]  # Plugins/AgentBridge
EXAMPLES = PLUGIN_ROOT / "Schemas" / "examples"
GOLDEN = Path(__file__).resolve().parent / "skill_graph_baseline_golden.json"

VOLATILE_METADATA_KEYS = {"generated_at", "source_run_id"}


def load_module(name: str, path: Path):
    """importlib 独立加载,绕开包相对导入。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalize(graph: dict) -> dict:
    """剥离易变字段(时间戳/run_id),其余全保留。"""
    out = json.loads(json.dumps(graph, ensure_ascii=False))
    for key in VOLATILE_METADATA_KEYS:
        out.get("metadata", {}).pop(key, None)
    return out


def main():
    planning = load_module(
        "skill_graph_planning",
        PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
    )
    contract = json.loads(
        (EXAMPLES / "phase11_root_skill_contract.example.json").read_text(encoding="utf-8")
    )
    # Step 1 确认的 clarification example 实际文件名,替换下行
    gate = json.loads(
        (EXAMPLES / "phase11_clarification_gate_report.example.json").read_text(encoding="utf-8")
    )
    graph = planning.create_skill_graph(contract, gate, run_id=None)
    GOLDEN.write_text(
        json.dumps(normalize(graph), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"golden written: {GOLDEN}")


if __name__ == "__main__":
    main()
```

注意:若 Step 1 查到的 clarification example 文件名不同,改脚本中文件名;若 example 的 capability 集合与 STAGES 期望不符导致节点为 0,改用 `ProjectState/runs/` 下最近一次成功 run 的 `root_skill_contract.json` + `clarification_gate_report.json` 作输入(同样是确定性快照),并在脚本注释里写明来源路径。

- [ ] **Step 3: 生成 golden 并人工抽查**

Run: `python Plugins/AgentBridge/Tests/golden/make_golden_skill_graph.py`
Expected: `golden written: ...`;打开 golden 文件确认 `nodes` 非空(应有 gameplay+baseline 共 ~16 节点)、`metadata` 无 `generated_at`。

- [ ] **Step 4: 写等价回归测试**

`Plugins/AgentBridge/Tests/scripts/test_phase13_registry_equivalence.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-01: Stage 3 注册表数据化前后,基线 skill_graph 等价。

对应 Phase 13 spec §3 第 5 条与验收判据 1。
"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = PLUGIN_ROOT / "Schemas" / "examples"
GOLDEN = PLUGIN_ROOT / "Tests" / "golden" / "skill_graph_baseline_golden.json"

VOLATILE_METADATA_KEYS = {"generated_at", "source_run_id"}


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _normalize(graph):
    out = json.loads(json.dumps(graph, ensure_ascii=False))
    for key in VOLATILE_METADATA_KEYS:
        out.get("metadata", {}).pop(key, None)
    # capability_gaps 是改造新增字段,基线输入下必须为空,比对前剥离
    assert out.get("metadata", {}).pop("capability_gaps", []) == []
    return out


class TestRegistryEquivalence:
    def test_sks01_baseline_skill_graph_unchanged(self):
        """SKS-01: 基线 Monopoly 输入产出与 golden 逐项一致。"""
        planning = _load_module(
            "skill_graph_planning",
            PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
        )
        contract = json.loads(
            (EXAMPLES / "phase11_root_skill_contract.example.json").read_text(encoding="utf-8")
        )
        gate = json.loads(
            (EXAMPLES / "phase11_clarification_gate_report.example.json").read_text(encoding="utf-8")
        )
        graph = planning.create_skill_graph(contract, gate, run_id=None)
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        assert _normalize(graph) == golden
```

(输入文件名与 make_golden 保持一致。)

- [ ] **Step 5: 跑测试确认改造前为绿**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_registry_equivalence.py -v`
Expected: PASS(改造前自然等价;注意 `_normalize` 里 capability_gaps 的 assert 此刻会因字段不存在 pop 出 `[]` 默认值而通过)。

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Tests/golden/ Plugins/AgentBridge/Tests/scripts/test_phase13_registry_equivalence.py
git commit -m "[skip-doc] test(phase13): Stage 3 等价回归 golden 快照与测试(改造前基线)"
```

---

### Task 2: 存量 manifest 补 capability_bindings + 占位数据文件

**Files:**
- Modify: `Plugins/AgentBridge/SkillTemplates/baseline/{hud,main_menu,pause,results,settings,start_screen}/manifest.yaml`(6 个)
- Modify: `Plugins/AgentBridge/SkillTemplates/genre_packs/boardgame/monopoly_like/{monopoly_board_topology,monopoly_tile_event_dispatch,monopoly_turn_and_dice_flow,monopoly_property_economy,monopoly_jail_and_bankruptcy,monopoly_phase1_ui_flow}/manifest.yaml`(6 个)
- Create: `Plugins/AgentBridge/SkillTemplates/registry_placeholders.yaml`

- [ ] **Step 1: 给 12 个 manifest 追加 capability_bindings 块**

数据**逐字段照抄** `skill_graph_planning.py:30-194` 两张表,只换载体不改内容。每个 manifest 文件末尾追加。对照表(capability_id → 宿主 manifest):

| capability_id | 宿主 manifest 目录 | instance_id | convergence_priority | fragment_family |
|---|---|---|---|---|
| gameplay-board-topology | monopoly_board_topology | skill-board-topology | 1 | board_topology_spec |
| gameplay-tile-system | monopoly_tile_event_dispatch | skill-tile-system | 2 | tile_system_spec |
| gameplay-turn-loop | monopoly_turn_and_dice_flow | skill-turn-loop | 3 | turn_flow_spec |
| gameplay-dice | monopoly_turn_and_dice_flow | skill-dice | 2 | dice_rule_spec |
| gameplay-economy | monopoly_property_economy | skill-economy | 4 | property_economy_spec |
| gameplay-player-management | monopoly_jail_and_bankruptcy | skill-player-management | 5 | player_management_spec |
| gameplay-jail | monopoly_jail_and_bankruptcy | skill-jail | 5 | jail_rule_spec |
| baseline-start-screen | baseline/start_screen | skill-baseline-start-screen | 6 | start_screen_spec |
| baseline-main-menu | baseline/main_menu | skill-baseline-main-menu | 6 | main_menu_spec |
| baseline-settings | baseline/settings | skill-baseline-settings | 5 | settings_spec |
| baseline-pause | baseline/pause | skill-baseline-pause | 5 | pause_spec |
| baseline-results | baseline/results | skill-baseline-results | 6 | results_spec |
| baseline-hud | baseline/hud | skill-baseline-hud | 4 | hud_spec |

注意 monopoly_phase1_ui_flow 没有 capability 绑定(两张表中无人指向它)——它**不加** capability_bindings 块,扫描器对无绑定 manifest 静默跳过。

示例——`monopoly_turn_and_dice_flow/manifest.yaml` 末尾追加(双绑定,列表形态的存在理由):

```yaml
# Phase 13: 能力绑定(原 skill_graph_planning.GAMEPLAY_NODE_CONFIGS 数据下沉,逐字照抄)
capability_bindings:
  - capability_id: gameplay-turn-loop
    instance_id: skill-turn-loop
    convergence_priority: 3
    related_clarification_items:
      - cg-max-game-length
    planning_notes:
      - "Turn Loop 组织掷骰、移动、过起点奖励与回合切换，是 gameplay 主骨架。"
    fragment_family: turn_flow_spec
  - capability_id: gameplay-dice
    instance_id: skill-dice
    convergence_priority: 2
    related_clarification_items:
      - cg-dice-roll-feedback
    planning_notes:
      - "Dice 节点单独保留，方便后续把规则语义与表现反馈拆开处理。"
    fragment_family: dice_rule_spec
```

示例——`baseline/hud/manifest.yaml` 末尾追加(单绑定):

```yaml
# Phase 13: 能力绑定(原 skill_graph_planning.BASELINE_NODE_CONFIGS 数据下沉,逐字照抄)
capability_bindings:
  - capability_id: baseline-hud
    instance_id: skill-baseline-hud
    convergence_priority: 4
    related_clarification_items:
      - cg-hud-layout-style
      - cg-dice-roll-feedback
    planning_notes:
      - "HUD 是 realization_eligible baseline，允许进入后续 Design Space Discovery。"
    fragment_family: hud_spec
```

其余 10 个 manifest 同构:`planning_notes` / `related_clarification_items` 必须与 `skill_graph_planning.py` 对应条目逐字一致(中文标点也要一致),否则 Task 4 等价回归会红。

- [ ] **Step 2: 写占位数据文件(3 个无模板 baseline 节点)**

`Plugins/AgentBridge/SkillTemplates/registry_placeholders.yaml`:

```yaml
# Phase 13 注册占位数据文件
# 这 3 个 baseline 能力尚无落地模板目录(template_source 恒为 future_baseline_template),
# 注册信息无 manifest 可承载,暂存于此。对应模板落地后,应把条目迁入其 manifest 的
# capability_bindings 并从本文件删除。本文件是数据不是代码,内容逐字照抄原
# skill_graph_planning.BASELINE_NODE_CONFIGS 对应条目。
placeholders:
  - capability_id: baseline-input-foundation
    instance_id: skill-baseline-input-foundation
    template_id: baseline.input_foundation.presence_only
    convergence_priority: 5
    related_clarification_items: []
    planning_notes:
      - "Input Foundation 只提供通用输入底座，不提前决定具体交互映射细节。"
    fragment_family: input_foundation_spec
  - capability_id: baseline-audio-foundation
    instance_id: skill-baseline-audio-foundation
    template_id: baseline.audio_foundation.presence_only
    convergence_priority: 5
    related_clarification_items: []
    planning_notes:
      - "Audio Foundation 先保证音量控制与基础 SFX/BGM 能力存在。"
    fragment_family: audio_foundation_spec
  - capability_id: baseline-platform-foundation
    instance_id: skill-baseline-platform-foundation
    template_id: baseline.platform_foundation.clarification_gated
    convergence_priority: 6
    related_clarification_items:
      - cg-platform-foundation-boundary
      - cg-platform-persistence
    planning_notes:
      - "Platform Foundation 当前受 Clarification Gate 约束，只保留节点与边界，不发散实现。"
    fragment_family: platform_foundation_spec
```

- [ ] **Step 3: YAML 语法自检**

Run: `python -c "import yaml,glob; [yaml.safe_load(open(p,encoding='utf-8')) for p in glob.glob('Plugins/AgentBridge/SkillTemplates/**/manifest.yaml',recursive=True)+['Plugins/AgentBridge/SkillTemplates/registry_placeholders.yaml']]; print('yaml ok')"`
Expected: `yaml ok`

- [ ] **Step 4: Commit**

```bash
git add Plugins/AgentBridge/SkillTemplates/
git commit -m "[skip-doc] feat(phase13): 12 manifest 补 capability_bindings + 3 占位节点数据文件(注册表数据下沉,内容逐字照抄)"
```

---

### Task 3: registry_scan 模块(扫描建映射,TDD)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/stages/registry_scan.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_registry_scan.py`

设计约束:**无相对导入**(只用 stdlib + yaml),`templates_root` 作参数注入,便于测试用临时目录。

- [ ] **Step 1: 写失败测试**

`Plugins/AgentBridge/Tests/scripts/test_phase13_registry_scan.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-02/SKS-08: 注册表扫描与 synthesized 审批过滤。"""
import importlib.util
from pathlib import Path

import pytest
import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REAL_TEMPLATES_ROOT = PLUGIN_ROOT / "SkillTemplates"


def _load():
    spec = importlib.util.spec_from_file_location(
        "registry_scan", PLUGIN_ROOT / "Compiler" / "stages" / "registry_scan.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestRegistryScan:
    def test_sks02_real_templates_cover_all_16_capabilities(self):
        """SKS-02: 真实模板树扫描出与原硬编码表相同的 16 个 capability。"""
        rs = _load()
        registry = rs.scan_capability_registry(REAL_TEMPLATES_ROOT)
        expected = {
            "gameplay-board-topology", "gameplay-tile-system", "gameplay-turn-loop",
            "gameplay-dice", "gameplay-economy", "gameplay-player-management",
            "gameplay-jail", "baseline-start-screen", "baseline-main-menu",
            "baseline-settings", "baseline-pause", "baseline-results", "baseline-hud",
            "baseline-input-foundation", "baseline-audio-foundation",
            "baseline-platform-foundation",
        }
        assert set(registry.keys()) == expected
        # 抽查双绑定模板:turn-loop 与 dice 同指一个 template_id
        assert registry["gameplay-turn-loop"]["template_id"] == "monopoly.turn_and_dice_flow.phase1"
        assert registry["gameplay-dice"]["template_id"] == "monopoly.turn_and_dice_flow.phase1"
        # 占位节点来自 registry_placeholders.yaml
        assert registry["baseline-input-foundation"]["template_id"] == "baseline.input_foundation.presence_only"

    def test_sks08_synthesized_requires_approved(self, tmp_path):
        """SKS-08: synthesized 区模板仅 review_status=approved 才入映射。"""
        rs = _load()
        syn = tmp_path / "synthesized" / "gameplay-auction"
        syn.mkdir(parents=True)
        manifest = {
            "template_id": "synthesized.gameplay-auction.v1",
            "review_status": "pending_review",
            "capability_bindings": [{
                "capability_id": "gameplay-auction",
                "instance_id": "skill-auction",
                "convergence_priority": 9,
                "related_clarification_items": [],
                "planning_notes": ["合成测试节点"],
                "fragment_family": "property_economy_spec",
            }],
        }
        (syn / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        registry = rs.scan_capability_registry(tmp_path)
        assert "gameplay-auction" not in registry  # 未审批,不可见

        manifest["review_status"] = "approved"
        (syn / "manifest.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True), encoding="utf-8"
        )
        registry = rs.scan_capability_registry(tmp_path)
        assert registry["gameplay-auction"]["template_source"] == "synthesized"
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_registry_scan.py -v`
Expected: FAIL(`registry_scan.py` 不存在)

- [ ] **Step 3: 实现 registry_scan.py**

`Plugins/AgentBridge/Compiler/stages/registry_scan.py`:

```python
# -*- coding: utf-8 -*-
"""Phase 13 能力注册表扫描。

把原 skill_graph_planning 两张硬编码表替换为数据扫描:
  - 各 SkillTemplate manifest.yaml 的 capability_bindings(自描述)
  - SkillTemplates/registry_placeholders.yaml(无模板占位节点)
  - SkillTemplates/synthesized/ 隔离区(仅 review_status=approved 纳入)

防固化守则:本模块只做结构扫描,不携带任何游戏领域语义。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

DEFAULT_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "SkillTemplates"
PLACEHOLDERS_FILE = "registry_placeholders.yaml"
SYNTHESIZED_DIR = "synthesized"
APPROVED = "approved"


def _binding_to_config(binding: Dict[str, Any], template_id: str, template_source: str) -> Dict[str, Any]:
    """把一条 capability_binding 转成与原硬编码表同构的节点配置。"""
    return {
        "instance_id": binding["instance_id"],
        "template_id": template_id,
        "convergence_priority": binding["convergence_priority"],
        "related_clarification_items": list(binding.get("related_clarification_items", [])),
        "planning_notes": list(binding.get("planning_notes", [])),
        "template_source": template_source,
        "fragment_family": binding.get("fragment_family", ""),
        "depends_on_capabilities": list(binding.get("depends_on_capabilities", [])),
    }


def scan_capability_registry(templates_root: str | Path | None = None) -> Dict[str, Dict[str, Any]]:
    """扫描模板树,构建 capability_id → 节点配置映射。

    优先级:正式库 manifest > 占位文件;synthesized 区只纳入 approved,
    且不覆盖正式库同名 capability(正式库优先)。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    registry: Dict[str, Dict[str, Any]] = {}

    # 1) 正式库 + synthesized 区的 manifest 扫描
    synthesized_root = root / SYNTHESIZED_DIR
    for manifest_path in sorted(root.rglob("manifest.yaml")):
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        bindings = manifest.get("capability_bindings") or []
        if not bindings:
            continue
        is_synthesized = synthesized_root in manifest_path.parents
        if is_synthesized and manifest.get("review_status") != APPROVED:
            continue  # 人没点头的,装作看不见
        template_id = manifest.get("template_id", "")
        # 正式库人写模板无 review_status 字段,默认信任(spec §3 第 2 条)
        template_source = "synthesized" if is_synthesized else "plugin_skill_template"
        for binding in bindings:
            capability_id = binding.get("capability_id", "")
            if not capability_id or not binding.get("instance_id"):
                continue
            if capability_id in registry and not is_synthesized:
                # 正式库重复绑定:保留先扫到的,后续 Stage 3 仍可经 metadata 警告
                continue
            if capability_id in registry and is_synthesized:
                continue  # 正式库优先,synthesized 不覆盖
            registry[capability_id] = _binding_to_config(binding, template_id, template_source)

    # 2) 占位数据文件(仅在 manifest 未提供同名 capability 时生效)
    placeholders_path = root / PLACEHOLDERS_FILE
    if placeholders_path.is_file():
        data = yaml.safe_load(placeholders_path.read_text(encoding="utf-8")) or {}
        for entry in data.get("placeholders", []):
            capability_id = entry.get("capability_id", "")
            if not capability_id or capability_id in registry:
                continue
            registry[capability_id] = _binding_to_config(
                entry, entry.get("template_id", ""), "future_baseline_template"
            )

    return registry


def execution_family_whitelist(templates_root: str | Path | None = None) -> set[str]:
    """执行层 family 白名单 = 正式库(非 synthesized)manifest can_emit_families 的并集。

    数据驱动,不维护硬编码清单(防固化守则)。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    synthesized_root = root / SYNTHESIZED_DIR
    families: set[str] = set()
    for manifest_path in root.rglob("manifest.yaml"):
        if synthesized_root in manifest_path.parents:
            continue
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        families.update(manifest.get("can_emit_families") or [])
        # capability_bindings 里的 fragment_family 也是执行层既有词表
        # (如 dice_rule_spec 可能只出现在 binding,不在宿主模板 can_emit_families)
        for binding in manifest.get("capability_bindings") or []:
            if binding.get("fragment_family"):
                families.add(binding["fragment_family"])
    # 占位节点的 fragment_family 也属于执行层既有词表
    placeholders_path = root / PLACEHOLDERS_FILE
    if placeholders_path.is_file():
        data = yaml.safe_load(placeholders_path.read_text(encoding="utf-8")) or {}
        for entry in data.get("placeholders", []):
            if entry.get("fragment_family"):
                families.add(entry["fragment_family"])
    return families
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_registry_scan.py -v`
Expected: 2 PASS。若 SKS-02 缺 capability,核对 Task 2 哪个 manifest 漏加/字段拼错。

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/stages/registry_scan.py Plugins/AgentBridge/Tests/scripts/test_phase13_registry_scan.py
git commit -m "[skip-doc] feat(phase13): registry_scan 扫描建映射 + 审批过滤 + family 白名单(数据驱动)"
```

---

### Task 4: skill_graph_planning 切换扫描 + gap 显式化 + 等价回归

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py`(删 :30-194 两张表,改 :540-696)
- Modify: `Plugins/AgentBridge/Schemas/skill_graph.schema.json`(metadata 加 capability_gaps)
- Modify: `Plugins/AgentBridge/Schemas/examples/phase11_skill_graph.example.json`(metadata 加 `"capability_gaps": []`)
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_gap_recording.py`

说明:`EDGE_BLUEPRINTS`(:196-443)**本期保留在代码**——它是跨 skill 的图级关系,manifest 单点自描述承载不了;已知局限记入收尾文档。synthesized 节点的依赖边经 manifest `depends_on_capabilities` 声明、由本模块换算。

- [ ] **Step 1: 写失败测试(gap 显式化 + synthesized 节点入图)**

`Plugins/AgentBridge/Tests/scripts/test_phase13_gap_recording.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-03: capability gap 显式记录,不再静默丢弃;synthesized 节点带依赖边入图。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = PLUGIN_ROOT / "Schemas" / "examples"


def _load_planning():
    spec = importlib.util.spec_from_file_location(
        "skill_graph_planning",
        PLUGIN_ROOT / "Compiler" / "stages" / "skill_graph_planning.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _inputs():
    contract = json.loads(
        (EXAMPLES / "phase11_root_skill_contract.example.json").read_text(encoding="utf-8")
    )
    gate = json.loads(
        (EXAMPLES / "phase11_clarification_gate_report.example.json").read_text(encoding="utf-8")
    )
    return contract, gate


# 测试注入用注册表:只有一个真实条目,迫使其余 capability 全部成 gap
MINI_REGISTRY = {
    "gameplay-board-topology": {
        "instance_id": "skill-board-topology",
        "template_id": "monopoly.board_topology.phase1",
        "convergence_priority": 1,
        "related_clarification_items": [],
        "planning_notes": ["棋盘拓扑是 Monopoly 主链的起点，先锁定 28 格、角格索引与移动方向。"],
        "template_source": "plugin_skill_template",
        "fragment_family": "board_topology_spec",
        "depends_on_capabilities": [],
    },
    "gameplay-auction": {
        "instance_id": "skill-auction",
        "template_id": "synthesized.gameplay-auction.v1",
        "convergence_priority": 9,
        "related_clarification_items": [],
        "planning_notes": ["合成节点"],
        "template_source": "synthesized",
        "fragment_family": "property_economy_spec",
        "depends_on_capabilities": ["gameplay-board-topology"],
    },
}


class TestGapRecording:
    def test_sks03_unmapped_capability_recorded_not_dropped(self):
        """SKS-03: 注册表查不到的 required capability 进 metadata.capability_gaps。"""
        planning = _load_planning()
        contract, gate = _inputs()
        contract.setdefault("gameplay_capabilities", []).append(
            {"capability_id": "gameplay-stock-market", "activation": "required",
             "allows_design_space_discovery": True}
        )
        graph = planning.create_skill_graph(contract, gate, run_id=None, registry=MINI_REGISTRY)
        gaps = graph["metadata"]["capability_gaps"]
        gap_ids = {g["capability_id"] for g in gaps}
        assert "gameplay-stock-market" in gap_ids
        for gap in gaps:
            assert gap["reason"] == "no_template"
            assert gap["domain_type"] in ("gameplay", "baseline")

    def test_sks03b_synthesized_node_enters_graph_with_declared_edge(self):
        """SKS-03b: 注册表含 synthesized 条目时,节点入图且依赖边被换算。"""
        planning = _load_planning()
        contract, gate = _inputs()
        contract.setdefault("gameplay_capabilities", []).append(
            {"capability_id": "gameplay-auction", "activation": "required",
             "allows_design_space_discovery": True}
        )
        graph = planning.create_skill_graph(contract, gate, run_id=None, registry=MINI_REGISTRY)
        nodes = {n["instance_id"]: n for n in graph["nodes"]}
        assert "skill-auction" in nodes
        assert nodes["skill-auction"]["template_source"] == "synthesized"
        assert any(
            e["from"] == "skill-board-topology" and e["to"] == "skill-auction"
            and e["type"] == "dependency"
            for e in graph["edges"]
        )
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_gap_recording.py -v`
Expected: FAIL(`create_skill_graph` 无 registry 参数 / 无 capability_gaps)

- [ ] **Step 3: 改造 skill_graph_planning.py**

3a. 删除 :30-101 `GAMEPLAY_NODE_CONFIGS` 与 :103-194 `BASELINE_NODE_CONFIGS` 两张表(EDGE_BLUEPRINTS 保留)。

3b. `_build_gameplay_nodes` 改造(`_build_baseline_nodes` 同构,差异照旧保留 realization_class/template_source 逻辑):

```python
def _build_gameplay_nodes(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    registry: Dict[str, Dict[str, Any]],
    gaps: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """从 Root Skill Contract 派生 Gameplay 节点;查不到注册的能力显式记 gap。"""
    gate_item_map = _index_gate_items(clarification_gate_report)
    retained_clarifications = set(clarification_gate_report.get("retained_clarifications", []))
    nodes: List[Dict[str, Any]] = []

    for capability in root_skill_contract.get("gameplay_capabilities", []):
        if capability.get("activation") != "required":
            continue

        capability_id = capability.get("capability_id", "")
        config = registry.get(capability_id)
        if not config:
            # Phase 13: 不再静默丢弃,显式记录 capability gap
            gaps.append({
                "capability_id": capability_id,
                "domain_type": "gameplay",
                "reason": "no_template",
                "source_anchor": capability.get("source_anchor", ""),
            })
            continue
        # ……(以下与原实现一致:related_item_ids / gated_item_ids / planning_notes 组装)
```

节点 dict 组装与原实现逐字段一致(instance_id/capability_id/template_id/domain_type/status/allows_design_space_discovery/convergence_priority/template_source/planning_notes/related_clarification_items/gated_by_clarification_items)。baseline 侧的 `_resolve_baseline_template_source` 调用保留(template_source 仍按 6 文件齐全性实测,占位条目自然得 future_baseline_template)。

3c. `create_skill_graph` 签名与 gap/边换算:

```python
def create_skill_graph(
    root_skill_contract: Dict[str, Any],
    clarification_gate_report: Dict[str, Any],
    run_id: str | None = None,
    registry: Dict[str, Dict[str, Any]] | None = None,
) -> Dict[str, Any]:
    """生成 Skill Graph。registry 可注入(测试);缺省时扫描模板树。"""
    if registry is None:
        from . import registry_scan
        registry = registry_scan.scan_capability_registry()
    capability_gaps: List[Dict[str, Any]] = []
    generated_at = datetime.now(timezone.utc).isoformat()
    gameplay_nodes = _build_gameplay_nodes(root_skill_contract, clarification_gate_report, registry, capability_gaps)
    baseline_nodes = _build_baseline_nodes(root_skill_contract, clarification_gate_report, registry, capability_gaps)
    ...
    # 边:静态蓝图过滤 + synthesized 节点 manifest 声明依赖换算
    edges = _filter_edges(node_ids)
    capability_to_instance = {cid: cfg["instance_id"] for cid, cfg in registry.items()}
    for node in nodes:
        declared = registry.get(node["capability_id"], {}).get("depends_on_capabilities", [])
        for dep_capability in declared:
            dep_instance = capability_to_instance.get(dep_capability)
            if dep_instance and dep_instance in node_ids:
                edges.append({
                    "from": dep_instance,
                    "to": node["instance_id"],
                    "type": "dependency",
                    "reason": f"manifest capability_binding 声明依赖 {dep_capability}。",
                })
    ...
    # metadata 增加:
            "capability_gaps": capability_gaps,
```

注意:基线 Monopoly 输入下所有正式库条目 `depends_on_capabilities` 为空,新换算逻辑不产生新边——等价回归保持绿。

3d. `Plugins/AgentBridge/Schemas/skill_graph.schema.json`:打开文件找到 `metadata` 的 `properties`,追加(若 metadata 有 `required` 列表,**不要**把 capability_gaps 加进 required,保持向后兼容;若 `additionalProperties: false` 则本步必须加,否则校验会拒绝新字段):

```json
"capability_gaps": {
  "type": "array",
  "description": "注册表查不到模板的 required capability 显式记录(Phase 13,替代静默丢弃)",
  "items": {
    "type": "object",
    "properties": {
      "capability_id": {"type": "string", "description": "缺口能力 ID"},
      "domain_type": {"type": "string", "enum": ["gameplay", "baseline"], "description": "能力域"},
      "reason": {"type": "string", "description": "缺口原因,当前固定 no_template"},
      "source_anchor": {"type": "string", "description": "该能力在 GDD 中的出处锚点(可为空)"}
    },
    "required": ["capability_id", "domain_type", "reason"],
    "additionalProperties": false
  }
}
```

3e. `phase11_skill_graph.example.json` 的 metadata 里加 `"capability_gaps": []`。

- [ ] **Step 4: 全部 Phase 13 测试 + 等价回归 + schema strict**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_registry_equivalence.py Plugins/AgentBridge/Tests/scripts/test_phase13_registry_scan.py Plugins/AgentBridge/Tests/scripts/test_phase13_gap_recording.py -v`
Expected: 全 PASS(等价回归是关键门:红了先修等价,再做后面任务)
Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: 全 passed

- [ ] **Step 5: 全量系统测试回归(无编辑器路径)**

Run: `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`
Expected: 全 PASS。任何红用例先修再前进。

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Compiler/stages/skill_graph_planning.py Plugins/AgentBridge/Schemas/ Plugins/AgentBridge/Tests/scripts/test_phase13_gap_recording.py
git commit -m "[skip-doc] feat(phase13): Stage 3 注册表数据化 + capability gap 显式化(等价回归绿)"
```

---

### Task 5: FRAGMENT_FAMILY_MAP 数据化

**Files:**
- Modify: `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py:23-40`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_fragment_family.py`

- [ ] **Step 1: 写失败测试**

`Plugins/AgentBridge/Tests/scripts/test_phase13_fragment_family.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-04: FRAGMENT_FAMILY_MAP 由注册表派生,与原 16 条硬编码一致。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_16 = {
    "skill-board-topology": "board_topology_spec",
    "skill-tile-system": "tile_system_spec",
    "skill-turn-loop": "turn_flow_spec",
    "skill-dice": "dice_rule_spec",
    "skill-economy": "property_economy_spec",
    "skill-player-management": "player_management_spec",
    "skill-jail": "jail_rule_spec",
    "skill-baseline-start-screen": "start_screen_spec",
    "skill-baseline-main-menu": "main_menu_spec",
    "skill-baseline-settings": "settings_spec",
    "skill-baseline-pause": "pause_spec",
    "skill-baseline-results": "results_spec",
    "skill-baseline-hud": "hud_spec",
    "skill-baseline-input-foundation": "input_foundation_spec",
    "skill-baseline-audio-foundation": "audio_foundation_spec",
    "skill-baseline-platform-foundation": "platform_foundation_spec",
}


def test_sks04_family_map_derived_equals_legacy():
    spec = importlib.util.spec_from_file_location(
        "registry_scan", PLUGIN_ROOT / "Compiler" / "stages" / "registry_scan.py"
    )
    rs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rs)
    registry = rs.scan_capability_registry(PLUGIN_ROOT / "SkillTemplates")
    derived = {
        cfg["instance_id"]: cfg["fragment_family"]
        for cfg in registry.values() if cfg.get("fragment_family")
    }
    assert derived == EXPECTED_16
```

- [ ] **Step 2: 跑测试**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_fragment_family.py -v`
Expected: PASS(Task 2/3 已让数据齐备;此测试先锁住派生正确性)

- [ ] **Step 3: 替换 domain_skill_runtime 的硬编码表**

把 `domain_skill_runtime.py:23-40` 的字面量字典替换为:

```python
from . import registry_scan


def _build_fragment_family_map() -> Dict[str, str]:
    """Phase 13: fragment family 由注册表派生,替代硬编码(数据见各 manifest capability_bindings)。"""
    registry = registry_scan.scan_capability_registry()
    return {
        cfg["instance_id"]: cfg["fragment_family"]
        for cfg in registry.values()
        if cfg.get("fragment_family")
    }


FRAGMENT_FAMILY_MAP = _build_fragment_family_map()
```

变量名与用法不变(模块内所有 `FRAGMENT_FAMILY_MAP[...]` / `.get(...)` 调用零改动)。先 `grep -n "FRAGMENT_FAMILY_MAP" Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py` 确认只有定义处需要改。

- [ ] **Step 4: 回归**

Run: `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`
Expected: 全 PASS(Stage 4 相关用例覆盖 family 消费路径)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py Plugins/AgentBridge/Tests/scripts/test_phase13_fragment_family.py
git commit -m "[skip-doc] feat(phase13): FRAGMENT_FAMILY_MAP 由注册表派生,删除第三张硬编码表"
```

---

### Task 6: 合成校验器(synthesis_validator,TDD)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/stages/synthesis_validator.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_synthesis_validator.py`

- [ ] **Step 1: 写失败测试(合法包/缺文件/schema 违规/白名单越界)**

`Plugins/AgentBridge/Tests/scripts/test_phase13_synthesis_validator.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-05/06/07: 合成包机器校验——合法通过、缺件拒绝、schema 违规拒绝、家族越界拒绝。"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "synthesis_validator",
        PLUGIN_ROOT / "Compiler" / "stages" / "synthesis_validator.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _legal_package():
    """构造最小合法 6 文件包(内容为内存 dict,key=文件名)。"""
    manifest = "\n".join([
        "template_id: synthesized.gameplay-auction.v1",
        "display_name: 拍卖机制(合成)",
        "template_kind: genre_skill",
        "genre: monopoly_like",
        "template_version: \"1.0.0\"",
        "template_source: synthesized",
        "review_status: pending_review",
        "realization_class: realization_eligible",
        "can_emit_families:",
        "  - property_economy_spec",
        "capability_bindings:",
        "  - capability_id: gameplay-auction",
        "    instance_id: skill-auction",
        "    convergence_priority: 9",
        "    related_clarification_items: []",
        "    planning_notes:",
        "      - \"拍卖机制由 agent 合成,Phase 13 试制。\"",
        "    fragment_family: property_economy_spec",
        "    depends_on_capabilities:",
        "      - gameplay-economy",
    ])
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "auction_type": {"type": "string"},
            "starting_bid_rule": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"basis": {"type": "string"}},
            },
        },
        "required": ["auction_type"],
    }
    return {
        "manifest.yaml": manifest,
        "system_prompt.md": "你是桌游经济系统设计专家。",
        "domain_prompt.md": "拍卖有英式/荷兰式/密封出价三类……",
        "evaluator_prompt.md": "检查流拍处理是否定义。",
        "input_selector.yaml": "include_sections:\n  - economy\n",
        "output_schema.json": json.dumps(output_schema, ensure_ascii=False),
    }


WHITELIST = {"property_economy_spec", "hud_spec"}


class TestSynthesisValidator:
    def test_sks05_legal_package_passes(self):
        sv = _load()
        errors = sv.validate_synthesized_package(
            "gameplay-auction", _legal_package(), WHITELIST
        )
        assert errors == []

    def test_sks05b_missing_file_rejected(self):
        sv = _load()
        package = _legal_package()
        del package["evaluator_prompt.md"]
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("evaluator_prompt.md" in e for e in errors)

    def test_sks06_schema_missing_additional_properties_rejected(self):
        sv = _load()
        package = _legal_package()
        bad = json.loads(package["output_schema.json"])
        del bad["properties"]["starting_bid_rule"]["additionalProperties"]
        package["output_schema.json"] = json.dumps(bad)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e for e in errors)

    def test_sks07_family_outside_whitelist_rejected(self):
        sv = _load()
        package = _legal_package()
        package["manifest.yaml"] = package["manifest.yaml"].replace(
            "property_economy_spec", "totally_new_family"
        )
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("totally_new_family" in e for e in errors)

    def test_sks07b_template_id_dir_mismatch_rejected(self):
        sv = _load()
        package = _legal_package()
        errors = sv.validate_synthesized_package("gameplay-stock", package, WHITELIST)
        assert any("template_id" in e for e in errors)
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_synthesis_validator.py -v`
Expected: FAIL(模块不存在)

- [ ] **Step 3: 实现 synthesis_validator.py**

`Plugins/AgentBridge/Compiler/stages/synthesis_validator.py`:

```python
# -*- coding: utf-8 -*-
"""Phase 13 合成包机器校验器(双 gate 的第一道)。

只做结构与契约校验,不做语义判断(语义质量归人审 gate)。
防固化守则:本模块不携带游戏领域语义;family 白名单由调用方传入(数据驱动)。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Set

import yaml

REQUIRED_FILES = {
    "manifest.yaml",
    "system_prompt.md",
    "domain_prompt.md",
    "evaluator_prompt.md",
    "input_selector.yaml",
    "output_schema.json",
}
REQUIRED_MANIFEST_FIELDS = {
    "template_id", "display_name", "template_kind", "template_version",
    "template_source", "review_status", "realization_class",
    "can_emit_families", "capability_bindings",
}
REQUIRED_BINDING_FIELDS = {
    "capability_id", "instance_id", "convergence_priority", "fragment_family",
}


def _check_additional_properties(node: Any, path: str, errors: List[str]) -> None:
    """递归检查每个 object 节点显式声明 additionalProperties: false。"""
    if not isinstance(node, dict):
        return
    if node.get("type") == "object":
        if node.get("additionalProperties") is not False:
            errors.append(f"output_schema {path}: object 节点缺 additionalProperties: false")
        for key, child in (node.get("properties") or {}).items():
            _check_additional_properties(child, f"{path}.{key}", errors)
    if "items" in node:
        _check_additional_properties(node["items"], f"{path}[]", errors)


def validate_synthesized_package(
    capability_id: str,
    package: Dict[str, str],
    family_whitelist: Set[str],
) -> List[str]:
    """校验合成包;返回错误列表,为空即通过(错误文案直接回给 agent 重试)。"""
    errors: List[str] = []

    # 1) 6 文件齐全且非空
    for name in sorted(REQUIRED_FILES):
        if not package.get(name, "").strip():
            errors.append(f"缺少或为空: {name}")
    if errors:
        return errors  # 文件都不齐,后续检查无意义

    # 2) manifest 解析与必填字段
    try:
        manifest = yaml.safe_load(package["manifest.yaml"]) or {}
    except Exception as exc:
        return [f"manifest.yaml 解析失败: {exc}"]
    for field in sorted(REQUIRED_MANIFEST_FIELDS):
        if field not in manifest:
            errors.append(f"manifest 缺必填字段: {field}")

    # 3) template_id 与落盘目录命名一致(目录名 = capability_id)
    expected_template_id = f"synthesized.{capability_id}.v1"
    if manifest.get("template_id") != expected_template_id:
        errors.append(
            f"template_id 必须为 {expected_template_id},实际 {manifest.get('template_id')!r}"
        )
    if manifest.get("template_source") != "synthesized":
        errors.append("manifest.template_source 必须为 synthesized")
    if manifest.get("review_status") != "pending_review":
        errors.append("合成落盘时 review_status 必须为 pending_review(审批是人的动作)")

    # 4) capability_bindings 完整性
    bindings = manifest.get("capability_bindings") or []
    if not bindings:
        errors.append("capability_bindings 不能为空")
    for index, binding in enumerate(bindings):
        for field in sorted(REQUIRED_BINDING_FIELDS):
            if field not in binding:
                errors.append(f"capability_bindings[{index}] 缺字段: {field}")
        if binding.get("capability_id") != capability_id:
            errors.append(
                f"capability_bindings[{index}].capability_id 必须为 {capability_id}"
            )

    # 5) family 白名单(执行词表硬边界)
    for family in manifest.get("can_emit_families") or []:
        if family not in family_whitelist:
            errors.append(f"can_emit_families 越界: {family} 不在执行层白名单内")
    for index, binding in enumerate(bindings):
        family = binding.get("fragment_family", "")
        if family and family not in family_whitelist:
            errors.append(f"capability_bindings[{index}].fragment_family 越界: {family}")

    # 6) output_schema 合法 + 递归 additionalProperties
    try:
        schema = json.loads(package["output_schema.json"])
    except Exception as exc:
        errors.append(f"output_schema.json 解析失败: {exc}")
        return errors
    from jsonschema import Draft7Validator
    try:
        Draft7Validator.check_schema(schema)
    except Exception as exc:
        errors.append(f"output_schema 不是合法 draft-07 schema: {exc}")
    _check_additional_properties(schema, "<root>", errors)

    return errors
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_synthesis_validator.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/stages/synthesis_validator.py Plugins/AgentBridge/Tests/scripts/test_phase13_synthesis_validator.py
git commit -m "[skip-doc] feat(phase13): 合成包机器校验器(6文件/manifest/白名单/递归additionalProperties)"
```

---

### Task 7: skill_synthesis 模块(prepare/save/审阅清单,TDD)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/stages/skill_synthesis.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_skill_synthesis.py`

- [ ] **Step 1: 写失败测试(save 落盘 + 重试闭环 + 审阅清单)**

`Plugins/AgentBridge/Tests/scripts/test_phase13_skill_synthesis.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-09/10: 合成 save 落盘与重试闭环;审阅清单生成。"""
import importlib.util
import json
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load(name):
    spec = importlib.util.spec_from_file_location(
        name, PLUGIN_ROOT / "Compiler" / "stages" / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _legal_package():
    validator_test = importlib.util.spec_from_file_location(
        "vt", Path(__file__).resolve().parent / "test_phase13_synthesis_validator.py"
    )
    module = importlib.util.module_from_spec(validator_test)
    validator_test.loader.exec_module(module)
    return module._legal_package()


class TestSkillSynthesis:
    def test_sks09_save_rejects_then_accepts(self, tmp_path):
        """SKS-09: 非法包返回错误不落盘;修正后通过并落盘 pending_review。"""
        ss = _load("skill_synthesis")
        bad = _legal_package()
        del bad["domain_prompt.md"]
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=bad,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "rejected"
        assert any("domain_prompt.md" in e for e in result["errors"])
        assert not (tmp_path / "synthesized" / "gameplay-auction").exists()

        good = _legal_package()
        result = ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=good,
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        assert result["status"] == "saved"
        package_dir = tmp_path / "synthesized" / "gameplay-auction"
        assert (package_dir / "manifest.yaml").is_file()
        manifest = yaml.safe_load((package_dir / "manifest.yaml").read_text(encoding="utf-8"))
        assert manifest["review_status"] == "pending_review"

    def test_sks09b_prepare_payload_contains_exemplars_and_whitelist(self, tmp_path):
        """SKS-09b: prepare 载荷含 gap 上下文、6 文件规范、范例模板、白名单。"""
        ss = _load("skill_synthesis")
        payload = ss.build_synthesis_prepare_payload(
            capability_id="gameplay-auction",
            gap={"capability_id": "gameplay-auction", "domain_type": "gameplay",
                 "reason": "no_template", "source_anchor": "§2.4 地产拍卖"},
            gdd_excerpt="## 2.4 地产拍卖\n玩家拒购时地产进入英式拍卖……",
            constraints={"max_players": 6},
            templates_root=PLUGIN_ROOT / "SkillTemplates",
        )
        assert payload["capability_id"] == "gameplay-auction"
        assert "manifest.yaml" in payload["file_spec"]
        assert len(payload["exemplars"]) >= 1
        assert "property_economy_spec" in payload["family_whitelist"]
        assert payload["gdd_excerpt"].startswith("## 2.4")

    def test_sks10_review_checklist_lists_packages(self, tmp_path):
        """SKS-10: 审阅清单列出全部待审包及重点文件。"""
        ss = _load("skill_synthesis")
        ss.save_synthesized_package(
            capability_id="gameplay-auction",
            six_files=_legal_package(),
            templates_root=tmp_path,
            family_whitelist={"property_economy_spec"},
        )
        run_dir = tmp_path / "run"
        path = ss.generate_synthesis_review(run_dir, templates_root=tmp_path)
        text = Path(path).read_text(encoding="utf-8")
        assert "gameplay-auction" in text
        assert "output_schema.json" in text
        assert "review_status" in text
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_skill_synthesis.py -v`
Expected: FAIL(模块不存在)

- [ ] **Step 3: 实现 skill_synthesis.py**

`Plugins/AgentBridge/Compiler/stages/skill_synthesis.py`:

```python
# -*- coding: utf-8 -*-
"""Phase 13 S3.5 Skill 合成环节。

职责:为 capability gap 准备合成载荷(prepare)、接收 agent 产物并校验落盘(save)、
生成人审清单。本模块无相对导入,经 importlib 加载兄弟模块,便于独立测试。

信任链:save 内强制机器校验(第一道 gate);落盘 review_status=pending_review,
人审改 approved 后才会被 registry_scan 纳入(第二道 gate)。
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List, Set

import yaml

_STAGES_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "SkillTemplates"

FILE_SPEC = {
    "manifest.yaml": "身份证:template_id=synthesized.<capability_id>.v1、template_source=synthesized、review_status=pending_review、can_emit_families(白名单内)、capability_bindings 列表(capability_id/instance_id/convergence_priority/fragment_family,必要时 depends_on_capabilities)",
    "system_prompt.md": "人设:本 skill 是哪类领域专家、必须遵守的硬规则",
    "domain_prompt.md": "领域知识:该玩法的设计空间、维度与取舍(必须与 GDD 描述一致)",
    "evaluator_prompt.md": "自检清单:生成结果按什么标准检查遗漏与冲突",
    "input_selector.yaml": "取料单:include_sections/exclude_sections,从上游产物选取输入字段",
    "output_schema.json": "出货合同:draft-07 JSON Schema,root 与所有嵌套 object 必须 additionalProperties:false",
}


def _load_sibling(name: str):
    spec = importlib.util.spec_from_file_location(name, _STAGES_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pick_exemplars(templates_root: Path, domain_type: str, limit: int = 2) -> List[Dict[str, str]]:
    """选取 few-shot 范例模板:gameplay 取 genre_packs 下、baseline 取 baseline 下,
    按目录名排序取前 limit 个(确定性选取,不做语义相似度——防固化守则)。"""
    base = templates_root / ("genre_packs" if domain_type == "gameplay" else "baseline")
    exemplars: List[Dict[str, str]] = []
    if not base.is_dir():
        return exemplars
    for manifest_path in sorted(base.rglob("manifest.yaml"))[:limit]:
        bundle: Dict[str, str] = {"_dir": str(manifest_path.parent)}
        for name in FILE_SPEC:
            file_path = manifest_path.parent / name
            bundle[name] = file_path.read_text(encoding="utf-8") if file_path.is_file() else ""
        exemplars.append(bundle)
    return exemplars


def build_synthesis_prepare_payload(
    capability_id: str,
    gap: Dict[str, Any],
    gdd_excerpt: str,
    constraints: Dict[str, Any],
    templates_root: str | Path | None = None,
) -> Dict[str, Any]:
    """组装合成 prepare 载荷(MCP 工具直接透传给 agent)。"""
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    registry_scan = _load_sibling("registry_scan")
    whitelist = sorted(registry_scan.execution_family_whitelist(root))
    return {
        "capability_id": capability_id,
        "gap": gap,
        "gdd_excerpt": gdd_excerpt,
        "constraints": constraints,
        "file_spec": FILE_SPEC,
        "family_whitelist": whitelist,
        "naming_rules": {
            "template_id": f"synthesized.{capability_id}.v1",
            "package_dir": f"SkillTemplates/synthesized/{capability_id}/",
            "instance_id_prefix": "skill-",
        },
        "instructions": (
            "你正在为缺失的能力现场合成一个 SkillTemplate(6 文件包)。"
            "domain_prompt 必须忠实于 gdd_excerpt 的玩法描述;"
            "output_schema 的字段要覆盖该玩法的关键设计点;"
            "can_emit_families 与 fragment_family 只能从 family_whitelist 中选;"
            "完成后调用 compiler_skill_synthesis_save 提交,校验失败会返回具体错误,修正后重提。"
        ),
    }


def save_synthesized_package(
    capability_id: str,
    six_files: Dict[str, str],
    templates_root: str | Path | None = None,
    family_whitelist: Set[str] | None = None,
) -> Dict[str, Any]:
    """机器校验后落盘合成包;失败返回错误列表且不落盘(agent 重试闭环)。"""
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    if family_whitelist is None:
        registry_scan = _load_sibling("registry_scan")
        family_whitelist = registry_scan.execution_family_whitelist(root)
    validator = _load_sibling("synthesis_validator")
    errors = validator.validate_synthesized_package(capability_id, six_files, set(family_whitelist))
    if errors:
        return {"status": "rejected", "errors": errors, "package_dir": ""}

    package_dir = root / "synthesized" / capability_id
    package_dir.mkdir(parents=True, exist_ok=True)
    for name, content in six_files.items():
        (package_dir / name).write_text(content, encoding="utf-8")
    return {"status": "saved", "errors": [], "package_dir": str(package_dir)}


def generate_synthesis_review(
    run_dir: str | Path,
    templates_root: str | Path | None = None,
) -> str:
    """生成人审清单 synthesis_review.md(双 gate 的第二道入口)。"""
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    synthesized_root = root / "synthesized"
    lines = [
        "# 合成 Skill 人审清单",
        "",
        "审核要点:1) domain_prompt 与 GDD 玩法描述一致;2) output_schema 覆盖关键设计点;",
        "3) evaluator_prompt 能查出遗漏;4) 与最相近人写模板的丰富度对照(软基准,不做硬指标)。",
        "",
        "通过方式:把对应包 manifest.yaml 的 `review_status: pending_review` 改为 `approved`,",
        "然后重跑 Stage 3。未改为 approved 的包,编译器不会消费。",
        "",
    ]
    if synthesized_root.is_dir():
        for manifest_path in sorted(synthesized_root.rglob("manifest.yaml")):
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
            package_dir = manifest_path.parent
            lines.append(f"## {package_dir.name}")
            lines.append(f"- 状态: `review_status: {manifest.get('review_status', '?')}`")
            lines.append(f"- 目录: `{package_dir}`")
            lines.append(f"- 重点文件: `{package_dir / 'output_schema.json'}` / `{package_dir / 'domain_prompt.md'}` / `{package_dir / 'evaluator_prompt.md'}`")
            lines.append("")
    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    target = run_path / "synthesis_review.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return str(target)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_skill_synthesis.py -v`
Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/stages/skill_synthesis.py Plugins/AgentBridge/Tests/scripts/test_phase13_skill_synthesis.py
git commit -m "[skip-doc] feat(phase13): skill_synthesis prepare/save/审阅清单(机器校验重试闭环)"
```

---

### Task 8: MCP 合成工具对注册(双端交互面)

**Files:**
- Modify: `Plugins/AgentBridge/MCP/tool_definitions.py`(COMPILER_FRONTEND_TOOLS 字典追加 2 条)
- Modify: `Plugins/AgentBridge/MCP/compiler_tools.py`(追加 2 个 handler)
- Modify: `Plugins/AgentBridge/MCP/server.py`(TOOL_DISPATCH 追加 2 条,约 :789-821)
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_mcp_synthesis_tools.py`

- [ ] **Step 1: 写失败测试**

`Plugins/AgentBridge/Tests/scripts/test_phase13_mcp_synthesis_tools.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-11: MCP 合成工具对注册完整(定义/分发/handler 三处)。"""
import importlib.util
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def test_sks11_tools_registered():
    sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
    try:
        import tool_definitions
        importlib.reload(tool_definitions)
        assert "compiler_skill_synthesis_prepare" in tool_definitions.ALL_TOOLS
        assert "compiler_skill_synthesis_save" in tool_definitions.ALL_TOOLS
        # TOOL_COUNT 自动等于 ALL_TOOLS 长度(无漏登记)
        assert tool_definitions.TOOL_COUNT == len(tool_definitions.ALL_TOOLS)
        import compiler_tools
        importlib.reload(compiler_tools)
        assert callable(compiler_tools.compiler_skill_synthesis_prepare)
        assert callable(compiler_tools.compiler_skill_synthesis_save)
    finally:
        sys.path.remove(str(PLUGIN_ROOT / "MCP"))
```

(server.py 的 TOOL_DISPATCH 在 import 时可能拉起重依赖,分发登记用 grep 步骤验证,见 Step 4。)

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_mcp_synthesis_tools.py -v`
Expected: FAIL

- [ ] **Step 3: 三处注册**

3a. `tool_definitions.py` COMPILER_FRONTEND_TOOLS 字典(与 `compiler_stage4_node_prepare` 条目相邻处)追加:

```python
"compiler_skill_synthesis_prepare": {
    "description": "S3.5 合成准备:为指定 capability gap 返回 GDD 上下文、6 文件规范、范例模板与执行 family 白名单,供 Agent 现场合成 SkillTemplate。",
    "params": {
        "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        "capability_id": {"type": "string", "required": True, "description": "skill_graph metadata.capability_gaps 中的能力 ID"},
    },
    "returns": "gap 上下文、file_spec、exemplars、family_whitelist、naming_rules、instructions",
},
"compiler_skill_synthesis_save": {
    "description": "S3.5 合成提交:接收 6 文件内容,机器校验(6文件/manifest/白名单/additionalProperties)失败返回具体错误供重试;通过则落盘 SkillTemplates/synthesized/<capability_id>/ 并标 review_status=pending_review。",
    "params": {
        "session_path": {"type": "string", "required": True, "description": "session.json 路径"},
        "capability_id": {"type": "string", "required": True, "description": "目标能力 ID"},
        "six_files": {"type": "object", "required": True, "description": "key=文件名(manifest.yaml 等 6 个),value=完整文件内容字符串"},
    },
    "returns": "status=saved/rejected、errors[]、package_dir、review 提示",
},
```

3b. `compiler_tools.py` 末尾追加 handler(返回结构对齐既有 compiler 工具的 `{status, summary, data, warnings, errors}`;session 加载方式照抄同文件 `compiler_stage4_node_prepare` 开头的 session 读取代码):

```python
def compiler_skill_synthesis_prepare(session_path: str, capability_id: str) -> dict:
    """S3.5 合成准备:从 run 产物组装 gap 上下文 + 合成载荷。"""
    import importlib.util as _ilu
    from pathlib import Path as _Path

    stages_dir = _Path(__file__).resolve().parents[1] / "Compiler" / "stages"

    def _load(name):
        spec = _ilu.spec_from_file_location(name, stages_dir / f"{name}.py")
        module = _ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    # session → run 目录(照抄本文件其他工具的 session 解析方式)
    session_dir = _Path(session_path).resolve().parent
    skill_graph_path = session_dir / "skill_graph.json"
    if not skill_graph_path.is_file():
        return {"status": "failed", "summary": "skill_graph.json 不存在,先完成 Stage 3",
                "data": {}, "warnings": [], "errors": ["missing skill_graph.json"]}
    import json as _json
    graph = _json.loads(skill_graph_path.read_text(encoding="utf-8"))
    gaps = {g["capability_id"]: g for g in graph.get("metadata", {}).get("capability_gaps", [])}
    gap = gaps.get(capability_id)
    if gap is None:
        return {"status": "failed", "summary": f"{capability_id} 不在 capability_gaps 中",
                "data": {"known_gaps": sorted(gaps)}, "warnings": [], "errors": ["unknown gap"]}

    contract_path = session_dir / "root_skill_contract.json"
    constraints = {}
    if contract_path.is_file():
        contract = _json.loads(contract_path.read_text(encoding="utf-8"))
        constraints = contract.get("constraint_fields", {})

    # GDD 摘录:用 gap.source_anchor 提取对应章节;无 anchor 时给全文路径提示
    gdd_excerpt = ""
    gdd_dir = _Path(__file__).resolve().parents[3] / "ProjectInputs" / "GDD"
    anchor = gap.get("source_anchor", "")
    if anchor:
        coverage = _load("gdd_coverage")
        for gdd_path in sorted(gdd_dir.glob("*.md")):
            sections = coverage.split_gdd_sections(gdd_path.read_text(encoding="utf-8"))
            for section in sections:
                if section["heading"] == anchor:
                    gdd_excerpt = section["text"]
                    break
            if gdd_excerpt:
                break

    synthesis = _load("skill_synthesis")
    payload = synthesis.build_synthesis_prepare_payload(
        capability_id=capability_id, gap=gap,
        gdd_excerpt=gdd_excerpt, constraints=constraints,
    )
    return {"status": "success",
            "summary": f"合成准备完成: {capability_id}(范例 {len(payload['exemplars'])} 个)",
            "data": payload, "warnings": [], "errors": []}


def compiler_skill_synthesis_save(session_path: str, capability_id: str, six_files: dict) -> dict:
    """S3.5 合成提交:机器校验 + 落盘 + 审阅清单刷新。"""
    import importlib.util as _ilu
    from pathlib import Path as _Path

    stages_dir = _Path(__file__).resolve().parents[1] / "Compiler" / "stages"
    spec = _ilu.spec_from_file_location("skill_synthesis", stages_dir / "skill_synthesis.py")
    synthesis = _ilu.module_from_spec(spec)
    spec.loader.exec_module(synthesis)

    result = synthesis.save_synthesized_package(capability_id=capability_id, six_files=six_files)
    if result["status"] == "rejected":
        return {"status": "failed",
                "summary": f"合成包未通过机器校验({len(result['errors'])} 项),请按 errors 修正后重提",
                "data": result, "warnings": [], "errors": result["errors"]}

    session_dir = _Path(session_path).resolve().parent
    review_path = synthesis.generate_synthesis_review(session_dir)
    return {"status": "success",
            "summary": f"合成包已落盘 {result['package_dir']}(pending_review);人审清单: {review_path}",
            "data": {**result, "review_path": review_path,
                     "next": "人审通过后把 manifest review_status 改为 approved 并重跑 Stage 3"},
            "warnings": ["该包未经人审,Stage 3 暂不可见"], "errors": []}
```

注意:`gdd_coverage` 模块 Task 9 才创建——本 handler 对 anchor 为空/模块缺失要兼容。实施顺序上若先做本 Task,把 GDD 摘录块整体包 `try/except Exception: gdd_excerpt = ""`(Task 9 落地后自然生效)。

3c. `server.py` TOOL_DISPATCH 的 compiler 段(`"compiler_stage4_node_save"` 行后)追加:

```python
"compiler_skill_synthesis_prepare": ("compiler", compiler_tools.compiler_skill_synthesis_prepare),
"compiler_skill_synthesis_save": ("compiler", compiler_tools.compiler_skill_synthesis_save),
```

- [ ] **Step 4: 验证三处登记**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_mcp_synthesis_tools.py -v`
Expected: PASS
Run: `grep -n "compiler_skill_synthesis" Plugins/AgentBridge/MCP/server.py`
Expected: TOOL_DISPATCH 中 2 行
Run: `python -c "import sys; sys.path.insert(0,'Plugins/AgentBridge/MCP'); from tool_definitions import TOOL_COUNT; print(TOOL_COUNT)"`
Expected: 比改前 +2(把实测数记下来,document-release 时同步 mcp_tools_catalog)

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/MCP/ Plugins/AgentBridge/Tests/scripts/test_phase13_mcp_synthesis_tools.py
git commit -m "[skip-doc] feat(phase13): MCP 合成工具对(prepare/save)三处注册,工具数 +2"
```

---

### Task 9: gdd_coverage 模块(切分/矩阵/渲染,TDD)

**Files:**
- Create: `Plugins/AgentBridge/Compiler/stages/gdd_coverage.py`
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_gdd_coverage.py`

防固化守则(spec §5.3)在此落地:切分只认 markdown 结构;认领只靠 anchor 字符串等值;无任何游戏词汇;无全局忽略配置。

- [ ] **Step 1: 写失败测试**

`Plugins/AgentBridge/Tests/scripts/test_phase13_gdd_coverage.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-12/13: GDD 结构切分与反向覆盖矩阵(无人认领可见)。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

GDD = """# 测试游戏 GDD

## 2.1 棋盘与地块
28 格环形棋盘。

## 2.4 地产拍卖
玩家拒购时进入英式拍卖。

## 3.2 背景音乐
氛围性描述,随回合切换。
"""


def _load():
    spec = importlib.util.spec_from_file_location(
        "gdd_coverage", PLUGIN_ROOT / "Compiler" / "stages" / "gdd_coverage.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestGddCoverage:
    def test_sks12_split_by_structure_only(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        headings = [s["heading"] for s in sections]
        assert "2.1 棋盘与地块" in headings
        assert "2.4 地产拍卖" in headings
        assert "3.2 背景音乐" in headings
        auction = next(s for s in sections if s["heading"] == "2.4 地产拍卖")
        assert "英式拍卖" in auction["text"]

    def test_sks13_matrix_exposes_unclaimed(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        capabilities = [
            {"capability_id": "gameplay-board-topology", "source_anchor": "2.1 棋盘与地块"},
            {"capability_id": "gameplay-auction", "source_anchor": "2.4 地产拍卖"},
        ]
        matrix = gc.build_coverage_matrix(sections, capabilities)
        unclaimed = [r for r in matrix["rows"] if r["status"] == "unclaimed"]
        assert [r["heading"] for r in unclaimed] == ["3.2 背景音乐"]
        claimed = {r["heading"]: r["claimed_by"] for r in matrix["rows"] if r["status"] == "claimed"}
        assert claimed["2.4 地产拍卖"] == ["gameplay-auction"]
        # 无出处的 capability 也要可见
        capabilities.append({"capability_id": "gameplay-ghost", "source_anchor": ""})
        matrix = gc.build_coverage_matrix(sections, capabilities)
        assert "gameplay-ghost" in matrix["capabilities_without_anchor"]

    def test_sks13b_non_markdown_degrades_visibly(self):
        """非 markdown(无标题)输入:整篇成一个无人认领大段,不假装工作。"""
        gc = _load()
        sections = gc.split_gdd_sections("纯文本无标题的设计描述……")
        assert len(sections) == 1
        matrix = gc.build_coverage_matrix(sections, [])
        assert matrix["rows"][0]["status"] == "unclaimed"

    def test_sks13c_render_markdown(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        matrix = gc.build_coverage_matrix(
            sections, [{"capability_id": "gameplay-board-topology", "source_anchor": "2.1 棋盘与地块"}]
        )
        text = gc.render_coverage_markdown(matrix)
        assert "无人认领" in text
        assert "2.4 地产拍卖" in text
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_gdd_coverage.py -v`
Expected: FAIL

- [ ] **Step 3: 实现 gdd_coverage.py**

`Plugins/AgentBridge/Compiler/stages/gdd_coverage.py`:

```python
# -*- coding: utf-8 -*-
"""Phase 13 GDD 覆盖矩阵(三层保证模型的第二层:反向覆盖审计)。

防固化守则(spec §5.3,评审时强制对照):
  1. 切分只认 markdown 结构(标题行),零语义判断——本文件出现任何游戏词汇即违规;
  2. 不读不写任何全局忽略配置,矩阵每次从零生成,人的裁决只留在 run 级产物;
  3. 认领判定只靠 source_anchor 与标题的字符串等值,不依赖分类词表;
  4. 非 markdown 输入优雅降级为单一无人认领大段(可见失效,不假装工作)。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def split_gdd_sections(gdd_text: str) -> List[Dict[str, Any]]:
    """按 markdown 标题切分;无任何标题时整篇为一段(优雅降级)。"""
    lines = gdd_text.splitlines()
    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    for line_number, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if match:
            if current is not None:
                sections.append(current)
            current = {
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "start_line": line_number,
                "text": line + "\n",
            }
        elif current is not None:
            current["text"] += line + "\n"
    if current is not None:
        sections.append(current)
    if not sections:
        return [{
            "heading": "<整篇文档(未检出 markdown 标题,矩阵降级)>",
            "level": 0, "start_line": 1, "text": gdd_text,
        }]
    return sections


def build_coverage_matrix(
    sections: List[Dict[str, Any]],
    capabilities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """逐段比对认领关系。认领 = capability.source_anchor 与段落标题字符串等值。"""
    claims: Dict[str, List[str]] = {}
    without_anchor: List[str] = []
    for capability in capabilities:
        anchor = (capability.get("source_anchor") or "").strip()
        capability_id = capability.get("capability_id", "")
        if not anchor:
            without_anchor.append(capability_id)
            continue
        claims.setdefault(anchor, []).append(capability_id)

    rows = []
    for section in sections:
        claimed_by = sorted(claims.get(section["heading"], []))
        rows.append({
            "heading": section["heading"],
            "start_line": section["start_line"],
            "status": "claimed" if claimed_by else "unclaimed",
            "claimed_by": claimed_by,
        })
    matched_anchors = {row["heading"] for row in rows if row["claimed_by"]}
    dangling = sorted(set(claims) - matched_anchors)  # anchor 指向不存在的段落
    return {
        "rows": rows,
        "capabilities_without_anchor": sorted(without_anchor),
        "dangling_anchors": dangling,
        "unclaimed_count": sum(1 for row in rows if row["status"] == "unclaimed"),
    }


def render_coverage_markdown(matrix: Dict[str, Any]) -> str:
    """人读版:无人认领段落置顶(人审只需要看这部分)。"""
    lines = ["# GDD 覆盖矩阵", ""]
    unclaimed = [row for row in matrix["rows"] if row["status"] == "unclaimed"]
    lines.append(f"## ⚠️ 无人认领段落({len(unclaimed)})——逐条裁决:非功能可忽略 / 功能遗漏须打回重抽")
    lines.append("")
    for row in unclaimed:
        lines.append(f"- L{row['start_line']} {row['heading']}")
    lines.append("")
    lines.append("## 已认领段落")
    lines.append("")
    lines.append("| GDD 段落 | 认领能力 |")
    lines.append("|---|---|")
    for row in matrix["rows"]:
        if row["status"] == "claimed":
            lines.append(f"| {row['heading']} | {', '.join(row['claimed_by'])} |")
    if matrix["capabilities_without_anchor"]:
        lines.append("")
        lines.append("## ⚠️ 无出处能力(source_anchor 为空)")
        for capability_id in matrix["capabilities_without_anchor"]:
            lines.append(f"- {capability_id}")
    if matrix["dangling_anchors"]:
        lines.append("")
        lines.append("## ⚠️ 悬空 anchor(指向不存在的段落)")
        for anchor in matrix["dangling_anchors"]:
            lines.append(f"- {anchor}")
    return "\n".join(lines)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_gdd_coverage.py -v`
Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Compiler/stages/gdd_coverage.py Plugins/AgentBridge/Tests/scripts/test_phase13_gdd_coverage.py
git commit -m "[skip-doc] feat(phase13): GDD 覆盖矩阵(结构切分+anchor认领+无人认领可见,防固化守则落地)"
```

---

### Task 10: anchor 留痕接入 Stage 1 MCP save + 矩阵落盘 + promote 拦截

**Files:**
- Modify: `Plugins/AgentBridge/MCP/compiler_tools.py`(`compiler_root_skill_save` handler)
- Modify: `Plugins/AgentBridge/MCP/evidence_tools.py`(`evidence_promote_run` handler)
- Modify: `Plugins/AgentBridge/Schemas/root_skill_contract.schema.json`(capability 加可选 source_anchor)
- Test: `Plugins/AgentBridge/Tests/scripts/test_phase13_anchor_and_promote.py`

设计决策(spec §5.2 的兼容化落地):schema 中 `source_anchor` 为**可选**字段(老 example 不破);MCP `compiler_root_skill_save` 在 session 启用合成(`allow_skill_synthesis=true`)时**强制**所有 required capability 携带非空 source_anchor,未启用时降级为 warning。等价回归与既有系统测试不受影响。

- [ ] **Step 1: 写失败测试**

`Plugins/AgentBridge/Tests/scripts/test_phase13_anchor_and_promote.py`:

```python
# -*- coding: utf-8 -*-
"""SKS-14/15: anchor 强制留痕(合成开启时)与 synthesized run promote 拦截。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load_helper(module_name, file_name):
    spec = importlib.util.spec_from_file_location(
        module_name, PLUGIN_ROOT / "MCP" / file_name
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestAnchorEnforcement:
    def test_sks14_missing_anchor_listed(self):
        """SKS-14: 纯函数 _capabilities_missing_anchor 列出无出处能力。"""
        import sys
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import compiler_tools
            importlib.reload(compiler_tools)
            contract = {
                "gameplay_capabilities": [
                    {"capability_id": "gameplay-a", "activation": "required",
                     "source_anchor": "2.1 棋盘"},
                    {"capability_id": "gameplay-b", "activation": "required"},
                    {"capability_id": "gameplay-c", "activation": "optional"},
                ],
                "baseline_capabilities": [
                    {"capability_id": "baseline-x", "activation": "required",
                     "source_anchor": ""},
                ],
            }
            missing = compiler_tools._capabilities_missing_anchor(contract)
            assert missing == ["baseline-x", "gameplay-b"]
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))


class TestPromoteGuard:
    def test_sks15_synthesized_graph_refused(self, tmp_path):
        """SKS-15: skill_graph 含 synthesized 节点时 promote 守卫拒绝。"""
        import sys, json
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            run_dir = tmp_path / "run-x"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text(json.dumps({
                "nodes": [{"instance_id": "skill-auction", "template_source": "synthesized"}],
                "metadata": {},
            }), encoding="utf-8")
            reasons = evidence_tools._synthesized_promote_blockers(run_dir)
            assert reasons and "synthesized" in reasons[0]
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))

    def test_sks15b_unresolved_gaps_refused(self, tmp_path):
        """SKS-15b: 合成关闭/未完成时 gap 保留的 run 同样被 promote 守卫拒绝。"""
        import sys, json
        sys.path.insert(0, str(PLUGIN_ROOT / "MCP"))
        try:
            import evidence_tools
            importlib.reload(evidence_tools)
            run_dir = tmp_path / "run-y"
            run_dir.mkdir()
            (run_dir / "skill_graph.json").write_text(json.dumps({
                "nodes": [],
                "metadata": {"capability_gaps": [
                    {"capability_id": "gameplay-auction", "domain_type": "gameplay",
                     "reason": "no_template"}
                ]},
            }), encoding="utf-8")
            reasons = evidence_tools._synthesized_promote_blockers(run_dir)
            assert reasons and "capability_gaps" in reasons[0]
        finally:
            sys.path.remove(str(PLUGIN_ROOT / "MCP"))
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_anchor_and_promote.py -v`
Expected: FAIL(两个 helper 不存在)

- [ ] **Step 3: 实现两个纯函数 helper 并接线**

3a. `compiler_tools.py` 追加纯函数 + 在 `compiler_root_skill_save` handler 的 schema 校验之后、落盘之前接线:

```python
def _capabilities_missing_anchor(contract: dict) -> list:
    """列出 activation=required 但 source_anchor 缺失/为空的 capability_id(排序稳定)。"""
    missing = []
    for key in ("gameplay_capabilities", "baseline_capabilities"):
        for capability in contract.get(key, []):
            if capability.get("activation") != "required":
                continue
            if not (capability.get("source_anchor") or "").strip():
                missing.append(capability.get("capability_id", "<unknown>"))
    return sorted(missing)
```

在 `compiler_root_skill_save` 内接线(读 session 的合成开关;session 元数据读取方式照抄同文件既有 session 处理;若 session 无该字段默认 False):

```python
    missing_anchor = _capabilities_missing_anchor(payload)
    allow_synthesis = bool(session_metadata.get("allow_skill_synthesis", False))
    if missing_anchor and allow_synthesis:
        return {"status": "failed",
                "summary": f"{len(missing_anchor)} 个 required capability 缺 source_anchor(合成开启时强制留痕)",
                "data": {"capabilities_missing_anchor": missing_anchor},
                "warnings": [], "errors": ["missing source_anchor"]}
    if missing_anchor:
        warnings.append(f"capability 缺 source_anchor: {', '.join(missing_anchor)}(覆盖矩阵将列为无出处)")
```

并在 save 成功路径追加矩阵落盘(GDD 文本来源:session 元数据里的 gdd 路径;若 session 不记 GDD 路径,扫 `ProjectInputs/GDD/*.md` 取 session 创建时登记的那份——以 `compiler_create_session` 实际记录为准,实施时查该 handler 确认字段名):

> **勘误(2026-06-11 实施期)**:下方片段中的 `_load_stage_module("gdd_coverage")` helper 在实施收尾时已删除,实际实现为标准包导入(统一走 `Compiler.stages` 包路径);本片段仅作规划期记录,以 `Plugins/AgentBridge/MCP/compiler_tools.py` 现行代码为准。

```python
    # GDD 覆盖矩阵 sidecar(JSON + 人读 markdown)
    try:
        coverage = _load_stage_module("gdd_coverage")  # 同 Task 8 的 importlib 加载模式
        gdd_text = Path(gdd_path).read_text(encoding="utf-8")
        sections = coverage.split_gdd_sections(gdd_text)
        all_capabilities = (payload.get("gameplay_capabilities", [])
                            + payload.get("baseline_capabilities", []))
        matrix = coverage.build_coverage_matrix(sections, all_capabilities)
        (session_dir / "gdd_coverage_matrix.json").write_text(
            json.dumps(matrix, ensure_ascii=False, indent=2), encoding="utf-8")
        (session_dir / "gdd_coverage_matrix.md").write_text(
            coverage.render_coverage_markdown(matrix), encoding="utf-8")
    except Exception as exc:
        warnings.append(f"覆盖矩阵生成失败(不阻塞): {exc}")
```

3b. `evidence_tools.py` 追加纯函数 + 在 `evidence_promote_run` 的既有 promotable 检查处接线:

```python
def _synthesized_promote_blockers(run_dir) -> list:
    """Phase 13 promote 守卫(spec §4.1/§4.4):
    1) run 消费了 synthesized skill → 不可 promote(试制章,与 heuristic_fallback 同级);
    2) run 存在未解决 capability_gaps(合成关闭/未完成时 gap 保留)→ 不可 promote(产物不完整)。
    """
    import json
    from pathlib import Path
    graph_path = Path(run_dir) / "skill_graph.json"
    if not graph_path.is_file():
        return []
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    reasons = []
    blocked = [
        node.get("instance_id", "<unknown>")
        for node in graph.get("nodes", [])
        if node.get("template_source") == "synthesized"
    ]
    if blocked:
        reasons.append(f"run 含 synthesized 节点不可 promote(试制): {', '.join(sorted(blocked))}")
    gaps = graph.get("metadata", {}).get("capability_gaps", [])
    if gaps:
        gap_ids = sorted(g.get("capability_id", "<unknown>") for g in gaps)
        reasons.append(f"run 存在未解决 capability_gaps 不可 promote(产物不完整): {', '.join(gap_ids)}")
    return reasons
```

设计决策记录(对 spec §4.4 的精化):spec 写的 `generator_type=synthesized` 把"模板来源"与"生成器类型"两轴混在了一起——合成模板节点的生成器仍是 mcp_agent,真正的试制属性在**模板来源**。故落地为节点级 `template_source="synthesized"`(skill_graph 即 single source of truth,promote 守卫读它),不在 fragment 内重复另立字段。此精化在收尾 document-release 时写入 spec 修订记录。

接线:在 `evidence_promote_run` 既有的 fast_mode / heuristic_fallback 拒绝逻辑同一处,调用 `_synthesized_promote_blockers(run_dir)`,非空则按同样的拒绝路径返回。

3c. `root_skill_contract.schema.json`:gameplay/baseline capability 条目的 properties 各加(不进 required):

```json
"source_anchor": {
  "type": "string",
  "description": "该能力在 GDD 中的出处(markdown 段落标题,覆盖矩阵认领依据;Phase 13)"
}
```

若 capability 条目 `additionalProperties: false`,本步必加,否则带 anchor 的 contract 过不了校验。

- [ ] **Step 4: 测试与回归**

Run: `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_anchor_and_promote.py -v`
Expected: 2 PASS
Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict && python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/MCP/ Plugins/AgentBridge/Schemas/root_skill_contract.schema.json Plugins/AgentBridge/Tests/scripts/test_phase13_anchor_and_promote.py
git commit -m "[skip-doc] feat(phase13): anchor 留痕(合成开启时强制)+ 覆盖矩阵落盘 + synthesized promote 拦截"
```

---

### Task 11: 新 schema 登记(覆盖矩阵)+ example

**Files:**
- Create: `Plugins/AgentBridge/Schemas/gdd_coverage_matrix.schema.json`
- Create: `Plugins/AgentBridge/Schemas/examples/phase13_gdd_coverage_matrix.example.json`
- Modify: `Plugins/AgentBridge/Scripts/validation/validate_examples.py`(EXAMPLE_TO_SCHEMA 加 1 条)

- [ ] **Step 1: 写 schema**

`Plugins/AgentBridge/Schemas/gdd_coverage_matrix.schema.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "GDD 覆盖矩阵",
  "description": "Phase 13 反向覆盖审计 sidecar:GDD 段落与 capability 认领关系",
  "type": "object",
  "additionalProperties": false,
  "required": ["rows", "capabilities_without_anchor", "dangling_anchors", "unclaimed_count"],
  "properties": {
    "rows": {
      "type": "array",
      "description": "逐段认领状态",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["heading", "start_line", "status", "claimed_by"],
        "properties": {
          "heading": {"type": "string", "description": "GDD 段落标题"},
          "start_line": {"type": "integer", "description": "段落起始行号"},
          "status": {"type": "string", "enum": ["claimed", "unclaimed"], "description": "认领状态"},
          "claimed_by": {"type": "array", "items": {"type": "string"}, "description": "认领该段的 capability_id 列表"}
        }
      }
    },
    "capabilities_without_anchor": {
      "type": "array", "items": {"type": "string"},
      "description": "source_anchor 为空的能力(可见,待人裁决)"
    },
    "dangling_anchors": {
      "type": "array", "items": {"type": "string"},
      "description": "指向不存在段落的 anchor(抽取错误信号)"
    },
    "unclaimed_count": {"type": "integer", "description": "无人认领段落数"}
  }
}
```

- [ ] **Step 2: 写 example**

`Plugins/AgentBridge/Schemas/examples/phase13_gdd_coverage_matrix.example.json`:

```json
{
  "rows": [
    {"heading": "2.1 棋盘与地块", "start_line": 3, "status": "claimed", "claimed_by": ["gameplay-board-topology"]},
    {"heading": "2.4 地产拍卖", "start_line": 6, "status": "claimed", "claimed_by": ["gameplay-auction"]},
    {"heading": "3.2 背景音乐", "start_line": 9, "status": "unclaimed", "claimed_by": []}
  ],
  "capabilities_without_anchor": [],
  "dangling_anchors": [],
  "unclaimed_count": 1
}
```

- [ ] **Step 3: 登记映射并跑 strict**

`validate_examples.py` 的 EXAMPLE_TO_SCHEMA 字典(Phase 11 段落附近)加:

```python
    "phase13_gdd_coverage_matrix.example.json":
        "gdd_coverage_matrix.schema.json",
```

Run: `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict`
Expected: checked 比改前 +1,全 passed

- [ ] **Step 4: Commit**

```bash
git add Plugins/AgentBridge/Schemas/ Plugins/AgentBridge/Scripts/validation/validate_examples.py
git commit -m "[skip-doc] feat(phase13): gdd_coverage_matrix schema + example 登记(strict +1)"
```

---

### Task 12: 系统测试 Stage 13 登记 + 全量回归

**Files:**
- Modify: `Plugins/AgentBridge/Tests/run_system_tests.py`(STAGES 加第 13 项)

- [ ] **Step 1: 登记 Stage 13**

STAGES 字典(第 12 项后)追加。case 数 = 本计划全部 SKS 用例实数,先数一遍再填(Task 1-10 的测试函数:SKS-01,02,03,03b,04,05,05b,06,07,07b,08,09,09b,10,11,12,13,13b,13c,14,15 → 21 个,以实际为准):

```python
    13: {
        'name': 'Phase 13 Skill Synthesis（SKS）',
        'cases': 'SKS-01 ~ SKS-15(含子用例)',
        'case_ids': make_case_ids('SKS', 1, 15),
        'count': 21,
        'requires_editor': False,
        'requires_build': False,
    },
```

并对照本文件中 stage→脚本的执行映射处(看 Stage 7/12 怎么把 stage 关联到 `Tests/scripts/test_*.py`,照同一模式把 Stage 13 关联到 `test_phase13_*.py` 全部文件)。

- [ ] **Step 2: 全量跑**

Run: `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor`
Expected: 全 PASS,TOTAL_CASES 自动 +21(sum 计算)。把新总数记下来,document-release 时同步 test_spec.md 与 INDEX 权威数字表。

- [ ] **Step 3: Commit**

```bash
git add Plugins/AgentBridge/Tests/run_system_tests.py
git commit -m "[skip-doc] test(phase13): 系统测试登记 Stage 13 SKS(全量回归绿)"
```

---

### Task 13: 验收资产——Monopoly 扩展 GDD + 验收 runbook

**Files:**
- Create: `ProjectInputs/GDD/monopoly_extended_auction_v1.md`
- Create: `ProjectState/Reports/2026-06-XX/phase13_acceptance_runbook.md`(XX=实施当日)

- [ ] **Step 1: 写扩展 GDD(植入 2 个已知库外能力,验收判据 2 的标准答案)**

`ProjectInputs/GDD/monopoly_extended_auction_v1.md`:

```markdown
# Monopoly 扩展版 GDD(拍卖 + 股票市场)v1

> Phase 13 验收载体。基于 GDD_MonopolyGame.md 的核心规则,植入 2 个模板库外能力
> (地产拍卖、股票市场),用于验证 capability gap 显式化与 Skill 合成闭环。
> 已知标准答案:本 GDD 应产生且仅产生 2 个 capability gap。

## 1. 游戏概述

经典 Monopoly 地产玩法(28 格环形棋盘、2-6 玩家、掷骰移动、购地收租、
监狱与破产),全部沿用 GDD_MonopolyGame.md 的 Phase 1 规则,本文不重复。

## 2. 扩展玩法

### 2.1 地产拍卖

玩家落在无主地产且选择不购买时,该地产立即进入英式拍卖:
- 起拍价为地价的 50%,加价步长为 10 金;
- 全体未破产玩家轮流出价或弃权,连续全体弃权则流拍,地产保持无主;
- 最高出价者立即按出价支付并获得地契;
- 拍卖过程必须在 HUD 上有可见的出价面板与当前最高价显示。

### 2.2 股票市场

棋盘新增 1 个"交易所"角格(替换一个普通空白格):
- 玩家途经或落在交易所时,可买入/卖出股票(共 3 支,价格随回合数波动);
- 股价波动规则:每回合开始时按掷骰结果 ±10% 调整;
- 玩家破产判定时,持仓股票按现价折算入总资产;
- 股票持仓需要在 HUD 上常驻显示当前市值。

## 3. 表现要求

### 3.1 拍卖界面

拍卖面板为屏幕中央弹出层,含当前地产名、最高价、出价按钮与弃权按钮。

### 3.2 交易所界面

交易所面板含 3 支股票的现价与持仓数,买入/卖出各一个按钮。
```

(预期 gap:`gameplay-auction` 与 `gameplay-stock-market`;§1 全部能力命中现有库。)

- [ ] **Step 2: 写验收 runbook(真机 + 双端,人工执行步骤书)**

`ProjectState/Reports/2026-06-XX/phase13_acceptance_runbook.md`(完整步骤书,执行时逐条打勾留证):

```markdown
# Phase 13 验收 runbook

> 对应 spec §8 验收判据 1-7。每条做完在本文件勾选并贴证据路径。

## 判据 1-4(机器,已由 CI 化测试覆盖)
- [ ] `python -m pytest Plugins/AgentBridge/Tests/scripts/test_phase13_*.py -v` 全绿(贴输出)
- [ ] `python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor` 全绿(贴 TOTAL/通过数)
- [ ] `python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict` 全绿

## 判据 2+3+4 实战(Claude Code 端)
1. [ ] 新建 session(allow_skill_synthesis=true),GDD 指向 monopoly_extended_auction_v1.md
2. [ ] Agent 驱动 Stage 1:capability 全部带 source_anchor;查看 gdd_coverage_matrix.md,
       无人认领段落逐条人工裁决并把结论记到本文件
3. [ ] Stage 2 → Stage 3:确认 skill_graph.metadata.capability_gaps 恰为
       gameplay-auction + gameplay-stock-market 两条(标准答案断言)
4. [ ] Agent 调 compiler_skill_synthesis_prepare/save 合成两个包;故意先提一版缺
       evaluator_prompt 的,确认 save 返回具体错误(重试闭环实战证据)
5. [ ] 人审 synthesis_review.md,把两个 manifest review_status 改 approved
6. [ ] 重跑 Stage 3:gaps 清空,skill-auction / skill-stock-market 入图
7. [ ] Stage 4-7 走完,Handoff v3 生成;确认含 synthesized 节点的 run promote 被拒
       (调 evidence_promote_run,预期拒绝并给出 synthesized 节点清单)

## 判据 6(Codex 端)
8. [ ] 【需 msc 授权】在 ~/.codex/config.toml 注册 agentbridge MCP server
       (项目外改动,执行前先在会话里确认)
9. [ ] Codex 驱动重复步骤 1-4(同一 GDD、新 run),产物结构等价断言:
       全部 stage 产物 schema 校验过 + capability_gaps 集合一致 + 合成包过机器校验
       (不要求内容字节一致)

## 判据 5(真机,人审挑一端产物)
10. [ ] 真机 UE 5.5 Editor 执行 approved Handoff,拍卖面板/交易所面板的
        UI Widget 与 Actor 落地、基础交互响应
11. [ ] 截图 + 日志落 ProjectState/Evidence/,路径贴到本文件

## 判据 7(stretch,非阻塞)
12. [ ] jrpg_turn_based_v1.md 全量合成尝试,结果(成败皆可)记入对比报告
```

- [ ] **Step 3: Commit**

```bash
git add ProjectInputs/GDD/monopoly_extended_auction_v1.md ProjectState/Reports/
git commit -m "[skip-doc] feat(phase13): 验收 GDD(植入拍卖+股票市场已知 gap)+ 验收 runbook"
```

---

### Task 14: 收尾——task.md 重建 + document-release + 分支收尾

**Files:**
- Modify: `task.md`(从归档跳转页重建为 Phase 13 任务书,引用 spec/plan/runbook)
- 全文档同步:由 document-release skill 驱动(AGENTS/CLAUDE/README/INDEX/SRS/HLD/LLD-04/LLD-06/contracts/test_spec/acceptance_report/FEATURE_INVENTORY 等)

- [ ] **Step 1: 重建 task.md 为 Phase 13 任务书**

入口页指向:spec(`Docs/superpowers/specs/2026-06-10-phase13-skill-synthesis-design.md`)、plan(本文件)、runbook、当前进度。保留 Phase 11/12 归档链接块(照抄现 task.md 的归档段)。

- [ ] **Step 2: 跑收尾链**

依序:`superpowers:verification-before-completion`(全部验证命令重跑留证)→ `document-release` skill(强制门禁,同步全部受影响文档,**注意**:MCP 工具数 +2、系统测试数 +21、schema 数 +1 三个权威数字必须按实测更新 INDEX §4 / mcp_tools_catalog / schemas_catalog / test_spec)→ 对 doc 改动再 verify → `superpowers:finishing-a-development-branch`(merge / PR)。

- [ ] **Step 3: 最终提交(不带 skip-doc,走完整 document-release 门禁)**

```bash
git add -A
git commit -m "docs(phase13): document-release 同步 Skill 合成主链(Stage 3 数据化 + S3.5 合成 + 覆盖矩阵)"
```

---

## 任务依赖与执行顺序

```
Task 1(golden,必须最先)
  → Task 2(manifest 数据)→ Task 3(扫描)→ Task 4(Stage 3 切换+等价门)
  → Task 5(family 数据化)
  → Task 6(校验器)→ Task 7(合成模块)→ Task 8(MCP 工具)
  → Task 9(覆盖矩阵)→ Task 10(anchor+promote 接线)
  → Task 11(schema 登记)→ Task 12(测试登记)
  → Task 13(验收资产)→ Task 14(收尾)
```

严格顺序执行;Task 4 的等价回归红灯时**禁止前进**。

## 风险提示(执行者必读)

1. Task 2 的 manifest 数据**逐字照抄**是等价回归的生命线,中文标点差一个全句不等。
2. Task 8/10 改 MCP handler 时,session 元数据的实际字段名以 `compiler_create_session` 现行实现为准,动手前先读该函数。
3. Task 10 的 anchor 强制只在 `allow_skill_synthesis=true` 时生效——这是既有系统测试不破的关键开关,不要做成无条件强制。
4. 真机验收(runbook 步骤 10-11)依赖 UE Editor 在跑、Remote Control 30010 通,环境问题不算代码缺陷,如实记录。
5. Codex 注册(runbook 步骤 8)是项目外改动,必须先获 msc 明确授权。
```
