"""
Mvpv4TestCodex 文档重组 — 链接预校验(Phase 2.2)

关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §8
关联 plan: Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md Task 2.2

作用:
1. 全仓 grep 出所有指向旧路径(Docs/Current/History/Decisions/Proposals/superpowers + Plugins/AgentBridge/Docs/)的引用
2. 用 Docs/redirects.json 验证每个旧路径都能找到映射目标
3. 产出 Phase 4 重写清单(需要被 sed/redirect 重写的文件列表)

排除范围(这些文件本身就含旧路径,不算"未实地化"):
- Docs/archive/(归档区)
- Docs/superpowers/specs/2026-05-26-* + plans/2026-05-26-*(本次重组的 spec/plan/inventory 本身)
- Docs/redirects.json(映射源)
- ProjectState/Reports/(评审 / 审计报告,带历史路径引用)
- Docs/FEATURE_INVENTORY.md / archive/README.md(引用 archive/ 路径是设计意图)
- ProjectState/runs/(Phase 8/9/10/11 历史 evidence)
- 任何路径含 .git / __pycache__ / Saved / Intermediate / Binaries / Build / DerivedDataCache

退出码:0 = 全 PASS;1 = 有未映射链接
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / 'Docs'

# 旧路径前缀(在 inventory CSV 中登记的 108 份旧文档的目录前缀)
OLD_PATH_RE = re.compile(
    r'(?:Docs/(?:Current|History|Decisions|Proposals|superpowers)/[A-Za-z0-9_./\-]+\.md'
    r'|Plugins/AgentBridge/Docs/[A-Za-z0-9_./\-]+\.md)'
)

# 这些路径是本次重组的 metadata,不属于"待搬迁的旧文档",inventory CSV 也不登记
# 它们在新文档中出现是设计意图(作为本次重组工作的引用),不算"未映射的链接"
META_PATHS_EXCLUDE_FROM_HITS = {
    'Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md',
    'Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md',
    'Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md',
}

# 占位字符串模式(含 N/X 等单大写字母占位,如 taskN_phaseX.md / 0X_Closeout.md)
PLACEHOLDER_RE = re.compile(
    r'/task[A-Z]_phase[A-Z]\.md$'      # taskN_phaseX.md
    r'|/[A-Z]+_[A-Z]+\.md$'            # 全大写下划线占位
    r'|/0?[A-Z]_[A-Za-z]+\.md$'        # 0X_Closeout.md / 1N_Plan.md
)

# 排除路径前缀(这些文件出现旧路径引用是设计意图,不算未实地化)
EXCLUDE_PATH_PREFIXES = (
    'Docs/archive/',
    'Docs/redirects.json',
    'Docs/FEATURE_INVENTORY.md',
    'Docs/superpowers/',  # 本次重组 + 上次重组的 spec/plan/inventory(均自有历史引用,Phase 3 后搬 archive)
    'Docs/History/',  # 历史文档,本身在 Phase 3 被搬到 archive/history/,历史引用是快照
    'ProjectState/',
)

EXCLUDE_PATH_PARTS = (
    '.git', '__pycache__', 'Saved', 'Intermediate',
    'Binaries', 'Build', 'DerivedDataCache', 'node_modules',
    '.codex', '.claude/logs',
)

# 扫描的文件类型
SCAN_SUFFIXES = ('.md', '.py', '.json', '.ps1', '.yaml', '.yml')


def _should_skip(p: Path) -> bool:
    rel = p.relative_to(ROOT).as_posix()
    for prefix in EXCLUDE_PATH_PREFIXES:
        if rel.startswith(prefix):
            return True
    for part in p.parts:
        if part in EXCLUDE_PATH_PARTS:
            return True
    return False


def main():
    redirects = json.loads((DOCS / 'redirects.json').read_text(encoding='utf-8'))

    # 1. 全仓扫描旧路径引用
    hits: list[tuple[str, int, str, str]] = []  # (file, line, old_path, full_line)
    scanned = 0
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if _should_skip(p):
            continue
        scanned += 1
        try:
            text = p.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        for i, line in enumerate(text.split('\n'), 1):
            for m in OLD_PATH_RE.finditer(line):
                old_path = m.group(0)
                # 排除本次重组 metadata 路径(不是待搬迁的旧文档)
                if old_path in META_PATHS_EXCLUDE_FROM_HITS:
                    continue
                # 排除占位字符串
                if PLACEHOLDER_RE.search(old_path):
                    continue
                hits.append((p.relative_to(ROOT).as_posix(), i, old_path, line.strip()))

    print(f"扫描了 {scanned} 个文件,命中 {len(hits)} 处旧路径引用\n")

    # 2. 验证每个 old_path 都能在 redirects.json 找到映射
    unmapped: list[tuple[str, int, str, str]] = []
    files_with_hits: set[str] = set()
    for file, line_no, old_path, full_line in hits:
        files_with_hits.add(file)
        if old_path not in redirects:
            unmapped.append((file, line_no, old_path, full_line))

    if unmapped:
        print(f"❌ {len(unmapped)} 处链接未在 redirects.json 找到映射:")
        for file, line_no, old_path, full_line in unmapped[:20]:
            print(f"  - {old_path}")
            print(f"    @ {file}:{line_no} → {full_line[:120]}")
        if len(unmapped) > 20:
            print(f"  ...(还有 {len(unmapped) - 20} 处未列出)")
        print()
    else:
        print(f"✅ 全部 {len(hits)} 处旧路径引用都在 redirects.json 有映射\n")

    # 3. 产出 Phase 4 重写清单
    rewrite_list_path = ROOT / 'ProjectState' / 'Reports' / '2026-05-26' / 'phase4_rewrite_list.txt'
    rewrite_list_path.parent.mkdir(parents=True, exist_ok=True)
    with rewrite_list_path.open('w', encoding='utf-8', newline='\n') as f:
        f.write(f"# Phase 4 链接重写清单(Phase 2.2 自动产出,{len(files_with_hits)} 个文件需重写)\n")
        f.write(f"# 来源: Scripts/validation/link_precheck.py 2026-05-26\n")
        f.write(f"# 字典源: Docs/redirects.json({len(redirects)} 条映射)\n")
        f.write(f"# 总命中: {len(hits)} 处引用 / {len(unmapped)} 处未映射\n")
        f.write("#\n")
        f.write("# 每行 = 含旧路径引用的文件相对路径,Phase 4 用 redirects.json 批量重写\n")
        f.write("#\n")
        for file in sorted(files_with_hits):
            f.write(f"{file}\n")

    print(f"Phase 4 重写清单已落盘: {rewrite_list_path.relative_to(ROOT)}({len(files_with_hits)} 个文件)\n")

    if unmapped:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
