# Claude Code → Codex 交接文档

> 日期：2026-04-16
> 交接人：Claude Code（Opus 4.6）
> 接收人：Codex
> 分支：`docs/phase11-final-doc-pack`

---

## 1. 背景：为什么介入

Codex 执行到 TASK 09 并标记完成后，用户发现 **Stage 4（Domain Skill Runtime）的 Discovery、Candidates、Convergence 三阶段没有真正的发散创造能力**。

**根本原因**：`pipeline_orchestrator.py` 中 `llm_client=None` 硬编码，Stage 4 永远走 heuristic fallback 路径——`discovery_fallback.py` / `realization_fallback.py` / `convergence_fallback.py` 只是确定性算法，不是真正的设计探索。

**解决方案**：不在 pipeline 内部接入 LLM API，而是利用 MCP——调用 MCP 工具的 Agent（Claude）本身就是 LLM。新增两个 MCP 工具 `compiler_stage4_node_prepare` / `compiler_stage4_node_save`，让 Agent 逐节点、逐阶段执行真正的创造性生成。

---

## 2. 修改文件清单

### 2.1 代码修改（6 个文件）

| 文件 | 修改内容 |
|------|---------|
| `Plugins/AgentBridge/Compiler/pipeline/session.py` | 新增 `generator_provider` 字段（枚举 `"llm"` / `"heuristic_fallback"`）、`VALID_GENERATOR_PROVIDERS` 常量、`is_promotable` 计算属性（fast_mode=true 或 generator_provider="heuristic_fallback" 时为 false）、`to_dict()` 序列化、`__post_init__` 校验 |
| `Plugins/AgentBridge/Compiler/pipeline/pipeline_orchestrator.py` | Stage 4 执行后自动从 template 读取 `generator_provider_type` 并写入 session |
| `Plugins/AgentBridge/Compiler/stages/domain_skill_runtime.py` | 新增 `prepare_node_phase()` 和 `save_node_phase()` 两个 MCP 交互入口函数；新增 `_cv()` 防御性辅助函数替代 `_build_gameplay_spec_fragment` 中的硬编码 dict 访问，防止 KeyError |
| `Plugins/AgentBridge/MCP/compiler_tools.py` | 新增 `compiler_stage4_node_prepare` 和 `compiler_stage4_node_save` 两个 MCP 工具处理函数，加载 Stage 1-3 产物后调用 domain_skill_runtime 的 prepare/save |
| `Plugins/AgentBridge/MCP/tool_definitions.py` | 新增 2 个工具定义（参数规格 + 描述） |
| `Plugins/AgentBridge/MCP/server.py` | TOOL_DISPATCH 新增 2 条路由 |

### 2.2 Schema 修改（1 个文件）

| 文件 | 修改内容 |
|------|---------|
| `Plugins/AgentBridge/Schemas/compiler_session.schema.json` | 新增 `generator_provider` 枚举字段 |

### 2.3 新增 Baseline SkillTemplate 文件（36 个文件）

路径：`Plugins/AgentBridge/SkillTemplates/baseline/`

6 个 baseline 域，每个域 6 个文件：

| 域 | template_id | realization_class |
|----|-------------|-------------------|
| `start_screen/` | `baseline.start_screen.presence_only` | presence_only |
| `main_menu/` | `baseline.main_menu.presence_only` | presence_only |
| `settings/` | `baseline.settings.presence_only` | presence_only |
| `pause/` | `baseline.pause.presence_only` | presence_only |
| `results/` | `baseline.results.presence_only` | presence_only |
| `hud/` | `baseline.hud.realization_eligible` | realization_eligible |

每个域包含：`manifest.yaml`、`system_prompt.md`、`domain_prompt.md`、`evaluator_prompt.md`、`input_selector.yaml`、`output_schema.json`

### 2.4 设计文档更新（4 个文件）

| 文件 | 修改内容 |
|------|---------|
| `Docs/Phase11/01_Phase11_Unified_Architecture.md` | §4.4 工具总数 42→50 |
| `Docs/Phase11/11_Schema_and_Artifact_Reference.md` | §3.1 工具总数 42→50；§3.2 新增工具从 2 个扩展到 4 个（加入 stage4_node prepare/save） |
| `Docs/Phase11/12_Implementation_Taskbook.md` | 任务 2.4 加入 `agent_protocol.py` + MCP 交互模式；2.5-2.7 文件名改为 `*_fallback.py` 描述改为 Heuristic Fallback；新增 D.8 MCP Stage 4 工具 |
| `Docs/Phase11/14_Agent_Interaction_Protocol.md` | §4.0 Provider 表扩展为三路（MCP Agent / LLM Internal / Heuristic Fallback）；新增 §4.4 MCP Agent 交互流程；§9 fast_mode 表扩展为三列对比 |

### 2.5 task.md 更新

多处更新以匹配实现变化：
- TASK 02 新增 `generator_provider` 步骤和验收标准
- TASK 05 工具总数 47→50
- TASK 09 涉及文件列表（+3 MCP 文件）、Steps（+MCP 交互工具）、验收标准（+MCP Agent 模式、三路 Generator）
- 覆盖矩阵 Doc 14 行新增 TASK 09
- 里程碑 M6 状态已标记 ✅

---

## 3. 架构变化：三种 Generator 路径

```
路径 1: MCP Agent（当前主路径，推荐用于正式 run）
  Agent 调用 compiler_stage4_node_prepare → 拿到 prompt + context
  Agent 做创造性生成
  Agent 调用 compiler_stage4_node_save → 校验存储
  标记: generator_type="mcp_agent", promotable=true

路径 2: LLM Internal（已实现 Provider，需接入 llm_client）
  pipeline 内嵌 LLM API 调用（LLMProvider 代码已完整，见 agent_protocol.py:399-520）
  缺少：具体的 llm_client 实例（需实现 call(messages) -> str 接口）
  标记: generator_type="llm", promotable=true

路径 3: Heuristic Fallback（CI / fast_mode / 测试）
  *_fallback.py 确定性算法
  标记: generator_type="heuristic_fallback", promotable=false
```

`is_promotable` = `not fast_mode and generator_provider != "heuristic_fallback"`

---

## 4. Codex 需要知道的关键决策

### 4.1 文件重命名

原 TASK 09 预期的文件名已改变：

| 文档中的旧名 | 实际文件名 | 原因 |
|-------------|-----------|------|
| `discovery_engine.py` | `discovery_fallback.py` | 降级为 heuristic fallback |
| `realization_generator.py` | `realization_fallback.py` | 降级为 heuristic fallback |
| `convergence_engine.py` | `convergence_fallback.py` | 降级为 heuristic fallback |

### 4.2 `_cv()` 防御性修复

`domain_skill_runtime.py` 中 `_build_gameplay_spec_fragment()` 的所有 constraint field 访问已从：
```python
root_skill_contract["constraint_fields"]["board.layout_shape"]["value"]
```
改为：
```python
_cv("board.layout_shape")  # 返回 None 如果字段不存在
```
这防止了 constraint_fields 不完整时的 KeyError。

### 4.3 MCP 工具总数确认

Phase 10: 42 → Phase 11: 50（净增 8）

新增 8 个：
- `compiler_root_skill_prepare` / `save`（重命名，旧名 intake 作 alias 不计）
- `compiler_clarification_prepare` / `save`
- `compiler_skill_graph_prepare` / `save`（重命名，旧名 plan 作 alias 不计）
- `compiler_stage4_node_prepare` / `save`

实际净增工具 = clarification 2 + stage4_node 2 + evidence 3 + session 扩展 1 = 8（重命名 4 个不计新增）

---

## 5. 需要重新执行或审查的任务

### 5.1 TASK 09A（新增）：LLM Internal 路径接入

原 TASK 09 拆分为 09A + 09B。09A 是新增的前置任务——LLMProvider 代码已完整（`agent_protocol.py:399-520`），但缺少具体的 `llm_client` 实例。09A 实现多 provider 兼容的 LLM 客户端使其可用。

**执行时机**：TASK 08 之后、TASK 09B 之前。是 TASK 09B 三路 Generator 验证的前置依赖。

**具体操作和验收标准**：见 `task.md` TASK 09A 完整定义。

### 5.2 TASK 09B（原 TASK 09，需重新验收）

原证据 `task09_phase11_domain_skill_runtime.md` 在没有 LLM Internal、没有 MCP 交互工具时生成，不完整。

- **代码不需重做**——agent_protocol / fallback / domain_skill_runtime / MCP 工具已完成
- **当前正式口径已调整**——MCP Agent 与 Heuristic Fallback 保持正式验收；`LLM Internal` 暂不继续测试
- **暂停原因**——当前 `llm_client` / LLM Internal 链路不足以稳定承载高负载 `Candidates` prompt，相关诊断见 [stage4_candidates_prompt_vs_provider_diagnostic.md](/D:/UnrealProjects/Mvpv4TestCodex/ProjectState/Reports/2026-04-16/stage4_candidates_prompt_vs_provider_diagnostic.md)
- **恢复条件**——待后续 `llm_client` 框架升级完成后，再重开 `LLM Internal` 严格回归验收
- **当前证据要求**——更新 TASK 09B 证据报告，覆盖 MCP Agent、Heuristic Fallback 两条已完成路径，并附 `LLM Internal` 暂停依据

### 5.3 TASK 10：正常继续（当前待执行）

TASK 10 不受影响，可正常开始。注意：

- 读取 `domain_skill_runtime.py` 时注意 `prepare_node_phase` / `save_node_phase` 是新增的
- `cross_review_v2.py` / `lowering_v2.py` / `handoff_v3.py` 文件已由 Codex 之前创建（骨架），需要补充实现
- 需新增 5 个 Schema + example

### 5.4 TASK 11：正常继续

端到端 run 时注意：
- `metadata.json` 需包含 `generator_provider` 字段
- 如果使用 MCP Agent 路径，`generator_type` 应为 `"mcp_agent"`
- `is_promotable` 现在同时检查 `fast_mode` 和 `generator_provider`

### 5.5 TASK 14：已部分完成

6 个 Baseline SkillTemplate 目录（36 个文件）**已由 Claude Code 创建完毕**。Codex 需要：

- 验证已有模板内容是否满足 TASK 14 验收标准
- 确认 Skill Graph Planning 能引用 baseline template_id
- 生成 TASK 14 证据报告
- **不需要重新创建文件**

---

## 6. 建议执行顺序

```
1. TASK 09A：LLM Internal 路径接入（llm_client.py + llm_config + pipeline_orchestrator 接入）
2. TASK 09B：Domain Skill Runtime 当前验收口径收口（MCP Agent + Heuristic Fallback + LLM Internal 暂停依据）
3. TASK 10：Cross Review v2 + Build IR v2 + Handoff v3
4. TASK 11：端到端 run
5. TASK 12：Run Compare / Promote
6. TASK 13：fast_mode 完整策略
7. TASK 14：验收已有 Baseline Template（代码已就位，需验收 + 证据）
8. TASK 15：最终验收
```

> 备注：`LLM Internal` 严格验收不再阻塞当前主线，待后续 `llm_client` 框架升级后单独重开。

---

## 7. 验证命令

```bash
# Schema 校验
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 系统测试
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# 检查 MCP 工具数量（应为 50）
python -c "from Plugins.AgentBridge.MCP.server import TOOL_DISPATCH; print(len(TOOL_DISPATCH))"
```

---

## 8. 未提交的文件

当前分支 `docs/phase11-final-doc-pack` 有大量未提交修改。建议 Codex 在继续前先 `git status` 确认工作区状态，必要时先 commit 当前改动。
