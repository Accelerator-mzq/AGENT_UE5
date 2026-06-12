// Copyright Phase14 demo agent.
// 规则参数数据资产:把所有可调数值(初始资金/骰子/监狱/起点奖励/拍卖步长等)从 C++ 抽出,
// 满足施工规范 §3"规则参数一律数据驱动"。增量批与扇出只需改资产值,不改代码。
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MADemoRulesDataAsset.generated.h"

// Monopoly 规则参数集合。默认值在构造函数内按 GDD/契约硬约束填充,
// 编辑器可覆盖,DataAsset 实例放 Content/Data/。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoRulesDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UMADemoRulesDataAsset();

	// 初始资金(契约 economy.starting_cash = 1500)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
	int32 StartingCash = 1500;

	// 过/停起点奖励(契约 economy.start_bonus = 200)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Economy")
	int32 StartBonus = 200;

	// 骰子数量(契约 dice.count = 2)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Dice")
	int32 DiceCount = 2;

	// 骰子面数(契约 dice.sides = 6)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Dice")
	int32 DiceSides = 6;

	// 双数是否额外回合(契约 dice.doubles_extra_turn = true)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Dice")
	bool bDoublesGrantExtraTurn = true;

	// 三连双数入狱(契约 dice.triple_doubles_jail = true)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Dice")
	bool bTripleDoublesJail = true;

	// 监狱探访格索引(契约 jail.visit_tile_index = 7)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Jail")
	int32 JailVisitTileIndex = 7;

	// 保释金(契约 jail.bail_cost = 50)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Jail")
	int32 JailBailCost = 50;

	// 监狱最大停留回合(契约 jail.max_turns = 3)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Jail")
	int32 JailMaxTurns = 3;

	// 满色组租金倍率(契约 property.full_color_group_rent_multiplier = 2)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Property")
	int32 FullColorGroupRentMultiplier = 2;

	// 拍卖起拍价占地价比例(GDD 2.1:50%)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Auction")
	float AuctionStartPriceRatio = 0.5f;

	// 拍卖加价步长(GDD 2.1:10 金)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Auction")
	int32 AuctionBidStep = 10;

	// 股票初始价格(GDD 2.2:各 100 金)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stock")
	int32 StockInitialPrice = 100;

	// 股票每回合波动幅度(GDD 2.2:±10%)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Stock")
	float StockSwingRatio = 0.1f;

	// 僵局回合上限(provisional:GDD 只给目标时长未给硬上限,默认 200 回合判和局收敛)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Match")
	int32 MaxTurnsBeforeStalemate = 200;
};
