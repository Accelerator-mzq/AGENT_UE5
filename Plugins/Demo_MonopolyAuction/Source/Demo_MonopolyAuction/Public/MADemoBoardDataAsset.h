// Copyright Phase14 demo agent.
// 棋盘数据资产:28 格的完整静态数据(类型/名称/颜色组/价格/租金)。
// 数据驱动设计:默认 28 格在构造函数填充(GDD 2.3 数据表),可在编辑器覆盖。
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MADemoTypes.h"
#include "MADemoBoardDataAsset.generated.h"

// 棋盘静态拓扑 + 格子数据。GameState 初始化时投影为运行期态。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API UMADemoBoardDataAsset : public UDataAsset
{
	GENERATED_BODY()

public:
	UMADemoBoardDataAsset();

	// 28 格数据(顺时针 0..27)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Board")
	TArray<FMADemoTileInfo> Tiles;

	// 棋盘总格数(契约 board.tile_count = 28)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Board")
	int32 TileCount = 28;

	// 起点索引(契约 board.corner_indices.start = 0)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Board")
	int32 StartTileIndex = 0;

	// 前往监狱格索引(契约 board.corner_indices.go_to_jail = 21)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Board")
	int32 GoToJailTileIndex = 21;

	// 交易所角格索引(扩展 GDD 2.2:替换一个普通空白格;provisional 选 16 号原机会格)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Board")
	int32 ExchangeTileIndex = 16;

	// 用默认 28 格数据填充 Tiles(GDD 2.3),供运行期与冒烟使用。
	void BuildDefaultBoard();
};
