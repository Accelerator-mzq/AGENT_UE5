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
from Compiler.stages import skill_synthesis


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
    allow_skill_synthesis: bool = False,
) -> dict:
    """创建 Compiler Pipeline 会话。

    allow_skill_synthesis(Phase 13):MCP 侧合成开关入口——开启后持久化进
    session.json,后续 root_skill_save 的 anchor 强制随之生效。默认 False。
    """
    try:
        session = create_session(
            gdd_path,
            target_phase,
            output_dir,
            session_version=session_version,
            run_id=run_id,
            fast_mode=fast_mode,
            allow_skill_synthesis=bool(allow_skill_synthesis),
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
                # 回显开关终值(读 session 对象而非入参,所见即所存)
                "allow_skill_synthesis": session.allow_skill_synthesis,
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


def _capabilities_missing_anchor(contract: dict) -> list:
    """列出 activation=required 但 source_anchor 缺失/为空的 capability_id(排序稳定)。"""
    missing = []
    for key in ("gameplay_capabilities", "baseline_capabilities"):
        for capability in contract.get(key, []):
            if not isinstance(capability, dict):
                continue  # 畸形条目交给 schema 校验报错,这里不抢答
            if capability.get("activation") != "required":
                continue
            if not (capability.get("source_anchor") or "").strip():
                missing.append(capability.get("capability_id", "<unknown>"))
    return sorted(missing)


def compiler_root_skill_save(
    session_path: str,
    filled_data: dict[str, Any],
    action_name: str = "Root Skill",
) -> dict:
    """Phase 11 Stage 1 保存：校验并保存 Root Skill Contract。

    Phase 13 扩展(spec §5.2 兼容化落地):
      - session.allow_skill_synthesis=True 时,强制所有 required capability
        携带非空 source_anchor,缺失则整体 failed 且零落盘(合成留痕强制);
      - 未开启合成时缺 anchor 仅降级 warning(既有等价回归不受影响);
      - 保存成功后追加 GDD 覆盖矩阵 sidecar(三层保证模型第二层,失败不阻塞)。

    action_name 仅供 compiler_intake_save alias 转发时定制文案("Stage 1"),
    不暴露进 MCP 工具定义——两个工具各自保留调用方语义,行为完全同享。
    """
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)

        # anchor 留痕检查放在 save_stage(内含 schema 校验 + 落盘)之前:
        # 强制失败必须发生在落盘前。代价是 payload 同时缺 anchor 又不合 schema 时
        # 先报 anchor——两者都走 failed 重提路径,不影响最终一致性。
        anchor_warnings: list[str] = []
        missing_anchor = (
            _capabilities_missing_anchor(filled_data)
            if isinstance(filled_data, dict) else []
        )
        if missing_anchor:
            # 合成开关读取:CompilerSession.allow_skill_synthesis(Phase 13 最小扩展),
            # 旧 session 缺字段时 getattr 兜底为 False(降级 warning,不强制)
            if bool(getattr(session, "allow_skill_synthesis", False)):
                return _make_response(
                    "failed",
                    f"{action_name} 保存失败：{len(missing_anchor)} 个 required capability "
                    "缺 source_anchor（合成开启时强制留痕）",
                    data={"capabilities_missing_anchor": missing_anchor},
                    errors=[
                        "MISSING_SOURCE_ANCHOR: required capability 缺 source_anchor: "
                        + ", ".join(missing_anchor)
                    ],
                )
            anchor_warnings.append(
                f"capability 缺 source_anchor: {', '.join(missing_anchor)}（覆盖矩阵将列为无出处）"
            )

        result = save_stage(session, 1, filled_data)
        response = _wrap_save_result(f"{action_name} 保存", result)
        response["warnings"].extend(anchor_warnings)

        # GDD 覆盖矩阵 sidecar(JSON + 人读 markdown)——三层保证模型第二层。
        # 仅在带 capability 列表的 v2 root skill contract 保存成功后生成;
        # v1 gdd_projection 无这两个键,自然跳过,不污染 v1 产物目录。
        if response["status"] == "success" and isinstance(filled_data, dict) and (
            "gameplay_capabilities" in filled_data or "baseline_capabilities" in filled_data
        ):
            output_dir = Path(result["output_path"]).parent  # run 目录 = 契约落盘目录
            # 两段式 try(与 synthesis prepare 的 GDD 摘录同风格):
            # 模块导入问题与读取/解析问题分开归因,失败均降级 warning 不阻塞保存
            coverage = None
            try:
                from Compiler.stages import gdd_coverage as coverage  # lazy 包导入
            except ImportError:
                response["warnings"].append("gdd_coverage 模块缺失，覆盖矩阵未生成")
            if coverage is not None:
                try:
                    import json
                    gdd_text = Path(session.gdd_path).read_text(encoding="utf-8")
                    sections = coverage.split_gdd_sections(gdd_text)
                    all_capabilities = (
                        filled_data.get("gameplay_capabilities", [])
                        + filled_data.get("baseline_capabilities", [])
                    )
                    matrix = coverage.build_coverage_matrix(sections, all_capabilities)
                    matrix_path = output_dir / "gdd_coverage_matrix.json"
                    matrix_path.write_text(
                        json.dumps(matrix, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    (output_dir / "gdd_coverage_matrix.md").write_text(
                        coverage.render_coverage_markdown(matrix), encoding="utf-8"
                    )
                    response["data"]["gdd_coverage_matrix_path"] = str(matrix_path)
                except Exception as exc:
                    response["warnings"].append(f"覆盖矩阵生成失败（不阻塞）: {exc}")

        return response
    except Exception as exc:
        return _make_response(
            "failed",
            f"{action_name} 保存失败",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_intake_prepare(session_path: str) -> dict:
    """旧名 alias：v1 为 Intake，v2 等价于 Root Skill prepare。"""
    return _prepare_stage_tool("Stage 1 准备", session_path, 1)


def compiler_intake_save(session_path: str, filled_data: dict[str, Any]) -> dict:
    """旧名 alias：转发到 compiler_root_skill_save,与正名工具同享 Phase 13
    anchor 强制与覆盖矩阵落盘(封死绕行通道)。v1 行为无损:gdd_projection
    无 capability 键,anchor/矩阵块自然 no-op;文案保留 "Stage 1" 语义。"""
    return compiler_root_skill_save(session_path, filled_data, action_name="Stage 1")


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


def _resolve_node_state(session: CompilerSession, node_id: str, node_state: dict | None) -> dict | None:
    """优先使用调用方传入的 node_state，否则尝试从 sidecar 读回已保存状态。"""
    if node_state is not None:
        return node_state
    persisted_state = dsr_stage.load_mcp_node_state(session.output_dir, node_id)
    return persisted_state or None


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
            node_state=_resolve_node_state(session, node_id, node_state),
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
            node_state=_resolve_node_state(session, node_id, node_state),
            output_dir=session.output_dir,
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
            session.generator_provider = "mcp_agent"
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


# ---------------------------------------------------------------------------
# Phase 13 S3.5: Skill 合成工具对（prepare / save）
#
# skill_synthesis 走顶部包导入（与 domain_skill_runtime 同一套加载方式，
# 不再维护第三套 importlib 缓存）；测试可直接 monkeypatch
# Compiler.stages.skill_synthesis 实例的 DEFAULT_TEMPLATES_ROOT 等属性做注入。
# ---------------------------------------------------------------------------

def compiler_skill_synthesis_prepare(session_path: str, capability_id: str) -> dict:
    """S3.5 合成准备：为指定 capability gap 组装合成载荷。

    载荷 = gap 上下文 + GDD 摘录 + 约束 + 6 文件规范 + 范例模板 + family 白名单，
    经 skill_synthesis.build_synthesis_prepare_payload 组装后透传给 Agent。
    """
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    try:
        session = _load_session(session_path)

        # Stage 3 Skill Graph 是 capability gap 的事实源（照抄 stage4 工具的产物读取模式）
        skill_graph = _load_stage_artifact(session, 3)
        if not skill_graph:
            return _make_response(
                "failed",
                "合成准备失败：Stage 3 Skill Graph 产物不存在，请先完成 Stage 3",
                errors=["PREREQUISITE_MISSING: skill_graph.json"],
            )

        gaps = {
            gap.get("capability_id"): gap
            for gap in skill_graph.get("metadata", {}).get("capability_gaps", [])
        }
        gap = gaps.get(capability_id)
        if gap is None:
            return _make_response(
                "failed",
                f"合成准备失败：{capability_id} 不在 capability_gaps 中",
                data={"known_gaps": sorted(key for key in gaps if key)},
                errors=[f"UNKNOWN_CAPABILITY_GAP: {capability_id}"],
            )

        warnings: list[str] = []

        # 约束上下文来自 Stage 1 Root Skill Contract；缺失降级为空约束（不阻断合成）
        root_skill_contract = _load_stage_artifact(session, 1)
        constraints = root_skill_contract.get("constraint_fields", {}) if root_skill_contract else {}
        if not root_skill_contract:
            warnings.append("root_skill_contract.json 缺失，constraints 为空")

        # GDD 摘录：按 gap.source_anchor 提取 session.gdd_path 中对应章节。
        # gdd_coverage 已随 Task 9 落地；保留 ImportError 兜底只为模块缺失时
        # 优雅降级为空摘录（可见失效，不假装工作）。
        gdd_excerpt = ""
        anchor = (gap.get("source_anchor") or "").strip()
        if anchor:
            # 第一段 try 只管模块加载：缺模块单独识别为"未就绪"
            coverage = None
            try:
                from Compiler.stages import gdd_coverage as coverage  # lazy 包导入
            except ImportError:
                warnings.append("gdd_coverage 未就绪，摘录为空")
            # 第二段 try 管读取/解析：异常文本保留进 warning，不与"未就绪"混淆
            if coverage is not None:
                try:
                    gdd_text = Path(session.gdd_path).read_text(encoding="utf-8")
                    for section in coverage.split_gdd_sections(gdd_text):
                        if section.get("heading") == anchor:
                            gdd_excerpt = section.get("text", "")
                            break
                    if not gdd_excerpt:
                        warnings.append(f"GDD 中未找到 anchor 对应章节: {anchor}，摘录为空")
                except Exception as exc:
                    warnings.append(f"GDD 摘录失败（不阻塞）: {exc}")
        else:
            warnings.append("gap 无 source_anchor，GDD 摘录为空")

        try:
            payload = skill_synthesis.build_synthesis_prepare_payload(
                capability_id=capability_id,
                gap=gap,
                gdd_excerpt=gdd_excerpt,
                constraints=constraints,
            )
        except ValueError as exc:
            # 非法 capability_id（fail-fast）：数据/编程错误，不进 agent 重试闭环
            return _make_response(
                "failed",
                f"合成准备失败：capability_id 非法: {capability_id}",
                errors=[f"INVALID_ARGS: {exc}"],
            )

        return _make_response(
            "success",
            f"合成准备完成: {capability_id}（范例 {len(payload['exemplars'])} 个），"
            "请按 instructions 现场合成 6 文件包后调用 compiler_skill_synthesis_save 提交",
            data=payload,
            warnings=warnings,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            f"合成准备失败: {exc}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )


def compiler_skill_synthesis_save(session_path: str, capability_id: str, six_files: dict) -> dict:
    """S3.5 合成提交：机器校验后落盘 pending_review 并刷新人审清单。

    三态映射（save_synthesized_package → MCP 统一返回）：
      - saved    → success（包落盘 + 人审清单刷新；人审 approved 前 Stage 3 不可见）
      - rejected → failed（内容问题：按 errors 修正后重提，走 agent 重试闭环）
      - failed   → failed（环境问题：勿修改内容重试，先排查环境）
    两种 failed 的 summary 措辞可区分，data.synthesis_status 保留原始三态值。
    """
    target_path = Path(session_path)
    if not target_path.exists():
        return _missing_file_response(session_path, "session 文件")

    # MCP 层可能把 six_files 透传成字符串等非 dict 值：显式拦截，给明确文案
    if not isinstance(six_files, dict):
        return _make_response(
            "failed",
            "合成提交失败：six_files 必须是 object（key=文件名，value=文件内容字符串），"
            "请改为结构化对象后重提",
            errors=[f"INVALID_ARGS: six_files 期望 object，实际 {type(six_files).__name__}"],
        )

    try:
        session = _load_session(session_path)

        # 终审 I-2: provenance 戳记由 save 注入 manifest(spec §4.4 溯源承诺)——
        # run_id 取自 session(v2.0 自动生成;v1.0 可能为 None,落空字符串保持键形态稳定),
        # synthesized_by 固定标识 MCP agent 通道,agent 无法自报伪造
        provenance = {
            "synthesis_run_id": session.run_id or "",
            "synthesized_by": "mcp_agent",
        }

        # 不传 templates_root / family_whitelist：走插件默认模板树与正式库白名单
        result = skill_synthesis.save_synthesized_package(
            capability_id=capability_id,
            six_files=six_files,
            provenance=provenance,
        )
        synthesis_status = result.get("status")

        if synthesis_status == "rejected":
            return _make_response(
                "failed",
                f"合成包未通过机器校验（{len(result['errors'])} 项）：按 errors 修正后重提",
                data={"synthesis_status": "rejected", "package_dir": result.get("package_dir", "")},
                errors=result["errors"],
            )

        if synthesis_status == "failed":
            return _make_response(
                "failed",
                "合成包落盘失败（环境错误，非内容错误）：勿修改内容重试，"
                "请先排查环境（磁盘/权限），排查后可原样重提",
                data={"synthesis_status": "failed", "package_dir": result.get("package_dir", "")},
                errors=result["errors"],
            )

        # 显式判断 saved：三态契约外的未知值不默认当成功，走 failed（防上游悄悄加态）
        if synthesis_status != "saved":
            return _make_response(
                "failed",
                f"合成提交失败：save_synthesized_package 返回未知状态 {synthesis_status!r}",
                data={"synthesis_status": synthesis_status},
                errors=[f"TOOL_EXECUTION_FAILED: 未知 synthesis status: {synthesis_status!r}"],
            )

        # saved：刷新人审清单（run 目录 = session.output_dir，照抄现行 run 目录推导）
        warnings = ["该包未经人审，Stage 3 暂不可见（人审 approved 后才纳入注册表）"]
        review_path = None
        try:
            review_path = skill_synthesis.generate_synthesis_review(session.output_dir)
            review_note = f"，人审清单已刷新: {review_path}"
        except Exception as review_exc:
            # 包已落盘成功，清单刷新失败只降级为 warning，不掩盖 saved 事实
            warnings.append(f"人审清单刷新失败（包已落盘）: {review_exc}")
            review_note = "，但人审清单刷新失败（见 warnings）"

        return _make_response(
            "success",
            f"合成包已落盘 {result['package_dir']}（review_status=pending_review）{review_note}",
            data={
                "synthesis_status": "saved",
                "package_dir": result["package_dir"],
                "review_path": review_path,
                "next": "人审通过后把该包 manifest.yaml 的 review_status 改为 approved，再重跑 Stage 3",
            },
            warnings=warnings,
        )
    except Exception as exc:
        return _make_response(
            "failed",
            f"合成提交失败: {exc}",
            errors=[f"TOOL_EXECUTION_FAILED: {str(exc)}"],
        )
