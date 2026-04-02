"""
Phase 7 P1 收敛执行脚本。

固定职责：
1. 连续执行 3 轮 Phase 7 稳定性回归。
2. 为每一轮生成治理审计摘要。
3. 生成 JRPG pack 跨入口一致性报告。
4. 生成 Phase 7 归档前检查表与最终汇总。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_SCRIPTS_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PLUGIN_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SCRIPTS_DIR))

from bridge.project_config import get_dated_project_reports_dir
from compiler.handoff import build_handoff
from compiler.intake import read_gdd
from Plugins.AgentBridge.Skills.genre_packs._core import load_pack_manifest, load_pack_modules, resolve_active_pack
from Scripts.validation.phase7_governance_audit import (
    load_json_file,
    load_yaml_file,
    write_governance_audit_summary,
    build_jrpg_pack_consistency_payload,
    write_jrpg_pack_consistency_report,
    write_phase7_archive_preflight_checklist,
)


def main() -> int:
    """执行 Phase 7 P1 收敛序列。"""
    report_dir = Path(get_dated_project_reports_dir())
    report_dir.mkdir(parents=True, exist_ok=True)

    rounds: List[Dict[str, Any]] = []
    for round_index in range(1, 4):
        round_result = _run_single_round(round_index, report_dir)
        rounds.append(round_result)
        if round_result["status"] != "passed":
            break

    consistency_result = _run_jrpg_consistency_pass(report_dir, rounds)
    stability_summary = _write_stability_summary(report_dir, rounds, consistency_result)
    checklist_path = _write_archive_preflight(report_dir, rounds, consistency_result, stability_summary)

    print(f"PHASE7_STABILITY_SUMMARY={stability_summary['json_path']}")
    print(f"PHASE7_STABILITY_SUMMARY_MD={stability_summary['md_path']}")
    print(f"PHASE7_JRPG_CONSISTENCY={consistency_result.get('json_path', '')}")
    print(f"PHASE7_ARCHIVE_PREFLIGHT={checklist_path}")

    overall_passed = (
        all(round_entry["status"] == "passed" for round_entry in rounds)
        and len(rounds) == 3
        and consistency_result.get("overall_status") == "passed"
    )
    return 0 if overall_passed else 1


def _run_single_round(round_index: int, report_dir: Path) -> Dict[str, Any]:
    """执行单轮稳定性回归。"""
    round_label = f"phase7_p1_round{round_index}"
    commands = [
        {
            "name": "phase7_pytest",
            "command": [
                sys.executable,
                "-m",
                "pytest",
                "Plugins/AgentBridge/Tests/scripts/test_phase7_governance_and_jrpg.py",
                "--junitxml",
                str(report_dir / f"{round_label}_pytest.xml"),
            ],
        },
        {
            "name": "boardgame_greenfield_simulated",
            "command": [sys.executable, str(PROJECT_ROOT / "Scripts" / "run_greenfield_demo.py"), "simulated"],
        },
        {
            "name": "boardgame_brownfield_simulated",
            "command": [sys.executable, str(PROJECT_ROOT / "Scripts" / "run_brownfield_demo.py"), "simulated"],
        },
        {
            "name": "boardgame_playable_simulated",
            "command": [sys.executable, str(PROJECT_ROOT / "Scripts" / "run_boardgame_playable_demo.py"), "simulated"],
        },
        {
            "name": "jrpg_greenfield_simulated",
            "command": [
                sys.executable,
                str(PROJECT_ROOT / "Scripts" / "run_jrpg_turn_based_demo.py"),
                "simulated",
                "greenfield_bootstrap",
            ],
        },
        {
            "name": "jrpg_greenfield_smoke",
            "command": [
                sys.executable,
                str(PROJECT_ROOT / "Scripts" / "run_jrpg_turn_based_demo.py"),
                "bridge_rc_api",
                "greenfield_bootstrap",
            ],
        },
    ]

    round_entries: List[Dict[str, Any]] = []
    for command_entry in commands:
        round_entries.append(_run_command_with_reports(command_entry, report_dir, round_label))

    execution_entries = _build_governance_entries_from_round(round_entries)
    audit_summary = write_governance_audit_summary(
        str(report_dir),
        f"{round_label}_governance_audit",
        execution_entries,
    )

    round_status = (
        "passed"
        if all(entry["returncode"] == 0 for entry in round_entries) and audit_summary["overall_status"] == "passed"
        else "failed"
    )

    round_payload = {
        "round_index": round_index,
        "round_label": round_label,
        "generated_at": datetime.now().isoformat(),
        "commands": round_entries,
        "governance_audit": audit_summary,
        "status": round_status,
    }
    json_path = report_dir / f"{round_label}_summary.json"
    md_path = report_dir / f"{round_label}_summary.md"
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(round_payload, file, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as file:
        file.write(_render_round_markdown(round_payload))

    round_payload["json_path"] = str(json_path)
    round_payload["md_path"] = str(md_path)
    return round_payload


def _run_command_with_reports(command_entry: Dict[str, Any], report_dir: Path, round_label: str) -> Dict[str, Any]:
    """执行命令并收集本轮新生成的报告。"""
    name = command_entry["name"]
    command = command_entry["command"]
    before_reports = _snapshot_json_reports(report_dir)
    completed = subprocess.run(
        command,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    after_reports = _snapshot_json_reports(report_dir)
    new_reports = sorted(list(after_reports - before_reports), key=os.path.getmtime)

    log_path = report_dir / f"{round_label}_{name}.log"
    with open(log_path, "w", encoding="utf-8") as file:
        file.write(f"[command] {' '.join(command)}\n\n")
        file.write("[stdout]\n")
        file.write(completed.stdout or "")
        file.write("\n\n[stderr]\n")
        file.write(completed.stderr or "")

    return {
        "name": name,
        "command": command,
        "returncode": completed.returncode,
        "log_path": str(log_path),
        "new_reports": new_reports,
        "stdout_tail": (completed.stdout or "")[-1000:],
        "stderr_tail": (completed.stderr or "")[-1000:],
    }


def _build_governance_entries_from_round(
    round_entries: Iterable[Dict[str, Any]],
) -> List[Tuple[str, str, Dict[str, str] | None]]:
    """从单轮命令结果中提取治理审计输入。"""
    entries: List[Tuple[str, str, Dict[str, str] | None]] = []
    for entry in round_entries:
        report_prefix_map = {
            "boardgame_greenfield_simulated": ("execution_report_handoff.boardgame.prototype.", None),
            "boardgame_brownfield_simulated": ("execution_report_handoff.boardgame.prototype.", None),
            "boardgame_playable_simulated": (
                "execution_report_handoff.boardgame.prototype.",
                {
                    "phase6_runtime_smoke": "phase6_runtime_smoke_",
                    "phase6_runtime_acceptance": "phase6_runtime_acceptance_",
                },
            ),
            "jrpg_greenfield_simulated": ("execution_report_handoff.jrpg.prototype.", None),
            "jrpg_greenfield_smoke": (
                "execution_report_handoff.jrpg.prototype.",
                {
                    "phase7_jrpg_runtime_smoke": "phase7_jrpg_runtime_smoke_",
                    "phase7_jrpg_runtime_acceptance": "phase7_jrpg_runtime_acceptance_",
                },
            ),
        }
        if entry["name"] not in report_prefix_map:
            continue

        execution_prefix, extra_prefixes = report_prefix_map[entry["name"]]
        execution_report_path = _find_single_report(entry["new_reports"], execution_prefix)
        extra_report_paths = None
        if extra_prefixes:
            extra_report_paths = {
                report_name: _find_single_report(entry["new_reports"], prefix)
                for report_name, prefix in extra_prefixes.items()
            }
        entries.append((entry["name"], execution_report_path, extra_report_paths))
    return entries


def _run_jrpg_consistency_pass(report_dir: Path, rounds: List[Dict[str, Any]]) -> Dict[str, Any]:
    """补一轮 JRPG Brownfield 路径，并生成一致性报告。"""
    if not rounds:
        return {"overall_status": "failed", "error": "没有可用的稳定性轮次结果"}

    latest_round = rounds[-1]
    if latest_round["status"] != "passed":
        return {"overall_status": "failed", "error": "最后一轮稳定性回归未通过"}

    brownfield_entry = _run_command_with_reports(
        {
            "name": "jrpg_brownfield_simulated",
            "command": [
                sys.executable,
                str(PROJECT_ROOT / "Scripts" / "run_jrpg_turn_based_demo.py"),
                "simulated",
                "brownfield_expansion",
            ],
        },
        report_dir,
        "phase7_p1_consistency",
    )
    if brownfield_entry["returncode"] != 0:
        return {
            "overall_status": "failed",
            "error": f"JRPG Brownfield consistency 命令失败: {brownfield_entry['log_path']}",
        }

    latest_greenfield_execution = _extract_round_report(
        latest_round,
        "jrpg_greenfield_simulated",
        "execution_report_handoff.jrpg.prototype.",
    )
    latest_smoke_report = _extract_round_report(
        latest_round,
        "jrpg_greenfield_smoke",
        "phase7_jrpg_runtime_smoke_",
    )
    brownfield_execution = _find_single_report(
        brownfield_entry["new_reports"],
        "execution_report_handoff.jrpg.prototype.",
    )

    greenfield_handoff = _load_approved_handoff_from_execution_report(latest_greenfield_execution)
    brownfield_handoff = _load_approved_handoff_from_execution_report(brownfield_execution)
    smoke_report = load_json_file(latest_smoke_report)
    smoke_handoff = load_yaml_file(smoke_report.get("approved_handoff_path", ""))

    design_input = read_gdd(str(PROJECT_ROOT / "ProjectInputs" / "GDD" / "jrpg_turn_based_v1.md"))
    router_results = {
        "greenfield": resolve_active_pack(
            design_input=design_input,
            routing_context=greenfield_handoff.get("routing_context", {}),
        ),
        "brownfield": resolve_active_pack(
            design_input=design_input,
            routing_context=brownfield_handoff.get("routing_context", {}),
        ),
        "smoke": resolve_active_pack(
            design_input=design_input,
            routing_context=smoke_handoff.get("routing_context", {}),
        ),
    }

    manifest_path = smoke_handoff.get("metadata", {}).get("skill_pack_manifest", "")
    pack_manifest = load_pack_manifest(manifest_path)
    pack_modules = load_pack_modules(pack_manifest)
    payload = build_jrpg_pack_consistency_payload(
        greenfield_handoff=greenfield_handoff,
        brownfield_handoff=brownfield_handoff,
        smoke_handoff=smoke_handoff,
        router_results=router_results,
        pack_modules=pack_modules,
    )
    written = write_jrpg_pack_consistency_report(
        str(report_dir),
        "phase7_jrpg_pack_consistency_2026-04-02",
        payload,
    )
    written["brownfield_log_path"] = brownfield_entry["log_path"]
    return written


def _write_stability_summary(
    report_dir: Path,
    rounds: List[Dict[str, Any]],
    consistency_result: Dict[str, Any],
) -> Dict[str, str]:
    """写出三轮稳定性总汇。"""
    payload = {
        "report_type": "phase7_p1_stability_summary",
        "generated_at": datetime.now().isoformat(),
        "round_count": len(rounds),
        "rounds": rounds,
        "jrpg_pack_consistency": consistency_result,
        "overall_status": "passed"
        if len(rounds) == 3
        and all(round_entry["status"] == "passed" for round_entry in rounds)
        and consistency_result.get("overall_status") == "passed"
        else "failed",
    }
    json_path = report_dir / "phase7_p1_stability_summary_2026-04-02.json"
    md_path = report_dir / "phase7_p1_stability_summary_2026-04-02.md"
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)
    with open(md_path, "w", encoding="utf-8") as file:
        file.write(_render_stability_markdown(payload))
    return {"json_path": str(json_path), "md_path": str(md_path), "overall_status": payload["overall_status"]}


def _write_archive_preflight(
    report_dir: Path,
    rounds: List[Dict[str, Any]],
    consistency_result: Dict[str, Any],
    stability_summary: Dict[str, str],
) -> str:
    """写出归档前检查表。"""
    checklist_items = [
        (
            "三轮 Phase 7 稳定性回归全部通过",
            len(rounds) == 3 and all(round_entry["status"] == "passed" for round_entry in rounds),
            stability_summary["md_path"],
        ),
        (
            "每轮治理审计摘要均通过",
            all(round_entry["governance_audit"]["overall_status"] == "passed" for round_entry in rounds),
            rounds[-1]["governance_audit"]["md_path"] if rounds else "",
        ),
        (
            "JRPG pack 跨入口一致性报告通过",
            consistency_result.get("overall_status") == "passed",
            consistency_result.get("md_path", ""),
        ),
        (
            "E2E-35 与 E2E-36 已从单次通过升级为连续稳定通过",
            len(rounds) == 3 and all(round_entry["status"] == "passed" for round_entry in rounds),
            stability_summary["json_path"],
        ),
    ]
    return write_phase7_archive_preflight_checklist(
        str(report_dir),
        "phase7_archive_preflight_checklist_2026-04-02",
        checklist_items,
    )


def _snapshot_json_reports(report_dir: Path) -> set[str]:
    """获取当前报告目录下全部 JSON 文件快照。"""
    return {str(path) for path in report_dir.glob("*.json")}


def _find_single_report(report_paths: Iterable[str], prefix: str) -> str:
    """按前缀寻找唯一报告文件。"""
    matches = [report_path for report_path in report_paths if Path(report_path).name.startswith(prefix)]
    if len(matches) != 1:
        raise RuntimeError(f"报告前缀匹配不唯一: prefix={prefix}, matches={matches}")
    return matches[0]


def _extract_round_report(round_result: Dict[str, Any], entry_name: str, prefix: str) -> str:
    """从单轮结果里按命令名和前缀提取报告。"""
    for command_entry in round_result.get("commands", []):
        if command_entry["name"] == entry_name:
            return _find_single_report(command_entry["new_reports"], prefix)
    raise RuntimeError(f"未找到命令结果: {entry_name}")


def _load_approved_handoff_from_execution_report(execution_report_path: str) -> Dict[str, Any]:
    """根据 execution_report 回溯对应的 approved handoff。"""
    execution_report = load_json_file(execution_report_path)
    handoff_id = execution_report.get("source_handoff_id", "")
    approved_path = PROJECT_ROOT / "ProjectState" / "Handoffs" / "approved" / f"{handoff_id}.yaml"
    return load_yaml_file(str(approved_path))


def _render_round_markdown(payload: Dict[str, Any]) -> str:
    """渲染单轮结果 Markdown。"""
    lines = [
        f"# {payload['round_label']} 汇总",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 总状态：{payload['status']}",
        f"- 治理审计：{payload['governance_audit']['md_path']}",
        "",
    ]
    for command_entry in payload.get("commands", []):
        lines.append(f"## {command_entry['name']}")
        lines.append("")
        lines.append(f"- returncode：{command_entry['returncode']}")
        lines.append(f"- log：{command_entry['log_path']}")
        lines.append(f"- new_reports：{len(command_entry['new_reports'])}")
        lines.append("")
    return "\n".join(lines)


def _render_stability_markdown(payload: Dict[str, Any]) -> str:
    """渲染稳定性总汇 Markdown。"""
    lines = [
        "# Phase 7 P1 稳定性收敛汇总",
        "",
        f"- 生成时间：{payload['generated_at']}",
        f"- 总轮次：{payload['round_count']}",
        f"- 总状态：{payload['overall_status']}",
        f"- JRPG 一致性报告：{payload['jrpg_pack_consistency'].get('md_path', '')}",
        "",
    ]
    for round_entry in payload.get("rounds", []):
        lines.append(f"## {round_entry['round_label']}")
        lines.append("")
        lines.append(f"- 状态：{round_entry['status']}")
        lines.append(f"- 审计摘要：{round_entry['governance_audit']['md_path']}")
        lines.append(f"- 单轮汇总：{round_entry['md_path']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(main())
