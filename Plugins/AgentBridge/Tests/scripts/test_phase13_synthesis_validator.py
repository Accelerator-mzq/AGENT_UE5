# -*- coding: utf-8 -*-
"""SKS-05/06/07: 合成包机器校验——合法通过、缺件拒绝、schema 违规拒绝、家族越界拒绝。

额外覆盖前序审查点名的边缘用例:
  - package value 为 None 时不崩溃
  - manifest 顶层为 list 时给出具体错误
  - output_schema 顶层非 dict 时给出具体错误
"""
import importlib.util
import json
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[2]


def _load():
    """动态加载 synthesis_validator 模块(便于测试未安装为包的单文件模块)。"""
    spec = importlib.util.spec_from_file_location(
        "synthesis_validator",
        PLUGIN_ROOT / "Compiler" / "stages" / "synthesis_validator.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _legal_package():
    """构造最小合法 6 文件包(内容为内存 dict,key=文件名)。"""
    manifest = "\n".join([
        "template_id: synthesized.gameplay-auction.v1",
        "display_name: 拍卖机制(合成)",
        "template_kind: genre_skill",
        "genre: monopoly_like",
        "template_version: \"1.0.0\"",
        "template_source: synthesized",
        "review_status: pending_review",
        "realization_class: realization_eligible",
        "can_emit_families:",
        "  - property_economy_spec",
        "capability_bindings:",
        "  - capability_id: gameplay-auction",
        "    instance_id: skill-auction",
        "    convergence_priority: 9",
        "    related_clarification_items: []",
        "    planning_notes:",
        "      - \"拍卖机制由 agent 合成,Phase 13 试制。\"",
        "    fragment_family: property_economy_spec",
        "    depends_on_capabilities:",
        "      - gameplay-economy",
    ])
    output_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "auction_type": {"type": "string"},
            "starting_bid_rule": {
                "type": "object",
                "additionalProperties": False,
                "properties": {"basis": {"type": "string"}},
            },
        },
        "required": ["auction_type"],
    }
    return {
        "manifest.yaml": manifest,
        "system_prompt.md": "你是桌游经济系统设计专家。",
        "domain_prompt.md": "拍卖有英式/荷兰式/密封出价三类……",
        "evaluator_prompt.md": "检查流拍处理是否定义。",
        "input_selector.yaml": "include_sections:\n  - economy\n",
        "output_schema.json": json.dumps(output_schema, ensure_ascii=False),
    }


WHITELIST = {"property_economy_spec", "hud_spec"}


class TestSynthesisValidator:
    # ---- SKS-05: 合法包通过 ----

    def test_sks05_legal_package_passes(self):
        """合法 6 文件包,期望零错误。"""
        sv = _load()
        errors = sv.validate_synthesized_package(
            "gameplay-auction", _legal_package(), WHITELIST
        )
        assert errors == [], f"期望零错误,实际: {errors}"

    # ---- SKS-05b: 缺件拒绝 ----

    def test_sks05b_missing_file_rejected(self):
        """缺少 evaluator_prompt.md 时应返回含文件名的错误。"""
        sv = _load()
        package = _legal_package()
        del package["evaluator_prompt.md"]
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("evaluator_prompt.md" in e for e in errors), \
            f"期望包含 'evaluator_prompt.md' 的错误,实际: {errors}"

    # ---- SKS-06: output_schema 违规拒绝 ----

    def test_sks06_schema_missing_additional_properties_rejected(self):
        """嵌套 object 节点未声明 additionalProperties: false 应被拒绝。"""
        sv = _load()
        package = _legal_package()
        bad = json.loads(package["output_schema.json"])
        del bad["properties"]["starting_bid_rule"]["additionalProperties"]
        package["output_schema.json"] = json.dumps(bad)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e for e in errors), \
            f"期望包含 'additionalProperties' 的错误,实际: {errors}"

    # ---- SKS-07: family 越界拒绝 ----

    def test_sks07_family_outside_whitelist_rejected(self):
        """can_emit_families 中包含白名单外的 family 应被拒绝。"""
        sv = _load()
        package = _legal_package()
        package["manifest.yaml"] = package["manifest.yaml"].replace(
            "property_economy_spec", "totally_new_family"
        )
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("totally_new_family" in e for e in errors), \
            f"期望包含 'totally_new_family' 的错误,实际: {errors}"

    def test_sks07b_template_id_dir_mismatch_rejected(self):
        """capability_id 与 template_id 不匹配时应返回含 'template_id' 的错误。"""
        sv = _load()
        package = _legal_package()
        # 用 gameplay-stock 调用但 package 里 template_id 是 gameplay-auction
        errors = sv.validate_synthesized_package("gameplay-stock", package, WHITELIST)
        assert any("template_id" in e for e in errors), \
            f"期望包含 'template_id' 的错误,实际: {errors}"

    # ---- 边缘用例: 前序审查点名的三个防崩位置 ----

    def test_edge_package_value_none_no_crash(self):
        """package dict 中某个 value 为 None 时不应 AttributeError 崩溃。"""
        sv = _load()
        package = _legal_package()
        package["evaluator_prompt.md"] = None  # agent 传 null 的情形
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        # None 视为缺失/为空,应给出错误而非崩溃
        assert any("evaluator_prompt.md" in e for e in errors), \
            f"期望缺失错误,实际: {errors}"

    def test_edge_manifest_is_list_rejected(self):
        """manifest.yaml 顶层为 list 而非 mapping 时应给出具体错误。"""
        sv = _load()
        package = _legal_package()
        package["manifest.yaml"] = "- item1\n- item2\n"
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert errors, "期望至少一条错误"
        # 错误信息应能让 agent 理解根因
        combined = " ".join(errors)
        assert "manifest" in combined.lower() or "mapping" in combined.lower() or \
               "顶层" in combined, f"错误信息不够具体: {errors}"

    def test_edge_output_schema_not_dict_rejected(self):
        """output_schema.json 顶层为数组时应给出具体错误而非崩溃。"""
        sv = _load()
        package = _legal_package()
        package["output_schema.json"] = json.dumps(["not", "a", "dict"])
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert errors, "期望至少一条错误"
        combined = " ".join(errors)
        assert "output_schema" in combined.lower() or "schema" in combined.lower(), \
            f"错误信息不够具体: {errors}"
