// Copyright Phase14 demo agent.
// 全局基础类型:格子类型/颜色组/回合阶段枚举,格子信息/骰子结果结构。
// 这些是 Monopoly 主链的共享词表,被 GameState/GameMode/UI 共同引用。
#pragma once

#include "CoreMinimal.h"
#include "MADemoTypes.generated.h"

// 格子类型枚举(对应 GDD 2.2 节 8 种格子类型)。
// 交易所(Exchange)为扩展 GDD 2.2 新增的角格,替换一个普通空白格。
UENUM(BlueprintType)
enum class EMADemoTileType : uint8
{
	Start         UMETA(DisplayName = "起点"),
	Property      UMETA(DisplayName = "地产"),
	Tax           UMETA(DisplayName = "税务"),
	JailVisit     UMETA(DisplayName = "监狱探访"),
	FreeParking   UMETA(DisplayName = "免费停车"),
	GoToJail      UMETA(DisplayName = "前往监狱"),
	Chance        UMETA(DisplayName = "机会"),
	Community     UMETA(DisplayName = "公共基金"),
	Exchange      UMETA(DisplayName = "交易所")
};

// 颜色组枚举(对应 GDD 2.4 节,同组全持有则租金翻倍)。
UENUM(BlueprintType)
enum class EMADemoColorGroup : uint8
{
	None      UMETA(DisplayName = "无"),
	Brown     UMETA(DisplayName = "棕"),
	LightBlue UMETA(DisplayName = "浅蓝"),
	Pink      UMETA(DisplayName = "粉"),
	Orange    UMETA(DisplayName = "橙"),
	Red       UMETA(DisplayName = "红"),
	Green     UMETA(DisplayName = "绿"),
	Blue      UMETA(DisplayName = "蓝")
};

// 回合状态机阶段(对应 GDD 7 节状态机流程)。
UENUM(BlueprintType)
enum class EMADemoTurnPhase : uint8
{
	NotStarted        UMETA(DisplayName = "未开始"),
	WaitingForRoll    UMETA(DisplayName = "等待掷骰"),
	Resolving         UMETA(DisplayName = "结算格子事件"),
	WaitingForBuy     UMETA(DisplayName = "等待购买决策"),
	Auctioning        UMETA(DisplayName = "拍卖进行中"),
	TurnEnd           UMETA(DisplayName = "回合结束"),
	GameOver          UMETA(DisplayName = "游戏结束")
};

// 格子静态信息(数据驱动:由 BoardDataAsset 行投影而来)。
USTRUCT(BlueprintType)
struct FMADemoTileInfo
{
	GENERATED_BODY()

	// 格子索引(0-27)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tile")
	int32 TileIndex = 0;

	// 格子类型
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tile")
	EMADemoTileType TileType = EMADemoTileType::Start;

	// 格子显示名称
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tile")
	FString Name;

	// 颜色组(仅地产格有意义)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tile")
	EMADemoColorGroup ColorGroup = EMADemoColorGroup::None;

	// 购买价格(地产格);税务格此处复用为缴税金额
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tile")
	int32 Price = 0;

	// 基础租金(地产格)
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Tile")
	int32 BaseRent = 0;
};

// 掷骰结果(2D6,记录是否双数)。
USTRUCT(BlueprintType)
struct FMADemoDiceResult
{
	GENERATED_BODY()

	UPROPERTY(BlueprintReadOnly, Category = "Dice")
	int32 Die1 = 0;

	UPROPERTY(BlueprintReadOnly, Category = "Dice")
	int32 Die2 = 0;

	// 点数之和(移动步数)
	UPROPERTY(BlueprintReadOnly, Category = "Dice")
	int32 Sum = 0;

	// 是否双数(两骰相同)
	UPROPERTY(BlueprintReadOnly, Category = "Dice")
	bool bIsDouble = false;
};
