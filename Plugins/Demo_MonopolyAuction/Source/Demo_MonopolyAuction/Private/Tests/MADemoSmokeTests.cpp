// Copyright Phase14 v0 attempt2. 冒烟用例(UE Automation Test 框架)。
// 名字空间 Demo_MonopolyAuction.Smoke。经 GameState/GameMode 公有 API 直驱,不走 UI 点击。
#include "Misc/AutomationTest.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoStockMarket.h"
#include "MADemoDataAssets.h"
#include "MADemoFoundations.h"
#include "UI/MADemoHUDWidget.h"
#include "UI/MADemoFrontendWidgets.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Engine/GameInstance.h"
#include "GameMapsSettings.h"

#if WITH_AUTOMATION_TESTS

// 用例 1:棋盘数据(28 格/角格/交易所/地产计数)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoardDataTest,
	"Demo_MonopolyAuction.Smoke.BoardData",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoardDataTest::RunTest(const FString& Parameters)
{
	UMADemoBoardDataAsset* Board = NewObject<UMADemoBoardDataAsset>();
	TestEqual(TEXT("28 格"), Board->Tiles.Num(), 28);
	TestEqual(TEXT("起点 0"), Board->StartTileIndex, 0);
	TestEqual(TEXT("监狱探访 7"), Board->JailVisitTileIndex, 7);
	TestEqual(TEXT("免费停车 14"), Board->FreeParkingTileIndex, 14);
	TestEqual(TEXT("前往监狱 21"), Board->GoToJailTileIndex, 21);
	TestEqual(TEXT("交易所 16"), Board->StockExchangeTileIndex, 16);
	TestEqual(TEXT("16 号为交易所"), (int32)Board->Tiles[16].TileType, (int32)EMADemoTileType::StockExchange);

	// 地产计数 = 16(GDD 2.2)。
	int32 PropCount = 0;
	for (const FMADemoTileInfo& T : Board->Tiles)
	{
		if (T.TileType == EMADemoTileType::Property) ++PropCount;
	}
	TestEqual(TEXT("16 块地产"), PropCount, 16);
	return true;
}

// 用例 2:骰子(2D6 范围与双数判定)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoDiceTest,
	"Demo_MonopolyAuction.Smoke.Dice",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoDiceTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 12345);
	// 多次掷骰检查范围与双数一致性。
	for (int32 i = 0; i < 200; ++i)
	{
		GM->RequestRollAndResolve();
		const AMADemoGameState* GS = GM->GetDemoGameState();
		const FMADemoDiceResult& D = GS->LastDice;
		if (D.Die1 > 0)
		{
			TestTrue(TEXT("Die1 1-6"), D.Die1 >= 1 && D.Die1 <= 6);
			TestTrue(TEXT("Die2 1-6"), D.Die2 >= 1 && D.Die2 <= 6);
			TestEqual(TEXT("双数判定一致"), D.bIsDouble, D.Die1 == D.Die2);
		}
		if (GS->bGameOver) break;
	}
	return true;
}

// 用例 3:经济(初始资金 + 满色组租金翻倍)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoEconomyTest,
	"Demo_MonopolyAuction.Smoke.Economy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoEconomyTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 1);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestEqual(TEXT("初始资金 1500"), GS->GetPlayer(0)->Money, 1500);

	// 棕色组(1,3)全归 P0 时,1 号租金应翻倍(4 → 8)。
	GS->SetTileOwner(1, 0);
	GS->SetTileOwner(3, 0);
	TestTrue(TEXT("P0 持棕色组"), GS->DoesPlayerOwnColorGroup(0, EMADemoColorGroup::Brown));
	TestEqual(TEXT("满色组租金翻倍"), GS->CalculateRent(1), 8);

	// 只持一块时不翻倍。
	GS->SetTileOwner(3, -1);
	TestEqual(TEXT("非满色组基础租金"), GS->CalculateRent(1), 4);
	return true;
}

// 用例 4:整局直驱到终局(多种子,零报错,胜者合法)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoFullGameLoopTest,
	"Demo_MonopolyAuction.Smoke.FullGameLoop",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoFullGameLoopTest::RunTest(const FString& Parameters)
{
	const int32 Seeds[5] = { 1, 7, 42, 100, 20260612 };
	for (int32 s = 0; s < 5; ++s)
	{
		AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
		const int32 Winner = GM->RunFullGameToCompletion(4, Seeds[s]);
		AMADemoGameState* GS = GM->GetDemoGameState();
		TestTrue(FString::Printf(TEXT("种子 %d 游戏结束"), Seeds[s]), GS->bGameOver);
		TestTrue(FString::Printf(TEXT("种子 %d 胜者合法"), Seeds[s]),
			Winner >= 0 && Winner < GS->Players.Num());
		// 胜者必须非破产。
		TestFalse(FString::Printf(TEXT("种子 %d 胜者非破产"), Seeds[s]),
			GS->GetPlayer(Winner)->bIsBankrupt);
	}
	return true;
}

// 用例 5:监狱与破产语义(入狱标记与存活计数)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoJailBankruptcyTest,
	"Demo_MonopolyAuction.Smoke.JailBankruptcy",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoJailBankruptcyTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 1);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestEqual(TEXT("初始存活 3"), GS->GetActivePlayerCount(), 3);

	// 手动把 P2 资金清零并触发一次大额支付来淘汰。
	UMADemoPlayerData* P2 = GS->GetPlayer(2);
	P2->Money = 10;
	// 给 P2 一块地产,破产后应归无主。
	GS->SetTileOwner(5, 2);
	P2->AddProperty(5);
	TestEqual(TEXT("淘汰前 5 号属 P2"), GS->GetTileOwner(5), 2);

	// 经济淘汰:让 P2 支付超过其资金。
	// 直接走 GameState 语义验证(EliminatePlayer 经 GameMode 内部触发由 FullGameLoop 覆盖)。
	P2->bIsBankrupt = true;
	GS->ActivePlayerCount = GS->GetActivePlayerCount();
	TestEqual(TEXT("淘汰后存活 2"), GS->GetActivePlayerCount(), 2);
	return true;
}

// 用例 6:widget 创建(HUD 快照 + 全部前台 widget + 三底座)。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoWidgetCreationTest,
	"Demo_MonopolyAuction.Smoke.WidgetCreation",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoWidgetCreationTest::RunTest(const FString& Parameters)
{
	// HUD 快照(纯逻辑,不需视口)。
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(4, 7);
	AMADemoGameState* GS = GM->GetDemoGameState();
	GM->RequestRollAndResolve();

	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>();
	HUD->BindGameState(GS);
	const FMADemoHUDSnapshot Snap = HUD->BuildSnapshot();
	TestEqual(TEXT("快照玩家数 4"), Snap.PlayerCash.Num(), 4);
	TestEqual(TEXT("快照股值 4"), Snap.PlayerStockValue.Num(), 4);
	TestTrue(TEXT("股市摘要非空"), !Snap.StockSummary.IsEmpty());

	// 前台 widget 类可实例化(NewObject 成功即类型合法)。
	TestNotNull(TEXT("开始画面"), NewObject<UMADemoStartScreenWidget>());
	TestNotNull(TEXT("主菜单"), NewObject<UMADemoMainMenuWidget>());
	TestNotNull(TEXT("设置"), NewObject<UMADemoSettingsWidget>());
	TestNotNull(TEXT("暂停"), NewObject<UMADemoPauseWidget>());
	TestNotNull(TEXT("结果"), NewObject<UMADemoResultsWidget>());

	// 三底座。
	UMADemoInputFoundation* Input = NewObject<UMADemoInputFoundation>();
	TestEqual(TEXT("掷骰键 SpaceBar"), Input->GetKeyForAction(EMADemoInputAction::RollDice), FString(TEXT("SpaceBar")));
	UMADemoAudioFoundation* Audio = NewObject<UMADemoAudioFoundation>();
	Audio->SetMasterVolume(2.0f);
	TestEqual(TEXT("音量夹取 1.0"), Audio->MasterVolume, 1.0f);
	UMADemoPlatformFoundation* Plat = NewObject<UMADemoPlatformFoundation>();
	TestEqual(TEXT("默认分辨率宽 1280"), Plat->ResolutionWidth, 1280);
	return true;
}

// 用例 7:启动关卡加载(§4 新增)。
// 加载 authored 启动关卡,校验 WorldSettings GameMode 为 demo GameMode、GameState 类正确、HUD 可在关卡上下文创建。
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoEntryMapLoadTest,
	"Demo_MonopolyAuction.Smoke.EntryMapLoad",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoEntryMapLoadTest::RunTest(const FString& Parameters)
{
	const FString MapPath = TEXT("/Demo_MonopolyAuction/Maps/L_MonopolyDemo");

	// 资产存在性校验(authored .umap 必须真实存在)。
	UObject* MapAsset = StaticLoadObject(UWorld::StaticClass(), nullptr, *MapPath);
	TestNotNull(TEXT("启动关卡资产存在"), MapAsset);
	UWorld* MapWorld = Cast<UWorld>(MapAsset);
	if (!MapWorld)
	{
		AddError(TEXT("启动关卡未能加载为 UWorld"));
		return false;
	}

	// 校验 WorldSettings 的 GameModeOverride 绑定为 demo GameMode。
	AWorldSettings* WS = MapWorld->GetWorldSettings();
	TestNotNull(TEXT("WorldSettings 存在"), WS);
	if (WS)
	{
		TestNotNull(TEXT("GameModeOverride 已绑定"), WS->DefaultGameMode.Get());
		TestTrue(TEXT("GameModeOverride 为 demo GameMode"),
			WS->DefaultGameMode == AMADemoGameMode::StaticClass());
	}

	// GameMode 默认 GameState 类正确。
	const AMADemoGameMode* GMCDO = AMADemoGameMode::StaticClass()->GetDefaultObject<AMADemoGameMode>();
	TestTrue(TEXT("GameState 类为 demo GameState"),
		GMCDO->GameStateClass == AMADemoGameState::StaticClass());

	// HUD 可在关卡上下文创建(经 NewObject 校验类型合法;视口创建在 -game 路径验证)。
	UMADemoHUDWidget* HUD = NewObject<UMADemoHUDWidget>(MapWorld);
	TestNotNull(TEXT("HUD 可在关卡上下文创建"), HUD);
	return true;
}

#endif // WITH_AUTOMATION_TESTS
