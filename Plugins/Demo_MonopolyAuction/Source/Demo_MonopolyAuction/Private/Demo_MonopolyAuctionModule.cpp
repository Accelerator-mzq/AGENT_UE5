// Copyright Phase14 demo agent.
#include "Demo_MonopolyAuctionModule.h"

#define LOCTEXT_NAMESPACE "FDemo_MonopolyAuctionModule"

// 模块启动:demo 不需要运行期注册项,留空即可。
void FDemo_MonopolyAuctionModule::StartupModule()
{
}

// 模块卸载:无资源需释放。
void FDemo_MonopolyAuctionModule::ShutdownModule()
{
}

#undef LOCTEXT_NAMESPACE

// 以模块名注册:供 UBT 发现 Runtime 模块。
IMPLEMENT_MODULE(FDemo_MonopolyAuctionModule, Demo_MonopolyAuction)
