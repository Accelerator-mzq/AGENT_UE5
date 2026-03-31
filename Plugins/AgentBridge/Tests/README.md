# AgentBridge 系统测试体系

> 本目录包含 AgentBridge 插件的系统级测试用例文档、自动化脚本与全局执行入口。

## 目录结构

```
Tests/
├── run_system_tests.py        ← 全局入口：一键触发全部 134 条系统测试
├── SystemTestCases.md      ← 系统测试用例总表（主文档）
├── README.md               ← 本文件
└── scripts/                ← 自动化测试脚本
    ├── conftest.py         ← pytest 共享 fixtures
    ├── test_schema_validation.py
    ├── test_e2e_orchestrator.py
    └── test_mvp_regression.py
```

## 快速开始

```bash
# 一键执行全部 9 个 Stage（134 条用例）
python Plugins/AgentBridge/Tests/run_system_tests.py

# 交互模式：选择要执行的 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py --interactive

# 仅执行纯 Python Stage（不需要 UE5 Editor）
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# 指定 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=1,6,7

# 指定引擎路径
python Plugins/AgentBridge/Tests/run_system_tests.py --engine-root="E:\Epic Games\UE_5.5"

# 失败即停
python Plugins/AgentBridge/Tests/run_system_tests.py --fail-fast
```

## 9 个 Stage 流水线

| Stage | 名称 | 用例数 | 需要 Editor | 需要编译 | 自动化工具 |
|-------|------|--------|------------|---------|-----------|
| 1 | Schema 验证（SV） | 5 | — | — | `validate_examples.py` + `pytest` |
| 2 | 编译验证（BL） | 6 | — | 需要 | `Build.bat` (UBT) |
| 3 | Editor 启动 + RC 就绪 | 2 | 需要 | 需要 | `start_ue_editor_project.ps1` |
| 4 | L1/L2/L3 自动化测试 | 57 | 需要 | 需要 | `UnrealEditor-Cmd.exe -RunTests` |
| 5 | Commandlet 功能 | 8 | — | 需要 | `UnrealEditor-Cmd.exe -Tool` |
| 6 | Python 客户端 | 10 | — | — | `pytest` |
| 7 | Orchestrator | 31 | — | — | `pytest` + `orchestrator.py --channel mock` |
| 8 | Gauntlet CI/CD | 6 | 需要 | 需要 | `RunUAT.bat RunUnreal` |
| 9 | E2E 三通道一致性 | 11 | 需要 | 需要 | 多步流水线 |

## 与现有测试体系的关系

| 层级 | 位置 | 类型 | 说明 |
|------|------|------|------|
| L1/L2/L3 自动化测试 | `AgentBridgeTests/` | UE5 C++ Automation Test | 已稳定，不可修改 |
| Schema 校验工具 | `Scripts/validation/` | Python 内置校验 | 已稳定，不可修改 |
| **系统测试** | **`Tests/`（本目录）** | **全局入口 + 文档 + 脚本** | **活跃开发** |
| Gauntlet CI/CD | `Gauntlet/` | C# 配置 | 已稳定 |

## 报告输出

执行完成后自动生成 JSON 汇总报告到 `reports/` 目录：

```json
{
  "timestamp": "2026-03-31T10:00:00",
  "total_stages": 9,
  "passed": 9,
  "failed": 0,
  "skipped": 0,
  "total_cases": 134,
  "overall_status": "passed",
  "stages": [...]
}
```

## 文档与脚本的关系

- `SystemTestCases.md` 是权威来源，每条用例有唯一编号
- `scripts/` 下的脚本通过注释标注对应的用例编号
- `run_system_tests.py` 是全局编排入口，串联所有自动化工具链
