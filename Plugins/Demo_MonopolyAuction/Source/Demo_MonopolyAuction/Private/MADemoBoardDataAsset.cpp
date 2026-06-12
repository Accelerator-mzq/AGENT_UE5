// Copyright Phase14 demo agent.
#include "MADemoBoardDataAsset.h"

UMADemoBoardDataAsset::UMADemoBoardDataAsset()
{
	// 资产对象构造时即铺一份默认棋盘,保证无需手工 author .uasset 也能跑通逻辑与冒烟。
	// 编辑器中可对 Tiles 覆盖(数据驱动)。
	BuildDefaultBoard();
}

void UMADemoBoardDataAsset::BuildDefaultBoard()
{
	// 已有数据则不覆盖(尊重编辑器 author 的值)
	if (Tiles.Num() == TileCount)
	{
		return;
	}

	Tiles.Empty();
	Tiles.Reserve(TileCount);

	// 局部 lambda:追加一格。GDD 2.3 数据表逐行落地。
	auto Add = [this](int32 Index, EMADemoTileType Type, const TCHAR* Name,
		EMADemoColorGroup Color, int32 Price, int32 Rent)
	{
		FMADemoTileInfo Info;
		Info.TileIndex = Index;
		Info.TileType = Type;
		Info.Name = Name;
		Info.ColorGroup = Color;
		Info.Price = Price;
		Info.BaseRent = Rent;
		Tiles.Add(Info);
	};

	using ET = EMADemoTileType;
	using EC = EMADemoColorGroup;

	// GDD 2.3 棋盘数据表(0..27)。Price 在 Tax 格复用为缴税金额。
	Add(0,  ET::Start,       TEXT("起点"),       EC::None,      0,   0);
	Add(1,  ET::Property,    TEXT("地中海街"),   EC::Brown,     60,  4);
	Add(2,  ET::Community,   TEXT("公共基金"),   EC::None,      0,   0);
	Add(3,  ET::Property,    TEXT("波罗的海街"), EC::Brown,     80,  8);
	Add(4,  ET::Tax,         TEXT("所得税"),     EC::None,      200, 0);
	Add(5,  ET::Property,    TEXT("东方大道"),   EC::LightBlue, 100, 12);
	Add(6,  ET::Chance,      TEXT("机会"),       EC::None,      0,   0);
	Add(7,  ET::JailVisit,   TEXT("监狱探访"),   EC::None,      0,   0);
	Add(8,  ET::Property,    TEXT("佛蒙特大道"), EC::LightBlue, 120, 14);
	Add(9,  ET::Property,    TEXT("康涅狄格街"), EC::LightBlue, 140, 16);
	Add(10, ET::Property,    TEXT("圣查尔斯"),   EC::Pink,      160, 20);
	Add(11, ET::Property,    TEXT("弗吉尼亚街"), EC::Pink,      180, 22);
	Add(12, ET::Community,   TEXT("公共基金"),   EC::None,      0,   0);
	Add(13, ET::Property,    TEXT("田纳西街"),   EC::Pink,      200, 24);
	Add(14, ET::FreeParking, TEXT("免费停车"),   EC::None,      0,   0);
	Add(15, ET::Property,    TEXT("纽约大道"),   EC::Orange,    220, 28);
	// 扩展 GDD 2.2:交易所角格替换原 16 号机会格(provisional 选址)
	Add(16, ET::Exchange,    TEXT("交易所"),     EC::None,      0,   0);
	Add(17, ET::Property,    TEXT("肯塔基大道"), EC::Orange,    240, 30);
	Add(18, ET::Property,    TEXT("印第安纳街"), EC::Red,       260, 32);
	Add(19, ET::Property,    TEXT("伊利诺伊街"), EC::Red,       280, 34);
	Add(20, ET::Tax,         TEXT("奢侈税"),     EC::None,      150, 0);
	Add(21, ET::GoToJail,    TEXT("前往监狱"),   EC::None,      0,   0);
	Add(22, ET::Property,    TEXT("太平洋大道"), EC::Green,     300, 36);
	Add(23, ET::Community,   TEXT("公共基金"),   EC::None,      0,   0);
	Add(24, ET::Property,    TEXT("北卡罗来纳"), EC::Green,     320, 38);
	Add(25, ET::Property,    TEXT("宾夕法尼亚"), EC::Green,     340, 40);
	Add(26, ET::Chance,      TEXT("机会"),       EC::None,      0,   0);
	Add(27, ET::Property,    TEXT("百老汇"),     EC::Blue,      400, 50);
}
