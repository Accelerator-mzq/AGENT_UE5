// Copyright Phase14 v0 attempt2. Canvas HUD(保证截图可见的画面 HUD)。
#pragma once

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "MADemoHUD.generated.h"

class AMADemoGameState;

// 基于 AHUD 的画面 HUD:在 DrawHUD 里用 Canvas->DrawText 直接绘制到渲染帧。
// 这条路径绘制进场景视口画布,会被 -game 截图真实捕获(UMG/Slate 叠加层在标准截图里不稳定)。
// 与 UMADemoHUDWidget 并存:widget 走契约/交互/冒烟,Canvas HUD 走截图可见呈现。
UCLASS()
class DEMO_MONOPOLYAUCTION_API AMADemoHUD : public AHUD
{
	GENERATED_BODY()

public:
	virtual void BeginPlay() override;
	virtual void DrawHUD() override;

private:
	// 取当前 demo GameState。
	AMADemoGameState* GetDemoGameState() const;

	// 当前要绘制的面板名(由启动参数 -MADemoPanel= 指定;空=对局 HUD)。
	FString PanelMode;

	// 绘制对局 HUD(回合/玩家/股市)。
	void DrawGameHUD();

	// 绘制一个前台外壳面板(标题 + 条目列表)。
	void DrawShellPanel(const FString& Title, const TArray<FString>& Items);

	// 按 PanelMode 选择绘制内容。
	void DrawSelectedPanel();

	// 拍卖面板(增量批 1,GDD 3.1):标的/底价/起拍价、最高价+出价人(高亮)、
	// 轮到谁、各玩家弃权状态、出价记录滚动、键位提示。拍卖进行中渲染于屏幕中央。
	void DrawAuctionPanel();
};
