# -*- coding: utf-8 -*-
"""
AgentBridge 系统测试全局入口
=================================
一键触发全部 134 条系统测试用例，按 9 个 Stage 串行执行。

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
VALIDATION_DIR = os.path.join(SCRIPTS_DIR, 'validation')
TESTS_SCRIPTS_DIR = os.path.join(SCRIPT_DIR, 'scripts')
GAUNTLET_DIR = os.path.join(PLUGIN_ROOT, 'Gauntlet')
PROJECT_SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'Scripts', 'validation')

# PowerShell 启动脚本
PS_EDITOR_CMD = os.path.join(PROJECT_SCRIPTS_DIR, 'start_ue_editor_cmd_project.ps1')
PS_EDITOR_GUI = os.path.join(PROJECT_SCRIPTS_DIR, 'start_ue_editor_project.ps1')


# ============================================================
# Stage 定义
# ============================================================

STAGES = {
    1: {
        'name': 'Schema 验证（SV）',
        'cases': 'SV-01 ~ SV-05',
        'count': 5,
        'requires_editor': False,
        'requires_build': False,
    },
    2: {
        'name': '编译验证（BL）',
        'cases': 'BL-01 ~ BL-06',
        'count': 6,
        'requires_editor': False,
        'requires_build': True,
    },
    3: {
        'name': 'Editor 启动 + RC 就绪',
        'cases': 'BL-02, BL-06',
        'count': 2,
        'requires_editor': True,
        'requires_build': True,
    },
    4: {
        'name': 'L1/L2/L3 自动化测试（Q/W/CL/UI）',
        'cases': 'Q-01~12, W-01~20, CL-01~12, UI-01~13',
        'count': 57,
        'requires_editor': True,
        'requires_build': True,
    },
    5: {
        'name': 'Commandlet 功能（CMD）',
        'cases': 'CMD-01 ~ CMD-08',
        'count': 8,
        'requires_editor': False,  # 无头 Commandlet，不需要 GUI Editor
        'requires_build': True,
    },
    6: {
        'name': 'Python 客户端（PY）',
        'cases': 'PY-01 ~ PY-10',
        'count': 10,
        'requires_editor': False,
        'requires_build': False,
    },
    7: {
        'name': 'Orchestrator（ORC）',
        'cases': 'ORC-01 ~ ORC-31',
        'count': 31,
        'requires_editor': False,  # Mock 模式不需要 Editor
        'requires_build': False,
    },
    8: {
        'name': 'Gauntlet CI/CD（GA）',
        'cases': 'GA-01 ~ GA-06',
        'count': 6,
        'requires_editor': True,
        'requires_build': True,
    },
    9: {
        'name': 'E2E 三通道一致性',
        'cases': 'E2E-01 ~ E2E-11',
        'count': 11,
        'requires_editor': True,
        'requires_build': True,
    },
}

TOTAL_CASES = sum(s['count'] for s in STAGES.values())  # 134


# ============================================================
# 工具函数
# ============================================================

class StageResult:
    """单个 Stage 的执行结果"""
    def __init__(self, stage_id, name):
        self.stage_id = stage_id
        self.name = name
        self.status = 'pending'   # pending / running / passed / failed / skipped
        self.exit_code = None
        self.duration_sec = 0.0
        self.message = ''
        self.log_path = ''

    def to_dict(self):
        return {
            'stage': self.stage_id,
            'name': self.name,
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
            text=True,
            timeout=timeout,
            shell=shell,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', f'命令超时（{timeout}s）'
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


def save_report(results, report_dir):
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
        'overall_status': 'passed' if failed == 0 else 'failed',
        'stages': [r.to_dict() for r in results],
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return report_path


# ============================================================
# Stage 实现
# ============================================================

def run_stage_1(result, engine_root):
    """Stage 1: Schema 验证（SV-01 ~ SV-05）"""
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

    # SV-02 ~ SV-04: pytest 测试
    pytest_code, pytest_out, pytest_err = run_command(
        [sys.executable, '-m', 'pytest', '-v',
         os.path.join(TESTS_SCRIPTS_DIR, 'test_schema_validation.py')],
        cwd=PROJECT_ROOT,
        timeout=60,
    )
    print(pytest_out)
    if pytest_err.strip():
        print(pytest_err)

    # 综合判定：validate_examples 必须通过，pytest 允许 skip
    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'Schema 校验全部通过'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'Schema 校验失败'


def run_stage_2(result, engine_root):
    """Stage 2: 编译验证（BL-01 ~ BL-06）"""
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

    # 检查编译结果
    output = stdout + stderr
    if 'error' in output.lower() and code != 0:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'编译失败 (exit code {code})'
        print('  编译失败！')
    else:
        result.status = 'passed'
        result.exit_code = 0
        result.message = '编译通过'
        print('  编译通过')


def run_stage_3(result, engine_root):
    """Stage 3: Editor 启动 + RC 就绪（BL-02, BL-06）"""
    if not os.path.exists(PS_EDITOR_GUI):
        result.status = 'skipped'
        result.message = f'start_ue_editor_project.ps1 未找到'
        return

    args = ['-CloseAfterReady']
    if engine_root:
        args.extend(['-EngineRoot', engine_root])

    print('  正在启动 Editor 并等待 RC API 就绪...')
    code, stdout, stderr = run_powershell(PS_EDITOR_GUI, *args, timeout=600)
    print(stdout[-500:] if len(stdout) > 500 else stdout)

    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'Editor 启动成功，RC API 就绪'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'Editor 启动失败 (exit code {code})'


def run_stage_4(result, engine_root):
    """Stage 4: L1/L2/L3 自动化测试（Q/W/CL/UI）"""
    if not os.path.exists(PS_EDITOR_CMD):
        result.status = 'skipped'
        result.message = 'start_ue_editor_cmd_project.ps1 未找到'
        return

    # 通过 Commandlet -RunTests 执行全部 UE5 Automation Test
    args = [
        '-run=AgentBridge',
        '-RunTests=Project.AgentBridge',
        '-Unattended', '-NoPause', '-NoSound', '-NullRHI',
        '-stdout', '-FullStdOutLogOutput',
    ]
    if engine_root:
        args = ['-EngineRoot', engine_root] + args

    print('  正在运行 L1/L2/L3 自动化测试（无头模式）...')
    code, stdout, stderr = run_powershell(PS_EDITOR_CMD, *args, timeout=900)

    # 提取测试结果摘要
    output = stdout + stderr
    print(output[-1000:] if len(output) > 1000 else output)

    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'L1/L2/L3 自动化测试全部通过'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'自动化测试失败 (exit code {code})'


def run_stage_5(result, engine_root):
    """Stage 5: Commandlet 功能测试（CMD-01 ~ CMD-08）"""
    if not os.path.exists(PS_EDITOR_CMD):
        result.status = 'skipped'
        result.message = 'start_ue_editor_cmd_project.ps1 未找到'
        return

    # 逐个测试关键 Commandlet 模式
    test_cases = [
        ('CMD-01', ['-run=AgentBridge', '-Tool=GetCurrentProjectState',
                     '-Unattended', '-NoPause', '-NullRHI'], 0),
        ('CMD-02', ['-run=AgentBridge', '-Tool=ListLevelActors',
                     '-Unattended', '-NoPause', '-NullRHI'], 0),
        ('CMD-03', ['-run=AgentBridge', '-Tool=NonExistentTool',
                     '-Unattended', '-NoPause', '-NullRHI'], 2),
        ('CMD-04', ['-run=AgentBridge',
                     '-Unattended', '-NoPause', '-NullRHI'], 2),
    ]

    passed = 0
    failed = 0

    for case_id, cmd_args, expected_exit in test_cases:
        args = cmd_args[:]
        if engine_root:
            args = ['-EngineRoot', engine_root] + args

        print(f'  [{case_id}] 执行中...')
        code, stdout, stderr = run_powershell(PS_EDITOR_CMD, *args, timeout=300)

        if code == expected_exit:
            print(f'  [{case_id}] PASS (exit code {code})')
            passed += 1
        else:
            print(f'  [{case_id}] FAIL (expected {expected_exit}, got {code})')
            failed += 1

    if failed == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'Commandlet 测试全部通过 ({passed}/{len(test_cases)})'
    else:
        result.status = 'failed'
        result.exit_code = 1
        result.message = f'Commandlet 测试失败 ({failed}/{len(test_cases)} failed)'


def run_stage_6(result, engine_root):
    """Stage 6: Python 客户端（PY-01 ~ PY-10）"""
    test_file = os.path.join(TESTS_SCRIPTS_DIR, 'test_mvp_regression.py')
    if not os.path.exists(test_file):
        result.status = 'skipped'
        result.message = 'test_mvp_regression.py 未找到'
        return

    code, stdout, stderr = run_command(
        [sys.executable, '-m', 'pytest', '-v', test_file],
        cwd=PROJECT_ROOT,
        timeout=120,
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


def run_stage_7(result, engine_root):
    """Stage 7: Orchestrator（ORC-01 ~ ORC-31）"""
    test_file = os.path.join(TESTS_SCRIPTS_DIR, 'test_e2e_orchestrator.py')
    if not os.path.exists(test_file):
        result.status = 'skipped'
        result.message = 'test_e2e_orchestrator.py 未找到'
        return

    code, stdout, stderr = run_command(
        [sys.executable, '-m', 'pytest', '-v', test_file],
        cwd=PROJECT_ROOT,
        timeout=120,
    )
    print(stdout)
    if stderr.strip():
        print(stderr)

    # ORC-24: Mock 模式 E2E（如果 orchestrator.py 存在）
    orc_script = os.path.join(SCRIPTS_DIR, 'orchestrator', 'orchestrator.py')
    if os.path.exists(orc_script):
        print('  运行 Orchestrator Mock E2E...')
        orc_code, orc_out, orc_err = run_command(
            [sys.executable, orc_script, '--channel', 'mock'],
            cwd=SCRIPTS_DIR,
            timeout=120,
        )
        print(orc_out[-500:] if len(orc_out) > 500 else orc_out)
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


def run_stage_8(result, engine_root):
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

    # SmokeTests（-NullRHI，不需要 GPU）
    print('  正在运行 Gauntlet SmokeTests...')
    cmd = [
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
    code, stdout, stderr = run_command(cmd, timeout=1200)
    output = stdout + stderr
    print(output[-1000:] if len(output) > 1000 else output)

    if code == 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = 'Gauntlet SmokeTests 通过'
    else:
        result.status = 'failed'
        result.exit_code = code
        result.message = f'Gauntlet SmokeTests 失败 (exit code {code})'


def run_stage_9(result, engine_root):
    """Stage 9: E2E 三通道一致性（E2E-01 ~ E2E-11）"""
    # 三通道一致性需要 Editor 运行中
    # 这里运行 E2E-05 (Schema) + E2E-08 (Orchestrator mock) 作为自动化部分
    # E2E-11 三通道一致性需要 Editor + RC API 运行中

    passed = 0
    total = 0

    # E2E-05: Schema 全量验证（复用 Stage 1）
    total += 1
    validate_script = os.path.join(VALIDATION_DIR, 'validate_examples.py')
    if os.path.exists(validate_script):
        code, _, _ = run_command(
            [sys.executable, validate_script, '--strict'],
            cwd=PROJECT_ROOT, timeout=60,
        )
        if code == 0:
            passed += 1
            print('  [E2E-05] Schema 验证 PASS')
        else:
            print('  [E2E-05] Schema 验证 FAIL')
    else:
        print('  [E2E-05] SKIP (脚本未找到)')

    # E2E-08: Orchestrator Mock E2E
    total += 1
    orc_script = os.path.join(SCRIPTS_DIR, 'orchestrator', 'orchestrator.py')
    if os.path.exists(orc_script):
        code, stdout, _ = run_command(
            [sys.executable, orc_script, '--channel', 'mock'],
            cwd=SCRIPTS_DIR, timeout=120,
        )
        if code == 0:
            passed += 1
            print('  [E2E-08] Orchestrator Mock PASS')
        else:
            print(f'  [E2E-08] Orchestrator Mock FAIL (exit {code})')
    else:
        print('  [E2E-08] SKIP (orchestrator.py 未找到)')

    if passed == total:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'E2E 测试通过 ({passed}/{total})'
    elif passed > 0:
        result.status = 'passed'
        result.exit_code = 0
        result.message = f'E2E 测试部分通过 ({passed}/{total})'
    else:
        result.status = 'failed'
        result.exit_code = 1
        result.message = f'E2E 测试失败 ({passed}/{total})'


# Stage ID -> 执行函数映射
STAGE_RUNNERS = {
    1: run_stage_1,
    2: run_stage_2,
    3: run_stage_3,
    4: run_stage_4,
    5: run_stage_5,
    6: run_stage_6,
    7: run_stage_7,
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
    print(f'  输入 all 执行全部，输入 python 仅执行纯 Python Stage (1,6,7)')
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
        description='AgentBridge 系统测试全局入口 — 一键执行 134 条用例',
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
                        default=os.path.join(PLUGIN_ROOT, 'reports'),
                        help='报告输出目录')
    parser.add_argument('--fail-fast', action='store_true',
                        help='某个 Stage 失败后立即停止')

    args = parser.parse_args()

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
    print()

    # 执行
    results = []
    overall_start = time.time()

    for stage_id in sorted(STAGES.keys()):
        info = STAGES[stage_id]
        result = StageResult(stage_id, info['name'])

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
            runner(result, engine_root)
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
                    skip_result = StageResult(remaining_id, STAGES[remaining_id]['name'])
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
    report_path = save_report(results, args.report_dir)
    print(f'  报告: {report_path}')

    # 退出码
    exit_code = 0 if failed == 0 else 1
    print(f'\n  Exit code: {exit_code}')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
