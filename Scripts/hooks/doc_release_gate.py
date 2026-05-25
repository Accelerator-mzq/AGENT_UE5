"""document-release 跨平台门禁脚本

被以下入口调用:
  - .git/hooks/pre-commit, pre-push (跨平台硬底座)
  - Claude Code PreToolUse hook
  - OpenCode tool.execute.before plugin

CLI 子命令:
  check        校验是否允许 commit/push
  write-marker 由 skill 在审计完成后调用,写入合格 marker
  notify       软提示(写 stderr,永不阻塞)
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as _dt
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional


@dataclasses.dataclass(frozen=True)
class Marker:
    """记录一次合格的 document-release 运行"""
    branch: str
    head_sha: str
    staged_files_hash: str
    audit_evidence_path: str
    timestamp: str  # ISO 8601 with timezone

    def to_json(self) -> str:
        return json.dumps(dataclasses.asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, raw: str) -> "Marker":
        data = json.loads(raw)
        return cls(**data)


def _marker_path(marker_dir: Path, branch: str) -> Path:
    # branch 名中的 / 及 Windows 非法字符替换为 --,适配 NTFS / 跨平台
    safe = branch
    for ch in r'/\:*?"<>|':
        safe = safe.replace(ch, "--")
    return marker_dir / f"{safe}.json"


def write_marker_file(marker_dir: Path, marker: Marker) -> None:
    marker_dir.mkdir(parents=True, exist_ok=True)
    _marker_path(marker_dir, marker.branch).write_text(marker.to_json(), encoding="utf-8")


def read_marker_file(marker_dir: Path, branch: str) -> Optional[Marker]:
    path = _marker_path(marker_dir, branch)
    if not path.exists():
        return None
    try:
        return Marker.from_json(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, TypeError) as exc:
        # marker 文件损坏或字段不兼容,raise 显式异常含路径信息
        raise ValueError(f"marker 文件损坏: {path}") from exc


def compute_staged_files_hash(staged_paths: list[str]) -> str:
    # 排序后 sha256,保证与顺序无关
    payload = "\n".join(sorted(staged_paths))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---- evidence 校验 ----

REQUIRED_SECTIONS = ("## Coverage Map", "## Documentation health")


def validate_evidence(path: Path) -> tuple[bool, str]:
    """校验 audit.md 是否含必填的两个 H2 区块且区块内非空。

    返回 (ok, reason)。ok=False 时 reason 是中文/英文混合的拒绝原因。
    """
    if not path.exists():
        return False, f"evidence not found: {path}"
    text = path.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        if section not in text:
            return False, f"evidence 缺少必填区块: {section}"
        # 校验区块下方至少有一行非空非空白(不含下一个 H2)
        idx = text.index(section)
        rest = text[idx + len(section):]
        # 截到下一个 H2 之前
        next_h2 = rest.find("\n## ")
        block = rest if next_h2 == -1 else rest[:next_h2]
        non_empty_lines = [ln for ln in block.splitlines() if ln.strip()]
        if not non_empty_lines:
            return False, f"evidence 的 {section} 区块为空"
    return True, ""


# ---- check 主流程 ----


@dataclasses.dataclass(frozen=True)
class CheckResult:
    """check_marker 的返回值封装"""
    passed: bool
    reason: str  # passed=True 时为空字符串


MARKER_TTL = _dt.timedelta(hours=24)


def check_marker(
    *,
    marker_dir: Path,
    branch: str,
    head_sha: str,
    staged_paths: list[str],
    now: _dt.datetime,
    skip_staged_check: bool = False,  # 新参数: push 上下文不校验 staged hash
) -> CheckResult:
    """根据 marker / HEAD / staged 决定是否放行。

    与 spec §4.3 步骤 4-9 对应(步骤 1-3 由 CLI 上层处理)。
    push 上下文传 skip_staged_check=True,跳过 staged_files_hash 比对,
    因为 push 时 git diff --cached 返回空列表,强行比对会永久失效。
    """
    marker = read_marker_file(marker_dir, branch)
    if marker is None:
        return CheckResult(False, f"marker not found for branch {branch}")

    head_match = marker.head_sha == head_sha

    if not skip_staged_check:
        # commit/merge 上下文: 同时校验 HEAD SHA 与 staged 文件集 hash
        staged_hash = compute_staged_files_hash(staged_paths)
        hash_match = marker.staged_files_hash == staged_hash
        # 步骤 6: head 与 hash 任一变化即视为新内容,需重审
        if not head_match and not hash_match:
            return CheckResult(False, "HEAD 与 staged 文件集均与 marker 不一致,需要重跑 document-release")
        if not head_match:
            return CheckResult(False, "HEAD 已变化,需重跑 document-release")
        if not hash_match:
            return CheckResult(False, "staged 文件集已变化,需重跑 document-release")
    else:
        # push 上下文: git diff --cached 返回空列表,只校验 HEAD SHA
        if not head_match:
            return CheckResult(False, "HEAD 已变化,需重跑 document-release (push 上下文)")

    # 步骤 7: 24h 过期检查
    marker_time = _dt.datetime.fromisoformat(marker.timestamp)
    # 防御: marker 文件若由外部脚本/历史遗留写入,可能是 naive timestamp,补 UTC 后再比较
    if marker_time.tzinfo is None:
        marker_time = marker_time.replace(tzinfo=_dt.timezone.utc)
    if now - marker_time > MARKER_TTL:
        return CheckResult(False, "marker 已过期(>24h),需重跑 document-release")

    # 步骤 8: evidence 文件存在性检查
    if not Path(marker.audit_evidence_path).exists():
        return CheckResult(False, f"evidence 文件不存在: {marker.audit_evidence_path}")

    return CheckResult(True, "")


# ---- 逃生通道 ----

TRIVIAL_PREFIXES = (
    "Saved/", "Intermediate/", "DerivedDataCache/",
    "Binaries/", "Build/", ".codex/",
)
TRIVIAL_SUFFIXES = (".lock",)


def is_trivial(staged_paths: list[str]) -> bool:
    """全部 staged 文件落在白名单内 → trivial,自动放行,不写 marker。"""
    if not staged_paths:
        return False
    for p in staged_paths:
        norm = p.replace("\\", "/")
        if any(norm.startswith(pre) for pre in TRIVIAL_PREFIXES):
            continue
        if any(norm.endswith(suf) for suf in TRIVIAL_SUFFIXES):
            continue
        return False
    return True


def is_skip_doc_commit(message: str) -> bool:
    """commit message 首行是否以 [skip-doc] 开头(允许前置空白)。"""
    if not message:
        return False
    first_line = message.splitlines()[0]
    return bool(re.match(r"\s*\[skip-doc\]", first_line))


def log_skipped(log_path: Path, *, reason: str, branch: str, head: str) -> None:
    """append 一行到 skipped log,格式: ISO 时间 | branch | head | reason"""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    ts = _dt.datetime.now(_dt.timezone.utc).isoformat()
    line = f"{ts} | {branch} | {head} | {reason}\n"
    with log_path.open("a", encoding="utf-8") as f:
        f.write(line)


# ---- CLI ----

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MARKER_DIR = PROJECT_ROOT / "ProjectState" / "RuntimeConfigs" / "doc-release-markers"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "ProjectState" / "Reports"


def _marker_dir() -> Path:
    return Path(os.environ.get("DOC_RELEASE_MARKER_DIR", str(DEFAULT_MARKER_DIR)))


def _today_reports_dir() -> Path:
    today = _dt.datetime.now().strftime("%Y-%m-%d")
    return DEFAULT_REPORTS_DIR / today


def _default_skipped_log() -> Path:
    p = os.environ.get("DOC_RELEASE_SKIPPED_LOG")
    if p:
        return Path(p)
    return _today_reports_dir() / "doc_release_skipped.log"


def _git_staged_paths() -> list[str]:
    """通过 git diff --cached --name-only 取得当前 staged 文件列表"""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=PROJECT_ROOT,
            encoding="utf-8",
        )
    except (subprocess.CalledProcessError, OSError):
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _git_head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, encoding="utf-8"
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        return "UNKNOWN"


def _git_current_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=PROJECT_ROOT, encoding="utf-8"
        ).strip() or "HEAD-detached"
    except (subprocess.CalledProcessError, OSError):
        return "UNKNOWN"


def _check_skill_sha_consistency() -> tuple[bool, str]:
    """校验 canonical 与 mirror SKILL.md SHA 一致。mirror 不存在只 warn 不阻塞。

    对应 spec §4.3 step 3。
    """
    canonical = PROJECT_ROOT / ".claude" / "skills" / "document-release" / "SKILL.md"
    mirror = PROJECT_ROOT / ".agents" / "skills" / "document-release" / "SKILL.md"
    if not canonical.exists():
        return False, f"canonical SKILL.md 不存在: {canonical}"
    if not mirror.exists():
        # 副本不存在不阻塞(spec §4.3 step 3 fallback)
        return True, ""
    c_sha = hashlib.sha256(canonical.read_bytes()).hexdigest()
    m_sha = hashlib.sha256(mirror.read_bytes()).hexdigest()
    if c_sha != m_sha:
        return False, f"skill drift: canonical SHA != mirror SHA,请跑 python Scripts/sync_skills.py sync"
    return True, ""


def _cmd_check(args: argparse.Namespace) -> int:
    branch = args.branch or _git_current_branch()
    head = args.head or _git_head_sha()
    staged = args.simulate_staged or _git_staged_paths()

    # --trivial-only 模式: 仅做 trivial 白名单检查, 供 pre-commit hook 使用
    # pre-commit 阶段 COMMIT_EDITMSG 尚未写入, 完整 gate 由 commit-msg hook 负责
    if getattr(args, "trivial_only", False):
        if is_trivial(staged):
            return 0
        # 非 trivial 文件: 放行, 等 commit-msg hook 做完整校验
        return 0

    # 步骤 0a: skill SHA 一致性校验(spec §4.3 step 3)
    skill_ok, skill_reason = _check_skill_sha_consistency()
    if not skill_ok:
        print(f"\n[document-release gate] 阻止 {args.action}:\n  原因: {skill_reason}\n", file=sys.stderr)
        return 2

    # 步骤 0b: 逃生通道之 commit message [skip-doc]
    if args.commit_msg and is_skip_doc_commit(args.commit_msg):
        # dry-run 不写日志,只走逻辑判断
        if not args.dry_run:
            log_skipped(_default_skipped_log(), reason="commit msg [skip-doc]", branch=branch, head=head)
        return 0

    # 步骤 1: trivial 白名单
    if is_trivial(staged):
        return 0

    # 步骤 2: marker 校验; push 上下文跳过 staged hash 比对
    result = check_marker(
        marker_dir=_marker_dir(),
        branch=branch,
        head_sha=head,
        staged_paths=staged,
        now=_dt.datetime.now(_dt.timezone.utc),
        skip_staged_check=(args.action == "push"),  # push 时 git diff --cached 为空,不校验 staged
    )
    if result.passed:
        return 0

    msg = (
        f"\n[document-release gate] 阻止 {args.action}:\n"
        f"  原因: {result.reason}\n"
        f"  分支: {branch}  HEAD: {head[:12]}\n"
        f"  staged: {len(staged)} files\n"
        f"  逃生: 提交信息首行写 [skip-doc] 跳过,或调用 document-release skill 后重试\n"
    )
    print(msg, file=sys.stderr)
    return 2  # exit 2 让上层 hook 阻塞


def _cmd_notify(args: argparse.Namespace) -> int:
    print(
        f"[document-release notify] 你正在改 {args.path};收尾前记得调用 document-release skill。",
        file=sys.stderr,
    )
    return 0


def _cmd_write_marker(args: argparse.Namespace) -> int:
    evidence = Path(args.evidence)
    ok, reason = validate_evidence(evidence)
    if not ok:
        print(f"[document-release] 拒绝写 marker: {reason}", file=sys.stderr)
        return 2
    staged = args.simulate_staged or _git_staged_paths()
    marker = Marker(
        branch=args.branch or _git_current_branch(),
        head_sha=args.head or _git_head_sha(),
        staged_files_hash=compute_staged_files_hash(staged),
        audit_evidence_path=str(evidence),
        timestamp=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )
    if args.dry_run:
        print(f"[document-release] dry-run: marker 不写入 (branch={marker.branch}, head={marker.head_sha[:12]})", file=sys.stderr)
        return 0
    write_marker_file(_marker_dir(), marker)
    print(f"[document-release] marker 已写入: {marker.branch} @ {marker.head_sha[:12]}", file=sys.stderr)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="doc_release_gate", description="document-release 跨平台门禁")
    sub = p.add_subparsers(dest="cmd", required=True)

    pc = sub.add_parser("check", help="校验是否允许 commit/push")
    pc.add_argument("--action", choices=["commit", "push", "merge"], required=True)
    pc.add_argument("--branch")
    pc.add_argument("--head")
    pc.add_argument("--simulate-staged", nargs="*", default=None)
    pc.add_argument("--commit-msg", default=None)
    pc.add_argument("--dry-run", action="store_true")
    # 仅做 trivial 白名单检查, 跳过 marker / skip-doc 逻辑
    # 供 pre-commit hook 使用: 该阶段 COMMIT_EDITMSG 未写入
    pc.add_argument("--trivial-only", action="store_true")
    pc.set_defaults(func=_cmd_check)

    pn = sub.add_parser("notify", help="软提示,不阻塞")
    pn.add_argument("--path", required=True)
    pn.set_defaults(func=_cmd_notify)

    pw = sub.add_parser("write-marker", help="document-release skill 完成后写 marker")
    pw.add_argument("--branch")
    pw.add_argument("--head")
    pw.add_argument("--simulate-staged", nargs="*", default=None)
    pw.add_argument("--evidence", required=True)
    pw.add_argument("--dry-run", action="store_true")
    pw.set_defaults(func=_cmd_write_marker)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
