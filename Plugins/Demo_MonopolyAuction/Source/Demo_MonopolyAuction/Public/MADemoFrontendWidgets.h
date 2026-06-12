// Copyright Phase14 demo agent.
// 前台外壳 Widget 基类集合:开始画面/主菜单/设置/暂停/结果。
// 均为 presence_only baseline 能力:提供必备入口/控件能力位与意图委托,具体视觉由蓝图子类搭建。
// 拆为独立 UCLASS,逐个对应 baseline capability story。
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MADemoFrontendWidgets.generated.h"

// ── 开始画面(baseline-start-screen)────────────────────────────
// 必备元素:项目标识展示 + 用户交互触发 + 跳转主菜单。
UCLASS(BlueprintType, Blueprintable)
class DEMO_MONOPOLYAUCTION_API UMADemoStartScreenWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	// 项目标识文本(标题),provisional 默认值。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "StartScreen")
	FText ProjectTitle;

	// 用户按任意键/点击触发:请求跳转主菜单。蓝图重写做实际页面切换。
	UFUNCTION(BlueprintCallable, Category = "StartScreen")
	void RequestNavigateToMainMenu();

	// 跳转主菜单事件(蓝图实现真正的 Widget 切换)。
	UFUNCTION(BlueprintImplementableEvent, Category = "StartScreen")
	void OnNavigateToMainMenu();
};

// ── 主菜单(baseline-main-menu)─────────────────────────────────
// 必备按钮:New Game / Settings / Quit。
UCLASS(BlueprintType, Blueprintable)
class DEMO_MONOPOLYAUCTION_API UMADemoMainMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "MainMenu")
	void IntentNewGame();

	UFUNCTION(BlueprintCallable, Category = "MainMenu")
	void IntentOpenSettings();

	UFUNCTION(BlueprintCallable, Category = "MainMenu")
	void IntentQuit();

	UFUNCTION(BlueprintImplementableEvent, Category = "MainMenu")
	void OnNewGameRequested();

	UFUNCTION(BlueprintImplementableEvent, Category = "MainMenu")
	void OnSettingsRequested();

	UFUNCTION(BlueprintImplementableEvent, Category = "MainMenu")
	void OnQuitRequested();
};

// ── 设置(baseline-settings)────────────────────────────────────
// 必备控件:主音量/SFX 音量/窗口模式/分辨率/应用/返回。
// provisional 持久化策略 = session_only(契约 clarification_markers cg-platform-persistence 默认值)。
UCLASS(BlueprintType, Blueprintable)
class DEMO_MONOPOLYAUCTION_API UMADemoSettingsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	// 主音量 0..1
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float MasterVolume = 1.0f;

	// SFX 音量 0..1
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
	float SFXVolume = 1.0f;

	// 窗口模式(0=全屏,1=窗口,2=无边框)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
	int32 WindowMode = 1;

	// 分辨率索引(provisional:预设列表,默认 1280x720)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Settings")
	FString ResolutionLabel = TEXT("1280x720");

	// 应用设置(session_only:运行期生效,不落盘)。
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void ApplySettings();

	// 返回上一页。
	UFUNCTION(BlueprintCallable, Category = "Settings")
	void RequestBack();

	UFUNCTION(BlueprintImplementableEvent, Category = "Settings")
	void OnSettingsApplied();

	UFUNCTION(BlueprintImplementableEvent, Category = "Settings")
	void OnBackRequested();
};

// ── 暂停(baseline-pause)───────────────────────────────────────
// 必备:ESC 入口 / Resume / Settings / Quit to Menu。
UCLASS(BlueprintType, Blueprintable)
class DEMO_MONOPOLYAUCTION_API UMADemoPauseWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	UFUNCTION(BlueprintCallable, Category = "Pause")
	void IntentResume();

	UFUNCTION(BlueprintCallable, Category = "Pause")
	void IntentOpenSettings();

	UFUNCTION(BlueprintCallable, Category = "Pause")
	void IntentQuitToMenu();

	UFUNCTION(BlueprintImplementableEvent, Category = "Pause")
	void OnResumeRequested();

	UFUNCTION(BlueprintImplementableEvent, Category = "Pause")
	void OnSettingsRequested();

	UFUNCTION(BlueprintImplementableEvent, Category = "Pause")
	void OnQuitToMenuRequested();
};

// ── 结果(baseline-results)─────────────────────────────────────
// 必备:胜者信息 + 返回主菜单。
UCLASS(BlueprintType, Blueprintable)
class DEMO_MONOPOLYAUCTION_API UMADemoResultsWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	// 胜者展示文本
	UPROPERTY(BlueprintReadWrite, Category = "Results")
	FText WinnerInfo;

	// 设置胜者信息(由结束流程调用)。
	UFUNCTION(BlueprintCallable, Category = "Results")
	void SetWinner(const FString& WinnerName);

	UFUNCTION(BlueprintCallable, Category = "Results")
	void RequestReturnToMenu();

	UFUNCTION(BlueprintImplementableEvent, Category = "Results")
	void OnReturnToMenuRequested();
};
