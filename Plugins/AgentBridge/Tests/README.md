# AgentBridge 系统测试体系

> 本目录包含 AgentBridge 插件的系统级测试总表、全局执行入口与辅助脚本。
> 当前口径：10 个 Stage，248 条用例，已纳入 Phase 10 归档。

## 目录结构

```text
Tests/
├── run_system_tests.py        -> 全局入口，串行执行当前登记的 248 条系统测试
├── SystemTestCases.md         -> 权威测试总表
├── README.md                  -> 本文件
└── scripts/                   -> pytest 辅助脚本
```

## 快速开始

```powershell
# 执行全部 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py

# 交互模式
python Plugins/AgentBridge/Tests/run_system_tests.py --interactive

# 只跑无编辑器相关 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# 针对 Phase 10 对齐后的关键 Stage
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=7,9,10

# 单独验证 MCP 集成层
python Plugins/AgentBridge/Tests/run_system_tests.py --stage=10
```

## 10 个 Stage

| Stage | 名称 | 用例数 | 需要 Editor | 需要编译 | 说明 |
|-------|------|--------|------------|---------|------|
| 1 | Schema 验证（SV） | 10 | 否 | 否 | example / schema / 严格校验 |
| 2 | 编译与加载（BL） | 6 | 是 | 是 | UBT、插件加载、RC 探测 |
| 3 | L1/L2/L3 自动化测试（Q/W/CL/UI） | 57 | 是 | 是 | UE 自动化测试主干 |
| 4 | Commandlet 功能（CMD） | 8 | 否 | 是 | 无头工具与测试触发 |
| 5 | Python 客户端（PY） | 10 | 否 | 否 | Python Bridge / Mock |
| 6 | Orchestrator（ORC） | 37 | 否 | 否 | Orchestrator / mock / helper |
| 7 | Compiler Plane + Skills & Specs（CP/SS） | 64 | 否 | 否 | 含 Phase 10 CP-41~44 |
| 8 | Gauntlet CI/CD（GA） | 6 | 是 | 是 | SmokeTests / AllTests |
| 9 | 端到端集成（E2E） | 40 | 是 | 是 | 含 Phase 10 E2E-37~40 |
| 10 | MCP Server 集成（MCP） | 10 | 否 | 否 | 含 Phase 10 当前 MCP 42 工具与证据裁决 |

## Phase 10 特别说明

- `SystemTestCases.md` 已补入 Phase 10 的归档验收项。
- `run_system_tests.py` 已与总表对齐到 `248` 条用例。
- Phase 10 官方无编辑器验收口径不是单次长链路强跑，而是“Stage 分段等价验证”。

对应证据：

- [no_editor_equivalent_strategy.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/no_editor_equivalent_strategy.md)
- [task09_final_acceptance_validation.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-11/task09_final_acceptance_validation.md)

## 与现有测试体系的关系

| 层级 | 位置 | 类型 | 说明 |
|------|------|------|------|
| L1/L2/L3 自动化测试 | `AgentBridgeTests/` | UE5 C++ Automation Test | 稳定基线，不直接在这里改 |
| Schema 校验工具 | `Scripts/validation/` | Python 校验 | 基础校验链 |
| 系统测试 | `Tests/` | 总表 + 编排入口 | 当前活跃维护区域 |
| Gauntlet | `Gauntlet/` | C# 配置 | Editor 级集成与 CI |

## 报告输出

执行完成后会把系统测试报告输出到 `Plugins/AgentBridge/reports/<date>/`，JSON 中会记录：

- `total_stages`
- `passed / failed / skipped`
- `total_cases`
- `alignment_summary`
- 各 Stage 的 `case_ids / case_count / status`

## 文档与脚本关系

- [SystemTestCases.md](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/SystemTestCases.md) 是权威来源。
- [run_system_tests.py](/D:/UnrealProjects/Mvpv4TestCodex/Plugins/AgentBridge/Tests/run_system_tests.py) 必须与总表编号、数量、顺序完全一致。
- 归档阶段的新增验收项，应先补总表，再同步脚本与 README 口径。
