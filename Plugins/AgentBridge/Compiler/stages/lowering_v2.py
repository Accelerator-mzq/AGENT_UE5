"""
Lowering v2 — Stage 6 (v2.0)

职责：
  将 Cross-Review 审查通过的 reviewed_dynamic_spec_tree 下沉为 Build IR v2。
  四阶段管线：
    Phase A: Normalization — 归一化 family、消解别名
    Phase B: Dependency Closure — 按 Skill Graph 检查依赖闭合
    Phase C: Static Capability Binding — 绑定 Static Base + GDD-First 命名
    Phase D: Build IR Generation — 生成构建意图 + 验证点 + naming_resolution_log

输入：
  - cross_review_report v2（Stage 5 输出，含 reviewed_dynamic_spec_tree）
  - root_skill_contract（Constraint Fields 不可变更）
  - skill_graph（依赖关系）
  - StaticBase/vocabulary/ — 静态词表
  - StaticBase/lowering_maps/ — 语义→引擎映射表

输出：
  - build_ir v2（含 build_steps + validation_ir + lowering_report）
  - naming_resolution_log（sidecar, 每个 build step 的命名审计）

明确禁止：
  - 不允许修改 Constraint Field 值
  - 不允许误下沉 Phase 2+ 功能
  - Lowering 不再重新理解 GDD，只翻译已审查的 spec tree
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Phase A: Normalization
# ---------------------------------------------------------------------------

# family 别名映射（常见拼写或旧命名 -> 标准名）
FAMILY_ALIASES: Dict[str, str] = {
    "start_screen": "start_screen_spec",
    "main_menu": "main_menu_spec",
    "settings": "settings_spec",
    "pause_menu": "pause_menu_spec",
    "results": "results_spec",
    "hud": "hud_spec",
}


def _normalize_spec_tree(spec_tree: Dict[str, Any]) -> Dict[str, Any]:
    """归一化 family 名称、消解别名。"""
    normalized: Dict[str, Any] = {}
    for family, spec in spec_tree.items():
        canonical = FAMILY_ALIASES.get(family, family)
        normalized[canonical] = spec
    return normalized


# ---------------------------------------------------------------------------
# Phase B: Dependency Closure
# ---------------------------------------------------------------------------

def _check_dependency_closure(
    spec_tree: Dict[str, Any],
    skill_graph: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """检查 spec tree 覆盖的 families 是否满足 Skill Graph 的依赖关系。"""
    warnings: List[Dict[str, Any]] = []

    # 从 skill_graph 中提取 dependency 边
    nodes = {n["instance_id"]: n for n in skill_graph.get("nodes", [])}
    for edge in skill_graph.get("edges", []):
        if edge.get("type") != "dependency":
            continue
        from_node = nodes.get(edge.get("from", ""))
        to_node = nodes.get(edge.get("to", ""))
        if not from_node or not to_node:
            continue
        # 如果 to 节点有 spec 但 from 节点没有，说明依赖缺失
        # 这里使用 instance_id 做近似匹配
        from_id = from_node.get("instance_id", "")
        to_id = to_node.get("instance_id", "")
        if from_id not in spec_tree and to_id in spec_tree:
            warnings.append({
                "type": "dependency_gap",
                "from": from_id,
                "to": to_id,
                "message": f"依赖源 '{from_id}' 在 spec tree 中缺失，但被依赖方 '{to_id}' 存在",
            })

    return warnings


# ---------------------------------------------------------------------------
# Phase C: Static Capability Binding + GDD-First 命名
# ---------------------------------------------------------------------------

# GDD-First 四层命名优先级对应的 tier
NAMING_TIERS = ["gdd_explicit", "gdd_style", "project_convention", "default"]


def _resolve_name(
    family: str,
    spec: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
) -> Dict[str, Any]:
    """
    为单个 family 解析 GDD-First 命名。
    返回 naming_resolution_log 条目。
    """
    # 检查 root_skill_contract 中是否有 GDD 显式命名
    gdd_naming = root_skill_contract.get("naming_hints", {})
    constraint_fields = root_skill_contract.get("constraint_fields", {})

    # Tier 1: GDD 显式命名
    if family in gdd_naming:
        return {
            "family": family,
            "resolved": gdd_naming[family],
            "tier": "gdd_explicit",
            "evidence": f"Root Skill Contract naming_hints['{family}']",
        }

    # Tier 2: GDD 风格推导（从 constraint 中推断）
    for field_path, cdef in constraint_fields.items():
        if family in field_path:
            name_hint = cdef.get("naming_hint")
            if name_hint:
                return {
                    "family": family,
                    "resolved": name_hint,
                    "tier": "gdd_style",
                    "evidence": f"Constraint '{field_path}' naming_hint",
                }

    # Tier 3: 项目规范（from spec 中的 naming_override）
    naming_override = spec.get("naming_override") if isinstance(spec, dict) else None
    if naming_override:
        return {
            "family": family,
            "resolved": naming_override,
            "tier": "project_convention",
            "evidence": "spec.naming_override",
        }

    # Tier 4: 默认
    default_name = family.replace("_spec", "").replace("_", " ").title().replace(" ", "")
    return {
        "family": family,
        "resolved": default_name,
        "tier": "default",
        "evidence": "自动从 family 名转换",
    }


# ---------------------------------------------------------------------------
# Phase D: Build IR Generation
# ---------------------------------------------------------------------------

# Build step 类型映射
FAMILY_TO_STEP_TYPE: Dict[str, str] = {
    "start_screen_spec": "widget_creation",
    "main_menu_spec": "widget_creation",
    "settings_spec": "widget_creation",
    "pause_menu_spec": "widget_creation",
    "results_spec": "widget_creation",
    "hud_spec": "widget_creation",
}


def _generate_build_step(
    family: str,
    spec: Dict[str, Any],
    naming_entry: Dict[str, Any],
    step_index: int,
) -> Dict[str, Any]:
    """为单个 family 生成 build step。"""
    resolved_name = naming_entry.get("resolved", family)
    step_type = FAMILY_TO_STEP_TYPE.get(family, "asset_creation")

    # 从 spec 中提取 required_elements（如果有的话）
    required_elements: List[str] = []
    if isinstance(spec, dict):
        required_elements = spec.get("required_elements", [])

    return {
        "step_id": f"build_{step_index:03d}_{family}",
        "step_type": step_type,
        "family": family,
        "target_name": resolved_name,
        "description": f"创建 {resolved_name} ({family})",
        "inputs": {
            "spec": spec,
            "naming": naming_entry,
        },
        "outputs": {
            "asset_path": f"/Game/UI/{resolved_name}",
            "blueprint_class": f"WBP_{resolved_name}" if step_type == "widget_creation" else resolved_name,
        },
        "required_elements": required_elements,
        "constraints_applied": [],
        "naming_resolution": naming_entry,
    }


def _generate_validation_points(
    build_steps: List[Dict[str, Any]],
    cross_review_report: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """基于 build steps 和 cross-review 结果生成验证点。"""
    validations: List[Dict[str, Any]] = []

    # 为每个 build step 生成基础验证
    for step in build_steps:
        validations.append({
            "validation_id": f"val_{step['step_id']}",
            "step_ref": step["step_id"],
            "check_type": "asset_exists",
            "description": f"验证 {step.get('target_name', '')} 资产已创建",
            "expected": True,
        })

        # 如果有 required_elements，为每个生成验证
        for elem in step.get("required_elements", []):
            validations.append({
                "validation_id": f"val_{step['step_id']}_{elem}",
                "step_ref": step["step_id"],
                "check_type": "element_present",
                "description": f"验证 {step.get('target_name', '')} 包含 {elem}",
                "expected": True,
            })

    # 从 cross-review 的 issues 中生成回归验证
    for issue in cross_review_report.get("issues_found", []):
        if issue.get("severity") == "error":
            validations.append({
                "validation_id": f"val_regression_{issue.get('check_type', 'unknown')}",
                "step_ref": issue.get("fragment_id", ""),
                "check_type": "regression_guard",
                "description": f"回归验证: {issue.get('message', '')}",
                "expected": False,
            })

    return validations


# ---------------------------------------------------------------------------
# 主入口：生成 Build IR v2 + naming_resolution_log
# ---------------------------------------------------------------------------

def create_build_ir_v2(
    cross_review_report: Dict[str, Any],
    root_skill_contract: Dict[str, Any],
    skill_graph: Dict[str, Any],
    phase_scope: str,
) -> Dict[str, Any]:
    """
    Stage 6 v2.0: 生成 Build IR v2 + naming_resolution_log。

    输入: cross_review_report v2, root_skill_contract, skill_graph
    输出: dict 含 build_ir 和 naming_resolution_log 两个产物
    """
    review_id = cross_review_report.get("review_id", "")
    contract_id = root_skill_contract.get("contract_id", "")
    spec_tree = cross_review_report.get("reviewed_dynamic_spec_tree", {})

    # Phase A: Normalization
    normalized_tree = _normalize_spec_tree(spec_tree)

    # Phase B: Dependency Closure
    closure_warnings = _check_dependency_closure(normalized_tree, skill_graph)

    # Phase C + D: 对每个 family 生成命名解析 + build step
    naming_entries: List[Dict[str, Any]] = []
    build_steps: List[Dict[str, Any]] = []
    families_bound: List[str] = []
    families_partially_bound: List[str] = []
    unbound_requirements: List[str] = []

    for index, (family, spec) in enumerate(sorted(normalized_tree.items())):
        # 命名解析
        naming_entry = _resolve_name(family, spec, root_skill_contract)
        naming_entries.append(naming_entry)

        # Build step 生成
        step = _generate_build_step(family, spec, naming_entry, index + 1)
        build_steps.append(step)

        # 分类绑定状态
        if isinstance(spec, dict) and spec.get("realization_class") == "presence_only":
            families_bound.append(family)
        elif isinstance(spec, dict) and spec.get("required_elements"):
            families_bound.append(family)
        else:
            families_partially_bound.append(family)

    # 生成验证点
    validation_ir = _generate_validation_points(build_steps, cross_review_report)

    # 能力缺口
    capability_gaps: List[str] = []
    for gap in cross_review_report.get("capability_gap_list", []):
        if isinstance(gap, str):
            capability_gaps.append(gap)
        elif isinstance(gap, dict):
            capability_gaps.append(gap.get("description", str(gap)))

    # 依赖闭合 warning 也加入
    for w in closure_warnings:
        unbound_requirements.append(w.get("message", ""))

    # 构造 IR ID
    ir_id = f"ir.{contract_id.replace('rsc.', '')}" if contract_id else f"ir.build.{_now_iso()[:10]}"

    build_ir = {
        "ir_version": "2.0",
        "ir_id": ir_id,
        "source_review_id": review_id,
        "source_contract_id": contract_id,
        "phase_scope": phase_scope,
        "build_steps": build_steps,
        "validation_ir": validation_ir,
        "lowering_report": {
            "families_received": list(normalized_tree.keys()),
            "families_bound": families_bound,
            "families_partially_bound": families_partially_bound,
            "unbound_requirements": unbound_requirements,
            "capability_gaps": capability_gaps,
            "dependency_closure_warnings": closure_warnings,
        },
        "recovery_hints": [],
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.LoweringV2.v1",
            "phase_scope": phase_scope,
        },
    }

    # naming_resolution_log（sidecar 产物）
    naming_resolution_log = {
        "log_version": "1.0",
        "source_ir_id": ir_id,
        "entries": naming_entries,
        "summary": {
            "total": len(naming_entries),
            "by_tier": _count_by_tier(naming_entries),
        },
        "metadata": {
            "generated_at": _now_iso(),
            "generator": "AgentBridge.Compiler.LoweringV2.NamingResolver.v1",
        },
    }

    return {
        "build_ir": build_ir,
        "naming_resolution_log": naming_resolution_log,
    }


def _count_by_tier(entries: List[Dict[str, Any]]) -> Dict[str, int]:
    """统计各命名 tier 的计数。"""
    counts: Dict[str, int] = {}
    for entry in entries:
        tier = entry.get("tier", "unknown")
        counts[tier] = counts.get(tier, 0) + 1
    return counts
