# Phase 10 开发方案：MCP 重新定位为框架级 Agent 接口

> 文档类型：实施前方案
> 状态：待实施
> 起草日期：2026-04-10
> 依据：[12_MCP_Repositioning.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/Current/12_MCP_Repositioning.md)

---

## 1. 背景与目标

Phase 9 完成了 MCP Server 的 28 个工具实现（stdio 协议，Claude Code 已确认可用）。但这 28 个工具本质上是 Bridge 三通道的协议再包装——没有 MCP，Orchestrator 通过 `query_tools` / `write_tools` 已经能完整操作 UE5 Editor。

依据 `12_MCP_Repositioning.md` 的架构决策，Phase 10 将 MCP 从"执行层 Bridge 包装"重新定位为两个框架级 Agent 接口：

- **上游 Compiler Plane 接口**：让 AI Agent 通过 MCP 驱动 Skill-First Compiler 5 阶段主链
- **下游 Runtime Validation 接口**：让 AI Agent 代替人工完成运行时冒烟测试（val-13~val-19）

已有的 28 个 Bridge Passthrough 工具保留不删除（保 Phase 9 基线），但不再是 MCP 的核心价值。

---

## 2. 里程碑与任务总览

| 里程碑 | 任务范围 | 新增工具 | 验证门禁 |
|--------|---------|---------|---------|
| **M1** 架构重构 | TASK 01-03 | 0（重构不加工具） | 28 tools + 240 tests 不退化 |
| **M2** Compiler Plane | TASK 04-08 | 12 | 40 tools + pipeline 走通 MonopolyGame GDD |
| **M3** Runtime Validation | TASK 09-12 | 7 | 47 tools + val-15 Agent 驱动演练 |

---

## 3. 核心约束

### 不可修改

- `Plugins/AgentBridge/Source/` — C++ 核心
- `Plugins/AgentBridge/Scripts/bridge/*.py` — Bridge 客户端
- `Plugins/AgentBridge/Scripts/orchestrator/*.py` — Orchestrator 核心
- `Plugins/AgentBridge/AgentBridgeTests/` — 测试文件
- `Plugins/AgentBridge/Schemas/common/`、`feedback/`、`write_feedback/` — 稳定 Schema
- `Plugins/AgentBridge/Compiler/` 下的 5 个 skeleton 文件 — 只调用其函数，不修改其代码

### 可修改

- `Plugins/AgentBridge/MCP/` — 所有文件
- `Plugins/AgentBridge/Schemas/` — 非稳定 Schema（reviewed_handoff_v2 等）
- `Docs/`、`ProjectState/`、`ProjectInputs/` — 项目层
- `task.md`、`CLAUDE.md`、`AGENTS.md` — 根目录治理文件

### 编译产出目录

Phase 10 编译产出统一写到 `ProjectState/phase10/`，按 `phase8` 模式隔离。

### 集成验证 GDD

直接使用现有 `ProjectInputs/GDD/` 下的 MonopolyGame GDD 走通 pipeline。

---

## 4. M1：MCP Server 架构重构

### TASK 01：tool_definitions.py 命名空间化

**改动文件**：`Plugins/AgentBridge/MCP/tool_definitions.py`

在现有 5 个 dict 之外，新增两个空 dict 占位：

```python
COMPILER_PLANE_TOOLS = {}       # M2 填充
VALIDATION_PLANE_TOOLS = {}     # M3 填充

BRIDGE_PASSTHROUGH_TOOLS = {**LAYER1_QUERY_TOOLS, **LAYER1_WRITE_TOOLS,
                             **LAYER1_SERVICE_TOOLS, **LAYER2_ASSET_TOOLS, **LAYER3_TOOLS}

ALL_TOOLS = {**BRIDGE_PASSTHROUGH_TOOLS, **COMPILER_PLANE_TOOLS, **VALIDATION_PLANE_TOOLS}
```

**验证**：`python -m py_compile` 通过；`len(ALL_TOOLS) == 28`。

### TASK 02：server.py 模块化分发

**新建文件**：
- `Plugins/AgentBridge/MCP/compiler_dispatch.py` — Compiler Plane 工具分发（M1 为空壳）
- `Plugins/AgentBridge/MCP/validation_dispatch.py` — Validation Plane 工具分发（M1 为空壳）

**改动文件**：`Plugins/AgentBridge/MCP/server.py`

将 `TOOL_DISPATCH` 拆分为三个来源合并：

```python
from compiler_dispatch import COMPILER_DISPATCH    # M1 为空 dict
from validation_dispatch import VALIDATION_DISPATCH  # M1 为空 dict

BRIDGE_DISPATCH = { ... }  # 现有 28 个路由，不变
TOOL_DISPATCH = {**BRIDGE_DISPATCH, **COMPILER_DISPATCH, **VALIDATION_DISPATCH}
```

`create_mcp_server()` / `handle_list_tools()` / `handle_call_tool()` 逻辑不变。

### TASK 03：Phase 9 基线回归门禁

验证命令：

```bash
python -m py_compile Plugins/AgentBridge/MCP/tool_definitions.py Plugins/AgentBridge/MCP/server.py
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor
```

**产出**：`ProjectState/Reports/<date>/phase10_m1_regression.md`

---

## 5. M2：Compiler Plane Agent 接口

### 核心设计：prepare / save 工具对

每个编译阶段暴露两个工具：

- `*_prepare`（只读）：加载输入 + 返回模板 + Schema + 上下文 → Agent 用自身推理能力填充
- `*_save`（写入）：接收 Agent 填充的结果 → Schema 校验 → 保存到 `ProjectState/phase10/`

这是"Agent IS the AI logic, tools are the I/O interface"的设计——与 Compiler skeleton 中"实际字段值由 AI Agent 填充"的注释一致。

### 可复用函数（Compiler skeleton 已实现，MCP dispatch 只需调用）

| 阶段 | 文件 | 可复用函数 |
|------|------|-----------|
| Stage 1 | `Compiler/intake/design_intake.py` | `get_schema()`, `create_projection_template()`, `save_projection()` |
| Stage 2 | `Compiler/planner/planner.py` | `get_schema()`, `scan_skill_templates()`, `create_planner_output_template()`, `save_planner_output()` |
| Stage 3 | `Compiler/skill_runtime/skill_runtime.py` | `get_schema()`, `load_template_pack()`, `create_fragment_template()`, `save_fragment()` |
| Stage 4 | `Compiler/cross_review/cross_review.py` | `get_schema()`, `load_all_fragments()`, `create_review_report_template()`, `save_review_report()` |
| Stage 5 | `Compiler/lowering/lowering.py` | `get_schema()`, `create_build_ir_template()`, `save_build_ir()` |

### TASK 04：Stage 1 — Design Intake 工具对

**新增 MCP 工具**：

- `compiler_intake_prepare(gdd_path, target_phase)` → 返回 GDD 全文 + projection 模板 + schema
- `compiler_intake_save(projection, output_path?)` → jsonschema 校验 → 调用 `save_projection()`

**调用链**：

```
compiler_intake_prepare
  → design_intake.create_projection_template(gdd_path, target_phase)
  → 读 GDD 文件内容
  → design_intake.get_schema()
  → 返回 {template, gdd_content, schema}

compiler_intake_save
  → jsonschema.validate(projection, schema)
  → design_intake.save_projection(projection, output_path)
  → 返回 {status, saved_path}
```

**实现文件**：`Plugins/AgentBridge/MCP/compiler_dispatch.py`
**注册到**：`tool_definitions.py` 的 `COMPILER_PLANE_TOOLS`

### TASK 05：Stage 2 — Planner 工具对

**新增 MCP 工具**：

- `compiler_plan_prepare(projection_path, mode?)` → 返回 projection + 扫描到的 Skill Templates + planner 模板 + schema
- `compiler_plan_save(planner_output, output_path?)` → 校验 → 保存

**调用链**：

```
compiler_plan_prepare
  → 读 projection_path 获取 gdd_projection
  → planner.scan_skill_templates(SKILL_TEMPLATES_DIR)  # 扫描 6 个 Monopoly 模板
  → planner.create_planner_output_template(projection_id, mode, target_phase)
  → planner.get_schema()
  → 返回 {template, projection, available_templates[], schema}
```

### TASK 06：Stage 3 — Skill Runtime 工具对

**新增 MCP 工具**：

- `compiler_skill_run(skill_instance_id, template_dir, projection_path)` → 加载 Template Pack + GDD 切片 → 返回给 Agent
- `compiler_skill_save(fragment, output_dir?)` → 校验 → 保存

**调用链**：

```
compiler_skill_run
  → skill_runtime.load_template_pack(template_dir)  # manifest + prompts + schema
  → 读 projection 并按 input_selector.yaml 切片
  → skill_runtime.create_fragment_template(...)
  → 返回 {template, template_pack, projection_slice, schema}
```

此工具需要按 planner 输出的依赖顺序被调用 N 次（每个 Skill Instance 一次）。

### TASK 07：Stage 4+5 — Cross-Review + Lowering + Handoff 组装

**新增 MCP 工具**（5 个）：

- `compiler_review_prepare(fragments_dir, planner_output_path?)` → 加载所有 fragments → 返回 review 模板
- `compiler_review_save(review_report, output_path?)` → 校验 → 保存
- `compiler_lower_prepare(review_report_path)` → 加载 reviewed spec tree → 返回 lowering 模板
- `compiler_lower_save(build_ir, output_path?)` → 校验 → 保存
- `compiler_assemble_handoff(build_ir_path, review_report_path, projection_path, planner_path)` → 组装 Reviewed Handoff v2 → 校验 `reviewed_handoff_v2.schema.json` → 保存

### TASK 08：compiler_status 查询 + M2 集成验证

**新增 MCP 工具**：

- `compiler_status(session_dir?)` → 扫描 `ProjectState/phase10/` 中各阶段产出是否存在，返回 pipeline 状态

**M2 集成验证**：

1. `tools/list` 返回 40 工具（28 + 12 compiler）
2. 每个 `*_save` 工具拒绝不合法输入并返回 `validation_error`
3. 用现有 MonopolyGame GDD 走通 5 阶段全流程
4. `compiler_status` 正确反映各阶段状态
5. Phase 9 基线回归：240 条测试仍通过

**产出**：`ProjectState/Reports/<date>/phase10_m2_compiler_plane_validation.md`

---

## 6. M3：Runtime Validation Agent 接口

### TASK 09：感知工具（3 个）

**`val_screenshot`**（增强版截图）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| output_path | string | 否 | 截图保存路径 |
| viewport | string | 否 | `"editor"` 或 `"pie"`（默认 `"pie"`） |
| return_base64 | bool | 否 | 若 true，以 `ImageContent` 返回截图（MCP SDK 已确认支持 `types.ImageContent`） |

关键差异：`return_base64=true` 时 Agent 可直接"看到"截图做视觉判定。

**`val_read_widget_tree`**（读取控件树）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| root_widget | string | 否 | 起始 Widget 路径 |
| depth | int | 否 | 最大递归深度（默认 3） |

实现：`run_editor_python` 执行 Python 脚本遍历 widget hierarchy，返回控件名/类型/可见性/文本内容。

**`val_read_game_state`**（读取运行时状态）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| state_class | string | 否 | GameState 类路径 |
| properties | array | 否 | 需读取的属性列表 |

### TASK 10：交互工具（2 个）

**`val_simulate_input`**（模拟输入）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| action | string | 是 | `"click"` / `"hover"` / `"keypress"` / `"type"` |
| target | object | 否 | `{widget_path}` 或 `{screen_x, screen_y}` |
| key | string | 条件 | keypress/type 时使用 |
| text | string | 条件 | type 时使用 |

实现：通过 `run_editor_python` 调用 UE5 Automation Driver API，不修改稳定的 `ui_tools.py`。

**`val_pie_control`**（PIE 生命周期控制）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| action | string | 是 | `"start"` / `"stop"` / `"is_running"` |

### TASK 11：判定与证据工具（2 个）

**`val_save_judgment`**（保存 Agent 判定）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| check_id | string | 是 | 验证点 ID（如 `"val-15"`） |
| verdict | string | 是 | `"pass"` 或 `"fail"` |
| reasoning | string | 是 | Agent 的判定理由 |
| evidence_refs | array | 是 | 证据文件路径列表 |

保存到 `ProjectState/Reports/<date>/val_judgments/`。

**`val_generate_report`**（汇总验证报告）：

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| report_id | string | 是 | 报告标识 |
| check_ids | array | 是 | 需汇总的 check_id 列表 |

参考 `Scripts/orchestrator/report_generator.py` 的结构化报告模式（只读引用，不修改）。

### TASK 12：M3 集成验证 — Agent 驱动 val-15 演练

**验证流程**（需要运行中的 UE5 Editor）：

1. `val_pie_control(action="start")` → 启动 PIE
2. 等待 2 秒渲染稳定
3. `val_screenshot(viewport="pie", return_base64=true)` → Agent 看到截图
4. Agent 判定：场景是否非黑屏
5. `val_save_judgment(check_id="val-15", verdict="pass/fail", reasoning="...", evidence_refs=[...])` → 记录
6. `val_pie_control(action="stop")` → 停止 PIE
7. `val_generate_report(...)` → 生成报告

**验证门禁**：

1. `tools/list` 返回 47 工具（28 + 12 + 7）
2. val-15 可 Agent 驱动完成并产出证据
3. Phase 9 基线回归：240 条仍通过

**产出**：`ProjectState/Reports/<date>/phase10_m3_runtime_validation_report.md`

---

## 7. 工具总表（Phase 10 完成后：47 个）

### Bridge Passthrough（28 个，保留不变）

L1 Query(7) + L1 Write(6) + L1 Service(5) + L2 Asset(9) + L3 Fallback(1)

### Compiler Plane（12 个，新增）

| # | 工具 | 类型 | 阶段 |
|---|------|------|------|
| 1 | `compiler_intake_prepare` | read | Stage 1 |
| 2 | `compiler_intake_save` | write | Stage 1 |
| 3 | `compiler_plan_prepare` | read | Stage 2 |
| 4 | `compiler_plan_save` | write | Stage 2 |
| 5 | `compiler_skill_run` | read | Stage 3 |
| 6 | `compiler_skill_save` | write | Stage 3 |
| 7 | `compiler_review_prepare` | read | Stage 4 |
| 8 | `compiler_review_save` | write | Stage 4 |
| 9 | `compiler_lower_prepare` | read | Stage 5 |
| 10 | `compiler_lower_save` | write | Stage 5 |
| 11 | `compiler_assemble_handoff` | write | Handoff |
| 12 | `compiler_status` | read | 查询 |

### Validation Plane（7 个，新增）

| # | 工具 | 类型 | 用途 |
|---|------|------|------|
| 1 | `val_screenshot` | read | 增强截图 + ImageContent 返回 |
| 2 | `val_read_widget_tree` | read | 读取 UE5 控件树 |
| 3 | `val_read_game_state` | read | 读取运行时状态 |
| 4 | `val_simulate_input` | write | 模拟鼠标/键盘输入 |
| 5 | `val_pie_control` | write | 控制 PIE 生命周期 |
| 6 | `val_save_judgment` | write | 保存 Agent 判定结论 |
| 7 | `val_generate_report` | write | 汇总验证报告 |

---

## 8. 文件修改清单

### 新建文件

| 文件 | 用途 |
|------|------|
| `Plugins/AgentBridge/MCP/compiler_dispatch.py` | Compiler Plane 12 个工具的分发实现 |
| `Plugins/AgentBridge/MCP/validation_dispatch.py` | Validation Plane 7 个工具的分发实现 |

### 修改文件

| 文件 | 改动 |
|------|------|
| `Plugins/AgentBridge/MCP/tool_definitions.py` | 新增 `COMPILER_PLANE_TOOLS`(12) + `VALIDATION_PLANE_TOOLS`(7) |
| `Plugins/AgentBridge/MCP/server.py` | import 新 dispatch 模块，合并 `TOOL_DISPATCH` |
| `Plugins/AgentBridge/MCP/README.md` | 更新架构图、工具数（28→47）、三平面说明 |
| `task.md` | Phase 10 任务入口 |
| `CLAUDE.md` | 更新"当前阶段"为 Phase 10 |
| `Docs/Current/00_Index.md` | Phase 10 阶段名 + 新文档条目 |
| `Docs/Current/02_Current_Phase_Goals.md` | Phase 10 目标与成功标准 |
| `Docs/Current/05_Implementation_Boundary.md` | Phase 10 边界 |
| `Plugins/AgentBridge/Docs/architecture_overview.md` | 新增 Compiler Plane + Validation Plane 架构位置 |

---

## 9. 任务依赖图

```
M1: TASK 01 → TASK 02 → TASK 03（顺序，架构基础）
                                  ↓
M2: TASK 04 → TASK 05 → TASK 06 → TASK 07 → TASK 08（顺序，每阶段复用同一模式）
                                                       ↓
M3: TASK 09 ─┐
    TASK 10 ─┤→ TASK 11 → TASK 12
             │  （判定工具依赖感知+交互）
    （09 和 10 可并行）
```

---

## 10. 风险与缓解

| 风险 | 缓解 |
|------|------|
| PIE 自动化不稳定（start/stop） | `run_editor_python` + try/except + 明确错误返回 |
| Widget tree 读取返回过大 | `depth` 参数限制递归深度，默认 3 |
| Compiler skeleton 的 OUTPUT_DIR 硬编码 `ProjectState/phase8` | MCP dispatch 层覆盖 `output_path` 参数传入 `ProjectState/phase10/`，不修改 skeleton 代码 |
| MCP ImageContent 在 Claude Code 中的渲染 | 已确认 `mcp==1.26.0` 有 `types.ImageContent`；若 Claude Code 不渲染，fallback 为 base64 文本 |
| MonopolyGame GDD 复杂度导致 pipeline 验证耗时 | 只需走通 5 阶段产出，不要求 Agent 填充完美内容 |

---

## 11. 治理文档更新

Phase 10 启动时更新：
- `task.md` → Phase 10 任务
- `CLAUDE.md` → 当前阶段
- `Docs/Current/00_Index.md` → Phase 10 条目
- `Docs/Current/02_Current_Phase_Goals.md` → Phase 10 目标
- `Docs/Current/05_Implementation_Boundary.md` → Phase 10 边界

Phase 10 收尾时新增：
- `Docs/Current/15_Phase10_Closeout.md`
- `Docs/History/Tasks/task10_phase10.md`
