// Copyright Phase14 demo agent.
#include "MADemoStockMarket.h"
#include "MADemoRulesDataAsset.h"

void UMADemoStockMarket::InitializeStocks(const UMADemoRulesDataAsset* Rules)
{
	const int32 InitPrice = Rules ? Rules->StockInitialPrice : 100;
	Stocks.Empty();
	// 3 支股票 A/B/C,初始价相同(GDD 2.2)
	const TCHAR* Symbols[] = { TEXT("A"), TEXT("B"), TEXT("C") };
	for (const TCHAR* Sym : Symbols)
	{
		FMADemoStock S;
		S.Symbol = Sym;
		S.Price = InitPrice;
		Stocks.Add(S);
	}
}

void UMADemoStockMarket::ApplyTurnSwing(int32 DiceSum, float SwingRatio)
{
	// GDD 2.2:每回合开始按当轮掷骰结果对所有股票 ±SwingRatio 调整。
	// 确定性规则:用 DiceSum 与股票下标的奇偶组合决定涨跌方向,保证冒烟可复现。
	for (int32 i = 0; i < Stocks.Num(); ++i)
	{
		const bool bUp = ((DiceSum + i) % 2) == 0;
		const float Factor = bUp ? (1.0f + SwingRatio) : (1.0f - SwingRatio);
		// 价格至少保留 1,防止跌穿到 0/负
		Stocks[i].Price = FMath::Max(1, FMath::RoundToInt(Stocks[i].Price * Factor));
	}
}

int32 UMADemoStockMarket::GetPrice(int32 StockIndex) const
{
	return Stocks.IsValidIndex(StockIndex) ? Stocks[StockIndex].Price : 0;
}
