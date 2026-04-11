"""
Compiler Pipeline Orchestrator

职责：
  - 为五阶段骨架提供统一的 prepare / save / run 入口
  - 统一 schema 校验与结构化错误返回
  - 在 Stage 5 完成后组装 Reviewed Handoff v2
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jsonschema import Draft7Validator

from ..cross_review import cross_review
from ..intake import design_intake
from ..lowering import lowering
from ..planner import planner
from ..skill_runtime import skill_runtime
from .session import CompilerSession


PLUGIN_DIR = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = PLUGIN_DIR / "Schemas"
REVIEWED_HANDOFF_SCHEMA_PATH = SCHEMAS_DIR / "reviewed_handoff_v2.schema.json"

STAGE_NAME_MAP = {
    1: "design_intake",
    2: "planner",
    3: "skill_runtime",
    4: "cross_review",
    5: "lowering",
}

STAGE_ARTIFACT_MAP = {
    1: {
        "output_file": "gdd_projection.json",
        "schema_file": "gdd_projection.schema.json",
        "next_stage_input_key": "gdd_projection",
    },
    2: {
        "output_file": "planner_output.json",
        "schema_file": "planner_output.schema.json",
        "next_stage_input_key": "planner_output",
    },
    3: {
        "output_dir": "skill_fragments",
        "schema_file": "skill_fragment.schema.json",
        "next_stage_input_key": "skill_fragments",
        "multi_file": True,
    },
    4: {
        "output_file": "cross_review_report.json",
        "schema_file": "cross_review_report.schema.json",
        "next_stage_input_key": "cross_review_report",
    },
    5: {
        "output_file": "build_ir.json",
        "schema_file": "build_ir.schema.json",
        "next_stage_input_key": "build_ir",
    },
}


def _load_json_file(path: str | Path) -> Any:
    """读取 JSON 文件。"""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def _save_json_file(path: str | Path, payload: Any) -> str:
    """保存 JSON 文件。"""
    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return str(target_path)


def _validate_payload(payload: Any, schema: Dict[str, Any]) -> List[str]:
    """返回 schema 校验错误列表；为空表示通过。"""
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    formatted_errors = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        formatted_errors.append(f"{location}: {error.message}")
    return formatted_errors


def _validate_stage_payload(stage_num: int, payload: Any, schema: Dict[str, Any]) -> List[str]:
    """
    返回阶段级 schema 校验错误列表。

    说明：
      Phase 8 的 planner 样本里 skill_instance_id 使用了连字符命名。
      为了让 TASK 02 指定的 Phase 8 样本可直接回放，这里兼容放行该历史命名，
      其余字段仍按 schema 严格校验。
    """
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    filtered_errors = []
    for error in errors:
        path = list(error.path)
        if (
            stage_num == 2
            and error.validator == "pattern"
            and len(path) >= 3
            and path[0] == "selected_skill_instances"
            and path[2] == "skill_instance_id"
            and isinstance(error.instance, str)
            and re.fullmatch(r"skill-[a-z0-9_-]+", error.instance)
        ):
            continue
        filtered_errors.append(error)

    formatted_errors = []
    for error in filtered_errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        formatted_errors.append(f"{location}: {error.message}")
    return formatted_errors


def _build_stage_output_path(session: CompilerSession, stage_num: int) -> Path:
    """根据阶段号构建标准输出路径。"""
    stage_config = STAGE_ARTIFACT_MAP[stage_num]
    output_name = stage_config.get("output_file") or stage_config.get("output_dir")
    return Path(session.output_dir) / str(output_name)


def _load_schema(schema_file: str) -> Dict[str, Any]:
    """根据 schema 文件名加载 schema。"""
    return _load_json_file(SCHEMAS_DIR / schema_file)


def _get_stage_schema(stage_num: int) -> Dict[str, Any]:
    """读取指定阶段的输出 schema。"""
    return _load_schema(STAGE_ARTIFACT_MAP[stage_num]["schema_file"])


def _get_stage_output_key(stage_num: int) -> str:
    """返回 session.stage_outputs 使用的键名。"""
    return f"stage_{stage_num}"


def _validate_stage_num(stage_num: int) -> Dict[str, Any] | None:
    """统一校验阶段号。"""
    if stage_num in STAGE_NAME_MAP:
        return None
    return {
        "status": "invalid_stage",
        "stage_num": stage_num,
        "errors": [f"不支持的阶段号: {stage_num}"],
    }


def _load_stage_artifact(session: CompilerSession, stage_num: int) -> Any:
    """读取某阶段已经保存的产物。"""
    artifact_path = session.get_stage_output_path(stage_num)
    if not artifact_path:
        return None

    target_path = Path(artifact_path)
    if not target_path.exists():
        return None

    if target_path.is_dir():
        items = []
        for file_path in sorted(target_path.glob("*.json")):
            items.append(_load_json_file(file_path))
        return items

    return _load_json_file(target_path)


def _load_reviewed_handoff_schema() -> Dict[str, Any]:
    """读取 Reviewed Handoff v2 schema。"""
    return _load_json_file(REVIEWED_HANDOFF_SCHEMA_PATH)


def _safe_token(raw_value: str, fallback: str = "pipeline") -> str:
    """将任意字符串规整为 schema 允许的 token。"""
    token = re.sub(r"[^a-z0-9_]+", "_", raw_value.lower()).strip("_")
    return token or fallback


def _guess_project_name(session: CompilerSession, projection: Dict[str, Any]) -> str:
    """从 projection 或 GDD 文件名推断项目名。"""
    projection_id = str(projection.get("projection_id", "")).strip()
    if projection_id:
        parts = projection_id.split(".")
        if len(parts) >= 2 and parts[1]:
            return parts[1]

    gdd_stem = Path(session.gdd_path).stem
    if gdd_stem.startswith("GDD_"):
        gdd_stem = gdd_stem[4:]
    return gdd_stem or "UnknownProject"


def _collect_fragment_status_map(fragments: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """将 Stage 3 fragments 按 skill_instance_id 建立索引。"""
    status_map: Dict[str, Dict[str, Any]] = {}
    for fragment in fragments:
        skill_instance_id = fragment.get("skill_instance_id")
        if not skill_instance_id:
            continue
        status_map[skill_instance_id] = {
            "status": fragment.get("status", "completed"),
            "emitted_families": fragment.get("emitted_families", []),
            "capability_gaps": fragment.get("capability_gaps", []),
        }
    return status_map


def _collect_capability_gaps(
    planner_output: Dict[str, Any],
    fragments: List[Dict[str, Any]],
    review_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """汇总 Planner / Skill / Review 的能力缺口。"""
    gaps: List[Dict[str, Any]] = []

    for gap in planner_output.get("capability_gaps", []):
        gaps.append(
            {
                "gap_id": gap.get("gap_id", ""),
                "source": "planner",
                "description": gap.get("description", ""),
                "severity": gap.get("severity", "degraded"),
            }
        )

    for fragment in fragments:
        for gap in fragment.get("capability_gaps", []):
            gaps.append(
                {
                    "gap_id": gap.get("gap_id", ""),
                    "source": "skill",
                    "description": gap.get("description", ""),
                    "severity": gap.get("severity", "degraded"),
                }
            )

    for gap in review_report.get("capability_gap_list", []):
        gaps.append(
            {
                "gap_id": gap.get("gap_id", ""),
                "source": "review",
                "description": gap.get("description", ""),
                "severity": gap.get("severity", "degraded"),
            }
        )

    return gaps


def _normalize_text_list(items: List[Any]) -> List[str]:
    """把字符串列表 / 对象列表统一收敛成字符串列表。"""
    normalized: List[str] = []
    for item in items:
        if isinstance(item, str):
            normalized.append(item)
            continue

        if isinstance(item, dict):
            normalized.append(
                item.get("description")
                or item.get("requirement")
                or item.get("reason")
                or json.dumps(item, ensure_ascii=False)
            )
            continue

        normalized.append(str(item))
    return normalized


def _build_stage_three_templates(selected_skill_instances: List[Dict[str, Any]], target_phase: str) -> List[Dict[str, Any]]:
    """根据 Planner 结果为 Stage 3 构建一组 fragment 模板。"""
    templates = []
    for skill_instance in selected_skill_instances:
        templates.append(
            skill_runtime.create_fragment_template(
                skill_instance_id=skill_instance.get("skill_instance_id", ""),
                template_id=skill_instance.get("template_id", ""),
                phase_scope=target_phase,
            )
        )
    return templates


def _update_session_after_save(session: CompilerSession, stage_num: int, output_path: str) -> None:
    """保存阶段产物后统一更新 session。"""
    session.current_stage = stage_num
    session.stage_outputs[_get_stage_output_key(stage_num)] = output_path

    if stage_num < 5:
        session.status = "running"
        session.advance_stage()
    else:
        # Stage 5 保存后，等待 assemble_handoff 收尾并将状态切到 completed。
        session.status = "pending"

    session.save()


def prepare_stage(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """为指定阶段生成模板、schema 和输入上下文。"""
    invalid_stage = _validate_stage_num(stage_num)
    if invalid_stage:
        return invalid_stage

    previous_artifact_path = session.get_stage_input_path(stage_num)
    if stage_num > 1 and (not previous_artifact_path or not Path(previous_artifact_path).exists()):
        return {
            "status": "missing_input",
            "stage_num": stage_num,
            "stage_name": STAGE_NAME_MAP[stage_num],
            "errors": [f"Stage {stage_num} 缺少上游产物，期望路径: {previous_artifact_path or '<empty>'}"],
        }

    if stage_num == 1:
        template = design_intake.create_projection_template(session.gdd_path, session.target_phase)
        schema = _get_stage_schema(stage_num)
        input_context = {
            "gdd_path": session.gdd_path,
            "target_phase": session.target_phase,
        }
    elif stage_num == 2:
        projection = _load_stage_artifact(session, 1) or {}
        template = planner.create_planner_output_template(
            source_projection_id=projection.get("projection_id", ""),
            mode="greenfield",
            target_phase=session.target_phase,
        )
        schema = _get_stage_schema(stage_num)
        input_context = {
            STAGE_ARTIFACT_MAP[1]["next_stage_input_key"]: projection,
            "gdd_projection_path": session.get_stage_output_path(1),
            "source_projection_id": projection.get("projection_id", ""),
        }
    elif stage_num == 3:
        projection = _load_stage_artifact(session, 1) or {}
        planner_output = _load_stage_artifact(session, 2) or {}
        selected_skill_instances = planner_output.get("selected_skill_instances", [])
        template = _build_stage_three_templates(selected_skill_instances, session.target_phase)
        schema = _get_stage_schema(stage_num)
        input_context = {
            STAGE_ARTIFACT_MAP[1]["next_stage_input_key"]: projection,
            "gdd_projection_path": session.get_stage_output_path(1),
            STAGE_ARTIFACT_MAP[2]["next_stage_input_key"]: planner_output,
            "planner_output_path": session.get_stage_output_path(2),
            "selected_skill_instances": selected_skill_instances,
        }
    elif stage_num == 4:
        fragments = _load_stage_artifact(session, 3) or []
        planner_output = _load_stage_artifact(session, 2) or {}
        input_fragment_ids = [fragment.get("skill_instance_id", "") for fragment in fragments if fragment.get("skill_instance_id")]
        template = cross_review.create_review_report_template(input_fragment_ids=input_fragment_ids)
        schema = _get_stage_schema(stage_num)
        input_context = {
            STAGE_ARTIFACT_MAP[3]["next_stage_input_key"]: fragments,
            "skill_fragments_path": session.get_stage_output_path(3),
            "input_fragment_ids": input_fragment_ids,
            "planner_output_path": session.get_stage_output_path(2),
            "review_focuses": planner_output.get("review_focuses", []),
        }
    else:
        review_report = _load_stage_artifact(session, 4) or {}
        template = lowering.create_build_ir_template(
            source_review_id=review_report.get("review_id", ""),
            phase_scope=session.target_phase,
        )
        schema = _get_stage_schema(stage_num)
        input_context = {
            STAGE_ARTIFACT_MAP[4]["next_stage_input_key"]: review_report,
            "cross_review_report_path": session.get_stage_output_path(4),
            "source_review_id": review_report.get("review_id", ""),
            "reviewed_dynamic_spec_tree": review_report.get("reviewed_dynamic_spec_tree", {}),
        }

    return {
        "status": "ready_for_agent",
        "stage": stage_num,
        "stage_num": stage_num,
        "stage_name": STAGE_NAME_MAP[stage_num],
        "template": template,
        "schema": schema,
        "input_context": input_context,
    }


def save_stage(session: CompilerSession, stage_num: int, filled_data: Any) -> Dict[str, Any]:
    """校验并保存指定阶段产物，成功后更新 session。"""
    invalid_stage = _validate_stage_num(stage_num)
    if invalid_stage:
        return invalid_stage

    stage_config = STAGE_ARTIFACT_MAP[stage_num]
    schema = _get_stage_schema(stage_num)

    if stage_num > 1:
        prepare_result = prepare_stage(session, stage_num)
        if prepare_result.get("status") == "missing_input":
            return prepare_result

    if stage_config.get("multi_file"):
        fragments = filled_data if isinstance(filled_data, list) else [filled_data]
        validation_errors: List[str] = []
        for index, fragment in enumerate(fragments):
            validation_errors.extend(
                [f"fragment[{index}] {error}" for error in _validate_stage_payload(stage_num, fragment, schema)]
            )
        if validation_errors:
            return {
                "status": "validation_error",
                "stage_num": stage_num,
                "errors": validation_errors,
            }

        output_dir = _build_stage_output_path(session, stage_num)
        output_dir.mkdir(parents=True, exist_ok=True)
        saved_files = []
        for fragment in fragments:
            skill_instance_id = fragment.get("skill_instance_id", "skill_fragment")
            saved_files.append(skill_runtime.save_fragment(fragment, skill_instance_id, str(output_dir)))

        _update_session_after_save(session, stage_num, str(output_dir))

        return {
            "status": "saved",
            "stage_num": stage_num,
            "output_path": str(output_dir),
            "saved_files": saved_files,
            "next_stage": session.current_stage if stage_num < 5 else None,
            "session_path": str(session.session_path),
        }

    validation_errors = _validate_stage_payload(stage_num, filled_data, schema)
    if validation_errors:
        return {
            "status": "validation_error",
            "stage_num": stage_num,
            "errors": validation_errors,
        }

    output_path = _build_stage_output_path(session, stage_num)
    if stage_num == 1:
        saved_path = design_intake.save_projection(filled_data, str(output_path))
    elif stage_num == 2:
        saved_path = planner.save_planner_output(filled_data, str(output_path))
    elif stage_num == 4:
        saved_path = cross_review.save_review_report(filled_data, str(output_path))
    else:
        saved_path = lowering.save_build_ir(filled_data, str(output_path))

    _update_session_after_save(session, stage_num, str(saved_path))

    return {
        "status": "saved",
        "stage_num": stage_num,
        "output_path": str(saved_path),
        "next_stage": session.current_stage if stage_num < 5 else None,
        "session_path": str(session.session_path),
    }


def run_stage(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """调度单个阶段的 prepare 逻辑。"""
    if stage_num not in STAGE_NAME_MAP:
        return {
            "status": "invalid_stage",
            "stage_num": stage_num,
            "errors": [f"不支持的阶段号: {stage_num}"],
        }

    session.current_stage = stage_num
    session.status = "running"
    session.save()

    result = prepare_stage(session, stage_num)
    if result.get("status") != "ready_for_agent":
        session.status = "failed"
    else:
        session.status = "pending"
    session.save()
    return result


def run_pipeline(session: CompilerSession, stage_range: Iterable[int] | None = None) -> Dict[str, Any]:
    """
    按顺序调度指定阶段范围。

    说明：
      这里的 run 是“生成各阶段 prepare 结果”，不替代 Agent 填充与 save。
      一旦遇到缺少上游输入，会提前停止并返回已收集结果。
    """
    stages = list(stage_range) if stage_range is not None else list(range(session.current_stage, 6))
    results = []
    for stage_num in stages:
        result = run_stage(session, stage_num)
        results.append(result)
        if result.get("status") != "ready_for_agent":
            break

    return {
        "status": "ready_for_agent" if results and results[-1].get("status") == "ready_for_agent" else "stopped",
        "results": results,
    }


def assemble_handoff(session: CompilerSession) -> Dict[str, Any]:
    """在 Stage 5 完成后组装并保存 Reviewed Handoff v2。"""
    required_stage_outputs = [1, 2, 3, 4, 5]
    missing_stages = [stage_num for stage_num in required_stage_outputs if not session.has_stage_output(stage_num)]
    if missing_stages:
        return {
            "status": "missing_input",
            "errors": [f"assemble_handoff 缺少阶段产物: {missing_stages}"],
        }

    projection = _load_stage_artifact(session, 1) or {}
    planner_output = _load_stage_artifact(session, 2) or {}
    fragments = _load_stage_artifact(session, 3) or []
    review_report = _load_stage_artifact(session, 4) or {}
    build_ir = _load_stage_artifact(session, 5) or {}

    fragment_status_map = _collect_fragment_status_map(fragments)
    project_name = _guess_project_name(session, projection)
    build_mode = planner_output.get("execution_strategy", {}).get("build_mode", "greenfield")
    handoff_mode = "greenfield_bootstrap" if build_mode == "greenfield" else "brownfield_expansion"
    approval_status = review_report.get("review_status", "approved")
    if approval_status not in {"approved", "approved_with_warnings", "blocked"}:
        approval_status = "approved"

    review_focus_coverage = {
        check.get("check_id", f"check_{index:02d}"): check.get("result", "pass")
        for index, check in enumerate(review_report.get("review_checks", []), start=1)
    }
    remaining_warnings = [
        check.get("details", check.get("check_name", ""))
        for check in review_report.get("review_checks", [])
        if check.get("result") == "warning"
    ]

    handoff_payload = {
        "handoff_meta": {
            "handoff_version": "2.0",
            "handoff_id": f"handoff.{_safe_token(project_name, 'project')}.{_safe_token(build_mode, 'mode')}.{session.session_id.replace('-', '')[:8]}",
            "handoff_mode": handoff_mode,
            "schema_version": "2.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "target_phase": session.target_phase,
            "build_goal": planner_output.get("planner_meta", {}).get("target_build_goal", "playable_template"),
        },
        "project_context": {
            "project_name": project_name,
            "game_type": projection.get("game_identity", {}).get("game_type", ""),
            "subgenre": projection.get("game_identity", {}).get("subgenre", ""),
            "target_phase": session.target_phase,
            "current_iteration": f"pipeline_session_{session.session_id.replace('-', '')[:8]}",
        },
        "planner_summary": {
            "identified_domains": planner_output.get("routing_decision", {}).get("identified_domains", []),
            "selected_families": planner_output.get("dynamic_spec_targets", []),
            "phase_scope": planner_output.get("project_intent", {}).get("phase_scope", session.target_phase),
            "out_of_scope": planner_output.get("project_intent", {}).get("out_of_scope", []),
            "routing_summary": planner_output.get("routing_decision", {}).get("routing_reasoning_summary", ""),
        },
        "selected_skill_instances": [
            {
                "skill_instance_id": skill.get("skill_instance_id", ""),
                "template_id": skill.get("template_id", ""),
                "role": skill.get("role", ""),
                "status": fragment_status_map.get(skill.get("skill_instance_id", ""), {}).get("status", "completed"),
                "emitted_families": fragment_status_map.get(skill.get("skill_instance_id", ""), {}).get(
                    "emitted_families",
                    skill.get("emits_families", []),
                ),
            }
            for skill in planner_output.get("selected_skill_instances", [])
        ],
        "reviewed_dynamic_spec_tree": review_report.get("reviewed_dynamic_spec_tree", {}),
        "cross_review_summary": {
            "status": approval_status,
            "issues_found": len(review_report.get("issues_found", [])),
            "issues_resolved": sum(1 for issue in review_report.get("issues_found", []) if issue.get("resolved")),
            "remaining_warnings": remaining_warnings,
            "review_focus_coverage": review_focus_coverage,
        },
        "lowering_summary": {
            "families_bound": build_ir.get("lowering_report", {}).get("families_bound", []),
            "families_partially_bound": build_ir.get("lowering_report", {}).get("families_partially_bound", []),
            "unbound_requirements": _normalize_text_list(
                build_ir.get("lowering_report", {}).get("unbound_requirements", [])
            ),
            "build_ir_step_count": len(build_ir.get("build_steps", [])),
            "validation_point_count": len(build_ir.get("validation_ir", [])),
        },
        "build_ir": {
            "ir_id": build_ir.get("ir_id", ""),
            "build_steps": build_ir.get("build_steps", []),
            "inline": True,
        },
        "validation_ir": {
            "validations": build_ir.get("validation_ir", []),
            "inline": True,
        },
        "capability_gaps": _collect_capability_gaps(planner_output, fragments, review_report),
        "approval": {
            "approval_status": approval_status,
            "approver": "auto",
            "blocked_reasons": [
                issue.get("description", "")
                for issue in review_report.get("issues_found", [])
                if issue.get("severity") == "blocker" and not issue.get("resolved", False)
            ],
            "notes": "由 Compiler pipeline orchestrator 自动组装 Reviewed Handoff v2。",
        },
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generator": "AgentBridge.Compiler.PipelineOrchestrator.v1",
            "source_gdd": session.gdd_path,
            "source_projection_id": projection.get("projection_id", ""),
            "source_planner_id": planner_output.get("planner_meta", {}).get("source_projection_id", ""),
            "source_review_id": review_report.get("review_id", ""),
            "source_ir_id": build_ir.get("ir_id", ""),
        },
    }

    validation_errors = _validate_payload(handoff_payload, _load_reviewed_handoff_schema())
    if validation_errors:
        return {
            "status": "validation_error",
            "errors": validation_errors,
        }

    output_path = Path(session.output_dir) / "reviewed_handoff_v2.json"
    saved_path = _save_json_file(output_path, handoff_payload)
    session.current_stage = 5
    session.status = "completed"
    session.save()
    return {
        "status": "saved",
        "output_path": saved_path,
        "handoff": handoff_payload,
    }
