# -*- coding: utf-8 -*-
"""Phase 1.18 — FEATURE_INVENTORY backfill 脚本
对 Docs/FEATURE_INVENTORY.md 105 行表的 3 列(主文档锚点/测试覆盖/UE 5.7 状态)
按 family + 个别细化规则把 TBD 替换为实地锚点。
"""

import re
from pathlib import Path

# --- 锚点映射(主文档锚点列) ---
ANCHOR_DEFAULT = {
    'F-CPP':       'design/LLD/01_cpp_subsystem.md §2-§3',
    'F-BRG':       'design/LLD/02_bridge.md §2-§3',
    'F-ORC':       'design/LLD/03_orchestrator.md §2-§3',
    'F-CMP':       'design/LLD/04_compiler.md §2-§3',
    'F-MCP':       'design/LLD/05_mcp_server.md §2-§3',
    'F-SKL':       'design/LLD/06_skills_and_templates.md §2-§3',
    'F-RT':        'design/LLD/07_runtime_and_evidence.md §2.1',
    'F-TST':       'design/LLD/07_runtime_and_evidence.md §2.2 + testing/test_spec.md §3',
    'F-HOOK':      'design/LLD/07_runtime_and_evidence.md §2.2 + governance.md §1',
    'F-INP':       'design/LLD/07_runtime_and_evidence.md §2.2',
    'F-DEMO':      'design/LLD/07_runtime_and_evidence.md §2.2',
    'F-VAL':       'design/LLD/07_runtime_and_evidence.md §2.2',
    'F-CHN-S4':    'design/HLD.md §2.2 + design/LLD/04_compiler.md §4.2 + requirements/SRS.md §4.2',
    'F-CHN-MODE':  'requirements/SRS.md §4.4',
    'F-CHN':       'design/HLD.md §2 + requirements/SRS.md §4.1',
    'F-GOV':       'design/HLD.md §3 + requirements/SRS.md §4.3',
    'F-SCH':       'contracts/schemas_catalog.md 主表 + contracts/field_specification.md',
}

# F-CMP 细分(Legacy v1 vs Phase 11)
ANCHOR_CMP_LEGACY_V1 = 'design/LLD/04_compiler.md §2.2'   # F-CMP-01..06、F-CMP-20..24
ANCHOR_CMP_P11       = 'design/LLD/04_compiler.md §2.1'   # F-CMP-07..19

# --- 测试覆盖映射 ---
TEST_DEFAULT = {
    'F-CPP':       'testing/test_spec.md §3 Q+W+CL+UI(L1/L2/L3 自动化合并 57 case)',
    'F-ORC':       'testing/test_spec.md §3 ORC(37 case)',
    'F-CMP':       'testing/test_spec.md §3 CP+SS(64 case)',
    'F-MCP':       'testing/test_spec.md §3 MCP(10 case)',
    'F-SKL':       'testing/test_spec.md §3 SS(20 case)',
    'F-HOOK':      'Scripts/hooks/tests/(pytest)+ testing/test_spec.md §1',
    'F-INP':       'testing/test_spec.md §3 E2E + ORC',
    'F-VAL':       'testing/test_spec.md §3 SV + BL',
    'F-CHN-S4':    'testing/test_spec.md §3 P11(18 case)+ ORC',
    'F-CHN-MODE':  'testing/test_spec.md §3 P11(18 case)+ ORC',
    'F-CHN':       'testing/test_spec.md §3 P11(18 case)+ ORC',
    'F-GOV':       'testing/test_spec.md §3 P11(18 case)+ ORC',
    'F-SCH':       'testing/test_spec.md §5 Schema --strict 26/26',
}

# F-BRG 细分:01..04 走 Q+W+CL+UI;05..09 走 PY+CMD
TEST_BRG_L1_UI = 'testing/test_spec.md §3 Q+W+CL+UI'
TEST_BRG_PY    = 'testing/test_spec.md §3 PY + CMD'

# F-TST 细分:01..03 走 C++ Automation;04 走 E2E+GA
TEST_TST_CPP_AUTO = 'testing/test_spec.md §1 C++ Automation(独立 ~26 条)'
TEST_TST_E2E_GA   = 'testing/test_spec.md §3 E2E + GA(46 case)'

# F-RT / F-DEMO 默认 E2E+GA
TEST_RT_DEMO = 'testing/test_spec.md §3 E2E + GA(46 case)'

# --- UE 5.7 状态映射(根据 BC 命中) ---
# P1 confirmed -> migration
# P2 suspected -> unchanged-pending-test
# P3 / 无 BC   -> unchanged
UE57_STATUS = {
    # F-CPP-01..06: BC-008/010/012 P1 confirmed(Build 整体)
    'F-CPP-01': 'migration (BC-008/010/012 P1; BC-001/014 P2)',
    'F-CPP-02': 'migration (BC-008/010/012 P1; BC-005/014 P2)',
    'F-CPP-03': 'migration (BC-008/010/012 P1; BC-014/020 P2)',
    'F-CPP-04': 'migration (BC-008/010/012 P1; BC-004/014 P2)',
    'F-CPP-05': 'unchanged',  # 只是 USTRUCT
    'F-CPP-06': 'migration (BC-008/010/012 P1; BC-002/014/022/023 P2)',

    # F-BRG-01..04: BC-016 P1(EditorLevelLibrary) + ESU 间接 BC-008 P1
    'F-BRG-01': 'migration (BC-008/016 P1; BC-018 P2)',
    'F-BRG-02': 'migration (BC-008/016/017 P1; BC-018 P2)',
    'F-BRG-03': 'unchanged-pending-test (BC-018 P2)',
    'F-BRG-04': 'unchanged-pending-test (BC-018 P2)',
    # F-BRG-05..09:RC HTTP / UAT / helpers / config / core
    'F-BRG-05': 'unchanged-pending-test (BC-019 P2)',
    'F-BRG-06': 'unchanged-pending-test (BC-020 P2)',
    'F-BRG-07': 'unchanged-pending-test (BC-016/017/018 P2 间接)',
    'F-BRG-08': 'unchanged',
    'F-BRG-09': 'unchanged',

    # F-ORC-*: 纯 Python,主要受 BC-015 Config Layer 影响(P2)
    'F-ORC-01': 'unchanged-pending-test (BC-015 P2)',
    'F-ORC-02': 'unchanged',
    'F-ORC-03': 'unchanged-pending-test (BC-015 P2)',
    'F-ORC-04': 'unchanged',
    'F-ORC-05': 'unchanged',
    'F-ORC-06': 'unchanged',
    'F-ORC-07': 'unchanged',
    'F-ORC-08': 'unchanged',

    # F-CMP-*:Compiler 纯 Python,无直接 UE API
    'F-CMP-01': 'unchanged', 'F-CMP-02': 'unchanged', 'F-CMP-03': 'unchanged',
    'F-CMP-04': 'unchanged', 'F-CMP-05': 'unchanged', 'F-CMP-06': 'unchanged',
    'F-CMP-07': 'unchanged', 'F-CMP-08': 'unchanged', 'F-CMP-09': 'unchanged',
    'F-CMP-10': 'unchanged', 'F-CMP-11': 'unchanged', 'F-CMP-12': 'unchanged',
    'F-CMP-13': 'unchanged', 'F-CMP-14': 'unchanged', 'F-CMP-15': 'unchanged',
    'F-CMP-16': 'unchanged', 'F-CMP-17': 'unchanged', 'F-CMP-18': 'unchanged',
    'F-CMP-19': 'unchanged', 'F-CMP-20': 'unchanged', 'F-CMP-21': 'unchanged',
    'F-CMP-22': 'unchanged', 'F-CMP-23': 'unchanged', 'F-CMP-24': 'unchanged',

    # F-MCP-*:01..05 直接 passthrough UE binding;06..13 纯 Python 前后端
    'F-MCP-01': 'migration (BC-016 P1; BC-018 P2)',
    'F-MCP-02': 'migration (BC-016/017 P1; BC-018 P2)',
    'F-MCP-03': 'unchanged-pending-test (BC-018 P2)',
    'F-MCP-04': 'migration (BC-017 P1; BC-018/019 P2)',
    'F-MCP-05': 'unchanged-pending-test (BC-018/019 P2)',
    'F-MCP-06': 'unchanged',
    'F-MCP-07': 'unchanged',
    'F-MCP-08': 'unchanged',
    'F-MCP-09': 'unchanged',
    'F-MCP-10': 'unchanged',
    'F-MCP-11': 'unchanged',
    'F-MCP-12': 'unchanged-pending-test (BC-019 P2)',
    'F-MCP-13': 'unchanged-pending-test (BC-019 P2)',

    # F-SKL-*:Skill/Template 纯 prompt+schema 无 UE API
    'F-SKL-01': 'unchanged', 'F-SKL-02': 'unchanged',
    'F-SKL-03': 'unchanged', 'F-SKL-04': 'unchanged',

    # F-RT-01..05:BC-025 硬编码 UE_5.5 路径 P1
    'F-RT-01': 'migration (BC-025 P1; BC-015 P2)',
    'F-RT-02': 'migration (BC-025 P1; BC-020 P2)',
    'F-RT-03': 'unchanged',
    'F-RT-04': 'unchanged',
    'F-RT-05': 'unchanged',

    # F-CHN-*:Python 架构链路
    'F-CHN-01': 'unchanged', 'F-CHN-02': 'unchanged', 'F-CHN-03': 'unchanged',
    'F-CHN-04': 'unchanged', 'F-CHN-05': 'unchanged', 'F-CHN-06': 'unchanged',
    'F-CHN-07': 'unchanged',
    'F-CHN-S4-01': 'unchanged', 'F-CHN-S4-02': 'unchanged', 'F-CHN-S4-03': 'unchanged',
    # F-CHN-MODE-*:模式路由可能涉及 RC(BC-019 P2)
    'F-CHN-MODE-01': 'unchanged',
    'F-CHN-MODE-02': 'unchanged',
    'F-CHN-MODE-03': 'unchanged-pending-test (BC-019/025 P2)',

    # F-GOV-*:Python 治理
    'F-GOV-01': 'unchanged', 'F-GOV-02': 'unchanged',
    'F-GOV-03': 'unchanged', 'F-GOV-04': 'unchanged',

    # F-SCH-*:Schema 字段定义,UE 升级不动
    'F-SCH-01': 'unchanged', 'F-SCH-02': 'unchanged', 'F-SCH-03': 'unchanged',
    'F-SCH-04': 'unchanged', 'F-SCH-05': 'unchanged', 'F-SCH-06': 'unchanged',

    # F-VAL-*:BC-021 legacy automation token P2
    'F-VAL-01': 'migration (BC-025 P1; BC-021 P2)',
    'F-VAL-02': 'unchanged',
    'F-VAL-03': 'unchanged',

    # F-TST-01..03:BC-006 FAutomationTestBase P2
    'F-TST-01': 'unchanged-pending-test (BC-006/011/014 P2)',
    'F-TST-02': 'unchanged-pending-test (BC-006/011/014 P2)',
    'F-TST-03': 'unchanged-pending-test (BC-006/011/014 P2)',
    # F-TST-04:Python harness 但调 UAT
    'F-TST-04': 'migration (BC-025 P1; BC-020 P2)',

    # F-HOOK-*:Python Git hooks 无 UE API
    'F-HOOK-01': 'unchanged',
    'F-HOOK-02': 'unchanged',

    # F-INP-*:文件无 UE API
    'F-INP-01': 'unchanged',
    'F-INP-02': 'unchanged',

    # F-DEMO-02/03:boardgame demo + 资产生成
    'F-DEMO-02': 'migration (BC-025 P1; BC-019/020 P2)',
    'F-DEMO-03': 'unchanged-pending-test (BC-017/019 P2)',
}


def resolve_anchor(fid: str) -> str:
    """根据 F-* ID 解析主文档锚点。"""
    # F-CMP 细分
    if fid.startswith('F-CMP-'):
        num = int(fid.split('-')[-1])
        if 1 <= num <= 6 or 20 <= num <= 24:
            return ANCHOR_CMP_LEGACY_V1
        return ANCHOR_CMP_P11
    # F-CHN-S4 / F-CHN-MODE / F-CHN 优先序
    for prefix in ('F-CHN-S4', 'F-CHN-MODE', 'F-CHN'):
        if fid.startswith(prefix + '-'):
            return ANCHOR_DEFAULT[prefix]
    # 通用 family
    for prefix, anchor in ANCHOR_DEFAULT.items():
        if prefix.startswith('F-CHN'):
            continue
        if fid.startswith(prefix + '-'):
            return anchor
    raise ValueError(f'unknown F-* family: {fid}')


def resolve_test(fid: str) -> str:
    """根据 F-* ID 解析测试覆盖。"""
    # F-BRG 细分
    if fid.startswith('F-BRG-'):
        num = int(fid.split('-')[-1])
        if 1 <= num <= 4:
            return TEST_BRG_L1_UI
        return TEST_BRG_PY
    # F-TST 细分
    if fid.startswith('F-TST-'):
        num = int(fid.split('-')[-1])
        if 1 <= num <= 3:
            return TEST_TST_CPP_AUTO
        return TEST_TST_E2E_GA
    # F-RT / F-DEMO
    if fid.startswith('F-RT-') or fid.startswith('F-DEMO-'):
        return TEST_RT_DEMO
    # F-CHN-S4 / F-CHN-MODE / F-CHN
    for prefix in ('F-CHN-S4', 'F-CHN-MODE', 'F-CHN'):
        if fid.startswith(prefix + '-'):
            return TEST_DEFAULT[prefix]
    # 其他 family
    for prefix, test in TEST_DEFAULT.items():
        if prefix.startswith('F-CHN'):
            continue
        if fid.startswith(prefix + '-'):
            return test
    raise ValueError(f'unknown F-* family for test: {fid}')


def resolve_ue57(fid: str) -> str:
    if fid not in UE57_STATUS:
        raise ValueError(f'no UE57 status mapped for: {fid}')
    return UE57_STATUS[fid]


def main():
    inv_path = Path('Docs/FEATURE_INVENTORY.md')
    lines = inv_path.read_text(encoding='utf-8').splitlines(keepends=False)

    # 状态行替换
    for i, line in enumerate(lines):
        if line.startswith('> 状态: 骨架 v1.1'):
            lines[i] = '> 状态: v1.1 实地化(Phase 1.18 已回填),主文档锚点 / 测试覆盖 / UE 5.7 状态全部实地化'

    # 表行匹配:| F-XXX-NN | ... | 共 8 列 9 个分隔符
    row_re = re.compile(r'^\| (F-[A-Z0-9]+(?:-[A-Z0-9]+)*-\d+) \|')

    backfill_count = 0
    fid_seen = []
    for i, line in enumerate(lines):
        m = row_re.match(line)
        if not m:
            continue
        fid = m.group(1)
        fid_seen.append(fid)
        cols = line.split(' | ')
        # cols 结构:'| F-XXX' ... | UE 5.7 状态 |'
        # 用 '|' 切分得到 10 段(首尾空)
        parts = line.split('|')
        # parts: ['', ' F-XXX-NN ', ' 功能名 ', ' 简述 ', ' 模块归属 ', ' 主文档锚点 ', ' 证据源 ', ' 测试覆盖 ', ' UE 5.7 状态 ', '']
        if len(parts) != 10:
            raise SystemExit(f'unexpected column count {len(parts)} at line {i+1}: {line!r}')
        # 替换列 5(主文档锚点)/列 7(测试覆盖)/列 8(UE 5.7 状态)
        parts[5] = f' {resolve_anchor(fid)} '
        parts[7] = f' {resolve_test(fid)} '
        parts[8] = f' {resolve_ue57(fid)} '
        lines[i] = '|'.join(parts)
        backfill_count += 1

    out = '\n'.join(lines) + '\n'
    inv_path.write_text(out, encoding='utf-8')
    print(f'backfilled rows: {backfill_count}')
    print(f'unique IDs: {len(set(fid_seen))}')

    # 自检:数 TBD
    tbd_count = out.count('TBD')
    print(f'remaining TBD count: {tbd_count}')

    # UE 5.7 状态分布
    migration = sum(1 for fid in fid_seen if UE57_STATUS[fid].startswith('migration'))
    pending = sum(1 for fid in fid_seen if UE57_STATUS[fid].startswith('unchanged-pending-test'))
    unchanged = sum(1 for fid in fid_seen if UE57_STATUS[fid] == 'unchanged')
    print(f'UE 5.7 distribution: migration={migration}, unchanged-pending-test={pending}, unchanged={unchanged}')

    # BC-019 严格校验:不允许出现 'migration (BC-019'
    if 'migration (BC-019' in out:
        raise SystemExit('VIOLATION: BC-019 标为 migration,违反 P2 suspected 严守规则')
    print('BC-019 strict check: PASS')


if __name__ == '__main__':
    main()
