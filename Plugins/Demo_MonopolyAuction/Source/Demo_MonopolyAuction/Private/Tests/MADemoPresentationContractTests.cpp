// Copyright Phase15 presentation-1. 呈现契约用例(逐 rung 冻结)。
// 名字空间 Demo_MonopolyAuction.PresentationContract.*
// 形状:GameState API 直驱到目标局面 → 经 BuildSnapshot() 取快照 → 断言信息可见性 + 呈现入口存在。
// 禁止断言具体 widget 类名/控件树结构(规范 §4,那属实现用例)。
#include "Misc/AutomationTest.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoDataAssets.h"
#include "UI/MADemoHUDWidget.h"

#if WITH_AUTOMATION_TESTS

// 契约用例 C1:快照含回合号与玩家资金信息可读。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoPresentationContractSnapshotBasicTest,
	"Demo_MonopolyAuction.PresentationContract.SnapshotBasic",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoPresentationContractSnapshotBasicTest::RunTest(const FString& Parameters)
{
	// 直驱局面:初始化 2 名玩家
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 100);
	GM->StartTurn();
	AMADemoGameState* GS = GM->GetDemoGameState();

	// 创建 HUD Widget(呈现入口存在性)
	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>(GS);
	TestNotNull(TEXT("HUD 呈现入口可创建"), HUD);

	// 绑定并取快照
	HUD->BindGameState(GS);
	const FMADemoHUDSnapshot Snap = HUD->BuildSnapshot();

	// 断言信息可见:回合号可读
	TestTrue(TEXT("回合号 >= 0"), Snap.TurnNumber >= 0);

	// 断言玩家资金可读(初始 $1500)
	TestTrue(TEXT("快照含玩家资金数据"), Snap.PlayerCash.Num() >= 2);
	TestEqual(TEXT("P1 初始资金可达"), Snap.PlayerCash[0], 1500);
	TestEqual(TEXT("P2 初始资金可达"), Snap.PlayerCash[1], 1500);

	// 玩家索引信息可见
	TestTrue(TEXT("当前玩家索引可达"), Snap.CurrentPlayerIndex >= 0);
	TestTrue(TEXT("阶段文本非空"), !Snap.PhaseText.IsEmpty());

	return true;
}

// 契约用例 C2:拍卖阶段快照含拍卖地块标识与当前价可达。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoPresentationContractAuctionTest,
	"Demo_MonopolyAuction.PresentationContract.AuctionInfoReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoPresentationContractAuctionTest::RunTest(const FString& Parameters)
{
	// 直驱到拍卖局面:玩家资金不足自动购买阈值,落无主地产触发拍卖
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 42);
	AMADemoGameState* GS = GM->GetDemoGameState();

	// 压低资金确保拒购触发拍卖
	UMADemoPlayerData* P0 = GS->GetPlayer(0);
	TestNotNull(TEXT("P0 数据存在"), P0);
	if (!P0) return false;
	P0->Money = 50;  // 远低于购买缓冲
	P0->CurrentTileIndex = 1;
	GM->OnPlayerLanded(1);  // 直驱落格事件

	// 断言到达拍卖阶段
	TestEqual(TEXT("TurnPhase 应为 Auction"),
		(int32)GS->TurnPhase, (int32)EMADemoTurnPhase::Auction);
	TestTrue(TEXT("AuctionState 激活"), GS->AuctionState.bActive);
	TestEqual(TEXT("拍卖地块标识可达(格索引 1)"), GS->AuctionState.TileIndex, 1);

	// 通过 HUD 快照验证信息可见
	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>(GS);
	TestNotNull(TEXT("拍卖局面下 HUD 可创建"), HUD);
	HUD->BindGameState(GS);
	const FMADemoHUDSnapshot Snap = HUD->BuildSnapshot();

	// 快照阶段应为拍卖
	TestEqual(TEXT("快照阶段文本为拍卖中"), Snap.PhaseText, FString(TEXT("拍卖中")));
	TestEqual(TEXT("快照 TurnPhase 为 Auction"),
		(int32)Snap.TurnPhase, (int32)EMADemoTurnPhase::Auction);

	// 当前价通过 GameState 可达(快照不含,规范说明可通过 GameState 直读)
	const int32 HighestBid = GS->AuctionState.HighestBid;
	TestTrue(TEXT("当前价 >= 0(可达)"), HighestBid >= 0);
	TestTrue(TEXT("起拍价 > 0(可达)"), GS->AuctionState.StartPrice > 0);

	return true;
}

// 契约用例 C3:破产玩家信息在快照中正确标记。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoPresentationContractBankruptTest,
	"Demo_MonopolyAuction.PresentationContract.BankruptPlayerVisible",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoPresentationContractBankruptTest::RunTest(const FString& Parameters)
{
	// 直驱到一名玩家破产状态
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 77);
	AMADemoGameState* GS = GM->GetDemoGameState();

	// 直接设置 P1 破产标记(不走完整破产流程,仅验证快照可见性)
	UMADemoPlayerData* P1 = GS->GetPlayer(1);
	TestNotNull(TEXT("P1 数据存在"), P1);
	if (!P1) return false;
	P1->bIsBankrupt = true;
	P1->Money = 0;

	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>(GS);
	HUD->BindGameState(GS);
	const FMADemoHUDSnapshot Snap = HUD->BuildSnapshot();

	// 断言破产信息可见
	TestTrue(TEXT("快照含玩家破产数据"), Snap.PlayerBankrupt.Num() >= 2);
	TestTrue(TEXT("P2 破产标记在快照中可达"), Snap.PlayerBankrupt[1]);
	TestFalse(TEXT("P1 未破产标记正确"), Snap.PlayerBankrupt[0]);

	return true;
}

// 契约用例 C4:呈现入口在 GameState 上下文内可创建且 BuildSnapshot 不崩溃。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoPresentationContractEntryTest,
	"Demo_MonopolyAuction.PresentationContract.PresentationEntryExists",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoPresentationContractEntryTest::RunTest(const FString& Parameters)
{
	// 无 GameState 时:快照应返回空快照不崩溃
	UMADemoHUDWidget* HUDNoState = NewObject<UMADemoHUDWidget>();
	TestNotNull(TEXT("无 GameState 时 HUD 可创建"), HUDNoState);
	const FMADemoHUDSnapshot EmptySnap = HUDNoState->BuildSnapshot();
	TestEqual(TEXT("无 GameState 快照回合号为 0"), EmptySnap.TurnNumber, 0);

	// 有 GameState 时:快照含有效数据
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(4, 55);
	GM->StartTurn();
	AMADemoGameState* GS = GM->GetDemoGameState();

	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>(GS);
	TestNotNull(TEXT("有 GameState 时 HUD 可创建"), HUD);
	HUD->BindGameState(GS);

	const FMADemoHUDSnapshot Snap = HUD->BuildSnapshot();
	TestTrue(TEXT("快照有 4 玩家资金数据"), Snap.PlayerCash.Num() == 4);
	TestTrue(TEXT("快照阶段文本非空(进入回合)"), !Snap.PhaseText.IsEmpty());

	return true;
}

#endif // WITH_AUTOMATION_TESTS
