#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MMenuScreenWidget.generated.h"

class UButton;
class UTextBlock;

UCLASS()
class MVPV4TESTCODEX_API UMMenuScreenWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;

	// 配置通用菜单页的标题、副标题和按钮行为。
	void ConfigureScreen(
		const FString& InTitle,
		const FString& InSubtitle,
		const TArray<FString>& InButtonLabels,
		TFunction<void(int32)> InClickHandler);

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> TitleTextBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> SubtitleTextBlock;

	UPROPERTY()
	TObjectPtr<UButton> PrimaryButton;

	UPROPERTY()
	TObjectPtr<UButton> SecondaryButton;

	UPROPERTY()
	TObjectPtr<UButton> TertiaryButton;

	UPROPERTY()
	TObjectPtr<UButton> QuaternaryButton;

	UPROPERTY()
	TObjectPtr<UTextBlock> PrimaryButtonText;

	UPROPERTY()
	TObjectPtr<UTextBlock> SecondaryButtonText;

	UPROPERTY()
	TObjectPtr<UTextBlock> TertiaryButtonText;

	UPROPERTY()
	TObjectPtr<UTextBlock> QuaternaryButtonText;

	TFunction<void(int32)> ClickHandler;

	UFUNCTION()
	void HandlePrimaryButtonClicked();

	UFUNCTION()
	void HandleSecondaryButtonClicked();

	UFUNCTION()
	void HandleTertiaryButtonClicked();

	UFUNCTION()
	void HandleQuaternaryButtonClicked();

	void BuildRuntimeWidgetTree();
	void HandleButtonClicked(int32 ButtonIndex);
};
