#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerState.h"
#include "MMonopolyPlayerState.generated.h"

UCLASS()
class MVPV4TESTCODEX_API AMMonopolyPlayerState : public APlayerState
{
	GENERATED_BODY()

public:
	AMMonopolyPlayerState();

	// 玩家当前现金。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 Money = 1500;

	// 玩家当前所在格子索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 CurrentTileIndex = 0;

	// 玩家拥有的地产格索引列表。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TArray<int32> OwnedTileIndices;

	// 玩家是否处于监狱状态。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	bool bIsInJail = false;

	// 玩家剩余的监狱掷骰尝试次数。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 JailTurnsRemaining = 0;

	// 玩家是否已经破产。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	bool bIsBankrupt = false;

	// 玩家棋子的显示颜色。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	FLinearColor PlayerColor = FLinearColor::Red;

	// UI 展示名，默认回退到 PlayerState 自带名字。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	FString PlayerDisplayName;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void AddMoney(int32 Amount);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	bool DeductMoney(int32 Amount);

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	bool CanAfford(int32 Amount) const;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void AddProperty(int32 TileIndex);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void RemoveProperty(int32 TileIndex);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void RemoveAllProperties();

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	FString GetResolvedDisplayName() const;
};
