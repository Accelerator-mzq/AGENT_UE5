// Copyright Phase14 demo agent.
// 游戏模式(规则裁决核心)。回合状态机、掷骰、移动、过起点、格子事件分发、
// 购买/租金/税/监狱/破产/胜负判定全部在此裁决。施工规范 §3:GameMode 裁决,GameState 存态。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MADemoTypes.h"
#include "MADemoGameMode.generated.h"

class AMADemoGameState;
class UMADemoPlayerData;
class UMADemoBoardDataAsset;
class UMADemoRulesDataAsset;

// Monopoly 扩展版回合驱动 GameMode。
UCLASS(BlueprintType)
class DEMO_MONOPOLYAUCTION_API AMADemoGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMADemoGameMode();

	// 可在编辑器/默认对象指定的数据资产类(数据驱动入口)。
	// 缺省为空时 InitializeGame 会用代码默认资产兜底,保证无 PIE 也能跑通。
	UPROPERTY(EditDefaultsOnly, Category = "Data")
	TObjectPtr<UMADemoBoardDataAsset> DefaultBoardData;

	UPROPERTY(EditDefaultsOnly, Category = "Data")
	TObjectPtr<UMADemoRulesDataAsset> DefaultRulesData;

	// ── 对外驱动 API(冒烟与 PlayerController 意图入口)──────────────

	// 初始化一局:创建 N 个玩家、铺棋盘、置初始资金/股票。
	// 传入 RandomSeed 使整局确定可复现(冒烟断言用)。
	UFUNCTION(BlueprintCallable, Category = "Flow")
	void InitializeGame(int32 NumPlayers, int32 RandomSeed = 12345);

	// 开始当前玩家回合(回合数++,股票波动留待掷骰后)。进入 WaitingForRoll。
	UFUNCTION(BlueprintCallable, Category = "Flow")
	void StartTurn();

	// 请求掷骰并完成本步全部结算(移动→过起点→格子事件→双数处理)。
	// 为保证无人值守可驱动,购买决策走 AutoBuyPolicy 自动裁决。
	UFUNCTION(BlueprintCallable, Category = "Flow")
	void RequestRollAndResolve();

	// 推进到下一个存活玩家;若仅剩 1 人则收敛 GameOver。
	UFUNCTION(BlueprintCallable, Category = "Flow")
	void AdvanceToNextPlayer();

	// 是否已分出胜负
	UFUNCTION(BlueprintCallable, Category = "Flow")
	bool IsGameOver() const;

	// 一键驱动整局到终局(冒烟主入口):循环 StartTurn/RequestRollAndResolve 直到 GameOver 或回合上限。
	// 返回最终胜者索引(-1 = 达回合上限和局)。
	UFUNCTION(BlueprintCallable, Category = "Flow")
	int32 RunFullGameToCompletion();

	// 取本局 GameState(冒烟与 UI 用)
	UFUNCTION(BlueprintCallable, Category = "Flow")
	AMADemoGameState* GetDemoGameState() const;

protected:
	// 移动当前玩家 Steps 格(环形),处理过起点奖励,落地后分发格子事件。
	void MoveCurrentPlayer(int32 Steps);

	// 玩家落到 TileIndex 后的事件分发。
	void OnPlayerLanded(int32 TileIndex);

	// 处理地产格:无主→自动购买策略;他人→付租;自己→无事。
	void HandlePropertyTile(int32 TileIndex);

	// 处理税务格:强制扣款,不足则破产。
	void HandleTaxTile(int32 TileIndex);

	// 处理前往监狱格。
	void HandleGoToJail();

	// 监狱回合开始处理:尝试保释/掷双出狱/满 3 回合强制出狱。返回是否本回合可正常移动。
	bool HandleJailTurnStart();

	// 结算一笔支付:Payer 付 Amount 给 Creditor(Creditor 为空则付银行)。不足额触发破产。
	// 形参用 Creditor 而非 Owner,避免遮蔽 AActor::Owner 成员(C4458)。
	void ProcessPayment(UMADemoPlayerData* Payer, UMADemoPlayerData* Creditor, int32 Amount);

	// 淘汰玩家:地产清空归无主,标记破产。
	void EliminatePlayer(UMADemoPlayerData* Player);

	// 检查胜负:存活 1 人则置 WinnerIndex 与 GameOver。
	void CheckGameOver();

	// 掷一次骰(2D6,用确定性随机流)。
	FMADemoDiceResult RollDiceInternal();

	// 自动购买策略(无人值守):买得起且无主则买。可在子类/数据覆盖。
	bool AutoBuyPolicy(UMADemoPlayerData* Player, int32 TileIndex) const;

private:
	// 本局 GameState 缓存
	UPROPERTY(Transient)
	TObjectPtr<AMADemoGameState> CachedGameState;

	// 确定性随机流(由 InitializeGame 的 seed 播种)
	FRandomStream RandomStream;

	// 本回合连续双数计数
	int32 ConsecutiveDoubles = 0;
};
