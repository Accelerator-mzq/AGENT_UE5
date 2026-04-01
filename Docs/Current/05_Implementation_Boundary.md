# 本阶段实施边界

> 文档版本：L1-Phase6-v1

## P1 允许做到哪里

### Genre Pack Core

- 允许在 `Skills/genre_packs/_core/` 下落地 `manifest_loader`、`router_base`、`registry`、辅助模块
- 允许在不破坏当前 `mode_router.py` 的前提下，为 Genre Pack 接入新增旁路加载逻辑

### Boardgame 类型包

- 允许在 `Skills/genre_packs/boardgame/` 下新增 `required_skills/`、`review_extensions/`、`validation_extensions/`、`delta_policy/`
- 允许更新 `pack_manifest.yaml`，把当前最小声明扩展为 Phase 6 可用结构
- 允许在 `Specs/Contracts/Genres/Boardgame/` 下新增首批 genre contract

### Compiler / Evidence

- 允许扩展 `Scripts/compiler/generation/`、`review/`、`handoff/` 的 pack 接入逻辑
- 允许在真实 UE5 验证时把截图与说明写入 `ProjectState/Evidence/Phase6/`
- `ProjectState/Snapshots/` 继续作为 baseline/state snapshot 输出目录

## P2 只允许做到哪里

- `run_plan_builder.py` / `handoff_runner.py` 仍以最小兼容为主，不做大重构
- `patch / migration` 继续保证“可表达 + 可校验 + 可阻断”，不要求全自动执行
- `SystemTestCases.md` 本阶段不增加 Phase 6 用例正文，待阶段归档时再统一补录
- Base Skill Domains 仅允许依赖映射，不做完整实现

## 不允许做的

- 重写现有 C++ Subsystem
- 重构现有 Bridge 三通道主链
- 修改现有 Automation Test C++ 测试
- 修改现有稳定 Schema（`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`）
- 完整 Base Skill Domains / 自动审批治理
- 同时做多个 Genre Pack

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
