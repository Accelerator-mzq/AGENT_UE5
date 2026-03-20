// AgentBridgeTestsModule.cpp
// AGENT + UE5 可操作层 — 测试 Plugin 模块注册

#include "Modules/ModuleManager.h"
#include "Modules/ModuleInterface.h"

class FAgentBridgeTestsModule : public IModuleInterface
{
public:
	virtual void StartupModule() override
	{
		UE_LOG(LogTemp, Log, TEXT("[AgentBridgeTests] Test plugin loaded. L1/L2/L3 tests registered."));
	}

	virtual void ShutdownModule() override
	{
		UE_LOG(LogTemp, Log, TEXT("[AgentBridgeTests] Test plugin unloaded."));
	}
};

IMPLEMENT_MODULE(FAgentBridgeTestsModule, AgentBridgeTests)
