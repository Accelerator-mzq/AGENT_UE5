// Copyright Phase14 v0 attempt2. 单玩家运行期数据实现。
#include "MADemoPlayerData.h"

void UMADemoPlayerData::AddMoney(int32 Amount)
{
	Money += Amount;
}

bool UMADemoPlayerData::DeductMoney(int32 Amount)
{
	// 钱不够直接返回失败,由调用方触发破产流程。
	if (Money < Amount)
	{
		return false;
	}
	Money -= Amount;
	return true;
}

void UMADemoPlayerData::AddProperty(int32 TileIndex)
{
	OwnedProperties.AddUnique(TileIndex);
}

void UMADemoPlayerData::ClearProperties()
{
	OwnedProperties.Empty();
}
