#include "MBoardManager.h"

#include "Engine/World.h"
#include "MTile.h"
#include "MMonopolyTypes.h"

AMBoardManager::AMBoardManager()
{
	PrimaryActorTick.bCanEverTick = false;
}

void AMBoardManager::SpawnBoard(const TArray<FMTileData>& TileDataArray)
{
	UWorld* World = GetWorld();
	if (World == nullptr)
	{
		return;
	}

	ClearBoard();
	UClass* ResolvedTileClass = TileActorClass != nullptr ? TileActorClass.Get() : AMTile::StaticClass();

	for (const FMTileData& TileData : TileDataArray)
	{
		FActorSpawnParameters SpawnParameters;
		SpawnParameters.Owner = this;

		AMTile* TileActor = World->SpawnActor<AMTile>(ResolvedTileClass, CalculateTileWorldLocation(TileData.TileIndex), FRotator::ZeroRotator, SpawnParameters);
		if (TileActor == nullptr)
		{
			continue;
		}

		TileActor->InitTile(TileData);
		TileActors.Add(TileActor);
	}

	UE_LOG(LogTemp, Log, TEXT("[Phase8] BoardManager spawned %d tiles."), TileActors.Num());
}

FVector AMBoardManager::CalculateTileWorldLocation(const int32 TileIndex) const
{
	constexpr int32 BoardCellsPerSide = 8;
	const float CellSize = SideLength / static_cast<float>(BoardCellsPerSide - 1);

	int32 X = BoardCellsPerSide - 1;
	int32 Y = 0;

	if (TileIndex <= 7)
	{
		X = BoardCellsPerSide - 1 - TileIndex;
		Y = 0;
	}
	else if (TileIndex <= 14)
	{
		X = 0;
		Y = TileIndex - 7;
	}
	else if (TileIndex <= 21)
	{
		X = TileIndex - 14;
		Y = BoardCellsPerSide - 1;
	}
	else
	{
		X = BoardCellsPerSide - 1;
		Y = BoardCellsPerSide - 1 - (TileIndex - 21);
	}

	return GetActorLocation() + FVector((X - 3.5f) * CellSize, (Y - 3.5f) * CellSize, TileHeight);
}

AMTile* AMBoardManager::GetTileActor(const int32 TileIndex) const
{
	return TileActors.IsValidIndex(TileIndex) ? TileActors[TileIndex] : nullptr;
}

void AMBoardManager::HighlightTile(const int32 TileIndex, const bool bHighlight)
{
	if (AMTile* TileActor = GetTileActor(TileIndex))
	{
		TileActor->SetHighlight(bHighlight);
	}
}

FVector AMBoardManager::GetPlayerStandLocation(const int32 TileIndex, const int32 PlayerIndex) const
{
	const FVector BaseLocation = CalculateTileWorldLocation(TileIndex);
	const float Radius = 45.0f;
	const float AngleRadians = FMath::DegreesToRadians(90.0f * PlayerIndex);
	return BaseLocation + FVector(FMath::Cos(AngleRadians) * Radius, FMath::Sin(AngleRadians) * Radius, 70.0f);
}

void AMBoardManager::ClearBoard()
{
	for (AMTile* TileActor : TileActors)
	{
		if (TileActor != nullptr)
		{
			TileActor->Destroy();
		}
	}

	TileActors.Reset();
}
