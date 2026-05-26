"""Claude Code hook notify wrapper

从 stdin 读取 Claude Code hook JSON，提取 tool_input.file_path，
然后调用 doc_release_gate.py notify --path <path>。

此脚本被 .claude/settings.json 的 PreToolUse hook 调用，
当 Write/Edit 工具操作受控路径时触发软提示（永不阻塞，exit 0）。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

# 项目根目录（本文件位于 Scripts/hooks/，向上两层）
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATE_SCRIPT = PROJECT_ROOT / "Scripts" / "hooks" / "doc_release_gate.py"


def main() -> int:
    # 从 stdin 读取 Claude Code 传入的 hook JSON
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        # JSON 解析失败：静默放行，不阻塞
        return 0

    # 提取文件路径：Claude Code PreToolUse hook 的 tool_input 字段
    tool_input = data.get("tool_input", {})
    file_path = (
        tool_input.get("file_path")        # Write / Edit 工具
        or tool_input.get("path")          # 备用字段名
        or "（未知路径）"
    )

    # 调用 gate.py notify（软提示，永不阻塞）
    try:
        subprocess.run(
            [sys.executable, str(GATE_SCRIPT), "notify", "--path", file_path],
            check=False,  # notify 本身 exit 0，但不强制
        )
    except OSError:
        # 脚本不可达时静默放行
        pass

    return 0  # 永不阻塞


if __name__ == "__main__":
    sys.exit(main())
