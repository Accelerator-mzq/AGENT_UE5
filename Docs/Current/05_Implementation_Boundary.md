# 本阶段实施边界

> 文档版本：L1-Phase6-v2

## P1 允许做到哪里

### Genre Pack Core

- 允许在 `Skills/genre_packs/_core/` 下落地 `manifest_loader`、`router_base`、`registry`、`module_loader`
- 允许在不破坏 `mode_router.py` 的前提下，为 pack 机制接入并行选择逻辑

### Boardgame 类型包

- 允许在 `Skills/genre_packs/boardgame/` 下新增 required skills / review / validation / delta policy
- 允许更新 `pack_manifest.yaml`，把最小声明扩展为 Phase 6 可消费结构
- 允许在 `Specs/Contracts/Genres/Boardgame/` 下新增首批 genre contract

### Compiler / Runtime / Evidence

- 允许扩展 `Scripts/compiler/generation/`、`review/`、`handoff/` 的 pack 接入逻辑
- 允许在项目层 `Source/Mvpv4TestCodex/` 下新增最小 runtime actor
- 允许在 `ProjectState/RuntimeConfigs/` 写入 runtime config
- 允许在真实 UE5 验证时把截图与说明写入 `ProjectState/Evidence/Phase6/`

## P2 只允许做到哪里

- `run_plan_builder.py` / `handoff_runner.py` 仍以最小兼容为主，不做大重构
- `patch / migration` 继续保证“可表达 + 可校验 + 可阻断”
- `SystemTestCases.md` 本阶段不增加 Phase 6 用例正文，待阶段归档时再统一补录
- Base Skill Domains 仅允许依赖映射，不做完整实现

## 不允许做的

- 重写现有 C++ Subsystem
- 重构现有 Bridge 三通道主链
- 修改现有 Automation Test C++ 测试
- 修改现有稳定 Schema（`Schemas/common/` / `Schemas/feedback/` / `Schemas/write_feedback/`）
- 同时做多个 Genre Pack
