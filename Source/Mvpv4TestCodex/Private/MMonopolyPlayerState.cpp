#include "MMonopolyPlayerState.h"

AMMonopolyPlayerState::AMMonopolyPlayerState()
{
	PlayerDisplayName = TEXT("Player");
}

void AMMonopolyPlayerState::AddMoney(const int32 Amount)
{
	Money += FMath::Max(0, Amount);
}

bool AMMonopolyPlayerState::DeductMoney(const int32 Amount)
{
	const int32 SafeAmount = FMath::Max(0, Amount);
	if (Money < SafeAmount)
	{
		return false;
	}

	Money -= SafeAmount;
	return true;
}

bool AMMonopolyPlayerState::CanAfford(const int32 Amount) const
{
	return Money >= FMath::Max(0, Amount);
}

void AMMonopolyPlayerState::AddProperty(const int32 TileIndex)
{
	if (TileIndex != INDEX_NONE)
	{
		OwnedTileIndices.AddUnique(TileIndex);
	}
}

void AMMonopolyPlayerState::RemoveProperty(const int32 TileIndex)
{
	OwnedTileIndices.Remove(TileIndex);
}

void AMMonopolyPlayerState::RemoveAllProperties()
{
	OwnedTileIndices.Reset();
}

FString AMMonopolyPlayerState::GetResolvedDisplayName() const
{
	return PlayerDisplayName.IsEmpty() ? GetPlayerName() : PlayerDisplayName;
}
