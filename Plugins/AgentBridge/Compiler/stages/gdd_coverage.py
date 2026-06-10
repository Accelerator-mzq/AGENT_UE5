# -*- coding: utf-8 -*-
"""Phase 13 GDD 覆盖矩阵(三层保证模型的第二层:反向覆盖审计)。

防固化守则(spec §5.3,评审时强制对照):
  1. 切分只认 markdown 结构(标题行),零语义判断——本文件出现任何游戏词汇即违规;
  2. 不读不写任何全局忽略配置,矩阵每次从零生成,人的裁决只留在 run 级产物;
  3. 认领判定只靠 source_anchor 与标题的字符串等值,不依赖分类词表;
  4. 非 markdown 输入优雅降级为单一无人认领大段(可见失效,不假装工作)。
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def split_gdd_sections(gdd_text: str) -> List[Dict[str, Any]]:
    """按 markdown 标题切分;无任何标题时整篇为一段(优雅降级)。

    每段字段:heading(标题文本)/ level(标题层级)/ start_line(起始行号)
    / text(含标题行的原文)/ body(不含标题行的正文;降级段无标题行,body=全文)。
    """
    lines = gdd_text.splitlines()
    sections: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    for line_number, line in enumerate(lines, start=1):
        match = _HEADING_RE.match(line)
        if match:
            if current is not None:
                sections.append(current)
            current = {
                "heading": match.group(2).strip(),
                "level": len(match.group(1)),
                "start_line": line_number,
                "text": line + "\n",
                "body": "",
            }
        elif current is not None:
            current["text"] += line + "\n"
            current["body"] += line + "\n"
    if current is not None:
        sections.append(current)
    if not sections:
        return [{
            "heading": "<整篇文档(未检出 markdown 标题,矩阵降级)>",
            "level": 0, "start_line": 1, "text": gdd_text, "body": gdd_text,
        }]
    return sections


def _is_structural_container(
    section: Dict[str, Any], next_section: Dict[str, Any] | None
) -> bool:
    """纯结构容器判定(零语义):自身无正文 且 紧随其后是更深层标题。

    两个条件缺一不可——同级空段/末尾空段没有子段落承接覆盖责任,
    必须保持 unclaimed 可见,不许借容器身份被静默吞掉。
    """
    if next_section is None:
        return False  # 末尾段:无后继,谈不上"由子段落承担"
    if (section.get("body") or "").strip():
        return False  # 有自身正文:正文必须被认领,不许逃逸
    return next_section["level"] > section["level"]


def build_coverage_matrix(
    sections: List[Dict[str, Any]],
    capabilities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """逐段比对认领关系。认领 = capability.source_anchor 与段落标题字符串等值。"""
    claims: Dict[str, List[str]] = {}
    without_anchor: List[str] = []
    for capability in capabilities:
        anchor = (capability.get("source_anchor") or "").strip()
        capability_id = capability.get("capability_id", "")
        if not anchor:
            without_anchor.append(capability_id)
            continue
        claims.setdefault(anchor, []).append(capability_id)

    rows = []
    for index, section in enumerate(sections):
        claimed_by = sorted(claims.get(section["heading"], []))
        # 容器判定见 _is_structural_container:文档总标题/章标题这类
        # "无正文+紧随更深层标题"的段落,覆盖责任由子段落承担,不计入无人认领
        next_section = sections[index + 1] if index + 1 < len(sections) else None
        if claimed_by:
            status = "claimed"  # 认领优先:被 anchor 指到的容器也算认领
        elif _is_structural_container(section, next_section):
            status = "container"
        else:
            status = "unclaimed"
        rows.append({
            "heading": section["heading"],
            "start_line": section["start_line"],
            "status": status,
            "claimed_by": claimed_by,
        })
    matched_anchors = {row["heading"] for row in rows if row["claimed_by"]}
    dangling = sorted(set(claims) - matched_anchors)  # anchor 指向不存在的段落
    return {
        "rows": rows,
        "capabilities_without_anchor": sorted(without_anchor),
        "dangling_anchors": dangling,
        "unclaimed_count": sum(1 for row in rows if row["status"] == "unclaimed"),
    }


def render_coverage_markdown(matrix: Dict[str, Any]) -> str:
    """人读版:无人认领段落置顶(人审只需要看这部分)。"""
    lines = ["# GDD 覆盖矩阵", ""]
    unclaimed = [row for row in matrix["rows"] if row["status"] == "unclaimed"]
    lines.append(f"## ⚠️ 无人认领段落({len(unclaimed)})——逐条裁决:非功能可忽略 / 功能遗漏须打回重抽")
    lines.append("")
    for row in unclaimed:
        lines.append(f"- L{row['start_line']} {row['heading']}")
    # 容器段(纯结构标题)被省略必须可审计:标注省略数,区分"被省略"与"渲染漏了"
    container_count = sum(1 for row in matrix["rows"] if row["status"] == "container")
    if container_count:
        lines.append(f"(另有 {container_count} 个纯结构容器标题未列出)")
    lines.append("")
    lines.append("## 已认领段落")
    lines.append("")
    lines.append("| GDD 段落 | 认领能力 |")
    lines.append("|---|---|")
    for row in matrix["rows"]:
        if row["status"] == "claimed":
            lines.append(f"| {row['heading']} | {', '.join(row['claimed_by'])} |")
    if matrix["capabilities_without_anchor"]:
        lines.append("")
        lines.append("## ⚠️ 无出处能力(source_anchor 为空)")
        for capability_id in matrix["capabilities_without_anchor"]:
            lines.append(f"- {capability_id}")
    if matrix["dangling_anchors"]:
        lines.append("")
        lines.append("## ⚠️ 悬空 anchor(指向不存在的段落)")
        for anchor in matrix["dangling_anchors"]:
            lines.append(f"- {anchor}")
    return "\n".join(lines)
