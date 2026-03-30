# 本阶段实施边界

> 文档版本：L1-Phase3-v1

## P1 允许做到哪里

### 最小 Compiler 链路
- Design Input Intake（只读取 GDD，提取游戏类型）
- Project State Intake（返回模拟数据或调用现有查询接口）
- Mode Router（三级优先级判定：显式选择 > Preset > Auto 兜底）
- Handoff Builder（手工构造最小 Spec Tree）
- Handoff Serializer（YAML/JSON 序列化）

### 最小 Orchestrator 桥接
- Handoff Runner（读取 Handoff，调用 Run Plan Builder）
- Run Plan Builder（从 Handoff 生成 workflow_sequence）
- 桥接到现有 Bridge 接口（三种 bridge_mode：simulated / bridge_python / bridge_rc_api）
- 执行报告生成

### Schema 和配置
- Reviewed Handoff Schema（含 Brownfield 占位字段）
- Run Plan Schema
- 项目层配置文件（GDD / mode_override / compiler_profile）

### Genre Pack 最小骨架
- boardgame pack_manifest.yaml（对齐 Genre_Skill_Pack_Manifest_标准_v1）

## P2 只允许做到哪里

- Brownfield 能力占位：analysis/ 目录 README
- Spec 生成占位：generation/ 目录 README
- Cross-Spec Review 占位：review/ 目录 README
- Skills 体系占位：base_domains / genre_packs 目录 README
- Static Spec Base 占位：Specs/StaticBase/ 目录 README
- Patch / Migration Contract 占位：Specs/Contracts/ 目录 README

## 不允许做的

- 完整 Brownfield 实装
- 完整 Delta Scope Analysis / Baseline Understanding
- 完整 Regression Validation
- 复杂 Patch / Migration Contract 应用逻辑
- 多个 Genre Packs
- 完整 Cross-Spec Review
- Skill 动态加载 / 热更新
- 重写现有 C++ Subsystem
- 重构已有 Bridge 三通道主链
- 修改现有 Automation Test
- 修改现有 Schema 体系（只新增，不修改）

## 现有文件保护清单

以下文件/模块不允许大改：

| 文件 | 保护级别 | 理由 |
|------|---------|------|
| Source/AgentBridge/Public/AgentBridgeSubsystem.h | 高 | 核心 Subsystem，15 个接口已稳定 |
| Source/AgentBridge/Private/AgentBridgeSubsystem.cpp | 高 | 核心实现，已通过测试 |
| Source/AgentBridge/Public/BridgeTypes.h | 高 | 统一响应格式 |
| Scripts/bridge/*.py | 中 | 三通道客户端已稳定 |
| Scripts/orchestrator/orchestrator.py | 中 | 现有执行链，保留 run(spec_path) 入口 |
| Scripts/orchestrator/plan_generator.py | 中 | 现有计划生成器 |
| AgentBridgeTests/Private/*.cpp | 高 | 测试体系是验证基石 |
| Schemas/common/*.schema.json | 高 | 数据契约已稳定 |
| Schemas/feedback/*.schema.json | 高 | 数据契约已稳定 |

如需接入，应新增旁路入口，不修改现有代码。
