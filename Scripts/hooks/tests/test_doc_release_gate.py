"""doc_release_gate.py 单元测试"""
# 测试 marker IO、hash、check/write 流程
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from Scripts.hooks import doc_release_gate as gate


def test_marker_roundtrip(tmp_path: Path) -> None:
    # 写入 marker 后能原样读出
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    m = gate.Marker(
        branch="feat/x",
        head_sha="abc123",
        staged_files_hash="deadbeef",
        audit_evidence_path="ProjectState/Reports/2026-05-25/document_release_audit.md",
        timestamp="2026-05-25T10:00:00+08:00",
    )
    gate.write_marker_file(marker_dir, m)
    loaded = gate.read_marker_file(marker_dir, "feat/x")
    assert loaded == m


def test_marker_missing_returns_none(tmp_path: Path) -> None:
    # 不存在时返回 None,不抛错
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    assert gate.read_marker_file(marker_dir, "no-such-branch") is None


def test_compute_staged_files_hash_stable_under_order() -> None:
    # 同一组文件无论顺序如何,hash 一致
    h1 = gate.compute_staged_files_hash(["a.py", "b.py", "c.md"])
    h2 = gate.compute_staged_files_hash(["c.md", "b.py", "a.py"])
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex


def test_validate_evidence_rejects_missing_coverage_map(tmp_path: Path) -> None:
    # evidence 文件缺 "## Coverage Map" 区块 → reject
    evidence = tmp_path / "audit.md"
    evidence.write_text("# Audit\n\n## Documentation health\n\n- README: OK\n", encoding="utf-8")
    ok, reason = gate.validate_evidence(evidence)
    assert ok is False
    assert "Coverage Map" in reason


def test_validate_evidence_rejects_missing_health_section(tmp_path: Path) -> None:
    evidence = tmp_path / "audit.md"
    evidence.write_text("# Audit\n\n## Coverage Map\n\n| x | y |\n|---|---|\n| a | b |\n", encoding="utf-8")
    ok, reason = gate.validate_evidence(evidence)
    assert ok is False
    assert "Documentation health" in reason


def test_validate_evidence_rejects_empty_coverage_map(tmp_path: Path) -> None:
    # 区块标题存在但下方没有非空行 → reject
    evidence = tmp_path / "audit.md"
    evidence.write_text(
        "# Audit\n\n## Coverage Map\n\n\n## Documentation health\n\n- README: OK\n",
        encoding="utf-8",
    )
    ok, reason = gate.validate_evidence(evidence)
    assert ok is False
    assert "Coverage Map" in reason


def test_validate_evidence_passes_with_both_sections(tmp_path: Path) -> None:
    evidence = tmp_path / "audit.md"
    evidence.write_text(
        "# Audit\n\n## Coverage Map\n\n| x | y |\n|---|---|\n| a | b |\n\n## Documentation health\n\n- README: Updated\n",
        encoding="utf-8",
    )
    ok, reason = gate.validate_evidence(evidence)
    assert ok is True
    assert reason == ""


def test_validate_evidence_rejects_missing_file(tmp_path: Path) -> None:
    ok, reason = gate.validate_evidence(tmp_path / "nope.md")
    assert ok is False
    assert "not found" in reason.lower() or "不存在" in reason
