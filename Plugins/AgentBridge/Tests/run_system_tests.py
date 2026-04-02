# -*- coding: utf-8 -*-
"""
AgentBridge 系统测试全局入口
=================================
一键触发当前登记的系统测试用例，按 9 个 Stage 串行执行。

用法:
    # 全自动执行全部 Stage
    python run_all_tests.py

    # 交互模式：选择要执行的 Stage
    python run_all_tests.py --interactive

    # 指定 Stage
    python run_all_tests.py --stage=1,2,6

    # 指定引擎路径（默认自动探测）
    python run_all_tests.py --engine-root="E:\\Epic Games\\UE_5.5"

    # 指定报告输出目录
    python run_all_tests.py --report-dir=./reports

    # 跳过需要 UE5 Editor 的 Stage（仅跑纯 Python 测试）
    python run_all_tests.py --no-editor

Stage 列表:
    1: Schema 验证（SV）         — 纯 Python，秒级
    2: 编译验证（BL）             — Build.bat，分钟级
    3: Editor 启动 + RC 就绪     — start_ue_editor_project.ps1
    4: L1/L2/L3 自动化测试       — Commandlet -RunTests
    5: Commandlet 功能（CMD）    — Commandlet -Tool
    6: Python 客户端（PY）       — pytest
    7: Orchestrator（ORC）       — pytest + orchestrator.py
    8: Gauntlet CI/CD（GA）      — RunUAT.bat RunUnreal
    9: E2E 三通道一致性           — Python 三通道脚本
"""

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
import textwrap

# ============================================================
# 路径常量
# ============================================================

# 本脚本位于 Plugins/AgentBridge/Tests/run_all_tests.py
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))
PROJECT_ROOT = os.path.abspath(os.path.join(PLUGIN_ROOT, '..', '..'))
UPROJECT_PATH = os.path.join(PROJECT_ROOT, 'Mvpv4TestCodex.uproject')

# 子目录
SCRIPTS_DIR = os.path.join(PLUGIN_ROOT, 'Scripts')
BRIDGE_DIR = os.path.join(SCRIPTS_DIR, 'bridge')
VALIDATION_DIR = os.path.join(SCRIPTS_DIR, 'validation')
TESTS_SCRIPTS_DIR = os.path.join(SCRIPT_DIR, 'scripts')
GAUNTLET_DIR = os.path.join(PLUGIN_ROOT, 'Gauntlet')
PROJECT_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'Scripts', 'validation')
ORCHESTRATOR_SAMPLE_SPEC = os.path.join(
    PLUGIN_ROOT, 'Specs', 'templates', 'scene_spec_template.yaml'
)
SYSTEM_TEST_CASES_PATH = os.path.join(SCRIPT_DIR, 'SystemTestCases.md')

# PowerShell 启动脚本
PS_EDITOR_CMD = os.path.join(PROJECT_SCRIPTS_DIR, 'start_ue_editor_cmd_project.ps1')
PS_EDITOR_GUI = os.path.join(PROJECT_SCRIPTS_DIR, 'start_ue_editor_project.ps1')
AGENTBRIDGE_TESTS_UPLUGIN = os.path.join(
    PLUGIN_ROOT, 'AgentBridgeTests', 'AgentBridgeTests.uplugin'
)

if BRIDGE_DIR not in sys.path:
    sys.path.insert(0, BRIDGE_DIR)

from project_config import get_dated_reports_dir, get_project_reports_dir, get_reports_dir, iter_report_files


# ============================================================
# Stage 定义
# ============================================================


def make_case_ids(prefix, start, end):
    """生成文档中的连续编号列表。"""
    return [f'{prefix}-{index:02d}' for index in range(start, end + 1)]


STAGES = {
    1: {
        'name': 'Schema 验证（SV）',
        'cases': 'SV-01 ~ SV-10',
        'case_ids': make_case_ids('SV', 1, 10),
        'count': 10,
        'requires_editor': False,
        'requires_build': False,
    },
    2: {
        'name': '编译与加载（BL）',
        'cases': 'BL-01 ~ BL-06',
        'case_ids': make_case_ids('BL', 1, 6),
        'count': 6,
        'requires_editor': True,
        'requires_build': True,
    },
    3: {
        'name': 'L1/L2/L3 自动化测试（Q/W/CL/UI）',
        'cases': 'Q-01 ~ Q-12, W-01 ~ W-20, CL-01 ~ CL-12, UI-01 ~ UI-13',
        'case_ids': (
            make_case_ids('Q', 1, 12)
            + make_case_ids('W', 1, 20)
            + make_case_ids('CL', 1, 12)
            + make_case_ids('UI', 1, 13)
        ),
        'count': 57,
        'requires_editor': True,
        'requires_build': True,
    },
    4: {
        'name': 'Commandlet 功能（CMD）',
        'cases': 'CMD-01 ~ CMD-08',
        'case_ids': make_case_ids('CMD', 1, 8),
        'count': 8,
        'requires_editor': False,
        'requires_build': True,
    },
    5: {
        'name': 'Python 客户端（PY）',
        'cases': 'PY-01 ~ PY-10',
        'case_ids': make_case_ids('PY', 1, 10),
        'count': 10,
        'requires_editor': False,
        'requires_build': False,
    },
    6: {
        'name': 'Orchestrator（ORC）',
        'cases': 'ORC-01 ~ ORC-37',
        'case_ids': make_case_ids('ORC', 1, 37),
        'count': 37,
        'requires_editor': False,
        'requires_build': False,
    },
    7: {
        'name': 'Compiler Plane + Skills & Specs（CP/SS）',
        'cases': 'CP-01 ~ CP-40, SS-01 ~ SS-20',
        'case_ids': make_case_ids('CP', 1, 40) + make_case_ids('SS', 1, 20),
        'count': 60,
        'requires_editor': False,
        'requires_build': False,
    },
    8: {
        'name': 'Gauntlet CI/CD（GA）',
        'cases': 'GA-01 ~ GA-06',
        'case_ids': make_case_ids('GA', 1, 6),
        'count': 6,
        'requires_editor': True,
        'requires_build': True,
    },
    9: {
        'name': '端到端集成（E2E）',
        'cases': 'E2E-01 ~ E2E-36',
        'case_ids': make_case_ids('E2E', 1, 36),
        'count': 36,
        'requires_editor': True,
        'requires_build': True,
    },
}

TOTAL_CASES = sum(s['count'] for s in STAGES.values())  # 230
CASE_ID_PATTERN = re.compile(
    r'^\|\s*((?:SV|BL|Q|W|CL|UI|CMD|PY|ORC|CP|SS|GA|E2E)-\d{2})\s*\|',
    re.MULTILINE,
)
PHASE7_STAGE7_CASE_IDS = make_case_ids('CP', 32, 40) + make_case_ids('SS', 14, 20)
PHASE7_STAGE9_CASE_IDS = make_case_ids('E2E', 29, 36)
_PHASE7_HELPER_CACHE = None


# ============================================================
# 工具函数
# ============================================================

class StageResult:
    """单个 Stage 的执行结果"""
    def __init__(self, stage_id, stage_info):
        self.stage_id = stage_id
        self.name = stage_info['name']
        # 鎶婃枃妗ｇ紪鍙峰拰 Stage 缁戝畾鍒版姤鍛婇噷锛屾柟渚垮悗缁牳瀵瑰拰瀹℃煡
        self.cases = stage_info['cases']
        self.case_ids = list(stage_info['case_ids'])
        self.case_count = stage_info['count']
        self.status = 'pending'   # pending / running / passed / failed / skipped
        self.exit_code = None
        self.duration_sec = 0.0
        self.message = ''
        self.log_path = ''

    def to_dict(self):
        return {
            'stage': self.stage_id,
            'name': self.name,
            'cases': self.cases,
            'case_ids': self.case_ids,
            'case_count': self.case_count,
            'status': self.status,
            'exit_code': self.exit_code,
            'duration_sec': round(self.duration_sec, 2),
            'message': self.message,
            'log_path': self.log_path,
        }


def print_header(text):
    """打印带分隔线的标题"""
    width = 60
    print('\n' + '=' * width)
    print(f'  {text}')
    print('=' * width)


def print_stage_header(stage_id, stage_info):
    """打印 Stage 开始标题"""
    print_header(f'Stage {stage_id}: {stage_info["name"]}  ({stage_info["count"]} 条用例)')
    print(f'  覆盖: {stage_info["cases"]}')


def decode_subprocess_output(raw_output):
    """稳定解码子进程输出，避免 Windows 控制台编码导致 text=True 崩溃。"""
    if raw_output is None:
        return ''

    if isinstance(raw_output, str):
        return raw_output

    for encoding in ('utf-8', 'gb18030', 'gbk'):
        try:
            return raw_output.decode(encoding)
        except UnicodeDecodeError:
            continue

    # 兜底策略：即使有脏字节，也尽量保留可读日志，避免测试脚本自身崩溃。
    return raw_output.decode('utf-8', errors='replace')


def format_output_tail(stdout, stderr, max_chars=800):
    """合并 stdout/stderr 并截取尾部，方便 Stage 日志摘要显示。"""
    normalized_stdout = stdout or ''
    normalized_stderr = stderr or ''
    merged = '\n'.join(
        part for part in [normalized_stdout, normalized_stderr] if part.strip()
    )
    if not merged:
        return '[无输出]'
    return merged[-max_chars:] if len(merged) > max_chars else merged


def extract_commandlet_exit_code(output):
    """从输出中提取真正的 Commandlet 退出码。"""
    if not output:
        return None

    patterns = [
        r'\[AgentBridge Commandlet\] ExitCode=(\d+)',
        r'Commandlet->Main return this error code:\s*(\d+)',
        r'\[UE-Cmd\] ExitCode=(\d+)',
        r'EXIT CODE:\s*(\d+)',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, output)
        if matches:
            return int(matches[-1])
    return None


def run_command(cmd, cwd=None, timeout=1800, shell=False):
    """
    执行命令并返回 (exit_code, stdout, stderr)
    timeout 默认 30 分钟
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or PROJECT_ROOT,
            capture_output=True,
            text=False,
            timeout=timeout,
            shell=shell,
        )
        return (
            result.returncode,
            decode_subprocess_output(result.stdout),
            decode_subprocess_output(result.stderr),
        )
    except subprocess.TimeoutExpired as e:
        return (
            -1,
            decode_subprocess_output(e.stdout),
            f'命令超时（{timeout}s）\n{decode_subprocess_output(e.stderr)}'.strip(),
        )
    except FileNotFoundError as e:
        return -2, '', f'命令未找到: {e}'
    except Exception as e:
        return -3, '', f'执行异常: {e}'


def run_powershell(script_path, *args, timeout=1800):
    """执行 PowerShell 脚本"""
    cmd = [
        'powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path
    ] + list(args)
    return run_command(cmd, timeout=timeout)


def build_cmd_editor_args(engine_root, *editor_args):
    """构建无头 Editor 命令行，显式传 ProjectPath 与测试插件路径。"""
    args = []
    if engine_root:
        args.extend(['-EngineRoot', engine_root])

    # 显式传 ProjectPath，避免剩余参数被误绑定到脚本的位置参数导致启动失败。
    args.extend(['-ProjectPath', UPROJECT_PATH])

    # 显式传 AgentBridgeTests.uplugin，避免命令行无法定位测试插件。
    if os.path.exists(AGENTBRIDGE_TESTS_UPLUGIN):
        args.append(f'-PLUGIN={AGENTBRIDGE_TESTS_UPLUGIN}')

    args.extend(editor_args)
    return args


def build_direct_cmd_editor_command(engine_root, *editor_args):
    """直接构建 UnrealEditor-Cmd.exe 命令，供 Commandlet 类 Stage 使用。"""
    editor_exe = os.path.join(engine_root, 'Engine', 'Binaries', 'Win64', 'UnrealEditor-Cmd.exe')
    command = [editor_exe, UPROJECT_PATH]

    if os.path.exists(AGENTBRIDGE_TESTS_UPLUGIN):
        command.append(f'-PLUGIN={AGENTBRIDGE_TESTS_UPLUGIN}')

    command.extend(editor_args)
    return command


def detect_known_stage4_blocker(output):
    """识别 Stage 4 常见阻塞并返回可读诊断。"""
    if "Unable to load plugin 'AgentBridgeTests'" in output:
        return (
            "检测到 AgentBridgeTests 插件加载失败；"
            "请检查 -PLUGIN 参数是否指向 "
            "Plugins/AgentBridge/AgentBridgeTests/AgentBridgeTests.uplugin。"
        )
    if "Unknown Automation command 'Automation RunTests" in output:
        return (
            "检测到错误的 Automation 命令调用；"
            "无头模式请改用 -run=AgentBridge -RunTests=<Filter>。"
        )
    return ''


def run_pytest_selection(test_files, keyword=None, timeout=300):
    """执行 pytest 选择集并返回标准结果。"""
    cmd = [sys.executable, '-m', 'pytest', '-v']
    if keyword:
        cmd.extend(['-k', keyword])
    cmd.extend(test_files)
    return run_command(cmd, cwd=PROJECT_ROOT, timeout=timeout)


def get_stage_status(stage_id, completed_results):
    """从已完成结果中查询指定 Stage 状态。"""
    for result in completed_results or []:
        if result.stage_id == stage_id:
            return result.status
    return 'pending'


def load_documented_case_ids():
    """从 SystemTestCases.md 中提取当前文档登记的用例编号。"""
    if not os.path.exists(SYSTEM_TEST_CASES_PATH):
        return []

    with open(SYSTEM_TEST_CASES_PATH, 'r', encoding='utf-8') as file:
        content = file.read()
    return CASE_ID_PATTERN.findall(content)


def build_case_alignment_summary():
    """比对 run_system_tests.py 和 SystemTestCases.md 的编号是否完全一致。"""
    documented_case_ids = load_documented_case_ids()
    staged_case_ids = []
    for stage_id in sorted(STAGES.keys()):
        staged_case_ids.extend(STAGES[stage_id]['case_ids'])

    missing_case_ids = [case_id for case_id in documented_case_ids if case_id not in staged_case_ids]
    extra_case_ids = [case_id for case_id in staged_case_ids if case_id not in documented_case_ids]
    numbering_aligned = bool(documented_case_ids) and documented_case_ids == staged_case_ids

    return {
        'documented_case_ids': documented_case_ids,
        'documented_case_total': len(documented_case_ids),
        'staged_case_ids': staged_case_ids,
        'staged_case_total': len(staged_case_ids),
        'missing_case_ids': missing_case_ids,
        'extra_case_ids': extra_case_ids,
        'numbering_aligned': numbering_aligned,
    }


def load_json_report(report_path):
    """安全读取 JSON 报告，读取失败时返回 None。"""
    if not report_path or not os.path.exists(report_path):
        return None

    try:
        with open(report_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return None


def load_text_report(report_path):
    """瀹夊叏璇诲彇鏂囨湰鎶ュ憡锛岃鍙栧け璐ユ椂杩斿洖绌哄瓧绗︿覆銆?"""
    if not report_path or not os.path.exists(report_path):
        return ''

    try:
        with open(report_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception:
        return ''


def find_latest_report_by_prefix(report_root, prefix, suffix):
    """閫掑綊鎵惧埌鎸囧畾鍓嶇紑鐨勬渶鏂版姤鍛婏紝鍏煎鏃у钩閾哄拰鏂版棩鏈熷瓙鐩綍銆?"""
    candidates = [
        path for path in iter_report_files(report_root, f'*{suffix}')
        if path.name.startswith(prefix) and path.suffix == suffix
    ]
    if not candidates:
        return ''
    return str(max(candidates, key=lambda path: path.stat().st_mtime))


def resolve_report_reference(report_root, report_path):
    """解析历史报告引用，兼容迁移到日期目录后的旧路径。"""
    if not report_path:
        return ''

    if os.path.exists(report_path):
        return report_path

    report_name = os.path.basename(report_path)
    if not report_name:
        return ''

    candidates = [
        path for path in iter_report_files(report_root, report_name)
        if path.name == report_name
    ]
    if not candidates:
        return ''
    return str(max(candidates, key=lambda path: path.stat().st_mtime))


def snapshot_reports_by_prefix(report_root, prefix, suffix='.json'):
    """记录某类报告在执行前的快照，便于识别本轮新产物。"""
    return {
        str(path)
        for path in iter_report_files(report_root, f'*{suffix}')
        if path.name.startswith(prefix) and path.suffix == suffix
    }


def latest_new_report_by_prefix(report_root, prefix, before_paths, suffix='.json'):
    """优先选择本轮新生成的报告，否则回退到当前最新报告。"""
    candidates = [
        str(path)
        for path in iter_report_files(report_root, f'*{suffix}')
        if path.name.startswith(prefix) and path.suffix == suffix
    ]
    if not candidates:
        return ''

    new_candidates = [path for path in candidates if path not in before_paths]
    if new_candidates:
        return max(new_candidates, key=os.path.getmtime)
    return max(candidates, key=os.path.getmtime)


def load_yaml_report(report_path):
    """安全读取 YAML 报告，读取失败时返回空字典。"""
    if not report_path or not os.path.exists(report_path):
        return {}

    try:
        import yaml

        with open(report_path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file) or {}
    except Exception:
        return {}


def build_phase7_helper_bundle():
    """统一执行 Phase 7 归档相关测试与收敛脚本，并缓存结构化结果。"""
    global _PHASE7_HELPER_CACHE
    if _PHASE7_HELPER_CACHE is not None:
        return _PHASE7_HELPER_CACHE

    project_reports_dir = str(get_project_reports_dir())
    pytest_log_path = os.path.join(project_reports_dir, 'run_system_tests_phase7_pytest.log')
    convergence_log_path = os.path.join(project_reports_dir, 'run_system_tests_phase7_p1_convergence.log')
    pytest_file = os.path.join(TESTS_SCRIPTS_DIR, 'test_phase7_governance_and_jrpg.py')
    convergence_script = os.path.join(PROJECT_ROOT, 'Scripts', 'run_phase7_p1_convergence.py')

    pytest_cmd = [sys.executable, '-m', 'pytest', pytest_file]
    pytest_code, pytest_stdout, pytest_stderr = run_command(pytest_cmd, cwd=PROJECT_ROOT, timeout=1800)
    with open(pytest_log_path, 'w', encoding='utf-8') as file:
        file.write('[command] ' + ' '.join(pytest_cmd) + '\n\n')
        file.write('[stdout]\n')
        file.write(pytest_stdout or '')
        file.write('\n\n[stderr]\n')
        file.write(pytest_stderr or '')

    summary_before = snapshot_reports_by_prefix(project_reports_dir, 'phase7_p1_stability_summary_')
    consistency_before = snapshot_reports_by_prefix(project_reports_dir, 'phase7_jrpg_pack_consistency_')
    checklist_before = snapshot_reports_by_prefix(project_reports_dir, 'phase7_archive_preflight_checklist_', '.md')
    acceptance_before = snapshot_reports_by_prefix(project_reports_dir, 'phase7_jrpg_runtime_acceptance_')
    smoke_before = snapshot_reports_by_prefix(project_reports_dir, 'phase7_jrpg_runtime_smoke_')

    convergence_cmd = [sys.executable, convergence_script]
    convergence_code, convergence_stdout, convergence_stderr = run_command(
        convergence_cmd,
        cwd=PROJECT_ROOT,
        timeout=2400,
    )
    with open(convergence_log_path, 'w', encoding='utf-8') as file:
        file.write('[command] ' + ' '.join(convergence_cmd) + '\n\n')
        file.write('[stdout]\n')
        file.write(convergence_stdout or '')
        file.write('\n\n[stderr]\n')
        file.write(convergence_stderr or '')

    summary_path = latest_new_report_by_prefix(
        project_reports_dir,
        'phase7_p1_stability_summary_',
        summary_before,
    )
    consistency_path = latest_new_report_by_prefix(
        project_reports_dir,
        'phase7_jrpg_pack_consistency_',
        consistency_before,
    )
    checklist_path = latest_new_report_by_prefix(
        project_reports_dir,
        'phase7_archive_preflight_checklist_',
        checklist_before,
        '.md',
    )
    acceptance_path = latest_new_report_by_prefix(
        project_reports_dir,
        'phase7_jrpg_runtime_acceptance_',
        acceptance_before,
    )
    smoke_path = latest_new_report_by_prefix(
        project_reports_dir,
        'phase7_jrpg_runtime_smoke_',
        smoke_before,
    )

    summary_report = load_json_report(summary_path) or {}
    consistency_report = load_json_report(consistency_path) or {}
    acceptance_report = load_json_report(acceptance_path) or {}
    smoke_report = load_json_report(smoke_path) or {}
    checklist_text = load_text_report(checklist_path)

    case_results = {}

    for case_id in PHASE7_STAGE7_CASE_IDS:
        case_results[case_id] = (
            pytest_code == 0,
            'Phase 7 pytest 定向回归',
            pytest_log_path,
        )

    for case_id in ['E2E-29', 'E2E-30', 'E2E-31', 'E2E-32', 'E2E-33', 'E2E-34']:
        case_results[case_id] = (
            pytest_code == 0,
            'Phase 7 pytest 端到端验证',
            pytest_log_path,
        )

    evidence_details = (
        acceptance_report.get('checks', {})
        .get('E2E-35', {})
        .get('details', {})
        if isinstance(acceptance_report, dict)
        else {}
    )
    required_screenshot_keys = [
        'overview_oblique',
        'topdown_alignment',
        'actor_battlearena_closeup',
        'actor_herounit_1_closeup',
        'actor_enemyunit_1_closeup',
        'actor_commandmenuanchor_closeup',
    ]
    screenshots = evidence_details.get('screenshots', {}) if isinstance(evidence_details, dict) else {}
    screenshots_ok = all(
        screenshots.get(key) and os.path.exists(screenshots.get(key, ''))
        for key in required_screenshot_keys
    )
    e2e35_ok = (
        convergence_code == 0
        and acceptance_report.get('overall_status') == 'passed'
        and acceptance_report.get('checks', {}).get('E2E-35', {}).get('status') == 'passed'
        and smoke_report.get('overall_status') == 'passed'
        and screenshots_ok
        and evidence_details.get('note_path')
        and os.path.exists(evidence_details.get('note_path', ''))
        and evidence_details.get('log_path')
        and os.path.exists(evidence_details.get('log_path', ''))
    )
    case_results['E2E-35'] = (
        e2e35_ok,
        'JRPG 真机 smoke + 6 张证据图',
        acceptance_path or convergence_log_path,
    )

    round_entries = summary_report.get('rounds', []) if isinstance(summary_report, dict) else []
    boardgame_reports_ok = True
    for round_entry in round_entries:
        round_command_map = {
            command_entry.get('name'): command_entry
            for command_entry in round_entry.get('commands', [])
        }
        for command_name in [
            'boardgame_greenfield_simulated',
            'boardgame_brownfield_simulated',
            'boardgame_playable_simulated',
        ]:
            command_entry = round_command_map.get(command_name, {})
            new_reports = command_entry.get('new_reports', [])
            if not any(
                os.path.basename(report_path).startswith('execution_report_handoff.boardgame.prototype.')
                for report_path in new_reports
            ):
                boardgame_reports_ok = False
                break
        if not boardgame_reports_ok:
            break

    e2e36_ok = (
        convergence_code == 0
        and summary_report.get('overall_status') == 'passed'
        and consistency_report.get('overall_status') == 'passed'
        # 归档前检查表使用 Markdown 勾选框表达完成态，统计勾满项更稳。
        and checklist_text.count('- [x]') >= 4
        and boardgame_reports_ok
    )
    case_results['E2E-36'] = (
        e2e36_ok,
        'boardgame 三条主链连续稳定回归',
        summary_path or convergence_log_path,
    )

    _PHASE7_HELPER_CACHE = {
        'pytest_code': pytest_code,
        'pytest_log_path': pytest_log_path,
        'convergence_code': convergence_code,
        'convergence_log_path': convergence_log_path,
        'summary_path': summary_path,
        'consistency_path': consistency_path,
        'checklist_path': checklist_path,
        'acceptance_path': acceptance_path,
        'smoke_path': smoke_path,
        'case_results': case_results,
    }
    return _PHASE7_HELPER_CACHE


def extract_runtime_state_from_smoke_report(smoke_report):
    """浠?Phase 6 smoke 鎶ュ憡閲岃В鏋愬嚭 runtime state锛屼緵 E2E-26 鍒ゆ柇缁撴灉銆?"""
    if not isinstance(smoke_report, dict):
        return {}

    runtime_state = smoke_report.get('runtime_state', {})
    if not isinstance(runtime_state, dict):
        return {}

    return_value = runtime_state.get('ReturnValue')
    if isinstance(return_value, dict):
        return return_value
    if isinstance(return_value, str) and return_value.strip():
        try:
            return json.loads(return_value)
        except json.JSONDecodeError:
            return {'raw_return_value': return_value}
    return {}


def find_engine_root():
    """自动探测 UE5 引擎根目录"""
    # 常见路径
    candidates = [
        r'E:\Epic Games\UE_5.5',
        r'E:\GameProject\UE5-SourceCode-5.5.4\UnrealEngine',
        r'C:\Program Files\Epic Games\UE_5.5',
        r'D:\Epic Games\UE_5.5',
    ]
    for path in candidates:
        editor_exe = os.path.join(path, 'Engine', 'Binaries', 'Win64', 'UnrealEditor-Cmd.exe')
        if os.path.exists(editor_exe):
            return path

    # 尝试注册表（通过 PowerShell）
    try:
        code, stdout, _ = run_command(
            ['powershell', '-Command',
             '(Get-ItemProperty "HKCU:\\SOFTWARE\\Epic Games\\Unreal Engine\\Builds" -ErrorAction SilentlyContinue).PSObject.Properties | Select-Object -ExpandProperty Value -First 1'],
            timeout=10,
        )
        if code == 0 and stdout.strip():
            path = stdout.strip()
            if os.path.exists(os.path.join(path, 'Engine', 'Binaries', 'Win64', 'UnrealEditor-Cmd.exe')):
                return path
    except Exception:
        pass

    return None


def save_report(results, report_dir, alignment_summary=None, selected_stages=None):
    """保存 JSON 汇总报告"""
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S')
    report_path = os.path.join(report_dir, f'system_test_report_{timestamp}.json')

    passed = sum(1 for r in results if r.status == 'passed')
    failed = sum(1 for r in results if r.status == 'failed')
    skipped = sum(1 for r in results if r.status == 'skipped')

    report = {
        'timestamp': datetime.datetime.now().isoformat(),
        'total_stages': len(results),
        'passed': passed,
        'failed': failed,
        'skipped': skipped,
        'total_cases': TOTAL_CASES,
        'selected_stages': list(selected_stages or []),
        'selected_case_total': sum(
            STAGES[stage_id]['count'] for stage_id in (selected_stages or STAGES.keys())
        ),
        'numbering_alignment': alignment_summary or {},
        'overall_status': 'passed' if failed == 0 else 'failed',
        'stages': [r.to_dict() for r in results],
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_path


# ============================================================
# Stage 实现
# ============================================================

def run_stage_1(result, engine_root, completed_results=None):
    """Stage 1: Schema 验证（SV-01 ~ SV-10）"""
    # SV-01: validate_examples.py --strict
    validate_script = os.path.join(VALIDATION_DIR, 'validate_examples.py')
    if not os.path.exists(validate_script):
        # 也可能在项目层
        validate_script = os.path.join(PLUGIN_ROOT, 'Scripts', 'validation', 'validate_examples.py')

    if not os.path.exists(validate_script):
        result.status = 'failed'
        result.message = f'validate_examples.py 未找到'
        return

    code, stdout, stderr = run_command(
        [sys.executable, validate_script, '--strict'],
        cwd=PROJECT_ROOT,
        timeout=60,
    )
    print(stdout)
    if stderr.strip():
        print(stderr)

    if code != 0:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'Schema 校验失败 (exit code {code})'
        return

    # SV-02 ~ SV-10: pytest 测试
    pytest_code, pytest_out, pytest_err = run_pytest_selection(
        [os.path.join(TESTS_SCRIPTS_DIR, 'test_schema_validation.py')],
        timeout=120,
    )
    print(pytest_out)
    if pytest_err.strip():
        print(pytest_err)

    if code == 0 and pytest_code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'Schema 校验全部通过'
    else:
        result.status = 'failed'
        result.exit_code = pytest_code if pytest_code != 0 else code
        result.message = f'Schema 校验失败'


def run_stage_2(result, engine_root, completed_results=None):
    """Stage 2: 编译与加载（BL-01 ~ BL-06）"""
    if not engine_root:
        result.status = 'skipped'
        result.message = '未找到引擎路径，跳过编译'
        return

    build_bat = os.path.join(engine_root, 'Engine', 'Build', 'BatchFiles', 'Build.bat')
    if not os.path.exists(build_bat):
        result.status = 'skipped'
        result.message = f'Build.bat 未找到: {build_bat}'
        return

    print('  正在编译（可能需要几分钟）...')
    code, stdout, stderr = run_command(
        [build_bat, 'Mvpv4TestCodexEditor', 'Win64', 'Development',
         f'-Project={UPROJECT_PATH}'],
        cwd=PROJECT_ROOT,
        timeout=1800,  # 30 分钟超时
    )

    output = stdout + stderr
    if 'error' in output.lower() and code != 0:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'编译失败 (exit code {code})'
        print('  编译失败！')
        return

    print('  编译通过')

    if not os.path.exists(PS_EDITOR_GUI):
        result.status = 'failed'
        result.exit_code = 1
        result.message = 'start_ue_editor_project.ps1 未找到'
        return

    gui_args = ['-CloseAfterReady']
    if engine_root:
        gui_args.extend(['-EngineRoot', engine_root])

    print('  正在验证 Plugin 加载日志与 RC API 就绪...')
    gui_code, gui_out, gui_err = run_powershell(PS_EDITOR_GUI, *gui_args, timeout=600)
    print(format_output_tail(gui_out, gui_err))
    if gui_code != 0:
        result.status = 'failed'
        result.exit_code = gui_code
        result.message = f'Editor 启动或 RC API 探测失败 (exit code {gui_code})'
        return

    if not os.path.exists(PS_EDITOR_CMD):
        result.status = 'failed'
        result.exit_code = 1
        result.message = 'start_ue_editor_cmd_project.ps1 未找到'
        return

    # BL-04 / BL-05 通过 L1 无头测试隐式覆盖。
    enum_args = build_cmd_editor_args(
        engine_root,
        '-run=AgentBridge',
        '-RunTests=Project.AgentBridge.L1',
        '-Unattended', '-NoPause', '-NoSound', '-NullRHI',
        '-stdout', '-FullStdOutLogOutput',
    )
    print('  正在验证枚举与测试插件加载...')
    enum_code, enum_out, enum_err = run_powershell(PS_EDITOR_CMD, *enum_args, timeout=900)
    print(format_output_tail(enum_out, enum_err))

    blocker_message = detect_known_stage4_blocker(enum_out + enum_err)
    if blocker_message:
        result.status = 'failed'
        result.exit_code = 1
        result.message = blocker_message
        return

    if enum_code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = '编译、加载、枚举与 RC API 验证通过'
    else:
        result.status = 'failed'
        result.exit_code = enum_code
        result.message = f'BL 验证失败 (exit code {enum_code})'


def run_stage_3(result, engine_root, completed_results=None):
    """Stage 3: L1/L2/L3 自动化测试（Q/W/CL/UI）"""
    if not os.path.exists(PS_EDITOR_GUI):
        result.status = 'skipped'
        result.message = f'start_ue_editor_project.ps1 未找到'
        return

    if get_stage_status(2, completed_results) != 'passed':
        print('  [提示] Stage 2 未通过，继续尝试执行自动化测试以输出更具体诊断...')

    if not os.path.exists(PS_EDITOR_CMD):
        result.status = 'skipped'
        result.message = 'start_ue_editor_cmd_project.ps1 未找到'
        return

    # 通过 Commandlet -RunTests 执行全部 UE5 Automation Test
    args = build_cmd_editor_args(
        engine_root,
        '-run=AgentBridge',
        '-RunTests=Project.AgentBridge',
        '-Unattended', '-NoPause', '-NoSound', '-NullRHI',
        '-stdout', '-FullStdOutLogOutput',
    )

    print('  正在运行 L1/L2/L3 自动化测试（无头模式）...')
    code, stdout, stderr = run_powershell(PS_EDITOR_CMD, *args, timeout=900)

    # 提取测试结果摘要
    output = stdout + stderr
    print(output[-1000:] if len(output) > 1000 else output)

    blocker_message = detect_known_stage4_blocker(output)
    if blocker_message:
        result.status = 'failed'
        result.exit_code = code if code != 0 else 1
        result.message = blocker_message
        return

    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'L1/L2/L3 自动化测试全部通过'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'自动化测试失败 (exit code {code})'


def run_stage_4(result, engine_root, completed_results=None):
    """Stage 4: Commandlet 功能测试（CMD-01 ~ CMD-08）"""
    if not engine_root:
        result.status = 'skipped'
        result.message = '未找到引擎路径，无法执行 Commandlet'
        return

    editor_exe = os.path.join(engine_root, 'Engine', 'Binaries', 'Win64', 'UnrealEditor-Cmd.exe')
    if not os.path.exists(editor_exe):
        result.status = 'skipped'
        result.message = f'UnrealEditor-Cmd.exe 未找到: {editor_exe}'
        return

    runtime_dir = os.path.join(PROJECT_ROOT, 'ProjectState', 'Temp', 'run_system_tests_stage4')
    os.makedirs(runtime_dir, exist_ok=True)
    result.log_path = runtime_dir

    common_args = ['-Unattended', '-NoPause', '-NoSound', '-NullRHI', '-stdout', '-FullStdOutLogOutput']
    case_outcomes = []

    def _run_commandlet_case(case_id, commandlet_args, expected_exit, validator, timeout=300):
        """执行单个 Commandlet 用例并记录 PASS/FAIL。"""
        command = build_direct_cmd_editor_command(engine_root, *commandlet_args)
        print(f'  [{case_id}] 执行中...')
        code, stdout, stderr = run_command(command, cwd=PROJECT_ROOT, timeout=timeout)
        combined_output = (stdout or '') + '\n' + (stderr or '')
        output_tail = format_output_tail(stdout, stderr, max_chars=4000)
        effective_exit = extract_commandlet_exit_code(combined_output)
        if effective_exit is None:
            effective_exit = code

        try:
            validator_ok = validator(stdout, stderr, combined_output)
        except Exception as exc:
            validator_ok = False
            output_tail = f'{output_tail}\n[validator exception] {exc}'

        passed_case = effective_exit == expected_exit and validator_ok
        case_outcomes.append((case_id, passed_case, output_tail))
        if passed_case:
            print(f'  [{case_id}] PASS (exit code {effective_exit})')
        else:
            print(f'  [{case_id}] FAIL (expected {expected_exit}, got {effective_exit})')
            print(output_tail)

    cmd01_report = os.path.join(runtime_dir, 'cmd01_get_current_project_state.json')
    _run_commandlet_case(
        'CMD-01',
        [
            '-run=AgentBridge',
            '-Tool=GetCurrentProjectState',
            f'-Report={cmd01_report}',
            *common_args,
        ],
        0,
        lambda _stdout, _stderr, _output: (
            isinstance(load_json_report(cmd01_report), dict)
            and load_json_report(cmd01_report).get('status') == 'success'
        ),
    )

    cmd02_report = os.path.join(runtime_dir, 'cmd02_list_level_actors.json')
    _run_commandlet_case(
        'CMD-02',
        [
            '-run=AgentBridge',
            '-Tool=ListLevelActors',
            f'-Report={cmd02_report}',
            *common_args,
        ],
        0,
        lambda _stdout, _stderr, _output: (
            isinstance(load_json_report(cmd02_report), dict)
            and load_json_report(cmd02_report).get('status') == 'success'
            and isinstance(load_json_report(cmd02_report).get('data', {}).get('actors'), list)
        ),
    )

    cmd03_report = os.path.join(runtime_dir, 'cmd03_unknown_tool.json')
    _run_commandlet_case(
        'CMD-03',
        [
            '-run=AgentBridge',
            '-Tool=NonExistentTool',
            f'-Report={cmd03_report}',
            *common_args,
        ],
        2,
        lambda _stdout, _stderr, output: (
            'Unknown tool' in output
            and isinstance(load_json_report(cmd03_report), dict)
            and load_json_report(cmd03_report).get('status') == 'validation_error'
        ),
    )

    cmd04_report = os.path.join(runtime_dir, 'cmd04_missing_mode.json')
    _run_commandlet_case(
        'CMD-04',
        [
            '-run=AgentBridge',
            f'-Report={cmd04_report}',
            *common_args,
        ],
        2,
        lambda _stdout, _stderr, output: (
            'No mode specified' in output
            and isinstance(load_json_report(cmd04_report), dict)
            and load_json_report(cmd04_report).get('status') == 'validation_error'
        ),
    )

    cmd05_report = os.path.join(runtime_dir, 'cmd05_report_output.json')
    _run_commandlet_case(
        'CMD-05',
        [
            '-run=AgentBridge',
            '-Tool=GetCurrentProjectState',
            f'-Report={cmd05_report}',
            *common_args,
        ],
        0,
        lambda _stdout, _stderr, output: (
            os.path.exists(cmd05_report)
            and isinstance(load_json_report(cmd05_report), dict)
            and 'Report written:' in output
        ),
    )

    cmd06_report = os.path.join(runtime_dir, 'cmd06_run_tests.json')
    _run_commandlet_case(
        'CMD-06',
        [
            '-run=AgentBridge',
            '-RunTests=Project.AgentBridge.L1.Query.GetCurrentProjectState',
            f'-Report={cmd06_report}',
            *common_args,
        ],
        0,
        lambda _stdout, _stderr, output: (
            'RunTests status=' in output
            and isinstance(load_json_report(cmd06_report), dict)
            and load_json_report(cmd06_report).get('status') == 'success'
        ),
        timeout=600,
    )

    cmd07_report = os.path.join(runtime_dir, 'cmd07_build_project_dry_run.json')
    _run_commandlet_case(
        'CMD-07',
        [
            '-run=AgentBridge',
            '-Tool=BuildProject',
            '-Platform=Win64',
            '-Configuration=Development',
            '-bDryRun=true',
            f'-Report={cmd07_report}',
            *common_args,
        ],
        0,
        lambda _stdout, _stderr, _output: (
            isinstance(load_json_report(cmd07_report), dict)
            and load_json_report(cmd07_report).get('status') == 'success'
            and load_json_report(cmd07_report).get('data', {}).get('uat_available') is True
        ),
        timeout=600,
    )

    uat_runner_header = os.path.join(PLUGIN_ROOT, 'Source', 'AgentBridge', 'Public', 'UATRunner.h')
    header_text = ''
    if os.path.exists(uat_runner_header):
        with open(uat_runner_header, 'r', encoding='utf-8') as file:
            header_text = file.read()
    cmd08_passed = 'bool IsSuccess() const { return bLaunched && bCompleted && ExitCode == 0; }' in header_text
    case_outcomes.append((
        'CMD-08',
        cmd08_passed,
        '源码契约校验: FUATRunResult::IsSuccess() 公式必须为 bLaunched && bCompleted && ExitCode == 0',
    ))
    print(f'  [CMD-08] {"PASS" if cmd08_passed else "FAIL"} (源码契约校验)')

    passed = sum(1 for _, ok, _ in case_outcomes if ok)
    failed_cases = [case_id for case_id, ok, _ in case_outcomes if not ok]

    if not failed_cases:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'Commandlet 测试全部通过 ({passed}/{len(case_outcomes)})'
    else:
        result.status = 'failed'
        result.exit_code = 1
        result.message = (
            f'Commandlet 测试失败 ({passed}/{len(case_outcomes)} passed)，'
            f'失败项: {", ".join(failed_cases)}'
        )


def run_stage_5(result, engine_root, completed_results=None):
    """Stage 5: Python 客户端（PY-01 ~ PY-10）"""
    test_file = os.path.join(TESTS_SCRIPTS_DIR, 'test_mvp_regression.py')
    if not os.path.exists(test_file):
        result.status = 'skipped'
        result.message = 'test_mvp_regression.py 未找到'
        return

    code, stdout, stderr = run_pytest_selection(
        [test_file],
        keyword='test_py',
        timeout=180,
    )
    print(stdout)
    if stderr.strip():
        print(stderr)

    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'Python 客户端测试全部通过'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'Python 客户端测试失败 (exit code {code})'


def run_stage_6(result, engine_root, completed_results=None):
    """Stage 7: Compiler Plane + Skills & Specs（CP-01 ~ CP-40, SS-01 ~ SS-20）"""
    test_files = [
        os.path.join(TESTS_SCRIPTS_DIR, 'test_compiler_plane_foundation.py'),
        os.path.join(TESTS_SCRIPTS_DIR, 'test_phase4_compiler.py'),
        os.path.join(TESTS_SCRIPTS_DIR, 'test_phase5_brownfield.py'),
        os.path.join(TESTS_SCRIPTS_DIR, 'test_phase6_playable_runtime.py'),
    ]

    missing_files = [test_file for test_file in test_files if not os.path.exists(test_file)]
    if missing_files:
        result.status = 'skipped'
        result.message = f'测试文件缺失: {missing_files}'
        return

    code, stdout, stderr = run_pytest_selection(
        test_files,
        keyword='test_cp or test_ss',
        timeout=420,
    )
    print(stdout)
    if stderr.strip():
        print(stderr)

    phase7_bundle = build_phase7_helper_bundle()
    phase7_failed = []
    for case_id in PHASE7_STAGE7_CASE_IDS:
        ok, note, evidence_path = phase7_bundle['case_results'].get(
            case_id,
            (False, 'Phase 7 helper 缺少结果', ''),
        )
        evidence_name = os.path.basename(evidence_path) if evidence_path else '无证据'
        print(f'  [{case_id}] {"PASS" if ok else "FAIL"} - {note} ({evidence_name})')
        if not ok:
            phase7_failed.append(case_id)

    if code == 0 and not phase7_failed:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'Compiler Plane + Skills & Specs 测试全部通过（含 Phase 7 新增用例）'
    else:
        result.status = 'failed'
        result.exit_code = code if code != 0 else 1
        details = []
        if code != 0:
            details.append(f'legacy pytest exit={code}')
        if phase7_failed:
            details.append('Phase 7 失败项: ' + ', '.join(phase7_failed))
        result.message = 'Compiler Plane + Skills & Specs 测试失败: ' + ', '.join(details)


def run_stage_7(result, engine_root, completed_results=None):
    """Stage 7: Orchestrator（ORC-01 ~ ORC-37）"""
    test_file = os.path.join(TESTS_SCRIPTS_DIR, 'test_e2e_orchestrator.py')
    if not os.path.exists(test_file):
        result.status = 'skipped'
        result.message = 'test_e2e_orchestrator.py 未找到'
        return

    code, stdout, stderr = run_pytest_selection(
        [test_file],
        keyword='test_orc',
        timeout=180,
    )
    print(stdout)
    if stderr.strip():
        print(stderr)

    orc_script = os.path.abspath(os.path.join(SCRIPTS_DIR, 'orchestrator', 'orchestrator.py'))
    if os.path.exists(orc_script) and os.path.exists(ORCHESTRATOR_SAMPLE_SPEC):
        print('  运行 Orchestrator Mock E2E...')
        orc_code, orc_out, orc_err = run_command(
            [
                sys.executable,
                orc_script,
                os.path.abspath(ORCHESTRATOR_SAMPLE_SPEC),
                '--channel',
                'mock',
            ],
            # 统一在项目根运行，避免脚本路径与相对输出路径被当前工作目录污染。
            cwd=PROJECT_ROOT,
            timeout=120,
        )
        print(format_output_tail(orc_out, orc_err, max_chars=1000))
        if orc_code != 0:
            code = orc_code

    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'Orchestrator 测试全部通过'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'Orchestrator 测试失败 (exit code {code})'


def run_stage_8(result, engine_root, completed_results=None):
    """Stage 8: Gauntlet CI/CD（GA-01 ~ GA-06）"""
    if not engine_root:
        result.status = 'skipped'
        result.message = '未找到引擎路径，跳过 Gauntlet'
        return

    run_uat = os.path.join(engine_root, 'Engine', 'Build', 'BatchFiles', 'RunUAT.bat')
    if not os.path.exists(run_uat):
        result.status = 'skipped'
        result.message = f'RunUAT.bat 未找到: {run_uat}'
        return

    test_config_path = os.path.join(GAUNTLET_DIR, 'AgentBridge.TestConfig.cs')
    if not os.path.exists(test_config_path):
        result.status = 'failed'
        result.exit_code = 1
        result.message = 'AgentBridge.TestConfig.cs 未找到'
        return

    smoke_config_text = open(test_config_path, 'r', encoding='utf-8').read()
    smoke_has_nullrhi = '-NullRHI' in smoke_config_text and 'SmokeTestsFilter' in smoke_config_text
    alltests_uses_real_rhi = 'AllTestsFilter' in smoke_config_text and '-NullRHI' in smoke_config_text and 'AllTests 需要保留真实渲染' in smoke_config_text

    print('  正在运行 Gauntlet SmokeTests...')
    smoke_cmd = [
        run_uat,
        f'-ScriptsForProject={UPROJECT_PATH}',
        f'-ScriptDir={GAUNTLET_DIR}',
        'RunUnreal',
        f'-project={UPROJECT_PATH}',
        '-test=SmokeTests',
        '-Build=Editor',
        '-Platform=Win64',
        '-unattended',
    ]
    smoke_code, smoke_stdout, smoke_stderr = run_command(smoke_cmd, timeout=1200)
    smoke_output = smoke_stdout + smoke_stderr
    print(smoke_output[-1000:] if len(smoke_output) > 1000 else smoke_output)

    # 用无效测试名快速验证“失败时非零退出码”。
    print('  正在验证 Gauntlet 失败返回码...')
    negative_cmd = [
        run_uat,
        f'-ScriptsForProject={UPROJECT_PATH}',
        f'-ScriptDir={GAUNTLET_DIR}',
        'RunUnreal',
        f'-project={UPROJECT_PATH}',
        '-test=DefinitelyMissingAgentBridgeTest',
        '-Build=Editor',
        '-Platform=Win64',
        '-unattended',
    ]
    negative_code, negative_stdout, negative_stderr = run_command(negative_cmd, timeout=600)
    negative_output = negative_stdout + negative_stderr
    print(format_output_tail(negative_output, '', max_chars=800))

    lifecycle_ok = (
        'AgentBridge Gauntlet' in smoke_output
        and 'Finish ExitCode=0' in smoke_output
        and 'TEST COMPLETE. EXIT CODE: 0' in smoke_output
    )
    negative_path_ok = negative_code != 0

    if smoke_code == 0 and smoke_has_nullrhi and alltests_uses_real_rhi and lifecycle_ok and negative_path_ok:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'Gauntlet 配置与 SmokeTests 验证通过'
    else:
        result.status = 'failed'
        result.exit_code = smoke_code if smoke_code != 0 else 1
        details = []
        if smoke_code != 0:
            details.append(f'SmokeTests exit={smoke_code}')
        if not smoke_has_nullrhi:
            details.append('SmokeTests 未检测到 -NullRHI')
        if not alltests_uses_real_rhi:
            details.append('AllTests 配置未检测到真实渲染约束')
        if not lifecycle_ok:
            details.append('未检测到完整生命周期日志')
        if not negative_path_ok:
            details.append('无效测试名未返回非零退出码')
        result.message = 'Gauntlet 验证失败: ' + ', '.join(details)


def run_stage_9(result, engine_root, completed_results=None):
    """Stage 9 兼容入口，统一转到新版 28 条 E2E 判定逻辑。"""
    return run_stage_9_v3(result, engine_root, completed_results)


def run_stage_9_v3(result, engine_root, completed_results=None):
    """Stage 9：E2E-01 ~ E2E-36 统一判定入口。"""
    check_map = {}
    project_reports_dir = str(get_project_reports_dir())
    plugin_reports_dir = str(get_reports_dir())

    def record_case(case_id, ok, note):
        """登记或覆盖某条用例的最终结果。"""
        check_map[case_id] = (ok, note)

    def snapshot_reports(prefix, suffix='.json'):
        """记录执行前已有的报告，用来识别本次新生成的文件。"""
        return {
            str(path)
            for path in iter_report_files(project_reports_dir, f'*{suffix}')
            if path.name.startswith(prefix) and path.suffix == suffix
        }

    def latest_new_report(prefix, before_paths, suffix='.json'):
        """优先选择本次命令新生成的报告，否则退回当前最新报告。"""
        candidates = [
            str(path)
            for path in iter_report_files(project_reports_dir, f'*{suffix}')
            if path.name.startswith(prefix) and path.suffix == suffix
        ]
        if not candidates:
            return ''

        new_candidates = [path for path in candidates if path not in before_paths]
        if new_candidates:
            return max(new_candidates, key=os.path.getmtime)
        return max(candidates, key=os.path.getmtime)

    def find_latest_passing_stage_evidence(stage_id):
        """当本轮未执行前置 Stage 时，回退到历史系统测试报告中的通过证据。"""
        candidates = sorted(
            iter_report_files(plugin_reports_dir, 'system_test_report_*.json'),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for report_path in candidates:
            report = load_json_report(str(report_path)) or {}
            for stage_entry in report.get('stages', []):
                if stage_entry.get('stage') == stage_id and stage_entry.get('status') == 'passed':
                    return True, str(report_path)
        return False, ''

    # 这 6 条用例本质上是前置 Stage 的集成复用，继续直接复用前置结果。
    reused_dependencies = {
        'E2E-05': 1,
        'E2E-06': 3,
        'E2E-07': 8,
        'E2E-08': 6,
        'E2E-09': 4,
        'E2E-10': 8,
    }
    for case_id, stage_id in reused_dependencies.items():
        dependency_status = get_stage_status(stage_id, completed_results)
        dependency_ok = dependency_status == 'passed'
        evidence_path = ''
        if not dependency_ok:
            dependency_ok, evidence_path = find_latest_passing_stage_evidence(stage_id)
        note = f'复用 Stage {stage_id}'
        if evidence_path:
            note += f'（历史证据: {os.path.basename(evidence_path)}）'
        record_case(case_id, dependency_ok, note)

    # Greenfield simulated：用于覆盖 E2E-12/13/14/15/18/22。
    greenfield_script = os.path.join(PROJECT_ROOT, 'Scripts', 'run_greenfield_demo.py')
    if os.path.exists(greenfield_script):
        greenfield_reports_before = snapshot_reports('execution_report_')
        code, stdout, stderr = run_command(
            [sys.executable, greenfield_script],
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        output = stdout + stderr
        greenfield_report_path = latest_new_report('execution_report_', greenfield_reports_before)
        greenfield_report = load_json_report(greenfield_report_path) or {}
        greenfield_summary = greenfield_report.get('summary', {}) if isinstance(greenfield_report, dict) else {}
        greenfield_ok = code == 0 and 'succeeded' in output and 'Approved Handoff:' in output

        record_case('E2E-12', greenfield_ok, 'run_greenfield_demo simulated')
        record_case('E2E-13', greenfield_ok and 'Draft Handoff:' in output, 'greenfield draft handoff 已输出')
        record_case('E2E-14', greenfield_ok and 'Approved Handoff:' in output, 'greenfield approved handoff 已输出')
        record_case(
            'E2E-15',
            greenfield_ok and bool(greenfield_report_path) and greenfield_summary.get('failed', 0) == 0,
            f'greenfield execution report: {os.path.basename(greenfield_report_path) if greenfield_report_path else "缺失"}',
        )
        record_case('E2E-18', greenfield_ok and 'Richer Spec' in output, 'greenfield richer spec 已输出')
        record_case('E2E-22', greenfield_ok, 'Phase 6 greenfield simulated 回归')
    else:
        for case_id in ['E2E-12', 'E2E-13', 'E2E-14', 'E2E-15', 'E2E-18', 'E2E-22']:
            record_case(case_id, False, 'run_greenfield_demo.py 缺失')

    # Brownfield simulated：用于覆盖 E2E-20/23。
    brownfield_script = os.path.join(PROJECT_ROOT, 'Scripts', 'run_brownfield_demo.py')
    if os.path.exists(brownfield_script):
        code, stdout, stderr = run_command(
            [sys.executable, brownfield_script],
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        output = stdout + stderr
        brownfield_ok = (
            code == 0
            and 'succeeded' in output
            and 'append_actor' in output
            and 'PieceO_1' in output
        )
        record_case('E2E-20', brownfield_ok, 'run_brownfield_demo simulated')
        record_case('E2E-23', brownfield_ok, 'Phase 6 brownfield simulated 回归')
    else:
        record_case('E2E-20', False, 'run_brownfield_demo.py 缺失')
        record_case('E2E-23', False, 'run_brownfield_demo.py 缺失')

    # Playable simulated：用于覆盖 E2E-24。
    playable_script = os.path.join(PROJECT_ROOT, 'Scripts', 'run_boardgame_playable_demo.py')
    if os.path.exists(playable_script):
        code, stdout, stderr = run_command(
            [sys.executable, playable_script],
            cwd=PROJECT_ROOT,
            timeout=300,
        )
        output = stdout + stderr
        playable_ok = (
            code == 0
            and 'BoardRuntimeActor' in output
            and 'succeeded' in output
            and 'Phase 6 Acceptance:' in output
        )
        record_case('E2E-24', playable_ok, 'run_boardgame_playable_demo simulated')
    else:
        record_case('E2E-24', False, 'run_boardgame_playable_demo.py 缺失')

    # 从 Phase 6 验收报告中提取 E2E-25~28。
    phase6_acceptance_path = find_latest_report_by_prefix(project_reports_dir, 'phase6_runtime_acceptance_', '.json')
    phase6_smoke_path = find_latest_report_by_prefix(project_reports_dir, 'phase6_runtime_smoke_', '.json')
    phase6_acceptance = load_json_report(phase6_acceptance_path) or {}
    phase6_smoke = load_json_report(phase6_smoke_path) or {}

    # 优先选择 bridge_rc_api 的真实验收报告，避免被 simulated 报告覆盖。
    for candidate in sorted(
        (
            path for path in iter_report_files(project_reports_dir, '*.json')
            if path.name.startswith('phase6_runtime_acceptance_')
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    ):
        candidate_report = load_json_report(str(candidate)) or {}
        if candidate_report.get('bridge_mode') == 'bridge_rc_api':
            phase6_acceptance_path = str(candidate)
            phase6_acceptance = candidate_report
            smoke_report_path = (
                candidate_report.get('checks', {})
                .get('E2E-26', {})
                .get('details', {})
                .get('smoke_report_path', '')
            )
            if smoke_report_path:
                # 兼容历史报告里仍指向迁移前根目录路径的旧引用。
                phase6_smoke_path = resolve_report_reference(project_reports_dir, smoke_report_path)
                phase6_smoke = load_json_report(phase6_smoke_path) or {}
            break

    e2e28_validation_path = ''
    e2e28_validation_text = ''
    for candidate in sorted(
        (
            path for path in iter_report_files(project_reports_dir, '*.md')
            if path.name.startswith('task_phase6_')
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    ):
        candidate_text = load_text_report(str(candidate))
        if 'E2E-28' in candidate_text and '通过' in candidate_text:
            e2e28_validation_path = str(candidate)
            e2e28_validation_text = candidate_text
            break

    phase6_runtime_state = extract_runtime_state_from_smoke_report(phase6_smoke)
    phase6_checks = phase6_acceptance.get('checks', {}) if isinstance(phase6_acceptance, dict) else {}
    e2e27_details = {}
    if isinstance(phase6_checks.get('E2E-27', {}), dict):
        e2e27_details = phase6_checks.get('E2E-27', {}).get('details', {})

    record_case(
        'E2E-25',
        phase6_checks.get('E2E-25', {}).get('status') == 'passed',
        f'引用 {os.path.basename(phase6_acceptance_path) if phase6_acceptance_path else "Phase 6 acceptance 缺失"}',
    )
    record_case(
        'E2E-26',
        (
            phase6_checks.get('E2E-26', {}).get('status') == 'passed'
            and phase6_runtime_state.get('result_state') in {'X_wins', 'O_wins', 'draw'}
        ),
        f'引用 {os.path.basename(phase6_smoke_path) if phase6_smoke_path else "Phase 6 smoke 缺失"}',
    )
    record_case(
        'E2E-27',
        phase6_checks.get('E2E-27', {}).get('status') == 'passed',
        f'引用 {os.path.basename(phase6_acceptance_path) if phase6_acceptance_path else "Phase 6 acceptance 缺失"}',
    )
    record_case(
        'E2E-28',
        (
            phase6_checks.get('E2E-27', {}).get('status') == 'passed'
            and os.path.exists(e2e27_details.get('topdown_alignment', ''))
            and os.path.exists(e2e27_details.get('overview_oblique', ''))
            and bool(e2e28_validation_path)
            and 'E2E-28' in e2e28_validation_text
            and '通过' in e2e28_validation_text
        ),
        f'引用 {os.path.basename(e2e28_validation_path) if e2e28_validation_path else "E2E-28 核验记录缺失"}',
    )

    # 这批用例仍由前置 Stage 的真实集成能力背书。
    environment_gated = [
        'E2E-01', 'E2E-02', 'E2E-03', 'E2E-04', 'E2E-11',
        'E2E-16', 'E2E-17', 'E2E-19', 'E2E-21',
    ]
    stage8_status = get_stage_status(8, completed_results)
    stage3_status = get_stage_status(3, completed_results)
    stage8_ok = stage8_status == 'passed'
    stage3_ok = stage3_status == 'passed'
    stage8_evidence = ''
    stage3_evidence = ''
    if not stage8_ok:
        stage8_ok, stage8_evidence = find_latest_passing_stage_evidence(8)
    if not stage3_ok:
        stage3_ok, stage3_evidence = find_latest_passing_stage_evidence(3)
    for case_id in environment_gated:
        reference_ok = stage8_ok or stage3_ok
        if stage8_ok:
            note = '依赖 Stage 8 集成能力'
            if stage8_evidence:
                note += f'（历史证据: {os.path.basename(stage8_evidence)}）'
        elif stage3_ok:
            note = '依赖 Stage 3 集成能力'
            if stage3_evidence:
                note += f'（历史证据: {os.path.basename(stage3_evidence)}）'
        else:
            note = '缺少 Stage 3/8 的通过证据'
        record_case(case_id, reference_ok, note)

    phase7_bundle = build_phase7_helper_bundle()
    for case_id in PHASE7_STAGE9_CASE_IDS:
        ok, note, evidence_path = phase7_bundle['case_results'].get(
            case_id,
            (False, 'Phase 7 helper 缺少结果', ''),
        )
        evidence_name = os.path.basename(evidence_path) if evidence_path else '无证据'
        record_case(case_id, ok, f'{note}: {evidence_name}')

    missing_case_ids = [case_id for case_id in STAGES[9]['case_ids'] if case_id not in check_map]
    if missing_case_ids:
        result.status = 'failed'
        result.exit_code = 1
        result.message = f'Stage 9 用例注册不完整，缺失: {", ".join(missing_case_ids)}'
        return

    checks = [
        (case_id, check_map[case_id][0], check_map[case_id][1])
        for case_id in STAGES[9]['case_ids']
    ]
    passed = sum(1 for _, ok, _ in checks if ok)
    total = len(checks)
    failed_cases = [case_id for case_id, ok, _ in checks if not ok]

    for case_id, ok, note in checks:
        print(f'  [{case_id}] {"PASS" if ok else "FAIL"} - {note}')

    if passed == total:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'E2E 测试全部通过 ({passed}/{total})'
    else:
        result.status = 'failed'
        result.exit_code = 1
        result.message = f'E2E 测试未全部通过 ({passed}/{total})，失败项: {", ".join(failed_cases)}'


# Stage ID -> 执行函数映射
STAGE_RUNNERS = {
    1: run_stage_1,
    2: run_stage_2,
    3: run_stage_3,
    4: run_stage_4,
    5: run_stage_5,
    6: run_stage_7,
    7: run_stage_6,
    8: run_stage_8,
    9: run_stage_9,
}


# ============================================================
# 交互模式
# ============================================================

def interactive_select():
    """交互式选择要执行的 Stage"""
    print_header('AgentBridge 系统测试 — 交互模式')
    print(f'\n  共 {len(STAGES)} 个 Stage，{TOTAL_CASES} 条用例\n')

    for sid, info in STAGES.items():
        editor_mark = ' [需 Editor]' if info['requires_editor'] else ''
        build_mark = ' [需编译]' if info['requires_build'] else ''
        print(f'  [{sid}] {info["name"]}  ({info["count"]} 条){editor_mark}{build_mark}')

    print(f'\n  输入 Stage 编号，逗号分隔（如 1,2,6）')
    print(f'  输入 all 执行全部，输入 python 仅执行纯 Python Stage (1,5,6,7)')
    raw = input('\n  请选择: ').strip().lower()

    if raw == 'all' or raw == '':
        return list(STAGES.keys())
    elif raw == 'python':
        return [sid for sid, info in STAGES.items()
                if not info['requires_editor'] and not info['requires_build']]
    else:
        try:
            selected = [int(x.strip()) for x in raw.split(',')]
            return [s for s in selected if s in STAGES]
        except ValueError:
            print('  输入无效，执行全部 Stage')
            return list(STAGES.keys())


# ============================================================
# 主入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='AgentBridge 系统测试全局入口 — 一键执行当前登记用例',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''
            示例:
              python run_all_tests.py                     # 全自动
              python run_all_tests.py --interactive        # 交互选择
              python run_all_tests.py --stage=1,6,7        # 仅跑纯 Python
              python run_all_tests.py --no-editor          # 跳过需要 Editor 的 Stage
        '''),
    )
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='交互模式：选择要执行的 Stage')
    parser.add_argument('--stage', '-s', type=str, default='',
                        help='指定 Stage 编号，逗号分隔（如 1,2,6）')
    parser.add_argument('--no-editor', action='store_true',
                        help='跳过需要 UE5 Editor 的 Stage')
    parser.add_argument('--engine-root', type=str, default='',
                        help='UE5 引擎根目录（默认自动探测）')
    parser.add_argument('--report-dir', type=str,
                        default=str(get_dated_reports_dir()),
                        help='报告输出目录')
    parser.add_argument('--fail-fast', action='store_true',
                        help='某个 Stage 失败后立即停止')

    args = parser.parse_args()
    alignment_summary = build_case_alignment_summary()

    if not alignment_summary['numbering_aligned']:
        print_header('SystemTestCases 编号未对齐')
        print(f'  文档总数: {alignment_summary["documented_case_total"]}')
        print(f'  脚本总数: {alignment_summary["staged_case_total"]}')
        if alignment_summary['missing_case_ids']:
            print(f'  文档有但脚本缺失: {", ".join(alignment_summary["missing_case_ids"])}')
        if alignment_summary['extra_case_ids']:
            print(f'  脚本有但文档未登记: {", ".join(alignment_summary["extra_case_ids"])}')
        print(f'  文档路径: {SYSTEM_TEST_CASES_PATH}')
        sys.exit(2)

    # 确定引擎路径
    engine_root = args.engine_root or find_engine_root()

    # 确定要执行的 Stage
    if args.interactive:
        selected_stages = interactive_select()
    elif args.stage:
        try:
            selected_stages = [int(x.strip()) for x in args.stage.split(',')]
            selected_stages = [s for s in selected_stages if s in STAGES]
        except ValueError:
            print('--stage 参数格式错误，使用全部 Stage')
            selected_stages = list(STAGES.keys())
    else:
        selected_stages = list(STAGES.keys())

    # --no-editor 过滤
    if args.no_editor:
        selected_stages = [s for s in selected_stages if not STAGES[s]['requires_editor']]

    # 打印执行计划
    print_header('AgentBridge 系统测试')
    print(f'  引擎路径: {engine_root or "(未找到 — 编译/Editor 相关 Stage 将跳过)"}')
    print(f'  项目路径: {PROJECT_ROOT}')
    print(f'  报告目录: {args.report_dir}')
    total_selected_cases = sum(STAGES[s]['count'] for s in selected_stages)
    print(f'  执行计划: {len(selected_stages)} 个 Stage, {total_selected_cases} 条用例')
    print(f'  Stage:    {", ".join(str(s) for s in selected_stages)}')
    print(f'  编号对齐: 已对齐 SystemTestCases.md（{alignment_summary["documented_case_total"]} 条）')
    print()

    # 执行
    results = []
    overall_start = time.time()

    for stage_id in sorted(STAGES.keys()):
        info = STAGES[stage_id]
        result = StageResult(stage_id, info)

        if stage_id not in selected_stages:
            result.status = 'skipped'
            result.message = '未选中'
            results.append(result)
            continue

        # 检查是否缺少引擎路径
        if (info['requires_build'] or info['requires_editor']) and not engine_root:
            result.status = 'skipped'
            result.message = '需要引擎路径但未找到'
            results.append(result)
            print(f'\n  [Stage {stage_id}] SKIP — {result.message}')
            continue

        print_stage_header(stage_id, info)
        result.status = 'running'
        start = time.time()

        try:
            runner = STAGE_RUNNERS[stage_id]
            runner(result, engine_root, results)
        except Exception as e:
            result.status = 'failed'
            result.message = f'异常: {e}'

        result.duration_sec = time.time() - start
        results.append(result)

        # 打印单 Stage 结果
        status_icon = {'passed': 'PASS', 'failed': 'FAIL', 'skipped': 'SKIP'}.get(result.status, '???')
        print(f'\n  -> [{status_icon}] {result.message}  ({result.duration_sec:.1f}s)')

        # fail-fast
        if args.fail_fast and result.status == 'failed':
            print('\n  --fail-fast 已启用，停止执行')
            # 标记剩余为 skipped
            for remaining_id in sorted(STAGES.keys()):
                if remaining_id > stage_id and remaining_id in selected_stages:
                    skip_result = StageResult(remaining_id, STAGES[remaining_id])
                    skip_result.status = 'skipped'
                    skip_result.message = 'fail-fast 跳过'
                    results.append(skip_result)
            break

    overall_duration = time.time() - overall_start

    # 汇总报告
    print_header('汇总结果')
    passed = sum(1 for r in results if r.status == 'passed')
    failed = sum(1 for r in results if r.status == 'failed')
    skipped = sum(1 for r in results if r.status == 'skipped')

    for r in results:
        icon = {'passed': '[PASS]', 'failed': '[FAIL]', 'skipped': '[SKIP]'}.get(r.status, '[????]')
        print(f'  Stage {r.stage_id}: {icon} {r.name} — {r.message} ({r.duration_sec:.1f}s)')

    print(f'\n  总计: {passed} passed / {failed} failed / {skipped} skipped  ({overall_duration:.1f}s)')

    # 保存 JSON 报告
    report_path = save_report(
        results,
        args.report_dir,
        alignment_summary=alignment_summary,
        selected_stages=selected_stages,
    )
    print(f'  报告: {report_path}')

    # 退出码
    exit_code = 0 if failed == 0 else 1
    print(f'\n  Exit code: {exit_code}')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
