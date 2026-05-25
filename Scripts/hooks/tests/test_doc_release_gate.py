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


# ---- read_marker_file 异常包装测试 ----

def test_read_marker_raises_value_error_on_corrupt_json(tmp_path: Path) -> None:
    # marker 文件损坏时,read_marker_file 应抛出含路径信息的 ValueError
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    (marker_dir / "feat--x.json").write_text("not json at all", encoding="utf-8")
    with pytest.raises(ValueError, match="marker 文件损坏"):
        gate.read_marker_file(marker_dir, "feat/x")


# ---- check_marker 主流程测试 ----

import datetime as _dt


def _make_marker(tmp: Path, **overrides) -> gate.Marker:
    # 构造一个合法的 Marker,支持 overrides 覆盖任意字段
    defaults = dict(
        branch="feat/x",
        head_sha="abc123",
        staged_files_hash=gate.compute_staged_files_hash(["foo.py"]),
        audit_evidence_path=str(tmp / "audit.md"),
        timestamp=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return gate.Marker(**defaults)


def _write_valid_audit(path: Path) -> None:
    # 写入包含必填两个区块的合法 audit 文件
    path.write_text(
        "# Audit\n\n## Coverage Map\n\n| x | y |\n|---|---|\n| a | b |\n\n## Documentation health\n\n- README: Updated\n",
        encoding="utf-8",
    )


def test_check_blocks_when_marker_missing(tmp_path: Path) -> None:
    # marker 文件不存在时,check_marker 返回 passed=False
    marker_dir = tmp_path / "markers"
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False
    assert "marker not found" in result.reason.lower()


def test_check_blocks_when_head_and_hash_both_changed(tmp_path: Path) -> None:
    # HEAD 与 staged 文件集均变化时,check_marker 返回 passed=False
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    gate.write_marker_file(marker_dir, _make_marker(tmp_path, audit_evidence_path=str(audit)))
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="DIFFERENT",
        staged_paths=["bar.py"],  # 不同的 hash
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False


def test_check_passes_when_head_matches(tmp_path: Path) -> None:
    # HEAD 与 staged 均匹配,marker 未过期,evidence 存在时放行
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    gate.write_marker_file(marker_dir, _make_marker(tmp_path, audit_evidence_path=str(audit)))
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is True


def test_check_blocks_when_marker_older_than_24h(tmp_path: Path) -> None:
    # marker 时间戳超过 24h 时,check_marker 返回 passed=False
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    old_ts = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=25)).isoformat()
    gate.write_marker_file(
        marker_dir,
        _make_marker(tmp_path, audit_evidence_path=str(audit), timestamp=old_ts),
    )
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False
    assert "24h" in result.reason or "过期" in result.reason


def test_check_blocks_when_evidence_file_missing(tmp_path: Path) -> None:
    # evidence 文件不存在时,check_marker 返回 passed=False
    marker_dir = tmp_path / "markers"
    gate.write_marker_file(
        marker_dir,
        _make_marker(tmp_path, audit_evidence_path=str(tmp_path / "ghost.md")),
    )
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False
