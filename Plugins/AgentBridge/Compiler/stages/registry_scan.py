# -*- coding: utf-8 -*-
"""Phase 13 能力注册表扫描。

把原 skill_graph_planning 两张硬编码表替换为数据扫描:
  - 各 SkillTemplate manifest.yaml 的 capability_bindings(自描述)
  - SkillTemplates/registry_placeholders.yaml(无模板占位节点)
  - SkillTemplates/synthesized/ 隔离区(仅 review_status=approved 纳入)

防固化守则:本模块只做结构扫描,不携带任何游戏领域语义。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

# 默认模板根目录:相对本文件向上两级到插件根,再进 SkillTemplates
DEFAULT_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "SkillTemplates"
# 占位数据文件名(存放尚无模板目录的 capability 元数据)
PLACEHOLDERS_FILE = "registry_placeholders.yaml"
# synthesized 隔离区子目录名
SYNTHESIZED_DIR = "synthesized"
# 只有这个 review_status 值才允许 synthesized 节点进入注册表
APPROVED = "approved"


def _binding_to_config(binding: Dict[str, Any], template_id: str, template_source: str) -> Dict[str, Any]:
    """把一条 capability_binding 转成与原硬编码表同构的节点配置。

    字段对齐原则:所有原 GAMEPLAY_NODE_CONFIGS / BASELINE_NODE_CONFIGS 字段均保留,
    额外附加 template_source 与 fragment_family 供后续 Stage 使用。
    """
    return {
        "instance_id": binding["instance_id"],
        "template_id": template_id,
        "convergence_priority": binding["convergence_priority"],
        "related_clarification_items": list(binding.get("related_clarification_items", [])),
        "planning_notes": list(binding.get("planning_notes", [])),
        "template_source": template_source,
        "fragment_family": binding.get("fragment_family", ""),
        "depends_on_capabilities": list(binding.get("depends_on_capabilities", [])),
    }


def scan_capability_registry(templates_root: str | Path | None = None) -> Dict[str, Dict[str, Any]]:
    """扫描模板树,构建 capability_id → 节点配置映射。

    扫描顺序与优先级规则:
      1. 正式库 manifest(非 synthesized 目录下)最优先,先扫到的同名 capability 保留。
      2. synthesized 区仅 review_status==approved 才进入候选,且不覆盖正式库同名条目。
      3. 占位文件(registry_placeholders.yaml)最后处理,只填充正式库与 synthesized 均未提供的条目。

    参数:
        templates_root: 模板根目录路径;传 None 时使用 DEFAULT_TEMPLATES_ROOT。

    返回:
        capability_id → 节点配置字典的映射。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    registry: Dict[str, Dict[str, Any]] = {}

    # synthesized 隔离区路径,用于判断扫描到的 manifest 是否属于 synthesized 区
    synthesized_root = root / SYNTHESIZED_DIR

    # ── 第一遍:扫描所有 manifest.yaml(含 synthesized 区) ──
    for manifest_path in sorted(root.rglob("manifest.yaml")):
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            # 损坏的 manifest 静默跳过,不中断整个扫描
            continue

        bindings = manifest.get("capability_bindings") or []
        if not bindings:
            # 无 capability_bindings 的 manifest(如纯 UI flow 模板)不参与注册
            continue

        # 判断是否在 synthesized 隔离区
        is_synthesized = synthesized_root in manifest_path.parents

        if is_synthesized and manifest.get("review_status") != APPROVED:
            # synthesized 区未经审批的模板:对注册表不可见
            continue

        template_id = manifest.get("template_id", "")
        # 正式库模板无 review_status 字段,默认信任(spec §3 第 2 条)
        template_source = "synthesized" if is_synthesized else "plugin_skill_template"

        for binding in bindings:
            capability_id = binding.get("capability_id", "")
            if not capability_id or not binding.get("instance_id"):
                # 不完整的 binding 条目静默跳过
                continue

            if capability_id in registry:
                if not is_synthesized:
                    # 正式库出现重复绑定:保留先扫到的(按路径排序),后续 Stage 3 可通过 metadata 警告
                    continue
                else:
                    # synthesized 不覆盖正式库条目
                    continue

            registry[capability_id] = _binding_to_config(binding, template_id, template_source)

    # ── 第二遍:补充占位数据文件中未被 manifest 覆盖的 capability ──
    placeholders_path = root / PLACEHOLDERS_FILE
    if placeholders_path.is_file():
        try:
            data = yaml.safe_load(placeholders_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}

        for entry in data.get("placeholders", []):
            capability_id = entry.get("capability_id", "")
            if not capability_id or capability_id in registry:
                # 已被 manifest 覆盖或字段缺失:跳过
                continue
            registry[capability_id] = _binding_to_config(
                entry,
                entry.get("template_id", ""),  # 占位节点的 template_id 直接从条目读取
                "future_baseline_template",      # 占位节点的来源标记
            )

    return registry


def execution_family_whitelist(templates_root: str | Path | None = None) -> set[str]:
    """执行层 family 白名单 = 正式库(非 synthesized)manifest can_emit_families 的并集。

    同时收录 capability_bindings 里的 fragment_family 与占位节点的 fragment_family,
    确保 player_management_spec 等"仅出现在 binding、不在宿主 can_emit_families"的词汇也被纳入。

    数据驱动,不维护硬编码清单(防固化守则)。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    synthesized_root = root / SYNTHESIZED_DIR
    families: set[str] = set()

    # 扫描正式库 manifest(跳过 synthesized 区)
    for manifest_path in root.rglob("manifest.yaml"):
        if synthesized_root in manifest_path.parents:
            continue
        try:
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue

        # 模板自身宣告的 can_emit_families
        families.update(manifest.get("can_emit_families") or [])

        # capability_bindings 里的 fragment_family(节点产出片段族,语义独立于 can_emit_families)
        for binding in manifest.get("capability_bindings") or []:
            if binding.get("fragment_family"):
                families.add(binding["fragment_family"])

    # 占位节点的 fragment_family 也属于执行层既有词表
    placeholders_path = root / PLACEHOLDERS_FILE
    if placeholders_path.is_file():
        try:
            data = yaml.safe_load(placeholders_path.read_text(encoding="utf-8")) or {}
        except Exception:
            data = {}
        for entry in data.get("placeholders", []):
            if entry.get("fragment_family"):
                families.add(entry["fragment_family"])

    return families
