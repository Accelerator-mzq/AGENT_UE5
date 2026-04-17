"""TASK 14A：基于 runtime smoke 日志重建 UE 运行时验收报告。"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


REPORT_DATE = datetime.now().strftime("%Y-%m-%d")
REPORT_ROOT = PROJECT_ROOT / "ProjectState" / "Reports" / REPORT_DATE
PLAYABILITY_REPORT = REPORT_ROOT / "task14a_ue_runtime_playability_validation.md"
BASELINE_REPORT = REPORT_ROOT / "task14a_baseline_domain_runtime_validation.md"
SMOKE_LOG_REPORT = REPORT_ROOT / "task14a_ue_smoke_test_log.md"
LOG_ROOT = PROJECT_ROOT / "Saved" / "Logs"
TASK_MD_PATH = PROJECT_ROOT / "task.md"


@dataclass
class Marker:
    key: str
    label: str
    needle: str
    required: bool = True


RUNTIME_MARKERS: List[Marker] = [
    Marker("begin_play", "BeginPlay", "[Phase8] MonopolyGameMode BeginPlay started."),
    Marker("runtime_initialized", "Runtime initialized", "[Phase8] Runtime initialized."),
    Marker("hud_created", "HUD created", "[Phase8] HUD widget created: MGameHUDWidget"),
    Marker("start_screen", "Start Screen", "[Phase11] Start Screen shown."),
    Marker("main_menu", "Main Menu", "[Phase11] Main Menu shown."),
    Marker("settings_main", "Settings(MainMenu)", "[Phase11] Settings screen shown. Context=MainMenu"),
    Marker("gameplay_started", "Gameplay session", "[Phase11] Gameplay session started."),
    Marker("smoke_roll", "Smoke Roll", "[Phase11Smoke] Roll simulated."),
    Marker("smoke_pawn_moved", "Smoke Pawn Moved", "[Phase11Smoke] Pawn moved."),
    Marker("popup_ack", "Smoke Popup Ack", "[Phase11Smoke] Popup acknowledged."),
    Marker("player2_turn", "StartTurn Player 2", "[Phase8] StartTurn -> PlayerIndex=1"),
    Marker("pause", "Pause", "[Phase11] Pause menu shown."),
    Marker("settings_pause", "Settings(Pause)", "[Phase11] Settings screen shown. Context=PauseMenu"),
    Marker("resumed", "Resume", "[Phase11] Gameplay resumed from pause."),
    Marker("results", "Results", "[Phase11] Results screen shown."),
    Marker("returned_menu", "ReturnToMenu", "[Phase11] Returned to frontend menu."),
    Marker("smoke_completed", "Smoke Completed", "[Phase11Smoke] Runtime smoke completed."),
]


def _ensure_dir(path: Path) -> Path:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_text(path: Path, content: str) -> Path:
    """写入 UTF-8 文本。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _read_lines(path: Path) -> List[str]:
    """读取文本文件全部行。"""
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def _abs_link(path: Path, line: Optional[int] = None) -> str:
    """生成本地绝对路径 Markdown 链接目标。"""
    suffix = f"#L{line}" if line is not None else ""
    return f"/{path.as_posix()}{suffix}"


def _md_link(label: str, path: Path, line: Optional[int] = None) -> str:
    """生成聊天面板可点击的本地 Markdown 链接。"""
    return f"[{label}]({_abs_link(path, line)})"


def _find_line(lines: Iterable[str], needle: str) -> Optional[int]:
    """返回首个包含关键字的行号。"""
    for index, line in enumerate(lines, start=1):
        if needle in line:
            return index
    return None


def _find_latest_runtime_log() -> Path:
    """查找最新运行时日志。"""
    candidates = sorted(LOG_ROOT.glob("Mvpv4TestCodex*.log"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not candidates:
        raise FileNotFoundError(f"未找到运行时日志目录：{LOG_ROOT}")
    return candidates[0]


def _collect_runtime_markers(log_path: Path) -> Dict[str, Dict[str, object]]:
    """从日志中提取 smoke 所需关键锚点。"""
    lines = _read_lines(log_path)
    results: Dict[str, Dict[str, object]] = {}
    for marker in RUNTIME_MARKERS:
        line = _find_line(lines, marker.needle)
        results[marker.key] = {
            "label": marker.label,
            "needle": marker.needle,
            "line": line,
            "found": line is not None,
        }
    return results


def _domain_result(markers: Dict[str, Dict[str, object]]) -> Dict[str, Dict[str, object]]:
    """按 TASK 14A 口径整理六个 Baseline Domain。"""
    return {
        "Start Screen": {
            "passed": markers["start_screen"]["found"],
            "reason": "运行时日志记录了 Start Screen 展示。",
            "evidence": [("Start Screen", markers["start_screen"])],
        },
        "Main Menu": {
            "passed": markers["main_menu"]["found"],
            "reason": "运行时日志记录了 Main Menu 展示。",
            "evidence": [("Main Menu", markers["main_menu"])],
        },
        "Settings": {
            "passed": markers["settings_main"]["found"] and markers["settings_pause"]["found"],
            "reason": "运行时日志同时记录了 MainMenu 上下文和 Pause 上下文的 Settings 展示。",
            "evidence": [("Settings(MainMenu)", markers["settings_main"]), ("Settings(Pause)", markers["settings_pause"])],
        },
        "Pause": {
            "passed": markers["pause"]["found"] and markers["resumed"]["found"],
            "reason": "运行时日志记录了 Pause 展示与 Resume 恢复。",
            "evidence": [("Pause", markers["pause"]), ("Resume", markers["resumed"])],
        },
        "Results": {
            "passed": markers["results"]["found"] and markers["returned_menu"]["found"],
            "reason": "运行时日志记录了 Results 展示并返回主菜单。",
            "evidence": [("Results", markers["results"]), ("ReturnToMenu", markers["returned_menu"])],
        },
        "HUD": {
            "passed": markers["hud_created"]["found"] and markers["gameplay_started"]["found"],
            "reason": "运行时日志记录了 HUD 构建，并且 gameplay session 已启动。",
            "evidence": [("HUD", markers["hud_created"]), ("Gameplay", markers["gameplay_started"])],
        },
    }


def _playability_passed(markers: Dict[str, Dict[str, object]]) -> bool:
    """判断最小玩法闭环是否被 smoke 日志覆盖。"""
    required_keys = [
        "gameplay_started",
        "smoke_roll",
        "smoke_pawn_moved",
        "popup_ack",
        "player2_turn",
    ]
    return all(bool(markers[key]["found"]) for key in required_keys)


def _marker_link(log_path: Path, marker_info: Dict[str, object]) -> str:
    """将 marker 结果转成可点击链接。"""
    line = marker_info["line"]
    if line is None:
        return "`missing`"
    return _md_link(str(marker_info["label"]), log_path, int(line))


def _build_playability_report(log_path: Path, markers: Dict[str, Dict[str, object]]) -> str:
    """生成最小可玩性报告。"""
    passed = _playability_passed(markers)
    lines = [
        "# TASK 14A UE Runtime Playability Validation",
        "",
        "## Summary",
        "",
        f"- 运行入口：`runtime smoke`",
        f"- 日志文件：{_md_link(log_path.name, log_path)}",
        f"- 结论：`{'pass' if passed else 'blocked'}`",
        "",
        "## Gameplay Chain",
        "",
        f"- BeginPlay：{_marker_link(log_path, markers['begin_play'])}",
        f"- Gameplay started：{_marker_link(log_path, markers['gameplay_started'])}",
        f"- Simulated roll：{_marker_link(log_path, markers['smoke_roll'])}",
        f"- Pawn moved：{_marker_link(log_path, markers['smoke_pawn_moved'])}",
        f"- Popup acknowledged：{_marker_link(log_path, markers['popup_ack'])}",
        f"- Next player reached：{_marker_link(log_path, markers['player2_turn'])}",
        "",
        "## Assessment",
        "",
    ]

    if passed:
        lines.extend(
            [
                "- 已在真实 UE 运行时日志中看到“开始游戏 -> 掷骰 -> 移动 -> 弹窗确认/决策 -> 切换玩家”的闭环。",
                "- 该闭环由 runtime smoke 自动驱动，但所有锚点都来自真实运行时日志，而不是静态推断。",
            ]
        )
    else:
        lines.extend(
            [
                "- 仍缺失最小玩法闭环所需的一个或多个日志锚点。",
                "- 当前不能宣称 TASK 14A 已通过。",
            ]
        )

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- 当前结论：`{'pass' if passed else 'blocked'}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_baseline_report(log_path: Path, markers: Dict[str, Dict[str, object]]) -> str:
    """生成 Baseline Domain 运行时报告。"""
    domains = _domain_result(markers)
    passed = all(item["passed"] for item in domains.values())

    lines = [
        "# TASK 14A Baseline Domain Runtime Validation",
        "",
        "## Summary",
        "",
        f"- 运行入口：`runtime smoke`",
        f"- 日志文件：{_md_link(log_path.name, log_path)}",
        f"- 结论：`{'pass' if passed else 'blocked'}`",
        "",
        "## Domain Checks",
        "",
    ]

    for domain_name, info in domains.items():
        evidence = " / ".join(_marker_link(log_path, marker_info) for _, marker_info in info["evidence"])
        lines.extend(
            [
                f"### {domain_name}",
                "",
                f"- 状态：`{'pass' if info['passed'] else 'blocked'}`",
                f"- 结论：{info['reason']}",
                f"- 证据：{evidence}",
                "",
            ]
        )

    lines.extend(
        [
            "## Conclusion",
            "",
            f"- 当前结论：`{'pass' if passed else 'blocked'}`",
            "",
        ]
    )
    return "\n".join(lines)


def _build_smoke_log_report(log_path: Path, markers: Dict[str, Dict[str, object]]) -> str:
    """生成 smoke 日志摘要。"""
    lines = [
        "# TASK 14A UE Smoke Test Log",
        "",
        "## Runtime Context",
        "",
        f"- 生成时间：`{datetime.now().isoformat(timespec='seconds')}`",
        f"- 日志文件：{_md_link(log_path.name, log_path)}",
        f"- task.md：{_md_link('task.md', TASK_MD_PATH, 978)}",
        "",
        "## Marker Summary",
        "",
    ]

    for marker in RUNTIME_MARKERS:
        marker_info = markers[marker.key]
        status = "found" if marker_info["found"] else "missing"
        evidence = _marker_link(log_path, marker_info)
        lines.append(f"- {marker.label}: `{status}` {evidence}")

    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            f"- Smoke 完成：`{str(markers['smoke_completed']['found']).lower()}`",
            f"- 最小玩法闭环：`{str(_playability_passed(markers)).lower()}`",
            f"- Baseline 六域全部通过：`{str(all(item['passed'] for item in _domain_result(markers).values())).lower()}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """脚本入口。"""
    parser = argparse.ArgumentParser(description="TASK 14A runtime smoke 日志报告生成器")
    parser.add_argument("--log-path", type=Path, default=None, help="指定要解析的运行时日志")
    args = parser.parse_args()

    _ensure_dir(REPORT_ROOT)
    log_path = args.log_path.resolve() if args.log_path is not None else _find_latest_runtime_log()
    markers = _collect_runtime_markers(log_path)

    _write_text(PLAYABILITY_REPORT, _build_playability_report(log_path, markers))
    _write_text(BASELINE_REPORT, _build_baseline_report(log_path, markers))
    _write_text(SMOKE_LOG_REPORT, _build_smoke_log_report(log_path, markers))

    print(f"[task14a] playability_report={PLAYABILITY_REPORT}")
    print(f"[task14a] baseline_report={BASELINE_REPORT}")
    print(f"[task14a] smoke_report={SMOKE_LOG_REPORT}")
    print(f"[task14a] playability_passed={_playability_passed(markers)}")
    print(f"[task14a] baseline_passed={all(item['passed'] for item in _domain_result(markers).values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
