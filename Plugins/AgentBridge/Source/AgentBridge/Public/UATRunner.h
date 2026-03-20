// UATRunner.h
// AGENT + UE5 可操作层 — UAT (Unreal Automation Tool) 子进程封装
//
// UE5 官方模块：UAT (Unreal Automation Tool)
//
// UAT 是 UE5 的外部宿主程序（C#），通过 RunUAT.bat/.sh 启动。
// 本类封装 UAT 子进程调用，提供以下能力：
//   - BuildCookRun：编译 + 烹饪 + 打包
//   - RunAutomationTests：通过 UAT 运行自动化测试
//   - RunGauntlet：启动 Gauntlet 测试会话
//
// 与 Commandlet 的层次关系：
//   UAT 运行在引擎进程**外部**（C#）
//   Commandlet 运行在引擎进程**内部**（C++）
//   UAT 可以调用 Commandlet，不是并列关系
//
// 调用链：
//   AgentBridgeSubsystem::BuildProject()
//     → FUATRunner::BuildCookRun()
//       → FPlatformProcess::CreateProc("RunUAT.bat", args)
//         → UAT 外部进程

#pragma once

#include "CoreMinimal.h"
#include "HAL/PlatformProcess.h"

/**
 * UAT 子进程运行结果。
 */
struct AGENTBRIDGE_API FUATRunResult
{
	/** UAT 是否成功启动 */
	bool bLaunched = false;

	/** UAT 进程是否已完成（仅同步模式） */
	bool bCompleted = false;

	/** UAT 退出码（0=成功，仅同步模式可用） */
	int32 ExitCode = -1;

	/** 完整的 UAT 命令行（用于日志和调试） */
	FString CommandLine;

	/** 标准输出（仅同步模式且 bCaptureOutput=true 时填充） */
	FString StdOut;

	/** 标准错误（仅同步模式且 bCaptureOutput=true 时填充） */
	FString StdErr;

	/** 错误消息（启动失败时填充） */
	FString ErrorMessage;

	bool IsSuccess() const { return bLaunched && bCompleted && ExitCode == 0; }
};

/**
 * UAT 子进程封装。
 * 非 UObject——纯 C++ 工具类，可在任何线程使用。
 */
class AGENTBRIDGE_API FUATRunner
{
public:
	FUATRunner();

	// ============================================================
	// 核心操作
	// ============================================================

	/**
	 * 执行 BuildCookRun（编译 + 烹饪 + 打包）。
	 * 对应 UAT 命令：RunUAT BuildCookRun -project=... -platform=... -build -cook -stage -pak
	 *
	 * @param Platform    目标平台（Win64 / Linux / Mac / Android / IOS）
	 * @param Configuration 构建配置（Development / Shipping / DebugGame）
	 * @param bSync       是否同步等待完成（true=阻塞直到 UAT 退出，false=启动后立即返回）
	 */
	FUATRunResult BuildCookRun(
		const FString& Platform = TEXT("Win64"),
		const FString& Configuration = TEXT("Development"),
		bool bSync = false
	);

	/**
	 * 通过 UAT 运行自动化测试。
	 * 对应 UAT 命令：RunUAT RunAutomationTests -project=... -filter=...
	 *
	 * @param Filter      测试过滤表达式（如 "Project.AgentBridge"）
	 * @param ReportPath  报告输出路径
	 * @param bSync       是否同步等待完成
	 */
	FUATRunResult RunAutomationTests(
		const FString& Filter,
		const FString& ReportPath = TEXT(""),
		bool bSync = false
	);

	/**
	 * 启动 Gauntlet 测试会话。
	 * 对应 UAT 命令：RunUAT RunGauntlet -Test=... -project=...
	 *
	 * @param TestConfigName  Gauntlet 测试配置名（对应 .cs 文件中的类名）
	 * @param bSync           是否同步等待完成
	 */
	FUATRunResult RunGauntlet(
		const FString& TestConfigName,
		bool bSync = false
	);

	/**
	 * 执行任意 UAT 命令。
	 *
	 * @param UATCommand  UAT 命令及参数（如 "BuildCookRun -platform=Win64 ..."）
	 * @param bSync       是否同步等待完成
	 */
	FUATRunResult RunCustomCommand(
		const FString& UATCommand,
		bool bSync = false
	);

	// ============================================================
	// 配置
	// ============================================================

	/** 设置自定义 RunUAT 路径（默认自动检测） */
	void SetRunUATPath(const FString& InPath) { RunUATPath = InPath; }

	/** 设置自定义项目路径（默认使用当前项目） */
	void SetProjectPath(const FString& InPath) { ProjectPath = InPath; }

	/** 获取自动检测的 RunUAT 路径 */
	FString GetRunUATPath() const { return RunUATPath; }

	/** 检查 RunUAT 是否存在 */
	bool IsUATAvailable() const;

private:
	/** 执行 UAT 子进程 */
	FUATRunResult ExecuteUAT(const FString& Args, bool bSync);

	/** 自动检测 RunUAT 路径 */
	FString DetectRunUATPath() const;

	FString RunUATPath;
	FString ProjectPath;
};
