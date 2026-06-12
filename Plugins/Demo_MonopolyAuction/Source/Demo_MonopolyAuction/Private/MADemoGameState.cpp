// Copyright Phase14 demo agent.
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoBoardDataAsset.h"
#include "MADemoRulesDataAsset.h"
#include "MADemoStockMarket.h"

AMADemoGameState::AMADemoGameState()
{
	// GameState 不需要逐帧 Tick(施工规范 §2)
	PrimaryActorTick.bCanEverTick = false;
}

FMADemoTileInfo AMADemoGameState::GetTileInfo(int32 TileIndex) const
{
	if (BoardData && BoardData->Tiles.IsValidIndex(TileIndex))
	{
		return BoardData->Tiles[TileIndex];
	}
	return FMADemoTileInfo();
}

int32 AMADemoGameState::GetTileOwner(int32 TileIndex) const
{
	return TileOwners.IsValidIndex(TileIndex) ? TileOwners[TileIndex] : -1;
}

void AMADemoGameState::SetTileOwner(int32 TileIndex, int32 PlayerIndex)
{
	if (TileOwners.IsValidIndex(TileIndex))
	{
		TileOwners[TileIndex] = PlayerIndex;
	}
}

UMADemoPlayerData* AMADemoGameState::GetPlayer(int32 PlayerIndex) const
{
	return Players.IsValidIndex(PlayerIndex) ? Players[PlayerIndex] : nullptr;
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
	// 该颜色组所有地产格都必须属于此玩家
	bool bAnyInGroup = false;
	for (const FMADemoTileInfo& Tile : BoardData->Tiles)
	{
		if (Tile.TileType == EMADemoTileType::Property && Tile.ColorGroup == Group)
		{
			bAnyInGroup = true;
			if (GetTileOwner(Tile.TileIndex) != PlayerIndex)
			{
				return false;
			}
		}
	}
	return bAnyInGroup;
}

int32 AMADemoGameState::CalculateRent(int32 TileIndex) const
{
	const FMADemoTileInfo Info = GetTileInfo(TileIndex);
	if (Info.TileType != EMADemoTileType::Property)
	{
		return 0;
	}
	int32 Rent = Info.BaseRent;
	// 局部命名 OwnerIndex 避免遮蔽 AActor::Owner(C4458)
	const int32 OwnerIndex = GetTileOwner(TileIndex);
	// 满色组租金翻倍(GDD 2.4)
	const int32 Mult = RulesData ? RulesData->FullColorGroupRentMultiplier : 2;
	if (OwnerIndex >= 0 && DoesPlayerOwnColorGroup(OwnerIndex, Info.ColorGroup))
	{
		Rent *= Mult;
	}
	return Rent;
}

int32 AMADemoGameState::GetPlayerNetWorth(int32 PlayerIndex) const
{
	const UMADemoPlayerData* P = GetPlayer(PlayerIndex);
	if (!P)
	{
		return 0;
	}
	int32 Worth = P->Money;
	// 加地产购入价(简化估值:用地价)
	if (BoardData)
	{
		for (int32 PropIdx : P->OwnedProperties)
		{
			Worth += GetTileInfo(PropIdx).Price;
		}
	}
	// 加股票市值(GDD 2.2:破产判定时持仓按现价折算)
	if (StockMarket)
	{
		for (int32 i = 0; i < P->StockHoldings.Num(); ++i)
		{
			Worth += P->StockHoldings[i] * StockMarket->GetPrice(i);
		}
	}
	return Worth;
}
