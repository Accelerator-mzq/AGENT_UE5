// Copyright Phase14 v0 attempt2. Canvas HUD 实现。
#include "UI/MADemoHUD.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoFoundations.h"
#include "MADemoDataAssets.h"
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

	// 拍卖面板(增量批 1):拍卖进行中渲染于屏幕中央(GDD 2.1 出价过程须 HUD 可见)。
	if (GS && GS->TurnPhase == EMADemoTurnPhase::Auction && GS->AuctionState.bActive)
	{
		DrawAuctionPanel();
	}

	// 真实暂停面板覆盖层:Esc → IntentPause → TogglePauseState → 此处渲染(再 Esc 恢复)。
	// 绘制在拍卖面板之后:暂停期间拍卖冻结,暂停面板压最上层。
	if (GS && GS->bPaused)
	{
		DrawShellPanel(TEXT("已暂停 (PAUSED)"),
			{ TEXT("[Esc] 继续 (Resume)"), TEXT("暂停期间 Space/Enter 不响应"),
			  TEXT("Alt+F4 退出 (Quit)") });
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
	const float PanelX = 360.f, PanelY = 160.f, PanelW = 560.f;
	const float PanelH = 120.f + Items.Num() * 40.f;
	FCanvasTileItem Bg(FVector2D(PanelX, PanelY), FVector2D(PanelW, PanelH),
		FLinearColor(0.04f, 0.04f, 0.1f, 0.88f));
	Bg.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Bg);

	UFont* Font = GEngine ? GEngine->GetMediumFont() : nullptr;
	auto DrawLine = [&](const FString& Text, float X, float Y, FLinearColor Color, float Scale)
	{
		FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
		Item.Scale = FVector2D(Scale, Scale);
		Canvas->DrawItem(Item);
	};

	float Y = PanelY + 24.f;
	const float X = PanelX + 28.f;
	DrawLine(Title, X, Y, FLinearColor(1.f, 0.85f, 0.2f), 1.5f);
	Y += 50.f;
	for (const FString& Item : Items)
	{
		DrawLine(FString::Printf(TEXT("- %s"), *Item), X, Y, FLinearColor::White, 1.25f);
		Y += 40.f;
	}
}

void AMADemoHUD::DrawGameHUD()
{
	const AMADemoGameState* GS = GetDemoGameState();

	const float PanelX = 40.f, PanelY = 40.f, PanelW = 620.f, PanelH = 340.f;
	FCanvasTileItem Bg(FVector2D(PanelX, PanelY), FVector2D(PanelW, PanelH),
		FLinearColor(0.f, 0.f, 0.f, 0.65f));
	Bg.BlendMode = SE_BLEND_Translucent;
	Canvas->DrawItem(Bg);

	UFont* Font = GEngine ? GEngine->GetMediumFont() : nullptr;
	auto DrawLine = [&](const FString& Text, float X, float Y, FLinearColor Color)
	{
		FCanvasTextItem Item(FVector2D(X, Y), FText::FromString(Text), Font, Color);
		Item.Scale = FVector2D(1.2f, 1.2f);
		Canvas->DrawItem(Item);
	};

	float Y = PanelY + 12.f;
	const float X = PanelX + 16.f;
	DrawLine(TEXT("大富翁拍卖版 Demo"), X, Y, FLinearColor(1.f, 0.85f, 0.2f));
	Y += 34.f;

	if (!GS || GS->Players.Num() == 0)
	{
		DrawLine(TEXT("(等待对局初始化...)"), X, Y, FLinearColor::White);
		return;
	}

	const UMADemoPlayerData* Cur = GS->GetPlayer(GS->CurrentPlayerIndex);
	const FString CurTile = Cur ? GS->GetTileInfo(Cur->CurrentTileIndex).Name : TEXT("-");
	FString PhaseText;
	switch (GS->TurnPhase)
	{
	case EMADemoTurnPhase::WaitingForRoll: PhaseText = TEXT("等待掷骰"); break;
	case EMADemoTurnPhase::Resolving:      PhaseText = TEXT("结算中"); break;
	case EMADemoTurnPhase::TurnEnd:        PhaseText = TEXT("回合结束"); break;
	case EMADemoTurnPhase::Auction:        PhaseText = TEXT("拍卖中"); break;
	case EMADemoTurnPhase::GameOver:       PhaseText = TEXT("游戏结束"); break;
	default:                               PhaseText = TEXT("未开始"); break;
	}
	DrawLine(FString::Printf(TEXT("回合 %d   当前玩家 P%d   位置:%s   阶段:%s"),
		GS->TurnNumber, GS->CurrentPlayerIndex + 1, *CurTile, *PhaseText),
		X, Y, FLinearColor::White);
	Y += 26.f;

	const FMADemoDiceResult& D = GS->LastDice;
	const FString DiceText = (D.Die1 > 0)
		? FString::Printf(TEXT("掷骰:%d + %d = %d%s"), D.Die1, D.Die2, D.Sum(),
			D.bIsDouble ? TEXT(" (双数)") : TEXT(""))
		: TEXT("掷骰:(未掷)");
	DrawLine(DiceText, X, Y, FLinearColor(0.9f, 0.9f, 0.6f));
	Y += 30.f;

	for (int32 i = 0; i < GS->Players.Num(); ++i)
	{
		const UMADemoPlayerData* P = GS->GetPlayer(i);
		const FString Line = FString::Printf(TEXT("P%d  现金:$%d  股值:$%d  格:%d%s"),
			i + 1, P ? P->Money : 0, GS->GetPlayerStockValue(i),
			P ? P->CurrentTileIndex : 0, (P && P->bIsBankrupt) ? TEXT("  [破产]") : TEXT(""));
		const FLinearColor Col = (i == GS->CurrentPlayerIndex)
			? FLinearColor(0.6f, 1.f, 0.6f) : FLinearColor(0.85f, 0.85f, 0.85f);
		DrawLine(Line, X, Y, Col);
		Y += 24.f;
	}

	if (GS->StockMarket)
	{
		TArray<FString> Parts;
		for (int32 s = 0; s < GS->StockMarket->Stocks.Num(); ++s)
		{
			Parts.Add(FString::Printf(TEXT("%s:%d"),
				*GS->StockMarket->Stocks[s].Symbol, GS->StockMarket->GetPrice(s)));
		}
		DrawLine(FString::Printf(TEXT("股市  %s"), *FString::Join(Parts, TEXT("  "))),
			X, Y, FLinearColor(0.6f, 0.9f, 1.f));
		Y += 26.f;
	}

	// 键位提示按真实行为分阶段(宣称对齐,试玩反馈修复轮):
	// 等待掷骰提示 Space,回合结束提示 Enter;暂停时由暂停面板提示 Esc。
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
	DrawLine(Hint, X, Y, FLinearColor(0.7f, 1.f, 0.7f));
	Y += 24.f;

	// 最近拍卖结果一行(成交/流拍后面板已收,主面板保留可见结果,增量批 1)。
	if (!GS->AuctionState.bActive && GS->AuctionState.BidLog.Num() > 0)
	{
		DrawLine(FString::Printf(TEXT("上一场拍卖:%s"), *GS->AuctionState.BidLog.Last()),
			X, Y, FLinearColor(1.f, 0.75f, 0.45f));
	}

	if (GS->bGameOver && GS->WinnerIndex >= 0)
	{
		DrawLine(FString::Printf(TEXT(">>> 玩家 P%d 获胜! <<<"), GS->WinnerIndex + 1),
			PanelX + 16.f, PanelY + PanelH + 16.f, FLinearColor(1.f, 0.8f, 0.2f));
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
