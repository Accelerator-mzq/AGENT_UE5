// Copyright Phase14 v0 attempt2. 玩家意图转发(键盘输入)。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "MADemoPlayerController.generated.h"

// 玩家控制器:把键盘意图转发给 GameMode,不持有规则。
// 键位(provisional):Space=掷骰并推进、Enter=确认/结束回合、Esc=暂停。
UCLASS()
class DEMO_MONOPOLYAUCTION_API AMADemoPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AMADemoPlayerController();

protected:
	virtual void SetupInputComponent() override;

	// 掷骰意图(Space):转发 RequestRollAndResolve。
	UFUNCTION()
	void IntentRollDice();

	// 结束回合/确认意图(Enter):若处于回合结束态则切玩家。
	UFUNCTION()
	void IntentEndTurn();

	// 暂停意图(Esc):切换暂停态(v0 仅日志 + 暂停 widget 呈现)。
	UFUNCTION()
	void IntentPause();
};
