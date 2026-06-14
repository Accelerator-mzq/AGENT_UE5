// Copyright Phase15 presentation-3. 程序化 3D 棋盘 Actor。
// 施工规范 §7:用引擎基础几何 + 动态材质实例(MID)程序化拼出 28 个地块 mesh 组件排成方形环。
// 不引入外部资产,全部依赖 /Engine/BasicShapes/ 内置几何与 BasicShapeMaterial。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MADemoTypes.h"
#include "MADemoGameState.h"
#include "MADemoBoard3DActor.generated.h"

class UStaticMeshComponent;
class UMaterialInstanceDynamic;
class ACameraActor;

// 单个地块的 3D 组件引用记录。
USTRUCT()
struct FMADemoTile3DEntry
{
	GENERATED_BODY()

	// 地块基座 Mesh 组件(Cube)。
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> MeshComp;

	// 动态材质实例(按地产组着色)。
	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> MID;

	// 对应棋盘格索引。
	int32 TileIndex = -1;
};

// 单个玩家棋子的 3D 组件引用记录。
USTRUCT()
struct FMADemoPawn3DEntry
{
	GENERATED_BODY()

	// 棋子 Mesh 组件(Cylinder)。
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> MeshComp;

	// 动态材质实例(按玩家颜色着色)。
	UPROPERTY()
	TObjectPtr<UMaterialInstanceDynamic> MID;

	// 对应玩家索引。
	int32 PlayerIndex = -1;

	// 玩家基础颜色(HDR,用于每帧重算高亮避免累积溢出)。
	FLinearColor BaseColor = FLinearColor::White;
};

// 程序化 3D 棋盘 Actor。
// BeginPlay 时读 GameState 棋盘拓扑,程序化 spawn 28 个地块 mesh 组件排成方形环。
// 各地块的动态材质颜色按地产组(ColorGroup)着色;拥有者/拍卖中状态后续 Tick 更新。
UCLASS()
class DEMO_MONOPOLYAUCTION_API AMADemoBoard3DActor : public AActor
{
	GENERATED_BODY()

public:
	AMADemoBoard3DActor();

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;

	// 外部调用:根据当前 GameState 刷新地块颜色(归属/拍卖状态)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Board3D")
	void RefreshTileColors();

	// 外部调用:根据当前 GameState 刷新玩家棋子位置与高亮。
	UFUNCTION(BlueprintCallable, Category = "Demo|Board3D")
	void RefreshPawnPositions();

	// 3D 棋盘每格边长(厘米,UE 默认 1 unit = 1cm)。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float TileSize = 150.f;

	// 相邻格间距(厘米)。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float TileGap = 10.f;

	// 地块基座高度(厘米)。v2:增大到 60 确保地块有明显立体感。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float TileHeight = 60.f;

	// 相机俯视高度(厘米)。v2:调整为 2200,配合 FindLookAtRotation 精确对准棋盘。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float CameraHeight = 2200.f;

	// 相机俯角(度,负值朝下)。v2:实际由 FindLookAtRotation 计算,此字段保留备用。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float CameraPitch = -55.f;

private:
	// 根组件(场景根)。
	UPROPERTY()
	TObjectPtr<USceneComponent> RootSceneComp;

	// 28 个地块 3D 记录。
	UPROPERTY()
	TArray<FMADemoTile3DEntry> TileEntries;

	// 俯视相机 Actor。
	UPROPERTY()
	TObjectPtr<ACameraActor> BoardCamera;

	// 缓存 GameState 指针。
	UPROPERTY()
	TObjectPtr<AMADemoGameState> CachedGS;

	// 棋盘中心(相机对准点)。
	FVector BoardCenter = FVector::ZeroVector;

	// N 个玩家棋子 3D 记录(BeginPlay 时按 GameState 玩家数 spawn)。
	UPROPERTY()
	TArray<FMADemoPawn3DEntry> PawnEntries;

	// 棋子 Cylinder 半径(cm)。修复为 30,棋子直径 60cm < TileSize*0.4=60cm,可安全站在格内。
	// 旧值 60 导致直径 120cm 几乎等于格宽,偏移后棋子跨格边缘悬空。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float PawnRadius = 30.f;

	// 棋子高度(cm)。设为 180 确保在俯视视角中明显突出地块。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float PawnHeight = 180.f;

	// 当前玩家棋子放大系数。
	UPROPERTY(EditAnywhere, Category = "Demo|Board3D")
	float PawnActiveScale = 1.5f;

	// 将 28 格方形环映射到世界坐标(row=7×7 方形环)。
	// 28 格索引从右下角起点顺时针:底排 7 格→右排 6 格→顶排 7 格→左排 6 格→回起点。
	// 本函数返回第 i 格的中心世界位置(XY 平面)。
	FVector GetTileWorldPosition(int32 TileIndex) const;

	// 根据地产组枚举取配置颜色。
	FLinearColor GetColorGroupColor(EMADemoColorGroup Group) const;

	// 根据地块归属/拍卖状态取显示颜色。
	FLinearColor GetTileDisplayColor(int32 TileIndex) const;

	// 初始化程序化地块 mesh(BeginPlay 调用)。
	void BuildBoard3D();

	// 初始化玩家棋子 mesh(BuildBoard3D 之后调用)。
	void BuildPawns3D();

	// 创建并定位俯视相机。
	void SetupBoardCamera();

	// 刷新间隔累计(节省 CPU,不每帧刷新)。
	float RefreshAccum = 0.f;

	// 刷新颜色的时间间隔(秒)。
	static constexpr float RefreshInterval = 0.5f;
};
