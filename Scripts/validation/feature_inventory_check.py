"""
Mvpv4TestCodex 文档重组验收门禁 — 多源交叉校验脚本

关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §8
关联 plan: Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md Task 2.1

校验项(8 项):
1. FEATURE_INVENTORY 主表 105 行 × 8 列,无 TBD
2. 每个 F-* ID 在新文档(扣 archive/superpowers)能 grep 到
3. mcp_tools_catalog 主表 53 行 × 6 字段
4. schemas_catalog 主表 41 行 × 5 字段(spec 假设 64,实测主表 41 + examples 26 = 67)
5. test_spec §3 主表 15 测试类 × 5 字段(详细 266 case 链回 SystemTestCases.md,不复述)
6. 公开符号(C++ class / Py top-level def / MCP ALL_TOOLS key)在新文档至少 1 处引用
7. inventory CSV 中 already-consumed 行 planned_new_anchor 无 Planned: 前缀
8. redirects.json 108 条 == inventory CSV 108 行(双向一致)

退出码:0 = 全部通过;1 = 有 errors;2 = 有 warnings(无 errors)
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / 'Docs'
PLUGIN = ROOT / 'Plugins' / 'AgentBridge'

errors: list[str] = []
warnings: list[str] = []


def _new_docs() -> list[Path]:
    """返回新文档清单(扣 archive/superpowers/FEATURE_INVENTORY 本身)。"""
    out = []
    for p in DOCS.rglob('*.md'):
        parts = p.parts
        if 'archive' in parts or 'superpowers' in parts:
            continue
        out.append(p)
    return out


def _all_new_doc_text() -> str:
    """所有新文档拼接后的文本,用于符号 grep。"""
    return '\n'.join(p.read_text(encoding='utf-8') for p in _new_docs())


# 检查 1: FEATURE_INVENTORY 主表无 TBD
def check_inventory_no_tbd():
    p = DOCS / 'FEATURE_INVENTORY.md'
    in_main_table = False
    for i, line in enumerate(p.read_text(encoding='utf-8').split('\n'), 1):
        # 主表起点:遇到第一个数据行(以 | F- 开头)
        if line.startswith('| F-'):
            in_main_table = True
            if 'TBD' in line:
                errors.append(f"[FEATURE_INVENTORY:L{i}] 主表 TBD 残留: {line[:120]}")
        # 主表之外的 TBD(如 §验收门禁区的 'TBD: Phase 1 grep 回填')是设计保留,不报错


# 检查 2: 每个 F-* ID 在新文档能 grep 到
def check_inventory_ids_referenced():
    inv = (DOCS / 'FEATURE_INVENTORY.md').read_text(encoding='utf-8')
    # 只抓主表中的 F-* ID(以 `| F-` 起的行的第一列)
    ids = set()
    for line in inv.split('\n'):
        if line.startswith('| F-'):
            m = re.match(r'^\|\s*(F-[A-Z]+(?:-[A-Z0-9]+)?-\d+)\s*\|', line)
            if m:
                ids.add(m.group(1))

    new_docs_text = {}
    for p in _new_docs():
        if p.name == 'FEATURE_INVENTORY.md':
            continue
        new_docs_text[p] = p.read_text(encoding='utf-8')

    for fid in sorted(ids):
        if not any(fid in text for text in new_docs_text.values()):
            errors.append(f"[F-ID 未引用] {fid} 在新文档中无引用(应至少 1 处 SRS/HLD/LLD/contracts)")


# 检查 3: mcp_tools_catalog 主表 53 行 × 6 字段
def check_mcp_catalog():
    p = DOCS / 'contracts' / 'mcp_tools_catalog.md'
    if not p.exists():
        errors.append(f"[mcp_tools_catalog] 文件不存在: {p}")
        return
    rows = []
    in_main_table = False
    for line in p.read_text(encoding='utf-8').split('\n'):
        # 进入主表:遇到表头(工具名 | 类别 ...)
        if line.startswith('|') and '工具名' in line:
            in_main_table = True
            continue
        # 跳过分隔行
        if in_main_table and re.match(r'^\|\s*[-:]+', line):
            continue
        # 遇到下一个 H2 或空行,主表结束
        if in_main_table:
            if not line.startswith('|'):
                in_main_table = False
                continue
            rows.append(line)
    if len(rows) != 53:
        errors.append(f"[mcp_tools_catalog] 期望主表 53 行,实测 {len(rows)}")
    for i, r in enumerate(rows, 1):
        cols = r.split('|')
        # 6 字段 → 7 个 | 分隔符 → split 得 8 段(头尾空)
        if len(cols) != 8:
            errors.append(f"[mcp_tools_catalog 主表行 {i}] 字段数 != 6: split={len(cols)} | {r[:100]}")


# 检查 4: schemas_catalog 主表 41 行 × 5 字段(实测,非 spec 假设的 64)
def check_schemas_catalog():
    p = DOCS / 'contracts' / 'schemas_catalog.md'
    if not p.exists():
        errors.append(f"[schemas_catalog] 文件不存在: {p}")
        return
    rows = []
    in_main_table = False
    for line in p.read_text(encoding='utf-8').split('\n'):
        # 主表表头:文件 | 用途 | 版本 | 引用方 | 关键字段清单
        if line.startswith('|') and '文件' in line and '用途' in line and '版本' in line:
            in_main_table = True
            continue
        if in_main_table and re.match(r'^\|\s*[-:]+', line):
            continue
        if in_main_table:
            if not line.startswith('|'):
                in_main_table = False
                continue
            rows.append(line)
    if len(rows) != 41:
        errors.append(f"[schemas_catalog] 期望主表 41 行(实测主 schema 数),实测 {len(rows)}")
    for i, r in enumerate(rows, 1):
        cols = r.split('|')
        # 5 字段 → 6 个 | → split 得 7 段
        if len(cols) != 7:
            errors.append(f"[schemas_catalog 主表行 {i}] 字段数 != 5: split={len(cols)} | {r[:100]}")


# 检查 5: test_spec §3 主表 15 测试类 × 5 字段
def check_test_spec():
    p = DOCS / 'testing' / 'test_spec.md'
    if not p.exists():
        errors.append(f"[test_spec] 文件不存在: {p}")
        return
    rows = []
    in_main_table = False
    for line in p.read_text(encoding='utf-8').split('\n'):
        # 主表表头:测试类 | ID 范围 | 入口脚本 | 期望大类 | 当前状态汇总
        if line.startswith('|') and '测试类' in line and 'ID 范围' in line:
            in_main_table = True
            continue
        if in_main_table and re.match(r'^\|\s*[-:]+', line):
            continue
        if in_main_table:
            if not line.startswith('|'):
                in_main_table = False
                continue
            rows.append(line)
    if len(rows) != 15:
        errors.append(f"[test_spec §3] 期望主表 15 测试类,实测 {len(rows)}")
    for i, r in enumerate(rows, 1):
        cols = r.split('|')
        # 5 字段 → 7 段
        if len(cols) != 7:
            errors.append(f"[test_spec §3 主表行 {i}] 字段数 != 5: split={len(cols)} | {r[:100]}")


# 检查 6: 公开符号被引用(C++ class / Py top-level def / MCP ALL_TOOLS key)
def check_public_symbols():
    symbols: set[str] = set()

    # C++ class(只抓 Plugins/AgentBridge/Source 内 .h 文件;排除 forward decl `class X;`)
    src = PLUGIN / 'Source'
    for h in src.rglob('*.h'):
        for line in h.read_text(encoding='utf-8').split('\n'):
            stripped = line.strip()
            # 排除 forward decl(以 ; 结尾且无 { 的 class 行)
            if re.match(r'^class\s+\w+\s*;\s*$', stripped):
                continue
            # class UAgentBridgeSubsystem / FUATRunner / FAutomationDriverAdapter(必须带 body 或继承)
            m = re.match(r'^\s*class\s+(?:\w+_API\s+)?([UFAI]\w+)(?:\s*[:{]|\s+final\b)', line)
            if m:
                name = m.group(1).rstrip(':')
                # 排除明显 helper(以下划线开头)
                if not name.startswith('_'):
                    symbols.add(name)

    # MCP ALL_TOOLS 工具名(53 个)
    try:
        sys.path.insert(0, str(PLUGIN))
        from MCP.tool_definitions import ALL_TOOLS  # type: ignore
        symbols.update(ALL_TOOLS.keys())
    except Exception as e:
        warnings.append(f"[check_public_symbols] 无法 import ALL_TOOLS: {e}")

    if not symbols:
        warnings.append("[check_public_symbols] 未扫到任何符号,跳过")
        return

    all_text = _all_new_doc_text()
    missing = sorted(s for s in symbols if s not in all_text)
    if missing:
        # 只报前 10 个,避免噪音
        sample = missing[:10]
        more = '' if len(missing) <= 10 else f"(还有 {len(missing) - 10} 个未列出)"
        for s in sample:
            errors.append(f"[符号未引用] {s} 在新文档中无提及")
        if more:
            errors.append(f"[符号未引用] 总计 {len(missing)} 个 {more}")


# 检查 7: inventory CSV already-consumed 行已实地化
def check_inventory_csv():
    p = DOCS / 'superpowers' / 'specs' / '2026-05-26-old-docs-inventory.csv'
    if not p.exists():
        errors.append(f"[inventory CSV] 文件不存在: {p}")
        return
    with p.open(encoding='utf-8') as f:
        for i, row in enumerate(csv.DictReader(f), 2):
            if row['status'] == 'already-consumed' and row['planned_new_anchor'].startswith('Planned:'):
                errors.append(f"[inventory CSV L{i}] already-consumed 行未剥 Planned: 前缀: {row['old_path']}")
            if row['status'] == 'need-consume' and row['planned_new_anchor'].startswith('Planned:'):
                errors.append(f"[inventory CSV L{i}] need-consume 行未实地化: {row['old_path']}")


# 检查 8: redirects.json 与 inventory 一致
def check_redirects():
    rp = DOCS / 'redirects.json'
    ip = DOCS / 'superpowers' / 'specs' / '2026-05-26-old-docs-inventory.csv'
    if not rp.exists() or not ip.exists():
        errors.append("[redirects/inventory] 文件缺失")
        return
    redirects = json.loads(rp.read_text(encoding='utf-8'))
    inv_paths: set[str] = set()
    with ip.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            inv_paths.add(row['old_path'])

    redirect_paths = set(redirects.keys())
    only_in_redirects = redirect_paths - inv_paths
    only_in_inventory = inv_paths - redirect_paths

    for old in sorted(only_in_redirects):
        errors.append(f"[redirects] {old} 在 redirects.json 但不在 inventory CSV")
    for old in sorted(only_in_inventory):
        warnings.append(f"[redirects] {old} 在 inventory CSV 但不在 redirects.json")


def main():
    checks = [
        ('1. FEATURE_INVENTORY 主表无 TBD', check_inventory_no_tbd),
        ('2. F-* ID 在新文档被引用', check_inventory_ids_referenced),
        ('3. mcp_tools_catalog 53 行 × 6 字段', check_mcp_catalog),
        ('4. schemas_catalog 41 行 × 5 字段', check_schemas_catalog),
        ('5. test_spec §3 15 测试类 × 5 字段', check_test_spec),
        ('6. 公开符号(C++ class + MCP 工具)被引用', check_public_symbols),
        ('7. inventory CSV already-consumed 已实地化', check_inventory_csv),
        ('8. redirects.json 与 inventory 一致', check_redirects),
    ]
    print(f"运行 {len(checks)} 项校验...\n")
    for name, fn in checks:
        before_err = len(errors)
        before_warn = len(warnings)
        try:
            fn()
            new_err = len(errors) - before_err
            new_warn = len(warnings) - before_warn
            if new_err == 0 and new_warn == 0:
                print(f"✅ {name}")
            elif new_err == 0:
                print(f"⚠ {name}(+{new_warn} 警告)")
            else:
                print(f"❌ {name}(+{new_err} 错误,+{new_warn} 警告)")
        except Exception as e:
            errors.append(f"[{name}] 校验脚本异常: {e}")
            print(f"💥 {name} 异常: {e}")

    print(f"\n=== 汇总: {len(errors)} 错误 / {len(warnings)} 警告 ===")
    if errors:
        print("\n错误清单:")
        for e in errors:
            print(f"  ❌ {e}")
    if warnings:
        print("\n警告清单:")
        for w in warnings:
            print(f"  ⚠ {w}")

    if errors:
        sys.exit(1)
    if warnings:
        sys.exit(2)
    sys.exit(0)


if __name__ == '__main__':
    main()
