// Copyright Phase14 v0 attempt2. 股票市场子系统(GDD 2.2)。
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MADemoTypes.h"
#include "MADemoStockMarket.generated.h"

// 股票市场态(GDD 2.2)。3 支股票 A/B/C,每回合按掷骰确定性波动。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoStockMarket : public UObject
{
	GENERATED_BODY()

public:
	// 3 支股票。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Stock")
	TArray<FMADemoStock> Stocks;

	// 初始化 3 支股票(A/B/C),初始价取自规则资产。
	void InitializeStocks(int32 InitialPrice);

	// 按掷骰和确定性施加本回合波动(±SwingPercent%)。
	// 确定性:用掷骰和的奇偶 + 股票索引决定涨跌方向,保证冒烟可复现。
	void ApplyTurnSwing(int32 DiceSum, int32 SwingPercent);

	// 取某支股票现价。
	int32 GetPrice(int32 StockIndex) const;
};
