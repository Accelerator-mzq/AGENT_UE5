# -*- coding: utf-8 -*-
"""SKS-12/13: GDD 结构切分与反向覆盖矩阵(无人认领可见)。"""
import importlib.util
import json
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
        # body 是不含标题行的正文(职责内聚:切分层直接产出,矩阵层不再剥首行)
        assert "英式拍卖" in auction["body"]
        assert "2.4 地产拍卖" not in auction["body"]

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
        # 降级段无标题行可剥,body 即全文
        assert sections[0]["body"] == sections[0]["text"]
        matrix = gc.build_coverage_matrix(sections, [])
        assert matrix["rows"][0]["status"] == "unclaimed"
        # 无容器时渲染不出现容器计数行(N>0 才显示)
        assert "纯结构容器" not in gc.render_coverage_markdown(matrix)

    def test_sks13c_render_markdown(self):
        gc = _load()
        sections = gc.split_gdd_sections(GDD)
        matrix = gc.build_coverage_matrix(
            sections, [{"capability_id": "gameplay-board-topology", "source_anchor": "2.1 棋盘与地块"}]
        )
        text = gc.render_coverage_markdown(matrix)
        assert "无人认领" in text
        assert "2.4 地产拍卖" in text
        # 容器段被省略必须可审计:GDD 总标题是唯一容器,渲染须标注省略数
        assert "(另有 1 个纯结构容器标题未列出)" in text

    def test_sks13d_container_rule_boundaries(self):
        """容器规则边界:只有"无正文+紧随更深层标题"才算容器,其余空段不许静默吞。

        回归向量:若判定被"简化"成只看正文为空(丢掉对下一段层级的检查),
        同级空段/末尾空段会被吞成 container——本测试专门钉死这三类边界。
        """
        gc = _load()
        boundary_gdd = (
            "# 文档总标题\n"
            "\n"
            "## A 同级空段\n"
            "\n"
            "## B 有正文段\n"
            "正文内容。\n"
            "\n"
            "## C 末尾空段\n"
        )
        sections = gc.split_gdd_sections(boundary_gdd)
        matrix = gc.build_coverage_matrix(sections, [])
        status = {r["heading"]: r["status"] for r in matrix["rows"]}
        # ① 文档总标题:无正文且紧随更深层标题 → container
        assert status["文档总标题"] == "container"
        # ② 同级空段(后随同级标题)→ unclaimed,不许静默吞
        assert status["A 同级空段"] == "unclaimed"
        # ③ 末尾空段(无后继段落)→ unclaimed,不许静默吞
        assert status["C 末尾空段"] == "unclaimed"
        # ⑤ unclaimed_count 只数 unclaimed,排除 container(A/B/C 三段)
        assert matrix["unclaimed_count"] == 3
        assert matrix["unclaimed_count"] == sum(
            1 for r in matrix["rows"] if r["status"] == "unclaimed"
        )
        # ④ 被 anchor 认领的容器 → claimed(认领优先于容器判定)
        matrix2 = gc.build_coverage_matrix(
            sections, [{"capability_id": "cap-doc", "source_anchor": "文档总标题"}]
        )
        status2 = {r["heading"]: r["status"] for r in matrix2["rows"]}
        assert status2["文档总标题"] == "claimed"

    def test_sks13d2_structural_container_helper_direct(self):
        """直接打 _is_structural_container helper:四种邻接关系逐一验证。"""
        gc = _load()
        sections = gc.split_gdd_sections(
            "# 文档总标题\n\n## A 同级空段\n\n## B 有正文段\n正文内容。\n"
        )
        title, empty_a, body_b = sections[0], sections[1], sections[2]
        # 无正文 + 下一段更深层 → 容器
        assert gc._is_structural_container(title, empty_a) is True
        # 无正文 + 下一段同级 → 非容器
        assert gc._is_structural_container(empty_a, body_b) is False
        # 末尾段(无后继)→ 非容器
        assert gc._is_structural_container(body_b, None) is False
        # 有正文 + 下一段更深层 → 非容器(正文必须被认领,不许借容器身份逃逸)
        prosy = gc.split_gdd_sections("# 带正文的总标题\n概述正文。\n\n## 子段\n内容。\n")
        assert gc._is_structural_container(prosy[0], prosy[1]) is False


class TestGddCoverageMatrixSchemaAntiDrift:
    """SKS-13-schema: 真实 build_coverage_matrix 输出须通过 gdd_coverage_matrix schema 校验。

    此测试锁住 schema 与实现不漂移——若 gdd_coverage.py 改动了输出字段,
    此测试变红,要求同步更新 schema 和 example。
    """

    def test_real_output_validates_against_schema(self):
        """用覆盖三态(claimed/unclaimed/container)的真实输出对 schema 做正向校验。"""
        try:
            import jsonschema
        except ImportError:
            import pytest
            pytest.skip("jsonschema 未安装,跳过 schema 防漂移测试")

        gc = _load()

        # 构造覆盖三态的输入:# 总标题(container)+ ## 2.1(claimed)+ ## 2.2(unclaimed)
        gdd_text = (
            "# 设计文档\n"
            "\n"
            "## 2.1 棋盘系统\n"
            "40 格环形棋盘,支持地产购买与地租收取。\n"
            "\n"
            "## 2.2 计分规则\n"
            "胜负以持有净资产判定,零资产时破产。\n"
        )
        sections = gc.split_gdd_sections(gdd_text)
        capabilities = [
            # anchor 认领 → claimed
            {"capability_id": "gameplay-board-topology", "source_anchor": "2.1 棋盘系统"},
            # 空 anchor → capabilities_without_anchor
            {"capability_id": "baseline-audio-placeholder", "source_anchor": ""},
            # 指向不存在段落 → dangling_anchors
            {"capability_id": "gameplay-auction", "source_anchor": "3.1 不存在的段落"},
        ]
        matrix = gc.build_coverage_matrix(sections, capabilities)

        # 加载 schema 文件
        schema_path = PLUGIN_ROOT / "Schemas" / "gdd_coverage_matrix.schema.json"
        assert schema_path.exists(), f"schema 文件不存在: {schema_path}"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        # 校验真实输出对 schema 全过(如有违规则打印详细错误)
        validator = jsonschema.Draft7Validator(schema)
        errors = list(validator.iter_errors(matrix))
        assert not errors, (
            f"真实 build_coverage_matrix 输出不满足 schema,字段可能已漂移:\n"
            + "\n".join(f"  {e.json_path}: {e.message}" for e in errors)
        )

        # 进一步确认三态覆盖到
        statuses = {row["status"] for row in matrix["rows"]}
        assert "container" in statuses, "测试输入应包含 container 段落"
        assert "claimed" in statuses, "测试输入应包含 claimed 段落"
        assert "unclaimed" in statuses, "测试输入应包含 unclaimed 段落"

        # capabilities_without_anchor / dangling_anchors 均非空
        assert matrix["capabilities_without_anchor"], "测试输入应包含无 anchor 的 capability"
        assert matrix["dangling_anchors"], "测试输入应包含 dangling anchor"
