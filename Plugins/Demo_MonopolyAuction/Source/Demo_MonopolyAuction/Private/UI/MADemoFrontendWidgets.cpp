// Copyright Phase14 v0 attempt2. 前台外壳 widget 实现。
#include "UI/MADemoFrontendWidgets.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/Border.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Blueprint/WidgetTree.h"

void UMADemoFrontendPanelBase::NativeConstruct()
{
	Super::NativeConstruct();
	ConfigurePanel();
	BuildPanel();
}

void UMADemoFrontendPanelBase::BuildPanel()
{
	if (!WidgetTree)
	{
		return;
	}
	UCanvasPanel* Root = WidgetTree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("Root"));
	WidgetTree->RootWidget = Root;

	UBorder* Panel = WidgetTree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("Panel"));
	Panel->SetBrushColor(FLinearColor(0.05f, 0.05f, 0.1f, 0.85f));
	Panel->SetPadding(FMargin(24.f));

	ContentBox = WidgetTree->ConstructWidget<UVerticalBox>(UVerticalBox::StaticClass(), TEXT("Box"));
	Panel->SetContent(ContentBox);

	// 标题。
	UTextBlock* Title = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), TEXT("Title"));
	FSlateFontInfo TitleFont = Title->GetFont();
	TitleFont.Size = 26;
	Title->SetFont(TitleFont);
	Title->SetColorAndOpacity(FSlateColor(FLinearColor(1.f, 0.85f, 0.2f)));
	Title->SetText(FText::FromString(PanelTitle));
	ContentBox->AddChildToVerticalBox(Title);

	// 元素条目。
	for (const FString& Elem : Elements)
	{
		UTextBlock* Line = WidgetTree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass());
		FSlateFontInfo Font = Line->GetFont();
		Font.Size = 18;
		Line->SetFont(Font);
		Line->SetColorAndOpacity(FSlateColor(FLinearColor::White));
		Line->SetText(FText::FromString(FString::Printf(TEXT("- %s"), *Elem)));
		ContentBox->AddChildToVerticalBox(Line);
	}

	if (UCanvasPanelSlot* PanelSlot = Root->AddChildToCanvas(Panel))
	{
		PanelSlot->SetPosition(FVector2D(440.f, 220.f));
		PanelSlot->SetSize(FVector2D(420.f, 320.f));
		PanelSlot->SetAutoSize(false);
	}
}

// --- 开始画面 ---
void UMADemoStartScreenWidget::ConfigurePanel()
{
	PanelTitle = TEXT("大富翁拍卖版 — 开始");
	Elements = { TEXT("项目标识: Demo_MonopolyAuction"),
		TEXT("按 [Enter] 开始"), TEXT("进入主菜单") };
}
void UMADemoStartScreenWidget::NavigateToMainMenu() {}

// --- 主菜单 ---
void UMADemoMainMenuWidget::ConfigurePanel()
{
	PanelTitle = TEXT("主菜单");
	Elements = { TEXT("New Game"), TEXT("Settings"), TEXT("Quit") };
}
void UMADemoMainMenuWidget::IntentNewGame() {}
void UMADemoMainMenuWidget::IntentOpenSettings() {}
void UMADemoMainMenuWidget::IntentQuit() {}

// --- 设置 ---
void UMADemoSettingsWidget::ConfigurePanel()
{
	PanelTitle = TEXT("设置");
	Elements = { TEXT("Master Volume"), TEXT("SFX Volume"),
		TEXT("Window Mode"), TEXT("Resolution"), TEXT("Apply"), TEXT("Back") };
}
void UMADemoSettingsWidget::ApplySettings() {}
void UMADemoSettingsWidget::Back() {}

// --- 暂停 ---
void UMADemoPauseWidget::ConfigurePanel()
{
	PanelTitle = TEXT("暂停");
	Elements = { TEXT("Resume"), TEXT("Settings"), TEXT("Quit to Menu") };
}
void UMADemoPauseWidget::Resume() {}
void UMADemoPauseWidget::QuitToMenu() {}

// --- 结果 ---
void UMADemoResultsWidget::ConfigurePanel()
{
	PanelTitle = TEXT("对局结果");
	Elements = { TEXT("winner_info"), TEXT("Return to Menu") };
}
void UMADemoResultsWidget::ShowResult(AMADemoGameState* GameState)
{
	if (GameState && GameState->bGameOver)
	{
		Elements = {
			FString::Printf(TEXT("winner_info: 胜者 P%d 获胜"), GameState->WinnerIndex + 1),
			TEXT("Return to Menu")
		};
	}
}
void UMADemoResultsWidget::ReturnToMenu() {}
