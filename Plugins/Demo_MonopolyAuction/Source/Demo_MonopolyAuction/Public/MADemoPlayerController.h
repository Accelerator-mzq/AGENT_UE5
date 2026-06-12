// Copyright Phase14 demo agent.
// 玩家控制器:仅转发玩家意图到 GameMode,不持有任何规则。施工规范 §3:UI/Controller 只发意图。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "MADemoPlayerController.generated.h"

class AMADemoGameMode;

// 热座本地多人下唯一的本地控制器,把按钮意图(掷骰/购买/拍卖出价)转发给 GameMode。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API AMADemoPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	// 意图:请求掷骰并结算当前玩家这一步。
	UFUNCTION(BlueprintCallable, Category = "Intent")
	void IntentRollDice();

	// 意图:结束当前玩家回合,推进到下一玩家。
	UFUNCTION(BlueprintCallable, Category = "Intent")
	void IntentEndTurn();

protected:
	// 取当前 GameMode(仅服务器/单机本地存在)。
	AMADemoGameMode* GetDemoGameMode() const;
};
