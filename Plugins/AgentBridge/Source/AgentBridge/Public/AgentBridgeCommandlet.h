// AgentBridgeCommandlet.h
// AGENT + UE5 可操作层 — Commandlet 无头执行入口
//
// UE5 官方模块：Command-Line / Commandlet
//
// 用途：
//   1. 无头执行 Spec 文件（CI/CD 中自动化场景布局）
//   2. 无头运行 Automation Test（CI/CD 中自动化测试）
//   3. 无头执行单个 Bridge 工具（脚本化批处理）
//
// 调用方式：
//   # 执行 Spec
//   UE5Editor-Cmd.exe MyGame.uproject -run=AgentBridge \
//       -Spec="AgentSpecs/levels/warehouse.yaml" \
//       -Report="Artifacts/reports/warehouse_report.json" \
//       -Unattended -NoPause -NullRHI
//
//   # 运行 Automation Test
//   UE5Editor-Cmd.exe MyGame.uproject -run=AgentBridge \
//       -RunTests="Project.AgentBridge.L1" \
//       -Report="Artifacts/test_report.json" \
//       -Unattended -NoPause -NullRHI
//
//   # 执行单个工具
//   UE5Editor-Cmd.exe MyGame.uproject -run=AgentBridge \
//       -Tool="ListLevelActors" \
//       -Unattended -NoPause -NullRHI
//
// 退出码：
//   0 = 全部成功
//   1 = 存在 mismatch 或 warning
//   2 = 存在 failed 或参数错误

#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"
#include "AgentBridgeCommandlet.generated.h"

UCLASS()
class AGENTBRIDGE_API UAgentBridgeCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	UAgentBridgeCommandlet();

	//~ Begin UCommandlet Interface
	virtual int32 Main(const FString& Params) override;
	//~ End UCommandlet Interface

private:
	/** 解析命令行参数 */
	void ParseParams(const FString& Params);

	/** 模式 1：执行 Spec 文件 */
	int32 RunSpec();

	/** 模式 2：运行 Automation Test */
	int32 RunTests();

	/** 模式 3：执行单个 Bridge 工具 */
	int32 RunSingleTool();

	/** 输出报告到文件 */
	void WriteReport(const FString& JsonContent);

	// 解析后的参数
	FString SpecPath;
	FString TestFilter;
	FString ToolName;
	FString ReportPath;
};
