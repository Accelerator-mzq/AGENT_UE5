// Copyright Phase14 demo agent.
#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

// Demo_MonopolyAuction 运行时模块入口。仅做模块生命周期登记,无额外逻辑。
class FDemo_MonopolyAuctionModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
