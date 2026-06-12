# Phase 15 — 呈现增量轴 + 反馈回流通道设计(文字 HUD → 面板 → 2D 棋盘 → 3D 场景)

> 日期:2026-06-12
> 状态:设计定稿,待 msc 审阅后转 writing-plans
> 上游输入:Phase 14 收尾在册输入(task.md §5 / acceptance_report.md 附 4.4)+ msc 启动指令(2026-06-12)
> 关联:Phase 14 spec `2026-06-11-phase14-demo-first-design.md` / 验收 runbook `ProjectState/Reports/2026-06-12/phase14_acceptance_runbook.md`

## 1. 背景与目标

### 1.1 Phase 15 在册输入

1. **呈现/图形增量轴**(msc 试玩直接诉求,C4 PROCEED 时裁归 Phase 15):demo 只有文字 HUD,无图形页面;capability 切批机制缺呈现升级轴。
2. **试玩反馈回流无机制通道**(P14-BL-06):C4 修复轮(Enter/Esc 空操作)发生在 story 机制外,证据与 story 状态漂移。
3. 词表扩展 / Stage 1 模板固化(Phase 13 遗留)与 P14-BL-01~06 在 brainstorming 中评估纳入范围(裁决见 §2)。

### 1.2 范围红线(msc 裁决,2026-06-12,先于本设计)

**"扇出 N demo + 挑选会话层"维持去除状态,不纳入本期**;恢复需 msc 主动提出。本设计中所有机制(呈现阶梯/反馈批)按单 demo 设计,不为扇出预留显式接口。

### 1.3 目标(一句话)

把"呈现/图形"建成与玩法批同等地位的增量维度(机制能力),无人值守把 Demo_MonopolyAuction 的呈现从文字 HUD 逐级升到 3D 场景(面板 → 2D 棋盘 → 3D),并把试玩反馈回流建成机制内闭环(反馈批),人只在两个试玩窗口出现。

## 2. 范围定盘(brainstorming 裁决,2026-06-12)

| 决策点 | 裁决 |
|---|---|
| 呈现目标层级 | **Rung 3(3D 场景化)**:3D 棋盘 + 棋子 actor + 相机,HUD 叠加 |
| 爬梯方式 | **逐级三批**:presentation-1(UMG 面板)→ presentation-2(2D 棋盘)→ presentation-3(3D);每批结束 demo 仍可玩、冒烟全绿;3D 批失败时停在 rung2 仍是完整可玩交付 |
| backlog 纳入 | **推荐包**:纳入 BL-01(路径越界)/BL-04(errorMessage)/BL-05(行为校验)/BL-06(反馈回流=次轴);**不纳入** BL-02/BL-03/词表扩展与模板固化 |
| 人审窗口 | **两窗口**:窗口 1 = rung2 后试玩 2D 版(产生真实反馈,实证回流通道);窗口 2 = rung3 后终裁 |
| 呈现批来源机制 | **机制内置呈现阶梯(数据驱动)**:planner 增 presentation 轴,阶梯定义为项目层数据文件;不走 GDD 解析(避免被迫做词表扩展、避免动 Stage 1-3 稳定资产) |
| 反馈回流形状 | **反馈批模型(全 story 化)**:反馈登记 → 确定性转 feedback story 进 story_store → 走同一 fetch/submit 门禁 + 不退化守门 |

## 3. 总体架构与数据流

```
GDD(不改)→ Stage 1-3(零改动)→ demo_plan 切批
                                   ├─ 玩法批(v0 / increment-1 已 verified;increment-2 继续留批)
                                   ├─ [新] 呈现批 ×3(presentation-1/2/3,来源:项目层呈现阶梯数据)
                                   └─ [新] 反馈批(feedback-N,来源:试玩窗口反馈登记,确定性转换)
 → story_store 状态机(story_kind: capability / documentation / +feedback;依赖门/幂等/.part 不变)
 → MCP demo_story_fetch / demo_story_submit(双端中立;submit 新增行为校验门禁 = BL-05)
 → coding agent 实施(施工规范 1.1.0 → 1.2.0:§7 程序化 3D 通路 + 呈现层架构约束)
 → 机器冒烟(逐 rung 不退化:逻辑用例永冻 + 呈现契约用例逐 rung 冻结,见 §4.6)
 → 【窗口 1】rung2 后 msc 试玩:反馈登记 → feedback 批 → 机制内修复 → 复验
 → 【窗口 2】rung3 后 msc 试玩:Phase 15 终裁(PROCEED / PIVOT / KILL)
```

三个关键架构决定:

1. **呈现批不经 GDD/Stage 1-3,由项目层阶梯数据驱动**。"棋盘""token"等游戏语义全在项目层数据文件里,planner 机制代码保持零游戏语义(防固化守则不破)。代价是 GDD 输入纯度被稀释——施工规范已开"项目层人工输入"先例;"GDD 声明目标 rung → 阶梯映射"留作后续演进。
2. **planner 增加批次追加模式(amend)**,呈现批与反馈批共享同一机制入口:读现 run 的 demo_plan + story 状态,把新批追加到已 verified 批序列末尾,已有批一字不动。Phase 14 的 run 数据(v0/increment-1 verified、increment-2 留批)原样保值。
3. **冻结分层**(逻辑 / 呈现契约 / 呈现实现三层,§4.6):呈现是"升级替换"不是纯叠加(3D 上线后 2D 棋盘退役),"不退化"判据必须按层定义,否则 rung3 撞 rung2 守门。

## 4. 组件设计

### 4.1 呈现阶梯(presentation ladder)

- **插件层**:`presentation_ladder.schema.json`(新 Schema);planner 读取与展开机制。
- **项目层实例**:`ProjectInputs/PresentationLadder/monopoly_demo_ladder.json`,随实施 plan 一并起草、**实施启动前**经 msc 审定——归输入端(性质同 GDD/施工规范),不构成中途人审,与"决策两端化"不冲突;agent 从 GDD 自动生成阶梯草案属后续演进,本期 YAGNI。
- rung 定义字段:`rung_id`(1/2/3)、呈现要求清单(文本,GDD 锚点可选)、批内 story 切分(见 §4.5)、每 story 显式 `evidence_class`(不走 domain_type 机械映射)、`interaction_claims`(交互宣称,喂行为校验)、`supersedes`(显式声明退役的下层实现用例,见 §4.6)。
- 确定性:同(现 plan + 阶梯实例)输入同输出,golden 测试守门。

### 4.2 planner amend 模式

- 入口:`demo_plan_main.py` 扩展(如 `--amend-presentation` / `--amend-feedback`,CLI 形态实施期定);零 LLM、确定性。
- 依赖规则机械化:追加批的首 story 挂在"当前最后一个已 verified 批的末位文档 story"上;presentation-N+1 挂 presentation-N 末位;**increment-2 留批不在已执行序列里,不挡呈现批**。
- `batch_id` 模式扩展:`^(v0|increment-[1-9][0-9]*|presentation-[1-9][0-9]*|feedback-[1-9][0-9]*)$`;`demo_plan.schema.json` / `demo_story.schema.json` 同步升版(`story_schema_version` / plan 版本 1.0.0 → 1.1.0,const 钉死;interaction_claims 字段同此版进入)。
- 每个追加批末尾保持机械追加文档 story(Phase 14 机制不变)。

### 4.3 行为校验门禁(BL-05)+ BL-01/04

story 新增 `interaction_claims` 字段(呈现批从阶梯数据带入;玩法/反馈批可选):

```json
"interaction_claims": [{"input": "Space", "behavior": "推进回合"}]
```

`evidence_validator` 新增三道对账(submit 阻塞,拒收附具体错误清单,沿用自修闭环):

1. **claim ↔ 用例**:每条 interaction_claim 必须在 test_report 中有对应 Automation 用例且 pass;用例形状钉死为 InteractionSemantics 模式(Phase 14 C4 修复轮实证:输入直驱 PlayerController 处理函数 → 断言 GameState 变化,机器可跑,不依赖 UI 点击模拟)。
2. **README ↔ claim**:README 键位表宣称 ⊆ interaction_claims 并集(防"文档写了键位、代码没行为")。
3. **截图存在性**:呈现 story 截图必交且文件真实落盘。

同模块顺手修复:

- **BL-01**:路径型证据字段统一 `resolve()` + `is_relative_to(项目根)`(同 MCP `plugin_root` 口径),越界即拒。
- **BL-04**:smoke 报告 suites 透传 UE `errorMessage` 详情(3D 批无人值守失败排障的直接依赖)。

### 4.4 反馈批机制(BL-06 根治)

- **新 Schema**:`feedback_entry.schema.json`:`{feedback_id, window_id, phenomenon(现象), expectation(期望), severity(blocker|major|minor), related_rung/related_capability(可选), status(open|in_batch|resolved)}`;实例落 `ProjectState/runs/<run_id>/feedback/`。
- **登记**:新 MCP 工具 `demo_feedback_log`(单条登记;工具数 57→58;双端中立,试玩窗口由会话 agent 替 msc 登记);查询走文件/CLI,不加查询工具(YAGNI)。
- **转换**:planner amend 吃 open 状态反馈条目,确定性切 `feedback-N` 批(每窗口一批,每条反馈一个 story,机械规则零 LLM);`story_kind = feedback`,materials 引用反馈条目路径 + 相关原 story。
- **修复**:走同一 fetch/submit 完整门禁;附加校验 = 全部已冻结层(逻辑 + 各已验收 rung 呈现契约)hash 不变且全绿。
- **闭环**:反馈条目状态机 `open → in_batch → resolved`;批全 verified 后窗口复验。
- **边界**:反馈批只吃结构化功能反馈;PIVOT 级方向性裁决不进反馈批,沿用 Phase 14 PIVOT note 机制。

### 4.5 demo 侧三个 rung 交付物(阶梯实例的设计基线)

- **presentation-1(2 story + 1 文档 story)**:
  1. HUD 面板化:5 行文本 → 回合/阶段指示器、玩家卡片(色块+资金条)、拍卖弹窗面板、事件提示区;纯 Slate/UMG 代码构建 + 程序化配色;`FMADemoHUDSnapshot` 快照接口不变。
  2. 前台外壳面板化:presence_only 文本条目 → 真按钮 + 布局(开始/主菜单/设置/暂停/结果)。
- **presentation-2(2 story + 1 文档 story)**:
  1. 2D 棋盘渲染:环形地块布局、地产组配色、归属/拍卖中高亮,数据从 GameState 快照拉。
  2. token 动态:玩家棋子随位置移动(插值可选)、当前回合玩家高亮。
- **presentation-3(3 story + 1 文档 story)**:
  1. 程序化 3D 棋盘:引擎基础几何拼地块环 + 动态材质实例着色 + 地块标签;落现关卡 `L_MonopolyDemo`(演进非重建)。
  2. 棋子 actor + 插值移动(GameState 位置驱动)。
  3. 相机 + 整合:固定机位 CameraActor(简单插值运镜),HUD 面板(rung1 产物)叠加保留,**2D 棋盘 widget 退役**(走 §4.6 supersedes 声明)。

### 4.6 冻结分层与 supersedes 机制(关键架构决定)

| 层 | 冻结策略 | 例 |
|---|---|---|
| 逻辑冒烟用例 | 永久冻结(hash 不变 + 全绿),Phase 14 现状 | 一局驱动到终局零报错 |
| 呈现契约用例 | 每 rung 验收后冻结;断言**信息可见性**(状态经快照可达 + 呈现入口存在),不绑具体 widget 类 | "拍卖进行时,呈现层能暴露当前拍卖地块与当前价" |
| 呈现实现用例 | 不冻结;随 rung 替换可退役,但退役必须在阶梯数据 `supersedes` 字段显式声明,机制核对声明才放行 hash 变更 | "2D 棋盘 widget 存在" |

呈现契约用例样例(钉死形状,防实施期再现"可玩定义缝"):

```cpp
// 呈现契约用例:实现无关,断言信息可见性,经快照接口取值。
// 契约:拍卖进行时,呈现层必须能取到当前拍卖地块与当前价。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoPresentationContract_AuctionInfo, ...)
bool FMADemoPresentationContract_AuctionInfo::RunTest(const FString&)
{
    // 1. GameState API 直驱一局进入拍卖阶段(不走 UI 点击)
    // 2. 经呈现快照接口(BuildSnapshot 或其继任契约)取快照
    // 3. 断言:快照含拍卖地块标识(非空)与当前价(>0)
    // 4. 断言:呈现入口存在(viewport 中存在注册的呈现根)
    // 禁止:断言任何具体 widget 类名/控件树结构(那属实现用例)
}
```

### 4.7 施工规范 1.1.0 → 1.2.0(项目层实例,注入机制不变)

- **§7 资产通路扩展**:程序化 3D 通路 = 引擎自带基础几何(Cube/Plane/Cylinder/Sphere)+ 动态材质实例程序化配色 + authored 关卡 actor 摆放(在 Phase 14 已实证关卡通路上扩展);**禁外部资产导入**(无美术管线);相机限定固定机位 + 简单插值,禁复杂 cinematic。
- **新增呈现层架构约束章节**:呈现只读 GameState 快照;呈现组件三层独立可替换(HUD 面板 / 棋盘渲染 / 世界 actor);配色/布局参数数据驱动(DataAsset);呈现批不得改玩法逻辑文件(冻结 hash 守门技术钉死)。
- 既有约束(TObjectPtr/禁热路径字符串/禁无谓 Tick/中文注释等)沿用。

## 5. 非目标 / YAGNI(记 backlog 或留后续 Phase)

- 扇出 N demo + 挑选会话层(msc 裁决去除,恢复需 msc 主动提出)
- 词表扩展 / Stage 1 模板固化(待下一份非 Monopoly GDD 提供真实实证压力)
- P14-BL-02(文档对账裸写类名)/ P14-BL-03(velocity JSONL,扇出去除后无真实痛点)
- increment-2(股票市场):继续留批不执行
- 外部美术资产管线 / art bible
- 阶梯实例的 GDD 自动生成(本期人写)
- 反馈查询 MCP 工具(文件/CLI 足够)

## 6. 测试策略

- **机制层 pytest**(纯 Python):planner amend golden(呈现批追加/反馈批追加/依赖规则/increment-2 不挡/成环 fail-closed);`presentation_ladder` / `feedback_entry` schema + examples 入 strict 校验;evidence_validator 三道行为对账 + BL-01 越界 + BL-04 errorMessage;story_store feedback 流转(状态机/幂等/.part)。
- **系统测试**:新增 Stage 15 登记(纯 Python),`run_system_tests.py` TOTAL_CASES 与 `SystemTestCases.md` 同步(具体条数实施期定,权威源不变)。
- **demo 侧**(agent 生成,属 demo 交付物,不入 AgentBridgeTests):各 rung 呈现契约用例 + 实现用例 + InteractionSemantics 用例;冒烟 runner 扩展逐 rung 冒烟与冻结层校验。
- **Schema 数**:47 → 49(+presentation_ladder +feedback_entry);**MCP 工具数**:57 → 58(+demo_feedback_log),真实 stdio 实测,contracts 主表登记同步。

## 7. 验收判据(C 系,沿用 Phase 14 形状)

| 判据 | 内容 |
|---|---|
| C1 机器全绿 | pytest phase15 全绿 + strict 全过 + Stage 15 + 全量等价 + 工具数 58 |
| C2 切批标准答案 | amend 后呈现 3 批的批次数/story 数/拓扑序/依赖挂点机器断言(golden) |
| C3 无人值守 rung1+rung2 | presentation-1/2 全 story verified,行为校验过,截图真实 |
| C4 窗口 1 + 回流闭环 | msc 试玩 2D 版;反馈登记 → feedback 批 → 机制内修复 → 复验。**诚实条款**:若真实反馈为零,以显式标注"演练"的合成条目实证机制通道,不冒充真实反馈 |
| C5 无人值守 rung3 | presentation-3 全 story verified;逻辑冒烟 + 全部已冻结呈现契约不退化 |
| C6 窗口 2 终裁 | msc 试玩 3D 版,PROCEED / PIVOT / KILL |

接口中立随 C1 验:58 工具 stdio 可见,`demo_feedback_log` 可见。

## 8. 风险披露(如实)

1. **3D 批无人值守无实证先例**(Phase 14 只实证过 authored 关卡 + UMG)——本期最大赌注。缓解:逐级三批风险隔离(3D 失败时 demo 停在 rung2 仍是完整可玩交付)+ 施工规范 §7 先行扩展 + PIVOT/KILL 机制在位。
2. **呈现契约用例是新概念**,"信息可见性"断言可能再现 C3 式定义缝。缓解:§4.6 样例在 spec 层钉死形状,不留实施期解释空间。
3. **窗口 1 反馈样本不可控**。缓解:C4 诚实条款(演练条目显式标注)。
4. **环境预存问题**(遗留 headless UE Editor / Stage 4 stdin 阻塞,Phase 14 已知登记)。验收前处置,不计入 demo 失败归因。

## 9. 防固化条款(延续 Phase 13 spec §5.3 / Phase 14 spec §8)

- planner(含 amend)机制代码零游戏领域语义:切批只依赖通用结构字段(rung_id/story 切分/depends/supersedes/evidence_class),"棋盘""token"等语义只存在于项目层阶梯数据。
- 阶梯/反馈机制对任意 demo plugin 通用;Demo_MonopolyAuction 专属内容全部在项目层实例(阶梯 JSON/施工规范/GDD)。
- 红线不破:CLAUDE.md"绝对不要修改"清单(C++ 核心/bridge/orchestrator 核心/测试体系/稳定 Schema)零触碰;demo_story/demo_plan schema 属可改清单。

## 10. 收尾链

实施/验收完成后走项目标准收尾:`verification-before-completion → document-release(含 task.md 换页/contracts 登记/acceptance 附录/Reports 证据落盘)→ verification → finishing-a-development-branch`(merge 方式 msc 定)。
