# Phase 14 — Demo-First 增量主链设计(v0 可玩骨架 → 拓扑序增量)

> 日期:2026-06-11
> 状态:设计定稿,待 msc 审阅后转 writing-plans
> 上游输入:Phase 14 重定义输入(2026-06-11 三轮架构裁决,记忆 `project_phase14_redefinition_input`)
> 关联:Phase 13 spec `2026-06-10-phase13-skill-synthesis-design.md` / 验收 runbook `ProjectState/Reports/2026-06-11/phase13_acceptance_runbook.md`

## 1. 背景与目标

### 1.1 三个结构性缺口(Phase 13 收尾后实证诊断)

1. **逻辑层无执行者**:验收 run build_ir 16 步中 10 步为 `create_cpp_class`,插件内零代码消费该 action;真机只落过 6 个 UMG widget 空壳。
2. **lowering 语义坍塌**:`selected_realization` 收敛为词表枚举标签("·约束优先"类),玩法规则语义在 build_ir 层不可恢复;真语义在 GDD 与模板/合成包 6 文件原文中。
3. **表达天花板**:Stage 1 启发式模板 Monopoly 固化 + 21 family 词表挤压(Phase 13 验收发现 4/5)。

结论:"管线机械 lowering 到可玩 demo"路线不可达。**handoff 的消费者改为 coding agent**:管线产施工图,agent 读原文写代码,bridge 真机验证。对照实证:项目内唯一可玩物(`Source/Mvpv4TestCodex/` 的 MMonopoly* 全家桶)即早期 phase 由 agent 直接手写。

### 1.2 msc 两条裁决(对 Claude-Code-Game-Studios 的批评转化)

1. **决策两端化**:人只出现在两端(写 GDD / 试玩裁决),中间全自动;过程内设计取舍一律 agent 给默认值+留痕(provisional 机制),不许中途问人。
2. **demo-first**:先产出基础可玩 demo(v0),再逐步增量;文档不先行、不阻塞,人读文档后置投影。

### 1.3 目标(一句话)

无人值守从 GDD 产出一个可玩 v0(独立 runtime plugin),再完成一次"可玩→可玩"的增量批次(拍卖),全程人只在两个试玩窗口出现。

### 1.4 非目标 / YAGNI(记 backlog 或留后续 Phase)

- N demo 扇出与挑选会话层(Phase 15;本期 demo_plan/story 机制按可复用设计)
- Codex 端实证(接口 MCP 中立必须达成,双端跑通不要求)
- 词表扩展 / Stage 1 模板固化修复(JRPG 类 GDD 的施工图质量,Phase 14+)
- Stage 4-7 改造或删除(原样保留,demo 链路不消费)
- art bible(本期无美术管线,生成只会是空模板)
- demo plugin 脚手架工具(施工规范文档 + few-shot 足够)
- 增量批 2(股票市场):计划内留批,本期不执行

## 2. 范围定盘(brainstorming 五项裁决,2026-06-11)

| 决策点 | 裁决 |
|---|---|
| 验收范围 | v0 + 一次增量批(拍卖);扇出留 Phase 15 |
| v0 载体 | 独立 runtime plugin `Plugins/Demo_MonopolyAuction/`(Source+Content+Docs 自包含,可整体删除重建) |
| 驱动 GDD | `ProjectInputs/GDD/monopoly_extended_auction_v1.md`(管线前半段已实证,一次只测一个未知) |
| 可玩判据 | 机器冒烟守回归(驱动一局到终局零报错)+ msc 试玩终裁(PROCEED/PIVOT/KILL) |
| 双端 | 接口 MCP 中立 + 单端(Claude Code)实证 |

## 3. 总体架构与数据流

```
GDD(monopoly_extended_auction_v1)
 → Stage 1-3(现状零改动,自动):契约+覆盖矩阵+skill graph(库内节点绑模板,2 gap 如实记录)
 → [新] demo_plan 环节(自动,确定性零 LLM):拓扑序切批
    ├─ v0 批 = 全部库内绑定 required capability(16 节点)+ 末尾文档 story
    ├─ 增量批1 = gameplay-property-auction(合成)+ 末尾文档 story
    └─ 增量批2 = gameplay-stock-market(留批不执行)
 → [新] v0 整体生成(自动,无人值守):coding agent 经 demo_story_fetch 取施工图,
    在 Plugins/Demo_MonopolyAuction/ 写骨架+C++/BP+地图+冒烟用例,自修循环
 → [新] 机器冒烟(自动):一局驱动到终局零报错+截图 → demo_story_submit 交证据
 → 【人审窗口1】msc 试玩 v0(PROCEED/PIVOT/KILL)+ 批拍卖合成包(Phase 13 原 gate 原位)
 → [新] 增量批1(自动):逐 story 实施,门禁 = v0 冒烟用例 hash 不变且全绿
 → 【人审窗口2】msc 试玩 v1,Phase 14 终裁
```

三个关键架构决定:

1. **Stage 4-7 不进 demo 链路**。story 材料 = GDD 锚点段落原文 + skill graph 节点 + 模板/合成包 6 文件原文(全文路径指针,agent 自读,零语义压缩),正面绕开 lowering 坍塌。Stage 4-7 与旧链路原样保留(审计/回归资产),Phase 15 扇出时再决定 design_space 如何接回当"N 方向分化器"。
2. **人只在两个窗口**,窗口 1 天然落在"已有可玩物之后"(合成 capability 全属增量批,v0 不依赖人审)。
3. **demo plugin 与手写代码硬隔离**:施工规范禁止依赖 `Source/Mvpv4TestCodex` 的 MMonopoly* 类;v0 成败对 GDD 负责,参考既有代码风格不算作弊,链接依赖算违规(submit 校验)。

## 4. 组件设计

### 4.1 demo_plan 环节

- 位置:插件层 `Plugins/AgentBridge/Compiler/demo_plan/`(机制);输出落项目层 `ProjectState/runs/<run_id>/demo_plan.json` + `stories/*.json`(实例)。
- 切批规则通用、零游戏领域语义(防固化守则机器化):v0 批 = 库内绑定 required capability 全集;增量批 = 每个合成 capability 一批;批内 story 按 skill graph 依赖边拓扑序;每批末尾机械追加一个文档 story(见 4.7)。
- 确定性:同输入同输出,golden 测试守门。

### 4.2 story schema(插件层新增 `demo_story.schema.json`)

核心字段:

- `story_id` / `batch`(v0 | increment-N)/ `capability_id` / `depends_on`
- `materials`:全部为路径指针(GDD 锚点段落、模板或合成包 6 文件、契约、施工规范),agent 读全文
- `evidence_class`:Logic / Integration / Visual / Config 四级,决定 submit 必交证据
- `acceptance_criteria`:机械生成保底(编译+测试+冒烟+对 GDD 锚点自证清单)
- `status`:pending → in_progress → submitted → verified(可重入,见 §5.2);submit 校验失败 story 回 in_progress 并附错误清单,自修轮次 +1

### 4.3 MCP 工具对(55→57,双端中立)

- `demo_story_fetch(run_id, story_id?)`:发下一个(或指定)story 全包 + 施工规范全文 + 材料路径清单,置 in_progress。
- `demo_story_submit(run_id, story_id, evidence)`:evidence = {files_changed, test_report, smoke_report, screenshots, provisional_decisions, doc_paths};机器校验按 evidence_class 齐全、引用路径存在、冒烟 pass;**增量批附加校验:v0 冒烟用例文件 hash 不变且全绿**(防改判据作弊,"可玩→可玩"的机器守门)。校验失败返回具体错误(Phase 13 save 同款重试闭环);落盘走 `.part` 事务。

### 4.4 施工规范层(construction manifest)

- 实例落项目层 `ProjectInputs/ConstructionManifest/demo_plugin_standards.md`,机制(读取+注入 fetch 载荷)在插件层;带版本戳,story 引用版本不符告警。
- 内容:plugin 骨架规范(.uplugin/Build.cs/Content 布局)、UE 编码约束(TObjectPtr、禁热路径字符串、禁无谓 Tick、UPROPERTY 宏齐全;参考 CCGS unreal-specialist 约束清单)、GameMode/State/Subsystem 分层职责、**规则参数必须数据驱动(DataAsset/DataTable,为增量与扇出留缝)**、禁依赖清单(MMonopoly* 等)、provisional 决策留痕格式、冒烟用例规范、中文注释。

### 4.5 demo plugin 骨架与交付物

`Plugins/Demo_MonopolyAuction/`:

- plugin 命名由 demo_plan 从契约 id 数据驱动派生(机制代码零游戏语义,Demo_MonopolyAuction 是本 GDD 的预期派生值,非硬编码)
- `Source/`(runtime module)+ `Content/`(地图/BP/DataAsset)+ `.uplugin`
- `Docs/`(维护文档包,见 4.7)+ `README.md`(**试玩说明**:试玩入口地图、操作方式、一局预期流程、provisional 决策摘要;Visual 级必交证据)
- 冒烟用例(agent 生成,属 demo 交付物,不入 AgentBridgeTests)

### 4.6 机器冒烟

- v0 冒烟 = GameState API 直驱一局到终局零报错(不走 UI 点击)+ widget 创建冒烟 + 截图落盘;runner 复用既有 uat_runner / Automation Test 通路。
- runner 前置环境自检(Editor 在线/RC 端口/插件加载),自检不过算环境故障,不计入 demo 失败与自修轮次(与 Phase 13 发现 3 的 bridge 缺陷隔离归因)。
- v0 经 msc PROCEED 后冒烟用例冻结(hash 对账基线)。

### 4.7 维护文档包(后置投影,msc 裁决 2026-06-11)

- **时机后置,绝不前置**:每批功能 story 全部 verified 后,该批末尾的文档 story 才执行;文档只描述已存在且已验证的东西。
- **单一事实源 + agent 叙述**:结构性内容(系统清单/依赖/决策记录/逐批变更)从机器产物(契约/story/provisional/velocity log)投影,头部标注"生成物,与 run 数据不一致时以数据为准";叙述性内容(设计意图/架构讲解)由刚完成实施的 agent 起草。
- 清单(CCGS 模板按本质裁剪映射):demo 设计文档(系统总览+全部设计决策含 provisional 依据)、架构文档(plugin 结构/类职责/数据资产/扩展点)、changelog(v0→vN 逐批)、demo_plan 人读版(一次性投影)、评审留痕汇编(msc 裁决+合成包审批,窗口后追加)。art bible 本期不生成。
- 落点:`Plugins/Demo_MonopolyAuction/Docs/`(demo 自包含,随 plugin 删除/重建;不入项目层 Docs/,后者归 document-release 管)。
- submit 校验:文档存在 + 引用对账(文档提到的类/资产必须真实存在)。

## 5. 失败路径与错误处理

### 5.1 v0 自修循环与里程碑

两道里程碑:(a) plugin 骨架可编译;(b) 完整 loop 冒烟通过。每道自修上限默认 5 轮(plan 阶段可调),超限即停——不硬凑、不降判据,落盘失败报告进 PIVOT 评估。无人值守是判据组成部分:v0 段任何人工干预如实记录,该 run 标记"未达成无人值守"(可继续,判据如实降级)。

### 5.2 中断与事务

story 状态机可重入:in_progress 可重新 fetch 续作;submit 走 `.part` 事务;会话中断不产生半成品状态。

### 5.3 试玩窗口三向裁决

- **PROCEED**:批合成包,进增量批。
- **PIVOT**:写 pivot note(什么成立/什么不成立/修什么),demo plugin 整体删除重建,重跑 v0;不设硬上限但逐次落盘归因,连续同因 PIVOT 升级为 KILL 评估。
- **KILL**:失败归档(归因+可复用残值+教训),Phase 14 以"实证失败"收尾——合法产出。

### 5.4 增量批失败不毁 v0

v0 回归被破(hash 变/用例红)→ submit 拒;自修超限 → 增量批失败落盘,v0 保持有效交付物。

### 5.5 provisional 决策

GDD 未规定的设计点:agent 给默认值 + 记入 `provisional_decisions[]`(决策/依据/影响面),不许中途问人;msc 试玩窗口批量裁决,需改的转为下一批 story。

### 5.6 velocity log

逐 story、逐自修轮记录时间戳与结果,落 `ProjectState/runs/<run_id>/velocity_log.json`;Phase 15 扇出成本估算的唯一实测依据。

## 6. 测试

- **等价回归先行**:既有 13 Stage / 364 case 全绿保持;demo_plan 为纯新增环节,Stage 1-7 代码零改动。
- 新增 pytest(`Plugins/AgentBridge/Tests/scripts/`,登记系统测试 Stage 14;`run_system_tests.py` TOTAL_CASES 同步):demo_plan 切批确定性 golden、机制零游戏语义检查(机制代码不得出现 monopoly/auction 等领域词)、story schema 校验、fetch/submit 状态机与重入、evidence_class 分级校验、v0 hash 守门、施工规范版本对账、文档 story 引用对账。
- 新 schema(demo_plan / demo_story)入 `validate_examples.py --strict` examples 体系。
- 红线:`AgentBridgeTests/` 稳定区零改动;agent 生成的冒烟用例属 demo 交付物,不入插件测试体系。

## 7. 验收判据(6 条)

| # | 层 | 判据 |
|---|---|---|
| C1 | 机器 | 新增 pytest 全绿 + 364 等价回归全绿 + schema strict 全过 |
| C2 | 实战 | demo_plan 对验收 GDD 产出标准答案:v0 批=16 库内 capability(+文档 story),增量批=拍卖+股票,批内拓扑序正确 |
| C3 | 真机 | **v0 无人值守实证**:首次 fetch 到 v0 submit verified 零人工干预(驱动形态——headless 会话或 driver 脚本——由 plan 定,判据只看零干预);`Plugins/Demo_MonopolyAuction/` 编译过+一局驱动到终局零报错+截图落盘+试玩 README+文档包齐全(机器校验);干预/超限如实降级记录 |
| C4 | 人 | msc 试玩 v0,PROCEED/PIVOT/KILL 裁决留痕 |
| C5 | 真机+人 | 增量批 1(拍卖)实施后:v0 冒烟 hash 不变且全绿 + 拍卖用例绿 + 文档包更新过校验 + msc 试玩 v1 终裁 |
| C6 | 接口 | 两个新 MCP 工具注册成功(55→57)、工具契约过校验(Codex 可接入,本期不实证) |

证据一律落 `ProjectState/Reports/` + `ProjectState/Evidence/`。

**如实记录条款**:C3 是本期最大赌注("agent 无人值守写出可玩 v0"至今无实证)。C3/C5 失败不掩盖、不降判据硬凑;KILL + 归因归档是合法收尾;C1/C2/C6(机制层)独立计算成败。

## 8. 治理条款

- 防固化守则(Phase 13 spec §5.3)继续强制:demo_plan/story/submit 机制代码零游戏领域语义(测试守门,见 §6)。
- Phase 13 合成包人审 gate 原位不动(机器强制,不设旁路)。
- 新增 agent 交互面一律 MCP(双端中立);harness 专属机制只用于工程治理。
- 稳定区红线(CLAUDE.md"绝对不要修改"清单)不触碰。

## 9. 风险与缓解

| 风险 | 缓解 |
|---|---|
| v0 16-capability 整体生成失败率高(最大赌注) | 两道里程碑+自修上限;PIVOT 删 plugin 重建零残留;KILL 合法收尾;velocity log 留实测 |
| agent 链接依赖手写 MMonopoly* 混淆实证 | 施工规范禁依赖清单 + submit 机器校验 include/模块依赖 |
| agent 改 v0 冒烟用例"作弊"过增量门禁 | PROCEED 后用例冻结,submit hash 对账 |
| 冒烟 runner 受既有 bridge 缺陷(RC 404 等)拖累 | 前置环境自检,环境故障与 demo 失败分离归因 |
| 文档包变成新的"文档先行" | 文档 story 机械排批末,且只在功能 story 全 verified 后执行 |
| demo_plan 切批规则被游戏语义渗透固化 | 零领域语义机器检查入测试 |

## 10. 关键决策记录(brainstorming 用户裁决,2026-06-11)

1. 范围 = v0 + 一次增量批(拍卖);扇出/挑选留 Phase 15。
2. 载体 = 独立 runtime plugin,禁依赖手写 MMonopoly*。
3. GDD = monopoly_extended_auction_v1(一次只测一个未知)。
4. 可玩判据 = 机器冒烟(回归)+ msc 试玩(终裁)。
5. 双端 = 接口 MCP 中立 + Claude Code 单端实证。
6. 架构 = 方案 A:v0 单 agent 整体生成,增量 dev-story 式逐 story 闭环。
7. 维护文档包要生成(msc 明确要求,后期维护需要),但后置投影式:批末文档 story、单一事实源、art bible 本期不生成、落 plugin 内 Docs/。
8. v0 交付物含试玩说明 README(Visual 级必交证据)。
