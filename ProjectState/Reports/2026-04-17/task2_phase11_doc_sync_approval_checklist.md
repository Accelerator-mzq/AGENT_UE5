# 任务 2 审批用修改清单

## 1. 目的

基于以下 4 份验证报告，收敛出需要进入人工审批的文档修改项：

- `doc_link_report.md`
- `schema_alignment_report.md`
- `mcp_tool_count_report.md`
- `phase11_copy_consistency_report.md`

本清单只回答 5 件事：

1. 改哪个文件
2. 改哪个段落
3. 建议怎么改
4. 为什么改
5. 这部分是否应作为历史保留

本清单不直接修改任何正式文档，只作为下一步人工审批依据。

## 2. 逐条审批清单

| 文件 | 段落 | 建议改法 | 理由 | 是否历史保留 |
|------|------|---------|------|--------------|
| `Plugins/AgentBridge/Docs/compiler_design.md` | `## 2. 当前模块结构` 下的 `### 2.1 Phase 8 新链路（Skill-First 6 阶段，推荐）` | 将该节从“当前推荐主链”改为“Phase 8 历史主链快照”；同时新增或改写为当前 Phase 11 主链摘要：MCP 前端 Stage 1-3、Compiler Core Stage 4-7、Reviewed Handoff v3、Run 治理、53 工具口径。 | 文档头已声明为 `v1.0.0（Phase 11 已完成）`，但正文仍把 Phase 8 的 6 阶段链路写成“推荐”，与当前 `architecture_overview.md` 的 7 阶段主链口径冲突。 | `是`，但必须显式降格为“历史快照”，不能继续作为当前事实描述。 |
| `Plugins/AgentBridge/Docs/compiler_design.md` | `## 2. 当前模块结构` 中 MCP 描述列表 | 将“前端（Stage 1-2）”“Bridge Passthrough 28 工具”“Stage 3-5 由 Compiler Core 调度”更新为当前口径：前端 Stage 1-3、Core Stage 4-7、MCP 总数 53（49 正式 + 4 alias）、Bridge Passthrough 不再用 28 工具描述当前实现。 | 当前实现和工具计数报告已经确认是 `53 = 49 正式 + 4 alias`，继续保留 Stage 1-2 / Stage 3-5 / 28 工具会让读者误判 MCP 和 Compiler 的当前职责边界。 | `否`，这是当前事实描述，必须改。 |
| `Plugins/AgentBridge/Docs/compiler_design.md` | `## 3. 两条主链` | 将 Greenfield / Brownfield 描述从旧的 `design_input_intake -> review -> Reviewed Handoff` 旧链路，改成“当前主链指向 Phase 11 Pipeline Orchestrator / Session v2 / Stage 1-7；旧链路仅保留回归说明”。 | 该节现在仍在描述旧式编译入口和旧 Handoff 语义，和 Phase 11 实际以 Session + Pipeline Orchestrator + Stage 1-7 运行不一致。 | `部分保留`，旧链路可以保留，但必须移入“历史/回归”语境。 |
| `Plugins/AgentBridge/Docs/compiler_design.md` | `## 4. 当前输出`、`## 5. 项目层入口`、`## 6. Phase 7 当前输出`、`## 7. 当前边界` | 统一重写为当前 Phase 11 输出与边界：Root Skill Contract、Clarification Gate Report、Skill Graph、design_space_report、realization_candidates、converged_realization_pack、skill_fragment_v2、cross_review_report_v2、build_ir_v2、reviewed_handoff_v3、run_id 隔离、compare/promote/fast_mode。删除或历史化 Phase 7 专属叙述。 | 这些小节名称叫“当前输出/当前边界”，但内容仍停在 Phase 7/8/旧 Handoff 链路，最容易误导。 | `否`，这是当前事实描述，必须改。 |
| `Plugins/AgentBridge/Docs/greenfield_pipeline.md` | 文档头与 `## 1. 概述` | 在标题下补一行显式说明：本文件是 `Phase 8 Greenfield 历史快照`，不再代表当前 Phase 11 主链；并增加“当前主链参见 architecture_overview / compiler_design / canonical 文档”的跳转说明。 | 这份文档整体仍是 Phase 8 口径，但标题是通用的“Greenfield E2E 管线”，如果不加历史标签，很容易被误读成当前推荐入口。 | `是`，建议保留为历史快照，但必须显式标注。 |
| `Plugins/AgentBridge/Docs/greenfield_pipeline.md` | `## 2. Phase 8 新链路（Skill-First）` | 保留原链路图，但小节标题改为“Phase 8 历史链路”；不要把 `reviewed_handoff_v2.json` 和旧 `build_ir.json` 路径继续写成当前主输出。 | 当前 Phase 11 已经升级到 Build IR v2、Reviewed Handoff v3、run 目录隔离，旧 Phase 8 样例路径不应继续承担当前说明职责。 | `是`，作为历史样例保留。 |
| `Plugins/AgentBridge/Docs/greenfield_pipeline.md` | `## 3. 运行方式` 与 `## 4. 当前限制` | 将“当前限制”改成“历史链路限制”；运行方式部分补一句“当前不作为主开发入口，仅用于回归或历史说明”。 | 现在的表述仍在用“当前”指代旧链路，会和 Phase 11 实际任务入口冲突。 | `是`，但需要改名为历史限制/历史入口。 |
| `Plugins/AgentBridge/Docs/reviewed_handoff_design.md` | 文档头、`## 1. 定位`、`### 1.1 版本演进` | 将文档定位从“Reviewed Handoff 机制设计（v0.8.0）”升级为包含 v1 / v2 / v3 的演进设计；新增 v3 行，明确当前正式交接物是 `reviewed_handoff_v3.schema.json`。 | 当前文档只覆盖 v1/v2，但 Phase 11 正式口径已经是 Reviewed Handoff v3；继续停在 v2 会和当前架构总览、Schema 对齐结果冲突。 | `部分保留`，v1/v2 演进表应保留，但必须补 v3 并改成当前总览。 |
| `Plugins/AgentBridge/Docs/reviewed_handoff_design.md` | `## 2. Schema 概述` | 将 Schema 主路径从 `Schemas/reviewed_handoff.schema.json` 改为当前以 `reviewed_handoff_v3.schema.json` 为主；保留 v1/v2 作为历史兼容说明。顶层字段与结构说明需改为 v3 字段集合。 | Schema 对齐报告已经显示 `reviewed_handoff_v3.schema.json` 存在且属于 Phase 11 第二批；现文档仍以 v1 schema 为主，事实已过期。 | `否`，这是当前正式格式说明，必须改。 |
| `Plugins/AgentBridge/Docs/reviewed_handoff_design.md` | `## 4. 生命周期` | 将 `draft -> approved -> run_plan_builder.py -> handoff_runner.py` 的主流程改为当前 Phase 11 路径：Pipeline Orchestrator / run_id workspace / Reviewed Handoff v3 / Execution 消费边界；旧人工审批流仅作为历史说明保留。 | 当前主链已经不是旧式 `draft/approved + run_plan_builder` 运行模式，这一节继续按旧主流程描述会误导执行入口。 | `部分保留`，旧审批流可作为历史保留，但不能继续写成当前主流程。 |
| `Plugins/AgentBridge/Docs/reviewed_handoff_design.md` | `## 7. 与 Run Plan 的关系`、`## 8. 参考` | 将“Run Plan Builder 是当前消费端”的表述改成“Run Plan 属于旧链路/兼容概念”；参考链接更新为 v3 schema、Phase 11 canonical 文档和当前验证脚本。 | 该节现在直接把旧 Run Plan Builder 写成当前必经路径，和 Phase 11 Session/Pipeline/run_id 模型不一致。 | `部分保留`，Run Plan 可以保留为历史兼容术语，但不能继续作为当前事实。 |
| `Plugins/AgentBridge/Docs/ue5_capability_map.md` | `## 8. Phase 7 当前补充` | 整节删除，不做回写扩展。 | 该节是明确的阶段残留，且标题直接写了 “Phase 7 当前补充”；它已经不承担 Phase 11 当前说明职责，保留只会制造混乱。 | `否`，建议直接删除，不作为历史段落继续保留在正文中。 |

## 3. 本轮不进入审批的文件

以下文件虽然在扫描中命中过旧关键词，但本轮不建议纳入修改：

- `Plugins/AgentBridge/Docs/architecture_overview.md`
  - 原因：当前 Phase 11 总口径锚定文档，命中的 `v0.8.0 / v0.9.0 / 28 工具` 主要位于历史版本表与历史对照说明中，不属于误导性的当前事实描述。
- `Plugins/AgentBridge/Docs/skills_and_specs_overview.md`
  - 原因：`Reviewed Handoff v2`、`MCP 28 工具` 出现在阶段演进表中，语义是历史阶段说明，不是当前主链说明。
- `Plugins/AgentBridge/Docs/tool_contract_v0_1.md`
- `Plugins/AgentBridge/Docs/field_specification_v0_1.md`
- `Plugins/AgentBridge/Docs/orchestrator_design.md`
  - 原因：本轮 4 份报告未给出足够强的当前事实冲突证据，暂不纳入审批范围。
- 9 份 Phase 11 canonical 文档
  - 原因：任务 2 的目标应是让其他文档向 canonical 对齐，不应反向修改 canonical 定义。

## 4. 建议审批顺序

建议按以下顺序审批并执行：

1. `compiler_design.md`
2. `reviewed_handoff_design.md`
3. `greenfield_pipeline.md`
4. `ue5_capability_map.md`

这样可以先修正最容易误导当前开发口径的两份框架设计文档，再处理历史快照和阶段残留。
