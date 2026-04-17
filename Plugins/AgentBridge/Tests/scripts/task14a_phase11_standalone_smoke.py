"""TASK 14A: 标准 cooked/staged standalone smoke 自动化脚本。"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


PROJECT_ROOT = Path(__file__).resolve().parents[4]
REPORT_DATE = datetime.now().strftime("%Y-%m-%d")
REPORT_ROOT = PROJECT_ROOT / "ProjectState" / "Reports" / REPORT_DATE
STAGED_ROOT = PROJECT_ROOT / "ProjectState" / "StagedBuilds" / "task14a_standalone_runtime_smoke"
UAT_LOG = REPORT_ROOT / "task14a_standalone_uat.log"
SMOKE_LOG = REPORT_ROOT / "task14a_standalone_smoke.log"
REPORT_PATH = REPORT_ROOT / "task14a_standalone_runtime_smoke_validation.md"
VALIDATION_SCRIPT = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Tests" / "scripts" / "task14a_phase11_ue_runtime_validation.py"
PLAYABILITY_REPORT = REPORT_ROOT / "task14a_ue_runtime_playability_validation.md"
BASELINE_REPORT = REPORT_ROOT / "task14a_baseline_domain_runtime_validation.md"
SMOKE_SUMMARY_REPORT = REPORT_ROOT / "task14a_ue_smoke_test_log.md"
UAT_PATH = Path(r"E:\Epic Games\UE_5.5\Engine\Build\BatchFiles\RunUAT.bat")
UPROJECT_PATH = PROJECT_ROOT / "Mvpv4TestCodex.uproject"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def abs_link(path: Path, line: Optional[int] = None) -> str:
    suffix = f"#L{line}" if line is not None else ""
    return f"/{path.as_posix()}{suffix}"


def md_link(label: str, path: Path, line: Optional[int] = None) -> str:
    return f"[{label}]({abs_link(path, line)})"


def find_line(path: Path, needle: str) -> Optional[int]:
    for index, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        if needle in line:
            return index
    return None


def run_command(command: List[str], log_path: Path, cwd: Path, timeout: Optional[int] = None) -> int:
    """把标准输出和错误都写入本地日志，便于后续留证。"""
    ensure_dir(log_path.parent)
    with log_path.open("w", encoding="utf-8", errors="replace") as log_file:
        log_file.write(f"$ {' '.join(command)}\n\n")
        log_file.flush()
        process = subprocess.Popen(
            command,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        try:
            assert process.stdout is not None
            for line in process.stdout:
                log_file.write(line)
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            log_file.write("\n[TIMEOUT] command exceeded timeout and was killed.\n")
            return 124


def find_staged_executable(staged_root: Path) -> Path:
    candidates = sorted(
        [
            path
            for path in staged_root.rglob("*.exe")
            if path.name.lower().startswith("mvpv4testcodex") and "crashreport" not in path.name.lower()
        ]
    )
    if not candidates:
        raise FileNotFoundError(f"未找到 staged 可执行程序: {staged_root}")
    return candidates[0]


def run_standalone_smoke(exe_path: Path, log_path: Path) -> int:
    # staged standalone 路径在当前环境下使用 -nullrhi 会导致退出码异常，这里保留真实窗口化运行。
    command = [
        str(exe_path),
        "-Phase11RuntimeSmoke",
        "-unattended",
        "-nosplash",
        "-nosound",
        "-windowed",
        "-ResX=1280",
        "-ResY=720",
        "-log",
        f"-ABSLOG={log_path}",
    ]
    completed = subprocess.run(command, cwd=str(exe_path.parent), timeout=300)
    return completed.returncode


def run_validation(log_path: Path) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(VALIDATION_SCRIPT), "--log-path", str(log_path)]
    return subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )


def build_report(
    uat_exit_code: int,
    smoke_exit_code: int,
    staged_exe: Path,
    validation_output: str,
) -> str:
    uat_log_link = md_link(UAT_LOG.name, UAT_LOG)
    smoke_log_link = md_link(SMOKE_LOG.name, SMOKE_LOG)
    staged_exe_link = md_link(staged_exe.name, staged_exe)
    playability_link = md_link(PLAYABILITY_REPORT.name, PLAYABILITY_REPORT)
    baseline_link = md_link(BASELINE_REPORT.name, BASELINE_REPORT)
    smoke_summary_link = md_link(SMOKE_SUMMARY_REPORT.name, SMOKE_SUMMARY_REPORT)

    playability_line = find_line(PLAYABILITY_REPORT, "当前结论")
    baseline_line = find_line(BASELINE_REPORT, "当前结论")
    smoke_complete_line = find_line(SMOKE_LOG, "[Phase11Smoke] Runtime smoke completed.")

    passed = (
        uat_exit_code == 0
        and smoke_exit_code == 0
        and "playability_passed=True" in validation_output
        and "baseline_passed=True" in validation_output
    )

    lines = [
        "# TASK 14A Standalone Runtime Smoke Validation",
        "",
        "## Summary",
        "",
        f"- 验证链路：`BuildCookRun -> staged standalone exe -> runtime smoke -> TASK 14A validation`",
        f"- UAT 结果：`{uat_exit_code}` {uat_log_link}",
        f"- Standalone smoke 结果：`{smoke_exit_code}` {smoke_log_link}",
        f"- Staged 可执行程序：{staged_exe_link}",
        f"- 结论：`{'pass' if passed else 'blocked'}`",
        "",
        "## Validation Output",
        "",
        "```text",
        validation_output.strip(),
        "```",
        "",
        "## Evidence",
        "",
        f"- 可玩性报告：{md_link(PLAYABILITY_REPORT.name, PLAYABILITY_REPORT, playability_line)}",
        f"- Baseline 报告：{md_link(BASELINE_REPORT.name, BASELINE_REPORT, baseline_line)}",
        f"- Smoke 摘要：{smoke_summary_link}",
        f"- Standalone 完成锚点：{md_link('Runtime smoke completed', SMOKE_LOG, smoke_complete_line)}",
        "",
        "## Conclusion",
        "",
    ]

    if passed:
        lines.extend(
            [
                "- 标准 cooked/staged standalone 路径已跑通，不再依赖 raw DebugGame + .uproject 的非标准运行方式。",
                "- TASK 14A 的运行时证据现在同时具备 Editor game 路径与 staged standalone 路径。",
            ]
        )
    else:
        lines.extend(
            [
                "- standalone 链路仍未完全通过，需要继续检查 BuildCookRun 或 staged exe 日志。",
            ]
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="TASK 14A standalone runtime smoke 自动化")
    parser.add_argument("--skip-build", action="store_true", help="复用已有 staged 输出，跳过 BuildCookRun")
    args = parser.parse_args()

    ensure_dir(REPORT_ROOT)
    if not args.skip_build and STAGED_ROOT.exists():
        shutil.rmtree(STAGED_ROOT)

    uat_exit_code = 0
    if not args.skip_build:
        command = [
            str(UAT_PATH),
            "BuildCookRun",
            f"-project={UPROJECT_PATH}",
            "-platform=Win64",
            "-clientconfig=Development",
            "-target=Mvpv4TestCodex",
            "-build",
            "-cook",
            "-stage",
            "-archive",
            f"-archivedirectory={STAGED_ROOT}",
            "-pak",
            "-iostore",
            "-map=/Game/Maps/L_MonopolyBoard",
            "-nop4",
            "-utf8output",
            "-unattended",
        ]
        uat_exit_code = run_command(command, UAT_LOG, PROJECT_ROOT, timeout=3600)
        if uat_exit_code != 0:
            REPORT_PATH.write_text(
                build_report(uat_exit_code, -1, STAGED_ROOT, "BuildCookRun failed before standalone smoke."),
                encoding="utf-8",
            )
            return uat_exit_code

    staged_exe = find_staged_executable(STAGED_ROOT)
    if SMOKE_LOG.exists():
        SMOKE_LOG.unlink()

    smoke_exit_code = run_standalone_smoke(staged_exe, SMOKE_LOG)
    validation_result = run_validation(SMOKE_LOG)
    validation_output = (validation_result.stdout or "") + ("\n" + validation_result.stderr if validation_result.stderr else "")

    REPORT_PATH.write_text(
        build_report(uat_exit_code, smoke_exit_code, staged_exe, validation_output),
        encoding="utf-8",
    )

    if validation_result.returncode != 0:
        return validation_result.returncode
    if smoke_exit_code != 0:
        return smoke_exit_code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
