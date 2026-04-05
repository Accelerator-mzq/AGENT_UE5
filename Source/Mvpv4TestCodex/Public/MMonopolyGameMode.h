#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MMonopolyTypes.h"
#include "MMonopolyGameMode.generated.h"

class AMBoardManager;
class ACameraActor;
class AMDice;
class AMMonopolyGameState;
class AMMonopolyPlayerState;
class AMPlayerPawn;
class UMGameHUDWidget;
class UMPopupWidget;

UCLASS()
class MVPV4TESTCODEX_API AMMonopolyGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMMonopolyGameMode();

	virtual void BeginPlay() override;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 DefaultPlayerCount = 2;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 PassStartReward = 200;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 BailAmount = 50;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TSubclassOf<AMBoardManager> BoardManagerClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TSubclassOf<AMPlayerPawn> PlayerPawnClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TSubclassOf<AMDice> DiceClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TSubclassOf<UMGameHUDWidget> HUDWidgetClass;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TSubclassOf<UMPopupWidget> PopupWidgetClass;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void OnPlayerRequestRoll();

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void RequestEndTurnFromUI();

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void RequestPayBailFromUI();

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	AMMonopolyGameState* GetMonopolyGameState() const;

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	AMMonopolyPlayerState* GetMonopolyPlayerState(int32 PlayerIndex) const;

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	AMPlayerPawn* GetCurrentPlayerPawn() const;

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	FLinearColor GetPlayerColor(int32 PlayerIndex) const;

private:
	UPROPERTY()
	TObjectPtr<AMBoardManager> BoardManager;

	UPROPERTY()
	TObjectPtr<AMDice> DiceActor;

	UPROPERTY()
	TObjectPtr<ACameraActor> BoardCameraActor;

	UPROPERTY()
	TArray<TObjectPtr<AMPlayerPawn>> PlayerPawns;

	UPROPERTY()
	TObjectPtr<UMGameHUDWidget> ActiveHUDWidget;

	UPROPERTY()
	TObjectPtr<UMPopupWidget> ActivePopupWidget;

	UPROPERTY()
	FMDiceResult LastDiceResult;

	UPROPERTY()
	bool bPendingExtraTurn = false;

	void EnsureRuntimeActors();
	void InitializeMonopolyPlayers(int32 PlayerCount);
	void SpawnPlayerPawns();
	void MovePlayerPawnToTile(int32 PlayerIndex, int32 TileIndex);
	void RefreshTileOwnershipVisuals();
	void CreateHUDWidget();
	void StartTurn();
	void SetTurnState(EMTurnState NewTurnState);
	void RollAndMoveCurrentPlayer();
	void HandleJailTurn();
	void ResolveCurrentTileEvent();
	void ResolvePropertyTile(AMMonopolyPlayerState* CurrentPlayerState, int32 CurrentPlayerIndex, const FMTileData& TileData);
	void ResolveChanceTile(AMMonopolyPlayerState* CurrentPlayerState);
	void ResolveCommunityChestTile(AMMonopolyPlayerState* CurrentPlayerState);
	void ResolveTaxTile(AMMonopolyPlayerState* CurrentPlayerState, const FMTileData& TileData);
	void ProcessPostEvent();
	void EndTurn();
	int32 FindNextNonBankruptPlayer(int32 StartIndex) const;
	bool TryPurchaseProperty(int32 PlayerIndex, int32 TileIndex);
	void CollectRent(int32 PayerIndex, int32 ReceiverIndex, int32 TileIndex);
	int32 CalculateEffectiveRent(const FMTileData& TileData) const;
	bool TransferMoney(AMMonopolyPlayerState* FromPlayer, AMMonopolyPlayerState* ToPlayer, int32 Amount);
	bool DeductMoney(AMMonopolyPlayerState* PlayerState, int32 Amount);
	void SendToJail(int32 PlayerIndex);
	void PayBail(int32 PlayerIndex, bool bContinueWithRoll);
	void ForcePayBail(int32 PlayerIndex);
	void TriggerBankruptcy(int32 PlayerIndex, const FString& Reason);
	void ReleaseAllProperties(AMMonopolyPlayerState* PlayerState);
	void CheckGameEndCondition();
	void DeclareWinner(AMMonopolyPlayerState* Winner);
	void ShowPopup(const FString& Title, const FString& Message, const TArray<FString>& ButtonLabels, TFunction<void(int32)> Callback);
	void CloseActivePopup();
};
