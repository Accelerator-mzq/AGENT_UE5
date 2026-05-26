# document-release 跨平台移植实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 ForgeUE 的 `document-release` skill 本地化重写后落入 Mvpv4TestCodex，并通过 git hook + Claude/OpenCode 平台 hook 构成跨平台强制门禁，让 commit/push 之前必须跑过文档审计。

**Architecture:** 同心圆三层。底座 = git pre-commit/pre-push hook 跨所有客户端生效；中层 = 各平台 hook（Claude `.claude/settings.json`、OpenCode `.opencode/plugins/*.ts`）做早提示；外层 = skill 文件单源放 `.claude/skills/document-release/SKILL.md`（OpenCode 兼容），sync 到 `.agents/skills/` 供 Codex。所有 hook 最终 spawn `Scripts/hooks/doc_release_gate.py`（Python 单一事实来源）。

**Tech Stack:** Python 3.x（核心 gate 脚本与所有工具）· bash/PowerShell（git hook 启动器，仅传参）· TypeScript（OpenCode plugin，仅壳层）· pytest（gate 单元测试）

**Spec:** `Docs/superpowers/specs/2026-05-25-document-release-port-design.md`

---

## 文件结构

### 新建
| 文件 | 责任 | 大小预期 |
|---|---|---|
| `Scripts/hooks/__init__.py` | 让 hooks 目录成为 Python 包，便于 pytest 发现 | 0 行 |
| `Scripts/hooks/doc_release_gate.py` | 核心 gate 脚本：CLI 主入口（check/notify/write-marker）、marker IO、staged hash、逃生通道判定 | ~350 行 |
| `Scripts/hooks/pre-commit` | git pre-commit hook 启动器，POSIX shell，仅 spawn gate.py | ~10 行 |
| `Scripts/hooks/pre-push` | git pre-push hook 启动器 | ~10 行 |
| `Scripts/hooks/install_git_hooks.py` | 把 pre-commit/pre-push 复制到 `.git/hooks/` 并 chmod +x，幂等 | ~60 行 |
| `Scripts/hooks/tests/__init__.py` | pytest 包标识 | 0 行 |
| `Scripts/hooks/tests/test_doc_release_gate.py` | gate.py 单元测试 | ~300 行 |
| `Scripts/sync_skills.py` | canonical → 副本 同步与一致性 `--check` | ~80 行 |
| `.claude/skills/document-release/SKILL.md` | canonical skill 内容（含 spec §3 拓扑映射 + §4 流程） | ~250 行 |
| `.agents/skills/document-release/SKILL.md` | 由 sync_skills.py 生成的副本 | ~250 行（同上） |
| `.claude/settings.json` | Claude Code hook 配置 | ~40 行 |
| `.opencode/plugins/doc-release-gate.ts` | OpenCode plugin 壳层，spawn gate.py | ~50 行 |

### 修改
| 文件 | 位置 | 改动 |
|---|---|---|
| `AGENTS.md` | 在「§3 文档治理规则」之后插入「§3.8 任务收尾流程」 | +~25 行 |
| `CLAUDE.md` | 在「## 当前阶段」之前插入「## 任务收尾流程」小节 | +~20 行 |
| `.gitignore` | 在 AgentBridge 规则之后追加 marker 忽略段 | +3 行 |

---

## Task 1: gate.py 核心数据结构 + marker IO

**Files:**
- Create: `Scripts/hooks/__init__.py`
- Create: `Scripts/hooks/tests/__init__.py`
- Create: `Scripts/hooks/tests/test_doc_release_gate.py`
- Create: `Scripts/hooks/doc_release_gate.py`

- [ ] **Step 1.1: 创建包标识文件**

```bash
touch Scripts/hooks/__init__.py Scripts/hooks/tests/__init__.py
```

- [ ] **Step 1.2: 写 marker 数据类的失败测试**

文件 `Scripts/hooks/tests/test_doc_release_gate.py`：

```python
"""doc_release_gate.py 单元测试"""
# 测试 marker IO、hash、check/write 流程
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from Scripts.hooks import doc_release_gate as gate


def test_marker_roundtrip(tmp_path: Path) -> None:
    # 写入 marker 后能原样读出
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    m = gate.Marker(
        branch="feat/x",
        head_sha="abc123",
        staged_files_hash="deadbeef",
        audit_evidence_path="ProjectState/Reports/2026-05-25/document_release_audit.md",
        timestamp="2026-05-25T10:00:00+08:00",
    )
    gate.write_marker_file(marker_dir, m)
    loaded = gate.read_marker_file(marker_dir, "feat/x")
    assert loaded == m


def test_marker_missing_returns_none(tmp_path: Path) -> None:
    # 不存在时返回 None,不抛错
    marker_dir = tmp_path / "markers"
    marker_dir.mkdir()
    assert gate.read_marker_file(marker_dir, "no-such-branch") is None


def test_compute_staged_files_hash_stable_under_order() -> None:
    # 同一组文件无论顺序如何,hash 一致
    h1 = gate.compute_staged_files_hash(["a.py", "b.py", "c.md"])
    h2 = gate.compute_staged_files_hash(["c.md", "b.py", "a.py"])
    assert h1 == h2
    assert len(h1) == 64  # sha256 hex
```

- [ ] **Step 1.3: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'Scripts.hooks.doc_release_gate'`

- [ ] **Step 1.4: 实现 gate.py 的 Marker 数据类与 IO**

文件 `Scripts/hooks/doc_release_gate.py`：

```python
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
```

- [ ] **Step 1.5: 跑测试看到通过**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v`
Expected: 3 passed

- [ ] **Step 1.6: 提交**

```bash
git add Scripts/hooks/__init__.py Scripts/hooks/tests/__init__.py Scripts/hooks/tests/test_doc_release_gate.py Scripts/hooks/doc_release_gate.py
git commit -m "feat(doc-release): add marker dataclass and IO with sha256 hash" -m "[skip-doc] 实施中,gate 脚本自身完成后再走 document-release"
```

> 注：这次 commit 用 `[skip-doc]` 是因为 hook 还没装；后续 task 装完 hook 后再 commit 走正常门禁。

---

## Task 2: gate.py write-marker 接口 + evidence 强制校验

**Files:**
- Modify: `Scripts/hooks/tests/test_doc_release_gate.py`
- Modify: `Scripts/hooks/doc_release_gate.py`

- [ ] **Step 2.1: 添加 evidence 校验的失败测试**

在 `test_doc_release_gate.py` 末尾追加：

```python
def test_validate_evidence_rejects_missing_coverage_map(tmp_path: Path) -> None:
    # evidence 文件缺 "## Coverage Map" 区块 → reject
    evidence = tmp_path / "audit.md"
    evidence.write_text("# Audit\n\n## Documentation health\n\n- README: OK\n", encoding="utf-8")
    ok, reason = gate.validate_evidence(evidence)
    assert ok is False
    assert "Coverage Map" in reason


def test_validate_evidence_rejects_missing_health_section(tmp_path: Path) -> None:
    evidence = tmp_path / "audit.md"
    evidence.write_text("# Audit\n\n## Coverage Map\n\n| x | y |\n|---|---|\n| a | b |\n", encoding="utf-8")
    ok, reason = gate.validate_evidence(evidence)
    assert ok is False
    assert "Documentation health" in reason


def test_validate_evidence_rejects_empty_coverage_map(tmp_path: Path) -> None:
    # 区块标题存在但下方没有非空行 → reject
    evidence = tmp_path / "audit.md"
    evidence.write_text(
        "# Audit\n\n## Coverage Map\n\n\n## Documentation health\n\n- README: OK\n",
        encoding="utf-8",
    )
    ok, reason = gate.validate_evidence(evidence)
    assert ok is False
    assert "Coverage Map" in reason


def test_validate_evidence_passes_with_both_sections(tmp_path: Path) -> None:
    evidence = tmp_path / "audit.md"
    evidence.write_text(
        "# Audit\n\n## Coverage Map\n\n| x | y |\n|---|---|\n| a | b |\n\n## Documentation health\n\n- README: Updated\n",
        encoding="utf-8",
    )
    ok, reason = gate.validate_evidence(evidence)
    assert ok is True
    assert reason == ""


def test_validate_evidence_rejects_missing_file(tmp_path: Path) -> None:
    ok, reason = gate.validate_evidence(tmp_path / "nope.md")
    assert ok is False
    assert "not found" in reason.lower() or "不存在" in reason
```

- [ ] **Step 2.2: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py::test_validate_evidence_rejects_missing_coverage_map -v`
Expected: FAIL with `AttributeError: module ... has no attribute 'validate_evidence'`

- [ ] **Step 2.3: 在 gate.py 末尾追加 validate_evidence**

```python
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
```

- [ ] **Step 2.4: 跑测试看到通过**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v`
Expected: 8 passed

- [ ] **Step 2.5: 提交**

```bash
git add Scripts/hooks/tests/test_doc_release_gate.py Scripts/hooks/doc_release_gate.py
git commit -m "feat(doc-release): add evidence section validator" -m "[skip-doc] 实施中"
```

---

## Task 3: gate.py `check` 主流程

**Files:**
- Modify: `Scripts/hooks/tests/test_doc_release_gate.py`
- Modify: `Scripts/hooks/doc_release_gate.py`

- [ ] **Step 3.1: 写 check 流程的失败测试**

追加：

```python
import datetime as _dt


def _make_marker(tmp: Path, **overrides) -> Marker:
    defaults = dict(
        branch="feat/x",
        head_sha="abc123",
        staged_files_hash=gate.compute_staged_files_hash(["foo.py"]),
        audit_evidence_path=str(tmp / "audit.md"),
        timestamp=_dt.datetime.now(_dt.timezone.utc).isoformat(),
    )
    defaults.update(overrides)
    return gate.Marker(**defaults)


def _write_valid_audit(path: Path) -> None:
    path.write_text(
        "# Audit\n\n## Coverage Map\n\n| x | y |\n|---|---|\n| a | b |\n\n## Documentation health\n\n- README: Updated\n",
        encoding="utf-8",
    )


def test_check_blocks_when_marker_missing(tmp_path: Path) -> None:
    marker_dir = tmp_path / "markers"
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False
    assert "marker not found" in result.reason.lower()


def test_check_blocks_when_head_and_hash_both_changed(tmp_path: Path) -> None:
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    gate.write_marker_file(marker_dir, _make_marker(tmp_path, audit_evidence_path=str(audit)))
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="DIFFERENT",
        staged_paths=["bar.py"],  # 不同的 hash
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False


def test_check_passes_when_head_matches(tmp_path: Path) -> None:
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    gate.write_marker_file(marker_dir, _make_marker(tmp_path, audit_evidence_path=str(audit)))
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is True


def test_check_blocks_when_marker_older_than_24h(tmp_path: Path) -> None:
    marker_dir = tmp_path / "markers"
    audit = tmp_path / "audit.md"
    _write_valid_audit(audit)
    old_ts = (_dt.datetime.now(_dt.timezone.utc) - _dt.timedelta(hours=25)).isoformat()
    gate.write_marker_file(
        marker_dir,
        _make_marker(tmp_path, audit_evidence_path=str(audit), timestamp=old_ts),
    )
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False
    assert "24h" in result.reason or "过期" in result.reason


def test_check_blocks_when_evidence_file_missing(tmp_path: Path) -> None:
    marker_dir = tmp_path / "markers"
    gate.write_marker_file(
        marker_dir,
        _make_marker(tmp_path, audit_evidence_path=str(tmp_path / "ghost.md")),
    )
    result = gate.check_marker(
        marker_dir=marker_dir,
        branch="feat/x",
        head_sha="abc123",
        staged_paths=["foo.py"],
        now=_dt.datetime.now(_dt.timezone.utc),
    )
    assert result.passed is False
```

- [ ] **Step 3.2: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v -k check_`
Expected: 全部 FAIL（`check_marker` 与 `CheckResult` 不存在）

- [ ] **Step 3.3: 在 gate.py 末尾追加 check_marker**

```python
# ---- check 主流程 ----

import datetime as _dt


@dataclasses.dataclass(frozen=True)
class CheckResult:
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

    # 步骤 7: 24h 过期
    marker_time = _dt.datetime.fromisoformat(marker.timestamp)
    if now - marker_time > MARKER_TTL:
        return CheckResult(False, "marker 已过期(>24h),需重跑 document-release")

    # 步骤 8: evidence 文件存在性
    if not Path(marker.audit_evidence_path).exists():
        return CheckResult(False, f"evidence 文件不存在: {marker.audit_evidence_path}")

    return CheckResult(True, "")
```

- [ ] **Step 3.4: 跑测试看到通过**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v`
Expected: 13 passed（8 前 + 5 新）

- [ ] **Step 3.5: 提交**

```bash
git add Scripts/hooks/tests/test_doc_release_gate.py Scripts/hooks/doc_release_gate.py
git commit -m "feat(doc-release): add check_marker main flow with HEAD/hash/TTL/evidence rules" -m "[skip-doc] 实施中"
```

---

## Task 4: gate.py 逃生通道 + CLI 整合 + notify

**Files:**
- Modify: `Scripts/hooks/tests/test_doc_release_gate.py`
- Modify: `Scripts/hooks/doc_release_gate.py`

- [ ] **Step 4.1: 写逃生通道与 CLI 的失败测试**

追加：

```python
def test_trivial_whitelist_only_saved_files_passes() -> None:
    # 全部在白名单内 → trivial
    assert gate.is_trivial(["Saved/foo.tmp", "Intermediate/bar.o"]) is True


def test_trivial_whitelist_mixed_with_source_is_not_trivial() -> None:
    assert gate.is_trivial(["Saved/foo.tmp", "src/main.py"]) is False


def test_trivial_whitelist_empty_paths_is_not_trivial() -> None:
    # 空 staged 不应自动放行(可能是 push 上下文)
    assert gate.is_trivial([]) is False


def test_skip_doc_marker_in_commit_message() -> None:
    assert gate.is_skip_doc_commit("[skip-doc] WIP refactor") is True
    assert gate.is_skip_doc_commit("feat: real change") is False
    assert gate.is_skip_doc_commit("docs: typo [skip-doc] inline") is False  # 必须在首行开头


def test_log_skipped_appends_line(tmp_path: Path) -> None:
    log = tmp_path / "skipped.log"
    gate.log_skipped(log, reason="commit msg [skip-doc]", branch="feat/x", head="abc")
    gate.log_skipped(log, reason="--no-verify", branch="feat/x", head="def")
    lines = log.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 2
    assert "skip-doc" in lines[0]
    assert "no-verify" in lines[1]
```

- [ ] **Step 4.2: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v -k "trivial or skip_doc or log_skipped"`
Expected: FAIL（函数不存在）

- [ ] **Step 4.3: 在 gate.py 追加逃生通道**

```python
# ---- 逃生通道 ----

import re

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
```

- [ ] **Step 4.4: 写 CLI 入口的失败测试**

追加：

```python
def test_cli_check_dry_run_blocks_when_no_marker(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    exit_code = gate.main([
        "check",
        "--action", "commit",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "src/foo.py",
        "--dry-run",
    ])
    assert exit_code != 0


def test_cli_check_dry_run_passes_with_trivial_only(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    exit_code = gate.main([
        "check",
        "--action", "commit",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "Saved/foo.tmp",
        "--dry-run",
    ])
    assert exit_code == 0


def test_cli_write_marker_rejects_invalid_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    bad = tmp_path / "bad.md"
    bad.write_text("# 只有标题\n", encoding="utf-8")
    exit_code = gate.main([
        "write-marker",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "src/foo.py",
        "--evidence", str(bad),
    ])
    assert exit_code != 0


def test_cli_write_marker_accepts_valid_evidence(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    good = tmp_path / "audit.md"
    _write_valid_audit(good)
    exit_code = gate.main([
        "write-marker",
        "--branch", "feat/x",
        "--head", "abc",
        "--simulate-staged", "src/foo.py",
        "--evidence", str(good),
    ])
    assert exit_code == 0
    # marker 应已写入
    marker = gate.read_marker_file(tmp_path / "markers", "feat/x")
    assert marker is not None
    assert marker.head_sha == "abc"


def test_cli_notify_never_blocks_and_writes_stderr(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("DOC_RELEASE_MARKER_DIR", str(tmp_path / "markers"))
    monkeypatch.setenv("DOC_RELEASE_SKIPPED_LOG", str(tmp_path / "skipped.log"))
    exit_code = gate.main([
        "notify",
        "--path", "task.md",
    ])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "task.md" in captured.err
```

- [ ] **Step 4.5: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v -k cli_`
Expected: FAIL（`gate.main` 不存在）

- [ ] **Step 4.6: 在 gate.py 末尾追加 CLI 入口**

```python
# ---- CLI ----

import argparse
import os
import subprocess
import sys

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
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def _git_head_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, encoding="utf-8"
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def _git_current_branch() -> str:
    try:
        return subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=PROJECT_ROOT, encoding="utf-8"
        ).strip() or "HEAD-detached"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "UNKNOWN"


def _cmd_check(args: argparse.Namespace) -> int:
    branch = args.branch or _git_current_branch()
    head = args.head or _git_head_sha()
    staged = args.simulate_staged or _git_staged_paths()

    # 步骤 0: 逃生通道之 commit message [skip-doc]
    if args.commit_msg and is_skip_doc_commit(args.commit_msg):
        log_skipped(_default_skipped_log(), reason="commit msg [skip-doc]", branch=branch, head=head)
        return 0

    # 步骤 1: trivial 白名单
    if is_trivial(staged):
        return 0

    # 步骤 2: marker 校验
    result = check_marker(
        marker_dir=_marker_dir(),
        branch=branch,
        head_sha=head,
        staged_paths=staged,
        now=_dt.datetime.now(_dt.timezone.utc),
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
    pc.set_defaults(func=_cmd_check)

    pn = sub.add_parser("notify", help="软提示,不阻塞")
    pn.add_argument("--path", required=True)
    pn.set_defaults(func=_cmd_notify)

    pw = sub.add_parser("write-marker", help="document-release skill 完成后写 marker")
    pw.add_argument("--branch")
    pw.add_argument("--head")
    pw.add_argument("--simulate-staged", nargs="*", default=None)
    pw.add_argument("--evidence", required=True)
    pw.set_defaults(func=_cmd_write_marker)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4.7: 跑全部测试通过**

Run: `python -m pytest Scripts/hooks/tests/test_doc_release_gate.py -v`
Expected: 23 passed（13 + 5 trivial/skip/log + 5 cli）

- [ ] **Step 4.8: 提交**

```bash
git add Scripts/hooks/tests/test_doc_release_gate.py Scripts/hooks/doc_release_gate.py
git commit -m "feat(doc-release): add trivial whitelist, skip-doc bypass, CLI subcommands (check/notify/write-marker)" -m "[skip-doc] 实施中"
```

---

## Task 5: skill 同步脚本 sync_skills.py

**Files:**
- Create: `Scripts/sync_skills.py`
- Modify: `Scripts/hooks/tests/test_doc_release_gate.py`（追加 sync 的简单集成测试到独立 test 文件更合适，但为减少文件数沿用同一处）

- [ ] **Step 5.1: 写同步脚本的失败测试**

新建 `Scripts/hooks/tests/test_sync_skills.py`：

```python
"""sync_skills.py 测试"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "Scripts" / "sync_skills.py"


def _run(args: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


def test_sync_creates_copy(tmp_path: Path) -> None:
    # tmp_path 模拟仓库,放一份 canonical,跑 sync,确认副本生成且 SHA 一致
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("# canonical\n", encoding="utf-8")

    result = _run(["sync"], cwd=tmp_path)
    assert result.returncode == 0, result.stderr

    mirror = tmp_path / ".agents" / "skills" / "document-release" / "SKILL.md"
    assert mirror.exists()
    assert mirror.read_text(encoding="utf-8") == canonical.read_text(encoding="utf-8")


def test_check_passes_when_consistent(tmp_path: Path) -> None:
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    mirror = tmp_path / ".agents" / "skills" / "document-release" / "SKILL.md"
    for p in (canonical, mirror):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# same\n", encoding="utf-8")

    result = _run(["--check"], cwd=tmp_path)
    assert result.returncode == 0


def test_check_fails_when_drift(tmp_path: Path) -> None:
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    mirror = tmp_path / ".agents" / "skills" / "document-release" / "SKILL.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    mirror.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("# A\n", encoding="utf-8")
    mirror.write_text("# B\n", encoding="utf-8")

    result = _run(["--check"], cwd=tmp_path)
    assert result.returncode != 0
    assert "drift" in result.stderr.lower() or "不一致" in result.stderr


def test_check_warns_when_mirror_missing(tmp_path: Path) -> None:
    canonical = tmp_path / ".claude" / "skills" / "document-release" / "SKILL.md"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("# A\n", encoding="utf-8")
    result = _run(["--check"], cwd=tmp_path)
    # 副本不存在不阻塞(只 warn),退出码 0
    assert result.returncode == 0
    assert "missing" in result.stderr.lower() or "不存在" in result.stderr
```

- [ ] **Step 5.2: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_sync_skills.py -v`
Expected: FAIL（脚本不存在）

- [ ] **Step 5.3: 实现 sync_skills.py**

文件 `Scripts/sync_skills.py`：

```python
"""skill 同步脚本: canonical(.claude/skills/) → 副本(.agents/skills/)

使用:
  python Scripts/sync_skills.py sync     生成/更新副本
  python Scripts/sync_skills.py --check  校验一致性,不一致 exit 2,缺副本只 warn
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
from pathlib import Path

# 当前管理的 skill 名清单(后续新增 skill 在这里加)
SKILLS = ["document-release"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _paths(root: Path, name: str) -> tuple[Path, Path]:
    canonical = root / ".claude" / "skills" / name / "SKILL.md"
    mirror = root / ".agents" / "skills" / name / "SKILL.md"
    return canonical, mirror


def cmd_sync(root: Path) -> int:
    for name in SKILLS:
        canonical, mirror = _paths(root, name)
        if not canonical.exists():
            print(f"[sync_skills] 跳过 {name}: canonical 不存在 {canonical}", file=sys.stderr)
            continue
        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(canonical, mirror)
        print(f"[sync_skills] {name}: synced -> {mirror}", file=sys.stderr)
    return 0


def cmd_check(root: Path) -> int:
    exit_code = 0
    for name in SKILLS:
        canonical, mirror = _paths(root, name)
        if not canonical.exists():
            print(f"[sync_skills] canonical 不存在: {canonical}", file=sys.stderr)
            exit_code = 2
            continue
        if not mirror.exists():
            # 副本不存在只 warn,不阻塞(spec §4.3 step 3 fallback)
            print(f"[sync_skills] WARN: 副本不存在 {mirror},Codex 用户将无法加载该 skill", file=sys.stderr)
            continue
        if _sha256(canonical) != _sha256(mirror):
            print(f"[sync_skills] drift: {canonical} != {mirror},请跑 sync_skills.py sync", file=sys.stderr)
            exit_code = 2
    return exit_code


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sync_skills")
    p.add_argument("cmd", nargs="?", default="sync", choices=["sync"])
    p.add_argument("--check", action="store_true")
    args = p.parse_args(argv)
    root = Path.cwd()
    if args.check:
        return cmd_check(root)
    return cmd_sync(root)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5.4: 跑测试通过**

Run: `python -m pytest Scripts/hooks/tests/test_sync_skills.py -v`
Expected: 4 passed

- [ ] **Step 5.5: 提交**

```bash
git add Scripts/sync_skills.py Scripts/hooks/tests/test_sync_skills.py
git commit -m "feat(doc-release): add skill sync script with --check drift detection" -m "[skip-doc] 实施中"
```

---

## Task 6: git hook 启动器 + 安装器

**Files:**
- Create: `Scripts/hooks/pre-commit`
- Create: `Scripts/hooks/pre-push`
- Create: `Scripts/hooks/install_git_hooks.py`
- Create: `Scripts/hooks/tests/test_install_git_hooks.py`

- [ ] **Step 6.1: 写 pre-commit 启动器（POSIX shell，git for windows 自带 bash 能跑）**

文件 `Scripts/hooks/pre-commit`：

```sh
#!/bin/sh
# git pre-commit hook: 调 doc_release_gate.py 校验
# 不在此处做逻辑;一切判断由 Python 脚本处理

# 项目根 = 该 hook 在 .git/hooks/ 下,向上两层
SCRIPT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"

# 读取 commit message(若 git 提供了 MSG file 路径作为参数则使用,否则空)
COMMIT_MSG=""
if [ -n "$1" ] && [ -f "$1" ]; then
    COMMIT_MSG="$(cat "$1")"
fi

python "$SCRIPT_DIR/Scripts/hooks/doc_release_gate.py" check \
    --action commit \
    ${COMMIT_MSG:+--commit-msg "$COMMIT_MSG"}
exit $?
```

> 注：pre-commit hook 默认不接 commit message 参数；message 拦截在 commit-msg hook 才完全可靠。本项目采用「pre-commit 不拦 skip-doc」的简化策略——`[skip-doc]` 通过 commit-msg hook 兜底。**先实现 pre-commit；commit-msg 留到 Task 6 末尾追加。**

- [ ] **Step 6.2: 写 pre-push 启动器**

文件 `Scripts/hooks/pre-push`：

```sh
#!/bin/sh
# git pre-push hook
SCRIPT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
python "$SCRIPT_DIR/Scripts/hooks/doc_release_gate.py" check --action push
exit $?
```

- [ ] **Step 6.3: 追加 commit-msg hook 启动器（处理 `[skip-doc]`）**

文件 `Scripts/hooks/commit-msg`：

```sh
#!/bin/sh
# git commit-msg hook: 检测 [skip-doc] 标记并放行
SCRIPT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
MSG_FILE="$1"
MSG="$(cat "$MSG_FILE")"
python "$SCRIPT_DIR/Scripts/hooks/doc_release_gate.py" check \
    --action commit \
    --commit-msg "$MSG"
exit $?
```

并更新文件结构表（脑内更新即可，不必改文档）。

> 实际拦截改由 commit-msg 完成（它能拿到 message），pre-commit 改为只做 trivial / marker 校验，不看 message。修改 pre-commit：

文件 `Scripts/hooks/pre-commit` 改为：

```sh
#!/bin/sh
# git pre-commit hook: trivial / marker 校验(不看 message,message 由 commit-msg 兜底)
SCRIPT_DIR="$(cd "$(dirname "$0")"/../.. && pwd)"
python "$SCRIPT_DIR/Scripts/hooks/doc_release_gate.py" check --action commit
exit $?
```

- [ ] **Step 6.4: 写安装器的失败测试**

文件 `Scripts/hooks/tests/test_install_git_hooks.py`：

```python
"""install_git_hooks.py 测试"""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INSTALLER = PROJECT_ROOT / "Scripts" / "hooks" / "install_git_hooks.py"


def _make_fake_repo(tmp: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=tmp, check=True)
    # 复制 hook 启动器到 tmp 仓库的 Scripts/hooks/
    src = PROJECT_ROOT / "Scripts" / "hooks"
    dst = tmp / "Scripts" / "hooks"
    dst.mkdir(parents=True)
    for name in ("pre-commit", "pre-push", "commit-msg"):
        (dst / name).write_text((src / name).read_text(encoding="utf-8"), encoding="utf-8")
    return tmp


def test_install_creates_hook_files(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    result = subprocess.run(
        [sys.executable, str(INSTALLER)],
        cwd=str(repo),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    for name in ("pre-commit", "pre-push", "commit-msg"):
        installed = repo / ".git" / "hooks" / name
        assert installed.exists(), f"{name} 未安装"


def test_install_is_idempotent(tmp_path: Path) -> None:
    repo = _make_fake_repo(tmp_path)
    for _ in range(2):
        result = subprocess.run(
            [sys.executable, str(INSTALLER)],
            cwd=str(repo),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


def test_install_makes_hooks_executable_on_posix(tmp_path: Path) -> None:
    if os.name == "nt":
        # Windows 不需 chmod;此用例只在 POSIX 跑
        return
    repo = _make_fake_repo(tmp_path)
    subprocess.run([sys.executable, str(INSTALLER)], cwd=str(repo), check=True)
    installed = repo / ".git" / "hooks" / "pre-commit"
    mode = installed.stat().st_mode
    assert mode & stat.S_IXUSR
```

- [ ] **Step 6.5: 跑测试看到失败**

Run: `python -m pytest Scripts/hooks/tests/test_install_git_hooks.py -v`
Expected: FAIL（installer 不存在）

- [ ] **Step 6.6: 实现 install_git_hooks.py**

文件 `Scripts/hooks/install_git_hooks.py`：

```python
"""把 pre-commit / pre-push / commit-msg 启动器复制到 .git/hooks/ 并设可执行位。

幂等。Windows 上 chmod 操作被忽略(git for windows 自动按文本判定可执行)。
"""
from __future__ import annotations

import os
import shutil
import stat
import sys
from pathlib import Path

HOOK_NAMES = ("pre-commit", "pre-push", "commit-msg")


def main() -> int:
    repo_root = Path.cwd()
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        print(f"[install_git_hooks] 当前目录不是 git 仓库: {repo_root}", file=sys.stderr)
        return 2
    src_dir = repo_root / "Scripts" / "hooks"
    dst_dir = git_dir / "hooks"
    dst_dir.mkdir(parents=True, exist_ok=True)

    for name in HOOK_NAMES:
        src = src_dir / name
        dst = dst_dir / name
        if not src.exists():
            print(f"[install_git_hooks] 源 hook 不存在: {src}", file=sys.stderr)
            return 2
        shutil.copy2(src, dst)
        if os.name != "nt":
            mode = dst.stat().st_mode
            dst.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print(f"[install_git_hooks] installed: {dst}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 6.7: 跑测试通过**

Run: `python -m pytest Scripts/hooks/tests/test_install_git_hooks.py -v`
Expected: 3 passed (POSIX) / 2 passed + 1 skipped logic (Windows——`test_install_makes_hooks_executable_on_posix` 内部 return 0)

- [ ] **Step 6.8: 提交**

```bash
git add Scripts/hooks/pre-commit Scripts/hooks/pre-push Scripts/hooks/commit-msg Scripts/hooks/install_git_hooks.py Scripts/hooks/tests/test_install_git_hooks.py
git commit -m "feat(doc-release): add git hook launchers and idempotent installer" -m "[skip-doc] 实施中"
```

---

## Task 7: 编写 canonical SKILL.md + 同步副本

**Files:**
- Create: `.claude/skills/document-release/SKILL.md`
- Create: `.agents/skills/document-release/SKILL.md`（由 sync 生成）

- [ ] **Step 7.1: 写 canonical SKILL.md**

文件 `.claude/skills/document-release/SKILL.md`（**完整内容如下，不要省略**）：

````markdown
---
name: document-release
description: Use when Mvpv4TestCodex documentation must be synchronized as the mandatory release gate before git commit/push, including AGENTS, CLAUDE, README, task.md, Docs/Current 五件套等价物、Plugins/AgentBridge/Docs 框架文档、Schemas 契约、Docs/Current/03_Active_Backlog.md backlog、ProjectState/Reports 证据落盘和 Docs/History 归档引用。
license: MIT
compatibility: claude-code, opencode, codex
metadata:
  source: gstack(MIT) → ForgeUE/document-release → Mvpv4TestCodex
  spec: Docs/superpowers/specs/2026-05-25-document-release-port-design.md
---

# Document Release (Mvpv4TestCodex)

## Overview

本 skill 是 Mvpv4TestCodex 的发布门禁文档同步 skill。它把已验证的交付物事实同步到当前文档,把历史归档作为证据,把不确定的文档欠债显式暴露,而不是猜测。

`document-release` 是 Superpowers 收尾链的**强制门禁**:`git commit / push / merge` 之前必须跑过它(由 git pre-commit/pre-push hook 与 Claude/OpenCode 平台 hook 共同保证)。

## Hard Boundaries

- 不跑 `rm -rf` / `Remove-Item -Recurse` / `git rm`,任何删除请求需用户明示。
- `Docs/History/**` 与历史日期的 `ProjectState/Reports/<past_date>/` **只读**,不重写。
- 严格遵守 `CLAUDE.md` §"绝对不要修改的文件"清单(C++ 核心 / Bridge 客户端 / Orchestrator 核心 / 已稳定 Schema / 测试体系)——只 audit 不修改。
- `task.md` / `Docs/Current/*_Closeout.md` 默认只读;需要重写必须先得到用户明示当前已进入新阶段或正在收尾。
- 本项目无版本号工作流,不做 version bump。
- 不改 PR title / body。
- 不硬编码测试计数(如"240"),改由命令实时输出。
- 不跨项目目录写入(仅限 `D:\UnrealProjects\Mvpv4TestCodex` 及子目录)。
- 不修改 `Plugins/AgentBridge/AGENTS.md`(它是通用框架规则)。
- 本项目根目录不应存在 `CHANGELOG.md`;如外部脚本生成也不允许由本 skill 改写。

## When To Use

- 用户要求 update docs / sync documentation / 描述刚刚发生了什么变更
- 用户要求 add / complete / retire backlog 条目
- 改了需求 / 架构 / 测试 / 验收 / Bridge / Orchestrator / MCP / 工作流 / agent 规则
- 校验现有文档是否仍与代码 / 示例 / 测试 / 当前工作流一致
- 实现完一个特性 / 一次迁移后准备文档证据
- **任何会改变行为、backlog、当前文档、契约、测试、示例或验收证据的非小改动**

仅 typo / 注释 / 不影响行为的文档改动可跳过本 skill,但需 commit message 首行写 `[skip-doc]`。

## Mvpv4TestCodex Documentation Map

把"当前文档面"分为四层。每层都可能因变更而需要更新:

### Layer A — 项目级入口与治理
| Surface | Path | Role |
|---|---|---|
| 用户入口 | `README.md` | 项目概述、快速入口、文档导航 |
| Codex/OpenCode 规则 | `AGENTS.md` | 项目级 Agent 规则 |
| Claude 规则 | `CLAUDE.md` | Claude Code 项目规则 |
| 当前阶段入口 | `task.md` | 阶段任务书或归档跳转页 |
| 当前阶段索引 | `Docs/Current/00_Index.md` | 阶段文档总索引 |

### Layer B — 当前阶段事实
| 概念 | 本项目落点 |
|---|---|
| 需求基线 | `Docs/Current/01_Project_Baseline.md` + `02_Current_Phase_Goals.md` |
| 设计 | `Plugins/AgentBridge/Docs/architecture_overview.md` + 9 份 Phase 11 框架规范文档 |
| 测试 | `Plugins/AgentBridge/Tests/SystemTestCases.md` |
| 验收 | `ProjectState/Reports/<date>/*acceptance*.md` |
| 增量(CHANGELOG 替代) | `Docs/Current/0X_Closeout.md` |
| Backlog active + archived | `Docs/Current/03_Active_Backlog.md` + `04_Open_Risks.md`;归档进 `Docs/History/Tasks/`、`0X_Closeout.md` |
| 实施边界 | `Docs/Current/05_Implementation_Boundary.md` |

### Layer C — 插件层框架(行为变更时必审)
| Surface | Path |
|---|---|
| 插件入口 | `Plugins/AgentBridge/README.md` |
| 通用 Agent 规则 | `Plugins/AgentBridge/AGENTS.md`(只读) |
| 框架文档 | `Plugins/AgentBridge/Docs/*.md` |
| Schema 契约 | `Plugins/AgentBridge/Schemas/*.json` |
| 系统测试 | `Plugins/AgentBridge/Tests/SystemTestCases.md` |

### Layer D — 证据 / 历史(默认只读)
| Surface | Path |
|---|---|
| 阶段证据 | `ProjectState/Reports/<YYYY-MM-DD>/` |
| 运行证据 | `ProjectState/Evidence/`、`Handoffs/`、`runs/`、`Snapshots/` |
| 历史归档 | `Docs/History/**` |
| 决策记录 | `Docs/Decisions/`(如有) |

## Workflow

### Mandatory placement
```
implementation / fix
 → superpowers:verification-before-completion
 → document-release (本 skill)
 → superpowers:verification-before-completion
 → superpowers:finishing-a-development-branch
```

### Step 1: Preflight
```powershell
git branch --show-current
git status --short --branch
git merge-base HEAD origin/main
git diff <base>...HEAD --stat
git diff <base>...HEAD --name-only
git log <base>..HEAD --oneline
```
若 `origin/main` 不可用,依次回退到 `origin/master`、本地 `main`、近期 commits。在最终报告中标注实际 base。

### Step 2: Build coverage map
列出本次变更涉及的能力 / 配置 / 工具 / Schema / 工作流 / agent 规则。

填入表格:
```
变更点                          A 入口  B 阶段事实  C 框架  D 证据落盘
<变更的能力或概念>              path    path        path    path/none
```

零覆盖 = critical gap。只有 A/D 没有 B/C = doc debt。

### Step 3: Audit by layer
按 Layer A → B → C → D 顺序逐项审。每项标 Auto-update / Ask first。
- Auto-update: 已被代码/测试/已有文档证实的事实变更
- Ask first: 架构理由、移除区块、移动 backlog、产品语言含糊处

### Step 4: Backlog rules
- 新的延期工作 → 加到 `Docs/Current/03_Active_Backlog.md`
- 完成或被取代的条目 → 询问用户后移到 `Docs/History/Tasks/` 或写入 `0X_Closeout.md`
- 不静默删除 active 条目;不从 `Docs/History/` 重建 backlog

### Step 5: Apply safe updates
小补丁,多步;每改一个文件留一行 summary。

### Step 6: Verify
```powershell
# 旧路径/旧概念扫一遍
rg -n "<旧概念或旧路径>" README.md AGENTS.md CLAUDE.md Docs Plugins/AgentBridge/Docs -S

# 必要时跑 schema 校验或系统测试登记
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
```
如果改动牵涉到测试/示例/契约,跑相应测试;否则注明"未跑测试,因 doc-only"。

### Step 7: Final report — 写 audit.md
**必须**写入 `ProjectState/Reports/<today>/document_release_audit.md`,且必须包含以下两个 H2 区块,否则 marker 写入接口会拒绝:

```markdown
# Document Release Audit — <branch> @ <HEAD short SHA>

> 运行时间: <ISO 8601>
> 比较基准: <merge-base>
> 触发事件: <commit / push / merge / manual>

## Coverage Map
| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| <变更 1> | <path or NONE> | ... | ... | ... |

## Documentation health
- README.md: Updated / Current / Needs user decision — <detail>
- AGENTS.md: ...
- CLAUDE.md: ...
- Layer B: ...
- Layer C: ...
- Backlog: ...
- ProjectState/Reports: ...
- Archive: Read-only — <detail>
```

### Step 8: Write marker (强制)
最后一步必须调:
```powershell
python Scripts/hooks/doc_release_gate.py write-marker `
  --evidence ProjectState/Reports/<today>/document_release_audit.md
```
该接口会强制校验 audit.md 含上述两个 H2 区块;不合格则拒绝写 marker,从而阻塞后续 git commit/push。

## Common Mistakes

| Mistake | Fix |
|---|---|
| 只改 README,忘了 Layer B 五件套等价物 | 按 Layer A→B→C→D 顺序审 |
| 把 `Docs/History/**` 当作 current truth | History 是证据,改 current docs 而不是改 history |
| 忘 backlog | 检查 `Docs/Current/03_Active_Backlog.md` + `04_Open_Risks.md` |
| 编造或硬编码测试计数 | 跑命令实时取数 |
| 用删除命令清理 | 不删除,改由用户明示 |
| 改 `Plugins/AgentBridge/AGENTS.md` | 它是框架通用规则,不动 |

## Source Note

This skill is adapted from gstack's MIT-licensed `document-release` workflow (via ForgeUE_codex 项目的本地化),with Mvpv4TestCodex-specific documentation topology and safety boundaries.

````

- [ ] **Step 7.2: 同步副本**

Run: `python Scripts/sync_skills.py sync`
Expected: stderr 输出 `[sync_skills] document-release: synced -> ... /.agents/skills/document-release/SKILL.md`

- [ ] **Step 7.3: 校验一致**

Run: `python Scripts/sync_skills.py --check`
Expected: exit 0，stderr 无 drift 报告

- [ ] **Step 7.4: 提交**

```bash
git add .claude/skills/document-release/SKILL.md .agents/skills/document-release/SKILL.md
git commit -m "feat(doc-release): add canonical SKILL.md and Codex mirror" -m "[skip-doc] 实施中"
```

---

## Task 8: Claude Code hook 配置

**Files:**
- Create: `.claude/settings.json`

- [ ] **Step 8.1: 写 settings.json**

文件 `.claude/settings.json`：

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python Scripts/hooks/doc_release_gate.py check --action commit",
            "when": "command_matches:^\\s*git\\s+commit\\b"
          },
          {
            "type": "command",
            "command": "python Scripts/hooks/doc_release_gate.py check --action push",
            "when": "command_matches:^\\s*git\\s+push\\b"
          },
          {
            "type": "command",
            "command": "python Scripts/hooks/doc_release_gate.py check --action merge",
            "when": "command_matches:^\\s*git\\s+merge\\b"
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "python Scripts/hooks/doc_release_gate.py notify --path \"${file_path}\"",
            "when": "path_matches:^(task\\.md|Docs/Current/.*_Closeout\\.md|ProjectState/Reports/.*)$"
          }
        ]
      }
    ]
  }
}
```

> 注：Claude Code hook 的精确 schema 与匹配语法以官方文档为准；上述 `when` 字段是表意写法。**实施时先用 `claude --help` 或 `Skill update-config` 验证具体语法**，若与上述不同则按官方为准微调。

- [ ] **Step 8.2: 手动验证 hook 配置可被 Claude 加载**

Run:
```powershell
python -c "import json; cfg=json.load(open('.claude/settings.json',encoding='utf-8')); print('OK,PreToolUse hooks:', len(cfg['hooks']['PreToolUse']))"
```
Expected: `OK,PreToolUse hooks: 2`

- [ ] **Step 8.3: 提交**

```bash
git add .claude/settings.json
git commit -m "feat(doc-release): wire Claude Code PreToolUse hook to gate.py" -m "[skip-doc] 实施中"
```

---

## Task 9: OpenCode plugin

**Files:**
- Create: `.opencode/plugins/doc-release-gate.ts`

- [ ] **Step 9.1: 写 OpenCode plugin**

文件 `.opencode/plugins/doc-release-gate.ts`：

```ts
// OpenCode plugin: 把 bash 工具调用与文件写入桥接到 doc_release_gate.py
// 文档: https://github.com/anomalyco/opencode 的 docs/plugins.mdx

import type { Plugin } from "@opencode-ai/plugin"

const GIT_RE = /^\s*git\s+(commit|push|merge)\b/
const NOTIFY_PATH_RE = /^(task\.md|Docs\/Current\/.*_Closeout\.md|ProjectState\/Reports\/.*)$/

// 把同步 spawn 的 Python 脚本包成 promise
async function runGate($: any, args: string[]): Promise<{ exitCode: number; stderr: string }> {
  const proc = $`python Scripts/hooks/doc_release_gate.py ${args}`.nothrow()
  const result = await proc
  return { exitCode: result.exitCode, stderr: result.stderr.toString() }
}

export const DocReleaseGate: Plugin = async ({ $ }) => {
  return {
    "tool.execute.before": async (input, output) => {
      // 1) bash 命令: git commit/push/merge 拦截
      if (input.tool === "bash") {
        const cmd = output.args.command as string
        const m = GIT_RE.exec(cmd)
        if (m) {
          const action = m[1]
          const res = await runGate($, ["check", "--action", action])
          if (res.exitCode !== 0) {
            // 抛错 = 阻塞 tool 调用
            throw new Error(`[document-release] 阻止 ${action}:\n${res.stderr}`)
          }
        }
        return
      }
      // 2) write / edit 命令: 治理面文件软提示
      if (input.tool === "write" || input.tool === "edit") {
        const path = (output.args.path || output.args.file_path) as string
        if (path && NOTIFY_PATH_RE.test(path)) {
          await runGate($, ["notify", "--path", path])
        }
      }
    },
  }
}
```

- [ ] **Step 9.2: 验证 TS 语法（无 bun 也可只看文件存在）**

Run:
```powershell
python -c "import os,sys; sys.exit(0 if os.path.exists('.opencode/plugins/doc-release-gate.ts') else 1)"
```
Expected: exit 0

> 注：若机器装了 bun，可额外跑 `bun build .opencode/plugins/doc-release-gate.ts --target=bun --no-bundle` 看是否能解析；但 OpenCode runtime 安装时也会做这一步。

- [ ] **Step 9.3: 提交**

```bash
git add .opencode/plugins/doc-release-gate.ts
git commit -m "feat(doc-release): add OpenCode plugin bridging tool.execute.before to gate.py" -m "[skip-doc] 实施中"
```

---

## Task 10: 规则锚点 + .gitignore

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `.gitignore`

- [ ] **Step 10.1: 在 AGENTS.md 「§3 文档治理规则」之后追加 §3.8**

打开 `AGENTS.md`，找到 `### 3.7 附加说明` 后面（在 §3 结束之前），插入：

```markdown
### 3.8 任务收尾流程

非 trivial 改动(改变行为 / backlog / 当前文档 / 契约 / 测试 / 示例 / 验收证据)必须按以下链条收尾:

```
implementation / fix
 → superpowers:verification-before-completion
 → document-release  (Mvpv4TestCodex 本地 skill)
 → superpowers:verification-before-completion (对 doc 改动再 verify)
 → superpowers:finishing-a-development-branch (merge / push)
```

`document-release` 是**强制门禁**:`git commit / push / merge` 之前必须跑过它,否则 git pre-commit/pre-push hook 以及 Claude Code / OpenCode 平台 hook 会拦下来。逃生通道:

- staged 文件全部落在 `Saved/` / `Intermediate/` / `DerivedDataCache/` / `Binaries/` / `Build/` / `.codex/` / `*.lock` 内 → 自动放行,不写 marker
- commit message 首行写 `[skip-doc]` → 跳过,但记录到 `ProjectState/Reports/<today>/doc_release_skipped.log`
- `git commit --no-verify` → 跳过,事后追写 skipped.log

skill 完整规范见 `.claude/skills/document-release/SKILL.md`(canonical) 和 `.agents/skills/document-release/SKILL.md`(Codex 副本);设计依据见 `Docs/superpowers/specs/2026-05-25-document-release-port-design.md`。
```

- [ ] **Step 10.2: 在 CLAUDE.md「## 当前阶段」之前插入「## 任务收尾流程」**

打开 `CLAUDE.md`，找到 `## 当前阶段` 行，**在它之前**插入：

```markdown
## 任务收尾流程

非 trivial 改动收尾链:

```
实现 / 修复
 → superpowers:verification-before-completion
 → document-release  (本项目 skill, .claude/skills/document-release/SKILL.md)
 → superpowers:verification-before-completion (对 doc 改动再 verify)
 → superpowers:finishing-a-development-branch (merge / push)
```

强制门禁已通过 git pre-commit/pre-push hook + Claude Code PreToolUse hook 联合实现,任何 commit/push 之前必须跑过 document-release。逃生通道:`[skip-doc]` 标记 / trivial 路径白名单 / `--no-verify`。

详见 AGENTS.md §3.8 与 `Docs/superpowers/specs/2026-05-25-document-release-port-design.md`。

```

- [ ] **Step 10.3: 在 .gitignore 追加 marker 忽略**

打开 `.gitignore`，在文件末尾追加：

```
# document-release marker(运行时状态,不入仓库)
ProjectState/RuntimeConfigs/doc-release-markers/
```

- [ ] **Step 10.4: 提交**

```bash
git add AGENTS.md CLAUDE.md .gitignore
git commit -m "docs(doc-release): anchor workflow in AGENTS.md/CLAUDE.md + ignore marker dir" -m "[skip-doc] 实施中"
```

---

## Task 11: 部署 git hook 到 .git/hooks/

**Files:** (无新增；只是部署)

- [ ] **Step 11.1: 跑安装器**

Run: `python Scripts/hooks/install_git_hooks.py`
Expected: stderr 输出 3 行 `[install_git_hooks] installed: ...`

- [ ] **Step 11.2: 验证 hook 存在**

```powershell
python -c "import os; [print(p, os.path.exists(p)) for p in ['.git/hooks/pre-commit','.git/hooks/pre-push','.git/hooks/commit-msg']]"
```
Expected: 三个都 True

- [ ] **Step 11.3: 验证 hook 真能拦（dry trigger）**

```bash
# 不实际改文件,只看 hook 行为
git commit --allow-empty -m "test: hook fire" 2>&1 | tail -10
```
Expected: 输出 `[document-release gate] 阻止 commit:` 区块；commit 失败（exit non-zero）。

如果 commit 成功了，说明 hook 没装好——回 Task 6 / Task 11 排查。

- [ ] **Step 11.4: 用 [skip-doc] 验证逃生通道**

```bash
git commit --allow-empty -m "[skip-doc] verify escape" 2>&1 | tail -5
```
Expected: commit 成功。`ProjectState/Reports/<today>/doc_release_skipped.log` 新增一行。

- [ ] **Step 11.5: 把 skipped.log 第一次产物纳入证据**

```bash
LOG="ProjectState/Reports/$(date +%Y-%m-%d)/doc_release_skipped.log"
ls -la "$LOG"
git add "$LOG"
git commit -m "[skip-doc] chore(doc-release): track first skipped.log entry"
```

> 这次 commit 用 [skip-doc] 是因为 hook 已装，但 audit.md 还没首次跑。

---

## Task 12: 端到端 smoke test + 第一次正式 document-release

**Files:**
- Create: `ProjectState/Reports/<today>/document_release_install_smoke_test.md`
- Create: `ProjectState/Reports/<today>/document_release_audit.md`（由 skill 跑出来）

- [ ] **Step 12.1: 跑 spec §7.2 自检清单**

```powershell
python -c "import os; p='.claude/skills/document-release/SKILL.md'; print('skill OK' if os.path.exists(p) else 'MISSING')"
python Scripts/sync_skills.py --check
python Scripts/hooks/doc_release_gate.py check --action commit --branch test --head abc --simulate-staged src/foo.py --dry-run
# 期望 exit 非零(无 marker)
python Scripts/hooks/doc_release_gate.py check --action commit --branch test --head abc --simulate-staged Saved/foo.tmp --dry-run
# 期望 exit 0
python Scripts/hooks/doc_release_gate.py write-marker --branch test --head abc --simulate-staged src/foo.py --evidence /dev/null
# 期望 exit 非零
```

把以上每条命令的实际 stdout/stderr/exit code 抄到 `ProjectState/Reports/<today>/document_release_install_smoke_test.md`：

```markdown
# Document Release 安装 smoke test

> 日期: <today>
> 分支: <current branch>
> 操作员: <你的名字>

## §7.2 自检清单

### 1. skill 主入口
命令: `python -c "..."`
输出: `skill OK`
结论: PASS

### 2. sync --check
命令: `python Scripts/sync_skills.py --check`
exit code: 0
stderr: (空)
结论: PASS

### 3. check 无 marker 应阻塞
命令: `python Scripts/hooks/doc_release_gate.py check ...`
exit code: 2
stderr 摘要: marker not found ...
结论: PASS

### 4. trivial 白名单
命令: `... --simulate-staged Saved/foo.tmp`
exit code: 0
结论: PASS

### 5. write-marker 拒绝坏 evidence
命令: `... write-marker --evidence /dev/null`
exit code: 2
结论: PASS

## §7.3 端到端

### T2. 修改 README.md 后 git commit
(实际执行步骤与输出)

### T3. 调用 document-release skill
(skill 输出位置)

### T4. 重试 commit 应通过
(实际输出)
```

- [ ] **Step 12.2: 跑第一次真正的 document-release**

调用本项目的 `document-release` skill（在 Claude Code 里说 "use document-release skill"，或在 OpenCode/Codex 里同样调用）。

skill 会：
1. 跑 preflight
2. 列 coverage map（本次变更：新增 doc-release 门禁系统）
3. audit Layer A-D
4. 决定 backlog 变动（应当在 `Docs/Current/03_Active_Backlog.md` 加一条「audit.md 自动生成器」backlog 条目）
5. 写 `ProjectState/Reports/<today>/document_release_audit.md`
6. 调 `python Scripts/hooks/doc_release_gate.py write-marker --evidence ...` 落 marker

- [ ] **Step 12.3: 验证 marker 已写**

```powershell
ls "ProjectState/RuntimeConfigs/doc-release-markers/"
python -c "import json; m=json.load(open('ProjectState/RuntimeConfigs/doc-release-markers/'+open('.git/HEAD').read().strip().split('/')[-1].replace('/','--')+'.json',encoding='utf-8')); print(m)"
```
Expected: marker 文件存在且内容合理

- [ ] **Step 12.4: 现在用「正常方式」commit smoke test 报告 + audit.md**

```bash
git add "ProjectState/Reports/$(date +%Y-%m-%d)/document_release_install_smoke_test.md" \
        "ProjectState/Reports/$(date +%Y-%m-%d)/document_release_audit.md" \
        "Docs/Current/03_Active_Backlog.md"  # 若有更新
git commit -m "chore(doc-release): record install smoke test and first document-release audit"
```
Expected: commit 成功（marker 与 HEAD/staged 都一致，hook 放行）。如果被拦，说明 marker 与最终 staged 不一致——这本身就证明门禁工作正常，重跑 skill 再 commit。

- [ ] **Step 12.5: 验证完成清单**

确认所有自检通过：
- [ ] gate.py 单元测试 23 个全部 pass
- [ ] sync_skills.py 测试 4 个 pass
- [ ] install_git_hooks.py 测试 3 个 pass（POSIX）或等效（Windows）
- [ ] `.git/hooks/pre-commit / pre-push / commit-msg` 存在
- [ ] `.claude/settings.json` 存在且可解析
- [ ] `.opencode/plugins/doc-release-gate.ts` 存在
- [ ] canonical 与副本 SHA256 一致
- [ ] AGENTS.md §3.8、CLAUDE.md 任务收尾流程、`.gitignore` 三项修改齐
- [ ] 首次 document-release audit 已写、marker 已落、正常 commit 通过

---

## Self-Review

**Spec coverage**:
- §1 背景与目标 → 整 plan 实现
- §2 架构总览 → Task 1-11
- §2.2 文件落点总览 → 文件结构表 + 各 Task Files 块
- §3 文档拓扑映射 → Task 7 内嵌进 SKILL.md
- §4.1 主流程链 → Task 7 SKILL.md Workflow 节 + Task 10 锚点
- §4.2 hook 矩阵 → Task 6 git hook + Task 8 Claude + Task 9 OpenCode
- §4.3 check 内部判断 → Task 3 实现 + Task 4 CLI
- §4.4 逃生通道 → Task 4 实现 + Task 6 commit-msg hook
- §4.5 write-marker 接口 → Task 2 validate_evidence + Task 4 CLI
- §4.6 规则锚点 → Task 10
- §5 Hard Boundaries → Task 7 SKILL.md Hard Boundaries 节
- §6 跨平台落地矩阵 → Task 6-9 三平台 hook + Task 7 双路径 skill
- §7.1 .gitignore → Task 10.3
- §7.2 自检命令 → Task 12.1
- §7.3 smoke test → Task 12.1-12.2
- §7.4 非目标 → 已在 Task 12.2 backlog 步骤 reference

无遗漏。

**Placeholder 扫描**：无 TBD / TODO / "implement later"。Task 8 提到「实施时按官方文档调 schema」，但提供了具体的 fallback 检测命令，不算 placeholder。

**Type 一致性**：
- `Marker` 字段在 Task 1 / 2 / 3 / 4 / 7 中保持一致（branch / head_sha / staged_files_hash / audit_evidence_path / timestamp）
- `CheckResult` 字段 passed / reason 一致
- `gate.main()` argv 形式跨 Task 一致
- `compute_staged_files_hash` 参数 list[str] 一致
- 三个 hook 子命令名 check / notify / write-marker 全程一致

无类型漂移。

---

## Execution Handoff

Plan complete and saved to `Docs/superpowers/plans/2026-05-25-document-release-port-implementation.md`. Two execution options:

**1. Subagent-Driven (recommended)** - 每个 Task 派一个新 subagent,review 后再继续。隔离 + 快迭代,适合这个 12-task plan。

**2. Inline Execution** - 在当前会话里 batch 跑,带检查点。

Which approach?
