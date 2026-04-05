#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "MMonopolyTypes.h"
#include "MMonopolyGameState.generated.h"

class AMMonopolyPlayerState;

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMOnTurnNumberChanged, int32, NewTurnNumber);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMOnActivePlayerChanged, int32, NewPlayerIndex, AMMonopolyPlayerState*, NewPlayerState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMOnMoneyChanged, AMMonopolyPlayerState*, PlayerState, int32, NewMoney);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMOnPawnMoved, AMMonopolyPlayerState*, PlayerState, int32, NewTileIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMOnTurnStateChanged, EMTurnState, NewTurnState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMOnPropertyPurchased, AMMonopolyPlayerState*, PlayerState, int32, TileIndex);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FMOnRentPaid, AMMonopolyPlayerState*, Payer, AMMonopolyPlayerState*, Receiver, int32, Amount);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(FMOnPlayerJailed, AMMonopolyPlayerState*, PlayerState, int32, RemainingTurns);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMOnPlayerBankrupt, AMMonopolyPlayerState*, PlayerState);
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FMOnGameOver, AMMonopolyPlayerState*, Winner);

UCLASS()
class MVPV4TESTCODEX_API AMMonopolyGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	AMMonopolyGameState();

	// 28 个格子的核心数据表。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TArray<FMTileData> TileDataArray;

	// 当前参与游戏的玩家状态列表。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TArray<TObjectPtr<AMMonopolyPlayerState>> MonopolyPlayers;

	// 当前回合编号，从 1 开始计数。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 TurnNumber = 1;

	// 当前行动玩家在 MonopolyPlayers 中的索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 CurrentPlayerIndex = 0;

	// 当前玩家连续掷出双骰的次数。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 ConsecutiveDoublesCount = 0;

	// 当前游戏阶段。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	EMGamePhase GamePhase = EMGamePhase::Setup;

	// 当前轮转状态机状态。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	EMTurnState TurnState = EMTurnState::None;

	// 当前仍未破产的玩家数。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 ActivePlayerCount = 0;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnTurnNumberChanged OnTurnNumberChanged;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnActivePlayerChanged OnActivePlayerChanged;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnMoneyChanged OnMoneyChanged;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnPawnMoved OnPawnMoved;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnTurnStateChanged OnTurnStateChanged;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnPropertyPurchased OnPropertyPurchased;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnRentPaid OnRentPaid;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnPlayerJailed OnPlayerJailed;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnPlayerBankrupt OnPlayerBankrupt;

	UPROPERTY(BlueprintAssignable, Category = "Monopoly|Events")
	FMOnGameOver OnGameOver;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void InitializeTileData();

	const FMTileData* GetTileData(int32 TileIndex) const;

	FMTileData* GetMutableTileData(int32 TileIndex);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	bool SetTileOwner(int32 TileIndex, int32 OwnerPlayerIndex);

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	bool DoesPlayerOwnFullColorGroup(int32 PlayerIndex, EMColorGroup ColorGroup) const;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void RegisterMonopolyPlayer(AMMonopolyPlayerState* PlayerState);

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	AMMonopolyPlayerState* GetMonopolyPlayer(int32 PlayerIndex) const;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetCurrentPlayerIndex(int32 NewPlayerIndex);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetTurnNumber(int32 NewTurnNumber);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetTurnState(EMTurnState NewTurnState);
};
