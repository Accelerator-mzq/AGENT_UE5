// Copyright Phase14 v0 attempt2. 回合状态机与规则裁决核心。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "MADemoTypes.h"
#include "MADemoGameMode.generated.h"

class AMADemoGameState;
class UMADemoPlayerData;
class UMADemoBoardDataAsset;
class UMADemoRulesDataAsset;
class UMADemoHUDWidget;

// 回合驱动核心 + 规则裁决。唯一改写游戏状态的入口。
// 支持两种驱动:(1) 冒烟/自动驾驶经公有 API 直驱整局;(2) 人玩经 PlayerController 意图逐步推进。
UCLASS()
class DEMO_MONOPOLYAUCTION_API AMADemoGameMode : public AGameModeBase
{
	GENERATED_BODY()

public:
	AMADemoGameMode();

	virtual void BeginPlay() override;

	// --- 对外驱动 API ---

	// 初始化一局:N 名玩家 + 确定性种子。铺棋盘、发初始资金、置起点、初始化股票。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	void InitializeGame(int32 NumPlayers, int32 Seed);

	// 开始当前玩家回合(处理监狱回合开始、股票波动)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	void StartTurn();

	// 掷骰 + 移动 + 落点结算 + 双数处理(一次掷骰的完整推进)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	void RequestRollAndResolve();

	// 切到下一个存活玩家。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	void AdvanceToNextPlayer();

	// 冒烟/自动驾驶主入口:从初始化驱动整局到终局。返回胜者索引。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	int32 RunFullGameToCompletion(int32 NumPlayers, int32 Seed);

	// 当前是否游戏结束。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	bool IsGameOver() const;

	// 取本 GameMode 持有的 GameState(便捷)。
	AMADemoGameState* GetDemoGameState() const;

	// 自动驾驶:推进一回合(用于人玩模式下的 -ExecCmds 自动演示)。返回是否仍在进行。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	bool AutoAdvanceOneTurn();

	// --- 暂停(Esc 意图,试玩反馈修复轮)---

	// 切换暂停态(Esc)。暂停时掷骰/结束回合意图被拒。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	void TogglePauseState();

	// 直接设暂停态(冒烟用例直驱用)。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	void SetPauseState(bool bNewPaused);

	// 当前是否暂停。
	UFUNCTION(BlueprintCallable, Category = "Demo|Flow")
	bool IsPaused() const;

protected:
	// 棋盘数据资产类(默认用代码兜底资产)。
	UPROPERTY(EditDefaultsOnly, Category = "Demo|Config")
	TObjectPtr<UMADemoBoardDataAsset> ConfiguredBoardData;

	// 规则数据资产类。
	UPROPERTY(EditDefaultsOnly, Category = "Demo|Config")
	TObjectPtr<UMADemoRulesDataAsset> ConfiguredRulesData;

	// 当前局确定性骰子流。
	FRandomStream DiceStream;

	// 本回合内连续双数计数。
	int32 ConsecutiveDoubles = 0;

	// HUD widget(人玩模式 C++ CreateWidget 呈现)。
	UPROPERTY()
	TObjectPtr<UMADemoHUDWidget> HUDWidget;

	// --- 内部裁决 ---

	// 掷一次骰(2D6),确定性。
	FMADemoDiceResult RollDice();

	// 移动当前玩家 Steps 格(环形 28,过起点 +200)。
	void MoveCurrentPlayer(int32 Steps);

	// 玩家落点结算分发。
	void OnPlayerLanded(int32 TileIndex);

	// 地产格处理(自动购买 / 付租 / 拍卖骨架)。
	void HandlePropertyTile(int32 TileIndex);

	// 税务格处理。
	void HandleTaxTile(int32 TileIndex);

	// 前往监狱处理。
	void HandleGoToJail();

	// 监狱回合开始处理(保释 / 掷双出狱 / 满回合强制出狱)。
	void HandleJailTurnStart();

	// 支付(付不起触发破产)。返回是否成功。
	bool ProcessPayment(UMADemoPlayerData* Payer, int32 Amount, int32 ReceiverIndex);

	// 淘汰玩家(地产归无主、退场)。
	void EliminatePlayer(UMADemoPlayerData* Player);

	// 检查游戏是否结束(存活 1 人或达回合上限按净资产)。
	void CheckGameOver();

	// 自动购买策略(买得起且留够保释金缓冲才买)。
	bool AutoBuyPolicy(int32 TileIndex);

	// 刷新 HUD(人玩模式)。
	void RefreshHUD();

	// 延迟创建 HUD(确保 PC/视口就绪)。
	void CreateHUDDeferred();

private:
	// 缓存 GameState 指针。
	UPROPERTY()
	TObjectPtr<AMADemoGameState> CachedGameState;

	// 是否为人玩/自动驾驶演示模式(关卡上下文,创建 HUD)。
	bool bInteractiveContext = false;

	// 自动驾驶:启动参数请求的演示回合数(0 表示纯人玩,不自动推进)。
	int32 AutoPlayTurns = 0;

	// 自动驾驶:演示完成后是否自动截图并退出。
	bool bAutoShotAndExit = false;

	// 已自动推进的回合计数。
	int32 AutoPlayedTurns = 0;

	// 截图输出绝对路径(启动参数 -MADemoShotPath= 指定;留空则用默认 Saved 目录)。
	FString AutoShotPath;

	// 真实 Esc 路径截图:-MADemoAutoPauseShot 时延迟注入 Escape 按键事件(走输入管线)再截图退出。
	bool bAutoPauseShot = false;

	// 注入 Escape 按键事件(真实输入管线 → IntentPause → TogglePauseState)。
	void InjectEscapeKey();

	// 解析启动参数(自动驾驶演示用)。
	void ParseLaunchArgs();

	// 自动驾驶定时器回调。
	void AutoPlayTick();

	// 请求一次带 UI 的视口截图到指定路径。
	void RequestViewportScreenshot(const FString& OutPath);

	// 截图后退出的延迟回调。
	void FinishAutoShot();

	// 自动驾驶定时器句柄。
	FTimerHandle AutoPlayTimerHandle;

	// 退出延迟句柄。
	FTimerHandle QuitTimerHandle;
};
