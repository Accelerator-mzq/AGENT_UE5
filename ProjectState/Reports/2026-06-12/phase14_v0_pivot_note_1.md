# Phase 14 v0 PIVOT Note #1

> 裁决:msc,2026-06-12,C4 人审窗口 1。本次为 Phase 14 首次 PIVOT(spec §5.3:不设硬上限,逐次落盘归因,连续同因升级 KILL 评估)。

## 裁决与归因

**PIVOT 理由**:v0 一号尝试(`Demo_MonopolyAuction`,attempt 1)机器面全绿(17/17 verified、冒烟 7/7、编译过、自修 2+0 轮),但**无 authored 启动关卡与交互入口,人无法实际游玩**——"可玩"在 msc 语义(键盘玩一局)与机器门禁语义(GameState API 直驱 loop)之间存在定义缝。

**根因三层**(详见 runbook C4 问答记录):
1. 工具链:无人值守命令行无编辑器资产创建通路(bridge 资产工具有 Phase 13 已知缺陷);
2. 机制门禁:施工规范/冒烟/证据分级没有任何一条要求 authored 资产——agent 按门禁施工且如实披露;
3. **spec 源头(根因)**:"可玩"被拆成机器 loop+人试玩两半,"人可交互地玩"从未成为 v0 的机器可校验交付物。责任在 spec 设计,agent 是缝的诚实暴露者。

## 一号尝试中成立的(attempt 2 保留复用)

- 无人值守机制全链工作:fetch/submit 证据门、velocity 留痕、provisional 留痕、自修轮纪律、环境故障归因分离
- 规则引擎设计与实现质量(GameMode/GameState/数据驱动 DataAsset/确定性骰子)——架构形状可在 attempt 2 重写时参考(代码已删,设计文档归档于 attempt1 证据)
- 冒烟测试形状(FullGameLoop 多种子直驱)继续作为回归基线的一部分

## 不成立的(attempt 2 修正)

- v0 交付物缺"人可玩"硬判据 → 施工规范 v1.1.0 新增(见下)
- agent 无资产创建通路 → 规范新增 UnrealEditor-Cmd 编辑器 Python 通路

## 修正动作

1. 施工规范 1.0.1 → **1.1.0**:
   - §1 必含清单加 authored 启动关卡(`Content/Maps/` 下 .umap,WorldSettings 绑定 demo GameMode)
   - 新增 **v0 可玩硬判据**:`-game` 模式可启动进入对局、键盘意图可推进游戏、HUD 呈现状态
   - §4 冒烟必含启动关卡加载用例(地图加载+GameMode/GameState 类校验+HUD 于关卡上下文创建)
   - 新增 §7 无人值守资产创建通路(UnrealEditor-Cmd -run=pythonscript;WBP 非必需,HUD 允许 C++ CreateWidget)
2. 删除 `Plugins/Demo_MonopolyAuction/` 整体(PIVOT 零残留原则)
3. 重新生成 demo_plan(story 全部回 pending,盖 1.1.0 版本戳)
4. 重跑 v0(attempt 2,无人值守窗口重新起算,自修上限同 5 轮/里程碑)

## 一号尝试证据归档

`ProjectState/Evidence/phase14_v0_attempt1/`(冒烟报告×2/visual_dumps×9/渲染 PNG/设计文档副本);
velocity_log 不清空(历史事件保留,attempt 2 事件继续追加,以时间戳分界 2026-06-12T00:53:47Z)。
