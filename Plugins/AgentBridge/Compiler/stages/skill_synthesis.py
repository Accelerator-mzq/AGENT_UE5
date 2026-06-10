# -*- coding: utf-8 -*-
"""Phase 13 S3.5 Skill 合成环节。

职责:为 capability gap 准备合成载荷(prepare)、接收 agent 产物并校验落盘(save)、
生成人审清单。本模块无相对导入,经 importlib 加载兄弟模块,便于独立测试。

信任链:save 内强制机器校验(第一道 gate);落盘 review_status=pending_review,
人审改 approved 后才会被 registry_scan 纳入(第二道 gate)。

安全约束:save 只落盘 FILE_SPEC 中的 6 个规范文件名;six_files 出现任何
规范外 key(含路径分隔符的穿越企图)一律 rejected,错误文案列出非法文件名。
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

_STAGES_DIR = Path(__file__).resolve().parent
DEFAULT_TEMPLATES_ROOT = Path(__file__).resolve().parents[2] / "SkillTemplates"
# synthesized 隔离区子目录名(与 registry_scan.SYNTHESIZED_DIR 同义,
# 本模块不在 import 期加载兄弟模块,故本地定义一份常量)
SYNTHESIZED_DIR_NAME = "synthesized"

# 6 文件规范:key=落盘文件名(唯一允许写盘的名字),value=给 agent 的内容说明
FILE_SPEC = {
    "manifest.yaml": "身份证:template_id=synthesized.<capability_id>.v1、template_source=synthesized、review_status=pending_review、can_emit_families(白名单内)、capability_bindings 列表(capability_id/instance_id/convergence_priority/fragment_family,必要时 depends_on_capabilities)",
    "system_prompt.md": "人设:本 skill 是哪类领域专家、必须遵守的硬规则",
    "domain_prompt.md": "领域知识:该玩法的设计空间、维度与取舍(必须与 GDD 描述一致)",
    "evaluator_prompt.md": "自检清单:生成结果按什么标准检查遗漏与冲突",
    "input_selector.yaml": "取料单:include_sections/exclude_sections,从上游产物选取输入字段",
    "output_schema.json": "出货合同:draft-07 JSON Schema,root 与所有嵌套 object 必须 additionalProperties:false",
}


def _load_sibling(name: str):
    """经 importlib 加载同目录兄弟模块(本目录未安装为包,不能相对导入)。"""
    spec = importlib.util.spec_from_file_location(name, _STAGES_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pick_exemplars(templates_root: Path, domain_type: str, limit: int = 2) -> List[Dict[str, str]]:
    """选取 few-shot 范例模板:gameplay 取 genre_packs 下、baseline 取 baseline 下,
    按目录名排序取前 limit 个(确定性选取,不做语义相似度——防固化守则)。"""
    base = templates_root / ("genre_packs" if domain_type == "gameplay" else "baseline")
    exemplars: List[Dict[str, str]] = []
    if not base.is_dir():
        return exemplars
    for manifest_path in sorted(base.rglob("manifest.yaml"))[:limit]:
        bundle: Dict[str, str] = {"_dir": str(manifest_path.parent)}
        for name in FILE_SPEC:
            file_path = manifest_path.parent / name
            bundle[name] = file_path.read_text(encoding="utf-8") if file_path.is_file() else ""
        exemplars.append(bundle)
    return exemplars


def build_synthesis_prepare_payload(
    capability_id: str,
    gap: Dict[str, Any],
    gdd_excerpt: str,
    constraints: Dict[str, Any],
    templates_root: str | Path | None = None,
) -> Dict[str, Any]:
    """组装合成 prepare 载荷(MCP 工具直接透传给 agent)。"""
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    registry_scan = _load_sibling("registry_scan")
    whitelist = sorted(registry_scan.execution_family_whitelist(root))
    return {
        "capability_id": capability_id,
        "gap": gap,
        "gdd_excerpt": gdd_excerpt,
        "constraints": constraints,
        "file_spec": FILE_SPEC,
        "exemplars": _pick_exemplars(root, gap.get("domain_type", "gameplay")),
        "family_whitelist": whitelist,
        "naming_rules": {
            "template_id": f"synthesized.{capability_id}.v1",
            "package_dir": f"SkillTemplates/synthesized/{capability_id}/",
            "instance_id_prefix": "skill-",
        },
        "instructions": (
            "你正在为缺失的能力现场合成一个 SkillTemplate(6 文件包)。"
            "domain_prompt 必须忠实于 gdd_excerpt 的玩法描述;"
            "output_schema 的字段要覆盖该玩法的关键设计点;"
            "can_emit_families 与 fragment_family 只能从 family_whitelist 中选;"
            "完成后调用 compiler_skill_synthesis_save 提交,校验失败会返回具体错误,修正后重提。"
        ),
    }


def save_synthesized_package(
    capability_id: str,
    six_files: Dict[str, str],
    templates_root: str | Path | None = None,
    family_whitelist: Set[str] | None = None,
) -> Dict[str, Any]:
    """机器校验后落盘合成包;失败返回错误列表且不落盘(agent 重试闭环)。

    落盘安全:只遍历 FILE_SPEC 的 6 个规范文件名写盘;six_files 中出现的
    任何额外 key(含 '../' 等路径穿越形式)直接 rejected,不触盘。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    if family_whitelist is None:
        registry_scan = _load_sibling("registry_scan")
        family_whitelist = registry_scan.execution_family_whitelist(root)

    errors: List[str] = []

    # ── 第一道防线:文件名集合校验(在内容校验之前,防路径穿越触盘) ──
    extra_keys = sorted(set(six_files) - set(FILE_SPEC))
    if extra_keys:
        errors.append(
            f"包含规范外的多余文件: {extra_keys}。"
            f"仅允许提交这 6 个文件: {sorted(FILE_SPEC)}"
        )

    # ── 第二道防线:内容机器校验(缺件/manifest 契约/schema/family 白名单) ──
    validator = _load_sibling("synthesis_validator")
    errors.extend(
        validator.validate_synthesized_package(capability_id, six_files, set(family_whitelist))
    )
    if errors:
        return {"status": "rejected", "errors": errors, "package_dir": ""}

    # 校验全过才触盘;只写 FILE_SPEC 的 6 个名字(此时 validator 已保证全部存在非空)
    package_dir = root / "synthesized" / capability_id
    package_dir.mkdir(parents=True, exist_ok=True)
    for name in FILE_SPEC:
        (package_dir / name).write_text(six_files[name], encoding="utf-8")
    return {"status": "saved", "errors": [], "package_dir": str(package_dir)}


def _load_manifest_or_none(manifest_path: Path) -> Optional[Dict[str, Any]]:
    """读取 manifest;解析异常或顶层非 dict 时返回 None(调用方标'损坏')。"""
    try:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return manifest if isinstance(manifest, dict) else None


def _render_package_entry(package_dir: Path, status_line: str) -> List[str]:
    """渲染单个合成包的清单条目(三级标题 + 状态/目录/重点文件)。"""
    return [
        f"### {package_dir.name}",
        f"- 状态: {status_line}",
        f"- 目录: `{package_dir}`",
        f"- 重点文件: `{package_dir / 'output_schema.json'}` / `{package_dir / 'domain_prompt.md'}` / `{package_dir / 'evaluator_prompt.md'}`",
        "",
    ]


def generate_synthesis_review(
    run_dir: str | Path,
    templates_root: str | Path | None = None,
) -> str:
    """生成人审清单 synthesis_review.md(双 gate 的第二道入口)。

    分组规则:pending_review(及其他未审批状态、manifest 损坏件)排前作为人审待办,
    approved 归"已审批"段;损坏 manifest 标"损坏,须排查"而非让清单生成崩掉。
    """
    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    synthesized_root = root / SYNTHESIZED_DIR_NAME

    # 按 review_status 分两组:(目录, 状态行) 元组列表
    pending: List[Tuple[Path, str]] = []
    approved: List[Tuple[Path, str]] = []
    if synthesized_root.is_dir():
        for manifest_path in sorted(synthesized_root.rglob("manifest.yaml")):
            package_dir = manifest_path.parent
            manifest = _load_manifest_or_none(manifest_path)
            if manifest is None:
                # 坏 manifest:留在待办组并显式标损坏(容错,不中断清单生成)
                pending.append((package_dir, "manifest 损坏,须排查(无法解析或顶层非 mapping)"))
                continue
            status = manifest.get("review_status", "?")
            entry = (package_dir, f"`review_status: {status}`")
            if status == "approved":
                approved.append(entry)
            else:
                pending.append(entry)

    lines = [
        "# 合成 Skill 人审清单",
        "",
        "审核要点:1) domain_prompt 与 GDD 玩法描述一致;2) output_schema 覆盖关键设计点;",
        "3) evaluator_prompt 能查出遗漏;4) 与最相近人写模板的丰富度对照(软基准,不做硬指标)。",
        "",
        "通过方式:把对应包 manifest.yaml 的 `review_status: pending_review` 改为 `approved`,",
        "然后重跑 Stage 3。未改为 approved 的包,编译器不会消费。",
        "",
        "## 待审包(人审待办)",
        "",
    ]
    if pending:
        for package_dir, status_line in pending:
            lines.extend(_render_package_entry(package_dir, status_line))
    else:
        lines.extend(["(无待审包)", ""])

    lines.extend(["## 已审批(approved)", ""])
    if approved:
        for package_dir, status_line in approved:
            lines.extend(_render_package_entry(package_dir, status_line))
    else:
        lines.extend(["(无已审批包)", ""])

    run_path = Path(run_dir)
    run_path.mkdir(parents=True, exist_ok=True)
    target = run_path / "synthesis_review.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    return str(target)
