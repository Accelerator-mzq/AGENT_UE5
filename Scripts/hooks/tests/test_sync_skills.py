"""sync_skills.py 测试"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "Scripts" / "sync_skills.py"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_sync_creates_copy(tmp_path: Path) -> None:
    # tmp_path 模拟仓库,放一份 canonical,跑 sync,确认副本生成且 SHA 一致
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# canonical\n", encoding="utf-8")

    result = _run(["sync"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    mirror = tmp_path / ".agents" / "skills" / "document-release" / "SKILL.md"
    assert mirror.exists()
    assert mirror.read_text(encoding="utf-8") == canonical.read_text(encoding="utf-8")


def test_check_passes_when_consistent(tmp_path: Path) -> None:
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    mirror = tmp_path / ".agents" / "skills" / "document-release" / "SKILL.md"
    for p in (canonical, mirror):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# same\n", encoding="utf-8")

    result = _run(["--check"], cwd=tmp_path)
    assert result.returncode == 0


def test_check_fails_when_drift(tmp_path: Path) -> None:
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    mirror = tmp_path / ".agents" / "skills" / "document-release" / "SKILL.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    mirror.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("# A\n", encoding="utf-8")
    mirror.write_text("# B\n", encoding="utf-8")

    result = _run(["--check"], cwd=tmp_path)
    assert result.returncode != 0
    assert "drift" in result.stderr.lower() or "不一致" in result.stderr


def test_check_warns_when_mirror_missing(tmp_path: Path) -> None:
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("# A\n", encoding="utf-8")
    result = _run(["--check"], cwd=tmp_path)
    # 副本不存在不阻塞(只 warn),退出码 0
    assert result.returncode == 0
    assert "missing" in result.stderr.lower() or "不存在" in result.stderr
