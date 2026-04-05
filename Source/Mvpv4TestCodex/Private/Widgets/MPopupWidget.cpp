#include "MPopupWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"

namespace MonopolyPopup
{
	// 统一弹窗文本样式，保证按钮和正文在运行时可直接辨识。
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

		Text->SetFont(MakeFont(FontSize, FontSize >= 20 ? TEXT("Bold") : TEXT("Regular")));
		Text->SetColorAndOpacity(FSlateColor(Color));
		Text->SetShadowOffset(FVector2D(1.0f, 1.0f));
		Text->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.7f));
	}
}

TSharedRef<SWidget> UMPopupWidget::RebuildWidget()
{
	BuildRuntimeWidgetTree();
	const TSharedRef<SWidget> SlateWidget = Super::RebuildWidget();
	UE_LOG(LogTemp, Log, TEXT("[Phase8] Popup RebuildWidget prepared. RootWidget=%s"),
		WidgetTree != nullptr && WidgetTree->RootWidget != nullptr ? TEXT("ok") : TEXT("null"));
	return SlateWidget;
}

void UMPopupWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (PrimaryButton != nullptr && !PrimaryButton->OnClicked.IsAlreadyBound(this, &UMPopupWidget::HandlePrimaryButtonClicked))
	{
		PrimaryButton->OnClicked.AddDynamic(this, &UMPopupWidget::HandlePrimaryButtonClicked);
	}

	if (SecondaryButton != nullptr && !SecondaryButton->OnClicked.IsAlreadyBound(this, &UMPopupWidget::HandleSecondaryButtonClicked))
	{
		SecondaryButton->OnClicked.AddDynamic(this, &UMPopupWidget::HandleSecondaryButtonClicked);
	}

	if (TertiaryButton != nullptr && !TertiaryButton->OnClicked.IsAlreadyBound(this, &UMPopupWidget::HandleTertiaryButtonClicked))
	{
		TertiaryButton->OnClicked.AddDynamic(this, &UMPopupWidget::HandleTertiaryButtonClicked);
	}

	SetIsFocusable(true);
	SetVisibility(ESlateVisibility::Visible);

	if (SecondaryButton != nullptr)
	{
		SecondaryButton->SetVisibility(ESlateVisibility::Collapsed);
	}

	if (TertiaryButton != nullptr)
	{
		TertiaryButton->SetVisibility(ESlateVisibility::Collapsed);
	}
}

void UMPopupWidget::ShowPopup(const FString& InTitle, const FString& InMessage, const TArray<FString>& ButtonLabels, TFunction<void(int32)> InClickHandler)
{
	ClickHandler = MoveTemp(InClickHandler);

	if (TitleTextBlock != nullptr)
	{
		TitleTextBlock->SetText(FText::FromString(InTitle));
	}

	if (MessageTextBlock != nullptr)
	{
		MessageTextBlock->SetText(FText::FromString(InMessage));
	}

	const TArray<UButton*> Buttons = { PrimaryButton, SecondaryButton, TertiaryButton };
	const TArray<UTextBlock*> ButtonTexts = { PrimaryButtonText, SecondaryButtonText, TertiaryButtonText };

	for (int32 Index = 0; Index < Buttons.Num(); ++Index)
	{
		if (Buttons[Index] == nullptr || ButtonTexts[Index] == nullptr)
		{
			continue;
		}

		const bool bVisible = ButtonLabels.IsValidIndex(Index);
		Buttons[Index]->SetVisibility(bVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
		if (bVisible)
		{
			ButtonTexts[Index]->SetText(FText::FromString(ButtonLabels[Index]));
		}
	}
}

void UMPopupWidget::ClosePopup()
{
	RemoveFromParent();
}

void UMPopupWidget::HandlePrimaryButtonClicked()
{
	HandleButtonClicked(0);
}

void UMPopupWidget::HandleSecondaryButtonClicked()
{
	HandleButtonClicked(1);
}

void UMPopupWidget::HandleTertiaryButtonClicked()
{
	HandleButtonClicked(2);
}

void UMPopupWidget::BuildRuntimeWidgetTree()
{
	if (WidgetTree == nullptr)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Phase8] Popup BuildRuntimeWidgetTree skipped: WidgetTree=null"));
		return;
	}

	if (WidgetTree->RootWidget != nullptr)
	{
		return;
	}

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("PopupCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* RootBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("PopupRootBorder"));
	RootBorder->SetPadding(FMargin(20.0f));
	RootBorder->SetBrushColor(FLinearColor(0.05f, 0.05f, 0.08f, 0.92f));
	Canvas->AddChild(RootBorder);

	if (UCanvasPanelSlot* BorderSlot = Cast<UCanvasPanelSlot>(RootBorder->Slot))
	{
		BorderSlot->SetAnchors(FAnchors(0.5f, 0.5f));
		BorderSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		BorderSlot->SetPosition(FVector2D::ZeroVector);
		BorderSlot->SetAutoSize(true);
	}

	RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("PopupRootBox"));
	RootBorder->SetContent(RootBox);

	TitleTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TitleTextBlock"));
	TitleTextBlock->SetText(FText::FromString(TEXT("提示")));
	MonopolyPopup::StyleText(TitleTextBlock, 24);
	RootBox->AddChildToVerticalBox(TitleTextBlock);

	MessageTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("MessageTextBlock"));
	MessageTextBlock->SetText(FText::GetEmpty());
	MessageTextBlock->SetAutoWrapText(true);
	MonopolyPopup::StyleText(MessageTextBlock, 16);
	if (UVerticalBoxSlot* MessageSlot = RootBox->AddChildToVerticalBox(MessageTextBlock))
	{
		MessageSlot->SetPadding(FMargin(0.0f, 12.0f, 0.0f, 16.0f));
	}

	PrimaryButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("PrimaryButton"));
	PrimaryButton->SetBackgroundColor(FLinearColor(0.20f, 0.60f, 1.0f));
	PrimaryButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("PrimaryButtonText"));
	PrimaryButtonText->SetText(FText::FromString(TEXT("确定")));
	MonopolyPopup::StyleText(PrimaryButtonText, 15, FLinearColor::Black);
	PrimaryButton->AddChild(PrimaryButtonText);
	RootBox->AddChildToVerticalBox(PrimaryButton);

	SecondaryButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("SecondaryButton"));
	SecondaryButton->SetBackgroundColor(FLinearColor(0.76f, 0.76f, 0.76f));
	SecondaryButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SecondaryButtonText"));
	SecondaryButtonText->SetText(FText::FromString(TEXT("取消")));
	MonopolyPopup::StyleText(SecondaryButtonText, 15, FLinearColor::Black);
	SecondaryButton->AddChild(SecondaryButtonText);
	if (UVerticalBoxSlot* SecondarySlot = RootBox->AddChildToVerticalBox(SecondaryButton))
	{
		SecondarySlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));
	}

	TertiaryButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("TertiaryButton"));
	TertiaryButton->SetBackgroundColor(FLinearColor(0.95f, 0.75f, 0.26f));
	TertiaryButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TertiaryButtonText"));
	TertiaryButtonText->SetText(FText::FromString(TEXT("第三选项")));
	MonopolyPopup::StyleText(TertiaryButtonText, 15, FLinearColor::Black);
	TertiaryButton->AddChild(TertiaryButtonText);
	if (UVerticalBoxSlot* TertiarySlot = RootBox->AddChildToVerticalBox(TertiaryButton))
	{
		TertiarySlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] Popup BuildRuntimeWidgetTree complete."));
}

void UMPopupWidget::HandleButtonClicked(const int32 ButtonIndex)
{
	TFunction<void(int32)> LocalHandler = MoveTemp(ClickHandler);
	ClosePopup();
	if (LocalHandler)
	{
		LocalHandler(ButtonIndex);
	}
}
