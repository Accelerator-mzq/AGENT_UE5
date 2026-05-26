# Docs Restructure for UE 5.7 Refactor — Design Spec

> 文档版本: v1.1
> 日期: 2026-05-26
> 作者: Claude Code (msc 主导决断)
> 类型: superpowers spec (brainstorming 阶段产物)
> 后续: 通过 `superpowers:writing-plans` 生成 implementation plan
>
> **修订记录**
> - v1.1 (2026-05-26): 按 Codex 对抗性审查全收修订:
>   - 收紧验收门禁: 文件/家族/字数级 → 符号/工具/字段/用例级双向 traceability (§1.4/§3.2/§8)
>   - 旧文档清单 + archive/README v1 反向映射前移到 Phase 0,解除 Phase 2/3 死锁 (§6)
>   - UE 5.7 扫描范围扩到项目层 Source/Blueprint/资产/Config/Build/Plugin 依赖,产出格式加 URL/置信度/误报状态/验证命令/复核人 (§7)
>   - 新增 `redirects.json` 机器可读旧→新路径映射,Phase 4 grep 校验覆盖所有被搬迁路径 (§6/§8)
>   - 插件 Docs 抽取后,原位置每个旧文件保留 redirect stub,避免深链断 (§5.2)
> - v1.0 (2026-05-26): 初版

---

## 0. 目的与场景

将 Mvpv4TestCodex 项目当前(Phase 11 已完成口径,UE 5.5.4)所有功能,整合为一套统一的 `Docs/` 文档结构,**用作 UE 5.7 重构的输入规格**。

**核心约束(msc 反复强调)**:
1. **不能遗漏功能** — 这是首要约束,所有设计决策围绕这一点
2. **不是机械搬运** — 需要对项目整体理解后整合,不复制粘贴
3. **去除冗余** — 同一事实在新文档中只声明一次,跨文档引用而非复述
4. **as-is 主 + to-be 补** — 主体写当前 UE 5.5.4 事实,每模块底部加 UE 5.7 迁移记号

**目标读者**:
- 主读者: UE 5.7 重构开发者(可能是未来的 msc 自己 / Claude Code / Codex / 其他 Agent)
- 次读者: 任何接手本项目的 Agent

---

## 1. 已确认前提(brainstorming 阶段决断,不再回退)

### 1.1 范围: 项目层 + 插件层全量

- 新 `Docs/` 覆盖项目层(Docs/Current/History/Decisions/Proposals/superpowers + 顶层 anchor) **以及**插件层 `Plugins/AgentBridge/Docs/` 30 份
- `Plugins/AgentBridge/Schemas/` 本体不动(契约文件,留在原位),只在 `Docs/contracts/schemas_catalog.md` 索引
- `ProjectState/` 不动
- 项目根 `README/AGENTS/CLAUDE/task.md` 四个 anchor 不动,只更新链接

**与 2026-05-26 旧 memory 冲突说明**: memory `project_docs_restructure_deferred.md` 中"插件层 Plugins/AgentBridge/Docs (30 份) 与 Schemas (40+) 不动"前提**已废除**。Schemas 仍不动(只索引),但 Plugins/.../Docs 30 份要被消化到新文档,原位置抽取后清空(留 README 指针)。

### 1.2 大小写: 保留大写 `Docs/`

- 与 AGENTS/CLAUDE/README/task.md 已有的硬编码路径完全兼容
- 零链接重写(只在内容层面更新,不动目录名)

### 1.3 Fidelity: as-is 主 + to-be 补

- 主体写当前 UE 5.5.4 已实现事实
- 每个模块/章节末尾加 `## UE 5.7 Migration Notes` 子节,标注 deprecated/migration/unchanged/new
- to-be 部分等 **Phase 0 UE 5.7 breaking change 扫描** 完成后填实

### 1.4 验收: 多源交叉矩阵 + 半自动 grep + 人工 checklist 双重门禁

- `Docs/FEATURE_INVENTORY.md` 作为单点验收底座
- **门禁强度: 符号/工具/字段/用例级的双向 traceability**(不是文件/家族/字数级,Codex 对抗审已驳回粗粒度门禁)
- 半自动: Python 脚本扫代码符号 + Schema 字段 + MCP 工具签名 + 测试用例,与 FEATURE_INVENTORY + contracts/* + test_spec 对账
- 人工: `acceptance/acceptance_report.md` 末尾 checklist,**全量勾选**(非抽样),msc 审
- 机器可读路径映射: `Docs/redirects.json` 由 Phase 0.4 产出,Phase 2 用它校验全仓 markdown 链接命中率

### 1.5 FEATURE_INVENTORY 粒度: 工具家族,53 详情扔 catalog

- FEATURE_INVENTORY 每行 = 一个原子功能或工具家族(~80-150 行)
- "工具家族"划分规则: 按 `mcp_tools_catalog.md` 的 4 大类别(28 Bridge + 10 前端 + 11 后端 + 4 alias)再细分到 ~10 个语义家族(例: Bridge L1 查询族 / L1 写族 / L1 反馈族 / L3 UI 族 / 前端 Stage 1-3 族 / 后端 Run 治理族 / 后端 Evidence 族 等)
- **粒度分层规则**: FEATURE_INVENTORY 走家族粒度只是 inventory 层面;contracts/mcp_tools_catalog.md 必须**每工具 1 行 + 完整字段签名**(工具名/类别/输入 Schema/输出 Schema/错误码/使用场景);schemas_catalog.md 必须每 Schema 1 行 + 5 字段;test_spec.md 必须每用例 1 行 + 5 字段。粗粒度只用于"模块视角",细粒度由 catalog 层兜底
- 53 个 MCP 工具详情归 `contracts/mcp_tools_catalog.md`
- 64 个 Schema 归 `contracts/schemas_catalog.md`
- 266 条测试用例归 `testing/test_spec.md`

### 1.6 UE 5.7 状态填表前置: 必须先扫描

- 在写 FEATURE_INVENTORY 的"UE 5.7 状态"列前,必须完成 Phase 0 breaking change 扫描
- 扫描产出: `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`(单独 spec)

---

## 2. 顶层目录结构

```
Docs/
├── INDEX.md                              # 入口 · 阅读顺序 · 版本号 · 旧→新映射快速跳转
├── FEATURE_INVENTORY.md                  # ★ 多源交叉矩阵 = 验收底座
├── governance.md                         # 文档治理 · document-release · hooks · 信任分层
├── requirements/
│   └── SRS.md                            # 系统功能"做什么" · 单文件 · 6000-8000 字
├── design/
│   ├── HLD.md                            # 架构"怎么分层" · 单文件 · 4000-5000 字
│   └── LLD/                              # 详细实现"怎么实现" · 按模块拆
│       ├── README.md                     # LLD 总入口与索引
│       ├── 01_cpp_subsystem.md
│       ├── 02_bridge.md
│       ├── 03_orchestrator.md
│       ├── 04_compiler.md
│       ├── 05_mcp_server.md
│       ├── 06_skills_and_templates.md
│       └── 07_runtime_and_evidence.md
├── testing/
│   └── test_spec.md                      # 测试体系与 266 条用例索引
├── acceptance/
│   └── acceptance_report.md              # Phase 11 验收基线 + UE 5.7 验收模板
├── contracts/
│   ├── schemas_catalog.md                # 64 个 Schema 索引
│   ├── mcp_tools_catalog.md              # 53 个 MCP 工具签名表
│   ├── tool_contract.md                  # L1/L2/L3 工具协议
│   └── field_specification.md            # 共享字段规范
└── archive/
    ├── README.md                         # ★ 旧→新反向映射主表
    ├── current/                          # 旧 Docs/Current 17 份原样搬入
    ├── history/                          # 旧 Docs/History 整树
    ├── proposals/                        # 旧 Docs/Proposals
    ├── decisions/                        # 旧 Docs/Decisions
    ├── superpowers/                      # 旧 Docs/superpowers/{specs,plans}
    └── plugins/                          # ★ 旧 Plugins/AgentBridge/Docs 30 份抽取后归档
```

**总文件数**: 五件套 + governance + contracts = **6 + 4 = 10 个核心权威文档**(SRS, HLD, LLD/{README+7}, test_spec, acceptance_report, governance, schemas_catalog, mcp_tools_catalog, tool_contract, field_specification)。

加 INDEX + FEATURE_INVENTORY + archive/README + LLD/README = 14 份索引/治理文档。

总计约 **22 份新文档**,替代原 ~50 份项目层文档 + 30 份插件层文档 = 80 份旧文档。

---

## 3. FEATURE_INVENTORY.md 设计

### 3.1 矩阵列定义

| 列 | 含义 | 校验规则 |
|----|------|----------|
| `ID` | 永久不变的稳定 ID,前缀: `CPP`/`BRG`/`ORC`/`CMP`/`MCP`/`SKL`/`RT`/`CHN`/`GOV`/`SCH` | 唯一 |
| `功能名` | 简短功能名 | 不超 50 字符 |
| `简述` | 一句话用途 | 不超 120 字符 |
| `模块归属` | 主模块 | 必须命中 SRS §3.X 之一 |
| `主文档锚点` | `SRS §3.X.Y / LLD/0X#LNN / HLD §Z` | 必须 grep 命中 |
| `证据源` | 代码文件 / Schema / 测试用例 / 旧文档 | 至少 1 个证据源 |
| `测试覆盖` | testing/test_spec.md 对应类(SV/Q/W/CL/UI/...) | 必填,可填"无" |
| `UE 5.7 状态` | `unchanged` / `migration` / `deprecated` / `new` | Phase 0 扫描后填 |

### 3.2 防遗漏的"多源交叉"门禁(符号/字段/用例级)

| 证据源 | 数量 | 存在性门禁 | **细粒度门禁(Codex 强化)** |
|--------|------|------------|------------------------------|
| 代码模块(C++ 10 + Bridge 9 + Orch 11 + Comp 34 + MCP 7) | 71 | 每文件至少被 1 个 F-* 引用 | 每个 **公开符号(类/函数/MCP 工具)** 至少被 1 个 F-* 或 catalog 行引用;扫描时遍历 .h/.cpp 中 `class U*/F*`、Python 中 `def `、MCP server 中 `@mcp.tool` |
| MCP 工具 | 53 | catalog 53 行 | 每行 **6 字段完整**(工具名 / 类别 / 输入 Schema / 输出 Schema / 错误码 / 使用场景);缺任一字段视为该行不合规 |
| Schema | 64 | catalog 64 行 | 每行 **5 字段完整**(文件 / 用途 / 版本 / 引用方 / 关键字段清单);"关键字段清单"要列出 Schema 顶层 properties keys |
| 测试用例 | 266 | test_spec 266 行 | 每行 **5 字段**(ID / 测试目标 / 入口脚本 / 期望结果 / 当前状态 pass/fail/skip);状态来自最近一次系统测试报告 |
| Skill 模板 | 12 Skill / 72 文件 | F-SKL-* 至少覆盖每个 Skill | 每个 Skill 6 文件齐全(manifest / system / domain / evaluator / input_selector / output_schema);grep 校验 |
| phase11_feature_coverage_report 内 15 文档 | 15 | 每份对应功能在 FEATURE_INVENTORY ≥ 1 行 | 每份的"新增功能"小节列出的功能点逐条命中 F-* ID |
| 旧文档总集(~80 份) | ~80 | 每份在 archive/README.md 有归宿 | 每份在 `Docs/redirects.json` 有 old→new 映射条目(机器可读);archive 后无外部断链 |
| `redirects.json` | n/a | 文件存在 | 全仓 markdown 链接 grep 后,所有指向 archive 前路径的链接都能在 redirects.json 找到映射目标 |

### 3.3 反向去重机制

旧文档同一事实多处重复(例如 "53 工具" 在 README/Index/Closeout/AGENTS 都出现) → 新文档处理:

- **唯一权威位置**: 选最权威/最新的文档作为定义点(例如 `contracts/mcp_tools_catalog.md` 是 "53 工具" 的唯一定义点)
- 其他文档**只引用,不复述** — INDEX/SRS/HLD 提到时写 "详见 contracts/mcp_tools_catalog.md"
- archive/README.md 反向映射表标注: `README.md(旧)中的"53 工具"声明 → contracts/mcp_tools_catalog.md`(已被吸收)
- 过时的 / 与现状冲突的内容(如旧 planning 中的 "50 工具") → **不进新文档**,在 archive/README.md 注 `deprecated`
- **权威定义点索引**: `INDEX.md` 维护"硬事实 → 权威文档"映射表,例如 `53 工具 → contracts/mcp_tools_catalog.md`、`7 阶段主链 → SRS §4.1`、`Schema --strict 26/26 → testing/test_spec.md §5`。任何引用这些硬事实的位置都必须链回权威定义点,不复述数字

---

## 4. 五件套大纲

### 4.1 requirements/SRS.md (单文件 ~6000-8000 字)

只写"做什么",不写"怎么做"。每个模块小节用统一模板。

```
0. 文档元信息
1. 项目定位与范围
   1.1 项目定位
   1.2 目标引擎版本(UE 5.5.4 → 5.7)
   1.3 文档覆盖范围(项目层 + 插件层全量)
   1.4 阅读顺序

2. 系统总体概览(短,详见 HLD)
   2.1 双层架构(项目层 + 插件层)
   2.2 核心链路一图
   2.3 工具体系层级 L1/L2/L3
   2.4 三层信任(L0/L1 当前 / L2 Canonical / L3-L5 历史)

3. 模块功能需求(核心)
   3.1 C++ 编辑器子系统       [F-CPP-*]
   3.2 Bridge 工具体系         [F-BRG-*]
   3.3 Orchestrator           [F-ORC-*]
   3.4 Compiler               [F-CMP-*]
   3.5 MCP Server             [F-MCP-*]
   3.6 Skill & Template 体系   [F-SKL-*]
   3.7 运行时与证据           [F-RT-*]

4. 端到端链路(横切)
   4.1 7 阶段主链 v2          [F-CHN-*]
   4.2 Stage 4 三路生成策略    [F-CHN-S4-*]
   4.3 Run 治理               [F-GOV-*]
   4.4 模式路由(Greenfield / Brownfield / Playable Runtime)
   4.5 Clarification + Constraint/Variant 决策

5. 数据契约总览
   5.1 Schema 体系(链回 contracts/schemas_catalog.md)
   5.2 MCP 工具体系(链回 contracts/mcp_tools_catalog.md)
   5.3 Reviewed Handoff 主契约(v1/v2/v3 演进与当前权威版本)
   5.4 共享字段规范(链回 contracts/field_specification.md)

6. 非功能需求
   6.1 校验强度(Schema --strict 26/26, SystemTest 266)
   6.2 命名规范(GDD-First, UE5 路径, naming_resolution_log)
   6.3 可观测性(Evidence/Reports/Snapshots)
   6.4 文档治理(链回 governance.md)
   6.5 安全/边界

7. 外部接口
   7.1 Remote Control HTTP API(端口 30010)
   7.2 UAT CLI
   7.3 MCP stdio 协议
   7.4 Agent 接入面(Claude Code / Codex / Gemini)

8. UE 5.7 迁移说明(汇总)
   8.1 Breaking change 总览表(由 Phase 0 扫描产出)
   8.2 按模块迁移要点

附录
  A. 术语表(Skill / Spec / Handoff / Run / Stage / Domain / Provider 等)
  B. 与旧文档映射(简表,详表→ archive/README.md)
```

**模块小节统一模板(3.1-3.7 都按这个写)**:

```markdown
### 3.X <模块名> [F-XXX-*]

- **用途**: 一句话
- **对外接口**: 关键类/函数/工具列表(列名即可,不列签名)
- **功能列表**: 引用 FEATURE_INVENTORY F-XXX-* 行(不复述详情)
- **数据契约**: 链回 contracts/{schemas,tool_contract,field_specification}
- **测试覆盖**: 链回 testing/test_spec.md §X.Y(对应测试类)
- **详细实现**: → design/LLD/0X_<module>.md
- **UE 5.7 迁移记号**: (Phase 0 扫描后填实)
```

### 4.2 design/HLD.md (单文件 ~4000-5000 字)

```
1. 架构总览
   1.1 双层架构图
   1.2 进程拓扑(UE Editor / Bridge / MCP Server / Agent)
   1.3 数据流总图(GDD → ... → Evidence)
2. 核心链路 v2 架构
   2.1 7 Stage 拓扑(每 Stage 输入/输出契约简述)
   2.2 Stage 4 三路生成策略架构
   2.3 v1/v2 session 共存与路由
3. Run 治理架构
4. 工具体系架构(L1/L2/L3 + 4 通道)
5. Schema 与契约架构(v1→v2→v3 演进策略)
6. 测试架构
7. 跨切面(命名解析、决策日志、错误处理、可观测性)
8. 关键 ADR(从 Docs/Decisions/ 抽取,若有保留价值)
9. UE 5.7 架构迁移影响
```

### 4.3 design/LLD/

```
LLD/
├── README.md                     # 7 模块导航与版本号
├── 01_cpp_subsystem.md           # Subsystem/Commandlet/UATRunner/AutomationDriver 类图、关键方法签名、扩展点
├── 02_bridge.md                  # 9 Python 模块、L1 查询/写/反馈接口逐个签名、RC HTTP 调用栈
├── 03_orchestrator.md            # 11 Orchestrator 模块、Plan/Verifier/Reporter 状态机、ForgeUE importer
├── 04_compiler.md                # Scripts/compiler(15) + Plugins/.../Compiler(高阶 9 Stage)
├── 05_mcp_server.md              # server.py 工具注册、py_channel/rc_channel、4 类工具 dispatcher
├── 06_skills_and_templates.md    # SkillGraph 数据结构、Domain Skill Runtime、Skill 模板 6 文件结构
└── 07_runtime_and_evidence.md    # UE 关卡引导、Evidence 落盘、Reports 生成、Run Workspace
```

每个 LLD 模块文件统一格式:

```markdown
## 模块概述
## 内部分层
## 关键类/函数签名(可粘贴到 IDE 检索)
## 数据流
## 扩展点
## 已知约束与陷阱
## UE 5.7 迁移变更点(具体到方法签名级)
```

### 4.4 testing/test_spec.md

```
1. 测试体系架构(C++ Automation / Python pytest / Gauntlet / SystemTest 索引层)
2. 测试分层(单元 / 集成 / E2E / 回归)
3. 系统测试用例总表(266 条,按 16 类逐类索引)
   - 每类: 用例 ID 范围 / 测试目标 / 入口脚本 / 期望结果
4. 关键测试入口(run_system_tests.py 模式、--interactive/--no-editor、Stage 14a)
5. Schema 严格校验(validate_examples.py --strict 26/26 的具体覆盖映射)
6. CI/Gauntlet(AgentBridgeGauntletController 接入)
7. UE 5.7 测试迁移(Automation Framework / pytest 兼容性扫描)
```

### 4.5 acceptance/acceptance_report.md

```
1. Phase 11 as-is 验收基线
   逐项搬入 task15_phase11_final_acceptance + phase11_feature_coverage_report 的结论行
   (这是 acceptance,不是 evidence — evidence 留在 ProjectState/Reports 原地)
2. 验收门禁清单
   - Schema --strict 26/26
   - SystemTest 266 条结果
   - UE 运行时 Editor + Standalone 双路径
   - MCP 工具注册数 53
3. UE 5.7 重构验收模板(空模板,等重构完成后填)
4. 防遗漏 checklist
   人工对账 FEATURE_INVENTORY 中每个 F-* ID 已被验收覆盖
```

### 4.6 contracts/

```
contracts/
├── schemas_catalog.md       # 64 行表:文件名 | 用途 | 版本 | 引用方
├── mcp_tools_catalog.md     # 53 行表:工具名 | 类别 | 输入/输出 Schema | 使用场景
├── tool_contract.md         # 抽取自 Plugins/.../Docs/tool_contract_v0_1.md
└── field_specification.md   # 抽取自 Plugins/.../Docs/field_specification_v0_1.md
```

### 4.7 INDEX.md (顶层入口)

```
1. 文档版本与日期
2. 项目状态一句话(Phase 11 已完成 / UE 5.5.4 → 5.7 重构进行中)
3. 阅读顺序(给新接手 Agent / 开发者)
4. 文档导航树(展开 Docs/ 全目录,每个文件一句话用途)
5. 权威定义点索引(硬事实 → 权威文档映射表)
6. 旧→新跳转快查(常见 5-10 份旧文档的新归宿,详表→ archive/README.md)
7. 常用命令(从旧 README.md 搬迁)
```

### 4.8 governance.md (顶层,与五件套并列)

```
1. 文档生产规则
   1.1 document-release 强制门禁(git pre-commit/pre-push + Claude Code/Codex hook)
   1.2 trivial 路径白名单 / [skip-doc] / --no-verify 三种逃生
   1.3 .claude/skills/document-release/SKILL.md + .agents/skills/.../SKILL.md 双路径同步
2. 文档信任分层(L0/L1 当前 / L2 Canonical / L3-L5 历史)
3. 阶段切换信号
4. Agent 行为规则索引(链回 AGENTS.md / CLAUDE.md,不复述)
5. Git hooks 一览(链回 Scripts/hooks/)
6. 项目根目录的 anchor 文件契约(README/AGENTS/CLAUDE/task.md 不动)
```

---

## 5. archive/ 归档与"旧→新"映射

### 5.1 archive/README.md(反向映射主表)

每一份旧文档都必须在表里有一行,标注归宿。即使是"仅作历史保留"也要标注。

**机器可读对应物**: `Docs/redirects.json` 同步维护,格式 `{ "old/path.md": "new/path.md#section" }`,作为 Phase 4 grep 自动重写的字典源。

**完整 Docs/Current 17 份归宿示例**(spec 中给出全部以避免后续遗漏):

```markdown
| 旧路径 | 内容主题 | 新归宿 | 状态 |
|--------|----------|--------|------|
| `Docs/Current/00_Index.md` | 当前阶段索引 | `INDEX.md`(全替换) | 已消化 |
| `Docs/Current/01_Project_Baseline.md` | Phase 11 基线 | `requirements/SRS.md §1` + `acceptance/acceptance_report.md §1` | 已消化 |
| `Docs/Current/02_Current_Phase_Goals.md` | 阶段目标完成状态 | `acceptance/acceptance_report.md §1` | 已消化 |
| `Docs/Current/03_Active_Backlog.md` | 活动 backlog(已转追溯) | `acceptance/acceptance_report.md §1.附` | archive-only |
| `Docs/Current/04_Open_Risks.md` | 风险记录(追溯) | `archive/current/04_Open_Risks.md` | archive-only |
| `Docs/Current/05_Implementation_Boundary.md` | 实施边界 | `requirements/SRS.md §6.5` + `governance.md §6` | 已消化 |
| `Docs/Current/06_Current_Task_List.md` | 当前任务入口 | `INDEX.md §3` | 已消化 |
| `Docs/Current/07_Evidence_And_Artifacts.md` | Evidence 落盘规则 | `requirements/SRS.md §6.3` + `governance.md §1` | 已消化 |
| `Docs/Current/08_Phase8_Retrospective.md` | Phase 8 复盘 | `archive/current/08_*.md` | archive-only |
| `Docs/Current/10_Phase8_Closeout.md` | Phase 8 收尾 | `archive/current/10_*.md` | archive-only |
| `Docs/Current/11_Phase9_Closeout.md` | Phase 9 收尾 | `archive/current/11_*.md` | archive-only |
| `Docs/Current/12_MCP_Repositioning.md` | MCP 重定位背景 | `archive/current/12_*.md` | archive-only |
| `Docs/Current/14_MCP_Cognitive_Bridge_Anchor.md` | MCP 总口径 | `design/HLD.md §4` + `requirements/SRS.md §3.5` | 已消化 |
| `Docs/Current/15_Skill_Spec_Handoff_Chain.md` | 4 层主链 | `requirements/SRS.md §4` + `design/HLD.md §2` | 已消化 |
| `Docs/Current/16_MCP_Repositioning_Plan.md` | MCP 重定位方案 v3 | `design/HLD.md §4` + `archive/current/16_*.md` | 部分消化 + 归档 |
| `Docs/Current/17_Phase10_Closeout.md` | Phase 10 收尾 | `archive/current/17_*.md` | archive-only |
| `Docs/Current/18_Phase11_Closeout.md` | Phase 11 收尾 | `acceptance/acceptance_report.md §1` | 已消化 |
```

`Docs/History` 整树:每个 `Tasks/task*.md` / `Proposals/*.md` / `Phase11_Design_Pack/*.md` 必须在 `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv`(Phase 0.1 强制产出)中有一行。`Docs/Decisions/`、`Docs/Proposals/`、`Docs/superpowers/{specs,plans}/` 同理。**spec 不在正文穷举,但 inventory CSV 必须穷举**。

插件 Docs 30 份示例:

```markdown
| 旧路径 | 内容主题 | 新归宿 | 状态 |
|--------|----------|--------|------|
| `Plugins/AgentBridge/Docs/architecture_overview.md` | 总体架构 | `design/HLD.md §1-2` | 已消化 |
| `Plugins/AgentBridge/Docs/tool_contract_v0_1.md` | L1/L2/L3 协议 | `contracts/tool_contract.md` | 抽取归档 |
| `Plugins/AgentBridge/Docs/field_specification_v0_1.md` | 字段规范 | `contracts/field_specification.md` | 抽取归档 |
| `Plugins/AgentBridge/Docs/feedback_interface_catalog.md` | 7 反馈接口 | `requirements/SRS.md §3.2` + `contracts/mcp_tools_catalog.md` | 已消化 |
| ... 完整列出 30 份 → 见 inventory CSV ... |
```

### 5.2 plugins/ 子目录的特殊处理(防深链断)

旧 `Plugins/AgentBridge/Docs/` 30 份处理规则:

- 已消化的: 抽取核心内容到 `Docs/contracts/` 或 `Docs/design/HLD/LLD/`,**原文件搬到 `Docs/archive/plugins/<原文件名>`**(保留路径名,git mv 保留 history)
- `Plugins/AgentBridge/Docs/` 原位置: **不简单清空**,每个旧文件保留一个 **redirect stub**(同名 `.md`),内容固定模板:

  ```markdown
  # [Deprecated] <原标题>

  此文档已迁移到新文档体系。请查看:
  - **权威新归宿**: [<新路径>](/D:/UnrealProjects/Mvpv4TestCodex/Docs/<...>)
  - **历史原版**: [archive/plugins/<原文件名>](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/plugins/<原文件名>)
  - **统一入口**: [Docs/INDEX.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/INDEX.md)

  > 重定向源: `Docs/redirects.json`
  ```

- redirect stub 文件比"清空 + 单一 README 指针"多 30 个文件,但**保证任何已有外部链接、IDE 跳转、AGENTS.md 残留引用、Codex/Claude Code 缓存中的旧路径都不会 404**
- 旧目录 `Plugins/AgentBridge/Docs/` 顶层 README 同步更新为 stub 索引,列出 30 个 stub + 新归宿对应表

---

## 6. 实施方法论(消化 + 去重 + 重组)

具体执行规则,落地到 implementation plan 时按下面 4 个 Phase 拆任务。

### Phase 0: 前置扫描 + 反向映射 v1

- **0.1 旧文档全清单 + archive/README v1 反向映射**(关键前移,解除 Phase 2/3 死锁)
  - Glob 所有 .md(项目层 ~50 + 插件层 30 = ~80 份)
  - 产出: `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv`
  - **同时产出 `Docs/archive/README.md` 反向映射 v1**(此时新文档还没写,新归宿先填 `Planned: <预期路径 + 章节>`,后续 Phase 1 写完后实地化)
  - CSV 列: `old_path | content_topic | status (already-consumed/need-consume/archive-only/deprecated) | planned_new_anchor | cross_refs_count | notes`
  - 列全所有: `Docs/Current/*` (17 份) / `Docs/History/Tasks/task*.md` / `Docs/History/Proposals/*.md` / `Docs/History/Phase11_Design_Pack/*.md` / `Docs/Decisions/*` / `Docs/Proposals/*` / `Docs/superpowers/{specs,plans}/*` / `Plugins/AgentBridge/Docs/*` (30 份)
- **0.2 UE 5.5.4 → 5.7 breaking change 扫描**(扫描范围与产出格式见 §7)
  - 产出: `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`
  - 扫描完成 → FEATURE_INVENTORY 的"UE 5.7 状态"列、SRS/LLD 的"迁移记号"才能填实
- **0.3 FEATURE_INVENTORY 第一版**
  - 填"模块归属 + 证据源",主文档锚点先标 `TBD`,等 Phase 1 写作完成后回填
- **0.4 redirects.json 初版**
  - 机器可读 `{ "old/path.md": "new/path.md#section" }`
  - 来源: `2026-05-26-old-docs-inventory.csv` 的 `planned_new_anchor` 列
  - 这份 JSON 是 Phase 2 链接校验脚本的字典,Phase 4 自动重写的源

**Phase 0 与 Phase 1 并行关系**: Phase 0.2(UE 5.7 扫描)与 Phase 1 的 SRS/HLD/LLD 主体撰写可以并行;**Phase 0.1 (inventory + archive/README v1) 是 Phase 1 与 Phase 2 的共同前置**,必须先做完。Phase 0.4 redirects.json 是 Phase 2/4 的前置。

### Phase 1: 写五件套 + governance + contracts(并行同步更新 inventory)

每份新文档按下面步骤:

- 1.1 起一份新文档,先写章节大纲(参照本 spec §4)
- 1.2 对每个章节,从旧文档证据源**摘取事实**,**用自己的话重写**(不复制粘贴)
- 1.3 同一事实多处出现 → 选最权威/最新的源消化,**inventory CSV 的 `planned_new_anchor` 列改为实际 anchor**;archive/README v1 同步更新
- 1.4 硬事实(数字、版本号、工具数等)在新文档**只声明一次**;`INDEX.md` 维护"权威定义点"索引表
- 1.5 过时 / 冲突内容 → 不进新文档,在 inventory CSV 注 `deprecated`,archive/README.md 同步标记
- 1.6 每完成一份新文档,跑 §6.Phase 2 的子集校验(对应章节是否已被 inventory 中所有 `need-consume` 行命中)

**推荐写作顺序**: contracts/ → SRS → HLD → LLD → test_spec → acceptance_report → governance → FEATURE_INVENTORY 回填锚点 → INDEX

**理由**: contracts/ 是机械可校验的契约表,先建立后,SRS/HLD/LLD 才能引用进去。

### Phase 2: 校验门禁(不依赖 Phase 3 产物)

- **2.1 写 grep 校验脚本**: `Scripts/validation/feature_inventory_check.py`
  - 遍历代码文件 + 文件内公开符号、Schema 文件 + 字段、MCP 工具 + 完整签名、测试用例 + 状态
  - 检查每一项是否在 FEATURE_INVENTORY 有 F-* ID,且锚点不为 TBD
  - 检查每个 F-* ID 是否在 SRS / LLD 找到锚点
  - 检查 inventory CSV 中每行 `status`,所有 `need-consume` 必须已被 `planned_new_anchor` 实地化
  - 检查 redirects.json 中每个 old_path 都能在 inventory CSV 找到对应行
  - 缺漏 → 报错列出"未归宿项"
- **2.2 链接预校验**(在 Phase 3 搬迁前跑)
  - 全仓 grep 所有 markdown 链接
  - 每个指向 inventory 中旧路径的链接,必须能在 redirects.json 找到映射目标
  - 失败项产生"Phase 4 重写清单"
- **2.3 人工 checklist**
  - acceptance_report.md §4 写 checklist
  - msc 全量勾选(非抽样)

### Phase 3: archive 搬迁(只搬,不写映射)

- 3.1 `git mv` 旧 `Docs/Current/`、`Docs/History/`、`Docs/Proposals/`、`Docs/Decisions/`、`Docs/superpowers/{specs,plans}/` 到 `Docs/archive/<对应子目录>/`(保留 git 历史)
- 3.2 抽取 `Plugins/.../Docs/` 30 份的核心内容到 contracts/SRS/HLD/LLD 后,`git mv` 原文件到 `Docs/archive/plugins/`
- 3.3 `Plugins/AgentBridge/Docs/` 原位置每个旧文件**保留 redirect stub**(见 §5.2),不简单清空
- 3.4 archive/README.md 从 Phase 0.1 / Phase 1 持续更新,这里只做"实地化检查"(把所有 `Planned: ...` 改为已落地的实际新路径)

### Phase 4: 链接重写(覆盖所有被搬迁路径)

- 4.1 grep 范围覆盖 inventory CSV 中**所有**旧路径前缀:
  - `Docs/Current/` / `Docs/History/` / `Docs/Decisions/` / `Docs/Proposals/` / `Docs/superpowers/{specs,plans}/`
  - `Plugins/AgentBridge/Docs/`(因为有 stub,这里只校验不重写)
- 4.2 用 `redirects.json` 自动批量重写,目标文件:
  - `AGENTS.md` / `CLAUDE.md` / `README.md` / `task.md`
  - `Plugins/AgentBridge/README.md` / `Plugins/AgentBridge/AGENTS.md`
  - `.claude/skills/document-release/SKILL.md` + `.agents/skills/document-release/SKILL.md`
  - `Docs/superpowers/specs/` 其他 spec / `Docs/superpowers/plans/`
  - `Scripts/hooks/doc_release_gate.py`(若有硬编码路径)
  - 任何 inventory 之外的项目内 markdown / 配置(grep 后人工裁决)
- 4.3 跑 document-release skill 同步(sync_skills.py)
- 4.4 提交前 grep 二次校验:
  - **范围**: `archive/` 之外的项目内文件
  - **目标**: 所有 inventory 中旧路径前缀
  - **预期**: 0 残留(archive 内部允许保留旧路径,因为是原样归档)
  - **stub 除外**: `Plugins/AgentBridge/Docs/*.md` 中的 redirect stub 本身指向新路径,不算残留

---

## 7. UE 5.7 breaking change 扫描范围与方法

(单独 spec: `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`)

扫描产出后回填到 FEATURE_INVENTORY 和 SRS/LLD 的"UE 5.7 迁移记号"。

### 7.1 扫描范围(覆盖项目层 + 插件层 + 资产 + 配置 + 构建,Codex 强化)

1. **C++ 代码层** — 扫描所有 .h/.cpp:
   - 项目层 `Source/Mvpv4TestCodex/`(若存在;UE 项目层 Source 可能为空或 minimal,先 ls 确认)
   - 插件层 `Plugins/AgentBridge/Source/`
   - 扫 UE API 符号: `UEditorSubsystem` / `UEditorAssetSubsystem` / `IAutomationLatentCommand` / `FAutomationTestBase` / `IRemoteControlModule` / `FRemoteControlField` / `UCommandlet` / `UFactory` / `FSlateApplication` / `IPluginManager` / `FModuleManager` / 其他 UE 模块依赖
2. **构建系统** — `*.Build.cs` / `*.Target.cs` / `*.uplugin` / `Source/*/*.uproject`
3. **资产层**(静态扫不能完全枚举,需 5.7 编辑器实测验证为辅) — Content/ 下 .uasset / .umap / Blueprint / DataAsset / Niagara / .uphysicsasset
4. **配置层** — `Config/*.ini`(DefaultEditor / DefaultEngine / DefaultGame / DefaultInput / 等);**不扫 `Saved/`、`Intermediate/`、`DerivedDataCache/`、`Binaries/`**
5. **Python Editor API** — `unreal` module binding 变化;`bridge_core.py`、`ue_helpers.py`、`uat_runner.py` 内 grep
6. **Remote Control 协议** — RC HTTP API 端点变更;`bridge_core.py` + `remote_control_client.py` 内 grep
7. **UAT / UBT 命令行** — `uat_runner.py` + `Scripts/validation/*.ps1` 内 grep
8. **Plugin 依赖** — `.uplugin` 中 Plugins 节,5.7 兼容性 / 是否 deprecated
9. **PowerShell / 项目脚本** — `Scripts/` 下硬编码 UE 版本/路径 (例如 `UE_5.5` / `Engine\Binaries\Win64`)

### 7.2 扫描产出格式(每条 breaking change 完整字段)

| 字段 | 内容 | 必填 | 备注 |
|------|------|------|------|
| `id` | `UE57-BC-NNN` 顺序编号 | ✅ | 稳定 ID |
| `api_or_key` | 完整符号名 / 配置 key / 资产路径 | ✅ | grep 锚点 |
| `category` | 1-9 类(C++ / 构建 / 资产 / 配置 / Python / RC / UAT / Plugin / Script) | ✅ | |
| `usage_in_5_5_4` | 当前调用方式或值 | ✅ | |
| `usage_in_5_7` | 迁移后调用方式或值 | ✅ | 来源未确认时填 `TBD` |
| `source_url` | UE 5.6/5.7 release notes / forum / API doc 链接 | ✅ | 无来源填 `inferred-from-grep` |
| `confidence` | `high` / `medium` / `low` | ✅ | 基于来源权威性;`inferred-from-grep` 默认 low |
| `impacted_files` | 项目内 grep 结果(文件 + 行号列表) | ✅ | 无影响项标 `none-found` |
| `migration_difficulty` | `low` / `medium` / `high` | ✅ | |
| `false_positive_status` | `confirmed` / `suspected` / `false-positive` | ✅ | Phase 0.2 末由 msc 人工裁决,false-positive 不进入迁移列表 |
| `validation_command` | 迁移后跑什么证明工作(如 `python Tests/test_xxx.py` / `RunUAT BuildEditor` / `5.7 编辑器手验`) | ✅ | |
| `reviewer` | msc / 其他 Agent / Codex | ✅ | 复核签名 |
| `linked_F_id` | 关联的 FEATURE_INVENTORY F-* ID(可多个) | 选填 | 多对多 |

### 7.3 误报与未覆盖的兜底

- `confidence: low` 且 `false_positive_status: suspected` 的项不进 SRS/LLD 迁移记号,只在 scan spec 的"待验证清单"区
- 静态扫无法覆盖的项(资产层、运行时行为):scan spec 末尾列"已扫范围 / 未覆盖范围",未覆盖项在 SRS/LLD 对应位置标 `TBD-need-runtime-validation`,留待 UE 5.7 实测填实

---

## 8. 验收门禁(本 spec 的"完成"定义,符号/字段/用例级)

整个文档重组工作"完成"的定义:

| 门禁项 | 验收方式 | 必须通过 |
|--------|----------|----------|
| FEATURE_INVENTORY 矩阵填实 | 所有 F-* ID 的"主文档锚点"非 TBD;grep 脚本通过(无未归宿项) | ✅ |
| 五件套(SRS/HLD/LLD/test_spec/acceptance_report)产出 | 文件存在 + **每个 F-* ID 在主文档能 grep 到具体描述段落**(不只字数) | ✅ |
| contracts/mcp_tools_catalog.md | 53 行 + 每行 6 字段完整(工具名/类别/输入 Schema/输出 Schema/错误码/使用场景) | ✅ |
| contracts/schemas_catalog.md | 64 行 + 每行 5 字段完整(文件/用途/版本/引用方/关键字段清单) | ✅ |
| contracts/tool_contract.md + field_specification.md | 内容从插件 Docs 抽取后字段无遗漏 | ✅ |
| testing/test_spec.md | 266 行 + 每行 5 字段(ID/目标/入口/期望/当前状态);状态来自最近一次 system test 报告 | ✅ |
| **公开符号 traceability** | 代码内每个 class/function/MCP tool/Schema 字段都被至少 1 个 F-* 或 catalog 行引用 | ✅ |
| `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv` | 列全 ~80 份旧文档;`status` 列对所有 `need-consume` 行,`planned_new_anchor` 已实地化 | ✅ |
| `Docs/redirects.json` | 列全 inventory CSV 所有 old→new 映射;Phase 4 grep 校验通过 | ✅ |
| governance.md / INDEX.md | 文件存在;INDEX 旧→新跳转链接全部命中(redirects.json 校验) | ✅ |
| archive/README.md 反向映射 | 旧文档每份在表里有归宿;无 `Planned: TBD` 残留 | ✅ |
| 插件 Docs redirect stubs | `Plugins/AgentBridge/Docs/*.md` 30 份保留 stub,每个指向新归宿(redirects.json 一致) | ✅ |
| Phase 0 UE 5.7 breaking change 扫描 | scan spec 产出;每条 12 字段完整;`false_positive_status: suspected` 已由 msc 人工裁决 | ✅ |
| FEATURE_INVENTORY 的 UE 5.7 状态列 | 全填实(不剩 TBD),`migration` 项已链回 scan spec 对应 `UE57-BC-NNN` ID | ✅ |
| 链接重写完成 | `archive/` 之外的项目内文件 grep inventory 中所有旧路径前缀,0 残留(stub 除外) | ✅ |
| document-release skill 跑过 | hook 通过 | ✅ |
| 人工 checklist | acceptance_report.md §4 由 msc **全量勾选**(非抽样) | ✅ |

---

## 9. 已知风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 旧文档实际 ~80 份,消化工作量大 | 实施周期延长 | 分批走:contracts 优先,SRS 次之,LLD 最后;每批走完一次 Phase 2 子集校验 |
| UE 5.7 release notes 信息不全 / 静态扫不能覆盖资产层运行时行为 | 扫描结果不完整,迁移记号填错 | scan spec 标"已扫范围 / 未覆盖范围";`false_positive_status` 字段过滤;未覆盖项 SRS/LLD 标 `TBD-need-runtime-validation` |
| FEATURE_INVENTORY 与新文档锚点的双向引用易出现 stale | grep 验收虽能查到但维护成本高 | grep 校验脚本作为 git pre-commit 入口,每次改 SRS/LLD 必须重跑 |
| `Plugins/AgentBridge/Docs/` 抽取后原文件搬走,可能破坏插件 AGENTS.md / IDE 跳转 / 外部缓存中的旧路径 | 插件层深链断裂 | 每个旧文件保留 redirect stub(§5.2),不简单清空;`redirects.json` 兜底 |
| msc 旧 memory 中"插件层 Docs 不动"前提冲突 | memory 误导未来对话 | 本 spec 通过后,清理 memory `project_docs_restructure_deferred.md` 中"插件层不动"的句子,更新为"已废除,改为全量重构" |
| Phase 2/3 顺序死锁(校验依赖 Phase 3 才有的 archive/README) | 阻塞实施 | **已修(v1.1)**: archive/README 反向映射 v1 前移到 Phase 0.1,Phase 2 只校验已有映射,Phase 3 只做搬迁 |
| 验收门禁过于粗(文件/家族/字数级,通过但功能可能遗漏) | "无遗漏"承诺不可信 | **已修(v1.1)**: §3.2/§8 升级到符号/工具字段/Schema 字段/测试用例字段级双向 traceability |
| UE 5.7 扫描漏项目层 Source / 资产 / Config / Build | 迁移结论不完整 | **已修(v1.1)**: §7.1 扫描范围扩到 9 类;§7.2 产出 12 字段含来源 URL / 置信度 / 误报状态 / 验证命令 / 复核人 |
| Codex 对抗审 v1 之后是否还有未识别风险 | 未知未知 | spec 通过后 implementation 阶段每个 Phase 末尾走 `superpowers:verification-before-completion`;重大节点可再请 Codex 复审 |

---

## 10. 下一步

本 spec 通过 msc 审阅后:

1. 调用 `superpowers:writing-plans` 生成 implementation plan
2. Implementation plan 按 Phase 0/1/2/3/4 拆任务,每个 Phase 末尾走 `superpowers:verification-before-completion`
3. 全部完成后走 `document-release` + `superpowers:finishing-a-development-branch`
