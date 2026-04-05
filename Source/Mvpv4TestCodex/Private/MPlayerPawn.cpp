#include "MPlayerPawn.h"

#include "Components/StaticMeshComponent.h"
#include "Components/TextRenderComponent.h"
#include "UObject/ConstructorHelpers.h"

AMPlayerPawn::AMPlayerPawn()
{
	SceneRoot = CreateDefaultSubobject<USceneComponent>(TEXT("SceneRoot"));
	SetRootComponent(SceneRoot);

	PawnMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("PawnMesh"));
	PawnMesh->SetupAttachment(SceneRoot);
	PawnMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	PawnMesh->SetRelativeScale3D(FVector(0.45f, 0.45f, 0.45f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> SphereMesh(TEXT("/Engine/BasicShapes/Sphere.Sphere"));
	if (SphereMesh.Succeeded())
	{
		PawnMesh->SetStaticMesh(SphereMesh.Object);
	}

	PawnLabel = CreateDefaultSubobject<UTextRenderComponent>(TEXT("PawnLabel"));
	PawnLabel->SetupAttachment(SceneRoot);
	PawnLabel->SetHorizontalAlignment(EHorizTextAligment::EHTA_Center);
	PawnLabel->SetVerticalAlignment(EVerticalTextAligment::EVRTA_TextCenter);
	PawnLabel->SetWorldSize(30.0f);
	PawnLabel->SetRelativeLocation(FVector(0.0f, 0.0f, 90.0f));
	PawnLabel->SetRelativeRotation(FRotator(90.0f, 0.0f, 0.0f));

	PrimaryActorTick.bCanEverTick = false;
}

void AMPlayerPawn::MoveToTile(const FVector& WorldLocation, const int32 NewTileIndex)
{
	CurrentTileIndex = NewTileIndex;
	SetActorLocation(WorldLocation);
}

void AMPlayerPawn::SetPawnColor(const FLinearColor& InColor)
{
	PawnMesh->SetVectorParameterValueOnMaterials(TEXT("Color"), FVector(InColor));
	PawnLabel->SetTextRenderColor(InColor.ToFColor(true));
}

void AMPlayerPawn::SetLabelText(const FString& InLabel)
{
	PawnLabel->SetText(FText::FromString(InLabel));
}
