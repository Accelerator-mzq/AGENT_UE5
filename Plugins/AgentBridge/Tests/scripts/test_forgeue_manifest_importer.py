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
    """ForgeUE_codex manifest.json 必读字段:schema_version / run_id / assets[]."""
    parsed = importer.parse_manifest(str(_MANIFEST_PATH))

    assert parsed["schema_version"] == "1.0.0"
    assert parsed["run_id"] == "run_p4_full"
    assert len(parsed["assets"]) == 1
    asset = parsed["assets"][0]
    assert asset["asset_kind"] == "texture"
    assert asset["ue_naming"]["ue_name"] == "T_run_p4_full_step_image_cand_e0726e0a_0"
    assert asset["source_uri"].endswith(".png")


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
