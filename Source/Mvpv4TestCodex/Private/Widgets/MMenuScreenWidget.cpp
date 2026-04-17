#include "MMenuScreenWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"

namespace MonopolyMenuScreen
{
	// 统一菜单文本样式，保证运行时无蓝图资源时也能直接可用。
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

		Text->SetFont(MakeFont(FontSize, FontSize >= 28 ? TEXT("Bold") : TEXT("Regular")));
		Text->SetColorAndOpacity(FSlateColor(Color));
		Text->SetShadowOffset(FVector2D(1.0f, 1.0f));
		Text->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.75f));
		Text->SetJustification(ETextJustify::Center);
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

TSharedRef<SWidget> UMMenuScreenWidget::RebuildWidget()
{
	BuildRuntimeWidgetTree();
	return Super::RebuildWidget();
}

void UMMenuScreenWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (PrimaryButton != nullptr && !PrimaryButton->OnClicked.IsAlreadyBound(this, &UMMenuScreenWidget::HandlePrimaryButtonClicked))
	{
		PrimaryButton->OnClicked.AddDynamic(this, &UMMenuScreenWidget::HandlePrimaryButtonClicked);
	}

	if (SecondaryButton != nullptr && !SecondaryButton->OnClicked.IsAlreadyBound(this, &UMMenuScreenWidget::HandleSecondaryButtonClicked))
	{
		SecondaryButton->OnClicked.AddDynamic(this, &UMMenuScreenWidget::HandleSecondaryButtonClicked);
	}

	if (TertiaryButton != nullptr && !TertiaryButton->OnClicked.IsAlreadyBound(this, &UMMenuScreenWidget::HandleTertiaryButtonClicked))
	{
		TertiaryButton->OnClicked.AddDynamic(this, &UMMenuScreenWidget::HandleTertiaryButtonClicked);
	}

	if (QuaternaryButton != nullptr && !QuaternaryButton->OnClicked.IsAlreadyBound(this, &UMMenuScreenWidget::HandleQuaternaryButtonClicked))
	{
		QuaternaryButton->OnClicked.AddDynamic(this, &UMMenuScreenWidget::HandleQuaternaryButtonClicked);
	}

	SetIsFocusable(true);
	SetVisibility(ESlateVisibility::Visible);
}

void UMMenuScreenWidget::ConfigureScreen(
	const FString& InTitle,
	const FString& InSubtitle,
	const TArray<FString>& InButtonLabels,
	TFunction<void(int32)> InClickHandler)
{
	ClickHandler = MoveTemp(InClickHandler);

	if (TitleTextBlock != nullptr)
	{
		TitleTextBlock->SetText(FText::FromString(InTitle));
	}

	if (SubtitleTextBlock != nullptr)
	{
		SubtitleTextBlock->SetText(FText::FromString(InSubtitle));
	}

	const TArray<UButton*> Buttons = { PrimaryButton, SecondaryButton, TertiaryButton, QuaternaryButton };
	const TArray<UTextBlock*> ButtonTexts = { PrimaryButtonText, SecondaryButtonText, TertiaryButtonText, QuaternaryButtonText };
	for (int32 Index = 0; Index < Buttons.Num(); ++Index)
	{
		if (Buttons[Index] == nullptr || ButtonTexts[Index] == nullptr)
		{
			continue;
		}

		const bool bVisible = InButtonLabels.IsValidIndex(Index);
		Buttons[Index]->SetVisibility(bVisible ? ESlateVisibility::Visible : ESlateVisibility::Collapsed);
		Buttons[Index]->SetIsEnabled(bVisible);
		if (bVisible)
		{
			ButtonTexts[Index]->SetText(FText::FromString(InButtonLabels[Index]));
		}
	}
}

void UMMenuScreenWidget::HandlePrimaryButtonClicked()
{
	HandleButtonClicked(0);
}

void UMMenuScreenWidget::HandleSecondaryButtonClicked()
{
	HandleButtonClicked(1);
}

void UMMenuScreenWidget::HandleTertiaryButtonClicked()
{
	HandleButtonClicked(2);
}

void UMMenuScreenWidget::HandleQuaternaryButtonClicked()
{
	HandleButtonClicked(3);
}

void UMMenuScreenWidget::BuildRuntimeWidgetTree()
{
	if (WidgetTree == nullptr || WidgetTree->RootWidget != nullptr)
	{
		return;
	}

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("MenuCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* RootBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("MenuRootBorder"));
	RootBorder->SetPadding(FMargin(28.0f));
	RootBorder->SetBrushColor(FLinearColor(0.03f, 0.04f, 0.07f, 0.92f));
	Canvas->AddChild(RootBorder);

	if (UCanvasPanelSlot* BorderSlot = Cast<UCanvasPanelSlot>(RootBorder->Slot))
	{
		BorderSlot->SetAnchors(FAnchors(0.5f, 0.5f));
		BorderSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		BorderSlot->SetPosition(FVector2D::ZeroVector);
		BorderSlot->SetAutoSize(true);
	}

	UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("MenuRootBox"));
	RootBorder->SetContent(RootBox);

	TitleTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TitleTextBlock"));
	TitleTextBlock->SetText(FText::FromString(TEXT("Monopoly")));
	MonopolyMenuScreen::StyleText(TitleTextBlock, 32);
	RootBox->AddChildToVerticalBox(TitleTextBlock);

	SubtitleTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("SubtitleTextBlock"));
	SubtitleTextBlock->SetAutoWrapText(true);
	SubtitleTextBlock->SetText(FText::FromString(TEXT("准备进入前台菜单。")));
	MonopolyMenuScreen::StyleText(SubtitleTextBlock, 16, FLinearColor(0.82f, 0.88f, 0.95f));
	if (UVerticalBoxSlot* SubtitleSlot = RootBox->AddChildToVerticalBox(SubtitleTextBlock))
	{
		SubtitleSlot->SetPadding(FMargin(0.0f, 10.0f, 0.0f, 18.0f));
	}

	const TArray<FName> ButtonNames =
	{
		TEXT("PrimaryButton"),
		TEXT("SecondaryButton"),
		TEXT("TertiaryButton"),
		TEXT("QuaternaryButton")
	};
	const TArray<FName> ButtonTextNames =
	{
		TEXT("PrimaryButtonText"),
		TEXT("SecondaryButtonText"),
		TEXT("TertiaryButtonText"),
		TEXT("QuaternaryButtonText")
	};
	const TArray<FLinearColor> ButtonColors =
	{
		FLinearColor(0.20f, 0.60f, 1.0f),
		FLinearColor(0.30f, 0.82f, 0.36f),
		FLinearColor(0.95f, 0.75f, 0.26f),
		FLinearColor(0.82f, 0.32f, 0.32f)
	};

	for (int32 Index = 0; Index < ButtonNames.Num(); ++Index)
	{
		UButton* Button = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), ButtonNames[Index]);
		MonopolyMenuScreen::StyleButton(Button, ButtonColors[Index]);

		UTextBlock* ButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), ButtonTextNames[Index]);
		ButtonText->SetText(FText::FromString(TEXT("按钮")));
		MonopolyMenuScreen::StyleText(ButtonText, 16, FLinearColor::Black);
		Button->AddChild(ButtonText);

		if (UVerticalBoxSlot* ButtonSlot = RootBox->AddChildToVerticalBox(Button))
		{
			ButtonSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));
		}

		Button->SetVisibility(ESlateVisibility::Collapsed);

		switch (Index)
		{
		case 0:
			PrimaryButton = Button;
			PrimaryButtonText = ButtonText;
			break;
		case 1:
			SecondaryButton = Button;
			SecondaryButtonText = ButtonText;
			break;
		case 2:
			TertiaryButton = Button;
			TertiaryButtonText = ButtonText;
			break;
		default:
			QuaternaryButton = Button;
			QuaternaryButtonText = ButtonText;
			break;
		}
	}
}

void UMMenuScreenWidget::HandleButtonClicked(const int32 ButtonIndex)
{
	if (ClickHandler)
	{
		ClickHandler(ButtonIndex);
	}
}
