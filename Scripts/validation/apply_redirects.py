"""
Mvpv4TestCodex 文档重组 — Phase 4 链接批量重写

关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §8
关联 plan: Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md Task 4.1-4.3

作用:
按 Docs/redirects.json 把 17 个文件中的旧路径引用批量重写为新归宿。
- 旧路径前缀:Docs/{Current,History,Decisions,Proposals,superpowers}/ + Plugins/AgentBridge/Docs/
- 新归宿统一加 Docs/ 前缀,多 anchor 取首项,剥末尾括号注释

重写形态(3 种):
1. 绝对路径(markdown link href):/D:/UnrealProjects/Mvpv4TestCodex/<old>
   → /D:/UnrealProjects/Mvpv4TestCodex/Docs/<new-anchor>
2. inline code 反引号:`<old>` → `Docs/<new-anchor>`
3. 裸路径(纯字符串引用):<old> → Docs/<new-anchor>

注意:
- 按 redirects key 长度倒序替换(避免短前缀先吃掉长 key)
- redirects value 中的 (全替换) / (Phase 0.4 产出) 等末尾括号注释会被剥
- 多 anchor "A + B" 取首项 A;B 部分如出现 broken link 需 Phase 4 Step 2 人工调整

退出码:0 = 全 PASS;1 = 文件读写出错
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / 'Docs'


def normalize_new(value: str) -> str:
    """把 redirects value 转换成完整的新链接 anchor(带 Docs/ 前缀)。

    示例:
    - 'archive/current/04_Open_Risks.md'
      → 'Docs/archive/current/04_Open_Risks.md'
    - 'INDEX.md (全替换)'
      → 'Docs/INDEX.md'
    - 'requirements/SRS.md#1 + acceptance/acceptance_report.md#1'
      → 'Docs/requirements/SRS.md#1'(取首 anchor)
    """
    # 1) 多 anchor 取首项
    first = value.split(' + ')[0].strip()
    # 2) 剥末尾 ' (注释)'(如 (全替换) / (Phase 0.4 产出))
    first = re.sub(r'\s*\([^)]*\)\s*$', '', first).strip()
    # 3) 加 Docs/ 前缀(若未带)
    return first if first.startswith('Docs/') else f'Docs/{first}'


def main():
    redirects = json.loads((DOCS / 'redirects.json').read_text(encoding='utf-8'))

    # 加载 17 文件清单(由 link_precheck.py 产出)
    list_path = ROOT / 'ProjectState' / 'Reports' / '2026-05-26' / 'phase4_rewrite_list.txt'
    lines = list_path.read_text(encoding='utf-8').splitlines()
    files = [l for l in lines if l and not l.startswith('#')]

    # 按 key 长度倒序(长 key 先替换,避免短前缀提前吃掉)
    keys_sorted = sorted(redirects.keys(), key=len, reverse=True)

    stats = {'rewrites': 0, 'files_changed': 0, 'files_total': len(files)}
    for fp in files:
        p = ROOT / fp
        if not p.exists():
            print(f'  跳过(文件不存在):{fp}')
            continue
        text = p.read_text(encoding='utf-8')
        original = text
        for old in keys_sorted:
            new = normalize_new(redirects[old])
            # 形态 1:绝对路径
            text = text.replace(
                f'/D:/UnrealProjects/Mvpv4TestCodex/{old}',
                f'/D:/UnrealProjects/Mvpv4TestCodex/{new}',
            )
            # 形态 2/3:裸 old → new(覆盖 backtick / markdown 相对 link / 句中纯字符串)
            text = text.replace(old, new)
        if text != original:
            p.write_text(text, encoding='utf-8', newline='\n')
            diff_count = sum(
                1 for a, b in zip(original.split('\n'), text.split('\n')) if a != b
            )
            stats['rewrites'] += diff_count
            stats['files_changed'] += 1
            print(f"  ✍️  {fp}({diff_count} 行变更)")

    print(
        f"\n总计: {stats['files_changed']}/{stats['files_total']} 文件改动,"
        f"{stats['rewrites']} 行变更"
    )
    return 0


if __name__ == '__main__':
    sys.exit(main())
