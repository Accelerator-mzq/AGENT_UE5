"""skill 同步脚本: canonical(.claude/skills/) → 副本(.agents/skills/)

使用:
  python Scripts/sync_skills.py sync     生成/更新副本
  python Scripts/sync_skills.py --check  校验一致性,不一致 exit 2,缺副本只 warn
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

# 当前管理的 skill 名清单(后续新增 skill 在这里加)
SKILLS = ["document-release"]


def _sha256(path: Path) -> str:
    """计算文件 SHA-256 哈希值"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paths(root: Path, name: str) -> tuple[Path, Path]:
    """返回 (canonical 路径, mirror 路径) 元组"""
    canonical = root / ".claude" / "skills" / name / "SKILL.md"
    mirror = root / ".agents" / "skills" / name / "SKILL.md"
    return canonical, mirror


def cmd_sync(root: Path) -> int:
    """执行同步: 将 canonical 复制到 mirror"""
    for name in SKILLS:
        canonical, mirror = _paths(root, name)
        if not canonical.exists():
            print(f"[sync_skills] 跳过 {name}: canonical 不存在 {canonical}", file=sys.stderr)
            continue
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(canonical, mirror)
        print(f"[sync_skills] {name}: synced -> {mirror}", file=sys.stderr)
    return 0


def cmd_check(root: Path) -> int:
    """校验一致性: canonical 不存在返回 2，mirror 不存在只 warn，内容不一致返回 2"""
    exit_code = 0
    for name in SKILLS:
        canonical, mirror = _paths(root, name)
        if not canonical.exists():
            print(f"[sync_skills] canonical 不存在: {canonical}", file=sys.stderr)
            exit_code = 2
            continue
        if not mirror.exists():
            # 副本不存在只 warn,不阻塞(spec §4.3 step 3 fallback)
            print(f"[sync_skills] WARN: 副本不存在 {mirror},Codex 用户将无法加载该 skill", file=sys.stderr)
            continue
        if _sha256(canonical) != _sha256(mirror):
            print(f"[sync_skills] drift: {canonical} != {mirror},请跑 sync_skills.py sync", file=sys.stderr)
            exit_code = 2
    return exit_code


def main(argv: list[str] | None = None) -> int:
    """解析命令行参数并分发到对应命令"""
    p = argparse.ArgumentParser(prog="sync_skills")
    p.add_argument("cmd", nargs="?", default="sync", choices=["sync"])
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    root = Path.cwd()
    if args.check:
        return cmd_check(root)
    return cmd_sync(root)


if __name__ == "__main__":
    sys.exit(main())
