# AgentBridge Docs — Deprecated 目录

> **本目录所有原始内容已整合到主文档体系 `Docs/`**,各文件保留 redirect stub 兜底深链。
> 主入口: [Docs/INDEX.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/INDEX.md)
> 完整反向映射: [Docs/archive/README.md](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/README.md)
> 机器可读映射: [Docs/redirects.json](/D:/UnrealProjects/Mvpv4TestCodex/Docs/redirects.json)
> 历史原版全文: [Docs/archive/plugins/](/D:/UnrealProjects/Mvpv4TestCodex/Docs/archive/plugins/)

## 为什么保留 stub?

避免外部 IDE 跳转 / Codex 缓存 / AGENTS.md 残留引用 / 历史 commit message 深链 404,本目录保留 31 个同名 stub 兜底。

每个 stub 仅含 5 行:标题 + 权威新归宿链接 + 历史原版链接 + INDEX 链接 + redirects.json 注脚。

## 31 stub 索引

| 原文件 | 新归宿 |
|--------|--------|
| `Archive/Phase1-2/bridge_implementation_plan.md` | archive/plugins/Archive/Phase1-2/bridge_implementation_plan.md |
| `Archive/Phase1-2/mvp_scope.md` | archive/plugins/Archive/Phase1-2/mvp_scope.md |
| `Archive/Phase1-2/mvp_smoke_test_plan.md` | archive/plugins/Archive/Phase1-2/mvp_smoke_test_plan.md |
| `agent_interaction_protocol.md` | governance.md#4 |
| `architecture_overview.md` | design/HLD.md#1-2 |
| `base_skill_domains_design.md` | design/LLD/06_skills_and_templates.md |
| `baseline_realization_policy.md` | design/LLD/06_skills_and_templates.md |
| `boardgame_playable_pipeline.md` | design/LLD/03_orchestrator.md |
| `bridge_verification_and_error_handling.md` | design/LLD/02_bridge.md |
| `clarification_gate_rules.md` | design/LLD/04_compiler.md |
| `compiler_design.md` | design/LLD/04_compiler.md |
| `constraint_variant_policy.md` | design/LLD/06_skills_and_templates.md |
| `design_space_discovery.md` | design/LLD/04_compiler.md |
| `editor_screenshot_evidence_workflow.md` | testing/test_spec.md + governance.md#1 |
| `feedback_interface_catalog.md` | requirements/SRS.md#3.2 + contracts/mcp_tools_catalog.md |
| `feedback_write_mapping.md` | requirements/SRS.md#3.2 + contracts/mcp_tools_catalog.md |
| `field_specification_v0_1.md` | contracts/field_specification.md |
| `forgeue_manifest_integration.md` | design/LLD/02_bridge.md + design/LLD/03_orchestrator.md |
| `genre_pack_core_design.md` | design/LLD/06_skills_and_templates.md |
| `governance_loop_minimal_design.md` | governance.md#3 |
| `greenfield_pipeline.md` | design/LLD/03_orchestrator.md |
| `jrpg_genre_pack_design.md` | design/LLD/06_skills_and_templates.md + testing/test_spec.md |
| `orchestrator_design.md` | design/LLD/03_orchestrator.md |
| `reviewed_handoff_design.md` | design/LLD/04_compiler.md + contracts/handoff_contract.md |
| `root_skill_contract_standard.md` | requirements/SRS.md#3 + design/LLD/06_skills_and_templates.md |
| `run_isolation_compare_promote.md` | design/LLD/03_orchestrator.md + governance.md#3 |
| `skill_graph_and_domain_skill.md` | design/LLD/06_skills_and_templates.md |
| `skills_and_specs_overview.md` | requirements/SRS.md#4 + design/LLD/06_skills_and_templates.md |
| `tool_contract_v0_1.md` | contracts/tool_contract.md |
| `ue5_capability_map.md` | design/LLD/02_bridge.md + design/HLD.md#3 |
| `universal_baseline_standard.md` | requirements/SRS.md#3 + design/LLD/06_skills_and_templates.md |

## 升级路径

新功能 / 新文档不应再加到本目录,统一去 `Docs/`(新文档骨架见 `Docs/INDEX.md` §3 文档导航树):

- 契约层 → `Docs/contracts/`
- 需求 → `Docs/requirements/SRS.md`
- 架构 → `Docs/design/HLD.md` + `Docs/design/LLD/<模块>.md`
- 测试 → `Docs/testing/test_spec.md`
- 验收 → `Docs/acceptance/acceptance_report.md`
- 治理 → `Docs/governance.md`
