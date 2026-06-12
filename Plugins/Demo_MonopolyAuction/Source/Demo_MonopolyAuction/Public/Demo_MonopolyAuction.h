// Copyright Phase14 v0 attempt2. 模块入口头文件。
#pragma once

#include "CoreMinimal.h"
#include "Modules/ModuleManager.h"

// Demo_MonopolyAuction 运行时模块。无特殊启动逻辑,使用默认模块实现即可。
class FDemo_MonopolyAuctionModule : public IModuleInterface
{
public:
	virtual void StartupModule() override;
	virtual void ShutdownModule() override;
};
