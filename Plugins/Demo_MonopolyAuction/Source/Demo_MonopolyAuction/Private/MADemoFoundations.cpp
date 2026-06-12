// Copyright Phase14 demo agent.
#include "MADemoFoundations.h"
#include "InputCoreTypes.h"
#include "Kismet/KismetSystemLibrary.h"

// ── 输入底座 ──────────────────────────────────────────────
void UMADemoInputFoundation::InitializeDefaultBindings()
{
	// provisional 默认键位:确认=Enter 取消=Esc 暂停=Esc 掷骰=Space
	DefaultBindings.Empty();
	DefaultBindings.Add(EMADemoInputAction::MenuConfirm, EKeys::Enter);
	DefaultBindings.Add(EMADemoInputAction::MenuCancel, EKeys::Escape);
	DefaultBindings.Add(EMADemoInputAction::PauseInput, EKeys::Escape);
	DefaultBindings.Add(EMADemoInputAction::RollDice, EKeys::SpaceBar);
}

FKey UMADemoInputFoundation::GetBinding(EMADemoInputAction Action) const
{
	if (const FKey* Found = DefaultBindings.Find(Action))
	{
		return *Found;
	}
	return EKeys::Invalid;
}

// ── 音频底座 ──────────────────────────────────────────────
void UMADemoAudioFoundation::SetBGMVolume(float Volume)
{
	BGMVolume = FMath::Clamp(Volume, 0.0f, 1.0f);
}

void UMADemoAudioFoundation::SetSFXVolume(float Volume)
{
	SFXVolume = FMath::Clamp(Volume, 0.0f, 1.0f);
}

void UMADemoAudioFoundation::PlayBasicSFX(const FString& SFXTag)
{
	// demo 级:仅记录最近播放标签,真实播放交蓝图绑定 USoundBase
	LastPlayedSFXTag = SFXTag;
}

// ── 平台底座 ──────────────────────────────────────────────
void UMADemoPlatformFoundation::ApplyDisplaySettings(int32 InWindowMode, int32 InResolutionX, int32 InResolutionY)
{
	// session_only:仅更新运行期态,不写入配置文件
	WindowMode = FMath::Clamp(InWindowMode, 0, 2);
	ResolutionX = FMath::Max(640, InResolutionX);
	ResolutionY = FMath::Max(480, InResolutionY);
}

void UMADemoPlatformFoundation::RequestQuit(UObject* WorldContextObject)
{
	// 退出处理能力位:走标准退出请求
	if (WorldContextObject)
	{
		UKismetSystemLibrary::QuitGame(WorldContextObject, nullptr,
			EQuitPreference::Quit, false);
	}
}
