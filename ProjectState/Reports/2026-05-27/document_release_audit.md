# Document Release Audit — chore/retire-ue57-refactor-plan @ pre-commit

> 运行时间: 2026-05-27T22:00:00+08:00
> 比较基准: main @ 7cd10f8(PR #42 merge)
> 触发事件: 用户决定企汰 UE 5.7 重构计划(2026-05-27),修 3 个 L0/L1 文档的"UE 5.5.4 → 5.7 重构准备中"状态描述
> 范围: 3 files / +13 / -4(不含 hook 自动追加的 doc_release_skipped.log)

## 背景

Phase 12 LLM Internal Reopen 收尾后(PR #41 + #42 均已 merge 到 main),用户决定企汰 UE 5.7 重构计划。

经讨论确认范围 = **(A')+(1) 选项的细化**:
- **不动** `Docs/superpowers/specs/2026-05-26-ue57-breaking-changes-scan.md`(它是 BC 知识库,不是任务书;P1 6 条已 msc 裁决 + P2/P3 留实测,被 17 处文档结构性 anchor,保留作未来可能的重启资产)
- **只改** L0/L1 文档的"项目状态"描述,把"UE 5.5.4 → UE 5.7 重构准备中"翻面为"UE 5.5.4 稳定 / UE 5.7 计划已企汰"

3 个改动文件:
- `Docs/INDEX.md` §1 项目状态 + §3 状态表格 UE 引擎目标版本 cell
- `Docs/acceptance/acceptance_report.md` §2 门禁定位翻面(原 UE 5.7 重构验收 → main 主线回归门禁)+ §3 模板加企汰标注
- `task.md` 顶部加企汰说明

## Coverage Map

| 变更点 | A 入口 | B 阶段事实 | C 框架 | D 证据落盘 |
|---|---|---|---|---|
| 企汰 UE 5.7 重构计划 + 标注 BC 知识库保留作重启资产 | task.md(本次)+ Docs/INDEX.md(本次,§1+§3 表格)+ README.md(无需改,Phase 12 收尾时已无 5.7 措辞) | Docs/acceptance/acceptance_report.md §2 门禁翻面 + §3 模板企汰标注(本次)+ Docs/design/HLD.md / Docs/design/LLD/01-07 / Docs/contracts/* / Docs/requirements/SRS.md(**不动** — 这些是结构性引用 BC 知识库,UE 5.7 计划企汰不影响 BC 知识库的存在意义;若未来真重启 UE 5.7 工作,这些 anchor 直接可用) | Plugins/AgentBridge/Docs/(无关) | 本 audit.md(本次)|

零覆盖:无。

## Documentation health

- **README.md**: Current — 顶部"当前状态: Phase 12 LLM Internal Reopen 已完成(2026-05-27),Phase 11 已归档" 已不含"UE 5.7 重构准备中" 表述(Phase 12 T20 收尾时已经清干净),无需改。
- **AGENTS.md** / **CLAUDE.md**: Current — 无 UE 5.7 状态描述,不需改。
- **task.md**: Updated — 顶部加"UE 5.5.4 稳定"+"UE 5.7 重构计划已企汰"说明 + 指向 BC 知识库 spec 路径供未来重启参考。
- **Docs/INDEX.md**: Updated
  - §1 项目状态(line 11):翻面为"UE 5.5.4 稳定" + 加"UE 5.7 重构计划已企汰 2026-05-27" 注 + 显式说明"LLD/01-07 §UE 5.7 迁移变更点 等 anchor 在 BC 知识库 spec 仍保留,不主动维护但不删除"。
  - §3 表格(line 112)UE 引擎目标版本:从"UE 5.5.4 → 5.7"改为"UE 5.5.4 稳定(UE 5.7 重构计划已企汰 2026-05-27,BC 知识库保留)"。
- **Docs/acceptance/acceptance_report.md**: Updated
  - §2 验收门禁清单(line 79):加企汰警告,把 5 个门禁原定位"UE 5.7 重构验收必须逐项通过"改为"Phase 12 收尾后改作 UE 5.5.4 主线的回归门禁基线"。
  - §3 UE 5.7 重构验收模板(line 137):标题加"**计划已企汰 2026-05-27**,模板保留作未来可能重启的资产" + 顶部加企汰警告 + 说明本阶段不再主动维护、不阻塞主线。
- **Docs/governance.md** / **Docs/redirects.json** / **Docs/contracts/{tool_contract,field_specification,schemas_catalog,mcp_tools_catalog}.md** / **Docs/design/HLD.md** / **Docs/design/LLD/{README,01,02,03,04,05,06,07}_*.md** / **Docs/requirements/SRS.md** / **Docs/FEATURE_INVENTORY.md** / **Docs/testing/test_spec.md**: Current — 这些文档对 UE 5.7 BC 知识库的 17 处结构性引用全部保留;UE 5.7 计划企汰不影响 BC 知识库本身的存在意义。
- **Layer C 框架**:
  - **Plugins/AgentBridge/README.md** / **AGENTS.md** / **Docs/\*.md**: Current — 框架文档不涉及 UE 5.7 状态。
  - **Plugins/AgentBridge/Schemas/\*.json**: Current — schema 与 UE 版本计划无关。
  - **Plugins/AgentBridge/Tests/SystemTestCases.md**: Current — 测试用例不涉及 UE 5.7 状态。
- **Backlog**:
  - **完成或被取代条目**:本次没有完成新工作,但企汰了"UE 5.7 重构"作为短期目标。
  - **新延期工作**:无(企汰即"无限期延期",不视为新 backlog)。
  - **已知 follow-up 不变**:Phase 12 的 3 个 follow-up(retry_policy / model_registry auto-prefix / dead code)在 PR #42 已收掉。
- **ProjectState/Reports**:
  - **2026-05-27/document_release_audit.md**:本次覆盖写(此前 PR #42 的 audit 在 git 历史中可追溯)。
- **Archive**: Read-only — 本次不动 Docs/archive/** 或 Docs/History/**。

## Hard Boundaries 自检

- 0 改动 `Source/*` C++ 核心 ✓
- 0 改动 `Scripts/bridge/*` ✓
- 0 改动 `Scripts/orchestrator/*` ✓
- 0 改动 `AgentBridgeTests/` ✓
- 0 改动 `Plugins/AgentBridge/Schemas/`(稳定 Schema)✓
- 0 改动 `Plugins/AgentBridge/AGENTS.md` ✓
- 0 改动 `Docs/History/**` 或历史日期 `ProjectState/Reports/<past_date>/` ✓
- 0 删除任何文件(仅改 3 个 L0/L1 文档的状态描述)✓
- 0 触 BC 知识库 spec 本体(2026-05-26-ue57-breaking-changes-scan.md 内容不变,17 处跨文档引用不变)✓

## 关键设计决策

1. **不动 BC 知识库 spec 本体**:它是"BC 字典/扫描结果固化",不是任务书。25 条 BC 中 P1 6 条已 msc 裁决,P2/P3 留实测 — 这是真正的知识积累,未来若重启 UE 5.7 工作直接可用。
2. **保留 17 处跨文档结构性引用**:LLD/01-07 § UE 5.7 迁移变更点 + HLD §UE 5.7 升级 BC 表 + contracts §UE 5.5.4 → 5.7 升级表 + acceptance_report §3 模板,这些是"未来若重启 UE 5.7 工作的最小启动包",企汰不应破坏这层结构。
3. **§2 验收门禁翻面**:原 5 个门禁(Schema --strict / 系统测试 / 真 LLM acceptance / promotable / 文档同步)是好门禁,只是不再绑定 UE 5.7 上下文 — 翻面为"UE 5.5.4 主线回归门禁",让它继续 work 作为日常 regression baseline。

## 本次 audit 信号

3 个 L0/L1 文档的状态描述翻面,**保留所有结构性引用与 BC 知识库**,企汰动作精确限定在"项目状态语义"而非"知识资产"。这是对 user 意图(企汰任务,不丢知识)的最小化忠实表达。
