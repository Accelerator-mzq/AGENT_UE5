// Copyright Phase15 presentation-2/3. 棋盘呈现实现用例(board-2d rung2-impl)。
// 名字空间 Demo_MonopolyAuction.PresentationImpl.Board2D.*
//
// *** supersedes 已激活(presentation-3 camera-integration,2026-06-14) ***
// rung3 story 按阶梯声明 supersedes 本文件(rung2-impl),以下变更已执行:
//   1. DrawBoard2D() 的 DrawHUD() 调用已从 MADemoHUD.cpp 移除(2D Canvas 棋盘退役)。
//   2. 2D Canvas 棋盘渲染实现(DrawBoard2D + token 2D 渲染)由 3D 棋盘/棋子完全接管。
//   3. 本文件各用例逐一评估:所有用例均属数据层验证(颜色配置/棋盘数据/API),
//      不直接调用 DrawBoard2D() 渲染——在 rung3 时代仍然成立,故予以保留。
//   4. 仅呈现渲染调用(DrawBoard2D)已退役;数据层验证(ColorPalette/BoardData/OwnerAPI/
//      TokenColor/TokenPosition)在 3D 棋盘中同样适用,继续通过。
//
// 注意:rung2-contract(MADemoPresentationRung2ContractTests.cpp)仍冻结不变。
#include "Misc/AutomationTest.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoPresentationConfig.h"
#include "MADemoDataAssets.h"
#include "MADemoTypes.h"
#include "UI/MADemoHUD.h"

#if WITH_AUTOMATION_TESTS

// -------------------------------------------------------------------------
// 实现 Board2D.HUDClassExists:AMADemoHUD 可实例化(Canvas HUD 入口存在)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplHUDClassTest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.HUDClassExists",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplHUDClassTest::RunTest(const FString& Parameters)
{
	// AMADemoHUD 可用 NewObject 创建(离线 - 无 World 上下文)。
	AMADemoHUD* HUD = NewObject<AMADemoHUD>();
	TestNotNull(TEXT("[HUDClass] AMADemoHUD 可实例化"), HUD);

	// AMADemoHUD 是 AHUD 子类(Canvas HUD 基类)。
	TestTrue(TEXT("[HUDClass] AMADemoHUD 是 AHUD 子类"), HUD->IsA<AHUD>());

	return true;
}

// -------------------------------------------------------------------------
// 实现 Board2D.ColorGroupPaletteValid:ColorGroupPalette 各色均不全黑(可见性)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplColorPaletteTest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.ColorGroupPaletteValid",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplColorPaletteTest::RunTest(const FString& Parameters)
{
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[Palette] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	// 验证 8 个颜色组配色都有可见亮度(至少一通道 > 0.05)。
	const int32 ExpectedGroups = 8; // None + 7 色组
	TestTrue(TEXT("[Palette] ColorGroupPalette 含 8 条"), Cfg->ColorGroupPalette.Num() >= ExpectedGroups);

	for (int32 i = 1; i < FMath::Min(Cfg->ColorGroupPalette.Num(), ExpectedGroups); ++i)
	{
		const FLinearColor& C = Cfg->ColorGroupPalette[i];
		const bool bVisible = C.R > 0.05f || C.G > 0.05f || C.B > 0.05f;
		TestTrue(FString::Printf(TEXT("[Palette] 色组 %d 可见"), i), bVisible);
	}

	// 玩家归属色 4 条各不相同(区分度)。
	TestTrue(TEXT("[Palette] PlayerOwnershipColors >= 4"), Cfg->PlayerOwnershipColors.Num() >= 4);
	if (Cfg->PlayerOwnershipColors.Num() >= 2)
	{
		const FLinearColor& P0Col = Cfg->PlayerOwnershipColors[0];
		const FLinearColor& P1Col = Cfg->PlayerOwnershipColors[1];
		const bool bDistinct =
			FMath::Abs(P0Col.R - P1Col.R) > 0.1f ||
			FMath::Abs(P0Col.G - P1Col.G) > 0.1f ||
			FMath::Abs(P0Col.B - P1Col.B) > 0.1f;
		TestTrue(TEXT("[Palette] P1/P2 归属色有区分"), bDistinct);
	}

	return true;
}

// -------------------------------------------------------------------------
// 实现 Board2D.BoardDataBuildDefault:UMADemoBoardDataAsset CDO 含 28 格可遍历。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplBoardDataTest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.BoardDataBuildDefault",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplBoardDataTest::RunTest(const FString& Parameters)
{
	// 创建独立棋盘数据资产,调 BuildDefaultBoard,验证铺出 28 格。
	UMADemoBoardDataAsset* Board = NewObject<UMADemoBoardDataAsset>();
	TestNotNull(TEXT("[BoardData] BoardDataAsset 可创建"), Board);
	if (!Board) return false;

	Board->BuildDefaultBoard();
	TestEqual(TEXT("[BoardData] BuildDefaultBoard 铺出 28 格"), Board->Tiles.Num(), 28);

	// 至少包含 Property 类型格。
	bool bHasProperty = false;
	for (const FMADemoTileInfo& T : Board->Tiles)
	{
		if (T.TileType == EMADemoTileType::Property) { bHasProperty = true; break; }
	}
	TestTrue(TEXT("[BoardData] 存在地产格"), bHasProperty);

	// 至少包含起点格(StartTileIndex 指向的格子)。
	TestTrue(TEXT("[BoardData] StartTileIndex 合法"), Board->StartTileIndex >= 0 && Board->StartTileIndex < 28);

	return true;
}

// -------------------------------------------------------------------------
// 实现 Board2D.TileOwnershipWriteRead:SetTileOwner/GetTileOwner 正确回读(rung2 特有 API 验证)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplOwnershipAPITest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.TileOwnershipWriteRead",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplOwnershipAPITest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(4, 2001);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[OwnerAPI] GameState 存在"), GS);
	if (!GS) return false;

	// 设置 4 名玩家各拥有一块地产,验证逐格回读正确。
	const int32 TileIndices[4] = { 1, 3, 6, 9 };
	for (int32 p = 0; p < 4; ++p)
	{
		GS->SetTileOwner(TileIndices[p], p);
	}

	for (int32 p = 0; p < 4; ++p)
	{
		TestEqual(FString::Printf(TEXT("[OwnerAPI] 格 %d 归属 P%d"), TileIndices[p], p + 1),
			GS->GetTileOwner(TileIndices[p]), p);
	}

	// 未设置的格仍为 -1(无主)。
	TestEqual(TEXT("[OwnerAPI] 格 2 无主"), GS->GetTileOwner(2), -1);
	TestEqual(TEXT("[OwnerAPI] 格 5 无主"), GS->GetTileOwner(5), -1);

	return true;
}

// -------------------------------------------------------------------------
// 实现 Board2D.AuctionHighlightConfig:TileAuctionHighlightColor 配置可达且为亮色。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplAuctionHighlightTest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.AuctionHighlightConfig",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplAuctionHighlightTest::RunTest(const FString& Parameters)
{
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[Highlight] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	// 拍卖高亮色要求:亮度足够(Luminance > 0.5 或单通道 > 0.7)。
	const FLinearColor& HC = Cfg->TileAuctionHighlightColor;
	const bool bBright = HC.R > 0.7f || HC.G > 0.7f || HC.B > 0.7f;
	TestTrue(TEXT("[Highlight] TileAuctionHighlightColor 亮度足够"), bBright);

	// 棋盘背景色比高亮色暗(确保对比度)。
	const FLinearColor& BgC = Cfg->BoardBgColor;
	const float BgLum = BgC.R * 0.2126f + BgC.G * 0.7152f + BgC.B * 0.0722f;
	const float HLum  = HC.R  * 0.2126f + HC.G  * 0.7152f + HC.B  * 0.0722f;
	TestTrue(TEXT("[Highlight] 高亮色比棋盘背景亮"), HLum > BgLum);

	return true;
}

// -------------------------------------------------------------------------
// 实现 Board2D.TokenColorDistinct:玩家 token 配色各不相同(P1/P2/P3/P4 区分度)。
// board-tokens rung2 story:每个 token 应有独立可辨的颜色。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplTokenColorTest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.TokenColorDistinct",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplTokenColorTest::RunTest(const FString& Parameters)
{
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[TokenColor] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	// 至少 4 个玩家归属色(token 复用 PlayerOwnershipColors)。
	TestTrue(TEXT("[TokenColor] PlayerOwnershipColors >= 4"), Cfg->PlayerOwnershipColors.Num() >= 4);

	// 相邻玩家间颜色有明显区分(至少一通道差 > 0.15)。
	for (int32 i = 0; i + 1 < FMath::Min(Cfg->PlayerOwnershipColors.Num(), 4); ++i)
	{
		const FLinearColor& A = Cfg->PlayerOwnershipColors[i];
		const FLinearColor& B = Cfg->PlayerOwnershipColors[i + 1];
		const bool bDistinct =
			FMath::Abs(A.R - B.R) > 0.15f ||
			FMath::Abs(A.G - B.G) > 0.15f ||
			FMath::Abs(A.B - B.B) > 0.15f;
		TestTrue(FString::Printf(TEXT("[TokenColor] P%d/P%d token 颜色有区分"), i + 1, i + 2), bDistinct);
	}

	// 每个 token 颜色有足够亮度(可在棋盘深色背景上可见,至少一通道 > 0.2)。
	for (int32 i = 0; i < FMath::Min(Cfg->PlayerOwnershipColors.Num(), 4); ++i)
	{
		const FLinearColor& C = Cfg->PlayerOwnershipColors[i];
		const bool bVisible = C.R > 0.2f || C.G > 0.2f || C.B > 0.2f;
		TestTrue(FString::Printf(TEXT("[TokenColor] P%d token 颜色可见"), i + 1), bVisible);
	}

	return true;
}

// -------------------------------------------------------------------------
// 实现 Board2D.TokenPositionAfterMove:掷骰后 CurrentTileIndex 更新,token 应跟随新位置。
// board-tokens rung2 story:回合推进(Space→掷骰)后玩家位置从 GameState 可读到新格。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard2DImplTokenMoveTest,
	"Demo_MonopolyAuction.PresentationImpl.Board2D.TokenPositionAfterMove",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard2DImplTokenMoveTest::RunTest(const FString& Parameters)
{
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 2100);
	GM->StartTurn();
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[TokenMove] GameState 存在"), GS);
	if (!GS) return false;

	// 记录初始位置。
	const UMADemoPlayerData* P0 = GS->GetPlayer(0);
	TestNotNull(TEXT("[TokenMove] P0 数据存在"), P0);
	if (!P0) return false;

	const int32 InitTile = P0->CurrentTileIndex;

	// 触发掷骰(等价于 Space 键意图 → RequestRollAndResolve)。
	TestEqual(TEXT("[TokenMove] 初始阶段为 WaitingForRoll"),
		(int32)GS->TurnPhase, (int32)EMADemoTurnPhase::WaitingForRoll);
	GM->RequestRollAndResolve();

	// 掷骰后骰子有效(Die1 > 0)。
	TestTrue(TEXT("[TokenMove] 骰子有效(Die1>0)"), GS->LastDice.Die1 > 0);

	// P0 的 CurrentTileIndex 已更新(≥ InitTile,骰子步数 ≥ 2)。
	const int32 NewTile = P0->CurrentTileIndex;
	// 骰子至少 2(1+1),所以新位置应该不同(除非骰子结果为 0,正常骰面最小 2)。
	const int32 DiceSum = GS->LastDice.Sum();
	TestEqual(TEXT("[TokenMove] token 位置已移动到骰子步数对应格"),
		NewTile, (InitTile + DiceSum) % 28);

	// 新 token 位置在棋盘合法范围内(0~27)。
	TestTrue(TEXT("[TokenMove] 新 token 位置在棋盘范围"), NewTile >= 0 && NewTile < 28);

	return true;
}

#endif // WITH_AUTOMATION_TESTS
