# -*- coding: utf-8 -*-
"""demo 冒烟 runner:UE Automation commandlet 驱动 + 环境故障与 demo 失败分离归因。

用法(runbook):
  python Plugins/AgentBridge/Scripts/demo_smoke/runner.py \
      --filter "<PluginName>.Smoke" --out ProjectState/Evidence/<name>_smoke_report.json \
      [--v0-filter "<PluginName>.Smoke.V0"] [--editor-cmd <UnrealEditor-Cmd.exe>]

环境约定:editor-cmd 缺省读环境变量 AGENTBRIDGE_UE_CMD;uproject 取项目根唯一 .uproject。
报告契约(evidence_validator 消费):{"status": "pass|fail", "v0_regression": "pass|fail|n/a",
"counts": {...}, "suites": [...], "screenshots": [...], "log_path": ...}
退出码契约:0=pass / 1=demo 失败(计自修轮) / 3=环境故障(不计自修轮,spec §5.1 归因分离)。
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# runner.py → demo_smoke → Scripts → AgentBridge → Plugins → 项目根(共 4 级 parents)
PROJECT_ROOT = Path(__file__).resolve().parents[4]


class EnvironmentFault(RuntimeError):
    """环境故障(编辑器缺失/报告未产出):不计入 demo 失败与自修轮次。"""


def precheck(editor_cmd, uproject) -> dict:
    """前置自检:editor 与 uproject 均需存在,否则归类为环境故障直接拒绝开跑。"""
    missing = [str(p) for p in (editor_cmd, uproject) if not Path(p).exists()]
    if missing:
        return {"ok": False, "kind": "environment", "missing": missing}
    return {"ok": True, "kind": "ready", "missing": []}


def run_automation(editor_cmd, uproject, test_filter: str, report_dir, log_path) -> None:
    """启动 UE Automation commandlet(同步阻塞);真机参数微调记 runbook,不改报告契约。"""
    cmd = [str(editor_cmd), str(uproject),
           f"-ExecCmds=Automation RunTests {test_filter}; Quit",
           "-unattended", "-nopause", "-nosplash",
           f"-ReportExportPath={report_dir}", f"-abslog={log_path}"]
    # check=False:UE 进程非零退出不抛异常,由 build_smoke_report 解析报告判定通过/失败
    subprocess.run(cmd, check=False, timeout=1800)


def build_smoke_report(report_dir, v0_regression: str, screenshots: list,
                       log_path: str = "") -> dict:
    """解析 UE -ReportExportPath 产出的 index.json,转成 evidence_validator 消费的报告契约。

    Args:
        report_dir: UE 写入 index.json 的目录路径。
        v0_regression: "pass" / "fail" / "n/a"(无 v0 回归段时传 n/a)。
        screenshots: 截图文件路径列表。
        log_path: 对应的 abslog 路径(可选,供溯查)。

    Raises:
        EnvironmentFault: index.json 不存在时抛出,归因为环境故障而非 demo 失败。
    """
    index = Path(report_dir) / "index.json"
    if not index.exists():
        raise EnvironmentFault(f"UE 报告未产出(index.json 缺失): {report_dir}")
    data = json.loads(index.read_text(encoding="utf-8-sig"))
    # notRun 同样视为失败:未执行的用例意味着管道未走完
    failed = int(data.get("failed", 0)) + int(data.get("notRun", 0))
    return {
        "status": "pass" if failed == 0 else "fail",
        "v0_regression": v0_regression,
        "counts": {k: data.get(k, 0) for k in ("succeeded", "succeededWithWarnings", "failed", "notRun")},
        "suites": [{"name": t.get("fullTestPath", ""), "state": t.get("state", "")}
                   for t in data.get("tests", [])],
        "screenshots": list(screenshots),
        "log_path": log_path,
    }


def main() -> int:
    """CLI 入口:返回退出码 0/1/3。"""
    parser = argparse.ArgumentParser(description="Phase 14 demo 冒烟 runner")
    parser.add_argument("--filter", required=True, help="Automation 测试过滤器")
    parser.add_argument("--v0-filter", default=None, help="v0 回归段过滤器(可选)")
    parser.add_argument("--out", required=True, help="输出报告 JSON 路径")
    parser.add_argument("--editor-cmd", default=os.environ.get("AGENTBRIDGE_UE_CMD", ""),
                        help="UnrealEditor-Cmd.exe 路径,缺省读 AGENTBRIDGE_UE_CMD")
    parser.add_argument("--screenshots", nargs="*", default=[], help="附加截图路径列表")
    args = parser.parse_args()

    # 环境自检:uproject 与 editor-cmd 必须存在
    uprojects = sorted(PROJECT_ROOT.glob("*.uproject"))
    if not uprojects or not args.editor_cmd:
        print("[ENV] 环境自检失败: 缺 uproject 或 editor-cmd(AGENTBRIDGE_UE_CMD)", file=sys.stderr)
        return 3
    check = precheck(Path(args.editor_cmd), uprojects[0])
    if not check["ok"]:
        print(f"[ENV] 环境自检失败: {check['missing']}", file=sys.stderr)
        return 3

    out_path = Path(args.out)
    work = out_path.parent / (out_path.stem + "_work")
    work.mkdir(parents=True, exist_ok=True)

    try:
        # v0 回归段(可选):先单独跑一轮,记录 v0_state
        v0_state = "n/a"
        if args.v0_filter:
            v0_dir = work / "v0"
            run_automation(Path(args.editor_cmd), uprojects[0], args.v0_filter, v0_dir,
                           work / "v0.log")
            v0_state = "pass" if build_smoke_report(v0_dir, "n/a", [])["status"] == "pass" else "fail"

        # 主冒烟段
        main_dir = work / "main"
        run_automation(Path(args.editor_cmd), uprojects[0], args.filter, main_dir,
                       work / "main.log")
        report = build_smoke_report(main_dir, v0_state, args.screenshots,
                                    log_path=str(work / "main.log"))
    except EnvironmentFault as exc:
        # 环境故障:退出码 3,不计入 demo 失败与自修轮次
        print(f"[ENV] {exc}", file=sys.stderr)
        return 3

    # 写报告 JSON
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{'OK' if report['status'] == 'pass' else 'FAIL'}] 冒烟报告 → {out_path}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    sys.exit(main())
