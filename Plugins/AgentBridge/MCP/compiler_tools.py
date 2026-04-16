"""
Compiler 前端 MCP 工具适配层。

职责：
  - 把 Compiler pipeline 的 session / prepare / save 能力适配成 MCP 工具返回格式
  - v1 保留 Intake/Planner；v2 覆盖 Root Skill、Clarification、Skill Graph
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
from Compiler.stages import domain_skill_runtime as dsr_stage


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
        "stage_name": result.get("stage_name"),
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


def _prepare_stage_tool(action_name: str, session_path: str, stage_num: int) -> dict:
    """读取 session 并调用指定 stage 的 prepare。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        result = prepare_stage(session, stage_num)
        return _wrap_prepare_result(action_name, result)
    except Exception as exc:
        return _make_response(
            "failed",
            f"{action_name}失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def _save_stage_tool(action_name: str, session_path: str, filled_data: dict[str, Any], stage_num: int) -> dict:
    """读取 session 并调用指定 stage 的 save。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        result = save_stage(session, stage_num, filled_data)
        return _wrap_save_result(action_name, result)
    except Exception as exc:
        return _make_response(
            "failed",
            f"{action_name}失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def _load_stage_for_plan_alias(session_path: str) -> int:
    """旧 plan alias：v1 指向 Planner Stage 2，v2 指向 Skill Graph Stage 3。"""
    session = _load_session(session_path)
    return 3 if session.session_version == "2.0" else 2


def compiler_create_session(
    gdd_path: str,
    target_phase: str,
    output_dir: str,
    session_version: str = "1.0",
    run_id: str | None = None,
    fast_mode: bool = False,
) -> dict:
    """创建 Compiler Pipeline 会话。"""
    try:
        session = create_session(
            gdd_path,
            target_phase,
            output_dir,
            session_version=session_version,
            run_id=run_id,
            fast_mode=fast_mode,
        )
        session_path = session.save()
        return _make_response(
            "success",
            "Compiler Pipeline 会话创建成功",
            data={
                "session_id": session.session_id,
                "session_path": session_path,
                "output_dir": session.output_dir,
                "session_version": session.session_version,
                "run_id": session.run_id,
                "fast_mode": session.fast_mode,
            },
        )
    except Exception as exc:
        return _make_response(
            "failed",
            "Compiler Pipeline 会话创建失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_root_skill_prepare(session_path: str) -> dict:
    """Phase 11 Stage 1 准备：生成 Root Skill Contract 模板。"""
    return _prepare_stage_tool("Root Skill 准备", session_path, 1)


def compiler_root_skill_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """Phase 11 Stage 1 保存：校验并保存 Root Skill Contract。"""
    return _save_stage_tool("Root Skill 保存", session_path, filled_data, 1)


def compiler_intake_prepare(session_path: str) -> dict:
    """旧名 alias：v1 为 Intake，v2 等价于 Root Skill prepare。"""
    return _prepare_stage_tool("Stage 1 准备", session_path, 1)


def compiler_intake_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """旧名 alias：v1 为 Intake，v2 等价于 Root Skill save。"""
    return _save_stage_tool("Stage 1 保存", session_path, filled_data, 1)


def compiler_clarification_prepare(session_path: str) -> dict:
    """Phase 11 Stage 2 准备：生成 Clarification Gate 模板。"""
    return _prepare_stage_tool("Clarification 准备", session_path, 2)


def compiler_clarification_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """Phase 11 Stage 2 保存：校验并保存 Clarification Gate Report。"""
    return _save_stage_tool("Clarification 保存", session_path, filled_data, 2)


def compiler_skill_graph_prepare(session_path: str) -> dict:
    """Phase 11 Stage 3 准备：生成 Skill Graph 模板。"""
    return _prepare_stage_tool("Skill Graph 准备", session_path, 3)


def compiler_skill_graph_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """Phase 11 Stage 3 保存：校验并保存 Skill Graph。"""
    return _save_stage_tool("Skill Graph 保存", session_path, filled_data, 3)


def compiler_plan_prepare(session_path: str) -> dict:
    """旧名 alias：v1 为 Planner Stage 2，v2 等价于 Skill Graph prepare。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        stage_num = _load_stage_for_plan_alias(session_path)
        result = prepare_stage(_load_session(session_path), stage_num)
        return _wrap_prepare_result("Stage 2/Skill Graph 准备", result)
    except Exception as exc:
        return _make_response(
            "failed",
            "Stage 2/Skill Graph 准备失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_plan_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """旧名 alias：v1 为 Planner Stage 2，v2 等价于 Skill Graph save。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)
        stage_num = 3 if session.session_version == "2.0" else 2
        result = save_stage(session, stage_num, filled_data)
        return _wrap_save_result("Stage 2/Skill Graph 保存", result)
    except Exception as exc:
        return _make_response(
            "failed",
            "Stage 2/Skill Graph 保存失败",
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


# ---------------------------------------------------------------------------
# Stage 4 逐节点交互（MCP Agent 即 Generator）
# ---------------------------------------------------------------------------

def _load_stage_artifact(session: CompilerSession, stage_num: int) -> dict:
    """读取指定阶段的产物 JSON。"""
    import json
    output_path = session.get_stage_output_path(stage_num)
    if not output_path or not Path(output_path).exists():
        return {}
    with Path(output_path).open("r", encoding="utf-8") as f:
        return json.load(f)


def compiler_stage4_node_prepare(
    session_path: str,
    node_id: str,
    phase: str,
    node_state: dict | None = None,
) -> dict:
    """Stage 4 逐节点准备：返回 SkillTemplate prompts + Context Bundle 供 Agent 创造性生成。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)

        # 加载前置阶段产物
        root_skill_contract = _load_stage_artifact(session, 1)
        clarification_gate_report = _load_stage_artifact(session, 2)
        skill_graph = _load_stage_artifact(session, 3)

        if not skill_graph:
            return _make_response(
                "failed",
                "Stage 4 准备失败：Stage 3 Skill Graph 产物不存在",
                errors=["PREREQUISITE_MISSING: skill_graph.json"],
            )

        result = dsr_stage.prepare_node_phase(
            node_id=node_id,
            phase=phase,
            skill_graph=skill_graph,
            root_skill_contract=root_skill_contract,
            clarification_gate_report=clarification_gate_report,
            phase_scope=session.target_phase,
            node_state=node_state,
        )

        if result.get("status") == "error":
            return _make_response("failed", result["error"], errors=[result["error"]])

        if result.get("status") == "skipped":
            return _make_response(
                "success",
                result.get("reason", "节点跳过"),
                data=result,
            )

        return _make_response(
            "success",
            f"Stage 4 节点 {node_id} {phase} 准备完成，请阅读 prompts 和 context_bundle 后生成输出",
            data=result,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            f"Stage 4 节点准备失败: {exc}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_stage4_node_save(
    session_path: str,
    node_id: str,
    phase: str,
    output: dict,
    node_state: dict | None = None,
) -> dict:
    """Stage 4 逐节点保存：校验 Agent 输出，convergence 完成后自动生成 Fragment。"""
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)

        root_skill_contract = _load_stage_artifact(session, 1)
        clarification_gate_report = _load_stage_artifact(session, 2)
        skill_graph = _load_stage_artifact(session, 3)

        if not skill_graph:
            return _make_response(
                "failed",
                "Stage 4 保存失败：Stage 3 Skill Graph 产物不存在",
                errors=["PREREQUISITE_MISSING: skill_graph.json"],
            )

        result = dsr_stage.save_node_phase(
            node_id=node_id,
            phase=phase,
            output=output,
            skill_graph=skill_graph,
            root_skill_contract=root_skill_contract,
            clarification_gate_report=clarification_gate_report,
            phase_scope=session.target_phase,
            node_state=node_state,
        )

        if result.get("status") == "error":
            return _make_response("failed", result["error"], errors=[result["error"]])

        if result.get("status") == "validation_failed":
            return _make_response(
                "failed",
                f"Stage 4 节点 {node_id} {phase} 输出校验失败",
                data=result,
                errors=result.get("errors", []),
            )

        # 记录 generator_provider 到 session（MCP Agent 模式）
        if not session.generator_provider:
            session.generator_provider = "llm"  # MCP Agent 视为 LLM 驱动
            session.save()

        summary = f"Stage 4 节点 {node_id} {phase} 保存成功"
        if result.get("fragment"):
            summary += "，Fragment 已生成"

        return _make_response("success", summary, data=result)
    except Exception as exc:
        return _make_response(
            "failed",
            f"Stage 4 节点保存失败: {exc}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )
