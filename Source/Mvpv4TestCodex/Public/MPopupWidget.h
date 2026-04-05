#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MPopupWidget.generated.h"

class UButton;
class UTextBlock;
class UVerticalBox;

UCLASS()
class MVPV4TESTCODEX_API UMPopupWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;

	// 弹窗标题文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> TitleTextBlock;

	// 弹窗正文文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> MessageTextBlock;

	// 主按钮。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UButton> PrimaryButton;

	// 次按钮。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UButton> SecondaryButton;

	// 第三个按钮。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UButton> TertiaryButton;

	void ShowPopup(const FString& InTitle, const FString& InMessage, const TArray<FString>& ButtonLabels, TFunction<void(int32)> InClickHandler);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void ClosePopup();

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> PrimaryButtonText;

	UPROPERTY()
	TObjectPtr<UTextBlock> SecondaryButtonText;

	UPROPERTY()
	TObjectPtr<UTextBlock> TertiaryButtonText;

	UPROPERTY()
	TObjectPtr<UVerticalBox> RootBox;

	TFunction<void(int32)> ClickHandler;

	UFUNCTION()
	void HandlePrimaryButtonClicked();

	UFUNCTION()
	void HandleSecondaryButtonClicked();

	UFUNCTION()
	void HandleTertiaryButtonClicked();

	// 在 Slate 可见树重建前准备好弹窗内容，避免 AddToViewport 后界面为空。
	void BuildRuntimeWidgetTree();

	void HandleButtonClicked(int32 ButtonIndex);
};
