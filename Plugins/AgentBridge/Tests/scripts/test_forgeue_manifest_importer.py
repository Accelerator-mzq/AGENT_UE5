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
    """ForgeUE_codex manifest.json 必读字段:schema_version / run_id / assets[]。"""
    parsed = importer.parse_manifest(str(_MANIFEST_PATH))

    assert parsed["schema_version"] == "1.0.0"
    assert parsed["run_id"] == "run_p4_full"
    assert len(parsed["assets"]) == 6, "fixture 扩到 6 种 asset_kind"

    kinds = {a["asset_kind"] for a in parsed["assets"]}
    assert kinds == {"texture", "sprite_sheet", "sound_wave", "static_mesh", "material", "file_media_source"}

    # texture entry 字段健康检查(回归保护)
    tex = next(a for a in parsed["assets"] if a["asset_kind"] == "texture")
    assert tex["ue_naming"]["ue_name"].startswith("T_")
    assert tex["source_uri"].endswith(".png")


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


def test_import_from_manifest_simulated_returns_six_ops_one_per_asset():
    """simulated mode:6 种 asset 各产出一条 op 模拟结果,全 success。"""
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
    assert len(result["asset_results"]) == 6

    # 6 种 kind 全覆盖
    kinds_in_results = {r["asset_kind"] for r in result["asset_results"]}
    assert kinds_in_results == {"texture", "sprite_sheet", "sound_wave", "static_mesh", "material", "file_media_source"}

    # 全 simulated 标记
    for r in result["asset_results"]:
        assert r["status"] == "success"
        assert r["simulated"] is True


def test_import_from_manifest_simulated_without_plan_path_still_works():
    """plan_path 可选:只有 manifest 时,6 条 asset_results 但 plan_id=None。"""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=None,
        bridge_mode="simulated",
    )

    assert result["status"] == "success"
    assert result["plan_id"] is None
    assert len(result["asset_results"]) == 6


def test_import_from_manifest_rejects_unknown_bridge_mode():
    """contract guard: 未知 bridge_mode 必须早期失败。"""
    with pytest.raises(ValueError, match="unsupported bridge_mode"):
        importer.import_from_manifest(
            manifest_path=str(_MANIFEST_PATH),
            bridge_mode="totally_made_up",
        )


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
    assert len(inner["asset_results"]) == 6


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
    assert len(payload["asset_results"]) == 6


def test_cli_main_unimplemented_mode_returns_nonzero(capsys):
    """CLI: 未实现 mode 应 return 非 0 并把错误打到 stderr,不抛 traceback 出去。"""
    rc = importer.main([
        "--manifest", str(_MANIFEST_PATH),
        "--bridge-mode", "bridge_python",
    ])
    captured = capsys.readouterr()

    assert rc != 0
    assert "bridge_python" in captured.err


# ============================================================
# Task 3.2 新增:每种 asset_kind 的 simulated 字段健康检查
# ============================================================

@pytest.mark.parametrize("kind,prefix", [
    ("texture",            "T_"),
    ("sprite_sheet",       "T_"),
    ("sound_wave",         "S_"),
    ("static_mesh",        "SM_"),
    ("material",           "M_"),
    ("file_media_source",  "MS_"),
])
def test_simulated_per_kind_target_object_path_uses_correct_prefix(kind, prefix):
    """每种 asset_kind 的 target_object_path 必须用对应 prefix(回归保护命名策略)。"""
    result = importer.import_from_manifest(
        manifest_path=str(_MANIFEST_PATH),
        plan_path=str(_PLAN_PATH),
        bridge_mode="simulated",
    )

    matching = [r for r in result["asset_results"] if r["asset_kind"] == kind]
    assert len(matching) >= 1, f"fixture 必须含至少 1 个 {kind} entry"

    for r in matching:
        # target_object_path 形如 /Game/.../<PREFIX>name
        leaf_name = r["target_object_path"].rsplit("/", 1)[-1]
        assert leaf_name.startswith(prefix), \
            f"{kind} target {leaf_name!r} 应以 {prefix!r} 开头"
