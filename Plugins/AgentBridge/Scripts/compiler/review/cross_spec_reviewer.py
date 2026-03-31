"""
Cross Spec Reviewer
执行 Phase 4 的最小静态审查。
"""

from typing import Any, Dict, List


def review_dynamic_spec_tree(
    design_input: Dict[str, Any],
    dynamic_spec_tree: Dict[str, Any],
    static_spec_context: Dict[str, Any],
    routing_context: Dict[str, Any],
) -> Dict[str, Any]:
    """对 dynamic spec tree 做最小但可判定的编译期审查。"""
    errors: List[str] = []
    warnings: List[str] = []
    capability_gaps = {
        "required_static_templates": [],
        "unresolved_refs": [],
        "unsupported_gdd_sections": [],
        "missing_patch_contracts": [],
        "unsupported_regression_checks": [],
    }

    loaded_specs = static_spec_context.get("loaded_specs", {})
    required_spec_ids = static_spec_context.get("required_spec_ids", [])

    for spec_id in required_spec_ids:
        if spec_id not in loaded_specs:
            capability_gaps["required_static_templates"].append(spec_id)
            errors.append(f"缺少必需静态基座: {spec_id}")

    actors = dynamic_spec_tree.get("scene_spec", {}).get("actors", [])
    _validate_actor_list(actors, errors)
    _validate_preview_pieces(design_input, actors, errors, capability_gaps)

    unsupported_sections = design_input.get("parsing_notes", {}).get("unsupported_sections", [])
    capability_gaps["unsupported_gdd_sections"].extend(unsupported_sections)

    if routing_context.get("mode") == "brownfield_expansion":
        capability_gaps["missing_patch_contracts"].append("Phase 4 尚未实现 Brownfield Patch Contract")
        capability_gaps["unsupported_regression_checks"].append("Phase 4 尚未实现 Brownfield Regression Contract")

    reviewed = len(errors) == 0
    review_notes = _build_review_notes(
        reviewed=reviewed,
        actor_count=len(actors),
        errors=errors,
        warnings=warnings,
    )

    return {
        "status": "reviewed" if reviewed else "blocked",
        "reviewed": reviewed,
        "reviewer": "AgentBridge.Compiler.CrossSpecReviewer.v0.4",
        "review_notes": review_notes,
        "errors": errors,
        "warnings": warnings,
        "capability_gaps": capability_gaps,
    }


def _validate_actor_list(actors: List[Dict[str, Any]], errors: List[str]) -> None:
    """检查 actor 列表的基础合法性。"""
    actor_names = []
    for actor in actors:
        actor_name = actor.get("actor_name", "")
        actor_class = actor.get("actor_class", "")
        transform = actor.get("transform", {})

        if not actor_name:
            errors.append("存在缺少 actor_name 的 Actor")
        actor_names.append(actor_name)

        if not isinstance(actor_class, str) or not actor_class.strip():
            errors.append(f"Actor {actor_name or '<unknown>'} 的 actor_class 为空")

        _validate_transform_triplet(actor_name, transform, errors)

    duplicate_names = sorted({name for name in actor_names if name and actor_names.count(name) > 1})
    for duplicate_name in duplicate_names:
        errors.append(f"Actor 名称重复: {duplicate_name}")


def _validate_transform_triplet(
    actor_name: str,
    transform: Dict[str, Any],
    errors: List[str],
) -> None:
    """检查 transform 是否为 3 维数值数组。"""
    for key in ["location", "rotation", "relative_scale3d"]:
        value = transform.get(key)
        if not isinstance(value, list) or len(value) != 3:
            errors.append(f"Actor {actor_name or '<unknown>'} 的 {key} 不是合法三元组")
            continue
        if not all(isinstance(item, (int, float)) for item in value):
            errors.append(f"Actor {actor_name or '<unknown>'} 的 {key} 含非数值字段")


def _validate_preview_pieces(
    design_input: Dict[str, Any],
    actors: List[Dict[str, Any]],
    errors: List[str],
    capability_gaps: Dict[str, List[str]],
) -> None:
    """检查示例棋子与 piece_catalog / preview_policy 是否一致。"""
    piece_catalog = design_input.get("piece_catalog", [])
    preview_policy = design_input.get("prototype_preview", {})
    piece_symbols = {piece.get("symbol"): piece for piece in piece_catalog}
    expected_counts = preview_policy.get("piece_counts", {}) if preview_policy.get("generate_preview") else {}

    actual_counts: Dict[str, int] = {}
    for actor in actors:
        actor_name = actor.get("actor_name", "")
        if not actor_name.startswith("Piece"):
            continue

        symbol = _extract_piece_symbol(actor_name)
        actual_counts[symbol] = actual_counts.get(symbol, 0) + 1

        if symbol not in piece_symbols:
            gap_message = f"Actor {actor_name} 引用了未声明的棋子类型 {symbol}"
            capability_gaps["unresolved_refs"].append(gap_message)
            errors.append(gap_message)

    if preview_policy.get("generate_preview", False):
        for symbol, expected_count in expected_counts.items():
            if actual_counts.get(symbol, 0) != int(expected_count):
                errors.append(
                    f"预览棋子数量不一致: {symbol} 期望 {expected_count}，实际 {actual_counts.get(symbol, 0)}"
                )
    elif any(actual_counts.values()):
        errors.append("GDD 显式要求不生成示例棋子，但 scene_spec 中仍存在预览棋子")


def _extract_piece_symbol(actor_name: str) -> str:
    """从 PieceX_1 这类命名中提取棋子符号。"""
    if "_" in actor_name:
        return actor_name.split("_", 1)[0].replace("Piece", "")
    return actor_name.replace("Piece", "")


def _build_review_notes(
    reviewed: bool,
    actor_count: int,
    errors: List[str],
    warnings: List[str],
) -> str:
    """生成简短审查摘要。"""
    if reviewed:
        return f"Cross-Spec Review 通过；生成 Actor {actor_count} 个，warnings={len(warnings)}。"
    return f"Cross-Spec Review 阻塞；errors={len(errors)}，warnings={len(warnings)}。"
