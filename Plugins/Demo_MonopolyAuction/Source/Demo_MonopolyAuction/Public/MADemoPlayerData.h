// Copyright Phase14 v0 attempt2. 单玩家运行期数据。
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MADemoPlayerData.generated.h"

// 单玩家运行期数据(UObject 建模)。
// 热座多人下用 UObject 而非 PlayerState,避免引入网络栈,使冒烟可纯逻辑直驱。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoPlayerData : public UObject
{
	GENERATED_BODY()

public:
	// 玩家索引(0 起)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	int32 PlayerIndex = 0;

	// 当前资金。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	int32 Money = 1500;

	// 当前所在格索引。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	int32 CurrentTileIndex = 0;

	// 拥有的地产索引列表。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	TArray<int32> OwnedProperties;

	// 是否在监狱中。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	bool bIsInJail = false;

	// 监狱已停留回合数。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	int32 JailTurnsServed = 0;

	// 是否已破产。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	bool bIsBankrupt = false;

	// 玩家颜色标识。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	FLinearColor PlayerColor = FLinearColor::White;

	// 3 支股票持仓数量(索引 0/1/2 对应 A/B/C)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Player")
	TArray<int32> StockHoldings;

	// 增加资金。
	void AddMoney(int32 Amount);

	// 扣款,返回是否成功(钱够)。
	bool DeductMoney(int32 Amount);

	// 是否买得起。
	bool CanAfford(int32 Amount) const { return Money >= Amount; }

	// 增加一块地产。
	void AddProperty(int32 TileIndex);

	// 破产清算:清空地产(地产归无主由 GameState 处理)。
	void ClearProperties();
};
