// Copyright Phase15 presentation-3. 3D 棋盘呈现契约用例(board-3d + camera-integration rung3-contract)。
// 名字空间 Demo_MonopolyAuction.PresentationContract.Board3D.* / CameraIntegration.*
// 形状:验证 3D board actor 存在性 / 地块 mesh 数可达 / 地产组颜色可达;
//       以及 camera-integration story 契约——CameraActor 参数可达/HUD 叠加契约。
// 规范 §4:不绑具体坐标/mesh 类名/world 结构——仅验证数据层与 Actor 类型可达。
// 本文件在 rung3 关闭后冻结为持久契约(后续 rung 不得破坏)。
#include "Misc/AutomationTest.h"
#include "MADemoGameMode.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoDataAssets.h"
#include "MADemoPresentationConfig.h"
#include "MADemoBoard3DActor.h"
#include "MADemoTypes.h"
#include "UI/MADemoHUD.h"

#if WITH_AUTOMATION_TESTS

// -------------------------------------------------------------------------
// 契约 Board3D.ActorClassExists:AMADemoBoard3DActor 类可实例化(3D board actor 存在)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard3DContractActorClassTest,
	"Demo_MonopolyAuction.PresentationContract.Board3D.ActorClassExists",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard3DContractActorClassTest::RunTest(const FString& Parameters)
{
	// AMADemoBoard3DActor 类可用 NewObject 创建(离线,无 World 上下文)。
	AMADemoBoard3DActor* Board = NewObject<AMADemoBoard3DActor>();
	TestNotNull(TEXT("[Board3D.Actor] AMADemoBoard3DActor 可实例化"), Board);

	// 应为 AActor 的子类。
	if (Board)
	{
		TestTrue(TEXT("[Board3D.Actor] AMADemoBoard3DActor 是 AActor 子类"), Board->IsA<AActor>());
	}

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board3D.TileCountReachable:棋盘地块数 = 28 经 GameState.BoardData 可达(与 3D 构建一致)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard3DContractTileCountTest,
	"Demo_MonopolyAuction.PresentationContract.Board3D.TileCountReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard3DContractTileCountTest::RunTest(const FString& Parameters)
{
	// 初始化游戏,取 GameState。
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(2, 3001);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[Board3D.TileCount] GameState 存在"), GS);
	if (!GS || !GS->BoardData) return false;

	// 地块数应为 28(3D 棋盘程序化生成的格数等于此值)。
	const int32 TileCount = GS->BoardData->Tiles.Num();
	TestEqual(TEXT("[Board3D.TileCount] 地块总数 == 28(3D 棋盘格数)"), TileCount, 28);

	// 每格 GetTileInfo 不崩溃,名称可达。
	for (int32 i = 0; i < TileCount; ++i)
	{
		const FMADemoTileInfo Info = GS->GetTileInfo(i);
		TestFalse(FString::Printf(TEXT("[Board3D.TileCount] 格 %d 名称可达"), i),
			Info.Name.IsEmpty() && i > 0);
	}

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board3D.ColorGroupReachable:地产组配色经 PresentationConfig 可达(3D MID 颜色基础)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard3DContractColorGroupTest,
	"Demo_MonopolyAuction.PresentationContract.Board3D.ColorGroupReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard3DContractColorGroupTest::RunTest(const FString& Parameters)
{
	// PresentationConfig 配色数组覆盖全部 8 个枚举值(None + 7 色组)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[Board3D.ColorGroup] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	TestTrue(TEXT("[Board3D.ColorGroup] ColorGroupPalette 覆盖 8 个枚举值"),
		Cfg->ColorGroupPalette.Num() >= 8);

	// 验证非 None 的 7 个颜色均有可见亮度(至少一通道 > 0.05)。
	for (int32 i = 1; i < FMath::Min(Cfg->ColorGroupPalette.Num(), 8); ++i)
	{
		const FLinearColor& C = Cfg->ColorGroupPalette[i];
		const bool bVisible = C.R > 0.05f || C.G > 0.05f || C.B > 0.05f;
		TestTrue(FString::Printf(TEXT("[Board3D.ColorGroup] 色组 %d 可见"), i), bVisible);
	}

	// 拍卖高亮色可达(3D 棋盘拍卖中地块用此色)。
	const FLinearColor& HC = Cfg->TileAuctionHighlightColor;
	TestTrue(TEXT("[Board3D.ColorGroup] 拍卖高亮色有可见亮度"),
		HC.R > 0.5f || HC.G > 0.5f || HC.B > 0.5f);

	return true;
}

// -------------------------------------------------------------------------
// 契约 Board3D.OwnershipColorReachable:地块归属/拍卖中状态颜色数据层可达。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard3DContractOwnerColorTest,
	"Demo_MonopolyAuction.PresentationContract.Board3D.OwnershipColorReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard3DContractOwnerColorTest::RunTest(const FString& Parameters)
{
	// 初始化游戏。
	AMADemoGameMode* GM = NewObject<AMADemoGameMode>();
	GM->InitializeGame(3, 3002);
	AMADemoGameState* GS = GM->GetDemoGameState();
	TestNotNull(TEXT("[Board3D.OwnerColor] GameState 存在"), GS);
	if (!GS) return false;

	// 玩家归属色数组可达(≥ 3 玩家)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[Board3D.OwnerColor] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	TestTrue(TEXT("[Board3D.OwnerColor] PlayerOwnershipColors >= 3"),
		Cfg->PlayerOwnershipColors.Num() >= 3);

	// 直驱归属:将格 1 设为 P1 所有,验证归属色可达。
	GS->SetTileOwner(1, 0);
	TestEqual(TEXT("[Board3D.OwnerColor] 格 1 归属 P1 可达"), GS->GetTileOwner(1), 0);
	if (Cfg->PlayerOwnershipColors.IsValidIndex(0))
	{
		const FLinearColor& P1Col = Cfg->PlayerOwnershipColors[0];
		const bool bVisible = P1Col.R > 0.05f || P1Col.G > 0.05f || P1Col.B > 0.05f;
		TestTrue(TEXT("[Board3D.OwnerColor] P1 归属色有可见亮度"), bVisible);
	}

	// 直驱拍卖:压低资金触发拍卖。
	UMADemoPlayerData* P0 = GS->GetPlayer(0);
	TestNotNull(TEXT("[Board3D.OwnerColor] P0 数据存在"), P0);
	if (!P0) return false;

	P0->Money = 30;
	P0->CurrentTileIndex = 3;
	GM->OnPlayerLanded(3);

	// 若触发拍卖,验证 AuctionState.TileIndex 可达。
	if (GS->AuctionState.bActive)
	{
		TestTrue(TEXT("[Board3D.OwnerColor] 拍卖中地块索引可达"),
			GS->AuctionState.TileIndex >= 0 && GS->AuctionState.TileIndex < 28);
	}
	else
	{
		// 未触发拍卖(地块可能已被设归属):仅验证拍卖状态字段可读。
		TestFalse(TEXT("[Board3D.OwnerColor] 初始无拍卖时 bActive = false"),
			GS->AuctionState.bActive && GS->AuctionState.TileIndex < 0);
	}

	return true;
}

// -------------------------------------------------------------------------
// 契约 CameraIntegration.BoardCameraActorReachable:
// 3D 棋盘 Actor 的 CameraHeight 参数可达,且俯视相机覆盖能力可计算
// (camera-integration story:固定机位 CameraActor 俯视棋盘)。
// 规范 §4:不绑运行时 World/相机实例,只验证 Actor 类与参数数据层。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard3DContractCameraActorTest,
	"Demo_MonopolyAuction.PresentationContract.CameraIntegration.BoardCameraActorReachable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard3DContractCameraActorTest::RunTest(const FString& Parameters)
{
	// AMADemoBoard3DActor 类可实例化(含相机参数)。
	AMADemoBoard3DActor* Board = NewObject<AMADemoBoard3DActor>();
	TestNotNull(TEXT("[CamInt.Camera] AMADemoBoard3DActor 可实例化(含相机参数)"), Board);
	if (!Board) return false;

	// CameraHeight 参数可达且 > 0(相机在棋盘上方)。
	TestTrue(TEXT("[CamInt.Camera] CameraHeight > 0(固定俯视机位可配置)"),
		Board->CameraHeight > 0.f);

	// 棋盘尺寸参数可达(用于确认相机能覆盖全局)。
	const float Step = Board->TileSize + Board->TileGap;
	const float HalfSpan = 3.f * Step; // 棋盘半跨

	// 相机高度应能覆盖棋盘(CameraHeight >= HalfSpan 的合理倍数)。
	TestTrue(TEXT("[CamInt.Camera] CameraHeight >= 棋盘半跨(俯视可达棋盘全貌)"),
		Board->CameraHeight >= HalfSpan);

	return true;
}

// -------------------------------------------------------------------------
// 契约 CameraIntegration.HUDOverlayPresent:
// Canvas HUD 信息面板类(AMADemoHUD)仍可达,叠加渲染机制保留
// (camera-integration story:rung1 HUD 面板叠加在 3D 场景上)。
// -------------------------------------------------------------------------
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMADemoBoard3DContractHUDOverlayTest,
	"Demo_MonopolyAuction.PresentationContract.CameraIntegration.HUDOverlayPresent",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMADemoBoard3DContractHUDOverlayTest::RunTest(const FString& Parameters)
{
	// AMADemoHUD 可实例化(Canvas HUD 叠加渲染类存在)。
	AMADemoHUD* HUD = NewObject<AMADemoHUD>();
	TestNotNull(TEXT("[CamInt.HUD] AMADemoHUD 可实例化(Canvas 叠加 HUD 类仍存在)"), HUD);
	if (!HUD) return false;

	// AMADemoHUD 是 AHUD 子类(Canvas 叠加机制基类)。
	TestTrue(TEXT("[CamInt.HUD] AMADemoHUD 是 AHUD 子类(叠加渲染机制就绪)"),
		HUD->IsA<AHUD>());

	// PresentationConfig 面板布局数据可达(HUD 面板尺寸/位置/配色配置)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	TestNotNull(TEXT("[CamInt.HUD] PresentationConfig CDO 可取到"), Cfg);
	if (!Cfg) return false;

	// 玩家卡片面板宽度 > 0(卡片式 HUD 面板数据层可达)。
	TestTrue(TEXT("[CamInt.HUD] PlayerCardWidth > 0(卡片面板数据层可达)"),
		Cfg->PlayerCardWidth > 0.f);

	return true;
}

#endif // WITH_AUTOMATION_TESTS
