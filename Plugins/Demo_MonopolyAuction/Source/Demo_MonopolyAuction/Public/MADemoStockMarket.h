// Copyright Phase14 demo agent.
// 股票市场运行期态(UObject)。3 支股票 A/B/C,价格随回合波动。
// v0 阶段仅落地数据结构与定价/波动逻辑骨架,完整交易 UI 在 increment-2。
#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MADemoStockMarket.generated.h"

class UMADemoRulesDataAsset;

// 单支股票当前态。
USTRUCT(BlueprintType)
struct FMADemoStock
{
	GENERATED_BODY()

	// 股票代码(A/B/C)
	UPROPERTY(BlueprintReadOnly, Category = "Stock")
	FString Symbol;

	// 现价
	UPROPERTY(BlueprintReadOnly, Category = "Stock")
	int32 Price = 100;
};

// 股票市场:3 支股票现价管理与回合波动。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoStockMarket : public UObject
{
	GENERATED_BODY()

public:
	// 当前 3 支股票
	UPROPERTY(BlueprintReadOnly, Category = "Stock")
	TArray<FMADemoStock> Stocks;

	// 用规则资产初始化 3 支股票(各 StockInitialPrice)
	UFUNCTION(BlueprintCallable, Category = "Stock")
	void InitializeStocks(const UMADemoRulesDataAsset* Rules);

	// 回合开始波动:按掷骰和的奇偶决定涨跌方向,幅度 ±StockSwingRatio。
	// 传入 DiceSum 使波动确定可测(GDD 2.2:按当轮掷骰结果调整)。
	UFUNCTION(BlueprintCallable, Category = "Stock")
	void ApplyTurnSwing(int32 DiceSum, float SwingRatio);

	// 取某支股票现价
	UFUNCTION(BlueprintCallable, Category = "Stock")
	int32 GetPrice(int32 StockIndex) const;
};
