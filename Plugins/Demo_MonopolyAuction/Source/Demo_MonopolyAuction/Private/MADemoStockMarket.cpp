// Copyright Phase14 v0 attempt2. 股票市场子系统实现。
#include "MADemoStockMarket.h"

void UMADemoStockMarket::InitializeStocks(int32 InitialPrice)
{
	Stocks.Empty();
	const TCHAR* Symbols[3] = { TEXT("A"), TEXT("B"), TEXT("C") };
	for (int32 i = 0; i < 3; ++i)
	{
		FMADemoStock Stock;
		Stock.Symbol = Symbols[i];
		Stock.Price = InitialPrice;
		Stocks.Add(Stock);
	}
}

void UMADemoStockMarket::ApplyTurnSwing(int32 DiceSum, int32 SwingPercent)
{
	// 确定性波动:奇数和让偶数索引股上涨/奇数索引股下跌,偶数和反之。
	// 这样不引入随机源,冒烟多种子直驱仍可复现。
	const bool bSumOdd = (DiceSum % 2) != 0;
	for (int32 i = 0; i < Stocks.Num(); ++i)
	{
		const bool bIndexEven = (i % 2) == 0;
		const bool bUp = (bSumOdd == bIndexEven);
		const int32 Delta = FMath::Max(1, (Stocks[i].Price * SwingPercent) / 100);
		Stocks[i].Price = bUp ? (Stocks[i].Price + Delta) : FMath::Max(1, Stocks[i].Price - Delta);
	}
}

int32 UMADemoStockMarket::GetPrice(int32 StockIndex) const
{
	if (Stocks.IsValidIndex(StockIndex))
	{
		return Stocks[StockIndex].Price;
	}
	return 0;
}
