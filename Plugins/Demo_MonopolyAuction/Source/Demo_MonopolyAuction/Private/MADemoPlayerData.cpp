// Copyright Phase14 demo agent.
#include "MADemoPlayerData.h"

void UMADemoPlayerData::AddMoney(int32 Amount)
{
	// 仅接受非负加款
	Money += FMath::Max(0, Amount);
}

bool UMADemoPlayerData::DeductMoney(int32 Amount)
{
	const int32 Need = FMath::Max(0, Amount);
	if (Money < Need)
	{
		// 不足额:不扣款,交由破产流程处理(调用方据返回值决定)
		return false;
	}
	Money -= Need;
	return true;
}

bool UMADemoPlayerData::CanAfford(int32 Amount) const
{
	return Money >= FMath::Max(0, Amount);
}

void UMADemoPlayerData::AddProperty(int32 TileIndex)
{
	OwnedProperties.AddUnique(TileIndex);
}
