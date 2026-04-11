"""
MCP 后端证据裁决工具适配层。

职责：
  - 读取标准化测试证据目录
  - 基于 manifest 做轻量 pass/fail/escalate 初判
  - 输出结构化验收摘要
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_DIR / "Scripts"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from evidence import evidence_manager
from evidence.run_id import validate_run_id


def _make_response(
    status: str,
    summary: str,
    data: dict | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict:
    """构造与 Bridge 工具一致的统一返回格式。"""
    return {
        "status": status,
        "summary": summary,
        "data": data or {},
        "warnings": warnings or [],
        "errors": errors or [],
    }


def _get_evidence_root() -> Path:
    """兼容 evidence_manager 中可能被临时改写的根目录变量。"""
    return Path(evidence_manager.EVIDENCE_ROOT)


def _get_run_dir(run_id: str) -> Path:
    """返回 run_id 对应的证据目录。"""
    if not validate_run_id(run_id):
        raise ValueError(f"非法 run_id: {run_id}")
    return _get_evidence_root() / run_id


def _missing_path_response(path: Path, label: str) -> dict:
    """统一处理路径不存在。"""
    return _make_response(
        "failed",
        f"{label}不存在",
        errors=[f"FILE_NOT_FOUND: {path.as_posix()}"],
    )


def _list_files(run_dir: Path, subdir: str) -> list[Path]:
    """列出某个证据子目录下的全部文件。"""
    target_dir = run_dir / subdir
    if not target_dir.exists():
        return []
    return sorted(path for path in target_dir.iterdir() if path.is_file())


def _to_relative_paths(run_dir: Path, files: list[Path]) -> list[str]:
    """将绝对路径转换为相对 run_id 目录的路径。"""
    return [path.relative_to(run_dir).as_posix() for path in files]


def _read_text_file(path: Path) -> str:
    """以宽松方式读取文本内容，避免日志中的异常编码中断流程。"""
    return path.read_text(encoding="utf-8", errors="ignore")


def _derive_open_questions(manifest: dict[str, Any]) -> list[str]:
    """从 manifest 中提取当前仍未解决的问题。"""
    summary = manifest.get("summary", {})
    evidence_items = manifest.get("evidence_items", [])

    questions = []
    if not evidence_items:
        questions.append("当前 run_id 下没有登记任何证据项。")
    if summary.get("total_checks", 0) <= 0:
        questions.append("summary.total_checks 为 0，无法证明测试覆盖度。")
    if summary.get("warnings", 0) > 0:
        questions.append(f"存在 {summary.get('warnings', 0)} 条 warning，需要确认是否影响验收。")
    if manifest.get("status") == "pending":
        questions.append("manifest 仍处于 pending，尚未形成明确验收结论。")
    return questions


def _derive_judgment(manifest: dict[str, Any], criteria: dict[str, Any] | None = None) -> dict[str, Any]:
    """根据 manifest 与简单准则生成轻量判定结果。"""
    criteria = criteria or {}
    summary = manifest.get("summary", {})
    evidence_items = manifest.get("evidence_items", [])
    manifest_status = manifest.get("status", "pending")

    required_types = criteria.get("required_types", [])
    min_checks = criteria.get("min_checks", 0)

    if not isinstance(required_types, list):
        raise ValueError("criteria.required_types 必须是数组")
    if not isinstance(min_checks, int) or min_checks < 0:
        raise ValueError("criteria.min_checks 必须是大于等于 0 的整数")

    present_types = {item.get("type") for item in evidence_items}
    missing_types = sorted(item_type for item_type in required_types if item_type not in present_types)
    total_checks = summary.get("total_checks", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    warnings_count = summary.get("warnings", 0)

    open_questions = _derive_open_questions(manifest)
    if missing_types:
        open_questions.append("缺少必需证据类型: " + ", ".join(missing_types))
    if total_checks < min_checks:
        open_questions.append(
            f"检查数量不足：要求至少 {min_checks} 项，当前 {total_checks} 项。"
        )

    if failed > 0 or manifest_status == "fail":
        judgment = "fail"
        confidence = "high" if not missing_types and total_checks >= min_checks else "medium"
        reasoning = f"已记录失败检查 {failed} 项，当前证据支持直接判定为 fail。"
    elif not evidence_items or missing_types or total_checks < min_checks or warnings_count > 0 or manifest_status == "escalate":
        judgment = "escalate"
        confidence = "low" if not evidence_items else "medium"
        reasoning = "当前证据存在缺口或不确定项，建议升级人工确认。"
    elif manifest_status == "pass" or (total_checks > 0 and passed >= total_checks):
        judgment = "pass"
        confidence = "high"
        reasoning = "当前证据覆盖完整，且未发现失败项，可初步判定为 pass。"
    else:
        judgment = "escalate"
        confidence = "medium"
        reasoning = "当前证据没有明确失败，但也不足以自动通过，建议升级人工确认。"

    return {
        "judgment": judgment,
        "confidence": confidence,
        "reasoning": reasoning,
        "open_questions": open_questions,
        "required_types": required_types,
        "missing_types": missing_types,
        "min_checks": min_checks,
        "evidence_count": len(evidence_items),
        "summary": summary,
    }


def evidence_load_manifest(run_id: str) -> dict:
    """读取指定 run_id 的 evidence manifest。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        return _make_response(
            "success",
            "Evidence manifest 加载成功",
            data=manifest,
        )
    except FileNotFoundError as exc:
        message = str(exc).split(": ", 1)[-1]
        return _missing_path_response(Path(message), "manifest 文件")
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence manifest 加载失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_load_screenshots(run_id: str) -> dict:
    """列出 screenshots 目录下的全部文件。"""
    try:
        run_dir = _get_run_dir(run_id)
        if not run_dir.exists():
            return _missing_path_response(run_dir, "run_id 目录")

        files = _list_files(run_dir, "screenshots")
        return _make_response(
            "success",
            "Screenshots 读取成功",
            data={
                "run_id": run_id,
                "files": _to_relative_paths(run_dir, files),
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Screenshots 读取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_load_logs(run_id: str) -> dict:
    """读取 logs 目录下的全部日志文件内容。"""
    try:
        run_dir = _get_run_dir(run_id)
        if not run_dir.exists():
            return _missing_path_response(run_dir, "run_id 目录")

        logs = []
        for file_path in _list_files(run_dir, "logs"):
            logs.append(
                {
                    "file": file_path.relative_to(run_dir).as_posix(),
                    "content": _read_text_file(file_path),
                }
            )

        return _make_response(
            "success",
            "Logs 读取成功",
            data={
                "run_id": run_id,
                "logs": logs,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Logs 读取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_load_report(run_id: str) -> dict:
    """读取 reports 目录下的全部报告文件内容。"""
    try:
        run_dir = _get_run_dir(run_id)
        if not run_dir.exists():
            return _missing_path_response(run_dir, "run_id 目录")

        reports = []
        for file_path in _list_files(run_dir, "reports"):
            reports.append(
                {
                    "file": file_path.relative_to(run_dir).as_posix(),
                    "content": _read_text_file(file_path),
                }
            )

        return _make_response(
            "success",
            "Reports 读取成功",
            data={
                "run_id": run_id,
                "reports": reports,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Reports 读取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_judge_acceptance(run_id: str, criteria: dict[str, Any]) -> dict:
    """基于 manifest 覆盖度与摘要做轻量验收判定。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        judgment = _derive_judgment(manifest, criteria)
        return _make_response(
            "success",
            "Evidence acceptance 判定完成",
            data=judgment,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence acceptance 判定失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_decide_escalation(run_id: str) -> dict:
    """判断当前 run_id 是否需要升级人工确认。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        summary = manifest.get("summary", {})
        open_questions = _derive_open_questions(manifest)

        needs_human = False
        reasons = []
        if manifest.get("status") == "escalate":
            needs_human = True
            reasons.append("manifest 已显式标记为 escalate")
        if summary.get("warnings", 0) > 0:
            needs_human = True
            reasons.append(f"存在 {summary.get('warnings', 0)} 条 warning")
        if summary.get("total_checks", 0) <= 0:
            needs_human = True
            reasons.append("未记录有效检查数量")
        if summary.get("failed", 0) > 0 and summary.get("passed", 0) > 0:
            needs_human = True
            reasons.append("同时存在 passed 与 failed，需要人工确认边界")

        if needs_human:
            reason = "；".join(reasons)
            escalation_note = "建议人工复核以下问题：" + "；".join(open_questions or reasons)
        else:
            reason = "当前证据状态明确，无需升级人工确认"
            escalation_note = ""

        return _make_response(
            "success",
            "Evidence escalation 判定完成",
            data={
                "needs_human": needs_human,
                "reason": reason,
                "escalation_note": escalation_note,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence escalation 判定失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_export_summary(run_id: str) -> dict:
    """汇总 manifest 并导出结构化验收摘要。"""
    try:
        manifest = evidence_manager.load_manifest(run_id)
        judgment = _derive_judgment(manifest, {})
        return _make_response(
            "success",
            "Evidence summary 导出成功",
            data={
                "run_id": manifest.get("run_id"),
                "test_type": manifest.get("test_type"),
                "status": manifest.get("status"),
                "evidence_count": len(manifest.get("evidence_items", [])),
                "judgment": judgment.get("judgment"),
                "open_questions": judgment.get("open_questions", []),
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence summary 导出失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def evidence_list_runs(date_filter: str | None = None) -> dict:
    """列出当前证据根目录下的全部 run_id。"""
    try:
        runs = evidence_manager.list_runs(date_filter)
        return _make_response(
            "success",
            "Evidence runs 列出成功",
            data={"runs": runs},
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Evidence runs 列出失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )
