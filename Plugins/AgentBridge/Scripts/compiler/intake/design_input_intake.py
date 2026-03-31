"""
Design Input Intake
读取项目层 GDD，提取 Phase 4 所需的结构化设计输入。
"""

import os
import re
from typing import Any, Dict, List, Optional


def read_gdd(gdd_path: str) -> Dict[str, Any]:
    """
    读取单个 GDD 文件并返回结构化设计输入。

    Args:
        gdd_path: GDD 文件路径

    Returns:
        结构化 design_input 字典
    """
    if not os.path.exists(gdd_path):
        raise FileNotFoundError(f"GDD 文件不存在: {gdd_path}")

    with open(gdd_path, "r", encoding="utf-8") as file:
        content = file.read()

    return build_design_input(content, gdd_path)


def read_gdd_from_directory(gdd_dir: str) -> Dict[str, Any]:
    """
    从目录读取 GDD。

    当前 Phase 4 仍以单个主 GDD 为主；如果目录中有多个 Markdown 文件，
    这里会按文件名排序后读取第一个文件，并把全部文件路径记录到 source_files。
    """
    if not os.path.isdir(gdd_dir):
        raise NotADirectoryError(f"GDD 目录不存在: {gdd_dir}")

    gdd_files = sorted(
        os.path.join(gdd_dir, file_name)
        for file_name in os.listdir(gdd_dir)
        if file_name.endswith(".md")
    )

    if not gdd_files:
        raise FileNotFoundError(f"GDD 目录中没有找到 .md 文件: {gdd_dir}")

    design_input = read_gdd(gdd_files[0])
    design_input["source_files"] = gdd_files
    return design_input


def build_design_input(content: str, source_file: str) -> Dict[str, Any]:
    """将 Markdown GDD 转成 Phase 4 结构化输入。"""
    game_type = extract_game_type(content)
    board = extract_board_spec(content)
    piece_catalog = extract_piece_catalog(content)
    rules = extract_rules(content)
    initial_layout = extract_initial_layout(content, board)
    prototype_preview = extract_prototype_preview(content, piece_catalog)
    technical_requirements = extract_technical_requirements(content)
    feature_tags = extract_feature_tags(game_type, board, rules, prototype_preview)
    parsing_notes = collect_parsing_notes(content)

    return {
        "game_type": game_type,
        "feature_tags": feature_tags,
        "board": board,
        "piece_catalog": piece_catalog,
        "rules": rules,
        "initial_layout": initial_layout,
        "prototype_preview": prototype_preview,
        "technical_requirements": technical_requirements,
        "scene_requirements": extract_scene_requirements(board, piece_catalog, prototype_preview),
        "raw_content": content,
        "source_file": source_file,
        "source_files": [source_file],
        "parsing_notes": parsing_notes,
    }


def extract_game_type(content: str) -> str:
    """从 GDD 内容提取游戏类型。"""
    normalized = content.lower()
    if "boardgame" in normalized or "棋盘游戏" in content or "棋盘" in content:
        return "boardgame"
    return "unknown"


def extract_board_spec(content: str) -> Dict[str, Any]:
    """解析棋盘规格。"""
    board_section = _extract_markdown_section(content, "棋盘")
    board_type = _extract_value_after_colon(board_section, "类型") or "grid_board"
    grid_size = _extract_first_pair(board_type) or _extract_first_pair(content) or [3, 3]
    cell_size = _extract_value_pair(board_section, "每格尺寸") or [100, 100]
    total_size = _extract_value_pair(board_section, "总尺寸") or [
        grid_size[0] * cell_size[0],
        grid_size[1] * cell_size[1],
    ]
    location = _extract_world_location(board_section) or [0.0, 0.0, 0.0]
    material = _extract_value_after_colon(board_section, "材质") or "DefaultBoardMaterial"

    return {
        "board_name": "Board",
        "board_type": board_type,
        "grid_size": grid_size,
        "cell_size_cm": cell_size,
        "total_size_cm": total_size,
        "location": [float(location[0]), float(location[1]), float(location[2])],
        "material": material,
    }


def extract_piece_catalog(content: str) -> List[Dict[str, Any]]:
    """解析棋子目录。"""
    piece_catalog: List[Dict[str, Any]] = []

    for symbol in ["X", "O"]:
        section = _extract_markdown_section(content, f"棋子 {symbol}")
        if not section:
            continue

        shape = _extract_value_after_colon(section, "形状") or "Cube"
        color = _extract_value_after_colon(section, "颜色") or "White"
        size_triplet = _extract_value_triplet(section, "尺寸")
        radius = _extract_single_number_after_key(section, "半径")
        if size_triplet:
            dimensions = size_triplet
        elif radius is not None:
            diameter = float(radius) * 2.0
            dimensions = [diameter, diameter, diameter]
        else:
            dimensions = [50.0, 50.0, 50.0]

        max_count = _extract_single_number_after_key(section, "数量")
        piece_catalog.append(
            {
                "piece_id": f"piece_{symbol.lower()}",
                "symbol": symbol,
                "display_name": symbol,
                "actor_name_prefix": f"Piece{symbol}",
                "shape": shape,
                "color": color,
                "dimensions_cm": [float(dimensions[0]), float(dimensions[1]), float(dimensions[2])],
                "max_count": int(max_count) if max_count is not None else 1,
                "actor_class": "/Script/Engine.StaticMeshActor",
            }
        )

    return piece_catalog


def extract_rules(content: str) -> Dict[str, Any]:
    """解析核心玩法与规则表达。"""
    gameplay_section = _extract_markdown_section(content, "核心玩法")
    rule_lines = _extract_bullet_lines(gameplay_section)

    turn_model = "turn_based" if any("回合" in line for line in rule_lines) else "unknown"
    victory_condition = ""
    for line in rule_lines:
        if "胜利条件" in line:
            victory_condition = line.replace("胜利条件：", "").strip()
            break

    return {
        "rule_summary": rule_lines,
        "turn_model": turn_model,
        "victory_condition": victory_condition or "未明确说明",
    }


def extract_initial_layout(content: str, board: Dict[str, Any]) -> Dict[str, Any]:
    """解析初始布局。"""
    layout_section = _extract_markdown_section(content, "初始场景布局")
    layout_lines = _extract_bullet_lines(layout_section)

    return {
        "board_location": board.get("location", [0.0, 0.0, 0.0]),
        "board_centered_at_origin": any("世界原点" in line for line in layout_lines),
        "initial_pieces": [],
        "starts_empty": any("空棋盘" in line for line in layout_lines),
        "spawn_policy": "dynamic" if any("动态生成" in line for line in layout_lines) else "static",
        "layout_notes": layout_lines,
    }


def extract_prototype_preview(content: str, piece_catalog: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    解析原型预览策略。

    规则：
    - GDD 明确写 0：不生成示例棋子
    - GDD 明确写数量：按 GDD
    - GDD 未写：默认 1 个 X + 1 个 O
    """
    preview_lines = [
        line.strip()
        for line in content.splitlines()
        if "示例棋子" in line or "预览棋子" in line
    ]
    piece_symbols = [piece.get("symbol") for piece in piece_catalog if piece.get("symbol")]
    default_counts = {symbol: 1 for symbol in piece_symbols[:2]}

    if not preview_lines:
        return {
            "generate_preview": bool(default_counts),
            "source": "default",
            "piece_counts": default_counts,
            "explicitly_defined": False,
            "raw_rule": "",
        }

    preview_line = preview_lines[0]
    normalized = preview_line.replace("：", ":")

    if re.search(r":\s*0\s*$", normalized) or "不生成" in preview_line or "无示例" in preview_line:
        return {
            "generate_preview": False,
            "source": "gdd_explicit_zero",
            "piece_counts": {symbol: 0 for symbol in piece_symbols},
            "explicitly_defined": True,
            "raw_rule": preview_line,
        }

    piece_counts: Dict[str, int] = {}

    # 支持 "X=2, O=1" / "X:2 O:1" 等写法
    for symbol, count_text in re.findall(r"([A-Za-z])\s*[:=]\s*(\d+)", normalized):
        piece_counts[symbol.upper()] = int(count_text)

    # 支持 "2 个 X" 这类写法
    for count_text, symbol in re.findall(r"(\d+)\s*个\s*([A-Za-z])", normalized):
        piece_counts[symbol.upper()] = int(count_text)

    if not piece_counts:
        piece_counts = default_counts
        source = "default"
        explicitly_defined = False
    else:
        source = "gdd_explicit_counts"
        explicitly_defined = True

    return {
        "generate_preview": any(count > 0 for count in piece_counts.values()),
        "source": source,
        "piece_counts": piece_counts,
        "explicitly_defined": explicitly_defined,
        "raw_rule": preview_line,
    }


def extract_technical_requirements(content: str) -> Dict[str, Any]:
    """解析技术需求。"""
    technical_section = _extract_markdown_section(content, "技术需求")
    technical_lines = _extract_bullet_lines(technical_section)

    engine_version = "UE5.5.4"
    for line in technical_lines:
        engine_match = re.search(r"UE\s*([0-9.]+)", line, re.IGNORECASE)
        if engine_match:
            engine_version = f"UE{engine_match.group(1)}"
            break

    actor_class = "/Script/Engine.StaticMeshActor"
    if any("StaticMeshActor" in line for line in technical_lines):
        actor_class = "/Script/Engine.StaticMeshActor"

    return {
        "target_engine_version": engine_version,
        "actor_class": actor_class,
        "requires_transform_operations": any("Transform" in line for line in technical_lines),
        "notes": technical_lines,
    }


def extract_feature_tags(
    game_type: str,
    board: Dict[str, Any],
    rules: Dict[str, Any],
    prototype_preview: Dict[str, Any],
) -> List[str]:
    """根据解析结果生成 feature tags。"""
    tags: List[str] = []

    if game_type:
        tags.append(game_type)

    if rules.get("turn_model") == "turn_based":
        tags.append("turn_based")

    grid_size = board.get("grid_size", [])
    if grid_size == [3, 3]:
        tags.append("grid_3x3")
    elif len(grid_size) == 2:
        tags.append(f"grid_{grid_size[0]}x{grid_size[1]}")

    if prototype_preview.get("generate_preview"):
        tags.append("prototype_preview")

    return tags


def extract_scene_requirements(
    board: Dict[str, Any],
    piece_catalog: List[Dict[str, Any]],
    prototype_preview: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """保留 Phase 3 的 scene_requirements 字段，同时升级为结构化摘要。"""
    return [
        {
            "requirement_type": "board",
            "grid_size": board.get("grid_size", []),
            "total_size_cm": board.get("total_size_cm", []),
        },
        {
            "requirement_type": "pieces",
            "piece_symbols": [piece.get("symbol") for piece in piece_catalog],
            "preview_policy": prototype_preview.get("source"),
        },
    ]


def collect_parsing_notes(content: str) -> Dict[str, Any]:
    """记录解析说明，供 review 阶段补充 capability gaps。"""
    supported_sections = ["游戏类型", "核心玩法", "场景需求", "初始场景布局", "技术需求"]
    found_sections = []
    for line in content.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped in supported_sections:
            found_sections.append(stripped)

    unsupported_sections = [
        section for section in found_sections if section not in supported_sections
    ]

    return {
        "supported_sections": supported_sections,
        "found_sections": found_sections,
        "unsupported_sections": unsupported_sections,
    }


def _extract_markdown_section(content: str, heading_name: str) -> str:
    """提取指定标题下的正文。"""
    lines = content.splitlines()
    collecting = False
    heading_level = 0
    section_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            current_level = len(stripped) - len(stripped.lstrip("#"))
            current_name = stripped.lstrip("#").strip()
            if collecting and current_level <= heading_level:
                break
            if current_name == heading_name:
                collecting = True
                heading_level = current_level
                continue

        if collecting:
            section_lines.append(line)

    return "\n".join(section_lines).strip()


def _extract_bullet_lines(section: str) -> List[str]:
    """提取 Markdown bullet 内容。"""
    lines: List[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith("-"):
            lines.append(stripped.lstrip("-").strip())
    return lines


def _extract_value_after_colon(section: str, field_name: str) -> str:
    """提取“字段：值”中的值。"""
    pattern = rf"{re.escape(field_name)}\s*[：:]\s*(.+)"
    match = re.search(pattern, section)
    return match.group(1).strip() if match else ""


def _extract_first_pair(text: str) -> Optional[List[int]]:
    """提取首个 x*y 数值对。"""
    match = re.search(r"(\d+)\s*[xX]\s*(\d+)", text)
    if not match:
        return None
    return [int(match.group(1)), int(match.group(2))]


def _extract_value_pair(section: str, field_name: str) -> Optional[List[float]]:
    """提取二维尺寸。"""
    value = _extract_value_after_colon(section, field_name)
    if not value:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)", value)
    if not match:
        return None

    return [float(match.group(1)), float(match.group(2))]


def _extract_value_triplet(section: str, field_name: str) -> Optional[List[float]]:
    """提取三维尺寸。"""
    value = _extract_value_after_colon(section, field_name)
    if not value:
        return None

    match = re.search(
        r"(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)",
        value,
    )
    if not match:
        return None

    return [float(match.group(1)), float(match.group(2)), float(match.group(3))]


def _extract_world_location(section: str) -> Optional[List[float]]:
    """提取世界坐标。"""
    match = re.search(
        r"\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)",
        section,
    )
    if not match:
        return None
    return [float(match.group(1)), float(match.group(2)), float(match.group(3))]


def _extract_single_number_after_key(section: str, field_name: str) -> Optional[float]:
    """提取字段后出现的首个数字。"""
    value = _extract_value_after_colon(section, field_name)
    if not value:
        return None

    match = re.search(r"(\d+(?:\.\d+)?)", value)
    return float(match.group(1)) if match else None


if __name__ == "__main__":
    test_gdd_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "ProjectInputs",
        "GDD",
        "boardgame_tictactoe_v1.md",
    )
    if os.path.exists(test_gdd_path):
        result = read_gdd(test_gdd_path)
        print(f"游戏类型: {result['game_type']}")
        print(f"设计输入字段: {sorted(result.keys())}")
