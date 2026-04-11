"""
Compiler 前端 MCP 工具适配层。

职责：
  - 把 Compiler pipeline 的 session / prepare / save 能力适配成 MCP 工具返回格式
  - 只覆盖 Stage 1-2：会话创建、Intake prepare/save、Planner prepare/save、状态查询
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parents[1]
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from Compiler.pipeline.pipeline_orchestrator import prepare_stage, save_stage
from Compiler.pipeline.session import CompilerSession, create_session


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


def _load_session(session_path: str) -> CompilerSession:
    """读取 session.json。"""
    return CompilerSession.load(session_path)


def _missing_file_response(path: str, label: str) -> dict:
    """统一处理文件不存在。"""
    return _make_response(
        "failed",
        f"{label}不存在",
        errors=[f"FILE_NOT_FOUND: {path}"],
    )


def _wrap_prepare_result(action_name: str, result: dict) -> dict:
    """把 prepare_stage 的结果转换成 MCP 工具输出。"""
    if result.get("status") != "ready_for_agent":
        return _make_response(
            "failed",
            f"{action_name}失败",
            data={"stage": result.get("stage_num")},
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
        )

    return _make_response(
        "success",
        f"{action_name}成功",
        data={
            "stage": result.get("stage"),
            "stage_name": result.get("stage_name"),
            "template": result.get("template"),
            "schema": result.get("schema"),
            "input_context": result.get("input_context", {}),
        },
        warnings=result.get("warnings", []),
    )


def _wrap_save_result(action_name: str, result: dict) -> dict:
    """把 save_stage 的结果转换成 MCP 工具输出。"""
    if result.get("status") != "saved":
        return _make_response(
            "failed",
            f"{action_name}失败",
            data={"stage": result.get("stage_num")},
            errors=result.get("errors", []),
            warnings=result.get("warnings", []),
        )

    response_data = {
        "stage": result.get("stage_num"),
        "output_path": result.get("output_path"),
        "next_stage": result.get("next_stage"),
        "session_path": result.get("session_path"),
    }
    if "saved_files" in result:
        response_data["saved_files"] = result["saved_files"]

    return _make_response(
        "success",
        f"{action_name}成功",
        data=response_data,
        warnings=result.get("warnings", []),
    )


def compiler_create_session(gdd_path: str, target_phase: str, output_dir: str) -> dict:
    """创建 Compiler Pipeline 会话。"""
    try:
        session = create_session(gdd_path, target_phase, output_dir)
        session_path = session.save()
        return _make_response(
            "success",
            "Compiler Pipeline 会话创建成功",
            data={
                "session_id": session.session_id,
                "session_path": session_path,
                "output_dir": session.output_dir,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Compiler Pipeline 会话创建失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_intake_prepare(session_path: str) -> dict:
    """Stage 1 准备：生成 GDD Projection 模板。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        result = prepare_stage(session, 1)
        return _wrap_prepare_result("Stage 1 准备", result)
    except Exception as exc:
        return _make_response(
            "failed",
            "Stage 1 准备失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_intake_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """Stage 1 保存：校验并保存 GDD Projection。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        result = save_stage(session, 1, filled_data)
        return _wrap_save_result("Stage 1 保存", result)
    except Exception as exc:
        return _make_response(
            "failed",
            "Stage 1 保存失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_plan_prepare(session_path: str) -> dict:
    """Stage 2 准备：生成 Planner Output 模板。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        result = prepare_stage(session, 2)
        return _wrap_prepare_result("Stage 2 准备", result)
    except Exception as exc:
        return _make_response(
            "failed",
            "Stage 2 准备失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_plan_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """Stage 2 保存：校验并保存 Planner Output。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        result = save_stage(session, 2, filled_data)
        return _wrap_save_result("Stage 2 保存", result)
    except Exception as exc:
        return _make_response(
            "failed",
            "Stage 2 保存失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_get_session_status(session_path: str) -> dict:
    """查询 Compiler Pipeline 会话状态。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        return _make_response(
            "success",
            "Compiler Pipeline 会话状态获取成功",
            data=session.to_dict(),
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Compiler Pipeline 会话状态获取失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )
