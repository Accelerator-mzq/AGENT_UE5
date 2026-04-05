#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MPlayerPawn.generated.h"

class UStaticMeshComponent;
class UTextRenderComponent;

UCLASS()
class MVPV4TESTCODEX_API AMPlayerPawn : public AActor
{
	GENERATED_BODY()

public:
	AMPlayerPawn();

	// 棋子根节点。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<USceneComponent> SceneRoot;

	// 用基础球体表示玩家棋子。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UStaticMeshComponent> PawnMesh;

	// 显示玩家名字缩写。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextRenderComponent> PawnLabel;

	// 对应 MonopolyPlayers 数组中的玩家索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 PlayerIndex = INDEX_NONE;

	// 当前所在格子索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 CurrentTileIndex = 0;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void MoveToTile(const FVector& WorldLocation, int32 NewTileIndex);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetPawnColor(const FLinearColor& InColor);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetLabelText(const FString& InLabel);
};
