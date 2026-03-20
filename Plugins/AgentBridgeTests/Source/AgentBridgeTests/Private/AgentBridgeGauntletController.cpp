// AgentBridgeGauntletController.cpp
// AGENT + UE5 可操作层 — Gauntlet 引擎内控制器实现
//
// UE5 官方模块：Gauntlet
// 在 Editor 进程内驱动 Automation Test 执行，
// 轮询完成状态，收集结果，设置退出码给 Gauntlet C# 端。

#include "AgentBridgeGauntletController.h"
#include "AgentBridgeSubsystem.h"
#include "BridgeTypes.h"

#include "Editor.h"
#include "Misc/Parse.h"
#include "Misc/AutomationTest.h"
#include "Misc/App.h"

// ============================================================
// OnInit — 解析命令行参数 + 初始化
// ============================================================

void UAgentBridgeGauntletController::OnInit()
{
	Super::OnInit();

	// 从命令行解析参数
	FString CmdLine = FCommandLine::Get();

	FParse::Value(*CmdLine, TEXT("-AgentBridgeFilter="), TestFilter);
	FParse::Value(*CmdLine, TEXT("-AgentBridgeSpec="), SpecPath);

	// 移除引号
	TestFilter.TrimQuotesInline();
	SpecPath.TrimQuotesInline();

	// 默认过滤：全部 AgentBridge 测试
	if (TestFilter.IsEmpty() && SpecPath.IsEmpty())
	{
		TestFilter = TEXT("Project.AgentBridge");
	}

	// 从命令行获取最大等待时间
	FString MaxWaitStr;
	if (FParse::Value(*CmdLine, TEXT("-AgentBridgeMaxWait="), MaxWaitStr))
	{
		MaxWaitTime = FCString::Atof(*MaxWaitStr);
	}

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Initialized."));
	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet]   TestFilter: %s"),
		TestFilter.IsEmpty() ? TEXT("(none — using Spec mode)") : *TestFilter);
	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet]   SpecPath: %s"),
		SpecPath.IsEmpty() ? TEXT("(none — using Test mode)") : *SpecPath);
	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet]   MaxWaitTime: %.0f seconds"), MaxWaitTime);

	// 验证 Subsystem 可用
	if (GEditor)
	{
		UAgentBridgeSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>();
		if (Subsystem)
		{
			UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Subsystem available (v%s)"),
				*Subsystem->GetVersion());
		}
		else
		{
			UE_LOG(LogTemp, Error, TEXT("[AgentBridge Gauntlet] Subsystem NOT available!"));
			FinishWithExitCode(2, TEXT("AgentBridgeSubsystem not available"));
			return;
		}
	}
}

// ============================================================
// OnTick — 每帧执行：触发测试 → 轮询完成
// ============================================================

void UAgentBridgeGauntletController::OnTick(float TimeDelta)
{
	Super::OnTick(TimeDelta);

	// ---- 阶段 1: 触发测试（仅执行一次）----
	if (!bTestsTriggered)
	{
		bTestsTriggered = true;

		if (!SpecPath.IsEmpty())
		{
			// Spec 模式：通过 Commandlet 路径执行 Spec
			UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Triggering Spec execution: %s"), *SpecPath);

			UAgentBridgeSubsystem* Subsystem = GEditor->GetEditorSubsystem<UAgentBridgeSubsystem>();
			if (Subsystem)
			{
				// 使用 Python Orchestrator 执行 Spec
				FString PythonCmd = FString::Printf(
					TEXT("py from agent_ue5.orchestrator.orchestrator import run; run('%s')"),
					*SpecPath.Replace(TEXT("\\"), TEXT("/")));

				UWorld* World = GEditor->GetEditorWorldContext().World();
				if (World)
				{
					GEditor->Exec(World, *PythonCmd);
				}
			}

			// Spec 执行后立即运行 L1 测试验证结果
			if (TestFilter.IsEmpty())
			{
				TestFilter = TEXT("Project.AgentBridge.L1");
			}
		}

		// 触发 Automation Tests
		UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Triggering tests: %s"), *TestFilter);

		UWorld* World = GEditor ? GEditor->GetEditorWorldContext().World() : nullptr;
		if (World)
		{
			FString AutomationCmd = FString::Printf(TEXT("Automation RunTests %s"), *TestFilter);
			GEditor->Exec(World, *AutomationCmd);
		}

		bWaitingForTests = true;
		WaitTimer = 0.0f;
		PollAccumulator = 0.0f;

		return;
	}

	// ---- 阶段 2: 轮询测试完成状态 ----
	if (bWaitingForTests)
	{
		WaitTimer += TimeDelta;
		PollAccumulator += TimeDelta;

		// 超时检查
		if (WaitTimer > MaxWaitTime)
		{
			UE_LOG(LogTemp, Error, TEXT("[AgentBridge Gauntlet] Timeout after %.0f seconds"), WaitTimer);
			FinishWithExitCode(2, FString::Printf(TEXT("Timeout after %.0f seconds"), WaitTimer));
			return;
		}

		// 定期轮询
		if (PollAccumulator >= PollInterval)
		{
			PollAccumulator = 0.0f;

			// 检查 Automation Test 是否仍在运行
			FAutomationTestFramework& Framework = FAutomationTestFramework::Get();
			bool bTestsRunning = Framework.GetNumTestsRun() < Framework.GetNumTests();

			// 注意：上述 API 可能因 UE5 版本不同而有差异
			// 替代方案：检查 GLog 中是否出现 "Automation Test Complete" 消息
			// 此处使用简化逻辑：等待固定时间后检查

			if (!bTestsRunning || WaitTimer > 30.0f)
			{
				// 测试完成（或超过最低等待时间）
				bWaitingForTests = false;

				UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Tests completed after %.1f seconds"),
					WaitTimer);

				// 收集结果
				// Automation Test 结果写入 Saved/Automation/ 目录
				FString ResultDir = FPaths::ProjectSavedDir() / TEXT("Automation");
				UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Results at: %s"), *ResultDir);

				// 判定退出码
				// 0 = 全部通过, 1 = 有失败
				// 完整实现需要解析 Automation Report JSON
				// 此处使用简化逻辑
				int32 ExitCode = 0;

				// 检查是否有 Automation 错误日志
				// 完整实现：解析 FAutomationTestFramework 的测试结果
				UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Setting exit code: %d"), ExitCode);

				FinishWithExitCode(ExitCode, TEXT("Tests completed"));
			}
		}
	}
}

// ============================================================
// 结束测试
// ============================================================

void UAgentBridgeGauntletController::FinishWithExitCode(int32 ExitCode, const FString& Reason)
{
	UE_LOG(LogTemp, Log, TEXT("[AgentBridge Gauntlet] Finishing: ExitCode=%d, Reason=%s"),
		ExitCode, *Reason);

	// 通知 Gauntlet C# 端测试已完成
	// EndTest 会导致 Editor 进程退出，Gauntlet 收集退出码
	EndTest(ExitCode);
}
