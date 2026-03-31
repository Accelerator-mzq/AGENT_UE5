# Greenfield E2E 管线

> 文档版本：v0.4.0 | 适用范围：AgentBridge 框架 Greenfield 端到端管线

---

## 1. 概述

Greenfield 管线是从零构建新游戏样板的完整端到端流程。Phase 3 已验证 simulated 模式的完整链路跑通。

---

## 2. 完整管线

```
ProjectInputs/GDD/boardgame_tictactoe_v1.md     ← 设计输入
    ↓
Scripts/compiler/intake/design_input_intake.py   ← 解析 GDD
    ↓
Scripts/compiler/intake/project_state_intake.py  ← 采集项目状态
    ↓
Scripts/compiler/routing/mode_router.py          ← 模式路由（→ greenfield）
    ↓
Scripts/compiler/handoff/handoff_builder.py      ← 构建 Handoff
    ↓
Scripts/compiler/handoff/handoff_serializer.py   ← 序列化为 YAML
    ↓
ProjectState/Handoffs/draft/handoff_xxx.yaml     ← 草稿 Handoff
    ↓
人工审批（手工移动文件）
    ↓
ProjectState/Handoffs/approved/handoff_xxx.yaml  ← 已审批 Handoff
    ↓
Scripts/orchestrator/run_plan_builder.py         ← 生成 Run Plan
    ↓
Scripts/orchestrator/handoff_runner.py           ← 执行 Run Plan
    ↓
Scripts/bridge/*                                 ← Bridge 工具调用
    ↓
UE5 Editor（Actor 生成 / Transform 设置）
    ↓
ProjectState/Reports/                            ← 执行报告
```

---

## 3. 每个环节的输入 / 输出

| 环节 | 输入 | 输出 |
|------|------|------|
| Design Input Intake | GDD markdown 文件 | design_input 字典（game_type / board / pieces / rules） |
| Project State Intake | 项目路径 | project_state 字典（has_existing_content / actor_count） |
| Mode Router | design_input + project_state + Presets | routing_result（resolved_mode: greenfield） |
| Handoff Builder | design_input + routing_result + project_state | Handoff 字典（符合 Schema） |
| Handoff Serializer | Handoff 字典 | YAML 文件（ProjectState/Handoffs/draft/） |
| Run Plan Builder | approved Handoff YAML | Run Plan 字典（workflow_sequence + checkpoints） |
| Handoff Runner | Run Plan | 执行结果（per-step status + report） |

---

## 4. 执行模式

Handoff Runner 支持三种执行模式：

| 模式 | 说明 | 用途 |
|------|------|------|
| `simulated` | 不调用真实 Bridge，打印模拟输出 | 开发验证、CI 测试 |
| `bridge_python` | 通过通道 A（Python import unreal）调用 Bridge | 进程内执行 |
| `bridge_rc_api` | 通过通道 B（HTTP REST :30010）调用 Bridge | Agent 远程执行 |

当前默认模式：`simulated`

---

## 5. 运行方式

### 5.1 完整端到端运行

```bash
# 从项目根目录运行
python run_greenfield_demo.py
```

该脚本依次执行：
1. Compiler（design_input_intake → mode_router → handoff_builder → serializer）
2. 自动审批（将 draft 移到 approved）
3. Run Plan Builder（生成执行计划）
4. Handoff Runner（执行计划）
5. Report 输出

### 5.2 分步运行

```bash
# 步骤 1：仅运行 Compiler
cd Plugins/AgentBridge/Scripts
python compiler_main.py

# 步骤 2：手工将 draft Handoff 移到 approved
# mv ProjectState/Handoffs/draft/xxx.yaml ProjectState/Handoffs/approved/

# 步骤 3：运行 Handoff Runner（需要 approved Handoff）
# 由 run_greenfield_demo.py 内部调用
```

---

## 6. 当前限制

| 限制 | 说明 | 计划解决 |
|------|------|---------|
| 仅支持 simulated 模式 | UE5 真实调用未联调 | Phase 3 遗留 / Phase 4 前置 |
| project_state_intake 返回模拟数据 | 未桥接真实 Bridge 查询 | Phase 5 |
| 仅支持 boardgame 类型 GDD | 其他类型无解析器 | Phase 6 |
| Handoff 审批为手工操作 | 无自动化治理流程 | Phase 7 |
| 无 Spec 自动生成 | dynamic_spec_tree 直接从 design_input 转换 | Phase 4 |
| 无 Cross-Spec Review | 引用完整性未检查 | Phase 4 |

---

## 7. 与 Brownfield 管线的区别

| 维度 | Greenfield | Brownfield（Phase 5） |
|------|-----------|----------------------|
| 基线 | 无（空项目） | 有（需要 Baseline Understanding） |
| Spec 类型 | Full Dynamic Spec Tree | Delta Dynamic Spec Tree |
| 操作类型 | 全部 create | create / patch / expand |
| 风险 | 低（无已有内容） | 中-高（需保护已有内容） |
| Regression | 不需要 | 必须（确认不破坏已有内容） |
