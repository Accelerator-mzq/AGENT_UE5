#include "MGameHUDWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "MMonopolyGameMode.h"
#include "MMonopolyGameState.h"
#include "MMonopolyPlayerState.h"
#include "Styling/CoreStyle.h"

namespace MonopolyHUD
{
	// 统一 HUD 文本样式，保证运行时构建的文本在深色背景上可读。
	static FSlateFontInfo MakeFont(int32 Size, const TCHAR* Weight = TEXT("Regular"))
	{
		return FCoreStyle::GetDefaultFontStyle(Weight, Size);
	}

	static void StyleText(UTextBlock* Text, int32 FontSize, const FLinearColor& Color = FLinearColor::White)
	{
		if (Text == nullptr)
		{
			return;
		}

		Text->SetFont(MakeFont(FontSize, FontSize >= 18 ? TEXT("Bold") : TEXT("Regular")));
		Text->SetColorAndOpacity(FSlateColor(Color));
		Text->SetShadowOffset(FVector2D(1.0f, 1.0f));
		Text->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.7f));
	}

	static void StyleButton(UButton* Button, const FLinearColor& BackgroundColor)
	{
		if (Button == nullptr)
		{
			return;
		}

		Button->SetBackgroundColor(BackgroundColor);
	}
}

TSharedRef<SWidget> UMGameHUDWidget::RebuildWidget()
{
	BuildRuntimeWidgetTree();
	const TSharedRef<SWidget> SlateWidget = Super::RebuildWidget();
	UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD RebuildWidget prepared. RootWidget=%s"),
		WidgetTree != nullptr && WidgetTree->RootWidget != nullptr ? TEXT("ok") : TEXT("null"));
	return SlateWidget;
}

void UMGameHUDWidget::NativeConstruct()
{
	Super::NativeConstruct();

	UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD NativeConstruct called. RootWidget=%s"),
		WidgetTree != nullptr && WidgetTree->RootWidget != nullptr ? TEXT("exists") : TEXT("null"));

	if (RollButton != nullptr && !RollButton->OnClicked.IsAlreadyBound(this, &UMGameHUDWidget::HandleRollClicked))
	{
		RollButton->OnClicked.AddDynamic(this, &UMGameHUDWidget::HandleRollClicked);
	}

	if (EndTurnButton != nullptr && !EndTurnButton->OnClicked.IsAlreadyBound(this, &UMGameHUDWidget::HandleEndTurnClicked))
	{
		EndTurnButton->OnClicked.AddDynamic(this, &UMGameHUDWidget::HandleEndTurnClicked);
	}

	if (PayBailButton != nullptr && !PayBailButton->OnClicked.IsAlreadyBound(this, &UMGameHUDWidget::HandlePayBailClicked))
	{
		PayBailButton->OnClicked.AddDynamic(this, &UMGameHUDWidget::HandlePayBailClicked);
	}

	SetIsFocusable(true);
	SetVisibility(ESlateVisibility::Visible);
	RefreshAllText();

	UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD NativeConstruct done. Visibility=%d RootWidget=%s"),
		static_cast<int32>(GetVisibility()),
		WidgetTree != nullptr && WidgetTree->RootWidget != nullptr ? TEXT("ok") : TEXT("null"));
}

void UMGameHUDWidget::BindToGame(AMMonopolyGameMode* InGameMode, AMMonopolyGameState* InGameState)
{
	CachedGameMode = InGameMode;
	CachedGameState = InGameState;

	if (CachedGameState != nullptr)
	{
		if (!CachedGameState->OnTurnNumberChanged.IsAlreadyBound(this, &UMGameHUDWidget::HandleTurnNumberChanged))
		{
			CachedGameState->OnTurnNumberChanged.AddDynamic(this, &UMGameHUDWidget::HandleTurnNumberChanged);
		}

		if (!CachedGameState->OnActivePlayerChanged.IsAlreadyBound(this, &UMGameHUDWidget::HandleActivePlayerChanged))
		{
			CachedGameState->OnActivePlayerChanged.AddDynamic(this, &UMGameHUDWidget::HandleActivePlayerChanged);
		}

		if (!CachedGameState->OnMoneyChanged.IsAlreadyBound(this, &UMGameHUDWidget::HandleMoneyChanged))
		{
			CachedGameState->OnMoneyChanged.AddDynamic(this, &UMGameHUDWidget::HandleMoneyChanged);
		}

		if (!CachedGameState->OnPawnMoved.IsAlreadyBound(this, &UMGameHUDWidget::HandlePawnMoved))
		{
			CachedGameState->OnPawnMoved.AddDynamic(this, &UMGameHUDWidget::HandlePawnMoved);
		}

		if (!CachedGameState->OnTurnStateChanged.IsAlreadyBound(this, &UMGameHUDWidget::HandleTurnStateChanged))
		{
			CachedGameState->OnTurnStateChanged.AddDynamic(this, &UMGameHUDWidget::HandleTurnStateChanged);
		}
	}

	RefreshAllText();
}

void UMGameHUDWidget::HandleRollClicked()
{
	if (CachedGameMode != nullptr)
	{
		CachedGameMode->OnPlayerRequestRoll();
	}
}

void UMGameHUDWidget::HandleEndTurnClicked()
{
	if (CachedGameMode != nullptr)
	{
		CachedGameMode->RequestEndTurnFromUI();
	}
}

void UMGameHUDWidget::HandlePayBailClicked()
{
	if (CachedGameMode != nullptr)
	{
		CachedGameMode->RequestPayBailFromUI();
	}
}

void UMGameHUDWidget::HandleTurnNumberChanged(const int32 NewTurnNumber)
{
	if (TurnNumberText != nullptr)
	{
		TurnNumberText->SetText(FText::FromString(FString::Printf(TEXT("回合：%d"), NewTurnNumber)));
	}
}

void UMGameHUDWidget::HandleActivePlayerChanged(const int32 NewPlayerIndex, AMMonopolyPlayerState* NewPlayerState)
{
	if (CurrentPlayerText != nullptr)
	{
		const FString PlayerName = NewPlayerState != nullptr ? NewPlayerState->GetResolvedDisplayName() : TEXT("未知玩家");
		CurrentPlayerText->SetText(FText::FromString(FString::Printf(TEXT("当前玩家：P%d %s"), NewPlayerIndex + 1, *PlayerName)));
	}

	if (MoneySummaryText != nullptr)
	{
		MoneySummaryText->SetText(FText::FromString(BuildMoneySummary()));
	}

	RefreshAllText();
}

void UMGameHUDWidget::HandleMoneyChanged(AMMonopolyPlayerState* PlayerState, const int32 NewMoney)
{
	if (MoneySummaryText != nullptr)
	{
		MoneySummaryText->SetText(FText::FromString(BuildMoneySummary()));
	}

	if (StatusText != nullptr && PlayerState != nullptr)
	{
		StatusText->SetText(FText::FromString(FString::Printf(TEXT("%s 资金变为 %d"), *PlayerState->GetResolvedDisplayName(), NewMoney)));
	}
}

void UMGameHUDWidget::HandlePawnMoved(AMMonopolyPlayerState* PlayerState, const int32 NewTileIndex)
{
	if (TileInfoText != nullptr && PlayerState != nullptr)
	{
		TileInfoText->SetText(FText::FromString(FString::Printf(TEXT("%s 到达格子 %d"), *PlayerState->GetResolvedDisplayName(), NewTileIndex)));
	}
}

void UMGameHUDWidget::HandleTurnStateChanged(const EMTurnState NewTurnState)
{
	const UEnum* EnumPtr = StaticEnum<EMTurnState>();
	const FString StateName = EnumPtr != nullptr
		? EnumPtr->GetDisplayNameTextByValue(static_cast<int64>(NewTurnState)).ToString()
		: TEXT("Unknown");

	if (StatusText != nullptr)
	{
		StatusText->SetText(FText::FromString(FString::Printf(TEXT("状态：%s"), *StateName)));
	}

	RefreshAllText();
}

void UMGameHUDWidget::BuildRuntimeWidgetTree()
{
	if (WidgetTree == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Phase8] HUD BuildRuntimeWidgetTree skipped: WidgetTree=null"));
		return;
	}

	if (WidgetTree->RootWidget != nullptr)
	{
		UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD BuildRuntimeWidgetTree skipped: RootWidget already exists."));
		return;
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD BuildRuntimeWidgetTree start. RootWidget=null"));

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("HudCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* RootBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("HudRootBorder"));
	RootBorder->SetPadding(FMargin(18.0f));
	RootBorder->SetBrushColor(FLinearColor(0.02f, 0.03f, 0.04f, 0.82f));
	Canvas->AddChild(RootBorder);

	if (UCanvasPanelSlot* BorderSlot = Cast<UCanvasPanelSlot>(RootBorder->Slot))
	{
		BorderSlot->SetAnchors(FAnchors(0.0f, 0.0f));
		BorderSlot->SetAlignment(FVector2D::ZeroVector);
		BorderSlot->SetPosition(FVector2D(20.0f, 20.0f));
		BorderSlot->SetAutoSize(true);
		UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD CanvasPanelSlot configured."));
	}

	UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("HudRootBox"));
	RootBorder->SetContent(RootBox);

	CurrentPlayerText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("CurrentPlayerText"));
	CurrentPlayerText->SetText(FText::FromString(TEXT("当前玩家：等待初始化")));
	MonopolyHUD::StyleText(CurrentPlayerText, 18);
	RootBox->AddChildToVerticalBox(CurrentPlayerText);

	TurnNumberText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TurnNumberText"));
	MonopolyHUD::StyleText(TurnNumberText, 16);
	if (UVerticalBoxSlot* TurnSlot = RootBox->AddChildToVerticalBox(TurnNumberText))
	{
		TurnSlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
	}

	MoneySummaryText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("MoneySummaryText"));
	MoneySummaryText->SetAutoWrapText(true);
	MonopolyHUD::StyleText(MoneySummaryText, 16);
	if (UVerticalBoxSlot* MoneySlot = RootBox->AddChildToVerticalBox(MoneySummaryText))
	{
		MoneySlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
	}

	TileInfoText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TileInfoText"));
	TileInfoText->SetAutoWrapText(true);
	MonopolyHUD::StyleText(TileInfoText, 16);
	if (UVerticalBoxSlot* TileSlot = RootBox->AddChildToVerticalBox(TileInfoText))
	{
		TileSlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 0.0f));
	}

	StatusText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("StatusText"));
	StatusText->SetAutoWrapText(true);
	MonopolyHUD::StyleText(StatusText, 14, FLinearColor(0.87f, 0.91f, 1.0f));
	if (UVerticalBoxSlot* StatusSlot = RootBox->AddChildToVerticalBox(StatusText))
	{
		StatusSlot->SetPadding(FMargin(0.0f, 6.0f, 0.0f, 14.0f));
	}

	RollButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("RollButton"));
	MonopolyHUD::StyleButton(RollButton, FLinearColor(0.20f, 0.60f, 1.0f));
	UTextBlock* RollText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("RollText"));
	RollText->SetText(FText::FromString(TEXT("掷骰子")));
	MonopolyHUD::StyleText(RollText, 15, FLinearColor::Black);
	RollButton->AddChild(RollText);
	RootBox->AddChildToVerticalBox(RollButton);

	EndTurnButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("EndTurnButton"));
	MonopolyHUD::StyleButton(EndTurnButton, FLinearColor(0.30f, 0.82f, 0.36f));
	UTextBlock* EndTurnText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("EndTurnText"));
	EndTurnText->SetText(FText::FromString(TEXT("结束回合")));
	MonopolyHUD::StyleText(EndTurnText, 15, FLinearColor::Black);
	EndTurnButton->AddChild(EndTurnText);
	if (UVerticalBoxSlot* EndTurnSlot = RootBox->AddChildToVerticalBox(EndTurnButton))
	{
		EndTurnSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));
	}

	PayBailButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("PayBailButton"));
	MonopolyHUD::StyleButton(PayBailButton, FLinearColor(1.0f, 0.68f, 0.24f));
	UTextBlock* BailText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("PayBailText"));
	BailText->SetText(FText::FromString(TEXT("支付保释金")));
	MonopolyHUD::StyleText(BailText, 15, FLinearColor::Black);
	PayBailButton->AddChild(BailText);
	if (UVerticalBoxSlot* BailSlot = RootBox->AddChildToVerticalBox(PayBailButton))
	{
		BailSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] HUD BuildRuntimeWidgetTree complete."));
}

void UMGameHUDWidget::RefreshAllText() const
{
	if (CurrentPlayerText != nullptr)
	{
		FString PlayerText = TEXT("当前玩家：等待初始化");
		if (CachedGameState != nullptr)
		{
			if (const AMMonopolyPlayerState* CurrentPlayerState = CachedGameState->GetMonopolyPlayer(CachedGameState->CurrentPlayerIndex))
			{
				PlayerText = FString::Printf(TEXT("当前玩家：P%d %s"), CachedGameState->CurrentPlayerIndex + 1, *CurrentPlayerState->GetResolvedDisplayName());
			}
		}
		CurrentPlayerText->SetText(FText::FromString(PlayerText));
	}

	if (TurnNumberText != nullptr)
	{
		const FString TurnText = CachedGameState != nullptr
			? FString::Printf(TEXT("回合：%d"), CachedGameState->TurnNumber)
			: TEXT("回合：等待初始化");
		TurnNumberText->SetText(FText::FromString(TurnText));
	}

	if (MoneySummaryText != nullptr)
	{
		MoneySummaryText->SetText(FText::FromString(BuildMoneySummary()));
	}

	if (TileInfoText != nullptr)
	{
		FString TileText = TEXT("当前位置：等待玩家移动");
		if (CachedGameState != nullptr)
		{
			if (const AMMonopolyPlayerState* CurrentPlayerState = CachedGameState->GetMonopolyPlayer(CachedGameState->CurrentPlayerIndex))
			{
				TileText = FString::Printf(TEXT("当前位置：格子 %d"), CurrentPlayerState->CurrentTileIndex);
			}
		}
		TileInfoText->SetText(FText::FromString(TileText));
	}

	if (StatusText != nullptr)
	{
		FString StateText = TEXT("状态：等待初始化");
		if (CachedGameState != nullptr)
		{
			if (const UEnum* EnumPtr = StaticEnum<EMTurnState>())
			{
				StateText = FString::Printf(TEXT("状态：%s"), *EnumPtr->GetDisplayNameTextByValue(static_cast<int64>(CachedGameState->TurnState)).ToString());
			}
		}
		StatusText->SetText(FText::FromString(StateText));
	}

	const AMMonopolyPlayerState* CurrentPlayerState = CachedGameState != nullptr
		? CachedGameState->GetMonopolyPlayer(CachedGameState->CurrentPlayerIndex)
		: nullptr;
	const bool bCanRoll = CachedGameState != nullptr && CachedGameState->TurnState == EMTurnState::WaitForRoll;
	const bool bCanEndTurn = CachedGameState != nullptr
		&& CachedGameState->TurnState != EMTurnState::GameOver
		&& CachedGameState->TurnState != EMTurnState::WaitingForPopup;
	const bool bCanPayBail = bCanRoll && CurrentPlayerState != nullptr && CurrentPlayerState->bIsInJail;

	if (RollButton != nullptr)
	{
		RollButton->SetIsEnabled(bCanRoll);
	}

	if (EndTurnButton != nullptr)
	{
		EndTurnButton->SetIsEnabled(bCanEndTurn);
	}

	if (PayBailButton != nullptr)
	{
		PayBailButton->SetIsEnabled(bCanPayBail);
		PayBailButton->SetVisibility(CurrentPlayerState != nullptr && CurrentPlayerState->bIsInJail ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
	}
}

FString UMGameHUDWidget::BuildMoneySummary() const
{
	if (CachedGameState == nullptr || CachedGameState->MonopolyPlayers.IsEmpty())
	{
		return TEXT("资金：尚未初始化");
	}

	TArray<FString> Lines;
	for (int32 PlayerIndex = 0; PlayerIndex < CachedGameState->MonopolyPlayers.Num(); ++PlayerIndex)
	{
		const AMMonopolyPlayerState* PlayerState = CachedGameState->MonopolyPlayers[PlayerIndex];
		if (PlayerState == nullptr)
		{
			continue;
		}

		Lines.Add(FString::Printf(TEXT("P%d %s：%d"), PlayerIndex + 1, *PlayerState->GetResolvedDisplayName(), PlayerState->Money));
	}

	return FString::Join(Lines, TEXT("\n"));
}
