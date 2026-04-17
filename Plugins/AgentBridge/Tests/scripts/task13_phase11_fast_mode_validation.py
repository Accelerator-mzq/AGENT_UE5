"""TASK 13：完整 fast_mode 策略验收脚本。"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from jsonschema import validators


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MCP_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge" / "MCP"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from Plugins.AgentBridge.Compiler.pipeline.pipeline_orchestrator import (  # noqa: E402
    assemble_handoff,
    build_run_metadata,
    prepare_stage,
    save_stage,
)
from Plugins.AgentBridge.Compiler.pipeline.session import CompilerSession, create_session, generate_run_id  # noqa: E402
from Plugins.AgentBridge.Compiler.stages import clarification_gate as clarification_gate_stage  # noqa: E402
import evidence_tools  # noqa: E402


REPORT_DATE = "2026-04-16"
REPORT_ROOT = PROJECT_ROOT / "ProjectState" / "Reports" / REPORT_DATE
OUTPUT_ROOT = REPORT_ROOT / "task13_validation_outputs"
RUNS_ROOT = PROJECT_ROOT / "ProjectState" / "runs"
GDD_PATH = PROJECT_ROOT / "ProjectInputs" / "GDD" / "GDD_MonopolyGame.md"
SCHEMAS_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Schemas"
VALIDATE_EXAMPLES_SCRIPT = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "validation" / "validate_examples.py"


def _now_iso() -> str:
    """返回统一 UTC 时间。"""
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    """确保目录存在。"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path) -> Dict[str, Any]:
    """读取 JSON。"""
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Dict[str, Any]) -> Path:
    """写入 JSON。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write_text(path: Path, content: str) -> Path:
    """写入文本文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _abs_link(path: Path) -> str:
    """生成聊天面板可点击的绝对路径。"""
    return f"/{path.as_posix()}"


def _md_link(label: str, path: Path) -> str:
    """生成 Markdown 本地文件链接。"""
    return f"[{label}]({_abs_link(path)})"


def _assert(condition: bool, message: str) -> None:
    """统一断言。"""
    if not condition:
        raise AssertionError(message)


def _validate_with_schema(schema_name: str, payload: Dict[str, Any]) -> None:
    """按 schema 文件名校验 payload。"""
    schema = _read_json(SCHEMAS_DIR / schema_name)
    validator_cls = validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator_cls(schema).validate(payload)


def _prepare_and_save_auto(session: CompilerSession, stage_num: int) -> Dict[str, Any]:
    """执行自动阶段的 prepare + save。"""
    prepared = prepare_stage(session, stage_num)
    if prepared.get("status") != "ready_for_agent":
        raise RuntimeError(f"stage{stage_num}.prepare 失败: {json.dumps(prepared, ensure_ascii=False)}")

    if stage_num == 6:
        filled_data = {
            "build_ir": prepared["template"],
            "naming_resolution_log": prepared["input_context"]["naming_resolution_log"],
        }
    else:
        filled_data = prepared["template"]

    saved = save_stage(session, stage_num, filled_data)
    if saved.get("status") != "saved":
        raise RuntimeError(f"stage{stage_num}.save 失败: {json.dumps(saved, ensure_ascii=False)}")
    return prepared


def _validate_examples_strict() -> Dict[str, Any]:
    """执行 validate_examples.py --strict。"""
    result = subprocess.run(
        [sys.executable, str(VALIDATE_EXAMPLES_SCRIPT), "--strict"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            "validate_examples.py --strict 失败:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    summary: Dict[str, int] = {}
    summary_keys = {
        "Checked examples": "checked_examples",
        "Passed": "passed",
        "Failed": "failed",
        "Reference-only skipped": "reference_only_skipped",
        "Unmapped examples": "unmapped_examples",
        "Missing schema targets": "missing_schema_targets",
    }
    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        for prefix, target_key in summary_keys.items():
            if not line.startswith(prefix):
                continue
            _, _, value = line.partition(":")
            value = value.strip()
            if value.isdigit():
                summary[target_key] = int(value)

    return {
        "returncode": result.returncode,
        "summary": summary,
        "stderr": result.stderr.strip(),
    }


def _validate_gate_fast_mode_rules() -> Dict[str, Any]:
    """直接验证 Clarification Gate 的 fast_mode 风险分档规则。"""
    contract = {
        "contract_id": "task13-fast-mode-gate",
        "phase_scope": {"out_of_scope": []},
        "constraint_fields": {},
        "variant_fields": {},
        "baseline_capabilities": [],
        "gameplay_capabilities": [],
        "clarification_markers": [
            {
                "item_id": "cg-medium-safe",
                "topic": "medium safe default item",
                "suggested_decision": clarification_gate_stage.DECISION_ACCEPT_WITH_SAFE_DEFAULT,
                "risk_level": clarification_gate_stage.RISK_MEDIUM,
                "provisional_default": "medium-default",
                "reason": "medium marker for TASK 13 validation",
            },
            {
                "item_id": "cg-high-safe",
                "topic": "high safe default item",
                "suggested_decision": clarification_gate_stage.DECISION_ACCEPT_WITH_SAFE_DEFAULT,
                "risk_level": clarification_gate_stage.RISK_HIGH,
                "provisional_default": "high-default",
                "reason": "high marker for TASK 13 validation",
            },
            {
                "item_id": "cg-critical-safe",
                "topic": "critical safe default item",
                "suggested_decision": clarification_gate_stage.DECISION_ACCEPT_WITH_SAFE_DEFAULT,
                "risk_level": clarification_gate_stage.RISK_CRITICAL,
                "provisional_default": "critical-default",
                "reason": "critical marker for TASK 13 validation",
            },
        ],
    }

    report = clarification_gate_stage.create_clarification_gate_report(
        root_skill_contract=contract,
        fast_mode=True,
        run_id="task13-fast-mode-gate",
    )
    item_map = {item["item_id"]: item for item in report["items"]}
    blocking_ids = [item.get("item_id", "") for item in report.get("blocking_items", [])]

    medium_item = item_map["cg-medium-safe"]
    high_item = item_map["cg-high-safe"]
    critical_item = item_map["cg-critical-safe"]

    _assert(
        medium_item["decision"] == clarification_gate_stage.DECISION_ACCEPT_WITH_SAFE_DEFAULT,
        "medium 风险项在 fast_mode 下应保持 accept_with_safe_default",
    )
    _assert(
        medium_item.get("provisional_warning") is True,
        "medium 自动默认项必须带 provisional_warning=true",
    )
    _assert(
        high_item["decision"] == clarification_gate_stage.DECISION_CLARIFICATION_REQUIRED,
        "high 风险项不应在 fast_mode 下被自动默认",
    )
    _assert(
        critical_item["decision"] == clarification_gate_stage.DECISION_CLARIFICATION_REQUIRED,
        "critical 风险项不应在 fast_mode 下被自动默认",
    )
    _assert(
        "cg-critical-safe" in blocking_ids,
        "critical 风险项必须进入 blocking_items",
    )

    return {
        "report": report,
        "item_decisions": {
            "cg-medium-safe": {
                "decision": medium_item["decision"],
                "provisional_warning": medium_item.get("provisional_warning"),
            },
            "cg-high-safe": {
                "decision": high_item["decision"],
                "provisional_warning": high_item.get("provisional_warning"),
            },
            "cg-critical-safe": {
                "decision": critical_item["decision"],
                "blocking": "cg-critical-safe" in blocking_ids,
            },
        },
    }


def _validate_run_artifacts(run_dir: Path) -> None:
    """校验 fast_mode run 的核心产物 schema。"""
    schema_map = {
        "root_skill_contract.json": "root_skill_contract.schema.json",
        "clarification_gate_report.json": "clarification_gate_report.schema.json",
        "skill_graph.json": "skill_graph.schema.json",
        "design_space_report.json": "design_space_report.schema.json",
        "realization_candidates.json": "realization_candidates.schema.json",
        "converged_realization_pack.json": "converged_realization_pack.schema.json",
        "cross_review_report.json": "cross_review_report_v2.schema.json",
        "build_ir.json": "build_ir_v2.schema.json",
        "naming_resolution_log.json": "naming_resolution_log.schema.json",
        "reviewed_handoff_v3.json": "reviewed_handoff_v3.schema.json",
    }
    for file_name, schema_name in schema_map.items():
        path = run_dir / file_name
        _assert(path.exists(), f"缺少产物: {path}")
        _validate_with_schema(schema_name, _read_json(path))

    fragment_paths = sorted((run_dir / "skill_fragments").glob("*.json"))
    _assert(bool(fragment_paths), "fast_mode run 必须产出 skill_fragments")
    for fragment_path in fragment_paths:
        _validate_with_schema("skill_fragment_v2.schema.json", _read_json(fragment_path))


def _run_fast_mode_pipeline() -> Dict[str, Any]:
    """执行完整 fast_mode run。"""
    run_id = generate_run_id()
    run_dir = _ensure_dir(RUNS_ROOT / run_id)
    session = create_session(
        str(GDD_PATH),
        "phase11_task13_fast_mode_validation",
        str(run_dir),
        session_version="2.0",
        run_id=run_id,
        fast_mode=True,
    )
    session.save()

    for stage_num in [1, 2, 3, 4, 5, 6]:
        _prepare_and_save_auto(session, stage_num)

    stage7_prepared = prepare_stage(session, 7)
    if stage7_prepared.get("status") != "ready_for_agent":
        raise RuntimeError(f"stage7.prepare 失败: {json.dumps(stage7_prepared, ensure_ascii=False)}")

    handoff_result = assemble_handoff(session)
    if handoff_result.get("status") != "saved":
        raise RuntimeError(f"stage7.assemble 失败: {json.dumps(handoff_result, ensure_ascii=False)}")

    session = CompilerSession.load(run_dir / "session.json")
    clarification_gate_report = _read_json(run_dir / "clarification_gate_report.json")
    cross_review_report = _read_json(run_dir / "cross_review_report.json")
    design_space_report = _read_json(run_dir / "design_space_report.json")
    realization_candidates = _read_json(run_dir / "realization_candidates.json")
    converged_pack = _read_json(run_dir / "converged_realization_pack.json")
    fragments = [
        _read_json(path)
        for path in sorted((run_dir / "skill_fragments").glob("*.json"))
    ]

    metadata = build_run_metadata(
        session=session,
        clarification_gate_report=clarification_gate_report,
        cross_review_report=cross_review_report,
        completed_at=_now_iso(),
    )
    _write_json(run_dir / "metadata.json", metadata)

    _validate_run_artifacts(run_dir)

    _assert(metadata["fast_mode"] is True, "metadata.fast_mode 必须为 true")
    _assert(metadata["promotable"] is False, "fast_mode run 必须不可 promote")
    _assert(
        metadata.get("clarification_gate_policy") == "auto_default_low_medium_only",
        "fast_mode metadata 必须记录 clarification_gate_policy",
    )

    _assert(
        design_space_report.get("metadata", {}).get("entry_count") == 0,
        "fast_mode 下 design_space_report entry_count 应为 0",
    )
    _assert(
        realization_candidates.get("metadata", {}).get("entry_count") == 0,
        "fast_mode 下 realization_candidates entry_count 应为 0",
    )
    _assert(
        converged_pack.get("metadata", {}).get("entry_count") == 0,
        "fast_mode 下 converged_realization_pack entry_count 应为 0",
    )
    _assert(
        design_space_report.get("metadata", {}).get("fast_mode_skipped") is True,
        "design_space_report.metadata.fast_mode_skipped 必须为 true",
    )
    _assert(
        realization_candidates.get("metadata", {}).get("fast_mode_skipped") is True,
        "realization_candidates.metadata.fast_mode_skipped 必须为 true",
    )
    _assert(
        converged_pack.get("metadata", {}).get("fast_mode_skipped") is True,
        "converged_realization_pack.metadata.fast_mode_skipped 必须为 true",
    )

    completed_discovery_records = [
        record
        for record in converged_pack.get("metadata", {}).get("lifecycle_records", [])
        if record.get("allows_design_space_discovery") and record.get("status") == "completed"
    ]
    _assert(bool(completed_discovery_records), "fast_mode run 仍应覆盖 discovery-capable 节点")
    _assert(
        all(record.get("mode") == "fast_mode_default" for record in completed_discovery_records),
        "discovery-capable 节点在 fast_mode 下应以 fast_mode_default 完成",
    )

    fast_mode_fragments = [
        fragment
        for fragment in fragments
        if fragment.get("metadata", {}).get("fast_mode_default") is True
    ]
    _assert(bool(fast_mode_fragments), "至少应存在一个带 fast_mode_default 标记的 fragment")
    _assert(
        any(
            any(item.get("fast_mode_default") is True for item in fragment.get("design_decision_log", []))
            for fragment in fragments
        ),
        "fragment.design_decision_log 中至少应有一个 fast_mode_default=true",
    )

    promote_result = evidence_tools.evidence_create_batch(
        run_id,
        promoted_by="task13_validation",
        notes="TASK 13 fast_mode should reject promote",
    )
    _assert(
        promote_result.get("status") != "success",
        "TASK 12 promote 工具必须拒绝 fast_mode run",
    )

    cleanup_policy = evidence_tools.DEFAULT_CLEANUP_POLICY
    _assert(
        cleanup_policy.get("fast_mode_runs", {}).get("policy") == "keep_latest_n",
        "fast_mode cleanup policy 应为 keep_latest_n",
    )

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "metadata": metadata,
        "clarification_gate_report": clarification_gate_report,
        "design_space_report": design_space_report,
        "realization_candidates": realization_candidates,
        "converged_realization_pack": converged_pack,
        "fragments": fragments,
        "promote_reject": promote_result,
        "cleanup_policy": cleanup_policy,
    }


def _build_heuristic_fixture_run() -> Dict[str, Any]:
    """创建 heuristic_fallback 最小夹具并验证不可 promote。"""
    run_id = generate_run_id()
    run_dir = _ensure_dir(RUNS_ROOT / run_id)
    session_payload = {
        "session_id": f"fixture-{run_id}",
        "created_at": _now_iso(),
        "gdd_path": str(GDD_PATH),
        "target_phase": "phase11_task13_heuristic_fixture",
        "output_dir": str(run_dir),
        "current_stage": 7,
        "stage_outputs": {},
        "status": "completed",
        "session_version": "2.0",
        "fast_mode": False,
        "run_id": run_id,
        "generator_provider": "heuristic_fallback",
    }
    metadata_payload = {
        "run_id": run_id,
        "session_id": session_payload["session_id"],
        "session_version": "2.0",
        "fast_mode": False,
        "generator_provider": "heuristic_fallback",
        "created_at": session_payload["created_at"],
        "completed_at": _now_iso(),
        "status": "completed",
        "pipeline_stages_completed": [1, 2, 3, 4, 5, 6, 7],
        "constraint_violations": 0,
        "provisional_items": [],
        "clarification_gate_policy": "formal_mode_keep_high_risk_questions",
        "promotable": False,
        "output_dir": str(run_dir),
    }
    _write_json(run_dir / "session.json", session_payload)
    _write_json(run_dir / "metadata.json", metadata_payload)

    session = CompilerSession.load(run_dir / "session.json")
    _assert(session.is_promotable is False, "heuristic_fallback session.is_promotable 必须为 false")

    promote_result = evidence_tools.evidence_create_batch(
        run_id,
        promoted_by="task13_validation",
        notes="TASK 13 heuristic fallback should reject promote",
    )
    _assert(
        promote_result.get("status") != "success",
        "heuristic_fallback run 必须不可 promote",
    )

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "session": session_payload,
        "metadata": metadata_payload,
        "promote_reject": promote_result,
    }


def main() -> int:
    """脚本主入口。"""
    _ensure_dir(REPORT_ROOT)
    _ensure_dir(OUTPUT_ROOT)

    report_path = REPORT_ROOT / "task13_phase11_fast_mode_validation.md"
    summary_path = OUTPUT_ROOT / "task13_fast_mode_summary.json"
    gate_report_path = OUTPUT_ROOT / "task13_fast_mode_gate_report.json"

    gate_validation = _validate_gate_fast_mode_rules()
    _write_json(gate_report_path, gate_validation["report"])

    fast_mode_run = _run_fast_mode_pipeline()
    heuristic_fixture = _build_heuristic_fixture_run()
    strict_result = _validate_examples_strict()

    summary_payload = {
        "task": "TASK 13",
        "validated_at": _now_iso(),
        "gate_validation": gate_validation["item_decisions"],
        "fast_mode_run": {
            "run_id": fast_mode_run["run_id"],
            "promotable": fast_mode_run["metadata"]["promotable"],
            "clarification_gate_policy": fast_mode_run["metadata"]["clarification_gate_policy"],
            "generator_provider": fast_mode_run["metadata"].get("generator_provider"),
            "stage4_entry_count": {
                "design_space": fast_mode_run["design_space_report"]["metadata"]["entry_count"],
                "candidates": fast_mode_run["realization_candidates"]["metadata"]["entry_count"],
                "converged": fast_mode_run["converged_realization_pack"]["metadata"]["entry_count"],
            },
        },
        "heuristic_fixture": {
            "run_id": heuristic_fixture["run_id"],
            "promotable": heuristic_fixture["metadata"]["promotable"],
            "generator_provider": heuristic_fixture["metadata"]["generator_provider"],
        },
        "validate_examples": strict_result,
    }
    _write_json(summary_path, summary_payload)

    run_dir = Path(fast_mode_run["run_dir"])
    heuristic_dir = Path(heuristic_fixture["run_dir"])
    report_lines = [
        "# TASK 13 Phase 11 Fast Mode Validation",
        "",
        "## Summary",
        "",
        "- fast_mode session 已完成 Stage 1-7 执行，并写入不可 promote 的 run metadata。",
        "- Clarification Gate fast_mode 规则已验证：medium 可自动默认但带 warning，high/critical 不会被偷偷默认。",
        "- Stage 4 在 fast_mode 下被显式跳过，三类聚合产物 entry_count 均为 0，并带 `fast_mode_skipped=true`。",
        "- fragment 已带 `fast_mode_default` 标记，且 TASK 12 的 promote 工具会拒绝 fast_mode run。",
        "- `generator_provider = heuristic_fallback` 的 run 也已验证不可 promote。",
        "- `validate_examples.py --strict` 已通过。",
        "",
        "## Evidence",
        "",
        f"- 验收报告：{_md_link('task13_phase11_fast_mode_validation.md', report_path)}",
        f"- 验收摘要：{_md_link('task13_fast_mode_summary.json', summary_path)}",
        f"- Gate 验证报告：{_md_link('task13_fast_mode_gate_report.json', gate_report_path)}",
        f"- fast_mode session：{_md_link('session.json', run_dir / 'session.json')}",
        f"- fast_mode metadata：{_md_link('metadata.json', run_dir / 'metadata.json')}",
        f"- fast_mode clarification：{_md_link('clarification_gate_report.json', run_dir / 'clarification_gate_report.json')}",
        f"- fast_mode design_space：{_md_link('design_space_report.json', run_dir / 'design_space_report.json')}",
        f"- fast_mode candidates：{_md_link('realization_candidates.json', run_dir / 'realization_candidates.json')}",
        f"- fast_mode converged：{_md_link('converged_realization_pack.json', run_dir / 'converged_realization_pack.json')}",
        f"- fast_mode handoff：{_md_link('reviewed_handoff_v3.json', run_dir / 'reviewed_handoff_v3.json')}",
        f"- heuristic fixture session：{_md_link('session.json', heuristic_dir / 'session.json')}",
        f"- heuristic fixture metadata：{_md_link('metadata.json', heuristic_dir / 'metadata.json')}",
        "",
        "## Validation Checks",
        "",
        f"- fast_mode run_id: `{fast_mode_run['run_id']}`",
        f"- fast_mode promotable: `{fast_mode_run['metadata']['promotable']}`",
        f"- fast_mode clarification_gate_policy: `{fast_mode_run['metadata']['clarification_gate_policy']}`",
        f"- design_space entry_count: `{fast_mode_run['design_space_report']['metadata']['entry_count']}`",
        f"- realization_candidates entry_count: `{fast_mode_run['realization_candidates']['metadata']['entry_count']}`",
        f"- converged entry_count: `{fast_mode_run['converged_realization_pack']['metadata']['entry_count']}`",
        f"- fast_mode promote reject: `{fast_mode_run['promote_reject'].get('errors', [])}`",
        f"- heuristic fixture run_id: `{heuristic_fixture['run_id']}`",
        f"- heuristic promote reject: `{heuristic_fixture['promote_reject'].get('errors', [])}`",
        (
            "- validate_examples.py --strict: "
            f"`checked={strict_result['summary'].get('checked_examples', 0)}`, "
            f"`passed={strict_result['summary'].get('passed', 0)}`, "
            f"`failed={strict_result['summary'].get('failed', 0)}`"
        ),
        "",
        "## Gate Decisions",
        "",
        f"- medium: `{json.dumps(gate_validation['item_decisions']['cg-medium-safe'], ensure_ascii=False)}`",
        f"- high: `{json.dumps(gate_validation['item_decisions']['cg-high-safe'], ensure_ascii=False)}`",
        f"- critical: `{json.dumps(gate_validation['item_decisions']['cg-critical-safe'], ensure_ascii=False)}`",
        "",
        "## Cleanup Policy",
        "",
        f"- fast_mode_runs.policy: `{fast_mode_run['cleanup_policy']['fast_mode_runs']['policy']}`",
        f"- fast_mode_runs.default_keep_count: `{fast_mode_run['cleanup_policy']['fast_mode_runs']['default_keep_count']}`",
        "",
    ]
    _write_text(report_path, "\n".join(report_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
