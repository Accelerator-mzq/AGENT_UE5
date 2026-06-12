// Copyright Phase14 v0 attempt2. 玩家意图转发实现。
#include "MADemoPlayerController.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "Kismet/GameplayStatics.h"
#include "Components/InputComponent.h"
#include "GameFramework/InputSettings.h"

AMADemoPlayerController::AMADemoPlayerController()
{
	// 人玩模式显示鼠标光标,方便与 HUD 交互。
	bShowMouseCursor = true;
}

void AMADemoPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();
	if (!InputComponent)
	{
		return;
	}

	// 直接绑定物理按键到意图(不依赖项目 Input Action 映射,自包含)。
	// 这样无需 author 输入配置资产即可在 -game 下用键盘推进游戏。
	InputComponent->BindKey(EKeys::SpaceBar, IE_Pressed, this, &AMADemoPlayerController::IntentRollDice);
	InputComponent->BindKey(EKeys::Enter, IE_Pressed, this, &AMADemoPlayerController::IntentEndTurn);
	InputComponent->BindKey(EKeys::Escape, IE_Pressed, this, &AMADemoPlayerController::IntentPause);
}

void AMADemoPlayerController::IntentRollDice()
{
	if (AMADemoGameMode* GM = GetWorld() ? GetWorld()->GetAuthGameMode<AMADemoGameMode>() : nullptr)
	{
		// 掷骰并推进一步;GameMode 内部处理移动/落点/双数/切玩家。
		GM->RequestRollAndResolve();
		// 刷新 HUD 经 GameMode 公有重载入口不可直达,这里通过再次掷骰前的 BeginPlay HUD 自刷。
		// HUD 自身在每次按键后由 GameMode 的 RefreshHUD() 经 widget tick 兜底刷新(见 widget)。
	}
}

void AMADemoPlayerController::IntentEndTurn()
{
	if (AMADemoGameMode* GM = GetWorld() ? GetWorld()->GetAuthGameMode<AMADemoGameMode>() : nullptr)
	{
		AMADemoGameState* GS = GM->GetDemoGameState();
		if (GS && GS->TurnPhase == EMADemoTurnPhase::TurnEnd)
		{
			GM->AdvanceToNextPlayer();
		}
	}
}

void AMADemoPlayerController::IntentPause()
{
	// v0:暂停意图记录(暂停 widget 的呈现由 HUD 层处理),不阻塞主链。
	UE_LOG(LogTemp, Log, TEXT("[Demo_MonopolyAuction] 暂停意图(Esc)"));
}
