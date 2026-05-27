# -*- coding: utf-8 -*-
"""LLM 依赖版本登记 — 实施期实际装版本快照。

Phase 12 LLM Internal Reopen T01:在 task 启动前显式探测 litellm /
instructor / pydantic / httpx 是否装载,缺包给清晰错误提示。

退出码约定:
- 0:所有必需包均已装
- 1:存在未装包(打印 "未装" 标记)
"""

import sys

# 必需包及其最低版本约束(版本约束字符串用于打印提示,实际安装由 pip 保证)
REQUIRED = {
    "litellm": ">=1.0",
    "instructor": ">=0.5",
    "pydantic": ">=2.0",
    "httpx": ">=0.25",
}


def check_versions() -> dict[str, str | None]:
    """返回 {pkg: installed_version | None}。

    None 表示该包未装(importlib.metadata 找不到该 distribution)。
    """
    import importlib.metadata as md
    result: dict[str, str | None] = {}
    for pkg in REQUIRED:
        try:
            result[pkg] = md.version(pkg)
        except md.PackageNotFoundError:
            result[pkg] = None
    return result


if __name__ == "__main__":
    versions = check_versions()
    print("LLM 依赖装版本探测:")
    for pkg, ver in versions.items():
        print(f"  {pkg}: {ver or '未装'} ({REQUIRED[pkg]})")
    missing = [p for p, v in versions.items() if v is None]
    sys.exit(1 if missing else 0)
