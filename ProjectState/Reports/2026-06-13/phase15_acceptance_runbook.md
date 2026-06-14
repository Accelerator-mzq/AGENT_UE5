# Phase 15 验收 runbook(呈现增量轴 + 反馈回流通道)

> 日期:2026-06-13(发起)
> 分支:`feat/phase15-presentation-axis`(机制层已合 main,PR #47,merge commit cc2a005)
> 范围:C1-C6 验收(沿用 Phase 14 形状);机制层已 Ready to merge,本 runbook 跑验收
> 验收 run:`ProjectState/runs/run-p15-acceptance/`(Phase 14 run `run-20260611-052252-5101` 的副本——保 Phase 14 run 原样作证据)

## 判据总览

| 判据 | 内容 | 状态 |
|---|---|---|
| C1 | 机器全绿(pytest 46+56 / strict 32 / Stage 15+14 / 工具 58) | ✅ 通过(2026-06-13 主会话亲跑) |
| C2 | 切批标准答案(amend 后呈现 3 批 golden) | ✅ 通过(2026-06-13,golden ALL PASS) |
| C3 | 无人值守 rung1+rung2(presentation-1/2 全 story verified) | 🔄 进行中(编辑器 `E:\Epic Games\UE_5.5` 已定位) |
| C4 | 窗口 1 + 回流闭环(msc 试玩 2D + 反馈批) | ⏸ 待 msc(依赖 C3) |
| C5 | 无人值守 rung3(3D) | ⏸ 待 C3 |
| C6 | 窗口 2 终裁 | ⏸ 待 msc(依赖 C5) |

> 环境更正(2026-06-13):先前误报"编辑器不可用"——只搜了 C:/D: 盘。实际引擎在 **E 盘**:`E:\Epic Games\UE_5.5`(Phase 14 日志 BuildId=37670630 + 注册表 `HKLM\SOFTWARE\EpicGames\Unreal Engine\5.5` 确认)。`UnrealEditor-Cmd.exe` + `Build.bat` 均在,runner precheck = ready。C3/C5 走 commandlet 模式(无需常驻 RC 编辑器)。`AGENTBRIDGE_UE_CMD = E:\Epic Games\UE_5.5\Engine\Binaries\Win64\UnrealEditor-Cmd.exe`。

## C1 — 机器全绿 ✅

主会话亲跑(2026-06-13),证据 `ProjectState/Reports/2026-06-13/phase15_mechanism_verification.md`:
- pytest `-k phase15` = 46 passed;`-k phase14` = 56 passed
- `validate_examples.py --strict` = 32/32
- 系统测试 Stage 15 PRX-01~46 / Stage 14 全 PASS,TOTAL_CASES = 466(15 stage)
- `len(ALL_TOOLS)` = 58;红线 diff 空

## C2 — 切批标准答案(golden) ✅

驱动:`python Plugins/AgentBridge/Scripts/demo_plan_main.py --run-dir ProjectState/runs/run-p15-acceptance --amend-presentation --ladder ProjectInputs/PresentationLadder/monopoly_demo_ladder.json`
结果:`[OK] amend 落盘: +3 批 / +10 story`(CLI 自带 schema 自校验通过)。

golden 断言(2026-06-13,**ALL PASS**):
- 批序 = `v0 / increment-1 / increment-2 / presentation-1 / presentation-2 / presentation-3`
- plan_schema_version 升 1.1.0
- story 数 = presentation-1:3(2+doc)/ presentation-2:3 / presentation-3:4(3+doc)
- **presentation-1 首 story 锚在 `story-increment-1-docs`(最后一个全 verified 批末位;increment-2 pending 未作锚也未阻塞)** — 关键行为
- 链式:presentation-2 首挂 `story-presentation-1-docs`;presentation-3 首挂 `story-presentation-2-docs`
- increment-2(股票留批)仍 pending,未被动
- 各批末位为文档 story
- rung3 supersedes 带入 `MADemoPresentationRung2Tests.cpp`
- presentation-1 hud-panels 带 3 条 interaction_claims + ladder_rung_path 指向阶梯实例

C2 实证:呈现阶梯机制在真实 Phase 14 run 上正确切出三批呈现增量,锚点/链式/留批不挡/supersedes/claims 全部符合设计。

## C3 — presentation 无人值守(进行中)

### presentation-1 hud-panels ✅ verified(2026-06-13)

无人值守管线端到端跑通第一个呈现 story:fetch → coding agent 真机面板化 → 编译 exit 0 → 冒烟 21/21 → 截图 → **门禁 submit verified**(story_status=verified,errors[],attempts 0)。
- **可见证据**:`ProjectState/Evidence/p15_pres1_hud.png` 显示结构化面板——深蓝指示区(回合/阶段/当前玩家)、4 张横排玩家卡片、**P1 当前玩家金色高亮(◀ + 黄边)**、每卡绿色资金条、底部提示条。与旧文字行明显不同。主会话亲验截图内容。
- **行为门禁**:InteractionSemantics.Space/Enter/Esc 三键 + 4 个 PresentationContract 用例全 Success;README 键位节对账过。
- 改动面:`MADemoHUD.cpp`(Canvas HUD 面板化)+ `MADemoPresentationConfig.h/.cpp`(配色 DataAsset)+ 2 测试文件 + README;冻结文件 `MADemoSmokeTests.cpp` 未动;`FMADemoHUDSnapshot` 未改;玩法逻辑未改。

**两个真实发现(主会话独立核查抓出,非 agent 声称)**:
1. **面板化改对层**:agent 首轮把面板化做在了 UMG widget(`MADemoHUDWidget`),但 demo 可见 HUD 是 Canvas 版 `AMADemoHUD`(HUDClass 每帧最上层即时绘制,UMG widget 自 Phase 14 起被遮挡)。首轮机器证据全绿但截图仍是旧文字——空验证。主会话亲验截图发现后 redirect 改到 Canvas 层,面板才真正可见。教训:呈现批必须人/主会话亲验截图,机器门禁查不出"截图内容是旧的"。
2. **stale v0 基线**:基底 run `run-20260611-052252-5101` 是早期 dev run,其 v0 基线冻结于 2026-06-11 的 `MADemoSmokeTests.cpp`,而当前 HEAD 是 Phase 14 最终版(经试玩反馈修复轮改过)。主会话 hash 对账发现不匹配(非 agent 改文件),按"Phase 15 新验收"口径 re-freeze v0 基线对齐当前 Phase 14-final 状态(2026-06-13T12:24)。

**P15 验收期 backlog**:
- **P15A-BL-01(runner 观测)**:`demo_smoke/runner.py` 多段回归在 UE 5.5 下,regression 段偶尔只写 index.html 不写 index.json → build_smoke_report 抛 EnvironmentFault → 误归因退出码 3(实际 regression_1.log 显示 TEST COMPLETE EXIT CODE 0、测试全过)。最终报告仍有效(status/v0_regression=pass)。需查 UE 5.5 ReportExportPath 第二段不写 json 的根因。

### presentation-1 frontend-panels ✅ verified(2026-06-13)

前台外壳(开始/主菜单/设置/暂停/结果)Canvas 层(`AMADemoHUD::DrawShellPanel`)从裸文字条目升级为标题区+按钮样式块布局(首按钮高亮)。截图主会话亲验(`p15_pres1_frontend_menu.png` 等显示真按钮面板);冒烟 26/26 pass、v0 回归 pass、5 个 FrontendPanelContract 用例 Success;门禁 verified。无 interaction_claims(前台导航不在键盘 claims),行为门放行。

### presentation-1 docs ✅ verified → **presentation-1(rung 1)完整闭环**

demo Docs changelog + architecture 投影呈现层(可见 HUD=Canvas `AMADemoHUD`、呈现配置 DataAsset `UMADemoPresentationConfig` 扩展点),引用对账过;门禁 verified。
**rung1 层已冻结**(`evidence_validator.freeze_layer`):`rung1-contract`(MADemoPresentationContractTests.cpp)+ `rung1-impl`(MADemoPresentationRung1Tests.cpp)——presentation-2/3 不得改,不退化锚点。

**P15A-BL-02(机制缝)**:`evidence_validator` 第 1b 段"呈现批截图必交"对 presentation 批的**所有** story 触发,含 documentation kind 文档 story——文档 story 本不该需截图。当前以"附所述面板截图"务实绕过,机制应改为 `startswith("presentation") and story_kind != "documentation"`。

### presentation-2(2D 棋盘)✅ 完整 verified(2026-06-13)

- **board-2d**(`AMADemoHUD::DrawBoard2D`):方形环 28 地块 + 地产组配色 + 归属 + 拍卖高亮;契约/实现用例各 5,冒烟 36/36;`p15_pres2_board.png` 主会话亲验。
- **board-tokens**:玩家 token(各色+编号)随位置移动 + 当前玩家白描边高亮 + 同格错开;Space claim 由 rung1 InteractionSemantics.Space 守门;冒烟 40/40;`p15_pres2_tokens.png` 主会话亲验。
- **docs**:changelog 投影 2D 棋盘层。
- **rung2 层已冻结**:`rung2-contract` + `rung2-impl`(presentation-3 经 supersedes 退役 rung2-impl)。

**C3 进度**:rung1 + rung2 全 verified(6 story);rung3(3D)待窗口 1 后执行。

## C4 — 窗口 1(msc 试玩 2D 版,回流闭环)✅ 完成(2026-06-13)

msc 试玩 2D 版**认可无真实问题**。按诚实条款走演练回流闭环(显式标注"演练",不冒充真实反馈),用真实小改进实证通道:
- `demo_feedback_log` 登记演练条目 fb-w1-01(token 偏小,期望放大)→ status open
- `--amend-feedback` 确定性切 feedback-1 批(锚在 presentation-2-docs)→ 条目 in_batch
- coding agent 机制内修复:`AMADemoHUD::DrawBoard2D` token 放大(14/18px + 3px 白描边 + 黄三角浮标),尺寸进 DataAsset
- 经证据门 submit verified → **反馈条目机制流转 `resolved`**;5 个冻结层(v0 + rung1/rung2 契约/实现)hash 全 OK、冒烟 40/40 不退化
- feedback-1-docs verified

**回流闭环端到端实证(BL-06 次轴)**:试玩反馈 → 登记 → 切批 → 机制内修复 → 复验 → resolved。证据 `p15_fb1_tokens.png`(token 放大对比 `p15_pres2_tokens.png`)。

## C5 — rung3(3D 场景化)无人值守 ✅ 完成(2026-06-13/14,最大赌注实证成立)

3D 无人值守做成了(经 1 轮 redirect)。3 个 capability + docs 全 verified:
- **board-3d** ✅:`AMADemoBoard3DActor` 程序化 28 地块 Cube mesh 方形环 + 动态材质 ColorBoost 着色 + 60cm 立体高度 + FindLookAtRotation 斜俯视相机;落 L_MonopolyDemo 运行时构建。**关键事件**:第一轮 agent 把 2D Canvas 叠加层误当 3D(机器全绿但截图是灰地面),主会话亲验截图抓出 → redirect 修材质/相机/光照 → 真彩色立体 3D 棋盘(`p15_pres3_board3d.png`)。
- **pawn-actors** ✅:3D 圆柱棋子随 GameState 位置移动 + 当前玩家白高亮(`p15_pres3_pawns.png`)。
- **camera-integration** ✅:相机整合 + **Canvas 2D 棋盘退役**(移除 DrawBoard2D 调用),HUD 面板叠加保留;rung2-impl 经阶梯 supersedes 豁免退役——**spec §4.6 冻结分层退役机制端到端实证**(`p15_pres3_camera.png` 确认 2D 退役)。
- **docs** ✅;**rung3 层已冻结**。

**C5 backlog(主会话亲跑 submit 暴露的机制缝)**:
- **P15A-BL-03(冻结基线 stale)**:rung 经 supersedes 退役某冻结层文件后,该层冻结基线未自动更新,导致后续不带该 supersedes 的 story(如批末文档 story)撞旧 hash。当前以"退役后 runbook 手动 re-freeze 该层到当前态"绕过。机制应在 supersedes 生效时更新/移除对应冻结层。
- **P15A-BL-04(文档对账误判)**:`_check_doc_references` 把 changelog 里反引号包裹的引擎资产路径(`/Engine/BasicShapes/Cube.Cube`)当 plugin Content 资产校验失败。引擎资产不在 plugin Content,文档不应被此卡。机制应排除 `/Engine/` 等引擎前缀,或仅校验 plugin 内资产。

**C5 视觉 provisional**:3D 地块颜色偏暗(BasicShapeMaterial PBR 光照限制)、棋子鲜艳度有限、直接落位无插值——窗口 2 msc 反馈可经回流通道调。

**全批次:presentation-1/2/3 + feedback-1 共 12 story 全 verified**。

## C6 — 窗口 2(msc 试玩 3D 版,Phase 15 终裁)✅ **PROCEED**(2026-06-14)

msc 试玩 3D 版,提一条真实反馈(棋子未完全立于 3D 地块)→ 走反馈回流通道(feedback-2,**真实反馈非演练**):
- `demo_feedback_log` 登记 fb-w2-01 → `--amend-feedback` 切 feedback-2 批
- 主会话亲读代码诊断根因(棋子无条件 ±PawnRadius 偏移推出格)→ coding agent 修复(PawnRadius 60→30 + 单人居中多人小偏移 + Z 贴顶面)→ submit verified → 条目 resolved → **msc 实机复验认可**
- 冒烟 54/54、全冻结层 hash OK

**Phase 15 终裁:PROCEED**(msc,2026-06-14)。

## 验收总结:C1-C6 全闭环,14/14 story verified

| 判据 | 结果 |
|---|---|
| C1 机器全绿 | ✅ |
| C2 切批 golden | ✅ |
| C3 rung1+rung2 无人值守 | ✅ 6 story(HUD/前台面板 + 2D 棋盘/token) |
| C4 窗口 1 + 回流 | ✅ 演练反馈闭环(BL-06) |
| C5 rung3(3D)无人值守 | ✅ 3 story(3D 棋盘/棋子/相机,2D 退役)——最大赌注实证成立(经 1 轮 redirect) |
| C6 窗口 2 终裁 | ✅ **PROCEED**;真实反馈回流闭环(feedback-2) |

**呈现增量轴**(文字→面板→2D 棋盘→3D)+ **反馈回流通道**(两窗口,演练+真实各一)两条主轴全部实证。14 story = presentation-1/2/3(10)+ feedback-1/2(4)全 verified;六个冻结 rung 层守不退化。

**两窗口反馈回流对照**:窗口 1(C4)演练条目实证机制通道;窗口 2(C6)真实试玩反馈(棋子定位)经同一通道闭环修复 + msc 复验——**真实反馈端到端走通,BL-06 双重实证**。

**验收期 backlog**(P15A-BL-01~04,主会话亲跑暴露):runner UE5.5 回归段 index.json quirk / 呈现批截图门误触发文档 story / supersedes 退役后冻结基线 stale / 文档对账误判引擎资产路径。另:**呈现契约用例测"数据可达"过但截图视觉(彩色/立体/对齐)需人亲验**——3D 两轮、棋子一轮都是机器全绿但视觉问题靠主会话亲验/msc 试玩抓出,记为 P15A-BL-05(呈现批视觉验证机制缺口)。

## C5 — presentation 无人值守 rung3(3D)

环境就绪(同 C3)。待 presentation-1/2 完成 + 窗口 1 后执行。

## C3 环境(已就绪)

**阻塞原因(2026-06-13 实测)**:
- RC 30010 不可达(HTTP 000,2s 超时)— 无在线编辑器
- `AGENTBRIDGE_UE_CMD` 未设;常见安装位(C:/D: 的 Epic Games/UE_*)均未找到 `UnrealEditor-Cmd.exe`
- coding agent 无人值守需:编辑器编译 C++/UMG + Automation 冒烟 + `-game` HighResShot 真实截图(施工规范 §0/§4/§7)

evidence_validator 的呈现批门禁(截图必交 + 行为校验 + 冻结分层 + 冒烟 pass)无编辑器无法满足;按"宣称成功必须附证据"原则,**不在无编辑器下写无法验证的 demo 代码**。

**解门所需(任一)**:
1. msc 提供 `AGENTBRIDGE_UE_CMD`(UnrealEditor-Cmd.exe 绝对路径)+ 拉起编辑器(或允许 commandlet 模式),则可驱动 coding agent 跑 presentation-1(UMG 面板,最低风险 rung)起步;
2. 或 msc 指明本机 UE 安装路径,我设环境变量后续作。

**C3 流程(解门后)**:fetch story-presentation-1-hud-panels → coding agent 写 UMG 面板(只读 GameState 快照,呈现契约用例 + InteractionSemantics 用例)→ 编译 + 冒烟 + 截图 → submit(行为门禁 + 截图必交)→ presentation-1 全 verified 后 runbook 调 `evidence_validator.freeze_layer` 冻 `rung1-contract`/`rung1-impl` 层 → presentation-2 同构。

## C4 / C6 — msc 试玩两窗口(待 msc)

- **窗口 1(C4,rung2 后)**:msc 试玩 2D 棋盘版 → `demo_feedback_log` 登记反馈 → `--amend-feedback` 切 feedback 批 → coding agent 修复 → 复验(回流闭环实证)。诚实条款:若零真实反馈,用显式标注"演练"的合成条目实证机制通道。
- **窗口 2(C6,rung3 后)**:msc 试玩 3D 版 → Phase 15 终裁(PROCEED / PIVOT / KILL)。

## 当前结论

机制层验收 C1/C2 自动闭环(机器证据全绿 + 切批 golden 在真实 run 上 ALL PASS)。C3+ 卡在 UE 编辑器不可用——这正是 Phase 15 真正的赌注(3D 批无人值守),需真机方能实证。待 msc 提供编辑器路径/拉起编辑器后续作 C3。
