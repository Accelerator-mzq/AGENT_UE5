# -*- coding: utf-8 -*-
"""Phase 13 合成包机器校验器(双 gate 的第一道)。

只做结构与契约校验,不做语义判断(语义质量归人审 gate)。
防固化守则:本模块不携带游戏领域语义;family 白名单由调用方传入(数据驱动)。

公开 API:
    validate_synthesized_package(capability_id, package, family_whitelist) -> List[str]
    validate_capability_id(capability_id) -> List[str]
    返回错误列表,为空即通过。错误文案直接回给 agent 做修正重试,必须具体可操作。
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Set

import yaml
from jsonschema import Draft7Validator

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

# capability_id 格式硬约束(单一事实源):仅小写字母/数字/连字符/下划线,
# 且以字母或数字开头。capability_id 直接用作落盘目录名,放开此约束会引入
# 路径穿越('../../evil' 实测可逃出 synthesized/ 隔离区落盘到上级目录)。
CAPABILITY_ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]*\Z")


def validate_capability_id(capability_id: Any) -> List[str]:
    """校验 capability_id 格式;返回错误列表,为空即通过。

    capability_id 是落盘目录名,本校验是路径穿越的第一道防线,
    save/prepare 入口与 validate_synthesized_package 开头均复用本函数。
    """
    if not isinstance(capability_id, str) or not CAPABILITY_ID_PATTERN.match(capability_id):
        return [
            "capability_id 格式非法(仅允许小写字母/数字/连字符/下划线,"
            f"且以字母或数字开头): {capability_id!r}"
        ]
    return []


# schema 递归最大深度:超过即报错停止,防恶意/失控嵌套触发 RecursionError
# (合成重试闭环依赖校验器永不抛异常——异常会被误归因甚至中断闭环)
_MAX_SCHEMA_DEPTH = 64

# dict-of-schemas 递归区段: value 是 {名字: 子schema} 映射,不受 type 门控
# (LLM 高频遗漏 type: object 声明,只写 properties——递归不能依赖 type)
_DICT_OF_SCHEMAS_KEYS = ("properties", "$defs", "definitions")

# list-of-schemas 递归区段: value 是 [子schema, ...] 列表
# (items 在 draft-07 可为单 schema 或 tuple 形列表,统一包成列表处理)
_LIST_OF_SCHEMAS_KEYS = ("items", "anyOf", "oneOf", "allOf")


def _check_additional_properties(
    node: Any, path: str, errors: List[str], depth: int = 0
) -> None:
    """递归检查每个 object 节点均显式声明 additionalProperties: false。

    LLM 合成的 schema 常遗漏嵌套对象的此字段,导致运行时接受不期望的键。
    校验器在此强制要求,错误信息包含 JSON 路径方便 agent 精准修正。

    递归覆盖路径:
      - dict-of-schemas: properties / $defs / definitions(不受 type 门控)
      - list-of-schemas: items(单 schema 自动包成单元素列表)/ anyOf / oneOf / allOf
    深度超过 _MAX_SCHEMA_DEPTH 时报错并停止,防 RecursionError 逃逸。
    """
    if not isinstance(node, dict):
        return
    if depth > _MAX_SCHEMA_DEPTH:
        errors.append(
            f"output_schema {path}: 嵌套过深(>{_MAX_SCHEMA_DEPTH} 层),请简化结构"
        )
        return

    # additionalProperties 检查仅针对显式声明 type: object 的节点
    if node.get("type") == "object":
        if node.get("additionalProperties") is not False:
            errors.append(
                f"output_schema {path}: object 节点缺 additionalProperties: false"
            )

    # dict-of-schemas 区段: 不受 type 门控,只要存在就递归
    for section in _DICT_OF_SCHEMAS_KEYS:
        children = node.get(section)
        if isinstance(children, dict):
            for name, child in children.items():
                # properties 的路径保持简短(<root>.字段名);定义区带区段前缀
                child_path = (
                    f"{path}.{name}" if section == "properties"
                    else f"{path}.{section}.{name}"
                )
                _check_additional_properties(child, child_path, errors, depth + 1)

    # list-of-schemas 区段: items 单 schema 形包成单元素列表统一处理
    for section in _LIST_OF_SCHEMAS_KEYS:
        subschemas = node.get(section)
        if subschemas is None:
            continue
        if not isinstance(subschemas, list):
            subschemas = [subschemas]
        for index, sub in enumerate(subschemas):
            _check_additional_properties(
                sub, f"{path}.{section}[{index}]", errors, depth + 1
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
    # =========================================================
    # 检查点 0: capability_id 格式(路径穿越防线)
    #   非法时直接返回——后续 template_id 比对等检查全部失去意义
    # =========================================================
    id_errors = validate_capability_id(capability_id)
    if id_errors:
        return id_errors

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
        if "fragment_family" not in binding:
            continue  # 字段缺失已由检查点 5 的必填字段检查报错,此处不重复
        family = binding.get("fragment_family")
        if not family:
            # 空串/None 不得静默绕过白名单(空值既不在白名单内也不该被跳过)
            errors.append(f"capability_bindings[{index}].fragment_family 不能为空")
        elif family not in family_whitelist:
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
    # (Draft7Validator 在模块顶部导入: 缺依赖应在加载期立即暴露,
    #  而非在校验期被 except 吞掉误归因为 agent 的 schema 错误导致重试死循环)
    try:
        Draft7Validator.check_schema(schema)
    except Exception as exc:
        errors.append(f"output_schema 不是合法 draft-07 schema: {exc}")

    # 递归检查所有 object 节点的 additionalProperties
    _check_additional_properties(schema, "<root>", errors)

    return errors
