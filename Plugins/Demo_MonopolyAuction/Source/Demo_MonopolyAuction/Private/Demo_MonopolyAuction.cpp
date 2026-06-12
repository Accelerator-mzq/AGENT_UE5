// Copyright Phase14 v0 attempt2. 模块入口实现。
#include "Demo_MonopolyAuction.h"

#define LOCTEXT_NAMESPACE "FDemo_MonopolyAuctionModule"

// 模块无运行时初始化需求,留空实现即可。
void FDemo_MonopolyAuctionModule::StartupModule()
{
}

void FDemo_MonopolyAuctionModule::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE

// 注册模块到引擎。
IMPLEMENT_MODULE(FDemo_MonopolyAuctionModule, Demo_MonopolyAuction)
