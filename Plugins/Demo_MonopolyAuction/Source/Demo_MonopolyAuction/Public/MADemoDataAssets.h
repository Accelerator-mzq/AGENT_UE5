// Copyright Phase14 v0 attempt2. 数据驱动资产:棋盘与规则。
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MADemoTypes.h"
#include "MADemoDataAssets.generated.h"

// 棋盘数据资产(GDD 2.3)。28 格静态数据 + 角格/交易所选址。
// 构造时铺默认棋盘,扇出时改本资产即可,C++ 不硬编码布局。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoBoardDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UMADemoBoardDataAsset();

	// 28 格静态数据。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Board")
	TArray<FMADemoTileInfo> Tiles;

	// 起点格索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Board")
	int32 StartTileIndex = 0;

	// 监狱探访格索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Board")
	int32 JailVisitTileIndex = 7;

	// 免费停车格索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Board")
	int32 FreeParkingTileIndex = 14;

	// 前往监狱格索引。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Board")
	int32 GoToJailTileIndex = 21;

	// 交易所角格索引(扩展 GDD 2.2,provisional 选 16 号原机会格)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Board")
	int32 StockExchangeTileIndex = 16;

	// 铺默认 28 格棋盘(GDD 2.3 数据表 + 交易所替换)。
	void BuildDefaultBoard();
};

// 规则数据资产。所有可调数值下沉于此,对应契约硬约束或 provisional 默认值。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoRulesDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UMADemoRulesDataAsset();

	// 初始资金(契约 economy.starting_cash)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 StartingCash = 1500;

	// 过起点奖励(契约 economy.start_bonus)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 StartBonus = 200;

	// 骰子数量(契约 dice.count)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 DiceCount = 2;

	// 骰子面数(契约 dice.sides)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 DiceSides = 6;

	// 保释金(契约 jail.bail_cost)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 JailBailCost = 50;

	// 监狱最大停留回合(契约 jail.max_turns)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 JailMaxTurns = 3;

	// 满色组租金倍率(契约 property.full_color_group_rent_multiplier)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 FullColorGroupRentMultiplier = 2;

	// 拍卖起拍价占地价比例(GDD 2.1,百分比)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 AuctionStartPricePercent = 50;

	// 拍卖加价步长(GDD 2.1)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 AuctionBidStep = 10;

	// 股票初始价(GDD 2.2)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 StockInitialPrice = 100;

	// 股价波动幅度(GDD 2.2,百分比 ±10%)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 StockSwingPercent = 10;

	// 僵局回合上限(provisional,契约 cg-max-game-length 高风险未决,给可收敛默认)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 MaxGameRounds = 200;

	// 自动购买保留缓冲(provisional,AutoBuyPolicy 留够保释金缓冲才买)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Rules")
	int32 AutoBuyReserveBuffer = 100;
};
