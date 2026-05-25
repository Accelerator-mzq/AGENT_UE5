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
    return Marker.from_json(path.read_text(encoding="utf-8"))


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
