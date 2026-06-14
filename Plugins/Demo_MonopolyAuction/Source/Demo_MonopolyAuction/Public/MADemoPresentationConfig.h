// Copyright Phase15 presentation-1. 呈现配色/布局尺寸数据资产。
// 规范 §8:呈现参数一律进 DataAsset,C++ 不硬编码可调参数。
#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "MADemoPresentationConfig.generated.h"

// 呈现配置数据资产(UDataAsset 子类)。
// CDO 默认值即运行期兜底值:无 authored .uasset 时直接用代码默认(provisional)。
// 扇出时修改本 DataAsset 实例即可改配色/布局,C++ 不改。
UCLASS(BlueprintType, meta=(DisplayName="MA Demo Presentation Config"))
class DEMO_MONOPOLYAUCTION_API UMADemoPresentationConfig : public UDataAsset
{
	GENERATED_BODY()

public:
	// --- 面板布局尺寸(像素) ---

	// 指示区(回合/阶段)面板宽度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float IndicatorPanelWidth = 560.f;

	// 指示区面板高度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float IndicatorPanelHeight = 70.f;

	// 指示区面板左上角 X 偏移(距屏幕左边)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float IndicatorPanelX = 40.f;

	// 指示区面板左上角 Y 偏移。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float IndicatorPanelY = 40.f;

	// 玩家卡片区左上角 X。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float PlayerCardPanelX = 40.f;

	// 玩家卡片区左上角 Y(指示区下方)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float PlayerCardPanelY = 120.f;

	// 单张玩家卡片宽度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float PlayerCardWidth = 260.f;

	// 单张玩家卡片高度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float PlayerCardHeight = 110.f;

	// 玩家卡片水平间距。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float PlayerCardGap = 10.f;

	// 资金条最大宽度(像素;满额 = 1500)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float MoneyBarMaxWidth = 220.f;

	// 资金条高度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float MoneyBarHeight = 10.f;

	// 拍卖弹窗宽度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float AuctionPanelWidth = 480.f;

	// 拍卖弹窗高度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float AuctionPanelHeight = 420.f;

	// 提示条左上角 X。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float HintBarX = 40.f;

	// 提示条左上角 Y(屏幕底部附近,高度 720 减 60)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float HintBarY = 660.f;

	// 提示条宽度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float HintBarWidth = 700.f;

	// 提示条高度。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	float HintBarHeight = 40.f;

	// --- 配色方案 ---

	// 面板背景色(半透明黑)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor PanelBgColor = FLinearColor(0.f, 0.f, 0.f, 0.65f);

	// 指示区背景色(深蓝半透明)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor IndicatorBgColor = FLinearColor(0.05f, 0.1f, 0.25f, 0.75f);

	// 当前玩家高亮背景色(金色)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor ActivePlayerHighlightColor = FLinearColor(0.9f, 0.75f, 0.1f, 0.4f);

	// 普通玩家卡片背景色。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor PlayerCardBgColor = FLinearColor(0.08f, 0.08f, 0.08f, 0.75f);

	// 破产玩家卡片背景色(暗红)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor BankruptCardBgColor = FLinearColor(0.25f, 0.05f, 0.05f, 0.6f);

	// 资金条底色(深灰)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor MoneyBarBgColor = FLinearColor(0.2f, 0.2f, 0.2f, 1.f);

	// 资金条前景色(绿色)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor MoneyBarFgColor = FLinearColor(0.2f, 0.8f, 0.3f, 1.f);

	// 拍卖弹窗背景色(深紫半透明)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor AuctionPanelBgColor = FLinearColor(0.1f, 0.05f, 0.2f, 0.88f);

	// 拍卖最高价高亮色(亮黄)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor AuctionHighBidColor = FLinearColor(1.f, 0.9f, 0.1f, 1.f);

	// 拍卖弹窗边框色。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor AuctionBorderColor = FLinearColor(0.6f, 0.3f, 1.f, 1.f);

	// 普通文字颜色(白)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor TextColorDefault = FLinearColor(1.f, 1.f, 1.f, 1.f);

	// 标题文字颜色(金黄)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor TextColorTitle = FLinearColor(1.f, 0.85f, 0.2f, 1.f);

	// 提示文字颜色(浅绿)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Colors")
	FLinearColor TextColorHint = FLinearColor(0.7f, 1.f, 0.7f, 1.f);

	// --- 字体尺寸 ---

	// 指示区字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 IndicatorFontSize = 20;

	// 玩家卡片名称字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 PlayerNameFontSize = 16;

	// 玩家卡片数值字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 PlayerValueFontSize = 14;

	// 拍卖标题字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 AuctionTitleFontSize = 20;

	// 拍卖最高价字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 AuctionHighBidFontSize = 18;

	// 拍卖出价记录字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 AuctionLogFontSize = 12;

	// 提示区字体大小。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Font")
	int32 HintFontSize = 14;

	// 拍卖出价记录最大显示条数(超出从顶部截断)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	int32 AuctionLogMaxLines = 6;

	// 资金条满额参考(用于比例计算,等于 StartingCash)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Layout")
	int32 MoneyBarFullAmount = 1500;

	// --- 前台外壳面板按钮样式 ---

	// 按钮背景色(普通状态,深蓝灰)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	FLinearColor ButtonBgColor = FLinearColor(0.08f, 0.12f, 0.22f, 0.9f);

	// 按钮高亮背景色(焦点/选中状态,金色)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	FLinearColor ButtonHighlightColor = FLinearColor(0.85f, 0.65f, 0.1f, 0.9f);

	// 按钮文字颜色(普通状态,白)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	FLinearColor ButtonTextColor = FLinearColor(1.f, 1.f, 1.f, 1.f);

	// 按钮文字高亮颜色(选中状态,深色以对比金底)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	FLinearColor ButtonTextHighlightColor = FLinearColor(0.08f, 0.04f, 0.0f, 1.f);

	// 按钮高度(像素)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	float ButtonHeight = 44.f;

	// 按钮间垂直间距(像素)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	float ButtonSpacing = 8.f;

	// 按钮内左侧文字 X 边距(像素)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	float ButtonPaddingX = 20.f;

	// 前台外壳面板宽度(覆盖原来的面板宽度硬编码)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	float ShellPanelWidth = 560.f;

	// 前台外壳面板左上角 X(屏幕水平中心左侧)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	float ShellPanelX = 360.f;

	// 前台外壳面板顶部 Y。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|ShellButton")
	float ShellPanelY = 160.f;

	// --- 2D 棋盘布局(presentation-2 board-2d)---

	// 棋盘格子尺寸(像素,正方形)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardTileSize = 36.f;

	// 棋盘区域左上角 X(屏幕右侧区域)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardOriginX = 680.f;

	// 棋盘区域左上角 Y。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardOriginY = 260.f;

	// 棋盘格子间距(像素)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardTileGap = 2.f;

	// 棋盘背景色(深灰半透明)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	FLinearColor BoardBgColor = FLinearColor(0.05f, 0.05f, 0.08f, 0.82f);

	// 棋盘格子默认填充色(无主地产,深灰)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	FLinearColor TileColorUnowned = FLinearColor(0.18f, 0.18f, 0.18f, 1.f);

	// 拍卖高亮边框色(拍卖中地块)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	FLinearColor TileAuctionHighlightColor = FLinearColor(1.f, 0.9f, 0.1f, 1.f);

	// 特殊格(非地产)填充色(角格/税务/机会等)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	FLinearColor TileColorSpecial = FLinearColor(0.08f, 0.08f, 0.14f, 1.f);

	// 各地产组配色(按 EMADemoColorGroup 顺序:None/Brown/LightBlue/Pink/Orange/Red/Green/Blue)。
	// 索引对应枚举值(0=None, 1=Brown, 2=LightBlue, 3=Pink, 4=Orange, 5=Red, 6=Green, 7=Blue)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	TArray<FLinearColor> ColorGroupPalette = {
		FLinearColor(0.18f, 0.18f, 0.18f, 1.f),   // None(灰)
		FLinearColor(0.45f, 0.25f, 0.08f, 1.f),   // Brown(棕)
		FLinearColor(0.45f, 0.78f, 0.95f, 1.f),   // LightBlue(浅蓝)
		FLinearColor(0.85f, 0.45f, 0.65f, 1.f),   // Pink(粉)
		FLinearColor(0.95f, 0.55f, 0.1f, 1.f),    // Orange(橙)
		FLinearColor(0.9f, 0.18f, 0.18f, 1.f),    // Red(红)
		FLinearColor(0.15f, 0.72f, 0.3f, 1.f),    // Green(绿)
		FLinearColor(0.15f, 0.38f, 0.88f, 1.f),   // Blue(蓝)
	};

	// 玩家归属色(按玩家索引 0~3:P1 赤/P2 青/P3 黄/P4 紫)。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	TArray<FLinearColor> PlayerOwnershipColors = {
		FLinearColor(0.95f, 0.25f, 0.25f, 0.85f), // P1 红
		FLinearColor(0.25f, 0.85f, 0.95f, 0.85f), // P2 青
		FLinearColor(0.95f, 0.85f, 0.2f, 0.85f),  // P3 黄
		FLinearColor(0.65f, 0.25f, 0.9f, 0.85f),  // P4 紫
	};

	// --- 棋盘玩家 Token 尺寸(feedback-1 反馈回流:token 可辨识性改进) ---

	// 普通玩家 token 边长(像素)。反馈前为 10px;放大至 14px 改善远观可辨识性。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardTokenSize = 14.f;

	// 当前回合玩家 token 边长(像素)。反馈前为 13px;放大至 18px 并配合加粗描边+浮标。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardTokenActiveSize = 18.f;

	// 当前回合 token 外描边宽度(像素,四周均匀)。反馈前为 2px;加粗至 3px。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardTokenActiveStrokeWidth = 3.f;

	// 当前回合 token 浮标三角高度(像素,显示在 token 正上方)。0 = 不显示。
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Presentation|Board2D")
	float BoardTokenActiveMarkerHeight = 6.f;
};
