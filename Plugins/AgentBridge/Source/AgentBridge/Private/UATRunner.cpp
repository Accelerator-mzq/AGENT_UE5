// UATRunner.cpp
// AGENT + UE5 可操作层 — UAT 子进程封装实现
//
// UE5 官方模块：UAT (Unreal Automation Tool)
// UAT 运行在引擎进程外部（C#），通过 FPlatformProcess::CreateProc 启动。

#include "UATRunner.h"
#include "Misc/Paths.h"
#include "Misc/FileHelper.h"
#include "HAL/PlatformProcess.h"
#include "HAL/PlatformFileManager.h"

FUATRunner::FUATRunner()
{
	RunUATPath = DetectRunUATPath();
	ProjectPath = FPaths::GetProjectFilePath();
}

// ============================================================
// 路径检测
// ============================================================

FString FUATRunner::DetectRunUATPath() const
{
	FString EngineDir = FPaths::EngineDir();

#if PLATFORM_WINDOWS
	FString Path = EngineDir / TEXT("Build/BatchFiles/RunUAT.bat");
#elif PLATFORM_LINUX || PLATFORM_MAC
	FString Path = EngineDir / TEXT("Build/BatchFiles/RunUAT.sh");
#else
	FString Path = EngineDir / TEXT("Build/BatchFiles/RunUAT.bat");
#endif

	return FPaths::ConvertRelativePathToFull(Path);
}

bool FUATRunner::IsUATAvailable() const
{
	return FPaths::FileExists(RunUATPath);
}

// ============================================================
// 核心执行
// ============================================================

FUATRunResult FUATRunner::ExecuteUAT(const FString& Args, bool bSync)
{
	FUATRunResult Result;
	Result.CommandLine = FString::Printf(TEXT("%s %s"), *RunUATPath, *Args);

	// 检查 RunUAT 存在
	if (!IsUATAvailable())
	{
		Result.bLaunched = false;
		Result.ErrorMessage = FString::Printf(TEXT("RunUAT not found at: %s"), *RunUATPath);
		UE_LOG(LogTemp, Error, TEXT("[AgentBridge UAT] %s"), *Result.ErrorMessage);
		return Result;
	}

	UE_LOG(LogTemp, Log, TEXT("[AgentBridge UAT] Executing: %s"), *Result.CommandLine);

	if (bSync)
	{
		// 同步模式：阻塞等待 UAT 完成
		int32 ReturnCode = -1;
		FString StdOut;
		FString StdErr;

		FPlatformProcess::ExecProcess(
			*RunUATPath,
			*Args,
			&ReturnCode,
			&StdOut,
			&StdErr
		);

		Result.bLaunched = true;
		Result.bCompleted = true;
		Result.ExitCode = ReturnCode;
		Result.StdOut = StdOut;
		Result.StdErr = StdErr;

		if (ReturnCode == 0)
		{
			UE_LOG(LogTemp, Log, TEXT("[AgentBridge UAT] Completed successfully (exit code 0)"));
		}
		else
		{
			UE_LOG(LogTemp, Warning, TEXT("[AgentBridge UAT] Completed with exit code: %d"), ReturnCode);
			if (!StdErr.IsEmpty())
			{
				UE_LOG(LogTemp, Warning, TEXT("[AgentBridge UAT] StdErr: %s"), *StdErr);
			}
		}
	}
	else
	{
		// 异步模式：启动后立即返回
		FProcHandle ProcHandle = FPlatformProcess::CreateProc(
			*RunUATPath,
			*Args,
			/*bLaunchDetached=*/true,
			/*bLaunchHidden=*/false,
			/*bLaunchReallyHidden=*/false,
			/*OutProcessID=*/nullptr,
			/*PriorityModifier=*/0,
			/*OptionalWorkingDirectory=*/nullptr,
			/*PipeWriteChild=*/nullptr
		);

		Result.bLaunched = ProcHandle.IsValid();
		Result.bCompleted = false;
		Result.ExitCode = -1;

		if (!Result.bLaunched)
		{
			Result.ErrorMessage = FString::Printf(TEXT("Failed to launch process: %s"), *RunUATPath);
			UE_LOG(LogTemp, Error, TEXT("[AgentBridge UAT] %s"), *Result.ErrorMessage);
		}
		else
		{
			UE_LOG(LogTemp, Log, TEXT("[AgentBridge UAT] Process launched (async mode)"));
		}
	}

	return Result;
}

// ============================================================
// BuildCookRun
// UAT 命令: BuildCookRun -project=... -platform=... -build -cook -stage -pak
// ============================================================

FUATRunResult FUATRunner::BuildCookRun(
	const FString& Platform,
	const FString& Configuration,
	bool bSync)
{
	FString Args = FString::Printf(
		TEXT("BuildCookRun")
		TEXT(" -project=\"%s\"")
		TEXT(" -platform=%s")
		TEXT(" -clientconfig=%s")
		TEXT(" -build -cook -stage -pak")
		TEXT(" -unattended -utf8output"),
		*ProjectPath,
		*Platform,
		*Configuration
	);

	return ExecuteUAT(Args, bSync);
}

// ============================================================
// RunAutomationTests
// UAT 命令: RunAutomationTests -project=... -filter=...
// ============================================================

FUATRunResult FUATRunner::RunAutomationTests(
	const FString& Filter,
	const FString& ReportPath,
	bool bSync)
{
	FString Args = FString::Printf(
		TEXT("RunAutomationTests")
		TEXT(" -project=\"%s\"")
		TEXT(" -filter=\"%s\"")
		TEXT(" -unattended -utf8output -nullrhi"),
		*ProjectPath,
		*Filter
	);

	if (!ReportPath.IsEmpty())
	{
		Args += FString::Printf(TEXT(" -ReportOutputPath=\"%s\""), *ReportPath);
	}

	return ExecuteUAT(Args, bSync);
}

// ============================================================
// RunGauntlet
// UAT 命令: RunGauntlet -Test=... -project=...
// ============================================================

FUATRunResult FUATRunner::RunGauntlet(
	const FString& TestConfigName,
	bool bSync)
{
	FString Args = FString::Printf(
		TEXT("RunGauntlet")
		TEXT(" -project=\"%s\"")
		TEXT(" -Test=%s")
		TEXT(" -unattended -utf8output"),
		*ProjectPath,
		*TestConfigName
	);

	return ExecuteUAT(Args, bSync);
}

// ============================================================
// RunCustomCommand
// ============================================================

FUATRunResult FUATRunner::RunCustomCommand(
	const FString& UATCommand,
	bool bSync)
{
	FString Args = FString::Printf(
		TEXT("%s -project=\"%s\" -unattended -utf8output"),
		*UATCommand,
		*ProjectPath
	);

	return ExecuteUAT(Args, bSync);
}
