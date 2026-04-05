#pragma once

#include "CoreMinimal.h"
#include "MMonopolyTypes.generated.h"

UENUM(BlueprintType)
enum class EMTileType : uint8
{
	Start UMETA(DisplayName = "Start"),
	Property UMETA(DisplayName = "Property"),
	Chance UMETA(DisplayName = "Chance"),
	CommunityChest UMETA(DisplayName = "CommunityChest"),
	Tax UMETA(DisplayName = "Tax"),
	JailVisit UMETA(DisplayName = "JailVisit"),
	GoToJail UMETA(DisplayName = "GoToJail"),
	FreeParking UMETA(DisplayName = "FreeParking")
};

UENUM(BlueprintType)
enum class EMColorGroup : uint8
{
	None UMETA(DisplayName = "None"),
	Brown UMETA(DisplayName = "Brown"),
	LightBlue UMETA(DisplayName = "LightBlue"),
	Pink UMETA(DisplayName = "Pink"),
	Orange UMETA(DisplayName = "Orange"),
	Red UMETA(DisplayName = "Red"),
	Green UMETA(DisplayName = "Green"),
	Blue UMETA(DisplayName = "Blue")
};

UENUM(BlueprintType)
enum class EMTurnState : uint8
{
	None UMETA(DisplayName = "None"),
	WaitForRoll UMETA(DisplayName = "WaitForRoll"),
	RollingDice UMETA(DisplayName = "RollingDice"),
	MovingPawn UMETA(DisplayName = "MovingPawn"),
	ResolvingTileEvent UMETA(DisplayName = "ResolvingTileEvent"),
	WaitingForPopup UMETA(DisplayName = "WaitingForPopup"),
	EndingTurn UMETA(DisplayName = "EndingTurn"),
	GameOver UMETA(DisplayName = "GameOver")
};

UENUM(BlueprintType)
enum class EMGamePhase : uint8
{
	None UMETA(DisplayName = "None"),
	Setup UMETA(DisplayName = "Setup"),
	InProgress UMETA(DisplayName = "InProgress"),
	Finished UMETA(DisplayName = "Finished")
};

USTRUCT(BlueprintType)
struct FMTileData
{
	GENERATED_BODY()

	// 逻辑格子索引，与棋盘上的 TileActor 一一对应。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 TileIndex = INDEX_NONE;

	// UI 和调试统一展示的格子名字。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	FString TileName;

	// 当前格子的功能类型。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	EMTileType TileType = EMTileType::Property;

	// 房产颜色组，仅可购买地块使用。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	EMColorGroup ColorGroup = EMColorGroup::None;

	// 购买价格，非房产格默认为 0。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 Cost = 0;

	// 基础租金，若形成整组垄断后可翻倍。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 Rent = 0;

	// 税务格使用的固定扣费。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 TaxAmount = 0;

	// 当前业主在 MonopolyPlayers 数组中的索引，-1 表示无人拥有。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 OwnerPlayerIndex = INDEX_NONE;

	// 是否允许被玩家购买。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	bool bCanBeOwned = false;
};

USTRUCT(BlueprintType)
struct FMDiceResult
{
	GENERATED_BODY()

	// 第一个骰子点数。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 DieA = 1;

	// 第二个骰子点数。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 DieB = 1;

	// 两个骰子的总和。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	int32 Total = 2;

	// 是否为双骰。
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Monopoly")
	bool bIsDouble = false;
};
