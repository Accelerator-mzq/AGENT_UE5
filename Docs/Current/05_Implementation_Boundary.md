# 本阶段实施边界

> 文档版本：L1-Phase5-v2

## P1 允许做到哪里

### Brownfield 分析链

- 允许扩展 `project_state_intake.py`
- 允许在 `Scripts/compiler/analysis/` 下新增 `baseline_builder.py`、`delta_scope_analyzer.py`、辅助 loader
- `ProjectState/Snapshots/` 作为默认 baseline/state snapshot 输出目录
- `ProjectInputs/Baselines/` 只作为人工/冻结 baseline 输入，不作为默认输出目录

### Contract 体系

- `Specs/Contracts/` 允许落地 registry / manifest / template / schema
- 允许落地 `SpecPatchContractModel` / `MigrationContractModel` / `RegressionValidationContractModel`
- 允许在 Brownfield Handoff 中写入 Contract 引用

### Compiler / Demo / Evidence

- 允许扩展 `handoff_builder.py`、`compiler_main.py`
- 允许新增 `Scripts/run_brownfield_demo.py`
- 允许新增项目层证据脚本，如 `Scripts/validation/capture_phase5_evidence.py`
- 允许在真实 UE5 验证时把截图与说明写入 `ProjectState/Evidence/Phase5/`

## P2 只允许做到哪里

- `run_plan_builder.py` / `handoff_runner.py` 只做 Brownfield 最小兼容，不做大重构
- `patch / migration` 先保证“可表达 + 可校验 + 可阻断”，不要求全自动执行
- `SystemTestCases.md` 本阶段不增加 Phase 5 用例正文，待阶段归档时再统一补录

## 不允许做的

- 重写现有 C++ Subsystem
- 重构现有 Bridge 三通道主链
- 修改现有 Automation Test C++ 测试
- 修改现有稳定 Schema（`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`）
- 完整 Genre Skill Pack / Base Skill Domains / 自动审批治理

## 现有文件保护清单

| 文件 | 保护级别 | 理由 |
|------|---------|------|
| `Source/AgentBridge/Public/AgentBridgeSubsystem.h` | 高 | 核心 Subsystem 接口 |
| `Source/AgentBridge/Private/AgentBridgeSubsystem.cpp` | 高 | 核心实现 |
| `Scripts/bridge/*.py` | 高 | 稳定 Bridge 主链 |
| `Scripts/orchestrator/orchestrator.py` | 高 | 既有执行入口 |
| `Scripts/orchestrator/plan_generator.py` | 高 | 既有计划生成器 |
| `Scripts/orchestrator/verifier.py` | 高 | 既有验证器 |
| `Scripts/orchestrator/report_generator.py` | 高 | 既有报告器 |
| `Scripts/orchestrator/spec_reader.py` | 高 | 既有 Spec 读取器 |
| `Schemas/common/*.schema.json` | 高 | 稳定契约 |
| `Schemas/feedback/*.schema.json` | 高 | 稳定契约 |
| `Schemas/write_feedback/*.schema.json` | 高 | 稳定契约 |

如需扩展，应优先新增旁路入口和编译期扩展，不直接破坏稳定核心。
