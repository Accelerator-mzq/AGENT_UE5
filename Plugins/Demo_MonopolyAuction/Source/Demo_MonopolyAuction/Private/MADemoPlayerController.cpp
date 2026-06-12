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
		// 暂停时掷骰意图被拒(GameMode 内亦有守卫,双保险)。
		if (GM->IsPaused())
		{
			return;
		}
		// 掷骰并结算;结算完停 TurnEnd 等 Enter(回合节奏归玩家,试玩反馈修复轮)。
		GM->RequestRollAndResolve();
	}
}

void AMADemoPlayerController::IntentEndTurn()
{
	if (AMADemoGameMode* GM = GetWorld() ? GetWorld()->GetAuthGameMode<AMADemoGameMode>() : nullptr)
	{
		// 暂停时结束回合意图被拒。
		if (GM->IsPaused())
		{
			return;
		}
		AMADemoGameState* GS = GM->GetDemoGameState();
		if (GS && GS->TurnPhase == EMADemoTurnPhase::TurnEnd)
		{
			GM->AdvanceToNextPlayer();
		}
	}
}

void AMADemoPlayerController::IntentPause()
{
	// Esc 切换暂停态:暂停面板由 Canvas HUD 按 GameState.bPaused 渲染;再按 Esc 恢复。
	if (AMADemoGameMode* GM = GetWorld() ? GetWorld()->GetAuthGameMode<AMADemoGameMode>() : nullptr)
	{
		GM->TogglePauseState();
		UE_LOG(LogTemp, Log, TEXT("[Demo_MonopolyAuction] 暂停切换(Esc)→ %s"),
			GM->IsPaused() ? TEXT("已暂停") : TEXT("已恢复"));
	}
}
