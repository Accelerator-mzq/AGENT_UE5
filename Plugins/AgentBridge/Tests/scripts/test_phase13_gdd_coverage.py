# -*- coding: utf-8 -*-
"""SKS-12/13: GDD 结构切分与反向覆盖矩阵(无人认领可见)。"""
import importlib.util
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]

GDD = """# 测试游戏 GDD

## 2.1 棋盘与地块
28 格环形棋盘。

## 2.4 地产拍卖
玩家拒购时进入英式拍卖。

## 3.2 背景音乐
氛围性描述,随回合切换。
"""


def _load():
    spec = importlib.util.spec_from_file_location(
        "gdd_coverage", PLUGIN_ROOT / "Compiler" / "stages" / "gdd_coverage.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestGddCoverage:
    def test_sks12_split_by_structure_only(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        headings = [s["heading"] for s in sections]
        assert "2.1 棋盘与地块" in headings
        assert "2.4 地产拍卖" in headings
        assert "3.2 背景音乐" in headings
        auction = next(s for s in sections if s["heading"] == "2.4 地产拍卖")
        assert "英式拍卖" in auction["text"]

    def test_sks13_matrix_exposes_unclaimed(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        capabilities = [
            {"capability_id": "gameplay-board-topology", "source_anchor": "2.1 棋盘与地块"},
            {"capability_id": "gameplay-auction", "source_anchor": "2.4 地产拍卖"},
        ]
        matrix = gc.build_coverage_matrix(sections, capabilities)
        unclaimed = [r for r in matrix["rows"] if r["status"] == "unclaimed"]
        assert [r["heading"] for r in unclaimed] == ["3.2 背景音乐"]
        claimed = {r["heading"]: r["claimed_by"] for r in matrix["rows"] if r["status"] == "claimed"}
        assert claimed["2.4 地产拍卖"] == ["gameplay-auction"]
        # 无出处的 capability 也要可见
        capabilities.append({"capability_id": "gameplay-ghost", "source_anchor": ""})
        matrix = gc.build_coverage_matrix(sections, capabilities)
        assert "gameplay-ghost" in matrix["capabilities_without_anchor"]

    def test_sks13b_non_markdown_degrades_visibly(self):
        """非 markdown(无标题)输入:整篇成一个无人认领大段,不假装工作。"""
        gc = _load()
        sections = gc.split_gdd_sections("纯文本无标题的设计描述……")
        assert len(sections) == 1
        matrix = gc.build_coverage_matrix(sections, [])
        assert matrix["rows"][0]["status"] == "unclaimed"

    def test_sks13c_render_markdown(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        matrix = gc.build_coverage_matrix(
            sections, [{"capability_id": "gameplay-board-topology", "source_anchor": "2.1 棋盘与地块"}]
        )
        text = gc.render_coverage_markdown(matrix)
        assert "无人认领" in text
        assert "2.4 地产拍卖" in text
