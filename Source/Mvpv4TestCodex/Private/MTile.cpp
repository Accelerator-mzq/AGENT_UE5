#include "MTile.h"

#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "UObject/ConstructorHelpers.h"

AMTile::AMTile()
{
	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	SetRootComponent(SceneRoot);

	TileMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("TileMesh"));
	TileMesh->SetupAttachment(SceneRoot);
	TileMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	TileMesh->SetRelativeScale3D(FVector(1.6f, 1.6f, 0.25f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		TileMesh->SetStaticMesh(CubeMesh.Object);
	}

	TileLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("TileLabel"));
	TileLabel->SetupAttachment(SceneRoot);
	TileLabel->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
	TileLabel->SetVerticalAlignment(EVerticalTextAligment::EVRTA_TextCenter);
	TileLabel->SetWorldSize(44.0f);
	TileLabel->SetRelativeLocation(FVector(0.0f, 0.0f, 55.0f));
	TileLabel->SetRelativeRotation(FRotator(90.0f, 0.0f, 0.0f));

	PrimaryActorTick.bCanEverTick = false;
}

void AMTile::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	TileLabel->SetText(FText::FromString(FString::Printf(TEXT("%d\n%s"), TileData.TileIndex, *TileData.TileName)));
	TileLabel->SetTextRenderColor(ResolveLabelColor());
}

void AMTile::InitTile(const FMTileData& InTileData)
{
	TileData = InTileData;
	TileIndex = InTileData.TileIndex;
	TileLabel->SetText(FText::FromString(FString::Printf(TEXT("%d\n%s"), TileData.TileIndex, *TileData.TileName)));
	TileLabel->SetTextRenderColor(ResolveLabelColor());
}

void AMTile::SetOwnerColor(const FLinearColor& InOwnerColor)
{
	TileMesh->SetVectorParameterValueOnMaterials(TEXT("Color"), FVector(InOwnerColor));
	TileLabel->SetTextRenderColor(InOwnerColor.ToFColor(true));
}

void AMTile::SetHighlight(const bool bEnabled)
{
	const float ScaleZ = bEnabled ? 0.4f : 0.25f;
	TileMesh->SetRelativeScale3D(FVector(1.6f, 1.6f, ScaleZ));
}

FColor AMTile::ResolveLabelColor() const
{
	switch (TileData.ColorGroup)
	{
	case EMColorGroup::Brown:
		return FColor(150, 96, 64);
	case EMColorGroup::LightBlue:
		return FColor(96, 190, 255);
	case EMColorGroup::Pink:
		return FColor(255, 96, 192);
	case EMColorGroup::Orange:
		return FColor(255, 160, 64);
	case EMColorGroup::Red:
		return FColor(220, 64, 64);
	case EMColorGroup::Green:
		return FColor(80, 180, 96);
	case EMColorGroup::Blue:
		return FColor(64, 96, 220);
	default:
		return FColor::White;
	}
}
