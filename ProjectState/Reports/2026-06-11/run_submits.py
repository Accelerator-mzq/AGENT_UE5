# -*- coding: utf-8 -*-
"""Phase14 v0 顺序提交器:对剩余 capability story 逐个 fetch(推进游标)→submit。
每个 story 用 mcp_driver 经真实 MCP stdio 调用;打印每步状态。
docs story 不在此处(最后单独处理)。
"""
import json
import subprocess
import sys
from pathlib import Path

PY = r"C:\Python312\python.exe"
DRIVER = "ProjectState/Reports/2026-06-11/mcp_driver.py"
ARGS_DIR = Path("ProjectState/Reports/2026-06-11/submit_args")
SESSION = "ProjectState/runs/run-20260611-052252-5101"

# 计划顺序中,start-screen / main-menu 已提交;以下为剩余 capability(docs 除外)
REMAINING = [
    "story-skill-baseline-input-foundation",
    "story-skill-baseline-settings",
    "story-skill-baseline-audio-foundation",
    "story-skill-baseline-pause",
    "story-skill-baseline-platform-foundation",
    "story-skill-board-topology",
    "story-skill-dice",
    "story-skill-tile-system",
    "story-skill-turn-loop",
    "story-skill-economy",
    "story-skill-player-management",
    "story-skill-baseline-hud",
    "story-skill-baseline-results",
    "story-skill-jail",
]


def call(tool, arg):
    res = subprocess.run([PY, DRIVER, tool, arg], capture_output=True, text=True, encoding="utf-8")
    # 驱动器输出整块 pretty JSON;从第一个 '{' 到最后一个 '}' 截取整体解析
    out = res.stdout or ""
    start = out.find("{")
    end = out.rfind("}")
    if start < 0 or end < 0:
        raise RuntimeError(f"无 JSON 输出: stdout={res.stdout!r} stderr={res.stderr!r}")
    return json.loads(out[start:end + 1])


def main():
    for sid in REMAINING:
        fetched = call("demo_story_fetch", json.dumps({"session_path": SESSION}))
        got = fetched.get("data", {}).get("story", {}).get("story_id")
        if got != sid:
            print(f"[WARN] fetch 返回 {got},期望 {sid}(游标可能已过);继续按期望 submit")
        args_path = str(ARGS_DIR / f"{sid}.json")
        sub = call("demo_story_submit", args_path)
        data = sub.get("data", {})
        status = data.get("story_status")
        errors = data.get("errors") or sub.get("errors")
        print(f"{sid}: {status} | attempts={data.get('attempts')} | errors={errors}")
        if status != "verified":
            print(f"[STOP] {sid} 未通过,停止以便排查")
            return 1
    print("=== 14 个剩余 capability story 全部 verified ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
