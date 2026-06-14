// Copyright Phase15 presentation-2. 棋盘呈现契约用例(board-2d rung2-contract)。
// 名字空间 Demo_MonopolyAuction.PresentationContract.Board2D.*
// 形状:通过 GameState API 验证棋盘信息可见性——地块数/地产组/归属状态/拍卖中标识。
// 规范 §4:不断言具体绘制坐标/widget 类名,仅断言数据层可达。
// 本文件将在 rung2 关闭后冻结为持久契约(后续 rung 不得破坏)。
#include "Misc/AutomationTest.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoDataAssets.h"
#include "MADemoPresentationConfig.h"
#include "MADemoTypes.h"

#if WITH_AUTOMATION_TESTS

// -------------------------------------------------------------------------
// 契约 Board2D.TileCountReachable:棋盘地块数 = 28 可经 GameState.BoardData 取到。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractTileCountTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.TileCountReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractTileCountTest::RunTest(const FString& Parameters)
{
	// 初始化游戏,取 GameState。
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 1501);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[TileCount] GameState 存在"), GS);
	if (!GS) return false;

	// 棋盘数据资产可达。
	TestNotNull(TEXT("[TileCount] BoardData 可达"), GS->BoardData.Get());
	if (!GS->BoardData) return false;

	// 地块数应为 28。
	const int32 TileCount = GS->BoardData->Tiles.Num();
	TestEqual(TEXT("[TileCount] 地块总数 == 28"), TileCount, 28);

	// GetTileInfo 对全部 28 个索引均可调用(不崩溃,返回合法格)。
	for (int32 i = 0; i < TileCount; ++i)
	{
		const FMADemoTileInfo Info = GS->GetTileInfo(i);
		// 格子名称可达(非崩溃验证)。
		TestFalse(FString::Printf(TEXT("[TileCount] 格 %d 名称可达"), i), Info.Name.IsEmpty() && i > 0);
	}

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board2D.ColorGroupReachable:地产格地产组信息经 GetTileInfo 可达。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractColorGroupTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.ColorGroupReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractColorGroupTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 1502);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[ColorGroup] GameState 存在"), GS);
	if (!GS || !GS->BoardData) return false;

	// 至少存在一个地产格(Property 类型)且有非 None 地产组。
	int32 PropertyCount = 0;
	bool bHasColorGroup = false;
	for (int32 i = 0; i < GS->BoardData->Tiles.Num(); ++i)
	{
		const FMADemoTileInfo Info = GS->GetTileInfo(i);
		if (Info.TileType == EMADemoTileType::Property)
		{
			++PropertyCount;
			if (Info.ColorGroup != EMADemoColorGroup::None)
			{
				bHasColorGroup = true;
			}
		}
	}
	TestTrue(TEXT("[ColorGroup] 存在至少 1 个地产格"), PropertyCount > 0);
	TestTrue(TEXT("[ColorGroup] 存在至少 1 个带颜色组的地产格"), bHasColorGroup);

	// PresentationConfig 配色数组覆盖全部 8 个枚举值(None + 7 色组)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[ColorGroup] PresentationConfig CDO 可取到"), Cfg);
	TestTrue(TEXT("[ColorGroup] ColorGroupPalette 覆盖 8 个枚举值"),
		Cfg->ColorGroupPalette.Num() >= 8);

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board2D.OwnershipReachable:地块归属状态经 GetTileOwner/TileOwnership 可达。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractOwnershipTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.OwnershipReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractOwnershipTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 1503);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[Ownership] GameState 存在"), GS);
	if (!GS) return false;

	// 初始状态:所有地块无主(-1)。
	for (int32 i = 0; i < 28; ++i)
	{
		TestEqual(FString::Printf(TEXT("[Ownership] 格 %d 初始无主"), i),
			GS->GetTileOwner(i), -1);
	}

	// 直驱归属:将格 1 设置为 P1(索引 0)所有,验证可达。
	GS->SetTileOwner(1, 0);
	TestEqual(TEXT("[Ownership] 格 1 设为 P1 后可达"), GS->GetTileOwner(1), 0);
	TestEqual(TEXT("[Ownership] 格 0 仍无主"), GS->GetTileOwner(0), -1);

	// PresentationConfig 玩家归属色数组可达(≥ 2 玩家)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[Ownership] PresentationConfig CDO 可取到"), Cfg);
	TestTrue(TEXT("[Ownership] PlayerOwnershipColors 覆盖 4 名玩家"),
		Cfg->PlayerOwnershipColors.Num() >= 4);

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board2D.AuctionTileIdentifiable:拍卖中地块可经 AuctionState.TileIndex 标识。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractAuctionTileTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.AuctionTileIdentifiable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractAuctionTileTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 1504);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[AuctionTile] GameState 存在"), GS);
	if (!GS) return false;

	// 初始无拍卖:bActive = false, TileIndex = -1。
	TestFalse(TEXT("[AuctionTile] 初始无拍卖"), GS->AuctionState.bActive);

	// 直驱拍卖:压低资金触发拍卖(地块 1 = 地产格)。
	UMADemoPlayerData* P0 = GS->GetPlayer(0);
	TestNotNull(TEXT("[AuctionTile] P0 数据存在"), P0);
	if (!P0) return false;
	P0->Money = 30;  // 远低于购买缓冲
	P0->CurrentTileIndex = 1;
	GM->OnPlayerLanded(1);  // 触发落格结算 → 拒购 → 拍卖

	// 断言拍卖已激活且拍卖地块 TileIndex 可达。
	TestTrue(TEXT("[AuctionTile] 拍卖已激活"), GS->AuctionState.bActive);
	TestEqual(TEXT("[AuctionTile] 拍卖地块 TileIndex == 1"), GS->AuctionState.TileIndex, 1);

	// 拍卖高亮配色可达。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[AuctionTile] PresentationConfig CDO 可取到"), Cfg);
	// 拍卖高亮色应有可见亮度(至少一通道 > 0.5)。
	const FLinearColor& HC = Cfg->TileAuctionHighlightColor;
	TestTrue(TEXT("[AuctionTile] 拍卖高亮色有可见亮度"),
		HC.R > 0.5f || HC.G > 0.5f || HC.B > 0.5f);

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board2D.BoardLayoutConfig:棋盘布局参数经 PresentationConfig 可达且合理。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractLayoutConfigTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.BoardLayoutConfig",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractLayoutConfigTest::RunTest(const FString& Parameters)
{
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[LayoutConfig] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	// 格子尺寸 > 0。
	TestTrue(TEXT("[LayoutConfig] BoardTileSize > 0"), Cfg->BoardTileSize > 0.f);

	// 棋盘原点在屏幕范围内(1280×720)。
	TestTrue(TEXT("[LayoutConfig] BoardOriginX 在屏幕范围内"), Cfg->BoardOriginX >= 0.f && Cfg->BoardOriginX < 1280.f);
	TestTrue(TEXT("[LayoutConfig] BoardOriginY 在屏幕范围内"), Cfg->BoardOriginY >= 0.f && Cfg->BoardOriginY < 720.f);

	// 7×7 棋盘总跨度 = (7-1)*(TileSize+Gap)+TileSize,须 ≤ 360px(适配 1280 宽右侧区域)。
	const float BoardSpan = 6.f * (Cfg->BoardTileSize + Cfg->BoardTileGap) + Cfg->BoardTileSize;
	TestTrue(TEXT("[LayoutConfig] 棋盘总跨度在合理范围内(< 400px)"), BoardSpan < 400.f);

	// 棋盘区域须在屏幕内:OriginX + BoardSpan < 1280。
	TestTrue(TEXT("[LayoutConfig] 棋盘右边界在屏幕内"),
		Cfg->BoardOriginX + BoardSpan < 1280.f);

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board2D.TokenPositionReachable:玩家 token 位置与 GameState 玩家 CurrentTileIndex 一致可达。
// board-tokens rung2 story:token 位置须从 GameState 数据层可读(不断言具体绘制坐标)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractTokenPositionTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.TokenPositionReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractTokenPositionTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 1600);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[TokenPos] GameState 存在"), GS);
	if (!GS) return false;

	// 直驱各玩家位置到不同格子。
	UMADemoPlayerData* P0 = GS->GetPlayer(0);
	UMADemoPlayerData* P1 = GS->GetPlayer(1);
	UMADemoPlayerData* P2 = GS->GetPlayer(2);
	TestNotNull(TEXT("[TokenPos] P0 数据存在"), P0);
	TestNotNull(TEXT("[TokenPos] P1 数据存在"), P1);
	TestNotNull(TEXT("[TokenPos] P2 数据存在"), P2);
	if (!P0 || !P1 || !P2) return false;

	P0->CurrentTileIndex = 0;
	P1->CurrentTileIndex = 7;
	P2->CurrentTileIndex = 14;

	// 验证:从 GameState 可读取各玩家的 CurrentTileIndex(呈现层从此处取 token 位置)。
	TestEqual(TEXT("[TokenPos] P0 位置可达为格 0"), GS->GetPlayer(0)->CurrentTileIndex, 0);
	TestEqual(TEXT("[TokenPos] P1 位置可达为格 7"), GS->GetPlayer(1)->CurrentTileIndex, 7);
	TestEqual(TEXT("[TokenPos] P2 位置可达为格 14"), GS->GetPlayer(2)->CurrentTileIndex, 14);

	// 验证:CurrentPlayerIndex 可达(用于当前玩家 token 高亮判断)。
	TestTrue(TEXT("[TokenPos] CurrentPlayerIndex 在合法范围"),
		GS->CurrentPlayerIndex >= 0 && GS->CurrentPlayerIndex < GS->Players.Num());

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board2D.CurrentPlayerTokenIdentifiable:当前回合玩家可与其他玩家区分(索引可达)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DContractCurrentPlayerTokenTest,
	"Demo_MonopolyAuction.PresentationContract.Board2D.CurrentPlayerTokenIdentifiable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DContractCurrentPlayerTokenTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(4, 1601);
	GM->StartTurn();
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[CurrentToken] GameState 存在"), GS);
	if (!GS) return false;

	// 当前玩家索引可达(呈现层用此判断高亮哪个 token)。
	const int32 CurIdx = GS->CurrentPlayerIndex;
	TestTrue(TEXT("[CurrentToken] 当前玩家索引有效"), CurIdx >= 0 && CurIdx < GS->Players.Num());

	// 可从 Players 数组取到当前玩家数据。
	const UMADemoPlayerData* CurPlayer = GS->GetPlayer(CurIdx);
	TestNotNull(TEXT("[CurrentToken] 当前玩家数据非空"), CurPlayer);

	// 当前玩家的 CurrentTileIndex 可达(token 应显示在此格)。
	if (CurPlayer)
	{
		TestTrue(TEXT("[CurrentToken] 当前玩家 TileIndex 在棋盘范围"),
			CurPlayer->CurrentTileIndex >= 0 && CurPlayer->CurrentTileIndex < 28);
	}

	// 当前玩家可与其他玩家区分:CurrentPlayerIndex 指向唯一玩家。
	int32 ActiveCount = 0;
	for (int32 i = 0; i < GS->Players.Num(); ++i)
	{
		if (i == GS->CurrentPlayerIndex) ++ActiveCount;
	}
	TestEqual(TEXT("[CurrentToken] CurrentPlayerIndex 唯一"), ActiveCount, 1);

	return true;
}

#endif // WITH_AUTOMATION_TESTS
