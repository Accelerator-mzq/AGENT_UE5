# Skills / Specs 体系概述

> 文档版本：v0.5.0 | 适用范围：AgentBridge 插件 Skills 与 Specs 体系

---

## 1. 概述

Skills 和 Specs 是 AgentBridge 框架的两个互补体系：

- **Skills**：编译驱动力 — 决定"怎么编译"（编译策略、类型化规则、审查扩展）
- **Specs**：编译地基 — 决定"编译的边界是什么"（静态基座、契约、模板）

两者共同服务于 Skill Compiler Plane，将设计输入转化为合法的 Dynamic Spec Tree。

---

## 2. Skills 体系

### 2.1 双核心架构

| 核心 | 定位 | 阶段 |
|------|------|------|
| **Base Skill Domains** | 通用编译骨架（10 个域） | Phase 7 完整化 |
| **Genre Skill Packs** | 类型化编译策略包 | Phase 6 完整化 |

### 2.2 Base Skill Domains（10 个域）

通用编译能力骨架，适用于所有游戏类型：

| 域 | 职责 | 优先级 |
|----|------|--------|
| Design & Project State Intake | 设计输入和项目状态吸收 | P0 |
| Baseline Understanding | 基线理解（Brownfield） | P0 |
| Delta Scope Analysis | 增量范围分析（Brownfield） | P0 |
| Product & Scope | 产品范围和目标 | P0 |
| Runtime & Gameplay | 运行时和游戏逻辑 | P0 |
| World & Level | 世界和关卡构建 | P0 |
| Presentation & Asset | 视觉呈现和资产 | P1 |
| Config & Platform | 配置和平台 | P1 |
| QA & Validation | 测试和验证 | P1 |
| Planning & Governance | 规划和治理 | P2 |

**当前状态**：目录已保留，Phase 7 完整实装。

### 2.3 Genre Skill Packs（类型包）

针对特定游戏类型的编译策略包。每个类型包包含：

| 组件 | 说明 |
|------|------|
| `pack_manifest.yaml` | 类型包清单（激活规则、依赖、策略） |
| Router | 类型识别和路由规则 |
| Required Skills | 必需编译技能 |
| Optional Skills | 可选编译技能 |
| Review Extensions | 类型化审查扩展 |
| Validation Extensions | 类型化验证扩展 |
| Delta Policy | Brownfield 增量策略 |

**首个类型包**：`boardgame`（棋盘游戏）

**当前状态**：Phase 6 已落地 `_core` 最小机制与 `boardgame` 首个真实类型包。Compiler 现在会真正消费 pack manifest、required skills、review extensions、validation extensions 与 delta policy。

### 2.4 目录结构

```text
Skills/
├── base_domains/                    # 通用编译域（Phase 7 完整化）
│   └── README.md
└── genre_packs/
    ├── _core/
    │   ├── manifest_loader.py
    │   ├── registry.py
    │   ├── router_base.py
    │   └── module_loader.py
    └── boardgame/
        ├── pack_manifest.yaml
        ├── required_skills/
        ├── review_extensions/
        ├── validation_extensions/
        └── delta_policy/
```

---

## 3. Specs 体系

### 3.1 三个子目录

| 子目录 | 定位 | 阶段 |
|--------|------|------|
| **StaticBase/** | 静态基座定义 — 框架能力地基 | Phase 4 实装 |
| **Contracts/** | 契约模型 — Patch / Migration / Regression | Phase 5 实装 |
| **templates/** | Spec 模板 — 已有 scene_spec 模板 | Phase 1-2 已有 |

### 3.2 Static Spec Base

静态基座定义框架级能力边界，分两层：

**Layer A — 通用基础（6 个）**：
1. GameplayFrameworkStaticSpec — Runtime 表达地基
2. UIModelStaticSpec — UI 层基础表达
3. AudioEventStaticSpec — 音频层基础表达
4. WorldBuildStaticSpec — 场景构建基础表达
5. ConfigStaticSpec — 配置层基础表达
6. ValidationStaticSpec — 验证层基础表达

**Layer B — Boardgame 类型（4 个）**：
7. BoardgameStaticSpec — 棋盘游戏核心表达
8. BoardgameUIStaticSpec — 棋盘游戏 UI 表达
9. BoardgameAudioStaticSpec — 棋盘游戏音频表达
10. BoardgameValidationStaticSpec — 棋盘游戏验证表达

**当前状态**：`Specs/StaticBase/` 已完成 Phase 4 最小落地，并继续作为后续扩展地基。

### 3.3 Contracts

约束 Brownfield 修改的契约模型：

| 契约类型 | 说明 | 阶段 |
|---------|------|------|
| SpecPatchContract | 局部受控增量修改契约 | Phase 5 |
| MigrationContract | 跨契约边界结构变更契约 | Phase 5 |
| RegressionValidationContract | 回归验证契约 | Phase 5 |

**当前状态**：`Specs/Contracts/` 已完成 Phase 5 最小落地，并在 Phase 6 新增 Boardgame Genre Contracts：

- `TurnFlowPatchContract`
- `DecisionUIPatchContract`

### 3.4 Templates（已有）

Phase 1-2 创建的 Spec 模板：
- `scene_spec_template.yaml` — 通用场景 Spec 模板
- `scene_spec_task14_cpp_plugin_runtime.yaml` — Task14 运行时 Spec
- `scene_spec_task14_semantic_runtime.yaml` — Task14 语义运行时 Spec

### 3.5 目录结构

```
Specs/
├── StaticBase/                      # 静态基座（已落地）
│   └── README.md
├── Contracts/                       # 契约模型（已落地最小体系）
│   └── README.md
└── templates/                       # Spec 模板（已有）
    ├── scene_spec_template.yaml
    ├── scene_spec_task14_cpp_plugin_runtime.yaml
    └── scene_spec_task14_semantic_runtime.yaml
```

---

## 4. Skills 与 Specs 的依赖关系

```
Static Spec Base（地基）
    ↓ 提供模板、Schema、约束
Skills（编译驱动力）
    ├── Base Skill Domains → 通用编译
    └── Genre Skill Packs → 类型化编译
    ↓ 生成
Dynamic / Delta Spec Tree
    ↓ 组装
Reviewed Handoff
```

**依赖方向**：Static Spec Base → Skill Compilation → Spec Tree → Handoff

**规则**：
- Skills 必须引用 Static Base 的定义，不可自行发明长期契约
- 当 Static Base 不完整时，Skills 应报告 capability_gaps 而非跳过
- Genre Skill Packs 是 Static Base 扩展的重要需求来源

---

## 5. 演进路线

| 阶段 | Skills 进展 | Specs 进展 |
|------|------------|------------|
| **Phase 3（已完成）** | boardgame 最小骨架 | 最小 pack manifest + 现有 templates |
| **Phase 4（已完成）** | — | Static Base Layer A+B + 自动 Spec 生成 |
| **Phase 5（已完成）** | — | Brownfield Baseline / Delta / Contracts 最小落地 |
| **Phase 6（进行中）** | Genre Pack 完整化 + `_core` 机制 + boardgame playable pipeline | Boardgame Genre Contracts |
| **Phase 7** | Base Domains 完整实装 + 第二个类型包 | — |
