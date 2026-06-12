// Copyright Phase14 demo agent.
#include "MADemoHUDWidget.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"

FMADemoHUDSnapshot UMADemoHUDWidget::BuildSnapshot() const
{
	FMADemoHUDSnapshot Snap;
	AMADemoGameState* GS = BoundGameState;
	if (!GS)
	{
		return Snap;
	}

	Snap.TurnNumber = GS->TurnNumber;

	const UMADemoPlayerData* Cur = GS->GetPlayer(GS->CurrentPlayerIndex);
	if (Cur)
	{
		Snap.CurrentPlayerName = Cur->DisplayName;
		Snap.CurrentPlayerColor = Cur->PlayerColor;
	}

	// 各玩家摘要(GDD 4.1 + 扩展:名/现金/股票市值)
	for (const TObjectPtr<UMADemoPlayerData>& P : GS->Players)
	{
		if (!P)
		{
			continue;
		}
		int32 StockValue = 0;
		if (GS->StockMarket)
		{
			for (int32 i = 0; i < P->StockHoldings.Num(); ++i)
			{
				StockValue += P->StockHoldings[i] * GS->StockMarket->GetPrice(i);
			}
		}
		const FString Line = FString::Printf(TEXT("%s%s  $%d  股值:$%d"),
			*P->DisplayName, P->bIsBankrupt ? TEXT("(破产)") : TEXT(""),
			P->Money, StockValue);
		Snap.PlayerSummaries.Add(Line);
	}

	// 骰子结果文本(扩展 dice.roll_feedback variant)
	const FMADemoDiceResult& D = GS->LastDiceResult;
	Snap.DiceResultText = FString::Printf(TEXT("骰子:%d + %d = %d%s"),
		D.Die1, D.Die2, D.Sum, D.bIsDouble ? TEXT(" (双数)") : TEXT(""));

	// 3 支股票现价摘要(扩展 GDD 4.1:股价走势摘要)
	if (GS->StockMarket)
	{
		TArray<FString> Parts;
		for (const FMADemoStock& S : GS->StockMarket->Stocks)
		{
			Parts.Add(FString::Printf(TEXT("%s:$%d"), *S.Symbol, S.Price));
		}
		Snap.StockSummaryText = FString::Join(Parts, TEXT("  "));
	}

	return Snap;
}

void UMADemoHUDWidget::RefreshHUD()
{
	OnHUDRefreshed(BuildSnapshot());
}
