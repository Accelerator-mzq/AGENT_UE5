#include "MMonopolyGameState.h"

#include "MMonopolyPlayerState.h"

namespace MonopolyGameState
{
	static FMTileData MakePropertyTile(const int32 TileIndex, const TCHAR* TileName, const EMColorGroup ColorGroup, const int32 Cost, const int32 Rent)
	{
		FMTileData TileData;
		TileData.TileIndex = TileIndex;
		TileData.TileName = TileName;
		TileData.TileType = EMTileType::Property;
		TileData.ColorGroup = ColorGroup;
		TileData.Cost = Cost;
		TileData.Rent = Rent;
		TileData.bCanBeOwned = true;
		return TileData;
	}

	static FMTileData MakeSimpleTile(const int32 TileIndex, const TCHAR* TileName, const EMTileType TileType)
	{
		FMTileData TileData;
		TileData.TileIndex = TileIndex;
		TileData.TileName = TileName;
		TileData.TileType = TileType;
		return TileData;
	}

	static FMTileData MakeTaxTile(const int32 TileIndex, const TCHAR* TileName, const int32 TaxAmount)
	{
		FMTileData TileData = MakeSimpleTile(TileIndex, TileName, EMTileType::Tax);
		TileData.TaxAmount = TaxAmount;
		return TileData;
	}
}

AMMonopolyGameState::AMMonopolyGameState()
{
	InitializeTileData();
}

void AMMonopolyGameState::InitializeTileData()
{
	TileDataArray.Reset();
	TileDataArray.Reserve(28);

	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(0, TEXT("起点"), EMTileType::Start));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(1, TEXT("地中海街"), EMColorGroup::Brown, 60, 4));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(2, TEXT("公共基金"), EMTileType::CommunityChest));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(3, TEXT("波罗的海街"), EMColorGroup::Brown, 80, 8));
	TileDataArray.Add(MonopolyGameState::MakeTaxTile(4, TEXT("所得税"), 200));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(5, TEXT("东方大道"), EMColorGroup::LightBlue, 100, 12));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(6, TEXT("机会"), EMTileType::Chance));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(7, TEXT("监狱探访"), EMTileType::JailVisit));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(8, TEXT("佛蒙特大道"), EMColorGroup::LightBlue, 120, 14));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(9, TEXT("康涅狄格街"), EMColorGroup::LightBlue, 140, 16));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(10, TEXT("圣查尔斯"), EMColorGroup::Pink, 160, 20));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(11, TEXT("弗吉尼亚街"), EMColorGroup::Pink, 180, 22));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(12, TEXT("公共基金"), EMTileType::CommunityChest));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(13, TEXT("田纳西街"), EMColorGroup::Pink, 200, 24));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(14, TEXT("免费停车"), EMTileType::FreeParking));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(15, TEXT("纽约大道"), EMColorGroup::Orange, 220, 28));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(16, TEXT("机会"), EMTileType::Chance));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(17, TEXT("肯塔基大道"), EMColorGroup::Orange, 240, 30));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(18, TEXT("印第安纳街"), EMColorGroup::Red, 260, 32));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(19, TEXT("伊利诺伊街"), EMColorGroup::Red, 280, 34));
	TileDataArray.Add(MonopolyGameState::MakeTaxTile(20, TEXT("奢侈税"), 150));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(21, TEXT("前往监狱"), EMTileType::GoToJail));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(22, TEXT("太平洋大道"), EMColorGroup::Green, 300, 36));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(23, TEXT("公共基金"), EMTileType::CommunityChest));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(24, TEXT("北卡罗来纳"), EMColorGroup::Green, 320, 38));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(25, TEXT("宾夕法尼亚"), EMColorGroup::Green, 340, 40));
	TileDataArray.Add(MonopolyGameState::MakeSimpleTile(26, TEXT("机会"), EMTileType::Chance));
	TileDataArray.Add(MonopolyGameState::MakePropertyTile(27, TEXT("百老汇"), EMColorGroup::Blue, 400, 50));
}

const FMTileData* AMMonopolyGameState::GetTileData(const int32 TileIndex) const
{
	return TileDataArray.IsValidIndex(TileIndex) ? &TileDataArray[TileIndex] : nullptr;
}

FMTileData* AMMonopolyGameState::GetMutableTileData(const int32 TileIndex)
{
	return TileDataArray.IsValidIndex(TileIndex) ? &TileDataArray[TileIndex] : nullptr;
}

bool AMMonopolyGameState::SetTileOwner(const int32 TileIndex, const int32 OwnerPlayerIndex)
{
	FMTileData* TileData = GetMutableTileData(TileIndex);
	if (TileData == nullptr || !TileData->bCanBeOwned)
	{
		return false;
	}

	TileData->OwnerPlayerIndex = OwnerPlayerIndex;
	return true;
}

bool AMMonopolyGameState::DoesPlayerOwnFullColorGroup(const int32 PlayerIndex, const EMColorGroup ColorGroup) const
{
	if (ColorGroup == EMColorGroup::None || PlayerIndex == INDEX_NONE)
	{
		return false;
	}

	bool bFoundAtLeastOneTile = false;
	for (const FMTileData& TileData : TileDataArray)
	{
		if (TileData.ColorGroup != ColorGroup)
		{
			continue;
		}

		bFoundAtLeastOneTile = true;
		if (TileData.OwnerPlayerIndex != PlayerIndex)
		{
			return false;
		}
	}

	return bFoundAtLeastOneTile;
}

void AMMonopolyGameState::RegisterMonopolyPlayer(AMMonopolyPlayerState* PlayerState)
{
	if (PlayerState == nullptr)
	{
		return;
	}

	MonopolyPlayers.AddUnique(PlayerState);
	ActivePlayerCount = MonopolyPlayers.Num();
}

AMMonopolyPlayerState* AMMonopolyGameState::GetMonopolyPlayer(const int32 PlayerIndex) const
{
	return MonopolyPlayers.IsValidIndex(PlayerIndex) ? MonopolyPlayers[PlayerIndex] : nullptr;
}

void AMMonopolyGameState::SetCurrentPlayerIndex(const int32 NewPlayerIndex)
{
	CurrentPlayerIndex = NewPlayerIndex;
	OnActivePlayerChanged.Broadcast(CurrentPlayerIndex, GetMonopolyPlayer(CurrentPlayerIndex));
}

void AMMonopolyGameState::SetTurnNumber(const int32 NewTurnNumber)
{
	TurnNumber = FMath::Max(1, NewTurnNumber);
	OnTurnNumberChanged.Broadcast(TurnNumber);
}

void AMMonopolyGameState::SetTurnState(const EMTurnState NewTurnState)
{
	TurnState = NewTurnState;
	OnTurnStateChanged.Broadcast(TurnState);
}
