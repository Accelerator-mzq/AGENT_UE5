#include "MDice.h"

#include "Components/StaticMeshComponent.h"
#include "UObject/ConstructorHelpers.h"

AMDice::AMDice()
{
	DiceMesh = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DiceMesh"));
	SetRootComponent(DiceMesh);
	DiceMesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	DiceMesh->SetRelativeScale3D(FVector(0.35f, 0.35f, 0.35f));

	static ConstructorHelpers::FObjectFinder<UStaticMesh> CubeMesh(TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (CubeMesh.Succeeded())
	{
		DiceMesh->SetStaticMesh(CubeMesh.Object);
	}

	PrimaryActorTick.bCanEverTick = false;
}

FMDiceResult AMDice::RollDice()
{
	FMDiceResult Result;
	Result.DieA = FMath::RandRange(1, 6);
	Result.DieB = FMath::RandRange(1, 6);
	Result.Total = Result.DieA + Result.DieB;
	Result.bIsDouble = Result.DieA == Result.DieB;
	return Result;
}

void AMDice::PlayRollAnimation()
{
	// Phase 8 先使用轻量实现，仅做旋转反馈，不引入额外时间轴资产。
	AddActorLocalRotation(FRotator(0.0f, 180.0f, 180.0f));
}
