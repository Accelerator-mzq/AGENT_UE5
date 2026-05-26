# Phase 10 执行交接文档

> 交接日期：2026-04-11
> 来源：Claude Code（Phase 10 准备阶段 — 文档修订与架构对齐）
> 接收方：Codex（Phase 10 执行阶段）
> 状态：治理文档已收敛，可进入实现

---

## 1. 我做了什么

### 1.1 总体工作

Phase 10 准备阶段的核心任务是 **MCP 重定位与治理文档收敛**。

在 Phase 9 完成 MCP Server 28 工具正式化之后，经过架构评审确定了 MCP 的真正定位：

- **旧理解**：MCP = 28 个 Bridge 工具的对外暴露层（执行包装）
- **新定位**：MCP = 认知桥接层（Cognitive Bridge Layer）
  - 前端（Stage 1-2）：GDD → Root Skill → Sub-Skill Graph → Spec Family 映射的认知分解
  - 中段：Bridge Passthrough 28 工具保留为可选外部协议适配层
  - 后端：测试证据判读 → pass / fail / escalate 的认知裁决

### 1.2 修订规则（R1-R4）

所有文档修订遵循 4 条统一规则：

| 规则 | 内容 |
|------|------|
| R1 | MCP 前端边界 = Stage 1-2；Stage 3-5 = Compiler Core 调度 |
| R2 | 四层标准表述：Skill → Static Spec → Dynamic Spec → Reviewed Handoff |
| R3 | 测试 MCP = 证据读取 + 判读 + pass/fail/escalate；不控制 PIE、不模拟输入 |
| R4 | Execution Adapter = 可选薄协议适配层，不是 MCP 核心价值 |

### 1.3 具体文件变更清单

#### 新建文件（7 个）

| 文件 | 分类 | 作用 |
|------|------|------|
| `Docs/design/HLD.md#4` | 一级治理 | MCP 总口径声明，所有 MCP 文档的优先裁决依据 |
| `Docs/requirements/SRS.md#4` | 一级治理 | Skill/Spec/Handoff 四层主链定义，含流程图和边界声明 |
| `Docs/design/HLD.md#4` | 一级治理 | MCP 重定位完整方案，含架构图、Monopoly 示例、验收标准 |
| `Docs/archive/proposals/Phase10_Compiler_Capability_Bus_v3.md` | 二级提案 | 前端认知分解接口定义（Stage 1-2 的 MCP 工具） |
| `Docs/archive/proposals/Phase10_Execution_MCP_Adapter_v3.md` | 二级提案 | 执行层 MCP Adapter 边界说明 |
| `Docs/archive/proposals/Phase10_Validation_Testing_Plane_v3.md` | 二级提案 | 测试 MCP 角色定义（Evidence Judge） |
| `Docs/archive/proposals/Phase10_MCP_Testing_Toolset_v2.md` | 二级提案 | 测试工具集最小实现说明 |

#### 修改文件（8 个）

| 文件 | 改了什么 |
|------|----------|
| `CLAUDE.md` | 阅读顺序加入 14/15/16；当前阶段改为 Phase 10 准备 |
| `AGENTS.md` | 版本升 v1.2；文档路径表加入 14/15/16；阅读顺序更新 |
| `Docs/INDEX.md` | 阶段名改 Phase 10 准备；文件表加入 14/15/16；事实来源更新 |
| `Plugins/AgentBridge/README.md` | 加入 MCP 重定位注释和参考链接 |
| `Plugins/AgentBridge/AGENTS.md` | 框架组件列表加入"MCP 认知桥接层" |
| `Docs/design/HLD.md#1-2` | 版本升 v0.9.0；§1.1/§2/§5.3/§9 四处架构图全部更新 |
| `Docs/design/LLD/04_compiler.md` | 版本升 v0.9.0；MCP 描述从"执行通道"改为"认知桥接层" |
| `Docs/requirements/SRS.md#4` | 版本升 v0.9.0；加入四层标准表述和 Dynamic Spec 约束说明 |

#### 已删除

| 路径 | 原因 |
|------|------|
| `Phase 10/`（根目录临时文件夹，7 个草稿文件） | 内容已全部收入上述正式文档，用户确认后删除 |

---

## 2. 你应该读什么

### 2.1 必读（按顺序）

1. `CLAUDE.md` — 项目入口，列出阅读顺序和禁改文件清单
2. `AGENTS.md` — 项目级 Agent 规则，含文档路径表
3. `Docs/INDEX.md` — 当前阶段索引
4. **`Docs/design/HLD.md#4`** — MCP 总口径，优先裁决依据
5. **`Docs/requirements/SRS.md#4`** — 四层主链定义
6. **`Docs/design/HLD.md#4`** — 完整重定位方案，§11 列出待实现事项

### 2.2 执行参考

7. `Docs/archive/proposals/Phase10_Compiler_Capability_Bus_v3.md` — Stage 1-2 MCP 工具的接口设计
8. `Docs/archive/proposals/Phase10_Execution_MCP_Adapter_v3.md` — 执行适配层边界
9. `Docs/archive/proposals/Phase10_Validation_Testing_Plane_v3.md` — 测试裁决层角色
10. `Docs/archive/proposals/Phase10_MCP_Testing_Toolset_v2.md` — 测试工具集最小实现

### 2.3 现有实现参考

11. `Docs/design/HLD.md#1-2` — 已更新的架构全图
12. `Docs/design/LLD/04_compiler.md` — 编译器设计文档
13. `Docs/requirements/SRS.md#4` — Skill/Spec 体系说明
14. `Plugins/AgentBridge/MCP/server.py` — 现有 MCP Server 实现（28 工具）
15. `Plugins/AgentBridge/Compiler/` — 现有 Compiler skeleton（5 个 Stage 骨架）

---

## 3. 待实现事项

以下事项在治理文档中已定义清楚，但需要你在执行阶段落地。详见 `Docs/design/HLD.md#4` §11。

### 3.1 Compiler 5-Stage 独立编排入口

- 当前 `Plugins/AgentBridge/Compiler/` 有 5 个阶段骨架，各有 `get_schema()` / `create_*_template()` / `save_*()` 三件套
- **缺少**：统一的 session / pipeline 编排入口（串联 Stage 1-5 + Handoff 组装）
- **缺少**：MCP Compiler Plane 工具注册（12 个 prepare/save 对）
- **缺少**：Stage 间产物传递规范
- 接口设计参考：`Docs/archive/proposals/Phase10_Compiler_Capability_Bus_v3.md`

### 3.2 测试证据标准化 / run_id 规范

- 后端 MCP 证据裁决层需要通过 run_id 定位测试证据
- **缺少**：run_id 生成规则
- **缺少**：证据存放目录结构标准化
- **缺少**：证据索引 manifest
- 角色定义参考：`Docs/archive/proposals/Phase10_Validation_Testing_Plane_v3.md`

### 3.3 Phase 10 计划同步修订

- `val_simulate_input` 和 `val_pie_control` 两个工具**与治理口径矛盾**（R3 规则），应从 MCP Validation Plane 移出
- 改为 UE 官方测试体系的自动化脚本或 Compiler Core 执行通道

---

## 4. 绝对不能动的文件

详见 `CLAUDE.md` "绝对不要修改的文件" 一节。核心包括：

- `Plugins/AgentBridge/Source/` — C++ 核心
- `Plugins/AgentBridge/Scripts/bridge/*.py` — Bridge 客户端
- `Plugins/AgentBridge/Scripts/orchestrator/*.py` — Orchestrator 核心
- `Plugins/AgentBridge/AgentBridgeTests/` — 测试体系
- `Plugins/AgentBridge/Schemas/common/`、`feedback/`、`write_feedback/` — 已稳定 Schema

---

## 5. 可以修改的文件

Phase 10 执行阶段的主要改动范围：

| 范围 | 路径 |
|------|------|
| Compiler 框架 | `Plugins/AgentBridge/Compiler/` |
| Compiler 旧链路 | `Plugins/AgentBridge/Scripts/compiler/` |
| MCP Server 扩展 | `Plugins/AgentBridge/MCP/` |
| Skill 模板 | `Plugins/AgentBridge/SkillTemplates/` |
| Schema 扩展 | `Plugins/AgentBridge/Schemas/`（非 common/feedback/write_feedback） |
| 项目实例 | `ProjectInputs/`、`ProjectState/` |
| 文档 | `Docs/` |
| 任务入口 | 根目录 `task.md` |

---

## 6. 验证命令

```bash
# Schema 校验（确保 MVP 不被破坏）
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 系统测试（不需要 Editor 的 Stage）
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# MCP 协议级验证（28 工具仍正常）
# 见 task.md §6.2 的 PowerShell 脚本
```

---

## 7. 关键概念速查

| 概念 | 含义 | 参考文档 |
|------|------|----------|
| MCP 前端 | Stage 1-2 的 GDD 认知分解接口 | 14 号文档 §1、§5 |
| MCP 后端 | 测试证据裁决（pass/fail/escalate） | 14 号文档 §1、16 号文档 §8 |
| Bridge Passthrough | 现有 28 个 MCP 工具，可选外部协议适配层 | 14 号文档 §4 |
| Compiler Core | Stage 3-5 调度（Skill Runtime → Cross-Review → Lowering） | 15 号文档 §5、16 号文档 §5.4-5.5 |
| 四层主链 | Skill → Static Spec → Dynamic Spec → Reviewed Handoff | 15 号文档全文 |
| Dynamic Spec | 结构受 Static Spec 约束，内容由 AI Agent 填充 | 15 号文档 §2.3 |
| prepare/save 模式 | Agent 在 Stage 3-5 参与的方式：Core 发 prepare → Agent 填充 → Core 收 save | 16 号文档 §5.4-5.5 |

---

## 8. 注意事项

1. **14 号文档是最高优先级裁决依据**——如果其他文档与 14 号冲突，以 14 号为准
2. **MCP 不是全流程总线**——Stage 3-5 的 AI Agent 参与是通过 Compiler Core 内部 prepare/save 调度，不是 MCP 对外工具
3. **现有 28 个 Bridge 工具不删除**——它们作为 Passthrough 保留，但不再是 MCP 的核心价值
4. **代码风格**：Python 中文注释、YAML/JSON 中文 description、文档全中文
5. **Phase 8/9 基线必须保住**——任何改动前先跑 `validate_examples.py --strict` 和系统测试确认不回归
