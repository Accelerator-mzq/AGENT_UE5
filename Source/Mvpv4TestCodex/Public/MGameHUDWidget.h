#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MMonopolyTypes.h"
#include "MGameHUDWidget.generated.h"

class AMMonopolyGameMode;
class AMMonopolyGameState;
class AMMonopolyPlayerState;
class UButton;
class UTextBlock;

UCLASS()
class MVPV4TESTCODEX_API UMGameHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void BindToGame(AMMonopolyGameMode* InGameMode, AMMonopolyGameState* InGameState);

	// 当前轮到的玩家文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> CurrentPlayerText;

	// 当前回合数文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> TurnNumberText;

	// 所有玩家资金汇总文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> MoneySummaryText;

	// 当前格子提示文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> TileInfoText;

	// 系统状态文本。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextBlock> StatusText;

private:
	UPROPERTY()
	TObjectPtr<UButton> RollButton;

	UPROPERTY()
	TObjectPtr<UButton> EndTurnButton;

	UPROPERTY()
	TObjectPtr<UButton> PayBailButton;

	UPROPERTY()
	TObjectPtr<AMMonopolyGameMode> CachedGameMode;

	UPROPERTY()
	TObjectPtr<AMMonopolyGameState> CachedGameState;

	UFUNCTION()
	void HandleRollClicked();

	UFUNCTION()
	void HandleEndTurnClicked();

	UFUNCTION()
	void HandlePayBailClicked();

	UFUNCTION()
	void HandleTurnNumberChanged(int32 NewTurnNumber);

	UFUNCTION()
	void HandleActivePlayerChanged(int32 NewPlayerIndex, AMMonopolyPlayerState* NewPlayerState);

	UFUNCTION()
	void HandleMoneyChanged(AMMonopolyPlayerState* PlayerState, int32 NewMoney);

	UFUNCTION()
	void HandlePawnMoved(AMMonopolyPlayerState* PlayerState, int32 NewTileIndex);

	UFUNCTION()
	void HandleTurnStateChanged(EMTurnState NewTurnState);

	// 在 Slate 可见树重建前准备好 WidgetTree，避免 NativeConstruct 创建过晚导致界面空白。
	void BuildRuntimeWidgetTree();

	void RefreshAllText() const;
	FString BuildMoneySummary() const;
};
