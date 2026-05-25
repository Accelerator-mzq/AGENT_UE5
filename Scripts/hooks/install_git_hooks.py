"""把 pre-commit / pre-push / commit-msg 启动器复制到 .git/hooks/ 并设可执行位。

幂等。Windows 上 chmod 操作被忽略(git for windows 自动按文本判定可执行)。
"""
from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path

# 需要安装的 hook 名称列表
HOOK_NAMES = ("pre-commit", "pre-push", "commit-msg")


def main() -> int:
    # 以当前工作目录作为 repo 根目录
    repo_root = Path.cwd()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        print(f"[install_git_hooks] 当前目录不是 git 仓库: {repo_root}", file=sys.stderr)
        return 2
    # 源 hook 文件所在目录
    src_dir = repo_root / "Scripts" / "hooks"
    # 目标 .git/hooks/ 目录
    dst_dir = git_dir / "hooks"
    dst_dir.mkdir(parents=True, exist_ok=True)

    for name in HOOK_NAMES:
        src = src_dir / name
        dst = dst_dir / name
        if not src.exists():
            print(f"[install_git_hooks] 源 hook 不存在: {src}", file=sys.stderr)
            return 2
        # 复制文件（幂等：已存在则覆盖）
        shutil.copy2(src, dst)
        # POSIX 上设可执行位；Windows 上 git for windows 自动处理
        if os.name != "nt":
            mode = dst.stat().st_mode
            dst.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[install_git_hooks] installed: {dst}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
