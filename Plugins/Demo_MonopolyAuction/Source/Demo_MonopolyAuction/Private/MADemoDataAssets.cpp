// Copyright Phase14 v0 attempt2. 数据驱动资产实现。
#include "MADemoDataAssets.h"

// 构造时铺默认棋盘,保证代码默认资产可兜底(无需 author DataAsset 实例)。
UMADemoBoardDataAsset::UMADemoBoardDataAsset()
{
	BuildDefaultBoard();
}

// 内部小工具:构造单格信息。
static FMADemoTileInfo MakeTile(EMADemoTileType InType, const TCHAR* InName,
	EMADemoColorGroup InColor, int32 InPrice, int32 InRent)
{
	FMADemoTileInfo Info;
	Info.TileType = InType;
	Info.Name = InName;
	Info.ColorGroup = InColor;
	Info.Price = InPrice;
	Info.BaseRent = InRent;
	return Info;
}

// 铺 28 格棋盘(GDD 2.3 数据表)。16 号原机会格替换为交易所(GDD 2.2 扩展)。
void UMADemoBoardDataAsset::BuildDefaultBoard()
{
	Tiles.Empty();
	Tiles.Reserve(28);

	// 0  起点
	Tiles.Add(MakeTile(EMADemoTileType::Start, TEXT("起点"), EMADemoColorGroup::None, 0, 0));
	// 1  地中海街 Brown 60/4
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("地中海街"), EMADemoColorGroup::Brown, 60, 4));
	// 2  公共基金
	Tiles.Add(MakeTile(EMADemoTileType::Community, TEXT("公共基金"), EMADemoColorGroup::None, 0, 0));
	// 3  波罗的海街 Brown 80/8
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("波罗的海街"), EMADemoColorGroup::Brown, 80, 8));
	// 4  所得税(缴 200)
	Tiles.Add(MakeTile(EMADemoTileType::Tax, TEXT("所得税"), EMADemoColorGroup::None, 200, 0));
	// 5  东方大道 LightBlue 100/12
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("东方大道"), EMADemoColorGroup::LightBlue, 100, 12));
	// 6  机会
	Tiles.Add(MakeTile(EMADemoTileType::Chance, TEXT("机会"), EMADemoColorGroup::None, 0, 0));
	// 7  监狱探访
	Tiles.Add(MakeTile(EMADemoTileType::JailVisit, TEXT("监狱探访"), EMADemoColorGroup::None, 0, 0));
	// 8  佛蒙特大道 LightBlue 120/14
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("佛蒙特大道"), EMADemoColorGroup::LightBlue, 120, 14));
	// 9  康涅狄格街 LightBlue 140/16
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("康涅狄格街"), EMADemoColorGroup::LightBlue, 140, 16));
	// 10 圣查尔斯 Pink 160/20
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("圣查尔斯"), EMADemoColorGroup::Pink, 160, 20));
	// 11 弗吉尼亚街 Pink 180/22
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("弗吉尼亚街"), EMADemoColorGroup::Pink, 180, 22));
	// 12 公共基金
	Tiles.Add(MakeTile(EMADemoTileType::Community, TEXT("公共基金"), EMADemoColorGroup::None, 0, 0));
	// 13 田纳西街 Pink 200/24
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("田纳西街"), EMADemoColorGroup::Pink, 200, 24));
	// 14 免费停车
	Tiles.Add(MakeTile(EMADemoTileType::FreeParking, TEXT("免费停车"), EMADemoColorGroup::None, 0, 0));
	// 15 纽约大道 Orange 220/28
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("纽约大道"), EMADemoColorGroup::Orange, 220, 28));
	// 16 交易所(替换原机会格,GDD 2.2 扩展)
	Tiles.Add(MakeTile(EMADemoTileType::StockExchange, TEXT("交易所"), EMADemoColorGroup::None, 0, 0));
	// 17 肯塔基大道 Orange 240/30
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("肯塔基大道"), EMADemoColorGroup::Orange, 240, 30));
	// 18 印第安纳街 Red 260/32
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("印第安纳街"), EMADemoColorGroup::Red, 260, 32));
	// 19 伊利诺伊街 Red 280/34
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("伊利诺伊街"), EMADemoColorGroup::Red, 280, 34));
	// 20 奢侈税(缴 150)
	Tiles.Add(MakeTile(EMADemoTileType::Tax, TEXT("奢侈税"), EMADemoColorGroup::None, 150, 0));
	// 21 前往监狱
	Tiles.Add(MakeTile(EMADemoTileType::GoToJail, TEXT("前往监狱"), EMADemoColorGroup::None, 0, 0));
	// 22 太平洋大道 Green 300/36
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("太平洋大道"), EMADemoColorGroup::Green, 300, 36));
	// 23 公共基金
	Tiles.Add(MakeTile(EMADemoTileType::Community, TEXT("公共基金"), EMADemoColorGroup::None, 0, 0));
	// 24 北卡罗来纳 Green 320/38
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("北卡罗来纳"), EMADemoColorGroup::Green, 320, 38));
	// 25 宾夕法尼亚 Green 340/40
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("宾夕法尼亚"), EMADemoColorGroup::Green, 340, 40));
	// 26 机会
	Tiles.Add(MakeTile(EMADemoTileType::Chance, TEXT("机会"), EMADemoColorGroup::None, 0, 0));
	// 27 百老汇 Blue 400/50
	Tiles.Add(MakeTile(EMADemoTileType::Property, TEXT("百老汇"), EMADemoColorGroup::Blue, 400, 50));

	StartTileIndex = 0;
	JailVisitTileIndex = 7;
	FreeParkingTileIndex = 14;
	GoToJailTileIndex = 21;
	StockExchangeTileIndex = 16;
}

// 规则资产构造:全部使用契约硬约束默认值(已在头文件成员初始化)。
UMADemoRulesDataAsset::UMADemoRulesDataAsset()
{
}
