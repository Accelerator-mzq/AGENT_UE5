#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MMonopolyTypes.h"
#include "MTile.generated.h"

class UStaticMeshComponent;
class UTextRenderComponent;

UCLASS()
class MVPV4TESTCODEX_API AMTile : public AActor
{
	GENERATED_BODY()

public:
	AMTile();

	virtual void OnConstruction(const FTransform& Transform) override;

	// 格子的可视根节点。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<USceneComponent> SceneRoot;

	// 使用基础几何体充当 Phase 8 的占位格子。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UStaticMeshComponent> TileMesh;

	// 使用文本组件展示格子名字和索引。
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Monopoly")
	TObjectPtr<UTextRenderComponent> TileLabel;

	// 当前格子的索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	int32 TileIndex = INDEX_NONE;

	// 当前格子的逻辑数据快照。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Monopoly")
	FMTileData TileData;

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void InitTile(const FMTileData& InTileData);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetOwnerColor(const FLinearColor& InOwnerColor);

	UFUNCTION(BlueprintCallable, Category = "Monopoly")
	void SetHighlight(bool bEnabled);

private:
	FColor ResolveLabelColor() const;
};
