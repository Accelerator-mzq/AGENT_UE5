# 本阶段实施边界

> 文档版本：L1-Phase5-v1

## P1 允许做到哪里

### Brownfield 分析链

- `Scripts/compiler/analysis/` 下新增 `baseline_builder.py`、`delta_scope_analyzer.py`
- `project_state_intake.py` 允许桥接真实 Bridge 查询
- `ProjectState/Snapshots/` / `ProjectInputs/Baselines/` 允许作为基线实例落点

### Contract 体系

- `Specs/Contracts/` 下可新增 Contract registry、manifest、template、schema
- 允许落地 `SpecPatchContract`、`MigrationContract`、`RegressionValidationContract`
- 允许在 `reviewed_handoff` 的现有 Brownfield 字段内填充 Contract 引用和差量上下文

### Compiler / Handoff 集成

- 允许扩展 `handoff_builder.py`、`compiler_main.py`、`project_state_intake.py`
- 允许为 Brownfield 模式补 `baseline_context`、`delta_context`、`tree_type=delta`
- 允许新增 Phase 5 Python 测试和系统测试条目

## P2 只允许做到哪里

- `run_plan_builder.py` 与 `handoff_runner.py` 只允许做 Brownfield 最小兼容适配，不做大重构
- Greenfield 现有执行链必须继续保持可用
- Contract 先保证“可表达 + 可校验 + 可报告缺口”，不要求一步到位完成全自动回归执行

## 不允许做的

- 完整 Genre Skill Pack 机制
- 完整 Base Skill Domains 机制
- 自动化 Handoff 审批治理
- 重写现有 C++ Subsystem
- 重构已有 Bridge 三通道主链
- 修改现有 Automation Test C++ 测试
- 修改现有稳定 Schema（`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`）

## 现有文件保护清单

以下文件/模块不允许大改：

| 文件 | 保护级别 | 理由 |
|------|---------|------|
| `Source/AgentBridge/Public/AgentBridgeSubsystem.h` | 高 | 核心 Subsystem，稳定接口 |
| `Source/AgentBridge/Private/AgentBridgeSubsystem.cpp` | 高 | 核心实现，已通过测试 |
| `Source/AgentBridge/Public/BridgeTypes.h` | 高 | 统一响应格式 |
| `Scripts/bridge/*.py` | 高 | 三通道客户端已稳定 |
| `Scripts/orchestrator/orchestrator.py` | 高 | 现有执行链入口 |
| `Scripts/orchestrator/plan_generator.py` | 高 | 现有计划生成器 |
| `Scripts/orchestrator/verifier.py` | 高 | 现有验证器 |
| `Scripts/orchestrator/report_generator.py` | 高 | 现有报告生成器 |
| `Scripts/orchestrator/spec_reader.py` | 高 | 现有 Spec 读取器 |
| `AgentBridgeTests/Private/*.cpp` | 高 | 测试体系基石 |
| `Schemas/common/*.schema.json` | 高 | 稳定数据契约 |
| `Schemas/feedback/*.schema.json` | 高 | 稳定数据契约 |
| `Schemas/write_feedback/*.schema.json` | 高 | 稳定数据契约 |

如需接入，应优先通过新增旁路入口和编译期扩展完成，不直接破坏稳定核心。
