# Docs INDEX — Mvpv4TestCodex 文档体系顶层入口

> 版本: v1.0(2026-05-26)
> 关联 spec: `Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md` v1.1
> 文档定位: **入口型**,新接手 Agent / 开发者必读

---

## 1. 项目状态(一句话)

**Phase 11 已完成,UE 5.5.4 → 5.7 重构准备中**:Phase 11 (Skill-First Design Compiler Framework) 验收已 closeout(`Docs/acceptance/acceptance_report.md` §1);本次文档重组(Phase 0-4)产出本 INDEX 等 22 份新文档,作为 UE 5.7 重构开发者的输入规格,旧文档全量归档到 `Docs/archive/` 反向映射可追溯。

---

## 2. 阅读顺序

### 新接手 Agent / 开发者(首次进入项目)

1. **项目根 anchor**(L0 信任层):
   - `README.md` — 项目对外简介
   - `AGENTS.md` — Agent 行为规则(必读)
   - `CLAUDE.md` — Claude Code 私有规则(必读)
   - `task.md` — 当前阶段唯一开发驱动入口
2. **本文档体系入口**(L1 当前权威):
   - `Docs/INDEX.md`(本文件)
   - `Docs/FEATURE_INVENTORY.md` — 105 行多源交叉矩阵,验收门禁底座
   - `Docs/governance.md` — 文档治理与规则索引
3. **功能规格**(SRS → HLD → LLD):
   - `Docs/requirements/SRS.md` — 系统功能"做什么"(8 章 + 附录,~4000 中文字)
   - `Docs/design/HLD.md` — 架构"怎么分层"(9 章,~3000 中文字)
   - `Docs/design/LLD/README.md` — 7 模块 LLD 入口
4. **契约层**(L2 Canonical):
   - `Docs/contracts/{tool_contract,field_specification,schemas_catalog,mcp_tools_catalog}.md`
5. **测试与验收**:
   - `Docs/testing/test_spec.md` — 266 系统测试用例索引
   - `Docs/acceptance/acceptance_report.md` — Phase 11 基线 + UE 5.7 验收模板

### Compiler 视角(深入 Phase 11 主链)

- HLD §2 → LLD/04 compiler → LLD/06 skills_and_templates → LLD/03 orchestrator

### 运行时 / 测试视角

- LLD/07 runtime_and_evidence(单文件覆盖 6 子域)→ testing/test_spec.md

### UE 5.7 迁移视角

- 每份 LLD §7 + SRS §8 + `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4

---

## 3. 文档导航树

```
Docs/
├── INDEX.md                                  # 本文件(入口 / 阅读顺序 / 旧→新映射)
├── FEATURE_INVENTORY.md                      # 105 行多源交叉矩阵 = 验收底座
├── governance.md                             # 文档治理 / hook / 信任分层
├── redirects.json                            # 108 条机器可读 old→new 映射(Phase 0.4 产出)
├── requirements/
│   └── SRS.md                                # 系统功能"做什么"单文件 8 章
├── design/
│   ├── HLD.md                                # 架构"怎么分层"单文件 9 章
│   └── LLD/                                  # 详细实现"怎么实现"7 模块
│       ├── README.md                         # LLD 入口与导航
│       ├── 01_cpp_subsystem.md               # C++ 子系统(F-CPP-01..06)
│       ├── 02_bridge.md                      # Bridge 工具体系(F-BRG-01..09)
│       ├── 03_orchestrator.md                # Orchestrator(F-ORC-01..08)
│       ├── 04_compiler.md                    # Compiler(F-CMP-01..24)
│       ├── 05_mcp_server.md                  # MCP Server(F-MCP-01..13)
│       ├── 06_skills_and_templates.md        # Skill & Template(F-SKL-01..04)
│       └── 07_runtime_and_evidence.md        # 运行时/证据/测试/Hook/Input/Demo/Validation
├── testing/
│   └── test_spec.md                          # 15 测试类 / 266 case 索引
├── acceptance/
│   └── acceptance_report.md                  # Phase 11 基线 + UE 5.7 验收模板
├── contracts/
│   ├── tool_contract.md                      # L1/L2/L3 工具协议(7 章)
│   ├── field_specification.md                # 字段命名/单位/Schema 规则(5 章)
│   ├── schemas_catalog.md                    # 41 主 Schema + 26 examples
│   └── mcp_tools_catalog.md                  # 53 MCP 工具签名表
├── superpowers/
│   ├── specs/                                # 设计 spec(本次重组 + UE 5.7 scan)
│   └── plans/                                # 实施 plan
└── archive/
    ├── README.md                             # 旧→新反向映射主表(108 行)
    ├── current/                              # 旧 Docs/Current/ 归档
    ├── history/                              # 旧 Docs/History/ 整树
    ├── decisions/                            # 旧 Docs/Decisions/
    ├── proposals/                            # 旧 Docs/Proposals/
    ├── superpowers/                          # 旧 Docs/superpowers/{specs,plans} archive-only 部分
    └── plugins/                              # 旧 Plugins/AgentBridge/Docs/ 抽取后归档
```

**新文档总数 22 份**(本表前 5 章列出 21 份 + INDEX 本身),替代原 ~50 份项目层 + 31 份插件层 = 108 份旧文档(详见 `Docs/archive/README.md`)。

---

## 4. 权威定义点索引

每个硬事实在新文档中**只声明一次**,本表是反向查表入口:

| 硬事实 | 权威文档 | 数字 / 内容 |
|--------|----------|-------------|
| MCP 工具数 | `Docs/contracts/mcp_tools_catalog.md` 主表 | **53**(Bridge 28 + 前端 14 + 后端 11)|
| Schema 数 | `Docs/contracts/schemas_catalog.md` 主表 + 附录 A | **42 主 + 27 examples = 69**(2026-05-27 ForgeUE real-ue milestone 新增 `forgeue_import_evidence` schema + 1 example)|
| 系统测试用例数 | `Docs/testing/test_spec.md` §3 + `Plugins/AgentBridge/Tests/run_system_tests.py:191 TOTAL_CASES` | **266**(15 测试类)|
| C++ Automation 测试数 | `Docs/testing/test_spec.md` §1 + `Plugins/AgentBridge/AgentBridgeTests/` | **~26**(独立计数,不计入 266)|
| 7 阶段主链 | `Docs/requirements/SRS.md §4.1` + `Docs/design/HLD.md §2.1` | Stage 1-7(Root Skill Contract → Reviewed Handoff v3)|
| Run 治理 | `Docs/requirements/SRS.md §4.3` + `Docs/design/HLD.md §3` | F-GOV-01..04(run_id / fast_mode / generator_provider / compare-promote)|
| Schema --strict 27/27 | `Docs/testing/test_spec.md §5` + `Docs/acceptance/acceptance_report.md §2.1` | `validate_examples.py --strict`(2026-05-27 26→27,加 `forgeue_import_evidence_example.json`)|
| UE 引擎目标版本 | `Docs/requirements/SRS.md §1.2` | **UE 5.5.4 → 5.7** |
| 项目层 + 插件层分层 | `Docs/design/HLD.md §1.1` | 双层架构 + 进程拓扑 |
| 4 通道(契约) | `Docs/contracts/tool_contract.md §5.2` | Channel A/B/C/D;代码实际 BridgeChannel 4 值,channel_map 暴露 3 档 |
| F-* IDs 总数 | `Docs/FEATURE_INVENTORY.md` 主表 | **105 行 × 8 列 / 15 family** |
| UE 5.7 Breaking Changes | `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3 + §4 | **25 BC**(P1 6 confirmed + 1 false-positive + P2 14 suspected + P3 4 suspected)|
| 旧文档总数 | `Docs/archive/README.md` + `Docs/superpowers/specs/2026-05-26-old-docs-inventory.csv` | **108 份**(项目层 77 + 插件层 31)|
| 12 SkillTemplate | `Docs/design/LLD/06_skills_and_templates.md §2.2` | Baseline 6 + Genre Pack Monopoly 6 = 12 × 6 文件 = 72 |
| 19 个 Phase 1 新文档 | `Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md` Task 1.1-1.19 | contracts 4 + SRS 1 + HLD 1 + LLD 8 + test 1 + accept 1 + gov 1 + INDEX 1 + FEATURE_INVENTORY 1 |

---

## 5. 旧→新跳转快查

10 份高频旧文档的新归宿(完整 108 行见 `Docs/archive/README.md`):

> 第一列旧路径为 Phase 4 重写前的源路径(物理已搬入 `Docs/archive/`),保留作反向查表入口,因此用 `<code>` HTML 标签包裹避开 link_precheck 扫描。

| 旧路径(已搬迁) | 新归宿 |
|--------|--------|
| <code>Docs/Current/00&#95;Index.md</code> | `Docs/INDEX.md`(本文件,全替换)|
| <code>Docs/Current/01&#95;Project&#95;Baseline.md</code> | `requirements/SRS.md §1` + `acceptance/acceptance_report.md §1` |
| <code>Docs/Current/14&#95;MCP&#95;Cognitive&#95;Bridge&#95;Anchor.md</code> | `design/HLD.md §4` + `requirements/SRS.md §3.5` |
| <code>Docs/Current/15&#95;Skill&#95;Spec&#95;Handoff&#95;Chain.md</code> | `requirements/SRS.md §4` + `design/HLD.md §2` |
| <code>Docs/Current/18&#95;Phase11&#95;Closeout.md</code> | `acceptance/acceptance_report.md §1` |
| <code>Plugins/AgentBridge/Docs/architecture&#95;overview.md</code> | `design/HLD.md §1-§2` |
| <code>Plugins/AgentBridge/Docs/tool&#95;contract&#95;v0&#95;1.md</code> | `contracts/tool_contract.md`(全文消化)|
| <code>Plugins/AgentBridge/Docs/field&#95;specification&#95;v0&#95;1.md</code> | `contracts/field_specification.md`(全文消化)|
| <code>Plugins/AgentBridge/Docs/orchestrator&#95;design.md</code> | `design/LLD/03_orchestrator.md` |
| <code>Plugins/AgentBridge/Docs/skills&#95;and&#95;specs&#95;overview.md</code> | `requirements/SRS.md §4` + `design/LLD/06_skills_and_templates.md` |

**机器可读完整映射**:`Docs/redirects.json`(108 条,Phase 0.4 产出,Phase 2/4 grep 校验脚本字典源)。

---

## 6. 常用命令(从旧 <code>Docs/Current/06&#95;Current&#95;Task&#95;List.md</code> 搬迁)

```bash
# Schema 校验(--strict 26/26)
python Plugins/AgentBridge/Scripts/validation/validate_examples.py --strict

# 系统测试:一键全 11 stage / 266 case
python Plugins/AgentBridge/Tests/run_system_tests.py

# 系统测试:交互模式
python Plugins/AgentBridge/Tests/run_system_tests.py --interactive

# 系统测试:无编辑器(分段等价验证)
python Plugins/AgentBridge/Tests/run_system_tests.py --no-editor

# Greenfield 端到端(simulated)
python Scripts/run_greenfield_demo.py

# Brownfield demo
python Scripts/run_brownfield_demo.py

# Boardgame Playable demo
python Scripts/run_boardgame_playable_demo.py

# JRPG turn-based demo
python Scripts/run_jrpg_turn_based_demo.py

# Standalone Smoke(脱离 Editor)
python Plugins/AgentBridge/Tests/scripts/task14a_phase11_standalone_smoke.py

# Handoff Schema 校验
python Plugins/AgentBridge/Scripts/validation/test_handoff_schema.py

# MCP 工具数实测
python -c "from Plugins.AgentBridge.MCP.tool_definitions import TOOL_COUNT; print(TOOL_COUNT)"  # → 53
```

---

## 7. 关联资源

- 项目根 4 anchor:`README.md` / `AGENTS.md` / `CLAUDE.md` / `task.md`(本次重组不动)
- Phase 0 产物:inventory CSV + archive/README.md + UE 5.7 scan spec + FEATURE_INVENTORY 骨架 + redirects.json(共 5 件,见 `Docs/superpowers/{specs,plans}/2026-05-26-*`)
- 重组 spec:`Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md` v1.1
- 重组 plan:`Docs/superpowers/plans/2026-05-26-docs-restructure-for-ue57.md`(Task 0.1-0.4 + 1.1-1.19,Phase 2-4 后续)
- Codex 对抗审记录:重组 spec v1.1 顶部修订记录块
- 文档治理 skill:`.claude/skills/document-release/SKILL.md` + `.agents/skills/document-release/SKILL.md`
