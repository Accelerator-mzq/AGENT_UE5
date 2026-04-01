// Copyright Epic Games, Inc. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "Engine/StaticMeshActor.h"
#include "BoardgamePrototypeBoardActor.generated.h"

class UTextRenderComponent;
class UStaticMeshComponent;

UCLASS()
class MVPV4TESTCODEX_API ABoardgamePrototypeBoardActor : public AStaticMeshActor
{
	GENERATED_BODY()

public:
	ABoardgamePrototypeBoardActor();

	virtual void BeginPlay() override;
	virtual void NotifyActorOnClicked(FKey ButtonPressed = EKeys::LeftMouseButton) override;

	UFUNCTION(BlueprintCallable, Category = "AgentBridge|Runtime")
	bool LoadRuntimeConfigFromFile(const FString& RuntimeConfigPath);

	UFUNCTION(BlueprintCallable, Category = "AgentBridge|Runtime")
	bool ApplyMoveByCell(int32 Row, int32 Col);

	UFUNCTION(BlueprintCallable, Category = "AgentBridge|Runtime")
	bool ApplyMoveByWorldLocation(const FVector& WorldLocation);

	UFUNCTION(BlueprintCallable, Category = "AgentBridge|Runtime")
	FString GetBoardRuntimeState() const;

	UFUNCTION(BlueprintCallable, Category = "AgentBridge|Runtime")
	void ResetBoard();

protected:
	bool TryResolveCellFromWorldLocation(const FVector& WorldLocation, int32& OutRow, int32& OutCol) const;
	bool DetectWin(FString& OutWinner) const;
	bool DetectDraw() const;
	bool SpawnPieceActor(int32 Row, int32 Col, const FString& PieceSymbol);
	void UpdateStatusText();
	void ClearSpawnedPieces();
	FVector GetCellWorldLocation(int32 Row, int32 Col) const;
	FString MakePieceActorName(const FString& PieceSymbol) const;
	bool LoadConfigJson(const FString& RuntimeConfigPath, TSharedPtr<FJsonObject>& OutJson) const;
	void ApplyBoardVisualStyle();
	void ApplyPieceVisualStyle(UStaticMeshComponent* MeshComponent, const FString& PieceSymbol);

protected:
	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	UTextRenderComponent* StatusTextComponent;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	FString LoadedRuntimeConfigPath;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	FString CurrentPlayer;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	FString ResultState;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	int32 Rows;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	int32 Cols;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	float CellSizeX;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	float CellSizeY;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	FVector BoardOrigin;

	UPROPERTY(VisibleAnywhere, Category = "AgentBridge|Runtime")
	int32 MoveCounter;

	TArray<FString> BoardCells;
	TArray<TWeakObjectPtr<AActor>> SpawnedPieces;
	TMap<FString, FVector> PieceScaleMap;
	TMap<FString, FString> PieceMeshPathMap;
};
