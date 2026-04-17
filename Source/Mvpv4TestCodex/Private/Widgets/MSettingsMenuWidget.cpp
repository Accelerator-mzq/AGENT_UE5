#include "MSettingsMenuWidget.h"

#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/ComboBoxString.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/Slider.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Styling/CoreStyle.h"

namespace MonopolySettingsMenu
{
	// 统一设置页文本样式，避免运行时纯代码构建时出现默认字号混乱。
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

		Text->SetFont(MakeFont(FontSize, FontSize >= 24 ? TEXT("Bold") : TEXT("Regular")));
		Text->SetColorAndOpacity(FSlateColor(Color));
		Text->SetShadowOffset(FVector2D(1.0f, 1.0f));
		Text->SetShadowColorAndOpacity(FLinearColor(0.0f, 0.0f, 0.0f, 0.75f));
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

TSharedRef<SWidget> UMSettingsMenuWidget::RebuildWidget()
{
	BuildRuntimeWidgetTree();
	return Super::RebuildWidget();
}

void UMSettingsMenuWidget::NativeConstruct()
{
	Super::NativeConstruct();

	if (MasterVolumeSlider != nullptr && !MasterVolumeSlider->OnValueChanged.IsAlreadyBound(this, &UMSettingsMenuWidget::HandleMasterVolumeChanged))
	{
		MasterVolumeSlider->OnValueChanged.AddDynamic(this, &UMSettingsMenuWidget::HandleMasterVolumeChanged);
	}

	if (SfxVolumeSlider != nullptr && !SfxVolumeSlider->OnValueChanged.IsAlreadyBound(this, &UMSettingsMenuWidget::HandleSfxVolumeChanged))
	{
		SfxVolumeSlider->OnValueChanged.AddDynamic(this, &UMSettingsMenuWidget::HandleSfxVolumeChanged);
	}

	if (ApplyButton != nullptr && !ApplyButton->OnClicked.IsAlreadyBound(this, &UMSettingsMenuWidget::HandleApplyClicked))
	{
		ApplyButton->OnClicked.AddDynamic(this, &UMSettingsMenuWidget::HandleApplyClicked);
	}

	if (BackButton != nullptr && !BackButton->OnClicked.IsAlreadyBound(this, &UMSettingsMenuWidget::HandleBackClicked))
	{
		BackButton->OnClicked.AddDynamic(this, &UMSettingsMenuWidget::HandleBackClicked);
	}

	SetIsFocusable(true);
	SetVisibility(ESlateVisibility::Visible);
	RefreshDisplayedValues();
}

void UMSettingsMenuWidget::ConfigureSettings(
	float InMasterVolume,
	float InSfxVolume,
	const TArray<FString>& InWindowModeOptions,
	const FString& InSelectedWindowMode,
	const TArray<FString>& InResolutionOptions,
	const FString& InSelectedResolution,
	TFunction<void(float, float, const FString&, const FString&)> InApplyHandler,
	TFunction<void()> InBackHandler)
{
	ApplyHandler = MoveTemp(InApplyHandler);
	BackHandler = MoveTemp(InBackHandler);

	if (MasterVolumeSlider != nullptr)
	{
		MasterVolumeSlider->SetValue(FMath::Clamp(InMasterVolume, 0.0f, 1.0f));
	}

	if (SfxVolumeSlider != nullptr)
	{
		SfxVolumeSlider->SetValue(FMath::Clamp(InSfxVolume, 0.0f, 1.0f));
	}

	PopulateComboBox(WindowModeComboBox, InWindowModeOptions, InSelectedWindowMode);
	PopulateComboBox(ResolutionComboBox, InResolutionOptions, InSelectedResolution);
	RefreshDisplayedValues();
}

void UMSettingsMenuWidget::HandleMasterVolumeChanged(const float NewValue)
{
	if (MasterVolumeValueText != nullptr)
	{
		MasterVolumeValueText->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(NewValue * 100.0f))));
	}
}

void UMSettingsMenuWidget::HandleSfxVolumeChanged(const float NewValue)
{
	if (SfxVolumeValueText != nullptr)
	{
		SfxVolumeValueText->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(NewValue * 100.0f))));
	}
}

void UMSettingsMenuWidget::HandleApplyClicked()
{
	if (ApplyHandler)
	{
		const FString WindowModeOption = WindowModeComboBox != nullptr ? WindowModeComboBox->GetSelectedOption() : FString();
		const FString ResolutionOption = ResolutionComboBox != nullptr ? ResolutionComboBox->GetSelectedOption() : FString();
		ApplyHandler(
			MasterVolumeSlider != nullptr ? MasterVolumeSlider->GetValue() : 1.0f,
			SfxVolumeSlider != nullptr ? SfxVolumeSlider->GetValue() : 1.0f,
			WindowModeOption,
			ResolutionOption);
	}
}

void UMSettingsMenuWidget::HandleBackClicked()
{
	if (BackHandler)
	{
		BackHandler();
	}
}

void UMSettingsMenuWidget::BuildRuntimeWidgetTree()
{
	if (WidgetTree == nullptr || WidgetTree->RootWidget != nullptr)
	{
		return;
	}

	UCanvasPanel* Canvas = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("SettingsCanvas"));
	WidgetTree->RootWidget = Canvas;

	UBorder* RootBorder = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("SettingsRootBorder"));
	RootBorder->SetPadding(FMargin(28.0f));
	RootBorder->SetBrushColor(FLinearColor(0.04f, 0.05f, 0.09f, 0.94f));
	Canvas->AddChild(RootBorder);

	if (UCanvasPanelSlot* BorderSlot = Cast<UCanvasPanelSlot>(RootBorder->Slot))
	{
		BorderSlot->SetAnchors(FAnchors(0.5f, 0.5f));
		BorderSlot->SetAlignment(FVector2D(0.5f, 0.5f));
		BorderSlot->SetPosition(FVector2D::ZeroVector);
		BorderSlot->SetAutoSize(true);
	}

	UVerticalBox* RootBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("SettingsRootBox"));
	RootBorder->SetContent(RootBox);

	TitleTextBlock = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("TitleTextBlock"));
	TitleTextBlock->SetText(FText::FromString(TEXT("设置")));
	MonopolySettingsMenu::StyleText(TitleTextBlock, 28);
	RootBox->AddChildToVerticalBox(TitleTextBlock);

	auto AddSliderRow = [this, RootBox](const TCHAR* LabelText, const FName LabelName, const FName SliderName, const FName ValueName, TObjectPtr<USlider>& SliderRef, TObjectPtr<UTextBlock>& ValueRef)
	{
		UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), LabelName);
		Label->SetText(FText::FromString(LabelText));
		MonopolySettingsMenu::StyleText(Label, 16);
		if (UVerticalBoxSlot* LabelSlot = RootBox->AddChildToVerticalBox(Label))
		{
			LabelSlot->SetPadding(FMargin(0.0f, 16.0f, 0.0f, 4.0f));
		}

		UHorizontalBox* Row = WidgetTree->ConstructWidget<UHorizontalBox>(UHorizontalBox::StaticClass(), FName(*FString::Printf(TEXT("%sRow"), LabelText)));
		RootBox->AddChildToVerticalBox(Row);

		SliderRef = WidgetTree->ConstructWidget<USlider>(USlider::StaticClass(), SliderName);
		SliderRef->SetMinValue(0.0f);
		SliderRef->SetMaxValue(1.0f);
		SliderRef->SetStepSize(0.05f);
		if (UHorizontalBoxSlot* SliderSlot = Row->AddChildToHorizontalBox(SliderRef))
		{
			SliderSlot->SetPadding(FMargin(0.0f, 0.0f, 12.0f, 0.0f));
			SliderSlot->SetSize(FSlateChildSize(ESlateSizeRule::Fill));
		}

		ValueRef = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), ValueName);
		ValueRef->SetText(FText::FromString(TEXT("100%")));
		MonopolySettingsMenu::StyleText(ValueRef, 14, FLinearColor(0.95f, 0.95f, 0.95f));
		Row->AddChildToHorizontalBox(ValueRef);
	};

	AddSliderRow(TEXT("主音量"), TEXT("MasterVolumeLabel"), TEXT("MasterVolumeSlider"), TEXT("MasterVolumeValueText"), MasterVolumeSlider, MasterVolumeValueText);
	AddSliderRow(TEXT("音效音量"), TEXT("SfxVolumeLabel"), TEXT("SfxVolumeSlider"), TEXT("SfxVolumeValueText"), SfxVolumeSlider, SfxVolumeValueText);

	auto AddComboRow = [this, RootBox](const TCHAR* LabelText, const FName LabelName, const FName ComboName, TObjectPtr<UComboBoxString>& ComboRef)
	{
		UTextBlock* Label = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), LabelName);
		Label->SetText(FText::FromString(LabelText));
		MonopolySettingsMenu::StyleText(Label, 16);
		if (UVerticalBoxSlot* LabelSlot = RootBox->AddChildToVerticalBox(Label))
		{
			LabelSlot->SetPadding(FMargin(0.0f, 16.0f, 0.0f, 4.0f));
		}

		ComboRef = WidgetTree->ConstructWidget<UComboBoxString>(UComboBoxString::StaticClass(), ComboName);
		RootBox->AddChildToVerticalBox(ComboRef);
	};

	AddComboRow(TEXT("窗口模式"), TEXT("WindowModeLabel"), TEXT("WindowModeComboBox"), WindowModeComboBox);
	AddComboRow(TEXT("分辨率"), TEXT("ResolutionLabel"), TEXT("ResolutionComboBox"), ResolutionComboBox);

	ApplyButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("ApplyButton"));
	MonopolySettingsMenu::StyleButton(ApplyButton, FLinearColor(0.20f, 0.60f, 1.0f));
	ApplyButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("ApplyButtonText"));
	ApplyButtonText->SetText(FText::FromString(TEXT("应用")));
	MonopolySettingsMenu::StyleText(ApplyButtonText, 15, FLinearColor::Black);
	ApplyButton->AddChild(ApplyButtonText);
	if (UVerticalBoxSlot* ApplySlot = RootBox->AddChildToVerticalBox(ApplyButton))
	{
		ApplySlot->SetPadding(FMargin(0.0f, 20.0f, 0.0f, 0.0f));
	}

	BackButton = WidgetTree->ConstructWidget<UButton>(UButton::StaticClass(), TEXT("BackButton"));
	MonopolySettingsMenu::StyleButton(BackButton, FLinearColor(0.78f, 0.78f, 0.78f));
	BackButtonText = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("BackButtonText"));
	BackButtonText->SetText(FText::FromString(TEXT("返回")));
	MonopolySettingsMenu::StyleText(BackButtonText, 15, FLinearColor::Black);
	BackButton->AddChild(BackButtonText);
	if (UVerticalBoxSlot* BackSlot = RootBox->AddChildToVerticalBox(BackButton))
	{
		BackSlot->SetPadding(FMargin(0.0f, 8.0f, 0.0f, 0.0f));
	}
}

void UMSettingsMenuWidget::RefreshDisplayedValues() const
{
	if (MasterVolumeSlider != nullptr && MasterVolumeValueText != nullptr)
	{
		MasterVolumeValueText->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(MasterVolumeSlider->GetValue() * 100.0f))));
	}

	if (SfxVolumeSlider != nullptr && SfxVolumeValueText != nullptr)
	{
		SfxVolumeValueText->SetText(FText::FromString(FString::Printf(TEXT("%d%%"), FMath::RoundToInt(SfxVolumeSlider->GetValue() * 100.0f))));
	}
}

void UMSettingsMenuWidget::PopulateComboBox(UComboBoxString* ComboBox, const TArray<FString>& Options, const FString& SelectedOption) const
{
	if (ComboBox == nullptr)
	{
		return;
	}

	ComboBox->ClearOptions();
	for (const FString& Option : Options)
	{
		ComboBox->AddOption(Option);
	}

	if (!SelectedOption.IsEmpty())
	{
		ComboBox->SetSelectedOption(SelectedOption);
	}
	else if (Options.Num() > 0)
	{
		ComboBox->SetSelectedOption(Options[0]);
	}
}
