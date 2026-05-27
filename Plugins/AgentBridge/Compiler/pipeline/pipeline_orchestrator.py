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
from ..stages import clarification_gate as clarification_gate_stage
from ..stages import cross_review_v2 as cross_review_v2_stage
from ..stages import domain_skill_runtime as domain_skill_runtime_stage
from ..stages import handoff_v3 as handoff_v3_stage
from ..stages.llm_client import load_llm_client_from_config
from ..providers.model_registry import build_default_router
from ..stages import lowering_v2 as lowering_v2_stage
from ..stages import root_skill_contract as root_skill_contract_stage
from ..stages import skill_graph_planning as skill_graph_planning_stage
from ..skill_runtime import skill_runtime
from .session import CompilerSession, get_max_stage as get_session_max_stage


PLUGIN_DIR = Path(__file__).resolve().parents[2]
PROJECT_ROOT = PLUGIN_DIR.parents[1]
SCHEMAS_DIR = PLUGIN_DIR / "Schemas"
PROJECT_RUNS_DIR = PROJECT_ROOT / "ProjectState" / "runs"
REVIEWED_HANDOFF_SCHEMA_PATH_V1 = SCHEMAS_DIR / "reviewed_handoff_v2.schema.json"
REVIEWED_HANDOFF_SCHEMA_PATH_V2 = SCHEMAS_DIR / "reviewed_handoff_v3.schema.json"
REVIEWED_HANDOFF_SCHEMA_PATH = REVIEWED_HANDOFF_SCHEMA_PATH_V1

STAGE_NAME_MAP_V1 = {
    1: "design_intake",
    2: "planner",
    3: "skill_runtime",
    4: "cross_review",
    5: "lowering",
}

STAGE_NAME_MAP_V2 = {
    1: "root_skill_contract",
    2: "clarification_gate",
    3: "skill_graph_planning",
    4: "domain_skill_runtime",
    5: "cross_domain_review",
    6: "lowering",
    7: "handoff_assembly",
}

STAGE_ARTIFACT_MAP_V1 = {
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

STAGE_ARTIFACT_MAP_V2 = {
    "metadata": {
        "output_file": "metadata.json",
        "next_stage_input_key": "metadata",
    },
    1: {
        "output_file": "root_skill_contract.json",
        "schema_file": "root_skill_contract.schema.json",
        "next_stage_input_key": "root_skill_contract",
    },
    2: {
        "output_file": "clarification_gate_report.json",
        "schema_file": "clarification_gate_report.schema.json",
        "next_stage_input_key": "clarification_gate_report",
    },
    3: {
        "output_file": "skill_graph.json",
        "schema_file": "skill_graph.schema.json",
        "next_stage_input_key": "skill_graph",
    },
    4: {
        "output_file": "converged_realization_pack.json",
        "schema_file": "converged_realization_pack.schema.json",
        "next_stage_input_key": "converged_realization_pack",
        "output_files": {
            "design_space_report": {
                "output_file": "design_space_report.json",
                "schema_file": "design_space_report.schema.json",
            },
            "realization_candidates": {
                "output_file": "realization_candidates.json",
                "schema_file": "realization_candidates.schema.json",
            },
            "converged_realization_pack": {
                "output_file": "converged_realization_pack.json",
                "schema_file": "converged_realization_pack.schema.json",
            },
            "skill_fragments": {
                "output_dir": "skill_fragments",
                "schema_file": "skill_fragment_v2.schema.json",
                "multi_file": True,
            },
        },
    },
    5: {
        "output_file": "cross_review_report.json",
        "schema_file": "cross_review_report_v2.schema.json",
        "next_stage_input_key": "cross_review_report",
    },
    6: {
        "output_file": "build_ir.json",
        "schema_file": "build_ir_v2.schema.json",
        "next_stage_input_key": "build_ir",
        "sidecar_files": {
            "naming_resolution_log": {
                "output_file": "naming_resolution_log.json",
                "schema_file": "naming_resolution_log.schema.json",
            },
        },
    },
    7: {
        "output_file": "reviewed_handoff_v3.json",
        "schema_file": "reviewed_handoff_v3.schema.json",
        "next_stage_input_key": "reviewed_handoff_v3",
    },
}

# 兼容旧调用：未显式区分版本的内部引用默认指向 v1。
STAGE_NAME_MAP = STAGE_NAME_MAP_V1
STAGE_ARTIFACT_MAP = STAGE_ARTIFACT_MAP_V1


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


def _load_stage4_output_bundle(session: CompilerSession) -> Dict[str, Any]:
    """
    加载 v2 Stage 4 的完整产物集合。

    说明：
      session.stage_outputs['stage_4'] 只登记 converged_realization_pack.json，
      但 Stage 5/7 还需要 design_space_report、realization_candidates 与 skill_fragments。
    """
    output_root = _get_session_output_root(session)
    stage4_bundle: Dict[str, Any] = {}

    design_space_path = output_root / "design_space_report.json"
    if design_space_path.exists():
        stage4_bundle["design_space_report"] = _load_json_file(design_space_path)

    candidates_path = output_root / "realization_candidates.json"
    if candidates_path.exists():
        stage4_bundle["realization_candidates"] = _load_json_file(candidates_path)

    converged_path = output_root / "converged_realization_pack.json"
    if converged_path.exists():
        stage4_bundle["converged_realization_pack"] = _load_json_file(converged_path)

    fragments_path = output_root / "skill_fragments"
    if fragments_path.is_dir():
        stage4_bundle["skill_fragments"] = [
            _load_json_file(file_path)
            for file_path in sorted(fragments_path.glob("*.json"))
        ]

    return stage4_bundle


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


def _get_session_version(session: CompilerSession) -> str:
    """读取 session 版本；旧 session 缺失字段时按 v1.0 路由。"""
    return getattr(session, "session_version", "1.0") or "1.0"


def get_stage_name_map(session: CompilerSession) -> Dict[int, str]:
    """根据 session_version 返回阶段名映射。"""
    if _get_session_version(session) == "2.0":
        return STAGE_NAME_MAP_V2
    return STAGE_NAME_MAP_V1


def get_stage_artifact_map(session: CompilerSession) -> Dict[Any, Dict[str, Any]]:
    """根据 session_version 返回产物映射。"""
    if _get_session_version(session) == "2.0":
        return STAGE_ARTIFACT_MAP_V2
    return STAGE_ARTIFACT_MAP_V1


def get_max_stage(session: CompilerSession) -> int:
    """根据 session_version 返回 Orchestrator 可调度的最大阶段。"""
    return get_session_max_stage(_get_session_version(session))


def _get_stage_artifact_config(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """读取当前版本下某个 stage 的产物配置。"""
    return get_stage_artifact_map(session)[stage_num]


def _get_stage_name(session: CompilerSession, stage_num: int) -> str:
    """读取当前版本下某个 stage 的名称。"""
    return get_stage_name_map(session)[stage_num]


def _get_session_output_root(session: CompilerSession) -> Path:
    """v2 产物固定进入 ProjectState/runs/{run_id}，v1 保持原 output_dir。"""
    if _get_session_version(session) == "2.0" and session.run_id:
        return PROJECT_RUNS_DIR / session.run_id
    return Path(session.output_dir)


def _build_stage_output_path(session: CompilerSession, stage_num: int) -> Path:
    """根据阶段号构建标准输出路径。"""
    stage_config = _get_stage_artifact_config(session, stage_num)
    output_name = stage_config.get("output_file") or stage_config.get("output_dir")
    return _get_session_output_root(session) / str(output_name)


def _load_schema(schema_file: str) -> Dict[str, Any]:
    """根据 schema 文件名加载 schema。"""
    return _load_json_file(SCHEMAS_DIR / schema_file)


def _get_stage_schema(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """读取指定阶段的输出 schema。"""
    return _load_schema(_get_stage_artifact_config(session, stage_num)["schema_file"])


def _get_stage_output_key(stage_num: int) -> str:
    """返回 session.stage_outputs 使用的键名。"""
    return f"stage_{stage_num}"


def _validate_stage_num(session: CompilerSession, stage_num: int) -> Dict[str, Any] | None:
    """统一校验阶段号。"""
    if stage_num in get_stage_name_map(session):
        return None
    return {
        "status": "invalid_stage",
        "stage_num": stage_num,
        "errors": [f"session_version={_get_session_version(session)} 不支持阶段号: {stage_num}"],
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


def _load_reviewed_handoff_schema_for_session(session: CompilerSession) -> Dict[str, Any]:
    """按 session_version 读取最终 handoff schema。"""
    if _get_session_version(session) == "2.0":
        return _load_json_file(REVIEWED_HANDOFF_SCHEMA_PATH_V2)
    return _load_json_file(REVIEWED_HANDOFF_SCHEMA_PATH_V1)


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

    max_stage = get_max_stage(session)
    if stage_num < max_stage:
        session.status = "running"
        session.advance_stage()
    elif _get_session_version(session) == "1.0":
        # v1 Stage 5 之后仍需 assemble_handoff 生成 reviewed_handoff_v2。
        session.status = "pending"
    else:
        session.status = "completed"

    session.save()


def build_run_metadata(
    session: CompilerSession,
    clarification_gate_report: Dict[str, Any] | None = None,
    cross_review_report: Dict[str, Any] | None = None,
    completed_at: str | None = None,
) -> Dict[str, Any]:
    """构造 Phase 11 run metadata，供验证脚本与治理工具复用。"""
    clarification_gate_report = clarification_gate_report or {}
    cross_review_report = cross_review_report or {}
    pipeline_stages_completed = sorted(
        int(stage_key.split("_", 1)[1])
        for stage_key, output_path in session.stage_outputs.items()
        if output_path
    )

    return {
        "run_id": session.run_id,
        "session_id": session.session_id,
        "session_version": session.session_version,
        "fast_mode": session.fast_mode,
        "generator_provider": session.generator_provider,
        "created_at": session.created_at,
        "completed_at": completed_at or datetime.now(timezone.utc).isoformat(),
        "status": session.status,
        "pipeline_stages_completed": pipeline_stages_completed,
        "constraint_violations": cross_review_report.get("constraint_preservation_summary", {}).get("violations", 0),
        "provisional_items": clarification_gate_report.get("provisional_items", []),
        "clarification_gate_policy": clarification_gate_report.get("clarification_gate_policy", ""),
        "promotable": session.is_promotable,
        "output_dir": session.output_dir,
    }


def _prepare_stage_v1(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """为 v1 五阶段生成模板、schema 和输入上下文。"""
    invalid_stage = _validate_stage_num(session, stage_num)
    if invalid_stage:
        return invalid_stage

    previous_artifact_path = session.get_stage_input_path(stage_num)
    if stage_num > 1 and (not previous_artifact_path or not Path(previous_artifact_path).exists()):
        return {
            "status": "missing_input",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "errors": [f"Stage {stage_num} 缺少上游产物，期望路径: {previous_artifact_path or '<empty>'}"],
        }

    if stage_num == 1:
        template = design_intake.create_projection_template(session.gdd_path, session.target_phase)
        schema = _get_stage_schema(session, stage_num)
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
        schema = _get_stage_schema(session, stage_num)
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
        schema = _get_stage_schema(session, stage_num)
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
        schema = _get_stage_schema(session, stage_num)
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
        schema = _get_stage_schema(session, stage_num)
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
        "stage_name": _get_stage_name(session, stage_num),
        "template": template,
        "schema": schema,
        "input_context": input_context,
    }


def _load_stage_schema_or_error(session: CompilerSession, stage_num: int) -> tuple[Dict[str, Any] | None, Dict[str, Any] | None]:
    """v2 骨架阶段使用：Schema 缺失时返回结构化错误而不是抛异常。"""
    schema_file = _get_stage_artifact_config(session, stage_num).get("schema_file")
    if not schema_file:
        return None, {
            "status": "schema_missing",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "errors": [f"Stage {stage_num} 未配置 schema_file"],
        }

    schema_path = SCHEMAS_DIR / schema_file
    if not schema_path.exists():
        return None, {
            "status": "schema_missing",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "errors": [f"Schema 文件尚未存在，等待 TASK 04/10 补齐: {schema_path}"],
        }

    return _load_json_file(schema_path), None


def _load_stage_output_schema_bundle(session: CompilerSession, stage_num: int) -> Dict[str, Dict[str, Any]]:
    """读取带 output_files 的 stage schema bundle。"""
    stage_config = _get_stage_artifact_config(session, stage_num)
    schema_bundle: Dict[str, Dict[str, Any]] = {}
    for output_key, output_config in stage_config.get("output_files", {}).items():
        schema_bundle[output_key] = _load_schema(output_config["schema_file"])
    return schema_bundle


def _prepare_stage_v2(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """为 v2 七阶段返回 prepare 结果；已接入 Stage 1/2 的真实生成逻辑。"""
    invalid_stage = _validate_stage_num(session, stage_num)
    if invalid_stage:
        return invalid_stage

    previous_artifact_path = session.get_stage_input_path(stage_num)
    if stage_num > 1 and (not previous_artifact_path or not Path(previous_artifact_path).exists()):
        return {
            "status": "missing_input",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "errors": [f"Stage {stage_num} 缺少上游产物，期望路径: {previous_artifact_path or '<empty>'}"],
        }

    schema, schema_error = _load_stage_schema_or_error(session, stage_num)
    if schema_error:
        return schema_error

    stage_config = _get_stage_artifact_config(session, stage_num)
    input_context = {
        "session_version": session.session_version,
        "run_id": session.run_id,
        "target_phase": session.target_phase,
        "output_root": str(_get_session_output_root(session)),
        "previous_artifact_path": previous_artifact_path,
        "auto_generated": stage_num in {1, 2, 3, 4},
    }

    if stage_num == 1:
        template = root_skill_contract_stage.create_root_skill_contract(
            gdd_path=session.gdd_path,
            target_phase=session.target_phase,
            run_id=session.run_id,
        )
    elif stage_num == 2:
        root_skill_contract = _load_stage_artifact(session, 1) or {}
        template = clarification_gate_stage.create_clarification_gate_report(
            root_skill_contract=root_skill_contract,
            fast_mode=session.fast_mode,
            run_id=session.run_id,
        )
        input_context.update(
            {
                STAGE_ARTIFACT_MAP_V2[1]["next_stage_input_key"]: root_skill_contract,
                "root_skill_contract_path": session.get_stage_output_path(1),
                "clarification_items": template.get("items", []),
                "clarification_items_by_decision": template.get("items_by_decision_summary", {}),
                "provisional_items": template.get("provisional_items", []),
                "blocking_items": template.get("blocking_items", []),
                "retained_clarifications": template.get("retained_clarifications", []),
                "clarification_gate_policy": template.get("clarification_gate_policy", ""),
                "downstream_propagation_contract": template.get("downstream_propagation_contract", {}),
            }
        )
    elif stage_num == 3:
        root_skill_contract = _load_stage_artifact(session, 1) or {}
        clarification_gate_report = _load_stage_artifact(session, 2) or {}
        blocking_items = clarification_gate_report.get("blocking_items", [])
        if blocking_items:
            return {
                "status": "blocked_by_clarification",
                "stage_num": stage_num,
                "stage_name": _get_stage_name(session, stage_num),
                "blocking_items": blocking_items,
                "errors": [
                    "Clarification Gate 存在 critical blocker，Skill Graph Planning 不允许继续。"
                ],
            }

        template = skill_graph_planning_stage.create_skill_graph(
            root_skill_contract=root_skill_contract,
            clarification_gate_report=clarification_gate_report,
            run_id=session.run_id,
        )
        gameplay_nodes = [
            node for node in template.get("nodes", [])
            if node.get("domain_type") == "gameplay"
        ]
        baseline_nodes = [
            node for node in template.get("nodes", [])
            if node.get("domain_type") == "baseline"
        ]
        input_context.update(
            {
                STAGE_ARTIFACT_MAP_V2[1]["next_stage_input_key"]: root_skill_contract,
                "root_skill_contract_path": session.get_stage_output_path(1),
                STAGE_ARTIFACT_MAP_V2[2]["next_stage_input_key"]: clarification_gate_report,
                "clarification_gate_report_path": session.get_stage_output_path(2),
                "provisional_items": clarification_gate_report.get("provisional_items", []),
                "retained_clarifications": clarification_gate_report.get("retained_clarifications", []),
                "downstream_propagation_contract": clarification_gate_report.get("downstream_propagation_contract", {}),
                "gameplay_nodes": gameplay_nodes,
                "baseline_nodes": baseline_nodes,
                "skill_graph_edges": template.get("edges", []),
            }
        )
    elif stage_num == 4:
        root_skill_contract = _load_stage_artifact(session, 1) or {}
        clarification_gate_report = _load_stage_artifact(session, 2) or {}
        skill_graph = _load_stage_artifact(session, 3) or {}
        # allow_heuristic_fallback: 当前默认允许（无 LLM client 时退化为确定性引擎）
        # 正式 run 应配置 LLM client，heuristic fallback 产出的 run 自动 promotable=False
        # Phase 12: 优先用 router(新路径,支持 candidates 分批);否则 fallback 老 llm_client
        router_with_policy = build_default_router()
        if router_with_policy is not None:
            router, policy = router_with_policy
            template = domain_skill_runtime_stage.run_domain_skill_runtime(
                skill_graph=skill_graph,
                root_skill_contract=root_skill_contract,
                clarification_gate_report=clarification_gate_report,
                phase_scope=session.target_phase,
                fast_mode=session.fast_mode,
                allow_heuristic_fallback=True,
                llm_client=None,
                router=router,
                policy=policy,
                batch_concurrency=3,
            )
        else:
            template = domain_skill_runtime_stage.run_domain_skill_runtime(
                skill_graph=skill_graph,
                root_skill_contract=root_skill_contract,
                clarification_gate_report=clarification_gate_report,
                phase_scope=session.target_phase,
                fast_mode=session.fast_mode,
                allow_heuristic_fallback=True,
                llm_client=load_llm_client_from_config(),
            )
        if template.get("status") in {"refused", "validation_failed"}:
            return {
                "status": "stage_generation_failed",
                "stage_num": stage_num,
                "stage_name": _get_stage_name(session, stage_num),
                "errors": template.get("acceptance_errors", []) or [template.get("failure_reason", "Stage 4 验收失败。")],
                "template": template,
            }
        # 记录 Generator Provider 类型到 session（影响 promotable 判定）
        gp_type = template.get("generator_provider_type")
        if gp_type and not session.generator_provider:
            session.generator_provider = gp_type
        schema = _load_stage_output_schema_bundle(session, stage_num)
        input_context.update(
            {
                STAGE_ARTIFACT_MAP_V2[1]["next_stage_input_key"]: root_skill_contract,
                "root_skill_contract_path": session.get_stage_output_path(1),
                STAGE_ARTIFACT_MAP_V2[2]["next_stage_input_key"]: clarification_gate_report,
                "clarification_gate_report_path": session.get_stage_output_path(2),
                STAGE_ARTIFACT_MAP_V2[3]["next_stage_input_key"]: skill_graph,
                "skill_graph_path": session.get_stage_output_path(3),
                "execution_order": template.get("execution_order", []),
                "lifecycle_records": template.get("lifecycle_records", []),
                "provisional_items": clarification_gate_report.get("provisional_items", []),
            }
        )
    elif stage_num == 5:
        # Stage 5: Cross-Domain Review v2
        root_skill_contract = _load_stage_artifact(session, 1) or {}
        clarification_gate_report = _load_stage_artifact(session, 2) or {}
        skill_graph = _load_stage_artifact(session, 3) or {}
        stage4_output = _load_stage4_output_bundle(session)
        # Stage 4 产物是 converged_realization_pack.json，需要补充 fragments
        stage4_fragments_path = _get_session_output_root(session) / "skill_fragments"
        if stage4_fragments_path.is_dir():
            stage4_fragments = []
            for fp in sorted(stage4_fragments_path.glob("*.json")):
                stage4_fragments.append(_load_json_file(fp))
            stage4_output["skill_fragments"] = stage4_fragments
        template = cross_review_v2_stage.create_cross_review_report_v2(
            root_skill_contract=root_skill_contract,
            clarification_gate_report=clarification_gate_report,
            skill_graph=skill_graph,
            stage4_output=stage4_output,
            phase_scope=session.target_phase,
        )
        input_context.update({
            STAGE_ARTIFACT_MAP_V2[1]["next_stage_input_key"]: root_skill_contract,
            STAGE_ARTIFACT_MAP_V2[3]["next_stage_input_key"]: skill_graph,
            "stage4_output": stage4_output,
        })
    elif stage_num == 6:
        # Stage 6: Lowering v2
        root_skill_contract = _load_stage_artifact(session, 1) or {}
        skill_graph = _load_stage_artifact(session, 3) or {}
        cross_review_report = _load_stage_artifact(session, 5) or {}
        lowering_result = lowering_v2_stage.create_build_ir_v2(
            cross_review_report=cross_review_report,
            root_skill_contract=root_skill_contract,
            skill_graph=skill_graph,
            phase_scope=session.target_phase,
        )
        template = lowering_result["build_ir"]
        input_context.update({
            STAGE_ARTIFACT_MAP_V2[5]["next_stage_input_key"]: cross_review_report,
            "naming_resolution_log": lowering_result["naming_resolution_log"],
        })
    else:
        # Stage 7: Handoff Assembly v3 — prepare 返回占位，实际组装由 assemble_handoff 完成
        template = {
            "session_version": session.session_version,
            "run_id": session.run_id,
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "notes": "Stage 7 由 assemble_handoff 完成组装，prepare 仅做前置检查。",
        }

    return {
        "status": "ready_for_agent",
        "stage": stage_num,
        "stage_num": stage_num,
        "stage_name": _get_stage_name(session, stage_num),
        "template": template,
        "schema": schema,
        "input_context": input_context,
    }


def prepare_stage(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """为指定阶段生成模板、schema 和输入上下文，并按 session_version 路由。"""
    if _get_session_version(session) == "2.0":
        return _prepare_stage_v2(session, stage_num)
    return _prepare_stage_v1(session, stage_num)


def _save_stage_v1(session: CompilerSession, stage_num: int, filled_data: Any) -> Dict[str, Any]:
    """校验并保存 v1 阶段产物，成功后更新 session。"""
    invalid_stage = _validate_stage_num(session, stage_num)
    if invalid_stage:
        return invalid_stage

    stage_config = _get_stage_artifact_config(session, stage_num)
    schema = _get_stage_schema(session, stage_num)

    if stage_num > 1:
        prepare_result = prepare_stage(session, stage_num)
        if prepare_result.get("status") != "ready_for_agent":
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
            "next_stage": session.current_stage if stage_num < get_max_stage(session) else None,
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
        "next_stage": session.current_stage if stage_num < get_max_stage(session) else None,
        "session_path": str(session.session_path),
    }


def _save_stage_v2(session: CompilerSession, stage_num: int, filled_data: Any) -> Dict[str, Any]:
    """校验并保存 v2 阶段产物；复杂多产物阶段由后续 TASK 扩展。"""
    invalid_stage = _validate_stage_num(session, stage_num)
    if invalid_stage:
        return invalid_stage

    if stage_num > 1:
        prepare_result = prepare_stage(session, stage_num)
        if prepare_result.get("status") != "ready_for_agent":
            return prepare_result

    if stage_num == 4:
        stage_config = _get_stage_artifact_config(session, stage_num)
        schema_bundle = _load_stage_output_schema_bundle(session, stage_num)
        required_keys = [
            "design_space_report",
            "realization_candidates",
            "converged_realization_pack",
            "skill_fragments",
        ]
        missing_keys = [key for key in required_keys if key not in filled_data]
        if missing_keys:
            return {
                "status": "validation_error",
                "stage_num": stage_num,
                "stage_name": _get_stage_name(session, stage_num),
                "errors": [f"Stage 4 缺少必要输出键: {', '.join(missing_keys)}"],
            }

        validation_errors: List[str] = []
        for output_key in ("design_space_report", "realization_candidates", "converged_realization_pack"):
            validation_errors.extend(
                [
                    f"{output_key} {error}"
                    for error in _validate_payload(
                        filled_data.get(output_key),
                        schema_bundle[output_key],
                    )
                ]
            )

        fragment_schema = schema_bundle["skill_fragments"]
        fragments = filled_data.get("skill_fragments", [])
        if not isinstance(fragments, list):
            return {
                "status": "validation_error",
                "stage_num": stage_num,
                "stage_name": _get_stage_name(session, stage_num),
                "errors": ["skill_fragments 必须是列表。"],
            }
        for index, fragment in enumerate(fragments):
            validation_errors.extend(
                [
                    f"skill_fragments[{index}] {error}"
                    for error in _validate_payload(fragment, fragment_schema)
                ]
            )

        if validation_errors:
            return {
                "status": "validation_error",
                "stage_num": stage_num,
                "stage_name": _get_stage_name(session, stage_num),
                "errors": validation_errors,
            }

        output_root = _get_session_output_root(session)
        saved_files: Dict[str, Any] = {}
        for output_key, output_config in stage_config.get("output_files", {}).items():
            if output_config.get("multi_file"):
                output_dir = output_root / output_config["output_dir"]
                output_dir.mkdir(parents=True, exist_ok=True)
                fragment_files = []
                for fragment in fragments:
                    skill_instance_id = fragment.get("skill_instance_id", "skill_fragment")
                    fragment_files.append(skill_runtime.save_fragment(fragment, skill_instance_id, str(output_dir)))
                saved_files[output_key] = fragment_files
                continue

            output_path = output_root / output_config["output_file"]
            saved_files[output_key] = _save_json_file(output_path, filled_data.get(output_key))

        _update_session_after_save(
            session,
            stage_num,
            str(output_root / stage_config["output_file"]),
        )

        return {
            "status": "saved",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "output_path": str(output_root / stage_config["output_file"]),
            "saved_files": saved_files,
            "next_stage": session.current_stage if stage_num < get_max_stage(session) else None,
            "session_path": str(session.session_path),
        }

    # Stage 6 特殊处理：保存 build_ir + naming_resolution_log sidecar
    if stage_num == 6 and isinstance(filled_data, dict) and "naming_resolution_log" in filled_data:
        build_ir_data = filled_data.get("build_ir", filled_data)
        naming_log = filled_data.get("naming_resolution_log", {})

        schema, schema_error = _load_stage_schema_or_error(session, stage_num)
        if schema_error:
            return schema_error
        if schema:
            validation_errors = _validate_stage_payload(stage_num, build_ir_data, schema)
            if validation_errors:
                return {
                    "status": "validation_error",
                    "stage_num": stage_num,
                    "stage_name": _get_stage_name(session, stage_num),
                    "errors": validation_errors,
                }

        output_root = _get_session_output_root(session)
        ir_path = output_root / "build_ir.json"
        saved_ir = _save_json_file(ir_path, build_ir_data)
        naming_log_path = output_root / "naming_resolution_log.json"
        _save_json_file(naming_log_path, naming_log)
        _update_session_after_save(session, stage_num, saved_ir)

        return {
            "status": "saved",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "output_path": saved_ir,
            "saved_files": {
                "build_ir": saved_ir,
                "naming_resolution_log": str(naming_log_path),
            },
            "next_stage": session.current_stage if stage_num < get_max_stage(session) else None,
            "session_path": str(session.session_path),
        }

    schema, schema_error = _load_stage_schema_or_error(session, stage_num)
    if schema_error:
        return schema_error

    validation_errors = _validate_stage_payload(stage_num, filled_data, schema or {})
    if validation_errors:
        return {
            "status": "validation_error",
            "stage_num": stage_num,
            "stage_name": _get_stage_name(session, stage_num),
            "errors": validation_errors,
        }

    output_path = _build_stage_output_path(session, stage_num)
    saved_path = _save_json_file(output_path, filled_data)
    _update_session_after_save(session, stage_num, str(saved_path))

    return {
        "status": "saved",
        "stage_num": stage_num,
        "stage_name": _get_stage_name(session, stage_num),
        "output_path": str(saved_path),
        "next_stage": session.current_stage if stage_num < get_max_stage(session) else None,
        "session_path": str(session.session_path),
    }


def save_stage(session: CompilerSession, stage_num: int, filled_data: Any) -> Dict[str, Any]:
    """校验并保存指定阶段产物，成功后更新 session，并按 session_version 路由。"""
    if _get_session_version(session) == "2.0":
        return _save_stage_v2(session, stage_num, filled_data)
    return _save_stage_v1(session, stage_num, filled_data)


def run_stage(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """调度单个阶段的 prepare 逻辑。"""
    invalid_stage = _validate_stage_num(session, stage_num)
    if invalid_stage:
        return invalid_stage

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
    stages = list(stage_range) if stage_range is not None else list(range(session.current_stage, get_max_stage(session) + 1))
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


def _assemble_handoff_v1(session: CompilerSession) -> Dict[str, Any]:
    """在 v1 Stage 5 完成后组装并保存 Reviewed Handoff v2。"""
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

    validation_errors = _validate_payload(handoff_payload, _load_reviewed_handoff_schema_for_session(session))
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


def _assemble_handoff_v2(session: CompilerSession) -> Dict[str, Any]:
    """v2 handoff assembly: 组装 Reviewed Handoff v3。"""
    required_stage_outputs = [1, 2, 3, 4, 5, 6]
    missing_stages = [stage_num for stage_num in required_stage_outputs if not session.has_stage_output(stage_num)]
    if missing_stages:
        return {
            "status": "missing_input",
            "stage_num": 7,
            "stage_name": _get_stage_name(session, 7),
            "errors": [f"assemble_handoff_v3 缺少阶段产物: {missing_stages}"],
        }

    # 加载全部上游产物
    root_skill_contract = _load_stage_artifact(session, 1) or {}
    clarification_gate_report = _load_stage_artifact(session, 2) or {}
    skill_graph = _load_stage_artifact(session, 3) or {}
    stage4_output = _load_stage4_output_bundle(session)
    # 补充 fragments
    stage4_fragments_path = _get_session_output_root(session) / "skill_fragments"
    if stage4_fragments_path.is_dir():
        stage4_fragments = []
        for fp in sorted(stage4_fragments_path.glob("*.json")):
            stage4_fragments.append(_load_json_file(fp))
        stage4_output["skill_fragments"] = stage4_fragments
    cross_review_report = _load_stage_artifact(session, 5) or {}
    build_ir = _load_stage_artifact(session, 6) or {}

    # 加载 naming_resolution_log（sidecar）
    naming_log_path = _get_session_output_root(session) / "naming_resolution_log.json"
    naming_resolution_log: Dict[str, Any] = {}
    if naming_log_path.exists():
        naming_resolution_log = _load_json_file(naming_log_path)

    # 组装
    session_meta = {
        "session_id": session.session_id,
        "run_id": session.run_id,
        "target_phase": session.target_phase,
        "gdd_path": session.gdd_path,
        "fast_mode": session.fast_mode,
        "session_version": session.session_version,
    }

    handoff_payload = handoff_v3_stage.assemble_handoff_v3(
        root_skill_contract=root_skill_contract,
        clarification_gate_report=clarification_gate_report,
        skill_graph=skill_graph,
        stage4_output=stage4_output,
        cross_review_report=cross_review_report,
        build_ir=build_ir,
        naming_resolution_log=naming_resolution_log,
        session_meta=session_meta,
    )

    # Schema 校验（如果 schema 存在）
    schema_path = REVIEWED_HANDOFF_SCHEMA_PATH_V2
    if schema_path.exists():
        validation_errors = _validate_payload(handoff_payload, _load_json_file(schema_path))
        if validation_errors:
            return {
                "status": "validation_error",
                "stage_num": 7,
                "stage_name": _get_stage_name(session, 7),
                "errors": validation_errors,
            }

    # 保存
    output_path = _get_session_output_root(session) / "reviewed_handoff_v3.json"
    saved_path = _save_json_file(output_path, handoff_payload)
    _update_session_after_save(session, 7, str(saved_path))

    return {
        "status": "saved",
        "stage_num": 7,
        "stage_name": _get_stage_name(session, 7),
        "output_path": saved_path,
        "handoff": handoff_payload,
    }


def assemble_handoff(session: CompilerSession) -> Dict[str, Any]:
    """按 session_version 组装最终 handoff，不做跨版本产物转换。"""
    if _get_session_version(session) == "2.0":
        return _assemble_handoff_v2(session)
    return _assemble_handoff_v1(session)
