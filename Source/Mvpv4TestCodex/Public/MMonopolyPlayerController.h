#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "MMonopolyPlayerController.generated.h"

UCLASS()
class MVPV4TESTCODEX_API AMMonopolyPlayerController : public APlayerController
{
	GENERATED_BODY()

public:
	AMMonopolyPlayerController();

	virtual void BeginPlay() override;

	// 当前局是否允许响应本地输入。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	bool bInputEnabledForTurn = true;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetTurnInputEnabled(bool bEnabled);
};
