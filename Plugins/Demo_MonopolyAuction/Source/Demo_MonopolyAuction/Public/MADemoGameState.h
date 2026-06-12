// Copyright Phase14 demo agent.
// 全量游戏状态(GameStateBase 派生)。承载棋盘所有权/玩家集合/回合数/股票/拍卖态。
// 施工规范 §3:GameState 全量状态,冒烟测试经 GameState API 直驱;UI 只读本类。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameStateBase.h"
#include "MADemoTypes.h"
#include "MADemoGameState.generated.h"

class UMADemoPlayerData;
class UMADemoBoardDataAsset;
class UMADemoRulesDataAsset;
class UMADemoStockMarket;

// 拍卖运行期态(v0 保留结构,完整流程在 increment-1)。
USTRUCT(BlueprintType)
struct FMADemoAuctionState
{
	GENERATED_BODY()

	// 是否有拍卖正在进行
	UPROPERTY(BlueprintReadOnly, Category = "Auction")
	bool bActive = false;

	// 被拍地产格索引
	UPROPERTY(BlueprintReadOnly, Category = "Auction")
	int32 TileIndex = -1;

	// 当前最高价
	UPROPERTY(BlueprintReadOnly, Category = "Auction")
	int32 HighestBid = 0;

	// 当前最高出价者玩家索引(-1 = 尚无)
	UPROPERTY(BlueprintReadOnly, Category = "Auction")
	int32 HighestBidderIndex = -1;
};

// Demo 全量状态。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API AMADemoGameState : public AGameStateBase
{
	GENERATED_BODY()

public:
	AMADemoGameState();

	// ── 静态数据资产引用 ──────────────────────────────
	// 棋盘数据(数据驱动来源)
	UPROPERTY(BlueprintReadOnly, Category = "Data")
	TObjectPtr<UMADemoBoardDataAsset> BoardData;

	// 规则参数数据
	UPROPERTY(BlueprintReadOnly, Category = "Data")
	TObjectPtr<UMADemoRulesDataAsset> RulesData;

	// ── 运行期态 ────────────────────────────────────
	// 玩家集合(顺序即回合顺序)
	UPROPERTY(BlueprintReadOnly, Category = "State")
	TArray<TObjectPtr<UMADemoPlayerData>> Players;

	// 每格所有者玩家索引(-1 = 无主),长度 = 棋盘格数
	UPROPERTY(BlueprintReadOnly, Category = "State")
	TArray<int32> TileOwners;

	// 当前回合玩家索引
	UPROPERTY(BlueprintReadOnly, Category = "State")
	int32 CurrentPlayerIndex = 0;

	// 当前回合数(从 1 起)
	UPROPERTY(BlueprintReadOnly, Category = "State")
	int32 TurnNumber = 0;

	// 当前回合阶段
	UPROPERTY(BlueprintReadOnly, Category = "State")
	EMADemoTurnPhase TurnPhase = EMADemoTurnPhase::NotStarted;

	// 最近一次掷骰结果(HUD 显示)
	UPROPERTY(BlueprintReadOnly, Category = "State")
	FMADemoDiceResult LastDiceResult;

	// 股票市场态
	UPROPERTY(BlueprintReadOnly, Category = "State")
	TObjectPtr<UMADemoStockMarket> StockMarket;

	// 拍卖态
	UPROPERTY(BlueprintReadOnly, Category = "State")
	FMADemoAuctionState AuctionState;

	// 胜者玩家索引(-1 = 未决出)
	UPROPERTY(BlueprintReadOnly, Category = "State")
	int32 WinnerIndex = -1;

	// ── 状态查询 API(UI 只读、冒烟可断言)────────────
	// 取格子静态信息
	UFUNCTION(BlueprintCallable, Category = "State")
	FMADemoTileInfo GetTileInfo(int32 TileIndex) const;

	// 取格子所有者(-1 = 无主)
	UFUNCTION(BlueprintCallable, Category = "State")
	int32 GetTileOwner(int32 TileIndex) const;

	// 设置格子所有者
	UFUNCTION(BlueprintCallable, Category = "State")
	void SetTileOwner(int32 TileIndex, int32 PlayerIndex);

	// 取玩家数据
	UFUNCTION(BlueprintCallable, Category = "State")
	UMADemoPlayerData* GetPlayer(int32 PlayerIndex) const;

	// 存活(未破产)玩家数
	UFUNCTION(BlueprintCallable, Category = "State")
	int32 GetActivePlayerCount() const;

	// 某玩家是否持有指定颜色组全部地产(满组租金翻倍判定)
	UFUNCTION(BlueprintCallable, Category = "State")
	bool DoesPlayerOwnColorGroup(int32 PlayerIndex, EMADemoColorGroup Group) const;

	// 计算某地产格当前应付租金(含满组翻倍)
	UFUNCTION(BlueprintCallable, Category = "State")
	int32 CalculateRent(int32 TileIndex) const;

	// 玩家总资产(现金 + 股票市值;破产判定与排名用)
	UFUNCTION(BlueprintCallable, Category = "State")
	int32 GetPlayerNetWorth(int32 PlayerIndex) const;
};
