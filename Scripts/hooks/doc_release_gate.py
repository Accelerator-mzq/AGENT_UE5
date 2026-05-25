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

import dataclasses
import datetime as _dt
import hashlib
import json
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
    # branch 名中的 / 替换为 -- 以适配 Windows 文件系统
    safe = branch.replace("/", "--")
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
) -> CheckResult:
    """根据 marker / HEAD / staged 决定是否放行。

    与 spec §4.3 步骤 4-9 对应(步骤 1-3 由 CLI 上层处理)。
    """
    marker = read_marker_file(marker_dir, branch)
    if marker is None:
        return CheckResult(False, f"marker not found for branch {branch}")

    staged_hash = compute_staged_files_hash(staged_paths)
    head_match = marker.head_sha == head_sha
    hash_match = marker.staged_files_hash == staged_hash
    # 步骤 6: head 与 hash 任一变化即视为新内容,需重审
    if not head_match and not hash_match:
        return CheckResult(False, "HEAD 与 staged 文件集均与 marker 不一致,需要重跑 document-release")
    if not head_match:
        return CheckResult(False, "HEAD 已变化,需重跑 document-release")
    if not hash_match:
        return CheckResult(False, "staged 文件集已变化,需重跑 document-release")

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
