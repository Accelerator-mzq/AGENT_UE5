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


def test_check_handles_naive_timestamp_in_marker(tmp_path: Path) -> None:
    # marker 若由外部脚本写入 naive timestamp, check_marker 应当当 UTC 处理,而不是崩溃
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    naive_ts = _dt.datetime.now().isoformat()  # 故意 naive
    gate.write_marker_file(
        marker_dir,
        _make_marker(tmp_path, audit_evidence_path=str(audit), timestamp=naive_ts),
    )
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    # 不崩,且因为是 naive→UTC 假设,刚写入应当未过期
    assert result.passed is True


# ---- Step 4.1: 逃生通道测试 ----

def test_trivial_whitelist_only_saved_files_passes() -> None:
    # 全部在白名单内 → trivial
    assert gate.is_trivial(["Saved/foo.tmp", "Intermediate/bar.o"]) is True


def test_trivial_whitelist_mixed_with_source_is_not_trivial() -> None:
    assert gate.is_trivial(["Saved/foo.tmp", "src/main.py"]) is False


def test_trivial_whitelist_empty_paths_is_not_trivial() -> None:
    # 空 staged 不应自动放行(可能是 push 上下文)
    assert gate.is_trivial([]) is False


def test_skip_doc_marker_in_commit_message() -> None:
    assert gate.is_skip_doc_commit("[skip-doc] WIP refactor") is True
    assert gate.is_skip_doc_commit("feat: real change") is False
    assert gate.is_skip_doc_commit("docs: typo [skip-doc] inline") is False  # 必须在首行开头


def test_log_skipped_appends_line(tmp_path: Path) -> None:
    log = tmp_path / "skipped.log"
    gate.log_skipped(log, reason="commit msg [skip-doc]", branch="feat/x", head="abc")
    gate.log_skipped(log, reason="--no-verify", branch="feat/x", head="def")
    lines = log.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert "skip-doc" in lines[0]
    assert "no-verify" in lines[1]


# ---- Step 4.4: CLI 入口测试 ----

def test_cli_check_dry_run_blocks_when_no_marker(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    exit_code = gate.main([
        "check",
        "--action", "commit",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "src/foo.py",
        "--dry-run",
    ])
    assert exit_code != 0


def test_cli_check_dry_run_passes_with_trivial_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    exit_code = gate.main([
        "check",
        "--action", "commit",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "Saved/foo.tmp",
        "--dry-run",
    ])
    assert exit_code == 0


def test_cli_write_marker_rejects_invalid_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    bad = tmp_path / "bad.md"
    bad.write_text("# 只有标题\n", encoding="utf-8")
    exit_code = gate.main([
        "write-marker",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "src/foo.py",
        "--evidence", str(bad),
    ])
    assert exit_code != 0


def test_cli_write_marker_accepts_valid_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    good = tmp_path / "audit.md"
    _write_valid_audit(good)
    exit_code = gate.main([
        "write-marker",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "src/foo.py",
        "--evidence", str(good),
    ])
    assert exit_code == 0
    # marker 应已写入
    marker = gate.read_marker_file(tmp_path / "markers", "feat/x")
    assert marker is not None
    assert marker.head_sha == "abc"


def test_cli_notify_never_blocks_and_writes_stderr(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    exit_code = gate.main([
        "notify",
        "--path", "task.md",
    ])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "task.md" in captured.err
