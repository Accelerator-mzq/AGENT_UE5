// Copyright Phase14 v0 attempt2. 常驻 HUD widget 实现。
#include "UI/MADemoHUDWidget.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Blueprint/WidgetTree.h"

void UMADemoHUDWidget::BindGameState(AMADemoGameState* InGameState)
{
	GameStateRef = InGameState;
	RefreshHUD();
}

void UMADemoHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();

	// 代码构建 widget 树:左上角半透明背景 + 纵向文本块。
	// 这样无需 author WBP 即可在 -game 画面真实呈现 HUD(规范 §3 C++ CreateWidget 兜底)。
	if (!WidgetTree)
	{
		return;
	}

	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
	WidgetTree->RootWidget = Root;

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("Panel"));
	Panel->SetBrushColor(FLinearColor(0.f, 0.f, 0.f, 0.6f));
	Panel->SetPadding(FMargin(16.f));

	UVerticalBox* Box = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("Box"));
	Panel->SetContent(Box);

	auto MakeText = [&](const TCHAR* Name, int32 Size, FLinearColor Color) -> UTextBlock*
	{
		UTextBlock* T = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), Name);
		FSlateFontInfo Font = T->GetFont();
		Font.Size = Size;
		T->SetFont(Font);
		T->SetColorAndOpacity(FSlateColor(Color));
		Box->AddChildToVerticalBox(T);
		return T;
	};

	TitleText = MakeText(TEXT("TitleText"), 22, FLinearColor(1.f, 0.85f, 0.2f));
	TitleText->SetText(FText::FromString(TEXT("大富翁拍卖版 Demo")));
	StatusText = MakeText(TEXT("StatusText"), 18, FLinearColor::White);
	PlayersText = MakeText(TEXT("PlayersText"), 16, FLinearColor(0.9f, 0.9f, 0.9f));
	StockText = MakeText(TEXT("StockText"), 14, FLinearColor(0.6f, 0.9f, 1.f));
	HintText = MakeText(TEXT("HintText"), 14, FLinearColor(0.7f, 1.f, 0.7f));
	HintText->SetText(FText::FromString(TEXT("[Space] 掷骰推进   [Enter] 结束回合   [Esc] 暂停")));

	if (UCanvasPanelSlot* PanelSlot = Root->AddChildToCanvas(Panel))
	{
		PanelSlot->SetPosition(FVector2D(40.f, 40.f));
		PanelSlot->SetSize(FVector2D(560.f, 320.f));
		PanelSlot->SetAutoSize(false);
	}

	RefreshHUD();
}

void UMADemoHUDWidget::NativeTick(const FGeometry& MyGeometry, float InDeltaTime)
{
	Super::NativeTick(MyGeometry, InDeltaTime);
	// 每帧拉最新状态,保证键盘按键推进后 HUD 实时反映(不在 Tick 做字符串重查找以外的逻辑)。
	RefreshHUD();
}

FMADemoHUDSnapshot UMADemoHUDWidget::BuildSnapshot() const
{
	FMADemoHUDSnapshot Snap;
	if (!GameStateRef)
	{
		return Snap;
	}
	const AMADemoGameState* GS = GameStateRef;
	Snap.TurnNumber = GS->TurnNumber;
	Snap.CurrentPlayerIndex = GS->CurrentPlayerIndex;

	const UMADemoPlayerData* Cur = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (Cur)
	{
		Snap.CurrentTileName = GS->GetTileInfo(Cur->CurrentTileIndex).Name;
	}

	for (int32 i = 0; i < GS->Players.Num(); ++i)
	{
		const UMADemoPlayerData* P = GS->GetPlayer(i);
		Snap.PlayerCash.Add(P ? P->Money : 0);
		Snap.PlayerStockValue.Add(GS->GetPlayerStockValue(i));
		Snap.PlayerTileIndex.Add(P ? P->CurrentTileIndex : 0);
		Snap.PlayerBankrupt.Add(P ? P->bIsBankrupt : true);
	}

	const FMADemoDiceResult& D = GS->LastDice;
	if (D.Die1 > 0)
	{
		Snap.DiceText = FString::Printf(TEXT("%d + %d = %d%s"),
			D.Die1, D.Die2, D.Sum(), D.bIsDouble ? TEXT(" (双数)") : TEXT(""));
	}
	else
	{
		Snap.DiceText = TEXT("(未掷骰)");
	}

	if (GS->StockMarket)
	{
		TArray<FString> Parts;
		for (int32 s = 0; s < GS->StockMarket->Stocks.Num(); ++s)
		{
			Parts.Add(FString::Printf(TEXT("%s:%d"),
				*GS->StockMarket->Stocks[s].Symbol, GS->StockMarket->GetPrice(s)));
		}
		Snap.StockSummary = FString::Join(Parts, TEXT("  "));
	}

	switch (GS->TurnPhase)
	{
	case EMADemoTurnPhase::NotStarted:     Snap.PhaseText = TEXT("未开始"); break;
	case EMADemoTurnPhase::WaitingForRoll: Snap.PhaseText = TEXT("等待掷骰"); break;
	case EMADemoTurnPhase::Resolving:      Snap.PhaseText = TEXT("结算中"); break;
	case EMADemoTurnPhase::TurnEnd:        Snap.PhaseText = TEXT("回合结束"); break;
	case EMADemoTurnPhase::GameOver:       Snap.PhaseText = TEXT("游戏结束"); break;
	}
	return Snap;
}

void UMADemoHUDWidget::ApplySnapshotToText(const FMADemoHUDSnapshot& Snap)
{
	if (StatusText)
	{
		const FString Status = FString::Printf(
			TEXT("回合 %d   当前玩家 P%d   位置: %s   阶段: %s\n掷骰: %s"),
			Snap.TurnNumber, Snap.CurrentPlayerIndex + 1,
			*Snap.CurrentTileName, *Snap.PhaseText, *Snap.DiceText);
		StatusText->SetText(FText::FromString(Status));
	}
	if (PlayersText)
	{
		FString Lines;
		for (int32 i = 0; i < Snap.PlayerCash.Num(); ++i)
		{
			Lines += FString::Printf(TEXT("P%d  现金:$%d  股值:$%d  格:%d%s\n"),
				i + 1, Snap.PlayerCash[i], Snap.PlayerStockValue[i], Snap.PlayerTileIndex[i],
				Snap.PlayerBankrupt[i] ? TEXT("  [破产]") : TEXT(""));
		}
		PlayersText->SetText(FText::FromString(Lines));
	}
	if (StockText)
	{
		StockText->SetText(FText::FromString(FString::Printf(TEXT("股市  %s"), *Snap.StockSummary)));
	}
}

void UMADemoHUDWidget::RefreshHUD()
{
	const FMADemoHUDSnapshot Snap = BuildSnapshot();
	ApplySnapshotToText(Snap);
	OnHUDRefreshed(Snap);
}
