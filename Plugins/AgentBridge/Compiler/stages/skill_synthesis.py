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
import os
import shutil
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


# _load_sibling 的模块级缓存:同名兄弟模块全进程只 exec 一次。
# 约束:兄弟模块不得引入跨实例类比较(isinstance 跨多次加载会失败)或可变全局态,
# 否则缓存实例与测试中各自加载的实例之间会出现状态分裂。
_SIBLING_CACHE: Dict[str, Any] = {}


def _load_sibling(name: str):
    """经 importlib 加载同目录兄弟模块(本目录未安装为包,不能相对导入);带缓存。"""
    cached = _SIBLING_CACHE.get(name)
    if cached is None:
        spec = importlib.util.spec_from_file_location(name, _STAGES_DIR / f"{name}.py")
        cached = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cached)
        _SIBLING_CACHE[name] = cached
    return cached


def _pick_exemplars(templates_root: Path, domain_type: str, limit: int = 2) -> List[Dict[str, str]]:
    """选取 few-shot 范例模板:gameplay 取 genre_packs 下、baseline 取 baseline 下,
    按目录名排序取前 limit 个(确定性选取,不做语义相似度——防固化守则)。"""
    base = templates_root / ("genre_packs" if domain_type == "gameplay" else "baseline")
    exemplars: List[Dict[str, str]] = []
    if not base.is_dir():
        return exemplars
    for manifest_path in sorted(base.rglob("manifest.yaml"))[:limit]:
        # _dir 用相对 templates_root 的 POSIX 形式:载荷不泄露绝对盘符路径,跨机器可比
        relative_dir = manifest_path.parent.relative_to(templates_root).as_posix()
        bundle: Dict[str, str] = {"_dir": relative_dir}
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
    """组装合成 prepare 载荷(MCP 工具直接透传给 agent)。

    capability_id 格式非法时抛 ValueError(fail-fast):prepare 的 capability_id
    来自 skill_graph gaps,正常流程不可能非法,非法即编程错误,不走 agent 重试
    闭环;同时防止 naming_rules.package_dir 携带穿越路径误导 agent。
    """
    # ── 入口防线: capability_id 格式校验(单一事实源在 synthesis_validator) ──
    validator = _load_sibling("synthesis_validator")
    id_errors = validator.validate_capability_id(capability_id)
    if id_errors:
        raise ValueError(id_errors[0])

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
    provenance: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """机器校验后落盘合成包;失败返回错误列表且不落盘(agent 重试闭环)。

    provenance(终审 I-2,spec §4.4 溯源戳记):形如
    {"synthesis_run_id": "...", "synthesized_by": "..."} 的字典;校验通过后、
    落盘前由本函数注入 manifest 顶层(save 注入而非 agent 自报,agent 无法伪造)。
    None 时不注入、manifest 原文落盘(向后兼容,不重写不重排)。
    synthesis_validator 对 manifest 是必填检查而非白名单,多出的戳记键不会被拒。

    返回 status 语义:
      - "rejected": 内容/契约/状态不合规(含 approved 防覆盖),agent 修正后可重试
      - "failed":   校验全过但落盘 IO 失败(环境错误,非内容错误),原样重试或人工排查
      - "saved":    成功落盘 pending_review

    落盘安全(对称双侧防线):
      - capability_id 直接用作落盘目录名,入口先做格式校验,非法立即 rejected
        (在任何路径拼接/mkdir 之前;'../../evil' 实测可逃出 synthesized/ 隔离区)
      - six_files 只遍历 FILE_SPEC 的 6 个规范文件名写盘;出现任何额外 key
        (含 '../' 等路径穿越形式)直接 rejected,不触盘

    事务性落盘(temp-then-swap):全部文件先写入 .tmp-<capability_id>/(manifest
    暂存为 manifest.yaml.part),写完整后换名到最终目录,最后把 .part 改回
    manifest.yaml。manifest.yaml 是 registry_scan 与审阅清单的发现锚点,temp 区
    始终没有这个文件名,任何中途失败的半成品对两个消费方都不可见;失败即清理 temp。
    残余窗口:旧 pending 包 rmtree 与换名之间进程被杀会丢旧包(可重新合成,接受)。
    """
    # ── 入口防线: capability_id 格式校验(单一事实源在 synthesis_validator) ──
    validator = _load_sibling("synthesis_validator")
    id_errors = validator.validate_capability_id(capability_id)
    if id_errors:
        return {"status": "rejected", "errors": id_errors, "package_dir": ""}

    root = Path(templates_root) if templates_root else DEFAULT_TEMPLATES_ROOT
    synthesized_root = root / SYNTHESIZED_DIR_NAME
    package_dir = synthesized_root / capability_id

    # ── approved 防覆盖: 已审批包是人审资产,拒绝静默重写(撤销审批是人的动作) ──
    # pending_review 现存包允许覆盖(agent 重试语义);manifest 损坏件覆盖即修复
    existing_manifest = _load_manifest_or_none(package_dir / "manifest.yaml") \
        if (package_dir / "manifest.yaml").is_file() else None
    if existing_manifest is not None and existing_manifest.get("review_status") == "approved":
        return {
            "status": "rejected",
            "errors": [
                f"该包已审批(review_status=approved),拒绝覆盖: {package_dir}。"
                "如需重合成,请人工先撤销审批(把 review_status 改回 pending_review)。"
            ],
            "package_dir": "",
        }

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
    errors.extend(
        validator.validate_synthesized_package(capability_id, six_files, set(family_whitelist))
    )
    if errors:
        return {"status": "rejected", "errors": errors, "package_dir": ""}

    # ── provenance 戳记注入(校验通过后、落盘前;在 six_files 副本上操作,不污染调用方) ──
    # validator 已保证 manifest.yaml 可解析且顶层为 mapping,safe_load 不会再失败
    files_to_write = dict(six_files)
    if provenance:
        manifest_data = yaml.safe_load(files_to_write["manifest.yaml"])
        manifest_data.update(provenance)
        files_to_write["manifest.yaml"] = yaml.safe_dump(
            manifest_data, allow_unicode=True, sort_keys=False
        )

    # ── 事务性落盘: temp-then-swap ──
    # capability_id 格式校验已禁 '.',故 '.tmp-' 前缀目录永不与合法包目录撞名,
    # rmtree 残留 temp 不可能误删真实包
    temp_dir = synthesized_root / f".tmp-{capability_id}"
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)  # 清理上次中断的残留
        temp_dir.mkdir(parents=True)
        # 只写 FILE_SPEC 的 6 个名字(此时 validator 已保证全部存在且为非空字符串);
        # manifest 暂存为 .part,保证 temp 区对 rglob("manifest.yaml") 的消费方不可见
        for name in FILE_SPEC:
            staged_name = "manifest.yaml.part" if name == "manifest.yaml" else name
            (temp_dir / staged_name).write_text(files_to_write[name], encoding="utf-8")
        if package_dir.exists():
            shutil.rmtree(package_dir)  # 覆盖 pending 包:换名前移除旧目录(Windows 必需)
        os.replace(temp_dir, package_dir)
        # 提交点: manifest.yaml 出现即包完整(此前任何失败,包都不可见)
        os.replace(package_dir / "manifest.yaml.part", package_dir / "manifest.yaml")
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return {
            "status": "failed",
            "errors": [f"落盘失败(IO/环境错误,非内容错误,可原样重试): {exc}"],
            "package_dir": "",
        }
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
