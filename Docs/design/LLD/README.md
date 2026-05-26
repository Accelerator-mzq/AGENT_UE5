# Detailed Design (LLD) — 入口与导航

> 版本: v1.0(2026-05-26)
> 关联 spec: `Docs/superpowers/specs/2026-05-26-docs-restructure-for-ue57.md` v1.1 §4.3
> 上游: `Docs/design/HLD.md`(架构层 9 章)+ `Docs/requirements/SRS.md` §3.1-§3.7(功能层)
> 下游: 实际代码(`Plugins/AgentBridge/` + `Source/` + `Scripts/`)

7 模块 LLD,与 HLD 配套使用。每份 LLD 走"模块概述 / 内部分层 / 关键签名 / 数据流 / 扩展点 / 已知约束 / UE 5.7 迁移变更点"7 章统一模板。

## 模块导航

| 模块 | LLD 文件 | SRS 对应 | F-* 范围 | 主要代码位置 |
|------|----------|----------|----------|--------------|
| C++ 编辑器子系统 | [01_cpp_subsystem.md](./01_cpp_subsystem.md) | SRS §3.1 | F-CPP-01..06 | `Plugins/AgentBridge/Source/AgentBridge/` |
| Bridge 工具体系 | [02_bridge.md](./02_bridge.md) | SRS §3.2 | F-BRG-01..09 | `Plugins/AgentBridge/Scripts/bridge/` |
| Orchestrator | [03_orchestrator.md](./03_orchestrator.md) | SRS §3.3 | F-ORC-01..08 | `Plugins/AgentBridge/Scripts/orchestrator/` |
| Compiler | [04_compiler.md](./04_compiler.md) | SRS §3.4 | F-CMP-01..24 | `Plugins/AgentBridge/{Scripts/compiler,Compiler}/` |
| MCP Server | [05_mcp_server.md](./05_mcp_server.md) | SRS §3.5 | F-MCP-01..13 | `Plugins/AgentBridge/MCP/` |
| Skill & Template 体系 | [06_skills_and_templates.md](./06_skills_and_templates.md) | SRS §3.6 | F-SKL-01..04 | `Plugins/AgentBridge/{SkillTemplates,Compiler/stages/{skill_graph_planning,domain_skill_runtime}}` |
| 运行时与证据 | [07_runtime_and_evidence.md](./07_runtime_and_evidence.md) | SRS §3.7 | F-RT-* + F-TST-* + F-HOOK-* + F-INP-* + F-DEMO-* + F-VAL-*(共 18 IDs) | `Plugins/AgentBridge/Tests/` + `Scripts/{hooks,validation,run_*_demo}` + `ProjectInputs/` + `ProjectState/` |

## LLD 文件统一格式

每个模块文件包含:

1. **模块概述** — 一段话角色定位 + F-* ID 范围
2. **内部分层** — 表格化列出子模块 / 角色 / 文件路径(+ 行数)
3. **关键类/函数签名** — IDE 可检索的方法签名 + 1 行中文用途;**不复制整文件**,只挑代表性 25-50 行
4. **数据流与状态机** — 3-5 个场景的 ASCII 图 / 拓扑描述
5. **扩展点** — 3-5 个可执行的扩展模式
6. **已知约束与陷阱** — 4-8 条具体约束(尽量带源文件:行号 anchor)
7. **UE 5.7 迁移变更点** — 引用 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` 的 BC-NNN ID;每条按 P1 confirmed / P2 suspected / P3 suspected 严格分级,**BC-019 严守 P2 suspected,不可升 P1**

## 阅读顺序建议

- **首次阅读**:HLD § 1-2 → LLD/01 cpp → LLD/02 bridge → LLD/05 mcp_server(自底向上理解执行栈)
- **Compiler 视角**:LLD/04 compiler → LLD/06 skills_and_templates → LLD/03 orchestrator(自上而下理解编译链)
- **运行时 / 测试视角**:LLD/07 runtime_and_evidence(单文件覆盖 6 子域)
- **UE 5.7 迁移视角**:每份 LLD §7 + 顶层 `Docs/requirements/SRS.md` §8 + scan spec §4 三档桶

## UE 5.7 迁移记号汇总

- P1 confirmed(msc 已裁决,必修):BC-008 / BC-010 / BC-012 / BC-016 / BC-017 / BC-025
- P2 suspected(pending-msc,5.7 实测阶段裁决):BC-001 / BC-002 / BC-004 / BC-005 / BC-006 / BC-011 / BC-014 / BC-015 / BC-018 / BC-019 / BC-020 / BC-021 / BC-022 / BC-023
- P3 suspected(低置信,待回扫):BC-003 / BC-009 / BC-013 / BC-024
- 详见 `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md` §3-§4 与 `Docs/requirements/SRS.md` §8

## 关联文档

- 上游:`Docs/design/HLD.md`(架构层)/ `Docs/requirements/SRS.md`(功能需求)
- 契约:`Docs/contracts/{tool_contract,field_specification,schemas_catalog,mcp_tools_catalog}.md`
- 索引:`Docs/FEATURE_INVENTORY.md`(105 行多源交叉矩阵,验收门禁底座)
- 测试:`Docs/testing/test_spec.md`(Task 1.15 落地)
- 验收:`Docs/acceptance/acceptance_report.md`(Task 1.16 落地)
- 治理:`Docs/governance.md`(Task 1.17 落地)
- 入口:`Docs/INDEX.md`(Task 1.19 落地)
