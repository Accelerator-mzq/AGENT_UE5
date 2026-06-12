// Copyright Phase14 v0 attempt2. 全量可读游戏状态。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "MADemoTypes.h"
#include "MADemoGameState.generated.h"

class UMADemoPlayerData;
class UMADemoStockMarket;
class UMADemoBoardDataAsset;
class UMADemoRulesDataAsset;

// 全量可读游戏状态。UI 与冒烟断言只经此读状态;改写只由 GameMode 入口。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API AMADemoGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	AMADemoGameState();

	// 棋盘数据(运行期持有的资产引用)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	TObjectPtr<UMADemoBoardDataAsset> BoardData;

	// 规则数据。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	TObjectPtr<UMADemoRulesDataAsset> RulesData;

	// 每格所有者玩家索引(-1=无主)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	TArray<int32> TileOwnership;

	// 全部玩家数据。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	TArray<TObjectPtr<UMADemoPlayerData>> Players;

	// 股票市场。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	TObjectPtr<UMADemoStockMarket> StockMarket;

	// 拍卖运行态(v0 数据骨架)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	FMADemoAuctionState AuctionState;

	// 当前回合数(从 1 起)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	int32 TurnNumber = 0;

	// 当前玩家索引。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	int32 CurrentPlayerIndex = 0;

	// 存活玩家数。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	int32 ActivePlayerCount = 0;

	// 当前回合阶段。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	EMADemoTurnPhase TurnPhase = EMADemoTurnPhase::NotStarted;

	// 最近一次掷骰结果。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	FMADemoDiceResult LastDice;

	// 是否游戏结束。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	bool bGameOver = false;

	// 是否暂停中(Esc 切换;暂停时掷骰/结束回合意图被拒)。改写只经 GameMode 入口。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	bool bPaused = false;

	// 胜者玩家索引(-1=未定)。
	UPROPERTY(BlueprintReadOnly, Category = "Demo|State")
	int32 WinnerIndex = -1;

	// --- 只读查询 API(冒烟与 UI 用)---

	// 取某格静态信息。
	FMADemoTileInfo GetTileInfo(int32 Index) const;

	// 取某格所有者(-1 无主)。
	int32 GetTileOwner(int32 Index) const;

	// 设置某格所有者。
	void SetTileOwner(int32 Index, int32 PlayerIndex);

	// 取某玩家数据。
	UMADemoPlayerData* GetPlayer(int32 Index) const;

	// 取存活玩家数。
	int32 GetActivePlayerCount() const;

	// 玩家是否持有某颜色组全部地产。
	bool DoesPlayerOwnColorGroup(int32 PlayerIndex, EMADemoColorGroup Group) const;

	// 计算某格租金(含满色组翻倍)。
	int32 CalculateRent(int32 TileIndex) const;

	// 计算某玩家净资产(现金 + 地产价 + 股票市值)。
	int32 GetPlayerNetWorth(int32 PlayerIndex) const;

	// 计算某玩家股票市值。
	int32 GetPlayerStockValue(int32 PlayerIndex) const;
};
