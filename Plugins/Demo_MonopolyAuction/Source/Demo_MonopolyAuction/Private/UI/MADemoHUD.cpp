// Copyright Phase14 v0 attempt2 / Phase15 presentation-1/2/3. Canvas HUD 实现。
// presentation-3 camera-integration:2D 棋盘 Canvas 渲染从对局 HUD 中退役,
// 3D 棋盘(AMADemoBoard3DActor)与 3D 棋子(3D Pawns)已完全接管棋盘呈现。
// DrawBoard2D 函数代码保留(历史参考),但 DrawHUD() 中不再调用。
#include "UI/MADemoHUD.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoFoundations.h"
#include "MADemoDataAssets.h"
#include "MADemoPresentationConfig.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"

void AMADemoHUD::BeginPlay()
{
	Super::BeginPlay();
	// 解析面板模式:用于 Visual story 截图分别呈现各前台外壳/底座(空=对局 HUD)。
	FString Panel;
	if (FParse::Value(FCommandLine::Get(), TEXT("MADemoPanel="), Panel))
	{
		PanelMode = Panel;
	}
}

AMADemoGameState* AMADemoHUD::GetDemoGameState() const
{
	return GetWorld() ? GetWorld()->GetGameState<AMADemoGameState>() : nullptr;
}

void AMADemoHUD::DrawHUD()
{
	Super::DrawHUD();
	if (!Canvas)
	{
		return;
	}
	DrawSelectedPanel();

	const AMADemoGameState* GS = GetDemoGameState();

	// presentation-3 camera-integration:2D Canvas 棋盘渲染已退役。
	// 3D 棋盘(AMADemoBoard3DActor)与 3D 棋子现已接管棋盘呈现,
	// HUD 只负责信息面板(卡片/指示区/提示条/拍卖弹窗)叠加。
	// DrawBoard2D() 函数代码保留但此处不再调用。

	// 拍卖面板(增量批 1):拍卖进行中渲染于屏幕中央(GDD 2.1 出价过程须 HUD 可见)。
	if (GS && GS->TurnPhase == EMADemoTurnPhase::Auction && GS->AuctionState.bActive)
	{
		DrawAuctionPanel();
	}

	// 真实暂停面板覆盖层:Esc → IntentPause → TogglePauseState → 此处渲染(再 Esc 恢复)。
	// 绘制在拍卖面板之后:暂停期间拍卖冻结,暂停面板压最上层。
	// 按钮布局:Resume / Quit to Menu / [键位说明]。
	if (GS && GS->bPaused)
	{
		DrawShellPanel(TEXT("已暂停 (PAUSED)"),
			{ TEXT("继续 (Resume)  [Esc]"),
			  TEXT("退出到菜单 (Quit to Menu)"),
			  TEXT("退出游戏 (Quit)  [Alt+F4]") });
	}
}

void AMADemoHUD::DrawSelectedPanel()
{
	// 各前台外壳/底座面板的固定条目(与 widget 必备元素一致,用于 Visual 截图呈现)。
	if (PanelMode == TEXT("start"))
	{
		DrawShellPanel(TEXT("开始画面 — 大富翁拍卖版"),
			{ TEXT("项目标识: Demo_MonopolyAuction"), TEXT("按 [Enter] 开始"), TEXT("-> 进入主菜单") });
	}
	else if (PanelMode == TEXT("menu"))
	{
		DrawShellPanel(TEXT("主菜单"),
			{ TEXT("New Game"), TEXT("Settings"), TEXT("Quit") });
	}
	else if (PanelMode == TEXT("settings"))
	{
		DrawShellPanel(TEXT("设置"),
			{ TEXT("Master Volume"), TEXT("SFX Volume"), TEXT("Window Mode"),
			  TEXT("Resolution"), TEXT("Apply"), TEXT("Back") });
	}
	// (原 -MADemoPanel=pause 演示分支已删除:暂停面板改由真实 Esc → bPaused 路径渲染,见 DrawHUD)
	else if (PanelMode == TEXT("results"))
	{
		const AMADemoGameState* GS = GetDemoGameState();
		const FString Winner = (GS && GS->WinnerIndex >= 0)
			? FString::Printf(TEXT("winner_info: 玩家 P%d 获胜"), GS->WinnerIndex + 1)
			: TEXT("winner_info: 玩家 P1 获胜");
		DrawShellPanel(TEXT("对局结果"), { Winner, TEXT("Return to Menu") });
	}
	else if (PanelMode == TEXT("input"))
	{
		DrawShellPanel(TEXT("输入底座 — 默认键位"),
			{ TEXT("menu_confirm  -> Enter"), TEXT("menu_cancel   -> Escape"),
			  TEXT("pause_input   -> Escape"), TEXT("roll_dice_action -> SpaceBar") });
	}
	else if (PanelMode == TEXT("audio"))
	{
		DrawShellPanel(TEXT("音频底座"),
			{ TEXT("bgm_volume_control: Master = 1.0"), TEXT("sfx_volume_control: SFX = 1.0"),
			  TEXT("basic_sfx_playback: 就绪") });
	}
	else if (PanelMode == TEXT("platform"))
	{
		DrawShellPanel(TEXT("平台底座"),
			{ TEXT("window_mode: Windowed"), TEXT("resolution: 1280 x 720"),
			  TEXT("quit_handling: RequestExit"), TEXT("persistence: session_only (provisional)") });
	}
	else
	{
		// 默认:对局 HUD。
		DrawGameHUD();
	}
}

void AMADemoHUD::DrawShellPanel(const FString& Title, const TArray<FString>& Items)
{
	// 取呈现配置 CDO,按钮配色/尺寸来自 DataAsset(规范 §8 不硬编码)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();

	const float PanelX = Cfg->ShellPanelX;
	const float PanelY = Cfg->ShellPanelY;
	const float PanelW = Cfg->ShellPanelWidth;
	// 面板总高:标题区(80) + 每个按钮(ButtonHeight + ButtonSpacing) + 底部边距(24)。
	const float BtnH    = Cfg->ButtonHeight;
	const float BtnGap  = Cfg->ButtonSpacing;
	const float PanelH  = 80.f + Items.Num() * (BtnH + BtnGap) + 24.f;

	// 外壳面板整体背景(深蓝半透明)。
	FCanvasTileItem Bg(FVector2D(PanelX, PanelY), FVector2D(PanelW, PanelH),
		FLinearColor(0.04f, 0.04f, 0.1f, 0.88f));
	Bg.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Bg);

	// 顶部标题分隔线(金色细条)。
	FCanvasTileItem TitleBar(FVector2D(PanelX, PanelY + 62.f), FVector2D(PanelW, 2.f),
		FLinearColor(1.f, 0.85f, 0.2f, 0.6f));
	TitleBar.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(TitleBar);

	UFont* Font = GEngine ? GEngine->GetMediumFont() : nullptr;

	// 辅助:绘制文字(带缩放)。
	auto DrawLine = [&](const FString& Text, float X, float Y, FLinearColor Color, float Scale)
	{
		FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
		Item.Scale = FVector2D(Scale, Scale);
		Canvas->DrawItem(Item);
	};

	// --- 标题区 ---
	const float TitleX = PanelX + 28.f;
	const float TitleY = PanelY + 18.f;
	DrawLine(Title, TitleX, TitleY, FLinearColor(1.f, 0.85f, 0.2f), 1.5f);

	// --- 按钮区:每个条目渲染为背景矩形 + 居中文字 ---
	float BtnY = PanelY + 80.f;
	const float BtnX      = PanelX + 20.f;
	const float BtnW      = PanelW - 40.f;  // 按钮左右各留 20px 边距
	const float TextPadX  = Cfg->ButtonPaddingX;

	for (int32 i = 0; i < Items.Num(); ++i)
	{
		// 首个按钮用高亮色(焦点态示意),其余用普通按钮色。
		const bool bHighlight = (i == 0);
		const FLinearColor BtnBg   = bHighlight ? Cfg->ButtonHighlightColor : Cfg->ButtonBgColor;
		const FLinearColor TextCol = bHighlight ? Cfg->ButtonTextHighlightColor : Cfg->ButtonTextColor;

		// 按钮背景矩形。
		FCanvasTileItem BtnTile(FVector2D(BtnX, BtnY), FVector2D(BtnW, BtnH), BtnBg);
		BtnTile.BlendMode = SE_BLEND_Translucent;
		Canvas->DrawItem(BtnTile);

		// 按钮内文字(垂直居中对齐:Y 偏移约 BtnH 的 30%)。
		const float TextY = BtnY + BtnH * 0.28f;
		DrawLine(Items[i], BtnX + TextPadX, TextY, TextCol, 1.25f);

		BtnY += BtnH + BtnGap;
	}
}

void AMADemoHUD::DrawGameHUD()
{
	const AMADemoGameState* GS = GetDemoGameState();

	// 取呈现配置 CDO(无 authored asset 时用代码默认值,规范 §8 配色/尺寸不硬编码)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();

	UFont* Font = GEngine ? GEngine->GetMediumFont() : nullptr;

	// 辅助:绘制一行文字(scale 可选)。
	auto DrawText = [&](const FString& Text, float X, float Y, FLinearColor Color, float Scale = 1.2f)
	{
		FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
		Item.Scale = FVector2D(Scale, Scale);
		Canvas->DrawItem(Item);
	};

	// 辅助:绘制矩形色块(半透明,需要 BlendMode)。
	auto DrawTile = [&](float X, float Y, float W, float H, FLinearColor Color)
	{
		FCanvasTileItem Tile(FVector2D(X, Y), FVector2D(W, H), Color);
		Tile.BlendMode = SE_BLEND_Translucent;
		Canvas->DrawItem(Tile);
	};

	// ------------------------------------------------------------------
	// 1. 指示区面板(顶部:回合 / 阶段 / 当前玩家)
	// ------------------------------------------------------------------
	const float IndX = Cfg->IndicatorPanelX;
	const float IndY = Cfg->IndicatorPanelY;
	const float IndW = Cfg->IndicatorPanelWidth;
	const float IndH = Cfg->IndicatorPanelHeight;
	DrawTile(IndX, IndY, IndW, IndH, Cfg->IndicatorBgColor);

	if (!GS || GS->Players.Num() == 0)
	{
		// 尚未初始化:仅显示等待提示。
		DrawText(TEXT("大富翁拍卖版 Demo — 等待初始化..."),
			IndX + 14.f, IndY + 20.f, Cfg->TextColorTitle, 1.3f);
		return;
	}

	// 阶段文字。
	FString PhaseText;
	switch (GS->TurnPhase)
	{
	case EMADemoTurnPhase::WaitingForRoll: PhaseText = TEXT("等待掷骰"); break;
	case EMADemoTurnPhase::Resolving:      PhaseText = TEXT("结算中");   break;
	case EMADemoTurnPhase::TurnEnd:        PhaseText = TEXT("回合结束"); break;
	case EMADemoTurnPhase::Auction:        PhaseText = TEXT("拍卖中");   break;
	case EMADemoTurnPhase::GameOver:       PhaseText = TEXT("游戏结束"); break;
	default:                               PhaseText = TEXT("未开始");   break;
	}

	// 指示区内容:回合 · 阶段 · 当前玩家。
	const FString IndLine = FString::Printf(TEXT("回合 %d   %s   当前: P%d"),
		GS->TurnNumber, *PhaseText, GS->CurrentPlayerIndex + 1);
	DrawText(IndLine, IndX + 14.f, IndY + (IndH - 20.f) * 0.5f, Cfg->TextColorTitle, 1.3f);

	// ------------------------------------------------------------------
	// 2. 玩家卡片区(4 张卡片横排,指示区下方)
	// ------------------------------------------------------------------
	const float CardPanelX = Cfg->PlayerCardPanelX;
	const float CardPanelY = Cfg->PlayerCardPanelY;
	const float CardW      = Cfg->PlayerCardWidth;
	const float CardH      = Cfg->PlayerCardHeight;
	const float CardGap    = Cfg->PlayerCardGap;
	const float BarMaxW    = Cfg->MoneyBarMaxWidth;
	const float BarH       = Cfg->MoneyBarHeight;

	const int32 NumPlayers = GS->Players.Num();
	for (int32 i = 0; i < NumPlayers; ++i)
	{
		const UMADemoPlayerData* P = GS->GetPlayer(i);
		const float CardX = CardPanelX + i * (CardW + CardGap);
		const float CardY = CardPanelY;

		// 卡片背景色:破产 → 暗红 / 当前玩家 → 金色高亮 / 其他 → 普通。
		const bool bBankrupt  = P && P->bIsBankrupt;
		const bool bIsActive  = (i == GS->CurrentPlayerIndex);
		FLinearColor CardBg = bBankrupt  ? Cfg->BankruptCardBgColor
		                    : bIsActive  ? Cfg->ActivePlayerHighlightColor
		                    :              Cfg->PlayerCardBgColor;
		DrawTile(CardX, CardY, CardW, CardH, CardBg);

		// 卡片边框(当前玩家亮边)——用一像素偏移的半透明白色外框模拟。
		if (bIsActive && !bBankrupt)
		{
			DrawTile(CardX - 2.f, CardY - 2.f, CardW + 4.f, 2.f, FLinearColor(1.f, 1.f, 0.5f, 0.8f));
			DrawTile(CardX - 2.f, CardY + CardH, CardW + 4.f, 2.f, FLinearColor(1.f, 1.f, 0.5f, 0.8f));
			DrawTile(CardX - 2.f, CardY, 2.f, CardH, FLinearColor(1.f, 1.f, 0.5f, 0.8f));
			DrawTile(CardX + CardW, CardY, 2.f, CardH, FLinearColor(1.f, 1.f, 0.5f, 0.8f));
		}

		// 玩家名称行。
		const FString NameLine = FString::Printf(TEXT("P%d%s"),
			i + 1, bBankrupt ? TEXT(" [破产]") : (bIsActive ? TEXT(" ◀") : TEXT("")));
		const FLinearColor NameCol = bBankrupt ? FLinearColor(0.6f, 0.4f, 0.4f, 1.f)
		                           : bIsActive ? FLinearColor(1.f, 1.f, 0.4f, 1.f)
		                           : Cfg->TextColorDefault;
		DrawText(NameLine, CardX + 10.f, CardY + 10.f, NameCol, 1.15f);

		// 现金数值行。
		const int32 Money = P ? P->Money : 0;
		const int32 StockVal = GS->GetPlayerStockValue(i);
		const FString MoneyLine = FString::Printf(TEXT("$%d  股$%d"), Money, StockVal);
		DrawText(MoneyLine, CardX + 10.f, CardY + 32.f, Cfg->TextColorDefault, 1.0f);

		// 格子行。
		const int32 TileIdx = P ? P->CurrentTileIndex : 0;
		DrawText(FString::Printf(TEXT("格 %d"), TileIdx),
			CardX + 10.f, CardY + 52.f, FLinearColor(0.75f, 0.75f, 0.75f, 1.f), 1.0f);

		// 资金条(底色 + 前景按比例宽度)。
		const float BarY = CardY + CardH - BarH - 8.f;
		const float BarX = CardX + 10.f;
		DrawTile(BarX, BarY, BarMaxW, BarH, Cfg->MoneyBarBgColor);

		const float Ratio = FMath::Clamp(
			static_cast<float>(Money) / FMath::Max(1, Cfg->MoneyBarFullAmount), 0.f, 1.f);
		if (Ratio > 0.f)
		{
			DrawTile(BarX, BarY, BarMaxW * Ratio, BarH, Cfg->MoneyBarFgColor);
		}
	}

	// ------------------------------------------------------------------
	// 3. 掷骰信息行(卡片区下方)
	// ------------------------------------------------------------------
	const float InfoY = CardPanelY + CardH + 14.f;
	const FMADemoDiceResult& D = GS->LastDice;
	const FString DiceText = (D.Die1 > 0)
		? FString::Printf(TEXT("掷骰:%d + %d = %d%s"), D.Die1, D.Die2, D.Sum(),
			D.bIsDouble ? TEXT(" (双数)") : TEXT(""))
		: TEXT("掷骰:(未掷)");
	DrawText(DiceText, CardPanelX, InfoY, FLinearColor(0.9f, 0.9f, 0.6f), 1.1f);

	// ------------------------------------------------------------------
	// 4. 股市行(掷骰下方)
	// ------------------------------------------------------------------
	if (GS->StockMarket)
	{
		TArray<FString> Parts;
		for (int32 s = 0; s < GS->StockMarket->Stocks.Num(); ++s)
		{
			Parts.Add(FString::Printf(TEXT("%s:%d"),
				*GS->StockMarket->Stocks[s].Symbol, GS->StockMarket->GetPrice(s)));
		}
		DrawText(FString::Printf(TEXT("股市  %s"), *FString::Join(Parts, TEXT("  "))),
			CardPanelX, InfoY + 26.f, FLinearColor(0.6f, 0.9f, 1.f), 1.1f);
	}

	// ------------------------------------------------------------------
	// 5. 提示条(底部固定位置,用 config 坐标)
	// ------------------------------------------------------------------
	DrawTile(Cfg->HintBarX, Cfg->HintBarY, Cfg->HintBarWidth, Cfg->HintBarHeight,
		FLinearColor(0.f, 0.f, 0.f, 0.55f));

	FString Hint;
	if (GS->bPaused)
	{
		Hint = TEXT("已暂停 — [Esc] 继续");
	}
	else
	{
		switch (GS->TurnPhase)
		{
		case EMADemoTurnPhase::WaitingForRoll:
			Hint = TEXT("[Space] 掷骰   [Esc] 暂停");
			break;
		case EMADemoTurnPhase::TurnEnd:
			Hint = TEXT("[Enter] 结束回合   [Esc] 暂停");
			break;
		case EMADemoTurnPhase::Auction:
			// 拍卖期键位提示在中央拍卖面板内,主面板只标状态。
			Hint = TEXT("拍卖进行中(见中央面板)");
			break;
		case EMADemoTurnPhase::GameOver:
			Hint = TEXT("对局已结束");
			break;
		default:
			Hint = TEXT("[Esc] 暂停");
			break;
		}
	}
	DrawText(Hint, Cfg->HintBarX + 12.f, Cfg->HintBarY + 10.f, Cfg->TextColorHint, 1.1f);

	// ------------------------------------------------------------------
	// 6. 最近拍卖结果 + 胜利提示(可选行)
	// ------------------------------------------------------------------
	if (!GS->AuctionState.bActive && GS->AuctionState.BidLog.Num() > 0)
	{
		DrawText(FString::Printf(TEXT("上一场拍卖:%s"), *GS->AuctionState.BidLog.Last()),
			CardPanelX, InfoY + 52.f, FLinearColor(1.f, 0.75f, 0.45f), 1.0f);
	}

	if (GS->bGameOver && GS->WinnerIndex >= 0)
	{
		// 胜利提示覆盖在面板中央下方。
		DrawText(FString::Printf(TEXT(">>> 玩家 P%d 获胜! <<<"), GS->WinnerIndex + 1),
			CardPanelX, CardPanelY + CardH + 80.f, FLinearColor(1.f, 0.8f, 0.2f), 1.5f);
	}
}

void AMADemoHUD::DrawBoard2D()
{
	// 2D 棋盘环形布局(presentation-2):28 格分布在矩形四边,格子带地产组配色+归属状态+拍卖高亮。
	// 纯只读 GameState,无规则逻辑。
	const AMADemoGameState* GS = GetDemoGameState();
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();

	UFont* Font = GEngine ? GEngine->GetSmallFont() : nullptr;

	// 辅助:绘制矩形色块。
	auto DrawTile = [&](float X, float Y, float W, float H, FLinearColor Color)
	{
		FCanvasTileItem Tile(FVector2D(X, Y), FVector2D(W, H), Color);
		Tile.BlendMode = SE_BLEND_Translucent;
		Canvas->DrawItem(Tile);
	};

	// 辅助:绘制文字(小字)。
	auto DrawLabel = [&](const FString& Text, float X, float Y, FLinearColor Color)
	{
		FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
		Item.Scale = FVector2D(0.7f, 0.7f);
		Canvas->DrawItem(Item);
	};

	const float TileSize = Cfg->BoardTileSize;
	const float Gap      = Cfg->BoardTileGap;
	const float Step     = TileSize + Gap;

	// 每边含角格的格数(7×7 矩形环,4边各 7 格,共 4×7=28 格)。
	const int32 SideCount = 7; // 每边含两端角格的格数

	// 棋盘整体尺寸:(SideCount-1)*Step + TileSize。
	const float BoardSpan = (SideCount - 1) * Step + TileSize;

	const float OriginX = Cfg->BoardOriginX;
	const float OriginY = Cfg->BoardOriginY;

	// 绘制棋盘背景(比格子稍大留出边距)。
	const float PadBg = 8.f;
	DrawTile(OriginX - PadBg, OriginY - PadBg - 18.f,
		BoardSpan + PadBg * 2.f, BoardSpan + PadBg * 2.f + 18.f,
		Cfg->BoardBgColor);

	// 棋盘标题文字。
	DrawLabel(TEXT("2D棋盘"), OriginX, OriginY - 16.f, Cfg->TextColorTitle);

	// 28 格环形布局:每边 7 格(含首尾角格),顺时针从左下角开始。
	// 索引 0~6:  下边,从左到右
	// 索引 7~13: 右边,从下到上(共享 6 和 0 号角)
	// 索引 14~20:上边,从右到左(共享 13 和 7 号角)
	// 索引 21~27:左边,从上到下(共享 20 和 14 号角)
	// 实际: 0=左下角, 6=右下角, 13=右上角, 20=左上角,
	//       7~12=右边(下→上), 14~19=上边(右→左), 21~26=左边(上→下)
	// 即:
	//   底边(下) index 0..6: (col=0..6, row=6)
	//   右边     index 7..13: (col=6, row=5..0) — 其中 13 = 右上角
	//   上边     index 14..20: (col=5..0, row=0) — 20 = 左上角
	//   左边     index 21..27: (col=0, row=1..6) — 27 = 左下角 = 与 0 相邻

	// 计算每个格子的像素坐标(左上角)。
	// 格 i 的格子逻辑坐标 (col, row) 在 7×7 格网格中(col/row 各 0~6)。
	auto GetTilePixelPos = [&](int32 TileIndex) -> FVector2D
	{
		TileIndex = TileIndex % 28;
		int32 Col = 0, Row = 0;
		if (TileIndex < 7)
		{
			// 下边:col = 0..6, row = 6
			Col = TileIndex;
			Row = 6;
		}
		else if (TileIndex < 13)
		{
			// 右边(不含角):col = 6, row = 5..(SideCount-1 - (TileIndex-7+1))
			Col = 6;
			Row = 6 - (TileIndex - 6); // row = 5..1
		}
		else if (TileIndex == 13)
		{
			// 右上角
			Col = 6; Row = 0;
		}
		else if (TileIndex < 20)
		{
			// 上边(不含角):col = 5..1, row = 0
			Col = 6 - (TileIndex - 13); // col = 5..1
			Row = 0;
		}
		else if (TileIndex == 20)
		{
			// 左上角
			Col = 0; Row = 0;
		}
		else if (TileIndex < 27)
		{
			// 左边(不含角):col = 0, row = 1..5
			Col = 0;
			Row = TileIndex - 20; // row = 1..6
		}
		else
		{
			// index 27:左下角旁(接回 0)
			Col = 0; Row = 6;
		}
		return FVector2D(OriginX + Col * Step, OriginY + Row * Step);
	};

	// 取地产组配色。
	auto GetGroupColor = [&](EMADemoColorGroup Group) -> FLinearColor
	{
		const int32 Idx = (int32)Group;
		if (Cfg->ColorGroupPalette.IsValidIndex(Idx))
		{
			return Cfg->ColorGroupPalette[Idx];
		}
		return Cfg->TileColorUnowned;
	};

	// 取归属覆盖色(有主时返回玩家色,否则返回透明 alpha=0)。
	auto GetOwnerColor = [&](int32 OwnerIdx) -> FLinearColor
	{
		if (OwnerIdx < 0) return FLinearColor(0.f, 0.f, 0.f, 0.f);
		if (Cfg->PlayerOwnershipColors.IsValidIndex(OwnerIdx))
		{
			return Cfg->PlayerOwnershipColors[OwnerIdx];
		}
		return FLinearColor(1.f, 1.f, 1.f, 0.5f);
	};

	// 拍卖中的地块索引(-1 表示无拍卖)。
	const int32 AuctionTile = (GS && GS->AuctionState.bActive) ? GS->AuctionState.TileIndex : -1;

	// 逐格绘制。
	const int32 NumTiles = 28;
	for (int32 i = 0; i < NumTiles; ++i)
	{
		const FVector2D Pos = GetTilePixelPos(i);

		// 取格子静态信息(无 GameState 时使用默认格)。
		FMADemoTileInfo Info;
		if (GS)
		{
			Info = GS->GetTileInfo(i);
		}

		// 决定格子底色:地产格 → 地产组色;特殊格 → 特殊色。
		FLinearColor TileBg;
		if (Info.TileType == EMADemoTileType::Property && Info.ColorGroup != EMADemoColorGroup::None)
		{
			TileBg = GetGroupColor(Info.ColorGroup);
		}
		else
		{
			TileBg = Cfg->TileColorSpecial;
		}
		DrawTile(Pos.X, Pos.Y, TileSize, TileSize, TileBg);

		// 归属覆盖层(有主时在格子内叠加玩家色半透明遮罩)。
		const int32 TileOwnerIdx = GS ? GS->GetTileOwner(i) : -1;
		if (TileOwnerIdx >= 0)
		{
			const FLinearColor OwnColor = GetOwnerColor(TileOwnerIdx);
			// 归属色盖住格子内侧(留 3px 边框)。
			DrawTile(Pos.X + 3.f, Pos.Y + 3.f, TileSize - 6.f, TileSize - 6.f, OwnColor);

			// 归属玩家标签(P1/P2...)。
			DrawLabel(FString::Printf(TEXT("P%d"), TileOwnerIdx + 1),
				Pos.X + 4.f, Pos.Y + TileSize * 0.4f, FLinearColor(1.f, 1.f, 1.f, 1.f));
		}

		// 拍卖高亮边框(拍卖中地块用金色亮边 2px)。
		if (i == AuctionTile)
		{
			// 上边框
			DrawTile(Pos.X, Pos.Y, TileSize, 2.f, Cfg->TileAuctionHighlightColor);
			// 下边框
			DrawTile(Pos.X, Pos.Y + TileSize - 2.f, TileSize, 2.f, Cfg->TileAuctionHighlightColor);
			// 左边框
			DrawTile(Pos.X, Pos.Y, 2.f, TileSize, Cfg->TileAuctionHighlightColor);
			// 右边框
			DrawTile(Pos.X + TileSize - 2.f, Pos.Y, 2.f, TileSize, Cfg->TileAuctionHighlightColor);
		}

		// 格子编号小标(右下角)。
		DrawLabel(FString::Printf(TEXT("%d"), i),
			Pos.X + TileSize - 13.f, Pos.Y + TileSize - 10.f,
			FLinearColor(0.75f, 0.75f, 0.75f, 0.85f));
	}

	// ---- 玩家 Token 渲染(presentation-2 board-tokens rung2) ----
	// 每位玩家一个明确 token:实心色块 + 玩家编号文字。
	// 当前回合玩家 token:加粗白描边 + 上方三角浮标,尺寸更大,远观可辨识(feedback-1 改进)。
	// 多玩家同格时按索引错开(offset),避免完全重叠。
	// 规则:纯只读 GameState,不写任何玩法逻辑;破产玩家跳过。
	if (GS)
	{
		// 计算每个格子上有多少玩家及各自在格内的偏移序号(用于错开显示)。
		// 先统计每格上的玩家列表。
		TMap<int32, TArray<int32>> TileToPlayers;
		for (int32 p = 0; p < GS->Players.Num(); ++p)
		{
			const UMADemoPlayerData* PD = GS->GetPlayer(p);
			if (!PD || PD->bIsBankrupt) continue;
			const int32 PTile = PD->CurrentTileIndex % 28;
			TileToPlayers.FindOrAdd(PTile).Add(p);
		}

		// token 尺寸从 DataAsset 取(feedback-1:普通 14px,当前玩家 18px)。
		const float TokenSize    = Cfg->BoardTokenSize;       // 普通 token 边长
		const float TokenSizeBig = Cfg->BoardTokenActiveSize; // 当前玩家 token 边长(更大)
		const float StrokeW      = Cfg->BoardTokenActiveStrokeWidth;    // 描边宽度
		const float MarkerH      = Cfg->BoardTokenActiveMarkerHeight;   // 浮标三角高度
		const float TokenPad     = 2.f;  // 距格子边距

		for (auto& Pair : TileToPlayers)
		{
			const int32 Tile     = Pair.Key;
			const TArray<int32>& Players = Pair.Value;
			const FVector2D TilePos = GetTilePixelPos(Tile);

			for (int32 slot = 0; slot < Players.Num(); ++slot)
			{
				const int32 p = Players[slot];
				const bool bIsActive = (p == GS->CurrentPlayerIndex);

				// 玩家 token 颜色(从 PlayerOwnershipColors 取,兜底白)。
				const FLinearColor PCol = Cfg->PlayerOwnershipColors.IsValidIndex(p)
					? FLinearColor(Cfg->PlayerOwnershipColors[p].R,
					               Cfg->PlayerOwnershipColors[p].G,
					               Cfg->PlayerOwnershipColors[p].B,
					               1.f)  // token 不透明
					: FLinearColor(1.f, 1.f, 1.f, 1.f);

				const float Sz = bIsActive ? TokenSizeBig : TokenSize;

				// 多玩家同格时错开:横向按 slot 偏移,以普通 token 尺寸为步长。
				// 排列从左上角开始,超出格子边界时折回下一行。
				const float ColIdx = static_cast<float>(slot % 2);
				const float RowIdx = static_cast<float>(slot / 2);
				const float OffX = TokenPad + ColIdx * (TokenSize + 2.f);
				const float OffY = TokenPad + RowIdx * (TokenSize + 2.f);

				const float TX = TilePos.X + OffX;
				const float TY = TilePos.Y + OffY;

				// 当前回合玩家:加粗白色描边 + 上方三角浮标(feedback-1 醒目改进)。
				if (bIsActive)
				{
					// 加粗外围白色描边(比 token 大 StrokeW px 四周,比旧版 2px 更粗)。
					DrawTile(TX - StrokeW, TY - StrokeW, Sz + StrokeW * 2.f, Sz + StrokeW * 2.f,
						FLinearColor(1.f, 1.f, 1.f, 0.95f));

					// 三角形浮标:用三个细长矩形叠出倒三角(▼)显示在 token 正上方。
					// 用三层递减宽度矩形模拟倒三角(Canvas 无原生三角形绘制 API)。
					if (MarkerH > 0.f)
					{
						// 浮标中心 X 对齐 token 中心,Y 紧贴 token 上方再留 1px 间隔。
						const float CX = TX + Sz * 0.5f;  // 浮标中心 X
						const float MY = TY - StrokeW - MarkerH - 1.f; // 浮标顶边 Y
						const int32 NumRows = FMath::Max(1, FMath::RoundToInt(MarkerH));
						for (int32 row = 0; row < NumRows; ++row)
						{
							// 从顶(尖端)到底(宽端):宽度从 1 线性增长到 MarkerH*2 。
							const float t = static_cast<float>(row) / FMath::Max(1, NumRows - 1);
							const float HalfW = FMath::Max(0.5f, t * (MarkerH));
							DrawTile(CX - HalfW, MY + row, HalfW * 2.f, 1.f,
								FLinearColor(1.f, 1.f, 0.2f, 1.f)); // 亮黄浮标,与白边区分
						}
					}
				}

				// token 实体色块。
				DrawTile(TX, TY, Sz, Sz, PCol);

				// token 内玩家编号文字(小字"1"~"4")。
				// 当前玩家用深色字对比亮边;其他玩家白字。
				DrawLabel(FString::Printf(TEXT("%d"), p + 1),
					TX + 1.f, TY + 1.f,
					bIsActive ? FLinearColor(0.05f, 0.05f, 0.05f, 1.f)
					           : FLinearColor(1.f, 1.f, 1.f, 0.9f));
			}
		}
	}
}

void AMADemoHUD::DrawAuctionPanel()
{
	const AMADemoGameState* GS = GetDemoGameState();
	if (!GS)
	{
		return;
	}
	const FMADemoAuctionState& A = GS->AuctionState;
	const FMADemoTileInfo Info = GS->GetTileInfo(A.TileIndex);

	// 面板尺寸:头部 3 行 + 玩家状态行 + 出价记录(最多 6 条)+ 提示行。
	const int32 LogShown = FMath::Min(A.BidLog.Num(), 6);
	const float PanelX = 700.f, PanelY = 60.f, PanelW = 540.f;
	const float PanelH = 200.f + (GS->Players.Num() + LogShown) * 24.f;
	FCanvasTileItem Bg(FVector2D(PanelX, PanelY), FVector2D(PanelW, PanelH),
		FLinearColor(0.10f, 0.06f, 0.02f, 0.92f));
	Bg.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Bg);

	UFont* Font = GEngine ? GEngine->GetMediumFont() : nullptr;
	auto DrawLine = [&](const FString& Text, float X, float Y, FLinearColor Color, float Scale = 1.15f)
	{
		FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
		Item.Scale = FVector2D(Scale, Scale);
		Canvas->DrawItem(Item);
	};

	float Y = PanelY + 14.f;
	const float X = PanelX + 20.f;

	// 顶部:地产名 + 地价 + 起拍价(GDD 3.1)。
	DrawLine(FString::Printf(TEXT("英式拍卖 — %s"), *Info.Name), X, Y,
		FLinearColor(1.f, 0.85f, 0.2f), 1.4f);
	Y += 36.f;
	DrawLine(FString::Printf(TEXT("地价 $%d   起拍 $%d   步长 $%d"),
		Info.Price, A.StartPrice,
		GS->RulesData ? GS->RulesData->AuctionBidStep : 10), X, Y, FLinearColor::White);
	Y += 26.f;

	// 当前最高价(高亮,GDD 3.1)。
	if (A.HighestBidderIndex >= 0)
	{
		DrawLine(FString::Printf(TEXT("当前最高:$%d(P%d)"),
			A.HighestBid, A.HighestBidderIndex + 1), X, Y, FLinearColor(1.f, 0.9f, 0.1f), 1.3f);
	}
	else
	{
		DrawLine(TEXT("尚无出价"), X, Y, FLinearColor(0.8f, 0.8f, 0.8f), 1.3f);
	}
	Y += 30.f;

	// 各玩家状态(弃权变灰,GDD 3.1)。
	for (int32 i = 0; i < GS->Players.Num(); ++i)
	{
		const bool bPassed = A.PassedPlayers.IsValidIndex(i) && A.PassedPlayers[i];
		const bool bTurn = (i == A.CurrentBidderIndex);
		const FString Line = FString::Printf(TEXT("P%d  %s%s"), i + 1,
			bPassed ? TEXT("已弃权") : TEXT("竞价中"),
			bTurn ? TEXT("  <- 轮到") : TEXT(""));
		const FLinearColor Col = bPassed
			? FLinearColor(0.45f, 0.45f, 0.45f)
			: (bTurn ? FLinearColor(0.6f, 1.f, 0.6f) : FLinearColor(0.85f, 0.85f, 0.85f));
		DrawLine(Line, X, Y, Col);
		Y += 24.f;
	}
	Y += 6.f;

	// 出价记录(最近 6 条,GDD 3.1 中部滚动列表)。
	for (int32 i = A.BidLog.Num() - LogShown; i < A.BidLog.Num(); ++i)
	{
		DrawLine(A.BidLog[i], X, Y, FLinearColor(0.7f, 0.85f, 1.f), 1.0f);
		Y += 24.f;
	}
	Y += 8.f;

	// 键位提示:拟出价金额 + 买不起提示。
	const int32 NextBid = (A.HighestBidderIndex < 0)
		? A.StartPrice
		: A.HighestBid + (GS->RulesData ? GS->RulesData->AuctionBidStep : 10);
	const UMADemoPlayerData* Bidder = GS->GetPlayer(A.CurrentBidderIndex);
	if (Bidder && Bidder->Money < NextBid)
	{
		DrawLine(FString::Printf(TEXT("P%d 现金不足($%d < $%d),只能 [Enter] 弃权"),
			A.CurrentBidderIndex + 1, Bidder->Money, NextBid), X, Y,
			FLinearColor(1.f, 0.5f, 0.4f));
	}
	else
	{
		DrawLine(FString::Printf(TEXT("[Space] 出价 $%d   [Enter] 弃权"), NextBid),
			X, Y, FLinearColor(0.7f, 1.f, 0.7f));
	}
}
