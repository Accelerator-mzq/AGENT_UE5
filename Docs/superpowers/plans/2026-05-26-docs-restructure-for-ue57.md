# Mvpv4TestCodex 文档重组 + UE 5.7 重构输入规格 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (推荐) 或 `superpowers:executing-plans` 来按任务执行此计划。所有步骤使用 checkbox(`- [ ]`)语法。

**Goal:** 将项目当前所有功能(Phase 11 / UE 5.5.4 口径)整合为统一的 `Docs/` 文档结构,作为 UE 5.7 重构开发者的输入规格;新文档必须能证明"无功能遗漏",同时不复制粘贴 / 去除冗余。

**Architecture:** 五件套(SRS / HLD / LLD / test_spec / acceptance_report)+ contracts/ + governance.md + FEATURE_INVENTORY + archive/,所有文档围绕 FEATURE_INVENTORY 矩阵和 `redirects.json` 形成双向 traceability;符号/工具/字段/用例级 grep 校验作为门禁。

**Tech Stack:** Markdown + JSON + Python 3.x(校验脚本)+ git mv(搬迁)+ ripgrep(grep 校验)+ document-release skill(收尾)。

**Spec 来源**: `Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md` (v1.1,Codex 对抗审过)

---

## 前置说明

### 工作单位粒度

此 plan 的"step"单位不同于代码 plan。文档写作类 step 估计 20-60 分钟,脚本/搬迁/grep 类 step 才是 2-5 分钟。`Files / Commit` 是步骤模板的固定头尾。

### 并行节奏(参 spec §6)

- **Phase 0.1**(旧文档清单 + archive/README v1)是 Phase 1 / Phase 2 的**共同前置**,必须先做完
- **Phase 0.4**(redirects.json)是 Phase 2 / Phase 4 的前置
- **Phase 0.2**(UE 5.7 扫描)与 Phase 1 主体撰写**可并行**;但 FEATURE_INVENTORY "UE 5.7 状态"列 + SRS/LLD "迁移记号"子节,必须等 Phase 0.2 完成才能填实
- **Phase 1 内 19 个文档**有依赖序: contracts → SRS → HLD → LLD → test_spec → acceptance → governance → FEATURE_INVENTORY 回填 → INDEX

### 分支建议

在 `feat/docs-restructure-ue57` 分支上执行;每 Phase 末尾走 `superpowers:verification-before-completion` + 中间 commit;最终走 `document-release` 与 `superpowers:finishing-a-development-branch` 收尾。

### 工作目录

所有路径相对项目根 `D:\UnrealProjects\Mvpv4TestCodex`(Windows + Git-Bash)。

---

## File Structure

**新建文件**:

```
Docs/
├── INDEX.md                                  # 入口
├── FEATURE_INVENTORY.md                      # 多源交叉矩阵
├── governance.md                             # 文档治理
├── redirects.json                            # 机器可读旧→新映射
├── requirements/SRS.md
├── design/
│   ├── HLD.md
│   └── LLD/
│       ├── README.md
│       ├── 01_cpp_subsystem.md
│       ├── 02_bridge.md
│       ├── 03_orchestrator.md
│       ├── 04_compiler.md
│       ├── 05_mcp_server.md
│       ├── 06_skills_and_templates.md
│       └── 07_runtime_and_evidence.md
├── testing/test_spec.md
├── acceptance/acceptance_report.md
├── contracts/
│   ├── schemas_catalog.md
│   ├── mcp_tools_catalog.md
│   ├── tool_contract.md
│   └── field_specification.md
└── archive/
    ├── README.md                              # 反向映射主表
    ├── current/                               # ← Docs/Current 整搬
    ├── history/                               # ← Docs/History 整搬
    ├── proposals/                             # ← Docs/Proposals 整搬
    ├── decisions/                             # ← Docs/Decisions 整搬
    ├── superpowers/                           # ← Docs/superpowers/* 整搬
    └── plugins/                               # ← Plugins/AgentBridge/Docs/* 抽取后整搬

Docs/superpowers/specs/
├── 2026-05-26-old-docs-inventory.csv         # Phase 0.1 产出
└── 2026-05-26-ue57-breaking-changes-scan.md  # Phase 0.2 产出

Scripts/validation/
└── feature_inventory_check.py                # Phase 2 产出
```

**修改文件**(链接重写):

```
项目根/AGENTS.md
项目根/CLAUDE.md
项目根/README.md
项目根/task.md
Plugins/AgentBridge/README.md
Plugins/AgentBridge/AGENTS.md
.claude/skills/document-release/SKILL.md
.agents/skills/document-release/SKILL.md
Scripts/hooks/doc_release_gate.py (若有硬编码路径)
Docs/superpowers/specs/ 其他 spec (反向引用,若有)
Docs/superpowers/plans/ 其他 plan (反向引用,若有)
```

**搬迁 + redirect stub**(`git mv` 后原位置写 stub):

```
Plugins/AgentBridge/Docs/*.md (30 份原位置写 redirect stub)
```

---

## Phase 0: 前置扫描 + 反向映射 v1

### Task 0.1: 建立旧文档全清单 + archive/README v1

**Files:**
- Create: `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv`
- Create: `Docs/archive/README.md`

- [ ] **Step 1: Glob 所有旧 markdown 文档**

Run:
```bash
find Docs -name "*.md" -not -path "*/superpowers/specs/2026-05-26-*" \
  -not -path "*/superpowers/plans/2026-05-26-docs-restructure*" \
  | sort > /tmp/old_docs_project.txt
find Plugins/AgentBridge/Docs -name "*.md" | sort > /tmp/old_docs_plugin.txt
wc -l /tmp/old_docs_project.txt /tmp/old_docs_plugin.txt
```

Expected: 项目层 ~50 行 + 插件层 30 行 = ~80 行

- [ ] **Step 2: 建 CSV 表头**

Create `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv`:
```csv
old_path,content_topic,status,planned_new_anchor,cross_refs_count,notes
```

字段含义:
- `old_path`: 相对项目根的路径
- `content_topic`: 一句话主题
- `status`: `already-consumed` / `need-consume` / `archive-only` / `deprecated`
- `planned_new_anchor`: `Planned: <预期新路径#section>`(Phase 1 时实地化)
- `cross_refs_count`: 该文档被多少其他文档引用(grep 统计)
- `notes`: 任何特殊处理说明

- [ ] **Step 3: 逐份填表 — 项目层 Docs/Current 17 份**

参照 spec v1.1 §5.1 已列出的 17 份完整归宿(已敲定),直接写入 CSV。

每行 cross_refs_count 通过命令获取:
```bash
# 示例:
grep -rl "Docs/Current/01_Project_Baseline" --include="*.md" . | grep -v "Docs/Current/01_Project_Baseline" | wc -l
```

- [ ] **Step 4: 逐份填表 — Docs/History 整树**

```bash
ls Docs/History/Tasks/*.md Docs/History/Proposals/*.md Docs/History/Phase11_Design_Pack/*.md 2>/dev/null
```

策略:
- `Tasks/task*.md`(各阶段历史任务): 全部 `archive-only`,新归宿 `archive/history/Tasks/<原文件名>`
- `Proposals/Phase*.md`: 全部 `archive-only`,新归宿 `archive/history/Proposals/<原文件名>`
- `Phase11_Design_Pack/*.md`: 16 份原始设计文档已被吸收到 Plugins/AgentBridge/Docs 8 份框架级规范,**已消化**,新归宿 `archive/history/Phase11_Design_Pack/<原文件名>`(保留追溯)

- [ ] **Step 5: 逐份填表 — Decisions / Proposals / superpowers**

```bash
ls Docs/Decisions/ Docs/Proposals/ Docs/superpowers/specs/ Docs/superpowers/plans/ 2>/dev/null
```

- Decisions/* → 全部 `archive-only` 到 `archive/decisions/`,关键 ADR 内容已被吸收到 HLD §8(若有)
- Proposals/* → 全部 `archive-only` 到 `archive/proposals/`
- superpowers/specs/* → 除本 spec 与 inventory/scan spec 外,其余 `archive-only` 到 `archive/superpowers/specs/`
- superpowers/plans/* → 类似 specs

- [ ] **Step 6: 逐份填表 — Plugins/AgentBridge/Docs 30 份**

参照 spec v1.1 §5.1 示例 + AGENTS.md §2.6 已列出的部分。需要 ls 全清单并逐份分类:

```bash
ls Plugins/AgentBridge/Docs/
```

预期 30 份,主要分类:
- `architecture_overview.md` / `tool_contract_v0_1.md` / `field_specification_v0_1.md` / `feedback_interface_catalog.md` 等基础契约 → `已消化`,新归宿到 contracts/* 或 design/HLD/LLD
- Phase 11 框架级规范 8 份(`root_skill_contract_standard.md` 等) → `已消化`,新归宿 SRS §3-4 + LLD/04 + LLD/06
- 其他次要文档 → 按内容判断 `已消化` 或 `archive-only`

- [ ] **Step 7: 起 archive/README.md v1(反向映射主表)**

Create `Docs/archive/README.md`:
```markdown
# Docs Archive — 旧→新反向映射主表

> 版本: v1(2026-05-26)由 inventory CSV 自动生成
> 后续: Phase 1 写作时同步实地化 `planned_new_anchor`

## 旧文档归宿表

| 旧路径 | 内容主题 | 新归宿 | 状态 |
|--------|----------|--------|------|
```

将 inventory CSV 逐行转为 markdown 表(可以 Python 脚本一次性转,或手工 Edit)。`planned_new_anchor` 字段前缀 `Planned: ` 表示尚未实地化。

- [ ] **Step 8: 跑双源对账校验**

确保 inventory CSV 行数 = 真实旧文档数:

```bash
csv_count=$(tail -n +2 Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv | wc -l)
real_count=$(cat /tmp/old_docs_project.txt /tmp/old_docs_plugin.txt | wc -l)
echo "CSV: $csv_count, Real: $real_count"
```

Expected: 两数相等(若有偏差 → 补漏到 CSV)

- [ ] **Step 9: Commit**

```bash
git add Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv \
        Docs/archive/README.md
git commit -m "docs(restructure-ue57): Phase 0.1 — 旧文档全清单 + archive/README v1

- inventory CSV: ~80 份旧文档归宿登记
- archive/README v1: 反向映射主表,planned_new_anchor 待 Phase 1 实地化"
```

---

### Task 0.2: UE 5.5.4 → 5.7 breaking change 扫描

**Files:**
- Create: `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`

> **注**: 此任务与 Phase 1 主体撰写**可并行**。本任务可以委派给 `Agent` 子代理(general-purpose 或 Plan)做调研,主线程同时跑 Phase 1。

- [ ] **Step 1: 起 scan spec 文件,写元信息与扫描范围声明**

Create `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`:
```markdown
# UE 5.5.4 → 5.7 Breaking Change Scan

> 日期: 2026-05-26
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §7
> 状态: 进行中

## 0. 扫描范围(9 类,见关联 spec §7.1)

1. C++ 代码层 — 项目层 Source + 插件层 Source
2. 构建系统 — *.Build.cs / *.Target.cs / *.uplugin
3. 资产层 — Content/ 下 .uasset / .umap / Blueprint
4. 配置层 — Config/*.ini
5. Python Editor API — unreal module binding
6. Remote Control 协议 — RC HTTP API 端点
7. UAT / UBT 命令行
8. Plugin 依赖
9. PowerShell / 项目脚本

## 1. 已扫范围
## 2. 未覆盖范围(留 UE 5.7 实测验证)
## 3. Breaking Change 表(12 字段)
```

- [ ] **Step 2: 第 1 类 — C++ 代码层符号扫描**

Run:
```bash
# 项目层 Source(可能为空)
ls Source/Mvpv4TestCodex/ 2>/dev/null || echo "项目层 Source 为空"

# 插件层 Source
grep -rn "UEditorSubsystem\|UEditorAssetSubsystem\|IAutomationLatentCommand\|FAutomationTestBase\|IRemoteControlModule\|FRemoteControlField\|UCommandlet\|UFactory\|FSlateApplication\|IPluginManager\|FModuleManager" \
  --include="*.h" --include="*.cpp" Plugins/AgentBridge/Source/ > /tmp/ue_symbols.txt
wc -l /tmp/ue_symbols.txt
```

把每个 grep 命中的符号 + 文件 + 行号写入 scan spec §3 表。

逐符号查 UE 5.6 / 5.7 release notes(或委派 Agent 用 WebFetch / WebSearch 查官方 docs.unrealengine.com 与 release notes 页)。

- [ ] **Step 3: 第 2 类 — 构建系统**

Run:
```bash
find . -name "*.Build.cs" -o -name "*.Target.cs" -o -name "*.uplugin" -o -name "*.uproject" 2>/dev/null | grep -v "Intermediate\|Saved"
```

逐个文件检查 5.7 兼容性变更点(主要看 .uplugin 的 EngineVersion 与依赖、.Build.cs 的 ModuleAPI 用法)。

- [ ] **Step 4: 第 3 类 — 资产层**

Run:
```bash
find Content -name "*.uasset" -o -name "*.umap" 2>/dev/null | wc -l
```

资产层不能完全静态扫,只统计数量并在 scan spec 的 §2 "未覆盖范围"标注: "资产层 .uasset/.umap 需 UE 5.7 编辑器实测验证,本扫描只列出数量"。

- [ ] **Step 5: 第 4 类 — 配置层**

Run:
```bash
ls Config/*.ini 2>/dev/null
```

逐份检查 5.7 引擎新增/废弃的 key(主要 DefaultEngine.ini / DefaultEditor.ini / DefaultInput.ini)。

- [ ] **Step 6: 第 5-9 类 — Python / RC / UAT / Plugin / Script**

Run:
```bash
grep -rn "import unreal\|unreal\." --include="*.py" Plugins/AgentBridge/Scripts/ Scripts/ > /tmp/python_unreal.txt
grep -rn "remote_control\|/remote/\|30010\|RC_" --include="*.py" Plugins/AgentBridge/Scripts/ > /tmp/rc_calls.txt
grep -rn "RunUAT\|UAT\|BuildEditor\|BuildCookRun" --include="*.py" --include="*.ps1" . > /tmp/uat_calls.txt
grep -rn "UE_5\.5\|UnrealEngine 5\.5\|Engine\\\\Binaries" --include="*.py" --include="*.ps1" Plugins/AgentBridge/Scripts/ Scripts/ > /tmp/hardcoded_ver.txt
```

- [ ] **Step 7: 逐条填 12 字段表**

scan spec §3 表头:
```markdown
| id | api_or_key | category | usage_in_5_5_4 | usage_in_5_7 | source_url | confidence | impacted_files | migration_difficulty | false_positive_status | validation_command | reviewer | linked_F_id |
```

每条 breaking change 必填前 12 字段。`linked_F_id` 选填(此时 FEATURE_INVENTORY 尚未完成,可暂空,Phase 1 写完后回填)。

委派 Agent(general-purpose,WebFetch 工具)逐条查官方 release notes,无来源时填 `inferred-from-grep` + `confidence: low`。

- [ ] **Step 8: msc 人工裁决 false-positive**

输出当前 scan spec §3 表给 msc,逐条标注 `false_positive_status`:
- `confirmed`: 真实迁移点
- `suspected`: 待 5.7 实测
- `false-positive`: 误报(不进 SRS/LLD 迁移记号)

- [ ] **Step 9: 总结与 Commit**

scan spec §1 / §2 末尾各写一段总结:
- §1 列出已扫的 9 类范围,每类扫到的 breaking change 数
- §2 列出未覆盖范围(资产层、UE 5.7 编辑器实测才能覆盖的行为变更)

```bash
git add Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md
git commit -m "docs(restructure-ue57): Phase 0.2 — UE 5.7 breaking change 扫描

- 扫描 9 类范围,每条 12 字段完整
- false_positive 已人工裁决
- 未覆盖项标 TBD-need-runtime-validation"
```

---

### Task 0.3: FEATURE_INVENTORY 第一版

**Files:**
- Create: `Docs/FEATURE_INVENTORY.md`

- [ ] **Step 1: 起文件 + 元信息 + 矩阵列头**

Create `Docs/FEATURE_INVENTORY.md`:
```markdown
# Mvpv4TestCodex — Feature Inventory(多源交叉矩阵)

> 版本: v1(2026-05-26)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §3
> 验收门禁底座: 每行 F-* ID 必须能在 SRS/LLD 锚点 grep 命中

## 矩阵主表

| ID | 功能名 | 简述 | 模块归属 | 主文档锚点 | 证据源 | 测试覆盖 | UE 5.7 状态 |
|----|--------|------|----------|------------|--------|----------|-------------|
```

- [ ] **Step 2: 填 C++ 模块行(F-CPP-*)**

参考 spec v1.1 §1.5 + Agent 探索的 5 个核心类(Subsystem / Commandlet / UATRunner / AutomationDriver / BridgeTypes)。

每行示例:
```markdown
| F-CPP-01 | AgentBridgeSubsystem | UEditorSubsystem 主入口 | C++ | TBD | Source/AgentBridge/Public/AgentBridgeSubsystem.h + Private/AgentBridgeSubsystem.cpp | TBD | TBD |
```

锚点先填 `TBD`(Phase 1 写完 SRS/LLD 后回填),UE 5.7 状态等 Task 0.2 完成后从 scan spec 回链。

- [ ] **Step 3: 填 Bridge 模块行(F-BRG-*)**

按 Bridge 9 个 Python 模块拆 ~10 行家族,例:
- F-BRG-01: L1 查询接口族(12 个工具)
- F-BRG-02: L1 写接口族(4 个工具)
- F-BRG-03: L1 反馈接口族(7 个工具)
- F-BRG-04: L3 UI 自动化族
- F-BRG-05: Remote Control HTTP 客户端
- F-BRG-06: UAT 包装器
- F-BRG-07: UE 资产/关卡 helpers
- F-BRG-08: 项目配置解析
- F-BRG-09: bridge_core 通信主体

- [ ] **Step 4: 填 Orchestrator 行(F-ORC-*)**

按 11 个 Orchestrator 模块拆,~8 行家族:
- F-ORC-01: 主体编排 + 通道选择(orchestrator.py)
- F-ORC-02: Plan 生成(plan_generator + run_plan_builder)
- F-ORC-03: Spec 读取(spec_reader)
- F-ORC-04: 验证与对标(verifier)
- F-ORC-05: 报告生成(report_generator)
- F-ORC-06: 故障恢复(recovery_planner)
- F-ORC-07: Handoff 执行(handoff_runner + validation_inserter)
- F-ORC-08: ForgeUE manifest 导入(forgeue_manifest_importer)

- [ ] **Step 5: 填 Compiler 行(F-CMP-*)**

按 Scripts/compiler(15)+ Plugins/.../Compiler(高阶 9 Stage)拆 ~15 行:
- F-CMP-01-05: Scripts/compiler 子模块(analysis / generation / handoff / intake / routing / review)
- F-CMP-06: 高阶 pipeline_orchestrator
- F-CMP-07-13: 7 个 Stage(root_skill_contract / clarification_gate / discovery_fallback / realization_fallback / convergence_fallback / agent_protocol / llm_client / handoff_v3 / cross_review_v2 / lowering_v2 / domain_skill_runtime / skill_graph_planning)
- F-CMP-14-15: cross_review / lowering / planner / skill_runtime 跨阶段组件

- [ ] **Step 6: 填 MCP 行(F-MCP-*)**

按 spec v1.5 工具家族粒度,~10 行:
- F-MCP-01: Bridge L1 查询族(对应 catalog 12 工具)
- F-MCP-02: Bridge L1 写族(catalog 4 工具)
- F-MCP-03: Bridge L1 反馈族(catalog 7 工具)
- F-MCP-04: Bridge L2 编辑器服务族
- F-MCP-05: Bridge L3 UI 族
- F-MCP-06: 前端 Stage 1 Root Skill Contract 族(catalog ~2 工具:prepare/save)
- F-MCP-07: 前端 Stage 2 Clarification Gate 族
- F-MCP-08: 前端 Stage 3 Skill Graph Planning 族
- F-MCP-09: 前端 Stage 4 节点交互族
- F-MCP-10: 后端 Evidence 读写族
- F-MCP-11: 后端 Run 治理族(compare/promote)
- F-MCP-12: 兼容 alias 族(4 个)

- [ ] **Step 7: 填 Skill / Runtime / Chain / Governance 行**

- F-SKL-01: SkillGraph 数据结构
- F-SKL-02: Domain Skill Runtime
- F-SKL-03: Baseline 6 Skill 模板(start_screen / main_menu / settings / pause / results / hud)
- F-SKL-04: Genre Pack — Monopoly 6 Skill
- F-RT-01: UE 关卡引导(Editor game)
- F-RT-02: Standalone staged 运行时
- F-RT-03: Evidence 落盘(ProjectState/Evidence)
- F-RT-04: Reports 生成
- F-RT-05: Run Workspace 隔离
- F-CHN-01-07: 7 阶段主链(Root Skill Contract / Clarification Gate / Skill Graph Planning / Domain Skill Runtime / Cross Review v2 / Build IR v2 / Reviewed Handoff v3)
- F-CHN-S4-01-03: Stage 4 三路(mcp_agent / llm / heuristic_fallback)
- F-CHN-MODE-01-03: 模式路由(Greenfield / Brownfield / Playable Runtime)
- F-GOV-01: run_id 生命周期
- F-GOV-02: fast_mode 不可 promote
- F-GOV-03: generator_provider 影响 is_promotable
- F-GOV-04: compare/promote 工具

- [ ] **Step 8: 填 Schema 行(F-SCH-*)**

由于 Schemas 64 个,这里 inventory 走家族:
- F-SCH-01: 主链 v3 Schema 集(root_skill_contract / skill_graph / design_space_report / realization_candidates / converged_realization_pack / clarification_gate_report / cross_review_report_v2 / build_ir_v2 / reviewed_handoff_v3)
- F-SCH-02: v1/v2 兼容 Schema(reviewed_handoff v1/v2 / build_ir v1 / cross_review_report v1 / skill_fragment v1)
- F-SCH-03: 共享基础(common/ 6 份)
- F-SCH-04: 反馈契约(feedback/ 9 份 + write_feedback/ 1 份)
- F-SCH-05: 治理(compiler_session / naming_resolution_log / design_decision_log / run_comparison / batch_manifest)
- F-SCH-06: Examples 与版本清单

- [ ] **Step 9: 末尾加"门禁规则区"**

```markdown
## 验收门禁(摘自关联 spec v1.1 §3.2 / §8)

| 证据源 | 数量 | 细粒度门禁 |
|--------|------|------------|
| 代码公开符号 | ~传 grep 统计 | 每符号 ≥ 1 F-* 或 catalog 行引用 |
| MCP 工具 | 53 | mcp_tools_catalog 53 行 + 每行 6 字段完整 |
| Schema | 64 | schemas_catalog 64 行 + 每行 5 字段完整 |
| 测试用例 | 266 | test_spec 266 行 + 每行 5 字段(含当前 pass/fail/skip) |
| 旧文档 | ~80 | redirects.json 每份有 old→new 映射 |
```

- [ ] **Step 10: Commit**

```bash
git add Docs/FEATURE_INVENTORY.md
git commit -m "docs(restructure-ue57): Phase 0.3 — FEATURE_INVENTORY v1

- ~80-100 行 F-* ID 覆盖项目所有功能家族
- 主文档锚点 + UE 5.7 状态待 Phase 1 / Phase 0.2 完成后回填"
```

---

### Task 0.4: redirects.json 初版

**Files:**
- Create: `Docs/redirects.json`

- [ ] **Step 1: 从 inventory CSV 生成 JSON**

写一次性脚本(放在 `/tmp/`,不入仓):

Create `/tmp/csv_to_redirects.py`:
```python
import csv, json, sys
redirects = {}
with open('Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        old = row['old_path']
        new = row['planned_new_anchor'].replace('Planned: ', '')
        redirects[old] = new
print(json.dumps(redirects, ensure_ascii=False, indent=2))
```

Run:
```bash
python /tmp/csv_to_redirects.py > Docs/redirects.json
```

- [ ] **Step 2: 校验 JSON 合法性**

Run:
```bash
python -c "import json; d = json.load(open('Docs/redirects.json', encoding='utf-8')); print(f'映射条目: {len(d)}')"
```

Expected: 条目数 = inventory CSV 行数

- [ ] **Step 3: Commit**

```bash
git add Docs/redirects.json
git commit -m "docs(restructure-ue57): Phase 0.4 — redirects.json 初版

- 机器可读 old→new 映射,Phase 2/4 grep 字典源
- planned_new_anchor 实地化进度由 Phase 1 同步更新"
```

---

## Phase 1: 写五件套 + governance + contracts

**通用步骤模板**(每个新文档任务都按这套来):

```
Step 1: 起新文件,写元信息(版本、日期、关联 spec、状态)
Step 2: 写章节大纲(从 spec v1.1 §4 复制对应小节)
Step 3-N: 逐章节,从 inventory CSV 找出"need-consume"列表中归属本文档的旧文档,逐份消化:
  - Read 旧文档
  - 摘取事实(数字、机制、契约)
  - 用自己的话重写到对应章节,不复制粘贴
  - inventory CSV 同步:status: need-consume → already-consumed,planned_new_anchor 实地化
  - archive/README.md 同步更新
Step N+1: 同一事实跨文档已经在新文档其他位置写过的,本文档只写"详见 <锚点>",不复述
Step N+2: 文件末尾加"## UE 5.7 Migration Notes"小节,引用 scan spec 中本模块对应的 breaking changes
Step N+3: 跑 grep 自检(本文档中所有 F-* ID 都能在 FEATURE_INVENTORY grep 到反向引用)
Step N+4: Commit
```

### Task 1.1: contracts/tool_contract.md(抽取自插件 Docs)

**Files:**
- Create: `Docs/contracts/tool_contract.md`
- Read: `Plugins/AgentBridge/Docs/tool_contract_v0_1.md`

- [ ] **Step 1: Read 源文件**

Read `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` 全文。

- [ ] **Step 2: 起新文件 + 章节大纲**

Create `Docs/contracts/tool_contract.md`:
```markdown
# Tool Contract — L1/L2/L3 工具协议

> 版本: v1.0(从 Plugins/AgentBridge/Docs/tool_contract_v0_1.md 抽取消化)
> 关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1

## 1. 分层定义
## 2. L1 语义工具
## 3. L2 编辑器服务工具
## 4. L3 UI 工具
## 5. 调用约束
## 6. 错误约定
## 7. UE 5.7 Migration Notes
```

- [ ] **Step 3: 消化原文 — L1/L2/L3 分层定义**

将 tool_contract_v0_1.md 中的层级定义,改写为更紧凑、契约语言。不复制段落,而是用契约表(每层"用途/输入约束/输出约束/失败行为")。

- [ ] **Step 4: 消化原文 — 调用约束与错误约定**

- [ ] **Step 5: 填 UE 5.7 Migration Notes**

从 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 找类别为 `Remote Control` 与 `Python Editor API` 的条目(L1/L2 工具受影响最多),逐条引用 `UE57-BC-NNN` ID。

- [ ] **Step 6: 同步更新 inventory CSV + archive/README.md**

inventory CSV 中 `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` 行:
- `status` → `already-consumed`
- `planned_new_anchor` → `contracts/tool_contract.md(全文)`

archive/README.md 表格对应行同步。

- [ ] **Step 7: Commit**

```bash
git add Docs/contracts/tool_contract.md \
        Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv \
        Docs/archive/README.md
git commit -m "docs(restructure-ue57): Phase 1.1 — contracts/tool_contract.md

- 抽取自 Plugins/AgentBridge/Docs/tool_contract_v0_1.md
- 消化重写,不复制粘贴
- L1/L2/L3 协议 / 调用约束 / 错误约定 / UE 5.7 迁移记号"
```

---

### Task 1.2: contracts/field_specification.md

**Files:**
- Create: `Docs/contracts/field_specification.md`
- Read: `Plugins/AgentBridge/Docs/field_specification_v0_1.md`

按 Task 1.1 通用步骤模板,把 field_specification_v0_1.md 消化重写到 `Docs/contracts/field_specification.md`。

章节大纲:
```markdown
1. 共享字段类型(transform / bounds / collision / material 等)
2. 命名规范(GDD-First + UE5 路径)
3. Schema 规则(版本化、扩展性、严格校验)
4. 字段引用追踪
5. UE 5.7 Migration Notes
```

最后 inventory CSV / archive/README.md 同步 + Commit。

---

### Task 1.3: contracts/schemas_catalog.md(64 行字段级表)

**Files:**
- Create: `Docs/contracts/schemas_catalog.md`

- [ ] **Step 1: 起文件 + 元信息**

Create `Docs/contracts/schemas_catalog.md`:
```markdown
# Schemas Catalog — 64 Schema 字段级索引

> 版本: v1.0
> 验收门禁: 每行 5 字段完整(文件/用途/版本/引用方/关键字段清单)

## 主表
| 文件 | 用途 | 版本 | 引用方 | 关键字段清单 |
|------|------|------|--------|--------------|
```

- [ ] **Step 2: glob 所有 Schema 文件**

Run:
```bash
find Plugins/AgentBridge/Schemas -name "*.json" -not -path "*/examples/*" | sort > /tmp/schemas.txt
find Plugins/AgentBridge/Schemas/examples -name "*.json" | sort >> /tmp/schemas.txt
wc -l /tmp/schemas.txt
```

Expected: 64 行

- [ ] **Step 3: 逐文件 jq 读 keys**

写脚本 `/tmp/schema_keys.py`:
```python
import json, glob
for path in sorted(glob.glob('Plugins/AgentBridge/Schemas/**/*.json', recursive=True)):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    props = d.get('properties', {}) or d.get('definitions', {})
    keys = ', '.join(list(props.keys())[:8]) + ('...' if len(props) > 8 else '')
    print(f"{path} | {keys}")
```

Run:
```bash
python /tmp/schema_keys.py > /tmp/schema_keys.txt
```

- [ ] **Step 4: 逐行填表**

每个 Schema 5 字段:
- 文件: 相对 `Plugins/AgentBridge/Schemas/` 的路径
- 用途: 一句话(从 Schema 的 `$id` / `title` / `description` 抽取)
- 版本: Schema 内 `version` 字段或路径中的 `_v2` / `_v3` 后缀
- 引用方: grep 哪些代码或 Schema 引用这个文件
- 关键字段清单: Step 3 抓的 keys

- [ ] **Step 5: 末尾加门禁验证小节**

```markdown
## 行数自检
- 期望: 64 行(参 spec v1.1 §3.2)
- 当前: <jq 统计>
```

Run:
```bash
grep -c "^| " Docs/contracts/schemas_catalog.md
```

Expected: 64 (+ 表头 1 行 + 分隔行 1 行 = 实际 grep 出 66,扣表头与分隔)

- [ ] **Step 6: 同步 inventory + archive/README + Commit**

```bash
git add Docs/contracts/schemas_catalog.md
git commit -m "docs(restructure-ue57): Phase 1.3 — schemas_catalog.md

- 64 Schema 字段级索引,每行 5 字段完整"
```

---

### Task 1.4: contracts/mcp_tools_catalog.md(53 行 6 字段)

**Files:**
- Create: `Docs/contracts/mcp_tools_catalog.md`

- [ ] **Step 1: 起文件 + 元信息**

Create `Docs/contracts/mcp_tools_catalog.md`:
```markdown
# MCP Tools Catalog — 53 工具字段级签名表

> 版本: v1.0
> 验收门禁: 53 行 + 每行 6 字段完整(工具名 / 类别 / 输入 Schema / 输出 Schema / 错误码 / 使用场景)

## 主表
| 工具名 | 类别 | 输入 Schema | 输出 Schema | 错误码 | 使用场景 |
|--------|------|-------------|-------------|--------|----------|
```

- [ ] **Step 2: 提取 MCP 工具注册清单**

Read `Plugins/AgentBridge/MCP/server.py` + `compiler_tools.py` + `evidence_tools.py` + `tool_definitions.py`,逐个工具记录:
- `@mcp.tool(...)` 装饰器或 `register_tool(...)` 调用
- 工具名(snake_case)
- 输入参数(对应 Schema 文件)
- 返回结构(对应 Schema 文件)

- [ ] **Step 3: 按 4 大类填表**

类别值:`Bridge` / `前端` / `后端` / `alias`

Expected 总数:53 行
- Bridge 28
- 前端 10
- 后端 11
- alias 4

- [ ] **Step 4: 每行 6 字段完整性自检**

Run:
```bash
awk -F'|' 'NF != 8 && /^\|/ && !/^\| 工具名/ && !/^\| ---/ {print NR": "$0}' Docs/contracts/mcp_tools_catalog.md
```

Expected: 空(每行都是 6 字段 → 7 个 `|` 分隔符 → awk NF=8)

- [ ] **Step 5: Commit**

```bash
git add Docs/contracts/mcp_tools_catalog.md
git commit -m "docs(restructure-ue57): Phase 1.4 — mcp_tools_catalog.md

- 53 工具字段级签名表(28 Bridge + 10 前端 + 11 后端 + 4 alias)
- 每行 6 字段完整"
```

---

### Task 1.5: requirements/SRS.md

**Files:**
- Create: `Docs/requirements/SRS.md`
- Read(消化源): Docs/Current/01_Project_Baseline.md / 02_Current_Phase_Goals.md / 14_MCP_Cognitive_Bridge_Anchor.md / 15_Skill_Spec_Handoff_Chain.md / 18_Phase11_Closeout.md / README.md(项目层) + Plugins/AgentBridge/Docs/feedback_interface_catalog.md / architecture_overview.md

- [ ] **Step 1: 起文件 + 元信息 + 大纲**

Create `Docs/requirements/SRS.md`,完整复制 spec v1.1 §4.1 大纲(0-8 章 + 附录)。

- [ ] **Step 2: 写 Section 0-1**(元信息、范围)

- [ ] **Step 3: 写 Section 2 系统总体概览**(短,链回 HLD)

- [ ] **Step 4: 写 Section 3 模块功能需求**

按 7 个模块小节(3.1-3.7)逐个写。每个模块小节模板:
```markdown
### 3.X <模块名> [F-XXX-*]

- **用途**: 一句话
- **对外接口**: 关键类/函数/工具列表(列名即可)
- **功能列表**: F-XXX-01 / F-XXX-02 / ...(引用 FEATURE_INVENTORY)
- **数据契约**: → contracts/{schemas_catalog.md / tool_contract.md / field_specification.md} 对应行
- **测试覆盖**: → testing/test_spec.md §X.Y
- **详细实现**: → design/LLD/0X_<module>.md
- **UE 5.7 迁移记号**: 引用 scan spec UE57-BC-NNN ID 列表
```

- [ ] **Step 5: 写 Section 4 端到端链路**

4.1-4.5 子节。从 15_Skill_Spec_Handoff_Chain.md / 16_MCP_Repositioning_Plan.md / phase11_feature_coverage_report.md 消化。

- [ ] **Step 6: 写 Section 5 数据契约总览**

短,主要是链回 contracts/ 4 份。

- [ ] **Step 7: 写 Section 6 非功能需求 / Section 7 外部接口**

- [ ] **Step 8: 写 Section 8 UE 5.7 迁移说明汇总**

从 scan spec 抽汇总。

- [ ] **Step 9: 写附录(术语表 / 旧→新简表)**

- [ ] **Step 10: 字数自检**

Run:
```bash
wc -w Docs/requirements/SRS.md
```

Expected: 6000-8000 字(参 spec v1.1 §4.1 目标)

- [ ] **Step 11: F-* ID 双向引用自检**

Run:
```bash
# SRS 中提到的 F-* ID 都必须在 FEATURE_INVENTORY 找到
grep -oE "F-[A-Z]+-[0-9]+" Docs/requirements/SRS.md | sort -u > /tmp/srs_ids.txt
grep -oE "F-[A-Z]+-[0-9]+" Docs/FEATURE_INVENTORY.md | sort -u > /tmp/inv_ids.txt
diff /tmp/srs_ids.txt /tmp/inv_ids.txt | grep "^<" && echo "SRS 中 F-* ID 缺失 inventory 中"
```

Expected: 空

- [ ] **Step 12: 同步 inventory CSV(SRS 锚点回填)+ archive/README.md + Commit**

```bash
git add Docs/requirements/SRS.md \
        Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv \
        Docs/archive/README.md \
        Docs/FEATURE_INVENTORY.md
git commit -m "docs(restructure-ue57): Phase 1.5 — requirements/SRS.md

- 单文件 SRS,8 章 + 附录,6000-8000 字
- 消化 ~10 份旧文档(Current 01/02/14/15/18 + Plugins/Docs 4 份)
- F-* ID 双向引用通过"
```

---

### Task 1.6: design/HLD.md

**Files:**
- Create: `Docs/design/HLD.md`
- Read(消化源): Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md / 15_Skill_Spec_Handoff_Chain.md / 16_MCP_Repositioning_Plan.md / 17_Phase10_Closeout.md / 18_Phase11_Closeout.md + Plugins/AgentBridge/Docs/architecture_overview.md / run_isolation_compare_promote.md / skill_graph_and_domain_skill.md / design_space_discovery.md / clarification_gate_rules.md / constraint_variant_policy.md / baseline_realization_policy.md / universal_baseline_standard.md / root_skill_contract_standard.md / agent_interaction_protocol.md

- [ ] **Step 1-10: 按通用模板,逐章节(1-9)写**

参照 spec v1.1 §4.2 大纲。每章节消化对应的旧文档源:
- §1 架构总览 ← architecture_overview.md
- §2 7 阶段主链 ← 15_Skill_Spec_Handoff_Chain.md + root_skill_contract_standard.md + clarification_gate_rules.md + skill_graph_and_domain_skill.md + agent_interaction_protocol.md
- §3 Run 治理 ← run_isolation_compare_promote.md + 18_Phase11_Closeout.md
- §4 工具体系架构 ← tool_contract.md(新) + 14_MCP_Cognitive_Bridge_Anchor.md
- §5 Schema 与契约架构 ← schemas_catalog.md(新)
- §6 测试架构 ← Plugins/AgentBridge/Tests/SystemTestCases.md
- §7 跨切面 ← naming_resolution_log.schema + design_decision_log.schema
- §8 ADR(从 Docs/Decisions/ 抽,若有)
- §9 UE 5.7 影响 ← scan spec

字数目标 4000-5000。

- [ ] **Step 11: 双向引用自检 + inventory 同步 + archive 同步 + Commit**

---

### Task 1.7-1.13: design/LLD/01-07_*.md(7 个模块 LLD)

每个 LLD 模块文件按相同模板,所以这里把 7 个任务的步骤合并描述,实施时**每个 LLD 文件独立一个任务,各跑一遍完整步骤 + commit**。

#### LLD 模块统一格式

```markdown
## 模块概述
## 内部分层
## 关键类/函数签名(可粘贴到 IDE 检索)
## 数据流
## 扩展点
## 已知约束与陷阱
## UE 5.7 迁移变更点(具体到方法签名级)
```

#### Task 1.7: LLD/01_cpp_subsystem.md

**Files:**
- Create: `Docs/design/LLD/01_cpp_subsystem.md`
- Read: Plugins/AgentBridge/Source/AgentBridge/{Public,Private}/*.h *.cpp(5 + 5 个文件)

**消化要点**:
- 5 个核心类(AgentBridgeSubsystem / AgentBridgeCommandlet / UATRunner / AutomationDriverAdapter / BridgeTypes)
- 每个类的关键方法签名(grep `^void\|^bool\|^TArray\|^FString` 等返回类型)
- UE 5.7 迁移点引用 scan spec C++ 代码层条目

步骤同 Task 1.5 通用模板。Commit message: `docs(restructure-ue57): Phase 1.7 — LLD/01_cpp_subsystem.md`

#### Task 1.8: LLD/02_bridge.md

**Files:**
- Create: `Docs/design/LLD/02_bridge.md`
- Read: Plugins/AgentBridge/Scripts/bridge/*.py(9 个文件)

**消化要点**:
- 9 个 Python 模块,逐模块写 "Module / Key Functions / Dependencies"
- L1 查询 12 工具、L1 写 4 工具、L1 反馈 7 工具的函数级签名
- 与 RC HTTP 通信调用栈
- UE 5.7 迁移点引用 scan spec Python / Remote Control 类条目

#### Task 1.9: LLD/03_orchestrator.md

**Files:**
- Create: `Docs/design/LLD/03_orchestrator.md`
- Read: Plugins/AgentBridge/Scripts/orchestrator/*.py(11 个文件)

**消化要点**:
- 11 个 Orchestrator 模块,逐模块写
- Plan / Verifier / Reporter 的状态机
- ForgeUE manifest importer 的契约
- Handoff Runner 与 Run Plan 的关系

#### Task 1.10: LLD/04_compiler.md

**Files:**
- Create: `Docs/design/LLD/04_compiler.md`
- Read: Plugins/AgentBridge/Scripts/compiler/*.py(15 个) + Plugins/AgentBridge/Compiler/**/*.py(高阶 pipeline + 9 Stage)

**消化要点**:
- Scripts/compiler 15 模块的 5 子目录(analysis / generation / handoff / intake / routing / review)
- Plugins/.../Compiler 高阶 pipeline_orchestrator + 9 Stage(root_skill_contract / clarification_gate / discovery_fallback / realization_fallback / convergence_fallback / agent_protocol / llm_client / handoff_v3 / cross_review_v2 / lowering_v2 / domain_skill_runtime / skill_graph_planning)
- 跨模块组件(cross_review / lowering / planner / skill_runtime)
- 这是最大的 LLD 文件,字数可能 5000+

#### Task 1.11: LLD/05_mcp_server.md

**Files:**
- Create: `Docs/design/LLD/05_mcp_server.md`
- Read: Plugins/AgentBridge/MCP/*.py(7 个文件)

**消化要点**:
- server.py 工具注册机制
- py_channel / rc_channel 双通道
- 4 类工具 dispatcher 实现细节
- 链接到 contracts/mcp_tools_catalog.md(不复述 53 工具)

#### Task 1.12: LLD/06_skills_and_templates.md

**Files:**
- Create: `Docs/design/LLD/06_skills_and_templates.md`
- Read: Plugins/AgentBridge/SkillTemplates/baseline/* + genre_packs/boardgame/monopoly_like/* + Plugins/AgentBridge/Docs/skill_graph_and_domain_skill.md + baseline_realization_policy.md

**消化要点**:
- SkillGraph 数据结构(节点/边/生命周期)
- Domain Skill Runtime 四重职责
- Baseline / GamePlay Skill 同构
- 12 Skill / 72 模板文件结构(每个 Skill 6 文件)

#### Task 1.13: LLD/07_runtime_and_evidence.md

**Files:**
- Create: `Docs/design/LLD/07_runtime_and_evidence.md`
- Read: Plugins/AgentBridge/Tests/run_system_tests.py + ProjectState/ 顶层目录结构 + Docs/Current/07_Evidence_And_Artifacts.md

**消化要点**:
- UE 关卡引导(Editor game + Standalone staged)
- Evidence 落盘规则
- Reports 生成流程
- Run Workspace 隔离实现

---

### Task 1.14: design/LLD/README.md(LLD 入口)

**Files:**
- Create: `Docs/design/LLD/README.md`

- [ ] **Step 1: 起文件**

```markdown
# Detailed Design (LLD) — 入口与导航

> 7 模块 LLD,与 HLD 配套使用

## 模块导航

| 模块 | LLD 文件 | SRS 对应 |
|------|----------|----------|
| C++ 编辑器子系统 | [01_cpp_subsystem.md](./01_cpp_subsystem.md) | SRS §3.1 |
| Bridge 工具体系 | [02_bridge.md](./02_bridge.md) | SRS §3.2 |
| Orchestrator | [03_orchestrator.md](./03_orchestrator.md) | SRS §3.3 |
| Compiler | [04_compiler.md](./04_compiler.md) | SRS §3.4 |
| MCP Server | [05_mcp_server.md](./05_mcp_server.md) | SRS §3.5 |
| Skill & Template 体系 | [06_skills_and_templates.md](./06_skills_and_templates.md) | SRS §3.6 |
| 运行时与证据 | [07_runtime_and_evidence.md](./07_runtime_and_evidence.md) | SRS §3.7 |

## LLD 文件统一格式

每个模块文件包含:
1. 模块概述
2. 内部分层
3. 关键类/函数签名(IDE 可检索)
4. 数据流
5. 扩展点
6. 已知约束与陷阱
7. UE 5.7 迁移变更点(方法签名级)

## UE 5.7 迁移记号汇总
→ 见 SRS §8 / scan spec
```

- [ ] **Step 2: Commit**

---

### Task 1.15: testing/test_spec.md

**Files:**
- Create: `Docs/testing/test_spec.md`
- Read: Plugins/AgentBridge/Tests/SystemTestCases.md + Plugins/AgentBridge/AgentBridgeTests/*.cpp + Plugins/AgentBridge/Tests/*.py

- [ ] **Step 1-9: 按通用模板写**

参 spec v1.1 §4.4 大纲(7 章),消化 SystemTestCases.md 266 行用例。每个测试用例 5 字段:
- ID(SV-01 / Q-04 / W-15 等)
- 测试目标
- 入口脚本(run_system_tests.py 选项 / pytest 路径 / Automation Spec 路径)
- 期望结果
- 当前状态(pass/fail/skip,从最近一次 ProjectState/Reports/ 抓)

- [ ] **Step 10: 自检 266 行 + 5 字段**

```bash
awk -F'|' 'NF != 7 && /^\| [A-Z]+-[0-9]+/ {print NR": "$0}' Docs/testing/test_spec.md
```

Expected: 空

- [ ] **Step 11: Commit**

---

### Task 1.16: acceptance/acceptance_report.md

**Files:**
- Create: `Docs/acceptance/acceptance_report.md`
- Read: ProjectState/Reports/2026-04-17/task15_phase11_final_acceptance.md + phase11_feature_coverage_report.md + Docs/Current/18_Phase11_Closeout.md

- [ ] **Step 1-9: 按 spec v1.1 §4.5 大纲**

4 章:
1. Phase 11 as-is 验收基线(从 task15 + phase11_coverage 消化,**只搬结论行,不搬 evidence 详情**)
2. 验收门禁清单
3. UE 5.7 重构验收模板(空模板,留给未来填)
4. 防遗漏 checklist(逐 F-* ID 勾选)

- [ ] **Step 10: Commit**

---

### Task 1.17: governance.md

**Files:**
- Create: `Docs/governance.md`
- Read: AGENTS.md §3 / CLAUDE.md / .claude/skills/document-release/SKILL.md / Scripts/hooks/

- [ ] **Step 1-7: 按 spec v1.1 §4.8 大纲(6 章)**

不复述 AGENTS.md / CLAUDE.md 的规则,只索引指向(governance.md 是入口型文档,正文应该短)。

- [ ] **Step 8: Commit**

---

### Task 1.18: FEATURE_INVENTORY 锚点回填

**Files:**
- Modify: `Docs/FEATURE_INVENTORY.md`(逐行把 `主文档锚点 TBD` 改为实际 anchor)

- [ ] **Step 1: 逐 F-* ID grep**

写脚本 `/tmp/inventory_anchor_fill.py`:
```python
import re
from pathlib import Path

inv = Path('Docs/FEATURE_INVENTORY.md').read_text(encoding='utf-8')
# 提取所有 F-* ID
ids = re.findall(r'F-[A-Z]+-\d+', inv)
print(f"Inventory 有 {len(ids)} 个 F-* ID")

# 对每个 ID,grep 所有新文档,找命中位置
for fid in sorted(set(ids)):
    locations = []
    for p in Path('Docs').rglob('*.md'):
        if 'archive' in p.parts or 'superpowers' in p.parts:
            continue
        content = p.read_text(encoding='utf-8')
        if fid in content:
            # 找行号
            for i, line in enumerate(content.split('\n'), 1):
                if fid in line:
                    locations.append(f"{p}#L{i}")
                    break
    print(f"{fid}: {' / '.join(locations) or 'MISSING'}")
```

Run:
```bash
python /tmp/inventory_anchor_fill.py > /tmp/anchor_map.txt
cat /tmp/anchor_map.txt | grep MISSING
```

Expected: 空(每个 F-* ID 都能在至少 1 处新文档找到)

- [ ] **Step 2: 手工把 anchor_map.txt 的输出粘到 FEATURE_INVENTORY 对应行的"主文档锚点"列**

- [ ] **Step 3: UE 5.7 状态列回填**

从 scan spec §3 表 + `linked_F_id` 列,把每个 F-* ID 对应的 UE 5.7 状态(unchanged / migration / deprecated / new)填入 FEATURE_INVENTORY。

- [ ] **Step 4: 自检无 TBD**

```bash
grep -n "TBD\|tbd" Docs/FEATURE_INVENTORY.md
```

Expected: 空(若有,定位并实地化)

- [ ] **Step 5: Commit**

```bash
git add Docs/FEATURE_INVENTORY.md
git commit -m "docs(restructure-ue57): Phase 1.18 — FEATURE_INVENTORY 锚点 + UE 5.7 状态回填

- 所有 F-* ID 主文档锚点实地化
- UE 5.7 状态列从 scan spec 回链"
```

---

### Task 1.19: INDEX.md

**Files:**
- Create: `Docs/INDEX.md`

- [ ] **Step 1: 起文件**

按 spec v1.1 §4.7 大纲(7 章)。

- [ ] **Step 2: 写权威定义点索引**

```markdown
## 5. 权威定义点索引

| 硬事实 | 权威文档 |
|--------|----------|
| 53 MCP 工具 | contracts/mcp_tools_catalog.md |
| 64 Schema | contracts/schemas_catalog.md |
| 266 测试用例 | testing/test_spec.md |
| 7 阶段主链 | requirements/SRS.md §4.1 |
| Run 治理(run_id/fast_mode/promote) | requirements/SRS.md §4.3 / design/HLD.md §3 |
| Schema --strict 26/26 | testing/test_spec.md §5 |
| UE 引擎目标版本 | requirements/SRS.md §1.2 |
| 项目层 + 插件层分层 | design/HLD.md §1.1 |
```

- [ ] **Step 3: 写文档导航树(所有 Docs/ 文件清单 + 一句话)**

- [ ] **Step 4: 写阅读顺序**

- [ ] **Step 5: Commit**

---

## Phase 2: 校验门禁

### Task 2.1: 写 feature_inventory_check.py

**Files:**
- Create: `Scripts/validation/feature_inventory_check.py`

- [ ] **Step 1: 起脚本骨架**

Create `Scripts/validation/feature_inventory_check.py`:
```python
"""
Mvpv4TestCodex 文档重组验收门禁 — 多源交叉校验脚本

关联 spec: Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md v1.1 §8

校验项:
1. FEATURE_INVENTORY 中所有 F-* ID 锚点非 TBD
2. 每个 F-* ID 在 SRS/LLD 能 grep 到
3. mcp_tools_catalog 53 行 + 每行 6 字段
4. schemas_catalog 64 行 + 每行 5 字段
5. test_spec 266 行 + 每行 5 字段
6. 公开符号(C++ class / Py def / @mcp.tool)被引用
7. inventory CSV 中所有 need-consume 已实地化
8. redirects.json 与 inventory 一致
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DOCS = ROOT / 'Docs'

errors = []
warnings = []

def check_inventory_no_tbd():
    """检查 1: FEATURE_INVENTORY 无 TBD"""
    p = DOCS / 'FEATURE_INVENTORY.md'
    content = p.read_text(encoding='utf-8')
    for i, line in enumerate(content.split('\n'), 1):
        if 'TBD' in line or 'tbd' in line:
            errors.append(f"[FEATURE_INVENTORY:L{i}] 发现 TBD: {line.strip()}")

def check_inventory_ids_referenced():
    """检查 2: 每个 F-* ID 在 SRS/LLD 能 grep 到"""
    inv = (DOCS / 'FEATURE_INVENTORY.md').read_text(encoding='utf-8')
    ids = set(re.findall(r'F-[A-Z]+-\d+', inv))
    for fid in sorted(ids):
        found = False
        for p in DOCS.rglob('*.md'):
            if 'archive' in p.parts or 'superpowers' in p.parts or p.name == 'FEATURE_INVENTORY.md':
                continue
            if fid in p.read_text(encoding='utf-8'):
                found = True
                break
        if not found:
            errors.append(f"[Inventory] F-* ID 未在新文档找到引用: {fid}")

def check_mcp_catalog():
    """检查 3: mcp_tools_catalog 53 行 + 6 字段"""
    p = DOCS / 'contracts' / 'mcp_tools_catalog.md'
    rows = [l for l in p.read_text(encoding='utf-8').split('\n') if l.startswith('|') and '工具名' not in l and '---' not in l]
    if len(rows) != 53:
        errors.append(f"[mcp_tools_catalog] 期望 53 行,实际 {len(rows)}")
    for i, r in enumerate(rows):
        cols = r.split('|')
        if len(cols) != 8:  # 6 字段 → 7 个分隔符 + 头尾 = 8
            errors.append(f"[mcp_tools_catalog:L{i}] 字段数 != 6: {r[:80]}")

def check_schemas_catalog():
    """检查 4: schemas_catalog 64 行 + 5 字段"""
    p = DOCS / 'contracts' / 'schemas_catalog.md'
    rows = [l for l in p.read_text(encoding='utf-8').split('\n') if l.startswith('|') and '文件' not in l and '---' not in l]
    if len(rows) != 64:
        errors.append(f"[schemas_catalog] 期望 64 行,实际 {len(rows)}")
    for i, r in enumerate(rows):
        cols = r.split('|')
        if len(cols) != 7:
            errors.append(f"[schemas_catalog:L{i}] 字段数 != 5: {r[:80]}")

def check_test_spec():
    """检查 5: test_spec 266 行 + 5 字段"""
    p = DOCS / 'testing' / 'test_spec.md'
    rows = [l for l in p.read_text(encoding='utf-8').split('\n') if re.match(r'^\| [A-Z]+-\d+', l)]
    if len(rows) != 266:
        errors.append(f"[test_spec] 期望 266 行,实际 {len(rows)}")
    for i, r in enumerate(rows):
        cols = r.split('|')
        if len(cols) != 7:
            errors.append(f"[test_spec:L{i}] 字段数 != 5: {r[:80]}")

def check_public_symbols():
    """检查 6: 公开符号被引用 — C++ class / Py def / @mcp.tool"""
    # C++ classes in Plugins/AgentBridge/Source/
    plugin_src = ROOT / 'Plugins' / 'AgentBridge' / 'Source'
    symbols = []
    for cpp in plugin_src.rglob('*.h'):
        for line in cpp.read_text(encoding='utf-8').split('\n'):
            m = re.match(r'^\s*class\s+(\w+_API\s+)?([UFI]\w+)', line)
            if m:
                symbols.append(m.group(2))
    # Python @mcp.tool 注册
    mcp_dir = ROOT / 'Plugins' / 'AgentBridge' / 'MCP'
    for py in mcp_dir.glob('*.py'):
        for line in py.read_text(encoding='utf-8').split('\n'):
            m = re.search(r'@mcp\.tool\([^)]*name=["\'](\w+)', line)
            if m:
                symbols.append(m.group(1))

    # 每个符号必须在新文档(SRS/LLD/contracts)被引用
    all_new_doc = ''
    for p in DOCS.rglob('*.md'):
        if 'archive' in p.parts or 'superpowers' in p.parts:
            continue
        all_new_doc += p.read_text(encoding='utf-8')
    for sym in set(symbols):
        if sym not in all_new_doc:
            errors.append(f"[符号未引用] {sym} 在新文档中没有提及")

def check_inventory_csv():
    """检查 7: inventory CSV 中所有 need-consume 已实地化"""
    import csv
    p = DOCS / 'superpowers' / 'specs' / '2026-05-26-old-docs-inventory.csv'
    with p.open(encoding='utf-8') as f:
        for i, row in enumerate(csv.DictReader(f), 2):
            if row['status'] == 'need-consume':
                if row['planned_new_anchor'].startswith('Planned:'):
                    errors.append(f"[inventory:L{i}] need-consume 行未实地化: {row['old_path']}")

def check_redirects():
    """检查 8: redirects.json 与 inventory 一致"""
    import csv
    redirects = json.loads((DOCS / 'redirects.json').read_text(encoding='utf-8'))
    inv_paths = set()
    p = DOCS / 'superpowers' / 'specs' / '2026-05-26-old-docs-inventory.csv'
    with p.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            inv_paths.add(row['old_path'])
    for old in redirects:
        if old not in inv_paths:
            errors.append(f"[redirects] 路径未在 inventory: {old}")
    for old in inv_paths:
        if old not in redirects:
            warnings.append(f"[redirects] inventory 路径未在 redirects: {old}")

def main():
    checks = [
        ('FEATURE_INVENTORY 无 TBD', check_inventory_no_tbd),
        ('F-* ID 在新文档被引用', check_inventory_ids_referenced),
        ('mcp_tools_catalog 53 行 + 6 字段', check_mcp_catalog),
        ('schemas_catalog 64 行 + 5 字段', check_schemas_catalog),
        ('test_spec 266 行 + 5 字段', check_test_spec),
        ('公开符号被引用', check_public_symbols),
        ('inventory CSV need-consume 实地化', check_inventory_csv),
        ('redirects.json 与 inventory 一致', check_redirects),
    ]
    for name, fn in checks:
        try:
            fn()
            print(f"✅ {name}")
        except Exception as e:
            print(f"💥 {name} 异常: {e}")

    print(f"\n错误: {len(errors)}")
    for e in errors:
        print(f"  ❌ {e}")
    print(f"\n警告: {len(warnings)}")
    for w in warnings:
        print(f"  ⚠️  {w}")

    sys.exit(1 if errors else 0)

if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 跑脚本看是否能正常运行**

Run:
```bash
python Scripts/validation/feature_inventory_check.py
```

Expected: 8 个检查全跑过,错误为 0(若有错误,回 Phase 1 修)

- [ ] **Step 3: Commit**

```bash
git add Scripts/validation/feature_inventory_check.py
git commit -m "docs(restructure-ue57): Phase 2.1 — feature_inventory_check.py

- 8 项校验(无 TBD / F-* 被引用 / catalog 字段级完整 / 符号引用 / inventory + redirects 一致性)"
```

---

### Task 2.2: 链接预校验

**Files:**
- Modify (optional): `Scripts/validation/feature_inventory_check.py`(可扩展)
- Create: `/tmp/phase4_rewrite_list.txt`(Phase 4 的重写清单)

- [ ] **Step 1: 全仓 grep markdown 链接**

Run:
```bash
grep -rEn "\(/?D:/UnrealProjects/Mvpv4TestCodex/Docs/(Current|History|Decisions|Proposals|superpowers)/" \
  --include="*.md" --include="*.py" --include="*.json" \
  . > /tmp/all_old_links.txt
grep -rEn "Plugins/AgentBridge/Docs/" \
  --include="*.md" --include="*.py" --include="*.json" \
  . > /tmp/all_plugin_doc_links.txt
wc -l /tmp/all_old_links.txt /tmp/all_plugin_doc_links.txt
```

- [ ] **Step 2: 用 redirects.json 验证每个链接能找到目标**

写脚本 `/tmp/validate_links.py`:
```python
import json, re
from pathlib import Path

redirects = json.loads(Path('Docs/redirects.json').read_text(encoding='utf-8'))
unmapped = []
with open('/tmp/all_old_links.txt', encoding='utf-8') as f:
    for line in f:
        m = re.search(r'(Docs/(Current|History|Decisions|Proposals|superpowers)/[^\)\s]+)', line)
        if m:
            old = m.group(1).rstrip(')')
            # 转换成 inventory 路径形式
            if old not in redirects:
                unmapped.append((line.strip(), old))

if unmapped:
    print(f"❌ {len(unmapped)} 条链接未在 redirects.json 找到:")
    for line, old in unmapped[:20]:
        print(f"  - {old}")
        print(f"    @ {line[:120]}")
else:
    print(f"✅ 所有旧链接都在 redirects.json 有映射")
```

Run:
```bash
python /tmp/validate_links.py
```

Expected: ✅(若有未映射,补到 inventory CSV + redirects.json,回 Phase 0)

- [ ] **Step 3: 产出 Phase 4 重写清单**

Run:
```bash
cat /tmp/all_old_links.txt /tmp/all_plugin_doc_links.txt | cut -d: -f1 | sort -u > /tmp/phase4_rewrite_list.txt
wc -l /tmp/phase4_rewrite_list.txt
```

Expected: ~20-50 文件(AGENTS / CLAUDE / README / task.md / Plugins/.../README / Plugins/.../AGENTS / .claude/skills/* / .agents/skills/* / Scripts/hooks/* / Docs/superpowers/specs|plans/*)

- [ ] **Step 4: Commit(无文件变更,只跑校验)**

无 commit(校验通过即可,有错回 Phase 1)。

---

### Task 2.3: 人工 checklist 准备

**Files:**
- Modify: `Docs/acceptance/acceptance_report.md`(加 §4 全量勾选清单)

- [ ] **Step 1: 在 acceptance_report.md §4 写全量 checklist**

```markdown
## 4. 防遗漏 checklist(msc 全量勾选)

按 FEATURE_INVENTORY 中每个 F-* ID 逐个勾选:

- [ ] F-CPP-01 AgentBridgeSubsystem — 已在 SRS §3.1 / LLD/01 / 测试覆盖 X 验证
- [ ] F-CPP-02 UATRunner — ...
- [ ] ... (~80-100 行)

按 mcp_tools_catalog 每个工具勾选:

- [ ] mcp_tool: list_level_actors — Bridge 类,catalog 6 字段完整
- [ ] mcp_tool: spawn_actor — ...
- [ ] ... (53 行)

按 schemas_catalog 每个 Schema 勾选:

- [ ] Schema: root_skill_contract.schema.json — 5 字段完整
- [ ] ... (64 行)
```

- [ ] **Step 2: msc 手过(实施时由 msc 实际勾选)**

- [ ] **Step 3: Commit**

```bash
git add Docs/acceptance/acceptance_report.md
git commit -m "docs(restructure-ue57): Phase 2.3 — 人工 checklist 就绪

- F-* / MCP / Schema 三类逐项勾选位"
```

---

## Phase 3: archive 搬迁

### Task 3.1: 搬 Docs/Current → archive/current

- [ ] **Step 1: git mv**

Run:
```bash
git mv Docs/Current Docs/archive/current
git status
```

Expected: 17 份文件 + 任何子目录全部 renamed → `archive/current/`

- [ ] **Step 2: Commit**

```bash
git commit -m "docs(restructure-ue57): Phase 3.1 — git mv Docs/Current → archive/current"
```

---

### Task 3.2: 搬 Docs/History → archive/history

- [ ] **Step 1: git mv**

Run:
```bash
git mv Docs/History Docs/archive/history
git status
```

- [ ] **Step 2: Commit**

```bash
git commit -m "docs(restructure-ue57): Phase 3.2 — git mv Docs/History → archive/history"
```

---

### Task 3.3: 搬 Docs/Decisions / Proposals / superpowers

- [ ] **Step 1: git mv 三个目录**

Run:
```bash
[ -d Docs/Decisions ] && git mv Docs/Decisions Docs/archive/decisions
[ -d Docs/Proposals ] && git mv Docs/Proposals Docs/archive/proposals
# superpowers 保留 specs/2026-05-26-* 与 plans/2026-05-26-* (本工作产物)
# 把 superpowers/specs/ 下其他文件移到 archive,本批 spec 保留
# 步骤(谨慎):
mkdir -p Docs/archive/superpowers/specs Docs/archive/superpowers/plans
for f in Docs/superpowers/specs/*.md; do
  name=$(basename "$f")
  case "$name" in
    2026-05-26-docs-restructure-for-ue57.md) ;;       # 保留
    2026-05-26-old-docs-inventory.csv) ;;             # 保留
    2026-05-26-ue57-breaking-changes-scan.md) ;;      # 保留
    *) git mv "$f" "Docs/archive/superpowers/specs/$name" ;;
  esac
done
for f in Docs/superpowers/plans/*.md; do
  name=$(basename "$f")
  case "$name" in
    2026-05-26-docs-restructure-for-ue57.md) ;;       # 保留(本 plan)
    *) git mv "$f" "Docs/archive/superpowers/plans/$name" ;;
  esac
done
```

- [ ] **Step 2: Commit**

```bash
git commit -m "docs(restructure-ue57): Phase 3.3 — git mv Decisions/Proposals/superpowers → archive/

- superpowers/specs|plans/ 保留 2026-05-26-* 本工作产物"
```

---

### Task 3.4: Plugins/AgentBridge/Docs 抽取后搬到 archive/plugins

- [ ] **Step 1: 校验已被消化的 30 份**

```bash
ls Plugins/AgentBridge/Docs/*.md | wc -l
# 检查 inventory CSV 中 30 份的 status 都是 already-consumed
python -c "
import csv
with open('Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv', encoding='utf-8') as f:
    rows = [r for r in csv.DictReader(f) if r['old_path'].startswith('Plugins/AgentBridge/Docs/')]
for r in rows:
    if r['status'] not in ('already-consumed', 'archive-only'):
        print(f'❌ {r[\"old_path\"]}: status={r[\"status\"]}')
"
```

Expected: 空

- [ ] **Step 2: git mv 到 archive/plugins/**

Run:
```bash
mkdir -p Docs/archive/plugins
for f in Plugins/AgentBridge/Docs/*.md; do
  name=$(basename "$f")
  if [ "$name" != "README.md" ]; then
    git mv "$f" "Docs/archive/plugins/$name"
  fi
done
git status
```

Expected: 30 份(除 README.md)renamed

- [ ] **Step 3: Commit**

```bash
git commit -m "docs(restructure-ue57): Phase 3.4 — Plugins/AgentBridge/Docs 30 份搬到 archive/plugins"
```

---

### Task 3.5: Plugins/AgentBridge/Docs 原位置写 redirect stub

**Files:**
- Create: `Plugins/AgentBridge/Docs/<原文件名>.md` × 30(stub)
- Modify: `Plugins/AgentBridge/Docs/README.md`(stub 索引)

- [ ] **Step 1: 用 redirects.json 自动生成 stub**

写脚本 `/tmp/gen_stubs.py`:
```python
import json
from pathlib import Path

redirects = json.loads(Path('Docs/redirects.json').read_text(encoding='utf-8'))
stub_dir = Path('Plugins/AgentBridge/Docs')

template = """# [Deprecated] {title}

此文档已迁移到新文档体系。请查看:

- **权威新归宿**: [{new_path}](/D:/UnrealProjects/Mvpv4TestCodex/{new_path})
- **历史原版**: [archive/plugins/{filename}](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/plugins/{filename})
- **统一入口**: [Docs/INDEX.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/INDEX.md)

> 重定向源: `Docs/redirects.json`
"""

for old_path, new_anchor in redirects.items():
    if not old_path.startswith('Plugins/AgentBridge/Docs/'):
        continue
    filename = Path(old_path).name
    if filename == 'README.md':
        continue
    title = filename.replace('_', ' ').replace('.md', '').title()
    stub = template.format(title=title, new_path=new_anchor, filename=filename)
    out = stub_dir / filename
    out.write_text(stub, encoding='utf-8')
    print(f"✍️  写 stub: {out}")
```

Run:
```bash
python /tmp/gen_stubs.py
ls Plugins/AgentBridge/Docs/*.md | wc -l
```

Expected: 30 stub + 1 README = 31

- [ ] **Step 2: 更新 Plugins/AgentBridge/Docs/README.md**

Modify:
```markdown
# AgentBridge Docs — Deprecated 目录

> 本目录的所有原始内容已整合到主文档体系 `Docs/`,各文件保留 redirect stub 兜底深链。
> 主入口: [Docs/INDEX.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/INDEX.md)

## 30 份 stub 索引

| 原文件 | 新归宿 |
|--------|--------|
| architecture_overview.md | design/HLD.md §1-2 |
| tool_contract_v0_1.md | contracts/tool_contract.md |
| ...(自动从 redirects.json 生成,完整 30 行)... |
```

可以用 Python 一次性生成这个表:
```python
import json
from pathlib import Path
redirects = json.loads(Path('Docs/redirects.json').read_text(encoding='utf-8'))
for old, new in redirects.items():
    if old.startswith('Plugins/AgentBridge/Docs/'):
        print(f"| {Path(old).name} | {new} |")
```

- [ ] **Step 3: git add stub + README**

```bash
git add Plugins/AgentBridge/Docs/
git commit -m "docs(restructure-ue57): Phase 3.5 — Plugins/AgentBridge/Docs 30 stub 兜底

- 每旧文件保留同名 stub 指向新归宿
- README.md 改为 stub 索引"
```

---

### Task 3.6: archive/README.md 实地化

**Files:**
- Modify: `Docs/archive/README.md`(把所有 `Planned: ...` 改为已落地路径)

- [ ] **Step 1: 跑校验**

```bash
grep "Planned:" Docs/archive/README.md
```

Expected: 空(若有,逐行实地化到真实新归宿)

- [ ] **Step 2: 同步 inventory CSV 状态**

```bash
grep "Planned:" Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv
```

Expected: 空(若有,Phase 1 漏更新,补)

- [ ] **Step 3: Commit**

```bash
git add Docs/archive/README.md Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv
git commit -m "docs(restructure-ue57): Phase 3.6 — archive/README + inventory CSV 实地化

- 所有 Planned: 改为实际新归宿路径"
```

---

## Phase 4: 链接重写

### Task 4.1: 自动批量重写

**Files:**
- Modify: `/tmp/phase4_rewrite_list.txt` 中列出的所有文件(预期 ~20-50 份)

- [ ] **Step 1: 写自动重写脚本**

Create `/tmp/apply_redirects.py`:
```python
import json
import sys
from pathlib import Path

redirects = json.loads(Path('Docs/redirects.json').read_text(encoding='utf-8'))

# 排除 archive/ 内部 + redirects.json 本身 + inventory CSV
EXCLUDE_PREFIXES = ('Docs/archive/', 'Docs/redirects.json', 'Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv')

# 待重写的文件清单(来自 phase4_rewrite_list.txt)
with open('/tmp/phase4_rewrite_list.txt', encoding='utf-8') as f:
    files = [l.strip() for l in f if l.strip()]

for fp in files:
    p = Path(fp)
    if any(str(p).startswith(e) for e in EXCLUDE_PREFIXES):
        continue
    if not p.exists():
        continue
    content = p.read_text(encoding='utf-8')
    changed = False
    for old, new in redirects.items():
        # 多种路径形式都要替换:
        # 1. (/D:/UnrealProjects/Mvpv4TestCodex/<old>)
        # 2. (<old>)
        # 3. `<old>`
        for fmt in [
            f"/D:/UnrealProjects/Mvpv4TestCodex/{old}",
            old,
        ]:
            if fmt in content:
                content = content.replace(fmt, new if not new.startswith('Docs/') else f"/D:/UnrealProjects/Mvpv4TestCodex/{new}")
                changed = True
    if changed:
        p.write_text(content, encoding='utf-8')
        print(f"✍️  重写: {p}")
```

Run:
```bash
python /tmp/apply_redirects.py
```

- [ ] **Step 2: 人工检查 diff**

```bash
git diff --stat
git diff AGENTS.md CLAUDE.md README.md task.md
```

人工确认链接重写正确,无误覆盖。

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md CLAUDE.md README.md task.md \
        Plugins/AgentBridge/README.md Plugins/AgentBridge/AGENTS.md \
        .claude/skills/document-release/SKILL.md \
        .agents/skills/document-release/SKILL.md \
        Scripts/hooks/doc_release_gate.py \
        Docs/superpowers/specs/ Docs/superpowers/plans/
git commit -m "docs(restructure-ue57): Phase 4.1 — 链接批量重写

- 全仓 AGENTS/CLAUDE/README/task/SKILL 等 ~20-50 文件
- 自动用 redirects.json 映射"
```

---

### Task 4.2: 同步 .claude / .agents skills

**Files:**
- Modify: `.claude/skills/document-release/SKILL.md`
- Modify: `.agents/skills/document-release/SKILL.md`

- [ ] **Step 1: 跑 sync_skills.py**

Run:
```bash
python Scripts/hooks/sync_skills.py
```

Expected: 两个 SKILL.md 一致(从 canonical 同步到副本)

- [ ] **Step 2: Commit(若有差异)**

```bash
git diff .claude/skills/document-release/SKILL.md .agents/skills/document-release/SKILL.md
git add .claude/skills/document-release/SKILL.md .agents/skills/document-release/SKILL.md
git commit -m "docs(restructure-ue57): Phase 4.2 — sync .claude/.agents document-release skill" || echo "无差异,跳过"
```

---

### Task 4.3: 最终 grep 0 残留校验

- [ ] **Step 1: 全仓 grep 旧路径前缀(排除 archive/)**

Run:
```bash
grep -rEn "Docs/(Current|History|Decisions|Proposals)/" \
  --include="*.md" --include="*.py" --include="*.json" \
  . --exclude-dir=archive --exclude-dir=Saved --exclude-dir=Intermediate \
  > /tmp/residual_links.txt
wc -l /tmp/residual_links.txt
```

Expected: 0 行(若 archive/README.md 或 inventory CSV 有引用是允许的,因为它们是描述性引用,但应该已经被 EXCLUDE_PREFIXES 排除)

- [ ] **Step 2: 单独检查 Plugins/AgentBridge/Docs/(stub 例外)**

```bash
grep -rEn "Plugins/AgentBridge/Docs/" \
  --include="*.md" --include="*.py" --include="*.json" \
  . --exclude-dir=archive --exclude-dir=Saved --exclude-dir=Intermediate \
  > /tmp/plugin_doc_residual.txt
# 期望: 只有 Plugins/AgentBridge/Docs/ 下的 stub 文件自身(指向 archive/plugins),其余 0
grep -v "Plugins/AgentBridge/Docs/.*\.md:" /tmp/plugin_doc_residual.txt
```

Expected: 空

- [ ] **Step 3: 跑 feature_inventory_check.py 完整校验**

```bash
python Scripts/validation/feature_inventory_check.py
```

Expected: 8 项全 ✅,错误 0

- [ ] **Step 4: Commit(若有清理)**

```bash
git status
# 若 Step 1/2 grep 命中,定位并清理,re-commit
```

---

### Task 4.4: document-release 收尾门禁

- [ ] **Step 1: 跑 document-release skill**

调用 `document-release` skill(本项目本地 skill)。预期 skill 会自动检查:
- 五件套 / contracts / governance 已落盘
- INDEX / FEATURE_INVENTORY 已落盘
- archive/README 反向映射完整
- AGENTS.md / CLAUDE.md / README.md / task.md 链接重写完成
- ProjectState/Reports 落证(可选,如有最终验收报告)

实际命令:
```bash
# 通过 skill 入口调用
# (Claude Code: 调用 Skill(document-release);命令行 hook 自动触发)
```

- [ ] **Step 2: 若 hook 拦截,按提示修复**

document-release 会生成 marker 文件到 `ProjectState/Reports/<today>/doc_release/`。检查 marker 内容是否完整。

- [ ] **Step 3: Commit(若 skill 产生 marker)**

```bash
git add ProjectState/Reports/
git commit -m "docs(restructure-ue57): Phase 4.4 — document-release 门禁通过"
```

---

### Task 4.5: superpowers:finishing-a-development-branch

- [ ] **Step 1: 跑 finishing skill**

调用 `superpowers:finishing-a-development-branch`。它会引导:
- 检查所有任务完成
- 选择 merge / PR / cleanup
- 创建最终 PR 或 merge

---

## 完成定义(链回 spec v1.1 §8 验收门禁)

整个 plan 完成的判定:

- [ ] FEATURE_INVENTORY 矩阵填实,无 TBD,grep 脚本通过
- [ ] 五件套(SRS / HLD / LLD/{README+7} / test_spec / acceptance_report)全部产出
- [ ] contracts/(4 份)+ governance.md + INDEX.md 产出
- [ ] 每个 F-* ID 在主文档能 grep 到具体描述段落
- [ ] contracts/mcp_tools_catalog 53 行 + 每行 6 字段完整
- [ ] contracts/schemas_catalog 64 行 + 每行 5 字段完整
- [ ] testing/test_spec 266 行 + 每行 5 字段
- [ ] 代码内每个公开符号(C++ class / Py def / @mcp.tool)被引用
- [ ] inventory CSV 列全 ~80 份,所有 need-consume 已实地化
- [ ] redirects.json 列全 + Phase 4 grep 校验通过
- [ ] archive/README 反向映射无 `Planned: TBD` 残留
- [ ] Plugins/AgentBridge/Docs 30 份保留 stub 指向新归宿
- [ ] UE 5.7 scan spec 完成,FEATURE_INVENTORY 状态列全填实
- [ ] 链接重写完成,archive/ 之外 0 残留(stub 除外)
- [ ] feature_inventory_check.py 8 项全 ✅
- [ ] document-release skill 跑过
- [ ] msc 全量勾选 acceptance_report §4 checklist

---

## Execution Handoff(将在编完此 plan 后由 writing-plans skill 询问)

**Plan complete and saved to** `Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — 每任务派 fresh subagent,任务间复审,迭代快
2. **Inline Execution** — 当前会话内顺序执行,checkpoints 复审

Which approach?
