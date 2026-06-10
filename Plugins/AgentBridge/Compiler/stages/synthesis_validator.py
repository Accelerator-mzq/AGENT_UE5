# -*- coding: utf-8 -*-
"""Phase 13 合成包机器校验器(双 gate 的第一道)。

只做结构与契约校验,不做语义判断(语义质量归人审 gate)。
防固化守则:本模块不携带游戏领域语义;family 白名单由调用方传入(数据驱动)。

公开 API:
    validate_synthesized_package(capability_id, package, family_whitelist) -> List[str]
    返回错误列表,为空即通过。错误文案直接回给 agent 做修正重试,必须具体可操作。
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Set

import yaml

# ---- 必需文件集合 ----
REQUIRED_FILES = {
    "manifest.yaml",
    "system_prompt.md",
    "domain_prompt.md",
    "evaluator_prompt.md",
    "input_selector.yaml",
    "output_schema.json",
}

# ---- manifest 必填顶层字段 ----
REQUIRED_MANIFEST_FIELDS = {
    "template_id",
    "display_name",
    "template_kind",
    "template_version",
    "template_source",
    "review_status",
    "realization_class",
    "can_emit_families",
    "capability_bindings",
}

# ---- capability_binding 条目必填字段 ----
REQUIRED_BINDING_FIELDS = {
    "capability_id",
    "instance_id",
    "convergence_priority",
    "fragment_family",
}


def _check_additional_properties(node: Any, path: str, errors: List[str]) -> None:
    """递归检查每个 object 节点均显式声明 additionalProperties: false。

    LLM 合成的 schema 常遗漏嵌套对象的此字段,导致运行时接受不期望的键。
    校验器在此强制要求,错误信息包含 JSON 路径方便 agent 精准修正。

    递归覆盖路径: properties / items / anyOf / oneOf / allOf / $defs / definitions。
    LLM 爱用 anyOf 做联合类型,嵌在组合器里的 object 同样必须收口。
    """
    if not isinstance(node, dict):
        return
    if node.get("type") == "object":
        if node.get("additionalProperties") is not False:
            errors.append(
                f"output_schema {path}: object 节点缺 additionalProperties: false"
            )
        # 递归检查 properties 下每个子节点
        properties = node.get("properties")
        if isinstance(properties, dict):
            for key, child in properties.items():
                _check_additional_properties(child, f"{path}.{key}", errors)
    # 处理数组的 items
    if "items" in node:
        _check_additional_properties(node["items"], f"{path}[]", errors)
    # 组合器: anyOf / oneOf / allOf 是 list of schemas
    for combinator in ("anyOf", "oneOf", "allOf"):
        subschemas = node.get(combinator)
        if isinstance(subschemas, list):
            for index, sub in enumerate(subschemas):
                _check_additional_properties(
                    sub, f"{path}.{combinator}[{index}]", errors
                )
    # 定义区: $defs / definitions 是 dict of schemas
    for defs_key in ("$defs", "definitions"):
        defs = node.get(defs_key)
        if isinstance(defs, dict):
            for name, sub in defs.items():
                _check_additional_properties(
                    sub, f"{path}.{defs_key}.{name}", errors
                )


def validate_synthesized_package(
    capability_id: str,
    package: Dict[str, Optional[str]],
    family_whitelist: Set[str],
) -> List[str]:
    """校验合成包;返回错误列表,为空即通过。

    Args:
        capability_id:     本次合成的 capability 标识符(即落盘目录名)。
        package:           6 文件内容字典,key=文件名,value=文件文本内容(可能为 None)。
        family_whitelist:  执行层允许的 fragment_family 集合,由调用方传入(数据驱动)。

    Returns:
        错误列表;为空表示通过机器 gate。文案直接回给 agent,必须具体可操作。
    """
    errors: List[str] = []

    # =========================================================
    # 检查点 1: 6 文件齐全且非空
    #   用 (... or "") 防御 agent 传 None 值导致 .strip() AttributeError
    # =========================================================
    for name in sorted(REQUIRED_FILES):
        if not (package.get(name) or "").strip():
            errors.append(f"缺少或为空: {name}")
    if errors:
        # 文件都不齐,后续检查无意义,提前返回
        return errors

    # =========================================================
    # 检查点 2: manifest.yaml 解析与顶层类型
    #   yaml.safe_load 返回 list/scalar 时给出明确错误,防止后续 .get() AttributeError
    # =========================================================
    try:
        manifest = yaml.safe_load(package["manifest.yaml"])
    except Exception as exc:
        return [f"manifest.yaml 解析失败: {exc}"]

    if not isinstance(manifest, dict):
        # 顶层若为 list 或 None,给出可操作的指导
        return [
            f"manifest.yaml 顶层必须是 mapping(dict),实际类型: {type(manifest).__name__}。"
            "请确认 YAML 以 'key: value' 形式书写,而非以 '- item' 开头的列表。"
        ]

    # =========================================================
    # 检查点 3: manifest 必填字段完整性
    # =========================================================
    for field in sorted(REQUIRED_MANIFEST_FIELDS):
        if field not in manifest:
            errors.append(f"manifest 缺必填字段: {field}")

    # =========================================================
    # 检查点 4: template_id 与落盘目录命名一致
    #   规则: template_id = "synthesized.<capability_id>.v1"
    # =========================================================
    expected_template_id = f"synthesized.{capability_id}.v1"
    actual_template_id = manifest.get("template_id")
    if actual_template_id != expected_template_id:
        errors.append(
            f"template_id 必须为 '{expected_template_id}',"
            f"实际为 {actual_template_id!r}。"
            f"目录名(capability_id)与 template_id 中段必须一致。"
        )

    # template_source 固定值校验
    if manifest.get("template_source") != "synthesized":
        errors.append(
            "manifest.template_source 必须为 'synthesized',"
            f"实际为 {manifest.get('template_source')!r}"
        )

    # review_status 固定值校验(审批是人的动作,落盘时必须为 pending_review)
    if manifest.get("review_status") != "pending_review":
        errors.append(
            "合成落盘时 review_status 必须为 'pending_review'(审批是人的动作),"
            f"实际为 {manifest.get('review_status')!r}"
        )

    # =========================================================
    # 检查点 5: capability_bindings 条目完整性
    #   先做 isinstance 守卫: 标量字符串是 truthy,会绕过 'or []' 被逐字符迭代,
    #   产生大量单字符垃圾错误掩盖真因——非 list 时给一条明确错误并跳过迭代
    # =========================================================
    bindings = manifest.get("capability_bindings") or []
    if not isinstance(bindings, list):
        errors.append(
            f"capability_bindings 必须是列表,实际: {type(bindings).__name__}。"
            "请以 '- capability_id: ...' 的 YAML 列表形式书写。"
        )
        bindings = []  # 置空以跳过后续所有针对 bindings 的迭代
    elif not bindings:
        errors.append("capability_bindings 不能为空,至少需要一个绑定条目")
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            errors.append(f"capability_bindings[{index}] 必须是 mapping,实际: {type(binding).__name__}")
            continue
        for field in sorted(REQUIRED_BINDING_FIELDS):
            if field not in binding:
                errors.append(f"capability_bindings[{index}] 缺字段: {field}")
        # binding.capability_id 必须与传入的 capability_id 一致
        if binding.get("capability_id") != capability_id:
            errors.append(
                f"capability_bindings[{index}].capability_id 必须为 '{capability_id}',"
                f"实际为 {binding.get('capability_id')!r}"
            )

    # =========================================================
    # 检查点 6: family 白名单边界(执行词表硬边界)
    #   can_emit_families 和每个 binding.fragment_family 均须在白名单内
    #   同样先做 isinstance 守卫,防标量字符串被逐字符迭代
    # =========================================================
    families = manifest.get("can_emit_families") or []
    if not isinstance(families, list):
        errors.append(
            f"can_emit_families 必须是列表,实际: {type(families).__name__}。"
            "请以 '- family_name' 的 YAML 列表形式书写。"
        )
    else:
        for family in families:
            if family not in family_whitelist:
                errors.append(
                    f"can_emit_families 越界: '{family}' 不在执行层白名单内。"
                    f"允许值: {sorted(family_whitelist)}"
                )
    for index, binding in enumerate(bindings):
        if not isinstance(binding, dict):
            continue
        family = binding.get("fragment_family", "")
        if family and family not in family_whitelist:
            errors.append(
                f"capability_bindings[{index}].fragment_family 越界: '{family}' 不在执行层白名单内。"
                f"允许值: {sorted(family_whitelist)}"
            )

    # =========================================================
    # 检查点 7: output_schema.json 合法 JSON + 合法 draft-07 schema
    #           + 递归 additionalProperties: false
    # =========================================================
    try:
        schema = json.loads(package["output_schema.json"])
    except Exception as exc:
        errors.append(f"output_schema.json 解析失败(非合法 JSON): {exc}")
        return errors

    # 顶层必须是 dict,不接受数组等其他类型
    if not isinstance(schema, dict):
        errors.append(
            f"output_schema.json 顶层必须是 JSON object({{...}}),实际类型: {type(schema).__name__}。"
            "请检查是否误将数组或标量作为根节点。"
        )
        return errors

    # 用 jsonschema 校验 schema 本身是否合法 draft-07
    try:
        from jsonschema import Draft7Validator  # 延迟导入,减少启动依赖
        Draft7Validator.check_schema(schema)
    except Exception as exc:
        errors.append(f"output_schema 不是合法 draft-07 schema: {exc}")

    # 递归检查所有 object 节点的 additionalProperties
    _check_additional_properties(schema, "<root>", errors)

    return errors
