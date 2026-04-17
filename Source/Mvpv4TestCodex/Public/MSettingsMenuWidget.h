#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MSettingsMenuWidget.generated.h"

class UButton;
class UComboBoxString;
class USlider;
class UTextBlock;

UCLASS()
class MVPV4TESTCODEX_API UMSettingsMenuWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;

	// 配置设置页的当前值、可选项和按钮回调。
	void ConfigureSettings(
		float InMasterVolume,
		float InSfxVolume,
		const TArray<FString>& InWindowModeOptions,
		const FString& InSelectedWindowMode,
		const TArray<FString>& InResolutionOptions,
		const FString& InSelectedResolution,
		TFunction<void(float, float, const FString&, const FString&)> InApplyHandler,
		TFunction<void()> InBackHandler);

private:
	UPROPERTY()
	TObjectPtr<UTextBlock> TitleTextBlock;

	UPROPERTY()
	TObjectPtr<UTextBlock> MasterVolumeValueText;

	UPROPERTY()
	TObjectPtr<UTextBlock> SfxVolumeValueText;

	UPROPERTY()
	TObjectPtr<USlider> MasterVolumeSlider;

	UPROPERTY()
	TObjectPtr<USlider> SfxVolumeSlider;

	UPROPERTY()
	TObjectPtr<UComboBoxString> WindowModeComboBox;

	UPROPERTY()
	TObjectPtr<UComboBoxString> ResolutionComboBox;

	UPROPERTY()
	TObjectPtr<UButton> ApplyButton;

	UPROPERTY()
	TObjectPtr<UButton> BackButton;

	UPROPERTY()
	TObjectPtr<UTextBlock> ApplyButtonText;

	UPROPERTY()
	TObjectPtr<UTextBlock> BackButtonText;

	TFunction<void(float, float, const FString&, const FString&)> ApplyHandler;
	TFunction<void()> BackHandler;

	UFUNCTION()
	void HandleMasterVolumeChanged(float NewValue);

	UFUNCTION()
	void HandleSfxVolumeChanged(float NewValue);

	UFUNCTION()
	void HandleApplyClicked();

	UFUNCTION()
	void HandleBackClicked();

	void BuildRuntimeWidgetTree();
	void RefreshDisplayedValues() const;
	void PopulateComboBox(UComboBoxString* ComboBox, const TArray<FString>& Options, const FString& SelectedOption) const;
};
