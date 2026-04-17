"""TASK 12：Run Compare / Promote 治理工具验收脚本。"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft7Validator


PROJECT_ROOT = Path(__file__).resolve().parents[4]
PLUGIN_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge"
MCP_DIR = PLUGIN_DIR / "MCP"

if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

import evidence_tools  # noqa: E402


REPORT_DATE = "2026-04-16"
REPORT_ROOT = PROJECT_ROOT / "ProjectState" / "Reports" / REPORT_DATE
OUTPUT_ROOT = REPORT_ROOT / "task12_validation_outputs"
RUNS_ROOT = PROJECT_ROOT / "ProjectState" / "runs"
BATCHES_ROOT = PROJECT_ROOT / "ProjectState" / "batches"

PROMOTABLE_RUN_A = "run-20260416-142558-7f47"
PROMOTABLE_RUN_B = "run-20260416-142757-47c4"
FAST_MODE_FIXTURE_RUN = "run-20260416-230000-fa57"
FAILED_FIXTURE_RUN = "run-20260416-230100-fa58"


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def _write_json(path: Path, payload) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    return path


def _validate_schema(payload: dict, schema_path: Path) -> None:
    schema = _load_json(schema_path)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda item: list(item.path))
    if not errors:
        return

    details = []
    for error in errors:
        location = ".".join(str(part) for part in error.path) or "<root>"
        details.append(f"{location}: {error.message}")
    raise AssertionError("schema 校验失败: " + " | ".join(details))


def _md_link(label: str, path: Path) -> str:
    return f"[{label}](/D:/{path.resolve().as_posix().split('D:/', 1)[-1]})"


def _assert_success(result: dict, label: str) -> dict:
    if result.get("status") != "success":
        raise AssertionError(f"{label} 失败: {result}")
    return result


def _assert_failed(result: dict, label: str) -> dict:
    if result.get("status") == "success":
        raise AssertionError(f"{label} 应失败但返回 success: {result}")
    return result


def _build_fixture_run(run_id: str, *, fast_mode: bool, status: str, execution_log: bool) -> Path:
    """创建最小治理验证夹具 run。"""
    run_dir = _ensure_dir(RUNS_ROOT / run_id)
    metadata = {
        "run_id": run_id,
        "session_id": f"fixture-{run_id}",
        "session_version": "2.0",
        "fast_mode": fast_mode,
        "generator_provider": "mcp_agent",
        "created_at": "2026-04-16T23:00:00+00:00",
        "completed_at": "2026-04-16T23:05:00+00:00",
        "status": status,
        "pipeline_stages_completed": [1, 2, 3, 4, 5, 6, 7],
        "constraint_violations": 0,
        "provisional_items": [],
        "promotable": not fast_mode and status == "completed",
        "output_dir": str(run_dir),
    }
    session = {
        "session_id": f"fixture-{run_id}",
        "created_at": "2026-04-16T23:00:00+00:00",
        "gdd_path": str(PROJECT_ROOT / "ProjectInputs" / "GDD" / "GDD_MonopolyGame.md"),
        "target_phase": "phase11_task12_validation_fixture",
        "output_dir": str(run_dir),
        "current_stage": 7,
        "stage_outputs": {},
        "status": status,
        "session_version": "2.0",
        "fast_mode": fast_mode,
        "run_id": run_id,
        "generator_provider": "mcp_agent",
    }
    _write_json(run_dir / "metadata.json", metadata)
    _write_json(run_dir / "session.json", session)
    if execution_log:
        _write_json(
            run_dir / "execution_log.json",
            {
                "run_id": run_id,
                "status": status,
                "events": [
                    "fixture validation log kept for failed run retention check"
                ],
            },
        )
    return run_dir


def main() -> int:
    _ensure_dir(REPORT_ROOT)
    _ensure_dir(OUTPUT_ROOT)

    comparison_output_path = OUTPUT_ROOT / "run_comparison.json"
    report_path = REPORT_ROOT / "task12_phase11_run_governance_validation.md"

    # 1. Compare 两个 promotable run，并保存 comparison 产物。
    comparison_result = _assert_success(
        evidence_tools.evidence_compare_runs(
            PROMOTABLE_RUN_A,
            PROMOTABLE_RUN_B,
            output_path=str(comparison_output_path),
        ),
        "evidence_compare_runs",
    )
    comparison_payload = _load_json(comparison_output_path)
    _validate_schema(
        comparison_payload,
        PROJECT_ROOT / "Plugins" / "AgentBridge" / "Schemas" / "run_comparison.schema.json",
    )

    # 2. 创建 batch，并验证 manifest/promotion_report 落盘。
    create_batch_result = _assert_success(
        evidence_tools.evidence_create_batch(
            PROMOTABLE_RUN_A,
            promoted_by="task12_validation",
            notes="TASK 12 validation create_batch",
        ),
        "evidence_create_batch",
    )
    batch_a_manifest_path = PROJECT_ROOT / create_batch_result["data"]["manifest_path"]
    batch_a_manifest = _load_json(batch_a_manifest_path)
    _validate_schema(
        batch_a_manifest,
        PROJECT_ROOT / "Plugins" / "AgentBridge" / "Schemas" / "batch_manifest.schema.json",
    )

    # 3. 再 promote 另一个 run，验证 active batch 唯一性与治理指针。
    promote_result = _assert_success(
        evidence_tools.evidence_promote_run(
            PROMOTABLE_RUN_B,
            promoted_by="task12_validation",
            notes="TASK 12 validation promote_run",
            update_base_project=True,
        ),
        "evidence_promote_run",
    )
    batch_b_manifest_path = PROJECT_ROOT / promote_result["data"]["manifest_path"]
    batch_b_manifest = _load_json(batch_b_manifest_path)
    _validate_schema(
        batch_b_manifest,
        PROJECT_ROOT / "Plugins" / "AgentBridge" / "Schemas" / "batch_manifest.schema.json",
    )

    batch_a_manifest = _load_json(batch_a_manifest_path)
    batch_b_manifest = _load_json(batch_b_manifest_path)
    active_batch_pointer = _load_json(BATCHES_ROOT / "active_batch.json")
    current_promoted_pointer = _load_json(BATCHES_ROOT / "current_promoted_batch.json")

    if batch_a_manifest["active"] is not False:
        raise AssertionError("第一个 batch 在第二次 promote 后应被置为 inactive")
    if batch_b_manifest["active"] is not True:
        raise AssertionError("最新 promote 的 batch 应为 active")
    if active_batch_pointer.get("active_batch_id") != batch_b_manifest["batch_id"]:
        raise AssertionError("active_batch.json 未指向最新 active batch")
    if current_promoted_pointer.get("batch_id") != batch_b_manifest["batch_id"]:
        raise AssertionError("current_promoted_batch.json 未同步更新")

    tools_visible = True
    try:
        import tool_definitions  # noqa: WPS433
        import server  # noqa: WPS433

        for tool_name in ["evidence_compare_runs", "evidence_create_batch", "evidence_promote_run"]:
            if tool_name not in tool_definitions.ALL_TOOLS or tool_name not in server.TOOL_DISPATCH:
                tools_visible = False
                break
    except Exception:
        tools_visible = False

    # 4. fast_mode run promote 必须被拒绝。
    fast_mode_run_dir = _build_fixture_run(
        FAST_MODE_FIXTURE_RUN,
        fast_mode=True,
        status="completed",
        execution_log=False,
    )
    fast_mode_reject = _assert_failed(
        evidence_tools.evidence_create_batch(
            FAST_MODE_FIXTURE_RUN,
            promoted_by="task12_validation",
            notes="should reject fast_mode",
        ),
        "fast_mode promote rejection",
    )

    # 5. failed run 需要保留 execution_log。
    failed_run_dir = _build_fixture_run(
        FAILED_FIXTURE_RUN,
        fast_mode=False,
        status="failed",
        execution_log=True,
    )
    failed_reject = _assert_failed(
        evidence_tools.evidence_create_batch(
            FAILED_FIXTURE_RUN,
            promoted_by="task12_validation",
            notes="should reject failed run",
        ),
        "failed run promote rejection",
    )
    if not (failed_run_dir / "execution_log.json").exists():
        raise AssertionError("failed run 的 execution_log.json 应被保留")

    report_lines = [
        "# TASK 12 Phase 11 Run Governance Validation",
        "",
        "## Summary",
        "",
        "- `evidence_compare_runs` 已跑通，并生成结构化 comparison 产物。",
        "- `evidence_create_batch` 已跑通，可从 promotable run 创建 batch。",
        "- `evidence_promote_run` 已跑通，可创建 active batch 并更新治理层 baseline 指针。",
        "- fast_mode run promote 已明确拒绝。",
        "- failed run 的 `execution_log.json` 在拒绝 promote 后仍被保留。",
        "",
        "## Evidence",
        "",
        f"- Compare 输出：{_md_link('run_comparison.json', comparison_output_path)}",
        f"- Batch A manifest：{_md_link('manifest.json', batch_a_manifest_path)}",
        f"- Batch A report：{_md_link('promotion_report.json', batch_a_manifest_path.parent / 'promotion_report.json')}",
        f"- Batch B manifest：{_md_link('manifest.json', batch_b_manifest_path)}",
        f"- Batch B report：{_md_link('promotion_report.json', batch_b_manifest_path.parent / 'promotion_report.json')}",
        f"- active batch 指针：{_md_link('active_batch.json', BATCHES_ROOT / 'active_batch.json')}",
        f"- current promoted 指针：{_md_link('current_promoted_batch.json', BATCHES_ROOT / 'current_promoted_batch.json')}",
        f"- fast_mode fixture metadata：{_md_link('metadata.json', fast_mode_run_dir / 'metadata.json')}",
        f"- failed fixture execution_log：{_md_link('execution_log.json', failed_run_dir / 'execution_log.json')}",
        "",
        "## Checks",
        "",
        f"- comparison 六类差异字段齐全：`{list(comparison_payload['details'].keys())}`",
        f"- Batch A active 状态：`{batch_a_manifest['active']}`",
        f"- Batch B active 状态：`{batch_b_manifest['active']}`",
        f"- 当前 active batch：`{active_batch_pointer['active_batch_id']}`",
        f"- 3 个治理工具可见：`{tools_visible}`",
        f"- promote 后原始 run A 仍存在：`{(RUNS_ROOT / PROMOTABLE_RUN_A).exists()}`",
        f"- promote 后原始 run B 仍存在：`{(RUNS_ROOT / PROMOTABLE_RUN_B).exists()}`",
        f"- fast_mode 拒绝错误：`{fast_mode_reject['errors'][0]}`",
        f"- failed run 拒绝错误：`{failed_reject['errors'][0]}`",
        "",
        "## Notes",
        "",
        "- 当前 `evidence_promote_run` 的 Base Project 更新采用治理层 baseline 指针方式，不直接回写 `Source/` 或 `Content/`。",
        "- promote 后原始 run 目录未被删除。",
    ]
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "report_path": str(report_path),
                "comparison_output": str(comparison_output_path),
                "batch_a": batch_a_manifest["batch_id"],
                "batch_b": batch_b_manifest["batch_id"],
                "active_batch": active_batch_pointer["active_batch_id"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
