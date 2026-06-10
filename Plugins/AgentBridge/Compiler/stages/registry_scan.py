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


def _scan_manifest_bindings(
    manifest_path: Path,
    registry: Dict[str, Dict[str, Any]],
    template_source: str,
) -> None:
    """读取单个 manifest 的 capability_bindings,把 registry 中尚不存在的 capability 填入。

    冲突语义:registry 已有同名 capability 时一律不覆盖。优先级由调用方的分遍
    扫描顺序保证(正式库一遍在前,synthesized 一遍在后),不依赖目录字母序。
    """
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    except Exception:
        # 损坏的 manifest 静默跳过,不中断整个扫描
        return

    bindings = manifest.get("capability_bindings") or []
    if not bindings:
        # 无 capability_bindings 的 manifest(如纯 UI flow 模板)不参与注册
        return

    if template_source == "synthesized" and manifest.get("review_status") != APPROVED:
        # synthesized 区未经审批的模板:对注册表不可见
        return

    template_id = manifest.get("template_id", "")
    for binding in bindings:
        capability_id = binding.get("capability_id", "")
        if not capability_id or not binding.get("instance_id"):
            # 不完整的 binding 条目静默跳过
            continue
        if capability_id in registry:
            # 同名 capability 已注册:保留先入条目(本遍内=先扫到的;跨遍=高优先级遍)
            continue
        registry[capability_id] = _binding_to_config(binding, template_id, template_source)


def scan_capability_registry(templates_root: str | Path | None = None) -> Dict[str, Dict[str, Any]]:
    """扫描模板树,构建 capability_id → 节点配置映射。

    三遍扫描保证优先级与 rglob 字母序无关(修复 synthesized 目录名靠前时抢跑正式库的 bug):
      1. 第一遍只扫正式库 manifest(非 synthesized 目录),正式库内部重复保留先扫到的。
      2. 第二遍扫 synthesized 区(仅 review_status==approved),只填正式库未占用的 capability。
      3. 第三遍占位文件(registry_placeholders.yaml),只填前两遍均未提供的条目。

    参数:
        templates_root: 模板根目录路径;传 None 时使用 DEFAULT_TEMPLATES_ROOT。

    返回:
        capability_id → 节点配置字典的映射。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    registry: Dict[str, Dict[str, Any]] = {}

    # synthesized 隔离区路径,用于把 manifest 分流到正式库遍 / synthesized 遍
    synthesized_root = root / SYNTHESIZED_DIR
    all_manifests = sorted(root.rglob("manifest.yaml"))
    official_manifests = [p for p in all_manifests if synthesized_root not in p.parents]
    synthesized_manifests = [p for p in all_manifests if synthesized_root in p.parents]

    # ── 第一遍:正式库 manifest(无 review_status 字段,默认信任,spec §3 第 2 条) ──
    for manifest_path in official_manifests:
        _scan_manifest_bindings(manifest_path, registry, "plugin_skill_template")

    # ── 第二遍:synthesized 隔离区(仅 approved,且不覆盖正式库同名 capability) ──
    for manifest_path in synthesized_manifests:
        _scan_manifest_bindings(manifest_path, registry, "synthesized")

    # ── 第三遍:补充占位数据文件中未被 manifest 覆盖的 capability ──
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
