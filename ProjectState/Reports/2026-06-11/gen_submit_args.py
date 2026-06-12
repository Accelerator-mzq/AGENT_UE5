# -*- coding: utf-8 -*-
"""Phase14 v0 submit args 生成器:为 17 个 v0 story 各产出 submit args JSON。
证据按 evidence_class 分级填充,路径一律项目根相对,plugin_root 固定。
不改任何机制代码;仅本会话产出 args 文件给 mcp_driver 喂入。
"""
import json
from pathlib import Path

SESSION = "ProjectState/runs/run-20260611-052252-5101"
PLUGIN_ROOT = "Plugins/Demo_MonopolyAuction"
SMOKE = "ProjectState/Evidence/phase14_v0_smoke_report.json"
RENDER = "ProjectState/Evidence/screenshots/demo_plugin_render_1280x720.png"
OUT_DIR = Path("ProjectState/Reports/2026-06-11/submit_args")
OUT_DIR.mkdir(parents=True, exist_ok=True)

SRC = f"{PLUGIN_ROOT}/Source/Demo_MonopolyAuction"

# 全量插件源文件(files_changed 通用集合)
FILES_ALL = [
    f"{PLUGIN_ROOT}/Demo_MonopolyAuction.uplugin",
    f"{PLUGIN_ROOT}/README.md",
    f"{SRC}/Demo_MonopolyAuction.Build.cs",
    f"{SRC}/Private/Demo_MonopolyAuctionModule.cpp",
    f"{SRC}/Private/MADemoBoardDataAsset.cpp",
    f"{SRC}/Private/MADemoFoundations.cpp",
    f"{SRC}/Private/MADemoFrontendWidgets.cpp",
    f"{SRC}/Private/MADemoGameMode.cpp",
    f"{SRC}/Private/MADemoGameState.cpp",
    f"{SRC}/Private/MADemoHUDWidget.cpp",
    f"{SRC}/Private/MADemoPlayerController.cpp",
    f"{SRC}/Private/MADemoPlayerData.cpp",
    f"{SRC}/Private/MADemoRulesDataAsset.cpp",
    f"{SRC}/Private/MADemoStockMarket.cpp",
    f"{SRC}/Private/Tests/MADemoSmokeTests.cpp",
    f"{SRC}/Private/Tests/MADemoVisualDumpTest.cpp",
    f"{SRC}/Public/Demo_MonopolyAuctionModule.h",
    f"{SRC}/Public/MADemoBoardDataAsset.h",
    f"{SRC}/Public/MADemoFoundations.h",
    f"{SRC}/Public/MADemoFrontendWidgets.h",
    f"{SRC}/Public/MADemoGameMode.h",
    f"{SRC}/Public/MADemoGameState.h",
    f"{SRC}/Public/MADemoHUDWidget.h",
    f"{SRC}/Public/MADemoPlayerController.h",
    f"{SRC}/Public/MADemoPlayerData.h",
    f"{SRC}/Public/MADemoRulesDataAsset.h",
    f"{SRC}/Public/MADemoStockMarket.h",
    f"{SRC}/Public/MADemoTypes.h",
]

# 截图证据降级统一披露(Visual 类)
SHOT_DEGRADE = {
    "decision": "Visual story 截图证据降级为:每 story 一份 widget 反射 dump(visual_dumps/*.json)+ 一张真实引擎渲染 PNG(1280x720 HighResShot)",
    "rationale": "本 demo UI 为 C++ UMG widget 基类,无 authored WBP 资产与 HUD 绑定关卡;无人值守命令行无法对每个具体页面做有意义渲染。按任务§7降级条款:用能产出的最接近物(反射 dump)替代,并如实披露;真实渲染 PNG 证明插件加载并渲染。",
    "scope": "全部 9 个 Visual 类 story 的截图证据"
}

# provisional 决策(各 story 专属)
PROV = {
    "story-skill-baseline-start-screen": [
        {"decision": "插件名定为 Demo_MonopolyAuction", "rationale": "施工规范§1 要求 Demo_ 前缀大驼峰,从契约 game_identity(monopoly_like)+扩展玩法(auction)派生", "scope": "整个 demo 插件命名"},
        {"decision": "开始画面标题用 '大富翁拍卖版 Demo'", "rationale": "GDD 1 未规定项目标识文案,给默认值", "scope": "start screen 标题"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-main-menu": [
        {"decision": "主菜单三按钮固定 New Game/Settings/Quit", "rationale": "契约 baseline-main-menu.required_elements 锁定", "scope": "主菜单"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-input-foundation": [
        {"decision": "默认键位 确认=Enter 取消=Esc 暂停=Esc 掷骰=Space", "rationale": "GDD 未规定具体键位,给约定俗成默认值", "scope": "输入底座默认绑定"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-settings": [
        {"decision": "设置持久化策略 = session_only", "rationale": "契约 clarification_markers cg-platform-persistence 的 provisional_default", "scope": "settings/platform 持久化"},
        {"decision": "默认分辨率 1280x720 / 窗口模式", "rationale": "GDD 未规定默认显示参数", "scope": "settings 默认显示项"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-audio-foundation": [
        {"decision": "音频底座仅记录音量与最近 SFX 标签,不绑定真实 SoundBase", "rationale": "presence_only baseline,真实音频资产由后续扇出补", "scope": "audio foundation"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-pause": [
        {"decision": "暂停四项 Resume/Settings/Quit to Menu + ESC 入口", "rationale": "契约 baseline-pause.required_elements 锁定", "scope": "pause"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-platform-foundation": [
        {"decision": "退出走 UKismetSystemLibrary::QuitGame;分辨率下限 640x480", "rationale": "契约 clarification_gated,GDD 未给硬边界,给安全默认", "scope": "platform foundation"},
        SHOT_DEGRADE,
    ],
    "story-skill-board-topology": [
        {"decision": "交易所角格选址 16 号(原机会格)", "rationale": "扩展 GDD 2.2 要求交易所替换一个普通空白格但未指定位置,选 16 号机会格", "scope": "棋盘 16 号格类型"},
    ],
    "story-skill-dice": [
        {"decision": "掷骰用 FRandomStream 确定性随机(seed 由 InitializeGame 传入)", "rationale": "GDD 3.4 未规定随机源;确定性流便于冒烟可复现断言", "scope": "骰子随机源"},
    ],
    "story-skill-tile-system": [
        {"decision": "Chance/Community/FreeParking/JailVisit/Exchange 落点 Phase1 无强制结算", "rationale": "GDD 3.2 明确 Phase1 这些格无事发生;交易所交易 UI 在 increment-2", "scope": "格子事件分发"},
    ],
    "story-skill-turn-loop": [
        {"decision": "僵局回合上限默认 200,达上限按净资产判最高者胜", "rationale": "契约 cg-max-game-length 高风险未决点;GDD 只给目标时长30-60min未给硬上限,给可收敛默认值", "scope": "回合上限与僵局收敛"},
        {"decision": "双数额外回合每玩家最多连掷10次保护", "rationale": "防御性上限,避免理论死循环;GDD 仅规定三连双入狱", "scope": "回合内重掷上限"},
    ],
    "story-skill-economy": [
        {"decision": "AutoBuyPolicy:买得起且留够保释金缓冲才买", "rationale": "无人值守需自动购买裁决;GDD 玩家自选,给保守自动策略避免立即破产", "scope": "无人值守购买策略"},
        {"decision": "破产清算:现金尽数转债主后退场,地产归无主", "rationale": "GDD 3.3 规定破产地产无主;不足额清算细节未规定,给简化全转", "scope": "破产清算"},
    ],
    "story-skill-player-management": [
        {"decision": "先手顺序按玩家索引固定(非随机)", "rationale": "GDD 3.1 提随机先手;为冒烟可复现改为固定顺序+确定性骰子", "scope": "先手顺序"},
        {"decision": "玩家棋子颜色用 6 色调色板", "rationale": "契约 cg-player-token-visual-style accept_with_safe_default", "scope": "玩家颜色"},
    ],
    "story-skill-baseline-hud": [
        {"decision": "HUD 快照含回合/当前玩家/各玩家现金+股值/骰子/3股摘要", "rationale": "GDD 4.1 常驻 + 扩展 4.1 股票常驻显示", "scope": "HUD 字段"},
        {"decision": "HUD 布局方式留待蓝图子类(C++ 仅供快照数据)", "rationale": "契约 cg-hud-layout-style send_to_design_space_discovery", "scope": "HUD 布局"},
        SHOT_DEGRADE,
    ],
    "story-skill-baseline-results": [
        {"decision": "结果页含胜者信息 + 返回主菜单", "rationale": "契约 baseline-results.required_elements 锁定", "scope": "results"},
        SHOT_DEGRADE,
    ],
    "story-skill-jail": [
        {"decision": "在狱掷双免费出狱并用该骰移动;满3回合强制付50出狱", "rationale": "GDD 监狱规则;不足额付保释则破产", "scope": "监狱出狱"},
    ],
}

# Visual 类(截图)与 Logic 类(test_report+smoke)分组
VISUAL = {
    "story-skill-baseline-start-screen", "story-skill-baseline-main-menu",
    "story-skill-baseline-input-foundation", "story-skill-baseline-settings",
    "story-skill-baseline-audio-foundation", "story-skill-baseline-pause",
    "story-skill-baseline-platform-foundation", "story-skill-baseline-hud",
    "story-skill-baseline-results",
}
# Visual story → 其专属 dump 文件
DUMP = {
    "story-skill-baseline-start-screen": "baseline-start-screen",
    "story-skill-baseline-main-menu": "baseline-main-menu",
    "story-skill-baseline-input-foundation": "baseline-input-foundation",
    "story-skill-baseline-settings": "baseline-settings",
    "story-skill-baseline-audio-foundation": "baseline-audio-foundation",
    "story-skill-baseline-pause": "baseline-pause",
    "story-skill-baseline-platform-foundation": "baseline-platform-foundation",
    "story-skill-baseline-hud": "baseline-hud",
    "story-skill-baseline-results": "baseline-results",
}
LOGIC = {
    "story-skill-board-topology", "story-skill-dice", "story-skill-tile-system",
    "story-skill-turn-loop", "story-skill-economy", "story-skill-player-management",
    "story-skill-jail",
}


def build(story_id):
    ev = {"files_changed": FILES_ALL, "plugin_root": PLUGIN_ROOT,
          "provisional_decisions": PROV.get(story_id, [])}
    if story_id in VISUAL:
        dump = f"ProjectState/Evidence/visual_dumps/{DUMP[story_id]}.json"
        ev["screenshots"] = [dump, RENDER]
    elif story_id in LOGIC:
        ev["test_report"] = SMOKE
        ev["smoke_report"] = SMOKE
    return {"session_path": SESSION, "story_id": story_id, "evidence": ev}


for sid in list(VISUAL) + list(LOGIC):
    path = OUT_DIR / f"{sid}.json"
    path.write_text(json.dumps(build(sid), ensure_ascii=False, indent=2), encoding="utf-8")

print(f"已生成 {len(VISUAL) + len(LOGIC)} 个 args 文件 → {OUT_DIR}")
