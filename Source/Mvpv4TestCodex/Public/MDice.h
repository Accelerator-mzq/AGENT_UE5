#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MMonopolyTypes.h"
#include "MDice.generated.h"

class UStaticMeshComponent;

UCLASS()
class MVPV4TESTCODEX_API AMDice : public AActor
{
	GENERATED_BODY()

public:
	AMDice();

	// 骰子占位模型。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UStaticMeshComponent> DiceMesh;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	FMDiceResult RollDice();

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void PlayRollAnimation();
};
