# -*- coding: utf-8 -*-
"""
Phase 4 Compiler / StaticBase / Review 测试
覆盖 StaticBase 装载、GDD 结构化解析、自动 spec 生成、review 缺口与 simulated E2E。
"""

import json
import os
import subprocess
import sys

import pytest


class TestPhase4Compiler:
    """Phase 4 最小编译链测试。"""

    def test_cp12_static_base_registry_loads(self, compiler_module):
        """CP-12: Static Base registry 可加载，且 10 个静态基座可见。"""
        from compiler.generation import load_phase4_static_specs, load_static_base_registry

        registry = load_static_base_registry()
        spec_ids = [entry["spec_id"] for entry in registry.get("static_specs", [])]
        assert len(spec_ids) == 10
        assert "WorldBuildStaticSpec" in spec_ids
        assert "BoardgameValidationStaticSpec" in spec_ids

        context = load_phase4_static_specs()
        assert set(context["loaded_specs"].keys()) == {
            "WorldBuildStaticSpec",
            "ValidationStaticSpec",
            "BoardgameStaticSpec",
            "BoardgameValidationStaticSpec",
        }
        assert context["missing_specs"] == []

    def test_cp13_design_input_extracts_phase4_fields(self, compiler_module, project_root):
        """CP-13: Phase 4 结构化字段可从井字棋 GDD 提取。"""
        from compiler.intake import read_gdd

        gdd_path = os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")
        design_input = read_gdd(gdd_path)

        expected_keys = {
            "game_type",
            "feature_tags",
            "board",
            "piece_catalog",
            "rules",
            "initial_layout",
            "prototype_preview",
            "technical_requirements",
        }
        assert expected_keys.issubset(design_input.keys())
        assert design_input["game_type"] == "boardgame"
        assert design_input["board"]["grid_size"] == [3, 3]
        assert design_input["board"]["cell_size_cm"] == [100.0, 100.0]
        assert {piece["symbol"] for piece in design_input["piece_catalog"]} == {"X", "O"}
        assert design_input["prototype_preview"]["piece_counts"] == {"X": 1, "O": 1}

    def test_cp14_build_handoff_generates_richer_spec_tree(self, compiler_module, project_root):
        """CP-14: Handoff 由自动生成链产出 richer spec 节点，并通过 schema 校验。"""
        jsonschema = pytest.importorskip("jsonschema")
        from compiler.intake import get_project_state_snapshot, read_gdd
        from compiler.handoff import build_handoff

        gdd_path = os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")
        schema_path = os.path.join(
            project_root,
            "Plugins",
            "AgentBridge",
            "Schemas",
            "reviewed_handoff.schema.json",
        )

        design_input = read_gdd(gdd_path)
        handoff = build_handoff(design_input, "greenfield_bootstrap", get_project_state_snapshot())
        actor_names = [actor["actor_name"] for actor in handoff["dynamic_spec_tree"]["scene_spec"]["actors"]]

        assert handoff["status"] == "reviewed"
        assert {"world_build_spec", "boardgame_spec", "validation_spec", "scene_spec"}.issubset(
            handoff["dynamic_spec_tree"].keys()
        )
        assert actor_names == ["Board", "PieceX_1", "PieceO_1"]

        with open(schema_path, "r", encoding="utf-8") as file:
            schema = json.load(file)
        jsonschema.validate(handoff, schema)

    def test_cp17_default_preview_policy_generates_one_x_and_one_o(self, compiler_module, project_root):
        """CP-17: GDD 未定义示例棋子时，默认生成 1 个 X 和 1 个 O。"""
        from compiler.handoff import build_handoff
        from compiler.intake import get_project_state_snapshot, read_gdd

        gdd_path = os.path.join(project_root, "ProjectInputs", "GDD", "boardgame_tictactoe_v1.md")
        design_input = read_gdd(gdd_path)
        handoff = build_handoff(
            design_input,
            "greenfield_bootstrap",
            get_project_state_snapshot(),
        )
        actor_names = [actor["actor_name"] for actor in handoff["dynamic_spec_tree"]["scene_spec"]["actors"]]

        assert design_input["prototype_preview"]["source"] == "default"
        assert design_input["prototype_preview"]["piece_counts"] == {"X": 1, "O": 1}
        assert actor_names == ["Board", "PieceX_1", "PieceO_1"]

    def test_cp18_explicit_preview_counts_follow_gdd(self, compiler_module, workspace_tmp_path):
        """CP-18: GDD 显式定义示例棋子数量时，自动生成链按 GDD 执行。"""
        from compiler.handoff import build_handoff
        from compiler.intake import read_gdd

        gdd_path = workspace_tmp_path / "boardgame_preview_override.md"
        gdd_path.write_text(
            "\n".join(
                [
                    "# 井字棋游戏 GDD v1",
                    "",
                    "## 游戏类型",
                    "棋盘游戏（Boardgame）",
                    "",
                    "## 核心玩法",
                    "- 3x3 棋盘",
                    "- 2 种棋子：X 和 O",
                    "- 回合制：玩家轮流放置棋子",
                    "- 胜利条件：横/竖/斜连成 3 个",
                    "",
                    "## 场景需求",
                    "### 棋盘",
                    "- 类型：3x3 网格",
                    "- 每格尺寸：100x100 cm",
                    "- 总尺寸：300x300 cm",
                    "- 材质：简单平面",
                    "- 位置：世界原点 (0, 0, 0)",
                    "",
                    "### 棋子 X",
                    "- 形状：Cube（立方体）",
                    "- 颜色：红色",
                    "- 尺寸：50x50x50 cm",
                    "- 数量：最多 5 个",
                    "",
                    "### 棋子 O",
                    "- 形状：Sphere（球体）",
                    "- 颜色：蓝色",
                    "- 半径：25 cm",
                    "- 数量：最多 4 个",
                    "",
                    "## 原型预览",
                    "- 示例棋子：X=2, O=1",
                    "",
                    "## 技术需求",
                    "- UE5.5.4",
                    "- 使用 StaticMeshActor",
                ]
            ),
            encoding="utf-8",
        )

        design_input = read_gdd(str(gdd_path))
        handoff = build_handoff(
            design_input,
            "greenfield_bootstrap",
            {"project_name": "Mvpv4TestCodex", "actor_count": 0, "is_empty": True},
        )
        actor_names = [actor["actor_name"] for actor in handoff["dynamic_spec_tree"]["scene_spec"]["actors"]]

        assert design_input["prototype_preview"]["source"] == "gdd_explicit_counts"
        assert design_input["prototype_preview"]["piece_counts"] == {"X": 2, "O": 1}
        assert actor_names == ["Board", "PieceX_1", "PieceX_2", "PieceO_1"]

    def test_cp15_preview_zero_generates_only_board(self, compiler_module, workspace_tmp_path):
        """CP-15: GDD 显式写 0 个示例棋子时，不生成预览棋子。"""
        from compiler.handoff import build_handoff
        from compiler.intake import read_gdd

        gdd_path = workspace_tmp_path / "boardgame_preview_zero.md"
        gdd_path.write_text(
            "\n".join(
                [
                    "# 井字棋游戏 GDD v1",
                    "",
                    "## 游戏类型",
                    "棋盘游戏（Boardgame）",
                    "",
                    "## 核心玩法",
                    "- 3x3 棋盘",
                    "- 2 种棋子：X 和 O",
                    "- 回合制：玩家轮流放置棋子",
                    "- 胜利条件：横/竖/斜连成 3 个",
                    "",
                    "## 场景需求",
                    "### 棋盘",
                    "- 类型：3x3 网格",
                    "- 每格尺寸：100x100 cm",
                    "- 总尺寸：300x300 cm",
                    "- 材质：简单平面",
                    "- 位置：世界原点 (0, 0, 0)",
                    "",
                    "### 棋子 X",
                    "- 形状：Cube（立方体）",
                    "- 颜色：红色",
                    "- 尺寸：50x50x50 cm",
                    "- 数量：最多 5 个",
                    "",
                    "### 棋子 O",
                    "- 形状：Sphere（球体）",
                    "- 颜色：蓝色",
                    "- 半径：25 cm",
                    "- 数量：最多 4 个",
                    "",
                    "## 原型预览",
                    "- 示例棋子：0",
                    "",
                    "## 技术需求",
                    "- UE5.5.4",
                    "- 使用 StaticMeshActor",
                ]
            ),
            encoding="utf-8",
        )

        design_input = read_gdd(str(gdd_path))
        handoff = build_handoff(
            design_input,
            "greenfield_bootstrap",
            {"project_name": "Mvpv4TestCodex", "actor_count": 0, "is_empty": True},
        )
        actor_names = [actor["actor_name"] for actor in handoff["dynamic_spec_tree"]["scene_spec"]["actors"]]

        assert design_input["prototype_preview"]["generate_preview"] is False
        assert actor_names == ["Board"]

    def test_cp16_review_reports_missing_template_gap(self, compiler_module):
        """CP-16: 缺失静态模板时，review 正确写入 capability_gaps。"""
        from compiler.review import review_dynamic_spec_tree

        design_input = {
            "piece_catalog": [{"symbol": "X"}, {"symbol": "O"}],
            "prototype_preview": {"generate_preview": True, "piece_counts": {"X": 1, "O": 1}},
            "parsing_notes": {"unsupported_sections": []},
        }
        dynamic_spec_tree = {
            "scene_spec": {
                "actors": [
                    {
                        "actor_name": "Board",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [0.0, 0.0, 0.0],
                            "rotation": [0.0, 0.0, 0.0],
                            "relative_scale3d": [3.0, 3.0, 0.1],
                        },
                    },
                    {
                        "actor_name": "PieceX_1",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [-100.0, -100.0, 50.0],
                            "rotation": [0.0, 0.0, 0.0],
                            "relative_scale3d": [0.5, 0.5, 0.5],
                        },
                    },
                    {
                        "actor_name": "PieceO_1",
                        "actor_class": "/Script/Engine.StaticMeshActor",
                        "transform": {
                            "location": [100.0, 100.0, 50.0],
                            "rotation": [0.0, 0.0, 0.0],
                            "relative_scale3d": [0.5, 0.5, 0.5],
                        },
                    },
                ]
            }
        }
        static_spec_context = {
            "loaded_specs": {
                "WorldBuildStaticSpec": {},
                "ValidationStaticSpec": {},
            },
            "required_spec_ids": [
                "WorldBuildStaticSpec",
                "ValidationStaticSpec",
                "BoardgameStaticSpec",
                "BoardgameValidationStaticSpec",
            ],
        }
        routing_context = {"mode": "greenfield_bootstrap"}

        result = review_dynamic_spec_tree(
            design_input=design_input,
            dynamic_spec_tree=dynamic_spec_tree,
            static_spec_context=static_spec_context,
            routing_context=routing_context,
        )

        assert result["status"] == "blocked"
        assert result["capability_gaps"]["required_static_templates"] == [
            "BoardgameStaticSpec",
            "BoardgameValidationStaticSpec",
        ]

    def test_e2e18_greenfield_phase4_simulated(self, project_root):
        """E2E-18: Phase 4 simulated 端到端可跑通。"""
        demo_script = os.path.join(project_root, "Scripts", "run_greenfield_demo.py")
        result = subprocess.run(
            [sys.executable, demo_script],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        combined_output = f"{result.stdout}\n{result.stderr}"

        assert result.returncode == 0, combined_output
        assert "succeeded" in combined_output
        assert "spawn_Board: success" in combined_output
