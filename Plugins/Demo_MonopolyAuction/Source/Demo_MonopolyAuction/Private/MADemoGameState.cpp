// Copyright Phase14 v0 attempt2. 全量可读游戏状态实现。
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoDataAssets.h"

AMADemoGameState::AMADemoGameState()
{
	// 状态层不需要 Tick。
	PrimaryActorTick.bCanEverTick = false;
}

FMADemoTileInfo AMADemoGameState::GetTileInfo(int32 Index) const
{
	if (BoardData && BoardData->Tiles.IsValidIndex(Index))
	{
		return BoardData->Tiles[Index];
	}
	return FMADemoTileInfo();
}

int32 AMADemoGameState::GetTileOwner(int32 Index) const
{
	if (TileOwnership.IsValidIndex(Index))
	{
		return TileOwnership[Index];
	}
	return -1;
}

void AMADemoGameState::SetTileOwner(int32 Index, int32 PlayerIndex)
{
	if (TileOwnership.IsValidIndex(Index))
	{
		TileOwnership[Index] = PlayerIndex;
	}
}

UMADemoPlayerData* AMADemoGameState::GetPlayer(int32 Index) const
{
	if (Players.IsValidIndex(Index))
	{
		return Players[Index];
	}
	return nullptr;
}

int32 AMADemoGameState::GetActivePlayerCount() const
{
	int32 Count = 0;
	for (const TObjectPtr<UMADemoPlayerData>& P : Players)
	{
		if (P && !P->bIsBankrupt)
		{
			++Count;
		}
	}
	return Count;
}

bool AMADemoGameState::DoesPlayerOwnColorGroup(int32 PlayerIndex, EMADemoColorGroup Group) const
{
	if (!BoardData || Group == EMADemoColorGroup::None)
	{
		return false;
	}
	// 遍历棋盘:某色组所有地产格是否都属该玩家。
	bool bFoundAny = false;
	for (int32 i = 0; i < BoardData->Tiles.Num(); ++i)
	{
		const FMADemoTileInfo& Tile = BoardData->Tiles[i];
		if (Tile.TileType == EMADemoTileType::Property && Tile.ColorGroup == Group)
		{
			bFoundAny = true;
			if (GetTileOwner(i) != PlayerIndex)
			{
				return false;
			}
		}
	}
	return bFoundAny;
}

int32 AMADemoGameState::CalculateRent(int32 TileIndex) const
{
	const FMADemoTileInfo Info = GetTileInfo(TileIndex);
	if (Info.TileType != EMADemoTileType::Property)
	{
		return 0;
	}
	int32 Rent = Info.BaseRent;
	const int32 TileOwnerIndex = GetTileOwner(TileIndex);
	// 满色组租金翻倍(契约 property.full_color_group_rent_multiplier)。
	if (TileOwnerIndex >= 0 && DoesPlayerOwnColorGroup(TileOwnerIndex, Info.ColorGroup))
	{
		const int32 Mult = (RulesData ? RulesData->FullColorGroupRentMultiplier : 2);
		Rent *= Mult;
	}
	return Rent;
}

int32 AMADemoGameState::GetPlayerStockValue(int32 PlayerIndex) const
{
	const UMADemoPlayerData* P = GetPlayer(PlayerIndex);
	if (!P || !StockMarket)
	{
		return 0;
	}
	int32 Value = 0;
	for (int32 s = 0; s < P->StockHoldings.Num(); ++s)
	{
		Value += P->StockHoldings[s] * StockMarket->GetPrice(s);
	}
	return Value;
}

int32 AMADemoGameState::GetPlayerNetWorth(int32 PlayerIndex) const
{
	const UMADemoPlayerData* P = GetPlayer(PlayerIndex);
	if (!P)
	{
		return 0;
	}
	int32 Worth = P->Money;
	// 地产按地价折算。
	for (int32 TileIdx : P->OwnedProperties)
	{
		Worth += GetTileInfo(TileIdx).Price;
	}
	// 加股票市值。
	Worth += GetPlayerStockValue(PlayerIndex);
	return Worth;
}
