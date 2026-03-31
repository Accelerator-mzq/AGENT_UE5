# Skill Compiler Plane 设计

> 文档版本：v0.4.0 | 适用范围：AgentBridge 插件 Skill Compiler Plane

---

## 1. 定位与职责

Skill Compiler Plane 是 AgentBridge 框架的**编译前端**，位于设计输入与执行编排之间。它负责将设计输入（GDD）和项目现状转化为结构化的 Reviewed Handoff 交接物，交给 Execution Orchestrator Plane 执行。

### 1.1 Compiler 是什么

- 从 GDD / Requirements 等设计输入中提取结构化信息
- 识别项目当前模式（Greenfield / Brownfield）
- 组装 Reviewed Handoff（正式交接物）
- 输出 YAML 格式的 Handoff 文件到 `ProjectState/Handoffs/draft/`

### 1.2 Compiler 不是什么

- 不是 AI Agent（不做需求理解或创意决策）
- 不是执行层（不调用 Bridge 工具）
- 不是 Spec 生成器（Phase 4 才实装自动 Spec 生成）
- 不负责 Handoff 审批（审批由人工或治理流程完成）

### 1.3 在系统中的位置

```
Design Inputs（GDD / Requirements）
  + Project State Inputs（现有项目状态）
      ↓
  Skill Compiler Plane ← 本文档描述的模块
      ├── Design Input Intake
      ├── Project State Intake
      ├── Mode Router
      ├── Handoff Builder
      └── Handoff Serializer
      ↓
  Reviewed Handoff（draft → 审批 → approved）
      ↓
  Execution Orchestrator Plane
      ├── Run Plan Builder
      ├── Handoff Runner → Bridge → UE5
      └── Report Generator
```

---

## 2. 模块结构

```
Scripts/compiler/
├── __init__.py
├── intake/
│   ├── __init__.py
│   ├── design_input_intake.py    # 设计输入解析
│   └── project_state_intake.py   # 项目状态采集
├── routing/
│   ├── __init__.py
│   └── mode_router.py            # 模式路由
├── handoff/
│   ├── __init__.py
│   ├── handoff_builder.py        # Handoff 构建
│   └── handoff_serializer.py     # Handoff 序列化
├── analysis/                     # 占位（Phase 5）
│   └── README.md
├── generation/                   # 占位（Phase 4）
│   └── README.md
└── review/                       # 占位（Phase 4）
    └── README.md
```

独立运行入口：`Scripts/compiler_main.py`

---

## 3. 已实装模块详解

### 3.1 Design Input Intake（design_input_intake.py）

**职责**：解析 GDD 文件，提取结构化设计信息。

**输入**：Markdown 格式的 GDD 文件路径（如 `ProjectInputs/GDD/boardgame_tictactoe_v1.md`）

**输出**：结构化的 design_input 字典，包含：
- `game_type`：游戏类型（如 "boardgame"）
- `board`：棋盘信息（尺寸、格子大小）
- `pieces`：棋子信息（类型、外观、尺寸）
- `rules`：规则信息（回合制、胜负条件）

**当前限制**：
- 仅支持 boardgame 类型的 GDD 解析
- 基于关键词匹配，非 NLP 语义理解
- 复杂 GDD 结构可能解析不完整

### 3.2 Project State Intake（project_state_intake.py）

**职责**：采集当前项目状态，为模式路由和增量分析提供输入。

**输出**：结构化的 project_state 字典，包含：
- `has_existing_content`：是否有已有内容
- `actor_count`：当前 Actor 数量
- `has_baseline`：是否有基线快照

**当前限制**：
- 返回模拟数据（硬编码空项目状态）
- Phase 5 将桥接到真实 Bridge 查询接口

### 3.3 Mode Router（mode_router.py）

**职责**：确定当前应使用 Greenfield 还是 Brownfield 模式。

**三级优先级**：
1. **显式覆盖**：`ProjectInputs/Presets/mode_override.yaml` 中指定的 `force_mode`
2. **编译器配置**：`ProjectInputs/Presets/compiler_profile.yaml` 中的默认模式
3. **自动检测**：基于 project_state 判断（有内容 → brownfield，无内容 → greenfield）

**输出**：`routing_result` 字典，包含 `resolved_mode`（greenfield / brownfield）和 `resolution_source`

### 3.4 Handoff Builder（handoff_builder.py）

**职责**：从编译结果构建 Reviewed Handoff 结构。

**输入**：design_input + routing_result + project_state

**输出**：符合 `reviewed_handoff.schema.json` 的 Handoff 字典，包含：
- `handoff_version` / `handoff_id` / `handoff_mode` / `status`
- `project_context`：项目上下文
- `routing_context`：模式路由结果
- `dynamic_spec_tree`：动态 Spec 树（当前为从 design_input 直接转换）
- `review_summary` / `capability_gaps` / `governance_context`

### 3.5 Handoff Serializer（handoff_serializer.py）

**职责**：将 Handoff 字典序列化为 YAML 文件，写入 `ProjectState/Handoffs/draft/`。

**文件命名**：`handoff_{handoff_id}_{timestamp}.yaml`

---

## 4. 数据流

```
ProjectInputs/GDD/boardgame_tictactoe_v1.md
    │
    ▼
design_input_intake.py  ──→  design_input（结构化设计信息）
                                    │
ProjectInputs/Presets/*.yaml        │
    │                               │
    ▼                               ▼
mode_router.py  ──────→  routing_result（greenfield/brownfield）
    ▲                               │
    │                               │
project_state_intake.py → project_state（项目现状）
                                    │
                                    ▼
                          handoff_builder.py  ──→  Handoff 字典
                                    │
                                    ▼
                          handoff_serializer.py  ──→  YAML 文件
                                    │
                                    ▼
                          ProjectState/Handoffs/draft/handoff_xxx.yaml
```

---

## 5. 运行方式

### 5.1 通过 compiler_main.py 独立运行

```bash
cd Plugins/AgentBridge/Scripts
python compiler_main.py
```

默认读取 `ProjectInputs/GDD/` 下的 GDD 文件，输出 Handoff 到 `ProjectState/Handoffs/draft/`。

### 5.2 通过 Scripts/run_greenfield_demo.py 端到端运行

```bash
python Scripts/run_greenfield_demo.py
```

完整链路：Compiler → Handoff → Run Plan → 执行 → Report。

---

## 6. 占位模块说明

### 6.1 analysis/（Phase 5 实装）

Brownfield 模式专用模块：
- `baseline_builder.py` — 基线构建器（扫描项目现状）
- `delta_scope_analyzer.py` — 增量范围分析器（对比 GDD 和基线）

### 6.2 generation/（Phase 4 实装）

Spec 自动生成模块：
- `spec_generation_dispatcher.py` — 从 design_input + Static Base 生成 Dynamic Spec Tree

### 6.3 review/（Phase 4 实装）

交叉审查模块：
- `cross_spec_reviewer.py` — 引用完整性 + 字段类型检查

---

## 7. 与其他模块的关系

| 模块 | 关系 |
|------|------|
| Execution Orchestrator | Compiler 输出 Handoff → Orchestrator 消费 Handoff |
| Bridge | Compiler 不直接调用 Bridge；通过 Orchestrator 间接使用 |
| Schemas | Handoff 必须符合 `reviewed_handoff.schema.json` |
| Skills/genre_packs | 未来 Compiler 将调用类型包获取编译策略（Phase 6） |
| Specs/StaticBase | 未来 Compiler 将引用 Static Base 生成 Spec（Phase 4） |
| ProjectInputs | Compiler 的输入源（GDD / Presets） |
| ProjectState | Compiler 的输出目标（Handoffs/draft/） |

---

## 8. 设计约束

1. Compiler 主体在插件层（`Plugins/AgentBridge/Scripts/compiler/`），不在项目层
2. 项目层只提供输入（GDD / Presets）和保存实例（Handoffs）
3. 不修改现有 Bridge / Orchestrator 核心文件
4. 所有新增通过新增文件实现
5. Handoff 必须通过 Schema 校验才视为有效
