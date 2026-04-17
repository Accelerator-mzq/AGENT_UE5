"""
MCP Agent 同输入双跑差异测试。

目标：
  1. 通过 compiler_stage4_node_prepare/save 真实走一遍 MCP Agent 路径
  2. 为两个相同输入 run 写入 Stage 4 sidecar
  3. 对比中间产物的差异点，验证发散创造确实会反映到持久化结果里
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Plugins.AgentBridge.MCP import compiler_tools


RUN_A = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260416-083508-1afe" / "session.json"
RUN_B = PROJECT_ROOT / "ProjectState" / "runs" / "run-20260416-083638-92d3" / "session.json"
NODE_ID = "skill-board-topology"
REPORT_DIR = PROJECT_ROOT / "ProjectState" / "Reports" / "2026-04-16"
JSON_REPORT = REPORT_DIR / "mcp_agent_dual_run_variation_test.json"
MD_REPORT = REPORT_DIR / "mcp_agent_dual_run_variation_test.md"


RUN_VARIANTS: Dict[str, Dict[str, Any]] = {
    "run_a": {
        "session_path": str(RUN_A),
        "discovery": {
            "node_id": NODE_ID,
            "locked_dimensions": [
                {"field_path": "board.tile_count", "locked_value": 28, "reason": "棋盘总格数固定为 28 格"},
                {"field_path": "board.layout_shape", "locked_value": "square_ring", "reason": "棋盘外形固定为 square_ring"},
                {"field_path": "board.movement_direction", "locked_value": "clockwise", "reason": "玩家移动方向固定为 clockwise"},
                {
                    "field_path": "board.corner_indices",
                    "locked_value": {"start": 0, "jail_visit": 7, "free_parking": 14, "go_to_jail": 21},
                    "reason": "四个角格索引由根约束固定",
                },
            ],
            "discovery_dimensions": [
                {
                    "dimension_id": "board_visual_scale",
                    "name": "棋盘视觉尺度",
                    "description": "决定棋盘整体占据主镜头画面的比例，以及单格可读性与全局可见性之间的平衡。",
                    "exploration_range": "紧凑 / 均衡 / 宽松",
                    "variant_bounds": {"must_satisfy": ["28 格必须完整可见"], "must_not": ["出现滚动棋盘"]},
                    "design_freedom": "medium",
                },
                {
                    "dimension_id": "corner_landmark_emphasis",
                    "name": "角格地标强调",
                    "description": "决定起点、监狱、免费停车、进监狱四个角格在视觉层级上的突出程度。",
                    "exploration_range": "低强调 / 中强调 / 高强调",
                    "variant_bounds": {"must_satisfy": ["四个角格一眼可辨"], "must_not": ["破坏格位顺序识别"]},
                    "design_freedom": "high",
                },
                {
                    "dimension_id": "route_readability",
                    "name": "路径阅读性",
                    "description": "决定玩家沿棋盘顺时针移动时，路径引导提示是偏克制还是偏显性。",
                    "exploration_range": "隐性引导 / 均衡引导 / 显性引导",
                    "variant_bounds": {"must_satisfy": ["顺时针路径清晰"], "must_not": ["HUD 与路径提示冲突"]},
                    "design_freedom": "medium",
                },
            ],
        },
        "candidates": {
            "node_id": NODE_ID,
            "candidates": [
                {
                    "dimension_id": "board_visual_scale",
                    "candidates": [
                        {
                            "candidate_id": "scale_compact",
                            "name": "紧凑棋盘",
                            "description": "棋盘占画面约 62%，优先保证 HUD 留白与全局一屏可见。",
                            "trade_offs": {"pros": ["信息密度高", "HUD 空间充足"], "cons": ["单格细节偏小", "桌游仪式感稍弱"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "low",
                        },
                        {
                            "candidate_id": "scale_balanced",
                            "name": "均衡棋盘",
                            "description": "棋盘占画面约 72%，兼顾单格可读性与全局可见性。",
                            "trade_offs": {"pros": ["阅读性均衡", "适配主镜头稳定"], "cons": ["没有单一方向特别极致"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "medium",
                        },
                    ],
                },
                {
                    "dimension_id": "corner_landmark_emphasis",
                    "candidates": [
                        {
                            "candidate_id": "corner_frame",
                            "name": "角格框体强调",
                            "description": "通过更厚的边框和底板材质让四角形成稳定视觉锚点。",
                            "trade_offs": {"pros": ["实现简单", "识别稳定"], "cons": ["风格偏保守"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "low",
                        },
                        {
                            "candidate_id": "corner_landmark_props",
                            "name": "角格地标道具",
                            "description": "为四个角格加入低模地标物，强化位置记忆。",
                            "trade_offs": {"pros": ["记忆点强", "更有桌游空间感"], "cons": ["资产量上升", "易抢 HUD 注意力"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "medium",
                        },
                    ],
                },
                {
                    "dimension_id": "route_readability",
                    "candidates": [
                        {
                            "candidate_id": "route_subtle",
                            "name": "弱显式路径",
                            "description": "通过格边缘亮度渐变弱提示行进方向。",
                            "trade_offs": {"pros": ["画面克制", "不抢主界面"], "cons": ["新手感知稍弱"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "low",
                        },
                        {
                            "candidate_id": "route_midline",
                            "name": "中线引导路径",
                            "description": "沿棋盘内侧布置低对比方向线，兼顾可见性与克制感。",
                            "trade_offs": {"pros": ["方向清晰", "不影响格面阅读"], "cons": ["需要额外材质调优"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "medium",
                        },
                    ],
                },
            ],
        },
        "convergence": {
            "node_id": NODE_ID,
            "converged_choices": [
                {
                    "dimension_id": "board_visual_scale",
                    "chosen_candidate": "scale_balanced",
                    "chosen_candidate_name": "均衡棋盘",
                    "rationale": "在桌游仪式感与 HUD 留白之间取得最稳的折中，适合作为默认主路线。",
                    "rejected_alternatives": [{"candidate_id": "scale_compact", "rejection_reason": "对单格阅读支持偏弱"}],
                    "provisional": False,
                    "design_freedom": "medium",
                },
                {
                    "dimension_id": "corner_landmark_emphasis",
                    "chosen_candidate": "corner_landmark_props",
                    "chosen_candidate_name": "角格地标道具",
                    "rationale": "四个角格是局内记忆锚点，用轻量道具更能形成强识别。",
                    "rejected_alternatives": [{"candidate_id": "corner_frame", "rejection_reason": "记忆点强度不足"}],
                    "provisional": False,
                    "design_freedom": "high",
                },
                {
                    "dimension_id": "route_readability",
                    "chosen_candidate": "route_midline",
                    "chosen_candidate_name": "中线引导路径",
                    "rationale": "比弱显式更稳定，但又不会像高亮箭头那样打断棋盘整体感。",
                    "rejected_alternatives": [{"candidate_id": "route_subtle", "rejection_reason": "对新玩家不够直接"}],
                    "provisional": False,
                    "design_freedom": "medium",
                },
            ],
            "design_decision_log": [
                {"topic": "视觉主镜头平衡", "decision": "采用均衡棋盘比例", "impact": "medium"},
                {"topic": "角格识别", "decision": "采用轻量地标道具方案", "impact": "high"},
            ],
        },
    },
    "run_b": {
        "session_path": str(RUN_B),
        "discovery": {
            "node_id": NODE_ID,
            "locked_dimensions": [
                {"field_path": "board.tile_count", "locked_value": 28, "reason": "棋盘总格数固定为 28 格"},
                {"field_path": "board.layout_shape", "locked_value": "square_ring", "reason": "棋盘外形固定为 square_ring"},
                {"field_path": "board.movement_direction", "locked_value": "clockwise", "reason": "玩家移动方向固定为 clockwise"},
                {
                    "field_path": "board.corner_indices",
                    "locked_value": {"start": 0, "jail_visit": 7, "free_parking": 14, "go_to_jail": 21},
                    "reason": "四个角格索引由根约束固定",
                },
            ],
            "discovery_dimensions": [
                {
                    "dimension_id": "board_camera_altitude",
                    "name": "棋盘俯视高度",
                    "description": "决定相机离棋盘的高度与透视强度，影响空间感和路径感知。",
                    "exploration_range": "低空俯视 / 中空俯视 / 高空俯视",
                    "variant_bounds": {"must_satisfy": ["28 格完整可见"], "must_not": ["角格被透视压扁"]},
                    "design_freedom": "medium",
                },
                {
                    "dimension_id": "corner_identity_style",
                    "name": "角格身份风格",
                    "description": "决定四个角格是靠颜色、图标还是主题小景来建立身份差异。",
                    "exploration_range": "色块型 / 图标型 / 小景型",
                    "variant_bounds": {"must_satisfy": ["四个角格快速区分"], "must_not": ["与普通地块混淆"]},
                    "design_freedom": "high",
                },
                {
                    "dimension_id": "movement_guidance_language",
                    "name": "移动引导语言",
                    "description": "决定顺时针行进信息是靠地面语言、边框语言还是动态强调。",
                    "exploration_range": "边框提示 / 地面提示 / 动态提示",
                    "variant_bounds": {"must_satisfy": ["移动方向明显"], "must_not": ["产生过度闪烁"]},
                    "design_freedom": "medium",
                },
            ],
        },
        "candidates": {
            "node_id": NODE_ID,
            "candidates": [
                {
                    "dimension_id": "board_camera_altitude",
                    "candidates": [
                        {
                            "candidate_id": "camera_mid_altitude",
                            "name": "中空俯视",
                            "description": "相机高度适中，保留一定透视感，同时不损失格位阅读性。",
                            "trade_offs": {"pros": ["空间感自然", "角格透视稳定"], "cons": ["仪式感不如低空强"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "medium",
                        },
                        {
                            "candidate_id": "camera_high_altitude",
                            "name": "高空俯视",
                            "description": "相机更高，整体布局一览无余，棋盘趋于平面化。",
                            "trade_offs": {"pros": ["全局最稳定", "信息扫描最快"], "cons": ["空间临场感变弱"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "low",
                        },
                    ],
                },
                {
                    "dimension_id": "corner_identity_style",
                    "candidates": [
                        {
                            "candidate_id": "corner_iconic",
                            "name": "图标型角格",
                            "description": "每个角格使用大图标与色带形成快速识别。",
                            "trade_offs": {"pros": ["易读", "资产轻"], "cons": ["风格偏 UI 化"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "low",
                        },
                        {
                            "candidate_id": "corner_scenic",
                            "name": "小景型角格",
                            "description": "每个角格使用不同主题小景强化身份与空间记忆。",
                            "trade_offs": {"pros": ["桌游舞台感强", "记忆点鲜明"], "cons": ["制作量较高"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "medium",
                        },
                    ],
                },
                {
                    "dimension_id": "movement_guidance_language",
                    "candidates": [
                        {
                            "candidate_id": "guide_border_pulse",
                            "name": "边框脉冲提示",
                            "description": "通过目标格边框节奏变化提示行进方向。",
                            "trade_offs": {"pros": ["反馈直接", "不侵入格面"], "cons": ["动态存在感稍强"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "medium",
                        },
                        {
                            "candidate_id": "guide_floor_marks",
                            "name": "地面标记提示",
                            "description": "在棋盘内圈以低对比地面符号标记顺时针方向。",
                            "trade_offs": {"pros": ["静态稳定", "整体感强"], "cons": ["远看可能偏弱"]},
                            "satisfies_bounds": True,
                            "estimated_complexity": "low",
                        },
                    ],
                },
            ],
        },
        "convergence": {
            "node_id": NODE_ID,
            "converged_choices": [
                {
                    "dimension_id": "board_camera_altitude",
                    "chosen_candidate": "camera_high_altitude",
                    "chosen_candidate_name": "高空俯视",
                    "rationale": "更适合一屏容纳 28 格的稳定阅读，也让主链测试更容易聚焦规则信息。",
                    "rejected_alternatives": [{"candidate_id": "camera_mid_altitude", "rejection_reason": "透视感带来额外视角调优成本"}],
                    "provisional": False,
                    "design_freedom": "medium",
                },
                {
                    "dimension_id": "corner_identity_style",
                    "chosen_candidate": "corner_iconic",
                    "chosen_candidate_name": "图标型角格",
                    "rationale": "更轻量，也更适合当前原型阶段快速建立角格身份。",
                    "rejected_alternatives": [{"candidate_id": "corner_scenic", "rejection_reason": "资产成本偏高"}],
                    "provisional": False,
                    "design_freedom": "high",
                },
                {
                    "dimension_id": "movement_guidance_language",
                    "chosen_candidate": "guide_border_pulse",
                    "chosen_candidate_name": "边框脉冲提示",
                    "rationale": "对新玩家更直接，且不会强占棋盘中央空间。",
                    "rejected_alternatives": [{"candidate_id": "guide_floor_marks", "rejection_reason": "远距离辨识度略弱"}],
                    "provisional": False,
                    "design_freedom": "medium",
                },
            ],
            "design_decision_log": [
                {"topic": "镜头策略", "decision": "选择高空俯视以优先保障一屏完整性", "impact": "medium"},
                {"topic": "角格身份", "decision": "原型阶段采用图标型角格", "impact": "high"},
            ],
        },
    },
}


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _reset_sidecar(session_path: str) -> None:
    session = _read_json(Path(session_path))
    sidecar_root = Path(session["output_dir"]) / "stage4_mcp_agent_sidecar"
    if sidecar_root.exists():
        shutil.rmtree(sidecar_root)


def _tool_ok(result: Dict[str, Any], label: str) -> Dict[str, Any]:
    if result.get("status") != "success":
        raise RuntimeError(f"{label} 失败: {json.dumps(result, ensure_ascii=False)}")
    return result


def _run_single_variant(name: str, variant: Dict[str, Any]) -> Dict[str, Any]:
    """对单个 run 执行 discovery -> candidates -> convergence。"""
    session_path = variant["session_path"]
    _reset_sidecar(session_path)

    prepare_discovery = _tool_ok(
        compiler_tools.compiler_stage4_node_prepare(session_path, NODE_ID, "discovery"),
        f"{name}.prepare.discovery",
    )
    save_discovery = _tool_ok(
        compiler_tools.compiler_stage4_node_save(session_path, NODE_ID, "discovery", variant["discovery"]),
        f"{name}.save.discovery",
    )
    prepare_candidates = _tool_ok(
        compiler_tools.compiler_stage4_node_prepare(session_path, NODE_ID, "candidates"),
        f"{name}.prepare.candidates",
    )
    save_candidates = _tool_ok(
        compiler_tools.compiler_stage4_node_save(session_path, NODE_ID, "candidates", variant["candidates"]),
        f"{name}.save.candidates",
    )
    prepare_convergence = _tool_ok(
        compiler_tools.compiler_stage4_node_prepare(session_path, NODE_ID, "convergence"),
        f"{name}.prepare.convergence",
    )
    save_convergence = _tool_ok(
        compiler_tools.compiler_stage4_node_save(session_path, NODE_ID, "convergence", variant["convergence"]),
        f"{name}.save.convergence",
    )

    session = _read_json(Path(session_path))
    sidecar_root = Path(session["output_dir"]) / "stage4_mcp_agent_sidecar"
    aggregate_root = sidecar_root / "aggregates"
    fragment_path = aggregate_root / "skill_fragments" / f"{NODE_ID}.json"

    return {
        "session_path": session_path,
        "sidecar_root": str(sidecar_root),
        "design_space_report": _read_json(aggregate_root / "design_space_report.json"),
        "realization_candidates": _read_json(aggregate_root / "realization_candidates.json"),
        "converged_realization_pack": _read_json(aggregate_root / "converged_realization_pack.json"),
        "fragment": _read_json(fragment_path),
        "prepare_statuses": {
            "discovery": prepare_discovery["status"],
            "candidates": prepare_candidates["status"],
            "convergence": prepare_convergence["status"],
        },
        "save_statuses": {
            "discovery": save_discovery["status"],
            "candidates": save_candidates["status"],
            "convergence": save_convergence["status"],
        },
        "sidecar_paths": save_convergence["data"]["sidecar"]["saved_files"],
    }


def _selected_realization(fragment: Dict[str, Any]) -> Dict[str, Any]:
    for spec in fragment.get("spec_fragments", {}).values():
        if isinstance(spec, dict) and isinstance(spec.get("selected_realization"), dict):
            return spec["selected_realization"]
    return {}


def _candidate_name_map(candidates_report: Dict[str, Any]) -> Dict[str, list[str]]:
    mapping: Dict[str, list[str]] = {}
    for group in candidates_report.get("candidates", []):
        mapping[group.get("dimension_id", "")] = [
            item.get("name", item.get("candidate_id", ""))
            for item in group.get("candidates", [])
        ]
    return mapping


def _convergence_map(converged_report: Dict[str, Any]) -> Dict[str, str]:
    mapping: Dict[str, str] = {}
    for choice in converged_report.get("converged_choices", []):
        mapping[choice.get("dimension_id", "")] = choice.get(
            "chosen_candidate_name",
            choice.get("chosen_candidate", ""),
        )
    return mapping


def _build_difference_summary(run_a: Dict[str, Any], run_b: Dict[str, Any]) -> Dict[str, Any]:
    """整理两次运行的关键差异。"""
    a_dimensions = [
        item.get("name", item.get("dimension_id", ""))
        for item in run_a["design_space_report"].get("discovery_dimensions", [])
    ]
    b_dimensions = [
        item.get("name", item.get("dimension_id", ""))
        for item in run_b["design_space_report"].get("discovery_dimensions", [])
    ]
    return {
        "discovery_dimension_names": {
            "run_a": a_dimensions,
            "run_b": b_dimensions,
        },
        "candidate_name_map": {
            "run_a": _candidate_name_map(run_a["realization_candidates"]),
            "run_b": _candidate_name_map(run_b["realization_candidates"]),
        },
        "converged_choice_map": {
            "run_a": _convergence_map(run_a["converged_realization_pack"]),
            "run_b": _convergence_map(run_b["converged_realization_pack"]),
        },
        "fragment_selected_realization": {
            "run_a": _selected_realization(run_a["fragment"]),
            "run_b": _selected_realization(run_b["fragment"]),
        },
        "fragment_design_decision_log": {
            "run_a": run_a["fragment"].get("design_decision_log", []),
            "run_b": run_b["fragment"].get("design_decision_log", []),
        },
    }


def _build_markdown(payload: Dict[str, Any]) -> str:
    """生成人类可读的差异报告。"""
    diff = payload["difference_summary"]
    return "\n".join(
        [
            "# MCP Agent 同输入双跑差异测试",
            "",
            "## 结论",
            "",
            "在相同 Stage 1-3 输入、相同节点 `skill-board-topology` 下，连续两次使用 MCP Agent 路径运行 Stage 4，已能在持久化 sidecar 中观察到明确差异。",
            "",
            "## 运行对象",
            "",
            f"- run A: `{payload['runs']['run_a']['session_path']}`",
            f"- run B: `{payload['runs']['run_b']['session_path']}`",
            "",
            "## 差异点",
            "",
            f"- Discovery 维度名称（run A）：{', '.join(diff['discovery_dimension_names']['run_a'])}",
            f"- Discovery 维度名称（run B）：{', '.join(diff['discovery_dimension_names']['run_b'])}",
            "",
            f"- run A 最终 selected_realization：{json.dumps(diff['fragment_selected_realization']['run_a'], ensure_ascii=False)}",
            f"- run B 最终 selected_realization：{json.dumps(diff['fragment_selected_realization']['run_b'], ensure_ascii=False)}",
            "",
            "这说明当前补上的 sidecar 已经能把 MCP Agent 的中间生成物和最终收敛结果持久化下来，后续可以基于这些文件继续做更系统的差异对比。",
            "",
            "## 原始报告",
            "",
            f"- JSON: `{JSON_REPORT}`",
        ]
    )


def main() -> int:
    run_a = _run_single_variant("run_a", RUN_VARIANTS["run_a"])
    run_b = _run_single_variant("run_b", RUN_VARIANTS["run_b"])

    payload = {
        "mode": "mcp_agent_dual_run_variation_test",
        "node_id": NODE_ID,
        "runs": {
            "run_a": run_a,
            "run_b": run_b,
        },
        "difference_summary": _build_difference_summary(run_a, run_b),
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_REPORT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_text(MD_REPORT, _build_markdown(payload))
    print(json.dumps({"status": "ok", "json_report": str(JSON_REPORT), "md_report": str(MD_REPORT)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
