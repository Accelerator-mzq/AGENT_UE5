// Copyright Phase14 v0 attempt2. 常驻 HUD widget(真实呈现于 -game 画面)。
#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "MADemoTypes.h"
#include "MADemoHUDWidget.generated.h"

class AMADemoGameState;
class UTextBlock;
class UVerticalBox;
class UBorder;

// HUD 常驻只读快照 widget。
// v0 用 C++ 在 NativeConstruct 里以代码构建 Slate 文本块(无需 WBP),
// 每帧 NativePaint 前由 NativeTick 拉 GameState 最新状态刷新,保证键盘推进后画面实时变化。
UCLASS()
class DEMO_MONOPOLYAUCTION_API UMADemoHUDWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	// 绑定 GameState(由 GameMode 创建后调用)。
	void BindGameState(AMADemoGameState* InGameState);

	// 主动刷新一次(GameMode 推进后调用)。
	UFUNCTION(BlueprintCallable, Category = "Demo|HUD")
	void RefreshHUD();

	// 由 GameState 产出当前快照(纯逻辑,可被冒烟断言)。
	UFUNCTION(BlueprintCallable, Category = "Demo|HUD")
	FMADemoHUDSnapshot BuildSnapshot() const;

	// 蓝图可绑定的刷新事件(扇出时自定义可视化)。
	UFUNCTION(BlueprintImplementableEvent, Category = "Demo|HUD")
	void OnHUDRefreshed(const FMADemoHUDSnapshot& Snapshot);

protected:
	virtual void NativeConstruct() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

	// 运行期 GameState 引用。
	UPROPERTY()
	TObjectPtr<AMADemoGameState> GameStateRef;

	// 代码构建的文本块(顶部状态行 + 玩家列表 + 股票行 + 提示行)。
	UPROPERTY()
	TObjectPtr<UTextBlock> TitleText;

	UPROPERTY()
	TObjectPtr<UTextBlock> StatusText;

	UPROPERTY()
	TObjectPtr<UTextBlock> PlayersText;

	UPROPERTY()
	TObjectPtr<UTextBlock> StockText;

	UPROPERTY()
	TObjectPtr<UTextBlock> HintText;

	// 把快照渲染成可见文本。
	void ApplySnapshotToText(const FMADemoHUDSnapshot& Snap);
};
