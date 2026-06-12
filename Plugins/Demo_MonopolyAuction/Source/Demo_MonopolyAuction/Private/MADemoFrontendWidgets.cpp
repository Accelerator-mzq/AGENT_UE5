// Copyright Phase14 demo agent.
#include "MADemoFrontendWidgets.h"

// ── 开始画面 ──────────────────────────────────────────────
void UMADemoStartScreenWidget::RequestNavigateToMainMenu()
{
	// 仅发意图;真正的页面切换由蓝图重写 OnNavigateToMainMenu 完成
	OnNavigateToMainMenu();
}

// ── 主菜单 ────────────────────────────────────────────────
void UMADemoMainMenuWidget::IntentNewGame()
{
	OnNewGameRequested();
}

void UMADemoMainMenuWidget::IntentOpenSettings()
{
	OnSettingsRequested();
}

void UMADemoMainMenuWidget::IntentQuit()
{
	OnQuitRequested();
}

// ── 设置 ──────────────────────────────────────────────────
void UMADemoSettingsWidget::ApplySettings()
{
	// session_only:运行期生效,不落盘(provisional cg-platform-persistence 默认值)
	MasterVolume = FMath::Clamp(MasterVolume, 0.0f, 1.0f);
	SFXVolume = FMath::Clamp(SFXVolume, 0.0f, 1.0f);
	OnSettingsApplied();
}

void UMADemoSettingsWidget::RequestBack()
{
	OnBackRequested();
}

// ── 暂停 ──────────────────────────────────────────────────
void UMADemoPauseWidget::IntentResume()
{
	OnResumeRequested();
}

void UMADemoPauseWidget::IntentOpenSettings()
{
	OnSettingsRequested();
}

void UMADemoPauseWidget::IntentQuitToMenu()
{
	OnQuitToMenuRequested();
}

// ── 结果 ──────────────────────────────────────────────────
void UMADemoResultsWidget::SetWinner(const FString& WinnerName)
{
	WinnerInfo = FText::FromString(FString::Printf(TEXT("%s 获胜!"), *WinnerName));
}

void UMADemoResultsWidget::RequestReturnToMenu()
{
	OnReturnToMenuRequested();
}
