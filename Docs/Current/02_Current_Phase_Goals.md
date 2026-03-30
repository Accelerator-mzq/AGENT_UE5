# Phase 3 目标

> 文档版本：L1-Phase3-v1

## 本期目标

本期目标不是做完整的最终框架，而是打通最小可验证闭环：

1. 在 AgentBridge 插件层建立 Skill Compiler Plane 最小框架
2. 打通 GDD → Compiler → Reviewed Handoff → Orchestrator → Bridge 执行 → Report 链路
3. 使用 Greenfield + Boardgame 作为首个验证场景
4. 在不破坏现有 MVP 的前提下接入

## 核心链路

```
ProjectInputs/GDD/ → compiler/intake/ → compiler/routing/ → compiler/handoff/
→ ProjectState/Handoffs/draft/ → 审批 → approved/
→ orchestrator/handoff_runner.py → run_plan_builder.py
→ 桥接到现有 Bridge 接口（SpawnActor 等）
→ UE5 中生成 Actor → ProjectState/Reports/
```

## 分层原则

- 项目层（本工程根目录）：只承接输入源、配置、实例、治理
- 插件层（Plugins/AgentBridge/）：承接 Compiler / Handoff / Orchestrator / Validation 通用框架

## 本期不做

- 完整 Brownfield 实装
- 完整 Delta Scope Analysis / Baseline Understanding
- 完整 Regression Validation
- 多个 Genre Packs（只做 boardgame 最小骨架）
- 重写现有 C++ Subsystem
- 重构已有 Bridge 三通道主链
- 修改现有 Automation Test / Schema 体系

## 成功标准

1. `python run_greenfield_demo.py` 端到端跑通（simulated 模式）
2. `python run_greenfield_demo.py bridge_rc_api` 在 UE5 中生成 Actor
3. Reviewed Handoff 实例通过 Schema 校验
4. 执行报告输出到 ProjectState/Reports/
5. 现有 Automation Test 仍然全部通过
6. 现有 validate_examples.py 仍然全部通过
