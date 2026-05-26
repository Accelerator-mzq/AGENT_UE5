"""install_git_hooks.py 测试"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INSTALLER = PROJECT_ROOT / "Scripts" / "hooks" / "install_git_hooks.py"


def _make_fake_repo(tmp: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    # 复制 hook 启动器到 tmp 仓库的 Scripts/hooks/
    src = PROJECT_ROOT / "Scripts" / "hooks"
    dst = tmp / "Scripts" / "hooks"
    dst.mkdir(parents=True)
    for name in ("pre-commit", "pre-push", "commit-msg"):
        (dst / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp


def test_install_creates_hook_files(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    result = subprocess.run(
        [sys.executable, str(INSTALLER)],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for name in ("pre-commit", "pre-push", "commit-msg"):
        installed = repo / ".git" / "hooks" / name
        assert installed.exists(), f"{name} 未安装"


def test_install_is_idempotent(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(INSTALLER)],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


def test_install_makes_hooks_executable_on_posix(tmp_path: Path) -> None:
    if os.name == "nt":
        # Windows 不需 chmod;此用例只在 POSIX 跑
        return
    repo = _make_fake_repo(tmp_path)
    subprocess.run([sys.executable, str(INSTALLER)], cwd=str(repo), check=True)
    installed = repo / ".git" / "hooks" / "pre-commit"
    mode = installed.stat().st_mode
    assert mode & stat.S_IXUSR
