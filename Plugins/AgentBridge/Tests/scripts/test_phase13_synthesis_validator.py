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

    # ---- Bug D: 标量字符串逐字符迭代防御 ----

    def test_bugd_families_scalar_string_single_error(self):
        """can_emit_families 是标量字符串时,应给恰好一条'必须是列表'错误,
        而非逐字符迭代产生 N 条单字符垃圾错误。"""
        sv = _load()
        package = _legal_package()
        package["manifest.yaml"] = package["manifest.yaml"].replace(
            "can_emit_families:\n  - property_economy_spec",
            "can_emit_families: property_economy_spec",
        )
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        list_errors = [e for e in errors if "必须是列表" in e and "can_emit_families" in e]
        assert len(list_errors) == 1, f"期望恰好一条'必须是列表'错误,实际: {errors}"
        # 不应出现逐字符垃圾(单字符越界错误)
        assert len(errors) == 1, \
            f"期望总共一条错误,无逐字符垃圾,实际 {len(errors)} 条: {errors}"

    def test_bugd_bindings_scalar_string_single_error(self):
        """capability_bindings 是标量字符串时,应给恰好一条'必须是列表'错误,
        而非逐字符迭代产生'必须是 mapping'垃圾错误。"""
        sv = _load()
        package = _legal_package()
        manifest_text = package["manifest.yaml"]
        # 把整个 capability_bindings 块替换为标量字符串
        package["manifest.yaml"] = (
            manifest_text.split("capability_bindings:")[0]
            + "capability_bindings: bogus_binding"
        )
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        list_errors = [e for e in errors if "必须是列表" in e and "capability_bindings" in e]
        assert len(list_errors) == 1, f"期望恰好一条'必须是列表'错误,实际: {errors}"
        assert len(errors) == 1, \
            f"期望总共一条错误,无逐字符垃圾,实际 {len(errors)} 条: {errors}"

    # ---- Bug B: anyOf/oneOf/allOf/$defs/definitions 内嵌 object 漏判 ----

    def test_bugb_anyof_nested_object_missing_ap_caught(self):
        """anyOf 内嵌的 object 节点缺 additionalProperties: false 应被抓到。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        # LLM 常见模式: 用 anyOf 做联合类型,其中 object 分支缺 additionalProperties
        schema["properties"]["payment_rule"] = {
            "anyOf": [
                {"type": "string"},
                {
                    "type": "object",
                    # 故意缺 additionalProperties: false
                    "properties": {"rate": {"type": "number"}},
                },
            ]
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        ap_errors = [e for e in errors if "additionalProperties" in e and "anyOf" in e]
        assert ap_errors, \
            f"期望抓到 anyOf 内嵌 object 缺 additionalProperties,实际: {errors}"

    def test_bugb_legal_anyof_union_passes(self):
        """合法的 anyOf 联合(object 分支带 additionalProperties: false)应零错误。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        schema["properties"]["payment_rule"] = {
            "anyOf": [
                {"type": "string"},
                {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {"rate": {"type": "number"}},
                },
            ]
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert errors == [], f"期望零错误,实际: {errors}"

    # ---- 审查 #1: 递归深度保护 ----

    def test_review1_deep_schema_no_crash_depth_error(self):
        """程序化构造深 100 的嵌套 schema:不应 RecursionError 崩溃,
        应含'嵌套过深'错误(合成重试闭环依赖校验器永不抛异常)。"""
        sv = _load()
        package = _legal_package()
        # 用循环构造 100 层嵌套 object(每层都合法声明 additionalProperties: false)
        node = {"type": "string"}
        for level in range(100):
            node = {
                "type": "object",
                "additionalProperties": False,
                "properties": {f"level_{level}": node},
            }
        package["output_schema.json"] = json.dumps(node)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("嵌套过深" in e for e in errors), \
            f"期望'嵌套过深'错误,实际: {errors}"

    # ---- 审查 #3: 无 type 的 properties 节点不应整体漏检 ----

    def test_review3_no_type_properties_node_nested_object_caught(self):
        """外层节点无 type 只有 properties(LLM 高频遗漏 type 声明),
        内嵌 object 缺 additionalProperties 应被抓到。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        schema["properties"]["fee_rule"] = {
            # 故意不写 type: object
            "properties": {
                "inner": {
                    "type": "object",
                    # 故意缺 additionalProperties
                    "properties": {"rate": {"type": "number"}},
                }
            }
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e and "inner" in e for e in errors), \
            f"期望抓到无 type 节点下内嵌 object 缺 additionalProperties,实际: {errors}"

    # ---- 审查 #4: tuple 形 items(list of schemas)不应跳过 ----

    def test_review4_items_tuple_form_caught(self):
        """items 为 list(draft-07 tuple validation 形)时,
        内含 object 缺 additionalProperties 应被抓到。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        schema["properties"]["bid_steps"] = {
            "type": "array",
            "items": [
                {"type": "string"},
                {
                    "type": "object",
                    # 故意缺 additionalProperties
                    "properties": {"amount": {"type": "number"}},
                },
            ],
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e and "items" in e for e in errors), \
            f"期望抓到 tuple 形 items 内 object 缺 additionalProperties,实际: {errors}"

    # ---- 审查 #7(Minor): 空字符串 fragment_family 不得绕过白名单 ----

    def test_review7_empty_fragment_family_rejected(self):
        """fragment_family 字段存在但为空串时应报'不能为空',而非静默绕过。"""
        sv = _load()
        package = _legal_package()
        package["manifest.yaml"] = package["manifest.yaml"].replace(
            "    fragment_family: property_economy_spec",
            "    fragment_family: \"\"",
        )
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("fragment_family" in e and "不能为空" in e for e in errors), \
            f"期望'fragment_family 不能为空'错误,实际: {errors}"

    # ---- 审查 #11(Minor): oneOf / allOf / $defs 各补一条最小测试 ----
    #      (definitions 与 $defs 同构,只测 $defs)

    def test_review11_oneof_nested_object_missing_ap_caught(self):
        """oneOf 内嵌 object 缺 additionalProperties 应被抓到。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        schema["properties"]["tax_rule"] = {
            "oneOf": [
                {"type": "string"},
                {"type": "object", "properties": {"pct": {"type": "number"}}},
            ]
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e and "oneOf" in e for e in errors), \
            f"期望抓到 oneOf 内嵌违规,实际: {errors}"

    def test_review11_allof_nested_object_missing_ap_caught(self):
        """allOf 内嵌 object 缺 additionalProperties 应被抓到。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        schema["properties"]["combo_rule"] = {
            "allOf": [
                {"type": "object", "properties": {"x": {"type": "number"}}},
            ]
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e and "allOf" in e for e in errors), \
            f"期望抓到 allOf 内嵌违规,实际: {errors}"

    def test_review11_defs_nested_object_missing_ap_caught(self):
        """$defs 内定义的 object 缺 additionalProperties 应被抓到。"""
        sv = _load()
        package = _legal_package()
        schema = json.loads(package["output_schema.json"])
        schema["$defs"] = {
            "shared_rule": {
                "type": "object",
                "properties": {"y": {"type": "string"}},
            }
        }
        package["output_schema.json"] = json.dumps(schema)
        errors = sv.validate_synthesized_package("gameplay-auction", package, WHITELIST)
        assert any("additionalProperties" in e and "$defs" in e for e in errors), \
            f"期望抓到 $defs 内嵌违规,实际: {errors}"


class TestNonStringFileValues:
    """Important 2: MCP 透传场景 agent 可能给文件 value 传 dict/list/int,
    校验器必须给结构化错误而非 AttributeError 穿透(校验器永不抛契约)。"""

    def test_non_string_values_structured_error_no_crash(self):
        """value 为 dict/list/int 时各返回含文件名的'必须是字符串'错误,不抛异常。"""
        sv = _load()
        for bad_value in ({"a": 1}, ["x"], 7):
            package = _legal_package()
            package["domain_prompt.md"] = bad_value
            errors = sv.validate_synthesized_package(
                "gameplay-auction", package, WHITELIST
            )
            assert any("domain_prompt.md" in e and "必须是字符串" in e for e in errors), \
                f"期望含文件名的'必须是字符串'错误({type(bad_value).__name__}),实际: {errors}"


class TestCapabilityIdFormat:
    """Spec 审查实证漏洞: capability_id 是落盘目录名,必须有格式硬校验
    (单一事实源在 validator,skill_synthesis 的 save/prepare 入口复用)。"""

    def test_validate_capability_id_illegal_forms_one_error_each(self):
        """穿越/盘符/反斜杠/空串等非法形式,各恰好返回一条格式错误。"""
        sv = _load()
        illegal = ["../../evil", "gameplay/../evil", "C:\\evil", "back\\slash", ""]
        for bad in illegal:
            errors = sv.validate_capability_id(bad)
            assert len(errors) == 1, \
                f"期望 {bad!r} 恰好一条格式错误,实际: {errors}"
            assert "capability_id" in errors[0], \
                f"错误文案应点名 capability_id,实际: {errors[0]}"

    def test_validate_capability_id_legal_passes(self):
        """合法 id(小写字母/数字/连字符/下划线)零错误。"""
        sv = _load()
        assert sv.validate_capability_id("gameplay-auction") == []
        assert sv.validate_capability_id("ui_hud2") == []

    def test_validate_synthesized_package_illegal_id_early_return(self):
        """非法 capability_id 时 validate_synthesized_package 直接返回格式错误,
        不再做 template_id 比对等无意义检查(错误列表恰好一条)。"""
        sv = _load()
        errors = sv.validate_synthesized_package("../../evil", _legal_package(), WHITELIST)
        assert len(errors) == 1, f"期望仅一条格式错误,实际: {errors}"
        assert "capability_id" in errors[0] and "../../evil" in errors[0], \
            f"错误文案应含字段名与非法值,实际: {errors[0]}"
