# -*- coding: utf-8 -*-
"""证据校验器:evidence_class 分级必交、路径存在、冒烟 pass、增量 hash 守门、文档引用对账。

机制分离:本模块只产出 {"status","errors"},状态流转归 story_store。
零游戏领域语义;自包含(不 import 包内其他模块)。
假设单写者顺序执行(与 story_store 同口径)。
"""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# evidence_class → 必交证据字段(spec §4.2/§4.3)
REQUIRED_EVIDENCE = {
    "Logic": ("files_changed", "test_report", "smoke_report"),
    "Integration": ("files_changed", "smoke_report"),
    "Visual": ("files_changed", "screenshots"),
    "Config": ("files_changed", "doc_paths"),
}

# 路径型证据字段(逐一检查相对 project_root 存在)
_PATH_FIELDS = ("files_changed", "test_report", "smoke_report", "screenshots", "doc_paths")

# 文档引用对账:反引号包裹的 UE 类名(A/U/F/E 前缀大驼峰)与资产路径
_CLASS_TOKEN = re.compile(r"`([AUFE][A-Z][A-Za-z0-9_]{2,})`")
_ASSET_TOKEN = re.compile(r"`(/[A-Za-z0-9_]+(?:/[A-Za-z0-9_.]+)+)`")

# 行为校验(P14-BL-05):InteractionSemantics 用例通过态 + README 键位 token
_PASS_STATES = {"success", "passed", "pass"}
_KEY_TOKEN = re.compile(r"\[([A-Za-z0-9]+)\]")


def _iter_paths(evidence: Dict[str, Any]):
    """遍历 evidence 中所有路径型字段，逐一 yield (field, 路径字符串)。"""
    for field in _PATH_FIELDS:
        value = evidence.get(field)
        if value is None:
            continue
        for item in (value if isinstance(value, list) else [value]):
            yield field, str(item)


def _sha256(path: Path) -> str:
    """计算文件的 SHA-256 十六进制摘要。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze_v0_baseline(project_root, run_dir, smoke_file_rel_paths: List[str]) -> Dict[str, Any]:
    """v0 PROCEED 后冻结冒烟用例 hash 基线,落盘 run 目录(人审窗口 1 的 runbook 步骤调用)。"""
    root = Path(project_root)
    # Windows 反斜杠统一转正斜杠，保证跨平台 key 一致
    files = {str(rel).replace("\\", "/"): _sha256(root / rel) for rel in smoke_file_rel_paths}
    baseline = {"files": files, "frozen_at": datetime.now(timezone.utc).isoformat()}
    path = Path(run_dir) / "v0_smoke_baseline.json"
    # 原子写入：先写临时文件再 replace，防止并发读到半写文件
    tmp = path.with_suffix(".json.part")
    tmp.write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return baseline


def _check_baseline(project_root: Path, baseline: Dict[str, Any]) -> List[str]:
    """对比现有文件 hash 与 v0 冻结基线，返回篡改/缺失错误列表。"""
    errors = []
    for rel, expected in baseline.get("files", {}).items():
        target = project_root / rel
        if not target.exists():
            errors.append(f"hash 守门: 基线文件缺失 {rel}")
        elif _sha256(target) != expected:
            errors.append(f"hash 守门: 基线文件被修改 {rel}(v0 冒烟用例 PROCEED 后冻结,不许动)")
    return errors


def _check_doc_references(doc_text: str, plugin_root: Path) -> List[str]:
    """文档提到的类/资产必须真实存在(spec §4.7 引用对账)。"""
    errors: List[str] = []
    source_dir = plugin_root / "Source"
    corpus = ""
    if source_dir.exists():
        # 扫描插件 Source 目录下所有 .h / .cpp 文件，拼接为语料库
        # errors="ignore" 容忍编码损坏字节;损坏恰落类名内为可接受的 over-strict(误报不漏报)
        # 拼接加换行分隔,防止文件 A 尾 + 文件 B 头跨界拼出假声明
        for ext in ("*.h", "*.cpp"):
            for f in sorted(source_dir.rglob(ext)):
                corpus += f.read_text(encoding="utf-8", errors="ignore") + "\n"
    # 检查文档中反引号包裹的 UE 类名是否出现在源码语料(词边界匹配,防前缀子串误放行)
    # 可选 MODULE_API 宏中缀:UE 导出类惯例为 class DEMOX_API AFoo,不加会大面积误拒
    for cls in sorted(set(_CLASS_TOKEN.findall(doc_text))):
        pattern = rf"(?:class|struct|enum class)\s+(?:[A-Z][A-Z0-9_]*_API\s+)?{re.escape(cls)}\b"
        if not re.search(pattern, corpus):
            errors.append(f"文档引用对账: 类 {cls} 在 plugin Source 中不存在")
    # 检查文档中反引号包裹的资产路径是否在 plugin Content 目录存在
    # UE Pkg.Object 点路径形式下 with_suffix 会替换最后一段点后缀,恰好命中包文件本体
    for asset in sorted(set(_ASSET_TOKEN.findall(doc_text))):
        parts = asset.strip("/").split("/")
        rel = Path(*parts[1:]) if len(parts) > 1 else Path(parts[0])
        candidates = [(plugin_root / "Content" / rel).with_suffix(suffix) for suffix in (".uasset", ".umap")]
        if not any(c.exists() for c in candidates):
            errors.append(f"文档引用对账: 资产 {asset} 在 plugin Content 中不存在")
    return errors


def _readme_key_tokens(readme_text: str) -> Optional[set]:
    """提取 README『## 键位』节中的 [Key] token;无该节返回 None(调用处报错)。"""
    lines = readme_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        # 键位须紧跟 `## ` 之后(容忍"## 键位表"等后缀,拒"## 其他键位说明"中段误匹配)
        if re.match(r"^##\s+键位", line.strip()):
            start = i + 1
            break
    if start is None:
        return None
    section = []
    for line in lines[start:]:
        if line.strip().startswith("## "):
            break
        section.append(line)
    return set(_KEY_TOKEN.findall("\n".join(section)))


def _check_interaction_claims(story: Dict[str, Any], evidence: Dict[str, Any],
                              root: Path, plugin_root) -> List[str]:
    """行为校验门禁(P14-BL-05):claims∪README 全集逐 key 对 InteractionSemantics 用例,
    claims ⊆ README。claims 为空整体放行(玩法/文档/反馈工单不强制)。"""
    claims = story.get("interaction_claims") or []
    if not claims:
        return []
    report_rel = evidence.get("test_report")
    if not report_rel or not (root / str(report_rel)).exists():
        return ["行为校验: interaction_claims 非空时必须提交 test_report(InteractionSemantics 用例报告)"]
    try:
        report = json.loads((root / str(report_rel)).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return [f"行为校验: test_report 不可解析: {exc}"]
    suites = report.get("suites") if isinstance(report, dict) else None
    if not isinstance(suites, list):
        return ["行为校验: test_report 缺 suites 数组(报告契约与冒烟报告同形)"]
    # 通过态用例名集合(大小写不敏感匹配 state)
    passing = {str(s.get("name", "")) for s in suites
               if str(s.get("state", "")).lower() in _PASS_STATES}

    errors: List[str] = []
    claimed = {c["input"] for c in claims}
    readme_tokens: set = set()
    if plugin_root is None:
        errors.append("行为校验: interaction_claims 非空时 evidence 必须带 plugin_root(README 对账需要)")
        # README 都查不了,后续全集逐 key 报"无用例"是噪声,早退
        return errors
    else:
        readme = Path(plugin_root) / "README.md"
        if not readme.exists():
            errors.append("行为校验: plugin README.md 不存在,无法做键位对账")
        else:
            tokens = _readme_key_tokens(readme.read_text(encoding="utf-8", errors="ignore"))
            if tokens is None:
                errors.append("行为校验: README 缺『## 键位』节(施工规范 §8 要求,机器对账锚)")
            else:
                readme_tokens = tokens
                # claims ⊆ README token:代码有行为文档必须宣称
                for missing in sorted(claimed - tokens):
                    errors.append(f"行为校验: README 键位节未宣称 [{missing}](代码有行为文档没写)")
    # 全集(claims ∪ README token)逐 key 必须有通过的 InteractionSemantics 用例
    # C4 教训:文档写了键位、代码没行为 → 这里拒
    for key in sorted(claimed | readme_tokens):
        token = f"InteractionSemantics.{key}"
        if not any(token in name for name in passing):
            errors.append(f"行为校验: 键位 [{key}] 无通过的 {token} 用例(命名约定见施工规范 §8)")
    return errors


def validate_evidence(story: Dict[str, Any], evidence: Dict[str, Any], project_root,
                      baseline: Optional[Dict[str, Any]] = None,
                      plugin_root=None,
                      frozen_layers: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """返回 {"status": "verified"|"rejected", "errors": [...]};错误信息具体可执行(重试闭环)。"""
    # frozen_layers:Task 8 分层冻结门禁用,本 Task 仅透传签名,暂不消费
    root = Path(project_root)
    errors: List[str] = []

    # ── 1. 分级必交字段检查 ──────────────────────────────────────────────────
    # evidence_class 未知/缺失时拒绝而非 KeyError 崩溃(重试闭环契约)
    required = REQUIRED_EVIDENCE.get(story.get("evidence_class"))
    if required is None:
        return {"status": "rejected",
                "errors": [f"evidence_class 非法或缺失: {story.get('evidence_class')!r}(合法值: {sorted(REQUIRED_EVIDENCE)})"]}
    for field in required:
        if evidence.get(field) is None:
            errors.append(f"缺少必交证据字段: {field}(evidence_class={story['evidence_class']})")

    # ── 1b. 呈现批附加必交:真实截图(Phase 15 spec §4.3 第 3 道) ──────────────
    # 仅当 evidence_class 本身未要求 screenshots 时补报,避免与第 1 段重复
    if str(story.get("batch_id", "")).startswith("presentation") \
            and "screenshots" not in (required or ()) and evidence.get("screenshots") is None:
        errors.append("缺少必交证据字段: screenshots(呈现批必交真实截图)")

    # ── 2. 路径越界 + 存在检查(P14-BL-01:resolve 后必须仍在项目根内) ────────
    root_resolved = root.resolve()
    for field, rel in _iter_paths(evidence):
        target = root / rel
        try:
            resolved = target.resolve()
        except OSError as exc:
            errors.append(f"证据路径不可解析: {field} -> {rel}({exc})")
            continue
        if not resolved.is_relative_to(root_resolved):
            errors.append(f"证据路径越界: {field} -> {rel} 不在项目根内(P14-BL-01 守门)")
            continue
        if not target.exists():
            errors.append(f"证据路径不存在: {field} -> {rel}")

    # ── 3. smoke_report 状态检查(读内容前二次越界过滤,与第 2 段双栅栏) ──────
    smoke_rel = evidence.get("smoke_report")
    smoke_path = (root / str(smoke_rel)) if smoke_rel else None
    if smoke_path is not None and smoke_path.resolve().is_relative_to(root_resolved) and smoke_path.exists():
        try:
            report = json.loads(smoke_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"smoke_report 不可解析: {exc}")
        else:
            # try/except/else 结构,避免 JSON null 与解析失败哨兵撞值导致静默放行
            # 合法 JSON 但非对象(如 null/数组/标量)时拒绝而非崩溃,保住重试闭环契约
            if not isinstance(report, dict):
                errors.append(f"smoke_report 格式错误: 期望 JSON 对象,实际 {type(report).__name__}")
            else:
                if report.get("status") != "pass":
                    errors.append(f"smoke_report 状态非 pass: {report.get('status')}")
                # 增量批还须 v0 回归通过
                if str(story.get("batch_id", "")).startswith("increment") and report.get("v0_regression") != "pass":
                    errors.append(f"增量批要求 v0 回归 pass,实际: {report.get('v0_regression')}")

    # ── 4. 增量批 baseline 检查 ─────────────────────────────────────────────
    if str(story.get("batch_id", "")).startswith("increment"):
        if baseline is None:
            errors.append("增量批必须提供 v0 baseline(先在人审窗口 1 冻结)")
        else:
            errors.extend(_check_baseline(root, baseline))

    # ── 4b. 行为校验门禁(P14-BL-05) ────────────────────────────────────────
    errors.extend(_check_interaction_claims(story, evidence, root, plugin_root))

    # ── 5. 文档 story 引用对账 ──────────────────────────────────────────────
    if story.get("story_kind") == "documentation":
        if plugin_root is None:
            errors.append("文档 story 校验需要 plugin_root")
        else:
            for rel in evidence.get("doc_paths") or []:
                doc_path = root / str(rel)
                if doc_path.exists():
                    errors.extend(_check_doc_references(
                        doc_path.read_text(encoding="utf-8", errors="ignore"), Path(plugin_root)))

    return {"status": "verified" if not errors else "rejected", "errors": errors}
