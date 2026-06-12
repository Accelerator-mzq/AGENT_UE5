// Copyright Phase14 v0 attempt2. 三大底座:输入/音频/平台。
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MADemoTypes.h"
#include "MADemoFoundations.generated.h"

// 输入底座:4 个意图动作的默认键位映射(menu_confirm/menu_cancel/pause_input/roll_dice_action)。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoInputFoundation : public UObject
{
	GENERATED_BODY()
public:
	UMADemoInputFoundation();

	// 意图动作 → 默认键名(provisional 默认键位)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Input")
	TMap<EMADemoInputAction, FString> DefaultBindings;

	// 取某动作默认键。
	FString GetKeyForAction(EMADemoInputAction Action) const;
};

// 音频底座:主音量 + SFX 音量 + 基础 SFX 播放接口(presence_only)。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoAudioFoundation : public UObject
{
	GENERATED_BODY()
public:
	// 主音量(0-1)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Audio")
	float MasterVolume = 1.0f;

	// SFX 音量(0-1)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Audio")
	float SFXVolume = 1.0f;

	// 设主音量(夹取 0-1)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Audio")
	void SetMasterVolume(float V);

	// 设 SFX 音量(夹取 0-1)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Audio")
	void SetSFXVolume(float V);

	// 播放一个基础音效(v0 仅接口占位,不阻塞玩法)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Audio")
	void PlayBasicSFX(const FString& SfxId);
};

// 平台底座:窗口模式 / 分辨率 / 退出处理(clarification_gated,session_only 持久化)。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoPlatformFoundation : public UObject
{
	GENERATED_BODY()
public:
	// 窗口模式("Windowed"/"Fullscreen")。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Platform")
	FString WindowMode = TEXT("Windowed");

	// 分辨率宽。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Platform")
	int32 ResolutionWidth = 1280;

	// 分辨率高。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Platform")
	int32 ResolutionHeight = 720;

	// 设窗口模式。
	UFUNCTION(BlueprintCallable, Category = "Demo|Platform")
	void SetWindowMode(const FString& Mode);

	// 设分辨率。
	UFUNCTION(BlueprintCallable, Category = "Demo|Platform")
	void SetResolution(int32 W, int32 H);

	// 退出处理(请求退出)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Platform")
	void RequestQuit();
};
