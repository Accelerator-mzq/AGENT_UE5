#include "MMonopolyPlayerController.h"

AMMonopolyPlayerController::AMMonopolyPlayerController()
{
	bShowMouseCursor = true;
	bEnableClickEvents = true;
	bEnableMouseOverEvents = true;
	DefaultMouseCursor = EMouseCursor::Default;
}

void AMMonopolyPlayerController::BeginPlay()
{
	Super::BeginPlay();

	// 输入模式由 GameMode 在 HUD 或弹窗创建后统一设置，这里只确保鼠标事件开关处于启用状态。
	bShowMouseCursor = true;
	bEnableClickEvents = true;
	bEnableMouseOverEvents = true;

	UE_LOG(LogTemp, Log, TEXT("[Phase8] PlayerController BeginPlay. Class=%s Click=%s Hover=%s Cursor=%s"),
		*GetClass()->GetName(),
		bEnableClickEvents ? TEXT("true") : TEXT("false"),
		bEnableMouseOverEvents ? TEXT("true") : TEXT("false"),
		bShowMouseCursor ? TEXT("true") : TEXT("false"));
}

void AMMonopolyPlayerController::SetTurnInputEnabled(const bool bEnabled)
{
	bInputEnabledForTurn = bEnabled;
	SetIgnoreMoveInput(!bEnabled);
	SetIgnoreLookInput(!bEnabled);
}
