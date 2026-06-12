// Copyright Phase14 增量批 1. 拍卖冒烟用例(GDD 2.1 英式拍卖)。
// 独立名字空间 Demo_MonopolyAuction.Inc1.*,独立新文件——v0 冻结文件 MADemoSmokeTests.cpp 零触碰。
#include "Misc/AutomationTest.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoDataAssets.h"

#if WITH_AUTOMATION_TESTS

// 用例 Inc1-1:拍卖触发条件(GDD 2.1:落无主地产且拒购立即触发;他人地产/已有主不触发)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoInc1AuctionTriggerTest,
	"Demo_MonopolyAuction.Inc1.AuctionTrigger",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoInc1AuctionTriggerTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();

	// 现金压到 AutoBuyPolicy 拒绝区间(50 < 地价60+缓冲100),落 1 号地中海街 → 触发拍卖。
	UMADemoPlayerData* P0 = GS->GetPlayer(0);
	P0->Money = 50;
	P0->CurrentTileIndex = 1;
	GM->OnPlayerLanded(1);

	const FMADemoAuctionState& A = GS->AuctionState;
	TestTrue(TEXT("拒购触发拍卖激活"), A.bActive);
	TestEqual(TEXT("回合阶段切到拍卖"), (int32)GS->TurnPhase, (int32)EMADemoTurnPhase::Auction);
	TestEqual(TEXT("标的为落格地产"), A.TileIndex, 1);
	// 起拍价 = 地价 x 50%(数据驱动对账,GDD 2.1 锁定)。
	const FMADemoTileInfo Info = GS->GetTileInfo(1);
	const int32 ExpectedStart = (Info.Price * GS->RulesData->AuctionStartPricePercent) / 100;
	TestEqual(TEXT("起拍价为地价 50%"), A.StartPrice, ExpectedStart);
	TestEqual(TEXT("轮转起点为落格玩家"), A.CurrentBidderIndex, 0);
	// 全员未破产 → 无人开场弃权(出价资格,评审清单 5)。
	for (int32 i = 0; i < GS->Players.Num(); ++i)
	{
		TestFalse(FString::Printf(TEXT("P%d 开场未弃权"), i + 1), A.PassedPlayers[i]);
	}

	// 反例 1:已有主地产不触发(StartAuction 守卫)。
	AMADemoGameMode* GM2 = NewObject<AMADemoGameMode>();
	GM2->InitializeGame(2, 7);
	AMADemoGameState* GS2 = GM2->GetDemoGameState();
	GS2->SetTileOwner(3, 1);
	GM2->StartAuction(3);
	TestFalse(TEXT("已有主地产不可拍"), GS2->AuctionState.bActive);

	// 反例 2:非地产格不触发。
	GM2->StartAuction(4); // 所得税格
	TestFalse(TEXT("非地产格不可拍"), GS2->AuctionState.bActive);

	// 反例 3:落他人地产走付租,不触发拍卖。
	UMADemoPlayerData* Q0 = GS2->GetPlayer(0);
	Q0->CurrentTileIndex = 3;
	GM2->OnPlayerLanded(3);
	TestFalse(TEXT("他人地产付租不触发拍卖"), GS2->AuctionState.bActive);
	return true;
}

// 用例 Inc1-2:出价推进(首口=起拍价,其后=最高+步长 10;轮转正确)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoInc1AuctionBidProgressionTest,
	"Demo_MonopolyAuction.Inc1.AuctionBidProgression",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoInc1AuctionBidProgressionTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();
	GM->StartAuction(1); // 地中海街:地价 60,起拍 30

	const FMADemoAuctionState& A = GS->AuctionState;
	const int32 Step = GS->RulesData->AuctionBidStep;
	const int32 Start = A.StartPrice;

	// 首口价 = 起拍价。
	TestEqual(TEXT("首口拟出价 = 起拍价"), GM->GetNextBidAmount(), Start);
	GM->AuctionBidCurrent(); // P0 出首口
	TestEqual(TEXT("首口成立"), A.HighestBid, Start);
	TestEqual(TEXT("最高出价人 P0"), A.HighestBidderIndex, 0);
	TestEqual(TEXT("轮到 P1"), A.CurrentBidderIndex, 1);

	// 第二口 = 最高 + 步长(GDD 2.1 加价步长 10)。
	TestEqual(TEXT("第二口拟出价 = 最高+步长"), GM->GetNextBidAmount(), Start + Step);
	GM->AuctionBidCurrent(); // P1 出
	TestEqual(TEXT("第二口成立"), A.HighestBid, Start + Step);
	TestEqual(TEXT("最高出价人 P1"), A.HighestBidderIndex, 1);
	TestEqual(TEXT("轮到 P2"), A.CurrentBidderIndex, 2);
	TestEqual(TEXT("第三口拟出价继续步进"), GM->GetNextBidAmount(), Start + Step * 2);
	TestTrue(TEXT("出价记录有 开拍+2 口"), A.BidLog.Num() >= 3);
	return true;
}

// 用例 Inc1-3:成交结算(其余全弃 → 最高者立付获契,GDD 2.1)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoInc1AuctionSettlementTest,
	"Demo_MonopolyAuction.Inc1.AuctionSettlement",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoInc1AuctionSettlementTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();
	const int32 P1CashBefore = GS->GetPlayer(1)->Money;

	GM->StartAuction(1); // 起拍 30,轮到 P0
	GM->AuctionPassCurrent(); // P0 弃权 → 轮到 P1
	GM->AuctionBidCurrent();  // P1 出 30 → 轮到 P2
	GM->AuctionPassCurrent(); // P2 弃权 → 仅剩最高者 P1 → 成交

	const FMADemoAuctionState& A = GS->AuctionState;
	TestFalse(TEXT("拍卖已收敛"), A.bActive);
	TestEqual(TEXT("地契归最高出价者 P1"), GS->GetTileOwner(1), 1);
	TestEqual(TEXT("按出价立即支付"), GS->GetPlayer(1)->Money, P1CashBefore - A.HighestBid);
	TestTrue(TEXT("P1 持有清单含标的"), GS->GetPlayer(1)->OwnedProperties.Contains(1));
	TestEqual(TEXT("拍后回合停 TurnEnd"), (int32)GS->TurnPhase, (int32)EMADemoTurnPhase::TurnEnd);
	TestTrue(TEXT("记录含成交"), A.BidLog.Last().Contains(TEXT("成交")));
	return true;
}

// 用例 Inc1-4:流拍归属(全员弃权无人出价 → 地产保持无主,不降价重拍,GDD 2.1)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoInc1AuctionNoSaleTest,
	"Demo_MonopolyAuction.Inc1.AuctionNoSale",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoInc1AuctionNoSaleTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();

	GM->StartAuction(27); // 百老汇:地价 400,起拍 200
	GM->AuctionPassCurrent(); // P0 弃权
	GM->AuctionPassCurrent(); // P1 弃权 → 全弃且无人出价 → 流拍

	const FMADemoAuctionState& A = GS->AuctionState;
	TestFalse(TEXT("拍卖已收敛"), A.bActive);
	TestEqual(TEXT("流拍保持无主"), GS->GetTileOwner(27), -1);
	TestEqual(TEXT("流拍后回合停 TurnEnd"), (int32)GS->TurnPhase, (int32)EMADemoTurnPhase::TurnEnd);
	TestTrue(TEXT("记录含流拍"), A.BidLog.Last().Contains(TEXT("流拍")));
	return true;
}

// 用例 Inc1-5:暂停冻结拍卖(Esc 暂停语义贯穿拍卖:出价/弃权均被拒,恢复后正常)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoInc1AuctionPausedFrozenTest,
	"Demo_MonopolyAuction.Inc1.AuctionPausedFrozen",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoInc1AuctionPausedFrozenTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();
	GM->StartAuction(1);

	GM->SetPauseState(true);
	GM->AuctionBidCurrent(); // 暂停中:出价被拒
	const FMADemoAuctionState& A = GS->AuctionState;
	TestEqual(TEXT("暂停中出价被拒(无最高价)"), A.HighestBidderIndex, -1);
	TestEqual(TEXT("暂停中轮转未推进"), A.CurrentBidderIndex, 0);
	GM->AuctionPassCurrent(); // 暂停中:弃权被拒
	TestFalse(TEXT("暂停中弃权被拒"), A.PassedPlayers[0]);
	TestTrue(TEXT("拍卖仍挂起"), A.bActive);

	GM->SetPauseState(false);
	GM->AuctionBidCurrent(); // 恢复后正常出价
	TestEqual(TEXT("恢复后出价生效"), A.HighestBidderIndex, 0);
	TestEqual(TEXT("恢复后首口=起拍价"), A.HighestBid, A.StartPrice);
	return true;
}

// 用例 Inc1-6:整局含自动拍卖收敛(多种子直驱零报错,拍卖不悬挂,胜者合法)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoInc1FullGameWithAuctionTest,
	"Demo_MonopolyAuction.Inc1.FullGameWithAuction",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoInc1FullGameWithAuctionTest::RunTest(const FString& Parameters)
{
	const int32 Seeds[3] = { 3, 11, 99 };
	for (int32 s = 0; s < 3; ++s)
	{
		AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
		const int32 Winner = GM->RunFullGameToCompletion(4, Seeds[s]);
		AMADemoGameState* GS = GM->GetDemoGameState();
		TestTrue(FString::Printf(TEXT("种子 %d 游戏结束"), Seeds[s]), GS->bGameOver);
		TestTrue(FString::Printf(TEXT("种子 %d 胜者合法"), Seeds[s]),
			Winner >= 0 && Winner < GS->Players.Num());
		TestFalse(FString::Printf(TEXT("种子 %d 胜者非破产"), Seeds[s]),
			GS->GetPlayer(Winner)->bIsBankrupt);
		TestFalse(FString::Printf(TEXT("种子 %d 拍卖不悬挂"), Seeds[s]),
			GS->AuctionState.bActive);
	}
	return true;
}

#endif // WITH_AUTOMATION_TESTS
