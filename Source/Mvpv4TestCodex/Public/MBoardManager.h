#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MBoardManager.generated.h"

class AMTile;
struct FMTileData;

UCLASS()
class MVPV4TESTCODEX_API AMBoardManager : public AActor
{
	GENERATED_BODY()

public:
	AMBoardManager();

	// 棋盘上生成出的 TileActor 列表。
	UPROPERTY(BlueprintReadOnly, Category = "Monopoly")
	TArray<TObjectPtr<AMTile>> TileActors;

	// 正方形棋盘外接边长。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	float SideLength = 2800.0f;

	// Tile 在地面上的高度偏移。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	float TileHeight = 30.0f;

	// 可替换的 Tile 类型，便于后续换成蓝图壳。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TSubclassOf<AMTile> TileActorClass;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SpawnBoard(const TArray<FMTileData>& TileDataArray);

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	FVector CalculateTileWorldLocation(int32 TileIndex) const;

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	AMTile* GetTileActor(int32 TileIndex) const;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void HighlightTile(int32 TileIndex, bool bHighlight);

	UFUNCTION(BlueprintPure, Category = "Monopoly")
	FVector GetPlayerStandLocation(int32 TileIndex, int32 PlayerIndex) const;

private:
	void ClearBoard();
};
