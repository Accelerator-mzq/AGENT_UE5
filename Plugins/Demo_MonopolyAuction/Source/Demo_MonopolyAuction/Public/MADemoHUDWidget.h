// Copyright Phase14 demo agent.
// HUD 常驻界面 Widget 基类。只读 GameState,展示当前回合/当前玩家/各玩家资金/骰子结果/股票摘要。
// GDD 4.1 + 扩展 4.1:常驻显示玩家股票持仓总市值与 3 支股票现价摘要。
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MADemoHUDWidget.generated.h"

class AMADemoGameState;

// HUD 数据快照(C++ 计算好喂给蓝图绑定,避免热路径字符串拼接)。
USTRUCT(BlueprintType)
struct FMADemoHUDSnapshot
{
	GENERATED_BODY()

	// 当前回合数
	UPROPERTY(BlueprintReadOnly, Category = "HUD")
	int32 TurnNumber = 0;

	// 当前玩家显示名
	UPROPERTY(BlueprintReadOnly, Category = "HUD")
	FString CurrentPlayerName;

	// 当前玩家颜色
	UPROPERTY(BlueprintReadOnly, Category = "HUD")
	FLinearColor CurrentPlayerColor = FLinearColor::White;

	// 各玩家资金摘要文本(每行一名玩家:名/现金/股票市值)
	UPROPERTY(BlueprintReadOnly, Category = "HUD")
	TArray<FString> PlayerSummaries;

	// 最近骰子结果文本
	UPROPERTY(BlueprintReadOnly, Category = "HUD")
	FString DiceResultText;

	// 3 支股票现价摘要文本
	UPROPERTY(BlueprintReadOnly, Category = "HUD")
	FString StockSummaryText;
};

// HUD Widget。蓝图子类绑定 TextBlock 等控件,数据由 BuildSnapshot 提供。
UCLASS(BlueprintType, Blueprintable)
class DEMO_MONOPOLYAUCTION_API UMADemoHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	// 绑定的 GameState(只读引用)
	UPROPERTY(BlueprintReadWrite, Category = "HUD")
	TObjectPtr<AMADemoGameState> BoundGameState;

	// 从 GameState 计算一份 HUD 快照(不修改任何状态)。
	UFUNCTION(BlueprintCallable, Category = "HUD")
	FMADemoHUDSnapshot BuildSnapshot() const;

	// 刷新事件:蓝图可重写,把快照绑到控件上。
	UFUNCTION(BlueprintImplementableEvent, Category = "HUD")
	void OnHUDRefreshed(const FMADemoHUDSnapshot& Snapshot);

	// 主动刷新:计算快照并广播给蓝图。
	UFUNCTION(BlueprintCallable, Category = "HUD")
	void RefreshHUD();
};
