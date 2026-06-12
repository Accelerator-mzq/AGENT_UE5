// Copyright Phase14 demo agent.
#include "MADemoPlayerController.h"
#include "MADemoGameMode.h"
#include "Engine/World.h"
#include "GameFramework/GameModeBase.h"

AMADemoGameMode* AMADemoPlayerController::GetDemoGameMode() const
{
	if (UWorld* World = GetWorld())
	{
		return World->GetAuthGameMode<AMADemoGameMode>();
	}
	return nullptr;
}

void AMADemoPlayerController::IntentRollDice()
{
	// 只转发意图,规则裁决在 GameMode
	if (AMADemoGameMode* GM = GetDemoGameMode())
	{
		GM->RequestRollAndResolve();
	}
}

void AMADemoPlayerController::IntentEndTurn()
{
	if (AMADemoGameMode* GM = GetDemoGameMode())
	{
		GM->AdvanceToNextPlayer();
		GM->StartTurn();
	}
}
