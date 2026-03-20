// AgentBridgeGauntletController.h
// AGENT + UE5 可操作层 — Gauntlet 引擎内控制器
//
// UE5 官方模块：Gauntlet
// 基类：UGauntletTestController
//
// GauntletTestController 是 Gauntlet 在引擎进程内部的"触角"：
//   - C# 端（TestConfig）负责启动/监控/停止 Editor 进程
//   - C++ 端（TestController）负责在 Editor 内驱动测试执行
//
// 本 Controller 的职责：
//   1. OnInit：解析命令行参数（测试过滤 / Spec 路径）
//   2. OnTick：触发 Automation RunTests 并轮询完成状态
//   3. OnComplete：收集结果，设置退出码
//
// 工作流：
//   Gauntlet C# → 启动 Editor(-ExecCmds="GauntletController AgentBridgeGauntletController")
//     → Editor 实例化本 Controller
//     → OnInit() → OnTick() 轮询 → 测试完成 → EndTest(ExitCode)
//     → Gauntlet C# 收集退出码和日志

#pragma once

#include "CoreMinimal.h"
#include "GauntletTestController.h"
#include "AgentBridgeGauntletController.generated.h"

UCLASS()
class UAgentBridgeGauntletController : public UGauntletTestController
{
	GENERATED_BODY()

public:
	// ============================================================
	// UGauntletTestController 接口
	// ============================================================

	virtual void OnInit() override;
	virtual void OnTick(float TimeDelta) override;

protected:
	/** 结束测试并设置退出码 */
	void FinishWithExitCode(int32 ExitCode, const FString& Reason);

private:
	/** 测试过滤表达式（从命令行 -AgentBridgeFilter 获取） */
	FString TestFilter;

	/** Spec 路径（从命令行 -AgentBridgeSpec 获取） */
	FString SpecPath;

	/** 是否已触发测试 */
	bool bTestsTriggered = false;

	/** 是否正在等待测试完成 */
	bool bWaitingForTests = false;

	/** 等待计时器（秒） */
	float WaitTimer = 0.0f;

	/** 最大等待时间（秒） */
	float MaxWaitTime = 300.0f;

	/** 轮询间隔（秒） */
	float PollInterval = 1.0f;

	/** 轮询累计器 */
	float PollAccumulator = 0.0f;
};
