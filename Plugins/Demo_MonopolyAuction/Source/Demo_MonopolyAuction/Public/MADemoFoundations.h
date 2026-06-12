// Copyright Phase14 demo agent.
// 基础底座(presence_only baselines):输入/音频/平台。
// 各自提供必备能力位的数据与意图接口,不绑定具体引擎子系统实现(demo 级)。
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MADemoFoundations.generated.h"

// 输入动作枚举(baseline-input-foundation 必备:菜单确认/取消/暂停/掷骰)。
UENUM(BlueprintType)
enum class EMADemoInputAction : uint8
{
	MenuConfirm   UMETA(DisplayName = "菜单确认"),
	MenuCancel    UMETA(DisplayName = "菜单取消"),
	PauseInput    UMETA(DisplayName = "暂停"),
	RollDice      UMETA(DisplayName = "掷骰")
};

// 输入底座:登记 4 个必备动作的默认按键映射(presence_only:声明能力位)。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoInputFoundation : public UObject
{
	GENERATED_BODY()

public:
	// 动作 → 默认按键名映射(provisional 默认值,可在设置/数据覆盖)。
	UPROPERTY(BlueprintReadOnly, Category = "Input")
	TMap<EMADemoInputAction, FKey> DefaultBindings;

	// 用 provisional 默认按键填充映射(Enter/Esc/Esc/Space)。
	UFUNCTION(BlueprintCallable, Category = "Input")
	void InitializeDefaultBindings();

	// 查询某动作的绑定键。
	UFUNCTION(BlueprintCallable, Category = "Input")
	FKey GetBinding(EMADemoInputAction Action) const;
};

// 音频底座:音量控制 + 基础 SFX 播放能力位(baseline-audio-foundation)。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoAudioFoundation : public UObject
{
	GENERATED_BODY()

public:
	// BGM 音量 0..1
	UPROPERTY(BlueprintReadOnly, Category = "Audio")
	float BGMVolume = 1.0f;

	// SFX 音量 0..1
	UPROPERTY(BlueprintReadOnly, Category = "Audio")
	float SFXVolume = 1.0f;

	// 设置 BGM 音量(clamp 0..1)。
	UFUNCTION(BlueprintCallable, Category = "Audio")
	void SetBGMVolume(float Volume);

	// 设置 SFX 音量(clamp 0..1)。
	UFUNCTION(BlueprintCallable, Category = "Audio")
	void SetSFXVolume(float Volume);

	// 播放一个基础 SFX(demo 级:仅记录最近播放标签,真实播放交蓝图/Sound 资产)。
	UFUNCTION(BlueprintCallable, Category = "Audio")
	void PlayBasicSFX(const FString& SFXTag);

	// 最近播放的 SFX 标签(冒烟断言用)
	UPROPERTY(BlueprintReadOnly, Category = "Audio")
	FString LastPlayedSFXTag;
};

// 平台底座:窗口模式/分辨率/退出处理(baseline-platform-foundation,clarification_gated)。
// provisional:持久化策略 session_only;退出走 RequestExit。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoPlatformFoundation : public UObject
{
	GENERATED_BODY()

public:
	// 当前窗口模式(0=全屏 1=窗口 2=无边框)
	UPROPERTY(BlueprintReadOnly, Category = "Platform")
	int32 WindowMode = 1;

	// 当前分辨率宽
	UPROPERTY(BlueprintReadOnly, Category = "Platform")
	int32 ResolutionX = 1280;

	// 当前分辨率高
	UPROPERTY(BlueprintReadOnly, Category = "Platform")
	int32 ResolutionY = 720;

	// 应用窗口/分辨率(session_only)。
	UFUNCTION(BlueprintCallable, Category = "Platform")
	void ApplyDisplaySettings(int32 InWindowMode, int32 InResolutionX, int32 InResolutionY);

	// 请求退出游戏(退出处理能力位)。
	UFUNCTION(BlueprintCallable, Category = "Platform")
	void RequestQuit(UObject* WorldContextObject);
};
