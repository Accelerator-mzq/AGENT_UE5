// Copyright Phase14 v0 attempt2. 前台外壳 widget(开始/主菜单/设置/暂停/结果)。
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MADemoFrontendWidgets.generated.h"

class UTextBlock;
class UVerticalBox;
class UButton;
class AMADemoGameState;

// 前台外壳基类:统一用代码构建一个标题 + 若干文本条目的简单可见面板。
// presence_only 契约:只需必备元素存在 + 可见,不展开完整交互。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoFrontendPanelBase : public UUserWidget
{
	GENERATED_BODY()

public:
	// 面板标题。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Frontend")
	FString PanelTitle;

	// 必备元素文本条目(按钮/控件名)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Frontend")
	TArray<FString> Elements;

protected:
	virtual void NativeConstruct() override;

	// 由子类在构造前填好 PanelTitle / Elements。
	virtual void ConfigurePanel() {}

	// 代码构建可见面板。
	void BuildPanel();

	UPROPERTY()
	TObjectPtr<UVerticalBox> ContentBox;
};

// 开始画面:项目标识 + 交互触发提示 + 进主菜单(required_elements)。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoStartScreenWidget : public UMADemoFrontendPanelBase
{
	GENERATED_BODY()
protected:
	virtual void ConfigurePanel() override;
public:
	// 进入主菜单意图。
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void NavigateToMainMenu();
};

// 主菜单:New Game / Settings / Quit。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoMainMenuWidget : public UMADemoFrontendPanelBase
{
	GENERATED_BODY()
protected:
	virtual void ConfigurePanel() override;
public:
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void IntentNewGame();
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void IntentOpenSettings();
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void IntentQuit();
};

// 设置:主音量/SFX音量/窗口模式/分辨率/Apply/Back。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoSettingsWidget : public UMADemoFrontendPanelBase
{
	GENERATED_BODY()
protected:
	virtual void ConfigurePanel() override;
public:
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void ApplySettings();
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void Back();
};

// 暂停:Resume / Settings / Quit to Menu(ESC 进入)。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoPauseWidget : public UMADemoFrontendPanelBase
{
	GENERATED_BODY()
protected:
	virtual void ConfigurePanel() override;
public:
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void Resume();
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void QuitToMenu();
};

// 结果:winner_info / Return to Menu。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoResultsWidget : public UMADemoFrontendPanelBase
{
	GENERATED_BODY()
protected:
	virtual void ConfigurePanel() override;
public:
	// 用 GameState 胜者信息填充结果(只读)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void ShowResult(AMADemoGameState* GameState);
	UFUNCTION(BlueprintCallable, Category = "Demo|Frontend")
	void ReturnToMenu();
};
