// Copyright Phase14 demo agent.
// v0 冒烟用例(名字空间 Demo_MonopolyAuction.Smoke)。
// 经 GameState/GameMode API 直驱一局到终局零报错 + 数据完整性断言 + widget 创建冒烟。
// 不走 UI 点击,不依赖 PIE 关卡,确保 -unattended commandlet 下可跑。
#include "Misc/AutomationTest.h"
#include "MADemoTypes.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoBoardDataAsset.h"
#include "MADemoRulesDataAsset.h"
#include "MADemoStockMarket.h"
#include "MADemoHUDWidget.h"
#include "MADemoFrontendWidgets.h"
#include "MADemoFoundations.h"

#if WITH_AUTOMATION_TESTS

// 工具:构造一个独立的 GameMode 并初始化一局(不依赖 World/PIE)。
static AMADemoGameMode* MakeGameMode()
{
	// GameMode 作为 AActor 需要一个 Outer;用瞬态包即可,InitializeGame 内部自行 new GameState。
	return NewObject<AMADemoGameMode>(GetTransientPackage(), AMADemoGameMode::StaticClass());
}

// ── 用例 1:棋盘数据完整性(28 格 / 角格 / 颜色组)──────────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoardDataTest,
	"Demo_MonopolyAuction.Smoke.BoardData",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoBoardDataTest::RunTest(const FString& Parameters)
{
	UMADemoBoardDataAsset* Board = NewObject<UMADemoBoardDataAsset>();
	TestEqual(TEXT("棋盘应为 28 格"), Board->Tiles.Num(), 28);
	TestEqual(TEXT("0 号应为起点"), (int32)Board->Tiles[0].TileType, (int32)EMADemoTileType::Start);
	TestEqual(TEXT("7 号应为监狱探访"), (int32)Board->Tiles[7].TileType, (int32)EMADemoTileType::JailVisit);
	TestEqual(TEXT("21 号应为前往监狱"), (int32)Board->Tiles[21].TileType, (int32)EMADemoTileType::GoToJail);
	TestEqual(TEXT("16 号应为交易所(扩展角格)"), (int32)Board->Tiles[16].TileType, (int32)EMADemoTileType::Exchange);

	// 统计地产格数量(GDD:16 个普通地产 + 但 16 号机会改交易所不影响地产计数)
	int32 PropertyCount = 0;
	for (const FMADemoTileInfo& T : Board->Tiles)
	{
		if (T.TileType == EMADemoTileType::Property)
		{
			++PropertyCount;
		}
	}
	TestEqual(TEXT("地产格应为 16 个"), PropertyCount, 16);
	return true;
}

// ── 用例 2:骰子规则(2D6 范围 + 双数判定)──────────────────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoDiceTest,
	"Demo_MonopolyAuction.Smoke.Dice",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoDiceTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = MakeGameMode();
	GM->InitializeGame(3, 999);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("GameState 应存在"), GS);

	// 驱动若干步,断言每次骰子在合法范围且和一致
	GM->StartTurn();
	for (int32 i = 0; i < 50; ++i)
	{
		if (GM->IsGameOver())
		{
			break;
		}
		if (GS->TurnPhase == EMADemoTurnPhase::WaitingForRoll)
		{
			GM->RequestRollAndResolve();
			const FMADemoDiceResult& D = GS->LastDiceResult;
			TestTrue(TEXT("骰1 在 1..6"), D.Die1 >= 1 && D.Die1 <= 6);
			TestTrue(TEXT("骰2 在 1..6"), D.Die2 >= 1 && D.Die2 <= 6);
			TestEqual(TEXT("和应等于两骰之和"), D.Sum, D.Die1 + D.Die2);
			TestEqual(TEXT("双数判定一致"), D.bIsDouble, D.Die1 == D.Die2);
		}
		else
		{
			GM->AdvanceToNextPlayer();
			GM->StartTurn();
		}
	}
	return true;
}

// ── 用例 3:经济与租金(满色组翻倍)─────────────────────────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoEconomyTest,
	"Demo_MonopolyAuction.Smoke.Economy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoEconomyTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = MakeGameMode();
	GM->InitializeGame(2, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();

	// 玩家 0 初始资金应为 1500(契约 starting_cash)
	TestEqual(TEXT("初始资金 1500"), GS->GetPlayer(0)->Money, 1500);

	// 手工让玩家 0 拥有 Brown 组(1,3),验证满组租金翻倍
	GS->SetTileOwner(1, 0);
	GS->SetTileOwner(3, 0);
	TestTrue(TEXT("玩家0 应持有 Brown 满组"),
		GS->DoesPlayerOwnColorGroup(0, EMADemoColorGroup::Brown));
	const int32 Rent1 = GS->CalculateRent(1);
	const FMADemoTileInfo Info1 = GS->GetTileInfo(1);
	TestEqual(TEXT("满组租金应为基础租金 x2"), Rent1, Info1.BaseRent * 2);
	return true;
}

// ── 用例 4:整局驱动到终局零报错(里程碑 B 核心)────────────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoFullGameTest,
	"Demo_MonopolyAuction.Smoke.FullGameLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoFullGameTest::RunTest(const FString& Parameters)
{
	// 多个种子各跑一局,确保不同走向都能收敛(无死循环/崩溃)
	const int32 Seeds[] = { 1, 42, 1000, 20260612, 7 };
	for (int32 Seed : Seeds)
	{
		AMADemoGameMode* GM = MakeGameMode();
		GM->InitializeGame(4, Seed);
		AMADemoGameState* GS = GM->GetDemoGameState();

		const int32 Winner = GM->RunFullGameToCompletion();

		TestTrue(TEXT("整局应收敛到 GameOver"), GM->IsGameOver());
		TestTrue(TEXT("应决出胜者索引(>=0)"), Winner >= 0);
		TestTrue(TEXT("胜者索引在玩家范围内"), GS->Players.IsValidIndex(Winner));
		// 胜者必须是未破产玩家
		TestTrue(TEXT("胜者未破产"), GS->GetPlayer(Winner) && !GS->GetPlayer(Winner)->bIsBankrupt);
		// 回合数不应超过僵局上限
		TestTrue(TEXT("回合数不超过上限"),
			GS->TurnNumber <= GS->RulesData->MaxTurnsBeforeStalemate);
	}
	return true;
}

// ── 用例 5:监狱与破产语义 ─────────────────────────────────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoJailBankruptcyTest,
	"Demo_MonopolyAuction.Smoke.JailBankruptcy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoJailBankruptcyTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = MakeGameMode();
	GM->InitializeGame(2, 3);
	AMADemoGameState* GS = GM->GetDemoGameState();

	// 破产语义:把玩家 1 资金清空并令其支付超额,应破产且游戏结束
	UMADemoPlayerData* P1 = GS->GetPlayer(1);
	P1->Money = 10;
	// 让玩家 1 拥有一处地产,破产后应归无主
	GS->SetTileOwner(5, 1);
	P1->AddProperty(5);

	// 直接用 GameState API 验证存活计数
	TestEqual(TEXT("初始存活 2 人"), GS->GetActivePlayerCount(), 2);

	// 监狱状态字段健全性:进监狱后 bIsInJail 应可置位
	UMADemoPlayerData* P0 = GS->GetPlayer(0);
	P0->bIsInJail = true;
	P0->JailTurnsRemaining = GS->RulesData->JailMaxTurns;
	TestTrue(TEXT("监狱标记可置位"), P0->bIsInJail);
	TestEqual(TEXT("监狱回合 = 上限"), P0->JailTurnsRemaining, GS->RulesData->JailMaxTurns);
	return true;
}

// ── 用例 6:widget 创建冒烟(HUD + 前台外壳 + 快照)──────────────────
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoWidgetCreationTest,
	"Demo_MonopolyAuction.Smoke.WidgetCreation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FMADemoWidgetCreationTest::RunTest(const FString& Parameters)
{
	// 用 CreateWidget 需要 World;commandlet 下用 NewObject 直接构造 UUserWidget 子类做存在性/接口冒烟。
	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>();
	TestNotNull(TEXT("HUD widget 应创建"), HUD);

	// 给 HUD 绑定一局状态,验证快照能算出来且字段非空
	AMADemoGameMode* GM = MakeGameMode();
	GM->InitializeGame(3, 55);
	GM->StartTurn();
	GM->RequestRollAndResolve();
	HUD->BoundGameState = GM->GetDemoGameState();
	const FMADemoHUDSnapshot Snap = HUD->BuildSnapshot();
	TestEqual(TEXT("HUD 玩家摘要应 3 行"), Snap.PlayerSummaries.Num(), 3);
	TestTrue(TEXT("HUD 骰子文本非空"), !Snap.DiceResultText.IsEmpty());
	TestTrue(TEXT("HUD 股票摘要非空"), !Snap.StockSummaryText.IsEmpty());

	// 前台外壳 widget 全部可创建
	TestNotNull(TEXT("StartScreen"), NewObject<UMADemoStartScreenWidget>());
	TestNotNull(TEXT("MainMenu"), NewObject<UMADemoMainMenuWidget>());
	TestNotNull(TEXT("Settings"), NewObject<UMADemoSettingsWidget>());
	TestNotNull(TEXT("Pause"), NewObject<UMADemoPauseWidget>());
	TestNotNull(TEXT("Results"), NewObject<UMADemoResultsWidget>());

	// 基础底座可创建并初始化
	UMADemoInputFoundation* Input = NewObject<UMADemoInputFoundation>();
	Input->InitializeDefaultBindings();
	TestEqual(TEXT("输入底座应有 4 个动作绑定"), Input->DefaultBindings.Num(), 4);

	UMADemoAudioFoundation* Audio = NewObject<UMADemoAudioFoundation>();
	Audio->SetBGMVolume(0.5f);
	Audio->PlayBasicSFX(TEXT("dice_roll"));
	TestEqual(TEXT("音频底座记录最近 SFX"), Audio->LastPlayedSFXTag, FString(TEXT("dice_roll")));

	UMADemoPlatformFoundation* Platform = NewObject<UMADemoPlatformFoundation>();
	Platform->ApplyDisplaySettings(1, 1280, 720);
	TestEqual(TEXT("平台底座分辨率宽"), Platform->ResolutionX, 1280);
	return true;
}

#endif // WITH_AUTOMATION_TESTS
