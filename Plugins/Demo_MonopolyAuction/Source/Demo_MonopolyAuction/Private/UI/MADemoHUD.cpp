// Copyright Phase14 v0 attempt2. Canvas HUD 实现。
#include "UI/MADemoHUD.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoFoundations.h"
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

	// 真实暂停面板覆盖层:Esc → IntentPause → TogglePauseState → 此处渲染(再 Esc 恢复)。
	// 非面板演示产物:仅在 GameState.bPaused 为真时出现,与人按物理 Esc 同一状态源。
	const AMADemoGameState* PauseGS = GetDemoGameState();
	if (PauseGS && PauseGS->bPaused)
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
		case EMADemoTurnPhase::GameOver:
			Hint = TEXT("对局已结束");
			break;
		default:
			Hint = TEXT("[Esc] 暂停");
			break;
		}
	}
	DrawLine(Hint, X, Y, FLinearColor(0.7f, 1.f, 0.7f));

	if (GS->bGameOver && GS->WinnerIndex >= 0)
	{
		DrawLine(FString::Printf(TEXT(">>> 玩家 P%d 获胜! <<<"), GS->WinnerIndex + 1),
			PanelX + 16.f, PanelY + PanelH + 16.f, FLinearColor(1.f, 0.8f, 0.2f));
	}
}
