// Copyright Phase14 v0 attempt2. 核心枚举与结构体定义。
#pragma once

#include "CoreMinimal.h"
#include "MADemoTypes.generated.h"

// 格子类型枚举(GDD 2.2)。前缀 EMADemo 避免与引擎及主模块类型冲突。
UENUM(BlueprintType)
enum class EMADemoTileType : uint8
{
	Start        UMETA(DisplayName = "起点"),
	Property     UMETA(DisplayName = "地产"),
	Tax          UMETA(DisplayName = "税务"),
	JailVisit    UMETA(DisplayName = "监狱探访"),
	FreeParking  UMETA(DisplayName = "免费停车"),
	GoToJail     UMETA(DisplayName = "前往监狱"),
	Chance       UMETA(DisplayName = "机会"),
	Community    UMETA(DisplayName = "公共基金"),
	StockExchange UMETA(DisplayName = "交易所")
};

// 颜色组枚举(GDD 2.4)。用于满色组租金翻倍判定。
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

// 回合状态机阶段(GDD 7 状态机投影)。
UENUM(BlueprintType)
enum class EMADemoTurnPhase : uint8
{
	NotStarted     UMETA(DisplayName = "未开始"),
	WaitingForRoll UMETA(DisplayName = "等待掷骰"),
	Resolving      UMETA(DisplayName = "结算中"),
	TurnEnd        UMETA(DisplayName = "回合结束"),
	GameOver       UMETA(DisplayName = "游戏结束")
};

// 玩家意图动作枚举(输入底座)。
UENUM(BlueprintType)
enum class EMADemoInputAction : uint8
{
	MenuConfirm UMETA(DisplayName = "菜单确认"),
	MenuCancel  UMETA(DisplayName = "菜单取消"),
	Pause       UMETA(DisplayName = "暂停"),
	RollDice    UMETA(DisplayName = "掷骰")
};

// 单格静态数据(GDD 2.3 数据表)。
USTRUCT(BlueprintType)
struct FMADemoTileInfo
{
	GENERATED_BODY()

	// 格子类型。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Tile")
	EMADemoTileType TileType = EMADemoTileType::Property;

	// 格子名称(中文)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Tile")
	FString Name;

	// 颜色组。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Tile")
	EMADemoColorGroup ColorGroup = EMADemoColorGroup::None;

	// 购买价格(地产)/缴纳金额(税务)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Tile")
	int32 Price = 0;

	// 基础租金。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Demo|Tile")
	int32 BaseRent = 0;
};

// 一次掷骰结果(GDD 3.4)。
USTRUCT(BlueprintType)
struct FMADemoDiceResult
{
	GENERATED_BODY()

	// 第一颗骰子点数(1-6)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Dice")
	int32 Die1 = 0;

	// 第二颗骰子点数(1-6)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Dice")
	int32 Die2 = 0;

	// 是否为双数(两颗相同)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Dice")
	bool bIsDouble = false;

	// 点数之和(移动步数)。
	int32 Sum() const { return Die1 + Die2; }
};

// 单支股票(GDD 2.2 股票市场)。
USTRUCT(BlueprintType)
struct FMADemoStock
{
	GENERATED_BODY()

	// 股票代码(A/B/C)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Stock")
	FString Symbol;

	// 当前价格。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Stock")
	int32 Price = 100;
};

// 拍卖运行态(GDD 2.1 地产拍卖,v0 仅落数据骨架)。
USTRUCT(BlueprintType)
struct FMADemoAuctionState
{
	GENERATED_BODY()

	// 是否拍卖进行中。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Auction")
	bool bActive = false;

	// 被拍地产索引。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Auction")
	int32 TileIndex = -1;

	// 当前最高出价。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Auction")
	int32 HighestBid = 0;

	// 当前最高出价玩家索引(-1 表示无人出价)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|Auction")
	int32 HighestBidderIndex = -1;
};

// HUD 单次快照(只读呈现用)。
USTRUCT(BlueprintType)
struct FMADemoHUDSnapshot
{
	GENERATED_BODY()

	// 当前回合数。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	int32 TurnNumber = 0;

	// 当前玩家索引。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	int32 CurrentPlayerIndex = 0;

	// 当前玩家所在格名称。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	FString CurrentTileName;

	// 各玩家现金(按索引)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	TArray<int32> PlayerCash;

	// 各玩家股票市值(按索引)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	TArray<int32> PlayerStockValue;

	// 各玩家所在格索引(按索引)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	TArray<int32> PlayerTileIndex;

	// 各玩家是否破产(按索引)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	TArray<bool> PlayerBankrupt;

	// 最近一次掷骰文本(如 "3 + 4 = 7")。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	FString DiceText;

	// 3 支股票现价摘要(如 "A:100 B:110 C:90")。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	FString StockSummary;

	// 当前回合阶段文本。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|HUD")
	FString PhaseText;
};
