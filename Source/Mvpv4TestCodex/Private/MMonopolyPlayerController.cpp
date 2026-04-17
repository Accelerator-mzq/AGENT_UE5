#include "MMonopolyPlayerController.h"

#include "MMonopolyGameMode.h"

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

void AMMonopolyPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	if (InputComponent != nullptr)
	{
		// 用最小绑定补 Pause 入口，避免引入额外的输入资产依赖。
		InputComponent->BindKey(EKeys::Escape, IE_Pressed, this, &AMMonopolyPlayerController::HandlePausePressed);
	}
}

void AMMonopolyPlayerController::SetTurnInputEnabled(const bool bEnabled)
{
	bInputEnabledForTurn = bEnabled;
	SetIgnoreMoveInput(!bEnabled);
	SetIgnoreLookInput(!bEnabled);
}

void AMMonopolyPlayerController::HandlePausePressed()
{
	if (AMMonopolyGameMode* MonopolyGameMode = GetWorld() != nullptr ? GetWorld()->GetAuthGameMode<AMMonopolyGameMode>() : nullptr)
	{
		MonopolyGameMode->TogglePauseMenuFromInput();
	}
}
