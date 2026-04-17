"""TASK 14：Baseline Domain Skill Template 全套验收脚本。"""

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

from Plugins.AgentBridge.Compiler.pipeline.session import create_session, generate_run_id  # noqa: E402
from Plugins.AgentBridge.Compiler.pipeline.pipeline_orchestrator import prepare_stage, save_stage  # noqa: E402
from Plugins.AgentBridge.Compiler.stages import domain_skill_runtime as dsr  # noqa: E402


REPORT_DATE = "2026-04-16"
REPORT_ROOT = PROJECT_ROOT / "ProjectState" / "Reports" / REPORT_DATE
OUTPUT_ROOT = REPORT_ROOT / "task14_validation_outputs"
RUNS_ROOT = PROJECT_ROOT / "ProjectState" / "runs"
SCHEMAS_DIR = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Schemas"
BASELINE_ROOT = PROJECT_ROOT / "Plugins" / "AgentBridge" / "SkillTemplates" / "baseline"
VALIDATE_EXAMPLES_SCRIPT = PROJECT_ROOT / "Plugins" / "AgentBridge" / "Scripts" / "validation" / "validate_examples.py"
GDD_PATH = PROJECT_ROOT / "ProjectInputs" / "GDD" / "GDD_MonopolyGame.md"

STANDARD_TEMPLATE_FILES = [
    "manifest.yaml",
    "system_prompt.md",
    "domain_prompt.md",
    "evaluator_prompt.md",
    "input_selector.yaml",
    "output_schema.json",
]

TEMPLATE_SPECS: Dict[str, Dict[str, Any]] = {
    "start_screen": {
        "template_id": "baseline.start_screen.presence_only",
        "realization_class": "presence_only",
        "instance_id": "skill-baseline-start-screen",
    },
    "main_menu": {
        "template_id": "baseline.main_menu.presence_only",
        "realization_class": "presence_only",
        "instance_id": "skill-baseline-main-menu",
    },
    "settings": {
        "template_id": "baseline.settings.presence_only",
        "realization_class": "presence_only",
        "instance_id": "skill-baseline-settings",
    },
    "pause": {
        "template_id": "baseline.pause.presence_only",
        "realization_class": "presence_only",
        "instance_id": "skill-baseline-pause",
    },
    "results": {
        "template_id": "baseline.results.presence_only",
        "realization_class": "presence_only",
        "instance_id": "skill-baseline-results",
    },
    "hud": {
        "template_id": "baseline.hud.realization_eligible",
        "realization_class": "realization_eligible",
        "instance_id": "skill-baseline-hud",
    },
}

EXPECTED_MISSING_TEMPLATES = {
    "baseline.input_foundation.presence_only",
    "baseline.audio_foundation.presence_only",
    "baseline.platform_foundation.clarification_gated",
}

PROJECT_SPECIFIC_MARKERS = [
    "monopoly",
    "boardwalk",
    "park place",
    "community chest",
    "free parking",
    "$1500",
]


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


def _read_text(path: Path) -> str:
    """读取文本。"""
    return path.read_text(encoding="utf-8")


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


def _load_yaml(path: Path) -> Dict[str, Any]:
    """读取 YAML。"""
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - 当前环境通常已安装 pyyaml
        raise RuntimeError("缺少 pyyaml，无法执行 TASK 14 验收。") from exc

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return data or {}


def _validate_with_schema(schema_name: str, payload: Dict[str, Any]) -> None:
    """按 schema 文件名校验 payload。"""
    schema = _read_json(SCHEMAS_DIR / schema_name)
    validator_cls = validators.validator_for(schema)
    validator_cls.check_schema(schema)
    validator_cls(schema).validate(payload)


def _prepare_and_save_auto(session, stage_num: int) -> Dict[str, Any]:
    """执行自动阶段的 prepare + save。"""
    prepared = prepare_stage(session, stage_num)
    if prepared.get("status") != "ready_for_agent":
        raise RuntimeError(f"stage{stage_num}.prepare 失败: {json.dumps(prepared, ensure_ascii=False)}")

    saved = save_stage(session, stage_num, prepared["template"])
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


def _validate_template_inventory() -> Dict[str, Any]:
    """校验 6 个 baseline 模板目录和内容约束。"""
    inventory: Dict[str, Any] = {}
    runtime_resolution: Dict[str, Any] = {}

    for template_name, spec in TEMPLATE_SPECS.items():
        template_dir = BASELINE_ROOT / template_name
        _assert(template_dir.is_dir(), f"缺少 baseline 模板目录: {template_dir}")

        file_map = {path.name: path for path in template_dir.iterdir() if path.is_file()}
        for file_name in STANDARD_TEMPLATE_FILES:
            _assert(file_name in file_map, f"{template_name} 缺少标准文件: {file_name}")

        manifest = _load_yaml(file_map["manifest.yaml"])
        input_selector = _load_yaml(file_map["input_selector.yaml"])
        output_schema = _read_json(file_map["output_schema.json"])
        system_prompt = _read_text(file_map["system_prompt.md"])
        domain_prompt = _read_text(file_map["domain_prompt.md"])
        evaluator_prompt = _read_text(file_map["evaluator_prompt.md"])

        _assert(manifest.get("template_id") == spec["template_id"], f"{template_name} template_id 不匹配")
        _assert(
            manifest.get("realization_class") == spec["realization_class"],
            f"{template_name} realization_class 不匹配",
        )

        prompts = dsr._resolve_template_prompts(spec["template_id"])
        _assert(prompts.get("system_prompt"), f"{template_name} system_prompt 运行时未能加载")
        _assert(prompts.get("domain_prompt"), f"{template_name} domain_prompt 运行时未能加载")
        _assert(prompts.get("evaluator_prompt"), f"{template_name} evaluator_prompt 运行时未能加载")
        runtime_resolution[spec["template_id"]] = {
            "resolved": True,
            "template_dir": str(template_dir),
        }

        combined_text = "\n".join(
            [
                json.dumps(manifest, ensure_ascii=False),
                json.dumps(input_selector, ensure_ascii=False),
                json.dumps(output_schema, ensure_ascii=False),
                system_prompt,
                domain_prompt,
                evaluator_prompt,
            ]
        ).lower()
        for marker in PROJECT_SPECIFIC_MARKERS:
            _assert(marker not in combined_text, f"{template_name} 含项目实例化数据标记: {marker}")

        content_checks: Dict[str, Any] = {}
        if template_name == "start_screen":
            enum_values = set(output_schema["properties"]["required_elements"]["items"]["enum"])
            _assert(
                {"project_identity_display", "user_interaction_trigger", "navigate_to_main_menu"}.issubset(enum_values),
                "start_screen 必须包含项目标识、用户交互触发、进入主菜单能力",
            )
            content_checks["required_elements"] = sorted(enum_values)
        elif template_name == "main_menu":
            enum_values = set(output_schema["properties"]["buttons"]["items"]["properties"]["button_id"]["enum"])
            _assert({"new_game", "settings", "quit"}.issubset(enum_values), "main_menu 必须包含 New Game / Settings / Quit")
            content_checks["buttons"] = sorted(enum_values)
        elif template_name == "settings":
            enum_values = set(output_schema["properties"]["required_controls"]["items"]["properties"]["control_id"]["enum"])
            expected_controls = {
                "master_volume_slider",
                "sfx_volume_slider",
                "window_mode_selector",
                "resolution_selector",
                "apply_button",
                "back_button",
            }
            _assert(expected_controls.issubset(enum_values), "settings 必须保留六项底线控件")
            content_checks["required_controls"] = sorted(enum_values)
        elif template_name == "pause":
            enum_values = set(output_schema["properties"]["buttons"]["items"]["properties"]["button_id"]["enum"])
            _assert({"resume", "settings", "quit_to_menu"}.issubset(enum_values), "pause 必须包含三个最低按钮")
            _assert(output_schema["properties"]["trigger_input"]["properties"]["key"]["default"] == "ESC", "pause 必须保留 ESC 入口")
            _assert(
                output_schema["properties"]["pause_state_management"]["properties"]["on_pause"]["default"] == "SetGamePaused(true)",
                "pause 必须保留 SetGamePaused(true)",
            )
            content_checks["buttons"] = sorted(enum_values)
        elif template_name == "results":
            _assert("Return to Menu" in domain_prompt, "results 必须包含 Return to Menu 能力")
            _assert(
                output_schema["properties"]["trigger"]["properties"]["method"]["default"] == "ShowResult",
                "results 必须包含 ShowResult() 触发入口",
            )
            content_checks["trigger_method"] = output_schema["properties"]["trigger"]["properties"]["method"]["default"]
        elif template_name == "hud":
            include_sections = set(input_selector.get("include_sections", []))
            _assert(
                {
                    "design_domains.turn_loop",
                    "design_domains.property_rules",
                    "design_domains.jail_rules",
                }.issubset(include_sections),
                "HUD 模板必须支持 gameplay 域输入",
            )
            _assert(
                "gameplay_coupling" in output_schema.get("required", []),
                "HUD output_schema 必须要求 gameplay_coupling",
            )
            content_checks["include_sections"] = sorted(include_sections)

        inventory[template_name] = {
            "template_id": spec["template_id"],
            "realization_class": spec["realization_class"],
            "files": sorted(file_map.keys()),
            "content_checks": content_checks,
        }

    return {
        "inventory": inventory,
        "runtime_resolution": runtime_resolution,
    }


def _run_stage4_baseline_validation() -> Dict[str, Any]:
    """生成一条新的 fast_mode run，用于校验 Skill Graph 与 Baseline Fragment。"""
    run_id = generate_run_id()
    run_dir = _ensure_dir(RUNS_ROOT / run_id)
    session = create_session(
        str(GDD_PATH),
        "phase11_task14_baseline_template_validation",
        str(run_dir),
        session_version="2.0",
        run_id=run_id,
        fast_mode=True,
    )
    session.save()

    for stage_num in [1, 2, 3, 4]:
        _prepare_and_save_auto(session, stage_num)

    skill_graph = _read_json(run_dir / "skill_graph.json")
    _validate_with_schema("skill_graph.schema.json", skill_graph)

    baseline_nodes = {
        node["instance_id"]: node
        for node in skill_graph.get("nodes", [])
        if node.get("domain_type") == "baseline"
    }
    implemented_sources: Dict[str, Any] = {}
    for template_name, spec in TEMPLATE_SPECS.items():
        node = baseline_nodes.get(spec["instance_id"])
        _assert(node is not None, f"skill_graph 缺少 baseline 节点: {spec['instance_id']}")
        _assert(node.get("template_id") == spec["template_id"], f"{spec['instance_id']} template_id 错误")
        _assert(
            node.get("template_source") == "plugin_skill_template",
            f"{spec['instance_id']} 应引用已存在的 plugin_skill_template",
        )
        implemented_sources[spec["instance_id"]] = {
            "template_id": node.get("template_id"),
            "template_source": node.get("template_source"),
        }

    missing_templates = set(skill_graph.get("metadata", {}).get("missing_baseline_templates", []))
    _assert(
        EXPECTED_MISSING_TEMPLATES.issubset(missing_templates),
        "skill_graph metadata 必须对未落地 baseline 模板给 warning",
    )

    fragment_dir = run_dir / "skill_fragments"
    fragment_checks: Dict[str, Any] = {}
    for template_name, spec in TEMPLATE_SPECS.items():
        fragment_path = fragment_dir / f"{spec['instance_id']}.json"
        _assert(fragment_path.exists(), f"缺少 Baseline Fragment: {fragment_path}")
        fragment = _read_json(fragment_path)
        _validate_with_schema("skill_fragment_v2.schema.json", fragment)
        for key in ["template_id", "status", "emitted_families", "spec_fragments", "assumptions", "confidence"]:
            _assert(key in fragment, f"{fragment_path.name} 缺少字段: {key}")
        _assert(fragment.get("template_id") == spec["template_id"], f"{fragment_path.name} template_id 不匹配")
        fragment_checks[spec["instance_id"]] = {
            "fragment_path": str(fragment_path),
            "template_id": fragment.get("template_id"),
            "status": fragment.get("status"),
            "emitted_families": fragment.get("emitted_families", []),
            "confidence": fragment.get("confidence", {}),
        }

    return {
        "run_id": run_id,
        "run_dir": str(run_dir),
        "implemented_sources": implemented_sources,
        "missing_baseline_templates": sorted(missing_templates),
        "fragment_checks": fragment_checks,
    }


def main() -> int:
    """脚本主入口。"""
    _ensure_dir(REPORT_ROOT)
    _ensure_dir(OUTPUT_ROOT)

    report_path = REPORT_ROOT / "task14_phase11_baseline_template_validation.md"
    summary_path = OUTPUT_ROOT / "task14_baseline_template_summary.json"

    template_validation = _validate_template_inventory()
    run_validation = _run_stage4_baseline_validation()
    strict_result = _validate_examples_strict()

    summary_payload = {
        "task": "TASK 14",
        "validated_at": _now_iso(),
        "template_inventory": template_validation["inventory"],
        "runtime_resolution": template_validation["runtime_resolution"],
        "skill_graph_validation": {
            "run_id": run_validation["run_id"],
            "implemented_sources": run_validation["implemented_sources"],
            "missing_baseline_templates": run_validation["missing_baseline_templates"],
        },
        "fragment_validation": run_validation["fragment_checks"],
        "validate_examples": strict_result,
    }
    _write_json(summary_path, summary_payload)

    run_dir = Path(run_validation["run_dir"])
    report_lines = [
        "# TASK 14 Phase 11 Baseline Template Validation",
        "",
        "## Summary",
        "",
        "- 6 个 Baseline Domain Skill Template 目录已校验通过，每个目录都包含 6 个标准文件。",
        "- Start Screen / Main Menu / Settings / Pause / Results / HUD 的内容底线已逐项校验。",
        "- HUD 模板已去除 Monopoly 项目实例化耦合名，模板目录未混入项目实例数据。",
        "- Skill Graph Planning 已按模板实际存在情况写入 `template_source`，已落地模板标记为 `plugin_skill_template`。",
        "- 未落地的 baseline template 已在 Skill Graph metadata 中给出 warning。",
        "- 新验证 run 已生成 Baseline Fragment，并验证结构字段齐全。",
        "- `validate_examples.py --strict` 已通过。",
        "",
        "## Evidence",
        "",
        f"- 验收报告：{_md_link('task14_phase11_baseline_template_validation.md', report_path)}",
        f"- 验收摘要：{_md_link('task14_baseline_template_summary.json', summary_path)}",
        f"- 验证 run skill_graph：{_md_link('skill_graph.json', run_dir / 'skill_graph.json')}",
        f"- Start Screen fragment：{_md_link('skill-baseline-start-screen.json', run_dir / 'skill_fragments' / 'skill-baseline-start-screen.json')}",
        f"- Main Menu fragment：{_md_link('skill-baseline-main-menu.json', run_dir / 'skill_fragments' / 'skill-baseline-main-menu.json')}",
        f"- Settings fragment：{_md_link('skill-baseline-settings.json', run_dir / 'skill_fragments' / 'skill-baseline-settings.json')}",
        f"- Pause fragment：{_md_link('skill-baseline-pause.json', run_dir / 'skill_fragments' / 'skill-baseline-pause.json')}",
        f"- Results fragment：{_md_link('skill-baseline-results.json', run_dir / 'skill_fragments' / 'skill-baseline-results.json')}",
        f"- HUD fragment：{_md_link('skill-baseline-hud.json', run_dir / 'skill_fragments' / 'skill-baseline-hud.json')}",
        "",
        "## Validation Checks",
        "",
        f"- run_id: `{run_validation['run_id']}`",
        f"- implemented template_source count: `{len(run_validation['implemented_sources'])}`",
        f"- missing baseline templates: `{json.dumps(run_validation['missing_baseline_templates'], ensure_ascii=False)}`",
        (
            "- validate_examples.py --strict: "
            f"`checked={strict_result['summary'].get('checked_examples', 0)}`, "
            f"`passed={strict_result['summary'].get('passed', 0)}`, "
            f"`failed={strict_result['summary'].get('failed', 0)}`"
        ),
        "",
        "## Implemented Templates",
        "",
    ]

    for template_name, data in template_validation["inventory"].items():
        report_lines.append(
            f"- `{template_name}` -> `{data['template_id']}` / `{data['realization_class']}` / files={len(data['files'])}"
        )

    report_lines.extend(
        [
            "",
            "## Skill Graph Template Sources",
            "",
        ]
    )
    for instance_id, data in run_validation["implemented_sources"].items():
        report_lines.append(
            f"- `{instance_id}` -> `{data['template_id']}` / `{data['template_source']}`"
        )

    _write_text(report_path, "\n".join(report_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
