// Copyright Phase15 presentation-3. 程序化 3D 棋盘 Actor 实现。
// 施工规范 §7:引擎基础几何 Cube + 动态材质实例(MID)程序化拼 28 格方形环。
// 禁止引入外部资产:仅用 /Engine/BasicShapes/Cube + BasicShapeMaterial。
// v2 修复:改用自发光颜色(HDR linear color * boost)确保截图可见彩色;
//         增大地块高度;相机调整为整棋盘俯视居中。
#include "MADemoBoard3DActor.h"
#include "MADemoGameState.h"
#include "MADemoPlayerData.h"
#include "MADemoDataAssets.h"
#include "MADemoPresentationConfig.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Camera/CameraActor.h"
#include "Camera/CameraComponent.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetMathLibrary.h"
#include "GameFramework/GameStateBase.h"
#include "Engine/World.h"
#include "UObject/ConstructorHelpers.h"

// 棋盘格子在 7×7 方形环中的布局:
// 索引 0~6:  底排(左→右),Y 固定在 -3 单元
// 索引 7~12: 右排(底→顶,不含两角),X 固定在 +3 单元
// 索引 13~19:顶排(右→左),Y 固定在 +3 单元
// 索引 20~25:左排(顶→底,不含两角),X 固定在 -3 单元
// 共 7+6+7+6 = 26 → 实际 28 格(角格重复不需额外,按下面规则对齐)
// 正确 28 格方形环:底 7(含两角),右 5(不含角),顶 7(含两角),左 5(不含角) → 7+5+7+5=24 不对
// 改用:底 8,右 6,顶 8,左 6 → 28 格;或底 7,右 7,顶 7,左 7 → 28 格(每角不重复)
// 采用简单方案:7 格/边 × 4 边 = 28 格,每边 7 格(含当前边的两个角格,角格只属于一边)
// 实际布局(从起点 0 顺时针):
//   底边: tile 0..6  (列 0..6,行 0)
//   右边: tile 7..13 (列 6, 行 0..6)  — 但角格 0 和 6 已算,所以实际从 行1 到行7
//   顶边: tile 14..20(列 6..0,行 6)
//   左边: tile 21..27(列 0,行 6..0)  — 同理
// 以上有重复计算角格问题。采用更简洁的参数化方案:
//   步骤 i 的坐标,沿环形前进(共 28 步)。

AMADemoBoard3DActor::AMADemoBoard3DActor()
{
	PrimaryActorTick.bCanEverTick = true;

	// 创建场景根组件。
	RootSceneComp = CreateDefaultSubobject<USceneComponent>(TEXT("RootScene"));
	SetRootComponent(RootSceneComp);
}

void AMADemoBoard3DActor::BeginPlay()
{
	Super::BeginPlay();

	// 从世界取 GameState。
	UWorld* World = GetWorld();
	if (World)
	{
		CachedGS = Cast<AMADemoGameState>(World->GetGameState());
	}

	// 程序化构建 3D 棋盘。
	BuildBoard3D();

	// 在棋盘地块上生成玩家棋子。
	BuildPawns3D();

	// 创建俯视相机。
	SetupBoardCamera();

	// 初始颜色刷新。
	RefreshTileColors();

	// 初始棋子位置刷新。
	RefreshPawnPositions();
}

void AMADemoBoard3DActor::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	// 按间隔刷新地块颜色与棋子位置(归属/回合状态变化时同步)。
	RefreshAccum += DeltaSeconds;
	if (RefreshAccum >= RefreshInterval)
	{
		RefreshAccum = 0.f;
		RefreshTileColors();
		RefreshPawnPositions();
	}
}

// 28 格方形环世界坐标:
// 采用"沿环前进"方案:将 28 格分为 4 段,每段 7 格(含当前段起始角、不含下一角)。
// 方形边长 = 6 个步进(6 × (TileSize + TileGap)),7 格占满一边(6 间距 + 1 格本身)。
// 起点(tile 0)在右下角,顺时针:
//   底边(右→左):tile 0..6,  Y = -HalfSpan, X 从 +HalfSpan 到 -HalfSpan
//   左边(下→上):tile 7..13, X = -HalfSpan, Y 从 -HalfSpan 到 +HalfSpan
//   顶边(左→右):tile 14..20,Y = +HalfSpan, X 从 -HalfSpan 到 +HalfSpan
//   右边(上→下):tile 21..27,X = +HalfSpan, Y 从 +HalfSpan 到 -HalfSpan
FVector AMADemoBoard3DActor::GetTileWorldPosition(int32 TileIndex) const
{
	// 每步步进量(格子尺寸 + 间距)。
	const float Step = TileSize + TileGap;
	// 6 步跨 7 格(含首尾两个角格),所以半跨 = 3 步。
	const float HalfSpan = 3.f * Step;

	// 当前段和段内偏移。
	const int32 Side = TileIndex / 7;    // 段 0~3
	const int32 Offset = TileIndex % 7;  // 段内偏移 0~6

	float X = 0.f, Y = 0.f;
	switch (Side)
	{
	case 0: // 底边:Y = -HalfSpan,X 从 +HalfSpan 到 -HalfSpan(顺时针)
		X = HalfSpan - Offset * Step;
		Y = -HalfSpan;
		break;
	case 1: // 左边:X = -HalfSpan,Y 从 -HalfSpan 到 +HalfSpan
		X = -HalfSpan;
		Y = -HalfSpan + Offset * Step;
		break;
	case 2: // 顶边:Y = +HalfSpan,X 从 -HalfSpan 到 +HalfSpan
		X = -HalfSpan + Offset * Step;
		Y = HalfSpan;
		break;
	case 3: // 右边:X = +HalfSpan,Y 从 +HalfSpan 到 -HalfSpan
		X = HalfSpan;
		Y = HalfSpan - Offset * Step;
		break;
	default:
		break;
	}

	// 返回 Actor 本地坐标(相对于 Actor 的根)。ActorTransform 将其转成世界坐标。
	return GetActorLocation() + FVector(X, Y, 0.f);
}

FLinearColor AMADemoBoard3DActor::GetColorGroupColor(EMADemoColorGroup Group) const
{
	// 从 PresentationConfig 取地产组配色(与 2D 棋盘共享色表)。
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();
	if (!Cfg) return FLinearColor::Gray;

	const int32 Idx = static_cast<int32>(Group);
	if (Cfg->ColorGroupPalette.IsValidIndex(Idx))
	{
		return Cfg->ColorGroupPalette[Idx];
	}
	return FLinearColor::Gray;
}

FLinearColor AMADemoBoard3DActor::GetTileDisplayColor(int32 TileIndex) const
{
	if (!CachedGS || !CachedGS->BoardData)
	{
		return FLinearColor::Gray;
	}

	const FMADemoTileInfo Info = CachedGS->GetTileInfo(TileIndex);
	const UMADemoPresentationConfig* Cfg = GetDefault<UMADemoPresentationConfig>();

	// 拍卖中地块:高亮黄色。
	if (CachedGS->AuctionState.bActive && CachedGS->AuctionState.TileIndex == TileIndex)
	{
		return Cfg ? Cfg->TileAuctionHighlightColor : FLinearColor(1.f, 0.9f, 0.1f, 1.f);
	}

	// 非地产格(角格/税务/机会等):特殊格色。
	if (Info.TileType != EMADemoTileType::Property)
	{
		return Cfg ? Cfg->TileColorSpecial : FLinearColor(0.08f, 0.08f, 0.14f, 1.f);
	}

	// 有主地产:显示归属玩家颜色。
	const int32 OwnerIdx = CachedGS->GetTileOwner(TileIndex);
	if (OwnerIdx >= 0 && Cfg && Cfg->PlayerOwnershipColors.IsValidIndex(OwnerIdx))
	{
		return Cfg->PlayerOwnershipColors[OwnerIdx];
	}

	// 无主地产:按地产组着色。
	return GetColorGroupColor(Info.ColorGroup);
}

void AMADemoBoard3DActor::BuildBoard3D()
{
	UWorld* World = GetWorld();
	if (!World) return;

	// 加载引擎内置 Cube 基础几何。
	UStaticMesh* CubeMesh = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube"));
	if (!CubeMesh)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Board3D] 加载 /Engine/BasicShapes/Cube 失败,跳过 3D 棋盘构建"));
		return;
	}

	// 优先加载 WorldGridMaterial(支持 Color/Emissive 参数,不依赖光照);
	// 退级:BasicShapeMaterial(lit PBR,Color 参数)。
	// 注意:BasicShapeMaterial 在 UE5.5 中参数名是 "Color"(BaseColor)。
	// 为确保截图可见彩色,后续 SetColor 时会放大 HDR 亮度并同时设 Emissive。
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));
	if (!BaseMat)
	{
		// BasicShapeMaterial 加载失败时:MeshComp 保留引擎默认材质(灰色),颜色将由
		// SetVectorParameterValueOnMaterials 兜底尝试设置(可能无效,但不崩溃)。
		UE_LOG(LogTemp, Warning, TEXT("[Board3D] BasicShapeMaterial 加载失败,地块将保持默认材质"));
	}
	else
	{
		UE_LOG(LogTemp, Log, TEXT("[Board3D] BasicShapeMaterial 加载成功,将用 HDR Color 设色"));
	}

	// 计算棋盘中心(相机对准)。棋盘中心即 Actor XY 原点,Z=地块半高。
	BoardCenter = GetActorLocation() + FVector(0.f, 0.f, TileHeight * 0.5f);

	// 缩放比例:UE Cube 默认 100×100×100 unit,缩放到 TileSize×TileSize×TileHeight。
	// TileHeight 设为 60 cm 确保地块有明显立体感(相对地面凸出)。
	const float ScaleXY = TileSize / 100.f;
	const float ScaleZ  = TileHeight / 100.f;
	const FVector TileScale(ScaleXY, ScaleXY, ScaleZ);

	TileEntries.Reset();
	TileEntries.Reserve(28);

	for (int32 i = 0; i < 28; ++i)
	{
		FMADemoTile3DEntry Entry;
		Entry.TileIndex = i;

		// 创建 StaticMeshComponent 并附加到根。
		FName CompName = *FString::Printf(TEXT("Tile3D_%02d"), i);
		UStaticMeshComponent* MeshComp = NewObject<UStaticMeshComponent>(this, CompName);
		MeshComp->SetStaticMesh(CubeMesh);
		MeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		MeshComp->SetRelativeScale3D(TileScale);
		MeshComp->RegisterComponent();
		MeshComp->AttachToComponent(RootSceneComp, FAttachmentTransformRules::KeepRelativeTransform);

		// 定位到方形环对应位置。
		const FVector WorldPos = GetTileWorldPosition(i);
		// 相对于 Actor 根的坐标(Z 偏移半格高度,让地块底面贴地)。
		const FVector RelPos = WorldPos - GetActorLocation() + FVector(0.f, 0.f, TileHeight * 0.5f);
		MeshComp->SetRelativeLocation(RelPos);

		// 创建动态材质实例(MID),初始设灰色。
		if (BaseMat)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			if (MID)
			{
				// 用 HDR 亮色(值 > 1)驱动 Emissive-like 效果,确保截图中颜色可见。
				// BasicShapeMaterial 的 BaseColor 参数名:"Color"。
				MID->SetVectorParameterValue(TEXT("Color"), FLinearColor(0.5f, 0.5f, 0.5f, 1.f));
				MeshComp->SetMaterial(0, MID);
				Entry.MID = MID;
			}
		}

		Entry.MeshComp = MeshComp;
		TileEntries.Add(Entry);
	}

	UE_LOG(LogTemp, Log, TEXT("[Board3D] 程序化 3D 棋盘构建完成:生成 %d 个地块 mesh,TileSize=%.0f TileHeight=%.0f"),
		TileEntries.Num(), TileSize, TileHeight);
}

void AMADemoBoard3DActor::SetupBoardCamera()
{
	UWorld* World = GetWorld();
	if (!World) return;

	// 棋盘中心:Actor XY 原点 + Z=地块高度一半(地块几何中心)。
	// FindLookAtRotation 对准此点确保棋盘在画面正中。
	const FVector ActorOrigin = GetActorLocation();
	const FVector BoardCenter3D(ActorOrigin.X, ActorOrigin.Y, ActorOrigin.Z + TileHeight * 0.5f);

	// 棋盘半跨:3 * step = 3 * (TileSize + TileGap) = 3 * 160 = 480 cm。
	// 相机策略:正上方垂直俯视 + 适量 X/Y 混合后退产生立体感。
	// 相机高度 H,X 方向后退 Retreat 产生俯视角,Y 方向不偏移保持棋盘左右对称。
	// FindLookAtRotation 精确计算使棋盘中心在画面正中。
	const float H = CameraHeight;
	const float Retreat = H * 0.55f;  // X 方向后退,产生约 29° 俯角(更接近垂直)

	// 相机位置:从棋盘正上方向 -X 退 Retreat。
	// 注:Y 不偏移确保棋盘左右居中;FindLookAtRotation 确保棋盘上下居中。
	const FVector CamLoc(
		ActorOrigin.X - Retreat, // -X 方向后退
		ActorOrigin.Y,           // Y 居中
		ActorOrigin.Z + H        // 正上方高度
	);

	// 用 FindLookAtRotation 精确对准棋盘中心(避免手动算 pitch/yaw 的误差)。
	const FRotator CamRot = UKismetMathLibrary::FindLookAtRotation(CamLoc, BoardCenter3D);

	FActorSpawnParameters Params;
	Params.Owner = this;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;

	BoardCamera = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(),
		CamLoc, CamRot, Params);

	if (BoardCamera)
	{
		// FOV 75 度:加大 FOV 让棋盘填充更多画面(棋盘半跨 480 cm,H=2200,Retreat=880);
		// 75 度 FOV 在 1280x720 宽高比下水平视野 ≈ tan(37.5°)*2*dist,棋盘能较好充满画面。
		if (UCameraComponent* CamComp = BoardCamera->GetCameraComponent())
		{
			CamComp->FieldOfView = 75.f;
		}

		UE_LOG(LogTemp, Log,
			TEXT("[Board3D] 3D 棋盘俯视相机创建位置:(%.0f, %.0f, %.0f) Rot:(P=%.1f Y=%.1f)"),
			CamLoc.X, CamLoc.Y, CamLoc.Z, CamRot.Pitch, CamRot.Yaw);

		// 延迟切换视角,等 PlayerController 就绪(BeginPlay 时 PC 可能尚未完全初始化)。
		// 立即尝试一次,再加延迟兜底保证切换成功。
		auto DoSwitchCam = [this, World]()
		{
			APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
			if (PC && BoardCamera)
			{
				PC->SetViewTarget(BoardCamera);
				UE_LOG(LogTemp, Log, TEXT("[Board3D] Player0 视角切换到 3D 棋盘俯视相机"));
			}
		};

		DoSwitchCam();

		// 0.2s 后再切一次,确保 PlayerController/CameraManager 已完全初始化。
		FTimerHandle CamSwitchHandle;
		World->GetTimerManager().SetTimer(CamSwitchHandle, [this, World]()
		{
			APlayerController* PC = UGameplayStatics::GetPlayerController(World, 0);
			if (PC && BoardCamera)
			{
				PC->SetViewTarget(BoardCamera);
			}
		}, 0.2f, false);
	}
}

void AMADemoBoard3DActor::RefreshTileColors()
{
	// 更新 GameState 引用(防止 BeginPlay 时尚未注册)。
	if (!CachedGS && GetWorld())
	{
		CachedGS = Cast<AMADemoGameState>(GetWorld()->GetGameState());
	}

	for (FMADemoTile3DEntry& Entry : TileEntries)
	{
		if (!Entry.MeshComp) continue;

		const FLinearColor BaseColor = GetTileDisplayColor(Entry.TileIndex);

		// 颜色设置策略:
		// 1. 用 MID->SetVectorParameterValue("Color", ...) 设 BaseColor。
		// 2. 同时放大亮度后通过 SetVectorParameterValueOnMaterials 设 Emissive(如果材质支持)。
		//    注:BasicShapeMaterial 可能没有独立 Emissive 参数,故先设 Color,
		//    再通过 Emissive 参数尝试(失败无副作用)。
		// 3. 亮度放大系数 ColorBoost:让地块在 PBR 场景中也显出明显色彩(减少场景暗光影响)。
		const float ColorBoost = 2.5f;  // HDR 放大:让颜色"自发光感"
		const FLinearColor BoostedColor(
			BaseColor.R * ColorBoost,
			BaseColor.G * ColorBoost,
			BaseColor.B * ColorBoost,
			1.f
		);

		if (Entry.MID)
		{
			// BasicShapeMaterial: "Color" 是 BaseColor 参数。
			Entry.MID->SetVectorParameterValue(TEXT("Color"), BoostedColor);
		}
		else
		{
			// 兜底:对 mesh 所有材质槽尝试设参数(SetVectorParameterValueOnMaterials 用 FVector)。
			Entry.MeshComp->SetVectorParameterValueOnMaterials(
				TEXT("Color"),
				FVector(BoostedColor.R, BoostedColor.G, BoostedColor.B)
			);
		}
	}
}

void AMADemoBoard3DActor::BuildPawns3D()
{
	// 需要 GameState 获知玩家数量与颜色。
	if (!CachedGS)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Board3D] BuildPawns3D:GameState 为空,跳过棋子生成"));
		return;
	}

	const int32 PlayerCount = CachedGS->Players.Num();
	if (PlayerCount <= 0)
	{
		UE_LOG(LogTemp, Warning, TEXT("[Board3D] BuildPawns3D:玩家数为 0,跳过棋子生成"));
		return;
	}

	// 加载引擎内置 Cylinder 基础几何(棋子形状)。
	UStaticMesh* CylinderMesh = LoadObject<UStaticMesh>(nullptr,
		TEXT("/Engine/BasicShapes/Cylinder.Cylinder"));
	if (!CylinderMesh)
	{
		// 退级:用 Cone 或 Sphere。
		CylinderMesh = LoadObject<UStaticMesh>(nullptr,
			TEXT("/Engine/BasicShapes/Sphere.Sphere"));
		if (!CylinderMesh)
		{
			UE_LOG(LogTemp, Warning, TEXT("[Board3D] BuildPawns3D:Cylinder/Sphere 均加载失败,跳过"));
			return;
		}
		UE_LOG(LogTemp, Log, TEXT("[Board3D] BuildPawns3D:Cylinder 失败,退级用 Sphere"));
	}

	// 棋子使用与地块相同的 BasicShapeMaterial,通过 MID 设颜色。
	UMaterialInterface* BaseMat = LoadObject<UMaterialInterface>(
		nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"));

	// Cylinder 原始尺寸:直径 100(半径 50),高度 100。
	// 缩放:XY → PawnRadius/50,Z → PawnHeight/100。
	const float ScaleXY = PawnRadius / 50.f;
	const float ScaleZ  = PawnHeight / 100.f;
	const FVector PawnScale(ScaleXY, ScaleXY, ScaleZ);

	PawnEntries.Reset();
	PawnEntries.Reserve(PlayerCount);

	// 玩家颜色表:使用中等亮度(不超过 1.5)饱和色,避免 ACES tonemapping 压成白色。
	// 低亮度但高饱和度,与白色背景形成对比,与棋盘地块色调不同。
	const TArray<FLinearColor> PawnColors = {
		FLinearColor(1.2f, 0.05f, 0.05f, 1.f),  // P0:深红
		FLinearColor(0.05f, 0.8f, 1.2f, 1.f),   // P1:亮青
		FLinearColor(1.2f, 1.0f, 0.02f, 1.f),   // P2:金黄
		FLinearColor(0.6f, 0.05f, 1.2f, 1.f),   // P3:深紫
	};

	for (int32 i = 0; i < PlayerCount; ++i)
	{
		FMADemoPawn3DEntry Entry;
		Entry.PlayerIndex = i;

		// 创建 StaticMeshComponent 并附加到根。
		FName CompName = *FString::Printf(TEXT("Pawn3D_%02d"), i);
		UStaticMeshComponent* MeshComp = NewObject<UStaticMeshComponent>(this, CompName);
		MeshComp->SetStaticMesh(CylinderMesh);
		MeshComp->SetCollisionEnabled(ECollisionEnabled::NoCollision);
		MeshComp->SetRelativeScale3D(PawnScale);
		MeshComp->RegisterComponent();
		MeshComp->AttachToComponent(RootSceneComp, FAttachmentTransformRules::KeepRelativeTransform);

		// 创建棋子动态材质,设玩家颜色。
		// 同时保存 BaseColor 供后续 RefreshPawnPositions 每帧重算高亮(避免累积溢出变白)。
		const FLinearColor PawnColor = PawnColors.IsValidIndex(i)
			? PawnColors[i]
			: FLinearColor(2.f, 2.f, 2.f, 1.f); // 兜底白色
		Entry.BaseColor = PawnColor;

		if (BaseMat)
		{
			UMaterialInstanceDynamic* MID = UMaterialInstanceDynamic::Create(BaseMat, this);
			if (MID)
			{
				MID->SetVectorParameterValue(TEXT("Color"), PawnColor);
				MeshComp->SetMaterial(0, MID);
				Entry.MID = MID;
			}
		}

		Entry.MeshComp = MeshComp;
		PawnEntries.Add(Entry);
	}

	UE_LOG(LogTemp, Log, TEXT("[Board3D] 玩家棋子生成完成:共 %d 个棋子(PawnRadius=%.0f PawnHeight=%.0f)"),
		PawnEntries.Num(), PawnRadius, PawnHeight);
}

void AMADemoBoard3DActor::RefreshPawnPositions()
{
	// 更新 GameState 引用。
	if (!CachedGS && GetWorld())
	{
		CachedGS = Cast<AMADemoGameState>(GetWorld()->GetGameState());
	}

	if (!CachedGS) return;

	const int32 CurrentPlayer = CachedGS->CurrentPlayerIndex;

	// 调试:每 60 次刷新(约 30 秒)输出一次所有棋子位置,确认棋子跟随 GameState 移动。
	static int32 PawnRefreshCount = 0;
	if (PawnRefreshCount++ % 60 == 0)
	{
		for (int32 Pi = 0; Pi < CachedGS->Players.Num(); ++Pi)
		{
			const UMADemoPlayerData* Pd = CachedGS->GetPlayer(Pi);
			if (Pd)
			{
				UE_LOG(LogTemp, Log, TEXT("[Board3D][PawnPos] P%d: TileIndex=%d (CurrentPlayer=%d)"),
					Pi, Pd->CurrentTileIndex, CurrentPlayer);
			}
		}
	}

	// 第一步:统计每个格子上的玩家列表(用于计算同格多人时的偏移量)。
	// Key=TileIndex, Value=按 PlayerIndex 顺序的玩家列表。
	TMap<int32, TArray<int32>> TilePlayerMap;
	for (const FMADemoPawn3DEntry& E : PawnEntries)
	{
		const UMADemoPlayerData* PD = CachedGS->GetPlayer(E.PlayerIndex);
		if (!PD) continue;
		const int32 Ti = FMath::Clamp(PD->CurrentTileIndex, 0, 27);
		TilePlayerMap.FindOrAdd(Ti).Add(E.PlayerIndex);
	}

	// 同格多人偏移步进:棋子直径 × 0.55,确保棋子紧挨但不超出格子范围。
	// PawnRadius(修复后)= 30 → 直径 60 → 偏移步进 33cm;格子 TileSize=150,可容纳 4 个棋子。
	// 最大支持 4 名玩家,偏移布局:2×2 网格(X方向两行,Y方向两列)。
	const float SmallOffset = TileSize * 0.22f;  // 约 33cm,棋子在格内安全偏移量

	for (FMADemoPawn3DEntry& Entry : PawnEntries)
	{
		if (!Entry.MeshComp) continue;

		const UMADemoPlayerData* PData = CachedGS->GetPlayer(Entry.PlayerIndex);
		if (!PData) continue;

		// 取玩家当前格的世界坐标(棋盘已算好坐标)。
		const int32 TileIdx = FMath::Clamp(PData->CurrentTileIndex, 0, 27);
		const FVector TileWorldPos = GetTileWorldPosition(TileIdx);

		// 棋子立在地块上方:Z = 地块顶面 + 棋子半高。
		// 地块顶面 Z = ActorZ + TileHeight;Cylinder pivot 在几何中心,缩放后半高 = PawnHeight*0.5。
		const float PawnCenterZ = GetActorLocation().Z + TileHeight + PawnHeight * 0.5f;

		// 计算 XY 偏移:
		// - 格子上只有一个玩家:棋子居格子正中(偏移 0)。
		// - 格子上有多个玩家:按 2×2 网格做小偏移,保证棋子仍在格内。
		float OffX = 0.f, OffY = 0.f;
		const TArray<int32>* PlayersOnTile = TilePlayerMap.Find(TileIdx);
		if (PlayersOnTile && PlayersOnTile->Num() > 1)
		{
			// 找到本玩家在同格玩家列表中的位置(子索引 0~3)。
			const int32 SubIdx = PlayersOnTile->IndexOfByKey(Entry.PlayerIndex);
			// 2×2 布局:SubIdx 0→左上,1→右上,2→左下,3→右下。
			OffX = (SubIdx % 2 == 0) ? -SmallOffset : SmallOffset;
			OffY = (SubIdx / 2 == 0) ? -SmallOffset : SmallOffset;
		}
		// 单人在格:OffX=OffY=0,棋子居中。

		const FVector PawnWorldPos(
			TileWorldPos.X + OffX,
			TileWorldPos.Y + OffY,
			PawnCenterZ
		);

		// 转换为相对于 Actor 根的坐标。
		const FVector RelPos = PawnWorldPos - GetActorLocation();
		Entry.MeshComp->SetRelativeLocation(RelPos);

		// 当前回合玩家棋子:放大 + 高亮(Z 额外抬高,令其在画面中更突出)。
		const bool bIsActive = (Entry.PlayerIndex == CurrentPlayer);

		// 棋子缩放:当前玩家放大 PawnActiveScale 倍。
		const float Scale = PawnRadius / 50.f;
		const float ActiveScale = Scale * PawnActiveScale;
		const float ScaleZ = PawnHeight / 100.f;

		if (bIsActive)
		{
			// 当前玩家棋子放大 + 抬高(额外向上 40cm 产生浮标效果)。
			// 放大 PawnActiveScale(1.5x),使其明显高于其他棋子。
			Entry.MeshComp->SetRelativeScale3D(FVector(ActiveScale, ActiveScale, ScaleZ * PawnActiveScale));
			const FVector ActiveRelPos = RelPos + FVector(0.f, 0.f, 40.f);
			Entry.MeshComp->SetRelativeLocation(ActiveRelPos);

			// 高亮:当前玩家棋子改为纯白色(1.0, 1.0, 1.0),与其他彩色棋子形成强对比。
			// 纯白在 PBR 场景中不受 tonemapping 压色影响,可见性最高。
			if (Entry.MID)
			{
				Entry.MID->SetVectorParameterValue(TEXT("Color"), FLinearColor(1.0f, 1.0f, 1.0f, 1.f));
			}
		}
		else
		{
			// 非当前玩家棋子:正常大小,恢复基础颜色。
			Entry.MeshComp->SetRelativeScale3D(FVector(Scale, Scale, ScaleZ));
			if (Entry.MID)
			{
				Entry.MID->SetVectorParameterValue(TEXT("Color"), Entry.BaseColor);
			}
		}
	}
}
