// Copyright Phase14 demo agent.
// 单玩家运行期数据(UObject)。本地热座多人下用 UObject 而非 APlayerState,
// 避免引入 PlayerController/Pawn 网络栈,冒烟可经 GameState API 纯逻辑直驱。
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MADemoPlayerData.generated.h"

// 玩家状态:资金/位置/地产/监狱/破产/股票持仓。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoPlayerData : public UObject
{
	GENERATED_BODY()

public:
	// 玩家序号(0..N-1)
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	int32 PlayerIndex = 0;

	// 显示名
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	FString DisplayName;

	// 当前资金
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	int32 Money = 0;

	// 当前所在格子索引
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	int32 CurrentTileIndex = 0;

	// 拥有的地产索引列表
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	TArray<int32> OwnedProperties;

	// 是否在监狱中
	UPROPERTY(BlueprintReadOnly, Category = "Jail")
	bool bIsInJail = false;

	// 监狱剩余回合(最多 JailMaxTurns)
	UPROPERTY(BlueprintReadOnly, Category = "Jail")
	int32 JailTurnsRemaining = 0;

	// 是否已破产(退出游戏)
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	bool bIsBankrupt = false;

	// 玩家颜色标识(HUD/棋子用)
	UPROPERTY(BlueprintReadOnly, Category = "Player")
	FLinearColor PlayerColor = FLinearColor::White;

	// 股票持仓:索引 0/1/2 对应 A/B/C,值为持有股数
	UPROPERTY(BlueprintReadOnly, Category = "Stock")
	TArray<int32> StockHoldings;

	// 增加资金
	UFUNCTION(BlueprintCallable, Category = "Player")
	void AddMoney(int32 Amount);

	// 扣除资金;返回是否足额(不足时不扣、返回 false,交由破产流程处理)
	UFUNCTION(BlueprintCallable, Category = "Player")
	bool DeductMoney(int32 Amount);

	// 是否买得起
	UFUNCTION(BlueprintCallable, Category = "Player")
	bool CanAfford(int32 Amount) const;

	// 登记一处地产
	UFUNCTION(BlueprintCallable, Category = "Player")
	void AddProperty(int32 TileIndex);
};
