# ForgeUE Manifest Import Bridge 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 AgentBridge 的 `handoff_runner.execute_run_plan` 能消费 ForgeUE_codex P4 输出的 `UEAssetManifest + import_plan.json`，把外部多模态资产 pipeline 的产出接入本项目 UE5 执行链。

**Architecture:** 新建独立 importer 模块 `forgeue_manifest_importer.py` 隔离所有 manifest 解析逻辑；最小侵入 `handoff_runner.execute_run_plan` 只多一个 `elif workflow_type == "import_assets"` dispatch 分支。Importer 复用 ForgeUE_codex 已有的三模式架构（`simulated` / `bridge_python` / `bridge_rc_api`）；本计划只完整实现 `simulated`，另两种留 `NotImplementedError` stub + 明确边界注释。所有真实集成测试用 fixture（直接复制自 ForgeUE_codex `demo_artifacts/p4_demo/`），保证两边契约不漂移。

**Tech Stack:** Python 3.x · jsonschema（已有依赖）· pytest（项目 conftest 在 `Plugins/AgentBridge/Tests/scripts/conftest.py`）· UTF-8 文件 IO · pathlib

---

## 文件结构

| 路径 | 责任 | 类型 |
|------|------|------|
| `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py` | 核心 importer：解析 manifest + import_plan，dispatch 到三种 bridge 模式，提供 CLI 入口 | 新建 |
| `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` | 在 `execute_run_plan` 加 `import_assets` dispatch（≤ 5 行新增） | 修改 |
| `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py` | 单元 + 集成测试：fixture-based | 新建 |
| `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json` | 真实 ForgeUE_codex P4 输出复制（fixture） | 新建 |
| `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json` | 真实 ForgeUE_codex P4 输出复制（fixture） | 新建 |
| `Plugins/AgentBridge/Docs/forgeue_manifest_integration.md` | 集成契约文档：输入字段、三种模式语义、版本兼容性、未实现部分 | 新建 |

**为什么放在 `Plugins/AgentBridge/Tests/scripts/`**：CLAUDE.md "绝对不要修改" 清单里禁的是 `Plugins/AgentBridge/AgentBridgeTests/`（UE C++ Automation Test 套件），不是 Python `Tests/`。后者下面 `conftest.py` 与现有 `test_e2e_orchestrator.py` 等均在此目录持续新增，是项目惯例位置。

---

## Task 0: 复制 ForgeUE_codex 真实 P4 输出作为测试 fixture

**Files:**
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json`
- Create: `Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json`

**为什么用真实输出做 fixture**：手写 mock 会让两边契约定义偷偷漂移；用 ForgeUE_codex 实际跑出来的输出，任何上游字段变化都会通过 fixture 失败暴露出来。

- [ ] **Step 1: 创建 fixture 目录**

```bash
mkdir -p "D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest"
```

- [ ] **Step 2: 复制真实 manifest.json**

```bash
cp "D:/ClaudeProject/ForgeUE_codex/demo_artifacts/p4_demo/test_p4_full_pipeline_writes_m0/FakeForgeProject/Content/Generated/run_p4_full/manifest.json" \
   "D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json"
```

- [ ] **Step 3: 复制真实 import_plan.json**

```bash
cp "D:/ClaudeProject/ForgeUE_codex/demo_artifacts/p4_demo/test_p4_full_pipeline_writes_m0/FakeForgeProject/Content/Generated/run_p4_full/import_plan.json" \
   "D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json"
```

- [ ] **Step 4: 验证 fixture 内容存在**

```bash
ls "D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/"
```
Expected output 包含两个文件：`manifest.json` `import_plan.json`

- [ ] **Step 5: 验证 fixture 关键字段**

```bash
python -c "import json; m=json.load(open('D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json',encoding='utf-8')); assert m['schema_version']=='1.0.0'; assert m['run_id']=='run_p4_full'; assert len(m['assets'])==1; assert m['assets'][0]['asset_kind']=='texture'; print('manifest OK')"
python -c "import json; p=json.load(open('D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json',encoding='utf-8')); assert p['manifest_id']=='m_run_p4_full'; assert len(p['operations'])==2; assert p['operations'][1]['kind']=='import_texture'; print('plan OK')"
```
Expected: `manifest OK` `plan OK`

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/
git commit -m "test: add ForgeUE_codex P4 manifest fixture for AgentBridge import bridge"
```

---

## Task 1: importer 核心模块——manifest 解析（TDD）

**Files:**
- Create: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`
- Create: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`

- [ ] **Step 1: 先写失败的解析测试**

写入 `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`：

```python
"""ForgeUE Manifest Importer 测试。

测试用 fixture 是直接从 ForgeUE_codex demo_artifacts/p4_demo/ 复制的真实 P4 输出，
任何上游字段漂移都会通过 fixture 加载失败立刻暴露。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# 让测试能找到 Scripts/orchestrator/ 目录
_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_ORCHESTRATOR_DIR = _PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "orchestrator"
if str(_ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(_ORCHESTRATOR_DIR))

import forgeue_manifest_importer as importer  # noqa: E402


_FIXTURE_DIR = (
    _PROJECT_ROOT
    / "Plugins"
    / "AgentBridge"
    / "Tests"
    / "fixtures"
    / "forgeue_manifest"
)
_MANIFEST_PATH = _FIXTURE_DIR / "manifest.json"
_PLAN_PATH = _FIXTURE_DIR / "import_plan.json"


def test_parse_manifest_reads_schema_version_and_assets():
    """ForgeUE_codex manifest.json 必读字段：schema_version / run_id / assets[]."""
    parsed = importer.parse_manifest(str(_MANIFEST_PATH))

    assert parsed["schema_version"] == "1.0.0"
    assert parsed["run_id"] == "run_p4_full"
    assert len(parsed["assets"]) == 1
    asset = parsed["assets"][0]
    assert asset["asset_kind"] == "texture"
    assert asset["ue_naming"]["ue_name"] == "T_run_p4_full_step_image_cand_e0726e0a_0"
    assert asset["source_uri"].endswith(".png")
```

- [ ] **Step 2: 跑测试验证失败**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py::test_parse_manifest_reads_schema_version_and_assets -v
```
Expected: FAIL，错误为 `ModuleNotFoundError: No module named 'forgeue_manifest_importer'`

- [ ] **Step 3: 写最小 importer 模块满足该测试**

写入 `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`：

```python
"""ForgeUE_codex UEAssetManifest 导入桥接。

读取 ForgeUE_codex P4 流水线产出的 `manifest.json` + `import_plan.json`，
按 bridge_mode 分发到 simulated / bridge_python / bridge_rc_api 三种执行通路。

输入契约固定为 ForgeUE_codex `framework.core.ue.UEAssetManifest`
（schema_version 1.0.0），asset_kind 枚举：
    texture / sound_wave / static_mesh / material / file_media_source

设计原则:
- 只负责"读 manifest → 翻译成 AgentBridge 可执行单元"
- 不做任何 UE Editor 内部副作用（那是 bridge_mode 各自下游的事）
- simulated 模式必须能完全离线跑通，作为契约不漂移的看护
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_manifest(manifest_path: str) -> dict[str, Any]:
    """读 ForgeUE_codex manifest.json 并做基本校验。

    返回的 dict 至少包含 ``schema_version`` / ``run_id`` / ``assets``。
    上游 schema 若往 2.x 演进且不向后兼容，本函数会通过断言早期失败。
    """
    raw = json.loads(Path(manifest_path).read_text(encoding="utf-8"))

    # 只允许已对齐的契约版本；上游升级时这里会显式断版本号。
    schema_version = raw.get("schema_version")
    if schema_version != "1.0.0":
        raise ValueError(
            f"unsupported manifest schema_version: {schema_version!r} "
            f"(this bridge only supports '1.0.0')"
        )

    if not isinstance(raw.get("assets"), list):
        raise ValueError("manifest.assets must be a list")

    return raw
```

- [ ] **Step 4: 跑测试验证通过**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py::test_parse_manifest_reads_schema_version_and_assets -v
```
Expected: PASS

- [ ] **Step 5: 增加错误路径测试**

在 `test_forgeue_manifest_importer.py` 末尾追加：

```python
def test_parse_manifest_rejects_unsupported_schema_version(tmp_path):
    """contract guard: 上游 schema_version 漂移必须显式失败,不能 silently 接受。"""
    bad = tmp_path / "bad_manifest.json"
    bad.write_text('{"schema_version": "2.0.0", "assets": []}', encoding="utf-8")

    with pytest.raises(ValueError, match="unsupported manifest schema_version"):
        importer.parse_manifest(str(bad))


def test_parse_manifest_rejects_non_list_assets(tmp_path):
    """contract guard: assets 必须是 list,防止上游契约畸变。"""
    bad = tmp_path / "bad_manifest.json"
    bad.write_text('{"schema_version": "1.0.0", "assets": "not-a-list"}', encoding="utf-8")

    with pytest.raises(ValueError, match="manifest.assets must be a list"):
        importer.parse_manifest(str(bad))
```

- [ ] **Step 6: 跑全部测试验证通过**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "feat(orchestrator): add ForgeUE manifest parser with schema_version contract guard"
```

---

## Task 2: importer 核心模块——simulated 模式 import_from_manifest（TDD）

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`

- [ ] **Step 1: 写失败的 simulated 集成测试**

在 `test_forgeue_manifest_importer.py` 末尾追加：

```python
def test_import_from_manifest_simulated_returns_one_op_per_asset():
    """simulated mode: 每个 asset entry → 一条 op 模拟结果, 状态 success."""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=str(_PLAN_PATH),
        bridge_mode="simulated",
    )

    assert result["status"] == "success"
    assert result["bridge_mode"] == "simulated"
    assert result["run_id"] == "run_p4_full"
    assert result["manifest_id"] == "m_run_p4_full"
    assert result["plan_id"] == "p_run_p4_full"
    assert len(result["asset_results"]) == 1

    asset_result = result["asset_results"][0]
    assert asset_result["status"] == "success"
    assert asset_result["asset_kind"] == "texture"
    assert asset_result["target_object_path"].startswith("/Game/Generated/Tavern/run_p4_full/T_")
    assert asset_result["simulated"] is True


def test_import_from_manifest_simulated_without_plan_path_still_works():
    """plan_path 可选: 只有 manifest 时,生成 asset_results 但不带 plan_id。"""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=None,
        bridge_mode="simulated",
    )

    assert result["status"] == "success"
    assert result["plan_id"] is None
    assert len(result["asset_results"]) == 1
```

- [ ] **Step 2: 跑测试验证失败**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py::test_import_from_manifest_simulated_returns_one_op_per_asset -v
```
Expected: FAIL，错误为 `AttributeError: module 'forgeue_manifest_importer' has no attribute 'import_from_manifest'`

- [ ] **Step 3: 实现 import_from_manifest（simulated 分支 + 其余 stub）**

在 `forgeue_manifest_importer.py` 末尾追加：

```python
_SUPPORTED_BRIDGE_MODES: tuple[str, ...] = (
    "simulated",
    "bridge_python",
    "bridge_rc_api",
)


def parse_import_plan(plan_path: str) -> dict[str, Any]:
    """读 ForgeUE_codex import_plan.json 并做基本结构校验。"""
    raw = json.loads(Path(plan_path).read_text(encoding="utf-8"))
    if not isinstance(raw.get("operations"), list):
        raise ValueError("import_plan.operations must be a list")
    return raw


def import_from_manifest(
    *,
    manifest_path: str,
    plan_path: str | None = None,
    bridge_mode: str = "simulated",
) -> dict[str, Any]:
    """主入口:按 bridge_mode dispatch,返回结构化执行结果。

    - simulated: 离线模拟,不副作用,用于契约校验 + handoff_runner 单元测试
    - bridge_python: 调 UE Python Editor API(本计划留 NotImplementedError stub)
    - bridge_rc_api: 调 Remote Control API(本计划留 NotImplementedError stub)
    """
    if bridge_mode not in _SUPPORTED_BRIDGE_MODES:
        raise ValueError(
            f"unsupported bridge_mode: {bridge_mode!r} "
            f"(expected one of {_SUPPORTED_BRIDGE_MODES})"
        )

    manifest = parse_manifest(manifest_path)
    plan = parse_import_plan(plan_path) if plan_path else None

    if bridge_mode == "simulated":
        asset_results = [_simulate_asset(asset) for asset in manifest["assets"]]
        return {
            "status": "success",
            "bridge_mode": bridge_mode,
            "run_id": manifest["run_id"],
            "manifest_id": manifest.get("manifest_id"),
            "plan_id": plan.get("plan_id") if plan else None,
            "asset_results": asset_results,
        }

    # bridge_python / bridge_rc_api 由 Task 4 填充 NotImplementedError stub
    raise NotImplementedError(
        f"bridge_mode={bridge_mode!r} not implemented in this milestone"
    )


def _simulate_asset(asset: dict[str, Any]) -> dict[str, Any]:
    """单 asset 的模拟执行结果——不做任何 UE 副作用。"""
    return {
        "status": "success",
        "asset_entry_id": asset.get("asset_entry_id"),
        "artifact_id": asset.get("artifact_id"),
        "asset_kind": asset.get("asset_kind"),
        "target_object_path": asset.get("target_object_path"),
        "source_uri": asset.get("source_uri"),
        "simulated": True,
    }
```

- [ ] **Step 4: 跑测试验证通过**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 5 passed

- [ ] **Step 5: 加 bridge_mode 校验测试**

在 `test_forgeue_manifest_importer.py` 末尾追加：

```python
def test_import_from_manifest_rejects_unknown_bridge_mode():
    """contract guard: 未知 bridge_mode 必须早期失败。"""
    with pytest.raises(ValueError, match="unsupported bridge_mode"):
        importer.import_from_manifest(
            manifest_path=str(_MANIFEST_PATH),
            bridge_mode="totally_made_up",
        )
```

- [ ] **Step 6: 跑测试**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 6 passed

- [ ] **Step 7: Commit**

```bash
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "feat(orchestrator): implement simulated bridge_mode for ForgeUE manifest importer"
```

---

## Task 3: handoff_runner.execute_run_plan 接入 import_assets dispatch（TDD）

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py:120-150`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`

- [ ] **Step 1: 写失败的 dispatch 集成测试**

在 `test_forgeue_manifest_importer.py` 末尾追加：

```python
def test_handoff_runner_dispatches_import_assets_to_forgeue_importer():
    """end-to-end: handoff_runner.execute_run_plan 收到 import_assets step
    时,应 dispatch 到 forgeue_manifest_importer 而不是 fall through 到
    "未实现的 workflow_type" silent skip 分支。
    """
    # 让 handoff_runner 能 import
    sys.path.insert(0, str(_ORCHESTRATOR_DIR.parent / "bridge"))
    sys.path.insert(0, str(_ORCHESTRATOR_DIR))
    import handoff_runner  # noqa: PLC0415

    run_plan = {
        "run_plan_id": "runplan.test.forgeue.dispatch",
        "source_handoff_id": "handoff.test.dispatch",
        "workflow_sequence": [
            {
                "step_id": "import_forgeue_textures",
                "workflow_type": "import_assets",
                "params": {
                    "manifest_path": str(_MANIFEST_PATH),
                    "plan_path": str(_PLAN_PATH),
                    "bridge_mode": "simulated",
                },
            }
        ],
    }

    result = handoff_runner.execute_run_plan(run_plan, bridge_mode="simulated")

    assert result["status"] == "succeeded"
    step_results = result["step_results"]
    assert len(step_results) == 1
    inner = step_results[0]["result"]
    assert inner["status"] == "success"
    assert inner["bridge_mode"] == "simulated"
    assert len(inner["asset_results"]) == 1
```

- [ ] **Step 2: 跑测试验证失败**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py::test_handoff_runner_dispatches_import_assets_to_forgeue_importer -v
```
Expected: FAIL，inner result 是 `{"status": "skipped", "reason": "未实现的 workflow_type: import_assets"}`

- [ ] **Step 3: 在 handoff_runner.py 加 dispatch 分支**

在 `Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` 中找到 `execute_run_plan` 函数（第 110 行起），把现有 dispatch chain 改为：

```python
        # 桥接到现有 Bridge 接口
        if workflow_type == "spawn_actor":
            result = execute_spawn_actor(params, bridge_mode)
            if result.get("status") == "success":
                action_results = execute_post_spawn_actions(result, params, bridge_mode)
                if action_results:
                    result["post_spawn_actions"] = action_results
        elif workflow_type == "set_actor_transform":
            result = execute_set_actor_transform(params, bridge_mode)
        elif workflow_type == "import_assets":
            # 接 ForgeUE_codex P4 manifest_only 输出
            # params 约定: manifest_path / plan_path(可选) / bridge_mode(可选,默认沿用外层)
            from forgeue_manifest_importer import import_from_manifest
            result = import_from_manifest(
                manifest_path=params["manifest_path"],
                plan_path=params.get("plan_path"),
                bridge_mode=params.get("bridge_mode", bridge_mode),
            )
        else:
            result = {"status": "skipped", "reason": f"未实现的 workflow_type: {workflow_type}"}
```

- [ ] **Step 4: 跑测试验证通过**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 7 passed

- [ ] **Step 5: 跑 AgentBridge 既有测试确认无回归**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/ -v --ignore=Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py 2>&1 | tail -30
```
Expected: 所有原有用例 PASS，无失败。

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "feat(orchestrator): dispatch import_assets workflow_type to ForgeUE manifest importer"
```

---

## Task 4: bridge_python / bridge_rc_api 显式 stub + 测试

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`

**为什么显式 stub 而不是默默 raise**：测试明确"这两个模式当前是未实现，未来要做"，下游使用方调用时报错信息要够具体，能直接指向后续工作。

- [ ] **Step 1: 写失败的 stub 测试**

在 `test_forgeue_manifest_importer.py` 末尾追加：

```python
@pytest.mark.parametrize("mode", ["bridge_python", "bridge_rc_api"])
def test_import_from_manifest_unimplemented_bridge_modes_raise_with_clear_message(mode):
    """bridge_python / bridge_rc_api 当前未实现, 必须 raise NotImplementedError
    且消息里点名 mode + 指向后续工作, 不能 silent return 假成功。
    """
    with pytest.raises(NotImplementedError) as exc:
        importer.import_from_manifest(
            manifest_path=str(_MANIFEST_PATH),
            plan_path=str(_PLAN_PATH),
            bridge_mode=mode,
        )
    assert mode in str(exc.value)
```

- [ ] **Step 2: 跑测试验证通过（Task 2 已实现 raise NotImplementedError，但消息要确保包含 mode 名）**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest "Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py::test_import_from_manifest_unimplemented_bridge_modes_raise_with_clear_message" -v
```
Expected: 2 passed（Task 2 实现的 stub 消息 `f"bridge_mode={bridge_mode!r} not implemented in this milestone"` 已经包含 mode 名）。

- [ ] **Step 3: 在 importer 文件顶部模块 docstring 后补"未实现部分"注释块，让 reader 一眼看到边界**

在 `forgeue_manifest_importer.py` 模块 docstring 与第一个 `from __future__` 之间插入：

```python
# ------------------------------------------------------------
# 未实现部分（后续 milestone 接入）
# ------------------------------------------------------------
# bridge_python:
#   在 UE Editor 进程内通过 unreal Python API 调 AssetTools.ImportAssets,
#   对每条 op 写 evidence（沿用 ForgeUE_codex 的 evidence.json 契约）。
#   只能在 UE Editor 内执行,不能离线跑;触发条件:UE Editor 启动 +
#   AgentBridge subsystem 已 ready。
#
# bridge_rc_api:
#   通过 Remote Control API（端口 30010）远程触发同样的导入。
#   依赖 bridge.remote_control_client; 触发条件: UE Editor + Remote Control
#   plugin enabled。
# ------------------------------------------------------------
```

- [ ] **Step 4: 跑全部测试**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 9 passed（7 已有 + 2 parametrize）

- [ ] **Step 5: Commit**

```bash
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "test(orchestrator): cover unimplemented bridge_python/bridge_rc_api stubs with clear messages"
```

---

## Task 5: CLI 入口——绕过 handoff 直接消费 ForgeUE_codex 输出

**Files:**
- Modify: `Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py`
- Modify: `Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py`

**为什么要 CLI**：开发期排查时希望直接拿一份 ForgeUE_codex 输出，不经 handoff 跑一遍 importer 看结果。也是给 ForgeUE_codex 那边将来作为"运行完 P4 后调一下 AgentBridge"的最低门槛接口。

- [ ] **Step 1: 写 CLI 失败测试**

在 `test_forgeue_manifest_importer.py` 末尾追加：

```python
def test_cli_main_simulated_prints_json_and_returns_zero(capsys):
    """CLI: --manifest + --plan + --bridge-mode simulated 应输出 JSON 到 stdout 并 return 0."""
    rc = importer.main([
        "--manifest", str(_MANIFEST_PATH),
        "--plan", str(_PLAN_PATH),
        "--bridge-mode", "simulated",
    ])
    captured = capsys.readouterr()

    assert rc == 0
    import json as _json
    payload = _json.loads(captured.out)
    assert payload["status"] == "success"
    assert payload["bridge_mode"] == "simulated"
    assert len(payload["asset_results"]) == 1


def test_cli_main_unimplemented_mode_returns_nonzero(capsys):
    """CLI: 未实现 mode 应 return 非 0 并把错误打到 stderr,不抛 traceback 出去。"""
    rc = importer.main([
        "--manifest", str(_MANIFEST_PATH),
        "--bridge-mode", "bridge_python",
    ])
    captured = capsys.readouterr()

    assert rc != 0
    assert "bridge_python" in captured.err
```

- [ ] **Step 2: 跑测试验证失败**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py::test_cli_main_simulated_prints_json_and_returns_zero -v
```
Expected: FAIL，错误为 `AttributeError: module 'forgeue_manifest_importer' has no attribute 'main'`

- [ ] **Step 3: 在 importer 文件末尾追加 CLI 入口**

```python
# ------------------------------------------------------------
# CLI 入口
# ------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """命令行入口:`python -m ... --manifest <path> [--plan <path>] [--bridge-mode simulated]`。

    成功:把 import_from_manifest 结果 JSON 打到 stdout, return 0
    失败:把错误消息打到 stderr, return 非 0(不抛 traceback)
    """
    import argparse
    import sys as _sys

    parser = argparse.ArgumentParser(
        description="ForgeUE_codex manifest importer (standalone CLI)",
    )
    parser.add_argument("--manifest", required=True, help="ForgeUE_codex manifest.json 路径")
    parser.add_argument("--plan", default=None, help="ForgeUE_codex import_plan.json 路径(可选)")
    parser.add_argument(
        "--bridge-mode",
        default="simulated",
        choices=list(_SUPPORTED_BRIDGE_MODES),
        help="桥接执行模式(默认 simulated)",
    )
    args = parser.parse_args(argv)

    try:
        result = import_from_manifest(
            manifest_path=args.manifest,
            plan_path=args.plan,
            bridge_mode=args.bridge_mode,
        )
    except (ValueError, NotImplementedError, FileNotFoundError) as exc:
        print(f"[forgeue_manifest_importer] {exc}", file=_sys.stderr)
        return 2

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    import sys as _sys
    _sys.exit(main())
```

- [ ] **Step 4: 跑测试验证通过**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 11 passed

- [ ] **Step 5: 手工跑一次 CLI 端到端确认**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py --manifest Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json --plan Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json --bridge-mode simulated
```
Expected: stdout 是一段 JSON，`"status": "success"` `"asset_results"` 含一条 texture entry，exit code 0

- [ ] **Step 6: Commit**

```bash
git add Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py
git commit -m "feat(orchestrator): add standalone CLI for ForgeUE manifest importer"
```

---

## Task 6: 集成契约文档

**Files:**
- Create: `Plugins/AgentBridge/Docs/forgeue_manifest_integration.md`

- [ ] **Step 1: 写文档**

写入 `Plugins/AgentBridge/Docs/forgeue_manifest_integration.md`：

```markdown
# ForgeUE_codex Manifest 集成契约

> 本文档定义 AgentBridge 如何消费 ForgeUE_codex P4 流水线产出的 `UEAssetManifest`，把外部多模态资产生成结果接入本项目 UE5 执行链。

## 上游契约

来源项目：`D:/ClaudeProject/ForgeUE_codex`（独立 Python 包，与本项目同机部署）。

来源模块：`framework.engine_bridge.unreal.contract.manifest_builder.build_manifest`。

产物：每个 ForgeUE_codex run 在 `<UEProject>/Content/Generated/<run_id>/` 下写出三个文件——
- `manifest.json` —— `UEAssetManifest` 序列化（**必须**）
- `import_plan.json` —— `UEImportPlan` 序列化（可选）
- `evidence.json` —— 上游执行 evidence（本桥不消费）

支持的 schema_version：**`1.0.0`**。上游升级到 2.x 时桥会在 `parse_manifest` 早期 raise `ValueError`。

## asset_kind 覆盖范围

来源 `_KIND_MAP`（`manifest_builder.py`）：

| modality.shape | asset_kind | UE prefix |
|---|---|---|
| image.raster | texture | T_ |
| image.sprite_sheet | texture | T_ |
| audio.waveform | sound_wave | S_ |
| mesh.gltf/fbx/obj | static_mesh | SM_ |
| material.definition | material | M_ |
| video.mp4 | file_media_source | MS_ |

## 三种 bridge_mode

| mode | 状态 | 副作用 | 用途 |
|---|---|---|---|
| `simulated` | **已实现** | 无 | 契约校验、handoff_runner 单元测试、CI/CD 离线门禁 |
| `bridge_python` | NotImplementedError stub | 调 UE Python Editor API | 未来 milestone：在 UE Editor 进程内导入 |
| `bridge_rc_api` | NotImplementedError stub | 调 Remote Control API（30010） | 未来 milestone：远程触发导入 |

## 两种调用入口

### A. 通过 handoff_runner（标准入口）

在 `run_plan.workflow_sequence` 加一步 `workflow_type: "import_assets"`：

```json
{
  "step_id": "import_forgeue_run_p4_full",
  "workflow_type": "import_assets",
  "params": {
    "manifest_path": "<absolute path to manifest.json>",
    "plan_path": "<absolute path to import_plan.json>",
    "bridge_mode": "simulated"
  }
}
```

dispatch 入口：`Plugins/AgentBridge/Scripts/orchestrator/handoff_runner.py` 的 `execute_run_plan`。

### B. 独立 CLI（排查、ad-hoc 集成）

```bash
python Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py \
  --manifest <path-to-manifest.json> \
  [--plan <path-to-import_plan.json>] \
  [--bridge-mode simulated]
```

成功：JSON 到 stdout、exit 0。失败：错误到 stderr、exit 非 0。

## 跨项目部署约束

ForgeUE_codex 的 `UEAssetManifest` 设计**假定 payload 文件已经物理位于 `<UEProject>/Content/Generated/<run_id>/`**（见 `manifest_builder.py` 模块 docstring）。这意味着：

1. **同机部署**：ForgeUE_codex 的 `UEOutputTarget.project_root` 必须配置成本项目工程根 `D:/UnrealProjects/Mvpv4TestCodex/`。
2. **跨机部署**：需要在两机之间提前同步 `Content/Generated/<run_id>/` 目录，本桥不负责文件搬运。

## 未实现部分 / 后续工作

- `bridge_python`：进入 UE Editor 进程实现真正导入。预计落点：在 `Plugins/AgentBridge/Source/AgentBridge/Private/` 加 `ImportFromForgeUEManifest` 蓝图节点，桥到 Python `forgeue_manifest_importer.import_from_manifest(..., bridge_mode="bridge_python")`。
- `bridge_rc_api`：通过 `bridge.remote_control_client` 远程触发同样的导入。
- evidence 回写：当前桥只 read manifest + plan，**不消费 evidence.json**，也不写回成功/失败 evidence。后续可加 evidence cross-check（对比 ForgeUE_codex 上游 evidence 与本侧导入结果）。
- 资产清单覆盖：当前 5+1 种 asset_kind 都在 simulated 模式下走通用 `_simulate_asset`；bridge_python 接入时需要按 asset_kind 分派到 UE 对应导入器。

## 版本约束

- 本桥支持 manifest `schema_version == "1.0.0"`。
- 上游 ForgeUE_codex 升级 schema 时，本桥应同步更新 `_SUPPORTED_SCHEMA_VERSIONS` 集合（当前以单值字符串硬编码）。
- fixture 同步：`Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/` 下的 manifest/import_plan 是从 `D:/ClaudeProject/ForgeUE_codex/demo_artifacts/p4_demo/test_p4_full_pipeline_writes_m0/...` 复制的真实输出，上游变更时应重新复制（避免契约漂移）。
```

- [ ] **Step 2: Commit**

```bash
git add Plugins/AgentBridge/Docs/forgeue_manifest_integration.md
git commit -m "docs(agentbridge): add ForgeUE_codex manifest integration contract"
```

---

## Task 7: 最终验证

**Files:** (无修改)

- [ ] **Step 1: 跑新增测试**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/test_forgeue_manifest_importer.py -v
```
Expected: 11 passed

- [ ] **Step 2: 跑既有 AgentBridge Python 测试无回归**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python -m pytest Plugins/AgentBridge/Tests/scripts/ -v 2>&1 | tail -40
```
Expected: 所有原有用例 PASS，整体绿色。

- [ ] **Step 3: 跑 ForgeUE_codex P4 测试确认上游契约没动**

```bash
cd D:/ClaudeProject/ForgeUE_codex && python -m pytest tests/integration/test_p4_ue_manifest_only.py -v 2>&1 | tail -20
```
Expected: 15 passed（与计划撰写时一致）

- [ ] **Step 4: 跑现有 Schema 校验确保未污染 schemas**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict 2>&1 | tail -10
```
Expected: 校验通过（具体 OK 行数视实际而定，关键是不能出现 ERROR）

- [ ] **Step 5: 手工 end-to-end smoke**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && python Plugins/AgentBridge/Scripts/orchestrator/forgeue_manifest_importer.py --manifest Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/manifest.json --plan Plugins/AgentBridge/Tests/fixtures/forgeue_manifest/import_plan.json --bridge-mode simulated
```
Expected: 输出 JSON 含 `"status": "success"` + 一条 `asset_kind: "texture"` 的 asset_result

- [ ] **Step 6: git status 确认所有改动已提交**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && git status
```
Expected: `nothing to commit, working tree clean`（除了已知的 `.codex/config.toml` modified——那是计划前就有的状态）

- [ ] **Step 7: 列出 commit 历史**

```bash
cd D:/UnrealProjects/Mvpv4TestCodex && git log --oneline -10
```
Expected: 顶部 6 个新 commit 按 Task 0-6 顺序排列（fixture / parser / simulated / dispatch / stub / CLI / docs）

---

## Self-Review 检查记录

**1. Spec coverage（覆盖度）**：
- ✅ "AgentBridge 加 manifest_only 模式的 import_assets 执行器" → Task 3
- ✅ "读 ForgeUE_codex 输出的 manifest.json + import_plan.json" → Task 1 / Task 2
- ✅ "至少 simulated 模式必须完整实现" → Task 2
- ✅ "bridge_python / bridge_rc_api 留 stub + 明确边界注释" → Task 4
- ✅ "独立 CLI 入口可绕过 handoff" → Task 5
- ✅ "测试用 fixture 验证契约不漂移" → Task 0 + 全部测试 import 它
- ✅ "集成契约文档" → Task 6
- ✅ "用 ForgeUE_codex 真实 P4 输出做 fixture" → Task 0 直接 cp 自 demo_artifacts
- ✅ "最小侵入 handoff_runner（只加 1 个 elif 分支）" → Task 3 Step 3

**2. Placeholder 扫描**：
- 所有 code step 都给出完整可执行代码块
- 没有 "TODO / TBD / similar to / write appropriate" 类占位
- 唯一的 "未实现" 部分是 bridge_python / bridge_rc_api，**已被 Task 4 显式覆盖为 NotImplementedError + 注释块**，不是占位

**3. 类型/接口一致性**：
- `parse_manifest(manifest_path: str) -> dict` —— Task 1 定义、Task 2 调用 ✅
- `parse_import_plan(plan_path: str) -> dict` —— Task 2 定义、`import_from_manifest` 调用 ✅
- `import_from_manifest(*, manifest_path, plan_path, bridge_mode) -> dict` —— Task 2 定义、Task 3 dispatch 调用、Task 5 CLI 调用 ✅（kw-only 关键字保持一致）
- `_SUPPORTED_BRIDGE_MODES` 元组 —— Task 2 定义、Task 5 CLI choices 引用 ✅
- handoff_runner dispatch 里读取的 params keys：`manifest_path` / `plan_path` / `bridge_mode` —— 与 importer 签名一致 ✅
