// Copyright Phase14 v0 attempt2. 三大底座实现。
#include "MADemoFoundations.h"
#include "HAL/PlatformMisc.h"

// 输入底座:填默认键位(provisional)。
UMADemoInputFoundation::UMADemoInputFoundation()
{
	DefaultBindings.Add(EMADemoInputAction::MenuConfirm, TEXT("Enter"));
	DefaultBindings.Add(EMADemoInputAction::MenuCancel, TEXT("Escape"));
	DefaultBindings.Add(EMADemoInputAction::Pause, TEXT("Escape"));
	DefaultBindings.Add(EMADemoInputAction::RollDice, TEXT("SpaceBar"));
}

FString UMADemoInputFoundation::GetKeyForAction(EMADemoInputAction Action) const
{
	const FString* Found = DefaultBindings.Find(Action);
	return Found ? *Found : FString();
}

// 音频底座。
void UMADemoAudioFoundation::SetMasterVolume(float V)
{
	MasterVolume = FMath::Clamp(V, 0.f, 1.f);
}

void UMADemoAudioFoundation::SetSFXVolume(float V)
{
	SFXVolume = FMath::Clamp(V, 0.f, 1.f);
}

void UMADemoAudioFoundation::PlayBasicSFX(const FString& SfxId)
{
	// v0 占位:仅记录,不引入音频资产(presence_only)。
	UE_LOG(LogTemp, Verbose, TEXT("[Demo_MonopolyAuction] PlayBasicSFX: %s (vol=%.2f)"), *SfxId, SFXVolume);
}

// 平台底座。
void UMADemoPlatformFoundation::SetWindowMode(const FString& Mode)
{
	WindowMode = Mode;
}

void UMADemoPlatformFoundation::SetResolution(int32 W, int32 H)
{
	ResolutionWidth = FMath::Max(1, W);
	ResolutionHeight = FMath::Max(1, H);
}

void UMADemoPlatformFoundation::RequestQuit()
{
	FPlatformMisc::RequestExit(false);
}
